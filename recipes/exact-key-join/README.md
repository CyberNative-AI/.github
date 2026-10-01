# Keep large join keys exact

A reproducible native-pandas recipe from CyberNative AI LLC.
AI-assisted work checked within CyberNative AI LLC; no independent reproduction
is claimed.

In the tested environment (Python 3.12.3, pandas 3.0.6, NumPy 2.3.2), three
distinct integer keys joined on a group and a key produced nine rows when the
left key was signed int64 and the right key was uint64. `validate="one_to_one"`
did not raise. All nine rows were marked `both`, so the merge indicator alone
also failed to detect the wrong associations.

The probe uses arithmetic constants `2**60 + 1`, `+ 2`, `+ 3`; these are
deterministic fixtures, not customer records or generated model data.

## Native recipe

1. Keep the original exact keys. Never convert identifiers through float.
2. Agree what equality means: exact text, or an exact common integer type whose
   range contains every key. The supplied sample tests both native choices.
3. Resolve missing keys before joining. pandas matches null keys to null keys.
4. Keep `validate="one_to_one"` when that is the real cardinality contract.
5. Check exact expected value pairs and row count. If every left row must match,
   reject `left_only` rows as well. An inner join can conceal missing matches.
6. Resolve duplicates or unmatched keys at source. Do not deduplicate, trim,
   case-fold, drop rows or change the equality rule without agreement.

The sample helper converts only `key`; `group` stays integer 7. Agree the
equality and domain of every join component before adapting this example.

The common-signed-type path and exact-text path each yielded the expected three
rows with the correct value pairs. The text path rejected duplicate right keys,
missing matches, null keys, keys already stored as floats and unequal `001`/`1`
keys. It also preserved an unsigned key above signed-int64 range.

## Run

Start with Git and Python 3.12 installed. In a terminal, get the files and run
only this recipe in a separate local environment. These commands are for macOS
and Linux:

```sh
git clone --depth 1 https://github.com/CyberNative-AI/.github.git exact-key-recipe
cd exact-key-recipe/recipes/exact-key-join
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python probe.py
```

If you already have the repository, start inside `recipes/exact-key-join` and
skip the clone. On Windows, use `py -3.12` instead of `python3` and
`.venv\Scripts\python.exe` instead of `.venv/bin/python`.

The clone and dependency installation need network access. The probe itself
runs offline with authored fixtures; no input file or customer data is needed.
A completed run prints JSON with the Python, pandas and NumPy versions. The
recorded `result.json` shows nine rows and `correct: false` for the deliberately
failing `mixed_integer_baseline`, then three correct pairs for
`common_signed_integer` and `exact_text`. The five rejection controls each show
`rejected: true`. The failing baseline is the demonstration, not a failed setup.
Compare your versions and result with `result.json`; a different baseline result
can reflect a different library version and does not establish a defect.

If `requirements.txt` is missing, check that the terminal is inside
`recipes/exact-key-join`. If package installation fails, keep the error and
check Python and network access; do not install into system Python. If the probe
exits with an assertion or traceback, record your versions and the failing check
before adapting the recipe. Do not remove validation or apply it to production
data to make the demonstration pass.

The program uses only in-memory fixtures and prints JSON. It performs no network
calls and writes no files. `checked_join` is a sample-specific acceptance helper,
not an arbitrary dtype normalizer or a supported library API.

## Limits

One Python/pandas/NumPy combination and tiny in-memory fixtures were tested.
No memory, throughput, Excel/CSV import, nullable-dtype matrix or deployed
pipeline claim follows. Exact text casting cannot recover bits already lost in
a float or recover zeros removed at import. The integer cast is safe only after
range and domain checks; arbitrary unsigned casts can wrap. These examples do
not define whether zero padding, whitespace or case should be significant.
Rerunning an in-memory calculation proves repeatability, not sink idempotency.

## Sources

- [Original user report](https://github.com/pandas-dev/pandas/issues/61688):
  reported June 22, 2025; read as open on October 1, 2026 UTC. The public report
  requested an exact three-row result or an error for a mixed-type composite
  join; its displayed failing example returned five rows. This probe uses
  different arithmetic inputs and recorded nine rows in the failing arm.
- [Native merge API](https://pandas.pydata.org/docs/reference/api/pandas.merge.html):
  cardinality validation, merge indicator and null-key behavior. Read October 1,
  2026 UTC. These features are the substitute; no replacement join tool is needed
  for the tested scope.

If you run this recipe, voluntary feedback can include your Python, pandas and
NumPy versions and whether the expected row-count and value-pair assertions
passed. Do not include identifiers, source files or customer data. An internal
run or a download does not establish independent use.

## Recipe license

The MIT License below applies only to the four files in this recipe directory:
README.md, probe.py, requirements.txt and result.json. It does not license other
repository content, linked third-party material or installed dependencies;
those retain their own terms.

MIT License

Copyright (c) 2026 CyberNative AI LLC

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
