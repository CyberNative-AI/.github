FROM debian:trixie
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends openssl nginx ca-certificates && rm -rf /var/lib/apt/lists/* \
    && rm -f /etc/nginx/sites-enabled/default
