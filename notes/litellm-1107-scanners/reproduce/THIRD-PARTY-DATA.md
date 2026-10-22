# Third-party data in this folder

`raw-rep1.tar.gz` and `raw-rep2.tar.gz` hold the unchanged output of trivy, grype, osv-scanner
and `pip-audit`. That output includes advisory records, descriptions, references and scores that
the scanners took from the databases below. That data belongs to its sources, and their terms
apply to it:

| Data in the raw output | Source | Terms |
|---|---|---|
| GHSA advisories (all four scanners) | [GitHub Advisory Database](https://github.com/github/advisory-database) | [CC BY 4.0](https://github.com/github/advisory-database/blob/main/LICENSE.md) |
| PYSEC advisories (osv-scanner, `pip-audit`) | [PyPA Advisory Database](https://github.com/pypa/advisory-database) | [CC BY 4.0](https://github.com/pypa/advisory-database/blob/main/LICENSE) |
| MAL malicious-package records (osv-scanner; MAL IDs also appear in grype and `pip-audit -s osv` output) | [OpenSSF Malicious Packages](https://github.com/ossf/malicious-packages) | [Apache 2.0](https://github.com/ossf/malicious-packages/blob/main/LICENSE); copy of the license: [`LICENSES/Apache-2.0.txt`](LICENSES/Apache-2.0.txt) |
| CVE descriptions and scores in grype's related vulnerabilities | [National Vulnerability Database](https://nvd.nist.gov/) (NIST) | [NVD terms of use](https://nvd.nist.gov/developers/terms-of-use) |
| EPSS scores in grype output | [EPSS](https://www.first.org/epss/) (FIRST) | as published by FIRST |

The scanners delivered this data through [OSV](https://google.github.io/osv.dev/data/), whose
source list gives the same licenses for the first three, and through the trivy and grype
databases. We did not edit it. None of these sources reviewed or endorsed this note.

Written by CyberNative AI LLC: `make_inputs.py`, `run_scanners.sh`, `score.py`,
`pip-audit.Dockerfile`, `score-rep1.json`, `score-rep2.json`, this file and the READMEs. The score
files summarize the raw output as outcomes, exit codes, advisory IDs, skip reasons and the last
line of each scanner's error output, cut to 200 characters. `LICENSES/Apache-2.0.txt` is the
unchanged license file from OpenSSF Malicious Packages.
