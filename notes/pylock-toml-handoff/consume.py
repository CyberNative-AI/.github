"""Consumer phase. Runs inside the target image with the tools venv python.

Usage: <tools-venv>/bin/python /x/consume.py TARGET   (TARGET = 3.12 or 3.10)
Writes /w/results/<TARGET>/cells.jsonl (one row per install) and oracle.jsonl.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # 3.10
    import tomli as tomllib
from packaging.markers import Marker, default_environment
from packaging.specifiers import SpecifierSet

TARGET = sys.argv[1]
W = Path("/w")
X = Path("/x")
B = W / "tools" / f"venv{TARGET}" / "bin"
PY = "/usr/local/bin/python3"
CUT = "2026-10-14T00:00:00Z"
LOCKS = W / "locks"
LABEL = sys.argv[2] if len(sys.argv) > 2 else TARGET
OUT = W / "results" / LABEL
SCR = W / "scratch" / LABEL
EXCLUDE = {"pip", "setuptools", "wheel"}
ENV = {
    **os.environ,
    "HOME": str(W / "home"),
    "UV_CACHE_DIR": str(W / "cache" / "uv"),
    "PIP_CACHE_DIR": str(W / "cache" / "pip"),
    "PDM_CACHE_DIR": str(W / "cache" / "pdm"),
    "POETRY_CACHE_DIR": str(W / "cache" / "poetry"),
    "UV_PYTHON_DOWNLOADS": "never",
    "PDM_CHECK_UPDATE": "false",
    "PIP_DISABLE_PIP_VERSION_CHECK": "1",
    "PATH": f"{B}:/usr/local/bin:/usr/bin:/bin",
}
ENV.pop("VIRTUAL_ENV", None)

SEL_FLAGS = {  # native install flags, identical selection to the producer export
    "uv": {"S0": ["--no-default-groups"], "S1": ["--no-default-groups", "--extra", "http"],
           "S2": ["--no-default-groups", "--group", "lint"], "M": ["--all-extras", "--all-groups"]},
    "uvc": {"S0": [], "S1": ["--extra", "http"], "S2": ["--group", "pyproject.toml:lint"],
            "M": ["--all-extras", "--group", "pyproject.toml:lint", "--group", "pyproject.toml:dev"]},
    "pdm": {"S0": ["--prod"], "S1": ["--prod", "-G", "http"], "S2": ["-G", "lint", "--without", "dev"],
            "M": ["-G", ":all"]},
    "poetry": {"S0": ["--only", "main"], "S1": ["--only", "main", "--extras", "http"],
               "S2": ["--with", "lint", "--without", "dev"], "M": ["--all-extras", "--all-groups"]},
}


def sh(cmd: list[str], cwd: Path | None = None, env: dict | None = None, timeout: int = 600) -> tuple[int, str]:
    try:
        p = subprocess.run(cmd, cwd=cwd, env=env or ENV, capture_output=True, text=True, timeout=timeout)
        return p.returncode, (p.stdout + p.stderr)[-2500:]
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


def installed(python: str) -> dict[str, str] | None:
    code = ("import importlib.metadata as m, json;"
            "print(json.dumps(sorted({(d.metadata['Name'] or '').lower().replace('_','-'): d.version"
            " for d in m.distributions()}.items())))")
    rc, out = sh([python, "-c", code])
    if rc != 0:
        return None
    rows = json.loads(out.strip().splitlines()[-1])
    return {k: v for k, v in rows if k not in EXCLUDE}


def fresh_venv(path: Path) -> str:
    if path.exists():
        shutil.rmtree(path)
    rc, out = sh([PY, "-m", "venv", "--without-pip", str(path)])
    assert rc == 0, out
    return str(path / "bin" / "python")


def cell(row: dict, cmd: list[str], venv: Path, cwd: Path | None = None, python: str | None = None,
         env: dict | None = None) -> dict:
    t0 = time.time()
    rc, out = sh(cmd, cwd=cwd, env=env)
    row.update(rc=rc, tail=out, seconds=round(time.time() - t0, 1), cmd=" ".join(cmd))
    row["installed"] = installed(python or str(venv / "bin" / "python")) if (python or venv.exists()) else None
    return row


def run_pylock(src: Path, producer: str, sel: str, consumer: str, extra: list[str], tag: str) -> dict:
    cid = f"{producer}/{sel}/pylock/{consumer}{tag}"
    d = SCR / cid.replace("/", "__")
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    shutil.copy(src, d / "pylock.toml")
    v = d / "venv"
    row = {"cell": cid, "producer": producer, "sel": sel, "kind": "pylock", "consumer": consumer,
           "consume_sel": tag.strip("+") or "default", "target": TARGET}
    if consumer == "pip":
        py = fresh_venv(v)
        return cell(row, [str(B / "python"), "-m", "pip", "--python", py, "install", "-r", "pylock.toml"], v, cwd=d)
    if consumer == "uv-install":
        py = fresh_venv(v)
        return cell(row, [str(B / "uv"), "pip", "install", "--python", py, "-r", "pylock.toml", *extra], v, cwd=d)
    if consumer == "uv-sync":
        py = fresh_venv(v)
        return cell(row, [str(B / "uv"), "pip", "sync", "--python", py, "pylock.toml", *extra], v, cwd=d)
    if consumer == "pipenv":
        env = {**ENV, "PIPENV_VENV_IN_PROJECT": "1", "PIPENV_YES": "1", "PIPENV_NOSPIN": "1",
               "PIPENV_IGNORE_VIRTUALENVS": "1", "PIPENV_DONT_USE_PYENV": "1"}
        r = cell(row, [str(B / "pipenv"), "sync", "--python", PY], d / ".venv", cwd=d, env=env)
        r["pipfile_created"] = (d / "Pipfile").exists()
        return r
    raise ValueError(consumer)


def run_req(src: Path, producer: str, sel: str, consumer: str) -> dict:
    cid = f"{producer}/{sel}/req/{consumer}"
    d = SCR / cid.replace("/", "__")
    if d.exists():
        shutil.rmtree(d)
    d.mkdir(parents=True)
    shutil.copy(src, d / "requirements.txt")
    v = d / "venv"
    py = fresh_venv(v)
    row = {"cell": cid, "producer": producer, "sel": sel, "kind": "req", "consumer": consumer,
           "consume_sel": "default", "target": TARGET}
    if consumer == "pip":
        return cell(row, [str(B / "python"), "-m", "pip", "--python", py, "install", "-r", "requirements.txt"], v, cwd=d)
    return cell(row, [str(B / "uv"), "pip", "install", "--python", py, "-r", "requirements.txt"], v, cwd=d)


def run_native(producer: str, sel: str) -> dict:
    base, fx = producer.split("-", 1)
    cid = f"{producer}/{sel}/native/{base}"
    d = SCR / cid.replace("/", "__")
    if d.exists():
        shutil.rmtree(d)
    row = {"cell": cid, "producer": producer, "sel": sel, "kind": "native", "consumer": base,
           "consume_sel": sel, "target": TARGET}
    if base == "pip":
        d.mkdir(parents=True)
        shutil.copy(W / "proj" / producer / f"{sel}.in", d / "req.in")
        py = fresh_venv(d / "venv")
        return cell(row, [str(B / "python"), "-m", "pip", "--python", py, "install", "--uploaded-prior-to", CUT,
                          "-r", "req.in"], d / "venv", cwd=d)
    shutil.copytree(W / "proj" / producer, d, ignore=shutil.ignore_patterns(".venv", "__pypackages__"))
    v = d / "venv"
    flags = SEL_FLAGS[base][sel]
    if base == "uv":
        env = {**ENV, "UV_PROJECT_ENVIRONMENT": str(v)}
        return cell(row, [str(B / "uv"), "sync", "--frozen", "--no-install-project", "--python", PY, *flags],
                    v, cwd=d, env=env)
    if base == "uvc":
        py = fresh_venv(v)
        return cell(row, [str(B / "uv"), "pip", "install", "--python", py, "--exclude-newer", CUT,
                          "-r", "pyproject.toml", *flags], v, cwd=d)
    py = fresh_venv(v)
    env = {**ENV, "VIRTUAL_ENV": str(v), "PATH": f"{v}/bin:{ENV['PATH']}"}
    if base == "pdm":
        sh([str(B / "pdm"), "use", "-f", py], cwd=d, env=env)
        return cell(row, [str(B / "pdm"), "sync", "--no-self", *flags], v, cwd=d, env=env)
    if base == "poetry":
        env["POETRY_VIRTUALENVS_CREATE"] = "false"
        return cell(row, [str(B / "poetry"), "install", "--no-root", "--no-interaction", *flags], v, cwd=d, env=env)
    raise ValueError(producer)


def oracle(path: Path, extras: set[str] | None, groups: set[str] | None) -> dict:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    env = dict(default_environment())
    envs = data.get("environments")
    reasons = []
    if envs and not any(Marker(m).evaluate(env, context="lock_file") for m in envs):
        reasons.append("environments")
    rp = data.get("requires-python")
    if rp and env["python_full_version"] not in SpecifierSet(rp):
        reasons.append("requires-python")
    sel_groups = set(groups) if groups is not None else set(data.get("default-groups", []))
    lenv = {**env, "extras": frozenset(extras or set()), "dependency_groups": frozenset(sel_groups)}
    chosen = {}
    for p in data.get("packages", []):
        m = p.get("marker")
        if m is None or Marker(m).evaluate(lenv, context="lock_file"):
            name = p["name"].lower().replace("_", "-")
            if "version" in p:
                chosen[name] = p["version"]
            else:
                chosen[name] = None
    top = {k: data.get(k) for k in ("lock-version", "environments", "requires-python", "extras",
                                    "dependency-groups", "default-groups", "created-by")}
    return {"refuse": reasons, "set": dict(sorted(chosen.items())), "top": top}


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    SCR.mkdir(parents=True, exist_ok=True)
    jobs = []
    orc = []
    for pl in sorted(LOCKS.glob("*/*/pylock.toml")):
        producer, sel = pl.parts[-3], pl.parts[-2]
        for consumer in ("pip", "uv-install", "uv-sync", "pipenv"):
            jobs.append(("pylock", pl, producer, sel, consumer, [], ""))
        orc.append({"lock": f"{producer}/{sel}", "consume_sel": "default", **oracle(pl, None, None)})
        if sel == "M":
            # Amendment 02: uv pip install has no --no-default-groups; "+S1" keeps default-groups.
            for tag, fl, ex, gr in (("+S1", ["--extra", "http"], {"http"}, None),
                                    ("+S2", ["--group", "lint"], set(), {"lint"})):
                jobs.append(("pylock", pl, producer, sel, "uv-install", fl, tag))
                orc.append({"lock": f"{producer}/{sel}", "consume_sel": tag.strip("+"), **oracle(pl, ex, gr)})
    for rq in sorted(LOCKS.glob("*/*/requirements.txt")):
        producer, sel = rq.parts[-3], rq.parts[-2]
        for consumer in ("pip", "uv-install"):
            jobs.append(("req", rq, producer, sel, consumer))
    for prod in sorted(p.name for p in LOCKS.iterdir() if p.is_dir()):
        for sel in ("S0", "S1", "S2", "M"):
            if (LOCKS / prod / sel).exists():
                jobs.append(("native", prod, sel))
    (OUT / "oracle.jsonl").write_text("".join(json.dumps(r, sort_keys=True) + "\n" for r in orc), encoding="utf-8")

    def go(j):
        try:
            if j[0] == "pylock":
                return run_pylock(*j[1:])
            if j[0] == "req":
                return run_req(*j[1:])
            return run_native(*j[1:])
        except Exception as exc:  # noqa: BLE001
            return {"cell": repr(j[:5]), "error": f"{type(exc).__name__}: {exc}", "target": TARGET}

    with ThreadPoolExecutor(max_workers=4) as pool, open(OUT / "cells.jsonl", "w", encoding="utf-8") as fh:
        for r in pool.map(go, jobs):
            fh.write(json.dumps(r, sort_keys=True) + "\n")
            fh.flush()
    print("cells", len(jobs))


if __name__ == "__main__":
    main()
