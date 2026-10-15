# Source files (CDC/NCHS ICD-10-CM releases)

All files are public-domain US government releases from the CDC/NCHS ICD-10-CM directory
<https://ftp.cdc.gov/pub/Health_Statistics/NCHS/Publications/ICD10CM/>. `SOURCES.sha256` lists their sha256 under the
short local names in the first column below; a second download on 2026-10-15 matched all seven hashes.

This work is not endorsed by the Centers for Disease Control and Prevention (CDC), the U.S. Department of Health and
Human Services (HHS) or the United States Government. The official files are available without charge from CDC/NCHS at
the links below.

| Local name | URL (under the directory above) |
|---|---|
| `fy25-desc.zip` | `2025/ICD10-CM%20Code%20Descriptions%202025.zip` |
| `fy26-desc.zip` | `2026/icd10cm-Code%20Descriptions-2026.zip` |
| `icd10cm-code-descriptions-2027.zip` | `2027/icd10cm-code-descriptions-2027.zip` |
| `icd10cm-addenda-2027.zip` | `2027/icd10cm-addenda-2027.zip` |
| `icd10cm-April-1-2026-XML.zip` | `2026-Update/icd10cm-April-1-2026-XML.zip` |
| `icd10cm-addenda-April-1-2026.zip` | `2026-Update/icd10cm-addenda-April-1-2026.zip` |
| `icd10cm-Code_Descriptions-April-1-2026.zip` | `2026-Update/icd10cm-Code%20Descriptions-April-1-2026.zip` |

`src/prep.py` reads four of them, extracted into one directory `x/`:

```
unzip -d x/fy25-desc fy25-desc.zip
unzip -d x/fy26-desc fy26-desc.zip
unzip -d x/icd10cm-code-descriptions-2027 icd10cm-code-descriptions-2027.zip
unzip -d x/apr26-xml icd10cm-April-1-2026-XML.zip
python3 -I src/prep.py x probes.jsonl > probes.meta.json
```

This rebuilds `inputs/probes.jsonl` (sha256 `d257358b0b0e833420b1d231f72ef8d2c3eac78831ec7d5d7cbe123c655c9152`) and
`inputs/probes.meta.json` byte for byte; we checked this from fresh downloads on 2026-10-15. The two addenda zips and
the April 2026 descriptions zip were downloaded with the others; no script reads them. `src/prep.py` uses the April
2026 tabular XML only to check that no code new in FY2027 had already appeared in the April 2026 update
(`apr26_added_billable` in `probes.meta.json` is empty).
