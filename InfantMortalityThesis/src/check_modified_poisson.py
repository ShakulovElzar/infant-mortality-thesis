"""Check src/modified_poisson.py against statsmodels on SYNTHETIC data.

Run: python -I src/check_modified_poisson.py
Pass = grouped estimates, robust SEs and the g-computation risk difference equal
the single-row statsmodels results (differences < 1e-8). No real data is used.
Result on 23 Nov 2026: beta diff 1.3e-12, SE diff 4.7e-12, RD equal.
"""
import sys
from pathlib import Path

import numpy as np
import polars as pl
import statsmodels.api as sm

sys.path.insert(0, str(Path(__file__).parent))
from modified_poisson import design, fit, rr, standardized_rd  # noqa: E402

rng = np.random.default_rng(1)
N = 300_000
age, race = rng.integers(1, 6, N), rng.integers(1, 4, N)
expo = (rng.random(N) < 0.03 + 0.01 * (age > 3)).astype(int)
y = (rng.random(N) < 0.004 * np.exp(0.6 * expo + 0.15 * (age - 3) + 0.3 * (race == 2))).astype(float)

Xi = np.column_stack([np.ones(N)] + [(age == a).astype(float) for a in range(2, 6)]
                     + [(race == r).astype(float) for r in (2, 3)] + [expo.astype(float)])
ref = sm.GLM(y, Xi, family=sm.families.Poisson()).fit(cov_type="HC0")

g = pl.DataFrame({"age": age, "race": race, "expo": expo, "y": y}).group_by("age", "race", "expo") \
      .agg(n=pl.len(), d=pl.col("y").sum())
X, names = design({c: g[c].to_numpy() for c in ("age", "race", "expo")}, ["age", "race", "expo"],
                  {"age": 1, "race": 1, "expo": 0})
res = fit(X, g["n"].to_numpy(), g["d"].to_numpy())
order = [names.index(t) for t in ["intercept", "age=2", "age=3", "age=4", "age=5", "race=2", "race=3", "expo=1"]]

beta_diff = np.max(np.abs(res["beta"][order] - ref.params))
se_diff = np.max(np.abs(np.sqrt(np.diag(res["cov_robust"]))[order] / ref.bse - 1))
exposed = g["expo"].to_numpy() == 1
rd_grouped = standardized_rd(res, X, g["n"].to_numpy(), exposed, [names.index("expo=1")], draws=100)["rd_per_1000"]
Xe = Xi[expo == 1]
X0 = Xe.copy()
X0[:, -1] = 0
rd_single = 1000 * np.mean(np.exp(Xe @ ref.params) - np.exp(X0 @ ref.params))

print(f"beta diff {beta_diff:.1e}, SE diff {se_diff:.1e}, RD {rd_grouped:.6f} vs {rd_single:.6f}, "
      f"RR {rr(res, names, 'expo=1')['rr']:.4f}")
assert beta_diff < 1e-8 and se_diff < 1e-8 and abs(rd_grouped - rd_single) < 1e-8
print("PASS")
