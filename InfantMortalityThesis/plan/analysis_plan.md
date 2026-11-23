# Analysis plan

**Version 1.0 — fixed 23 November 2026, before any exposure–outcome result was computed.**
Already computed before this date: counts, join checks and per-year missing/positive rates for single fields (`reports/profile/`). No death rate by exposure has been looked at. Any later change goes into the change log at the end, with its date and reason.

## 1. Data and population

- **Source:** CDC/NVSS linked birth–infant death cohort files, birth cohorts 2016–2023 (`data/cdc/*.zip`). Join rules: `AGENTS.md`.
- **Population:** live births to U.S. residents (`RESTATUS` 1–3). 29,882,341 births, 166,367 linked infant deaths.
- **Part 2 only:** singleton births (`DPLURAL` = 1).
- **Weights:** none (`RECWT` is for period files only).
- **Reporting flags:** for each item, use only records with its `F_*` flag = 1.
- **Missing codes:** treat "unknown/not stated" codes (`9`, `99`, `U`, blank) as missing, per the field's layout entry.

## 2. Outcomes

| Name | Definition | Role |
|---|---|---|
| `death_1y` | linked death, `AGEDX` 0–364 | main |
| `death_neo` | `AGEDX` 0–27 | secondary |
| `death_postneo` | `AGEDX` 28–364; survivors past 27 days only | secondary |
| `death_accident` | `UCODR130` = 139, accidents (V01–X59) | negative control, Part 2 only |

## 3. Part 1: prediction from information known before delivery

**Question:** how well can information known before delivery predict death before age one in later cohorts, and which items carry most of the predictive value?

**Two prediction times (input sets):**
- **Set A, "early pregnancy":** maternal age, race/Hispanic origin (`MRACEHISP`), nativity, education, marital status, payment source (`PAY_REC`), parity and prior outcomes (`PRIORLIVE`, `PRIORDEAD`, `PRIORTERM`, `LBO_REC`), birth intervals (`ILLB_R11`, `ILP_R11`), pre-pregnancy smoking (`CIG_0`), pre-pregnancy BMI (`BMI`), height, pre-pregnancy diabetes, pre-pregnancy hypertension, previous preterm birth, infertility treatment, previous cesareans (`RF_CESARN`), father's age, race and education (missing = own category), cohort year.
- **Set B, "before delivery" (main):** Set A plus first-trimester smoking (`CIG_1`), month prenatal care began (`PRECARE`), WIC, gestational diabetes, gestational hypertension, plurality, infections (`IP_*`).
- **Excluded on purpose (leakage):** total prenatal visits (`PREVIS`) and 2nd/3rd-trimester smoking (`CIG_2`, `CIG_3`), because all of them depend on how long the pregnancy lasted. Eclampsia (`RF_EHYPE`) also, because it can start during labor. Everything recorded at or after delivery is excluded as well: gestational age, birth weight, Apgar, NICU, abnormal conditions, congenital anomalies, labor and delivery items, delivery weight, weight gain, breastfeeding, transfers and all death fields.
- **Marital status:** California is not released from 2017. Code it with a "not released" category; also run Set B without marital status.

**Split by time:** train 2016–2020, tune on 2021, test once on 2022–2023 (7.26 M births). Note: 2020–2021 are COVID years; report test results per test year.

**Models (same inputs, same split):**
- (a) baseline: the training-period death rate for everyone;
- (b) logistic regression with maternal age group and race/Hispanic origin only;
- (c) L2-penalized logistic regression, all inputs (categories one-hot, BMI and age as splines);
- (d) `HistGradientBoostingClassifier`, with tuning on 2021 only;
- (e) optional: LightGBM.

**No outcome resampling.** If the training set must be reduced for memory, survivors may be subsampled with inverse-sampling weights, so that probabilities stay calibrated.

**Metrics** (test set, 1,000 bootstrap resamples of test births, 95% CI): PR-AUC (main metric; the base rate is about 0.55%), ROC-AUC, Brier score, calibration intercept and slope, and a calibration plot by risk decile. Also by race/Hispanic origin and by payment source.

**Factor ranking:** grouped permutation importance on the test set, where one group = one original item with all its recodes (drop in PR-AUC, 20 repeats). The top 10 are confirmed by refitting without that group. Importance means predictive value, not cause.

**Pre-set checks (pass/fail):**
1. The best model beats model (b) in PR-AUC, and the 95% CI of the difference excludes 0.
2. Calibration slope is between 0.9 and 1.1 on the test set.
3. Leakage: if any single input alone has ROC-AUC > 0.80, investigate it before any result is reported.

**Expectations stated in advance:** Set B beats Set A; the strongest groups include plurality, previous preterm birth, payment source/education and race/Hispanic origin; ROC-AUC is moderate (about 0.65–0.75), because the strongest predictors (gestational age, birth weight) are excluded by design.

## 4. Part 2: association of three maternal factors

**Question:** after adjustment for confounders, how much do pre-pregnancy hypertension, pre-pregnancy diabetes and pre-pregnancy BMI class change the risk of death before age one?

| Exposure | Coding | Adjustment set (from the DAGs in `plan/dags/`) |
|---|---|---|
| Pre-pregnancy hypertension | `RF_PHYPE` Y vs N | maternal age, race/Hispanic origin, nativity, education, payment source, parity, pre-pregnancy smoking, pre-pregnancy BMI class, cohort year |
| Pre-pregnancy diabetes | `RF_PDIAB` Y vs N | same as hypertension |
| Pre-pregnancy BMI class | `BMI_R` 1, 3, 4, 5, 6 vs 2 (18.5–24.9) | maternal age, race/Hispanic origin, nativity, education, payment source, parity, pre-pregnancy smoking, cohort year. **Not** hypertension or diabetes, which are mediators. |

- **DAG check (23 Nov 2026):** a back-door test in `networkx` on the three DAG files confirms that each planned set is valid, and that adding gestational age makes it invalid. Minimal valid sets are smaller (for example, diabetes: age, race, payment, BMI, year). The extra variables are kept for precision. A DAG is an assumption; the supervisor should review it.
- **Never adjusted for in the main models:** gestational age, birth weight, or anything after delivery. These are mediators, and adjusting for them opens a collider path.
- **Not used:** marital status (California not released 2017+) and father's items (missing is linked to marital status).
- **Note on the layout:** the guide prints `BMI_R` code 4 as "30.0–39.9", but code 5 is 35.0–39.9, so code 4 = 30.0–34.9.

**Model:** modified Poisson GLM (log link, robust sandwich SE, `statsmodels`), fitted **per cohort** to fit in memory. The 8 cohort estimates are pooled by fixed-effect inverse-variance meta-analysis; random-effects (DerSimonian–Laird) is a sensitivity analysis. Main estimate: pooled adjusted risk ratio (RR) with 95% CI.

**Absolute effect:** g-computation risk difference per 1,000 births, standardized to the exposure's own covariate distribution. The 95% CI comes from 1,000 draws of the coefficients from their robust covariance matrix.

**Unmeasured confounding:** E-value for each pooled RR and its CI limit.

**Pre-set checks (pass/fail):**
1. Direction: the per-cohort RR is on the same side of 1.0 in at least 7 of 8 cohorts.
2. Heterogeneity: report Cochran's Q and I²; if I² > 50%, report the random-effects result as main.
3. Negative control: the adjusted RR for `death_accident`. If its CI overlaps the main RR's CI and excludes 1.0, residual confounding is likely, and the main claim is weakened.
4. Collider demonstration: refit with gestational age (weeks) added. Report and explain; this is not a result about the effect.
5. Missing data: complete-case first. Compare missingness of BMI and each covariate by outcome (descriptive). If the death rate differs by more than 20% (relative) between records with and without a value, run multiple imputation (20 imputations, chained equations) as a sensitivity analysis.

**Multiple testing:** 3 exposures × 3 outcomes = 9 main results, all reported. Holm-adjusted p-values are a sensitivity analysis.

**Expectations stated in advance:** RR > 1 for hypertension and diabetes, stronger for neonatal than postneonatal death; BMI shows higher risk with increasing obesity class (and possibly with underweight).

## 5. Benchmark and reproducibility

- **Before any model:** reproduce the guide's cohort documentation tables (births, deaths, rates). Fail if any rate differs by more than 0.01 per 1,000.
- **Notebooks:** `01_benchmark` … `05_checks`; shared code in `src/`; versions pinned in `requirements.lock`; outputs committed, row-level data never.
- **Seeds:** fixed (`20261123`) for every random step.

## Change log

| Date | Change | Reason |
|---|---|---|
| 23 Nov 2026 | Version 1.0 | — |
| 23 Nov 2026 | Benchmark (section 5): deaths are compared by the birth weight on the death record, as CDC tabulates them. | CDC imputes birth weight separately on birth and death records; with the death-record weight, deaths match exactly. Not an analysis change. |
| 23 Nov 2026 | Benchmark result recorded: 2018–2023 PASS; 2016 and 2017 FAIL the strict rule because of CDC table issues (2016 file re-release has birth weight for 2,493 births listed "Not stated"; 2017 guide repeats all-races deaths in the NH White rows). Totals exact in all years. | Data accepted; reasons in `notebooks/01_benchmark.ipynb`. |
| 23 Nov 2026 | Missing-data check (section 4, check 5) already triggered by Table 1: BMI unknown 6.4% of deaths vs 2.3% of survivors. Multiple imputation is required as a sensitivity analysis. | Descriptive Table 1, before any model. |
| 23 Nov 2026 | Part 1 implementation details: logistic regression uses normalized weights and tol 1e-6 (the default stopped before convergence); calibration is fitted with a low-memory Newton solver (same model as statsmodels, which ran out of memory at 7 M rows); permutation importance uses all test deaths + 1 in 10 test survivors (weight 10). | Technical; no change to inputs, splits, models or rules. |
| 23 Nov 2026 | **Post-hoc sensitivity (added after seeing the importance results):** Sets A and B refit without `precare` (month prenatal care began), `illb` and `ilp` (birth intervals). | All three depend on pregnancy length: care cannot start after the birth, and CDC measures intervals up to this birth, so preterm births shorten them. This is the same timing leakage that excluded `PREVIS`. The original results stay the pre-registered main results; the strict results are reported next to them. |
