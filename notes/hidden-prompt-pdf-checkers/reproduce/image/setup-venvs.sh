#!/bin/bash
# Build the four venvs into /v (a host directory). Run inside the hidpdf-os image with network, as the calling user.
set -euxo pipefail
export PIP_DISABLE_PIP_VERSION_CHECK=1 HF_HOME=/v/hf
[ -x /v/pl/bin/python ] || python -m venv /v/pl
/v/pl/bin/pip install torch==2.8.0 --index-url https://download.pytorch.org/whl/cpu
grep -v -E '^(torch|nvidia-|triton)' /src/phantom-lint/requirements-frozen.txt > ${TMPDIR:-/tmp}/req-pl.txt
/v/pl/bin/pip install -r ${TMPDIR:-/tmp}/req-pl.txt
rm -rf "${TMPDIR:-/tmp}/pl-src"; cp -r /src/phantom-lint "${TMPDIR:-/tmp}/pl-src"
/v/pl/bin/python -m spacy download en_core_web_sm
/v/pl/bin/pip install setuptools wheel
# setup.py CustomInstall calls bare `python -m spacy download`: put the venv first on PATH, no build isolation
PATH=/v/pl/bin:$PATH /v/pl/bin/pip install --no-deps --no-build-isolation "${TMPDIR:-/tmp}/pl-src"
/v/pl/bin/python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('all-MiniLM-L6-v2')"
{ [ -x /v/d1/bin/python ] || python -m venv /v/d1; } && /v/d1/bin/pip install pdf-injection-scanner==0.2.1
{ [ -x /v/d2/bin/python ] || python -m venv /v/d2; } && /v/d2/bin/pip install "pymupdf==1.26.3" "python-docx==1.1.2" "pikepdf==9.11.0" "numpy==2.2.6"
{ [ -x /v/ex/bin/python ] || python -m venv /v/ex; } && /v/ex/bin/pip install "pypdf==6.1.1" "pdfminer.six==20250506" "pymupdf==1.26.3"
for e in pl d1 d2 ex; do /v/$e/bin/pip freeze > /v/freeze-$e.txt; done
echo SETUP_OK
