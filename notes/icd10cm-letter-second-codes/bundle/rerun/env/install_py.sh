set -e
python -m venv /w/envs/py
/w/envs/py/bin/pip install --no-input simple-icd-10-cm==1.5.0 icdlookup==0.1.0 cms-icd==0.3.1 icd10-coder==0.2.3
/w/envs/py/bin/pip freeze > /w/out/py-freeze.txt
python --version > /w/out/py-version.txt
