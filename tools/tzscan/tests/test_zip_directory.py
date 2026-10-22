"""Offline tests for tzscan's zip_directory_bytes limit.

The limit is 64 MiB and counts the central directories of every archive open at
once (a jar and the jars enclosing it), so raising it from 32 MiB per archive does
not raise the nested worst case. No other limit changes.
"""
import importlib.util
import io
import os
import tempfile
import unittest
import zipfile
from unittest import mock

HERE = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
_spec = importlib.util.spec_from_file_location("tzscan", os.path.join(HERE, "tzscan.py"))
tzscan = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(tzscan)
MiB, GiB = 1 << 20, 1 << 30


def jar_bytes(n, extra=()):
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_STORED) as z:
        for i in range(n):
            z.writestr(f"x/{i:06d}.class", b"")
        for name, data in extra:
            z.writestr(name, data)
    return buf.getvalue()


def cd_size(data):
    return tzscan.zip_directory_size(io.BytesIO(data), len(data))


def scan_dir(files, limit):
    with tempfile.TemporaryDirectory() as d:
        for rel, data in files.items():
            os.makedirs(os.path.dirname(os.path.join(d, rel)), exist_ok=True)
            with open(os.path.join(d, rel), "wb") as fh:
                fh.write(data)
        scan = tzscan.Scan(d)
        with mock.patch.dict(tzscan.LIMITS, {"zip_directory_bytes": limit}):
            tzscan.walk_dir(scan, d)
    return scan


def limit_problems(scan):
    return {p["path"]: p["message"] for p in scan.problems if p["kind"] == "limit"}


class ZipDirectoryLimit(unittest.TestCase):
    def test_limits_unchanged_except_zip_directory(self):
        self.assertEqual(tzscan.LIMITS, {
            "member_bytes": 4 * GiB, "decompressed_bytes": 64 * GiB, "members": 5_000_000,
            "zip_directory_bytes": 64 * MiB, "retained_bytes": 256 * MiB, "reports": 10_000,
            "scanned_bytes": 64 * GiB, "records": 200_000, "jar_depth": 3})

    def test_single_archive_at_and_over_limit(self):
        data = jar_bytes(200)
        cd = cd_size(data)
        self.assertEqual(limit_problems(scan_dir({"app/a.jar": data}, cd)), {})
        msg = limit_problems(scan_dir({"app/a.jar": data}, cd - 1))["app/a.jar"]
        self.assertIn(f"central directory of {cd} bytes, over the zip_directory_bytes limit", msg)
        self.assertNotIn("enclosing", msg)

    def test_nested_directories_count_together(self):
        inner = jar_bytes(150)
        outer = jar_bytes(150, [("lib/inner.jar", inner)])
        ci, co = cd_size(inner), cd_size(outer)
        sibling = jar_bytes(150)
        scan = scan_dir({"app/a.jar": outer, "app/b.jar": sibling}, max(co, ci) + min(co, ci) - 1)
        got = limit_problems(scan)
        self.assertEqual(list(got), ["app/a.jar!/lib/inner.jar"])
        self.assertIn(f"central directory of {ci} bytes (enclosing archives' directories hold {co} more)",
                      got["app/a.jar!/lib/inner.jar"])
        self.assertEqual(scan.open_cd, 0)  # released after each archive, so b.jar was examined
        # with room for both, the nested jar is examined
        self.assertEqual(limit_problems(scan_dir({"app/a.jar": outer}, co + ci)), {})

    def test_released_after_damaged_archive(self):
        scan = scan_dir({"app/a.jar": jar_bytes(10)[:-30] + b"\0" * 30, "app/b.jar": jar_bytes(10)}, MiB)
        self.assertEqual(scan.open_cd, 0)
        self.assertEqual(limit_problems(scan), {})


if __name__ == "__main__":
    unittest.main()
