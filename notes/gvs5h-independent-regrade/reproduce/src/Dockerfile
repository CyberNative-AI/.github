# Judge image: python 3.12 + the numpy/scipy versions pinned in LCB's uv.lock
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
RUN pip install --no-cache-dir numpy==2.2.5 scipy==1.15.2 && python -c "import numpy, scipy; print(numpy.__version__, scipy.__version__)"
