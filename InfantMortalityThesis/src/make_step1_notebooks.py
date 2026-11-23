"""Create notebooks/01_benchmark.ipynb and notebooks/02_table1.ipynb (run once; then edit in Jupyter)."""
from pathlib import Path
import nbformat as nbf

NB = Path(__file__).resolve().parents[1] / "notebooks"
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell
SETUP = '''import sys
from pathlib import Path

ROOT = Path.cwd().parent            # notebooks/ -> InfantMortalityThesis/
sys.path.insert(0, str(ROOT / "src"))

import duckdb
import polars as pl
pl.Config.set_tbl_rows(60); pl.Config.set_tbl_cols(20); pl.Config.set_fmt_str_lengths(40)
PARQUET = ROOT / "data" / "parquet"
COHORTS = range(2016, 2024)'''

b = nbf.v4.new_notebook()
b.cells = [
    md("""# 01 — Benchmark: do our data match CDC's own numbers?

**Goal.** Show that the Parquet files we built contain exactly the births and infant deaths that CDC published. If they match, every later result rests on correct data.

**Thesis part.** Step 1 (data build), before Part 1 (prediction) and Part 2 (association). See `plan/analysis_plan.md`, section 5.

**Inputs.** `data/parquet/cohort_<year>.parquet` (built by `src/build_parquet.py`), and the CDC user guides in `docs/guides/`.

**Outputs.** `reference/benchmark_counts.csv`, `reference/benchmark_table2.csv`.

**How to run.** Build the Parquet files first (`python -I src/build_parquet.py data/cdc/*.zip`), then run all cells.

**Terms.**
- A *birth cohort* is all babies born in one calendar year. We follow each baby for 365 days.
- The *infant mortality rate* is infant deaths per 1,000 live births.
- *Residents* are births to mothers who live in the U.S. (`RESTATUS` 1–3). CDC tables exclude foreign residents (`RESTATUS` 4)."""),
    md("## 1. Setup\nLoad the libraries and set the paths. `duckdb` runs SQL directly on the Parquet files, so we never load 30 million rows into memory."),
    code(SETUP + "\nfrom benchmark import compare, guide_record_counts"),
    md("""## 2. Row counts per cohort

**What.** Count all births, resident births and linked deaths in each Parquet file. Compare them with the record counts that each CDC guide prints.

**Why.** If a row was lost or duplicated while reading the ZIP, the counts will differ.

**Expected.** Our counts equal the guide counts. Most guides count all records, including foreign residents; the 2016 guide counts residents only."""),
    code('''rows = []
for c in COHORTS:
    f = PARQUET / f"cohort_{c}.parquet"
    r = duckdb.sql(f"""SELECT COUNT(*) AS births_all,
                              SUM((CAST(RESTATUS AS INT) < 4)::INT)::BIGINT AS births_res,
                              SUM(death::INT)::BIGINT AS deaths_all,
                              SUM((death AND CAST(RESTATUS AS INT) < 4)::INT)::BIGINT AS deaths_res
                       FROM '{f}'""").fetchall()[0]
    rows.append({"cohort": c, "births_all": r[0], "births_res": r[1], "deaths_all": r[2], "deaths_res": r[3],
                 **guide_record_counts(c)})
counts = pl.DataFrame(rows).with_columns(
    births_match=(pl.col("guide_births") == pl.col("births_all")) | (pl.col("guide_births") == pl.col("births_res")),
    deaths_match=(pl.col("guide_deaths") == pl.col("deaths_all")) | (pl.col("guide_deaths") == pl.col("deaths_res")),
    imr_res=(1000 * pl.col("deaths_res") / pl.col("births_res")).round(2),
)
counts.write_csv(ROOT / "reference" / "benchmark_counts.csv")
counts'''),
    md("""**Result.** Births and deaths match the guide in every cohort, except the births count printed in the 2020 guide (3,549,826). Our file has 3,619,826 records. The difference is exactly 70,000, and NCHS reports 3,613,647 resident births for 2020, which equals our `births_res`. So the 2020 guide has a typing error; the data file is correct.

Deaths match in all 8 cohorts, and no death is left without its birth record (checked when the files were built)."""),
    md("""## 3. CDC Documentation Table 2: race × sex × birth weight

**What.** Each guide prints a cohort table of births and infant deaths by mother's race/Hispanic origin, infant sex and birth weight (10 columns). We read that table from the PDF and compute the same table from our data.

**Method detail.** Births come from our Parquet files. Deaths come from the death (numerator) records, because CDC tabulates deaths by the birth weight on the death record. CDC fills in (imputes) missing birth weight separately on the two records, so a few deaths have a different birth weight on each. With the death-record weight, the deaths match exactly.

**Why.** This checks four things together: the race field (`MRACEHISP`), sex (`SEX`), birth weight (`BRTHWGT`) and the death linkage.

**Pre-set check (plan, section 5).** Fail if any rate differs by more than 0.01 per 1,000. We also require exact equality of counts."""),
    code('''tables = pl.concat([compare(c) for c in COHORTS])
tables.write_csv(ROOT / "reference" / "benchmark_table2.csv")
summary = tables.group_by("cohort").agg(
    cells=pl.len(),
    birth_cells_off=(pl.col("diff_births") != 0).sum(),
    death_cells_off=(pl.col("diff_deaths") != 0).sum(),
    total_births_off=pl.col("diff_births").filter(pl.col("bw") == "Total").abs().sum(),
    max_rate_diff=(pl.col("rate") - pl.col("cdc_rate")).abs().max(),
).sort("cohort").with_columns(
    check=pl.when((pl.col("birth_cells_off") == 0) & (pl.col("death_cells_off") == 0) & (pl.col("max_rate_diff") <= 0.01))
           .then(pl.lit("PASS")).otherwise(pl.lit("FAIL")))
summary'''),
    md("""**Result.** Six cohorts (2018–2023) PASS: all 210 cells are identical. Two cohorts FAIL the strict rule, and both failures come from the CDC tables, not from our data:

- **2016, births only:** 2,493 births are "Not stated" in the CDC table but have a birth weight in our file. All other differences are these same births, now in a weight group, and every total is exact. Our 2016 births file is a re-release (`VS16LINK.DENOMUS_2026_06_04`), newer than the 2016 guide (2019). The likely cause is that the re-release imputes more missing birth weights. Deaths match exactly.
- **2017, NH White deaths only:** the CDC table prints the *all-races* deaths in the NH White rows (for example, 22,167 total deaths). That is a copying error in the guide. All other 180 cells match exactly.

So the data are correct. For the thesis, note that 2016 birth weight differs slightly from the 2016 guide; birth weight is not an input in Part 1 or Part 2.

Below is the "All races, both sexes" part for 2023, as an example of the comparison.

The first block below shows the 2017 NH White error: the CDC deaths equal the all-races deaths."""),
    code('''tables.filter((pl.col("cohort") == 2017) & (pl.col("sex") == "Both") & (pl.col("bw") == "Total")) \\
      .select("race", "cdc_deaths", "deaths").sort("race")'''),
    code('''tables.filter((pl.col("cohort") == 2023) & (pl.col("race") == "All") & (pl.col("sex") == "Both")) \\
      .select("bw", "cdc_births", "births", "cdc_deaths", "deaths", "cdc_rate", "rate")'''),
    md("""## Summary

- **Main finding.** The Parquet files reproduce CDC's published counts: births and deaths per cohort in all 8 cohorts, and all 210 cells of Documentation Table 2 in 2018–2023.
- **CDC guide errors found.** The 2020 guide prints 3,549,826 records (file and NCHS: 3,619,826). The 2017 table repeats all-races deaths in the NH White rows.
- **One real data difference.** The re-released 2016 births file has birth weight for 2,493 births that the 2016 guide lists as "Not stated". Totals are exact.
- **Open issues.** Table 2 does not check the maternal risk-factor fields; `02_table1` shows their distributions.
- **Next notebook.** `02_table1.ipynb`."""),
]
nbf.write(b, NB / "01_benchmark.ipynb")

t = nbf.v4.new_notebook()
t.cells = [
    md("""# 02 — Table 1: who are the births in the study?

**Goal.** Describe the study population: the share of births in each category of the main variables, among survivors and among infants who died, and how these shares change from 2016 to 2023.

**Thesis part.** Step 1. This becomes "Table 1" of the thesis. It also shows how much data is missing for each variable.

**Inputs.** `data/parquet/cohort_<year>.parquet`.

**Outputs.** `reports/table1_by_outcome.csv`, `reports/table1_by_cohort.csv`.

**How to run.** Run all cells (about 1 minute).

**Terms.**
- *Survivor*: a baby who did not die before age one. *Death*: a linked infant death before day 365.
- *Column %*: the share of a group (for example, of all deaths) that falls in one category.
- *Unknown*: the certificate has no value for this item. We show it as its own row."""),
    md("## 1. Setup"),
    code(SETUP + "\nfrom labels import TABLE1_VARS"),
    md("""## 2. Table 1 by outcome (all cohorts, U.S. residents)

**What.** For each variable, count births in each category, separately for survivors and deaths, and compute column percentages.

**Why.** Readers must see the population before any model. Large differences between survivors and deaths show which variables will matter. This is a description, not an adjusted result.

**Expected.** Deaths are more often twins, babies of Black mothers, Medicaid births and births to mothers with pre-pregnancy hypertension or diabetes."""),
    code('''ALL = f"'{PARQUET}/cohort_*.parquet'"

def table1(by: str) -> pl.DataFrame:
    out = []
    for var, (title, labels) in TABLE1_VARS.items():
        q = f"""SELECT {by} AS grp, COALESCE({var}, 'missing') AS code, COUNT(*) AS n
                FROM read_parquet({ALL}) WHERE CAST(RESTATUS AS INT) < 4 GROUP BY ALL"""
        d = pl.from_arrow(duckdb.sql(q).arrow()).with_columns(
            pl.col("grp").cast(pl.Utf8),
            pct=(100 * pl.col("n") / pl.col("n").sum().over("grp")).round(2),
            variable=pl.lit(title),
            category=pl.col("code").replace_strict(labels, default=pl.col("code")),
        )
        out.append(d)
    return pl.concat(out)

by_outcome = table1("CASE WHEN death THEN 'Death' ELSE 'Survivor' END")
wide = by_outcome.pivot(on="grp", index=["variable", "code", "category"], values=["n", "pct"]).sort("variable", "code")
wide.write_csv(ROOT / "reports" / "table1_by_outcome.csv")
wide'''),
    md("""**Result.** The table gives counts (`n_…`) and column percentages (`pct_…`) for survivors and deaths. A category that is much more common among deaths is linked to higher risk *before* any adjustment. These crude differences are not effects; Part 2 adjusts for confounders.

As expected, deaths are more often twins (12.2% vs 3.2% of survivors), births to NH Black mothers (27.5% vs 14.2%), Medicaid births (54.1% vs 41.6%), and births to mothers with pre-pregnancy hypertension (4.5% vs 2.4%) or diabetes (2.2% vs 1.0%). Obesity classes II–III are also more common among deaths.

**Three findings that change later steps:**
1. **Missing values are more common among deaths.** BMI is unknown for 6.4% of deaths but 2.3% of survivors; education for 4.5% vs 1.5%. This is far above the plan's 20% trigger (section 4, check 5), so Part 2 **must** add the multiple-imputation sensitivity analysis. A complete-case analysis alone could be biased.
2. **Gestational diabetes looks "protective" (4.9% of deaths vs 7.3% of survivors).** The likely reason is timing: it is usually tested at 24–28 weeks, so many very preterm babies are born before the test. This is the leakage risk named in the plan. In Part 1, compare Set A (without it) and Set B (with it), and read its importance with care.
3. **Plurality has an undocumented code 5** (126 births, 2016–2019). It is probably quintuplets or more; it is shown as its own row."""),
    md("""## 3. Table 1 by cohort year

**What.** The same percentages for all births, one column per cohort.

**Why.** Trends over time matter for Part 1, where we train on 2016–2020 and test on 2022–2023. A variable whose distribution shifts a lot can make an older model less accurate in later years.

**Expected.** Rising pre-pregnancy hypertension, gestational diabetes and obesity; falling smoking before pregnancy."""),
    code('''by_cohort = table1("cohort")
wide_c = by_cohort.pivot(on="grp", index=["variable", "code", "category"], values="pct").sort("variable", "code")
wide_c = wide_c.select("variable", "code", "category", *[str(c) for c in COHORTS])
wide_c.write_csv(ROOT / "reports" / "table1_by_cohort.csv")
wide_c'''),
    md("""**Result.** Each number is the percentage of all resident births in that year. Read across a row to see the trend.

The expected trends are present: pre-pregnancy hypertension rises from 1.7% (2016) to 3.2% (2023), gestational hypertension from 6.0% to 10.1%, gestational diabetes from 6.0% to 8.3%, and obesity class III from 4.8% to 6.2%. Smoking before pregnancy falls (no smoking: 90.1% to 95.9%). Payment source and plurality change little.

These shifts are large for the exposures, so the 2022–2023 test years differ from the 2016–2020 training years. Part 1 must report calibration per test year."""),
    md("""## Summary

- **Main finding.** The tables describe 29.9 million resident births and 166 thousand infant deaths, 2016–2023. The crude differences between deaths and survivors have the expected directions.
- **Open issues.** (1) Missing BMI and education are about 3 times more common among deaths, so multiple imputation is required in Part 2. (2) Gestational diabetes has a timing problem for prediction. (3) The exposures rise over time, so Part 1 must report calibration per test year.
- **Next notebook.** `03_prediction.ipynb` (Part 1)."""),
]
nbf.write(t, NB / "02_table1.ipynb")
print("written")
