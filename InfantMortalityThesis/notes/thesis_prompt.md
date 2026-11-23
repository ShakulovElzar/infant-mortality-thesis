# Thesis work prompt

Agreed with the user on 23 Nov 2026. This is the master instruction for the analysis. The detailed, dated decisions are in `../plan/analysis_plan.md`; where the two differ, the plan wins.

```text
Thesis: UniME L-31 bachelor's thesis, March 2027 session.
Data: CDC/NVSS linked birth–infant death COHORT files, birth cohorts
2016–2023, in InfantMortalityThesis/data/cdc/*.zip (fixed-width; layouts in
each year's *_linkedUG.pdf on the CDC FTP; join rules and known quirks in
InfantMortalityThesis/AGENTS.md). Population: births to U.S. residents
(RESTATUS < 4). Outcome: death before 365 days (from the cohort join).
Secondary outcomes: neonatal (<28 days) and postneonatal (28–364 days).
Do not apply RECWT. Use reporting flags (F_*): keep only records with
flag = 1 for that item.

Work in steps. Stop after each step, show the result, and wait for my review.
For each step, also give me a 5-line plain-English explanation of the method
that I can defend at the exam.

STEP 0 — Analysis plan (before any exposure–outcome result is computed)
- Write a 2-page plan covering Parts 1 and 2 below: outcomes, inputs,
  splits, models, metrics, checks and pass/fail thresholds. Commit it
  with a date.
- Draw one DAG per Part-2 exposure (dagitty syntax).

STEP 1 — Data build and benchmark
- src/build_parquet.py: read each cohort ZIP once (stream, no extraction),
  keep ALL birth-record fields plus the death fields (age at death, UCOD,
  UCODR130, manner), write one Parquet file per cohort to an ignored folder.
- Build columns.csv (name, positions, codes, missing codes) from the guides;
  verify positions against EACH year's guide and list any differences.
- Benchmark: reproduce the guide's cohort documentation tables (births,
  deaths, rates). Fail if any rate differs by more than 0.01 per 1,000.
- Table 1 (tableone) of characteristics by outcome and by cohort.

PART 1 — Prediction with all factors known before birth
- Inputs: only items known before delivery (exact lists in the plan).
  EXCLUDE everything recorded at or after delivery: gestational age,
  birth weight, Apgar, NICU, abnormal conditions, congenital anomalies,
  labor/delivery items, delivery weight and weight gain, breastfeeding,
  transfers, and all death fields.
- Marital status: 2016 has California values, 2017+ does not; code it
  with an explicit "not released" category and run once without it.
- Split by time: train 2016–2020, validate/tune 2021, test 2022–2023.
  Touch the test set once, at the end.
- Models, all on the same inputs and split: (a) baseline: cohort-year
  rate; (b) logistic regression, maternal age + race only; (c) penalized
  logistic regression, all inputs; (d) HistGradientBoostingClassifier;
  (e) optional: LightGBM. No resampling (keep probabilities calibrated).
- Metrics on the test set with 1,000-sample bootstrap 95% CIs: PR-AUC
  (main), ROC-AUC, Brier score, calibration intercept and slope,
  calibration plot. Report also by race/Hispanic origin and payment source.
- Factor ranking: grouped permutation importance on the test set (each
  original item with all its recodes = one group), confirmed by drop-group
  refits for the top 10. State clearly: importance = predictive value,
  not cause.
- Pre-set checks: (1) the best model must beat model (b) in PR-AUC with a
  CI that excludes 0; (2) calibration slope between 0.9 and 1.1;
  (3) leakage check: any single input with ROC-AUC > 0.80 alone must be
  investigated before results are reported.

PART 2 — Association for three maternal factors, one at a time
- Exposures, each in its OWN model with its OWN DAG-based confounder set:
  (1) pre-pregnancy hypertension (RF_PHYPE), (2) pre-pregnancy diabetes
  (RF_PDIAB), (3) pre-pregnancy BMI class (BMI_R; reference 18.5–24.9).
- Population: singleton births (DPLURAL = 1).
- Confounders: per DAG (see plan). Never adjust for gestational age or
  birth weight in the main model.
- Model: modified Poisson GLM (log link, robust SE; fitted on covariate-pattern counts, src/modified_poisson.py) for
  adjusted risk ratios; g-computation risk difference per 1,000 births
  with 95% CI; E-value for each main RR.
- Replication: estimate per cohort (8 cohorts), forest plot, Cochran's Q.
- Pre-set checks: (1) negative-control outcome = accident deaths without
  suffocation (UCODR130 141–145, 148–151; amended 23 Nov 2026); the claim is weakened if its RR is similar to the main
  RR; (2) direction must agree in at least 7 of 8 cohorts; (3) collider
  demonstration: refit with gestational age added, report and explain;
  (4) complete-case first, then test whether missing BMI/covariates relate
  to death; multiple imputation only if they do.
- Multiple testing: 3 exposures × 3 outcomes; report all 9 results;
  Holm-adjusted p-values as a sensitivity analysis.

NOTEBOOK DOCUMENTATION (applies to every notebook)
- Each notebook starts with a Markdown cell: title, goal of this notebook,
  which thesis question/part it serves, inputs (files), outputs (files,
  tables, figures), and how to run it.
- Before each code section, a Markdown cell says in plain English: what
  this section does, why we do it, and what result to expect.
- After each important output (table, plot, metric), a Markdown cell says
  what the result shows and whether it passes the pre-set check.
- Code comments: short, only where the code is not obvious (a CDC code
  meaning, a field position, a method choice). No comments that repeat
  the code.
- The notebook ends with a Markdown "Summary" cell: main findings, open
  issues, and the next notebook to run.
- Write all Markdown in simple English: short sentences, one idea per
  sentence, define each term (e.g. "cohort", "risk ratio") the first
  time it appears.

Tools: DuckDB or polars on Parquet, statsmodels, scikit-learn,
tableone, matplotlib; Jupyter notebooks 01_benchmark, 02_table1,
03_prediction, 04_association, 05_checks, importing shared code from src/.
Pin versions in requirements.lock. Commit notebooks WITH outputs
(tables, plots, metrics), but never commit row-level data: outputs may
show only aggregated counts, rates and model results.

Deliverables: dated plan; columns.csv with year differences; benchmark
table; Table 1; Part 1 model comparison table, calibration plots and
factor ranking; Part 2 results table (RR, RD, CIs, E-values), forest
plots; one checks table with pass/fail against the pre-set thresholds;
short limitations list (live-birth selection, no geography, recording
quality of birth-certificate items).
```
