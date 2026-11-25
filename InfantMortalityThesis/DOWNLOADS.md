# Download manifest

Downloaded from the official sources listed in `SOURCES.md` on 20 November 2026. Raw data and source documents are ignored by Git.

| File | Bytes | SHA-256 |
|---|---:|---|
| `data/cdc/2017PE2016CO.zip` | 460,879,295 | `f04b30a2ccb768d15056f995f466aa725f9b15350b28dd76b8b66cc2b264bb65` |
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

CDC ZIP total: 3,536,420,020 bytes (eight ZIPs). The 2016-cohort ZIP was added on 23 Nov 2026; its size matches the CDC FTP listing and `unzip -tq` passed.

Integrity checks: `unzip -tq` passed for all seven CDC archives, the AHRF county ZIP, and its documentation ZIP. Both PDFs opened with `pdfinfo`; the MICS metadata parsed as JSON. Each CDC ZIP contains four members, including files for the birth cohort and the calendar period.


## Added 25 Nov 2026 (extra research, `06_extra_research`)

NCHS fetal-death public files 2016–2023 from https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Datasets/DVS/fetaldeathus/ (sizes equal the FTP listing; `unzip -tq` passed for all eight), their user guides from https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Dataset_Documentation/DVS/fetaldeath/, and NVSR 69(9) from https://www.cdc.gov/nchs/data/nvsr/nvsr69/NVSR-69-09-508.pdf.

| File | Bytes | SHA-256 |
|---|---|---|
| `data/fetal/Fetal2016US_COD.zip` | 2,998,299 | `01ebec5ecb3e8617309992aa8ff1b5018df7b4dcad10f415c79297bf9a1ab094` |
| `data/fetal/Fetal2017US_COD.zip` | 2,943,616 | `bdfd36862bd1de6cf085e2f2bc898a00133924f9e62afa9cda163e96d09701dd` |
| `data/fetal/Fetal2018US_COD.zip` | 2,663,640 | `11b56092229932ce5ad0503f8803ce09d627e66855474bd757b7bb258daf6538` |
| `data/fetal/Fetal2019US_COD.zip` | 2,561,768 | `c1ec8b7702deca5d73c6657f34dcddde1be2a03da2c1b2c776916dc136582da7` |
| `data/fetal/Fetal2020US_COD.zip` | 2,394,147 | `1e289b816ff401c21cd4bb2ff0dd48f4b6261edf4920cbb3b1eb13355593fef0` |
| `data/fetal/Fetal2021US_COD.zip` | 2,438,276 | `e12feaf0c8aff693a6c874ff62838936ea7ee8cc161bbdb07b744304ddac8c77` |
| `data/fetal/Fetal2022US_COD.zip` | 2,270,485 | `b95db4fa2240175fd054dcc870c365dd42044191814d96c11f243b3da128c4d2` |
| `data/fetal/Fetal2023US_COD.zip` | 2,219,550 | `54c89017ad1365a939a4889ea93d9c91583a5007384709df8379cc89f7bdcdd4` |
| `docs/external/nvsr69_09.pdf` | 829,032 | `f5564b360da0b8d6cf89103212057acd887dab57014b3167db28f4df5d8d5be8` |
| `docs/fetal_guides/2016FetalUserGuide.pdf` | 1,527,652 | `279e49dad94b3380890c4e43cdaa7d56647ed90ecc55a7b341bcf5f49542d14a` |
| `docs/fetal_guides/2017FetalUserGuide.pdf` | 1,434,014 | `7474a1dbbad1341101d38896b1ab296fe0d2d3dfbca74ed604d76c4d5d68aaa6` |
| `docs/fetal_guides/2018FetalUserGuide.pdf` | 1,751,923 | `d20152b6d939cc156158ab8945e5877e18a90f613c667514ad98483749657385` |
| `docs/fetal_guides/2019FetalUserGuide.pdf` | 820,522 | `47fab7cca670aa8098eef4eeda18bfa6cdcf4b16d58b68585b1f27bf81f6c53c` |
| `docs/fetal_guides/2020fetaluserguide.pdf` | 1,057,866 | `3771d8c766d97b9469ec1c1645e9752081550db319ccc62bb896b8d21e723e9a` |
| `docs/fetal_guides/2021fetaluserguide.pdf` | 1,066,595 | `e1e79b25665730158747a3645fc01db908fb6c904ba743dda9701a009cfe6d3a` |
| `docs/fetal_guides/2022fetaluserguide.pdf` | 1,092,157 | `d515813f89765af0ca2804afb7673f03e4efd4737f3de04e6939f9e7f43b20b3` |
| `docs/fetal_guides/2023fetaluserguide.pdf` | 1,064,197 | `947042d892ea1cf584392f55dbc833c30b7ff68b7290f5958164fefaf58863aa` |
