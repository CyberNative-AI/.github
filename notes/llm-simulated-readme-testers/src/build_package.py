"""Build the frozen reviewer packages (pre/post) from the ActivityBot clone. Stdlib only."""
import hashlib, json, subprocess, sys
from pathlib import Path

REPO = Path(sys.argv[1]); OUT = Path(sys.argv[2])
VERSIONS = {"pre": "fd68596346075f9e74c4fe2026c97b7816eef545", "post": "92089ff3155720eed88bf3aaf3ae3def81de79e0"}
DOCS = [".env.example", "README.md", "README_caddy.md", "README_docker.md", "README_nginx.md"]

def git(*a):
    return subprocess.run(["git", "-C", str(REPO), *a], check=True, capture_output=True).stdout

manifest = {}
for name, sha in VERSIONS.items():
    paths = git("ls-tree", "-r", "--name-only", sha).decode().splitlines()
    tree = sorted({p if not p.startswith("tests/") else "tests/ (PHP unit tests and JSON fixtures)" for p in paths})
    parts = ["# Repository file list\n\n" + "\n".join(tree) + "\n"]
    files = {}
    for d in DOCS:
        if d not in paths:
            continue
        body = git("show", f"{sha}:{d}").decode("utf-8")
        files[d] = hashlib.sha256(body.encode()).hexdigest()
        parts.append(f"# File: {d}\n\n````\n{body}\n````\n")
    text = "\n".join(parts)
    (OUT / f"{name}.md").write_text(text, encoding="utf-8", newline="\n")
    manifest[name] = {"commit": sha, "files": files, "package_sha256": hashlib.sha256(text.encode()).hexdigest(), "words": len(text.split())}
(OUT / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")
print(json.dumps(manifest, indent=2))
