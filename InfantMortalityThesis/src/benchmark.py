"""Compare our Parquet counts with CDC's own cohort documentation tables.

CDC table used: cohort "Documentation Table 2" in each user guide:
live births and infant deaths by race/Hispanic origin of mother, sex and
birth weight. It exists for all 8 cohorts and checks the fields
MRACEHISP, SEX, BRTHWGT and the death linkage at the same time.
"""
import re
import sys
import zipfile
from pathlib import Path

import duckdb
import polars as pl

sys.path.insert(0, str(Path(__file__).parent))
from cdc_layout import guide_text  # noqa: E402

PARQUET = Path(__file__).resolve().parents[1] / "data" / "parquet"
BW_BINS = ["<500", "500-749", "750-999", "1000-1249", "1250-1499", "1500-1999",
           "2000-2499", "2500+", "Not stated"]
SEXES = {"Both sexes": "Both", "Male": "M", "Female": "F"}


def race_of(label: str):
    s = label.strip()
    if s.lower().startswith("all races"):
        return "All"
    if "Hawaiian" in s:
        return "NH NHOPI"
    if "American Indian" in s:
        return "NH AIAN"
    if "Asian" in s:
        return "NH Asian"
    if "Black" in s:
        return "NH Black"
    if "White" in s:
        return "NH White"
    if s == "Hispanic":
        return "Hispanic"
    return None


def cdc_table2(cohort: int) -> pl.DataFrame:
    lines = guide_text(cohort)
    t6 = max(i for i, l in enumerate(lines) if l.startswith("Documentation Table 6."))
    start = next(i for i, l in enumerate(lines) if i > t6 and l.startswith("Documentation Table 2."))
    end = next(i for i, l in enumerate(lines) if i > start and l.startswith("Documentation Table 3."))
    rows, race, sex, births = [], None, None, None
    for l in lines[start:end]:
        s = l.strip()
        if s in SEXES:
            sex = SEXES[s]
        elif race_of(s) and not re.search(r"\d", s.split("/")[0]):
            race = race_of(s)
        elif s.startswith(("Live births", "Infant deaths")):
            # Some guides print "-" for zero.
            tail = s.split("..")[-1] if ".." in s else s
            nums = [0 if x == "-" else int(x.replace(",", "")) for x in re.findall(r"\d[\d,]*|(?<!\S)-(?!\S)", tail)]
            assert len(nums) == 10, (cohort, s)
            if s.startswith("Live births"):
                births = nums
            else:
                for b, (nb, nd) in zip(["Total"] + BW_BINS, zip(births, nums)):
                    rows.append({"race": race, "sex": sex, "bw": b, "cdc_births": nb, "cdc_deaths": nd})
    return pl.DataFrame(rows).unique(["race", "sex", "bw"], keep="first")


BW_CASE = """CASE WHEN BRTHWGT = '9999' OR BRTHWGT IS NULL THEN 'Not stated'
                  WHEN CAST(BRTHWGT AS INT) < 500 THEN '<500'  WHEN CAST(BRTHWGT AS INT) < 750 THEN '500-749'
                  WHEN CAST(BRTHWGT AS INT) < 1000 THEN '750-999' WHEN CAST(BRTHWGT AS INT) < 1250 THEN '1000-1249'
                  WHEN CAST(BRTHWGT AS INT) < 1500 THEN '1250-1499' WHEN CAST(BRTHWGT AS INT) < 2000 THEN '1500-1999'
                  WHEN CAST(BRTHWGT AS INT) < 2500 THEN '2000-2499' ELSE '2500+' END"""
RACE_CASE = """CASE MRACEHISP WHEN '1' THEN 'NH White' WHEN '2' THEN 'NH Black' WHEN '3' THEN 'NH AIAN'
                  WHEN '4' THEN 'NH Asian' WHEN '5' THEN 'NH NHOPI' WHEN '7' THEN 'Hispanic' END"""


def _grouped(source: str, value: str, table: pl.DataFrame | None = None) -> pl.DataFrame:
    q = f"""
    WITH b AS (SELECT {RACE_CASE} AS race, SEX AS sex, {BW_CASE} AS bw FROM {source})
    SELECT race, sex, bw, COUNT(*) AS {value} FROM b WHERE race IS NOT NULL
      GROUP BY GROUPING SETS ((race, sex, bw), (race, sex), (race, bw), (race))
    UNION ALL
    SELECT 'All' AS race, sex, bw, COUNT(*) AS {value} FROM b GROUP BY GROUPING SETS ((sex, bw), (sex), (bw), ())
    """
    con = duckdb.connect()
    if table is not None:
        con.register("t", table.to_arrow())
    return pl.from_arrow(con.sql(q).arrow()).with_columns(
        pl.col("sex").fill_null("Both"), pl.col("bw").fill_null("Total"))


def numerator_deaths(cohort: int) -> pl.DataFrame:
    """Cohort deaths read straight from the two numerator files in the ZIP.

    CDC tabulates deaths by the birth weight on the death (numerator) record.
    CDC imputes missing birth weight separately in the numerator and the
    denominator, so the two values can differ for a few records.
    """
    zp = next(Path(__file__).resolve().parents[1].glob(f"data/cdc/*PE{cohort}CO.zip"))
    z = zipfile.ZipFile(zp)
    recs = []
    for n in z.namelist():
        y = int(re.search(r"VS(\d+)LINK", n).group(1))
        y = y + 2000 if y < 100 else y
        if "NUMPUB" in n and y in (cohort, cohort + 1):
            for r in z.open(n):
                r = r.decode("latin-1")
                if r[8:12] == str(cohort) and int(r[103]) < 4:   # DOB_YY 9-12, RESTATUS 104
                    recs.append((r[116], r[474], r[511:515].strip() or None))  # MRACEHISP 117, SEX 475, BRTHWGT 512-515
    return pl.DataFrame(recs, schema=["MRACEHISP", "SEX", "BRTHWGT"], orient="row")


def our_table2(cohort: int) -> pl.DataFrame:
    births = _grouped(f"'{PARQUET}/cohort_{cohort}.parquet' WHERE CAST(RESTATUS AS INT) < 4", "births")
    deaths = _grouped("t", "deaths", numerator_deaths(cohort))
    return births.join(deaths, on=["race", "sex", "bw"], how="left").with_columns(pl.col("deaths").fill_null(0))


def compare(cohort: int) -> pl.DataFrame:
    cdc = cdc_table2(cohort)
    ours = our_table2(cohort)
    m = cdc.join(ours, on=["race", "sex", "bw"], how="left")
    return m.with_columns(
        pl.lit(cohort).alias("cohort"),
        (pl.col("births") - pl.col("cdc_births")).alias("diff_births"),
        (pl.col("deaths") - pl.col("cdc_deaths")).alias("diff_deaths"),
        (1000 * pl.col("deaths") / pl.col("births")).round(2).alias("rate"),
        (1000 * pl.col("cdc_deaths") / pl.col("cdc_births")).round(2).alias("cdc_rate"),
    )


def guide_record_counts(cohort: int) -> dict:
    """Record counts printed in the guide for the cohort files (all residents, incl. foreign)."""
    lines = guide_text(cohort)
    out = {}
    for i, l in enumerate(lines):
        for key, label in (("guide_births", "Cohort Denominator File"), ("guide_deaths", "Cohort Numerator File")):
            if label in l and key not in out:
                for nxt in lines[i + 1:i + 6]:
                    m = re.search(r"Record count.*?([\d,]{5,})\s*$", nxt)
                    if m:
                        out[key] = int(m.group(1).replace(",", ""))
                        break
    return out
