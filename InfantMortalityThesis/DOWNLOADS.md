# Download manifest

Downloaded from the official sources listed in `SOURCES.md` on 20 November 2026. Raw data and source documents are ignored by Git.

| File | Bytes | SHA-256 |
|---|---:|---|
| `data/cdc/2018PE2017CO.zip` | 451,827,431 | `60963545ea498b47c69a1cbf8810ccaa661dbec5d81edf133a2d052816422510` |
| `data/cdc/2019PE2018CO.zip` | 447,265,743 | `25901e1fa512dd57edb0e2a56af62069522ebd66bbec13ee3bb2ac00e5ee945d` |
| `data/cdc/2020PE2019CO.zip` | 438,388,388 | `6666ae775e793a33259e6e4ee19e8fa93928e21b9d6ff609c1ca40fb6f82ca6b` |
| `data/cdc/2021PE2020CO.zip` | 433,532,955 | `6ea469e22c7e841c32db8c92309ef108f1f5696981b7df16524f3a3704caa685` |
| `data/cdc/2022PE2021CO.zip` | 437,642,448 | `d83d1c79734ec8ff4ea21db9dc382a22fea244b2423ff81061242a5ba9e80503` |
| `data/cdc/2023PE2022CO.zip` | 434,390,502 | `1c2ad811a4b8c4aecded084162cfcba0ecf6d8c7dd06909aaacddd30967e3fe6` |
| `data/cdc/2024PE2023CO.zip` | 432,493,258 | `24742c158e15134383514a0516dbaa0e6f94ba49ec253fe552719ceaa5f735c8` |
| `data/county/AHRF_2024-2025_CSV.zip` | 23,287,136 | `6974adcd93ed8e0718d655e6912707bfc5ec37a9a2baf1fc27f59f12b5c441a0` |
| `docs/24PE23CO_linkedUG.pdf` | 1,079,044 | `fb5a352fce4d83770ec5335fe55df018a67b6dce9487307c12fdf64edda5382a` |
| `docs/AHRF_USER_TECH_2024-2025.zip` | 1,019,394 | `aa03026107b8acf7fd5c5f2d0c96c30b44d254cbb122a31141a3aee2d726f680` |
| `docs/DHS_Guide_to_Statistics_DHS7_v2.pdf` | 4,914,605 | `c92f43f3703806fae16894e9925e193e789c02169a82db010a069e21a8f79517` |
| `docs/MICS_Bangladesh_2019_metadata.json` | 5,406 | `f06ee33738f06b4113a0a5d1606538606675d524b3880e2f491ef1cbaa9b43c0` |

CDC ZIP total: 3,075,540,725 bytes.

Integrity checks: `unzip -tq` passed for all seven CDC archives, the AHRF county ZIP, and its documentation ZIP. Both PDFs opened with `pdfinfo`; the MICS metadata parsed as JSON. Each CDC ZIP contains four members, including files for the birth cohort and the calendar period.
