"""Extract coreutils invocations from bash `run:` steps of GitHub Actions jobs that run on ubuntu-latest.

Output: data/invocations.jsonl, one row per (repo, workflow, job, step, statement) coreutils call, with
the argv after `${{ }}`/parameter substitution to fixture tokens, plus stdin/stdout/exit-context flags.
Parsing only (YAML + shfmt AST); nothing from the repos is executed here.
"""
import json, pathlib, re, subprocess, sys, hashlib, random

ROOT = pathlib.Path(__file__).resolve().parent.parent
SHFMT = str(ROOT / "tools" / "shfmt")
BUILTINS = {"[", "test", "echo", "printf", "pwd", "true", "false"}  # bash builtins shadow these
WRAPPERS = {"timeout", "nice", "nohup", "stdbuf", "env", "chroot", "runcon"}
PROGRAMS = set((ROOT / "data" / "gnu94-programs.txt").read_text().split("\n")[-1].split()) - BUILTINS - {"md5sum.textutils"}
NON_CU_PREFIX = {"sudo", "time", "command", "exec", "builtin"}
GHEXPR = re.compile(r"\$\{\{.*?\}\}", re.S)


class Lit(str):
    pass


def yaml_load(text):
    import yaml
    class L(yaml.SafeLoader):
        pass
    # keep 'on' as a string key; we never need it
    L.yaml_implicit_resolvers = {k: [r for r in v if r[0] != "tag:yaml.org,2002:bool"] for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()}
    return yaml.load(text, Loader=L)


def runs_on_latest(job):
    ro = job.get("runs-on")
    vals = []
    def add(v):
        if isinstance(v, str): vals.append(v)
        elif isinstance(v, list): [add(x) for x in v]
        elif isinstance(v, dict):
            add(v.get("labels"))
    add(ro)
    joined = " ".join(vals)
    if "ubuntu-latest" in joined:
        return True
    m = re.search(r"\$\{\{\s*matrix\.([A-Za-z0-9_\-]+)", joined)
    if m:
        mat = (job.get("strategy") or {}).get("matrix")
        if isinstance(mat, dict):
            key = m.group(1)
            cand = mat.get(key)
            texts = json.dumps(cand) + json.dumps(mat.get("include", []))
            return "ubuntu-latest" in texts
    return False


def shell_is_bash(shell):
    if shell is None:
        return True
    s = str(shell).strip()
    return s in ("bash", "sh") or s.startswith("bash ") or s.startswith("sh ")


def word_value(word):
    """Return (string, kind) where kind in {'lit','sub'}; expansions replaced by fixture tokens."""
    parts = word.get("Parts", [])
    out, sub, glob = [], False, False
    def walk(ps, quoted):
        nonlocal sub, glob
        for p in ps:
            t = p.get("Type")
            if t == "Lit":
                v = p.get("Value", "")
                if not quoted:
                    if re.search(r"[*?]|\[.+\]", v): glob = True
                    v = re.sub(r"\\(.)", r"\1", v)
                out.append(v)
            elif t == "SglQuoted":
                out.append(p.get("Value", ""))
            elif t == "DblQuoted":
                walk(p.get("Parts", []), True)
            else:  # ParamExp, CmdSubst, ArithmExp, ProcSubst, ExtGlob, BraceExp...
                sub = True
                out.append("\x00")
    walk(parts, False)
    s = "".join(out)
    if sub:
        s = "f1.txt" if s == "\x00" else s.replace("\x00", "d1")
    return s, ("sub" if sub else "lit"), glob


def collect(node, ctx, acc):
    """Walk shfmt JSON. ctx: dict(piped_in, piped_out, consumed, tolerated)."""
    if isinstance(node, list):
        for n in node: collect(n, ctx, acc)
        return
    if not isinstance(node, dict):
        return
    t = node.get("Type")
    if t == "BinaryCmd":
        op = node.get("Op")
        # shfmt ops: 10 '&&', 11 '||', 12 '|', 13 '|&' (version-dependent); use the source op text
        opstr = op
        X, Y = node.get("X"), node.get("Y")
        if op in ("|", "|&") or opstr in ("|", "|&"):
            # without pipefail (GitHub's implicit `bash -e {0}`), only the last stage's status counts
            xctx = {**ctx, "piped_out": True}
            if not ctx.get("pipefail"):
                xctx["tolerated"] = True
            collect(X, xctx, acc)
            collect(Y, {**ctx, "piped_in": True}, acc)
        elif op in ("||",) or opstr == "||":
            collect(X, {**ctx, "tolerated": True}, acc)
            collect(Y, ctx, acc)
        elif op in ("&&",) or opstr == "&&":
            collect(X, {**ctx, "tolerated": True}, acc)
            collect(Y, ctx, acc)
        else:
            collect(X, ctx, acc); collect(Y, ctx, acc)
        return
    if t in ("IfClause", "WhileClause"):
        collect(node.get("Cond"), {**ctx, "tolerated": True}, acc)
        collect(node.get("Then") or node.get("Do"), ctx, acc)
        collect(node.get("Else"), ctx, acc)
        return
    if "Cmd" in node and "Position" in node:
        # a Stmt
        redirs = node.get("Redirs") or []
        rctx = dict(ctx)
        rctx["line"] = (node.get("Position") or {}).get("Line")
        for r in redirs:
            op = r.get("Op")
            if op in (">", ">>", "&>", ">|", "&>>"):
                if "N" not in r or (r.get("N") or {}).get("Value") in (None, "1"):
                    rctx["consumed"] = True
            if op in ("<", "<<", "<<<", "<<-"):
                rctx["piped_in"] = True
        if node.get("Negated"):
            rctx["tolerated"] = True
        collect(node["Cmd"], rctx, acc)
        return
    if t == "CallExpr":
        args = node.get("Args") or []
        vals = [word_value(w) for w in args]
        # nested command substitutions inside words and assignment values
        for w in args:
            for p in w.get("Parts", []):
                find_cmdsubst(p, ctx, acc)
        for a in (node.get("Assigns") or []):
            for p in (a.get("Value") or {}).get("Parts", []):
                # bare assignment: the substitution's status is the statement's status (trips -e);
                # assignment prefixed to a command: ignored
                find_cmdsubst(p, ctx, acc, tolerated=bool(args) or bool(ctx.get("tolerated")))
        i, sudo = 0, False
        while i < len(vals) and vals[i][1] == "lit" and vals[i][0] in NON_CU_PREFIX:
            if vals[i][0] == "sudo": sudo = True
            i += 1
            while i < len(vals) and vals[i][0].startswith("-") and vals[i][1] == "lit":
                i += 1
        if i >= len(vals) or vals[i][1] != "lit":
            return
        name = vals[i][0].rsplit("/", 1)[-1] if vals[i][0].startswith("/usr/bin/") or vals[i][0].startswith("/bin/") else vals[i][0]
        if name not in PROGRAMS:
            return
        argv = [v[0] for v in vals[i:]]
        argv[0] = name
        kinds = [v[1] for v in vals[i + 1:]]
        globs = [v[2] for v in vals[i + 1:]]
        if name in WRAPPERS:
            # keep the wrapper's own options/operands up to the child command; child -> 'true'
            j = 1
            while j < len(argv) and (argv[j].startswith("-") or (name == "timeout" and j == len([a for a in argv[1:j] if not a.startswith('-')]) + 1 and re.match(r"^[0-9.]+[smhd]?$", argv[j])) or (name == "env" and "=" in argv[j])):
                j += 1
            if name == "timeout" and j < len(argv) and re.match(r"^[0-9.]+[smhd]?$", argv[j]):
                j += 1
            if name == "nice" and j < len(argv) and re.match(r"^-?[0-9]+$", argv[j]):
                j += 1
            argv = argv[:j] + (["true"] if j < len(argv) or name != "env" else [])
            kinds, globs = kinds[:j - 1], globs[:j - 1]
        acc.append({"argv": argv, "sub": "sub" in kinds, "glob": any(globs), "sudo": sudo,
                    "piped_in": bool(ctx.get("piped_in")), "consumed": bool(ctx.get("piped_out") or ctx.get("consumed") or ctx.get("subst")),
                    "tolerated": bool(ctx.get("tolerated")), "line": ctx.get("line")})
        return
    for k, v in node.items():
        if k in ("Pos", "End"): continue
        if isinstance(v, (dict, list)):
            if isinstance(v, dict) and v.get("Type") == "CmdSubst":
                collect(v.get("Stmts"), {**ctx, "subst": True, "piped_in": False}, acc)
            else:
                collect(v, ctx, acc)


def find_cmdsubst(p, ctx, acc, tolerated=True):
    if isinstance(p, dict):
        if p.get("Type") == "CmdSubst":
            # $(...) in a command's arguments: its status is ignored under -e
            collect(p.get("Stmts"), {"subst": True, "tolerated": tolerated, "line": ctx.get("line"), "pipefail": ctx.get("pipefail")}, acc)
            return
        for k, v in p.items():
            if k not in ("Pos", "End") and isinstance(v, (dict, list)): find_cmdsubst(v, ctx, acc, tolerated)
    elif isinstance(p, list):
        for x in p: find_cmdsubst(x, ctx, acc, tolerated)


def annotate_ops(node, src):
    """shfmt encodes BinaryCmd Op as an int token; recover the operator text from source offsets."""
    if isinstance(node, list):
        for n in node: annotate_ops(n, src)
    elif isinstance(node, dict):
        if node.get("Type") == "BinaryCmd" and "OpPos" in node:
            o = node["OpPos"]["Offset"]
            seg = src[o:o + 2]
            node["_opstr"] = "||" if seg == "||" else "&&" if seg == "&&" else "|&" if seg == "|&" else "|" if seg[:1] == "|" else seg
        for k, v in node.items():
            if k not in ("Pos", "End", "OpPos"): annotate_ops(v, src)


def parse(script):
    b = script.encode()
    p = subprocess.run([SHFMT, "--to-json", "-ln", "bash"], input=b, capture_output=True, timeout=30)
    if p.returncode != 0:
        return None
    ast = json.loads(p.stdout)
    return ast


def main(repo_list):
    repos = [l.strip() for l in open(repo_list) if l.strip()]
    out = open(ROOT / "data" / ("invocations-" + pathlib.Path(repo_list).stem + ".jsonl"), "w")
    stats = open(ROOT / "data" / ("repostats-" + pathlib.Path(repo_list).stem + ".jsonl"), "w")
    for repo in repos:
        d = ROOT / "repos" / repo.replace("/", "__")
        wf = d / ".github" / "workflows"
        st = {"repo": repo, "head": (d / ".head").read_text().strip() if (d / ".head").exists() else None,
              "workflows": 0, "yaml_err": 0, "latest_jobs": 0, "latest_bash_steps": 0, "parse_fail": 0, "calls": 0}
        files = sorted([p for p in wf.glob("*") if p.suffix in (".yml", ".yaml")]) if wf.is_dir() else []
        for f in files:
            st["workflows"] += 1
            try:
                doc = yaml_load(f.read_text(errors="replace"))
            except Exception:
                st["yaml_err"] += 1; continue
            if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict):
                continue
            wdef = ((doc.get("defaults") or {}).get("run") or {}).get("shell") if isinstance(doc.get("defaults"), dict) else None
            for jn, job in doc["jobs"].items():
                if not isinstance(job, dict) or not runs_on_latest(job):
                    continue
                if job.get("container"):
                    continue  # steps run inside another image, not the runner's coreutils
                st["latest_jobs"] += 1
                jdef = ((job.get("defaults") or {}).get("run") or {}).get("shell") if isinstance(job.get("defaults"), dict) else None
                for si, step in enumerate(job.get("steps") or []):
                    if not isinstance(step, dict) or not isinstance(step.get("run"), str):
                        continue
                    sh = step.get("shell", jdef or wdef)
                    if not shell_is_bash(sh):
                        continue
                    st["latest_bash_steps"] += 1
                    script = GHEXPR.sub("${GHEXPR}", step["run"])
                    ast = parse(script)
                    if ast is None:
                        st["parse_fail"] += 1; continue
                    acc = []
                    # GitHub: no shell key -> `bash -e {0}`; `shell: bash` -> `bash --noprofile --norc -eo pipefail {0}`
                    shs = None if sh is None else str(sh).strip()
                    pipefail = shs == "bash" or (shs is not None and "pipefail" in shs)
                    collect(ast.get("Stmts"), {"pipefail": pipefail}, acc)
                    for a in acc:
                        a["pipefail"] = pipefail
                    for k, a in enumerate(acc):
                        a.update(repo=repo, workflow=f.name, job=str(jn), step=si, k=k)
                        out.write(json.dumps(a, sort_keys=True) + "\n")
                    st["calls"] += len(acc)
        stats.write(json.dumps(st, sort_keys=True) + "\n")
    out.close(); stats.close()


if __name__ == "__main__":
    main(sys.argv[1])
