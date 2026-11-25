# Thesis outline (25 Nov 2026)

Model: Max Kaparov's L-31 thesis (54 pages, 5 chapters; `docs/peer_reference/`, git-ignored). Supervisor: Prof. Daniele Ravì. Target: about 60 pages. LaTeX skeleton: `thesis/main.tex` (same headings).

## Front matter
Cover (UniME, MIFT, Bachelor's Degree in Computer Science L31, Curriculum Data Analysis; academic year to confirm), Contents, List of Figures, List of Tables, Abstract (1 page), Acknowledgement.

## 1 Introduction (about 4 pages)
1.1 Background and Motivation · 1.2 Problem Statement · 1.3 Research Questions and Objectives (RQ1 prediction, RQ2 association) · 1.4 Thesis Structure

## 2 State of the Art (about 6 pages)
2.1 Measuring Infant Mortality · 2.2 Maternal Risk Factors · 2.3 Prediction of Rare Outcomes · 2.4 Causal Inference from Observational Data · 2.5 Statistical Tools

## 3 Material and Methods (about 15 pages)
3.1 Data Source and Study Population · 3.2 Data Build and Validation · 3.3 Descriptive Analysis and Missing Data · 3.4 Pre-Registered Analysis Plan · 3.5 Part 1: Prediction · 3.6 Part 2: Association · 3.7 Extra Analyses (post-hoc, E1–E6) · 3.8 Software and Reproducibility

## 4 Results and Discussion (about 20 pages)
4.1 Data Validation against CDC · 4.2 Who Dies before Age One · 4.3 Model Comparison and Calibration (lead with strict 0.030) · 4.4 What Drives the Prediction (issue #4) · 4.5 Early vs Late Deaths, Subgroups and Fairness · 4.6 Decision Curves · 4.7 Adjusted Risk Ratios · 4.8 Robustness · 4.9 Negative Control and Collider Demonstration (issue #2) · 4.10 Cause of Death, Recording Bias and Stillbirths · 4.11 Mediation through Gestational Age (issue #1) · 4.12 Comparison with Published Studies

## 5 Conclusion and Future Works (about 4 pages)
5.1 Summary of Contributions · 5.2 Key Findings · 5.3 Limitations (results_overview Part III B, issues #3, #5) · 5.4 Future Works

## End matter
Bibliography (25–40 references) · Appendix A Pre-Set Checks · B Variables and Codes · C Causal Diagrams · D Analysis Plan Change Log

## New figures to draw
Data-flow diagram (ZIP -> fixed-width -> Parquet -> analysis tables); one example DAG.
