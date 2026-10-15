# ICD-10-CM's new BRCA and Lynch codes start with "QA". Does your validator accept a letter in position 2?

Since 1 October 2026, ICD-10-CM has its own codes for familial cancer syndrome with a pathogenic BRCA1 or BRCA2
mutation (`QA1.790`, `QA1.791`), Lynch syndrome (`QA1.71`) and Li-Fraumeni syndrome (`QA1.792`), plus `QA1.798` for
other inherited neoplasm predisposition syndromes of multiple systems. Their second character is a letter.

Until a year ago no ICD-10-CM code had a letter there. FY2026 added the first 13, in category `QA0`
(neurodevelopmental disorders related to specific genetic variants, such as `QA0.0101` SCN2A-related neurodevelopmental
disorder). CMS changed its own submission checks for them: in September 2025 it ended format edit -3852 and created
edit -4036 "to allow alphabetic values in Character 2"
([LTCH data specifications errata v4.02.2](https://www.cms.gov/files/document/ltch-data-specifications-errata-v4-02-2.pdf)).

Code that checks the shape of a code with `[A-Z][0-9]...` rejects all of these. We measured how often that happens
in open-source ICD-10-CM tools and two free services, two weeks into FY2027.

**Short answer: most tools built on the code files accept letter-second codes. One does not. Two public regex
examples reject all 18. The larger gap is currency: 7 of the 11 tools and services we ran do not yet answer from
FY2027, so they do not know the BRCA and Lynch codes.**

## What we did

We ran the default validity or lookup call of 9 ICD-10-CM packages from PyPI and npm (offline function, latest
release in 2025 or later) and of two free services, NLM Clinical Tables API v3 and the HL7 community terminology
server tx.fhir.org (`$validate-code`). Each got the same 88 codes:

- all 13 FY2026 `QA0` codes, and for each one an FY2026 code of the same length that is new in the same release
  (the control: same data year, same shape except position 2);
- all 5 FY2027 `QA1` codes, and 13 other codes new in FY2027 (does the tool have FY2027 data at all?);
- 13 codes valid in every year from FY2025 to FY2027, 13 codes deleted in FY2027, and 5 malformed strings.

We fixed the protocol and the scoring rule before running any QA code. The offline packages ran twice with no
network and gave byte-identical results. The services were queried three times within five minutes (the protocol
said at least 10 minutes apart) and gave identical answers each time. The protocol also set a ceiling of 0.5 requests per second per service, but our
service script only paused a fixed 0.5 seconds after each response, which does not enforce that ceiling; `RESULTS.md`
has the correction. Code lists come from the CDC/NCHS release files.

## Results

| Tool or service (default call) | Data year it answers from | FY2026 `QA0` | Same-shape control | FY2027 `QA1` | Other FY2027-new |
|---|---|---|---|---|---|
| @lowlysre/icd-10-cm 3.1.1 | FY2027 | 13/13 | 13/13 | 5/5 | 13/13 |
| cms-icd 0.3.1 (downloads the CMS release) | FY2027 | 13/13 | 13/13 | 5/5 | 13/13 |
| @cosyte/terminology 0.1.0 (ships no data; we loaded the FY2027 file) | FY2027 | 13/13 | 13/13 | 5/5 | 13/13 |
| NLM Clinical Tables API v3 | FY2027 | 13/13 | 13/13 | 5/5 | 13/13 |
| tx.fhir.org `$validate-code` | 2026-04-01 | 13/13 | 13/13 | 0/5 | 0/13 |
| simple-icd-10-cm 1.5.0 | April 2026 | 13/13 | 13/13 | 0/5 | 0/13 |
| @cyanheads/medical-codes-mcp-server 0.4.1 | FY2026 | 13/13 | 13/13 | 0/5 | 0/13 |
| icdlookup 0.1.0 | FY2026 | 13/13 | 13/13 | 0/5 | 0/13 |
| **icdwise 0.1.2** | FY2026, minus the 13 `QA0` codes | **0/13** | 13/13 | 0/5 | 0/13 |
| icd10-coder 0.2.3 | FY2025 | 0/13 | 0/13 | 0/5 | 0/13 |
| @easysolutions906/mcp-healthcare 1.1.3 | FY2025 | 0/13 | 0/13 | 0/5 | 0/13 |

Every tool accepted all 13 long-valid codes and rejected all 5 malformed strings, except that icdlookup holds no codes
with a 7th-character extension and accepted 5 of 13. Codes deleted in FY2027 are in the bundle; some tools keep
old codes on purpose.

**Tools that read the code files mostly absorbed the change.** Six of the 7 packages with FY2026 or later data, and
both services, accept every letter-second code their data covers. A shape regex in the source did not by itself
predict failure: one package's regex also excludes `QA`, but it falls back to checking the code list, as its
documentation says, and accepts them.

**One package rejects them by shape.** icdwise 0.1.2, an npm library and MCP server for ICD-10-CM validation in AI
agents, returns "Not a well-formed ICD-10-CM code" for all 13 FY2026 `QA0` codes and accepts all 13 controls. Its
bundled list has 74,706 codes, which is FY2026's 74,719 minus exactly those 13. Its build script reads the CDC file
with `/^([A-Z][0-9][0-9A-Z][0-9A-Z]{0,4})\s+(.+)$/` (`scripts/build-data.mjs`, line 33), which skips `QA` rows
without an error. So a refresh to FY2027 with the same build script would also leave out the BRCA, Lynch and
Li-Fraumeni codes. We reported it in [icdwise issue 1](https://github.com/qinisolabs/icdwise/issues/1), suggesting
`[0-9A-Z]` in position 2 of both its patterns and a rebuild of the bundled code list.

**Two public regex examples reject all 18 letter-second codes** and accept every other well-formed code we tried, including codes deleted in FY2027:

- John D. Cook's [2019 post](https://www.johndcook.com/blog/2019/05/05/regex_icd_codes/):
  `[A-TV-Z][0-9][0-9AB]\.?[0-9A-TV-Z]{0,4}`. The post says the pattern has "only false positives", and the author
  tested it against the CDC code lists. (It is published for searching free text; we
  anchored it with `^…$` to use it as a validator.) The post also says separately that "special codes" may begin
  with U, which the pattern leaves out; FY2027 has three: `U07.0`, `U07.1` and `U09.9`.
- The regex101 library entry [EOGAAH](https://regex101.com/library/EOGAAH) (2024):
  `^[a-zA-Z]\d[a-zA-Z\d]\.?([a-zA-Z\d]{0,4})?$`.

**Two weeks into FY2027, 4 of 11 answered from FY2027**, and one of the four only because we supplied the file. The
HL7 community server answers from the 2026-04-01 release; on 15 October it returned "Unknown code 'QA1.791'" for
the BRCA2 code. Two packages still ship FY2025 data, so they reject every FY2026 code, not only the `QA` ones.

## What to change

1. **If you check the format, allow a letter in position 2.** In the 2019 pattern, change position 2 from `[0-9]`
   to `[0-9A-Z]`, and position 1 from `[A-TV-Z]` to `[A-Z]`; in the regex101 pattern, change position 2 from `\d` to
   `[a-zA-Z\d]`. On our 88 codes both edited patterns
   accept 18/18 letter-second codes and every other valid code. The edited regex101 pattern also accepts the junk
   string `XYZ`, so it is a looser pre-filter than the original. `check_fix.py` in the bundle reruns this on the 88
   codes. Against all 74,879 codes in the FY2027 file, the edited regex101 pattern and the 2019 pattern with
   positions 1 and 2 edited accept every code. With only position 2 edited, the 2019 pattern still rejects the three
   U codes, including `U07.1` COVID-19.
2. **Parse the release files without a shape filter.** A regex that picks "code lines" out of `icd10cm-codes-2027.txt`
   drops `QA` rows with no error, so your code list is short and a refresh does not fix it. The FY2026 file has
   74,719 codes; the same file through a filter that requires a digit in position 2 keeps 74,706. Compare your count.
3. **Treat format checks as a pre-filter.** Whether a code is valid depends on the release. Check it against the code
   list for the date of service, and record which release your tool or terminology server answers from.
4. **Test the codes themselves.** Add `QA0.0101`, `QA1.791` and `U07.1` to your validator tests, and a currency check that
   fails when an FY2027 code such as `QA1.71` is unknown.

## What this does not show

- It is a small set: 9 packages, most with modest download counts, plus 2 services. We did not test EHRs,
  clearinghouses, commercial encoders, databases with CHECK constraints, or HL7 v2 and X12 validators, and we do not
  know how often hand-written patterns like these appear in production code.
- Service behaviour is from one day, and package versions change. One package has an open issue to move to FY2027.
- `QA` codes are rare so far. We expect the FY2027 BRCA and Lynch codes to be used more than the FY2026 ones, but we
  have no usage data.
- Before the run, while writing the adapters, we read the source of four of the packages, including the one that
  fails. The result counts what each call returned, not what we read.
- A second AI agent reran the study the same day with fresh installs and the same code, and got byte-identical
  outputs. That shows the outputs are stable; it is not an independent reproduction.

## Reproduce

Everything is in [`bundle/`](bundle/): the 88 probe codes with their source descriptions, the adapter for each
tool's call, the pinned package versions, raw rows from every run, the scoring script and its output, the pattern
checks and `check_fix.py`, the rerun, and SHA-256 sums of every file and of the CDC/NCHS release files we used
(`inputs/SOURCES.md`). Our code is MIT-licensed; that licence does not cover the public-domain CDC/NCHS data or the
response excerpts from each tool in the raw rows. This work uses CDC/NCHS materials and is not endorsed by CDC, HHS or the U.S. Government.

Offline, from `bundle/`, with Python 3.12 and the standard library only, this recomputes the table from the raw rows
and checks every file:

```
python3 src/score.py run1 run2 > score.json && sha256sum -c SHA256SUMS && python3 src/table.py score.json
```

Count the FY2026 codes yourself (network). This prints 74719:

```
curl -s -o fy26.zip "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD10CM/2026/icd10cm-Code%20Descriptions-2026.zip" && unzip -p fy26.zip icd10cm-codes-2026.txt | grep -c .
```

With a digit required in position 2 it prints 74706:
`unzip -p fy26.zip icd10cm-codes-2026.txt | grep -cE '^[A-Z][0-9][0-9A-Z][0-9A-Z]{0,4} '`.

Check a pattern against every FY2027 code (network). With position 2 edited and position 1 left as `[A-TV-Z]`, the
2019 pattern prints the codes it rejects, `U070`, `U071` and `U099`; with `^[A-Z]` in position 1 it prints nothing:

```
curl -s -o fy27.zip "https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD10CM/2027/icd10cm-code-descriptions-2027.zip" && unzip -p fy27.zip icd10cm-code-descriptions-2027/icd10cm-codes-2027.txt | cut -d' ' -f1 | grep -vE '^[A-TV-Z][0-9A-Z][0-9AB]\.?[0-9A-TV-Z]{0,4}$'
```

The offline recompute is the supported check. `RESULTS.md` in the bundle also has the deviations from the protocol,
the data licence notes and a historical outline of how our containers were set up, which is a record, not a ready
recipe: it installs third-party packages and calls public APIs, so run it only in an isolated executor you control.
Results will change as packages and services move to newer releases.

---

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai.
