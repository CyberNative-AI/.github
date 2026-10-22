# tzscan: find stale time-zone data inside a container image, without running it

On 1 November 2026 Alberta, the Northwest Territories and Manitoba stop falling back, and British Columbia stops on the same day. Time-zone data older than 2026e gets some of them wrong, and data older than 2026c is already wrong for Morocco. Many images carry more than one copy of that data: the operating system's, plus the JDK's, Go's, Node's ICU tables, PHP's built-in database, Joda-Time inside a plugin jar.

The usual check is a command run inside the container, one per runtime. Distroless and scratch images have no shell to run it in, and with many images you may not know which runtimes carry their own copy. tzscan reads the image's files, finds every copy it recognises and says whether each one is wrong for these changes. Nothing from the image is executed.

```sh
curl -fsSLO https://github.com/CyberNative-AI/.github/raw/refs/heads/main/tools/tzscan/tzscan.py
python3 tzscan.py registry.k8s.io/kube-controller-manager:v1.36.5
```

It needs Python 3.9 or newer and nothing else from outside the standard library. Given an image name, it pulls the image if it is not already local, then uses `docker create` (the container is never started) and `docker export`, and removes the container and its anonymous volumes; this needs Docker 20.10 or newer. Ctrl-C during the create waits for it to finish and then cleans up. If tzscan is killed outright (`kill -9`, out of memory, power loss) it cannot clean up; a leftover container carries the label `io.github.cybernative-ai.tzscan` and can be removed with `docker ps -aq --filter label=io.github.cybernative-ai.tzscan | xargs -r docker rm -f -v`.

Without Docker, or for a container you already have, give it an exported filesystem or an unpacked root:

```sh
podman export CONTAINER | python3 tzscan.py --tar -
python3 tzscan.py --tar rootfs.tar
python3 tzscan.py --dir /path/to/rootfs
```

Add `--json` for machine-readable output. Each target there has `complete` and a `problems` list naming anything that was not read.

## What a report looks like

`registry.k8s.io/kube-controller-manager:v1.36.5` (`sha256:2d717af1…9a4d`), scanned on 14 October 2026. The image has no shell:

```text
== registry.k8s.io/kube-controller-manager:v1.36.5
   -- used by default for local time
   STALE   usr/share/zoneinfo  [zoneinfo] data 2026b  wrong from 1 Nov: Edmonton, Inuvik, Winnipeg; Casablanca wrong now
             zoneinfo directory, zones measured; read by glibc/musl, Go (before its own copy), Python zoneinfo, .NET, Ruby tzinfo, PHP built with system tzdata
   -- library and program copies (matter only if that code is used)
   STALE   usr/local/bin/kube-controller-manager  [go-embedded] data <2026b  wrong from 1 Nov: Vancouver, Edmonton, Inuvik, Winnipeg; Casablanca wrong now
             embedded zoneinfo zip, zones measured; used by this Go program only when no zoneinfo directory is found ($ZONEINFO, /usr/share/zoneinfo, ...); this image has one, so this copy is a fallback
```

Copies are in two groups:
- **Used by default for local time:** the copy a program in the image reads unless it is told otherwise.
- **Library and program copies:** a library's or program's own copy. It matters when that code handles time zones, and some programs use it all the time: Trino computes `hour()` and `format_datetime` with its Joda-Time copy. "Library" does not mean harmless.

`data` is the oldest tz release that matches what the copy computes for these zones, or the version the copy declares where it can only be read from a label (see below).

## Exit status

| Code | Meaning |
|---|---|
| 0 | Every copy it found was verified current. |
| 1 | A copy used by default for local time is stale. |
| 2 | The scan was incomplete (a size limit, a damaged archive, a read or export failure), nothing was found, or a copy could not be judged. |
| 3 | Only library or program copies are stale. |

An incomplete scan exits 2 even when it found stale copies; they are still listed, with an `INCOMPLETE` line for each part it could not read. In a complete scan, a stale copy used by default gives 1 even if another copy could not be judged.

Exit 0 is about the copies tzscan recognises. It does not prove the image has no other copy (see Not established).

## Limits on what it reads

An image can be built to exhaust memory or disk, so tzscan reads each target within fixed bounds: 4 GiB for any one file or archive entry; 64 GiB read out of archives after decompression, the image tar itself included; 5,000,000 files and archive entries; 64 GiB of binary data searched; 256 MiB of data kept until the report; 10,000 copies and problems reported; 64 MiB of zip central directories open at once (a jar and the jars enclosing it); archives nested at most three levels inside a jar; 1 MiB of header data for one tar entry; and 128 KiB for one zone file. Reaching a bound reports the scan incomplete (exit 2); it is never skipped quietly. Large archives are spooled to a temporary file rather than held in memory. The bounds are constants at the top of `tzscan.py`. The largest images we checked stay well inside them: OpenSearch 3.9.0 has a 304 MB jar and about 378,000 files and archive entries, and ClickHouse an 840 MB binary.

## What it finds

| Copy | How it is judged |
|---|---|
| OS zoneinfo, and the same files shipped by Python `tzdata`, pytz, PostgreSQL and Go's `zoneinfo.zip` | **Measured:** the zone files are evaluated for Vancouver, Edmonton, Inuvik, Winnipeg and Casablanca on 15 December 2026. Symlinks, hardlinks and aliases are followed. |
| Go `time/tzdata` compiled into a binary | **Measured.** Default only when the image has no zoneinfo directory, because Go reads the system copy first. |
| PHP and MongoDB built-in database (timelib), including PECL `timezonedb.so` | **Measured.** |
| Zone files compiled into a binary (ClickHouse) | **Measured.** |
| Joda-Time in jars, including jars inside jars | **Measured** by decoding Joda's compiled zones. The jar's own version label is shown but not trusted. |
| JDK `tzdb.dat` and threetenbp `TZDB.dat` | Version recorded in the file. |
| ICU `zoneinfo64` in binaries, `.so`, `.dat` and `.res` files (Node.js, DuckDB) | Version recorded in the ICU data. |
| Rust `chrono-tz` | Crate version found in the binary. |
| Ruby `tzinfo-data`, moment-timezone, Python `tzdata` | Version label only. |

## What it cannot tell you

tzscan lists copies and which one is used by default. It does not see which copy a particular program actually calls. Only running that program shows that; the [“Am I affected?” checks in our runtimes guide](https://cybernative.ai/guides/canada-time-zone-change-2026-runtimes/#affected) do it one runtime at a time.

## How we checked it

We compared its verdicts on 59 images (65 copies) with results established without it: for runtime copies, the offsets the runtime printed when we ran it inside the image; for OS zoneinfo, the image's tzdata package version. It matched all 65, and it reported no stale copy as current. The images include Temurin 8–25, Corretto, distroless java and static, UBI OpenJDK, PHP 8.2–8.5, Go 1.25–1.27, Debian, Ubuntu, Alpine, UBI, Amazon Linux 2023, .NET, Ruby and Python bases, kube-controller-manager 1.34–1.37, MySQL, MariaDB, MongoDB 7–9, Elasticsearch, OpenSearch, Trino, ClickHouse and Node 22, 24 and 26. [VALIDATION.md](VALIDATION.md) lists each image digest, the expected release and the command behind it.

The fixes in our guides were also checked: a 2026e zoneinfo tree, a 2026e `tzdb.dat`, Joda-Time 2.15.0, an ICU 2026e `.res` override and PECL `timezonedb` 2026.5 each read as current. A tree with one stale zone is reported stale for that zone, and a tree missing a zone, a damaged `tzdb.dat` or an empty directory exits 2.

## Not established

- arm64 and Windows images; big-endian ICU data; ICU data with no table of contents and two version strings (reported as UNKNOWN).
- MySQL and MariaDB named time zones: they live in tables in the data directory, created at run time, not in the image.
- Rust `chrono-tz` newer than 0.10.4 (reported as UNKNOWN until mapped).
- Images that set `ZONEINFO` or `TZDIR`, or a JDK started with `-Djava.time.zone.DefaultZoneRulesProvider`: tzscan does not model that precedence.

## License

MIT. See [LICENSE](LICENSE).
