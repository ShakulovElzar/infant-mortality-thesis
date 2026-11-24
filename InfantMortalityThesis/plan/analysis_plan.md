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
| `death_accident` | `UCODR130` in 141–145 or 148–151: accidents **except** suffocation (transport, falls, firearms, drowning, choking on objects, fire, poisoning, other); about 1,850 deaths in 2016–2023 | negative control, Part 2 only (amended 23 Nov 2026, see change log) |

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

## 4. Part 2: association of five maternal factors

**Question:** after adjustment for confounders, how much do pre-pregnancy hypertension, pre-pregnancy diabetes, pre-pregnancy BMI class, smoking before pregnancy and the interval since the last pregnancy change the risk of death before age one? (Smoking and interval added 23 Nov 2026, see change log.)

| Exposure | Coding | Adjustment set (from the DAGs in `plan/dags/`) |
|---|---|---|
| Pre-pregnancy hypertension | `RF_PHYPE` Y vs N | maternal age, race/Hispanic origin, nativity, education, payment source, parity, pre-pregnancy smoking, pre-pregnancy BMI class, cohort year |
| Pre-pregnancy diabetes | `RF_PDIAB` Y vs N | same as hypertension |
| Pre-pregnancy BMI class | `BMI_R` 1, 3, 4, 5, 6 vs 2 (18.5–24.9) | maternal age, race/Hispanic origin, nativity, education, payment source, parity, pre-pregnancy smoking, cohort year. **Not** hypertension or diabetes, which are mediators. |
| Smoking before pregnancy | `CIG_0` 1–98 vs 0 cigarettes a day in the 3 months before pregnancy; valid only if `F_CIGS_0` = 1. Secondary: dose (`CIG0_R` 1–5, 6–10, 11–20, ≥21 vs 0). | maternal age, race/Hispanic origin, nativity, education, payment source, parity, cohort year. **Not** BMI, hypertension or diabetes, which smoking can change (mediators). |
| Interval since the last pregnancy (IPI) | months = `ILP_R` − gestational age of this birth (`COMBGEST` weeks × 7 / 30.44, rounded). `ILP_R` counts months up to *this birth* (codes 000–003 = plural delivery), so the current pregnancy must be subtracted. Classes <6, 6–11, 12–17, 24–59, ≥60 vs **18–23**. Births with an earlier pregnancy only (`ILP_R` 4–300); negative or missing IPI excluded. | maternal age, race/Hispanic origin, nativity, education, payment source, parity, smoking before pregnancy, earlier fetal death/termination (`PRIORTERM` > 0), earlier child now dead (`PRIORDEAD` > 0), previous preterm birth (`RF_PPB`), cohort year. **Not** BMI, hypertension or diabetes (a short interval can change them). |

- **DAG check (23 Nov 2026):** a back-door test on the DAG files confirms that each planned set is valid, and that adding gestational age makes it invalid (first done with `networkx` for 3 DAGs; now in `notebooks/04_association.ipynb`, section 4, for all 5, PASS). The four all-birth DAGs share one model; the interval DAG adds the interval and the earlier-pregnancy items. Minimal valid sets are smaller (for example, diabetes: age, race, payment, BMI, year). The extra variables are kept for precision. A DAG is an assumption; the supervisor should review it.
- **Never adjusted for in the main models:** gestational age, birth weight, or anything after delivery. These are mediators, and adjusting for them opens a collider path.
- **Not used:** marital status (California not released 2017+) and father's items (missing is linked to marital status).
- **Note on the layout:** the guide prints `BMI_R` code 4 as "30.0–39.9", but code 5 is 35.0–39.9, so code 4 = 30.0–34.9.

**Model:** modified Poisson GLM (log link, robust sandwich SE), fitted **per cohort**. All covariates are categories, so each model is fitted on counts per covariate pattern (births *n* and deaths *d* in each combination of categories), not on single births. This gives exactly the same estimates as the single-birth model, and the robust (HC0) covariance is also exact, because each birth's squared score in a pattern is d(1−μ)² + (n−d)μ² summed over the pattern. Code: `notebooks/04_association.ipynb`, checked against `statsmodels` on synthetic data before use. The 8 cohort estimates are pooled by fixed-effect inverse-variance meta-analysis; random-effects (DerSimonian–Laird) is a sensitivity analysis. Main estimate: pooled adjusted risk ratio (RR) with 95% CI.

**Absolute effect:** g-computation risk difference per 1,000 births, standardized to the exposure's own covariate distribution. The 95% CI comes from 1,000 draws of the coefficients from their robust covariance matrix.

**Unmeasured confounding:** E-value for each pooled RR and its CI limit.

**Pre-set checks (pass/fail):**
1. Direction: the per-cohort RR is on the same side of 1.0 in at least 7 of 8 cohorts.
2. Heterogeneity: report Cochran's Q and I²; if I² > 50%, report the random-effects result as main.
3. Negative control: the adjusted RR for `death_accident`. If its CI overlaps the main RR's CI and excludes 1.0, residual confounding is likely, and the main claim is weakened.
4. Collider demonstration: refit with gestational age (weeks) added. Report and explain; this is not a result about the effect.
5. Missing data: complete-case first. Compare missingness of BMI and each covariate by outcome (descriptive). If the death rate differs by more than 20% (relative) between records with and without a value, run multiple imputation (20 imputations, chained equations) as a sensitivity analysis.
   **Triggered** (Table 1: BMI unknown for 6.4% of deaths vs 2.3% of survivors). Details, fixed 23 Nov 2026 before any Part 2 result:
   - *Imputed:* pre-pregnancy BMI class (`BMI_R`) and mother's education (`MEDUC`), the two items whose missingness is clearly linked to death. Other covariates with small missingness (payment, race, nativity, parity, smoking; each ≤ 1%) stay complete-case in both analyses.
   - *Imputation models:* multinomial logistic regression for each of the two items, by chained equations (5 cycles), per cohort. Predictors: the other imputed item, pre-pregnancy hypertension and diabetes, all other confounders, plurality, and the outcomes `death_1y` and `death_neo` (an imputation model must include the outcome). Fitted on covariate-pattern counts, like the main models.
   - *Proper imputation:* for each of the 20 imputations, the imputation model is refitted on a bootstrap resample (Poisson weights) of the observed records, so the imputed values carry the uncertainty of the imputation model.
   - *Analysis:* the same modified Poisson models on each completed data set; log RRs and their robust variances combined with Rubin's rules, then pooled over cohorts as in the main analysis.

**Multiple testing:** 5 exposures × 3 outcomes = 15 main results, all reported. For BMI and the interval (several classes), the p-value per outcome is the joint Wald test of all classes. Holm-adjusted p-values are a sensitivity analysis.

**Expectations stated in advance:** RR > 1 for hypertension and diabetes, stronger for neonatal than postneonatal death; BMI shows higher risk with increasing obesity class (and possibly with underweight). Smoking before pregnancy: RR > 1, stronger for postneonatal death (sudden unexpected infant death). Interval: U-shape, highest risk below 6 months, raised risk at ≥60 months.

**Added sensitivity analyses (23 Nov 2026):** (a) BMI among births with an earlier pregnancy, with the interval class added, because a short interval can raise pre-pregnancy BMI (weight kept after the earlier pregnancy). (b) Interval measured from the last *live* birth (`ILLB_R`) instead of the last pregnancy of any outcome.

## 5. Benchmark and reproducibility

- **Before any model:** reproduce the guide's cohort documentation tables (births, deaths, rates). Fail if any rate differs by more than 0.01 per 1,000.
- **Notebooks:** `00_data_build`, `01_benchmark` … `05_checks`; all code in the notebooks (shared layout code in `notebooks/functions.ipynb`); versions pinned in `requirements.lock`; outputs committed, row-level data never.
- **Seeds:** fixed (`20261123`) for every random step.

## 6. Planned extensions (not yet run)

- **Part 1 by age at death** (agreed 23 Nov 2026, after the Part 1 results were seen, so it is an addition to the plan, not a pre-set analysis). Refit only the best model (boosting, Set B, best 2021 settings) separately for neonatal death (`AGEDX` 0–27) and postneonatal death (`AGEDX` 28–364, among babies alive at day 28). Same split, test once, 1,000-sample paired bootstrap, grouped permutation importance. Question: do different items predict early and late deaths (expected: plurality and birth history for neonatal, social items for postneonatal)? About 1 hour of compute. Run after the Part 1 re-run is verified.

## Change log

| Date | Change | Reason |
|---|---|---|
| 23 Nov 2026 | Version 1.0 | — |
| 23 Nov 2026 | Benchmark (section 5): deaths are compared by the birth weight on the death record, as CDC tabulates them. | CDC imputes birth weight separately on birth and death records; with the death-record weight, deaths match exactly. Not an analysis change. |
| 23 Nov 2026 | Benchmark result recorded: 2018–2023 PASS; 2016 and 2017 FAIL the strict rule because of CDC table issues (2016 file re-release has birth weight for 2,493 births listed "Not stated"; 2017 guide repeats all-races deaths in the NH White rows). Totals exact in all years. | Data accepted; reasons in `notebooks/01_benchmark.ipynb`. |
| 23 Nov 2026 | Missing-data check (section 4, check 5) already triggered by Table 1: BMI unknown 6.4% of deaths vs 2.3% of survivors. Multiple imputation is required as a sensitivity analysis. | Descriptive Table 1, before any model. |
| 23 Nov 2026 | Part 1 implementation details: logistic regression uses normalized weights and tol 1e-6 (the default stopped before convergence); calibration is fitted with a low-memory Newton solver (same model as statsmodels, which ran out of memory at 7 M rows); permutation importance uses all test deaths + 1 in 10 test survivors (weight 10). | Technical; no change to inputs, splits, models or rules. |
| 23 Nov 2026 | **Post-hoc sensitivity (added after seeing the importance results):** Sets A and B refit without `precare` (month prenatal care began), `illb` and `ilp` (birth intervals). | All three depend on pregnancy length: care cannot start after the birth, and CDC measures intervals up to this birth, so preterm births shorten them. This is the same timing leakage that excluded `PREVIS`. The original results stay the pre-registered main results; the strict results are reported next to them. |
| 23 Nov 2026 | **Part 2 fixes, made before any Part 2 result was computed.** (1) Negative-control outcome: `UCODR130` 141–145 and 148–151 (accidents without suffocation), instead of 139. (2) Models fitted on covariate-pattern counts with exact robust covariance (`notebooks/04_association.ipynb`, checked by `src/check_modified_poisson.py` on synthetic data). (3) Multiple-imputation details written out (section 4, check 5). | (1) Code 139 is a subtotal and is never recorded (0 deaths); 75% of the coded accidents are suffocation in bed (W75), which is linked to preterm birth, so hypertension could affect it through the infant and it would not be a clean negative control. (2) Lower memory, same results. (3) MI was triggered by Table 1; the plan had no details. |
| 23 Nov 2026 | **Code moved from `src/*.py` into the notebooks** (`00_data_build` new; Part 1 code in `03_prediction`; modified Poisson in `04_association`). All notebooks re-run from scratch. | User request: all code in notebooks. No method changed; results compared with the earlier run. |
| 23 Nov 2026 | **Two Part 2 exposures added:** smoking before pregnancy and interval since the last pregnancy, each with its own DAG (`plan/dags/dag_smoking.dagitty`, `dag_interval.dagitty`) and adjustment set. Shared DAG model gains Age, Payment, Parity → Smoke0 and Smoke0 → BMI, DM; the three original sets stay valid (re-checked). Sensitivity analyses (a) and (b) added. 15 main results. | User asked for a quality review of the exposure choice before Part 2. Rules fixed first: exposure exists before the pregnancy, modifiable, recorded well, enough exposed deaths, open question in the literature. Smoking (7.0% of singletons; only one-year US evidence for pre-pregnancy smoking) and interval (U-shape known from 2011–2015 period files, not cohort files) met them; infertility treatment, gestational conditions, infections and social items did not. Chosen after Part 1 results were seen; Part 1 gives prediction, not adjusted effects, and **no Part 2 result has been computed**. |
| 24 Nov 2026 | **Part 2 coding, fixed before the first Part 2 fit.** Population: resident singletons. Categories (reference in bold): age <20, 20–24, **25–29**, 30–34, 35–39, ≥40 (`MAGER9`); race/Hispanic origin `MRACEHISP` 1–7, **NH White**; nativity **U.S.-born** / foreign-born; education ≤11th grade, **high school**, some college/associate, bachelor's, graduate (`MEDUC`); payment Medicaid, **private**, self-pay, other; live birth order **1**, 2, 3, ≥4 (`LBO_REC`); smoking before pregnancy **0** / >0; BMI class **2**; gestational age (collider check only) <28, 28–31, 32–33, 34–36, 37–38, **39–40**, ≥41 weeks. Unknown codes and reporting flag ≠ 1 → missing → complete case. Year: one model per cohort, so no year term. Negative control (`death_accident`, about 1,850 deaths in all, about 230 per cohort): **one model on all 8 cohorts with cohort as a covariate**, and race classes NH AIAN, NH NHOPI and NH multiple merged, because per-cohort models with so few deaths do not converge or give no information. Pooled class estimates: univariate inverse-variance pooling; joint p-value per exposure–outcome: multivariate fixed-effect pooling of all class log RRs, Wald test. Pooled risk difference: inverse-variance pooling of per-cohort g-computation RDs, SE = SD of the 1,000 coefficient draws. Missing-data check (check 5) also run for smoking and the interval. | Implementation details the plan left open. Written before any Part 2 model was fitted. |
| 24 Nov 2026 | **Part 2 complete-case results computed** (`04_association`). Two code fixes during the run, neither a method change: the Newton fit now halves a step that lowers the likelihood (the gestational-age model overflowed), and `design()` uses the lowest present class when the reference class is absent (parity 1 cannot occur after a live birth). The synthetic check still PASSES. Results: all 15 tests significant; check 1 PASS for all infant-death classes; check 3 (negative control) PASS for hypertension, diabetes, BMI ≥35, WEAKENED for smoking, interval <12 months and BMI 30–34.9; check 5 triggered for every item, interval missing 16.8% with 56% higher death rate. | Record of the first Part 2 run. |
| 24 Nov 2026 | **Multiple imputation extended to the interval, and its details fixed before the imputation is run.** Imputed: BMI class, education, and the interval class. Interval population for imputation: births with a known interval (`ILP_R` 4–300) plus births with an unknown interval (999) who certainly had an earlier pregnancy (birth order ≥2 or an earlier fetal loss). Imputation models: multinomial logistic regression, main effects, fitted by L-BFGS on pattern counts, per cohort. Predictors: age, race, nativity, payment, birth order, smoking, hypertension, diabetes, the outcome (survived / neonatal death / postneonatal death), and the other imputed items (the interval model also uses earlier fetal loss, earlier child death, previous preterm birth; the interval is not a predictor in the BMI and education models). A missing non-imputed predictor is its own category. Chained equations, 5 cycles, start values drawn from the observed distribution. Every model fit uses a new Poisson bootstrap of the observed records (as MICE draws new parameters at every step). 20 imputations × 8 cohorts. Analysis: the five main exposures × three outcomes on each completed data set (risk-difference draws: 300 per imputation); Rubin's rules per cohort, then pooled over cohorts as in the main analysis. No joint Wald test under imputation. | User decision 24 Nov 2026: the interval is missing for 16.8% of births with an earlier pregnancy, with a 56% higher death rate (check 5, section 8 of `04_association`). |
| 24 Nov 2026 | **Multiple imputation done** (8 cohorts × 20 imputations, about 70 minutes). No pooled RR changes by more than 1.2%; fraction of missing information about 0 (hypertension, diabetes, smoking), 5% (BMI), 20–27% (interval). Check 5: PASS. | Record of the imputation run. |
