# Results — ICD-10-CM letter-second (QA) codes vs default tools

Run date 2026-10-15 UTC (2026-10-14 Pacific). Protocol frozen before any letter-second probe ran (`PROTOCOL.md`; `FREEZE.sha256` holds the frozen files' hashes as committed, before the edits in `EDITS.md`).
Status: **Executed** on our own hardware by the AI agent that designed the study. Not independently reproduced; a same-code rerun by a second AI agent is summarised under "Rerun".

## Ruling (mechanical, `src/score.py` → `score.json`): **CHANGE**
Exactly one tool met H1: **icdwise 0.1.2** (FORMAT_REJECT). 0 tools excluded; all 9 offline tools byte-identical across run1/run2 (G2);
0 error rows (G3). Two service passes gave identical accept vectors.

| tool (default call) | data vintage seen | QA26 | M26 control | QA27 | N27 | DEL27 accepted | class |
|---|---|---|---|---|---|---|---|
| @lowlysre/icd-10-cm 3.1.1 | FY2027 | 13/13 | 13/13 | 5/5 | 13/13 | 0/13 | QA_OK, current |
| cms-icd 0.3.1 (for_date 2026-10-14) | FY2027 (downloads CMS) | 13/13 | 13/13 | 5/5 | 13/13 | 6/13 | QA_OK, current |
| @cosyte/terminology 0.1.0 (FY2027 order file supplied) | FY2027 | 13/13 | 13/13 | 5/5 | 13/13 | 6/13 | QA_OK, current |
| NLM Clinical Tables API v3 | FY2027 | 13/13 | 13/13 | 5/5 | 13/13 | 0/13 | QA_OK, current |
| tx.fhir.org $validate-code | 2026-04-01 | 13/13 | 13/13 | 0/5 | 0/13 | 13/13 | QA_OK, not FY2027 |
| simple-icd-10-cm 1.5.0 | April 2026 | 13/13 | 13/13 | 0/5 | 0/13 | 13/13 | QA_OK, not FY2027 |
| @cyanheads/medical-codes-mcp-server 0.4.1 | FY2026 | 13/13 | 13/13 | 0/5 | 0/13 | 13/13 | QA_OK, not FY2027 |
| icdlookup 0.1.0 | FY2026 | 13/13 | 13/13 | 0/5 | 0/13 | 6/13 | QA_OK, not FY2027 |
| **icdwise 0.1.2** | FY2026 minus QA | **0/13** | 13/13 | 0/5 | 0/13 | 13/13 | **FORMAT_REJECT** |
| icd10-coder 0.2.3 | FY2025 | 0/13 | 0/13 | 0/5 | 0/13 | 13/13 | STALE_PRE26 |
| @easysolutions906/mcp-healthcare 1.1.3 | FY2025 | 0/13 | 0/13 | 0/5 | 0/13 | 13/13 | STALE_PRE26 |

OLD 13/13 and JUNK 0/5 for every tool, except icdlookup OLD 5/13 (it holds no codes with a 7th-character extension letter, e.g. `S31.120S`;
seen in G1 before freeze). DEL27 "accepted" 6/13 in cms-icd and cosyte are the 6 deleted billable codes that remain category headers in
FY2027 (`D69.1`, `I42.0`, `I42.8`, `M72.2`, `M86.8X1`, `M86.8X5`, each now subdivided); cosyte flags them `activity: header`, cms-icd returns
the description without a billable flag in this call. icdlookup's 6/13 are the same 6 codes for a different reason: its FY2026 data covers
them, and the other 7 carry a 7th-character extension it does not hold.

## What the result says
1. The format break has mostly been absorbed where tools are data-driven: 6 of the 7 packages with FY2026+ data, and both services,
   accept every letter-second code their data covers. A regex in source did not predict failure: cyanheads' shape regex also excludes
   QA, but its documented fallback to database membership accepts them.
2. One maintained tool fails in the way the change predicts. icdwise ("Verified ICD-10-CM code lookup & validation for AI agents", MCP
   server + library) returns `wellFormed:false`, "Not a well-formed ICD-10-CM code" for all 13 real FY2026 QA codes. Post hoc mechanism
   (not part of the ruling): its dataset has 74,706 codes = FY2026's 74,719 minus exactly the 13 QA codes, and its public
   `scripts/build-data.mjs` line 33 parses the CDC file with `/^([A-Z][0-9][0-9A-Z][0-9A-Z]{0,4})\s+(.+)$/`, which drops QA rows
   silently. `searchIcd10("SCN2A")` and `searchIcd10("Lynch syndrome")` return 0 results. A data refresh alone would also drop the 5
   FY2027 QA codes (BRCA1/BRCA2 familial cancer syndrome, Lynch, Li-Fraumeni).
3. The bigger exposure two weeks into FY2027 is currency, not format: 4 of 11 tools/services answer from FY2027 (one of them, cosyte,
   only because we supplied the FY2027 file; it ships no data), and so know the BRCA/Lynch QA1 codes; tx.fhir.org (the HL7 community terminology server) still answers with version 2026-04-01; two packages still ship FY2025.
4. Descriptive pattern arm (`patterns.json`): two public ICD-10 regexes (johndcook.com 2019, regex101 EOGAAH 2024)
   reject 18/18 letter-second codes and accept every other probe code. The 2019 post states its pattern lets no valid code slip by.
   Our encoding of the CMS edit -4036 prose rule accepts 18/18 (and 1/5 junk, `XYZ`: the prose allows a
   letter in position 3 as well).

## Deviations from the frozen protocol
- Service passes ran at 03:45:42Z, +45 s and 03:50:48Z (+5 min), not ≥ 10 min apart as written; all three accept vectors were identical
  (`run1/svc`, `run2-svc`, `run3-svc`). The ruling does not use services' agreement.
- The descriptive arm's johndcook pattern is published unanchored for free-text search; it is anchored here for validation use (stated in
  `src/patterns.py`).
- Correction (2026-10-15, added for publication): the protocol states a service rate of at most 0.5 requests/s per API. `adapters/services.py`
  does not enforce that: it pauses a fixed 0.5 s after each response, which allows nearly 2 requests/s when responses are fast. Each pass sent
  88 requests to one API, then 88 to the other. The frozen protocol and the raw rows are unchanged, and the study was not rerun for
  this correction.

## Limitations
- Small frame of 9 registry packages with modest downloads plus 2 services; no EHRs, clearinghouses, encoders, databases or HL7 v2/X12
  validators were observed. It says nothing about how often hand-written patterns appear in production code.
- One day of service behaviour; registry versions will move (cyanheads has an open FY2027 refresh issue #47).
- QA codes are rare today (13 neurodevelopmental genetic codes); the FY2027 BRCA/Lynch codes are likely to be used more, but we have no
  usage data.
- Executed on our own hardware by the AI agent that designed the study. A second AI agent reran it with fresh installs and the same code and got identical outputs ("Rerun"); that shows the outputs are stable, not that they were independently reproduced.

## Rerun (2026-10-15, added for publication)
A second AI agent, with no part in the main run, reran the study the same day with the same code: it downloaded the
seven CDC files again (all sha256 match `inputs/SOURCES.sha256`), rebuilt `inputs/probes.jsonl` byte for byte,
installed the 9 pinned packages fresh in clean containers (`python:3.12-slim`, `node:24.22.0-slim`, npm with
`--ignore-scripts`), ran the adapters twice offline and the services once, and scored with `src/score.py`. Every row
file is byte-identical to the main run's, and its `score.json` is byte-identical to `score.json` here: same classes,
same arm counts, same ruling (CHANGE; one hit). Its Python dependencies are the same versions as the main run's for
every package both installed. This shows the outputs are stable across fresh installs on one day; it used the same
code and the same kind of host, so it is not an independent reproduction. Files and its own notes: `rerun/`.

## Files
- `PROTOCOL.md`: the frozen protocol (public copy; see `EDITS.md`). `FREEZE.sha256`: the frozen files' sha256 as
  committed before the main run; they refer to the unedited copies.
- `inputs/`: `probes.jsonl` (88 probe codes; sha256 d257358b…9152), `probes.meta.json`, `controls.jsonl` (the 18 OLD
  and JUNK codes used for gate G1), `SOURCES.sha256` and `SOURCES.md` (CDC/NCHS download URLs and how to rebuild the
  probes).
- `adapters/`: one documented call per tool (`py_tools.py`, `node_tools.mjs`, `services.py`).
- `src/`: `prep.py` builds the probes; `score.py` applies the frozen classification and ruling; `patterns.py` is the
  descriptive pattern arm. Added after the result: `table.py` prints the table from `score.json`; `check_fix.py`
  applies the two public patterns and their position-2 edits to the probes (`check_fix.out`).
- Raw rows: `g1/` (gate G1, before freeze); `run1/` (offline tools and the first service pass, `run1/svc/`); `run2/`
  (offline tools, second run); `run2-svc/` and `run3-svc/` (second and third service passes). Each service folder has
  a `done_at.txt` timestamp where one was written.
- Outputs: `score.json` (from `run1` and `run2`), `patterns.json`, `check_fix.out`.
- `env/`: the main run's install scripts (historical records with no overall resource bounds; see "Reproduce"), `py-freeze.txt`, `package.json`, `package-lock.json` and `node-ls.txt`. The
  Python install also added five packages that were screened out of the frame (autoicd, icdmap, icd-mappings,
  icdcodex, hccinfhir) and their dependencies; the adapters do not import them.
- `rerun/`: the second agent's rows, environment record, source hashes and `score.json`.

## Reproduce
Offline, from this folder, with Python 3.12 and the standard library only. This recomputes `score.json` from the raw
rows, checks every file against `SHA256SUMS`, and prints the table:

```
python3 src/score.py run1 run2 > score.json && sha256sum -c SHA256SUMS && python3 src/table.py score.json
```

The descriptive arms: `python3 src/patterns.py inputs/probes.jsonl > patterns.json` and
`python3 src/check_fix.py inputs/probes.jsonl > check_fix.out`; both files must still match `SHA256SUMS`. The rerun:
`cd rerun && python3 ../src/score.py run1 run2 > score.json`.

Count the FY2026 codes in the CDC file (network; the zip's sha256 is `a852eb91…8f88`, `fy26-desc.zip` in
`inputs/SOURCES.sha256`). This prints 74719:

```
curl -s -o fy26.zip "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD10CM/2026/icd10cm-Code%20Descriptions-2026.zip" && unzip -p fy26.zip icd10cm-codes-2026.txt | grep -c .
```

The same file through a filter that requires a digit in position 2 keeps 74,706 codes, 13 fewer:
`unzip -p fy26.zip icd10cm-codes-2026.txt | grep -cE '^[A-Z][0-9][0-9A-Z][0-9A-Z]{0,4} '`.

The offline recompute above is the supported way to check this bundle. It needs no network and runs no third-party
code.

Full rerun outline (historical, for reference only). The commands below record how our containers were set up; we
have not run them verbatim from this folder, and they are not a safe execution recipe by themselves. They install
third-party registry packages and call two public APIs. Limits they do set: the scored offline tool runs use
`--network none`, `--cpus 2` and `--memory 4g`, npm installs use `--ignore-scripts`, and `services.py` sets a 30 s
timeout on each request. Limits they do not set: the install and gate-G1 commands have network and no CPU or memory
limit; no command enforces the protocol's 600 s per-tool ceiling or any total wall-time; nothing limits disk use or
response size; `services.py` runs on the host with network and only a fixed 0.5 s pause between requests (see the
rate correction under "Deviations"). The install scripts in `env/` and `rerun/env/` are historical records of the
same kind and have no overall bounds. To rerun, use an isolated, disposable CPU executor that you control, with
explicit CPU, memory, storage, network, wall-time and abort limits, cleanup afterwards, and no credentials or private
data mounted; keep requests to each API at or below 0.5 per second. Each tool run took a few seconds in our runs.

```
mkdir -p w/env/node w/lab && cp -r adapters inputs w/lab/ && cp env/package.json env/package-lock.json w/env/node/
# put the FY2027 order file at w/lab/inputs/icd10cm-order-2027.txt (from icd10cm-code-descriptions-2027.zip, see inputs/SOURCES.md)
docker run --rm -e HOME=/w/env/home -v "$PWD/w:/w" python:3.12-slim sh -c 'python -m venv /w/env/py && /w/env/py/bin/pip install simple-icd-10-cm==1.5.0 icdlookup==0.1.0 cms-icd==0.3.1 icd10-coder==0.2.3'
docker run --rm -v "$PWD/w:/w" -w /w/env/node node:22.23.3 npm ci --ignore-scripts
# gate G1, with network: cms-icd downloads and caches the CMS release under HOME on first use
docker run --rm -e HOME=/w/env/home -v "$PWD/w:/w" python:3.12-slim /w/env/py/bin/python /w/lab/adapters/py_tools.py /w/lab/inputs/controls.jsonl /w/lab/g1/py
for r in run1 run2; do
  docker run --rm --network none --cpus 2 --memory 4g -e HOME=/w/env/home -v "$PWD/w:/w" python:3.12-slim /w/env/py/bin/python /w/lab/adapters/py_tools.py /w/lab/inputs/probes.jsonl /w/lab/$r/py
  docker run --rm --network none --cpus 2 --memory 4g -v "$PWD/w:/w" node:22.23.3 node /w/lab/adapters/node_tools.mjs /w/lab/inputs/probes.jsonl /w/lab/$r/node /w/env/node/node_modules /w/lab/inputs/icd10cm-order-2027.txt
done
python3 adapters/services.py inputs/probes.jsonl w/lab/run1/svc   # two public APIs, 88 requests each, 0.5 s pause after each response
python3 src/score.py w/lab/run1 w/lab/run2
```

Results will change as registry packages and services move to newer releases; the rows here record what each call
returned on 2026-10-15 (UTC).

## Data and license
Code (`adapters/`, `src/`) is MIT-licensed (`LICENSE`). Probe codes and descriptions come from public-domain CDC/NCHS
ICD-10-CM files. The raw rows also hold up to 160 characters of each tool's or service's response (for example, a
code description or a version string) as returned on the run date.

This work uses CDC/NCHS materials. It is not endorsed by the Centers for Disease Control and Prevention (CDC), the
U.S. Department of Health and Human Services (HHS) or the United States Government. The official ICD-10-CM files are
available without charge from CDC/NCHS at the links in `inputs/SOURCES.md`. The MIT license covers our code only; it
does not cover the CDC/NCHS source data or the third-party response excerpts in the raw rows.
