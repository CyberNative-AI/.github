# Indra OCR vs Tesseract on Wikisource scans. Built once, run with --network none.
FROM debian:trixie-slim
ARG LANGS="ben tam tel kan mal guj pan ori hin mar san tha heb ara fas hye ell rus ukr eng fra"
ARG TESSDATA_BEST_SHA=e12c65a915945e4c28e237a9b52bc4a8f39a0cec
RUN apt-get update && apt-get install -y --no-install-recommends \
      python3 python3-venv ca-certificates curl tesseract-ocr \
      $(for l in $LANGS; do echo tesseract-ocr-$l; done) \
 && rm -rf /var/lib/apt/lists/*
RUN mkdir -p /opt/tessdata_best && cd /opt/tessdata_best \
 && for l in $LANGS osd; do curl -fsSL -o $l.traineddata https://raw.githubusercontent.com/tesseract-ocr/tessdata_best/$TESSDATA_BEST_SHA/$l.traineddata; done \
 && sha256sum *.traineddata > /opt/tessdata_best/SHA256SUMS
RUN python3 -m venv /opt/venv && /opt/venv/bin/pip install --no-cache-dir "indra-ocr==1.1.2" \
 && /opt/venv/bin/pip freeze > /opt/pip-freeze.txt
ENV HF_HOME=/opt/hf INDRA_OCR_MODEL_DIR=/opt/indra-models
RUN /opt/venv/bin/python -c "from huggingface_hub import snapshot_download as s; s('datalab-to/indra-ocr', revision='a1283c4b42a273c09480ad50e71461daff50fcc7', local_dir='/opt/indra-models', allow_patterns=['*.onnx','*.npz','*.json','LICENSE'])" \
 && cd /opt/indra-models && find . -type f | sort | xargs sha256sum > /opt/indra-models.SHA256SUMS \
 && chmod -R a+rX /opt
RUN tesseract --version > /opt/tesseract-version.txt 2>&1; dpkg -l 'tesseract-ocr*' | awk '/^ii/{print $2,$3}' > /opt/tesseract-dpkg.txt
