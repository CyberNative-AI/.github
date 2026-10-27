#!/usr/bin/env python3
"""tzscan: find the copies of the IANA time-zone database that it recognises
inside a container image or directory tree, without running anything from it,
and say whether each copy is still wrong for Canada's 1 November 2026 change
(and Morocco's September 2026 change).

usage:
  tzscan.py IMAGE [IMAGE ...]        # needs docker; uses `docker create` + `docker export`
  tzscan.py --tar rootfs.tar         # a `docker export` / `podman export` tar (or - for stdin)
  tzscan.py --dir /path/to/rootfs    # an unpacked root filesystem or any directory
  add --json for machine-readable output

Exit status: 0 every copy found was verified current; 1 a copy used by default
for local time is stale; 2 nothing found, a read error, or a copy that could not
be judged; 3 only library/program copies are stale. Any incomplete scan (a
limit reached, a damaged archive, a read or export failure, a target with no
judged copy) exits 2; stale copies it did find are still listed.

Python 3.9+ standard library only. Nothing inside the image is executed.
"""
import argparse
import bz2
import contextlib
import datetime as dt
import gzip
import hashlib
import io
import json
import lzma
import os
import re
import signal
import stat
import struct
import subprocess
import sys
import tarfile
import tempfile
import zipfile
import zlib
if sys.version_info < (3, 9):  # before "import zoneinfo": an ImportError here would exit 1 ("stale")
    sys.stderr.write("tzscan: needs Python 3.9 or newer; this is %d.%d\n" % sys.version_info[:2])
    sys.exit(2)
import zoneinfo
try:
    from compression import zstd  # Python 3.14+
except ImportError:
    zstd = None

UTC = dt.timezone.utc
PROBE = dt.datetime(2026, 12, 15, 12, tzinfo=UTC)

# zone -> (correct UTC offset in hours on 2026-12-15, release that brought it)
ZONES = {
    "America/Vancouver": (-7, "2026b"),
    "America/Edmonton": (-6, "2026c"),
    "Africa/Casablanca": (0, "2026c"),
    "America/Inuvik": (-6, "2026d"),
    "America/Winnipeg": (-5, "2026e"),
}
# Other names for the same rules, so a tree that only has the alias still counts.
ALIASES = {
    "Canada/Pacific": "America/Vancouver",
    "Canada/Mountain": "America/Edmonton",
    "America/Yellowknife": "America/Edmonton",
    "Canada/Central": "America/Winnipeg",
    "America/Rainy_River": "America/Winnipeg",
}
NAMES = {**{z: z for z in ZONES}, **ALIASES}
RELEASE_ORDER = ["2026b", "2026c", "2026d", "2026e"]

# Fingerprints identify zones in copies that carry no zone names (PHP/MongoDB
# timelib, raw TZif blobs): UTC offsets sampled 1970-01..2026-06, before any of
# these changes, so every tz release since 2018 agrees. Unique per zone in a
# full 2026c tree apart from true aliases (Yellowknife, Rainy_River).
SAMPLES = [dt.datetime(y, m, d, 12, tzinfo=UTC)
           for y in range(1970, 2027) for m in range(1, 13) for d in (1, 8, 15, 22)
           if (y, m) <= (2026, 6)]
FINGERPRINTS = {
    "c20a52820807437e": "America/Vancouver",
    "4da3bea528ce20fa": "America/Edmonton",
    "fcdad103826d4d6f": "America/Inuvik",
    "dcdf94f7f6c00c06": "America/Winnipeg",
    "60bf0be0c017ce5c": "Africa/Casablanca",
}

# chrono-tz crate version -> bundled tz release (read from each crate's tz/NEWS)
CHRONO_TZ = {"0.10.4": "2025b"}

USE = {
    "zoneinfo": "read by glibc/musl, Go (before its own copy), Python zoneinfo, .NET, Ruby tzinfo, PHP built with system tzdata",
    "go-embedded": "used by this Go program only when no zoneinfo directory is found ($ZONEINFO, /usr/share/zoneinfo, ...)",
    "jdk-tzdb": "used by java.time and java.util.TimeZone in this JDK",
    "threetenbp": "used only by code that calls org.threeten.bp time zones",
    "joda": "used by Joda-Time (org.joda.time.DateTimeZone)",
    "timelib": "PHP date functions / MongoDB date operators, unless PECL timezonedb (PHP) or --timeZoneInfo (mongod) overrides it",
    "icu": "used by ICU users (Node.js Intl and Date local time, DuckDB ICU, ...)",
    "tzif-blobs": "time-zone files compiled into this binary",
    "chrono-tz": "Rust chrono-tz compiled into this binary (version read from build paths)",
    "pkg-version": "library's own copy (version label only)",
}

# Containers tzscan creates carry this label, so a leftover from a killed run can be found.
LABEL = "io.github.cybernative-ai.tzscan"

KiB, MiB, GiB = 1 << 10, 1 << 20, 1 << 30
# Reaching a limit makes the scan incomplete (exit 2); it is never a quiet skip.
LIMITS = {
    "member_bytes": 4 * GiB,          # largest file or archive entry examined
    "decompressed_bytes": 64 * GiB,   # bytes read out of archives after decompression (the image tar too), per target
    "members": 5_000_000,             # files plus entries listed in archives, per target
    "zip_directory_bytes": 64 * MiB,  # central directories open at once: an archive and the ones enclosing it
                                      # (read into memory; a 64 MiB one peaks near 660 MB RSS)
    "retained_bytes": 256 * MiB,      # zone files, names, labels, ICU tables and reports kept until the end, per target
    "reports": 10_000,                # copies and problems reported, per target
    "scanned_bytes": 64 * GiB,        # binary bytes searched for embedded copies, per target
    "records": 200_000,               # embedded zone files and ICU tables parsed, per target
    "jar_depth": 3,                   # archives inside archives
}
PER_TARGET = ("decompressed_bytes", "members", "retained_bytes", "scanned_bytes", "records", "reports")
RECORD_MAX = 128 * KiB        # one zone file; real ones are under 10 KiB
ENTRY_COST, REPORT_COST = 128, 2 * KiB  # memory counted for each kept name or label, and each report, besides its text
ICU_TABLE_MAX = 4 * MiB       # one zoneinfo64 table; real ones are about 150 KiB
TAR_HEADER_MAX = 1 * MiB      # the header data (long names, pax, sparse maps) of one tar entry
XZ_MEMORY = 128 * MiB         # decoder memory for an xz-compressed tar; xz -9 needs 65 MiB
CHUNK, LOOKAHEAD = 8 * MiB, 1 * MiB   # binaries are read in chunks; a record must fit in the look-ahead
SPOOL = 64 * MiB              # archives larger than this are copied to a temporary file, not memory
BINARY_EXT = (".dat", ".res", ".so", ".node", ".duckdb_extension", ".exe", ".dll")


class Incomplete(Exception):
    """One file or archive could not be examined completely."""
    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


class Exhausted(Incomplete):
    """A per-target limit was reached; the rest of the target is not examined."""


def off_hours(z, t=PROBE):
    return t.astimezone(z).utcoffset().total_seconds() / 3600


def load_tzif(data):
    try:
        return zoneinfo.ZoneInfo.from_file(io.BytesIO(data))
    except Exception:
        return None


def fingerprint(z):
    return hashlib.sha256(repr([s.astimezone(z).utcoffset().total_seconds()
                                for s in SAMPLES]).encode()).hexdigest()[:16]


def judge_offsets(offsets):
    """offsets: zone -> hours or None. Returns (release, wrong_zones, unknown_zones)."""
    wrong, unknown = [], []
    for zone, (good, _) in ZONES.items():
        o = offsets.get(zone)
        if o is None:
            unknown.append(zone)
        elif o != good:
            wrong.append(zone)
    # oldest release consistent with what is right
    rel = "<2026b"
    for r in RELEASE_ORDER:
        need = [z for z, (_, zr) in ZONES.items() if RELEASE_ORDER.index(zr) <= RELEASE_ORDER.index(r)]
        if all(offsets.get(z) is not None and offsets[z] == ZONES[z][0] for z in need):
            rel = ">=2026e" if r == "2026e" else r
    if unknown and not wrong:
        rel = "UNKNOWN"
    return rel, wrong, unknown


def release_of_label(label):
    """'2026c', '2026.3', '2026cgtz', '1.2026.5' -> '2026c' (or None)."""
    m = re.search(r"(20\d\d)([a-z])", label)
    if m:
        return m.group(1) + m.group(2)
    m = re.search(r"(20\d\d)\.(\d+)$", label)
    if m and 1 <= int(m.group(2)) <= 26:
        return m.group(1) + "abcdefghijklmnopqrstuvwxyz"[int(m.group(2)) - 1]
    return None


def judge_release(rel):
    """For copies known only by version label."""
    if rel is None:
        return "UNKNOWN", [], list(ZONES)
    wrong = [z for z, (_, zr) in ZONES.items() if rel < zr]
    return (">=2026e" if rel >= "2026e" else rel), wrong, []


def _joda_reader(data):
    pos = [0]

    def u8():
        pos[0] += 1
        return data[pos[0] - 1]

    def s8():
        v = u8()
        return v - 256 if v > 127 else v

    def u16():
        return (u8() << 8) | u8()

    def s32():
        v = (u16() << 16) | u16()
        return v - (1 << 32) if v >= 1 << 31 else v

    def utf():
        n = u16()
        pos[0] += n
        return data[pos[0] - n:pos[0]].decode("utf-8", "replace")

    def millis():
        # org.joda.time.tz.DateTimeZoneBuilder.readMillis
        v = u8()
        form = v >> 6
        if form == 0:
            v &= 0x3F
            return (v - 64 if v >= 32 else v) * 1800000
        if form == 1:
            v &= 0x3F
            v = (v - 64 if v >= 32 else v) << 24
            return (v | (u8() << 16) | (u8() << 8) | u8()) * 60000
        if form == 2:
            v &= 0x3F
            w = (v - 64 if v >= 32 else v) << 32
            return (w | (u8() << 24) | (u8() << 16) | (u8() << 8) | u8()) * 1000
        w = 0
        for _ in range(8):
            w = (w << 8) | u8()
        return w - (1 << 64) if w >= 1 << 63 else w

    return u8, s8, u16, s32, utf, millis


def _joda_ofyear_instant(oy, year, std, save):
    mode, month, dom, dow, advance, mod = oy
    off = std + save if mode == "w" else (std if mode == "s" else 0)
    if dom >= 0:
        d = dt.date(year, month, dom)
    else:
        first_next = dt.date(year + (month == 12), month % 12 + 1, 1)
        d = first_next + dt.timedelta(days=dom)
    if dow:
        add = dow - d.isoweekday()
        if add:
            if advance and add < 0:
                add += 7
            elif not advance and add > 0:
                add -= 7
            d += dt.timedelta(days=add)
    epoch_ms = (d - dt.date(1970, 1, 1)).days * 86400000 + mod
    return epoch_ms - off


def joda_offset_hours(data, when=PROBE):
    """Offset of a compiled Joda-Time zone file (org/joda/time/tz/data/<zone>) at `when`."""
    u8, s8, u16, s32, utf, millis = _joda_reader(data)
    t = int(when.timestamp() * 1000)
    kind = chr(u8())
    if kind == "F":
        utf()
        return millis() / 3600000
    if kind not in "CP":
        raise ValueError("not a Joda zone")
    pool = [utf() for _ in range(u16())]
    size = s32()
    trans = []
    for _ in range(size):
        tr, wall, std = millis(), millis(), millis()
        (u8() if len(pool) < 256 else u16())
        trans.append((tr, wall, std))
    tail = None
    if u8():
        std = millis()
        recs = []
        for _ in range(2):
            oy = (chr(u8()), u8(), s8(), u8(), bool(u8()), millis())
            utf()
            recs.append((oy, millis()))
        tail = (std, recs)
    if trans and (t < trans[-1][0] or tail is None):
        wall = trans[0][1]
        for tr, w, _ in trans:
            if tr <= t:
                wall = w
        return wall / 3600000
    std, ((s_oy, s_save), (e_oy, e_save)) = tail
    y = when.year
    start = _joda_ofyear_instant(s_oy, y, std, e_save)
    end = _joda_ofyear_instant(e_oy, y, std, s_save)
    in_dst = (start <= t < end) if start < end else (t >= start or t < end)
    return (std + (s_save if in_dst else e_save)) / 3600000


class Scan:
    def __init__(self, target):
        self.target = target
        self.copies = []
        self.blobs = {}     # sha256 -> bytes of a small TZif file
        self.tzif = {}      # path -> sha256
        self.links = {}     # path -> (kind, target path)
        self.labels = {}    # path of tzdata.zi / +VERSION -> release
        self.problems = []
        self.used = dict.fromkeys(PER_TARGET, 0)
        self.full = False   # the report budget is spent; one final problem says so
        self.cleanup_error = None
        self.status = None
        self.open_cd = 0    # central directory bytes of the archives open now (nested jars)
        self.zoneinfo_env = None    # ZONEINFO as an absolute path inside the target, unnormalized; Go reads it first
        self.zoneinfo_zip = False   # Go opens it as a zip (the value ends in .zip), else as a directory
        self.zoneinfo_files = set() # with a zip ZONEINFO: every regular file, so an unread target is not taken as absent
        self.go_zips = {}           # path -> (zones, reasons) as Go reads that zip, or None when not read
        self.zoneinfo_named = set() # copy paths Go reads through ZONEINFO
        self.zoneinfo_full = False  # Go loads every measured zone there, so the copies after it are fallbacks
        self.zoneinfo_note = None

    def set_zoneinfo(self, z):
        """z: (absolute path, opened as a zip) from zoneinfo_path, or None when unset."""
        if z:
            self.zoneinfo_env, self.zoneinfo_zip = z

    # ---- reporting helpers -------------------------------------------------
    def room(self, record):
        """Count one report against the reports and retained_bytes limits before it is kept.
        The first refusal records one final problem (not counted) and stops the target."""
        if self.full:
            return False
        cost = REPORT_COST + len(repr(record))
        over = ("reports" if self.used["reports"] >= LIMITS["reports"] else
                "retained_bytes" if self.used["retained_bytes"] + cost > LIMITS["retained_bytes"] else None)
        if over:
            self.full = True
            self.problems.append({"kind": "limit", "path": self.target, "message":
                                  f"{over} limit ({LIMITS[over]}) reached; later copies and problems were not "
                                  f"recorded and the rest of this target was not examined"})
            return False
        self.used["reports"] += 1
        self.used["retained_bytes"] += cost
        return True

    def report(self, record):
        """Keep a copy record; returns it, or None when the report budget is spent."""
        if self.room(record):
            self.copies.append(record)
            return record
        return None

    def add(self, kind, path, how, rel, wrong, unknown, detail=None):
        return self.report({
            "kind": kind, "path": path, "how": how, "release": rel,
            "verdict": "STALE" if wrong else ("UNKNOWN" if unknown else "OK"),
            "wrong": wrong, "unknown": unknown, "use": USE[kind], "detail": detail or {},
        })

    def problem(self, kind, path, message):
        record = {"kind": kind, "path": path, "message": message}
        if self.room(record):
            self.problems.append(record)

    def spend(self, what, n):
        """Count work against a per-target limit before doing it."""
        if self.full:
            raise Exhausted("limit", "report budget spent; the rest of this target was not examined")
        self.used[what] += n
        if self.used[what] > LIMITS[what]:
            raise Exhausted("limit", f"{what} limit ({LIMITS[what]}) reached; the rest of this target was not examined")

    def keep_tzif(self, path, data):
        key = hashlib.sha256(data).hexdigest()
        if key not in self.blobs:
            self.spend("retained_bytes", ENTRY_COST + len(data))
            self.blobs[key] = data
        self.spend("retained_bytes", ENTRY_COST + len(path))
        self.tzif[path] = key

    def keep_link(self, path, kind, target):
        self.spend("retained_bytes", ENTRY_COST + len(path) + len(target))
        self.links[path] = (kind, target)

    @staticmethod
    def is_zone(path):
        return any(path == n or path.endswith("/" + n) for n in NAMES)

    # ---- per-entry dispatch ------------------------------------------------
    def entry(self, path, f, size, seekable):
        """f: a binary file object at the start of the file's data; size: its length.
        seekable: f is a real file that zipfile may seek in."""
        base = os.path.basename(path)
        if self.zoneinfo_zip:
            self.spend("retained_bytes", ENTRY_COST + len(path))
            self.zoneinfo_files.add(path)
            if base == os.path.basename(self.zoneinfo_env):  # also under a linked parent or through ..
                if size > SPOOL:
                    self.go_zips[path] = None
                else:
                    self.spend("scanned_bytes", size)
                    data = f.read(size)
                    zones, why = self.go_zip(data)
                    self.spend("retained_bytes", ENTRY_COST + sum(map(len, zones.values())))
                    self.go_zips[path] = (zones, why)
                    f, seekable = io.BytesIO(data), True
        low = base.lower()
        named = (base in ("tzdb.dat", "TZDB.dat", "zoneinfo64.res", "zoneinfo.zip", "dateutil-zoneinfo.tar.gz")
                 or low.endswith((".jar", ".war", ".ear") + BINARY_EXT) or ".so." in low)
        if size > LIMITS["member_bytes"]:
            if named or f.read(4) in (b"\x7fELF", b"TZif"):
                raise Incomplete("limit", f"{size} bytes, over the member_bytes limit ({LIMITS['member_bytes']}); not examined")
            return
        if path.endswith(("zoneinfo/tzdata.zi", "zoneinfo/+VERSION")):
            m = re.search(r"(20\d\d[a-z])", f.read(200).decode("latin1"))
            if m:
                self.spend("retained_bytes", ENTRY_COST + len(path))
                self.labels[path] = m.group(1)
            return
        if base in ("tzdb.dat", "TZDB.dat"):
            self.tzdb(path, f.read(4096), "jdk-tzdb")
        elif base == "zoneinfo64.res":
            self.binary(path, f, b"", icu_file=True)
        elif base == "zoneinfo.zip":
            with self.open_zip(path, f, size, seekable) as z:
                self.zipfile_tree(path, z)
        elif low.endswith((".jar", ".war", ".ear")):
            with self.open_zip(path, f, size, seekable) as z:
                self.jar(path, z, 0)
        elif base == "dateutil-zoneinfo.tar.gz":
            self.tarball_tree(path, f)
        elif path.endswith("tzinfo/data/version.rb"):
            m = re.search(rb"TZDATA\s*=\s*'([^']+)'", f.read(64 * KiB))
            self.label(path, "tzinfo-data (Ruby)", m and m.group(1).decode())
        elif path.endswith("tzdata/__init__.py"):
            m = re.search(rb'IANA_VERSION\s*=\s*"([^"]+)"', f.read(64 * KiB))
            if m:
                self.label(path, "tzdata (Python)", m.group(1).decode(), note="zone files beside it are measured separately")
        elif path.endswith("moment-timezone/data/packed/latest.json"):
            m = re.search(rb'"version"\s*:\s*"([^"]+)"', f.read(200))
            self.label(path, "moment-timezone", m and m.group(1).decode())
        else:
            head = f.read(4)
            if head == b"TZif" and size <= RECORD_MAX:
                data = head + f.read(size - 4)
                self.keep_tzif(path, data)
                if named:  # e.g. a small .dat of concatenated zone files
                    self.binary(path, io.BytesIO(data[4:]), head)
            elif head == b"\x7fELF" or named:
                self.binary(path, f, head)
            elif head == b"TZif" and self.is_zone(path):
                raise Incomplete("limit", f"zone file of {size} bytes, over the {RECORD_MAX}-byte zone file bound; not read")

    # ---- archives ----------------------------------------------------------
    @contextlib.contextmanager
    def open_zip(self, path, f, size, seekable):
        """A ZipFile over f, or over a copy when f is a stream. The central directory
        size, with those of the enclosing archives still open, is checked before
        zipfile reads it."""
        spool = None
        if not seekable:
            spool = io.BytesIO() if size <= SPOOL else tempfile.TemporaryFile()
            left = size
            while left:
                b = f.read(min(left, MiB))
                if not b:
                    raise Incomplete("read-error", "archive data ended early")
                spool.write(b)
                left -= len(b)
            f = spool
        try:
            cd = zip_directory_size(f, size)
            if self.open_cd + cd > LIMITS["zip_directory_bytes"]:
                outer = f" (enclosing archives' directories hold {self.open_cd} more)" if self.open_cd else ""
                raise Incomplete("limit", f"central directory of {cd} bytes{outer}, over the zip_directory_bytes limit "
                                          f"({LIMITS['zip_directory_bytes']}); not examined")
            try:
                z = zipfile.ZipFile(f)
            except (zipfile.BadZipFile, ValueError, EOFError, struct.error) as e:
                raise Incomplete("corrupt", f"damaged archive: {e}")
            self.open_cd += cd
            try:
                with z:
                    self.spend("members", len(z.infolist()))
                    yield z
            finally:
                self.open_cd -= cd
        finally:
            if spool:
                spool.close()

    def zread(self, z, name, cap):
        """Up to cap bytes of one archive entry; the inflated size counts against the limit first."""
        info = z.getinfo(name)
        n = min(info.file_size, cap)
        self.spend("decompressed_bytes", n)
        with z.open(info) as fh:
            return fh.read(n)

    def zipfile_tree(self, path, z):
        zones = {}
        for name in NAMES:
            try:
                info = z.getinfo(name)
            except KeyError:
                continue
            if info.file_size > RECORD_MAX:
                self.problem("limit", f"{path}!/{name}", f"zone file of {info.file_size} bytes, over the "
                                                         f"{RECORD_MAX}-byte zone file bound; not read")
                continue
            try:
                zones.setdefault(NAMES[name], self.zread(z, name, RECORD_MAX))
            except Exhausted:
                raise
            except Exception as e:
                self.problem("corrupt", f"{path}!/{name}", f"{type(e).__name__}: {e}")
        if zones:
            self.named(path, "zoneinfo", zones, "zoneinfo zip, zones measured")

    @staticmethod
    def go_zip(data):
        """(zone -> TZif bytes Go loads from this zip, reasons it loads none for some names)."""
        zones, why = {}, set()
        for name in NAMES:
            got = go_zip_read(data, name)
            if isinstance(got, bytes):
                if load_tzif(got):
                    zones.setdefault(NAMES[name], got)
                else:
                    why.add("its zone files are not ones Go can load")
            elif got:
                why.add(got)
        return zones, why

    def tarball_tree(self, path, f):
        zones = {}
        try:
            for t, m in tar_members(self, f):
                self.spend("members", 1)
                if not (m.isfile() and m.name in NAMES):
                    continue
                if m.size > RECORD_MAX:
                    self.problem("limit", f"{path}!/{m.name}", f"zone file of {m.size} bytes, over the "
                                                              f"{RECORD_MAX}-byte zone file bound; not read")
                else:
                    zones.setdefault(NAMES[m.name], t.extractfile(m).read())
        except Incomplete:
            raise
        except Exception as e:
            self.problem("corrupt", path, f"damaged tarball: {type(e).__name__}: {e}")
        if zones:
            self.named(path, "zoneinfo", zones, "zoneinfo tarball, zones measured")

    def jar(self, path, z, depth):
        names = set(z.namelist())
        if "org/joda/time/tz/data/ZoneInfoMap" in names:
            ver = None
            if "META-INF/MANIFEST.MF" in names:
                m = re.search(rb"Time-Zone-Database-Version:\s*(\S+)", self.zread(z, "META-INF/MANIFEST.MF", MiB))
                ver = m and m.group(1).decode()
            offsets = {}
            for zone in ZONES:
                try:
                    data = self.zread(z, "org/joda/time/tz/data/" + zone, RECORD_MAX + 1)
                    if len(data) > RECORD_MAX:
                        self.problem("limit", f"{path}!/org/joda/time/tz/data/{zone}",
                                     f"zone file over the {RECORD_MAX}-byte zone file bound; not read")
                    offsets[zone] = joda_offset_hours(data) if len(data) <= RECORD_MAX else None
                except Exhausted:
                    raise
                except Exception:
                    offsets[zone] = None
            rel, wrong, unknown = judge_offsets(offsets)
            self.add("joda", path, f"Joda-Time compiled zones measured (manifest says {ver or '?'})", rel, wrong, unknown,
                     {"label": ver, "offsetsDec15": offsets})
        for n in ("org/threeten/bp/TZDB.dat", "tzdb.dat", "lib/tzdb.dat"):
            if n in names:
                self.tzdb(f"{path}!/{n}", self.zread(z, n, 4096), "threetenbp" if "threeten" in n else "jdk-tzdb")
        nested = [n for n in z.namelist() if n.endswith((".jar", ".war"))]
        if nested and depth >= LIMITS["jar_depth"]:
            self.problem("limit", path, f"{len(nested)} archives nested more than {LIMITS['jar_depth']} levels deep "
                                        f"were not examined (jar_depth limit)")
            return
        for n in nested:
            inner = f"{path}!/{n}"
            try:
                info = z.getinfo(n)
                if info.file_size > LIMITS["member_bytes"]:
                    raise Incomplete("limit", f"{info.file_size} bytes, over the member_bytes limit; not examined")
                self.spend("decompressed_bytes", info.file_size)
                with z.open(info) as fh, self.open_zip(inner, fh, info.file_size, False) as zz:
                    self.jar(inner, zz, depth + 1)
            except Exhausted:
                raise
            except Incomplete as e:
                self.problem(e.kind, inner, str(e))
            except Exception as e:
                self.problem("corrupt", inner, f"{type(e).__name__}: {e}")

    # ---- detectors ---------------------------------------------------------
    def label(self, path, what, version, note=None):
        rel, wrong, unknown = judge_release(release_of_label(version or ""))
        self.add("pkg-version", path, f"{what} version label {version or '?'}", rel, wrong, unknown,
                 {"library": what, "label": version, **({"note": note} if note else {})})

    def tzdb(self, path, data, kind):
        # java.time TzdbZoneRulesProvider: byte 1, UTF "TZDB", short n, n x UTF version
        try:
            if data[0] != 1:
                raise ValueError
            ln = struct.unpack(">H", data[1:3])[0]
            if data[3:3 + ln] != b"TZDB":
                raise ValueError
            p = 3 + ln
            n = struct.unpack(">H", data[p:p + 2])[0]
            p += 2
            ln = struct.unpack(">H", data[p:p + 2])[0]
            ver = data[p + 2:p + 2 + ln].decode()
        except Exception:
            self.problem("corrupt", path, "not a TZDB file")
            return
        rel, wrong, unknown = judge_release(release_of_label(ver))
        self.add(kind, path, f"TZDB header version {ver}", rel, wrong, unknown, {"label": ver})

    ICU_VER = re.compile(rb"(?<=\x00\x00)(2\x000\x00[0-9]\x00[0-9]\x00[a-z]\x00)(?=\x00\x00)")

    def icu(self, path, pkgs, raw_versions, quiet):
        """pkgs: zoneinfo64.res tables listed in ICU common-data packages; raw_versions:
        version strings found anywhere in the file, used when there is no package."""
        if pkgs:
            for name, seg in pkgs:
                vers = {v.decode("utf-16le") for v in self.ICU_VER.findall(seg)}
                if len(vers) == 1:
                    v = vers.pop()
                    rel, wrong, unknown = judge_release(release_of_label(v))
                    self.add("icu", path, f"ICU package {name} TZVersion {v}", rel, wrong, unknown, {"label": v})
                else:
                    self.add("icu", path, f"ICU package {name}, version not determined", "UNKNOWN", [], list(ZONES))
            return
        vers = {v.decode("utf-16le") for v in raw_versions}
        if len(vers) == 1:
            v = vers.pop()
            rel, wrong, unknown = judge_release(release_of_label(v))
            self.add("icu", path, f"ICU zoneinfo64 TZVersion {v}", rel, wrong, unknown, {"label": v})
        elif vers or not quiet:
            self.add("icu", path, f"ICU zoneinfo64 present, version not determined ({sorted(vers)})",
                     "UNKNOWN", [], list(ZONES))

    def binary(self, path, f, head, icu_file=False):
        Embedded(self, path, head == b"\x7fELF", icu_file).run(f, head)

    def measure(self, zones):
        offsets = {}
        for zone in ZONES:
            z = load_tzif(zones[zone]) if zone in zones else None
            offsets[zone] = off_hours(z) if z else None
        return offsets

    def named(self, path, kind, zones, how):
        offsets = self.measure(zones)
        rel, wrong, unknown = judge_offsets(offsets)
        return self.add(kind, path, how, rel, wrong, unknown, {"offsetsDec15": offsets})

    def unnamed(self, path, kind, hits, how, extra=None):
        """hits: zone -> set of offsets measured in records identified as that zone."""
        offsets = {}
        for zone in ZONES:
            v = hits.get(zone)
            offsets[zone] = next(iter(v)) if v and len(v) == 1 else None
        rel, wrong, unknown = judge_offsets(offsets)
        self.add(kind, path, how + ", zones identified by history and measured", rel, wrong, unknown,
                 {"offsetsDec15": offsets, **(extra or {})})

    SYSTEM_TREES = ("usr/share/zoneinfo", "usr/lib/zoneinfo", "usr/share/lib/zoneinfo", "etc/zoneinfo")

    def classify(self):
        """Tier A: the copy a program in this image uses by default for local time.
        Tier B: a library's or program's own copy that matters only if that code is used."""
        # a system path that is a symlink to a tree elsewhere (e.g. /usr/share/zoneinfo -> ../lib/zoneinfo)
        for lp, (kind, tgt) in self.links.items():
            if lp in self.SYSTEM_TREES:
                dest = os.path.normpath(tgt.lstrip("/") if tgt.startswith("/") or kind == "hard"
                                        else os.path.join(os.path.dirname(lp), tgt))
                for c in self.copies:
                    if c["kind"] == "zoneinfo" and c["path"] == dest:
                        c.setdefault("linkedFrom", []).append(lp)
        system = lambda c: c["kind"] == "zoneinfo" and (c["path"] in self.SYSTEM_TREES or
                                                        any(l in self.SYSTEM_TREES for l in c.get("linkedFrom", [])))
        has_system = any(system(c) for c in self.copies)
        named = self.zoneinfo_named
        for c in self.copies:
            k, p = c["kind"], c["path"]
            if k == "zoneinfo":
                tier = "A" if system(c) or p in named else "B"
                if p in named:
                    c["use"] = (f"named by this image's ZONEINFO ({self.zoneinfo_env}): Go programs read it "
                                "before /usr/share/zoneinfo and before their own embedded copy")
                elif "pytz" in p:
                    c["use"] = "used by pytz"
                elif p.endswith("tzdata/zoneinfo"):
                    c["use"] = "Python tzdata package: used by zoneinfo only when the OS has no tz files"
                elif "postgresql" in p:
                    c["use"] = "PostgreSQL's own copy (servers built without --with-system-tzdata)"
                elif "dateutil" in p:
                    c["use"] = "used by dateutil.zoneinfo"
                elif p.endswith("zoneinfo.zip"):
                    c["use"] = "Go toolchain copy: used by Go programs only when no zoneinfo directory is found"
                elif tier == "B":
                    c["use"] = "a program's own copy at this path"
            elif k == "go-embedded":
                tier = "B" if has_system or self.zoneinfo_full else "A"
                c["use"] = USE[k] + (f"; this image's ZONEINFO names {self.zoneinfo_env}, so this copy is a fallback"
                                     if self.zoneinfo_full else "; this image has one, so this copy is a fallback" if has_system
                                     else "; this image has none, so this copy is the one used")
            elif k == "jdk-tzdb":
                tier = "B" if "!/" in p else "A"
            elif k == "icu":
                tier = "A" if (p.endswith("/node") or "libicudata" in p or p.endswith(".res") or p.endswith(".dat")) else "B"
            elif k in ("timelib", "tzif-blobs"):
                tier = "A"
            else:
                tier = "B"
            c["tier"] = tier

    # ---- after the walk: zoneinfo trees ------------------------------------
    def finish(self):
        def resolve(p, seen=0):
            while p in self.links and seen < 16:
                kind, tgt = self.links[p]
                p = os.path.normpath(os.path.join(os.path.dirname(p), tgt)) if kind == "sym" and not tgt.startswith("/") \
                    else os.path.normpath(tgt.lstrip("/") if kind == "sym" else tgt)
                seen += 1
            return self.blobs.get(self.tzif.get(p))
        roots = {}
        for p in list(self.tzif) + list(self.links):
            for name in NAMES:
                if p == name or p.endswith("/" + name):
                    root = p[: len(p) - len(name)].rstrip("/") or "."
                    data = resolve(p)
                    if data:
                        roots.setdefault(root, {}).setdefault(NAMES[name], data)
        seen = {}
        for root in sorted(roots, key=len):
            zones = roots[root]
            if os.path.basename(root) in ("posix", "right") and os.path.dirname(root) in roots:
                continue  # duplicate views of the parent tree
            key = hashlib.sha256(b"".join(zones.get(z, b"") for z in ZONES)).hexdigest()
            if key in seen:
                self.report(dict(seen[key], path=root, sameAs=seen[key]["path"]))
                continue
            c = self.named(root, "zoneinfo", zones, "zoneinfo directory, zones measured")
            if not c:
                continue
            seen[key] = c
            for f in ("tzdata.zi", "+VERSION", "version"):
                d = self.labels.get(f"{root}/{f}")
                if d:
                    c["detail"]["label"] = d
        for lp, (kind, tgt) in self.links.items():
            if os.path.basename(lp) in ("tzdb.dat", "TZDB.dat"):
                dest = os.path.normpath(tgt.lstrip("/") if tgt.startswith("/") or kind == "hard"
                                        else os.path.join(os.path.dirname(lp), tgt))
                for c in self.copies:
                    if c["path"] == dest:
                        c.setdefault("linkedFrom", []).append(lp)
        if self.zoneinfo_env:
            self.zoneinfo_source()
        self.classify()

    def physical(self, path):
        """The path, relative to the root, that opening absolute `path` in the target reaches. Links
        seen in the walk are followed where they occur, so `..` after a link climbs from its target,
        as the kernel does. None after 40 links (the kernel's ELOOP)."""
        todo, out, hops = path.split("/")[::-1], [], 0
        while todo:
            part = todo.pop()
            if part in ("", "."):
                continue
            if part == "..":
                out = out[:-1]
                continue
            link = self.links.get("/".join(out + [part]))
            if link is None:
                out.append(part)
                continue
            hops += 1
            if hops > 40:
                return None
            kind, tgt = link
            if kind == "hard" or tgt.startswith("/"):  # a tar hardlink names another member from the root
                out = []
            todo.extend(tgt.split("/")[::-1])
        return "/".join(out)

    def zoneinfo_source(self):
        """Find what Go's LoadLocation reads through ZONEINFO (time/zoneinfo.go): a value longer than
        4 characters ending in .zip is read as a zip, anything else as a directory of zone files.
        A zone Go cannot load there comes from the next source, so the copies after ZONEINFO are
        fallbacks only when every measured zone loads from it."""
        raw, zones, why = self.zoneinfo_env, {}, set()
        where = self.physical(raw)
        if where is None:
            self.problem("zoneinfo", raw, "ZONEINFO: too many levels of symbolic links; not established")
            return
        if self.zoneinfo_zip:
            if where in self.go_zips:
                if self.go_zips[where] is None:
                    self.problem("limit", raw, f"ZONEINFO names /{where}, over {SPOOL} bytes; not read as Go reads it")
                    return
                zones, why = self.go_zips[where]
            elif where in self.zoneinfo_files:
                self.problem("zoneinfo", raw, f"ZONEINFO names /{where}, which tzscan reads as a zip only under "
                                              f"the name {os.path.basename(raw)}; not established")
                return
            elif any(p.startswith(where + "/") for p in self.tzif):
                why.add("it is a directory, and Go opens a name ending in .zip as a zip file")
        else:
            for name in NAMES:
                p = self.physical(raw + "/" + name)
                if p is None:
                    self.problem("zoneinfo", raw + "/" + name, "ZONEINFO: too many levels of symbolic links; not established")
                    return
                data = self.blobs.get(self.tzif.get(p))
                if data and load_tzif(data):
                    zones.setdefault(NAMES[name], data)
        if not zones:
            self.zoneinfo_note = ("; ".join(sorted(why)) or "Go finds no zone files there") + \
                                 ", so Go programs use the copies below"
            return
        where = where or "."
        offsets = self.measure(zones)
        c = next((c for c in self.copies if c["kind"] == "zoneinfo" and c["path"] == where
                  and c["detail"].get("offsetsDec15") == offsets), None)
        c = c or self.named(where, "zoneinfo", zones, "named by ZONEINFO, zones read as Go reads them")
        if not c:
            return  # the report budget is spent, which is already a problem
        self.zoneinfo_named = {c["path"]} | ({c["sameAs"]} if c.get("sameAs") else set())
        self.zoneinfo_full = len(zones) == len(ZONES)
        if not self.zoneinfo_full:
            self.zoneinfo_note = (f"Go loads {len(zones)} of the {len(ZONES)} zones from /{where}; "
                                  "the others come from the copies below")

    def conclude(self):
        """Per-target exit status: incomplete first, then the published 1 / 2 / 3 / 0 order."""
        if not any(c["verdict"] in ("OK", "STALE") for c in self.copies):
            self.problem("nothing-judged", self.target, "no time-zone database copy found" if not self.copies
                         else "no copy could be judged")
        if self.problems:
            self.status = 2
        elif any(c["verdict"] == "STALE" and c.get("tier") == "A" for c in self.copies):
            self.status = 1
        elif any(c["verdict"] == "UNKNOWN" for c in self.copies):
            self.status = 2
        elif any(c["verdict"] == "STALE" for c in self.copies):
            self.status = 3
        else:
            self.status = 0


class Embedded:
    """Streams one binary through the embedded-copy detectors, holding at most
    CHUNK + LOOKAHEAD bytes of it. Records are parsed as they pass; only zone
    hits, version strings and zoneinfo64 tables are kept."""
    LABEL_RE = re.compile(rb"\x00(20[0-4]\d\.\d{1,2})\x00")
    CHRONO_RE = re.compile(rb"chrono-tz-(\d{1,9}\.\d{1,9}\.\d{1,9})")

    def __init__(self, scan, path, elf, icu_file):
        self.scan, self.path, self.elf, self.icu_file = scan, path, elf, icu_file
        self.php_n = self.tzif_n = 0
        self.php_hits, self.tzif_hits = {}, {}   # zone -> offsets
        self.zipzones = {}                        # zone name -> first stored zip entry body
        self.oversized = set()                    # zone names whose stored entry is over RECORD_MAX
        self.zoneinfo64 = False
        self.pkgs = []                            # [name, start, stop, bytes so far, position reached]
        self.vers, self.labels, self.chrono = set(), set(), set()
        self.after = {}                           # regex -> absolute end of its last match
        self.buf, self.base = bytearray(), 0

    def run(self, f, head):
        buf, base, done, eof = bytearray(head), 0, 0, False
        while True:
            while not eof and len(buf) - (done - base) < CHUNK + LOOKAHEAD:
                more = f.read(CHUNK)
                if not more:
                    eof = True
                    break
                self.scan.spend("scanned_bytes", len(more))
                self.capture(base + len(buf), more)
                buf += more
            limit = base + len(buf) - (0 if eof else LOOKAHEAD)
            if limit > done:
                self.buf, self.base = buf, base
                self.region(buf, done - base, limit - base)
                done = limit
            if eof:
                break
            cut = done - base - 64  # keep what a record header before `done` needs
            if cut > 0:
                del buf[:cut]
                base += cut
        self.buf = None
        self.finish()

    def matches(self, rx, lit, back, buf, s, e, span):
        """Matches of rx starting in buf[s:e], the same ones finditer would give. Each match
        starts `back` bytes after the literal lit, which bytes.find locates quickly;
        span covers the longest match."""
        pos = max(s, self.after.get(rx, 0) - self.base)
        stop, end = e - back + len(lit) - 1, min(len(buf), e + span)
        i = buf.find(lit, max(pos - back, 0), stop)
        while i >= 0:
            m = rx.match(buf, i + back, end)
            if m:
                self.after[rx] = self.base + m.end()
                yield m
                i = buf.find(lit, m.end() - back, stop)
            else:
                i = buf.find(lit, i + 1, stop)

    def region(self, buf, s, e):
        """Every record that starts in buf[s:e]; buf holds LOOKAHEAD bytes after e unless the file ended."""
        spend = self.scan.spend
        i = buf.find(b"PHP2", s, e + 3)
        while i >= 0:  # timelib: "PHP2" + 16 bytes + a TZif v2 body
            spend("records", 1)
            self.php_n += 1
            self.hit(self.php_hits, b"TZif2" + b"\0" * 15 + bytes(buf[i + 20:i + 20 + RECORD_MAX]))
            i = buf.find(b"PHP2", i + 4, e + 3)
        i = buf.find(b"TZif", s, e + 3)
        while i >= 0:
            spend("records", 1)
            self.tzif_n += 1
            self.hit(self.tzif_hits, bytes(buf[i:i + RECORD_MAX]))
            i = buf.find(b"TZif", i + 4, e + 3)
        for name in NAMES:  # stored zip entries named like our zones (Go time/tzdata, zoneinfo.zip)
            key = name.encode()
            i = buf.find(key, s, e + len(key) - 1)
            while i >= 0:
                h = i - 30
                if h >= 0 and buf[h:h + 4] == b"PK\x03\x04" and name not in self.zipzones:
                    method, = struct.unpack_from("<H", buf, h + 8)
                    csize, usize, nlen, xlen = struct.unpack_from("<IIHH", buf, h + 18)
                    at = i + nlen + xlen
                    if method == 0 and nlen == len(key) and buf[at:at + 4] == b"TZif":
                        spend("records", 1)
                        if usize > RECORD_MAX:
                            if name not in self.oversized:
                                self.oversized.add(name)
                                self.scan.problem("limit", f"{self.path}!/{name}", f"zone file of {usize} bytes, over "
                                                  f"the {RECORD_MAX}-byte zone file bound; not read")
                        else:
                            spend("retained_bytes", ENTRY_COST + usize)
                            self.zipzones[name] = bytes(buf[at:at + usize])
                i = buf.find(key, i + 1, e + len(key) - 1)
        if not self.zoneinfo64 and buf.find(b"zoneinfo64", s, e + 9) >= 0:
            self.zoneinfo64 = True
        i = buf.find(b"\xda\x27", s, e + 1)
        while i >= 0:  # ICU common-data package header: size, magic, ..., "CmnD"
            h = i - 2
            if h >= 0 and buf[h + 12:h + 16] == b"CmnD":
                self.toc(buf, h)
            i = buf.find(b"\xda\x27", i + 1, e + 1)
        for m in self.matches(Scan.ICU_VER, b"\x00\x002\x000\x00", 2, buf, s, e, 32):
            self.keep(self.vers, bytes(m.group(1)))
        for m in self.matches(self.LABEL_RE, b"\x0020", 0, buf, s, e, 16):
            self.keep(self.labels, bytes(m.group(1)))
        for m in self.matches(self.CHRONO_RE, b"chrono-tz-", 0, buf, s, e, 64):
            self.keep(self.chrono, bytes(m.group(1)))
        if len(self.vers) + len(self.labels) + len(self.chrono) > 10000:
            raise Incomplete("limit", "more than 10000 distinct version strings; not examined further")

    def keep(self, found, v):
        if v not in found:
            self.scan.spend("retained_bytes", ENTRY_COST + len(v))
            found.add(v)

    def hit(self, hits, blob):
        z = load_tzif(blob)
        if z is None:
            return
        try:
            zone = FINGERPRINTS.get(fingerprint(z))
        except Exception:
            return
        if zone:
            hits.setdefault(zone, set()).add(off_hours(z))

    def toc(self, buf, h):
        """zoneinfo64.res entries in a little-endian ICU 'CmnD' table of contents."""
        self.scan.spend("records", 1)
        try:
            toc = h + struct.unpack_from("<H", buf, h)[0]
            n = struct.unpack_from("<I", buf, toc)[0]
            if not 0 < n < 100000:
                return
            ents = [struct.unpack_from("<II", buf, toc + 4 + 8 * k) for k in range(n)]
        except struct.error:
            self.scan.problem("limit", self.path, "an ICU table of contents runs past the read-ahead window; not read")
            return
        for k, (no, do) in enumerate(ents):
            a = toc + no
            end = buf.find(b"\0", a, a + 256)
            name = bytes(buf[a:end]).decode("latin1") if end >= 0 else ""
            if name.endswith("/zoneinfo64.res"):
                start = self.base + toc + do
                stop = self.base + toc + ents[k + 1][1] if k + 1 < n else start + 400000
                self.want(name, start, max(start, stop))

    def want(self, name, start, stop):
        """Collect bytes [start, stop) of the file as they stream past."""
        if stop - start > ICU_TABLE_MAX:
            self.scan.problem("limit", self.path, f"ICU table {name} is {stop - start} bytes, over {ICU_TABLE_MAX}; not read")
            stop = start
        self.scan.spend("retained_bytes", stop - start)
        end = self.base + len(self.buf)
        a, b = max(start, self.base), min(stop, end)
        seg = bytearray(self.buf[a - self.base:b - self.base]) if b > a else bytearray()
        self.pkgs.append([name, start, stop, seg, max(b, start)])

    def capture(self, at, more):
        for p in self.pkgs:
            _, _, stop, seg, got = p
            a, b = max(got, at), min(stop, at + len(more))
            if b > a:
                seg += more[a - at:b - at]
                p[4] = b

    def finish(self):
        scan, path = self.scan, self.path
        found = False
        if self.php_n >= 50:
            labels = sorted(v.decode() for v in self.labels)
            scan.unnamed(path, "timelib", self.php_hits, f"{self.php_n} timelib records", {"labelsSeen": labels})
            found = True
        zones = {}
        for name in NAMES:
            if name in self.zipzones:
                zones.setdefault(NAMES[name], self.zipzones[name])
        if zones:
            scan.named(path, "go-embedded" if self.elf else "zoneinfo", zones, "embedded zoneinfo zip, zones measured")
            found = True
        if not found and self.tzif_n >= 50:
            scan.unnamed(path, "tzif-blobs", self.tzif_hits, f"{self.tzif_n} embedded TZif files")
        if self.zoneinfo64 or self.icu_file:
            scan.icu(path, [(p[0], bytes(p[3])) for p in self.pkgs], self.vers, quiet=not self.icu_file)
        for v in sorted(v.decode() for v in self.chrono):
            rel = CHRONO_TZ.get(v)
            older = tuple(map(int, v.split("."))) <= (0, 10, 4)
            r, wrong, unknown = judge_release(rel or ("2025b" if older else None))
            if older and not rel:
                r = "<=2025b"
            scan.add("chrono-tz", path, f"chrono-tz {v} ({rel or ('older than 0.10.4, so 2025b or older' if older else 'data release not mapped')})",
                     r, wrong, unknown, {"crate": v})


def zip_directory_size(f, size):
    """Central directory size from the end records, before zipfile allocates it."""
    tail = min(size, 65536 + 22)
    f.seek(size - tail)
    buf = f.read(tail)
    i = buf.rfind(b"PK\x05\x06")
    if i < 0 or len(buf) - i < 22:
        raise Incomplete("corrupt", "damaged archive: no end of central directory")
    entries, cd = struct.unpack_from("<HI", buf, i + 10)
    if entries == 0xFFFF or cd == 0xFFFFFFFF:  # zip64: the locator sits just before
        if i < 20 or buf[i - 20:i - 16] != b"PK\x06\x07":
            raise Incomplete("corrupt", "damaged archive: zip64 locator missing")
        f.seek(size - tail + i - 20 - 56)
        rec = f.read(56)
        if len(rec) < 56 or rec[:4] != b"PK\x06\x06":
            raise Incomplete("corrupt", "damaged archive: zip64 end record missing")
        cd, = struct.unpack_from("<Q", rec, 40)
    f.seek(0)
    return cd


def go_zip_read(data, name):
    """What Go's loadTzinfoFromZip (time/zoneinfo_read.go) gives for one zone name: its bytes,
    None when the zip has no such entry (Go goes on to the next source), or why Go fails.
    Go finds the end record in the last 22 bytes only, so an archive comment breaks it, and it
    reads stored entries only."""
    u16 = lambda b, o: int.from_bytes(b[o:o + 2], "little")
    u32 = lambda b, o: int.from_bytes(b[o:o + 4], "little")
    bad = "it is not a zip file Go can read"
    if len(data) < 22 or u32(data, len(data) - 22) != 0x06054B50:
        return bad
    n, size, off = u16(data, len(data) - 12), u32(data, len(data) - 10), u32(data, len(data) - 6)
    if off + size > len(data):
        return bad
    cd, want = data[off:off + size], name.encode()
    for _ in range(n):
        if len(cd) < 46 or u32(cd, 0) != 0x02014B50:
            break
        meth, usize, nl, xl, cl, at = u16(cd, 10), u32(cd, 24), u16(cd, 28), u16(cd, 30), u16(cd, 32), u32(cd, 42)
        zname, cd = cd[46:46 + nl], cd[46 + nl + xl + cl:]
        if zname != want:
            continue
        if meth != 0:
            return "its entries are compressed, and Go reads only stored ones"
        h = data[at:at + 30 + nl]
        if len(h) < 30 + nl or u32(h, 0) != 0x04034B50 or u16(h, 8) != meth or u16(h, 26) != nl or h[30:] != want:
            return bad
        start = at + 30 + nl + u16(h, 28)
        return data[start:start + usize] if start + usize <= len(data) else bad
    return None


class BoundedTarInfo(tarfile.TarInfo):
    """Refuses long-name and pax headers that tarfile would read whole into memory."""
    def _proc_member(self, tarfile_):
        if self.type in (tarfile.GNUTYPE_LONGNAME, tarfile.GNUTYPE_LONGLINK, tarfile.XHDTYPE,
                         tarfile.XGLTYPE, tarfile.SOLARIS_XHDTYPE) and self.size > TAR_HEADER_MAX:
            raise Incomplete("limit", f"a tar header extension of {self.size} bytes, over {TAR_HEADER_MAX}")
        return super()._proc_member(tarfile_)


class Prefixed:
    """A stream with its first bytes, already read to see the format, put back."""
    def __init__(self, head, f):
        self.head, self.f = head, f

    def read(self, n=-1):
        if self.head:
            k = len(self.head) if n is None or n < 0 else n
            b, self.head = self.head[:k], self.head[k:]
            return b
        return self.f.read(n)


class Inflate:
    """A bzip2, xz or zstd stream, decompressed at most n bytes per read."""
    def __init__(self, src, new):
        self.src, self.new, self.d, self.done = src, new, new(), False

    def read(self, n=-1):
        if n is None or n < 0:
            n = CHUNK
        try:
            while not self.done:
                if self.d.eof:  # another stream may follow, as in pbzip2 output
                    rest = self.d.unused_data or self.src.read(64 * KiB)
                    if not rest:
                        self.done = True
                        break
                    self.d = self.new()
                    try:
                        out = self.d.decompress(rest, n)
                    except Exception as e:  # padding or other trailing data, which tar readers ignore
                        if "memory" in str(e).lower():
                            raise
                        self.done = True
                        break
                elif self.d.needs_input:
                    raw = self.src.read(64 * KiB)
                    if not raw:
                        raise EOFError("compressed data ended early")
                    out = self.d.decompress(raw, n)
                else:
                    out = self.d.decompress(b"", n)
                if out:
                    return out
        except lzma.LZMAError as e:
            if "memory" in str(e).lower():
                raise Incomplete("limit", f"xz data needs more than {XZ_MEMORY} bytes of decoder memory")
            raise
        return b""


def decompressed(f):
    """f as a plain stream. gzip, bzip2, xz and zstd are decompressed here, a bounded
    amount per read, rather than by tarfile, which inflates a whole block at once."""
    head = b""
    while len(head) < 6:
        b = f.read(6 - len(head))
        if not b:
            break
        head += b
    src = Prefixed(head, f)
    if head.startswith(b"\x1f\x8b"):
        return gzip.GzipFile(fileobj=src, mode="rb")
    if head.startswith(b"BZh"):
        return Inflate(src, bz2.BZ2Decompressor)
    if head.startswith(b"\xfd7zXZ\x00"):
        return Inflate(src, lambda: lzma.LZMADecompressor(memlimit=XZ_MEMORY))
    if head.startswith(b"\x28\xb5\x2f\xfd") and zstd:
        return Inflate(src, zstd.ZstdDecompressor)
    return src


class Metered:
    """A tar stream as tarfile reads it, after decompression. Every byte counts against
    decompressed_bytes before tarfile gets it: headers, skipped members and padding too.
    While stop is set, reading past it is refused (header data of one entry)."""
    def __init__(self, scan, src):
        self.scan, self.src, self.pos, self.stop = scan, src, 0, None

    def read(self, n=-1):
        if n is None or n < 0:
            n = CHUNK
        if self.stop is not None and self.pos >= self.stop:
            raise Incomplete("limit", f"tar header data of one entry over {TAR_HEADER_MAX} bytes")
        self.scan.spend("decompressed_bytes", n)
        b = self.src.read(n)
        self.scan.used["decompressed_bytes"] -= n - len(b)
        self.pos += len(b)
        return b


def tar_members(scan, f):
    """(tarfile, member) for each entry of a plain or compressed tar stream."""
    meter = Metered(scan, decompressed(f))
    meter.stop = TAR_HEADER_MAX  # the first header is read on open
    with tarfile.open(fileobj=meter, mode="r|", tarinfo=BoundedTarInfo) as t:
        while True:
            m = t.next()
            if m is None:
                return
            del t.members[:]  # stream mode keeps every header otherwise
            meter.stop = None
            yield t, m
            # the next call skips to t.offset, then reads the next entry's headers
            meter.stop = max(meter.pos, t.offset) + TAR_HEADER_MAX


def _guard(scan, path, fn):
    """Run one entry; record what stops it. Returns False when the target must stop."""
    try:
        fn()
    except Exhausted as e:
        scan.problem(e.kind, path, str(e))
        return False
    except Incomplete as e:
        scan.problem(e.kind, path, str(e))
    except (OSError, EOFError, tarfile.TarError) as e:
        scan.problem("read-error", path, f"{type(e).__name__}: {e}")
    except (zipfile.BadZipFile, struct.error, zlib.error) as e:
        scan.problem("corrupt", path, f"{type(e).__name__}: {e}")
    except Exception as e:
        scan.problem("error", path, f"{type(e).__name__}: {e}")
    return not scan.full


def walk_tar(scan, fileobj):
    """Returns True when the archive was read to its end."""
    members, started = tar_members(scan, fileobj), False
    while True:
        try:
            item = next(members, None)
        except Incomplete as e:
            scan.problem(e.kind, scan.target, str(e))
            return False
        except Exception as e:
            scan.problem("read-error", scan.target, f"tar stream: {type(e).__name__}: {e}" if started else
                         f"not a readable tar archive: {type(e).__name__}: {e}")
            return False
        if item is None:
            return True
        started = True
        t, m = item
        path = m.name.lstrip("./")

        def one():
            scan.spend("members", 1)
            if m.issym():
                scan.keep_link(path, "sym", m.linkname)
            elif m.islnk():
                scan.keep_link(path, "hard", m.linkname.lstrip("./"))
            elif m.isfile():
                scan.entry(path, t.extractfile(m), m.size, False)
        if not _guard(scan, path, one):
            return False


def walk_dir(scan, top):
    if not os.path.isdir(top):
        scan.problem("read-error", top, "not a directory")
        return
    def onerror(e):
        scan.problem("read-error", os.path.relpath(e.filename, top) if e.filename else top, f"{type(e).__name__}: {e.strerror or e}")
    for dp, dn, fn in os.walk(top, onerror=onerror):
        if scan.full:
            return
        for name in fn + [d for d in dn if os.path.islink(os.path.join(dp, d))]:
            full = os.path.join(dp, name)
            path = os.path.relpath(full, top)

            def one():
                scan.spend("members", 1)
                if os.path.islink(full):
                    scan.keep_link(path, "sym", os.readlink(full))
                    return
                fd = os.open(full, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0))
                with os.fdopen(fd, "rb") as fh:
                    st = os.fstat(fh.fileno())
                    if stat.S_ISREG(st.st_mode):
                        scan.entry(path, fh, st.st_size, True)
            if not _guard(scan, path, one):
                return


# ---- docker ------------------------------------------------------------------
_SIG = {"defer": 0, "pending": []}


def _on_signal(signum, frame):
    if _SIG["defer"] and not _SIG["pending"]:
        _SIG["pending"].append(signum)
        print("tzscan: interrupted; finishing the Docker step so the container can be removed "
              "(interrupt again to stop waiting)", file=sys.stderr)
        return
    raise SystemExit(128 + signum)


@contextlib.contextmanager
def deferred_signals():
    """The first SIGINT/SIGTERM inside waits for the block to finish, then exits."""
    _SIG["defer"] += 1
    try:
        yield
    finally:
        _SIG["defer"] -= 1
    if not _SIG["defer"] and _SIG["pending"]:
        raise SystemExit(128 + _SIG["pending"][0])


def docker(*args):
    """Run docker in its own session, so a terminal Ctrl-C reaches only tzscan."""
    p = subprocess.Popen(["docker", *args], stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                         start_new_session=True)
    try:
        out, err = p.communicate()
    except BaseException:
        p.kill()
        p.wait()
        raise
    return p.returncode, out.decode(errors="replace").strip(), err.decode(errors="replace").strip()


def remove_container(scan, ref):
    """docker rm -f -v: the container and its anonymous volumes. A failure is reported."""
    try:
        rc, _, err = docker("rm", "-f", "-v", "--", ref)
    except SystemExit:
        print(f"tzscan: stopped before container {ref} was removed; remove it with: docker rm -f -v {ref}", file=sys.stderr)
        raise
    except OSError as e:
        rc, err = 1, str(e)
    if rc != 0 and "No such container" not in err:
        scan.cleanup_error = "; ".join(filter(None, [scan.cleanup_error, f"{ref}: {err}"]))
        print(f"tzscan: could not remove container {ref}: {err}\n"
              f"tzscan: remove it with: docker rm -f -v {ref}", file=sys.stderr)


def zoneinfo_path(value, workdir="/"):
    """(absolute path, opened as a zip) for ZONEINFO=value, or None if unset. A relative value is
    joined to the working directory as written: `..` is resolved against the image's own links.
    Go chooses zip or directory from the value itself."""
    if not value:
        return None
    path = value if value.startswith("/") else (workdir or "/").rstrip("/") + "/" + value
    return path, len(value) > 4 and value.endswith(".zip")


def zoneinfo_from_config(text):
    """ZONEINFO from `docker image inspect --format '{{json .Config}}'` output (the last entry wins)."""
    cfg = json.loads(text) or {}
    value = None
    for e in cfg.get("Env") or []:
        if e.startswith("ZONEINFO="):
            value = e[len("ZONEINFO="):]
    return zoneinfo_path(value, cfg.get("WorkingDir") or "/")


def scan_image(image, zoneinfo=None):
    scan = Scan(image)
    owned, cid, p, name, abandoned = [], None, None, None, False  # owned: every name tzscan asked Docker to create
    try:
        try:
            rc, _, err = docker("image", "inspect", "--format", "{{.Id}}", "--", image)
            if rc != 0:
                rc, _, err = docker("pull", "--", image)
                if rc != 0:
                    scan.problem("docker", image, f"docker pull failed: {err}")
                    return scan
            rc, out, err = docker("image", "inspect", "--format", "{{json .Config}}", "--", image)
            if rc != 0:
                scan.problem("docker", image, f"docker image inspect failed: {err}")
                return scan
        except OSError as e:
            scan.problem("docker", image, f"cannot run docker: {e}")
            return scan
        try:
            scan.set_zoneinfo(zoneinfo_from_config(out) if zoneinfo is None else zoneinfo_path(zoneinfo))
        except (ValueError, AttributeError, TypeError) as e:
            scan.problem("docker", image, f"unreadable image configuration: {type(e).__name__}: {e}")
            return scan
        with deferred_signals():
            for extra in ([], ["--entrypoint", ""]):
                name = "tzscan-" + os.urandom(8).hex()  # removable by name even if create is cut short
                owned.append(name)
                try:
                    rc, out, err = docker("create", "--pull", "never", "--name", name, "--label", LABEL + "=1",
                                          *extra, "--", image, "true")
                except SystemExit:
                    abandoned = True  # interrupted twice: Docker may still finish this create
                    raise
                if rc == 0:
                    break
                # a failed create does not prove the daemon created nothing (the reply may have
                # been lost), so the name is removed, and the result checked, before the next try
                remove_container(scan, name)
                owned.remove(name)
        if rc != 0:
            scan.problem("docker", image, f"docker create failed: {err}")
            return scan
        if not re.fullmatch(r"[0-9a-f]{64}", out):
            scan.problem("docker", image, f"docker create returned an unexpected container ID: {out[:100]!r}")
            return scan
        cid = out
        with tempfile.TemporaryFile() as errf:
            p = subprocess.Popen(["docker", "export", "--", cid], stdout=subprocess.PIPE, stderr=errf,
                                 start_new_session=True)
            if walk_tar(scan, p.stdout):
                after = 0
                while after <= 16 * MiB:  # end-of-archive padding
                    b = p.stdout.read(MiB)
                    if not b:
                        break
                    after += len(b)
                if after > 16 * MiB:
                    scan.problem("read-error", image, "docker export kept writing after the end of the archive")
                else:
                    rc = p.wait()
                    if rc != 0:
                        errf.seek(0)
                        msg = errf.read(4096).decode(errors="replace").strip()
                        scan.problem("read-error", image, f"docker export exited {rc}: {msg}")
    finally:
        if p and p.poll() is None:
            p.kill()
            p.wait()
        if owned:
            with deferred_signals():
                for n in owned:
                    remove_container(scan, cid if cid and n == name else n)
                if abandoned:
                    print(f"tzscan: stopped waiting for docker create; if Docker still creates container {name}, "
                          f"remove it with: docker rm -f -v {name}\n"
                          f"tzscan: leftovers carry a label: docker ps -a --filter label={LABEL}", file=sys.stderr)
    scan.finish()
    return scan


# ---- output ------------------------------------------------------------------
def print_scan(scan):
    print(f"== {scan.target}")
    if scan.zoneinfo_env:
        print(f"   ZONEINFO={scan.zoneinfo_env}" + (f": {scan.zoneinfo_note}" if scan.zoneinfo_note else ""))
    for tier, title in (("A", "used by default for local time"), ("B", "library and program copies (matter only if that code is used)")):
        group = [c for c in scan.copies if c.get("tier") == tier and not c.get("sameAs")]
        if not group:
            continue
        print(f"   -- {title}")
        merged = {}
        for c in group:  # identical copies of one library (e.g. a jar in every plugin) print once
            merged.setdefault((c["kind"], c["release"], c["verdict"], c["how"]), []).append(c)
        for cs in merged.values():
            c = cs[0]
            extra = ""
            if c["wrong"]:
                extra = "  wrong from 1 Nov: " + ", ".join(z.split("/")[1] for z in c["wrong"] if z != "Africa/Casablanca")
                if "Africa/Casablanca" in c["wrong"]:
                    extra += "; Casablanca wrong now"
            more = f" (+{len(cs) - 1} identical)" if len(cs) > 1 else ""
            print(f"   {c['verdict']:7} {c['path']}{more}  [{c['kind']}] data {c['release']}{extra}")
            print(f"   {'':7}   {c['how']}; {c['use']}")
            for lp in c.get("linkedFrom", []):
                print(f"   {'':7}   linked from {lp}")
    for pr in scan.problems:
        if pr["kind"] == "nothing-judged":
            print(f"   {pr['message']}")
        else:
            print(f"   INCOMPLETE {pr['path']}: {pr['message']}")
    if scan.problems and any(c["verdict"] == "STALE" for c in scan.copies):
        print("   scan incomplete (exit 2); the stale copies above are still stale")


class _Indented:
    """Writes one element of the JSON list as json.dumps(list, indent=1) would."""
    def __init__(self, out):
        self.out = out

    def write(self, s):
        self.out.write(s.replace("\n", "\n "))


def exit_status(statuses):
    st = set(statuses)
    for code in (2, 1, 3):
        if code in st:
            return code
    return 0


def main():
    sys.stdout.reconfigure(errors="backslashreplace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("images", nargs="*")
    ap.add_argument("--tar", action="append", default=[])
    ap.add_argument("--dir", action="append", default=[])
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--zoneinfo", metavar="PATH",
                    help="the ZONEINFO value the container runs with (absolute; empty for unset). "
                         "Images are otherwise read from their configuration; --tar and --dir have none")
    a = ap.parse_args()
    if not (a.images or a.tar or a.dir):
        ap.error("give an image, --tar or --dir")
    if a.zoneinfo and not a.zoneinfo.startswith("/"):
        ap.error("--zoneinfo takes an absolute path")
    for img in a.images:
        if not img or img.startswith("-"):
            ap.error(f"not an image name: {img!r}")
    # a terminated scan still removes its temporary container (finally blocks run on SystemExit)
    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)
    jobs = [(img, lambda img=img: scan_image(img, a.zoneinfo)) for img in a.images]
    for t in a.tar:
        def job(t=t):
            s = Scan(t)
            s.set_zoneinfo(zoneinfo_path(a.zoneinfo))
            try:
                fh = sys.stdin.buffer if t == "-" else open(t, "rb")
            except OSError as e:
                s.problem("read-error", t, f"{type(e).__name__}: {e}")
            else:
                with fh:
                    walk_tar(s, fh)
            s.finish()
            return s
        jobs.append((t, job))
    for d in a.dir:
        def job(d=d):
            s = Scan(d)
            s.set_zoneinfo(zoneinfo_path(a.zoneinfo))
            walk_dir(s, d)
            s.finish()
            return s
        jobs.append((d, job))
    statuses = []  # each target is printed when done, so only one target's findings are held
    for target, job in jobs:
        try:
            s = job()
        except Exception as e:
            s = Scan(target)
            s.problem("error", target, f"{type(e).__name__}: {e}")
        s.conclude()
        if a.json:
            sys.stdout.write(",\n " if statuses else "[\n ")
            json.dump({"target": s.target, "status": s.status, "complete": not s.problems,
                       **({"zoneinfoEnv": {"path": s.zoneinfo_env, "form": "zip" if s.zoneinfo_zip else "directory",
                                           "found": s.zoneinfo_full,
                                           **({"note": s.zoneinfo_note} if s.zoneinfo_note else {})}}
                          if s.zoneinfo_env else {}),
                       "copies": s.copies, "problems": s.problems,
                       **({"cleanupError": s.cleanup_error} if s.cleanup_error else {})}, _Indented(sys.stdout), indent=1)
        else:
            print_scan(s)
        sys.stdout.flush()
        statuses.append(s.status)
    if a.json:
        print("\n]")
    return exit_status(statuses)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (SystemExit, KeyboardInterrupt):
        raise
    except BaseException as e:  # never let a crash read as exit 1 ("stale")
        try:
            print(f"tzscan: internal error: {type(e).__name__}: {e}", file=sys.stderr)
            sys.stdout.flush()
        except BaseException:  # e.g. no memory left to print
            pass
        os._exit(2)  # sys.exit can itself fail when memory is exhausted, and Python then exits 1
