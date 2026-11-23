# Infant Mortality Thesis

## Scope

Main outcome: death before age one among U.S. live births. Candidate maternal factors include prepregnancy BMI, diabetes, and hypertension; audit field availability by cohort before fixing the final question. The main public data are the CDC/NVSS linked birth–infant death birth-cohort files. Keep raw downloads under `data/` and out of Git. Preserve source ZIPs and verify integrity before extraction. Do not mix birth-cohort and period denominators or use fields recorded after the prediction time.

## Data plan

- **Main:** CDC/NVSS `period-cohort-linked` archives, birth cohorts 2017–2023. Use birth-cohort records, not period records, for the principal model. The public files have no state/county geography from 2005 onward.
- **Later comparison:** DHS birth-history (BR) survey records from selected countries. Access requires the user's DHS account and survey permission. Treat maternal recall, censoring and survey weights explicitly. No person-level join to CDC.
- **Later comparison:** UNICEF MICS birth-history (BH) records, ideally one selected survey/country first. Download requires UNICEF authorization. No person-level join to CDC.
- **Optional separate county analysis:** CDC WONDER linked-birth aggregate output joined by county and year to HRSA AHRF and Census ACS or CDC SVI. This is ecological, not a feature layer on individual CDC children.

## Status

Workspace created on the SSD on 20 November 2026. All seven CDC birth-cohort ZIPs (2017–2023; 3,075,540,725 bytes) and the 2024–2025 HRSA county ZIP are downloaded; ZIP integrity checks passed and SHA-256 hashes are in `DOWNLOADS.md`. The user has no approved DHS or MICS microdata access; only public guides/metadata are saved. Each `YYYYPE(Y-1)CO.zip` holds the full cohort Y-1: denominator `..._add_Seq_for<Y-1>Cohort` plus numerators for Y-1 and Y; join on `CO_SEQNUM` (365-371) + `CO_YOD` (372-375), keep `RESTATUS<4` and `DOB_YY=cohort`, no `RECWT`. Profiled all cohorts on 23 Nov 2026 with `python3 -I src/profile_cohorts.py data/cdc/<zip> reports/profile/` (streams the ZIP, about 30 s each; output `reports/profile/<cohort>.json`). Cohorts 2018–2023 join cleanly: 22.08 M US-resident births, 121,307 deaths, 0 unmatched, IMR 5.35–5.63 per 1000. **2017 cohort fails**: its denominator `VS17LINK.Public.USDENPUB_20200520` has blank `CO_SEQNUM`, so 19,513 of 22,167 deaths do not join. Treat 2017 as unusable unless CDC has a re-sequenced file. Missing values are low (BMI about 2%, diabetes/hypertension 0.1–0.2%) except marital status (about 12%, California not released). Gestational hypertension rose from 6.4% to 10.1% and pre-pregnancy hypertension from 1.9% to 3.2% across 2017–2023. Next: audit CDC variables and build the first U.S. cohort analysis. County WONDER outcomes and international microdata remain future work.
