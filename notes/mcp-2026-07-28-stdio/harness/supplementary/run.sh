python3 - <<'PY'
import json,subprocess
cfg=json.load(open('/supp/config-supp.json'))
for s,v in sorted(cfg['servers'].items()):
    subprocess.run(['python3','/src/probe_era.py','/out/probe-%s.json'%s,'--']+v['cmd'])
PY
python3 /src/run_matrix.py /supp/config-supp.json /out --tag supp
