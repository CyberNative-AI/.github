"""Text-only gate analysis: max sliding-window cosine of each payload vs PhantomLint's default bad list,
using PhantomLint's own windowing (word_spans.extract_and_merge_spans) and encoder. Runs in /v/pl.
usage: python -I gate.py MANIFEST OUT.json
"""
import json, sys
from sentence_transformers import SentenceTransformer, util
from phantomlint.cli import DEFAULT_BADLIST, DEFAULT_THRESHOLD
from phantomlint.analyzers import filter_text
from phantomlint.word_spans import extract_and_merge_spans

man = json.load(open(sys.argv[1], encoding="utf-8"))
enc = SentenceTransformer("all-MiniLM-L6-v2")
known = enc.encode(DEFAULT_BADLIST, convert_to_tensor=True)
ws = [len(p.split()) for p in DEFAULT_BADLIST]
out = {"threshold": DEFAULT_THRESHOLD, "window": [min(ws), max(ws)], "payloads": {}}
for pid, text in man["payloads"].items():
    best = []
    def checker(spans):
        if not spans:
            return []
        texts = [filter_text(s.text) for s in spans]
        sims = util.cos_sim(enc.encode(texts, convert_to_tensor=True), known)
        for i, s in enumerate(spans):
            j = int(sims[i].argmax()); best.append((float(sims[i].max()), texts[i], DEFAULT_BADLIST[j]))
        return [s for i, s in enumerate(spans) if float(sims[i].max()) >= DEFAULT_THRESHOLD]
    extract_and_merge_spans(" ".join(text.split()), min(ws), max(ws), checker)
    best.sort(reverse=True)
    out["payloads"][pid] = {"max_cos": round(best[0][0], 4), "window": best[0][1], "nearest": best[0][2],
                            "passes_gate": best[0][0] >= DEFAULT_THRESHOLD, "top3": [[round(a, 4), b, c] for a, b, c in best[:3]]}
json.dump(out, open(sys.argv[2], "w", encoding="utf-8"), ensure_ascii=False, indent=1, sort_keys=True)
print(json.dumps({k: (v["max_cos"], v["passes_gate"], v["window"]) for k, v in out["payloads"].items()}, ensure_ascii=False))
