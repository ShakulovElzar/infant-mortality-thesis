"""Profile one CDC/NVSS linked birth-cohort ZIP by streaming (no extraction).

Usage: python3 -I src/profile_cohorts.py data/cdc/2024PE2023CO.zip reports/profile/
Writes <cohort>.json with counts, join success and per-field missing/positive rates.
"""
import sys, re, json, zipfile, collections, time, pathlib

def yr(name):
    v = int(re.search(r'VS(\d+)LINK', name).group(1))
    return v + 2000 if v < 100 else v

zp, outdir = sys.argv[1], pathlib.Path(sys.argv[2])
cohort = int(re.search(r'PE(\d{4})CO', zp).group(1))
z = zipfile.ZipFile(zp)
names = z.namelist()
den = [n for n in names if 'DENPUB' in n and yr(n) == cohort][0]
nums = [n for n in names if 'NUMPUB' in n and yr(n) in (cohort, cohort + 1)]
f = lambda r, a, b: r[a-1:b].decode('latin-1')

deaths, num_len = {}, collections.Counter()
for name in nums:
    with z.open(name) as fh:
        for r in fh:
            num_len[len(r.rstrip(b'\r\n'))] += 1
            if f(r, 9, 12) != str(cohort) or int(f(r, 104, 104)) >= 4:
                continue
            deaths[(f(r, 365, 371), f(r, 372, 375))] = int(f(r, 1356, 1358))

# (label, start, end, missing codes, positive codes)
FIELDS = [
    ('MAGER', 75, 76, set(), set()),
    ('MEDUC', 124, 124, {'9'}, set()),
    ('DMAR', 120, 120, {' '}, set()),
    ('PRECARE', 224, 225, {'99'}, set()),
    ('CIG_0', 253, 254, {'99'}, set()),
    ('BMI', 283, 286, {'99.9', '    '}, set()),
    ('RF_PDIAB', 313, 313, {'U', ' '}, {'Y'}),
    ('RF_GDIAB', 314, 314, {'U', ' '}, {'Y'}),
    ('RF_PHYPE', 315, 315, {'U', ' '}, {'Y'}),
    ('RF_GHYPE', 316, 316, {'U', ' '}, {'Y'}),
    ('PAY', 435, 435, {'9', ' '}, set()),
    ('COMBGEST', 490, 491, {'99'}, set()),
    ('BRTHWGT', 512, 515, {'9999'}, set()),
    ('AB_NICU', 519, 519, {'U', ' '}, {'Y'}),
]
t = time.time()
n = res = matched = neo = 0
den_len = collections.Counter()
miss, pos = collections.Counter(), collections.Counter()
for r in z.open(den):
    n += 1
    if n <= 1000:
        den_len[len(r.rstrip(b'\r\n'))] += 1
    if int(f(r, 104, 104)) >= 4:
        continue
    res += 1
    k = (f(r, 365, 371), f(r, 372, 375))
    if k in deaths:
        matched += 1
        neo += deaths[k] < 28
    for lab, a, b, mc, pc in FIELDS:
        v = f(r, a, b)
        if v in mc: miss[lab] += 1
        if v in pc: pos[lab] += 1

out = {
    'cohort': cohort, 'zip': pathlib.Path(zp).name, 'denominator_member': den,
    'numerator_members': nums, 'denominator_record_lengths': dict(den_len),
    'numerator_record_lengths': dict(num_len), 'denominator_records': n,
    'us_resident_births': res, 'cohort_deaths_in_numerators': len(deaths),
    'deaths_matched_to_births': matched, 'unmatched_deaths': len(deaths) - matched,
    'neonatal_deaths_lt28d': neo, 'imr_per_1000': round(1000 * matched / res, 3),
    'missing_pct': {k: round(100 * miss[k] / res, 3) for k, *_ in FIELDS},
    'positive_pct': {k: round(100 * pos[k] / res, 3) for k, *_ in FIELDS if pos[k] or k.startswith(('RF_', 'AB_'))},
    'seconds': round(time.time() - t),
}
outdir.mkdir(parents=True, exist_ok=True)
(outdir / f'{cohort}.json').write_text(json.dumps(out, indent=2))
print(cohort, 'done', out['imr_per_1000'], out['unmatched_deaths'])
