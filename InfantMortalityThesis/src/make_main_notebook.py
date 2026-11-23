"""Create main.ipynb at the repo root: the thesis overview.

It does no heavy computing. It only reads results saved by the work notebooks
(notebooks/01_... to 05_...) and shows them in thesis order. Sections whose
results do not exist yet say so. Re-run this script only to reset the layout;
after that, edit main.ipynb directly.
"""
from pathlib import Path

import nbformat as nbf

REPO = Path(__file__).resolve().parents[2]
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell

nb = nbf.v4.new_notebook()
nb.metadata["kernelspec"] = {"display_name": "Python (infant-mortality)", "language": "python", "name": "infant-mortality"}
nb.cells = [
    md("""# Maternal Health Factors and Infant Mortality in U.S. Birth Cohorts 2016–2023

**Thesis overview notebook.** It shows the main results of the thesis in chapter order. It does not compute anything heavy: it only loads tables and figures that the work notebooks saved. It runs in a few seconds.

| Chapter | Question | Work notebook | Status |
|---|---|---|---|
| 1. Data | Are our data the same as CDC's? | `notebooks/01_benchmark.ipynb` | done |
| 2. Population | Who are the births in the study? | `notebooks/02_table1.ipynb` | done |
| 3. Prediction (Part 1) | How well can information known before delivery predict infant death? | `notebooks/03_prediction.ipynb` | not started |
| 4. Association (Part 2) | How much do pre-pregnancy hypertension, diabetes and BMI change the risk? | `notebooks/04_association.ipynb` | not started |
| 5. Checks | Do the pre-set checks pass? | `notebooks/05_checks.ipynb` | not started |

**Plan.** All methods and pass/fail rules were fixed before the results, in `InfantMortalityThesis/plan/analysis_plan.md` (v1.0, 23 Nov 2026).

**How to run.** Start Jupyter from the repo root, then *Run All*. To update a chapter, re-run its work notebook first."""),
    md("## Setup\nFind the project folder and load the plotting libraries. `show_if()` prints a short note when a chapter has no results yet, instead of an error."),
    code('''from pathlib import Path
import polars as pl
import matplotlib.pyplot as plt

REPO = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "InfantMortalityThesis").is_dir())
P = REPO / "InfantMortalityThesis"
REPORTS, REF, FIG = P / "reports", P / "reference", P / "reports" / "figures"
FIG.mkdir(parents=True, exist_ok=True)
pl.Config.set_tbl_rows(40); pl.Config.set_tbl_width_chars(160); pl.Config.set_fmt_str_lengths(45)

def show_if(path):
    """Return True if a saved result exists; otherwise say which notebook makes it."""
    if path.exists():
        return True
    print(f"Not available yet: {path.relative_to(P)}. Run the work notebook for this chapter first.")
    return False'''),

    md("""## 1. Data: do our files match CDC?

**Data.** CDC/NVSS linked birth–infant death **cohort** files, 2016–2023. A *birth cohort* is all babies born in one year, each followed for 365 days. We use births to U.S. residents.

**Check.** We compared our counts with the counts that CDC prints in each user guide."""),
    code('''counts = pl.read_csv(REF / "benchmark_counts.csv")
counts.select("cohort", pl.col("births_res").alias("births"), pl.col("deaths_res").alias("infant_deaths"),
              pl.col("imr_res").alias("deaths_per_1000"), "births_match", "deaths_match")'''),
    md("""**Reading.** All 8 cohorts match CDC's death counts, and births match in 7 of 8 (the 2020 guide has a typing error; see `01_benchmark`). The infant mortality rate falls from 5.80 per 1,000 births (2016) to 5.35 (2020), then stays at about 5.5."""),
    code('''t2 = pl.read_csv(REF / "benchmark_table2.csv")
t2.group_by("cohort").agg(
    cells=pl.len(),
    cells_off=((pl.col("diff_births") != 0) | (pl.col("diff_deaths") != 0)).sum(),
).sort("cohort").with_columns(result=pl.when(pl.col("cells_off") == 0).then(pl.lit("exact")).otherwise(pl.lit("see note")))'''),
    md("""**Reading.** CDC Documentation Table 2 (race × sex × birth weight, 210 cells) matches exactly for 2018–2023. In 2016 the re-released births file has birth weight for 2,493 births that the older CDC table lists as "Not stated"; in 2017 the CDC table repeats the all-races deaths in the NH White rows. Neither is an error in our data."""),

    md("""## 2. Population (Table 1)

**What.** The share of births in each category, among survivors and among infant deaths. These are crude differences, not effects."""),
    code('''t1 = pl.read_csv(REPORTS / "table1_by_outcome.csv", infer_schema_length=0)
key = ["Pre-pregnancy hypertension", "Pre-pregnancy diabetes", "Pre-pregnancy BMI", "Plurality",
       "Mother's race/Hispanic origin", "Payment source"]
t1.filter(pl.col("variable").is_in(key)).select(
    "variable", "category", pl.col("pct_Survivor").alias("% of survivors"), pl.col("pct_Death").alias("% of deaths"))'''),
    md("""**Reading.** Deaths are more often twins, births to NH Black mothers, Medicaid births, and births to mothers with pre-pregnancy hypertension, diabetes or obesity. BMI is unknown for 6.4% of deaths but 2.3% of survivors, so Part 2 adds a multiple-imputation analysis."""),
    md("**Trends.** The figure shows how the three maternal factors change from 2016 to 2023."),
    code('''tc = pl.read_csv(REPORTS / "table1_by_cohort.csv", infer_schema_length=0)
years = [str(y) for y in range(2016, 2024)]
series = {
    "Pre-pregnancy hypertension": ("Pre-pregnancy hypertension", "Yes"),
    "Pre-pregnancy diabetes": ("Pre-pregnancy diabetes", "Yes"),
    "Obesity class III (BMI ≥ 40)": ("Pre-pregnancy BMI", "Obesity III >=40"),
    "Gestational hypertension": ("Gestational hypertension", "Yes"),
}
fig, ax = plt.subplots(figsize=(7, 4))
for label, (var, cat) in series.items():
    row = tc.filter((pl.col("variable") == var) & (pl.col("category") == cat))
    ax.plot([int(y) for y in years], [float(row[y][0]) for y in years], marker="o", label=label)
ax.set_xlabel("Birth cohort"); ax.set_ylabel("% of births"); ax.set_title("Maternal risk factors, U.S. births 2016–2023")
ax.legend(frameon=False); ax.grid(alpha=0.3)
fig.tight_layout(); fig.savefig(FIG / "risk_factor_trends.png", dpi=150); plt.show()'''),
    md("""**Reading.** All four factors rise. Pre-pregnancy hypertension almost doubles (1.7% to 3.2%). This matters for Part 1: models trained on 2016–2020 are tested on 2022–2023, when the population is different."""),

    md("""## 3. Prediction (Part 1)

**Question.** How well can information known before delivery predict death before age one in later cohorts (train 2016–2020, test 2022–2023)? Which items carry most of the predictive value?

**Main metric.** PR-AUC (area under the precision–recall curve), because only about 0.55% of babies die."""),
    code('''f = REPORTS / "part1_model_comparison.csv"
if show_if(f):
    display(pl.read_csv(f))'''),
    md("*Results and reading will be added after `03_prediction` runs.*"),

    md("""## 4. Association (Part 2)

**Question.** After adjustment for confounders, how much do pre-pregnancy hypertension, pre-pregnancy diabetes and BMI class change the risk of infant death? Results are *risk ratios* (RR: the risk with the factor divided by the risk without it) and *risk differences* per 1,000 births."""),
    code('''f = REPORTS / "part2_results.csv"
if show_if(f):
    display(pl.read_csv(f))'''),
    md("*Results and reading will be added after `04_association` runs.*"),

    md("""## 5. Pre-set checks

**What.** Each claim has a test, fixed in the plan, that can fail it: the CDC benchmark, model calibration, leakage, direction in 7 of 8 cohorts, the negative-control outcome, and missing data."""),
    code('''f = REPORTS / "checks.csv"
if show_if(f):
    display(pl.read_csv(f))'''),

    md("""## Limitations (so far)

- **Live births only.** Stillbirths are not in the data. A factor that causes stillbirth can look weaker among live births.
- **No geography.** The public files have no state or county, so area factors (poverty, hospitals) cannot be added per birth.
- **Certificate quality.** Risk factors come from birth certificates and can be under-reported.
- **Timing.** Some pregnancy items (for example gestational diabetes) are recorded only if the pregnancy lasts long enough for the test."""),
]
nbf.write(nb, REPO / "main.ipynb")
print("written", REPO / "main.ipynb")
