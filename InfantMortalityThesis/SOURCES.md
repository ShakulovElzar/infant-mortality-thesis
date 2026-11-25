# Source manifest

Main portal: https://www.cdc.gov/nchs/data_access/VitalStatsOnline.htm

| Birth cohort | Period/cohort ZIP | Downloaded bytes |
|---:|---|---:|
| 2023 | https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/period-cohort-linked/2024PE2023CO.zip | 432,493,258 |
| 2022 | https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/period-cohort-linked/2023PE2022CO.zip | 434,390,502 |
| 2021 | https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/period-cohort-linked/2022PE2021CO.zip | 437,642,448 |
| 2020 | https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/period-cohort-linked/2021PE2020CO.zip | 433,532,955 |
| 2019 | https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/period-cohort-linked/2020PE2019CO.zip | 438,388,388 |
| 2018 | https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/period-cohort-linked/2019PE2018CO.zip | 447,265,743 |
| 2017 | https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/period-cohort-linked/2018PE2017CO.zip | 451,827,431 |
| 2016 | https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/period-cohort-linked/2017PE2016CO.zip | 460,879,295 |

Total downloaded CDC ZIPs: 3,536,420,020 bytes (3.54 GB, eight cohorts 2016–2023). `DOWNLOADS.md` records SHA-256 checksums and integrity checks.

The ZIPs include period and cohort components. Use the birth-cohort denominator and matching numerator for the intended cohort. Exact member names must be inspected after download. See the [2024 period/2023 cohort guide](https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/DVS/period-cohort-linked/24PE23CO_linkedUG.pdf).

The 2023-cohort archive contains four files (2023 cohort denominator and numerator, plus 2024 period denominator and numerator) and expands to about 9.83 GB. Do not extract all seven archives at once; select cohort files for analysis. The 2023-cohort guide is saved in `docs/`.

## Later individual-level international datasets

- DHS Program birth recode (BR): https://dhsprogram.com/data/available-datasets.cfm . Access: register at https://dhsprogram.com/data/dataset_admin/login_main.cfm and request permission for selected country surveys. The user reported no current access on 20 November 2026. The public DHS API is aggregate indicators, not BR microdata. An official guide is saved in `docs/`.
- UNICEF MICS catalog: https://mics.unicef.org/surveys . As one candidate, the 2019 Bangladesh survey's BH dictionary is at https://micsnada.unicef.org/index.php/catalog/447/data-dictionary and its official microdata link is https://mics.unicef.org/catalog/get-microdata/BGD_2019_MICS6_v01_M . The user reported no current access. Register/request data at https://mics.ipums.org/mics/register.shtml or through the UNICEF catalog. The public catalog metadata for this survey is saved in `docs/`; it is not microdata. Check the actual BH file size and coverage after approval.

## Separate county-level dataset chain

- CDC WONDER linked birth/infant death: https://wonder.cdc.gov/lbd.html
- HRSA AHRF county files: https://data.hrsa.gov/data/download . The 2024–2025 county CSV archive is saved as `data/county/AHRF_2024-2025_CSV.zip` (about 23.3 MB, eight CSVs inside). Its technical documentation is in `docs/`.
- Census ACS API: https://www.census.gov/programs-surveys/acs/data/data-via-api.html
- CDC SVI: https://www.atsdr.cdc.gov/place-health/php/svi/svi-data-documentation-download.html

Public CDC individual records have no county identifiers; county sources can be joined only to aggregate WONDER output. See https://www.cdc.gov/nchs/nvss/dvs_data_release.htm .

## Future references (planned, not used yet)

- **CDC WONDER Linked Birth / Infant Death Records, 2017–2023 Expanded:** https://wonder.cdc.gov/lbd.html (help: https://wonder.cdc.gov/wonder/help/lbd-expanded.html). Online aggregate queries, free after accepting the data-use terms. Planned uses: (1) check our cohort counts and rates by year, maternal risk factor, birth weight and gestation against official tables; (2) a separate state- or large-county-level analysis. WONDER output is aggregate and suppresses small cells, so it cannot add columns to individual CDC records. Note that WONDER rates are period-based by default; compare like with like.
- **NCHS fetal-death files:** used since 25 Nov 2026 (`06_extra_research` section 6); see the section below.

## Used in the extra research (25 Nov 2026, `06_extra_research`)

- **NCHS fetal-death public files 2016–2023** (`Fetal<year>US_COD.zip`), https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/fetaldeathus/ ; user guides in `docs/fetal_guides/`. Stillbirth composite (section 6).
- **Ely DM, Gregory ECW, Drake P.** Infant mortality by maternal prepregnancy body mass index: United States, 2017–2018. *National Vital Statistics Reports* 69(9), 2020. Table 2 used as an external check (section 3). PDF in `docs/external/`.
- **Martin JA, Wilson EC, Osterman MJK, Saadi EW, Sutton SR, Hamilton BE.** Assessing the quality of medical and health data from the 2003 birth certificate revision: results from two states. *National Vital Statistics Reports* 62(2), 2013. Table 4: pre-pregnancy hypertension sensitivity 13/33 (state A). Bias analysis (section 5).
- **Howland RE, Mulready-Ward C, Madsen AM, et al.** Reliability of reported maternal smoking: comparing the birth certificate to maternal worksheets and prenatal and hospital medical records, New York City and Vermont, 2009. *Matern Child Health J* 19(9):1916–1924, 2015. Table 2 counts (smoking before pregnancy). Bias analysis (section 5).
- **Dietz P, Bombard J, Mulready-Ward C, et al.** Validation of selected items on the 2003 U.S. Standard Certificate of Live Birth: New York City and Vermont. *Public Health Reports* 130(1):60–70, 2015. Read only in its text: pre-pregnancy diabetes and hypertension could not be evaluated (small numbers). No value used.
- **Methods (not read in this session; standard references):** Lash TL, Fox MP, Fink AK, *Applying Quantitative Bias Analysis to Epidemiologic Data* (Springer); Vickers AJ, Elkin EB, Decision curve analysis, *Med Decis Making* 26:565–574, 2006.
