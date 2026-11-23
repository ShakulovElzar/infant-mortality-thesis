"""Part 1 inputs: items known before delivery, decoded from the CDC text codes.

Rules (plan, section 3):
- "Unknown / not stated" codes become missing (NaN).
- If an item's reporting flag is not 1 (the state did not collect it), the
  value becomes missing too.
- Set A = known in early pregnancy. Set B = Set A + items known before delivery.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class Feature:
    name: str      # our short name
    sql: str       # DuckDB expression on the Parquet columns
    kind: str      # "num" (number) or "cat" (category code)
    in_set: str    # "A" or "B"
    label: str     # plain-English label for tables


def num(col, missing=(), flag=None, cast="FLOAT"):
    cond = " OR ".join([f"{col} IS NULL"] + [f"{col} = '{m}'" for m in missing])
    f = f"COALESCE({flag}, '1') <> '1' OR " if flag else ""
    return f"CASE WHEN {f}{cond} THEN NULL ELSE CAST({col} AS {cast}) END"


def yn(col, flag=None):
    f = f"WHEN COALESCE({flag}, '1') <> '1' THEN NULL " if flag else ""
    return f"CAST(CASE {f}WHEN {col} = 'Y' THEN 1 WHEN {col} = 'N' THEN 0 ELSE NULL END AS FLOAT)"


FEATURES = [
    # Set A: known in early pregnancy
    Feature("mage", num("MAGER"), "num", "A", "Mother's age (years)"),
    Feature("race", num("MRACEHISP", ["8"]), "cat", "A", "Mother's race/Hispanic origin"),
    Feature("nativity", num("MBSTATE_REC", ["3"]), "cat", "A", "Mother born outside the U.S."),
    Feature("educ", num("MEDUC", ["9"], "F_MEDUC"), "cat", "A", "Mother's education"),
    Feature("marital", num("DMAR", ["9"]), "cat", "A", "Marital status"),
    Feature("pay", num("PAY_REC", ["9"], "F_PAY_REC"), "cat", "A", "Payment source"),
    Feature("priorlive", num("PRIORLIVE", ["99"]), "num", "A", "Prior births now living"),
    Feature("priordead", num("PRIORDEAD", ["99"]), "num", "A", "Prior births now dead"),
    Feature("priorterm", num("PRIORTERM", ["99"]), "num", "A", "Prior terminations/fetal deaths"),
    Feature("lbo", num("LBO_REC", ["9"]), "num", "A", "Live birth order"),
    Feature("illb", num("ILLB_R11", ["99"]), "cat", "A", "Interval since last live birth"),
    Feature("ilp", num("ILP_R11", ["99"]), "cat", "A", "Interval since last pregnancy"),
    Feature("cig0", num("CIG_0", ["99"], "F_CIGS_0"), "num", "A", "Cigarettes/day before pregnancy"),
    Feature("bmi", num("BMI", ["99.9"], "F_PWGT"), "num", "A", "Pre-pregnancy BMI"),
    Feature("height", num("MHTR", ["99"], "F_M_HT"), "num", "A", "Mother's height (inches)"),
    Feature("pdiab", yn("RF_PDIAB", "F_RF_PDIAB"), "cat", "A", "Pre-pregnancy diabetes"),
    Feature("phype", yn("RF_PHYPE", "F_RF_PHYPE"), "cat", "A", "Pre-pregnancy hypertension"),
    Feature("ppb", yn("RF_PPB", "F_RF_PPB"), "cat", "A", "Previous preterm birth"),
    Feature("inft", yn("RF_INFT", "F_RF_INFT"), "cat", "A", "Infertility treatment"),
    Feature("cesarn", num("RF_CESARN", ["99"], "F_RF_NCESAR"), "num", "A", "Number of previous cesareans"),
    Feature("fage", num("FAGECOMB", ["99"]), "num", "A", "Father's age"),
    Feature("frace", num("FRACEHISP", ["8", "9"]), "cat", "A", "Father's race/Hispanic origin"),
    Feature("feduc", num("FEDUC", ["9"], "F_FEDUC"), "cat", "A", "Father's education"),
    Feature("year", "CAST(cohort AS FLOAT)", "num", "A", "Birth cohort year"),
    # Set B adds: known before delivery
    Feature("cig1", num("CIG_1", ["99"], "F_CIGS_1"), "num", "B", "Cigarettes/day, 1st trimester"),
    Feature("precare", num("PRECARE", ["99"], "F_MPCB"), "num", "B", "Month prenatal care began"),
    Feature("wic", yn("WIC", "F_WIC"), "cat", "B", "WIC food program"),
    Feature("gdiab", yn("RF_GDIAB", "F_RF_GDIAB"), "cat", "B", "Gestational diabetes"),
    Feature("ghype", yn("RF_GHYPE", "F_RF_GHYPE"), "cat", "B", "Gestational hypertension"),
    Feature("plural", num("DPLURAL"), "num", "B", "Plurality (twins etc.)"),
    Feature("ip_gon", yn("IP_GON", "F_IP_GON"), "cat", "B", "Gonorrhea"),
    Feature("ip_syph", yn("IP_SYPH", "F_IP_SYPH"), "cat", "B", "Syphilis"),
    Feature("ip_chlam", yn("IP_CHLAM", "F_IP_CHLAM"), "cat", "B", "Chlamydia"),
    Feature("ip_hepb", yn("IP_HEPB", "F_IP_HEPB"), "cat", "B", "Hepatitis B"),
    Feature("ip_hepc", yn("IP_HEPC", "F_IP_HEPC"), "cat", "B", "Hepatitis C"),
]

SET_A = [f.name for f in FEATURES if f.in_set == "A"]
SET_B = SET_A + [f.name for f in FEATURES if f.in_set == "B"]
KIND = {f.name: f.kind for f in FEATURES}
LABEL = {f.name: f.label for f in FEATURES}
# Nominal categories for the tree model (ordered codes such as education stay numeric there).
TREE_CATEGORICAL = {"race", "nativity", "marital", "pay", "illb", "ilp", "frace"}
SPLINE = {"mage", "bmi"}
