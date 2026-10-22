# Reproduce

`repro.sh` runs inside the official AdGuard Home image. It runs the install wizard, prints the DNS
settings the wizard wrote, and then tests five configs while traffic to Quad9's address ranges is
allowed, dropped or refused. It needs `NET_ADMIN` to add the firewall rules inside the
container, and network access to install `iptables`, `bind-tools` and `curl` from Alpine's
packages. It changes nothing outside the container and takes a few minutes.

From this folder, on a Linux machine with Docker:

```sh
docker run --rm --cap-add NET_ADMIN -v "$PWD/repro.sh:/rep/repro.sh:ro" \
  --entrypoint sh adguard/adguardhome:v0.107.79 /rep/repro.sh
```

`output-2026-10-22.txt` is the output of that command on October 22, 2026, with image digest
`sha256:aba9e3bf0613be3ba3755e1fc311b126e2c24bec25e18b6483894a88283074f0`. A resolved name is a
NOERROR answer within 5 seconds (`dig +time=5 +tries=1`); `TIMEOUT` means no answer in that time.

## `data/`

Per-query results of the larger run described in the note: AdGuard Home v0.107.79 (same image),
20 names, everything run twice (`run1`, `run2`), 1,500 queries each. One line per query.

| Field | Values |
|---|---|
| `arm` | `D` wizard default; `S` default, with a working DNS server in the container's `/etc/resolv.conf`; `B` upstream `https://cloudflare-dns.com/dns-query`, default bootstrap; `R` `B` with bootstrap `1.1.1.1`, `1.0.0.1`; `F` default with `fallback_dns: [1.1.1.1]`; `U` upstream `https://1.1.1.1/dns-query` |
| `mode` | `M0` Quad9 reachable; `M1` packets dropped; `M2` refused (TCP reset, ICMP unreachable); `M3` a stand-in server answers `REFUSED` (plain DNS) and HTTP 200 with a `REFUSED` answer (DNS-over-HTTPS); `M4` the same, with HTTP 451 for DNS-over-HTTPS |
| `phase`, `set` | `C`/`C`: started with Quad9 already cut off, 20 names. `W`: started with Quad9 reachable; `W1` 10 names, then Quad9 cut off; `W2cached` the same 10 names; `W2new` 10 other names |
| `status`, `ok5` | `dig` status; `ok5` is true for NOERROR within 5 seconds |
| `query_ms`, `wall_ms`, `err`, `n_a` | `dig` query time, wall time, error text, number of A records |

For `M3` and `M4`, Quad9's addresses were redirected to the stand-in server, which used a test
certificate that AdGuard Home was told to trust. That server is not included here.
