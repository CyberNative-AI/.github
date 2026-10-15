set -e
cd /w/env
python -m venv py
. py/bin/activate
pip -q install --upgrade pip
for p in simple-icd-10-cm==1.5.0 cms-icd==0.3.1 icd10-coder==0.2.3 icdlookup==0.1.0 icdmap==0.1.1 icd-mappings==0.6.2 icdcodex==0.5.2 hccinfhir==0.4.0 autoicd==0.11.1; do pip -q install "$p" > "log-$p.txt" 2>&1 && echo "OK $p" || echo "FAIL $p"; done
pip freeze > py-freeze.txt
