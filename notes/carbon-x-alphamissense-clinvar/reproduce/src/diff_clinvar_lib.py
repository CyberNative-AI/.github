"""Diff two ClinVar GRCh38 VCFs: SNVs whose first definitive (P/LP or B/LB, >=1 star) label appears in T1."""
import gzip, json, sys, collections
PATH = {"Pathogenic", "Likely_pathogenic", "Pathogenic/Likely_pathogenic"}
BEN = {"Benign", "Likely_benign", "Benign/Likely_benign"}
STAR = {"criteria_provided,_single_submitter", "criteria_provided,_multiple_submitters,_no_conflicts",
        "reviewed_by_expert_panel", "practice_guideline"}

def info(s):
    d = {}
    for kv in s.split(";"):
        k, _, v = kv.partition("=")
        d[k] = v
    return d

def load(path, keep_all):
    out = {}
    with gzip.open(path, "rt") as f:
        for line in f:
            if line[0] == "#":
                continue
            c = line.rstrip("\n").split("\t")
            d = info(c[7])
            rec = {"chrom": c[0], "pos": int(c[1]), "id": c[2], "ref": c[3], "alt": c[4],
                   "clnsig": d.get("CLNSIG", ""), "revstat": d.get("CLNREVSTAT", ""),
                   "vc": d.get("CLNVC", ""), "mc": d.get("MC", ""), "gene": d.get("GENEINFO", "")}
            if keep_all:
                out[c[2]] = rec["clnsig"]
            else:
                out[c[2]] = rec
    return out

