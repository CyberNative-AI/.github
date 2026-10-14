import os, sys, json, torch
from pathlib import Path
out={"torch":torch.__version__}
for n in ["tar2pickle.tar","add_extension.pkl","inverted_registry.pkl"]:
    r,w=os.pipe(); s=os.dup(1); os.dup2(w,1)
    try:
        try: torch.load(Path("/pocs")/n); res="LOADED"
        except Exception as e: res=f"{type(e).__name__}: {str(e)[:300]}"
    finally:
        sys.stdout.flush(); os.dup2(s,1); os.close(w)
    cap=os.read(r,65536).decode(errors="replace"); os.close(r)
    out[n]={"result":res,"stdout":cap,"payload_ran":"Yippie" in cap}
print(json.dumps(out,indent=1))
