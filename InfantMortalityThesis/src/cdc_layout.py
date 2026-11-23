"""Parse the record layout of a CDC/NVSS linked birth/infant death user guide.

The guides are PDFs (docs/guides/*_linkedUG.pdf). We convert them with
`pdftotext -layout` (poppler) and read the layout table line by line.
Each layout row starts with a position ("9-12" or "104"), then a length,
an optional file code ("P,G" = in the public file), the field name and
its description. Code values follow on the same and the next lines.
"""
import re
import subprocess
from pathlib import Path

GUIDE_DIR = Path(__file__).resolve().parents[1] / "docs" / "guides"
# Cohort year -> guide file (guide "YYPE(YY-1)CO" documents cohort YY-1).
GUIDES = {c: GUIDE_DIR / f"{(c + 1) % 100:02d}PE{c % 100:02d}CO_linkedUG.pdf" for c in range(2016, 2024)}

ROW = re.compile(
    r"^(\s*)(\d{1,4})(?:-(\d{1,4}))?\s+\d+\s+"      # position, length (length is unreliable)
    r"(?:([PGT](?:,[PGT])?)\s+)?"              # file code, e.g. P,G
    r"([A-Za-z][A-Za-z0-9_]*(?:_ [A-Za-z0-9_]+)?)"  # name ("F_MM_ PLAC" has a typo space)
    r"(?:\s+(.*))?$"
)
MISSING_WORDS = re.compile(r"unknown|not stated|not classifiable", re.I)


def guide_text(cohort: int) -> list[str]:
    out = subprocess.run(["pdftotext", "-layout", str(GUIDES[cohort]), "-"],
                         check=True, capture_output=True, text=True).stdout
    return out.splitlines()


def parse_layout(cohort: int) -> list[dict]:
    """Return the main (U.S. file) layout rows: name, start, end, public, description, codes, missing."""
    lines = guide_text(cohort)
    begin = next(i for i, l in enumerate(lines) if re.match(r"^Position\s+Len", l))
    rows, cur, last_start = [], None, 0
    for line in lines[begin:]:
        m = ROW.match(line)
        # Indented rows are real only for fillers or public fields; other
        # indented matches are code lines such as "126   0   False".
        if m and m.group(1) and not (m.group(5).upper().startswith("FILLER") or m.group(4)):
            m = None
        if m:
            start = int(m.group(2))
            if start < last_start - 100:      # layout restarts: territory/geography part, stop
                break
            last_start = start
            cur = {
                "name": m.group(5).replace(" ", ""),
                "start": start,
                "end": int(m.group(3) or m.group(2)),
                "public": "P" in (m.group(4) or ""),
                "description": re.split(r"\s{2,}", (m.group(6) or "").strip())[0],
                "code_lines": [m.group(6) or ""],
            }
            rows.append(cur)
        elif cur is not None and line.strip():
            if line.lstrip().startswith(("Position", "Titles and codes")):
                if line.lstrip().startswith("Titles"):
                    break
                continue
            cur["code_lines"].append(line.strip())
    # Drop section headers such as "313-338 Risk Factors": no file code and
    # their range contains the next row's start.
    clean = []
    for i, r in enumerate(rows):
        nxt = rows[i + 1]["start"] if i + 1 < len(rows) else None
        if not r["public"] and not r["name"].upper().startswith("FILLER") and nxt is not None and r["start"] <= nxt <= r["end"] and r["end"] > r["start"]:
            continue
        clean.append(r)
    for r in clean:
        text = " | ".join(r.pop("code_lines"))
        r["codes"] = re.sub(r"\s{2,}", " ", text)[:400]
        miss = set()
        for part in text.split("|"):
            m = re.search(r"(?:^|\s{2,})(\S{1,5})\s{2,}[^|]*$", part.strip())
            if MISSING_WORDS.search(part):
                tok = re.findall(r"(?:^|\s)([0-9UXY]{1,4}|Blank|blank)(?=\s{1,}[A-Za-z])", part)
                if tok:
                    miss.add(tok[-1].replace("blank", "Blank"))
        r["missing"] = ";".join(sorted(miss))
    return clean


def check_tiling(rows: list[dict], length: int) -> list[str]:
    """Rows (fields + fillers) must cover 1..length with no gap or overlap."""
    problems, pos, prev = [], 1, ""
    for r in sorted((r for r in rows if r["start"] <= length), key=lambda r: r["start"]):
        if r["start"] > pos:
            problems.append(f"gap {pos}-{r['start'] - 1} before {r['name']}")
        elif r["start"] < pos and not (r["name"].upper().startswith("FILLER") or prev.upper().startswith("FILLER")):
            problems.append(f"overlap at {r['start']} ({r['name']})")
        pos, prev = max(pos, r["end"] + 1), r["name"]
    if pos <= length:
        problems.append(f"gap {pos}-{length} at end")
    return problems
