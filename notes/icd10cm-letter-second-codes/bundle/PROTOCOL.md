# Protocol — One year after ICD-10-CM put a letter in position 2, do default code tools accept those codes?

Status: FROZEN 2026-10-14 before any QA, M26, N27 or DEL27 probe was executed (only OLD+JUNK controls ran, `g1/`).
Risk tier 0/1: public-domain CDC/NCHS code files; registry packages pinned and installed once with network; every scored offline
run uses `docker run --network none` (2 CPU, 4 GB), CPU only, $0. cms-icd fetches the CMS release once with
network (its documented behaviour) and is then scored from its cache with network none. Service arm: two free public read APIs, ≤0.5 req/s,
88 probe codes each, no accounts, no personal data. No model inference, no GPU, no outside contact.
Ceiling: 600 s per tool per run, 2 full offline runs, 2 service passes; lead time ≤ 3 h. Abort: a tool run over 600 s is excluded.

## Why now (primary sources, fetched 2026-10-14)
- FY2026 ICD-10-CM (effective 2025-10-01) added 13 billable codes in a new category `QA0` (neurodevelopmental disorders related to
  specific genetic pathogenic variants, e.g. `QA0.0101` SCN2A-related neurodevelopmental disorder). These are the first ICD-10-CM
  codes whose 2nd character is a letter. Source: CDC/NCHS `icd10cm-codes-2026.txt` (ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD10CM/2026/).
- FY2027 (effective 2026-10-01, files public since 2026-06-16) adds 5 more: `QA1.71` Lynch syndrome, `QA1.790`/`QA1.791` familial
  cancer syndrome with pathogenic BRCA1/BRCA2 mutation, `QA1.792` Li-Fraumeni syndrome, `QA1.798` other. Source: `icd10cm-codes-2027.txt`,
  `icd10cm-codes-addenda-2027.txt`. These are high-use oncology-genetics concepts, so letter-second codes now reach routine data.
- CMS itself retired its own ICD-10 format edit -3852 and created edit -4036 to "allow alphabetic values in Character 2" (CMS LTCH data
  specifications errata v4.02.2, Sept 2025). Widely copied public patterns still require a digit in position 2 (johndcook.com
  2019 ICD regex post; regex101 library EOGAAH).
- Fresh practitioner evidence: GitHub lolotam/eyadex "fix(medical): accept FY2027 ICD-10-CM codes with a letter second (QA0…)"
  (closed 2026-10-13); cyanheads/medical-codes-mcp-server issue to refresh to FY2027 (open, 2026-09-24).
- Prior art searched (web, GitHub issue search "icd-10-cm 2027", "FY2027 icd"): no measurement of how default tools treat
  letter-second codes was found.

## Question
For the default validity/lookup call of maintained open-source ICD-10-CM tools (PyPI, npm) and two free public services, are
letter-second codes (QA) rejected while comparable codes from the same release are accepted?

## Frame (fixed before any QA probe was executed)
Registry search 2026-10-14: PyPI project names containing `icd` (simple index, 404 names) and npm search `icd-10-cm` / `icd10`.
Inclusion: offers an offline ICD-10-CM (US) validity or code-lookup function, latest release ≥ 2025-01-01, installs with pip/npm.
In (9): simple-icd-10-cm 1.5.0, icdlookup 0.1.0, cms-icd 0.3.1, icd10-coder 0.2.3 (PyPI); @lowlysre/icd-10-cm 3.1.1, icdwise 0.1.2,
@cyanheads/medical-codes-mcp-server 0.4.1, @easysolutions906/mcp-healthcare 1.1.3, @cosyte/terminology 0.1.0 (npm; a content-agnostic
loader, scored with the FY2027 CDC order file through its documented `ICD10CM_ORDER_FILE_FIELDS` preset).
Service arm (2): NLM Clinical Tables ICD-10-CM API v3; tx.fhir.org R4 `CodeSystem/$validate-code` (HL7 community terminology server).
Excluded with reason: autoicd/autoicd-js, @sequoiaport/codes, @pipeworx/* (remote API clients needing keys); icdcodex, icdmap, hccinfhir,
comorbidipy, icd-mappings (representation/mapping/risk models, no validity call); ICD10CodeLookUp, icd-validator, icd10-cm (PyPI),
icd-10-cm-core (release < 2025); simple-icd-10 (WHO ICD-10, not CM); pyhealth (pulls torch; runtime data download; descriptive only if time);
OHDSI Athena (anonymous API returns 403); health-data-faker (generator).
Adapters: `adapters/py_tools.py`, `adapters/node_tools.mjs`, `adapters/services.py` — one documented call per tool, recorded in each row's
`call` field. Input form: dotted (`QA0.0101`) except icd10-coder internal `_code_exists` and cosyte (undotted storage form, as documented).

## Probe arms (`src/prep.py`, seed 13826, `inputs/probes.jsonl` sha256 d257358b…9152, 88 rows)
- QA26: all 13 FY2026 letter-second billable codes. QA27: all 5 FY2027 letter-second codes.
- M26 (primary control): for each QA26 code, one FY2026-new non-QA billable code with the same length and last-character class
  (digit/letter). Same release year, same shape apart from position 2. Holds data vintage and length coverage fixed.
- N27: 13 random FY2027-new non-QA codes (data-currency control for QA27). OLD: 13 random codes valid FY2025–FY2027.
- DEL27: 13 random codes deleted in FY2027 (descriptive). JUNK: 5 malformed strings (negative control).
- The April 1 2026 update added no billable codes visible in its tabular names (checked; `inputs/probes.meta.json`).

## Classification per tool (computed mechanically by `src/score.py` from run-1 rows)
- STALE_PRE26: M26 accepted ≤ 2/13 (no FY2026 data; says nothing about format).
- FORMAT_REJECT: M26 ≥ 10/13 and QA26 ≤ 2/13.
- QA_OK: QA26 ≥ 12/13. OTHER: anything else (reported with rows).
- Secondary, FY2027: QA27_GAP if N27 ≥ 10/13 and QA27 ≤ 1/5 (FY2027 data present but the new letter-second codes missing).
  CURRENT27 if N27 ≥ 12/13 and QA27 ≥ 4/5. DEL27 acceptance reported descriptively (some tools keep historical codes by design).

## Hypothesis and pre-registered ruling
- H1: at least one maintained default tool with FY2026+ data rejects letter-second codes it should know (FORMAT_REJECT or QA27_GAP).
- CONTINUE: ≥ 2 tools from different maintainers are FORMAT_REJECT or QA27_GAP.
- CHANGE: exactly 1 such tool.
- STOP: 0 (the format break has been absorbed by maintained default tools; record the negative).
- INVALID: > 4 of 11 tools excluded by gates.
- Gates: G1 (passed before freeze, `g1/`): every adapter accepts 13/13 OLD and rejects 5/5 JUNK, except icdlookup, which rejects all 8
  OLD codes that carry a 7th-character extension letter (tool coverage property, recorded; M26 is shape-matched to QA26, so it cannot
  create a false FORMAT_REJECT). G2 determinism: offline tools run twice, rows byte-identical; a non-identical tool is excluded.
  G3: a tool with setup error or exception rows > 10% is excluded. Services: run twice ≥ 10 min apart; disagreement reported, first pass scored.
- Descriptive arm (not ruling): three public format patterns (johndcook.com 2019 ICD-10 regex; regex101 EOGAAH; CMS edit -4036 rule) applied
  to all probe codes.

## Consequences
- CONTINUE → a short public note within 48 h (letter-second codes and the BRCA/Lynch move); whether to report to any project is
  decided separately, after reading its contribution policy and existing issues.
- CHANGE → a narrower public note; no outside contact without a separate decision.
- STOP → record the negative: maintained default tools absorbed the change; the residual risk sits in hand-written patterns (descriptive arm).

## Disclosures and limitations (known before freeze)
- Before freeze we read the source of 4 tools while writing adapters: icdwise `dist/icd.js` contains a digit-second pattern; cyanheads `detect.js`
  documents the QA exception and falls back to DB membership; icd10-coder and easysolutions bundle FY2025 data; simple-icd-10-cm ships
  April 2026 data. No QA probe had been executed. The ruling counts executed behaviour, not source reading.
- Small frame (9 packages, most with modest downloads); results describe these defaults, not EHRs, clearinghouses, commercial encoders,
  or databases with CHECK constraints, which this run does not observe.
- Registry and service versions change; services were probed on one day.
- Executed on our hardware: "Executed", not independently reproduced.
