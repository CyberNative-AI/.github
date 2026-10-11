"""Census comparison: openFDA Orange Book bulk JSON vs the same-vintage legacy Orange Book files.

Families: A strength/ingredient, B TE code/RLD/RS/marketing status/approval date,
C1 patent use codes, C2 patent flags/delist/submission date, D exclusivity.
RAW_DIR holds products.txt, patent.txt, exclusivity.txt and drug-orangebook-0001-of-0001.json
(both input zips extracted into one directory). Aborts if an input hash differs.

Usage: python3 -I compare.py RAW_DIR OUT_JSON [--control]
--control compares legacy against API-shaped records rebuilt losslessly from legacy (negative control).
Stdlib only, deterministic, no network.
"""
import csv
import datetime
import hashlib
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

EXPECTED = {
    "products.txt": "01881fcea81c3dee9df65b1fbe2eba55f2934b327707bccffdc2864cbe285239",
    "patent.txt": "f909ff63621887801ba1523977204f80912740f4ab97c2ffa89fc236f898fcff",
    "exclusivity.txt": "f8f26ff708031abae27b53d00fd1704fc8b75dc5f7f05c6e079009394a0972f1",
    "drug-orangebook-0001-of-0001.json": "8f457a7ec5c9b680a499145a91c194a4530dd63c6f410cecade19a5e3c1508d2",
}
STATUS = {"RX": "HUMAN PRESCRIPTION DRUG", "OTC": "HUMAN OTC DRUG", "DISCN": "DISCONTINUED"}
PRE82 = "APPROVED PRIOR TO JAN 1, 1982"


def norm(s):
    s = re.sub(r"\s+", " ", (s or "").upper()).strip()
    return re.sub(r"\s*;\s*", ";", s)


def split_top(s):
    """Split on ';' outside parentheses."""
    parts, depth, cur = [], 0, ""
    for ch in s:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        if ch == ";" and depth == 0:
            parts.append(cur)
            cur = ""
        else:
            cur += ch
    parts.append(cur)
    return [norm(p) for p in parts]


def ymd(s):
    s = (s or "").strip()
    if not s:
        return ""
    if re.fullmatch(r"\d{8}", s):
        return s
    return datetime.datetime.strptime(s, "%b %d, %Y").strftime("%Y%m%d")


def read_tilde(path):
    rows = list(csv.reader(path.open(encoding="latin-1", newline=""), delimiter="~"))
    return [dict(zip(rows[0], r)) for r in rows[1:]]


def load_legacy(raw):
    prods = {(r["Appl_Type"], r["Appl_No"], r["Product_No"]): r for r in read_tilde(raw / "products.txt")}
    pats = read_tilde(raw / "patent.txt")
    excl = read_tilde(raw / "exclusivity.txt")
    return prods, pats, excl


def load_api(raw):
    recs = json.load((raw / "drug-orangebook-0001-of-0001.json").open())["results"]
    out = {}
    for r in recs:
        p = r["products"][0]
        out[(p["application_type"], p["application_number"], r["product_number"])] = r
    return out


def build_lossless(prods, pats, excl):
    """API-shaped records rebuilt from legacy without loss (negative control)."""
    out = {}
    pat_by = defaultdict(list)
    for r in pats:
        e = {"patent_number": r["Patent_No"], "expiration_date": ymd(r["Patent_Expire_Date_Text"])}
        if r["Patent_Use_Code"]:
            e["patent_use_code"] = r["Patent_Use_Code"]
        if r["Submission_Date"]:
            e["patent_submission_date"] = ymd(r["Submission_Date"])
        for src, dst in (("Drug_Substance_Flag", "drug_substance_flag"), ("Drug_Product_Flag", "drug_product_flag"), ("Delist_Flag", "patent_delist_flag")):
            if r[src] == "Y":
                e[dst] = True
        pat_by[(r["Appl_Type"], r["Appl_No"], r["Product_No"])].append(e)
    ex_by = defaultdict(list)
    for r in excl:
        ex_by[(r["Appl_Type"], r["Appl_No"], r["Product_No"])].append(
            {"exclusivity_code": r["Exclusivity_Code"], "exclusivity_expiration_date": ymd(r["Exclusivity_Date"])})
    for k, r in prods.items():
        ings = [norm(x) for x in r["Ingredient"].split(";")]
        strs = split_top(r["Strength"])
        if len(strs) != len(ings):
            strs = [norm(r["Strength"])] + [""] * (len(ings) - 1)
        df, _, route = r["DF;Route"].partition(";")
        p = {"active_ingredients": [{"name": i, "strength": s} for i, s in zip(ings, strs)],
             "brand_name": r["Trade_Name"], "application_name": r["Applicant"], "application_type": k[0],
             "application_number": k[1], "reference_listed_drug": r["RLD"] == "Yes",
             "reference_standard": r["RS"] == "Yes", "marketing_status": STATUS[r["Type"]],
             "application_full_name": r["Applicant_Full_Name"], "dosage_form": df, "route": route}
        if r["TE_Code"]:
            p["therapeutic_equivalence_codes"] = [c.strip() for c in re.split(r"[;,]", r["TE_Code"]) if c.strip()]
        rec = {"product_number": k[2], "products": [p]}
        if norm(r["Approval_Date"]) == PRE82:
            rec["approved_prior_to_1982"] = True
        else:
            rec["approval_date"] = ymd(r["Approval_Date"])
        if k in pat_by:
            rec["patents"] = pat_by[k]
        if k in ex_by:
            rec["exclusivity"] = ex_by[k]
        out[k] = rec
    return out


def family_a(k, L, A):
    p = A["products"][0]
    ai = p["active_ingredients"]
    l_ing, a_ing = norm(L["Ingredient"]), norm(";".join(x.get("name", "") for x in ai))
    a_parts = [norm(x.get("strength", "")) for x in ai if norm(x.get("strength", ""))]
    l_str, a_str = norm(L["Strength"]), ";".join(a_parts)
    if l_ing == a_ing and l_str == a_str:
        return None
    l_parts = split_top(L["Strength"])
    if any(s.count("(") != s.count(")") for s in a_parts):
        sub = "A1_paren_truncated"
    elif len(a_parts) != len(l_parts):
        sub = "A2_component_count"
    elif sorted(a_parts) == sorted(l_parts):
        sub = "A3_order_or_pairing"
    else:
        sub = "A4_other"
    value_changing = any(x not in l_parts for x in a_parts) or (l_ing != a_ing and sorted(l_ing.split(";")) != sorted(a_ing.split(";")))
    return {"key": "~".join(k), "sub": sub, "value_changing": value_changing,
            "legacy_ingredient": L["Ingredient"], "api_ingredient": a_ing, "legacy_strength": L["Strength"], "api_strengths": [x.get("strength") for x in ai]}


def family_b(k, L, A):
    p = A["products"][0]
    diffs = {}
    l_te = sorted(c.strip() for c in re.split(r"[;,]", L["TE_Code"]) if c.strip())
    a_te = sorted(p.get("therapeutic_equivalence_codes", []))
    if l_te != a_te:
        diffs["te_code"] = [L["TE_Code"], p.get("therapeutic_equivalence_codes")]
    if (L["RLD"] == "Yes") != p["reference_listed_drug"]:
        diffs["rld"] = [L["RLD"], p["reference_listed_drug"]]
    if (L["RS"] == "Yes") != p["reference_standard"]:
        diffs["rs"] = [L["RS"], p["reference_standard"]]
    if STATUS.get(L["Type"]) != p["marketing_status"]:
        diffs["marketing_status"] = [L["Type"], p["marketing_status"]]
    if norm(L["Approval_Date"]) == PRE82:
        ok = A.get("approved_prior_to_1982") is True and not A.get("approval_date")
    else:
        ok = ymd(L["Approval_Date"]) == A.get("approval_date") and not A.get("approved_prior_to_1982")
    if not ok:
        diffs["approval_date"] = [L["Approval_Date"], A.get("approval_date"), A.get("approved_prior_to_1982")]
    cosmetic = {}
    df, _, route = L["DF;Route"].partition(";")
    for name, lv, av in (("brand", L["Trade_Name"], p["brand_name"]), ("applicant", L["Applicant"], p["application_name"]),
                         ("applicant_full", L["Applicant_Full_Name"], p["application_full_name"]),
                         ("dosage_form", df, p["dosage_form"]), ("route", route, p["route"])):
        if norm(lv) != norm(av):
            cosmetic[name] = [lv, av]
    return diffs, cosmetic


def family_c(pats, api):
    leg_fact = defaultdict(set)  # (key, pno) -> {(use, expiry)}
    leg_attr = defaultdict(lambda: {"sub": False, "prod": False, "delist": False, "subdates": set()})
    rows = Counter()
    for r in pats:
        k = (r["Appl_Type"], r["Appl_No"], r["Product_No"])
        kp = (k, r["Patent_No"])
        rows[tuple(r.values())] += 1
        leg_fact[kp].add((r["Patent_Use_Code"], ymd(r["Patent_Expire_Date_Text"])))
        a = leg_attr[kp]
        a["sub"] |= r["Drug_Substance_Flag"] == "Y"
        a["prod"] |= r["Drug_Product_Flag"] == "Y"
        a["delist"] |= r["Delist_Flag"] == "Y"
        if r["Submission_Date"]:
            a["subdates"].add(ymd(r["Submission_Date"]))
    api_fact = defaultdict(set)
    api_attr = defaultdict(lambda: {"sub": False, "prod": False, "delist": False, "subdates": set()})
    for k, rec in api.items():
        for e in rec.get("patents", []):
            kp = (k, e["patent_number"])
            api_fact[kp].add((e.get("patent_use_code", "") or "", e.get("expiration_date", "")))
            a = api_attr[kp]
            a["sub"] |= e.get("drug_substance_flag") is True
            a["prod"] |= e.get("drug_product_flag") is True
            a["delist"] |= e.get("patent_delist_flag") is True
            if e.get("patent_submission_date"):
                a["subdates"].add(e["patent_submission_date"])
    c1_units, c1_miss = 0, []
    for kp, facts in leg_fact.items():
        for use, exp in sorted(facts):
            c1_units += 1
            if kp not in api_fact:
                reason = "patent_missing"
            elif (use, exp) in api_fact[kp]:
                continue
            elif use not in {u for u, _ in api_fact[kp]}:
                reason = "use_code_missing"
            else:
                reason = "expiry_differs"
            c1_miss.append({"key": "~".join(kp[0]), "patent": kp[1], "use": use, "expiry": exp, "reason": reason,
                            "api": sorted(api_fact.get(kp, set()))})
    c2_miss = []
    for kp, la in leg_attr.items():
        if kp not in api_attr:
            c2_miss.append({"key": "~".join(kp[0]), "patent": kp[1], "fields": ["patent_missing"]})
            continue
        aa = api_attr[kp]
        bad = [f for f in ("sub", "prod", "delist", "subdates") if la[f] != aa[f]]
        if bad:
            c2_miss.append({"key": "~".join(kp[0]), "patent": kp[1], "fields": bad,
                            "legacy": {f: sorted(la[f]) if f == "subdates" else la[f] for f in bad},
                            "api": {f: sorted(aa[f]) if f == "subdates" else aa[f] for f in bad}})
    api_only = [{"key": "~".join(kp[0]), "patent": kp[1], "use": u, "expiry": e}
                for kp, facts in api_fact.items() for u, e in sorted(facts) if (u, e) not in leg_fact.get(kp, set())]
    return {"C1_units": c1_units, "C1_mismatch": c1_miss, "C2_units": len(leg_attr), "C2_mismatch": c2_miss,
            "api_only_facts": api_only, "legacy_patent_rows": len(pats),
            "legacy_exact_duplicate_rows": sum(v - 1 for v in rows.values() if v > 1)}


def family_d(excl, api):
    leg = Counter(((r["Appl_Type"], r["Appl_No"], r["Product_No"]), r["Exclusivity_Code"], ymd(r["Exclusivity_Date"])) for r in excl)
    apis = Counter((k, e.get("exclusivity_code"), e.get("exclusivity_expiration_date")) for k, rec in api.items() for e in rec.get("exclusivity", []))
    miss = [{"key": "~".join(k), "code": c, "date": d} for (k, c, d) in leg if (k, c, d) not in apis]
    extra = [{"key": "~".join(k), "code": c, "date": d} for (k, c, d) in apis if (k, c, d) not in leg]
    return {"D_units": len(excl), "D_distinct": len(leg), "D_mismatch": miss, "api_only": extra}


def main():
    raw, out = Path(sys.argv[1]), Path(sys.argv[2])
    control = "--control" in sys.argv
    for name, h in EXPECTED.items():
        got = hashlib.sha256((raw / name).read_bytes()).hexdigest()
        if got != h:
            sys.exit(f"ABORT: {name} sha256 {got} != frozen {h}")
    prods, pats, excl = load_legacy(raw)
    api = build_lossless(prods, pats, excl) if control else load_api(raw)
    lk, ak = set(prods), set(api)
    res = {"mode": "control" if control else "main", "n_products": len(prods), "only_legacy": len(lk - ak), "only_api": len(ak - lk)}
    a_miss, b_miss, cos = [], [], Counter()
    b_field = Counter()
    for k in sorted(lk & ak):
        m = family_a(k, prods[k], api[k])
        if m:
            a_miss.append(m)
        d, c = family_b(k, prods[k], api[k])
        if d:
            b_miss.append({"key": "~".join(k), "diffs": d})
            b_field.update(d.keys())
        cos.update(c.keys())
    res["A"] = {"units": len(lk & ak), "mismatch": len(a_miss), "rate": len(a_miss) / len(lk & ak),
                "value_changing": sum(m["value_changing"] for m in a_miss), "by_sub": Counter(m["sub"] for m in a_miss), "rows": a_miss}
    res["B"] = {"units": len(lk & ak), "mismatch": len(b_miss), "rate": len(b_miss) / len(lk & ak), "by_field": b_field, "rows": b_miss,
                "cosmetic_by_field": cos}
    c = family_c(pats, api)
    c["C1_rate"] = len(c["C1_mismatch"]) / c["C1_units"]
    c["C1_by_reason"] = Counter(m["reason"] for m in c["C1_mismatch"])
    c["C2_rate"] = len(c["C2_mismatch"]) / c["C2_units"]
    c["C2_by_field"] = Counter(f for m in c["C2_mismatch"] for f in m["fields"])
    res["C"] = c
    d = family_d(excl, api)
    d["D_rate"] = len(d["D_mismatch"]) / d["D_distinct"]
    res["D"] = d
    pos = {k: any(m["key"] == k for m in a_miss) for k in ("N~020971~001", "N~020971~002", "N~220641~001")}
    res["positive_control"] = pos
    out.write_text(json.dumps(res, indent=1, sort_keys=True, default=lambda o: sorted(o) if isinstance(o, set) else o) + "\n")
    summary = {"mode": res["mode"], "only_legacy": res["only_legacy"], "only_api": res["only_api"],
               "A": [res["A"]["mismatch"], round(res["A"]["rate"], 5), res["A"]["value_changing"], dict(res["A"]["by_sub"])],
               "B": [res["B"]["mismatch"], round(res["B"]["rate"], 5), dict(b_field)], "B_cosmetic": dict(cos),
               "C1": [len(c["C1_mismatch"]), c["C1_units"], round(c["C1_rate"], 5), dict(c["C1_by_reason"])],
               "C2": [len(c["C2_mismatch"]), c["C2_units"], round(c["C2_rate"], 5), dict(c["C2_by_field"])],
               "C_api_only": len(c["api_only_facts"]), "C_legacy_dup_rows": c["legacy_exact_duplicate_rows"],
               "D": [len(d["D_mismatch"]), d["D_distinct"], round(d["D_rate"], 5)], "D_api_only": len(d["api_only"]), "positive": pos}
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
