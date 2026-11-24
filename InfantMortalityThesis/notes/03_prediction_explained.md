# Study guide: `notebooks/03_prediction.ipynb`, explained step by step

Written 24 Nov 2026 for exam preparation. Part A is the theory: every term the notebook uses. Part B goes through the notebook cell by cell. Part C lists likely exam questions with short answers. Numbers are from the run of 24 Nov 2026 (test births 2022–2023).

---

## Part A — Theory

### A1. The task: binary classification with a probability
Every birth has an outcome *y*: 1 = the baby died before age one, 0 = the baby survived. A *classifier* gives each birth a number *p* between 0 and 1: the predicted probability of death. We do not need a yes/no answer. We need good probabilities and a good *ranking* (risky births above safe births).

- **Base rate (prevalence):** the share of births with *y* = 1. Here 0.55% (5.5 per 1,000).
- **Class imbalance:** one class is much rarer than the other. With 0.55% deaths, a model that says "every baby survives" is right 99.45% of the time. That is why **accuracy** (share of correct yes/no answers) is useless here, and we use the metrics below.

### A2. Threshold, confusion matrix, precision and recall
To turn probabilities into yes/no, choose a *threshold* t: flag a birth if p ≥ t. Then every birth falls into one cell:

| | died (y = 1) | survived (y = 0) |
|---|---|---|
| flagged (p ≥ t) | true positive (TP) | false positive (FP) |
| not flagged | false negative (FN) | true negative (TN) |

- **Precision** = TP / (TP + FP): of the flagged births, the share that died. Example: in our top 1%, precision = 6.1% (60.8 per 1,000).
- **Recall** (sensitivity, true positive rate, TPR) = TP / (TP + FN): of all deaths, the share that was flagged. Example: the top 10% has recall 37.5%.
- **False positive rate (FPR)** = FP / (FP + TN): of all survivors, the share that was flagged.

A low threshold flags many births: recall goes up, precision goes down. A high threshold does the opposite. Every threshold gives one (recall, precision) pair and one (FPR, TPR) pair.

### A3. ROC curve and ROC-AUC
- **ROC curve:** plot TPR (y-axis) against FPR (x-axis) for every threshold. A model that guesses gives the diagonal line.
- **ROC-AUC:** the area under that curve. **Meaning:** the probability that a randomly chosen baby who died gets a higher predicted risk than a randomly chosen baby who survived. 0.5 = guessing, 1 = perfect.
- **Ours: 0.739** (best model). So in 74% of (death, survivor) pairs the model ranks the death higher.
- **Weakness with rare outcomes:** ROC-AUC uses the FPR, and with 7 million survivors even 50,000 false alarms are a tiny FPR. So ROC-AUC can look good while most flagged births are false alarms. That is why it is not our main metric.

### A4. Precision–recall curve and PR-AUC (average precision)
- **PR curve:** plot precision (y-axis) against recall (x-axis) for every threshold.
- **PR-AUC**, computed as **average precision (AP)**: the precision at each threshold, weighted by how much recall increases at that threshold, summed over all thresholds. Formula: AP = Σ (recallₖ − recallₖ₋₁) × precisionₖ.
- **Baseline:** a guessing model has precision = base rate everywhere, so AP = 0.0055.
- **Ours: 0.038**, about 7 times the base rate.
- **Why it is the main metric:** it looks only at the deaths and at the flagged births, so it is sensitive to false alarms. With rare outcomes it shows differences between models that ROC-AUC hides.
- **What it is not:** it is not a success rate and not the death rate of one group. It is an average over all cut-offs.

### A5. Brier score
The mean of (p − y)² over all births. 0 = perfect. It measures accuracy *and* calibration of the probabilities together. With a rare outcome it is dominated by the base rate: a model that predicts 0.0055 for everyone already gets about 0.0055. That is why our models differ only in the 4th decimal (0.0054–0.0055), and the Brier score is a weak way to compare them.

### A6. Calibration
A model is *calibrated* when its probabilities are true: among births with predicted risk 2%, about 2% die.
- **Calibration intercept (calibration-in-the-large):** fit `logit P(y=1) = c + logit(p)`, with logit(p) as a fixed *offset*. c = 0 means the average predicted risk equals the average observed risk. c > 0 means the model predicts too low overall.
- **Calibration slope:** fit `logit P(y=1) = a + b × logit(p)`. b = 1 is perfect. **b < 1** means the predictions are too extreme (too high for high-risk births, too low for low-risk ones), which is typical of overfitting. b > 1 means too timid.
- **Observed/expected (O/E):** observed deaths divided by the sum of predicted probabilities. 1 = perfect; 1.03 means 3% more deaths than predicted.
- **Calibration plot (deciles):** sort births by predicted risk, cut into 10 equal groups, and plot the mean predicted risk against the observed death rate in each group. Points on the diagonal = good.
- **Logit:** logit(p) = log(p / (1 − p)), the log of the odds. It maps 0–1 onto the whole number line.

### A7. Logistic regression
The model: logit(p) = β₀ + β₁x₁ + β₂x₂ + …  So p = 1 / (1 + e^−(β₀ + β·x)).
- Each β is a change in log-odds for a one-unit change in x. e^β is an *odds ratio*.
- **Maximum likelihood:** choose the β that make the observed outcomes most probable. The log-likelihood is Σ [y log p + (1 − y) log(1 − p)]. There is no formula for the solution, so it is found by iteration (Newton–Raphson, or the lbfgs solver in scikit-learn).
- **Penalized (L2, ridge) logistic regression:** maximize log-likelihood − (1 / 2C) × Σβ². The penalty shrinks coefficients toward 0 and protects against overfitting. **C** is the inverse strength: small C = strong penalty. We tried C = 0.01, 0.1, 1.
- **Limits:** the model is additive on the log-odds scale. It cannot find interactions (for example "twins *and* previous child death") unless you add them by hand.

### A8. Preparing inputs for logistic regression
- **One-hot encoding:** a category with k values becomes k columns of 0/1 (for example race 1–7 → 7 columns). The model then gets one coefficient per category.
- **Splines:** a smooth curve for a number, built from pieces of cubic polynomials joined at *knots*. Used for mother's age and BMI, because risk is U-shaped (high at very young and old ages, and at very low and very high BMI). A straight line cannot show a U.
- **Imputation for the model:** a missing number is replaced by the median; a missing category gets its own code (−1).
- **Missing indicator:** an extra 0/1 column that says "this value was missing". Missingness itself carries information (incomplete certificates go with higher risk).
- **Standardization:** subtract the mean, divide by the standard deviation. It puts numbers on one scale, so the penalty treats them equally and the solver converges.
- **Pipeline:** scikit-learn's way to chain these steps with the model, so the same steps are applied to train, tune and test data.

### A9. Decision trees and gradient boosting
- **Decision tree:** a series of yes/no questions ("plurality ≥ 2?", "prior births now dead ≥ 1?"). Each end point (*leaf*) gives a predicted risk. Trees find interactions naturally.
- **Gradient boosting:** builds many small trees one after another. Each new tree corrects the errors of the sum of the trees before it, by fitting the *gradient* of the loss (for probabilities: log-loss). The final prediction is the sum of all trees, put through the logistic function.
- **HistGradientBoostingClassifier** (scikit-learn): first groups each input into at most 255 bins (*histogram*), which makes training on millions of rows fast. It handles missing values natively (they go to whichever side of a split works best).
- **Settings we tuned:**
  - `learning_rate`: how much each tree contributes (0.1 or 0.05). Smaller = slower but often better.
  - `max_leaf_nodes`: size of each tree (31, 63, 127 leaves). Bigger = more interactions.
  - `min_samples_leaf`: the smallest leaf (500–2,000 births). Bigger = smoother, less overfitting.
- **Fixed settings:** `l2_regularization=1.0` (a penalty on leaf values), `categorical_features` (race, nativity, marital, payment, intervals, father's race are treated as unordered categories), and **early stopping**: 10% of the training rows are held back; training stops when the loss on them has not improved for 30 trees (`max_iter=2000` is only an upper limit).

### A10. Training on a sample, with weights
Training on 19 million births is slow and needs a lot of memory. So the training set keeps **all deaths and 1 in 10 survivors**, and each kept survivor gets **weight 10**. The weighted data then has the same death rate as the full data. This is called *inverse-probability weighting*. Unlike *oversampling* (copying deaths) or *undersampling without weights*, it keeps the predicted probabilities calibrated. The plan forbids resampling that changes the death rate for this reason.

### A11. Time split and tuning
- **Train** 2016–2020 → fit the models.
- **Tune (validation)** 2021 → choose settings (C, tree size). Choosing on the test set would make the test result look better than it is.
- **Test** 2022–2023 → touched once, at the end.
- A split *by time* copies real use: a model built on past births is used on future births. A random split would hide changes over time (for example the rising maternal risk factors).

### A12. Bootstrap confidence intervals
- **Bootstrap:** create many new data sets by resampling the test births with replacement, compute the metric on each, and take the 2.5th and 97.5th percentiles as the 95% CI.
- **Poisson bootstrap:** with 7 million births, resampling is slow. Instead each birth gets a random weight from a Poisson(1) distribution (0, 1, 2, …), which is how many times it would appear in a resample. For large n this is equivalent.
- **Paired comparison:** the same weights are used for every model in each resample, so the CI of the *difference* between two models is much narrower than comparing two separate CIs.

### A13. Importance: which inputs carry predictive value
- **Permutation importance:** shuffle one input across births (so it carries no information), predict again, and measure the drop in PR-AUC. Repeat 20 times. A big drop = the model relies on that input.
- **Weakness:** shuffling creates impossible combinations, and when two inputs share information, shuffling one exaggerates its role. So we confirm the top 10 by:
- **Drop-group refit:** retrain the model *without* the input and measure the PR-AUC drop. If other inputs can replace it, the drop is small.
- **Importance is not cause.** An input can predict because it marks something else (payment source marks income).

### A14. Leakage
*Leakage* = an input that contains information about the outcome that would not be available at prediction time. Example: total number of prenatal visits, which is higher when the pregnancy lasts longer. Leakage makes a model look better on paper than in real use.

---

## Part B — The notebook, cell by cell

The notebook has Markdown cells (explanations) and code cells. Below, each code cell is explained in order. "Line" means a line or a small group of lines that belong together.

### Cell: parameters (`REBUILD = False`)
- `REBUILD = False`: the default. Each heavy section only loads its saved results.
- The cell has the tag `parameters`. When the notebook is run with **papermill** (`-p REBUILD True`), papermill inserts a new cell right after it, `# Parameters / REBUILD = True`. That is the second small cell you see: it overrides the default. In the committed notebook it says `True`, because the full run recomputed everything.

### Cell: setup
- `import gc, json, time`: memory clean-up, reading settings stored as text, and the clock for log lines.
- `from dataclasses import dataclass`: a short way to define the `Feature` record.
- `import duckdb`: SQL directly on Parquet files. `joblib`: saves and loads fitted models. `matplotlib`: plots. `numpy`: arrays. `polars`: fast data tables.
- The `sklearn` imports: the model and preparation tools from Part A (A7–A9).
- `ROOT = Path.cwd().parent`: the notebook runs in `notebooks/`, so the project folder is one level up.
- `PARQUET`, `WORK`, `REPORTS = R`, `FIG`: where data, work files (ignored by Git), result tables and figures live.
- `SEED = 20261123`: the fixed random seed (the plan date). Every random step uses it, so the results are reproducible.
- `SURVIVOR_SAMPLE = 10`: keep 1 in 10 survivors (A10). `N_BOOT = 1000`: bootstrap resamples. `N_PERM = 20`: permutations per input.
- `pl.Config...`: how polars prints tables.
- `NAMES`: readable model names for tables.
- `def log(*a)`: prints the time and a message; `flush=True` makes it appear at once in the terminal.
- `def run_stage(stage, outputs)`: runs a heavy section only if `REBUILD` is set or one of its output files is missing; then `gc.collect()` frees memory.

### Cell: inputs (`Feature`, `num`, `yn`, `FEATURES`)
- `@dataclass(frozen=True) class Feature`: one record per input: short `name`, the DuckDB `sql` expression that builds it, its `kind` ("num" or "cat"), its set ("A" or "B"), and a `label` for tables.
- `def num(col, missing, flag, cast)`: builds SQL: *if* the reporting flag is not 1, or the value is null, or the value is an "unknown" code (for example "99") → NULL; *else* the value as a number. Reporting flag ≠ 1 means the state did not collect the item that year.
- `def yn(col, flag)`: same for Y/N items: Y → 1, N → 0, U or flag ≠ 1 → NULL.
- `FEATURES = [...]`: the 35 inputs. **Set A** (24, known in early pregnancy): mother's age, race/Hispanic origin, nativity, education, marital status, payment source, prior births now living, prior births now dead, prior terminations, birth order, the two intervals, cigarettes before pregnancy, BMI, height, pre-pregnancy diabetes and hypertension, previous preterm birth, infertility treatment, previous cesareans, father's age, race, education, and the cohort year. **Set B** adds 11 items known before delivery: 1st-trimester cigarettes, month prenatal care began, WIC, gestational diabetes and hypertension, plurality, and 5 infections.
- `SET_A`, `SET_B`: the name lists. `KIND`, `LABEL`: look-up tables.
- `TREE_CATEGORICAL`: inputs the tree model must treat as unordered categories (race 3 is not "more" than race 2). Education stays numeric there, because its codes are ordered.
- `SPLINE = {"mage", "bmi"}`: inputs that get splines in logistic regression.

### Cell: metrics (`SortedScores`, `brier`, `calibration`, `_logit_newton`)
- `class SortedScores`: computes AP and ROC-AUC fast, many times (1,000 bootstrap resamples × 7 million births).
  - `__init__`: sorts births by predicted risk, highest first (`argsort(-p)`), once. `ends` marks the last birth of each group of *tied* scores, because births with the same score must enter the curve together.
  - `metrics(w)`: with weights *w* (all 1, or bootstrap weights): cumulative weighted deaths (`tp`) and survivors (`fp`) down the sorted list = TP and FP at every threshold. Then recall = tp / P, precision = tp / (tp + fp), AP = Σ Δrecall × precision (A4), and ROC-AUC by the trapezoid rule over (FPR, TPR) (A3).
  - The `np.divide(..., where=...)` guard: in a resample, the top group can get weight 0, which would give 0/0. Its recall does not change there, so it adds nothing; precision is set to 0.
- `def brier(y, p, w)`: the weighted mean of (p − y)² (A5).
- `def calibration(y, p)`: clips p away from exactly 0 and 1 (so the logit is finite), computes logit(p), fits the slope model and the intercept model (A6) with `_logit_newton`, and returns both with 95% CIs (estimate ± 1.96 × SE) and O/E.
- `def _logit_newton(y, lp, offset)`: maximum-likelihood logistic regression with 1–2 parameters by **Newton–Raphson**: start at slope 1, intercept 0; each step computes the gradient `g` (sum of residuals y − μ) and the Hessian `H` (sum of μ(1 − μ)), and moves by H⁻¹g; stop when the step is below 1e-10. The covariance of the estimates is H⁻¹. It is the same model and the same answer as statsmodels `GLM(Binomial)`, but it keeps only sums in memory (statsmodels ran out of memory at 7 million rows).

### Cell: models
- `SETS`: three input sets: A, B, and B without marital status (marital status is missing for California from 2017, so we check that it does not matter).
- `LOGIT_C`, `HGB_GRID`: the settings tried on 2021 (A7, A9).
- `def logistic_pipeline(feats, C)`: the logistic-regression pipeline (A8). `ColumnTransformer` applies different steps to different columns: splines (with median imputation) and missing indicators for age and BMI; median imputation + missing indicator + standardization for other numbers; constant imputation (−1) + one-hot for categories. `sparse_threshold=1.0` keeps the result sparse (mostly zeros), which saves memory. Then `LogisticRegression(C=C, max_iter=5000, tol=1e-6)`: L2 penalty, lbfgs solver, a strict stopping rule.
- `def baseline_b_pipeline()`: model (b): only mother's age group and race, one-hot encoded.
- `def hgb(feats, params)`: the boosting model with the fixed settings of A9.
- `def fit(model, X, y, w)`: for a pipeline, the weights go to the logistic step (`lr__sample_weight`) and are **normalized to mean 1**: with raw weights (1 and 10) the solver stopped after 27 iterations, before it converged. For boosting, the weights go in directly.
- `def predict(model, X)`: predicts in chunks of 1 million rows, to limit memory; `[:, 1]` takes the probability of class 1 (death).
- `def load(name)`: reads a split, returns the table, the input matrix X (float32 saves half the memory), the outcome y and the weights w.

### Cell: data stage (`stage_data`)
- `cols = ...`: joins all 35 SQL expressions into one SELECT list.
- `base`: one SQL query over all 8 cohort files: the 35 inputs, the age group, `death`, `cohort`, and `sampled`. `hash(cohort, file_row_number) % 10 = 0` picks a fixed, pseudo-random 1 in 10 births: the same births every run. `WHERE RESTATUS < 4`: U.S. residents only.
- `parts`: **train** = 2016–2020, all deaths plus sampled survivors, weight 1 for deaths and 10 for survivors; **tune** = all 2021 births, weight 1; **test** = all 2022–2023 births, weight 1.
- `COPY (...) TO ... parquet`: DuckDB writes each split straight to a file, without loading it into Python.
- The log prints rows and deaths. **Result:** train 1,990,809 rows (106,391 deaths; weighted total 18.95 million births), tune 3,664,292 (19,965 deaths), test 7,263,775 (40,011 deaths).

### Cell: split table (display)
Counts rows and deaths in the three files without loading them (`scan_parquet` + `select(pl.len())`).

### Cell: fit stage (`stage_fit`)
- First it deletes the cached test predictions and bootstrap: new models make them out of date.
- `rate = ...`: model (a), the weighted training death rate. It predicts the same number for every birth. Its PR-AUC equals the base rate.
- Model (b) is fitted on age group + race and scored on 2021.
- The loop: for each set, logistic regression with each C (not for the no-marital set) and boosting with each grid setting. Each is fitted on train, scored on 2021 by PR-AUC, logged with its time, and the best per (model, set) is saved with `joblib`.
- `n_iter`: how many trees early stopping kept.
- **Result** (2021 PR-AUC): logistic A 0.0172–0.0180, B 0.0227–0.0237 (the penalty hardly matters); boosting A 0.0279–0.0287, B 0.0345–0.0370. The best boosting setting for both sets is learning rate 0.05, 127 leaves, 2,000 births per leaf (240–271 trees). Without marital status: 0.0370 vs 0.0370.

### Cell: tuning table (display)
Shows `part1_tuning.csv` sorted by set and PR-AUC.

### Cell: evaluate stage (`stage_evaluate`)
- `MODELS`: the 6 saved models to test.
- `test_predictions()`: predicts every test birth with every model, keeps death, cohort, race and payment, and caches the result (`test_preds.parquet`).
- `best_model_key()`: the best **Set B** model by **2021** PR-AUC. It is chosen before looking at the test.
- `sorted_`, `point`: AP, ROC-AUC and Brier for every model on the full test set.
- Bootstrap: 1,000 rounds of Poisson weights (A12); in each round, every model is scored with the **same** weights. Cached in `bootstrap.npz`.
- `rows`: per model, the point estimates, the 2.5/97.5 percentiles, and calibration (not for model a, whose prediction is a constant). Saved to `part1_model_comparison.csv`.
- `diffs`: paired PR-AUC differences between the best model and each other model, with CIs → `part1_pr_auc_differences.csv` (used by check 1).
- `yrs`: the same metrics for 2022 and 2023 separately.
- `dec`: the calibration deciles for the best Set B and Set A models (`np.quantile` gives the decile cut points; `searchsorted` puts each birth in its decile).
- `sub`: AP, ROC-AUC and O/E for the best model in each race and payment group with at least 20 deaths.

### Cell: comparison table (display), and checks 1 and 2
- Shows the main table. **Result:** see the table in Part C.
- **Check 1** reads the paired difference best − model (b): PASS if its lower 95% limit is above 0. Result: PASS.
- **Check 2** reads the slope of the best model: PASS if 0.9 ≤ slope ≤ 1.1. Result: 0.942 (0.934–0.951), PASS. Then the calibration plot: both axes on a log scale (`set_xscale("log")`), because risks range from about 1 to 22 per 1,000. **Reading:** the top decile is slightly over-predicted (21.8 predicted vs 20.7 observed per 1,000), the middle deciles slightly under-predicted (decile 6: 3.5 vs 4.0); overall O/E = 1.03.

### Cell: each test year (display)
2022 vs 2023. **Result:** boosting is stable (PR-AUC 0.0376 → 0.0386, slope 0.938 → 0.946). Logistic regression drifts more (O/E 1.08 → 1.12).

### Cell: subgroups (display)
- `RACE`, `PAY`: code → name maps. `replace_strict(..., default="Unknown")` labels the null code.
- **Result:** ROC-AUC 0.65 (NH NHOPI) to 0.73 (NH White). O/E close to 1 for large groups; **NH AIAN 1.15 and NH NHOPI 1.09** (the model under-predicts their risk). Births with unknown race or payment have a very high PR-AUC (0.09–0.11): an incomplete certificate is itself a risk marker.

### Cell: importance stage (`stage_importance`)
- Loads the best Set B model and the test set.
- Permutation importance uses all test deaths + the 1-in-10 sampled survivors (weight 10), for speed. `base_ap`: AP before shuffling. For each input: 20 shuffles (`rng.permutation`), AP drop each time; mean and SD saved.
- Drop-group refit for the top 10: the same model type and settings without that input, fitted on train and scored on the **full** test set.
- Leakage check: each input alone. Numbers with more than 50 values are cut into 50 quantile bins; each bin (or category, or "missing" = −999) gets its **training** death rate; that rate is the score on the test births; ROC-AUC of that score. Flag if > 0.80.

### Cell: importance plot and table (display)
- Bar chart of the top 20 mean drops, with SD error bars; the table joins the refit drop.
- **Result:**

| Input | Permutation drop | Refit drop |
|---|---|---|
| Plurality | 0.0193 | 0.0032 |
| Prior births now dead | 0.0100 | 0.0006 |
| Interval since last live birth | 0.0085 | 0.0010 |
| Month prenatal care began | 0.0066 | 0.0036 |
| Interval since last pregnancy | 0.0060 | 0.0017 |

- **Why the refit drops are smaller:** other inputs carry the same information. One example: the interval codes include "plural delivery" (code 00), so when plurality is removed, the interval partly replaces it.
- Pre-pregnancy hypertension and diabetes rank low (drop ≈ 0.0001): they are rare (1–3% of mothers), so they help little to *rank all births*. Part 2 measures how much they raise the risk for the mothers who have them. Cohort year has zero importance: trees cannot extrapolate to new years.

### Cell: check 3, leakage (display)
**Result:** PASS; the highest single input is father's education (ROC-AUC 0.63). But the check missed the **timing leakage** found by the importance analysis: `precare`, `illb` and `ilp` depend on how long the pregnancy lasted (care cannot start after the birth; CDC measures the intervals up to this birth, so a preterm birth shortens them).

### Cell: strict stage (`stage_strict`) and its table
- `TIMING_ITEMS`: the three leaky inputs.
- For Sets A and B: the best boosting settings from 2021, refit without them, predict the test set; paired bootstrap of the difference.
- **Result:** Set B 0.0380 → **0.0300**, Set A 0.0294 → **0.0191**; still calibrated (slope 0.937) and still about 3.4 times model (b). **For the thesis, the strict numbers are the honest estimate of what is known before delivery.** This analysis was added after seeing the importance results, and the change log says so.

---

## Part C — Results in one table, and exam questions

| Model | PR-AUC (95% CI) | ROC-AUC | Calibration slope |
|---|---|---|---|
| (a) baseline rate | 0.0055 | 0.500 | — |
| (b) age + race | 0.0087 (0.0086–0.0089) | 0.611 | — |
| (c) logistic, Set A / B | 0.0181 / 0.0239 | 0.700 / 0.717 | — |
| (d) boosting, Set A / B | 0.0294 / **0.0380 (0.0364–0.0396)** | 0.711 / **0.739** | B: 0.942 |
| (d) boosting, Set B strict | **0.0300 (0.0288–0.0314)** | 0.722 | 0.937 |

**Q: Why not accuracy?** With 0.55% deaths, "everyone survives" is 99.45% accurate and useless. We need ranking and probabilities.

**Q: What does PR-AUC 0.038 mean?** Average precision over all thresholds; 7 times the guessing value 0.0055. In practice: the top 1% of births by predicted risk has 60.8 deaths per 1,000 (11 times the average); the top 10% holds 37.5% of all deaths.

**Q: What does ROC-AUC 0.739 mean?** In 74% of pairs of one death and one survivor, the model gives the death the higher risk.

**Q: Why boosting over logistic regression?** Trees find interactions (plurality with birth history) without being told. Logistic regression is additive.

**Q: Why sample survivors, and why are the probabilities still right?** To save time and memory; each kept survivor has weight 10, so the weighted death rate equals the true one (calibration slope 0.94, O/E 1.03 prove it).

**Q: Why split by time?** It copies real use (train on the past, predict the future), and it shows drift over time.

**Q: How do you know the model is not just lucky?** 95% bootstrap CIs; the paired difference with model (b) excludes 0 (check 1); the order of models on 2021 and on 2022–2023 is the same.

**Q: Which items matter most, and does that mean they cause death?** Plurality and birth history. No: importance is predictive value, not cause. Part 2 handles cause.

**Q: What went wrong, and what did you do?** The single-item leakage check passed but missed timing leakage spread over three items. We reported strict models without them (PR-AUC 0.030) next to the pre-registered ones, and recorded it as post-hoc in the change log.

**Q: Is the model fair?** It ranks less well for small groups (NHOPI ROC-AUC 0.65) and under-predicts risk for NH AIAN births by 15%. This must be reported as a limitation.
