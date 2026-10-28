"""Build the frozen prompt frame: sample variants, extract 8,192-bp hg38 windows, join AlphaMissense.
usage: build_frame.py new_labels.jsonl hg38.fa.gz AlphaMissense_hg38.tsv.gz MANE.summary.txt.gz T0.vcf.gz out_frame.jsonl out_controls.jsonl
Windows are shown in gene (MANE Select) orientation, variant at 1-based window position 4097 on both strands."""
import gzip, json, random, sys, collections, hashlib
sys.path.insert(0, __file__.rsplit("/", 1)[0])
from diff_clinvar_lib import load, PATH, BEN
SEED = 17301
W, LEFT = 8192, 4096          # variant at 1-based window position LEFT+1 = 4097
OTHER = {"synonymous_variant", "intron_variant", "nonsense", "splice_donor_variant", "splice_acceptor_variant",
         "5_prime_UTR_variant", "3_prime_UTR_variant", "initiator_codon_variant", "stop_lost",
         "non-coding_transcript_variant"}
CHROMS = [str(i) for i in range(1, 23)] + ["X", "Y"]
GENE_CAP = 5
rows = [json.loads(l) for l in open(sys.argv[1])]
COMP = str.maketrans("ACGT", "TGCA")
strand = {}
with gzip.open(sys.argv[4], "rt") as f:
    for line in f:
        c = line.rstrip("\n").split("\t")
        if c[0].startswith("GeneID:") and c[9] == "MANE Select":
            strand[c[0].split(":")[1]] = c[13]
def gene_strand(r):
    if not r["gene"]:
        return None
    gid = r["gene"].split("|")[0].split(":")[1]
    return strand.get(gid)
# positive-control pool: expert-panel missense labels already definitive at T0 (so outside the frame)
t0 = load(sys.argv[5], False)
ctrl_pool = []
for r in t0.values():
    if r["vc"] == "single_nucleotide_variant" and r["revstat"] == "reviewed_by_expert_panel" and len(r["ref"]) == 1 and len(r["alt"]) == 1:
        terms = sorted({x.split("|")[1] for x in r["mc"].split(",") if "|" in x})
        lab = "pathogenic" if r["clnsig"] in PATH else "benign" if r["clnsig"] in BEN else None
        if lab and terms == ["missense_variant"] and r["chrom"] in [str(i) for i in range(1, 23)] + ["X", "Y"]:
            r.update(label=lab, mc_terms=terms, first_window_end="T0", gene_symbol=r["gene"].split(":")[0], set="CTRL", group="CTRL")
            ctrl_pool.append(r)
def group(r):
    return "W1019" if r["first_window_end"] == "20261019" else "W1025" if r["first_window_end"] == "20261025" else "W0905_0928"
cand = []
for r in rows:
    if r["chrom"] not in CHROMS:
        continue
    t = r["mc_terms"]
    r["set"] = "M" if t == ["missense_variant"] else "O" if len(t) == 1 and t[0] in OTHER else None
    r["group"] = group(r)
    r["gene_symbol"] = r["gene"].split(":")[0] if r["gene"] else ""
    r["strand"] = gene_strand(r)
    if r["group"] == "W1025" or (r["set"] and r["strand"] in ("+", "-")):
        cand.append(r)
for r in ctrl_pool:
    r["strand"] = gene_strand(r)
cand += [r for r in ctrl_pool if r["strand"] in ("+", "-")]
need = {"chr" + c for c in {r["chrom"] for r in cand}}
seq, cur, buf = {}, None, []
with gzip.open(sys.argv[2], "rt") as f:
    for line in f:
        if line[0] == ">":
            if cur in need:
                seq[cur] = "".join(buf)
            cur, buf = line[1:].split()[0], []
        elif cur in need:
            buf.append(line.strip())
    if cur in need:
        seq[cur] = "".join(buf)
excl = collections.Counter()
ok = []
for r in cand:
    s = seq["chr" + r["chrom"]]
    p0 = r["pos"] - 1
    if s[p0].upper() != r["ref"]:
        excl["ref_mismatch"] += 1; continue
    minus = r["strand"] == "-"
    lo = p0 - (W - 1 - LEFT) if minus else p0 - LEFT
    win = s[lo: lo + W].upper()
    if len(win) != W or set(win) - set("ACGT"):
        excl["non_ACGT_or_edge"] += 1; continue
    i = p0 - lo
    alt_g = win[:i] + r["alt"] + win[i + 1:]
    if minus:
        win, alt_g = win.translate(COMP)[::-1], alt_g.translate(COMP)[::-1]
    assert win[LEFT] == (r["ref"].translate(COMP) if minus else r["ref"]) and sum(a != b for a, b in zip(win, alt_g)) == 1 and alt_g[LEFT] != win[LEFT]
    r["ref_window"], r["alt_window"] = win, alt_g
    r["win_ref"], r["win_alt"] = win[LEFT], alt_g[LEFT]
    r["oriented"] = "minus" if minus else "plus"
    ok.append(r)
keys = {(("chr" + r["chrom"]), r["pos"], r["ref"], r["alt"]) for r in ok if r["set"] in ("M", "CTRL") or r["group"] == "W1025"}
am = collections.defaultdict(list)
with gzip.open(sys.argv[3], "rt") as f:
    for line in f:
        if line[0] == "#":
            continue
        c = line.rstrip("\n").split("\t")
        k = (c[0], int(c[1]), c[2], c[3])
        if k in keys:
            am[k].append((float(c[8]), c[9], c[6]))
for r in ok:
    v = am.get(("chr" + r["chrom"], r["pos"], r["ref"], r["alt"]))
    if v:
        r["am_score"] = sum(x[0] for x in v) / len(v)
        r["am_classes"] = sorted({x[1] for x in v})
        r["am_rows"] = len(v)
rng = random.Random(SEED)
frame = []
quota = {("M", "W1019"): 75, ("M", "W0905_0928"): 75, ("O", "W1019"): 30, ("O", "W0905_0928"): 30}
for (st, g), q in quota.items():
    for lab in ("pathogenic", "benign"):
        pool = [r for r in ok if r["set"] == st and r["group"] == g and r["label"] == lab and (st != "M" or "am_score" in r)]
        pool.sort(key=lambda r: int(r["id"]))
        rng.shuffle(pool)
        per_gene, pick = collections.Counter(), []
        for r in pool:
            if per_gene[r["gene_symbol"]] >= GENE_CAP:
                continue
            per_gene[r["gene_symbol"]] += 1
            pick.append(r)
            if len(pick) == q:
                break
        excl[f"pool_{st}_{g}_{lab}"] = len(pool)
        for r in pick:
            r["stratum"] = f"{st}|{g}"
        frame += pick
frame += [dict(r, stratum="STRICT|W1025") for r in ok if r["group"] == "W1025"]
cp = sorted([r for r in ok if r["set"] == "CTRL"], key=lambda r: int(r["id"]))
rng2 = random.Random(SEED + 1)
rng2.shuffle(cp)
ctrl, seen = [], set()
for lab in ("pathogenic", "benign"):
    k = 0
    for r in cp:
        if r["label"] == lab and r["gene_symbol"] not in seen and k < 10:
            seen.add(r["gene_symbol"]); k += 1
            ctrl.append(dict(r, stratum="CTRL|T0"))
with open(sys.argv[7], "w") as f:
    for r in ctrl:
        f.write(json.dumps(r, sort_keys=True) + "\n")
excl["ctrl_pool"] = len(cp)
frame.sort(key=lambda r: (r["stratum"], int(r["id"])))
with open(sys.argv[6], "w") as f:
    for r in frame:
        f.write(json.dumps(r, sort_keys=True) + "\n")
print(json.dumps({"frame_n": len(frame), "by_stratum_label": collections.Counter(f"{r['stratum']}|{r['label']}" for r in frame),
                  "excl_and_pools": excl, "M_with_am_in_ok": sum(1 for r in ok if r['set'] == 'M' and 'am_score' in r),
                  "M_in_ok": sum(1 for r in ok if r['set'] == 'M')}, indent=1, default=dict))
