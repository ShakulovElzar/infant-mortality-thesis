"""Convert one CDC linked birth-cohort ZIP into one Parquet file.

Run: python -I src/build_parquet.py data/cdc/2024PE2023CO.zip
Output: data/parquet/cohort_<year>.parquet (one row per birth, ignored by Git).

- Reads the ZIP as a stream (no extraction).
- Keeps every public field of that year's layout (fillers dropped), as text
  codes exactly as CDC wrote them, with spaces stripped and empty -> null.
- Renames the few fields that CDC renamed between years (same position),
  so every cohort uses the 2023 names.
- Adds the death fields from the two numerator files of the cohort
  (deaths in year Y and Y+1 to babies born in Y), joined on
  CO_SEQNUM + CO_YOD, plus `cohort` and `death` (True = linked infant death).
"""
import re
import sys
import zipfile
from pathlib import Path

import polars as pl
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).parent))
from cdc_layout import parse_layout  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "parquet"
DEN_LEN = 1346
CHUNK_BYTES = 600_000_000
# Older names -> 2023 names (same positions; checked in reference/layout_differences.md).
RENAME = {"AGED": "AGEDX", "AGER5": "AGER5X", "AGER22": "AGER22X", "UC0D": "UCOD", "CO_DODYY": "CO_YOD"}


def file_year(name: str) -> int:
    v = int(re.search(r"VS(\d+)LINK", name).group(1))
    return v + 2000 if v < 100 else v


def slice_cols(lines: pl.Series, fields: list[dict]) -> pl.DataFrame:
    df = pl.DataFrame({"line": lines})
    return df.select([
        pl.col("line").str.slice(f["start"] - 1, f["end"] - f["start"] + 1)
        .str.strip_chars().replace("", None).alias(f["name"])
        for f in fields
    ])


def key_expr() -> list[pl.Expr]:
    # 2017 pads CO_SEQNUM with spaces, numerators with zeros: compare as integers.
    return [pl.col("CO_SEQNUM").cast(pl.Int64, strict=False).alias("_seq"), pl.col("CO_YOD").alias("_yod")]


def build(zip_path: Path) -> Path:
    cohort = int(re.search(r"PE(\d{4})CO", zip_path.name).group(1))
    fields = [dict(f, name=RENAME.get(f["name"], f["name"])) for f in parse_layout(cohort)
              if f["public"] and not f["name"].upper().startswith("FILLER")]
    den_fields = [f for f in fields if f["end"] <= DEN_LEN]
    death_fields = [f for f in fields if f["start"] > DEN_LEN]

    z = zipfile.ZipFile(zip_path)
    names = z.namelist()
    den_name = next(n for n in names if ("DENPUB" in n or "DENOM" in n) and file_year(n) == cohort)
    num_names = [n for n in names if "NUMPUB" in n and file_year(n) in (cohort, cohort + 1)]

    # Deaths: both numerator files, keep babies born in the cohort year.
    key_fields = [f for f in den_fields if f["name"] in ("DOB_YY", "CO_SEQNUM", "CO_YOD")]
    deaths = []
    for n in num_names:
        lines = pl.Series(z.read(n).decode("latin-1").splitlines())
        d = slice_cols(lines, key_fields + death_fields)
        deaths.append(d.filter(pl.col("DOB_YY") == str(cohort)))
    deaths = pl.concat(deaths).with_columns(key_expr()).drop("DOB_YY", "CO_SEQNUM", "CO_YOD")
    assert deaths.select(pl.struct("_seq", "_yod").is_duplicated().any()).item() is False

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"cohort_{cohort}.parquet"
    deaths = deaths.with_columns(pl.lit(True).alias("death"))
    writer, n_rows, n_linked = None, 0, 0

    def write(body: bytes):
        nonlocal writer, n_rows, n_linked
        lines = pl.Series(body.decode("latin-1").splitlines())
        df = slice_cols(lines, den_fields).with_columns(key_expr())
        # Survivors have a blank CO_SEQNUM (null key), so they never match.
        df = df.join(deaths, on=["_seq", "_yod"], how="left")
        df = df.with_columns(pl.col("death").fill_null(False),
                             pl.lit(cohort, pl.Int16).alias("cohort")).drop("_seq", "_yod")
        n_rows += df.height
        n_linked += int(df["death"].sum())
        table = df.to_arrow()
        if writer is None:
            writer = pq.ParquetWriter(out, table.schema, compression="zstd")
        writer.write_table(table)

    rest = b""
    with z.open(den_name) as fh:
        while True:
            block = fh.read(CHUNK_BYTES)
            if not block:
                if rest.strip():
                    write(rest)
                break
            block = rest + block
            cut = block.rfind(b"\n") + 1
            body, rest = block[:cut], block[cut:]
            if body:
                write(body)
    writer.close()
    unmatched = deaths.height - n_linked
    print(f"{cohort}: births {n_rows:,}  deaths in numerators {deaths.height:,}  linked {n_linked:,}  "
          f"unmatched {unmatched}  -> {out.name} {out.stat().st_size / 1e6:,.0f} MB")
    assert unmatched == 0, "some deaths did not join to a birth"
    return out


if __name__ == "__main__":
    for p in sys.argv[1:]:
        build(Path(p))
