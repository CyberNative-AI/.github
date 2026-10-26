# Image: python 3.12 + geopandas/pyproj/shapely (VG250 x Zensus grid join) + pyarrow/pandas/scipy (pinned)
FROM python:3.12-slim@sha256:a6e34c598f2467ed0e9a8d349809fcd8b5c603269512df273a0bb1784edc11b1
RUN pip install --no-cache-dir geopandas==1.1.1 shapely==2.1.2 pyproj==3.7.2 pyogrio==0.11.1 pyarrow==21.0.0 pandas==2.3.3 numpy==2.3.4 scipy==1.16.3 && python -c "import geopandas, pyproj, pyarrow, scipy; print(geopandas.__version__, pyproj.__version__, pyarrow.__version__, scipy.__version__)"
