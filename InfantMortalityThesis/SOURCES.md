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

Total downloaded CDC ZIPs: 3,075,540,725 bytes (3.08 GB, or 2.86 GiB). `DOWNLOADS.md` records SHA-256 checksums and integrity checks.

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
