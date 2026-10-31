"""Query a llama-server running Carbon-X, one (arm, frame row) per request. Resumable on (arm, id), append-only,
hash-logged, optional thermal pause (>= 83 C until < 72 C; set CARBON_GPU to an nvidia-smi --id).
usage: FRAME_DIR=<dir with frame.jsonl, controls_frame.jsonl> run_fvep.py PLAN out.jsonl PORT   (PLAN: ctrl | main)"""
import json, os, pathlib, random, subprocess, sys, time, urllib.request
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import fvep
UUID = os.environ.get("CARBON_GPU", "0")
R17301 = pathlib.Path(os.environ.get("FRAME_DIR", "."))
plan, out_p, port = sys.argv[1], sys.argv[2], int(sys.argv[3])

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

def tasks():
    if plan == "ctrl":
        rows = [json.loads(l) for l in open(R17301 / "controls_frame.jsonl")]
        order = [("F_plus", None), ("F_gene", "minus")]
    else:
        rows = [json.loads(l) for l in open(R17301 / "frame.jsonl")]
        rows = [r for r in rows if r["stratum"].split("|")[0] in ("M", "O")]
        order = [("F_plus", "M"), ("F_gene", "M"), ("F_plus", "O"), ("F_gene", "O"), ("C_reseed", "M")]
    rng = random.Random(18001)
    rng.shuffle(rows)
    out = []
    for arm, sel in order:
        for r in rows:
            st = r["stratum"].split("|")[0]
            if plan == "main" and st != sel:
                continue
            if arm == "F_gene" and r["oriented"] != "minus":
                continue  # same message and seed as F_plus; the scorer reuses the F_plus record
            out.append((arm, r))
    return out

done = set()
try:
    done = {(x["arm"], x["id"]) for x in map(json.loads, open(out_p)) if x["error"] is None}  # errors retried next job
except FileNotFoundError:
    pass
n = 0
with open(out_p, "a") as out:
    for arm, r in tasks():
        if (arm, r["id"]) in done:
            continue
        t = temp()
        while t >= 83:
            print(f"thermal pause at {t} C", flush=True)
            time.sleep(30)
            t = temp()
            if t < 72:
                break
        content = fvep.message(r, arm)
        sd = fvep.seed(r, arm)
        payload = {"model": "carbon-x", "messages": [{"role": "user", "content": content}], "max_tokens": 4096,
                   "chat_template_kwargs": {"enable_thinking": False}, "seed": sd}
        t0 = time.time()
        try:
            resp = post(payload)
            ch = resp["choices"][0]
            rec = {"answer": ch["message"]["content"], "finish_reason": ch["finish_reason"], "usage": resp.get("usage"),
                   "error": None}
        except Exception as e:
            rec = {"answer": None, "finish_reason": None, "usage": None, "error": repr(e)[:500]}
        rec.update(arm=arm, id=r["id"], stratum=r["stratum"], prompt_sha256=fvep.sha(content), seed=sd,
                   seconds=round(time.time() - t0, 2), temp_before=t, ts=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        out.write(json.dumps(rec, sort_keys=True) + "\n")
        out.flush()
        n += 1
        print(f"{n} {arm} {r['id']} {r['stratum']} {rec['finish_reason']} {rec['seconds']}s T={t}", flush=True)
ok = {(x["arm"], x["id"]) for x in map(json.loads, open(out_p)) if x["error"] is None}
pending = sum((arm, r["id"]) not in ok for arm, r in tasks())
print("CLIENT_DONE", n, f"pending={pending}", flush=True)  # pending > 0 = error records to retry
