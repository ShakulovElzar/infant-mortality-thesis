"""Create notebooks/03_prediction.ipynb. Result notes are filled in from RESULT_NOTES after the run."""
import json
from pathlib import Path

import nbformat as nbf

NB = Path(__file__).resolve().parents[1] / "notebooks"
NOTES = json.loads((Path(__file__).parent / "part1_notes.json").read_text()) if (Path(__file__).parent / "part1_notes.json").exists() else {}
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell


def note(key):
    return md(NOTES.get(key, "*Result note: to be written after the run.*"))


SETUP = '''import sys
from pathlib import Path
ROOT = Path.cwd().parent
sys.path.insert(0, str(ROOT / "src"))
import polars as pl
import matplotlib.pyplot as plt
from features import LABEL, SET_A, SET_B
R, FIG = ROOT / "reports", ROOT / "reports" / "figures"
pl.Config.set_tbl_rows(50); pl.Config.set_tbl_width_chars(180); pl.Config.set_float_precision(4)
NAMES = {"a_baseline_rate": "(a) baseline rate", "b_age_race_logistic": "(b) age + race logistic",
         "c_logistic": "(c) penalized logistic", "d_hgb": "(d) gradient boosting"}'''

nb = nbf.v4.new_notebook()
nb.metadata["kernelspec"] = {"display_name": "Python (infant-mortality)", "language": "python", "name": "infant-mortality"}
nb.cells = [
    md("""# 03 — Part 1: predicting infant death from information known before delivery

**Goal.** Measure how well information that is known *before the baby is born* predicts death before age one, in birth cohorts the models have never seen. Then rank which items carry the most predictive value.

**Thesis part.** Part 1 (prediction). Plan: `plan/analysis_plan.md`, section 3. Methods and pass/fail rules were fixed before this run.

**Inputs.** `data/parquet/cohort_<year>.parquet`. The heavy work runs in `src/part1.py` (stages `data`, `fit`, `evaluate`, `importance`, about 1–2 hours in total). This notebook shows and explains the saved results.

**Outputs.** `reports/part1_*.csv` and `reports/figures/part1_*.png`.

**How to run.** From `InfantMortalityThesis/`: `python -I src/part1.py data`, then `fit`, `evaluate`, `importance`. Then run this notebook.

**Terms.**
- *Prediction* asks "which babies are at high risk?". It does **not** say what causes death.
- *Set A* = items known in early pregnancy (age, race, education, payment, history, BMI, pre-pregnancy diabetes and hypertension, father's items). *Set B* = Set A + items known before delivery (1st-trimester smoking, start of prenatal care, WIC, gestational diabetes and hypertension, plurality, infections).
- *PR-AUC* (area under the precision–recall curve) is the main metric. With 0.55% deaths, a model that guesses gets PR-AUC ≈ 0.0055.
- *ROC-AUC*: the chance that a random death gets a higher score than a random survivor (0.5 = guessing, 1 = perfect).
- *Brier score*: the mean squared error of the predicted probabilities (lower is better).
- *Calibration*: whether predicted risks equal observed risks. Slope 1 and intercept 0 are perfect."""),
    md("## 1. Setup"),
    code(SETUP),
    md("""## 2. Data split by time

**What.** Training uses births 2016–2020: all deaths and 1 in 10 survivors, with survivors weighted ×10, so that the model still learns the true death rate. Tuning uses all 2021 births. The test uses all 2022–2023 births, once, at the end.

**Why.** A split by time copies real use: a model built on past births is applied to future births. A random split would hide changes over time."""),
    code('''pl.DataFrame({
    "part": ["train (2016–2020, sampled)", "tune (2021)", "test (2022–2023)"],
    "rows": [pl.scan_parquet(ROOT / f"data/part1/{n}.parquet").select(pl.len()).collect().item() for n in ("train", "tune", "test")],
    "deaths": [pl.scan_parquet(ROOT / f"data/part1/{n}.parquet").select(pl.col("death").sum()).collect().item() for n in ("train", "tune", "test")],
})'''),
    md("""## 3. Tuning on 2021

**What.** For each model type and input set we tried a few settings: the penalty strength `C` for logistic regression, and the tree size and learning rate for gradient boosting. We kept the setting with the highest PR-AUC on 2021.

**Why.** Choosing settings on 2021, not on the test years, keeps the test honest."""),
    code('''tun = pl.read_csv(R / "part1_tuning.csv")
tun.with_columns(pl.col("model").replace(NAMES)).sort("set", "model", "tune_pr_auc", descending=[False, False, True])'''),
    note("tuning"),
    md("""## 4. Test results (2022–2023), with 95% bootstrap intervals

**What.** Every model predicts every 2022–2023 birth. We compute PR-AUC, ROC-AUC and the Brier score, with 95% intervals from 1,000 bootstrap resamples, and the calibration intercept and slope.

**Expected (stated in the plan).** Set B beats Set A. ROC-AUC is moderate (about 0.65–0.75), because gestational age and birth weight are excluded on purpose."""),
    code('''comp = pl.read_csv(R / "part1_model_comparison.csv")
comp.with_columns(pl.col("model").replace(NAMES)).select(
    "model", "set", "is_best", "pr_auc", "pr_auc_lo", "pr_auc_hi", "roc_auc", "roc_auc_lo", "roc_auc_hi",
    "brier", "cal_intercept", "cal_slope", "observed_over_expected")'''),
    note("test"),
    md("""### Pre-set check 1: does the best model beat model (b)?

**Rule.** The best Set B model (chosen on 2021) must beat model (b) in PR-AUC, and the 95% interval of the difference must exclude 0. The bootstrap uses the same resamples for both models, so the difference is paired."""),
    code('''diff = pl.read_csv(R / "part1_pr_auc_differences.csv")
print(diff)
row = diff.filter(pl.col("compared_with") == "b_age_race_logistic|-").row(0, named=True)
print("CHECK 1:", "PASS" if row["lo"] > 0 else "FAIL", f"(difference {row['pr_auc_diff']:.4f}, 95% CI {row['lo']:.4f} to {row['hi']:.4f})")'''),
    md("""### Pre-set check 2: calibration

**Rule.** The calibration slope of the best model must be between 0.9 and 1.1 on the test set. The plot compares predicted and observed death rates in ten groups (deciles) of predicted risk. Points on the diagonal mean good calibration."""),
    code('''best = comp.filter(pl.col("is_best")).row(0, named=True)
print("CHECK 2:", "PASS" if 0.9 <= best["cal_slope"] <= 1.1 else "FAIL", f"(slope {best['cal_slope']:.3f})")
dec = pl.read_csv(R / "part1_calibration_deciles.csv")
fig, ax = plt.subplots(figsize=(5.5, 5))
for m, d in dec.group_by("model", maintain_order=True):
    ax.plot(d["mean_predicted"] * 1000, d["observed_rate"] * 1000, "o-", label=m[0].replace("|", ", set "))
lim = [0.5, max(dec["observed_rate"].max(), dec["mean_predicted"].max()) * 1000 * 1.2]
ax.plot(lim, lim, "k--", lw=1, label="perfect calibration")
ax.set_xscale("log"); ax.set_yscale("log")
ax.set_xlabel("Predicted deaths per 1,000 births"); ax.set_ylabel("Observed deaths per 1,000 births")
ax.set_title("Calibration by decile of predicted risk, 2022–2023"); ax.legend(frameon=False, fontsize=8)
fig.tight_layout(); fig.savefig(FIG / "part1_calibration.png", dpi=150); plt.show()'''),
    note("calibration"),
    md("""## 5. Each test year separately

**Why.** The maternal risk factors rise from year to year (see `02_table1`). If a model gets worse or less calibrated in 2023 than in 2022, that shows the cost of time shift."""),
    code('''pl.read_csv(R / "part1_test_years.csv").filter(~pl.col("model").str.starts_with("a_")).select(
    "test_year", "model", "pr_auc", "roc_auc", "cal_intercept", "cal_slope", "observed_over_expected").sort("model", "test_year")'''),
    note("years"),
    md("""## 6. Subgroups (best model)

**What.** Performance and calibration by mother's race/Hispanic origin and by payment source. `observed_over_expected` above 1 means the model *under*-predicts risk in that group.

**Why.** A model can be accurate on average but unfair for one group."""),
    code('''RACE = {1: "NH White", 2: "NH Black", 3: "NH AIAN", 4: "NH Asian", 5: "NH NHOPI", 6: "NH multiple", 7: "Hispanic"}
PAY = {1: "Medicaid", 2: "Private", 3: "Self-pay", 4: "Other"}
sub = pl.read_csv(R / "part1_subgroups.csv")
sub.with_columns(group=pl.when(pl.col("variable") == "race").then(pl.col("code").replace_strict(RACE, default="Unknown", return_dtype=pl.Utf8))
                       .otherwise(pl.col("code").replace_strict(PAY, default="Unknown", return_dtype=pl.Utf8))) \\
   .select("variable", "group", "births", "deaths", "pr_auc", "roc_auc", "observed_over_expected")'''),
    note("subgroups"),
    md("""## 7. Which items carry predictive value?

**What.** *Permutation importance*: we shuffle one item across test births and measure how much PR-AUC drops (20 repeats). A large drop means the model relies on that item. For speed this uses all test deaths and 1 in 10 test survivors (weighted ×10). The top 10 are then confirmed by *drop-group refits*: the model is retrained without the item and tested again.

**Important.** Importance means predictive value, **not** cause. An item can predict well because it is a marker of something else (for example, payment source marks income)."""),
    code('''imp = pl.read_csv(R / "part1_importance.csv").with_columns(label=pl.col("feature").replace_strict(LABEL))
drop = pl.read_csv(R / "part1_dropgroup.csv").select("feature", pl.col("drop").alias("refit_drop"))
tab = imp.join(drop, on="feature", how="left")
fig, ax = plt.subplots(figsize=(7, 7))
t = tab.head(20).reverse()
ax.barh(t["label"], t["pr_auc_drop_mean"], xerr=t["pr_auc_drop_sd"], color="#4C72B0")
ax.set_xlabel("Drop in test PR-AUC when the item is shuffled"); ax.set_title("Permutation importance, best Set B model (top 20)")
fig.tight_layout(); fig.savefig(FIG / "part1_importance.png", dpi=150); plt.show()
tab.select("label", "pr_auc_drop_mean", "pr_auc_drop_sd", "refit_drop")'''),
    note("importance"),
    md("""### Pre-set check 3: leakage

**Rule.** If any single item alone reaches ROC-AUC > 0.80, it may contain information from after delivery, and it must be investigated before results are reported. Each item's score is the training death rate for its value."""),
    code('''leak = pl.read_csv(R / "part1_leakage.csv").with_columns(label=pl.col("feature").replace_strict(LABEL))
print("CHECK 3:", "PASS" if not (leak["roc_auc_alone"] > 0.80).any() else "INVESTIGATE")
leak.select("label", "roc_auc_alone", "flag_over_0_80")'''),
    note("leakage"),
    md("""## 8. Post-hoc sensitivity: without the timing items

**What.** After section 7, we refit the best boosting settings of Sets A and B **without** `precare`, `illb` and `ilp`, and test them on the same 2022–2023 births (1,000 paired bootstrap resamples).

**Why.** These items depend on the length of the pregnancy, so they leak a little information about preterm birth. This analysis was **not** in the original plan; it is recorded in the change log of `plan/analysis_plan.md`."""),
    code('''pl.read_csv(R / "part1_strict.csv").select("model", "pr_auc", "pr_auc_lo", "pr_auc_hi", "roc_auc", "cal_intercept", "cal_slope", "observed_over_expected")'''),
    note("strict"),
    md("## Summary"),
    note("summary"),
]
nbf.write(nb, NB / "03_prediction.ipynb")
print("written")
