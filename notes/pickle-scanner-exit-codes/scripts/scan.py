import subprocess, json, sys
from pathlib import Path
V="/w/venv/arm/bin/"; res={}
for p in sorted(Path("/pocs").iterdir()):
    r={}
    for tag,cmd in [("picklescan",["picklescan","-p",str(p)]),("picklescan_strict",["picklescan","--strict","-p",str(p)]),("modelscan",["modelscan","-p",str(p)]),("fickling",["fickling","--check-safety",str(p)])]:
        c=subprocess.run([V+cmd[0]]+cmd[1:],capture_output=True,text=True,timeout=120,cwd="/tmp")
        r[tag]={"rc":c.returncode,"out":(c.stdout+c.stderr)[-1500:]}
    res[p.name]=r
print(json.dumps(res,indent=1))
