"""Offline tests for ZONEINFO: Go's LoadLocation reads the zip or directory it
names before /usr/share/zoneinfo and before the program's embedded time/tzdata,
so that copy is the one used by default.

The zone files are generated: each holds one fixed offset, which is all tzscan
reads (the offset on 2026-12-15). Set TZSCAN_DOCKER_TESTS=1 to also build
images with `docker import` and scan them.
"""
import importlib.util
import io
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile
import unittest
import zipfile

HERE = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
TZSCAN = os.path.join(HERE, "tzscan.py")
_spec = importlib.util.spec_from_file_location("tzscan", TZSCAN)
tzscan = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tzscan)

# UTC offsets on 2026-12-15 in a 2026c copy (Inuvik and Winnipeg wrong) and a 2026e copy
OFFSETS = {
    "2026c": {"America/Vancouver": -7, "America/Edmonton": -6, "Africa/Casablanca": 0,
              "America/Inuvik": -7, "America/Winnipeg": -6},
    "2026e": {z: good for z, (good, _) in tzscan.ZONES.items()},
}


def tzif(hours):
    """A TZif v2 file with no transitions and one fixed offset."""
    chars = b"%+03d\0" % hours

    def block():
        return (b"TZif2" + b"\0" * 15 + struct.pack(">6l", 0, 0, 0, 0, 1, len(chars))
                + struct.pack(">lbB", hours * 3600, 0, 0) + chars)
    return block() + block() + b"\n<%+03d>%d\n" % (hours, -hours)


def zip_bytes(release, method=zipfile.ZIP_STORED, comment=b""):
    """A Go-style zoneinfo.zip: stored entries named like the zones."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", method) as z:
        for zone, hours in OFFSETS[release].items():
            z.writestr(zone, tzif(hours))
        z.comment = comment
    return buf.getvalue()


def deflated_zip(release):
    """The same entries compressed, as `zip -r` makes them; Go cannot read these."""
    return zip_bytes(release, zipfile.ZIP_DEFLATED)


def go_program(release):
    """An ELF file carrying an embedded zip, as Go's time/tzdata does."""
    return b"\x7fELF" + b"\0" * 4092 + zip_bytes(release) + b"\0" * 4096


def put(root, rel, data):
    path = os.path.join(root, rel)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as fh:
        fh.write(data)


def tree(root, rel, release):
    for zone, hours in OFFSETS[release].items():
        put(root, os.path.join(rel, zone), tzif(hours))


def run(*args):
    p = subprocess.run([sys.executable, TZSCAN, "--json", *args], capture_output=True, text=True)
    try:
        return p.returncode, json.loads(p.stdout)[0], p.stderr
    except ValueError:
        return p.returncode, None, p.stderr


def tiers(s):
    return {(c["kind"], c["path"]): (c["tier"], c["verdict"], c["release"]) for c in s["copies"]}


class ZoneinfoEnvDir(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def test_named_zip_is_the_copy_used(self):
        # the common scratch/distroless pattern: COPY zoneinfo.zip + ENV ZONEINFO=/zoneinfo.zip
        put(self.root, "zoneinfo.zip", zip_bytes("2026c"))
        rc, s, err = run("--dir", self.root, "--zoneinfo", "/zoneinfo.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s), {("zoneinfo", "zoneinfo.zip"): ("A", "STALE", "2026c")})
        self.assertEqual(s["zoneinfoEnv"], {"path": "/zoneinfo.zip", "form": "zip", "found": True})

    def test_unnamed_zip_unchanged(self):
        put(self.root, "zoneinfo.zip", zip_bytes("2026c"))
        for extra in ([], ["--zoneinfo", ""]):  # "" means unset
            rc, s, err = run("--dir", self.root, *extra)
            self.assertEqual(rc, 3, err)
            self.assertEqual(tiers(s), {("zoneinfo", "zoneinfo.zip"): ("B", "STALE", "2026c")})
            self.assertNotIn("zoneinfoEnv", s)

    def test_named_zip_makes_embedded_copy_a_fallback(self):
        # the zip was updated and the program still embeds an old copy: Go uses the zip
        put(self.root, "app/zoneinfo.zip", zip_bytes("2026e"))
        put(self.root, "app/server", go_program("2026c"))
        rc, s, err = run("--dir", self.root, "--zoneinfo", "/app/zoneinfo.zip")
        self.assertEqual(rc, 3, err)
        self.assertEqual(tiers(s), {("zoneinfo", "app/zoneinfo.zip"): ("A", "OK", ">=2026e"),
                                    ("go-embedded", "app/server"): ("B", "STALE", "2026c")})
        used = next(c["use"] for c in s["copies"] if c["kind"] == "go-embedded")
        self.assertIn("ZONEINFO names /app/zoneinfo.zip", used)

    def test_stale_named_zip_not_hidden_by_current_os_tree(self):
        tree(self.root, "usr/share/zoneinfo", "2026e")
        put(self.root, "app/zoneinfo.zip", zip_bytes("2026c"))
        rc, s, err = run("--dir", self.root, "--zoneinfo", "/app/zoneinfo.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s), {("zoneinfo", "usr/share/zoneinfo"): ("A", "OK", ">=2026e"),
                                    ("zoneinfo", "app/zoneinfo.zip"): ("A", "STALE", "2026c")})

    def test_named_path_missing_falls_back_to_embedded(self):
        put(self.root, "server", go_program("2026c"))
        rc, s, err = run("--dir", self.root, "--zoneinfo", "/nowhere/zoneinfo.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s), {("go-embedded", "server"): ("A", "STALE", "2026c")})
        self.assertEqual(s["zoneinfoEnv"]["path"], "/nowhere/zoneinfo.zip")
        self.assertFalse(s["zoneinfoEnv"]["found"])

    def test_named_symlink_followed(self):
        put(self.root, "usr/local/go/lib/time/zoneinfo.zip", zip_bytes("2026c"))
        os.symlink("usr/local/go/lib/time/zoneinfo.zip", os.path.join(self.root, "zoneinfo.zip"))
        rc, s, err = run("--dir", self.root, "--zoneinfo", "/zoneinfo.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("zoneinfo", "usr/local/go/lib/time/zoneinfo.zip")][0], "A")

    def test_named_directory(self):
        # a value that is not a zip names a zone tree
        tree(self.root, "opt/tz", "2026e")
        put(self.root, "server", go_program("2026c"))
        rc, s, err = run("--dir", self.root, "--zoneinfo", "/opt/tz")
        self.assertEqual(rc, 3, err)
        self.assertEqual(tiers(s), {("zoneinfo", "opt/tz"): ("A", "OK", ">=2026e"),
                                    ("go-embedded", "server"): ("B", "STALE", "2026c")})

    def test_relative_option_refused(self):
        rc, _, err = run("--dir", self.root, "--zoneinfo", "zoneinfo.zip")
        self.assertEqual(rc, 2)
        self.assertIn("absolute", err)

    def test_tar_input(self):
        put(self.root, "zoneinfo.zip", zip_bytes("2026c"))
        tar = os.path.join(tempfile.mkdtemp(), "image.tar")
        self.addCleanup(shutil.rmtree, os.path.dirname(tar))
        subprocess.run(["tar", "-C", self.root, "-cf", tar, "."], check=True)
        rc, s, err = run("--tar", tar, "--zoneinfo", "/zoneinfo.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("zoneinfo", "zoneinfo.zip")][0], "A")


class ZoneinfoFromConfig(unittest.TestCase):
    def cfg(self, env=None, workdir=""):
        return tzscan.zoneinfo_from_config(json.dumps({"Env": env, "WorkingDir": workdir}))

    def test_absolute(self):
        self.assertEqual(self.cfg(["PATH=/bin", "ZONEINFO=/zoneinfo.zip"]), ("/zoneinfo.zip", True))

    def test_relative_joins_working_dir_as_written(self):
        # `..` is left for the walk, where it climbs from the target of any link before it
        self.assertEqual(self.cfg(["ZONEINFO=zoneinfo.zip"], "/app"), ("/app/zoneinfo.zip", True))
        self.assertEqual(self.cfg(["ZONEINFO=../tz/zoneinfo.zip"], "/app/bin"), ("/app/bin/../tz/zoneinfo.zip", True))

    def test_zip_or_directory_follows_the_value(self):
        # Go: len(value) > 4 and value ends in ".zip"; everything else is a directory, "/" included
        self.assertEqual(self.cfg(["ZONEINFO=/"]), ("/", False))
        self.assertEqual(self.cfg(["ZONEINFO=/opt/tz"]), ("/opt/tz", False))
        self.assertEqual(self.cfg(["ZONEINFO=.zip"], "/app"), ("/app/.zip", False))
        self.assertEqual(self.cfg(["ZONEINFO=a.zip"], "/app"), ("/app/a.zip", True))
        self.assertEqual(self.cfg(["ZONEINFO=/tz.ZIP"]), ("/tz.ZIP", False))

    def test_last_entry_wins_and_empty_is_unset(self):
        self.assertEqual(self.cfg(["ZONEINFO=/a.zip", "ZONEINFO=/b.zip"]), ("/b.zip", True))
        self.assertIsNone(self.cfg(["ZONEINFO=/a.zip", "ZONEINFO="]))

    def test_unset(self):
        self.assertIsNone(self.cfg(None))
        self.assertIsNone(self.cfg(["ZONEINFOX=/a.zip", "TZ=America/Winnipeg"]))
        self.assertIsNone(tzscan.zoneinfo_from_config("null"))


class GoZipRead(unittest.TestCase):
    """go_zip_read against the rules of Go's loadTzinfoFromZip."""
    def test_stored_entry(self):
        self.assertEqual(tzscan.go_zip_read(zip_bytes("2026c"), "America/Inuvik"), tzif(-7))

    def test_missing_entry_is_not_an_error(self):
        self.assertIsNone(tzscan.go_zip_read(zip_bytes("2026c"), "Europe/Paris"))

    def test_compressed_entry(self):
        self.assertIn("compressed", tzscan.go_zip_read(deflated_zip("2026e"), "America/Inuvik"))

    def test_archive_comment_breaks_go(self):
        # Go reads the end record from the last 22 bytes only
        self.assertIn("not a zip", tzscan.go_zip_read(zip_bytes("2026e", comment=b"x"), "America/Inuvik"))
        self.assertIn("not a zip", tzscan.go_zip_read(b"", "America/Inuvik"))

    def test_bad_local_header(self):
        data = bytearray(zip_bytes("2026e"))
        data[0:4] = b"XXXX"  # the first local header
        self.assertIn("not a zip", tzscan.go_zip_read(bytes(data), "America/Vancouver"))


class ZoneinfoEffectiveSource(unittest.TestCase):
    """Negatives: the source Go reads through ZONEINFO is measured, or the scan is incomplete."""
    def setUp(self):
        self.root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.root)

    def scan(self, value):
        return run("--dir", self.root, "--zoneinfo", value)

    def link(self, target, name):
        os.symlink(target, os.path.join(self.root, name))

    def test_zip_under_another_name(self):
        put(self.root, "custom.zip", zip_bytes("2026c"))
        tree(self.root, "usr/share/zoneinfo", "2026e")
        rc, s, err = self.scan("/custom.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("zoneinfo", "custom.zip")], ("A", "STALE", "2026c"))
        self.assertTrue(s["complete"])

    def test_zip_under_linked_parent(self):
        put(self.root, "real/zoneinfo.zip", zip_bytes("2026c"))
        tree(self.root, "usr/share/zoneinfo", "2026e")
        self.link("real", "alias")
        rc, s, err = self.scan("/alias/zoneinfo.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("zoneinfo", "real/zoneinfo.zip")], ("A", "STALE", "2026c"))

    def test_absolute_link_starts_from_the_root(self):
        put(self.root, "real/zoneinfo.zip", zip_bytes("2026c"))
        put(self.root, "opt/real/zoneinfo.zip", zip_bytes("2026e"))
        tree(self.root, "usr/share/zoneinfo", "2026e")
        self.link("/real", "opt/alias")  # the target is the image's /real, never read on the host
        rc, s, err = self.scan("/opt/alias/zoneinfo.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("zoneinfo", "real/zoneinfo.zip")], ("A", "STALE", "2026c"))

    def test_dotdot_climbs_from_link_target(self):
        # /alias/.. is /deep, not /: the kernel follows alias before applying ..
        put(self.root, "zoneinfo.zip", zip_bytes("2026e"))
        put(self.root, "deep/zoneinfo.zip", zip_bytes("2026c"))
        os.makedirs(os.path.join(self.root, "deep/sub"))
        self.link("deep/sub", "alias")
        rc, s, err = self.scan("/alias/../zoneinfo.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("zoneinfo", "deep/zoneinfo.zip")][0], "A")
        self.assertEqual(tiers(s)[("zoneinfo", "zoneinfo.zip")][0], "B")

    def test_root_directory(self):
        tree(self.root, "", "2026c")
        tree(self.root, "usr/share/zoneinfo", "2026e")
        rc, s, err = self.scan("/")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("zoneinfo", ".")], ("A", "STALE", "2026c"))
        self.assertEqual(s["zoneinfoEnv"]["form"], "directory")

    def test_directory_through_dotdot_and_link(self):
        tree(self.root, "opt/tz", "2026c")
        tree(self.root, "srv/tz", "2026e")
        put(self.root, "server", go_program("2026e"))
        os.makedirs(os.path.join(self.root, "opt/x"))
        self.link("opt/x", "w")
        rc, s, err = self.scan("/w/../tz")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("zoneinfo", "opt/tz")], ("A", "STALE", "2026c"))

    def test_compressed_zip_keeps_embedded_copy_in_use(self):
        put(self.root, "zoneinfo.zip", deflated_zip("2026e"))
        put(self.root, "server", go_program("2026c"))
        rc, s, err = self.scan("/zoneinfo.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("go-embedded", "server")], ("A", "STALE", "2026c"))
        self.assertFalse(s["zoneinfoEnv"]["found"])
        self.assertIn("compressed", s["zoneinfoEnv"]["note"])

    def test_commented_zip_keeps_embedded_copy_in_use(self):
        put(self.root, "zoneinfo.zip", zip_bytes("2026e", comment=b"built by make"))
        put(self.root, "server", go_program("2026c"))
        rc, s, err = self.scan("/zoneinfo.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("go-embedded", "server")], ("A", "STALE", "2026c"))

    def test_zip_named_directory_keeps_embedded_copy_in_use(self):
        tree(self.root, "fake.zip", "2026e")
        put(self.root, "server", go_program("2026c"))
        rc, s, err = self.scan("/fake.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("go-embedded", "server")], ("A", "STALE", "2026c"))
        self.assertEqual(tiers(s)[("zoneinfo", "fake.zip")][0], "B")

    def test_zip_value_without_suffix_is_a_directory(self):
        # ZONEINFO=/zoneinfo names a zip file here, but Go reads /zoneinfo/America/... and finds nothing
        put(self.root, "zoneinfo", zip_bytes("2026e"))
        put(self.root, "server", go_program("2026c"))
        rc, s, err = self.scan("/zoneinfo")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("go-embedded", "server")], ("A", "STALE", "2026c"))

    def test_partial_zip_keeps_fallback_in_use(self):
        # Go loads Vancouver from the zip and the other zones from the embedded copy
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
            z.writestr("America/Vancouver", tzif(-7))
        put(self.root, "zoneinfo.zip", buf.getvalue())
        put(self.root, "server", go_program("2026c"))
        rc, s, err = self.scan("/zoneinfo.zip")
        self.assertEqual(rc, 1, err)
        t = tiers(s)
        self.assertEqual(t[("go-embedded", "server")], ("A", "STALE", "2026c"))
        self.assertEqual(t[("zoneinfo", "zoneinfo.zip")][0], "A")
        self.assertIn("1 of the 5 zones", s["zoneinfoEnv"]["note"])

    def test_partial_directory_current_is_incomplete_not_clean(self):
        put(self.root, "opt/tz/America/Vancouver", tzif(-7))
        put(self.root, "server", go_program("2026e"))
        rc, s, err = self.scan("/opt/tz")
        self.assertEqual(rc, 2, err)

    def test_final_link_to_other_name_is_incomplete(self):
        # tzscan reads the zip under the ZONEINFO file name only, so this one is not established
        put(self.root, "data/tzdata.bin", zip_bytes("2026c"))
        tree(self.root, "usr/share/zoneinfo", "2026e")
        self.link("data/tzdata.bin", "tz.zip")
        rc, s, err = self.scan("/tz.zip")
        self.assertEqual(rc, 2, err)
        self.assertFalse(s["complete"])
        self.assertTrue(any(p["kind"] == "zoneinfo" for p in s["problems"]))

    def test_link_loop_is_incomplete(self):
        tree(self.root, "usr/share/zoneinfo", "2026e")
        self.link("b.zip", "a.zip")
        self.link("a.zip", "b.zip")
        rc, s, err = self.scan("/a.zip")
        self.assertEqual(rc, 2, err)

    def test_tar_link_after_target(self):
        # in a tar the parent link can come after the zip it leads to
        put(self.root, "real/zoneinfo.zip", zip_bytes("2026c"))
        tree(self.root, "usr/share/zoneinfo", "2026e")
        self.link("real", "zz-alias")
        tar = os.path.join(tempfile.mkdtemp(), "image.tar")
        self.addCleanup(shutil.rmtree, os.path.dirname(tar))
        subprocess.run(["tar", "-C", self.root, "-cf", tar, "real", "usr", "zz-alias"], check=True)
        rc, s, err = run("--tar", tar, "--zoneinfo", "/zz-alias/zoneinfo.zip")
        self.assertEqual(rc, 1, err)
        self.assertEqual(tiers(s)[("zoneinfo", "real/zoneinfo.zip")][0], "A")


@unittest.skipUnless(os.environ.get("TZSCAN_DOCKER_TESTS") == "1" and shutil.which("docker"),
                     "set TZSCAN_DOCKER_TESTS=1 to build and scan images")
class ZoneinfoEnvImage(unittest.TestCase):
    def image(self, files, *changes):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        for rel, data in files.items():
            put(root, rel, data)
        tag = "tzscan-test/zoneinfo:" + os.urandom(6).hex()
        tar = subprocess.run(["tar", "-C", root, "-c", "."], capture_output=True, check=True).stdout
        subprocess.run(["docker", "import", *[x for c in changes for x in ("--change", c)], "-", tag],
                       input=tar, capture_output=True, check=True)
        self.addCleanup(subprocess.run, ["docker", "rmi", "-f", tag], capture_output=True)
        return tag

    def test_image_env_absolute(self):
        img = self.image({"zoneinfo.zip": zip_bytes("2026c")}, "ENV ZONEINFO=/zoneinfo.zip")
        rc, s, err = run(img)
        self.assertEqual(rc, 1, err)
        self.assertEqual(s["zoneinfoEnv"], {"path": "/zoneinfo.zip", "form": "zip", "found": True})

    def test_image_env_relative_to_workdir_and_override(self):
        img = self.image({"app/zoneinfo.zip": zip_bytes("2026c")}, "WORKDIR /app", "ENV ZONEINFO=zoneinfo.zip")
        rc, s, err = run(img)
        self.assertEqual(rc, 1, err)
        self.assertEqual(s["zoneinfoEnv"], {"path": "/app/zoneinfo.zip", "form": "zip", "found": True})
        rc, s, err = run(img, "--zoneinfo", "")  # a run-time value replaces the image's
        self.assertEqual(rc, 3, err)
        self.assertNotIn("zoneinfoEnv", s)

    def test_image_without_env_unchanged(self):
        rc, s, err = run(self.image({"zoneinfo.zip": zip_bytes("2026c")}))
        self.assertEqual(rc, 3, err)
        self.assertNotIn("zoneinfoEnv", s)


if __name__ == "__main__":
    unittest.main()
