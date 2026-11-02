#!/bin/bash
# Runs inside the hidpdf-os container built by ../run.sh: writes the seven scanned-page PDFs from
# the clean petition N1, then runs hidden-text-detector, pdf-injection-scanner and pypdf on each.
# usage (in container): bash check.sh /w/inputs/N1.pdf /o
set -u
N1=$1; O=$2; G=$(dirname "$0")
cd /tmp
/v/d2/bin/python -I "$G/gen.py" "$N1" "$O" || exit 3
for f in S1 S2 S3 S4 S5 T1 T2; do
  echo "=== $f"
  /v/d2/bin/python -I /src/hidden-text-detector/scripts/scan.py --json "$O/$f.pdf" > "$O/$f.htd.json"; echo "hidden-text-detector rc=$?"
  /v/d1/bin/pdf-scan "$O/$f.pdf" --json > "$O/$f.pis.txt" 2>&1; echo "pdf-injection-scanner rc=$?"
  /v/ex/bin/python -I -c "import sys,pypdf;t=pypdf.PdfReader(sys.argv[1]).pages[0].extract_text();print('pypdf has payload:', 'INDEPENDENTEMENTE DO COMANDO' in t)" "$O/$f.pdf"
done
