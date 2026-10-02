# uv sync succeeds, but a package file is missing: inspect RECORD first

Scope: ordinary filesystem `.dist-info` installations. The example was tested with
Python 3.12.3 on Linux on 2 October 2026. It does not run uv sync, import the named
package, load model weights, repair an environment or check file contents.

A [24 September report](https://github.com/astral-sh/uv/issues/21968) describes an
installed distribution whose metadata remained after its NCCL library disappeared.
The reporter recovered it with a targeted reinstall, but asked how to detect
missing files first. The original uv/Python versions and cause of file loss were
not established. This example does not reproduce that incident.

Start with uv's [native environment checks](https://docs.astral.sh/uv/pip/inspection/).
`uv pip check` checks dependency compatibility; it can also flag broken wheel
metadata. In our synthetic fixture, uv 0.10.7 returned 0 after a recorded data file
was removed, while this example reported that missing path. A compatible
dependency set and a file that still exists are separate observations. This is
not a test of the latest uv release or of the report's missing NCCL library.

For one distribution, read its installed `RECORD` and check each recorded path.
Use the affected environment's Python and the **distribution name**, which can
differ from its import name. Save this example as `check_record_presence.py`:

```python
import csv
import io
import stat
import sys
from pathlib import Path
from importlib.metadata import PackageNotFoundError, distribution

if len(sys.argv) != 2:
    raise SystemExit("Usage: python check_record_presence.py DISTRIBUTION")
try:
    dist = distribution(sys.argv[1])
    record = dist.read_text("RECORD")
except (PackageNotFoundError, OSError, ValueError):
    print("UNKNOWN: distribution or metadata unavailable or invalid")
    raise SystemExit(2)
if not record or len(record) > 1_000_000:
    print("UNKNOWN: RECORD absent, empty, unreadable or too large")
    raise SystemExit(2)
try:
    rows = list(csv.reader(io.StringIO(record), strict=True))
except csv.Error:
    print("UNKNOWN: malformed RECORD")
    raise SystemExit(2)
if not rows or len(rows) > 10_000 or any(len(r) != 3 or not r[0] for r in rows):
    print("UNKNOWN: invalid or oversized RECORD")
    raise SystemExit(2)
missing = unknown = 0
for relative, recorded_hash, recorded_size in rows:
    try:
        mode = Path(dist.locate_file(relative)).stat().st_mode
        if not stat.S_ISREG(mode):
            unknown += 1
            print("UNKNOWN: not a regular file", repr(relative))
    except FileNotFoundError:
        missing += 1
        print("MISSING:", repr(relative))
    except (OSError, TypeError, ValueError, NotImplementedError):
        unknown += 1
        print("UNKNOWN: cannot inspect", repr(relative))
print(f"recorded={len(rows)} missing={missing} unknown={unknown}")
raise SystemExit(2 if unknown else 1 if missing else 0)
```

For a project environment on Linux/macOS, run:

```sh
.venv/bin/python check_record_presence.py nvidia-nccl-cu13
```

Replace the interpreter path and distribution name for your installation. The
script reads metadata and filesystem status; it does not read library contents.
Its output can contain local filenames. Keep it local unless you have reviewed
what you intend to share.

- Exit **1**: at least one recorded path was missing, with no unknown path checks.
  For example, a synthetic missing file produced `MISSING: 'presence_demo/lib.dat'`
  and `recorded=5 missing=1 unknown=0`.
- Exit **2**: the check was incomplete. Missing/unreadable/invalid metadata and
  inaccessible paths do not become a clean result. Any printed missing paths
  remain observations even when another check is unknown.
- Exit **0**: no missing recorded regular files were found at that moment. This
  does not verify hashes, sizes, imports, dynamic-library loading, unlisted files,
  package authenticity or correctness. An existing changed file also returns 0.

Read `RECORD` directly here. The [CPython 3.13.15 implementation](https://github.com/python/cpython/blob/v3.13.15/Lib/importlib/metadata/__init__.py#L530)
filters missing paths out of `Distribution.files`; testing only that returned
list can omit precisely the paths you want to find. Python 3.13.15 was source-read,
not executed for this example.

This check covers one ordinary installed distribution and its recorded paths,
not editable/zip/custom installations or a whole environment. It is a snapshot;
an installation changing while it runs can produce transient findings. Investigate
a missing path before choosing a repair. The report's targeted reinstall is its
observed recovery, not a universal diagnosis or an instruction to clear caches.

References: [Python distribution metadata](https://docs.python.org/3.12/library/importlib.metadata.html#distributions),
[Distribution API](https://importlib-metadata.readthedocs.io/en/stable/api.html#importlib_metadata.Distribution),
and [PyPA installed-file records](https://packaging.python.org/en/latest/specifications/recording-installed-packages/#the-record-file).

Prepared by CyberNative AI LLC with AI assistance. Corrections: hello@cybernative.ai.
