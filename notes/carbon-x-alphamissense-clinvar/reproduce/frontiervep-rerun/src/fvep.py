"""Rerun message builders. Imported by run_fvep.py, tokcheck.py and score_fvep.py (no side effects).

Arms (frame rows come from the first run's frame.jsonl and controls_frame.jsonl, unchanged):
- F_plus: FrontierVEP template, window on the hg38 plus strand. Plus-strand-gene rows use the first run's window as is
  (variant at 4097); minus-strand-gene rows use the reverse complement of the first run's gene-oriented window, so the
  variant sits at 8192 - 4097 + 1 = 4096 and the alleles are the VCF REF/ALT.
- F_gene: FrontierVEP template, the first run's gene-oriented window (variant at 4097, alleles in gene orientation).
  Identical message to F_plus for plus-strand rows.
- C_reseed: the first run's own message (carbon-dna skill `ask`), byte-identical, with a different per-request seed.
"""
import hashlib

LEFT = 4096
WIN = 8192
# Template quoted by the Carbon-X maintainer on HF Carbon-X discussion #6 (2026-10-29 14:54Z), verbatim apart from the
# three variable fields and the DNA placeholder line, which becomes one unbroken uppercase line (vepqa_claims.py
# parse_prompt reads the window as a single [ACGTN]{1000,} run). No trailing newline (the quote ends at "* pathogenic").
TEMPLATE = (
    "Given a human single-nucleotide variant and its surrounding reference DNA sequence, classify the variant as "
    "either benign or pathogenic.\n\n"
    "The variant is at position {pos} in the reference sequence, using 1-based indexing. At this position, the "
    "reference allele {ref} is changed to the alternate allele {alt}.\n\n"
    "Reference DNA sequence:\n\n"
    "{dna}\n\n"
    "Provide your final answer enclosed in XML tags exactly as:\n\n"
    "<answer>TYPE</answer>\n\n"
    "where TYPE is exactly one of:\n\n"
    "* benign\n"
    "* pathogenic"
)
QUESTION = "variant differs from reference at one base. Is the change likely benign or pathogenic?"  # first run
COMP = str.maketrans("ACGTN", "TGCAN")


def revcomp(s):
    return s.translate(COMP)[::-1]


def placement(r, arm):
    """Return (dna, 1-based position, ref, alt) for the FrontierVEP arms, with identity assertions."""
    s, pos, ref, alt = r["ref_window"], LEFT + 1, r["win_ref"], r["win_alt"]
    assert len(s) == WIN and s[pos - 1] == ref, r["id"]
    assert r["alt_window"] == s[: pos - 1] + alt + s[pos:], r["id"]
    if arm == "F_plus" and r["oriented"] == "minus":
        s, pos, ref, alt = revcomp(s), WIN - LEFT, ref.translate(COMP), alt.translate(COMP)
        assert s[pos - 1] == ref, r["id"]
    if arm == "F_plus" or r["oriented"] != "minus":
        assert (ref, alt) == (r["ref"], r["alt"]), r["id"]  # plus-strand window shows the VCF alleles
    assert set(s) <= set("ACGT"), r["id"]
    return s, pos, ref, alt


def frontier_message(r, arm, wrap=False):
    s, pos, ref, alt = placement(r, arm)
    dna = f"<dna>{s}</dna>" if wrap else s
    return TEMPLATE.format(pos=pos, ref=ref, alt=alt, dna=dna)


def original_message(r):
    """Verbatim copy of message() in ../src/run_carbon.py."""
    orient = ("minus strand; sequences shown in gene orientation" if r["oriented"] == "minus" else
              "plus strand; sequences shown in gene orientation" if r.get("strand") == "+" else "genomic plus strand")
    context = (f"Position {LEFT + 1} (1-based): {r['win_ref']}>{r['win_alt']}. Gene: {r['gene_symbol'] or 'unknown'}. "
               f"Coordinates: GRCh38 chr{r['chrom']}:{r['pos']} ({orient}).")
    parts = [context, QUESTION, f"reference: <dna>{r['ref_window']}</dna>", f"variant: <dna>{r['alt_window']}</dna>"]
    return "\n\n".join(parts)


def message(r, arm):
    return original_message(r) if arm == "C_reseed" else frontier_message(r, arm)


def seed(r, arm):
    """F arms reuse the first run's per-variant seed (only the message changes); C_reseed uses a new one."""
    key = r["id"] if arm != "C_reseed" else "reseed:" + r["id"]
    return int(hashlib.sha256(key.encode()).hexdigest(), 16) % (2**31)


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()
