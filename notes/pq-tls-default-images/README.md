# 13 of 15 popular TLS server images already negotiate post-quantum key exchange. Pomerium and `kong:latest` do not

**Clarification, 2 November 2026.** An earlier version of this note quoted the paper's phrase "deliberate protocol
modernization" as if it described what operators intended, and answered it with "On a current image, PQ key exchange
takes no deliberate action." That reading was ours, not the paper's. In the paper (section 5.5.2), the phrase sums up a
comparison of TLS configurations: owner-managed domains with PQ key exchange had modestly stricter TLS settings than
owner-managed domains without it, for example less support for legacy protocol versions (10.5% vs. 11.9%) and
deprecated cipher suites (46.9% vs. 52.6%). The paper did not measure whether operators enabled PQ themselves. It also
reports the case this note tests, a server that supports PQ but does not choose it by default: in July 2025, 73 domains
advertised PQ support but negotiated classical groups by default, and by March 2026 two did. We reworded the two
sentences. The test and its results are unchanged.

At IMC 2026 (12–16 October), researchers from UNSW Sydney and Georgia Tech reported a gap in post-quantum TLS
([Mind the Gap: Policy vs Reality in Post-Quantum TLS Deployment](https://arxiv.org/abs/2607.29005)). In March 2026,
49.22% of their stable panel of 684,494 HTTPS domains negotiated hybrid post-quantum (PQ) key exchange, all of it
X25519MLKEM768. Almost all of it came through CDNs and managed hosting. More than 75% of provider-managed domains
supported it, against less than 10% of domains whose owners appear to run TLS themselves. Owner-managed domains
that did use PQ had modestly stricter TLS settings, which the authors sum up as "deliberate protocol modernization".

We tested the other side of that gap: what a self-hoster gets from the image. On 17 October 2026 we ran the
TLS web server and reverse proxy images with at least 250 million Docker Hub pulls at their current tag. We gave
each one a certificate and key and nothing else, then connected with an OpenSSL 3.5.7 client.

**13 of 15 negotiated X25519MLKEM768 with no configuration.** Two did not:

- **`pomerium/pomerium:latest` (Pomerium 0.33.4)** negotiated X25519. Its version output names Envoy build
  `20261001211751-8b998d0f6ff3`, which is the
  [commit that updated Pomerium's Envoy build to v1.38.5](https://github.com/pomerium/envoy-custom/commit/8b998d0f6ff30a8243296168125a783c35772141).
  Envoy added X25519MLKEM768 to its default curves only in v1.40.0
  ([envoy pull request 47225](https://github.com/envoyproxy/envoy/pull/47225), merged 17 September 2026), and
  plain Envoy v1.40.0 negotiated it in our test. Plain Envoy v1.38.5 with the same minimal setup negotiated X25519,
  and X25519MLKEM768 once we added one setting, `ecdh_curves: [X25519MLKEM768, X25519]`. That fits Pomerium
  inheriting Envoy 1.38's default, but does not prove it: Pomerium ships its own Envoy build.
- **`kong:latest`, the Docker Official Image that Kong maintains (Kong 3.9.4)**, negotiated X25519. Its nginx is built with
  OpenSSL 3.2.3, and OpenSSL added ML-KEM only in 3.5. Setting the group with
  `KONG_NGINX_PROXY_SSL_ECDH_CURVE=X25519MLKEM768:X25519` stops Kong from starting:
  `group 'X25519MLKEM768' cannot be set`. No setting can fix this image.
  Kong's other image, `kong/kong-gateway:latest` (Kong Gateway 3.16.0.1, OpenSSL 3.5.8), negotiated X25519MLKEM768.

| image (tag `latest` unless shown) | Docker Hub pulls | TLS library | default client gets |
|---|---|---|---|
| `nginx` | 13.5B | OpenSSL 3.5.7 | X25519MLKEM768 |
| `nginx:alpine` | (same repository) | OpenSSL 3.5.9 | X25519MLKEM768 |
| `envoyproxy/envoy:v1.40.0` (no `latest` tag) | 5.8B | BoringSSL | X25519MLKEM768 |
| `httpd` | 4.7B | OpenSSL 3.5.7 | X25519MLKEM768 |
| `traefik` | 3.6B | Go 1.26.9 | X25519MLKEM768 |
| **`pomerium/pomerium`** | 1.6B | **embedded Envoy v1.38.5** | **X25519** |
| `nginxinc/nginx-unprivileged` | 1.3B | OpenSSL 3.5.7 | X25519MLKEM768 |
| `haproxy` | 1.1B | OpenSSL 3.5.7 | X25519MLKEM768 |
| `kong/kong-gateway` | 0.93B | OpenSSL 3.5.8 | X25519MLKEM768 |
| `tomcat` (via tomcat-native) | 0.83B | OpenSSL 3.5.5 | X25519MLKEM768 |
| `caddy` | 0.75B | Go (Caddy 2.11.7) | X25519MLKEM768 |
| `jwilder/nginx-proxy` (its bundled TLS policy lines) | 0.55B | OpenSSL 3.5.7 | X25519MLKEM768 |
| `bitnami/nginx` | 0.44B | OpenSSL 3.5.9 | X25519MLKEM768 |
| **`kong`** (Docker Official) | 0.36B | **OpenSSL 3.2.3** | **X25519** |
| `jc21/nginx-proxy-manager` (its bundled TLS include) | 0.29B | OpenSSL 3.5.7 | X25519MLKEM768 |

Each handshake ran three times with the same result. A client offering only X25519MLKEM768 completed the handshake
with all 13 and failed with both exceptions. Pull counts were read on 17 October 2026. Two images above the pull
threshold were left out because they cannot run alone: `istio/proxyv2` (needs istiod; Envoy is covered above) and
`nginx/nginx-ingress` (needs a Kubernetes API).

## What this suggests about the gap

On a current image, PQ key exchange needs no setting. Low owner-managed adoption may therefore track
servers running older images, distribution packages or configurations that pin a curve list, more than a default
that owners have to change. That is a hypothesis. We did not measure deployed servers, older tags or distribution
packages.

Two facts point the same way. OpenSSL-based servers need OpenSSL 3.5 or newer: Debian 13 ships 3.5, while
[Debian 12](https://packages.debian.org/bookworm/openssl) and
[Ubuntu 24.04 LTS](https://packages.ubuntu.com/noble/openssl) ship 3.0. And an explicit curve list turns PQ off: our
negative control was the working nginx setup plus one line, `ssl_ecdh_curve X25519;`, and it negotiated X25519
and refused the PQ-only client. A list in any server's config that does not name X25519MLKEM768 can do the same.

## Check your own server

With a client that has OpenSSL 3.5 or newer (`openssl version`):

```sh
openssl s_client -connect example.com:443 -groups X25519MLKEM768 </dev/null
```

`Negotiated TLS1.3 group: X25519MLKEM768` in the output means the server does hybrid PQ key exchange. A server
that cannot fails the handshake with `alert handshake failure`.

## Run it yourself

The test pulls 16 third-party server images and the Debian base image from Docker Hub and runs them. Use a disposable Linux x86_64 machine or
VM with Docker, no credentials and no private data. Pulling and building need network access; the servers and the
client run on an internal Docker network with no outside access. Run the commands from a clean directory holding
only this bundle. They write a throwaway test key and certificate to `certs/` and results to `out/`.

```sh
mkdir -p certs
openssl req -x509 -newkey ec -pkeyopt ec_paramgen_curve:P-256 -nodes -days 30 \
  -subj /CN=probe.test -addext "subjectAltName=DNS:probe.test,DNS:target" \
  -keyout certs/key.pem -out certs/cert.pem
cat certs/cert.pem certs/key.pem > certs/combined.pem
chmod -R a+rX certs conf   # several images run as non-root and must read the test key and configs
docker build -t pqprobe-client:1 -f client.Dockerfile .
tail -n +2 images.tsv | cut -f2 | xargs -n1 docker pull
python3 run.py             # or name units: python3 run.py CPLUS CMINUS U06 U14
python3 summarize.py out
```

[`run.py`](run.py) starts each image with only a certificate and key (configs in [`conf/`](conf/)), connects
three times with the client's default groups and three times offering only X25519MLKEM768, and saves every raw
`openssl s_client` output and container log under `out/`. [`summarize.py`](summarize.py) reads only those raw files.
Images are pinned by digest in [`images.tsv`](images.tsv), with the pull counts we read. The client image is
Debian trixie (OpenSSL 3.5.7 in our runs; [`client.Dockerfile`](client.Dockerfile)); its nginx serves the two controls:
`CPLUS` (minimal setup, must negotiate X25519MLKEM768) and `CMINUS` (plus `ssl_ecdh_curve X25519;`, must not).
`U14-FIX`, `E1385-DEF` and `E1385-ECDH` are the Kong and Envoy v1.38.5 checks described above; they are not in
the 15.

Our raw output is in [`results/run1/`](results/run1/) and [`results/run2/`](results/run2/), with
[`summarize.py`](summarize.py) output for each in [`results/`](results/). `run1` also holds each image's version
output (`versions.txt`), the source of the TLS library column. `run1` came from our first harness, which is not
included, and has no Kong setting check because that attempt left no log. `run.py` is the second harness with
paths, container names and digest pins adapted to this directory; the two test-only secrets in
[`conf/pomerium.yaml`](conf/pomerium.yaml) were replaced with other test-only values. We removed the
`docker-run.json` command files from both runs because they held local paths; `run.py` writes them again under
`out/`. [`SHA256SUMS`](SHA256SUMS) covers every file.

## Limits

Supply side only: `latest` tags (Envoy: v1.40.0) with the minimum documented TLS setup, on one Linux x86_64 host.
No deployed servers, older tags, distribution packages, ACME-managed or UI-generated configurations; for
nginx-proxy and Nginx Proxy Manager we ran each image's server with its bundled TLS lines, not its full config
generator. One client (OpenSSL 3.5.7 with its default groups). Pomerium's cause rests on its version output and
the Envoy changes above; we did not build Pomerium with a newer Envoy. We ran the whole test twice on the same
host, the second time with a harness rewritten from the written method (`run.py` is that second harness). All 17
results (15 images, 2 controls) and the raw negotiated-group lines matched. That is a repeat by us, not an
independent reproduction. The Kong start error and the Envoy v1.38.5 checks come from the second run only.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. We publish dated corrections when errors are
confirmed. Corrections: hello@cybernative.ai.
