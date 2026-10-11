#!/usr/bin/env python3
"""Date-dependent impact of the API losses (not part of the pre-set decision rule).

Usage: python3 -I impact.py LEGACY_DIR API_JSON ASOF(YYYYMMDD) OUT_JSON
A date on or after ASOF counts as unexpired.
"""
import csv, io, json, sys, collections, datetime
L, A, ASOF, OUT = sys.argv[1:5]
def rd(p):
    rows = list(csv.reader(io.StringIO(open(p, encoding='utf-8-sig', newline='').read()), delimiter='~', quoting=csv.QUOTE_NONE))
    return [dict(zip(rows[0], [c.strip() for c in r])) for r in rows[1:] if r]
mdy = lambda s: datetime.datetime.strptime(s, '%b %d, %Y').strftime('%Y%m%d')
K = lambda r: (r['Appl_Type'], r['Appl_No'], r['Product_No'])
exc, pat, prod = rd(L+'/exclusivity.txt'), rd(L+'/patent.txt'), rd(L+'/products.txt')
api = json.load(open(A))['results']
ax = {}
for rec in api:
    p = rec['products'][0]; k = (p['application_type'], p['application_number'], rec['product_number'])
    ax[k] = [(e['exclusivity_code'], e['exclusivity_expiration_date']) for e in rec.get('exclusivity', [])]
lx = collections.defaultdict(set)
for r in exc: lx[K(r)].add((r['Exclusivity_Code'], mdy(r['Exclusivity_Date'])))
out = {'asof': ASOF}
# E1: (product, code) where the API's date for the code is past but legacy has an unexpired date for it
e1 = set()
for k, s in lx.items():
    for (c, d) in s:
        if d >= ASOF:
            a = [x[1] for x in ax[k] if x[0] == c]
            if a and a[0] < ASOF: e1.add((k, c))
out['E1_product_code_pairs_api_date_past_legacy_unexpired'] = [list(k) + [c] for k, c in sorted(e1)]
out['E1_products'] = len({k for k, c in e1})
# E2: products with API exclusivity entries, none unexpired, while legacy has an unexpired one
e2 = {k for k, s in lx.items() if any(d >= ASOF for _, d in s) and ax[k] and not any(x[1] >= ASOF for x in ax[k])}
out['E2_products_no_unexpired_api_exclusivity'] = [list(k) for k in sorted(e2)]
# E3: products with no API exclusivity at all while legacy has an unexpired one
out['E3_products_legacy_unexpired_api_none'] = sum(1 for k, s in lx.items() if any(d >= ASOF for _, d in s) and not ax[k])
# E4: products whose latest API exclusivity date is earlier than the latest legacy date
e4 = {k for k, s in lx.items() if ax[k] and max(x[1] for x in ax[k]) < max(d for _, d in s)}
out['E4_products_api_latest_date_earlier'] = len(e4)
out['E4_of_which_legacy_latest_unexpired'] = sum(1 for k in e4 if max(d for _, d in lx[k]) >= ASOF)
# Patent use codes lost on unexpired patents
apatuc = {}
for rec in api:
    p = rec['products'][0]; k = (p['application_type'], p['application_number'], rec['product_number'])
    apatuc[k] = {(e['patent_number'], e.get('patent_use_code', '')) for e in rec.get('patents', [])}
miss = [r for r in pat if r['Patent_Use_Code'] and (r['Patent_No'], r['Patent_Use_Code']) not in apatuc[K(r)]]
live = [r for r in miss if mdy(r['Patent_Expire_Date_Text']) >= ASOF]
pk = {K(r) for r in live}
ms = {K(r): r for r in prod}
out['C1_lost_use_code_rows'] = len(miss)
out['C1_lost_on_unexpired_patents'] = len(live)
out['C1_products'] = len(pk)
out['C1_products_marketed'] = sum(1 for k in pk if ms[k]['Type'] != 'DISCN')
out['C1_applications'] = len({(k[0], k[1]) for k in pk})
out['C1_application_types'] = dict(collections.Counter(k[0] for k in {(k[0], k[1]) for k in pk}))
out['C1_distinct_use_codes'] = len({r['Patent_Use_Code'] for r in live})
json.dump(out, open(OUT, 'w'), indent=1)
print(json.dumps({k: (len(v) if isinstance(v, list) else v) for k, v in out.items()}, indent=1))
