# Results overview and project audit

24 Nov 2026. Source of every number: `reports/*.csv` and the notebooks `00`–`05`. Population: U.S.-resident births 2016–2023 (29.9 million births, 166,367 infant deaths, 5.35–5.80 deaths per 1,000).

---

## Part I — What we found, and why it matters

### 1. The data are correct (Step 1)
- We rebuilt CDC's linked birth–infant death files from raw fixed-width text (80.9 GB) into one Parquet file per year. Every infant death joined to its birth (0 unmatched).
- Our counts equal CDC's published counts. CDC's detailed Table 2 is reproduced exactly for 2018–2023. In 2016 and 2017 the differences come from CDC's own tables (a re-released 2016 file, a copy error in the 2017 guide).
- **Real-life value:** anyone can reuse this pipeline to study U.S. infant deaths from the raw public files, with a documented check against CDC.

### 2. Who dies before age one (Table 1)
- Deaths are over-represented among twins (12.2% of deaths vs 3.2% of survivors), births to NH Black mothers (27.5% vs 14.2%), Medicaid births (54.1% vs 41.6%), and mothers with pre-pregnancy hypertension (4.5% vs 2.4%) or diabetes (2.2% vs 1.0%).
- The maternal risk factors **rise every year**: pre-pregnancy hypertension almost doubled from 2016 to 2023 (1.7% → 3.2%), and obesity increased.
- **Real-life value:** the population at risk is growing, so the same risk ratios mean more deaths each year.

### 3. Part 1: can we see infant death coming, before the baby is born?
| Model (test births 2022–2023, never seen in training) | PR-AUC | ROC-AUC |
|---|---|---|
| Guessing | 0.0055 | 0.50 |
| Mother's age + race only | 0.0087 | 0.61 |
| Gradient boosting, all pre-delivery items | **0.038** | **0.74** |
| Same, without the 3 items that leak pregnancy length (strict) | **0.030** | 0.72 |

- **In plain terms:** the 10% of births the model ranks highest contain 37.5% of all infant deaths. In the top 1%, about 1 baby in 16 dies, against 1 in 180 overall.
- The probabilities are reliable (calibration slope 0.94; 3% more deaths observed than predicted).
- **What drives the prediction:** twins, the mother's earlier births (an earlier child who died, birth intervals), and the start of prenatal care. Pre-pregnancy hypertension and diabetes matter little for *ranking all births*, because they are rare.
- **Early vs late deaths:** deaths in the first 4 weeks are predicted much better (PR-AUC 0.043, 12 × guessing) than deaths from 1 to 12 months (0.0067, 3.4 ×). Late deaths depend more on social and demographic items.
- **Fairness:** the model under-predicts risk for American Indian/Alaska Native births by 15%.
- **Real-life value:** a model like this could help programs that can visit only some families (for example nurse home-visiting) choose whom to reach first. Its limits are just as important: about half of infant deaths (47%) happen in the 80% of births it rates as lower risk, because the main causes (preterm birth, sudden infant death) are decided after delivery. It is a tool for prioritizing, not for diagnosis.

### 4. Part 2: how much do five maternal factors change the risk?
Adjusted for confounders chosen from a DAG, singleton births, pooled over 8 cohorts:

| Factor (vs reference) | Risk ratio (95% CI) | Extra deaths per 1,000 exposed births | Extra deaths per year in the U.S. *if causal* | Negative control |
|---|---|---|---|---|
| Pre-pregnancy diabetes | **1.84** (1.74–1.95) | 4.7 | about 160 | pass |
| Smoking before pregnancy | **1.68** (1.62–1.74) | 3.6 | about 890 (upper bound) | **weakened** |
| BMI ≥ 40 vs 18.5–24.9 | **1.53** (1.50–1.56) | 2.6 | about 490 | pass |
| Pre-pregnancy hypertension | **1.50** (1.45–1.54) | 2.9 | about 230 | pass |
| BMI 35–39.9 | 1.36 (1.31–1.40) | 1.6 | about 430 | pass |
| BMI 30–34.9 | 1.22 (1.20–1.24) | 1.0 | about 520 | weakened |
| Interval < 6 months vs 18–23 | **1.22** (1.18–1.26) | 1.1 | about 260 (upper bound) | **weakened** |

- **BMI** shows a dose–response; the interval shows a U-shape (also a small excess at ≥ 60 months).
- **Smoking** is linked twice as strongly to late deaths (RR 2.02) as to early deaths (1.41), which fits sudden unexpected infant death.
- **Robust:** all 8 cohorts agree in direction; multiple imputation of missing BMI, education and interval changes no RR by more than 1.2%.
- **Negative control:** babies of smokers also die 1.8 times as often in accidents, which smoking cannot cause. So part of the smoking and short-interval associations comes from unmeasured social differences. The diabetes, hypertension and severe-obesity results pass this test (though with few accident deaths).
- **Collider demonstration:** if you adjust for gestational age, hypertension falsely looks protective (1.50 → 0.90). This is why studies that "control for preterm birth" can mislead.
- **Real-life value:** the strongest, cleanest signals (diabetes, hypertension, severe obesity) are conditions that exist **before** pregnancy and can be treated. This supports **preconception care**: control blood sugar and blood pressure and support weight management *before* conception, not only during pregnancy. Diabetes, hypertension and BMI ≥ 35 together account for roughly 1,300 excess infant deaths a year among U.S. singletons if the associations are causal (an upper figure: some mothers have more than one factor, so the sum counts them twice). The excess deaths per year are a rough figure: RD × exposed births ÷ 8 years, and they assume causality.

### 5. How trustworthy is all this? (`05_checks`)
19 checks fixed before the results: 9 PASS, 1 FAIL (CDC's 2016–2017 tables), 3 WEAKENED (negative control: smoking, short interval, BMI 30–34.9), 2 APPLIED (random effects, imputation), 4 INFO. Every deviation from the plan is dated in the change log.

---

## Part II — Extra research (25 Nov 2026, `06_extra_research`)

All post-hoc; every rule was written in the plan before its run.

| Question | Result | Real-life meaning |
|---|---|---|
| Do our BMI data agree with NCHS? | Births per BMI class identical to NVSR 69(9); rates within 1.1% | An outside check of the data, not only of our own code |
| Does each factor act through the cause its biology predicts? | Diabetes → birth defects (RR 2.59 vs 1.64 for other causes); smoking → SUID (2.51 vs 1.40); hypertension → P07 code: no | Specific links support a real effect; poverty alone would raise all causes evenly |
| Can check-box errors explain the RRs? | No. Usual errors make the RRs too low (hypertension 1.50 → 1.75, smoking 1.68 → 2.18) | The Part 2 numbers are probably conservative |
| Do live births hide part of the harm? | Diabetes 1.84 → 2.48 and hypertension 1.50 → 1.74 with stillbirths | Preconception control of diabetes prevents stillbirths too, not only infant deaths |
| How much runs through earlier delivery? | Hypertension all of it (1.03); diabetes two thirds; BMI ≥ 40 half; smoking one third | For hypertension, preventing early delivery is the lever; for smoking, safe-sleep advice matters too (SUID) |
| Is the Part 1 model useful for a program? | Net benefit over "contact all / none" at every threshold 0.25–5% | Example: at a 1% threshold the model flags 10.4% of births with a net gain of 10.8 per 10,000 births |

---

## Part III — Audit: mistakes, weak points and improvements

### A. Mistakes found and already fixed during the work
1. The 2017 join failed (number padding) → compared as integers.
2. Wrong benchmark birth weight for deaths → numerator birth weight.
3. Out-of-memory crash in calibration → low-memory Newton solver (same results as statsmodels).
4. Missing settings after moving code to notebooks (`SETS`) → added; all notebooks lint-checked.
5. DuckDB decimal sums rounded rates to integers → cast to integers.
6. Newton overflow in the gestational-age model → step-halving.
7. Absent reference class gave collinear columns → fallback to the lowest present class.
8. Imputation lost births (a null comparison) → fixed and guarded by an assertion.
9. A wrong plain-language sentence ("4 in 100 die") → replaced by the top-risk table.
10. Papermill's leftover `REBUILD = True` cell restarted a 2.5-hour job → removed; runs now pass the parameter explicitly.

None of these changed a published number after it was reported, except item 9 (text only).

### B. Weak points that remain (say them in the limitations)
1. **Timing leakage in Part 1.** Three inputs carry a little information about pregnancy length. The pre-registered numbers (0.038) are optimistic; the strict model (0.030) is the honest headline. *Action:* lead with the strict numbers in the text.
2. **Residual social confounding in Part 2.** The negative control flags smoking, short intervals and BMI 30–34.9. Extra social markers explain part of it for smoking (RR 1.68 → 1.58), none of it for short intervals. Read these RRs as upper bounds.
3. **Exposure recording.** Hypertension, diabetes and smoking come from birth-certificate check boxes and self-report, which miss some cases. *Addressed 25 Nov 2026* (`06_extra_research` section 5): with published sensitivities the RRs stay above 1; the usual (non-differential) errors make them too low. The diabetes priors are assumptions (no validation value found).
4. **Live births only.** These factors also cause stillbirths. *Tested 25 Nov 2026* (`06_extra_research` section 6): with fetal deaths the diabetes RR rises from 1.84 to 2.48 (BIASED by the 20% rule) and hypertension from 1.50 to 1.74. The live-birth RRs under-state the harm. The interval could not be tested (not on the fetal file).
5. **No geography, no income.** The public files have no state or county since 2005, and no income.
6. **Interval measurement.** It is computed as months to birth minus gestational age, so it can be off by about one month near class borders.
7. **Bootstrap scope.** The Part 1 CIs cover test-set sampling only, not the variation from retraining the models.
8. **Unexplained postneonatal under-prediction** (13%) in the extension model.
9. **Very large sample.** Every Part 2 test is "significant" (Holm p < 1e-37). Judge the results by effect size and CI, not by p-values.
10. **Plan changes after Part 1.** Two exposures and the age-split extension were added after Part 1 results were seen (no Part 2 result was known). This is recorded, but an examiner may ask about it.

### C. Possible improvements, ranked by value for the thesis
1. **DONE 24 Nov 2026: test of the social-confounding explanation** (`04_association` section 18). Adding marital status, WIC and father's information lowers the smoking RR from 1.68 to **1.58** and its accident RR from 1.81 to 1.66; the short-interval RRs do not change; hypertension, diabetes and BMI are unchanged or slightly higher. So social confounding explains part of the smoking signal, not the interval signal; both stay upper bounds.
2. **Lead with strict Part 1 results** in the text (no code).
3. **DONE 25 Nov 2026: quantitative bias analysis** (`06_extra_research` section 5). All RRs robust.
4. **DONE 25 Nov 2026: stillbirth composite** (`06_extra_research` section 6). Diabetes biased by live-birth selection.
5. **Small code hygiene (about 5 minutes).** Make the calibration solver `_logit_newton` stop with an error if it does not converge, as the Part 2 fitter already does.

### D. Is the code finished?
Yes, for the planned analysis: data build, benchmark, Table 1, Part 1 (with strict and age-split analyses), Part 2 (with imputation and all checks), and the checks table. Items C1, C3 and C4 are done (C3 and C4 in `06_extra_research`); C2 is a writing task; C5 is a 5-minute fix.
