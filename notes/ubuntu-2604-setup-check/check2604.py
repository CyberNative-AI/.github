#!/usr/bin/env python3
"""check2604.py: predict GitHub Actions setup failures on Ubuntu 26.04 x64.

Covers the two setup actions that download per-OS-version builds:
  actions/setup-python  (actions/python-versions manifest, filtered by exact Ubuntu version)
  ruby/setup-ruby       (ruby-builder release assets, one per Ubuntu version)
Checks ubuntu-latest and the explicit ubuntu-26.04 label after matrix expansion. It follows local
composite actions (`uses: ./path`) with the inputs their callers supply. Each step is resolved
against the hosted 24.04 and 26.04 x64 images and classified:
  BREAK    has a build on 24.04 only
  OK       installs on 26.04
  ALREADY  fails on 24.04 too (not caused by the migration)
  UNKNOWN  the input cannot be resolved statically (expression, reusable workflow, a local
           action that is not in the checkout, ...)
Nothing is reported OK unless it was resolved.

usage: check2604.py [--data DIR] [--refresh] [--json] REPO_DIR [REPO_DIR ...]
Needs PyYAML. Data files (manifest, ruby versions, asset probe cache, hosted image cache) live
in --data; --refresh downloads the manifests and re-reads the image cache lists.
"""
import argparse, json, math, os, posixpath, re, sys, urllib.error, urllib.request

try:
    import tomllib
except ImportError:  # Python < 3.11: pyproject/Pipfile/mise inputs become UNKNOWN
    tomllib = None
import yaml

# Hosted image tool caches (actions/runner-images Ubuntu2404-Readme.md / Ubuntu2604-Readme.md,
# "Cached Tools"). The images change every week or two, so the lists are data: --data/hosted-cache.json,
# written by --refresh, dated with the build lists beside it. This table is used only when a data
# directory has no hosted-cache.json (read 2026-11-18: images 20261111.370.1 and 20261111.196.1).
CACHE = {
    "24.04": {"python": ["3.11.18", "3.12.16", "3.13.18", "3.14.10", "3.15.2"],
              "ruby": ["3.2.11", "3.3.13", "3.4.12", "4.0.9"]},
    "26.04": {"python": ["3.11.18", "3.12.16", "3.13.18", "3.14.10", "3.15.2"],
              "ruby": ["3.2.11", "3.3.13", "3.4.12", "4.0.9"]},
}
OSES = ("24.04", "26.04")
PY_MANIFEST_URL = "https://raw.githubusercontent.com/actions/python-versions/main/versions-manifest.json"
RUBY_VERSIONS_URL = "https://raw.githubusercontent.com/ruby/setup-ruby/master/ruby-builder-versions.json"
RUBY_ASSET_URL = "https://github.com/ruby/ruby-builder/releases/download/{e}-{v}/{e}-{v}-ubuntu-{os}-x64.tar.gz"
IMAGE_README_URL = "https://raw.githubusercontent.com/actions/runner-images/main/images/ubuntu/Ubuntu{n}-Readme.md"

# ---------------------------------------------------------------- node-semver subset
# satisfies(version, range) with node-semver's default options (no includePrerelease).
# Unsupported syntax raises ValueError, which the caller reports as UNKNOWN.
_VER = re.compile(r"^v?(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$")
_PART = re.compile(r"^[v=\s]*(\d+|[xX*])(?:\.(\d+|[xX*]))?(?:\.(\d+|[xX*]))?(?:-([0-9A-Za-z.-]+))?$")


def parse_ver(s):
    m = _VER.match(s.strip())
    if not m:
        raise ValueError("bad version " + s)
    pre = tuple(int(p) if p.isdigit() else p for p in m.group(4).split(".")) if m.group(4) else ()
    return (int(m.group(1)), int(m.group(2)), int(m.group(3))), pre


def cmp_ver(a, b):
    if a[0] != b[0]:
        return -1 if a[0] < b[0] else 1
    pa, pb = a[1], b[1]
    if pa == pb:
        return 0
    if not pa:
        return 1
    if not pb:
        return -1
    for x, y in zip(pa, pb):
        if x == y:
            continue
        if isinstance(x, int) and isinstance(y, int):
            return -1 if x < y else 1
        if isinstance(x, int):
            return -1
        if isinstance(y, int):
            return 1
        return -1 if x < y else 1
    return -1 if len(pa) < len(pb) else (1 if len(pa) > len(pb) else 0)


def _wild(p):
    return p is None or p in ("x", "X", "*")


def _partial(s):
    m = _PART.match(s)
    if not m:
        raise ValueError("bad partial " + s)
    return m.group(1), m.group(2), m.group(3), m.group(4)


def _v(ma, mi, pa, pre=None):
    return ((int(ma), int(mi), int(pa)), tuple(int(p) if p.isdigit() else p for p in pre.split(".")) if pre else ())


def _comparators(tok):
    """One range token -> list of (op, version) comparators (AND)."""
    m = re.match(r"^(<=|>=|<|>|=|~>|~|\^)?\s*(.*)$", tok)
    op, rest = m.group(1) or "", m.group(2)
    ma, mi, pa, pre = _partial(rest)
    if op in ("~", "~>"):
        if _wild(ma):
            return []
        if _wild(mi):
            return [(">=", _v(ma, 0, 0)), ("<", _v(int(ma) + 1, 0, 0, "0"))]
        if _wild(pa):
            return [(">=", _v(ma, mi, 0)), ("<", _v(ma, int(mi) + 1, 0, "0"))]
        return [(">=", _v(ma, mi, pa, pre)), ("<", _v(ma, int(mi) + 1, 0, "0"))]
    if op == "^":
        if _wild(ma):
            return []
        if _wild(mi):
            return [(">=", _v(ma, 0, 0)), ("<", _v(int(ma) + 1, 0, 0, "0"))]
        if _wild(pa):
            if int(ma) == 0:
                return [(">=", _v(ma, mi, 0)), ("<", _v(ma, int(mi) + 1, 0, "0"))]
            return [(">=", _v(ma, mi, 0)), ("<", _v(int(ma) + 1, 0, 0, "0"))]
        if int(ma) == 0:
            if int(mi) == 0:
                return [(">=", _v(ma, mi, pa, pre)), ("<", _v(ma, mi, int(pa) + 1, "0"))]
            return [(">=", _v(ma, mi, pa, pre)), ("<", _v(ma, int(mi) + 1, 0, "0"))]
        return [(">=", _v(ma, mi, pa, pre)), ("<", _v(int(ma) + 1, 0, 0, "0"))]
    if op in ("", "="):
        if _wild(ma):
            return []
        if _wild(mi):
            return [(">=", _v(ma, 0, 0)), ("<", _v(int(ma) + 1, 0, 0, "0"))]
        if _wild(pa):
            return [(">=", _v(ma, mi, 0)), ("<", _v(ma, int(mi) + 1, 0, "0"))]
        return [("=", _v(ma, mi, pa, pre))]
    # <, <=, >, >= with partials
    if _wild(ma):
        return [("<", _v(0, 0, 0, "0"))] if op in ("<", ">") else []
    if _wild(mi) or _wild(pa):
        mi0 = 0 if _wild(mi) else int(mi)
        if op == ">":
            return [(">=", _v(int(ma) + 1, 0, 0) if _wild(mi) else _v(ma, mi0 + 1, 0))]
        if op == ">=":
            return [(">=", _v(ma, mi0, 0))]
        if op == "<":
            return [("<", _v(ma, mi0, 0, "0"))]
        return [("<", _v(int(ma) + 1, 0, 0, "0") if _wild(mi) else _v(ma, mi0 + 1, 0, "0"))]
    return [(op, _v(ma, mi, pa, pre))]


def parse_range(r):
    sets = []
    for alt in r.split("||"):
        alt = alt.strip()
        hm = re.match(r"^(\S+)\s+-\s+(\S+)$", alt)
        if hm:
            lo = _comparators(">=" + hm.group(1))
            ma, mi, pa, pre = _partial(hm.group(2))
            if _wild(mi):
                hi = [("<", _v(int(ma) + 1, 0, 0, "0"))]
            elif _wild(pa):
                hi = [("<", _v(ma, int(mi) + 1, 0, "0"))]
            else:
                hi = [("<=", _v(ma, mi, pa, pre))]
            sets.append(lo + hi)
            continue
        alt = re.sub(r"(<=|>=|<|>|=|~>|~|\^)\s+", r"\1", alt)
        toks = alt.split() or ["*"]
        comps = []
        for t in toks:
            comps += _comparators(t)
        sets.append(comps)
    return sets


def satisfies(version, rng):
    v = parse_ver(version)
    for comps in parse_range(rng):
        ok = True
        for op, c in comps:
            r = cmp_ver(v, c)
            if not {"=": r == 0, "<": r < 0, "<=": r <= 0, ">": r > 0, ">=": r >= 0}[op]:
                ok = False
                break
        if not ok:
            continue
        if v[1]:  # prerelease: only if some comparator in this set has a prerelease on the same tuple
            if not any(c[1] and c[0] == v[0] for _, c in comps):
                continue
        return True
    return False


# ---------------------------------------------------------------- data
class Data:
    def __init__(self, d, refresh):
        self.dir = d
        os.makedirs(d, exist_ok=True)
        self.py_manifest = json.loads(self._get("versions-manifest.json", PY_MANIFEST_URL, refresh))
        self.ruby_versions = json.loads(self._get("ruby-builder-versions.json", RUBY_VERSIONS_URL, refresh))
        self.probe_path = os.path.join(d, "ruby-assets.json")
        self.probes = {}
        if os.path.exists(self.probe_path):
            with open(self.probe_path) as f:
                self.probes = json.load(f)
        self.cache = self._cache(refresh)

    def _cache(self, refresh):
        """The hosted images' cached Python and Ruby builds, CACHE's shape: read from the runner-images
        READMEs on refresh (and saved), else hosted-cache.json in this directory, else the CACHE table."""
        p = os.path.join(self.dir, "hosted-cache.json")
        if refresh:
            cache = {}
            for osv in OSES:
                with urllib.request.urlopen(IMAGE_README_URL.format(n=osv.replace(".", "")), timeout=60) as r:
                    cache[osv] = cached_lists(r.read().decode("utf-8"))
            with open(p, "w", encoding="utf-8") as f:
                json.dump(cache, f, indent=1, sort_keys=True)
        elif not os.path.exists(p):
            return CACHE
        with open(p, encoding="utf-8") as f:
            cache = json.load(f)
        for osv in OSES:
            for tool in ("python", "ruby"):
                if not all(_VER.match(v) for v in cache[osv][tool]):
                    raise ValueError(f"{p}: {osv} {tool} list is not exact versions")
        return cache

    def _get(self, name, url, refresh):
        p = os.path.join(self.dir, name)
        if refresh or not os.path.exists(p):
            with urllib.request.urlopen(url, timeout=60) as r, open(p, "wb") as f:
                f.write(r.read())
        with open(p, encoding="utf-8") as f:
            return f.read()

    def ruby_asset(self, engine, version, osv):
        key = f"{engine}-{version}-{osv}"
        if key not in self.probes:
            url = RUBY_ASSET_URL.format(e=engine, v=version, os=osv)
            req = urllib.request.Request(url, method="HEAD")
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    self.probes[key] = r.status
            except urllib.error.HTTPError as e:
                self.probes[key] = e.code
            except OSError:
                return None
            with open(self.probe_path, "w") as f:
                json.dump(self.probes, f, indent=0, sort_keys=True)
        return self.probes[key]


def cached_lists(md):
    """{"python": [...], "ruby": [...]} from a runner-images README's "Cached Tools" lists."""
    out = {}
    for tool in ("Python", "Ruby"):
        m = re.search(rf"^#### {tool}\n((?:- .+\n)+)", md, re.M)
        if not m:
            raise ValueError(f"runner-images README has no cached {tool} list")
        out[tool.lower()] = [line[2:].strip() for line in m.group(1).splitlines()]
        if not all(_VER.match(v) for v in out[tool.lower()]):
            raise ValueError(f"runner-images README: cached {tool} list is not exact versions")
    return out


# ---------------------------------------------------------------- resolution
class Unknown(Exception):
    pass


class _Unresolved:
    """A composite-action input whose value the files do not give; reading it is Unknown."""
    def __init__(self, why):
        self.why = why


def py_semantic(spec, allow_pre):
    """setup-python desugarVersion + pythonVersionToSemantic. Returns (range, freethreaded)."""
    ft = False
    m = re.match(r"^(\d+\.\d+(\.\d+)?)t$", spec)
    if m:
        spec, ft = m.group(1), True
    m = re.match(r"^(\d+\.\d+)t(-dev)$", spec)
    if m:
        spec, ft = m.group(1) + m.group(2), True
    spec = re.sub(r"^(\d+)\.(\d+)-dev$", r"~\1.\2.0-0", spec)
    spec = re.sub(r"(\d+\.\d+\.\d+)((?:a|b|rc)\d*)", r"\1-\2", spec)
    if allow_pre:
        spec = re.sub(r"^(\d+)\.(\d+)$", r"~\1.\2.0-0", spec)
    return spec, ft


def resolve_python(data, spec, osv, arch="x64", allow_pre=False, freethreaded=False):
    """Return the version setup-python would install on hosted ubuntu-<osv>, or None."""
    rng, ft = py_semantic(spec, allow_pre)
    ft = ft or freethreaded
    a = arch + ("-freethreaded" if ft else "")
    try:
        parse_range(rng)
    except ValueError:
        raise Unknown(f"unsupported version syntax {spec!r}")
    if a == "x64":  # hosted cache holds x64 non-freethreaded builds
        hits = [v for v in data.cache[osv]["python"] if satisfies(v, rng)]
        if hits:
            return max(hits, key=parse_ver)
    for rel in data.py_manifest:  # manifest is newest-first; first match wins
        try:
            if not satisfies(rel["version"], rng):
                continue
        except ValueError:
            continue
        for f in rel["files"]:
            if f.get("platform") == "linux" and f.get("arch") == a and f.get("platform_version") == osv:
                return rel["version"]
    return None


def _stable_ruby(engine, v):
    if engine == "ruby":
        return re.fullmatch(r"\d+(\.\d+)*", v) is not None
    return re.fullmatch(r"\d+(\.\d+)*", v) is not None and "preview" not in v and "rc" not in v


def resolve_ruby(data, spec, osv):
    """setup-ruby parseRubyEngineAndVersion + validateRubyEngineAndVersion + download."""
    if spec in ("head", "debug") or spec.endswith("-head") or spec.endswith("-dev"):
        raise Unknown(f"head build {spec!r} (separate asset repository)")
    if re.match(r"^\d", spec):
        engine, ver = "ruby", spec
    elif "-" not in spec:
        engine, ver = spec, ""
    else:
        engine, ver = spec.split("-", 1)
    versions = data.ruby_versions.get(engine)
    if versions is None:
        raise Unknown(f"engine {engine!r} not in setup-ruby's version list")
    if ver not in versions:
        rev = list(reversed(versions))
        found = next((v for v in rev if _stable_ruby(engine, v) and v.startswith(ver)), None)
        found = found or next((v for v in rev if v not in ("head", "debug") and v.startswith(ver)), None)
        if not found:
            return engine, None, None  # "Unknown version" error on every OS
        ver = found
    if engine == "ruby" and ver in data.cache[osv]["ruby"]:
        return engine, ver, 200
    return engine, ver, data.ruby_asset(engine, ver, osv)


# ---------------------------------------------------------------- workflow reading
class GitHubLoader(yaml.SafeLoader):
    """YAML typed as the Actions workflow reader types it (the YAML 1.2 core schema): a plain
    true/false/null/number is that type, and everything else is a string. PyYAML's own (YAML 1.1)
    typing differs: `yes` and `on` are booleans, `010` is 8, `1_000` and `1:20` are numbers, `1e5`
    is a string. Only the scalar types change; `<<` merge keys are kept."""
    yaml_implicit_resolvers = {}


GitHubLoader.add_implicit_resolver("tag:yaml.org,2002:null", re.compile(r"^(?:~|null|Null|NULL|)$"), list("~nN") + [""])
GitHubLoader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"), list("tTfF"))
GitHubLoader.add_implicit_resolver("tag:yaml.org,2002:int", re.compile(r"^(?:[-+]?[0-9]+|0o[0-7]+|0x[0-9a-fA-F]+)$"), list("-+0123456789"))
GitHubLoader.add_implicit_resolver(
    "tag:yaml.org,2002:float",
    re.compile(r"^(?:[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?|[-+]?\.(?:inf|Inf|INF)|\.(?:nan|NaN|NAN))$"),
    list("-+0123456789."))
GitHubLoader.add_implicit_resolver("tag:yaml.org,2002:merge", re.compile(r"^(?:<<)$"), ["<"])


_YAML_INT = re.compile(r"([-+]?[0-9]+)|0x([0-9a-fA-F]+)|0o([0-7]+)")
_YAML_FLOAT = re.compile(r"[-+]?(?:\.[0-9]+|[0-9]+(?:\.[0-9]*)?)(?:[eE][-+]?[0-9]+)?")


def _yaml_decimal(v):
    """A decimal YAML number as the runner holds it (a double). Unresolved when it is out of the double
    range: the runner's .NET reads it as infinity, an older .NET refuses the file."""
    digits = v.lstrip("+-").lstrip("0")
    if _YAML_INT.fullmatch(v) and len(digits) <= 15:
        return int(v)  # exactly a double; kept an int so it prints as one
    f = float(v)
    return _Unresolved(f"the number {v[:20]}… is out of range") if math.isinf(f) else f


def _gh_int(loader, node):
    """YamlObjectReader.MatchInteger: [-+]?[0-9]+ as a double; 0x.. and 0o.. as an Int32, so 2^31 and
    above wrap or refuse the file and are Unresolved here. Any other text under !!int is Unresolved."""
    v = loader.construct_scalar(node)
    m = _YAML_INT.fullmatch(v) if isinstance(v, str) else None
    if not m:
        return _Unresolved(f"the value {str(v)[:20]!r} is not read as GitHub reads it")
    if m.group(1) is not None:
        return _yaml_decimal(v)
    n = int(m.group(2), 16) if m.group(2) is not None else int(m.group(3), 8)
    return n if n < 2 ** 31 else _Unresolved(f"the number {v[:20]} is outside the range GitHub reads exactly")


def _gh_float(loader, node):
    """YamlObjectReader.MatchFloat; any other text under !!float is Unresolved."""
    v = loader.construct_scalar(node)
    if not isinstance(v, str):
        return _Unresolved("a number GitHub does not read")
    if v in (".inf", ".Inf", ".INF", "+.inf", "+.Inf", "+.INF"):
        return float("inf")
    if v in ("-.inf", "-.Inf", "-.INF"):
        return float("-inf")
    if v in (".nan", ".NaN", ".NAN"):
        return float("nan")
    if not _YAML_FLOAT.fullmatch(v):
        return _Unresolved(f"the value {v[:20]!r} is not read as GitHub reads it")
    return _yaml_decimal(v)


GitHubLoader.add_constructor("tag:yaml.org,2002:int", _gh_int)
GitHubLoader.add_constructor("tag:yaml.org,2002:float", _gh_float)


def load_yaml(txt):
    return yaml.load(txt, Loader=GitHubLoader)


def js_str(v):
    """How the runner stringifies a YAML scalar input (3.10 -> '3.1', 3.0 -> '3')."""
    if isinstance(v, _Unresolved):
        raise Unknown(v.why)
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    return str(v)


EXPR = re.compile(r"\$\{\{\s*(.*?)\s*\}\}")


_SEG = re.compile(r"\.([A-Za-z0-9_-]+)|\[(\d+)\]|\[['\"]([^'\"]+)['\"]\]")


_PATH = re.compile(r"(matrix|env|inputs)((?:\.[A-Za-z0-9_-]+|\[\d+\]|\[['\"][^'\"]+['\"]\])+)")


# ---------------------------------------------------------------- GitHub's string and name matching
# The runner compares strings with String.Equals(..., OrdinalIgnoreCase), and finds context keys and
# action inputs ignoring case the same way. ASCII is reproduced exactly. Where only a non-ASCII
# character could decide (.NET's invariant case mapping: the long s, the Kelvin sign, ...), the
# answer is Unknown rather than Python's own case rules.

def _units(s):
    b = s.encode("utf-16-le", "surrogatepass")
    return [b[i] | b[i + 1] << 8 for i in range(0, len(b), 2)]


def gh_same_text(a, b):
    """String.Equals(a, b, OrdinalIgnoreCase): True or False when certain, None when only a non-ASCII
    character could decide it. Strings of different UTF-16 length are never equal."""
    if a == b:
        return True
    ua, ub = _units(a), _units(b)
    if len(ua) != len(ub):
        return False
    unsure = False
    for x, y in zip(ua, ub):
        if x == y:
            continue
        if x < 128 and y < 128:
            if chr(x).upper() != chr(y).upper():
                return False
        else:
            unsure = True
    return None if unsure else True


_MISSING = object()


def gh_key(d, name, what):
    """d's value for `name`, matched ignoring case as GitHub matches context keys and input names;
    _MISSING when no key matches. Unknown when two keys with different values match, or when only a
    non-ASCII character decides whether a key matches."""
    hits = []
    for k in d:
        same = gh_same_text(k, name) if isinstance(k, str) else False
        if same is None:
            raise Unknown(f"{what} {name}: a key differs from it only in non-ASCII letters")
        if same:
            hits.append(d[k])
    if not hits:
        return _MISSING
    if any(v is not hits[0] and v != hits[0] for v in hits[1:]):
        raise Unknown(f"{what} {name} is given twice, in different case")
    return hits[0]


def lookup(e, ctx):
    """Value of a matrix./env./inputs. path such as matrix.os.image or matrix.plat[0]; Unknown otherwise.
    inputs. is known only inside a local composite action, where ctx carries the inputs its caller gave.
    matrix. and inputs. names match ignoring case (DictionaryContextData). env. names match exactly: on
    Linux the runner's env context is a CaseSensitiveDictionaryContextData, so env.python_version is
    not PYTHON_VERSION. A name the files do not set is Unknown (an earlier step may set it)."""
    m = _PATH.fullmatch(e.strip())
    if not m or m.group(1) not in ctx:
        raise Unknown(f"expression ${{{{ {e} }}}}")
    root = m.group(1)
    if root == "env" and ctx.get("env_why"):
        raise Unknown(ctx["env_why"])
    v = ctx[root]
    for i, seg in enumerate(_SEG.finditer(m.group(2))):
        key, idx, qkey = seg.groups()
        if idx is not None:
            if not isinstance(v, list) or int(idx) >= len(v):
                raise Unknown(f"expression ${{{{ {e} }}}}")
            v = v[int(idx)]
        else:
            name = key if key is not None else qkey
            if not isinstance(v, dict):
                v = _MISSING
            elif root == "env" and i == 0:
                v = v.get(name, _MISSING)
            else:
                v = gh_key(v, name, "expression")
            if v is _MISSING:
                raise Unknown(f"expression ${{{{ {e} }}}}")
    if isinstance(v, _Unresolved):
        raise Unknown(v.why)
    return v


def gh_value(e, ctx):
    """matrix.a, matrix.a.b, matrix.a[0] or matrix['a'] as the runner reads it in an expression: a
    property or element that is not there is null. Unknown where that is not reproduced exactly: an
    index into an object or a name on a list, an ambiguous key, a value GitHub reads differently, or
    a string with an expression in it (GitHub evaluates the matrix's expressions first)."""
    m = _PATH.fullmatch(e.strip())
    if not m or m.group(1) != "matrix" or "matrix" not in ctx:
        raise Unknown(f"expression ${{{{ {e} }}}}")
    v = ctx["matrix"]
    for seg in _SEG.finditer(m.group(2)):
        key, idx, qkey = seg.groups()
        if isinstance(v, _Unresolved):
            raise Unknown(v.why)
        if isinstance(v, dict):
            if idx is not None:
                raise Unknown(f"{e.strip()}: an index into an object")
            v = gh_key(v, key if key is not None else qkey, "matrix")
            v = None if v is _MISSING else v
        elif isinstance(v, list):
            if idx is None:
                raise Unknown(f"{e.strip()}: a name on a list")
            v = v[int(idx)] if int(idx) < len(v) else None
        else:
            v = None  # a property of a string, number, boolean or null is null
    if isinstance(v, _Unresolved):
        raise Unknown(v.why)
    if isinstance(v, str) and "${{" in v:
        raise Unknown(f"{e.strip()} is an expression")
    return v


_LIT = re.compile(r"'((?:[^']|'')*)'")


def fallback(e, ctx):
    """`matrix.os || 'ubuntu-latest'`: the first truthy operand, else the last one, as in the runner.
    Operands are matrix./env. paths or string literals; a matrix value missing from this combination
    is null. Any other operand (&&, !, ==, calls, inputs., vars.) leaves the expression Unknown."""
    v = None
    for p in (x.strip() for x in e.split("||")):  # && and comparisons bind tighter than ||
        lit = _LIT.fullmatch(p)
        if lit:
            v = lit.group(1).replace("''", "'")
        elif _PATH.fullmatch(p):
            v = gh_value(p, ctx) if p.startswith("matrix") else lookup(p, ctx)
        else:
            raise Unknown(f"expression ${{{{ {e} }}}}")
        if v is not None and v is not False and v != 0 and v != "" and v == v:  # NaN is falsy
            return v
    return "" if v is None else v


def substitute(val, ctx):
    """Replace ${{ matrix.x }} / ${{ env.X }} / ${{ a || 'b' }}; raise Unknown on anything else.
    One pass, as the runner evaluates a value once: env values are resolved where they are set
    (env_layer), so a value that still holds ${{ (a matrix item GitHub evaluates first) is Unknown."""
    if isinstance(val, (list, dict)):
        raise Unknown("non-scalar input")
    s = js_str(val)

    def rep(m):
        v = fallback(m.group(1), ctx) if "||" in m.group(1) else lookup(m.group(1), ctx)
        if isinstance(v, (list, dict)):
            raise Unknown(f"non-scalar {m.group(1)}")
        v = js_str(v)
        if "${{" in v:
            raise Unknown(f"{m.group(1)} is an expression")
        return v

    return EXPR.sub(rep, s)


# What the steps before a step may have changed: one account per position in a job (and in each local
# composite action it calls), carried forward step by step. {"env": {name: why}, "files": {prefix: (why,
# keep)}, "any": {prefix: (why, keep)}}: env names a step may have set through GITHUB_ENV
# (ANY_ENV: every name), workspace paths it may have changed ("" = the whole workspace; keep: what a
# sparse checkout leaves as given there). "files" holds on the success path, where every earlier step of
# the list ran as its condition says (so a checkout there that puts the files back did); "any" holds on
# every path, where an earlier step may have failed and such a checkout been skipped: a step that may run
# after a failure (always(), failure(), !cancelled(), ...) reads its files against "any", which no
# checkout ever narrows. The job starts with a missing root checkout fact in both accounts. Without
# that fact, everything not listed is as the selected files give it. A step changes
# nothing only when its effects are known from its source: actions/checkout of this repository at the
# triggering commit, and setup-python / setup-ruby without the inputs that run the repository's code.
# Any other step (run:, docker://, any other published action, a local action that is not a composite
# of such steps) may change every env value and every file. A step its condition rules out changes nothing.
ANY_ENV = "*"
NOTHING = {"env": {}, "files": {}, "any": {}}
# A local action's action.yml / action.yaml is a workspace file like any other: the runner
# loads it from the workspace when the step starts, so a step that may change the files may change it.
PY_EXPORTS = ("pythonLocation", "PKG_CONFIG_PATH", "Python_ROOT_DIR", "Python2_ROOT_DIR", "Python3_ROOT_DIR",
              "LD_LIBRARY_PATH", "PATH")  # setup-python v6 find-python.ts / find-pypy.ts / find-graalpy.ts
RUBY_EXPORTS = ("PATH", "JAVA_HOME")  # setup-ruby v1 common.js on Linux (TMPDIR/HOME only on Windows)


# A change to the files at a prefix: (why, keep). keep = (under, exact, files_in): what a sparse checkout
# of this repository leaves as given there (paths below `under`; `exact` paths and below; the files
# directly in a `files_in` folder). NOKEEP: nothing.
NOKEEP = ((), (), ())
# The key of a change to every folder below the root that holds its own Git repository (a `.git` file or
# folder) and is not a submodule .gitmodules lists: a checkout of this repository does not put those back.
GITDIRS = "\0git"
# This fallback describes an unestablished root. It does not imply a previous step changed Git.
NO_CHECKOUT = "\0checkout"
_EMPTY_WORKSPACE = {NO_CHECKOUT: ("was not established in the workspace by a root checkout", NOKEEP)}
JOB_START = {"env": {}, "files": _EMPTY_WORKSPACE, "any": _EMPTY_WORKSPACE}
MAX_SUBMODULES = 500  # submodule paths read from .gitmodules files in one run
MAX_SUBMODULE_DEPTH = 8
MAX_GITMODULES_BYTES = 1024 * 1024


def _gitmodules_paths(txt):
    """Every `path` value in a .gitmodules file (git config syntax: config.c parse_value / get_base_var),
    from every [submodule "..."] section, so a path git would ignore is still a submodule here. Anything
    this does not read exactly (an include, an old-style [submodule.x] header, a key on a header line, a
    line continuation, an unknown escape, an unterminated quote, a path with no value) is Unknown."""
    if "\0" in txt:
        raise Unknown(".gitmodules contains a NUL byte")
    out, section = [], None
    for n, line in enumerate(txt.lstrip("\ufeff").replace("\r\n", "\n").split("\n"), 1):
        t = line.strip(" \t\r\v\f")
        if not t or t[0] in "#;":
            continue
        if t[0] == "[":
            m = re.fullmatch(r'\[\s*([A-Za-z0-9-]+)(?:\s+"((?:[^"\\\n]|\\.)*)")?\s*\]\s*(?:[#;].*)?', t)
            if not m:
                raise Unknown(f".gitmodules line {n} is a section header this check does not read")
            name = m.group(1).lower()
            if name in ("include", "includeif"):
                raise Unknown(f".gitmodules line {n} includes another file")
            section = "submodule" if name == "submodule" and m.group(2) is not None else name
            continue
        m = re.fullmatch(r"([A-Za-z][A-Za-z0-9-]*)\s*(?:=(.*))?", t)
        if not m:
            raise Unknown(f".gitmodules line {n} is not a key = value line")
        if section is None:
            raise Unknown(f".gitmodules line {n} is outside a section")
        value = _git_config_value(m.group(2), n) if m.group(2) is not None else None
        if section == "submodule" and m.group(1).lower() == "path":
            if value is None:
                raise Unknown(f".gitmodules line {n} has a path with no value")
            out.append(value)
    return out


def _git_config_value(raw, n):
    """A git config value as config.c parse_value reads it: leading blanks dropped, trailing blanks
    outside quotes trimmed, quotes removed, a comment (# or ;) outside quotes ends it, escapes \\ \" n t b."""
    out, quote, trim = [], False, None
    i = 0
    while i < len(raw):
        c = raw[i]
        i += 1
        if c in " \t\r\v\f" and not quote:
            if trim is None:
                trim = len(out)
            if out:
                out.append(c)
            continue
        if not quote and c in "#;":
            break
        trim = None
        if c == "\\":
            if i >= len(raw):
                raise Unknown(f".gitmodules line {n} continues on the next line")
            e = raw[i]
            i += 1
            if e not in 'ntb\\"':
                raise Unknown(f".gitmodules line {n} has an escape git refuses")
            out.append({"n": "\n", "t": "\t", "b": "\b"}.get(e, e))
            continue
        if c == '"':
            quote = not quote
            continue
        out.append(c)
    if quote:
        raise Unknown(f".gitmodules line {n} has an unterminated quote")
    if trim is not None:
        out = out[:trim]
    return "".join(out)


def _submodules():
    """The submodule folders of this run's repository, from the .gitmodules at its root and, below each
    submodule, its own: ((path, level), ...), level 1 for the root's. A string (why) when the folder does
    not show them: a .gitmodules the caller could not read, too large, not text or not read exactly, a
    path that leaves the checkout, more than MAX_SUBMODULES paths, or a folder holding a Git repository
    the caller could not list."""
    run = _RUN
    if run is None:
        return "no repository"
    if run.subs is not None:
        return run.subs
    run.subs = _read_submodules(run)
    return run.subs


def _read_submodules(run):
    if any(k == ".git" or k.endswith("/.git") for k in run.unread):
        return "the folders that hold their own Git repository were not all listed"
    out, todo, spent = [], [("", 0)], 0
    while todo:
        d, lvl = todo.pop(0)
        rel = posixpath.join(d, ".gitmodules") if d else ".gitmodules"
        try:
            b = read_bytes(run.root, rel, limit=MAX_GITMODULES_BYTES - spent)
        except Unknown as u:
            return str(u)
        if b is None:
            if os.path.lexists(os.path.join(run.root, rel)):
                return f"{rel} could not be read"
            continue
        spent += len(b)
        if spent > MAX_GITMODULES_BYTES:
            return "the .gitmodules files are larger than this check reads"
        try:
            paths = _gitmodules_paths(b.decode("utf-8"))
        except UnicodeDecodeError:
            return f"{rel} is not UTF-8 text"
        except Unknown as u:
            return str(u).replace(".gitmodules", rel, 1)
        for p in paths:
            full = posixpath.normpath(posixpath.join(d, p))
            if (not p or p.startswith("/") or full in (".", "..", d)
                    or full.startswith("../") or (d and not full.startswith(d + "/"))
                    or ".git" in full.split("/")):
                return f"{rel} names a submodule path this check cannot place ({p!r})"
            out.append((full, lvl + 1))
            if len(out) > MAX_SUBMODULES:
                return "the repository has more submodules than this check reads"
            if lvl + 1 < MAX_SUBMODULE_DEPTH:
                todo.append((full, lvl + 1))
            elif os.path.lexists(os.path.join(run.root, full, ".gitmodules")):
                return "the submodules are nested deeper than this check reads"
    return tuple(out)


def _nested_repo(rel, listed):
    """The folder above `rel` (below the root) that holds its own Git repository and is not a listed
    submodule, or None. The browser's folder reader marks such a folder with an empty .git file."""
    run = _RUN
    parts = rel.split("/")
    for i in range(1, len(parts)):
        d = "/".join(parts[:i])
        if d not in listed and os.path.lexists(os.path.join(run.root, d, ".git")):
            return d
    return None


def _opaque(why):
    """The change of a step whose effects are not known: every variable and every file."""
    gone = {"": (why, NOKEEP)}
    return {"env": {ANY_ENV: why}, "files": gone, "any": gone}


def _merge_paths(a, b):
    out = {**b, **a}
    for p in a.keys() & b.keys():
        if a[p] != b[p]:
            out[p] = (a[p][0], NOKEEP)  # two changes at one prefix: as given only where both keep it
    return out


def _any(a):
    """The files an account says may have changed on any path (a change with no "any": its "files")."""
    return a.get("any", a["files"])


def _merge(a, b):
    """Both accounts at once (a change applied on top of a state): every change either lists."""
    if ANY_ENV in a["env"] or ANY_ENV in b["env"]:
        env = {ANY_ENV: a["env"].get(ANY_ENV) or b["env"][ANY_ENV]}
    else:
        env = {**b["env"], **a["env"]}
    return {"env": env, "files": _merge_paths(a["files"], b["files"]), "any": _merge_paths(_any(a), _any(b))}


def _everything(why, state):
    return _merge(state, _opaque(why))


def _norm_rel(p):
    """A workspace-relative path as the runner joins it to GITHUB_WORKSPACE: '' for the root, None if
    it leaves the workspace."""
    p = posixpath.normpath(p.strip()) if p.strip() else "."
    if p == ".":
        return ""
    if p == ".." or p.startswith(("../", "/")):
        return None
    return p


def _changed_at(paths, rel):
    rel = _norm_rel(rel)
    for p, (why, (under, exact, files_in)) in paths.items():
        if p == NO_CHECKOUT:
            continue
        if rel is None:
            return why
        if p == GITDIRS:
            subs = _submodules()
            if _nested_repo(rel, {q for q, _ in subs} if isinstance(subs, tuple) else set()):
                return why
            continue
        if not (p == "" or rel == p or rel.startswith(p + "/")):
            continue
        if (rel in exact or any(rel.startswith(k + "/") for k in under + exact)
                or posixpath.dirname(rel) in files_in):
            continue  # left as given by a sparse checkout of this repository
        return why
    missing = paths.get(NO_CHECKOUT)
    return missing[0] if missing else None


def _checkout_note(state, why):
    """Explain why a checkout did not establish a still-missing workspace root."""
    def note(paths):
        return {**paths, NO_CHECKOUT: (why, NOKEEP)} if NO_CHECKOUT in paths else paths

    return dict(state, files=note(state["files"]), any=note(_any(state)))


def file_changed(state, rel):
    """Why the file at `rel` is not established or may have changed, or None."""
    paths = state["files"]
    why = _changed_at(paths, rel)
    if why or not paths or _RUN is None:
        return why
    root = _RUN.root
    resolved = os.path.relpath(os.path.realpath(os.path.join(root, rel)), root)
    if resolved == rel or _norm_rel(resolved) is None:
        return None  # the reader rejects links that leave the selected folder
    why = _changed_at(paths, resolved)
    return f"points to {resolved}, which {why}" if why else None


def folder_changed(state, rel):
    """Why the action.yml / action.yaml of the local action folder `rel` may not be the one given, or None."""
    return file_changed(state, posixpath.join(rel, "action.yml")) or file_changed(state, posixpath.join(rel, "action.yaml"))


def env_layer(env, ctx, where):
    """The values of one env: block (workflow, job or step) as the runner sets them: each value is
    evaluated once, in the context of the level above it (ctx), and is a string. Exact-case keys, the
    later of two equal keys wins. A value that cannot be resolved here is kept as Unresolved, so only a
    step that reads it is UNKNOWN. Returns (values, why): why is set when the block is not a mapping
    (an expression), which leaves every env. read Unknown."""
    if env is None:
        return {}, None
    if not isinstance(env, dict):
        return {}, f"the {where} env: is an expression"
    out = {}
    for k, v in env.items():
        name = k if isinstance(k, str) else js_str(k)
        if v is None or isinstance(v, (list, dict)):
            out[name] = _Unresolved(f"env.{name} is not a string")
            continue
        try:
            out[name] = substitute(v, ctx)
        except Unknown as u:
            out[name] = _Unresolved(f"env.{name}: {u}")
    return out, None


def step_env(ctx, step, state):
    """The env context of `step` (runner: StepsRunner / CompositeActionHandler on Linux): the job's
    env, then the env: of each calling step (ctx["over"]), then the step's own env: evaluated against
    what is above it. A workflow or job env value that an earlier step may have set again through
    GITHUB_ENV (state) is Unknown; a step-level env: still wins over GITHUB_ENV. ctx["state"] is the
    account the step's reads of files are checked against."""
    env = ctx["env"]
    over = ctx.get("over", frozenset())
    changed = state["env"]
    if changed:
        env = {k: (v if k in over or (k not in changed and ANY_ENV not in changed)
                   else _Unresolved(f"env.{k} {changed.get(k) or changed[ANY_ENV]}")) for k, v in env.items()}
    base = dict(ctx, env=env)
    layer, why = env_layer(step.get("env"), base, "step")
    return dict(base, env={**env, **layer}, over=over | set(layer), env_why=why or ctx.get("env_why"), state=state)


def expand_matrix(strategy):
    """GitHub matrix semantics: product, exclude (partial match), include (extend or add)."""
    if not strategy or "matrix" not in strategy:
        return [{}]
    m = strategy["matrix"]
    if isinstance(m, str):
        raise Unknown("matrix is an expression")
    base = {k: v for k, v in m.items() if k not in ("include", "exclude")}
    for k, v in base.items():
        if isinstance(v, str) and EXPR.search(v):
            raise Unknown(f"matrix.{k} is an expression")
        if not isinstance(v, list):
            raise Unknown(f"matrix.{k} is not a list")
    combos = [{}]
    for k, vals in base.items():
        combos = [dict(c, **{k: v}) for c in combos for v in vals]
    if not base:
        combos = []
    excl = m.get("exclude") or []
    inc = m.get("include") or []
    if isinstance(excl, str) or isinstance(inc, str):
        raise Unknown("include/exclude is an expression")
    combos = [c for c in combos if not any(all(c.get(k) == v for k, v in e.items()) for e in excl)]
    originals = [dict(c) for c in combos]  # include entries never extend combinations added by include
    for e in inc:
        applied = False
        for c, orig in zip(combos, originals):
            if all(orig.get(k, v) == v for k, v in e.items() if k in base):
                c.update(e)
                applied = True
        if not applied:
            combos.append(dict(e))
    return combos or [{}]


def _ubuntu_latest(label):
    """Runner labels are case-insensitive; Unknown when only a non-ASCII letter could decide."""
    same = gh_same_text(label.strip(), "ubuntu-latest")
    if same is None:
        raise Unknown(f"runs-on label {label!r}")
    return same


def hosted_ubuntu_2604(runs_on):
    """True for the hosted x64 labels, with the existing ubuntu-latest rule for groups."""
    explicit = True
    if isinstance(runs_on, dict):
        explicit = "group" not in runs_on
        runs_on = runs_on.get("labels")
    if isinstance(runs_on, list):
        if any(isinstance(x, str) and EXPR.search(x) for x in runs_on):
            raise Unknown("runs-on expression")
        if len(runs_on) != 1:
            return False
        runs_on = runs_on[0]
    if isinstance(runs_on, str):
        if EXPR.search(runs_on):
            raise Unknown("runs-on expression")
        if explicit and gh_same_text(runs_on.strip(), "ubuntu-26.04") is True:
            return True
        return _ubuntu_latest(runs_on)
    return False


COND = re.compile(r"^\s*(matrix(?:\.[A-Za-z0-9_-]+|\[\d+\]|\['[^']+'\])+|runner\.os)\s*(==|!=)\s*'([^']*)'\s*$")
# What .NET's String.Trim() removes (Char.IsWhiteSpace), before ParseNumber reads a string.
_NET_SPACE = "\t\n\v\f\r \x85\xa0                　"
# What Double.TryParse accepts with AllowLeadingSign | AllowDecimalPoint | AllowExponent (ASCII digits only).
_NET_DOUBLE = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?")


def _gh_number(v, cond):
    """An operand of `==` as a number when the two types differ, as the runner converts it
    (ExpressionUtility.ConvertToNumber and ParseNumber): null 0, false 0, true 1. A string is trimmed;
    '' is 0; a decimal number in the form Double.TryParse accepts is its value; 0x.. and 0o.. are
    Int32 values; anything else is NaN. Unknown where the runner's answer is not reproduced exactly:
    a character other than printable ASCII left after trimming, a value out of the double range,
    a hex or octal value of 2^31 or more (Int32 wraps or refuses it), Infinity spelled out."""
    if v is None:
        return 0.0
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        if isinstance(v, int) and abs(v) >= 2 ** 53:
            raise Unknown(f"condition {cond!r}")
        return float(v)
    if isinstance(v, str):
        s = v.strip(_NET_SPACE)
        if s == "":
            return 0.0
        if not all(" " <= ch <= "~" for ch in s):
            raise Unknown(f"condition {cond!r}")
        if _NET_DOUBLE.fullmatch(s):
            f = float(s)
            if math.isinf(f):
                raise Unknown(f"condition {cond!r}")
            return f
        m = re.fullmatch(r"0x([0-9a-fA-F]+)|0o([0-7]+)", s)
        if m:
            n = int(m.group(1), 16) if m.group(1) is not None else int(m.group(2), 8)
            if n >= 2 ** 31:
                raise Unknown(f"condition {cond!r}")
            return float(n)
        if re.fullmatch(r"[+-]?infinity", s, re.I):
            raise Unknown(f"condition {cond!r}")
        return float("nan")
    raise Unknown(f"condition {cond!r}")


def gh_equal(a, b, cond):
    """The expression `a == b` (EvaluationResult.AbstractEqual): two strings compare ignoring case
    (OrdinalIgnoreCase), other equal types by value, and different types as numbers, so matrix value 1
    equals '1.0' and 0 equals ' ', and NaN equals nothing. Unknown for an object or array, or a value
    of a type a workflow does not give."""
    def kind(v):
        if v is None:
            return "null"
        if isinstance(v, bool):
            return "bool"
        if isinstance(v, (int, float)):
            return "num"
        if isinstance(v, str):
            return "str"
        raise Unknown(f"condition {cond!r}")
    ka, kb = kind(a), kind(b)
    if ka == kb == "str":
        same = gh_same_text(a, b)
        if same is None:
            raise Unknown(f"condition {cond!r}")
        return same
    if ka == kb:
        return a == b  # NaN == NaN is false, as in the runner
    return _gh_number(a, cond) == _gh_number(b, cond)


def _outside_literals(c):
    """(index, character) for each character of expression c outside its '...' string literals."""
    i, n = 0, len(c)
    while i < n:
        if c[i] == "'":
            j = i + 1
            while True:
                j = c.find("'", j)
                if j < 0:
                    raise Unknown(f"condition {c!r}")
                if c[j + 1:j + 2] != "'":  # '' is a quote inside a literal
                    break
                j += 2
            i = j + 1
            continue
        yield i, c[i]
        i += 1


def _wrapped(p):
    """True when the bracket that opens p closes at its last character."""
    depth = 0
    for i, ch in _outside_literals(p):
        depth += ch in "(["
        depth -= ch in ")]"
        if depth == 0:
            return i == len(p) - 1
    return False


def _conjuncts(c):
    """The top-level `&&` operands of expression c, with brackets around an operand removed. None when
    c has `||` or a logical `!` anywhere outside a literal (an operand then no longer decides the
    whole), or unbalanced brackets: those conditions are not evaluated here."""
    parts, start, depth, skip = [], 0, 0, False
    for i, ch in _outside_literals(c):
        if skip:
            skip = False
            continue
        if ch in "([":
            depth += 1
        elif ch in ")]":
            depth -= 1
            if depth < 0:
                return None
        elif ch == "|" or (ch == "!" and c[i + 1:i + 2] != "="):
            return None
        elif ch == "&" and c[i + 1:i + 2] == "&" and depth == 0:
            parts.append(c[start:i])
            start, skip = i + 2, True
    if depth:
        return None
    parts.append(c[start:])
    out = []
    for p in (x.strip() for x in parts):
        if p.startswith("(") and _wrapped(p):
            inner = _conjuncts(p[1:-1])
            if inner is None:
                return None
            out += inner
        else:
            out.append(p)
    return out


def step_runs(cond, ctx, *, prove=False):
    """Evaluate simple `if:` conditions; True when unconditioned or not matrix/OS related.
    The step is ruled out only when a top-level `&&` operand is a matrix or runner.os comparison that
    GitHub's typed `==` makes false; any other shape that mentions them is Unknown. With prove=True,
    return None when no operand rules it out but some operand could not be evaluated."""
    if cond is None:
        return True
    c = js_str(cond).strip()
    c = EXPR.fullmatch(c).group(1) if EXPR.fullmatch(c) else c
    if not prove and "matrix." not in c and "runner.os" not in c:
        return True
    parts = None if "${{" in c else _conjuncts(c)  # text around ${{ }} makes a string, not a test
    if parts is None:
        raise Unknown(f"condition {c!r}")
    uncertain = False
    for p in parts:
        if not prove and "matrix." not in p and "runner.os" not in p:
            continue  # unrelated to the runner (event, branch, ...): assume it can run
        mm = COND.match(p)
        if not mm:
            if prove:
                path = _PATH.fullmatch(p)
                if path and path.group(1) == "matrix":
                    try:
                        value = gh_value(p, ctx)
                    except Unknown:
                        value = None
                    if value is False:
                        return False
                    uncertain |= value is not True
                elif p.lower() == "false":
                    return False
                elif p.lower() != "true":
                    uncertain = True
                continue
            raise Unknown(f"condition {c!r}")
        try:
            left = "Linux" if mm.group(1) == "runner.os" else gh_value(mm.group(1), ctx)
            eq = gh_equal(left, mm.group(3), c)
        except Unknown:
            if not prove:
                raise
            uncertain = True
            continue
        if (mm.group(2) == "==") != eq:
            return False
    return None if uncertain else True


STATUS_FN = re.compile(r"\b(success|failure|always|cancelled)\s*\(", re.I)


def _on_success_path(s):
    """Whether step s runs only when every earlier step of its list succeeded (or continued on error):
    its if: calls no status check function, so GitHub reads it as success() && (if), or success() is a
    top-level && operand and no other status function is called. Inside a composite action success() is
    the action's own status (runner SuccessFunction: action_status for composite main steps), so this
    holds per list of steps. Any other step (always(), failure(), cancelled(), !cancelled(),
    success() || ...) may run after an earlier step failed and a checkout between them was skipped."""
    cond = s.get("if")
    if cond is None:
        return True
    c = js_str(cond).strip()
    c = EXPR.fullmatch(c).group(1) if EXPR.fullmatch(c) else c
    called = {m.lower() for m in STATUS_FN.findall(c)}
    if not called:
        return True
    if called != {"success"}:
        return False
    try:
        parts = _conjuncts(c)
    except Unknown:
        return False
    return parts is not None and any(re.fullmatch(r"success\s*\(\s*\)", p, re.I) for p in parts)


def _view(s, state):
    """The account step s reads files against: the success path's, or for a step that may run after a
    failure, the one over every path."""
    return state if _on_success_path(s) else dict(state, files=_any(state))


def _entry(view):
    """The account a called local action starts from. Its steps' status starts as success, so a step in
    it that may run after one of them failed still sees what the caller's steps did before the call."""
    return dict(view, any=view["files"])


def _after_call(state, s, end):
    """The caller's account after the local action call s, whose steps took _entry(...) to `end`. Only a
    call with no if: and no continue-on-error certainly ran and succeeded on the success path, so only
    then do its own checkouts count there ("files" = its "files"). With an if: it may have been skipped,
    so what was changed before it stays changed; with continue-on-error it may have stopped at any of
    its steps, so only its "any" holds. Over every path: both."""
    soft = s.get("continue-on-error") not in (None, False)
    if "if" not in s and not soft:
        files = end["files"]
    else:
        files = _merge_paths(state["files"], _any(end) if soft else end["files"])
    return {"env": end["env"], "files": files, "any": _merge_paths(_any(state), _any(end))}


MAX_BYTES = 256 * 1024  # one file; the same limit as the browser's folder reader (lib/select.js)
MAX_ACTION_BYTES = 8 * 1024 * 1024  # all local action files read in one run
MAX_ACTION_CALLS = 200  # local action steps followed in one run (every job and matrix combination)


class Stopped(Exception):
    """The run's work limit was reached: the rest of the repository is UNKNOWN, one row per job."""


class _Run:
    """Per-run state: files the caller could not read (repo-relative path -> reason), parsed local
    actions, which actions may run a setup step, and the work done so far."""
    def __init__(self, root, unread=None):
        self.root = os.path.realpath(root)
        self.unread = dict(unread or {})
        self.actions = {}  # rel -> parsed action dict, or the Unknown it raised
        self.may = {}  # rel -> True / False; None while being computed (a cycle)
        self.summ = {}  # rel -> what a call of the action may change (_summary); None while being computed
        self.bytes = 0  # raw bytes of local action files read, refused ones included
        self.calls = 0
        self.stopped = None
        self.subs = None  # _submodules(): ((path, level), ...) or why they are not known

    def spend(self, n):
        self.bytes += n


_RUN = None


def _run(root):
    global _RUN
    if _RUN is None or _RUN.root != os.path.realpath(root):
        _RUN = _Run(root)
    return _RUN


def read_bytes(root, rel, limit=MAX_BYTES, spent=None):
    """The bytes of a file inside the checkout; None if missing or if it (or a symlink) leaves the
    checkout. At most limit + 1 bytes are read, so a caller can tell a file over its limit. A file
    larger than MAX_BYTES, or that the caller could not read, is Unknown: never a shortened copy
    that may parse as something shorter. `spent(n)` is told how many bytes were read before the
    size is checked, so a budget counts the bytes of a file refused for its size too. The file is
    read unbuffered, so the bytes read are the bytes taken from the file: a buffered reader takes
    more than it returns (Python 3.14 reads ahead up to 128 KB)."""
    base = os.path.realpath(root)
    p = os.path.realpath(os.path.join(base, rel))
    if os.path.commonpath([base, p]) != base:
        return None
    key = os.path.relpath(p, base).replace(os.sep, "/")
    why = _run(root).unread.get(key)
    if why:
        raise Unknown(f"{key} was not read ({why})")
    if not os.path.isfile(p):
        return None
    want, parts, got = min(limit, MAX_BYTES) + 1, [], 0
    try:
        with open(p, "rb", buffering=0) as f:
            while got < want:
                chunk = f.read(want - got)
                if not chunk:
                    break
                parts.append(chunk)
                got += len(chunk)
    except OSError:
        raise Unknown(f"{key} could not be read")
    finally:
        if spent:
            spent(got)
    b = b"".join(parts)
    if len(b) > MAX_BYTES:
        raise Unknown(f"{key} is larger than {MAX_BYTES // 1024} KB, so it was not read")
    return b


def read_text(root, rel):
    b = read_bytes(root, rel)
    return None if b is None else b.decode("utf-8", errors="replace")


def py_specs_from_file(root, rel):
    """setup-python getVersionInputFromFile."""
    txt = read_text(root, rel)
    if txt is None:
        raise Unknown(f"python-version-file {rel} not in checkout")
    if rel.endswith(".toml"):
        if tomllib is None:
            raise Unknown("tomllib unavailable")
        try:
            cfg = tomllib.loads(txt)
        except Exception:
            raise Unknown(f"{rel} not parseable")
        v = (cfg.get("project", {}).get("requires-python") if "project" in cfg
             else cfg.get("tool", {}).get("poetry", {}).get("dependencies", {}).get("python"))
        if v is None:
            return []
        return [" ".join(v.split(","))]
    if ".tool-versions" in rel:
        for line in txt.split("\n"):
            if line.strip().startswith("#"):
                continue
            m = re.match(r"^\s*python\s*v?\s*(\S+)\s*$", line)
            if m:
                return [m.group(1)]
        return []
    if "Pipfile" in rel:
        if tomllib is None:
            raise Unknown("tomllib unavailable")
        try:
            req = tomllib.loads(txt).get("requires", {})
        except Exception:
            raise Unknown(f"{rel} not parseable")
        v = req.get("python_full_version", req.get("python_version"))
        return [v] if v else []
    out = []
    for line in txt.strip().splitlines():
        if line.startswith("#") or not line.strip():
            continue
        out.append(line.strip().split("/")[0])
    return out


def ruby_spec_default(root, wd, names=(".ruby-version", ".tool-versions", "mise.toml")):
    for name in names:
        txt = read_text(root, os.path.join(wd, name))
        if txt is None:
            continue
        txt = txt.strip()
        if name == ".ruby-version":
            return txt
        rx = r"^ruby\s+(\S+)" if name == ".tool-versions" else r"""^\s*ruby\s*=\s*['"]([^'"]+)['"]\s*(?:#.*)?$"""
        for line in txt.splitlines():
            m = re.match(rx, line)
            if m:
                return m.group(1)
        raise Unknown(f"{name} has no ruby line")
    raise Unknown("no ruby-version and no version file")


def classify(ok24, ok26):
    if ok26:
        return "OK"
    return "BREAK" if ok24 else "ALREADY"


def _with(w, name, default=None):
    """A `with:` input of the step. The runner passes it as INPUT_<NAME in upper case>, so the action
    reads `Python-Version` as python-version; Unknown when that is not certain."""
    v = gh_key(w, name, "input")
    return default if v is _MISSING else v


def _guard(ctx, rel):
    """Before a step reads the file `rel`: Unknown if an earlier step may have changed it."""
    why = file_changed(ctx.get("state", NOTHING), rel)
    if why:
        raise Unknown(f"{rel} {why}")
    return True


def check_step(data, root, step, ctx):
    uses = step.get("uses", "")
    w = step.get("with")
    if w is None:
        w = {}
    elif not isinstance(w, dict):
        raise Unknown("with: is not a list of inputs")
    action = uses.split("@")[0].lower()
    out = []
    if action == "actions/setup-python":
        arch = substitute(_with(w, "architecture", "x64"), ctx) or "x64"
        allow = substitute(_with(w, "allow-prereleases", "false"), ctx) == "true"
        ftin = substitute(_with(w, "freethreaded", "false"), ctx) == "true"
        # setup-python's resolveVersionInput: the inputs as resolved and trimmed (an input that resolves
        # to empty is not given), python-version first, then python-version-file, then .python-version.
        pv, pvf = _with(w, "python-version"), _with(w, "python-version-file")
        raw = substitute(pv, ctx) if pv is not None else ""
        specs = [s.strip() for s in raw.splitlines() if s.strip()]
        rel = ""
        if not specs and pvf is not None:
            rel = substitute(pvf, ctx).strip()
        if not specs:
            _guard(ctx, rel or ".python-version")
        if specs:
            src = "python-version"
        elif rel:
            specs, src = py_specs_from_file(root, rel), rel
        else:
            if read_text(root, ".python-version") is None:
                return [("NA", "setup-python", "", "no version: uses python from PATH")]
            specs, src = py_specs_from_file(root, ".python-version"), ".python-version"
        for s in specs:
            if s.startswith(("pypy", "graalpy")):
                out.append(("NA", "setup-python", s, "PyPy/GraalPy builds are not per Ubuntu version"))
                continue
            r24 = resolve_python(data, s, "24.04", arch, allow, ftin)
            r26 = resolve_python(data, s, "26.04", arch, allow, ftin)
            out.append((classify(r24, r26), "setup-python", s, f"{src}: 24.04->{r24} 26.04->{r26}"))
    elif action == "ruby/setup-ruby":
        # setup-ruby: core.getInput(key) || the default, so an input that resolves to empty is the default
        wd = substitute(_with(w, "working-directory", "."), ctx).strip() or "."
        raw = substitute(_with(w, "ruby-version", "default"), ctx).strip() or "default"
        if raw in ("default", ".ruby-version", ".tool-versions", "mise.toml"):
            for name in ((".ruby-version", ".tool-versions", "mise.toml") if raw == "default" else (raw,)):
                _guard(ctx, posixpath.join(wd, name))
        if raw == "default":
            spec, src = ruby_spec_default(root, wd), "version file"
        elif raw in (".ruby-version", ".tool-versions", "mise.toml"):
            spec, src = ruby_spec_default(root, wd, (raw,)), raw
        else:
            spec, src = raw, "ruby-version"
        e, v24, s24 = resolve_ruby(data, spec, "24.04")
        _, v26, s26 = resolve_ruby(data, spec, "26.04")
        if v24 is None:  # version resolution is the same on every OS
            return [("ALREADY", "setup-ruby", spec, "unknown version on every OS")]
        if s24 is None or s26 is None:
            raise Unknown("asset probe failed")
        out.append((classify(s24 == 200, s26 == 200), "setup-ruby", spec, f"{src}: {e}-{v26} 24.04 HTTP {s24}, 26.04 HTTP {s26}"))
    return out


SETUP = ("actions/setup-python", "ruby/setup-ruby")
MAX_ACTION_DEPTH = 8  # composite actions calling local composite actions


def _action_of(step):
    uses = step.get("uses", "")
    return uses.split("@")[0].lower() if isinstance(uses, str) else ""


def _local(step):
    """The repo-relative folder of a `uses: ./path` step, or None. The path is kept whole, as the
    runner keeps it: `./x@v1` is the folder `x@v1`, not `x`."""
    uses = step.get("uses", "")
    if not isinstance(uses, str) or not uses.startswith("./"):
        return None
    return uses[2:].rstrip("/") or "."


def _relevant(steps, root, seen=()):
    """Setup steps, and local action steps that may run one: the action is not readable, or it is
    composite and (through any depth of local actions) has a setup step. A JavaScript or Docker
    action, or a composite one with no setup step anywhere in it, cannot run setup-python/setup-ruby."""
    return [s for s in steps if isinstance(s, dict) and (_action_of(s) in SETUP or _may_setup(root, _local(s), seen))]


def _may_setup(root, rel, seen):
    """Whether a local action may run a setup step. Worked out once per action and run: False only
    when every action it reaches was read and none has a setup step."""
    if rel is None:
        return False
    run = _run(root)
    if "./" + rel in seen or len(seen) >= MAX_ACTION_DEPTH or run.may.get(rel, False) is None:
        return True  # reported as UNKNOWN by check_steps
    if rel in run.may:
        return run.may[rel]
    run.may[rel] = None
    try:
        action = _read_action(root, rel)
    except Unknown:
        run.may[rel] = True
        return True
    runs = action.get("runs") if isinstance(action.get("runs"), dict) else {}
    if str(runs.get("using", "")).lower() != "composite":
        run.may[rel] = False
        return False
    inner = runs.get("steps") if isinstance(runs.get("steps"), list) else []
    run.may[rel] = bool(_relevant(inner, root, seen + ("./" + rel,))) or _summary(root, rel, seen)[2]
    return run.may[rel]


def _label(s, at=None):
    """The step as a row names it; `at`: the local action it is a step of (None: the job)."""
    u = s.get("uses")
    what = "a run step" if "run" in s else f"uses: {u}" if isinstance(u, str) else "a step"
    return f"{what} in {at}" if at else what


def _in(via):
    return via[-1] if via else None


def _given(w, name):
    """Whether the input is set to something that may not be empty (an expression may be anything)."""
    v = _with(w, name)
    return v is not None and js_str(v).strip() != ""


def _is_expr(v, *names):
    return isinstance(v, str) and re.sub(r"\s+", "", v) in {"${{%s}}" % n for n in names}


def _effect(s, state, at=None, *, checkout_proven=False):
    """The account after a step that is not a local action. Only actions/checkout, setup-python and
    setup-ruby have effects known from their source; a run step, a docker:// step or any other
    published action may set any variable and change any file (GITHUB_ENV, the workspace)."""
    why = f"may be changed by an earlier step ({_label(s, at)})"
    uses = s.get("uses")
    if "run" in s or not isinstance(uses, str) or uses.startswith("docker://"):
        return _everything(why, state)
    w = s.get("with")
    w = {} if w is None else w
    if not isinstance(w, dict):
        return _everything(why, state)
    a = _action_of(s)
    try:
        if a == "actions/checkout":
            return _checkout_effect(s, w, state, at, s.get("if") is None or checkout_proven)
        if a == "actions/setup-python":
            cache = _with(w, "cache")
            cache = "" if cache is None else js_str(cache).strip()
            if _given(w, "pip-install") or _given(w, "pip-version") or cache not in ("", "pip", "pipenv"):
                # pip-install runs the packages' build code; pip-version runs pip install with the job's env
                # and pip config (find-python.ts installPip); the poetry cache runs poetry
                return _everything(why, state)
            change = {"env": dict.fromkeys(PY_EXPORTS, why), "files": {}}
            if cache:
                # cache-distributor.ts restores into `pip cache dir` (set by pip's env and config files, so it
                # may be a workspace folder) or ~/.local/share/virtualenvs (HOME may be set anywhere): the
                # folder is not known from the files, so neither is any workspace file after it.
                change["files"] = {"": (f"may be changed by an earlier step ({_label(s, at)}, which may restore its {cache} cache into the workspace)", NOKEEP)}
            return _merge(state, change)
        if a == "ruby/setup-ruby":
            bc = _with(w, "bundler-cache")  # setup-ruby: bundle install only when the input is 'true'
            if bc is not None and (EXPR.search(js_str(bc)) or js_str(bc).strip() == "true"):
                return _everything(why, state)  # bundle install evaluates the Gemfile and builds gems
            rg = _with(w, "rubygems")  # index.js: getInput || 'default'; else gem update --system runs an installer
            if rg is not None and js_str(rg).strip() not in ("", "default"):
                return _everything(why, state)
            return _merge(state, {"env": dict.fromkeys(RUBY_EXPORTS, why), "files": {}})
    except Unknown:
        return _everything(why, state)
    return _everything(why, state)


_GLOB = re.compile(r"[*?\[\]!\\#]")


def _sparse_keep(prefix, lines, cone):
    """What a sparse checkout into `prefix` leaves as given (git sparse-checkout): cone mode keeps the
    listed folders, the files directly in the root and in each folder above a listed one; non-cone mode
    keeps each pattern's path and what is below it. A pattern this does not read exactly (a glob, a
    negation, an expression, a path out of the checkout) keeps nothing."""
    under, exact, files_in = [], [], {prefix}
    for line in lines:
        q = line.strip()
        r = _norm_rel(q.strip("/")) if q.strip("/") else None
        if EXPR.search(q) or _GLOB.search(q) or r is None:
            return NOKEEP
        full = posixpath.join(prefix, r) if prefix else r
        if cone:
            under.append(full)
            d = posixpath.dirname(full)
            while d != prefix and d:
                files_in.add(d)
                d = posixpath.dirname(d)
        else:
            exact.append(full)
    return (tuple(under), tuple(exact), tuple(sorted(files_in)) if cone else ())


def _checkout_effect(s, w, state, at, proven):
    """actions/checkout (v4/v5 action.yml, src): it exports no variable. Into `path` (default the
    workspace root) it puts `repository` at `ref`. The snapshot given is this repository at the
    triggering commit: repository not given (or github.repository) and ref not given (or github.sha).
    An explicit ref, ${{ github.ref }} included, is fetched when the step runs and may have moved since
    the trigger (checkout input-helper.ts: only an unset ref on this repository pins github.sha).
    Into the root, if proven to run and clean (the default), it replaces the files of this repository:
    every file is as given, or with sparse-checkout only the paths it lists (filter alone leaves every
    file), except in submodule folders (_submodule_effect). It does so only when no earlier step may have
    changed how git runs. A step with unknown workspace or environment effects may change Git's
    config, hooks or executable. A checkout into .git also leaves later Git effects unknown.
    Anything else makes the files at its path not the ones given."""
    label = _label(s, at)
    pending = "" if proven else f"; checkout may not run: if: {js_str(s.get('if'))}"
    soft = s.get("continue-on-error") not in (None, False)
    if pending or soft:
        reason = pending or "; checkout may have failed: continue-on-error"
        state = _checkout_note(state, f"was not established in the workspace ({label}{reason})")
    repo, ref, path = _with(w, "repository"), _with(w, "ref"), _with(w, "path")
    ps = "" if path is None else js_str(path)
    prefix = None if EXPR.search(ps) else _norm_rel(ps)
    this = ((repo is None or js_str(repo).strip() == "" or _is_expr(repo, "github.repository"))
            and (ref is None or js_str(ref).strip() == "" or _is_expr(ref, "github.sha")))
    sparse, cm = _with(w, "sparse-checkout"), _with(w, "sparse-checkout-cone-mode")
    lines = [x.strip() for x in js_str(sparse).splitlines() if x.strip()] if sparse is not None else []
    cms = "" if cm is None else js_str(cm).strip()
    if prefix is None:  # an expression, or a path out of the workspace (which checkout refuses)
        why = f"may be changed by an earlier step ({_label(s, at)}, which checks out at a path the files do not give)"
        return _merge(state, {"env": {}, "files": {"": (why, NOKEEP)}})
    if prefix == ".git" or prefix.startswith(".git/"):  # hooks, config: how every later git runs
        return _everything(f"may be changed by an earlier step ({_label(s, at)})", state)
    keep = None  # every file of this repository
    if lines:
        keep = NOKEEP if EXPR.search(cms) else _sparse_keep(prefix, lines, cms == "" or cms.upper() == "TRUE")
    what = ("another repository or commit" if not this else "a second copy of this repository" if keep is None
            else "only part of this repository")
    why = f"may be changed by an earlier step ({label}, which checks out {what} at {prefix or 'the workspace root'}{pending})"
    keep = keep if this else NOKEEP
    clean = _with(w, "clean")
    workspace = state["files"].get("")
    git_known = ANY_ENV not in state["env"] and (workspace is None or workspace[1] != NOKEEP)
    clean_or_empty = (clean is None or js_str(clean).strip().upper() == "TRUE"
                      or state["files"].keys() == {NO_CHECKOUT})
    replaces = proven and not soft and git_known and clean_or_empty
    if this and prefix == "":
        gone = {} if keep is None else {"": (why, keep)}
        gone.update(_submodule_effect(s, w, state, at, sparse=keep is not None))
        if replaces:  # on the success path only: on any other path this checkout may have been skipped
            return {"env": state["env"], "files": gone, "any": _merge_paths(_any(state), gone)}
        return _merge(state, {"env": {}, "files": gone})
    if prefix:
        state = _checkout_note(state, f"was not established in the workspace root ({label} uses path: {ps}{pending})")
    return _merge(state, {"env": {}, "files": {prefix: (why, NOKEEP)}})


def _submodule_effect(s, w, state, at, sparse):
    """What a checkout of this repository into the root leaves of submodule folders (checkout v4/v5
    git-source-provider.ts, git-directory-helper.ts). git clean -ffdx, git reset --hard and the forced
    checkout put back the files of this repository only: a submodule's folder keeps what an earlier step
    left there, or is empty on a fresh workspace. `submodules: true` then runs git submodule update --init
    --force for the first level, `recursive` for every level, which puts back the submodule's tracked
    files; a file an earlier step added there stays (git clean is not run inside it), so a submodule an
    earlier step may have changed stays changed. A folder that holds its own Git repository and is no
    listed submodule is never put back. When the folder does not show the submodules, nothing is."""
    label = _label(s, at)
    subs = _submodules()
    if not isinstance(subs, tuple):
        return {"": (f"may be changed by an earlier step ({label}, which does not put back submodule folders, "
                     f"and which folders are submodules is not known: {subs})", NOKEEP)}
    sm = _with(w, "submodules")
    sm = "" if sm is None else js_str(sm).strip().upper()
    level = 0 if sparse else MAX_SUBMODULE_DEPTH if sm == "RECURSIVE" else 1 if sm == "TRUE" else 0
    out = {GITDIRS: (f"may be changed by an earlier step ({label}, which does not put back a folder that "
                     f"holds its own Git repository)", NOKEEP)}
    for p, lvl in subs:
        if lvl > level:
            out[p] = (f"may be changed by an earlier step ({label}, which does not check out the submodule at {p})", NOKEEP)
            continue
        for q, (why, keep) in state["files"].items():
            if q in (GITDIRS, NO_CHECKOUT):
                continue
            if q == "" or q == p or p.startswith(q + "/"):
                out[p] = (why, NOKEEP)
            elif q.startswith(p + "/"):
                out[q] = (why, keep)
    return out


def _summary(root, rel, seen=()):
    """What a call of the local action ./rel may change, worked out once per action from its files alone
    (each condition may hold, each input may be anything): (account, reads, blind). account: its steps'
    account from nothing; reads: the local action folders it calls, which the caller's account must not
    have changed; blind: it calls a local action after a step of its own that may have changed that
    action's files, so it may run a setup step the files do not show. Not readable, not composite, too
    deep or a cycle: everything."""
    run = _run(root)
    label = "./" + rel
    every = (_opaque(f"may be changed by an earlier step (uses: {label})"), frozenset(), False)
    if label in seen or len(seen) >= MAX_ACTION_DEPTH or run.summ.get(rel, False) is None:
        return every
    if rel in run.summ:
        return run.summ[rel]
    run.summ[rel] = None
    try:
        action = _read_action(root, rel)
    except Unknown:
        run.summ[rel] = every
        return every
    runs = action.get("runs") if isinstance(action.get("runs"), dict) else {}
    inner = runs.get("steps")
    if str(runs.get("using", "")).lower() != "composite" or not isinstance(inner, list):
        run.summ[rel] = every  # a JavaScript or Docker action of this repository
        return every
    state, reads, blind = NOTHING, {rel}, False
    for s in inner:
        if not isinstance(s, dict):
            continue
        sub = _local(s)
        if sub is None:
            state = _effect(s, state, label)
        elif _reads_changed(root, _view(s, state), sub, seen + (label,)):
            state, blind = _everything(f"may be changed by an earlier step (uses: ./{sub} in {label})", state), True
        else:
            ch, rd, bl = _summary(root, sub, seen + (label,))
            state, reads, blind = _after_call(state, s, _merge(_entry(_view(s, state)), ch)), reads | rd, blind or bl
    run.summ[rel] = (state, frozenset(reads), blind)
    return run.summ[rel]


def _after_local(root, state, s, rel, via):
    """The account after the call s of the local action ./rel when it reports nothing (no setup step in it)."""
    return _after_call(state, s, _merge(_entry(_view(s, state)), _summary(root, rel, via)[0]))


def _reads_changed(root, state, rel, via):
    """Why the files of the local action ./rel, or of a local action it calls, may not be the ones given
    (an earlier step may have changed them), or None. The runner loads each from the workspace when it
    starts, so a changed one may run a setup step the files do not show."""
    return folder_changed(state, rel) or next(
        (w for r in sorted(_summary(root, rel, via)[1]) if (w := folder_changed(state, r))), None)


def _read_action(root, rel):
    """The parsed action.yml of a local action folder, read once per run; Unknown if it is not in the
    checkout, cannot be read whole, or the run has read MAX_ACTION_BYTES of actions already."""
    run = _run(root)
    if rel not in run.actions:
        try:
            run.actions[rel] = _load_action(root, rel, run)
        except Unknown as u:
            run.actions[rel] = u
    got = run.actions[rel]
    if isinstance(got, Unknown):
        raise got
    return got


def _load_action(root, rel, run):
    """Reads an action.yml within the run's MAX_ACTION_BYTES budget: every raw byte read counts,
    including those of a file then refused for its size. Once the budget is spent no further file is
    opened, and a file that would pass it is read only up to the budget + 1 byte."""
    over = f"local action ./{rel} was not read (this check reads at most {MAX_ACTION_BYTES // 2**20} MB of local actions)"
    for name in ("action.yml", "action.yaml"):
        left = MAX_ACTION_BYTES - run.bytes
        if left <= 0:
            raise Unknown(over)
        path = os.path.join(rel, name)
        resolved = os.path.realpath(os.path.join(run.root, path))
        if os.path.commonpath((run.root, resolved)) != run.root:
            # A preferred manifest outside the selected tree is not evidence for the fallback.
            raise Unknown(f"local action ./{rel} has a manifest outside the checkout ({name})")
        b = read_bytes(root, path, left, spent=run.spend)
        if b is None:
            continue
        if len(b) > left:
            raise Unknown(over)
        try:
            doc = load_yaml(b.decode("utf-8", errors="replace"))
        except Exception as e:
            raise Unknown(f"local action ./{rel} YAML error {type(e).__name__}")
        return doc if isinstance(doc, dict) else {}
    raise Unknown(f"local action ./{rel} not in checkout")


def _action_inputs(action, step, ctx):
    """The inputs context of a composite action: the caller's with: values (resolved in the caller's
    context), else the action's declared default, else ''. An unresolvable value is read as Unknown."""
    declared = action.get("inputs") if isinstance(action.get("inputs"), dict) else {}
    given = step.get("with") if isinstance(step.get("with"), dict) else {}
    out = {}
    for name, spec in declared.items():
        key = str(name)
        try:
            raw, where = gh_key(given, key, "input"), "with"
        except Unknown as u:
            out[key] = _Unresolved(str(u))
            continue
        if raw is _MISSING:
            raw = spec.get("default", "") if isinstance(spec, dict) else ""
            where = "default"
        if raw is None:
            raw = ""
        try:
            out[key] = substitute(raw, ctx) if where == "with" else (
                _Unresolved(f"input {key} default is an expression") if isinstance(raw, str) and EXPR.search(raw) else js_str(raw))
        except Unknown as u:
            out[key] = _Unresolved(f"input {key}: {u}")
    return out


def check_steps(data, root, steps, ctx, depth=0, via=(), out=None, state=NOTHING):
    """Findings for the setup steps among `steps` (as (status, action, spec, why, via)), appended to
    `out`, following local composite actions, with one account (state) of what the steps before each
    step may have changed. Returns the account after the last step. A step that cannot be resolved is
    UNKNOWN, never skipped. Raises Stopped when the run has followed MAX_ACTION_CALLS local action steps
    (`out` keeps what was found)."""
    out = [] if out is None else out
    for s in steps:
        if isinstance(s, dict):
            state = _check_one(data, root, s, ctx, state, depth, via, out)
    return state


def _check_one(data, root, s, ctx, state, depth, via, out):
    """One step: its rows if it is a setup step, or a local action that may run one or whose files an
    earlier step may have changed; and the account after it."""
    rel = _local(s)
    if _action_of(s) == "actions/checkout":
        try:
            runs = step_runs(s.get("if"), ctx, prove=True)
        except Unknown:
            runs = None
        if runs is False:
            why = (f"was not established in the workspace ({_label(s, _in(via))} is skipped for this matrix leg: "
                   f"if: {js_str(s.get('if'))})")
            return _checkout_note(state, why)
        return _effect(s, state, _in(via), checkout_proven=runs is True)
    try:
        cond = None
        if not step_runs(s.get("if"), ctx):
            return state  # ruled out: it neither runs a setup step nor changes anything
    except Unknown as u:
        cond = u  # it may run
    if rel is None and _action_of(s) not in SETUP:
        return _effect(s, state, _in(via))
    view = _view(s, state)  # what it reads its files against
    if rel is not None and not _reads_changed(root, view, rel, via) and not _may_setup(root, rel, via):
        return _after_local(root, state, s, rel, via)
    after = _effect(s, state, _in(via)) if rel is None else None
    try:
        if cond:
            raise cond
        sctx = step_env(ctx, s, view)
        if rel is None:
            for st, act, spec, why in check_step(data, root, s, sctx):
                out.append((st, act, spec, why, via))
            return after
        return _after_call(state, s, _follow(data, root, s, rel, sctx, _entry(view), depth, via, out))
    except Unknown as u:
        out.append(("UNKNOWN", s.get("uses", ""), "", str(u), via))
        return after or _everything(f"may be changed by an earlier step ({_label(s, _in(via))})", state)


def _follow(data, root, s, rel, sctx, state, depth, via, out):
    """The steps of a local action that may run a setup step, read from the files only when no earlier
    step may have changed them; from the account it starts with (state, see _entry), the account after
    its last step."""
    run = _run(root)
    label = "./" + rel
    why = folder_changed(state, rel)
    if why:
        raise Unknown(f"local action {label} {why}")
    run.calls += 1
    if run.calls > MAX_ACTION_CALLS:
        run.stopped = f"this check stops after following {MAX_ACTION_CALLS} local action steps"
        raise Stopped(run.stopped)
    if label in via:
        raise Unknown(f"local action {label} calls itself")
    if depth >= MAX_ACTION_DEPTH:
        raise Unknown(f"local action {label} nested more than {MAX_ACTION_DEPTH} deep")
    action = _read_action(root, rel)
    runs = action.get("runs") if isinstance(action.get("runs"), dict) else {}
    if str(runs.get("using", "")).lower() != "composite":
        # a JavaScript or Docker action: setup-python/setup-ruby are not its steps, but it may change anything
        return _everything(f"may be changed by an earlier step ({_label(s, _in(via))})", state)
    actx = {"matrix": sctx.get("matrix", {}), "env": sctx["env"], "over": sctx["over"],
            "env_why": sctx.get("env_why"), "inputs": _action_inputs(action, s, sctx)}
    inner = runs.get("steps") if isinstance(runs.get("steps"), list) else []
    return check_steps(data, root, inner, actx, depth + 1, via + (label,), out, state)


def _job_relevant(root, steps):
    """Whether a job has a step to report: a setup step, or a local action that may run one or whose
    files an earlier step may have changed. Worked out from the files alone (each step may run), so it
    keeps every job the walk with the job's values could report."""
    if not isinstance(steps, list):
        return False
    state = JOB_START
    for s in steps:
        if not isinstance(s, dict):
            continue
        rel = _local(s)
        if rel is None:
            if _action_of(s) in SETUP:
                return True
            state = _effect(s, state)
        elif _reads_changed(root, _view(s, state), rel, ()) or _may_setup(root, rel, ()):
            return True
        else:
            state = _after_local(root, state, s, rel, ())
    return False


def check_workflow(data, root, path, doc):
    res = []
    run = _run(root)
    if doc is None:
        return res  # an empty file
    if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict):
        # e.g. a composite action.yml pasted as a workflow: nothing here was checked, so do not say so
        return [("UNKNOWN", "", "", f"{path}: not a workflow (no jobs)", False, "")]
    # workflow env: may use github, secrets, vars and inputs only, none of which the files give
    wenv, wwhy = env_layer(doc.get("env"), {}, "workflow")
    for jid, job in doc["jobs"].items():
        if not isinstance(job, dict):
            continue
        steps = job.get("steps") or []
        if "uses" in job and not steps:
            continue  # reusable workflow call: checked where defined (inputs there are UNKNOWN)
        if not _job_relevant(root, steps):
            continue
        loc = f"{path}:{jid}"
        if run.stopped:
            res.append(("UNKNOWN", "", "", f"{loc}: {run.stopped}", False, ""))
            continue
        try:
            combos = expand_matrix(job.get("strategy"))
        except Unknown as u:
            res.append(("UNKNOWN", "", "", f"{loc}: {u}", False, ""))
            continue
        soft_job = job.get("continue-on-error")
        for combo in combos:
            ctx = {"matrix": combo, "env": {}}
            label = ",".join(f"{k}={'?' if isinstance(v, _Unresolved) else js_str(v)}" for k, v in combo.items() if not isinstance(v, (dict, list)))
            where = f"{loc}[{label}]" if label else loc
            try:
                ro = job.get("runs-on")
                if isinstance(ro, str) and EXPR.search(ro):
                    ro = substitute(ro, ctx)
                elif isinstance(ro, list):
                    ro = [substitute(x, ctx) if isinstance(x, str) else x for x in ro]
                if not hosted_ubuntu_2604(ro):
                    continue
                if job.get("container"):
                    res.append(("NA", "", "", f"{where}: runs in a container", False, ""))
                    continue
                if not step_runs(job.get("if"), ctx):
                    continue
                try:
                    soft = soft_job is True or (isinstance(soft_job, str) and substitute(soft_job, ctx) == "true")
                except Unknown:
                    soft = None  # continue-on-error not static: the setup result is still known
                jenv, jwhy = env_layer(job.get("env"), {"matrix": combo}, "job")  # job env sees matrix, not env
                ctx.update(env={**wenv, **jenv}, over=frozenset(), env_why=wwhy or jwhy)
                found = []
                try:
                    check_steps(data, root, steps, ctx, out=found, state=JOB_START)
                finally:  # a Stopped run keeps what it found before the limit
                    for st, act, spec, why, via in found:
                        res.append((st, act, spec, f"{where}: {why}", soft, " > ".join(via)))
            except Unknown as u:
                res.append(("UNKNOWN", "", "", f"{where}: {u}", False, ""))
            except Stopped as u:
                res.append(("UNKNOWN", "", "", f"{where}: {u}", False, ""))
                break
    return res


_WORKFLOW = re.compile(r"\.github/workflows/([^/]+\.ya?ml)")


def check_repo(data, root, unread=None):
    """Every workflow in .github/workflows. `unread`: repo-relative paths the caller could not read
    (too large, over its limits) -> reason; reading one of them is UNKNOWN, and an unread workflow is a row."""
    global _RUN
    _RUN = _Run(root, unread)
    wfdir = os.path.join(root, ".github", "workflows")
    out = []
    names = {n for n in os.listdir(wfdir) if n.endswith((".yml", ".yaml"))} if os.path.isdir(wfdir) else set()
    names |= {m.group(1) for m in map(_WORKFLOW.fullmatch, _RUN.unread) if m}
    for name in sorted(names):
        p = os.path.join(wfdir, name)
        if os.path.islink(p):
            continue
        rel = f".github/workflows/{name}"
        try:
            txt = read_text(root, rel)
        except Unknown as u:
            out.append(("UNKNOWN", "", "", f"{rel}: {u}", False, ""))
            continue
        if txt is None:
            continue
        try:
            doc = load_yaml(txt)
        except Exception as e:
            out.append(("UNKNOWN", "", "", f".github/workflows/{name}: YAML error {type(e).__name__}", False, ""))
            continue
        try:
            out += check_workflow(data, root, rel, doc)
        except Exception as e:  # never a crash with no answer: what this file needed is not known
            out.append(("UNKNOWN", "", "", f"{rel}: this check could not read it ({type(e).__name__})", False, ""))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repos", nargs="+")
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
    ap.add_argument("--refresh", action="store_true", help="re-download manifests and re-read the image cache lists")
    ap.add_argument("--json", action="store_true", help="one JSON object per repo")
    ap.add_argument("--unread", metavar="FILE", help="JSON object: repo-relative path -> why it was not read")
    a = ap.parse_args(argv)
    data = Data(a.data, a.refresh)
    worst = 0
    for r in a.repos:
        unread = None
        if a.unread:
            with open(a.unread, encoding="utf-8") as f:
                unread = json.load(f)
        res = check_repo(data, r, unread)
        if a.json:
            print(json.dumps({"repo": r, "findings": [dict(zip(("status", "action", "spec", "where", "continueOnError", "via"), x)) for x in res]}))
        else:
            for st, act, spec, where, soft, via in res:
                if st != "NA":
                    print(f"{st:8} {act or '-':13} {spec or '-':10} {where}{' (continue-on-error)' if soft else ''}{f' (in {via})' if via else ''}")
        if any(x[0] == "BREAK" for x in res):
            worst = 1
    return worst


if __name__ == "__main__":
    sys.exit(main())
