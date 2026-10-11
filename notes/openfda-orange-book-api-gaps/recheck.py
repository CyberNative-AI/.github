#!/usr/bin/env python3
"""Second, separately written count of patent use codes (C1) and exclusivity (D).

Written without reading compare.py. Usage:
  python3 -I recheck.py LEGACY_DIR API_JSON OUT_JSON
LEGACY_DIR holds patent.txt, exclusivity.txt, products.txt (tilde-delimited, CRLF).
"""
import csv, json, sys, collections, datetime, io

legacy_dir, api_path, out_path = sys.argv[1:4]


def read_tilde(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        txt = f.read()
    rows = list(csv.reader(io.StringIO(txt), delimiter="~", quoting=csv.QUOTE_NONE))
    hdr = rows[0]
    out = []
    for r in rows[1:]:
        if not r:
            continue
        assert len(r) == len(hdr), (path, r)
        out.append(dict(zip(hdr, [c.strip() for c in r])))
    return out


def mdy(s):
    """'Aug 24, 2026' -> '20260824'"""
    return datetime.datetime.strptime(s, "%b %d, %Y").strftime("%Y%m%d")


def key(r):
    return (r["Appl_Type"], r["Appl_No"], r["Product_No"])


# ---------- legacy ----------
pat = read_tilde(f"{legacy_dir}/patent.txt")
exc = read_tilde(f"{legacy_dir}/exclusivity.txt")
prod = read_tilde(f"{legacy_dir}/products.txt")
leg_keys = {key(r) for r in prod}

# ---------- API ----------
api = json.load(open(api_path, encoding="utf-8"))["results"]
api_keys = set()
api_pat = collections.defaultdict(list)   # key -> list of (patent_number, expiry, use_code)
api_exc = collections.defaultdict(list)   # key -> list of (code, date)
for rec in api:
    p = rec["products"][0]
    k = (p["application_type"], p["application_number"], rec["product_number"])
    assert k not in api_keys
    api_keys.add(k)
    for e in rec.get("patents", []):
        api_pat[k].append((e["patent_number"], e.get("expiration_date", ""), e.get("patent_use_code", "")))
    for e in rec.get("exclusivity", []):
        api_exc[k].append((e["exclusivity_code"], e["exclusivity_expiration_date"]))

res = {"keys": {"legacy": len(leg_keys), "api": len(api_keys),
                "legacy_only": len(leg_keys - api_keys), "api_only": len(api_keys - leg_keys)}}

# ---------- C1 ----------
rows_total = len(pat)
facts = {}  # (key, patent, usecode) -> set of expiries
for r in pat:
    facts.setdefault((key(r), r["Patent_No"], r["Patent_Use_Code"]), set()).add(mdy(r["Patent_Expire_Date_Text"]))
c1 = {"legacy_rows": rows_total, "distinct_facts": len(facts),
      "facts_with_nonempty_use_code": sum(1 for f in facts if f[2]),
      "facts_with_empty_use_code": sum(1 for f in facts if not f[2])}

def present(k, pn, uc, exps, need_exp):
    for (apn, aexp, auc) in api_pat.get(k, []):
        if apn == pn and auc == uc and (not need_exp or aexp in exps):
            return True
    return False

miss_loose, miss_strict = [], []
for (k, pn, uc), exps in sorted(facts.items()):
    if not present(k, pn, uc, exps, False):
        miss_loose.append((k, pn, uc, sorted(exps)))
    if not present(k, pn, uc, exps, True):
        miss_strict.append((k, pn, uc, sorted(exps)))
c1["missing_patent_and_usecode_match"] = len(miss_loose)
c1["missing_patent_usecode_and_expiry_match"] = len(miss_strict)
c1["pct_loose"] = round(100 * len(miss_loose) / len(facts), 3)
c1["pct_strict"] = round(100 * len(miss_strict) / len(facts), 3)

# How is each loss classified? patent absent entirely vs patent present with other use code
cls = collections.Counter()
for (k, pn, uc, exps) in miss_strict:
    api_for_pn = [e for e in api_pat.get(k, []) if e[0] == pn]
    if not api_for_pn:
        cls["patent_absent"] += 1
    else:
        other = {e[2] for e in api_for_pn}
        if uc not in other:
            cls["patent_present_other_usecode"] += 1
        else:
            cls["patent_and_usecode_present_expiry_differs"] += 1
c1["strict_loss_classes"] = dict(cls)

# API entries per (key, patent): is it ever more than 1?
cnt = collections.Counter((k, e[0]) for k, es in api_pat.items() for e in es)
c1["api_entries"] = sum(cnt.values())
c1["api_entries_dup_key_patent"] = sum(1 for v in cnt.values() if v > 1)

# API-only entries (precision)
leg_pn = {(f[0], f[1]) for f in facts}
c1["api_entries_without_legacy_patent"] = sum(1 for (k, pn) in cnt if (k, pn) not in leg_pn)

# multi-code patents
by_pn = collections.defaultdict(list)
for r in pat:
    by_pn[(key(r), r["Patent_No"])].append(r["Patent_Use_Code"])
multi = {kp: v for kp, v in by_pn.items() if len(set(v)) > 1}
c1["patents_with_multiple_distinct_use_codes"] = len(multi)
last = first = other_pos = 0
for kp, codes in multi.items():
    a = [e[2] for e in api_pat.get(kp[0], []) if e[0] == kp[1]]
    if not a:
        continue
    if a[0] == codes[-1]:
        last += 1
    elif a[0] == codes[0]:
        first += 1
    else:
        other_pos += 1
c1["multi_code_kept_last_row"] = last
c1["multi_code_kept_first_row"] = first
c1["multi_code_kept_other"] = other_pos
# are all misses inside multi-code patents?
c1["misses_in_multicode_patents"] = sum(1 for m in miss_strict if (m[0], m[1]) in multi)
res["C1"] = c1

# ---------- D ----------
exc_rows = len(exc)
dfacts = {}
for r in exc:
    dfacts.setdefault((key(r), r["Exclusivity_Code"], mdy(r["Exclusivity_Date"])), 0)
    dfacts[(key(r), r["Exclusivity_Code"], mdy(r["Exclusivity_Date"]))] += 1
miss_d = [f for f in sorted(dfacts) if (f[1], f[2]) not in api_exc.get(f[0], [])]
d = {"legacy_rows": exc_rows, "distinct_facts": len(dfacts), "missing": len(miss_d),
     "pct": round(100 * len(miss_d) / len(dfacts), 3),
     "missing_by_code": dict(collections.Counter(f[1] for f in miss_d)),
     "api_entries": sum(len(v) for v in api_exc.values())}
# API entries without a legacy counterpart
leg_set = set(dfacts)
d["api_only_entries"] = sum(1 for k, es in api_exc.items() for e in es if (k, e[0], e[1]) not in leg_set)
# collapse structure: (key, code) with >1 distinct dates in legacy
bykc = collections.defaultdict(set)
for (k, c, dt) in dfacts:
    bykc[(k, c)].add(dt)
multi_kc = {kc for kc, v in bykc.items() if len(v) > 1}
d["key_code_pairs_with_multiple_dates"] = len(multi_kc)
d["misses_in_multidate_pairs"] = sum(1 for f in miss_d if (f[0], f[1]) in multi_kc)
d["misses_where_code_missing_entirely"] = sum(1 for f in miss_d if not any(e[0] == f[1] for e in api_exc.get(f[0], [])))
apicodes_dup = sum(1 for k, es in api_exc.items() for c, n in collections.Counter(e[0] for e in es).items() if n > 1)
d["api_key_code_pairs_with_multiple_entries"] = apicodes_dup
# which date does the API keep? earliest/latest
kept_early = kept_late = kept_mid = 0
for (k, c) in multi_kc:
    a = [e[1] for e in api_exc.get(k, []) if e[0] == c]
    if not a:
        continue
    s = sorted(bykc[(k, c)])
    if a[0] == s[0]:
        kept_early += 1
    elif a[0] == s[-1]:
        kept_late += 1
    else:
        kept_mid += 1
d["multidate_kept_earliest"] = kept_early
d["multidate_kept_latest"] = kept_late
d["multidate_kept_other"] = kept_mid
res["D"] = d

res["_miss_C1"] = [{"key": list(k), "patent": pn, "use_code": uc, "expiry": e} for (k, pn, uc, e) in miss_strict]
res["_miss_D"] = [{"key": list(f[0]), "code": f[1], "date": f[2]} for f in miss_d]
json.dump(res, open(out_path, "w"), indent=1)
print(json.dumps({k: v for k, v in res.items() if not k.startswith("_")}, indent=1))
