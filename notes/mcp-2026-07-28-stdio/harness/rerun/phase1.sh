set -u
cd /src
python3 - <<'PY'
import json,subprocess
cfg=json.load(open('/cfg/CONFIG.json'))
for s,v in sorted(cfg['servers'].items()):
    subprocess.run(['python3','/src/probe_era.py','/out/probes/%s.json'%s,'--']+v['cmd'],check=False)
PY
FAKES=$(python3 -c "import json;print(','.join(s for s,v in json.load(open('/cfg/CONFIG.json'))['servers'].items() if s=='fake-legacy_32602'))")
python3 /src/run_matrix.py /cfg/CONFIG.json /out --servers fake-legacy_32602 --tag classify
python3 /src/analyze.py --classify /cfg/CONFIG.json /out
