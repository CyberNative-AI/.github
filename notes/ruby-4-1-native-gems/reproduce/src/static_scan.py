"""Static predictor: word-boundary hits of identifiers removed between Ruby 4.0.7 and 4.1.0-preview1
public headers (data/removed.txt) in each native gem's C/C++ sources (read from data.tar.gz in memory)."""
import tarfile, io, re, json, pathlib, sys
GEMS = pathlib.Path("gems")
ids = [l.strip() for l in open("data/removed.txt") if l.strip()]
rx = re.compile(r"\b(" + "|".join(map(re.escape, ids)) + r")\b")
SRC = (".c", ".h", ".cc", ".cpp", ".cxx", ".hpp", ".hh", ".y", ".rl", ".inc")
out = []
for g in sorted(GEMS.glob("*.gem")):
    hits = {}; nsrc = 0; rust = False
    with tarfile.open(g) as t:
        data = tarfile.open(fileobj=io.BytesIO(t.extractfile("data.tar.gz").read()), mode="r:gz")
        for m in data.getmembers():
            if not m.isfile(): continue
            if m.name.endswith("Cargo.toml"): rust = True
            if not m.name.lower().endswith(SRC): continue
            # skip vendored third-party library trees that cannot include ruby.h
            nsrc += 1
            txt = data.extractfile(m).read().decode("utf-8", "replace")
            if "ruby" not in txt.lower(): continue
            for h in rx.findall(txt): hits.setdefault(h, set()).add(m.name)
    out.append({"gem": g.stem, "n_src": nsrc, "rust": rust, "hits": {k: sorted(v)[:5] for k, v in hits.items()}})
with open("data/static.jsonl", "w") as f:
    for r in out: f.write(json.dumps(r) + "\n")
print(sum(1 for r in out if r["hits"]), "of", len(out), "gems contain >=1 removed identifier")
