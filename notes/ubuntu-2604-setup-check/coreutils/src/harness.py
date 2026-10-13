"""Runs inside the arm container (network none, uid 1001). Executes each case's argv (shell=False) in a fresh
copy of the synthetic fixture and records rc/stdout/stderr/fs-state. Identical across arms except PATH.

usage: harness.py ARM CASES.jsonl OUT.jsonl
"""
import glob, hashlib, json, os, pathlib, re, shutil, stat, subprocess, sys, tempfile

ARM = sys.argv[1]
PATHS = {
    "gnu94": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "uutils": "/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
    "gnu97": "/opt/gnu97:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin",
}
FIXED_MTIME = 1760000000  # 2025-10-09, fixture files
STDIN_TEXT = ("banana 3\napple 10\nZebra\n  indented line\nv1.10.0\nv1.9.2\nhéllo wörld\na,b,c\n"
              "key=value\n{\"version\": \"1.2.3\"}\n\napple 10\n\ttabbed\tfield\nrefs/tags/v2.0.0\n")
F1 = STDIN_TEXT
F2 = "apple 10\ncherry 2\nbanana 3\n"
READERS_ALL = {"cat", "head", "tail", "wc", "sort", "uniq", "cut", "sha1sum", "sha224sum", "sha256sum", "sha384sum",
               "sha512sum", "md5sum", "b2sum", "cksum", "sum", "base64", "base32", "basenc", "od", "tac", "nl", "paste",
               "fold", "fmt", "expand", "unexpand", "comm", "join", "split", "csplit", "shuf", "pr", "tsort", "stat",
               "du", "ls", "dir", "vdir", "readlink", "realpath", "chmod", "chown", "chgrp", "truncate", "shred", "tee",
               "dd", "numfmt", "ptx", "touch", "rm", "unlink", "link"}
READERS_BUT_LAST = {"cp", "mv", "install", "ln"}


def build_fixture(root):
    root.mkdir(parents=True, exist_ok=True)
    files = {
        "f1.txt": F1, "f2.txt": F2, "README.md": "# demo\n\nText.\n", "VERSION": "1.4.2\n",
        "package.json": '{\n  "name": "demo",\n  "version": "1.4.2"\n}\n', "requirements.txt": "requests==2.32.0\nnumpy\n",
        "Cargo.toml": '[package]\nname = "demo"\nversion = "0.3.1"\n', "go.mod": "module example.com/demo\n\ngo 1.24\n",
        "d1/sub1.txt": "one\ntwo\n", "d1/inner/x.txt": "x\n", "d1/dist/demo-1.4.2.tar.gz": "tgz-bytes\n",
        "dist/demo-1.4.2.tar.gz": "tgz-bytes\n", "dist/demo-1.4.2-py3-none-any.whl": "whl-bytes\n",
        "build/out.bin": "\x00\x01binary\n", "script.sh": "#!/bin/sh\necho hi\n", "home/.profile": "# profile\n",
        "tmp/.keep": "",
    }
    for rel, txt in files.items():
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(txt)
    (root / "script.sh").chmod(0o755)
    os.symlink("f1.txt", root / "link1")
    os.symlink("missing.txt", root / "dangling")
    for p in sorted(root.rglob("*"), reverse=True):
        os.utime(p, (FIXED_MTIME, FIXED_MTIME), follow_symlinks=False)
    os.utime(root, (FIXED_MTIME, FIXED_MTIME))


def reroot(a):
    # absolute paths outside pseudo filesystems are rerooted into the case directory (mode B)
    if a.startswith("/") and not re.match(r"^/(dev|proc|sys)(/|$)", a):
        return "." + a
    if a.startswith("--") and "=/" in a:
        k, v = a.split("=", 1)
        return k + "=" + reroot(v)
    return a


def operands(argv):
    ops, after = [], False
    for a in argv[1:]:
        if a == "--": after = True; continue
        if not after and a.startswith("-") and a != "-": continue
        ops.append(a)
    return ops


def materialize(cwd, argv):
    name = argv[0]
    ops = operands(argv)
    if name in ("chmod", "chown", "chgrp"):
        ops = ops[1:]
    if name in READERS_BUT_LAST:
        ops = ops[:-1]
    elif name not in READERS_ALL:
        return
    for o in ops:
        if not o or o == "-" or any(ch in o for ch in "*?[") or "=" in o:
            continue
        p = (cwd / o)
        try:
            if os.path.lexists(p):
                continue
            p.parent.mkdir(parents=True, exist_ok=True)
            if o.endswith("/"):
                p.mkdir(parents=True, exist_ok=True); (p / "f1.txt").write_text(F1)
            else:
                p.write_text(F1)
            os.utime(p, (FIXED_MTIME, FIXED_MTIME))
        except OSError:
            pass


def expand_globs(cwd, argv):
    out = [argv[0]]
    for a in argv[1:]:
        if any(ch in a for ch in "*?[") and not a.startswith("-"):
            m = sorted(glob.glob(a, root_dir=cwd))
            out.extend(m if m else [a])
        else:
            out.append(a)
    return out


def snapshot(root):
    rows = []
    for dp, dns, fns in os.walk(root, followlinks=False):
        dns.sort()
        for n in sorted(dns + fns):
            p = os.path.join(dp, n)
            rel = os.path.relpath(p, root)
            st = os.lstat(p)
            if stat.S_ISLNK(st.st_mode):
                rows.append([rel, "l", os.readlink(p)])
            elif stat.S_ISDIR(st.st_mode):
                rows.append([rel, "d", oct(st.st_mode & 0o7777)])
            elif stat.S_ISREG(st.st_mode):
                h = hashlib.sha256(open(p, "rb").read()).hexdigest()[:16]
                rows.append([rel, "f", oct(st.st_mode & 0o7777), h])
            else:
                rows.append([rel, "o", oct(stat.S_IFMT(st.st_mode))])
    return sorted(rows)


CAP = 1 << 20  # AMENDMENT-01: stdout capped at 1 MiB, then the pipe is closed (child sees SIGPIPE/EPIPE)


def run_capped(argv, cwd, stdin, env, timeout=5.0):
    import selectors, time
    p = subprocess.Popen(argv, cwd=cwd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        p.stdin.write(stdin)
    except BrokenPipeError:
        pass
    p.stdin.close()
    sel = selectors.DefaultSelector()
    sel.register(p.stdout, selectors.EVENT_READ, "o"); sel.register(p.stderr, selectors.EVENT_READ, "e")
    so, se, trunc, open_ = bytearray(), bytearray(), False, 2
    end = time.monotonic() + timeout
    try:
        return _pump(p, sel, so, se, end)
    finally:
        # AMENDMENT-02: always release the selector and pipes (Python 3.14 GC left epoll fds open -> EMFILE)
        sel.close()
        for f in (p.stdout, p.stderr):
            try: f.close()
            except OSError: pass


def _pump(p, sel, so, se, end):
    import time
    trunc, open_ = False, 2
    while open_:
        left = end - time.monotonic()
        if left <= 0:
            p.kill(); p.wait()
            return "TIMEOUT", bytes(so), bytes(se), trunc
        for key, _ in sel.select(timeout=left):
            chunk = os.read(key.fileobj.fileno(), 65536)
            if not chunk:
                sel.unregister(key.fileobj); key.fileobj.close(); open_ -= 1; continue
            if key.data == "o":
                so += chunk
                if len(so) >= CAP:
                    del so[CAP:]; trunc = True
                    sel.unregister(key.fileobj); key.fileobj.close(); open_ -= 1
            elif len(se) < CAP:
                se += chunk
    try:
        rc = p.wait(timeout=max(0.1, end - time.monotonic()))
    except subprocess.TimeoutExpired:
        p.kill(); p.wait(); rc = "TIMEOUT"
    return rc, bytes(so), bytes(se), trunc


def main():
    cases = [json.loads(l) for l in open(sys.argv[2])]
    out = open(sys.argv[3], "w")
    base = pathlib.Path("/work")  # fixed path so absolute paths in output are identical across arms
    tmpl = base / "tmpl"
    build_fixture(tmpl)
    for c in cases:
        cwd = base / "case"
        if cwd.exists():
            shutil.rmtree(cwd, ignore_errors=True)
            if cwd.exists():
                os.system(f"chmod -R u+rwx '{cwd}' 2>/dev/null; rm -rf '{cwd}'")
        shutil.copytree(tmpl, cwd, symlinks=True)
        argv = list(c["argv"])
        if c["mode"] == "B":
            argv = [argv[0]] + [reroot(a) for a in argv[1:]]
            materialize(cwd, argv)
        argv = expand_globs(cwd, argv)
        before = snapshot(cwd)
        env = {"PATH": PATHS[ARM], "HOME": str(cwd / "home"), "USER": "runner", "LANG": "C.UTF-8",
               "TMPDIR": str(cwd / "tmp"), "GITHUB_ACTIONS": "true", "CI": "true",
               "FAKETIME": "2026-10-12 12:00:00", "LD_PRELOAD": "/usr/lib/x86_64-linux-gnu/faketime/libfaketime.so.1",
               "NO_FAKE_STAT": "1", "DONT_FAKE_MONOTONIC": "1"}
        stdin = STDIN_TEXT.encode() if c.get("piped_in") else b""
        rec = {"id": c["id"], "arm": ARM, "argv_run": argv}
        try:
            rc, so, se, trunc = run_capped(argv, cwd, stdin, env)
            rec.update(rc=rc, out=so[:4000].decode("utf-8", "backslashreplace"), out_trunc=trunc,
                       out_len=len(so), out_sha=hashlib.sha256(so).hexdigest()[:16],
                       err=se[:600].decode("utf-8", "backslashreplace"))
        except (FileNotFoundError, PermissionError, OSError) as e:
            rec.update(rc="EXEC_ERROR", out="", out_len=0, out_sha="exec_error", err=type(e).__name__ + ": " + str(e)[:200])
        try:
            after = snapshot(cwd)
        except OSError as e:
            after = [["SNAPSHOT_ERROR", type(e).__name__]]
        bset, aset = {json.dumps(r) for r in before}, {json.dumps(r) for r in after}
        rec["fs_added"] = sorted(aset - bset)[:40]
        rec["fs_removed"] = sorted(bset - aset)[:40]
        rec["fs_sha"] = hashlib.sha256(json.dumps(after).encode()).hexdigest()[:16]
        out.write(json.dumps(rec, sort_keys=True) + "\n")
        out.flush()
    out.close()


if __name__ == "__main__":
    main()
