"""Make a synthetic local-wheel fixture in a new directory, without overwrites."""
import base64
import csv
import hashlib
import io
from pathlib import Path
import sys
import zipfile


def wheel_bytes(label):
    files = {
        'demo_pkg/data.txt': (label + '\n').encode(),
        'demo_pkg-1.0.0.dist-info/METADATA': b'Metadata-Version: 2.1\nName: demo-pkg\nVersion: 1.0.0\n',
        'demo_pkg-1.0.0.dist-info/WHEEL': b'Wheel-Version: 1.0\nGenerator: synthetic-fixture\nRoot-Is-Purelib: true\nTag: py3-none-any\n',
    }
    rows = []
    for name, data in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=')
        rows.append([name, 'sha256=' + digest, str(len(data))])
    record = 'demo_pkg-1.0.0.dist-info/RECORD'
    rows.append([record, '', ''])
    output = io.StringIO(newline='')
    csv.writer(output, lineterminator='\n').writerows(rows)
    files[record] = output.getvalue().encode()
    result = io.BytesIO()
    with zipfile.ZipFile(result, 'w', compression=zipfile.ZIP_STORED) as archive:
        for name, data in files.items():
            info = zipfile.ZipInfo(name, date_time=(2026, 1, 1, 0, 0, 0))
            info.external_attr = 0o644 << 16
            archive.writestr(info, data)
    return result.getvalue()


PROJECT = '''[project]
name = "relock-example"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["demo-pkg"]

[tool.uv]
package = false

[tool.uv.sources]
demo-pkg = { path = "demo_pkg-1.0.0-py3-none-any.whl" }
'''


def make_fixture(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=False)
    (destination / 'pyproject.toml').write_text(PROJECT)
    (destination / 'demo_pkg-1.0.0-py3-none-any.whl').write_bytes(wheel_bytes('original'))
    (destination / 'replacement.whl').write_bytes(wheel_bytes('replacement'))
    return destination


if __name__ == '__main__':
    if len(sys.argv) != 2:
        raise SystemExit('Usage: python3 make_fixture.py NEW_DIRECTORY')
    make_fixture(sys.argv[1])
    print('Created synthetic fixture; the wheel contains metadata and a text file, no Python code.')
