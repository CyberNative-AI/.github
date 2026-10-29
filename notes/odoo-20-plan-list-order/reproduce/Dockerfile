# Odoo 20.0 Community (official image, pinned by digest) plus a PostgreSQL 16 server and libfaketime,
# so the whole run works offline in one container (docker run --network none).
FROM odoo@sha256:61e3c71b0503c5f658e604c3e340bede20b97d05f726179fa006eae50a32fd23
USER root
# The base image ships PGDG's postgresql-client-common but not the PGDG apt source, and Ubuntu's own
# postgresql-16 cannot install beside it. Add PGDG back with its signing key (checked by hash), install
# the server without creating a cluster, and build libfaketime 0.9.13 from its release tarball.
RUN set -eux; cd /tmp; \
    curl -fsSL -o pgdg.asc https://www.postgresql.org/media/keys/ACCC4CF8.asc; \
    curl -fsSL -o libfaketime.tar.gz https://github.com/wolfcw/libfaketime/archive/refs/tags/v0.9.13.tar.gz; \
    echo "0144068502a1eddd2a0280ede10ef607d1ec592ce819940991203941564e8e76  pgdg.asc" | sha256sum -c -; \
    echo "8e56deeb805682b025107e095f1d94a6ea677472f05824cd475f5c5e6e1a5ddf  libfaketime.tar.gz" | sha256sum -c -; \
    install -m 0644 pgdg.asc /usr/share/keyrings/pgdg.asc; \
    echo "deb [signed-by=/usr/share/keyrings/pgdg.asc] http://apt.postgresql.org/pub/repos/apt noble-pgdg main" > /etc/apt/sources.list.d/pgdg.list; \
    mkdir -p /etc/postgresql-common/createcluster.d; echo "create_main_cluster = false" > /etc/postgresql-common/createcluster.d/no-main.conf; \
    apt-get update; DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends postgresql-16 build-essential; \
    tar xzf libfaketime.tar.gz; cd libfaketime-0.9.13; \
    make FAKETIME_COMPILE_CFLAGS="-Wno-error -DFT_SEMAPHORE_BACKEND=FT_POSIX" PREFIX=/usr/local; make install PREFIX=/usr/local; \
    apt-get purge -y build-essential; apt-get autoremove -y; rm -rf /var/lib/apt/lists/* /tmp/*
