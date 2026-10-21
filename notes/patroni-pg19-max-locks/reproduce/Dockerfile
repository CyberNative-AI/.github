# Official postgres image (pass BASE by digest) + Patroni 4.1.5 from PyPI + etcd from Debian
ARG BASE
FROM ${BASE}
RUN apt-get update \
 && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3 python3-venv etcd-server etcd-client procps \
 && rm -rf /var/lib/apt/lists/*
RUN python3 -m venv /opt/patroni \
 && /opt/patroni/bin/pip install --no-cache-dir 'patroni[etcd3,psycopg3]==4.1.5' \
 && /opt/patroni/bin/pip freeze > /opt/patroni/freeze.txt \
 && (etcd --version; dpkg-query -W etcd-server python3) > /opt/patroni/versions.txt
ENV PATH=/opt/patroni/bin:$PATH
