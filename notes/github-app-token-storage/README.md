# GitHub App tokens: a SQLite test can miss the length limit

GitHub's [October 2 rollout notice](https://github.blog/changelog/2026-10-02-stateless-github-app-installation-tokens-rolled-out/) says newly minted installation tokens now use the stateless format by default. They are roughly 520 characters long instead of 40. Treat them as opaque strings; 520 is not a new exact-length validation rule.

If your local integration test uses SQLite, a column declared `VARCHAR(40)` can accept the longer value. That passing test does not prove compatibility with a deployed storage layer that enforces a 40-character limit.

## Reproduce the difference

Download [probe.py](./probe.py), then run it with Python 3 and its standard-library SQLite module:

```sh
python3 probe.py
```

Our October 4 run used Python 3.12.3 and SQLite 3.45.1:

```text
SQLite 3.45.1
VARCHAR(40): input=40, stored=40, equal=True
CHECK <=40: input=40, accepted
VARCHAR(40): input=520, stored=520, equal=True
CHECK <=40: input=520, rejected
PASS: declared length and enforced length differ in this SQLite fixture
```

The script uses only repeated `A` characters in an in-memory database. They are size surrogates, not GitHub tokens. It checks exact readback and exercises an explicit length constraint with both sizes. It does not read environment variables, open a database file or contact a service.

SQLite [ignores the numeric length in declarations such as `VARCHAR(255)`](https://sqlite.org/datatype3.html#affinity_name_examples). The explicit `CHECK(length(value) <= 40)` in this fixture has different behavior. This is documented SQLite behavior.

## What to change in your compatibility test

Run the storage round trip against the same engine and constraints your deployed application uses. Check that the returned value equals the input; a successful insert alone can miss truncation elsewhere in the path. Include application validation and any transport limits in your integration coverage, and keep real credentials out of diagnostic output.

GitHub also calls out legacy length validators, small storage limits, long authorization headers and old redaction patterns. Its temporary format-override header will stop being respected on November 30, 2026; see the [rollout notice](https://github.blog/changelog/2026-10-02-stateless-github-app-installation-tokens-rolled-out/) for the migration guidance.

**Limit:** this is a synthetic SQLite storage demonstration. We did not mint a token, test authentication, inspect a production database, exercise a proxy or evaluate a secret detector. A passing fixture is not end-to-end GitHub compatibility.

CyberNative AI LLC · [Corrections](mailto:hello@cybernative.ai)
