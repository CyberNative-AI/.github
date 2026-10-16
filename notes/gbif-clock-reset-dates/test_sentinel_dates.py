"""python3 -m unittest test_sentinel_dates  (no network; tests the `file` command only)"""

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

import sentinel_dates

# eventDate shapes seen in GBIF records; the last three rows have no single day or use year/month/day
ROWS = [
    ("1", "inat", "1980-01-01", "1980", "1", "1"),            # sentinel
    ("2", "inat", "1980-01-01T00:02", "1980", "1", "1"),      # sentinel, with time
    ("3", "inat", "1969-12-31T16:00:00-08:00", "1969", "12", "31"),  # sentinel, with offset
    ("4", "other", "1899-12-30", "1899", "12", "30"),         # sentinel
    ("5", "inat", "1980-01-02", "1980", "1", "2"),            # control day
    ("6", "inat", "2001-01-01", "2001", "1", "1"),            # sentinel, not in the default list
    ("7", "other", "1970-01-01/1970-12-31", "1970", "", ""),  # a year-long range: skipped
    ("8", "other", "1970", "1970", "", ""),                   # year only: skipped
    ("9", "other", "", "2000", "1", "1"),                     # no eventDate: year/month/day used
    ("10", "inat", "2000-01-01T14:30:00", "2000", "1", "1"),  # sentinel, daytime clock
    ("11", "inat\\x", "1980-01-03", "1980", "1", "3"),        # retained, with a backslash
]


def run(*argv):
    out = io.StringIO()
    sys.argv = ["sentinel_dates.py", *argv]
    with contextlib.redirect_stdout(out):
        sentinel_dates.main()
    return out.getvalue()


class FileCommand(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        self.path = self.dir / "occurrence.txt"
        lines = ["gbifID\tdatasetKey\teventDate\tyear\tmonth\tday"] + ["\t".join(r) for r in ROWS]
        self.path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    def test_counts_default_dates(self):
        text = run("file", str(self.path))
        self.assertIn("11 rows, 6 on a sentinel date", text)
        self.assertIn("1980-01-01         2", text)

    def test_exclude_writes_the_other_rows(self):
        clean = self.dir / "clean.tsv"
        run("file", str(self.path), "--exclude-to", str(clean))
        ids = [line.split("\t")[0] for line in clean.read_text(encoding="utf-8").splitlines()[1:]]
        self.assertEqual(ids, ["5", "6", "7", "8", "11"])

    def test_midnight_keeps_untimed_and_daytime_rows_on_1980_and_2000(self):
        clean = self.dir / "clean.tsv"
        text = run("file", str(self.path), "--midnight", "--exclude-to", str(clean))
        self.assertIn("11 rows, 3 on a sentinel date", text)
        ids = [line.split("\t")[0] for line in clean.read_text(encoding="utf-8").splitlines()[1:]]
        self.assertEqual(ids, ["1", "5", "6", "7", "8", "9", "10", "11"])

    def test_retained_rows_are_copied_byte_for_byte(self):
        clean = self.dir / "clean.tsv"
        run("file", str(self.path), "--exclude-to", str(clean))
        source = self.path.read_text(encoding="utf-8").splitlines()
        kept = clean.read_text(encoding="utf-8").splitlines()
        self.assertEqual(kept[0], source[0])
        self.assertIn("11\tinat\\x\t1980-01-03\t1980\t1\t3", kept)
        self.assertTrue(set(kept) <= set(source))

    def test_refuses_to_overwrite_the_download_or_any_existing_file(self):
        before = self.path.read_bytes()
        link = self.dir / "link.txt"
        link.symlink_to(self.path)
        hard = self.dir / "hard.txt"
        hard.hardlink_to(self.path)
        other = self.dir / "existing.tsv"
        other.write_text("keep me\n", encoding="utf-8")
        for target in (self.path, self.dir / "." / "occurrence.txt", link, hard, other):
            with self.subTest(target=target), self.assertRaises(SystemExit) as stop:
                run("file", str(self.path), "--exclude-to", str(target))
            self.assertIn("already exists", str(stop.exception.code))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(other.read_text(encoding="utf-8"), "keep me\n")

    def test_custom_dates(self):
        text = run("file", str(self.path), "--dates", "2001-01-01")
        self.assertIn("11 rows, 1 on a sentinel date", text)


if __name__ == "__main__":
    unittest.main()
