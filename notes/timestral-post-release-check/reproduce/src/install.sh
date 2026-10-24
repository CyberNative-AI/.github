#!/bin/sh
# Installs the pinned model stack into /opt/env (bulk bind) and downloads pinned weights into /opt/hf.
set -eu
python -m venv /opt/env/venv
P=/opt/env/venv/bin/pip
$P install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.8.0
$P install --no-cache-dir "timestral @ https://github.com/mistralai/timestral/archive/a534bdbd244d64f3d9d743f46c7bf6fc330ed4ff.tar.gz" \
  chronos-forecasting==2.3.2 "timesfm[torch]==3.0.2" statsforecast==2.1.1 pandas==2.3.3
$P freeze > /opt/env/freeze.txt
HF_HOME=/opt/hf /opt/env/venv/bin/python - <<'PY'
from huggingface_hub import snapshot_download
pins = {
 "mistralai/Timestral-5M": "bdd20cfc15a3fea0e4cb5ccef37f8d3ca7aa335f",
 "mistralai/Timestral-28M": "180698bbf5a50dda3516aa6419798437fb03a430",
 "mistralai/Timestral-209M": "9874d252ab0aae16f7f7c999f98f98d6ad7d8365",
 "amazon/chronos-2": "29ec3766d36d6f73f0696f85560a422f50e8498c",
 "autogluon/chronos-2-small": "ddec01313e50b6bc58ebaa92ede81bc24a3d9f9a",
 "google/timesfm-2.5-200m-pytorch": "1d952420fba87f3c6dee4f240de0f1a0fbc790e3",
}
import json
out = {}
for r, rev in pins.items():
    p = snapshot_download(r, revision=rev)
    out[r] = p
print(json.dumps(out, indent=1))
open("/opt/hf/paths.json", "w").write(json.dumps(out, indent=1))
PY
