"""Create metadata-only wheels for an offline uv lockfile inspection example."""
import csv
import hashlib
import io
import base64
from pathlib import Path
import sys
import zipfile


def wheel(directory, name, requires=None):
    normalized = name.replace("-", "_")
    dist = normalized + "-1.0.0.dist-info"
    metadata = f"Metadata-Version: 2.1\nName: {name}\nVersion: 1.0.0\n"
    if requires:
        metadata += f"Requires-Dist: {requires}\n"
    files = {
        dist + "/METADATA": (metadata + "\n").encode(),
        dist + "/WHEEL": b"Wheel-Version: 1.0\nGenerator: example\nRoot-Is-Purelib: true\nTag: py3-none-any\n",
    }
    record = io.StringIO()
    writer = csv.writer(record, lineterminator="\n")
    for filename, data in files.items():
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip("=")
        writer.writerow([filename, "sha256=" + digest, len(data)])
    writer.writerow([dist + "/RECORD", "", ""])
    files[dist + "/RECORD"] = record.getvalue().encode()
    with zipfile.ZipFile(directory / f"{normalized}-1.0.0-py3-none-any.whl", "w") as z:
        for filename, data in files.items():
            info = zipfile.ZipInfo(filename, (2026, 10, 3, 0, 0, 0))
            z.writestr(info, data)


def main():
    directory = Path(sys.argv[1])
    directory.mkdir(parents=True, exist_ok=False)
    wheel(directory, "demo-leaf")
    wheel(directory, "demo-parent", "demo-leaf==1.0.0")
    (directory / "pyproject.toml").write_text('''[project]
name = "lock-inspection-demo"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = ["demo-parent==1.0.0"]
''')


if __name__ == "__main__":
    main()
