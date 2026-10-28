"""Query a llama-server running Carbon-X with the carbon-dna skill's `ask` message, one frame row per request.
Resumable (skips ids already in the output), hash-logged, optional thermal pause (set CARBON_GPU to an nvidia-smi --id).
usage: run_carbon.py frame.jsonl out.jsonl PORT [--limit N] [--only-stratum PREFIX]"""
import hashlib, json, os, random, subprocess, sys, time, urllib.request
UUID = os.environ.get("CARBON_GPU", "0")
QUESTION = "variant differs from reference at one base. Is the change likely benign or pathogenic?"  # SKILL.md example
LEFT = 4096
frame_p, out_p, port = sys.argv[1], sys.argv[2], int(sys.argv[3])
limit = int(sys.argv[sys.argv.index("--limit") + 1]) if "--limit" in sys.argv else None
only = sys.argv[sys.argv.index("--only-stratum") + 1] if "--only-stratum" in sys.argv else None

def message(r):
    orient = ("minus strand; sequences shown in gene orientation" if r["oriented"] == "minus" else
              "plus strand; sequences shown in gene orientation" if r.get("strand") == "+" else "genomic plus strand")
    context = (f"Position {LEFT + 1} (1-based): {r['win_ref']}>{r['win_alt']}. Gene: {r['gene_symbol'] or 'unknown'}. "
               f"Coordinates: GRCh38 chr{r['chrom']}:{r['pos']} ({orient}).")
    parts = [context, QUESTION, f"reference: <dna>{r['ref_window']}</dna>", f"variant: <dna>{r['alt_window']}</dna>"]
    return "\n\n".join(parts)  # identical assembly to carbon.py ask()

def temp():
    try:
        return int(subprocess.run(["nvidia-smi", f"--id={UUID}", "--query-gpu=temperature.gpu", "--format=csv,noheader"],
                                  capture_output=True, text=True, timeout=20).stdout.strip())
    except Exception:
        return -1

def post(payload):
    req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions", json.dumps(payload).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as resp:
        return json.load(resp)

rows = [json.loads(l) for l in open(frame_p)]
rank = {"CTRL": -1, "M": 0, "STRICT": 1, "O": 2}
rng = random.Random(17301)
rng.shuffle(rows)
rows.sort(key=lambda r: rank[r["stratum"].split("|")[0]])  # stable: verdict cells (M) first, random order within
if only:
    rows = [r for r in rows if r["stratum"].startswith(only)]
done = set()
try:
    done = {json.loads(l)["id"] for l in open(out_p)}
except FileNotFoundError:
    pass
n = 0
with open(out_p, "a") as out:
    for r in rows:
        if r["id"] in done:
            continue
        if limit is not None and n >= limit:
            break
        t = temp()
        while t >= 83:
            print(f"thermal pause at {t} C", flush=True)
            time.sleep(30)
            t = temp()
            if t < 72:
                break
        content = message(r)
        seed = int(hashlib.sha256(r["id"].encode()).hexdigest(), 16) % (2**31)
        payload = {"model": "carbon-x", "messages": [{"role": "user", "content": content}], "max_tokens": 4096,
                   "chat_template_kwargs": {"enable_thinking": False}, "seed": seed}
        t0 = time.time()
        try:
            resp = post(payload)
            ch = resp["choices"][0]
            rec = {"id": r["id"], "stratum": r["stratum"], "answer": ch["message"]["content"],
                   "finish_reason": ch["finish_reason"], "usage": resp.get("usage"), "error": None}
        except Exception as e:
            rec = {"id": r["id"], "stratum": r["stratum"], "answer": None, "finish_reason": None, "usage": None,
                   "error": repr(e)[:500]}
        rec.update(prompt_sha256=hashlib.sha256(content.encode()).hexdigest(), seed=seed,
                   seconds=round(time.time() - t0, 2), temp_before=t, ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        out.write(json.dumps(rec, sort_keys=True) + "\n")
        out.flush()
        n += 1
        print(f"{n} {r['id']} {r['stratum']} {rec['finish_reason']} {rec['seconds']}s T={t}", flush=True)
print("CLIENT_DONE", n, flush=True)
