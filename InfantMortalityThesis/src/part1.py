"""Part 1: predict death before age one from information known before delivery.

Plan: plan/analysis_plan.md, section 3. Run the stages in order (each saves
its results, so later stages and notebooks/03_prediction.ipynb reuse them):

    python -I src/part1.py data       # build train / tune / test tables
    python -I src/part1.py fit        # fit and tune models on 2021
    python -I src/part1.py evaluate   # test metrics, bootstrap CIs, calibration, subgroups
    python -I src/part1.py importance # factor ranking, drop-group refits, leakage check

Train: 2016–2020 (all deaths + 10% of survivors, survivors weighted x10, so
probabilities stay calibrated). Tune: 2021 (all births). Test: 2022–2023 (all births, used once).
"""
import json
import sys
import time
from pathlib import Path

import duckdb
import joblib
import numpy as np
import polars as pl
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import MissingIndicator, SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, SplineTransformer, StandardScaler

sys.path.insert(0, str(Path(__file__).parent))
from features import FEATURES, KIND, SET_A, SET_B, SPLINE, TREE_CATEGORICAL  # noqa: E402
from metrics import SortedScores, brier, calibration  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
PARQUET = ROOT / "data" / "parquet"
WORK = ROOT / "data" / "part1"          # ignored by Git: tables, models, predictions
REPORTS = ROOT / "reports"
SEED = 20261123
SURVIVOR_SAMPLE = 10                    # keep 1 in 10 survivors in training
N_BOOT = 1000
N_PERM = 20

SETS = {"A": SET_A, "B": SET_B, "B_no_marital": [f for f in SET_B if f != "marital"]}
LOGIT_C = [0.01, 0.1, 1.0]
HGB_GRID = [
    {"learning_rate": 0.1, "max_leaf_nodes": 31, "min_samples_leaf": 1000},
    {"learning_rate": 0.1, "max_leaf_nodes": 63, "min_samples_leaf": 500},
    {"learning_rate": 0.05, "max_leaf_nodes": 127, "min_samples_leaf": 2000},
]


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


# ---------------------------------------------------------------- data
def stage_data():
    WORK.mkdir(parents=True, exist_ok=True)
    cols = ",\n  ".join(f"{f.sql} AS {f.name}" for f in FEATURES)
    base = f"""
      SELECT {cols},
        CAST(MAGER9 AS INT) AS agegrp, death, cohort,
        hash(cohort, file_row_number) % {SURVIVOR_SAMPLE} = 0 AS sampled
      FROM read_parquet('{PARQUET}/cohort_*.parquet', union_by_name = true, file_row_number = true)
      WHERE CAST(RESTATUS AS INT) < 4"""
    con = duckdb.connect()
    con.sql("SET threads TO 8")
    parts = {
        "train": f"SELECT *, CASE WHEN death THEN 1.0 ELSE {SURVIVOR_SAMPLE}.0 END AS w FROM ({base}) "
                 f"WHERE cohort BETWEEN 2016 AND 2020 AND (death OR sampled)",
        "tune": f"SELECT *, 1.0 AS w FROM ({base}) WHERE cohort = 2021",
        "test": f"SELECT *, 1.0 AS w FROM ({base}) WHERE cohort IN (2022, 2023)",
    }
    for name, q in parts.items():
        con.sql(f"COPY ({q}) TO '{WORK / name}.parquet' (FORMAT parquet)")
        n, d = con.sql(f"SELECT COUNT(*), SUM(death::INT) FROM '{WORK / name}.parquet'").fetchall()[0]
        log(f"{name}: {n:,} rows, {d:,} deaths")


def load(name, feats=None):
    df = pl.read_parquet(WORK / f"{name}.parquet")
    feats = feats or SET_B
    X = df.select(feats).to_numpy().astype(np.float32)
    return df, X, df["death"].to_numpy().astype(np.float64), df["w"].cast(pl.Float64).to_numpy()


# ---------------------------------------------------------------- models
def logistic_pipeline(feats, C):
    spl = [i for i, f in enumerate(feats) if f in SPLINE]
    numc = [i for i, f in enumerate(feats) if KIND[f] == "num" and f not in SPLINE]
    cat = [i for i, f in enumerate(feats) if KIND[f] == "cat"]
    pre = ColumnTransformer([
        ("spline", Pipeline([("imp", SimpleImputer(strategy="median")),
                             ("spl", SplineTransformer(n_knots=5, degree=3))]), spl),
        ("spline_missing", MissingIndicator(features="all"), spl),
        ("num", Pipeline([("imp", SimpleImputer(strategy="median", add_indicator=True)),
                          ("sc", StandardScaler())]), numc),
        ("cat", Pipeline([("imp", SimpleImputer(strategy="constant", fill_value=-1)),
                          ("oh", OneHotEncoder(handle_unknown="ignore"))]), cat),
    ], sparse_threshold=1.0)
    return Pipeline([("pre", pre), ("lr", LogisticRegression(C=C, max_iter=5000, tol=1e-6))])


def baseline_b_pipeline():
    # model (b): mother's age group + race/Hispanic origin only, as categories
    pre = ColumnTransformer([("cat", Pipeline([("imp", SimpleImputer(strategy="constant", fill_value=-1)),
                                                ("oh", OneHotEncoder(handle_unknown="ignore"))]), [0, 1])])
    return Pipeline([("pre", pre), ("lr", LogisticRegression(C=1.0, max_iter=5000, tol=1e-6))])


def hgb(feats, params):
    mask = [f in TREE_CATEGORICAL for f in feats]
    return HistGradientBoostingClassifier(
        **params, l2_regularization=1.0, max_iter=2000, early_stopping=True, validation_fraction=0.1,
        n_iter_no_change=30, scoring="loss", categorical_features=mask, random_state=SEED)


def fit(model, X, y, w):
    if isinstance(model, Pipeline):
        # Normalized weights (mean 1) and a strict tolerance: with raw weights the
        # default solver stopped after ~27 iterations, before convergence.
        return model.fit(X, y, lr__sample_weight=w / w.mean())
    return model.fit(X, y, sample_weight=w)


def predict(model, X, chunk=1_000_000):
    return np.concatenate([model.predict_proba(X[i:i + chunk])[:, 1] for i in range(0, len(X), chunk)])


def stage_fit():
    tr, _, ytr, wtr = load("train")
    tu, _, ytu, _ = load("tune")
    rows, best = [], {}
    rate = float(np.sum(wtr * ytr) / np.sum(wtr))
    joblib.dump(rate, WORK / "model_a_rate.joblib")
    rows.append({"model": "a_baseline_rate", "set": "-", "params": "", "tune_pr_auc": SortedScores(ytu, np.full(len(ytu), rate)).metrics()[0]})

    Xb_tr = tr.select("agegrp", "race").to_numpy().astype(np.float32)
    Xb_tu = tu.select("agegrp", "race").to_numpy().astype(np.float32)
    m = fit(baseline_b_pipeline(), Xb_tr, ytr, wtr)
    ap = SortedScores(ytu, predict(m, Xb_tu)).metrics()[0]
    rows.append({"model": "b_age_race_logistic", "set": "-", "params": "", "tune_pr_auc": ap})
    joblib.dump(m, WORK / "model_b.joblib")
    log("b", round(ap, 4))

    for set_name, feats in SETS.items():
        Xtr = tr.select(feats).to_numpy().astype(np.float32)
        Xtu = tu.select(feats).to_numpy().astype(np.float32)
        kinds = [("c_logistic", c, lambda c=c: logistic_pipeline(feats, c)) for c in LOGIT_C] if set_name != "B_no_marital" else []
        kinds += [("d_hgb", json.dumps(p), lambda p=p: hgb(feats, p)) for p in HGB_GRID]
        for kind, params, make in kinds:
            t = time.time()
            m = fit(make(), Xtr, ytr, wtr)
            ap = SortedScores(ytu, predict(m, Xtu)).metrics()[0]
            extra = {"n_iter": int(m.n_iter_)} if hasattr(m, "n_iter_") and kind == "d_hgb" else {}
            rows.append({"model": kind, "set": set_name, "params": str(params), "tune_pr_auc": ap, **extra})
            log(kind, set_name, params, round(ap, 4), f"{time.time() - t:.0f}s")
            key = (kind, set_name)
            if key not in best or ap > best[key][0]:
                best[key] = (ap, params)
                joblib.dump(m, WORK / f"model_{kind}_{set_name}.joblib")
    pl.DataFrame(rows).write_csv(REPORTS / "part1_tuning.csv")
    log("done fit")


# ---------------------------------------------------------------- evaluate
MODELS = [("b_age_race_logistic", "-"), ("c_logistic", "A"), ("d_hgb", "A"),
          ("c_logistic", "B"), ("d_hgb", "B"), ("d_hgb", "B_no_marital")]


def test_predictions():
    f = WORK / "test_preds.parquet"
    if f.exists():
        return pl.read_parquet(f)
    te = pl.read_parquet(WORK / "test.parquet")
    out = {"death": te["death"], "cohort": te["cohort"], "race": te["race"], "pay": te["pay"]}
    out["a_baseline_rate|-"] = np.full(te.height, joblib.load(WORK / "model_a_rate.joblib"))
    out["b_age_race_logistic|-"] = predict(joblib.load(WORK / "model_b.joblib"),
                                           te.select("agegrp", "race").to_numpy().astype(np.float32))
    for kind, s in MODELS[1:]:
        X = te.select(SETS[s]).to_numpy().astype(np.float32)
        out[f"{kind}|{s}"] = predict(joblib.load(WORK / f"model_{kind}_{s}.joblib"), X)
        log("predicted", kind, s)
    df = pl.DataFrame(out)
    df.write_parquet(f)
    return df


def best_model_key():
    tun = pl.read_csv(REPORTS / "part1_tuning.csv")
    b = tun.filter(pl.col("set") == "B").sort("tune_pr_auc", descending=True).row(0, named=True)
    return f"{b['model']}|B"


def stage_evaluate():
    pr = test_predictions()
    y = pr["death"].to_numpy().astype(np.float64)
    keys = [c for c in pr.columns if "|" in c]
    best = best_model_key()
    log("best model by 2021 PR-AUC:", best)
    sorted_ = {k: SortedScores(y, pr[k].to_numpy()) for k in keys}
    point = {k: sorted_[k].metrics() + (brier(y, pr[k].to_numpy()),) for k in keys}

    cache = WORK / "bootstrap.npz"
    if cache.exists():                      # reuse a finished bootstrap (same seed, same predictions)
        z = np.load(cache)
        boot = {k: z[k.replace("|", "__")] for k in keys}
    else:
        rng = np.random.default_rng(SEED)
        boot = {k: [] for k in keys}
        for r in range(N_BOOT):
            w = rng.poisson(1.0, len(y)).astype(np.float64)
            for k in keys:
                ap, auc = sorted_[k].metrics(w)
                boot[k].append((ap, auc, brier(y, pr[k].to_numpy(), w)))
            if r % 100 == 0:
                log("bootstrap", r)
        boot = {k: np.array(v) for k, v in boot.items()}
        np.savez(cache, **{k.replace("|", "__"): v for k, v in boot.items()})
    log("bootstrap ready", {k: v.shape for k, v in boot.items()})

    rows = []
    for k in keys:
        lo, hi = np.percentile(boot[k], [2.5, 97.5], axis=0)
        cal = calibration(y, pr[k].to_numpy()) if not k.startswith("a_") else {}
        rows.append({"model": k.split("|")[0], "set": k.split("|")[1], "is_best": k == best,
                     "pr_auc": point[k][0], "pr_auc_lo": lo[0], "pr_auc_hi": hi[0],
                     "roc_auc": point[k][1], "roc_auc_lo": lo[1], "roc_auc_hi": hi[1],
                     "brier": point[k][2], "brier_lo": lo[2], "brier_hi": hi[2], **cal})
    comp = pl.DataFrame(rows)
    comp.write_csv(REPORTS / "part1_model_comparison.csv")

    # paired differences in PR-AUC (bootstrap uses the same weights for every model)
    diffs = []
    for k in keys:
        if k == best:
            continue
        d = boot[best][:, 0] - boot[k][:, 0]
        diffs.append({"best": best, "compared_with": k, "pr_auc_diff": point[best][0] - point[k][0],
                      "lo": np.percentile(d, 2.5), "hi": np.percentile(d, 97.5)})
    pl.DataFrame(diffs).write_csv(REPORTS / "part1_pr_auc_differences.csv")

    # per test year
    yrs = []
    for yr in (2022, 2023):
        m = (pr["cohort"] == yr).to_numpy()
        for k in keys:
            p = pr[k].to_numpy()[m]
            ap, auc = SortedScores(y[m], p).metrics()
            cal = calibration(y[m], p) if not k.startswith("a_") else {}
            yrs.append({"test_year": yr, "model": k, "pr_auc": ap, "roc_auc": auc, "brier": brier(y[m], p), **cal})
    pl.DataFrame(yrs).write_csv(REPORTS / "part1_test_years.csv")

    # calibration by decile of predicted risk, for the best Set A and Set B models
    dec = []
    for k in [best, best.replace("|B", "|A")]:
        p = pr[k].to_numpy()
        q = np.quantile(p, np.linspace(0, 1, 11))
        idx = np.clip(np.searchsorted(q, p, side="right") - 1, 0, 9)
        for d in range(10):
            m = idx == d
            dec.append({"model": k, "decile": d + 1, "n": int(m.sum()), "mean_predicted": float(p[m].mean()),
                        "observed_rate": float(y[m].mean()), "deaths": int(y[m].sum())})
    pl.DataFrame(dec).write_csv(REPORTS / "part1_calibration_deciles.csv")

    # subgroups for the best model
    sub = []
    p = pr[best].to_numpy()
    for var in ("race", "pay"):
        vals = pr[var].to_numpy()
        for v in sorted(set(vals[~np.isnan(vals)].tolist())) + [np.nan]:
            m = np.isnan(vals) if np.isnan(v) else vals == v
            if y[m].sum() < 20:
                continue
            ap, auc = SortedScores(y[m], p[m]).metrics()
            sub.append({"variable": var, "code": None if np.isnan(v) else int(v), "births": int(m.sum()),
                        "deaths": int(y[m].sum()), "pr_auc": ap, "roc_auc": auc,
                        "observed_over_expected": float(y[m].sum() / p[m].sum())})
    pl.DataFrame(sub).write_csv(REPORTS / "part1_subgroups.csv")
    log("done evaluate")


# ---------------------------------------------------------------- importance and leakage
def stage_importance():
    best = best_model_key()
    kind = best.split("|")[0]
    feats = SETS["B"]
    model = joblib.load(WORK / f"model_{kind}_B.joblib")
    te = pl.read_parquet(WORK / "test.parquet")
    # subsample for permutation: all deaths + 1 in 10 survivors (weight 10)
    sub = te.filter(pl.col("death") | pl.col("sampled"))
    Xs = sub.select(feats).to_numpy().astype(np.float32)
    ys = sub["death"].to_numpy().astype(np.float64)
    ws = np.where(ys == 1, 1.0, float(SURVIVOR_SAMPLE))
    base_ap = SortedScores(ys, predict(model, Xs)).metrics(ws)[0]
    rng = np.random.default_rng(SEED)
    rows = []
    for j, f in enumerate(feats):
        drops = []
        for _ in range(N_PERM):
            Xp = Xs.copy()
            Xp[:, j] = rng.permutation(Xp[:, j])
            drops.append(base_ap - SortedScores(ys, predict(model, Xp)).metrics(ws)[0])
        rows.append({"feature": f, "pr_auc_drop_mean": float(np.mean(drops)), "pr_auc_drop_sd": float(np.std(drops))})
        log("perm", f, round(np.mean(drops), 5))
    imp = pl.DataFrame(rows).sort("pr_auc_drop_mean", descending=True)
    imp.write_csv(REPORTS / "part1_importance.csv")

    # drop-group refits for the top 10 (same model type and settings, refit without the item)
    tr, _, ytr, wtr = load("train")
    y_te = te["death"].to_numpy().astype(np.float64)
    full_ap = SortedScores(y_te, predict(model, te.select(feats).to_numpy().astype(np.float32))).metrics()[0]
    params = model.get_params()
    rows = []
    for f in imp["feature"][:10].to_list():
        keep = [x for x in feats if x != f]
        if kind == "d_hgb":
            m = HistGradientBoostingClassifier(**{**params, "categorical_features": [x in TREE_CATEGORICAL for x in keep]})
        else:
            m = logistic_pipeline(keep, params["lr__C"])
        m = fit(m, tr.select(keep).to_numpy().astype(np.float32), ytr, wtr)
        ap = SortedScores(y_te, predict(m, te.select(keep).to_numpy().astype(np.float32))).metrics()[0]
        rows.append({"feature": f, "test_pr_auc_without": ap, "test_pr_auc_full": full_ap, "drop": full_ap - ap})
        log("drop-refit", f, round(full_ap - ap, 5))
    pl.DataFrame(rows).write_csv(REPORTS / "part1_dropgroup.csv")

    # leakage: each input alone. Score = training death rate for its value (numbers in 50 quantile bins).
    rows = []
    for f in feats:
        xtr, xte = tr[f].to_numpy(), te[f].to_numpy()
        if KIND[f] == "num" and len(np.unique(xtr[~np.isnan(xtr)])) > 50:
            edges = np.unique(np.nanquantile(xtr, np.linspace(0, 1, 51)))
            btr, bte = np.digitize(xtr, edges), np.digitize(xte, edges)
        else:
            btr, bte = xtr, xte
        btr = np.where(np.isnan(btr), -999, btr)
        bte = np.where(np.isnan(bte), -999, bte)
        rate = (pl.DataFrame({"b": btr, "y": ytr, "w": wtr})
                .group_by("b").agg(r=(pl.col("y") * pl.col("w")).sum() / pl.col("w").sum()))
        score = (pl.DataFrame({"b": bte}).join(rate, on="b", how="left")["r"]
                 .fill_null(float(np.sum(ytr * wtr) / np.sum(wtr))).to_numpy())
        auc = SortedScores(y_te, score).metrics()[1]
        rows.append({"feature": f, "roc_auc_alone": auc, "flag_over_0_80": auc > 0.80})
    pl.DataFrame(rows).sort("roc_auc_alone", descending=True).write_csv(REPORTS / "part1_leakage.csv")
    log("done importance")


# ---------------------------------------------------------------- post-hoc sensitivity
TIMING_ITEMS = ["precare", "illb", "ilp"]   # depend on pregnancy length (see change log, 23 Nov 2026)


def stage_strict():
    """Post-hoc: best boosting settings of Sets A and B, refit without the timing items."""
    tun = pl.read_csv(REPORTS / "part1_tuning.csv")
    tr, _, ytr, wtr = load("train")
    te = pl.read_parquet(WORK / "test.parquet")
    y = te["death"].to_numpy().astype(np.float64)
    pr = test_predictions()
    rows, preds = [], {}
    for s in ("A", "B"):
        params = json.loads(tun.filter((pl.col("model") == "d_hgb") & (pl.col("set") == s))
                            .sort("tune_pr_auc", descending=True)["params"][0])
        feats = [f for f in SETS[s] if f not in TIMING_ITEMS]
        m = fit(hgb(feats, params), tr.select(feats).to_numpy().astype(np.float32), ytr, wtr)
        p = predict(m, te.select(feats).to_numpy().astype(np.float32))
        preds[f"d_hgb|{s}_strict"] = p
        preds[f"d_hgb|{s}"] = pr[f"d_hgb|{s}"].to_numpy()
        log("strict fitted", s)
    srt = {k: SortedScores(y, v) for k, v in preds.items()}
    rng = np.random.default_rng(SEED)
    boot = {k: [] for k in preds}
    for r in range(N_BOOT):
        w = rng.poisson(1.0, len(y)).astype(np.float64)
        for k in preds:
            boot[k].append(srt[k].metrics(w)[0])
        if r % 200 == 0:
            log("bootstrap", r)
    boot = {k: np.array(v) for k, v in boot.items()}
    for k, p in preds.items():
        ap, auc = srt[k].metrics()
        lo, hi = np.percentile(boot[k], [2.5, 97.5])
        rows.append({"model": k, "pr_auc": ap, "pr_auc_lo": lo, "pr_auc_hi": hi, "roc_auc": auc,
                     "brier": brier(y, p), **calibration(y, p)})
    for s in ("A", "B"):
        d = boot[f"d_hgb|{s}"] - boot[f"d_hgb|{s}_strict"]
        rows.append({"model": f"difference {s} - {s}_strict", "pr_auc": float(np.mean(d)),
                     "pr_auc_lo": np.percentile(d, 2.5), "pr_auc_hi": np.percentile(d, 97.5)})
    pl.DataFrame(rows).write_csv(REPORTS / "part1_strict.csv")
    log("done strict")


if __name__ == "__main__":
    {"data": stage_data, "fit": stage_fit, "evaluate": stage_evaluate, "importance": stage_importance,
     "strict": stage_strict}[sys.argv[1]]()
