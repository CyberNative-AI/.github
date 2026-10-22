"""Dockerfile rules used for the census: floating official node:lts* stages and what breaks on Node 26 (fixed before the run)."""
import re

OFFICIAL = {"node", "library/node", "docker.io/library/node", "index.docker.io/library/node",
            "registry-1.docker.io/library/node", "docker.io/node", "public.ecr.aws/docker/library/node",
            "mirror.gcr.io/library/node"}
VAR = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)(?::?-([^}]*))?\}|\$([A-Za-z_][A-Za-z0-9_]*)")
LTS_OS = {"lts", "lts-slim"}                                  # Node 24->26 and Debian bookworm->trixie
LTS_NODE = {"lts-alpine", "lts-alpine3.23", "lts-alpine3.24", "lts-bookworm", "lts-bookworm-slim",
            "lts-trixie", "lts-trixie-slim"}                   # Node 24->26 only
# command position: start, after ; & | ( `then` `do` `exec` `-c "`, optional sudo / env assignments
CMDPOS = r"(?:^|[;&|(]|\bthen\b|\bdo\b|\bexec\b|\belse\b|-c\s+[\"'])\s*(?:sudo\s+)?(?:[A-Z_][A-Z0-9_]*=\S*\s+)*"
YARN_CMD = re.compile(CMDPOS + r"yarn(?:\s|$|[\"';&|)])")
COREPACK_CMD = re.compile(CMDPOS + r"corepack(?:\s|$|[\"';&|)])")
APT_KEY = re.compile(r"\bapt-key\b")
YARN_INSTALL = re.compile(r"\bnpm\s+(?:i|install|add)\b[^;&|]*\byarn(?:@[^\s;&|]*)?(?=\s|$|[;&|])"
                          r"|\bapk\s+add\b[^;&|]*\byarn\b|\bapt(?:-get)?\s+[^;&|]*\binstall\b[^;&|]*\byarn\b"
                          r"|yarnpkg\.com/install\.sh|\bpnpm\s+add\b[^;&|]*\byarn\b|\bnpm\s+(?:i|install)\b[^;&|]*\bcorepack\b")
COREPACK_INSTALL = re.compile(r"\bnpm\s+(?:i|install|add)\b[^;&|]*\bcorepack(?:@[^\s;&|]*)?(?=\s|$|[;&|])")
APT_SEG = re.compile(r"^\s*(?:sudo\s+)?(?:DEBIAN_FRONTEND=\S+\s+)?apt(?:-get)?\s+(?:-\S+\s+)*install\b(.*)$")


def instructions(text):
    out, cur = [], ""
    for raw in text.replace("\r\n", "\n").split("\n"):
        s = raw.strip()
        if s.startswith("#"):
            continue
        if s.endswith("\\"):
            cur += s[:-1] + " "
            continue
        cur += s
        if cur.strip():
            out.append(cur.strip())
        cur = ""
    if cur.strip():
        out.append(cur.strip())
    return out


def subst(s, env):
    unresolved = []

    def rep(m):
        name = m.group(1) or m.group(3)
        if name in env and env[name] != "":
            return env[name]
        if m.group(2) is not None:
            return m.group(2)
        unresolved.append(name)
        return "${%s}" % name
    for _ in range(4):  # nested defaults ARG B=${A}
        new = VAR.sub(rep, s)
        if new == s:
            break
        s = new
    return s, unresolved


def image_name(ref):
    r = ref.split("@", 1)[0]
    last = r.rsplit("/", 1)[-1]
    if ":" in last:
        r = r.rsplit(":", 1)[0]
    return r.lower()


def tag_of(ref):
    if "@sha256:" in ref:
        return None
    last = ref.rsplit("/", 1)[-1]
    return last.rsplit(":", 1)[1].lower() if ":" in last else ""


def tag_class(ref):
    t = tag_of(ref)
    if t is None:
        return "PINNED"
    if t in LTS_OS:
        return "LTS_OS"
    if t in LTS_NODE:
        return "LTS_NODE"
    if t.startswith("lts"):
        return "LTS_STALE"
    return "OTHER"


def parse(text):
    ins = instructions(text)
    genv, stages, seen_from = {}, [], False
    for line in ins:
        kw, _, rest = line.partition(" ")
        kw = kw.upper()
        if kw == "ARG" and not seen_from:
            for part in rest.split():
                k, eq, v = part.partition("=")
                genv[k] = v.strip('"\'') if eq else genv.get(k, "")
        elif kw == "FROM":
            seen_from = True
            toks = [t for t in rest.split() if not t.startswith("--")]
            if not toks:
                continue
            ref, unres = subst(toks[0], genv)
            alias = toks[2].lower() if len(toks) >= 3 and toks[1].lower() == "as" else None
            parent = next((s for s in reversed(stages) if s["alias"] and s["alias"] == ref.lower()), None)
            st = {"ref": ref, "alias": alias, "runs": [], "cmds": [], "unresolved": unres, "parent": parent}
            if parent:
                st["root"], st["root_unres"] = parent["root"], parent["root_unres"]
            else:
                st["root"], st["root_unres"] = ref, unres
            stages.append(st)
        elif kw == "RUN" and stages:
            stages[-1]["runs"].append(exec_form(rest))
        elif kw in ("CMD", "ENTRYPOINT") and stages:
            stages[-1]["cmds"].append(exec_form(rest))
    return stages


def exec_form(rest):
    r = rest.strip()
    # strip RUN flags (--mount=..., --network=...)
    while r.startswith("--"):
        r = r.split(None, 1)[1] if len(r.split(None, 1)) > 1 else ""
    if r.startswith("["):
        try:
            import json
            parts = json.loads(r)
            if isinstance(parts, list):
                return " ".join(str(p) for p in parts)
        except Exception:
            pass
    return r


def chain(st, key):
    out, s = [], st
    while s:
        out = s[key] + out
        s = s["parent"]
    return out


def first_pos(rx, text):
    m = rx.search(text)
    return m.start() if m else None


def apt_lists(runs):
    lists = []
    for r in runs:
        for seg in re.split(r"&&|\|\||;|\|", r):
            m = APT_SEG.match(seg)
            if not m:
                continue
            toks = [t.strip("\"'") for t in m.group(1).split()]
            pk = [t for t in toks if t and not t.startswith("-")]
            unres = any(("$" in t or "`" in t) for t in pk)
            lists.append({"pkgs": pk, "unresolved": unres})
    return lists


def classify(text):
    stages = parse(text)
    res = {"stages": len(stages), "node_stages": 0, "classes": [], "lts_stages": 0,
           "Y_BUILD": False, "Y_RUNTIME": False, "C": False, "K": False, "apt": [], "unresolved_node": False}
    for i, st in enumerate(stages):
        if st["root_unres"]:
            if "node" in st["root"].lower() or image_name(st["root"]).startswith("${"):
                res["unresolved_node"] = True
            continue
        if image_name(st["root"]) not in OFFICIAL:
            continue
        res["node_stages"] += 1
        tc = tag_class(st["root"])
        res["classes"].append(tc)
        if tc not in ("LTS_OS", "LTS_NODE"):
            continue
        res["lts_stages"] += 1
        runs = " ; ".join(chain(st, "runs"))
        yi = first_pos(YARN_INSTALL, runs)
        yu = first_pos(YARN_CMD, runs)
        if yu is not None and (yi is None or yi > yu):
            res["Y_BUILD"] = True
        ci = first_pos(COREPACK_INSTALL, runs)
        cu = first_pos(COREPACK_CMD, runs)
        if cu is not None and (ci is None or ci > cu):
            res["C"] = True
        if tc == "LTS_OS" and APT_KEY.search(runs):
            res["K"] = True
        if i == len(stages) - 1:
            cmds = chain(st, "cmds")
            if cmds and YARN_CMD.search(cmds[-1]) and yi is None:
                res["Y_RUNTIME"] = True
        if tc == "LTS_OS":
            variant = "slim" if tag_of(st["root"]) == "lts-slim" else "full"
            for a in apt_lists(chain(st, "runs")):
                res["apt"].append({**a, "variant": variant})
    return res
