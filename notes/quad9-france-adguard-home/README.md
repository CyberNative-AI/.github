# Quad9 leaves France on November 24: a default AdGuard Home install stops resolving (tested October 22)

On October 22 Quad9 [announced](https://quad9.net/news/blog/au-revoir-france/) that it will
"withdraw Quad9 services from France as of Tuesday, November 24." AdGuard Home's install wizard
sets Quad9 as its only DNS server. If you run AdGuard Home in France and never changed its DNS
settings, it depends on a service that is going away.

We tested what happens when Quad9 stops answering a default install:

1. **It stops resolving.** With the wizard's settings, once Quad9 was cut off AdGuard Home could
   not resolve any name it had not already cached, and after a restart it answered SERVFAIL to
   every lookup. If your devices use AdGuard Home as their DNS server, none of them can look up a
   new name.
2. **Changing only the upstream is not enough.** If you replaced the Quad9 upstream with
   another provider's hostname but kept the default bootstrap servers, the hostname is still
   resolved through Quad9. That setup keeps working while it runs and fails at the next restart.
3. **A fallback server only partly helps.** `fallback_dns` rescues a restart, but on a running
   server it did not help when packets to Quad9 were dropped: lookups of new names timed out.

To remove this dependency, use a non-Quad9 upstream by IP address, or a non-Quad9 upstream
by hostname with non-Quad9 bootstrap servers (details below, in **Settings → DNS settings**).
Both configurations worked in every case we tested.

## Check yours

In the web interface, open **Settings → DNS settings** and look at **Upstream DNS servers** and
**Bootstrap DNS servers**. Quad9 entries look like `dns10.quad9.net` (or another `quad9.net`
name), `9.9.9.x`, `149.112.112.x` or `2620:fe::…`. The wizard default (Quad9-only upstream and
bootstrap, empty fallback) failed in our outage tests. A non-Quad9 hostname upstream with
Quad9-only bootstrap also failed after a restart. A non-Quad9 upstream by IP address did not
need bootstrap and kept working even with the default bootstrap list. We did not test mixed
lists, per-client or domain-specific overrides, or `upstream_dns_file` configurations.

Or read the config file. The install script puts it at `/opt/AdGuardHome/AdGuardHome.yaml`; the
official Docker image at `/opt/adguardhome/conf/AdGuardHome.yaml`:

```sh
grep -A6 -E '^  (upstream_dns|bootstrap_dns|fallback_dns):' AdGuardHome.yaml
```

This is what the wizard of v0.107.79, the current release, writes (the development branch has
the same defaults):

```yaml
  upstream_dns:
    - https://dns10.quad9.net/dns-query
  upstream_dns_file: ""
  bootstrap_dns:
    - 9.9.9.10
    - 149.112.112.10
    - 2620:fe::10
    - 2620:fe::fe:10
  fallback_dns: []
```

## Fix

Either of these resolved every name in every test below:

- **Upstream by IP address.** In **Upstream DNS servers**, replace the Quad9 line with a resolver
  you trust, written with its IP address instead of a hostname. We tested the DNS-over-HTTPS form
  `https://<IP>/dns-query`; it works only with providers whose certificate covers the IP address,
  so if yours does not, use the second option. Nothing then needs a bootstrap lookup.
- **Non-Quad9 upstream by hostname, with a non-Quad9 bootstrap.** In **Upstream DNS servers**,
  replace the Quad9 upstream with a non-Quad9 resolver you trust, given by hostname (or keep
  your existing non-Quad9 hostname upstream). In **Bootstrap DNS servers**, list plain IP
  addresses of a resolver other than Quad9. Changing only bootstrap does not replace a
  Quad9 upstream.

In `AdGuardHome.yaml` these are `upstream_dns` and `bootstrap_dns`. If you edit the file,
[stop AdGuard Home first](https://github.com/AdguardTeam/AdGuardHome/wiki/Configuration#configuration-file),
edit it while stopped, then start it; the running program can overwrite file edits. If you use
the web interface, save the settings, then restart once. Look up a name through AdGuard Home,
for example `dig @<AdGuard Home address> example.com` or `nslookup example.com <AdGuard Home address>`.

We used Cloudflare's addresses (`1.1.1.1`, `1.0.0.1`) as the stand-in in the test. We did not
compare providers, and this is not a recommendation for one. We also did not test lists that mix
Quad9 with another resolver.

## What we tested

AdGuard Home v0.107.79 (official Docker image) ran the install wizard; we then started it with
five configs while traffic to Quad9's address ranges `9.9.9.0/24` and `149.112.112.0/24` was
allowed, dropped, or refused (TCP reset, ICMP unreachable). "Cold" means AdGuard Home started
while Quad9 was already cut off; "warm" means it started with Quad9 reachable, answered five
names, and then Quad9 was cut off.

| Config | Quad9 reachable | Dropped, cold | Dropped, warm (new names) | Refused, cold | Refused, warm (new names) |
|---|---|---|---|---|---|
| Wizard default | 10/10 | 0/10 SERVFAIL | 0/5 timeout | 0/10 SERVFAIL | 0/5 SERVFAIL |
| Upstream by hostname, default (Quad9) bootstrap | 10/10 | 0/10 SERVFAIL | 5/5 | 0/10 SERVFAIL | 5/5 |
| Upstream by hostname, non-Quad9 bootstrap | 10/10 | 10/10 | 5/5 | 10/10 | 5/5 |
| Upstream by IP address | 10/10 | 10/10 | 5/5 | 10/10 | 5/5 |
| Wizard default + `fallback_dns` | 10/10 | 10/10 | 0/5 timeout | 10/10 | 5/5 |

Names already in the cache kept answering (5/5) in every config. A name counts as resolved if
`dig` got a NOERROR answer within 5 seconds. Each cell is from one run of
[`reproduce/repro.sh`](reproduce/repro.sh); its output is
[`reproduce/output-2026-10-22.txt`](reproduce/output-2026-10-22.txt). An earlier full run and a
cold-only run on October 22 gave the same results.

A larger run the same day used 20 names, ran everything twice, and also simulated Quad9
answering `REFUSED`, and DNS-over-HTTPS returning HTTP 451, from a stand-in server. The default
config resolved 0 of 20 names after a restart in all four ways of cutting Quad9 off. Having a
working DNS server configured on the host did not help: AdGuard Home does not use the system
resolver for its upstream or bootstrap lookups. With `fallback_dns` set, a running server that
got `REFUSED` from Quad9 passed `REFUSED` on to clients for 9 of 10 new names, in both runs. Per-query data:
[`reproduce/data/`](reproduce/data/).

## What we did not test

- **How Quad9 will withdraw.** Quad9's post does not say. Dropped packets, refused connections,
  `REFUSED` answers and HTTP 451 are our guesses at the range; a partial exit could behave
  differently. We have no vantage point in France.
- **IPv6.** Our test network had no IPv6, so the two IPv6 bootstrap addresses failed in every
  case, including the baseline.
- **Builds that embed AdGuard Home**, such as router firmware, NAS packages or the Home Assistant
  add-on. They may ship different defaults.
- **Other software pointed only at Quad9**, such as a router set to `9.9.9.9` or a phone whose
  private DNS is `dns.quad9.net`. An exclusive dependency on Quad9 may need reconfiguration when
  it withdraws; that is an inference from its announcement. We did not test those clients or
  their failover settings.
- One AdGuard Home version (v0.107.79) and 10 to 20 well-known names. We ran these tests
  ourselves; nobody outside our company has reproduced them yet.

## En bref (français)

Quad9 cessera de servir les utilisateurs en France le 24 novembre. L'assistant d'installation
d'AdGuard Home (v0.107.79) configure Quad9 comme seul serveur DNS upstream et seul serveur
d'amorçage. Dans notre test, une installation par défaut démarrée sans accès à Quad9 n'a résolu
aucun nom (SERVFAIL).

À vérifier dans **Paramètres → Paramètres DNS** : les valeurs par défaut utilisent seulement
Quad9 dans **Serveurs DNS upstream** et **Serveurs DNS d'amorçage**, sans serveur de secours.
Cette configuration a échoué dans nos tests de coupure. Un upstream autre que Quad9 donné par
nom d'hôte a aussi échoué au redémarrage lorsque l'amorçage utilisait seulement Quad9. Un
upstream autre que Quad9 donné par adresse IP a fonctionné même avec l'amorçage par défaut.

Remplacez l'upstream Quad9 par un résolveur autre que Quad9 auquel vous faites confiance : soit
par son adresse IP, soit par son nom d'hôte avec des serveurs d'amorçage autres que Quad9.
Changer seulement l'amorçage ne remplace pas un upstream Quad9. Pour DNS-over-HTTPS par adresse
IP, le certificat du fournisseur doit couvrir cette adresse. Si vous modifiez le fichier YAML,
arrêtez AdGuard Home avant de le modifier, puis démarrez-le. Dans l'interface web, enregistrez
les paramètres puis redémarrez une fois et testez une résolution. Nous n'avons pas testé les
listes mixtes, les exceptions par client ou domaine, ni les configurations `upstream_dns_file`.

## Reproduce

[`reproduce/`](reproduce/) has the script, its output and the per-query data, with the
command to run it on any Linux machine with Docker.

---

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will record dated corrections on this page.
