# Copyright (c) 2026 CyberNative AI LLC
# SPDX-License-Identifier: MIT
import base64, hashlib, pathlib, sys, zipfile

root_config = '''[project]
name = "release-root"
version = "0.0.0"
requires-python = ">=3.12"
[dependency-groups]
dev = ["dev-marker==1.0.0"]
[tool.uv]
package = false
default-groups = ["dev"]
no-index = true
find-links = ["wheels"]
[tool.uv.workspace]
members = ["member"]
'''

member_config = '''[project]
name = "release-member"
version = "0.0.0"
[dependency-groups]
docs = ["docs-marker==1.0.0"]
dev = ["dev-marker==1.0.0"]
[tool.uv]
package = false
default-groups = ["docs"]
'''

def wheel(directory, name):
    folder = name.replace('-', '_') + '-1.0.0.dist-info'
    files = {
        folder + '/METADATA': f'Metadata-Version: 2.1\nName: {name}\nVersion: 1.0.0\n',
        folder + '/WHEEL': 'Wheel-Version: 1.0\nGenerator: synthetic-fixture\nRoot-Is-Purelib: true\nTag: py3-none-any\n',
    }
    records = []
    for filename, content in files.items():
        data = content.encode()
        digest = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode().rstrip('=')
        records.append(f'{filename},sha256={digest},{len(data)}')
    records.append(folder + '/RECORD,,')
    files[folder + '/RECORD'] = '\n'.join(records) + '\n'
    with zipfile.ZipFile(directory / (name.replace('-', '_') + '-1.0.0-py3-none-any.whl'), 'w') as archive:
        for filename, content in files.items():
            archive.writestr(filename, content)

if len(sys.argv) != 2:
    raise SystemExit("Usage: python3 make_fixture.py NEW_DIRECTORY")
directory = pathlib.Path(sys.argv[1])
directory.mkdir()  # An existing directory is an error; nothing is overwritten.
(directory / "member").mkdir()
(directory / "wheels").mkdir()
(directory / "pyproject.toml").write_text(root_config)
(directory / "member/pyproject.toml").write_text(member_config)
for name in ("dev-marker", "docs-marker"):
    wheel(directory / "wheels", name)
print("Synthetic workspace created.")
