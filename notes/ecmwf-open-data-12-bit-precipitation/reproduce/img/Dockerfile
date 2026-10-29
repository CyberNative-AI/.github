FROM python:3.12-slim@sha256:05cda9777409a9c3ffddd94a4c476b79f0769a0b4857f0c7ed9226b6800b0d6f
COPY *.whl /w/
RUN pip install --no-cache-dir --no-index /w/*.whl && rm -rf /w && python -c "import eccodes,numpy;print(eccodes.codes_get_api_version(),numpy.__version__)"
USER 1000:1000
