# Runtime: OS tools only. Python venvs live in a host directory mounted at /v (built by setup-venvs.sh), read-only at run time.
FROM python@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f
RUN apt-get update && apt-get install -y --no-install-recommends \
      tesseract-ocr tesseract-ocr-eng poppler-utils libgl1 libglib2.0-0 \
  && rm -rf /var/lib/apt/lists/*
RUN tesseract --version > /opt/tesseract-version.txt 2>&1; pdftotext -v > /opt/poppler-version.txt 2>&1; true
