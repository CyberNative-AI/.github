#!/usr/bin/env python3
"""checkbeam2604.py: predict which erlef/setup-beam steps fail at setup when `ubuntu-latest`
moves from Ubuntu 24.04 to 26.04 (rollout 2026-10-19 to 11-19, actions/runner-images#14748).

setup-beam downloads Erlang/OTP from builds.hex.pm, from a list per Ubuntu version. Two causes:
  OTP  the requested otp-version resolves in amd64/ubuntu-24.04/builds.txt but not in
       amd64/ubuntu-26.04/builds.txt (no OTP 24 or 25 builds for 26.04)
  ref  the pinned setup-beam ref does not know the 26.04 image (ImageOS `ubuntu26`, added in
       v1.24.1) and fails for every OTP version
Each setup-beam step on an ubuntu-latest job (after matrix expansion) is resolved with a
Python port of the action's own version matching (v1.24.1) and classified:
  BREAK    installs on 24.04 today, fails at setup on 26.04
  OK       installs on 26.04
  ALREADY  fails on 24.04 too (not caused by the migration)
  UNKNOWN  the input cannot be resolved statically (expression, reusable workflow, ...)
Nothing is reported OK unless it was resolved.

usage: checkbeam2604.py [--data DIR] [--refresh] [--offline] [--json] REPO_DIR [REPO_DIR ...]
Needs Python 3.11+ and PyYAML. The builds.txt lists and looked-up setup-beam refs live in --data.
"""
import argparse, functools, json, os, re, sys, urllib.error, urllib.parse, urllib.request

if sys.version_info < (3, 11):
    sys.exit("checkbeam2604.py needs Python 3.11 or later")
import tomllib  # noqa: E402

import yaml  # noqa: E402

OSES = ("24.04", "26.04")
BUILDS_URL = "https://builds.hex.pm/builds/otp/amd64/ubuntu-{os}/builds.txt"
REF_URL = "https://raw.githubusercontent.com/erlef/setup-beam/{ref}/dist/index.js"
BEAM_ACTIONS = ("erlef/setup-beam", "erlef/setup-elixir")  # setup-elixir is the repository's old name
OTHER_ACTIONS = ("actions/setup-elixir", "gleam-lang/setup-erlang")

# erlef/setup-beam tags and main on 2026-10-13: name, commit, Ubuntu images its
# dist/index.js maps (24 = ImageOS ubuntu24, 26 = ubuntu26; - = neither).
SETUP_BEAM_REFS = """
1.0.0 45a82c0a5af423088acb72efa3b677d38af5b4bc -
v1 54075bcc5e249e4758d363f27d099f55d843f124 24,26
v1.0 45a82c0a5af423088acb72efa3b677d38af5b4bc -
v1.0.0 45a82c0a5af423088acb72efa3b677d38af5b4bc -
v1.1 1a3c64091d474cbde0480f3d6b9be27ac85a1fb4 -
v1.1.0 1a3c64091d474cbde0480f3d6b9be27ac85a1fb4 -
v1.2 413f3328711062ca1a27f4c0cefa38a797a874ef -
v1.2.0 811b4b88e8793da6b78b8fdee26d97f85c823afd -
v1.2.1 67712d17154d46c94d32e763f856b6d48c294b9e -
v1.2.2 413f3328711062ca1a27f4c0cefa38a797a874ef -
v1.3 2071beb570a53fb599fbd638d0a4f4577d57143d -
v1.3.0 2071beb570a53fb599fbd638d0a4f4577d57143d -
v1.4 584173361f39a00f77ffc37c6b9a090f9313605d -
v1.4.0 230dd25d80c9dc282a18834a6453c0217c466924 -
v1.4.1 7a03a874e96e3aa8ee0626a0152bb1f9aeaa1be9 -
v1.4.2 584173361f39a00f77ffc37c6b9a090f9313605d -
v1.5 3c118cec41f6c3bfc2c7f2aef9bec886ab0b2324 -
v1.5.0 3c118cec41f6c3bfc2c7f2aef9bec886ab0b2324 -
v1.6 885971a72ed1f9240973bd92ab57af8c1aa68f24 -
v1.6.0 885971a72ed1f9240973bd92ab57af8c1aa68f24 -
v1.7 11d59b146c83dbe8215ca203ebe4aca822d443a7 -
v1.7.0 78d10b5f616e2f356ec1bba98260ea57001d2363 -
v1.7.1 b50aa182196c819a7dadaf531df48de189d84c56 -
v1.7.2 11d59b146c83dbe8215ca203ebe4aca822d443a7 -
v1.8 ade4f1d5676f98d7d890c87e6151f47340ac235c -
v1.8.0 d8a37f5aac5697ad06bc85db417e9cd4e3b5c27d -
v1.8.1 830642517cf03e22e8e8db5e80ace29342f5be28 -
v1.8.2 9283f857f115cde44f2031cd545cad363fb5274d -
v1.8.3 ade4f1d5676f98d7d890c87e6151f47340ac235c -
v1.9 988e02bfe678367a02564f65ca2e37726dc0268f -
v1.9.0 988e02bfe678367a02564f65ca2e37726dc0268f -
v1.10 730ac65cba0700bad37c0744de4aa916c16bb728 -
v1.10.0 730ac65cba0700bad37c0744de4aa916c16bb728 -
v1.11 10d50f70626dbb9c5174531ada017b8b4f14c215 -
v1.11.0 c428d8c359c7a208a7471729c4a619c35780d541 -
v1.11.1 2e0500f2a50c7f883e15eb4d0fa7dc15d2c458c1 -
v1.11.2 10d50f70626dbb9c5174531ada017b8b4f14c215 -
v1.12 69fb25ba7e2c546dfc085871ecf2fc5382c9843d -
v1.12.0 69fb25ba7e2c546dfc085871ecf2fc5382c9843d -
v1.13 6b2f8153b4b819accafd6aa10674dd245410e536 -
v1.13.0 6b2f8153b4b819accafd6aa10674dd245410e536 -
v1.13.1 d85df626dd55cfc806e6b7593a0dfb2a465214a2 -
v1.14 713cc2ffe3d38766349884daa5a1180763755855 -
v1.14.0 713cc2ffe3d38766349884daa5a1180763755855 -
v1.15 c2e02f777c158310fc6d3d4e11b36a52d2d52db8 -
v1.15.0 b980a5ac9b7316a23ebc16de2bb69b7c3ad731b5 -
v1.15.1 c10774ce0f4adb77996edcc725050c161b3703cb -
v1.15.2 e3f6ffe2878180f57318bf13febd3933ee81f664 -
v1.15.3 a255120a8298b1d3ebd952d84954db5471801f8f -
v1.15.4 c2e02f777c158310fc6d3d4e11b36a52d2d52db8 -
v1.16 61e01a43a562a89bfc54c7f9a378ff67b03e4a21 -
v1.16.0 61e01a43a562a89bfc54c7f9a378ff67b03e4a21 -
v1.17 0a541161e47ec43ccbd9510053c5f336ca76c2a2 24
v1.17.0 a34c98fd51e370b4d4981854aba1eb817ce4e483 -
v1.17.1 b60baf47530760859821edca21cbcd3a1bd366cd -
v1.17.2 8b9cac4c04dbcd7bf8fd673e16f988225d89b09b -
v1.17.3 a23b1fc4452a892cf3e92cbc2c405256cd6c27ec -
v1.17.4 904c511e63061a8f501ae4b081ce2c0e9cfc70ab -
v1.17.5 2f0cc07b4b9bea248ae098aba9e1a8a1de5ec24c -
v1.17.6 0a541161e47ec43ccbd9510053c5f336ca76c2a2 24
v1.18 5304e04ea2b355f03681464e683d92e3b2f18451 24
v1.18.0 a6e26b22319003294c58386b6f25edbc7336819a 24
v1.18.1 b9c58b0450cd832ccdb3c17cc156a47065d2114f 24
v1.18.2 5304e04ea2b355f03681464e683d92e3b2f18451 24
v1.19 8aa8a857c6be0daae6e97272bb299d5b942675a4 24
v1.19.0 8aa8a857c6be0daae6e97272bb299d5b942675a4 24
v1.20 e6d7c94229049569db56a7ad5a540c051a010af9 24
v1.20.0 b29c86feb9d880f6fb0b1ae3d5be5aa9004157d7 24
v1.20.1 75edbb82877ab10edeb12a99c3cf2f0909f3dc87 24
v1.20.2 6389fe58dcb1ee91fd829c7c65bf8771b06dacc4 24
v1.20.3 8e7fdef09ffa3ea54328b5000c170a3b9b20ca96 24
v1.20.4 e6d7c94229049569db56a7ad5a540c051a010af9 24
v1.21 3580539ceec3dc05b0ed51e9e10b08eb7a7c2bb4 24
v1.21.0 3580539ceec3dc05b0ed51e9e10b08eb7a7c2bb4 24
v1.22 9d5b75ddfda22fb979d2270283237aef8aa68d6b 24
v1.22.0 9d5b75ddfda22fb979d2270283237aef8aa68d6b 24
v1.23 ee09b1e59bb240681c382eb1f0abc6a04af72764 24
v1.23.0 ee09b1e59bb240681c382eb1f0abc6a04af72764 24
v1.24 54075bcc5e249e4758d363f27d099f55d843f124 24,26
v1.24.0 fc68ffb90438ef2936bbb3251622353b3dcb2f93 24
v1.24.1 54075bcc5e249e4758d363f27d099f55d843f124 24,26
main 8736e9244717f9207464c14c6051b71d22253f60 24,26
"""


# ---------------------------------------------------------------- node-semver 7.7.4 subset
# setup-beam matches versions with node-semver (7.7.4 in its lockfile). This is a port of the
# parts it calls (Range, coerce, maxSatisfying, intersects, gt) in default, non-loose mode,
# using node-semver's own regular expressions. ASCII only: other input is UNKNOWN upstream.
MAX_LENGTH, MAX_SAFE_BUILD_LENGTH, LDN = 256, 250, "[a-zA-Z0-9-]"
_SRC = {}


def _tok(name, value):
    _SRC[name] = value
    return value


_NUM = _tok("NUM", r"0|[1-9]\d*")
_NUML = _tok("NUML", r"\d+")
_NONNUM = _tok("NONNUM", rf"\d*[a-zA-Z-]{LDN}*")
_MAIN = _tok("MAIN", rf"({_NUM})\.({_NUM})\.({_NUM})")
_MAINL = _tok("MAINL", rf"({_NUML})\.({_NUML})\.({_NUML})")
_PRID = f"(?:{_NONNUM}|{_NUM})"
_PRIDL = f"(?:{_NONNUM}|{_NUML})"
_PRE = rf"(?:-({_PRID}(?:\.{_PRID})*))"
_PREL = rf"(?:-?({_PRIDL}(?:\.{_PRIDL})*))"
_BID = f"{LDN}+"
_BUILD = rf"(?:\+({_BID}(?:\.{_BID})*))"
_FULLPLAIN = f"v?{_MAIN}{_PRE}?{_BUILD}?"
_LOOSEPLAIN = rf"[v=\s]*{_MAINL}{_PREL}?{_BUILD}?"
_GTLT = r"((?:<|>)?=?)"
_XID = rf"{_NUM}|x|X|\*"
_XPLAIN = rf"[v=\s]*({_XID})(?:\.({_XID})(?:\.({_XID})(?:{_PRE})?{_BUILD}?)?)?"
_COERCEPLAIN = r"(^|[^\d])(\d{1,16})(?:\.(\d{1,16}))?(?:\.(\d{1,16}))?"


def _rx(value):
    """node-semver's safeRe: bounded quantifiers; JS `$` is Python `\\Z`."""
    for t, mx in ((r"\s", 1), (r"\d", MAX_LENGTH), (LDN, MAX_SAFE_BUILD_LENGTH)):
        value = value.replace(t + "*", f"{t}{{0,{mx}}}").replace(t + "+", f"{t}{{1,{mx}}}")
    return re.compile(value.replace("$", r"\Z"), re.ASCII)


RX = {
    "FULL": _rx(f"^{_FULLPLAIN}$"),
    "LOOSE": _rx(f"^{_LOOSEPLAIN}$"),
    "BUILD": _rx(_BUILD),
    "XRANGE": _rx(rf"^{_GTLT}\s*{_XPLAIN}$"),
    "COERCE": _rx(rf"{_COERCEPLAIN}(?:$|[^\d])"),
    "COERCEFULL": _rx(rf"{_COERCEPLAIN}(?:{_PRE})?(?:{_BUILD})?(?:$|[^\d])"),
    "TILDETRIM": _rx(r"(\s*)(?:~>?)\s+"),
    "TILDE": _rx(f"^(?:~>?){_XPLAIN}$"),
    "CARETTRIM": _rx(r"(\s*)(?:\^)\s+"),
    "CARET": _rx(rf"^(?:\^){_XPLAIN}$"),
    "COMPARATOR": _rx(rf"^{_GTLT}\s*({_FULLPLAIN})$|^$"),
    "COMPARATORTRIM": _rx(rf"(\s*){_GTLT}\s*({_LOOSEPLAIN}|{_XPLAIN})"),
    "HYPHENRANGE": _rx(rf"^\s*({_XPLAIN})\s+-\s+({_XPLAIN})\s*$"),
    "STAR": _rx(r"(<|>)?=?\s*\*"),
    "GTE0": _rx(r"^\s*>=\s*0\.0\.0\s*$"),
}
MAX_SAFE_INTEGER = 2 ** 53 - 1
_WS = re.compile(r"\s+", re.ASCII)


class SemVerError(ValueError):
    pass


def _cmp_id(a, b):
    if isinstance(a, int) and isinstance(b, int):
        return 0 if a == b else (-1 if a < b else 1)
    an, bn = re.fullmatch(r"[0-9]+", str(a)) is not None, re.fullmatch(r"[0-9]+", str(b)) is not None
    if an and bn:
        a, b = int(a), int(b)
    if a == b:
        return 0
    if an and not bn:
        return -1
    if bn and not an:
        return 1
    return -1 if str(a) < str(b) else 1


class SemVer:
    def __init__(self, version, loose=False):
        if not isinstance(version, str):
            raise SemVerError("Invalid version. Must be a string.")
        if len(version) > MAX_LENGTH:
            raise SemVerError("version is too long")
        m = RX["LOOSE" if loose else "FULL"].search(version.strip())
        if not m:
            raise SemVerError(f"Invalid Version: {version}")
        self.major, self.minor, self.patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if max(self.major, self.minor, self.patch) > MAX_SAFE_INTEGER:
            raise SemVerError("Invalid version number")
        self.prerelease = []
        if m.group(4):
            for i in m.group(4).split("."):
                self.prerelease.append(int(i) if re.fullmatch(r"[0-9]+", i) and int(i) < MAX_SAFE_INTEGER else i)
        self.version = f"{self.major}.{self.minor}.{self.patch}"
        if self.prerelease:
            self.version += "-" + ".".join(str(p) for p in self.prerelease)

    def compare(self, other):
        if not isinstance(other, SemVer):
            if other == self.version:
                return 0
            other = SemVer(other)
        if other.version == self.version:
            return 0
        a, b = (self.major, self.minor, self.patch), (other.major, other.minor, other.patch)
        if a != b:
            return -1 if a < b else 1
        if self.prerelease and not other.prerelease:
            return -1
        if not self.prerelease and other.prerelease:
            return 1
        if not self.prerelease and not other.prerelease:
            return 0
        i = 0
        while True:
            x = self.prerelease[i] if i < len(self.prerelease) else None
            y = other.prerelease[i] if i < len(other.prerelease) else None
            if x is None and y is None:
                return 0
            if y is None:
                return 1
            if x is None:
                return -1
            if not (x == y and type(x) is type(y)):
                return _cmp_id(x, y)
            i += 1


def _cmp(a, op, b):
    r = a.compare(b)
    return {"": r == 0, "=": r == 0, ">": r > 0, ">=": r >= 0, "<": r < 0, "<=": r <= 0}[op]


def parse(version, loose=False):
    try:
        return SemVer(version, loose)
    except SemVerError:
        return None


def coerce(version, include_prerelease=False, loose=False):
    m = RX["COERCEFULL" if include_prerelease else "COERCE"].search(version)
    if not m:
        return None
    s = f"{m.group(2)}.{m.group(3) or '0'}.{m.group(4) or '0'}"
    if include_prerelease:
        s += (f"-{m.group(5)}" if m.group(5) else "") + (f"+{m.group(6)}" if m.group(6) else "")
    return parse(s, loose)


ANY = object()


class Comparator:
    def __init__(self, comp):
        comp = " ".join(x for x in _WS.split(comp.strip()))
        m = RX["COMPARATOR"].search(comp)
        if not m:
            raise SemVerError(f"Invalid comparator: {comp}")
        self.operator = m.group(1) if m.group(1) is not None else ""
        if self.operator == "=":
            self.operator = ""
        self.semver = ANY if not m.group(2) else SemVer(m.group(2))
        self.value = "" if self.semver is ANY else self.operator + self.semver.version

    def test(self, version):
        if self.semver is ANY:
            return True
        return _cmp(version, self.operator, self.semver)

    def intersects(self, comp):
        if self.operator == "":
            if self.value == "":
                return True
            return _range(comp.value).test(self.value)
        if comp.operator == "":
            if comp.value == "":
                return True
            return _range(self.value).test(comp.semver)
        if self.value.startswith("<0.0.0") or comp.value.startswith("<0.0.0"):
            return False
        if self.operator.startswith(">") and comp.operator.startswith(">"):
            return True
        if self.operator.startswith("<") and comp.operator.startswith("<"):
            return True
        if self.semver.version == comp.semver.version and "=" in self.operator and "=" in comp.operator:
            return True
        if _cmp(self.semver, "<", comp.semver) and self.operator.startswith(">") and comp.operator.startswith("<"):
            return True
        if _cmp(self.semver, ">", comp.semver) and self.operator.startswith("<") and comp.operator.startswith(">"):
            return True
        return False


def _isx(i):
    return i is None or i == "" or i.lower() == "x" or i == "*"


def _hyphen(m):
    frm, fM, fm, fp, fpr = m.group(1), m.group(2), m.group(3), m.group(4), m.group(5)
    to, tM, tm, tp, tpr = m.group(7), m.group(8), m.group(9), m.group(10), m.group(11)
    if _isx(fM):
        frm = ""
    elif _isx(fm):
        frm = f">={fM}.0.0"
    elif _isx(fp):
        frm = f">={fM}.{fm}.0"
    else:
        frm = f">={frm}"
    if _isx(tM):
        to = ""
    elif _isx(tm):
        to = f"<{int(tM) + 1}.0.0-0"
    elif _isx(tp):
        to = f"<{tM}.{int(tm) + 1}.0-0"
    elif tpr:
        to = f"<={tM}.{tm}.{tp}-{tpr}"
    else:
        to = f"<={to}"
    return f"{frm} {to}".strip()


def _tilde(m):
    M, mi, p, pr = m.group(1), m.group(2), m.group(3), m.group(4)
    if _isx(M):
        return ""
    if _isx(mi):
        return f">={M}.0.0 <{int(M) + 1}.0.0-0"
    if _isx(p):
        return f">={M}.{mi}.0 <{M}.{int(mi) + 1}.0-0"
    if pr:
        return f">={M}.{mi}.{p}-{pr} <{M}.{int(mi) + 1}.0-0"
    return f">={M}.{mi}.{p} <{M}.{int(mi) + 1}.0-0"


def _caret(m):
    M, mi, p, pr = m.group(1), m.group(2), m.group(3), m.group(4)
    if _isx(M):
        return ""
    if _isx(mi):
        return f">={M}.0.0 <{int(M) + 1}.0.0-0"
    if _isx(p):
        if M == "0":
            return f">={M}.{mi}.0 <{M}.{int(mi) + 1}.0-0"
        return f">={M}.{mi}.0 <{int(M) + 1}.0.0-0"
    if pr:
        if M == "0":
            if mi == "0":
                return f">={M}.{mi}.{p}-{pr} <{M}.{mi}.{int(p) + 1}-0"
            return f">={M}.{mi}.{p}-{pr} <{M}.{int(mi) + 1}.0-0"
        return f">={M}.{mi}.{p}-{pr} <{int(M) + 1}.0.0-0"
    if M == "0":
        if mi == "0":
            return f">={M}.{mi}.{p} <{M}.{mi}.{int(p) + 1}-0"
        return f">={M}.{mi}.{p} <{M}.{int(mi) + 1}.0-0"
    return f">={M}.{mi}.{p} <{int(M) + 1}.0.0-0"


def _xrange(m):
    ret, gtlt, M, mi, p = m.group(0), m.group(1), m.group(2), m.group(3), m.group(4)
    xM = _isx(M)
    xm = xM or _isx(mi)
    xp = xm or _isx(p)
    if gtlt == "=" and xp:
        gtlt = ""
    pr = ""
    if xM:
        return "<0.0.0-0" if gtlt in (">", "<") else "*"
    if gtlt and xp:
        if xm:
            mi = 0
        p = 0
        if gtlt == ">":
            gtlt = ">="
            if xm:
                M, mi, p = int(M) + 1, 0, 0
            else:
                mi, p = int(mi) + 1, 0
        elif gtlt == "<=":
            gtlt = "<"
            if xm:
                M = int(M) + 1
            else:
                mi = int(mi) + 1
        if gtlt == "<":
            pr = "-0"
        return f"{gtlt}{M}.{mi}.{p}{pr}"
    if xm:
        return f">={M}.0.0{pr} <{int(M) + 1}.0.0-0"
    if xp:
        return f">={M}.{mi}.0{pr} <{M}.{int(mi) + 1}.0-0"
    return ret


def _each(comp, rx, fn):
    return " ".join(rx.sub(fn, c, count=1) for c in _WS.split(comp.strip()))


def _parse_comparator(comp):
    comp = RX["BUILD"].sub("", comp, count=1)
    comp = _each(comp, RX["CARET"], _caret)
    comp = _each(comp, RX["TILDE"], _tilde)
    comp = " ".join(RX["XRANGE"].sub(_xrange, c.strip(), count=1) for c in _WS.split(comp))
    return RX["STAR"].sub("", comp.strip(), count=1)


class Range:
    def __init__(self, rng):
        raw = _WS.sub(" ", rng.strip())
        sets = [s for s in (self._parse(r.strip()) for r in raw.split("||")) if s]
        if not sets:
            raise SemVerError(f"Invalid SemVer Range: {raw}")
        if len(sets) > 1:
            first = sets[0]
            sets = [c for c in sets if c[0].value != "<0.0.0-0"]
            if not sets:
                sets = [first]
            elif len(sets) > 1:
                for c in sets:
                    if len(c) == 1 and c[0].value == "":
                        sets = [c]
                        break
        self.set = sets

    @staticmethod
    def _parse(rng):
        rng = RX["HYPHENRANGE"].sub(_hyphen, rng, count=1)
        rng = RX["COMPARATORTRIM"].sub(r"\1\2\3", rng)
        rng = RX["TILDETRIM"].sub(r"\1~", rng)
        rng = RX["CARETTRIM"].sub(r"\1^", rng)
        lst = _WS.split(" ".join(_parse_comparator(c) for c in rng.split(" ")))
        lst = [RX["GTE0"].sub("", c.strip(), count=1) for c in lst]
        out = {}
        for c in (Comparator(x) for x in lst):
            if c.value == "<0.0.0-0":
                return [c]
            out[c.value] = c
        if len(out) > 1 and "" in out:
            del out[""]
        return list(out.values())

    @property
    def range(self):
        return "||".join(" ".join(c.value.strip() for c in s) for s in self.set)

    def test(self, version):
        if not version:
            return False
        if isinstance(version, str):
            version = _semver(version)
            if version is None:
                return False
        for s in self.set:
            if all(c.test(version) for c in s):
                if version.prerelease:
                    if not any(c.semver is not ANY and c.semver.prerelease and
                               (c.semver.major, c.semver.minor, c.semver.patch) ==
                               (version.major, version.minor, version.patch) for c in s):
                        continue
                return True
        return False

    def intersects(self, other):
        return any(_satisfiable(t) and any(_satisfiable(r) and all(a.intersects(b) for a in t for b in r)
                                           for r in other.set) for t in self.set)


def _satisfiable(comps):
    rest = list(comps)
    test = rest.pop()
    ok = True
    while ok and rest:
        ok = all(test.intersects(o) for o in rest)
        test = rest.pop()
    return ok


@functools.lru_cache(maxsize=4096)
def _range(r):
    return Range(r)


@functools.lru_cache(maxsize=4096)
def _semver(v):
    try:
        return SemVer(v)
    except SemVerError:
        return None


def valid_range(r):
    try:
        return _range(r).range or "*"
    except SemVerError:
        return None


def max_satisfying(versions, rng):
    try:
        r = _range(rng)
    except SemVerError:
        return None
    best = best_sv = None
    for v in versions:
        if r.test(v) and (best is None or best_sv.compare(v) == -1):
            best, best_sv = v, SemVer(v)
    return best


# ---------------------------------------------------------------- setup-beam v1.24.1 matching
# getOTPVersions (linux) + getVersionFromSpec and its helpers, src/setup-beam.js at v1.24.1.
KNOWN_BRANCHES = ("main", "master", "maint")
JS_OBJECT_KEYS = {"constructor", "__proto__", "hasOwnProperty", "isPrototypeOf", "propertyIsEnumerable",
                  "toLocaleString", "toString", "valueOf", "__defineGetter__", "__defineSetter__",
                  "__lookupGetter__", "__lookupSetter__"}


class ActionError(Exception):
    """The action itself throws (for example `otp-version: '*'`): fails on every image."""


def _xyz_abc(pref, suf):
    dd = r"\.?(\d+)?"
    return re.compile(rf"{pref}(?:OTP-)?v?(\d+){dd * 5}(?:-rc\.?\d+)?(?:-otp-\d+)?{suf}", re.ASCII)


_IS_RC, _IS_VERSION, _SORT = _xyz_abc("^", r"(?:-rc\.?\d+)"), _xyz_abc("^", r"\Z"), _xyz_abc("", "")


def is_rc(v):
    return _IS_RC.search(v) is not None


def _branchy(v):
    return v in KNOWN_BRANCHES or any(b in v for b in KNOWN_BRANCHES)


def remove_v(v):
    return v.replace("v", "", 1) if _IS_VERSION.search(v) else v


def remove_otp(v):
    return v[4:] if v.startswith("OTP-") else v


def maybe_coerced(v):
    if is_rc(v):
        return remove_v(v)
    c = coerce(v)
    return v if c is None else c.version


def _sort_key(v):
    m = _SORT.search(v)
    if m is None:
        raise ActionError(f"cannot sort {v!r}")
    return "".join((g or "0").rjust(3, "0") for g in m.groups()[:6])


def _sort_versions(a, b):
    ka, kb = _sort_key(a), _sort_key(b)
    return -1 if ka < kb else (1 if ka > kb else 0)


def _parse_version(v):
    if "rc" not in v:
        p = v.split(".")
        v = ".".join((p + ["", "", ""])[:3]) + "+" + ".".join(p[3:])
    return coerce(v, include_prerelease=True, loose=True)


def _gt(a, b):
    a, b = _parse_version(a), _parse_version(b)
    if a is None or b is None:
        raise ActionError("Invalid version")
    try:
        return SemVer(a.version).compare(SemVer(b.version)) > 0
    except SemVerError as e:
        raise ActionError(str(e))


def _valid_version(v):
    return re.search("main|master|maint|nightly|latest", v) is None and not v.startswith(("a", "b"))


def _js_key_order(keys):
    ints = sorted((k for k in keys if re.fullmatch(r"0|[1-9][0-9]*", k) and int(k) < 2 ** 32 - 1), key=int)
    return ints + [k for k in keys if k not in ints]


def parse_listing(text):
    """getOTPVersions, linux: {key without OTP-: original name} in JS object key order."""
    out = {}
    for line in text.strip().split("\n"):
        m = re.match(r"^([^ ]+)?( .+)", line)
        if not m or m.group(1) is None:
            raise ValueError(f"unexpected builds.txt line {line!r}")
        out[remove_otp(m.group(1))] = m.group(1)
    return {k: out[k] for k in _js_key_order(list(out))}


_PREPARED = {}


def _prepare(listing, strict):
    """The spec-independent half of getVersionFromSpec: versions0 with `latest`, altVersions."""
    key = (id(listing), strict)
    if key not in _PREPARED:
        try:
            versions0 = dict(listing)
            latest = None
            for v in list(versions0):
                if _valid_version(v):
                    latest = latest if latest and _gt(latest, v) else v
            versions0["latest"] = latest
            alt = {}
            for version, alt_version in versions0.items():
                coerced = remove_v(version) if strict or is_rc(version) or _branchy(version) else maybe_coerced(version)
                alt[coerced] = sorted(alt.get(coerced, []) + [alt_version], key=functools.cmp_to_key(_sort_versions))
            _PREPARED[key] = (listing, versions0, alt, _js_key_order(list(alt)))
        except ActionError as e:
            _PREPARED[key] = (listing, e)
    got = _PREPARED[key]
    if isinstance(got[1], ActionError):
        raise got[1]
    return got[1:]


def version_from_spec(spec0, listing, strict):
    """getVersionFromSpec: the listing entry setup-beam installs, or None (not found).
    Raises ActionError where the action throws, ValueError where this port is not exact."""
    if re.search(r"[^\x20-\x7e]", spec0) or re.search(r"\d{16}", spec0) or spec0 in JS_OBJECT_KEYS:
        raise ValueError(f"unsupported version syntax {spec0!r}")
    versions0, alt, keys = _prepare(listing, strict)
    spec = remove_v(spec0)
    range_max = max_satisfying(keys, valid_range(spec0) or maybe_coerced(spec))
    if spec0 == "latest":
        return versions0.get(versions0["latest"]) if versions0["latest"] is not None else None
    if strict or is_rc(spec0) or _branchy(spec0) or spec0 == "nightly":
        return versions0.get(spec) or None
    if range_max is None:
        return None
    that = valid_range(_version_abc(spec))
    for this in reversed(alt[range_max]):
        this_range = valid_range(_version_abc(this))
        if that and this_range is None:
            raise ActionError("Invalid SemVer Range")
        if that and _range(that).intersects(_range(this_range)):
            return this
    return None


def _version_abc(v):
    m = re.search(r"\d+(?:\.[^.]+)?(?:\.[^.]+)?(?:\.)?(.*)", v, re.ASCII)
    if m is None:
        raise ActionError("Cannot read properties of null")
    return m.group(1)


def resolve_otp(data, spec, strict, osv):
    """Version string setup-beam installs on hosted ubuntu-<osv>; None if not found; 'ERROR ...'."""
    try:
        return version_from_spec(remove_otp(spec), data.listing[osv], strict)
    except ActionError as e:
        return f"ERROR {e}"


# ---------------------------------------------------------------- data
class Data:
    def __init__(self, d, refresh, offline=False):
        self.dir, self.offline = d, offline
        os.makedirs(d, exist_ok=True)
        self.listing = {osv: parse_listing(self._get(f"otp-builds-ubuntu-{osv}.txt", BUILDS_URL.format(os=osv), refresh))
                        for osv in OSES}
        self.refs = {}
        for line in SETUP_BEAM_REFS.strip().splitlines():
            name, sha, keys = line.split()
            self.refs[name] = self.refs[sha] = set() if keys == "-" else {"ubuntu" + k for k in keys.split(",")}
        self.ref_path = os.path.join(d, "setup-beam-refs.json")
        self.looked_up = {}
        if os.path.exists(self.ref_path):
            with open(self.ref_path) as f:
                self.looked_up = json.load(f)

    def _get(self, name, url, refresh):
        p = os.path.join(self.dir, name)
        if refresh or not os.path.exists(p):
            with urllib.request.urlopen(url, timeout=60) as r, open(p, "wb") as f:
                f.write(r.read())
        with open(p, encoding="utf-8") as f:
            return f.read()

    def ref_images(self, ref):
        """ImageOS keys the ref's dist/index.js maps, e.g. {'ubuntu24', 'ubuntu26'}; Unknown if unplaceable."""
        if ref in self.refs:
            return self.refs[ref]
        if re.fullmatch(r"[0-9a-f]{7,40}", ref):
            hits = {k for k in self.refs if len(k) == 40 and k.startswith(ref)}
            if len(hits) == 1:
                return self.refs[hits.pop()]
        if ref not in self.looked_up:
            if self.offline:
                raise Unknown(f"erlef/setup-beam@{ref} is not a release and --offline is set")
            try:
                url = REF_URL.format(ref=urllib.parse.quote(ref, safe=""))
                with urllib.request.urlopen(url, timeout=60) as r:
                    text = r.read().decode("utf-8", "replace")
                self.looked_up[ref] = sorted(set(re.findall(r"""^\s*['"]?(ubuntu\d\d)['"]?\s*:""", text, re.M)))
            except urllib.error.HTTPError as e:
                if e.code != 404:
                    raise Unknown(f"erlef/setup-beam@{ref}: HTTP {e.code}")
                self.looked_up[ref] = None
            except OSError:
                raise Unknown(f"erlef/setup-beam@{ref}: lookup failed (offline?)")
            with open(self.ref_path, "w") as f:
                json.dump(self.looked_up, f, indent=0, sort_keys=True)
        if self.looked_up[ref] is None:
            raise Unknown(f"erlef/setup-beam@{ref} not found")
        return set(self.looked_up[ref])


# ---------------------------------------------------------------- workflow reading
# Matrix, expression, runs-on and if: handling as in check2604.py (ubuntu-2604-setup-check).
class Unknown(Exception):
    pass


def js_str(v):
    """How the runner stringifies a YAML scalar input (3.10 -> '3.1', 3.0 -> '3')."""
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() else repr(v)
    return str(v)


EXPR = re.compile(r"\$\{\{\s*(.*?)\s*\}\}")


_SEG = re.compile(r"\.([A-Za-z0-9_-]+)|\[(\d+)\]|\[['\"]([^'\"]+)['\"]\]")


_PATH = re.compile(r"(matrix|env)((?:\.[A-Za-z0-9_-]+|\[\d+\]|\[['\"][^'\"]+['\"]\])+)")


def lookup(e, ctx):
    """Value of a matrix./env. path such as matrix.os.image or matrix.plat[0]; Unknown otherwise."""
    m = _PATH.fullmatch(e.strip())
    if not m:
        raise Unknown(f"expression ${{{{ {e} }}}}")
    v = ctx[m.group(1)]
    for seg in _SEG.finditer(m.group(2)):
        key, idx, qkey = seg.groups()
        if idx is not None:
            if not isinstance(v, list) or int(idx) >= len(v):
                raise Unknown(f"expression ${{{{ {e} }}}}")
            v = v[int(idx)]
        else:
            k = key if key is not None else qkey
            if isinstance(v, dict) and k not in v:  # property names are case-insensitive
                k = next((x for x in v if isinstance(x, str) and x.lower() == k.lower()), k)
            if not isinstance(v, dict) or k not in v:
                raise Unknown(f"expression ${{{{ {e} }}}}")
            v = v[k]
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
            try:
                v = lookup(p, ctx)
            except Unknown:
                if not p.startswith("matrix"):
                    raise
                v = None
        else:
            raise Unknown(f"expression ${{{{ {e} }}}}")
        if v is not None and v is not False and v != 0 and v != "":
            return v
    return "" if v is None else v


def substitute(val, ctx):
    """Replace ${{ matrix.x }} / ${{ env.X }} / ${{ a || 'b' }}; raise Unknown on anything else."""
    if isinstance(val, (list, dict)):
        raise Unknown("non-scalar input")
    s = js_str(val)

    def rep(m):
        v = fallback(m.group(1), ctx) if "||" in m.group(1) else lookup(m.group(1), ctx)
        if isinstance(v, (list, dict)):
            raise Unknown(f"non-scalar {m.group(1)}")
        return js_str(v)

    for _ in range(3):  # env values may themselves reference matrix values
        if not EXPR.search(s):
            return s
        s = EXPR.sub(rep, s)
    raise Unknown("nested expression")


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


def hosted_ubuntu_latest(runs_on):
    """True if runs-on selects the hosted ubuntu-latest label; Unknown if not static."""
    if isinstance(runs_on, dict):
        labels = runs_on.get("labels")
        if labels is None:
            return False  # runner group: larger/self-hosted runners
        runs_on = labels
    if isinstance(runs_on, list):
        if any(isinstance(x, str) and EXPR.search(x) for x in runs_on):
            raise Unknown("runs-on expression")
        return runs_on == ["ubuntu-latest"]
    if isinstance(runs_on, str):
        if EXPR.search(runs_on):
            raise Unknown("runs-on expression")
        return runs_on.strip() == "ubuntu-latest"
    return False


COND = re.compile(r"^\s*(matrix(?:\.[A-Za-z0-9_-]+|\[\d+\]|\['[^']+'\])+|runner\.os)\s*(==|!=)\s*'([^']*)'\s*$")


def step_runs(cond, ctx):
    """Evaluate simple `if:` conditions; True when unconditioned or not matrix/OS related."""
    if cond is None:
        return True
    c = js_str(cond).strip()
    c = EXPR.fullmatch(c).group(1) if EXPR.fullmatch(c) else c
    if "matrix." not in c and "runner.os" not in c:
        return True
    for p in re.split(r"\s*&&\s*", c):
        if "matrix." not in p and "runner.os" not in p:
            continue  # unrelated to the runner (event, branch, ...): assume it can run
        mm = COND.match(p.strip("() "))
        if not mm:
            raise Unknown(f"condition {c!r}")
        if mm.group(1) == "runner.os":
            left = "Linux"
        else:
            try:
                left = lookup(mm.group(1), ctx)
            except Unknown:
                left = None  # a missing matrix key compares as empty
        left = js_str(left) if left is not None else ""
        eq = left.lower() == mm.group(3).lower()  # expression string comparison ignores case
        if (mm.group(2) == "==") != eq:
            return False
    return True


def read_text(root, rel):
    """A file inside the checkout; None if missing or if it (or a symlink) leaves the checkout."""
    base = os.path.realpath(root)
    p = os.path.realpath(os.path.join(base, rel))
    if os.path.commonpath([base, p]) != base or not os.path.isfile(p):
        return None
    try:
        with open(p, encoding="utf-8", errors="replace") as f:
            return f.read(65536)
    except OSError:
        return None


# ---------------------------------------------------------------- setup-beam steps
def erlang_from_version_file(root, rel):
    """setup-beam parseVersionFile: erlang from .tool-versions (last line wins) or a .toml (mise)."""
    txt = read_text(root, rel)
    if txt is None:
        raise Unknown(f"version-file {rel} not in checkout")
    if rel.endswith(".toml"):
        try:
            v = (tomllib.loads(txt).get("tools") or {}).get("erlang")
        except Exception:
            raise Unknown(f"{rel} not parseable")
        v = v.get("version") if isinstance(v, dict) else v
        if v is not None and not isinstance(v, str):
            raise Unknown(f"{rel}: erlang version is not a string")
        return v
    found = None
    for line in re.split(r"\r?\n", txt):
        m = re.match(r"^([^ ]+)[ ]+(ref:v?)?([^ #]+)", line)
        if m and m.group(1) == "erlang":
            found = m.group(3)
    return found


def check_step(data, root, step, ctx):
    """[(status, spec, why)] for one setup-beam step, in the order the action fails."""
    uses = step.get("uses", "")
    ref = uses.split("@", 1)[1] if "@" in uses else ""
    if not ref:
        raise Unknown("no ref")
    w = step.get("with") or {}
    strict = substitute(w.get("version-type", "loose"), ctx).strip() == "strict"
    vf = substitute(w["version-file"], ctx).strip() if w.get("version-file") not in (None, "") else ""
    otp = substitute(w["otp-version"], ctx).strip() if w.get("otp-version") not in (None, "") else ""
    src = "otp-version"
    if vf:
        if not strict:
            return [("ALREADY", otp, "version-file needs version-type: strict")]
        from_file = erlang_from_version_file(root, vf)
        if otp and from_file:
            return [("ALREADY", otp, f"otp-version and {vf} both set")]
        if not otp:
            otp, src = from_file or "", vf
    if not otp:
        return [("ALREADY", "", "no otp-version")]
    images = data.ref_images(ref)
    pin = f"erlef/setup-beam@{ref}"
    if "ubuntu24" not in images:
        return [("ALREADY", otp, f"{pin} does not support the 24.04 image")]
    if otp == "false":
        if "ubuntu26" in images:
            return [("OK", otp, "otp-version false: no Erlang/OTP download")]
        raise Unknown(f"otp-version false with {pin}")
    try:
        r24, r26 = (resolve_otp(data, otp, strict, osv) for osv in OSES)
    except ValueError as e:
        raise Unknown(str(e))
    if r24 is None or r24.startswith("ERROR"):
        return [("ALREADY", otp, f"{src}: 24.04->{r24}")]
    causes = []
    if "ubuntu26" not in images:
        causes.append(f"{pin} does not know the 26.04 image (v1.24.1 or later does)")
    if r26 is None or r26.startswith("ERROR"):
        causes.append(f"{src}: 24.04->{r24} 26.04->None")
    if causes:
        return [("BREAK", otp, "; ".join(causes))]
    return [("OK", otp, f"{src}: 24.04->{r24} 26.04->{r26}")]


def check_workflow(data, root, path, doc):
    res = []
    if not isinstance(doc, dict) or not isinstance(doc.get("jobs"), dict):
        return res
    wenv = doc.get("env") if isinstance(doc.get("env"), dict) else {}
    for jid, job in doc["jobs"].items():
        if not isinstance(job, dict):
            continue
        steps = [s for s in (job.get("steps") or []) if isinstance(s, dict)]
        act = lambda s: s.get("uses", "").split("@")[0].lower()
        beam = [s for s in steps if act(s) in BEAM_ACTIONS]
        other = [s for s in steps if act(s) in OTHER_ACTIONS]
        if not beam and not other:
            continue
        name = "setup-beam" if beam else act(other[0])
        loc = f"{path}:{jid}"
        try:
            combos = expand_matrix(job.get("strategy"))
        except Unknown as u:
            res.append(("UNKNOWN", name, "", f"{loc}: {u}", False))
            continue
        jenv = job.get("env") if isinstance(job.get("env"), dict) else {}
        soft_job = job.get("continue-on-error")
        for combo in combos:
            ctx = {"matrix": combo, "env": {}}
            label = ",".join(f"{k}={js_str(v)}" for k, v in combo.items() if not isinstance(v, (dict, list)))
            where = f"{loc}[{label}]" if label else loc
            try:
                ro = job.get("runs-on")
                if isinstance(ro, str) and EXPR.search(ro):
                    ro = substitute(ro, ctx)
                elif isinstance(ro, list):
                    ro = [substitute(x, ctx) if isinstance(x, str) else x for x in ro]
                if not hosted_ubuntu_latest(ro):
                    continue
                if job.get("container"):
                    res.append(("NA", name, "", f"{where}: runs in a container", False))
                    continue
                if not step_runs(job.get("if"), ctx):
                    continue
                try:
                    soft = soft_job is True or (isinstance(soft_job, str) and substitute(soft_job, ctx) == "true")
                except Unknown:
                    soft = None  # continue-on-error not static: the setup result is still known
                ctx["env"] = {**wenv, **jenv}
                for s in other:
                    res.append(("UNKNOWN", act(s), "", f"{where}: {act(s)} is not checked", soft))
                for s in beam:
                    senv = s.get("env") if isinstance(s.get("env"), dict) else {}
                    sctx = {"matrix": combo, "env": {**ctx["env"], **senv}}
                    try:
                        if not step_runs(s.get("if"), sctx):
                            continue
                        if "ImageOS" in sctx["env"]:
                            res.append(("UNKNOWN", "setup-beam", "", f"{where}: ImageOS overridden", soft))
                            continue
                        for st, spec, why in check_step(data, root, s, sctx):
                            res.append((st, "setup-beam", spec, f"{where}: {why}", soft))
                    except Unknown as u:
                        res.append(("UNKNOWN", "setup-beam", "", f"{where}: {u}", soft))
            except Unknown as u:
                res.append(("UNKNOWN", name, "", f"{where}: {u}", False))
    return res


def check_repo(data, root):
    wfdir = os.path.join(root, ".github", "workflows")
    out = []
    if not os.path.isdir(wfdir):
        return out
    for name in sorted(os.listdir(wfdir)):
        if not name.endswith((".yml", ".yaml")):
            continue
        p = os.path.join(wfdir, name)
        if os.path.islink(p):
            continue
        try:
            with open(p, encoding="utf-8", errors="replace") as f:
                doc = yaml.safe_load(f)
        except Exception as e:
            out.append(("UNKNOWN", "", "", f".github/workflows/{name}: YAML error {type(e).__name__}", False))
            continue
        out += check_workflow(data, root, f".github/workflows/{name}", doc)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("repos", nargs="+")
    ap.add_argument("--data", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "data"))
    ap.add_argument("--refresh", action="store_true", help="re-download the builds.txt lists")
    ap.add_argument("--offline", action="store_true", help="never look up setup-beam refs (UNKNOWN instead)")
    ap.add_argument("--json", action="store_true", help="one JSON object per repo")
    a = ap.parse_args(argv)
    data = Data(a.data, a.refresh, a.offline)
    worst = 0
    for r in a.repos:
        res = check_repo(data, r)
        if a.json:
            print(json.dumps({"repo": r, "findings": [dict(zip(("status", "action", "spec", "where", "continueOnError"), x)) for x in res]}))
        else:
            for st, act, spec, where, soft in res:
                if st != "NA":
                    print(f"{st:8} {act or '-':13} {spec or '-':10} {where}{' (continue-on-error)' if soft else ''}")
        if any(x[0] == "BREAK" for x in res):
            worst = 1
    return worst


if __name__ == "__main__":
    sys.exit(main())
