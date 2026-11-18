"""The hosted image cache is dated data (hosted-cache.json in --data), not a table in the code.

python3 -m unittest discover -s tests (from the tool dir). The network test runs only with
CHECK2604_NETWORK=1: it runs the command line with --refresh against today's upstream lists.
"""
import contextlib, io, json, os, shutil, sys, tempfile, textwrap, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import check2604 as c  # noqa: E402

SNAPSHOT = os.path.join(HERE, "data")  # 2026-10-12 build lists and image caches
WORKFLOW = """\
    on: push
    jobs:
      test:
        runs-on: ubuntu-latest
        strategy:
          matrix:
            python-version: ["3.12", "3.9"]
        steps:
          - uses: actions/setup-python@v6
            with:
              python-version: ${{ matrix.python-version }}
    """
# Image 20261111.196.1 (Ubuntu 26.04), read 2026-11-18. When the image moves past 3.12.16, set
# CHECK2604_EXPECT_312 to its new cached 3.12 patch (the test also checks it is the cached one).
EXPECT_312 = os.environ.get("CHECK2604_EXPECT_312", "3.12.16")


def repo(d):
    os.makedirs(os.path.join(d, ".github", "workflows"))
    with open(os.path.join(d, ".github", "workflows", "ci.yml"), "w") as f:
        f.write(textwrap.dedent(WORKFLOW))
    return d


def cli(*argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = c.main(list(argv))
    return code, {line.split()[2]: line for line in out.getvalue().splitlines()}


class HostedCache(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, self.tmp)

    def data_dir(self, cache=None):
        d = os.path.join(self.tmp, "data")
        shutil.copytree(SNAPSHOT, d)
        if cache is None:
            os.remove(os.path.join(d, "hosted-cache.json"))
        else:
            with open(os.path.join(d, "hosted-cache.json"), "w") as f:
                json.dump(cache, f)
        return d

    def test_snapshot_reads_its_own_dated_cache(self):
        data = c.Data(SNAPSHOT, refresh=False)
        self.assertEqual(c.resolve_python(data, "3.12", "26.04"), "3.12.14")

    def test_cache_file_overrides_the_table(self):
        cache = json.loads(json.dumps(c.CACHE))
        cache["26.04"]["python"] = ["3.12.16"]
        data = c.Data(self.data_dir(cache), refresh=False)
        self.assertEqual(c.resolve_python(data, "3.12", "26.04"), "3.12.16")
        self.assertIsNone(c.resolve_python(data, "3.9", "26.04"))

    def test_no_cache_file_falls_back_to_the_table(self):
        data = c.Data(self.data_dir(), refresh=False)
        self.assertIs(data.cache, c.CACHE)
        self.assertEqual(c.resolve_python(data, "3.12", "26.04"), "3.12.16")

    def test_a_cache_file_that_is_not_versions_is_refused(self):
        cache = json.loads(json.dumps(c.CACHE))
        cache["26.04"]["python"] = ["3.12"]
        with self.assertRaises(ValueError):
            c.Data(self.data_dir(cache), refresh=False)

    def test_cached_lists_reads_the_readme_layout(self):
        md = "### Cached Tools\n\n#### Python\n- 3.11.18\n- 3.12.16\n\n#### Ruby\n- 3.2.11\n- 3.4.12\n\n#### Go\n- 1.25.4\n"
        self.assertEqual(c.cached_lists(md), {"python": ["3.11.18", "3.12.16"], "ruby": ["3.2.11", "3.4.12"]})
        with self.assertRaises(ValueError):
            c.cached_lists("#### Python\n- 3.12\n#### Ruby\n- 3.4.12\n")

    @unittest.skipUnless(os.environ.get("CHECK2604_NETWORK") == "1", "network: set CHECK2604_NETWORK=1")
    def test_refresh_bare_312_is_cached_build_and_39_still_fails(self):
        data = os.path.join(self.tmp, "data")  # empty: --refresh fetches every list
        code, lines = cli("--refresh", "--data", data, repo(os.path.join(self.tmp, "repo")))
        with open(os.path.join(data, "hosted-cache.json")) as f:
            cached = json.load(f)["26.04"]["python"]
        print("\n" + "\n".join(lines.values()), file=sys.stderr)
        self.assertIn(EXPECT_312, cached)
        self.assertTrue(lines["3.12"].startswith("OK "), lines["3.12"])
        self.assertIn(f"26.04->{EXPECT_312}", lines["3.12"])
        self.assertTrue(lines["3.9"].startswith("BREAK "), lines["3.9"])
        self.assertIn("26.04->None", lines["3.9"])
        self.assertEqual(code, 1)  # a BREAK sets the exit status


if __name__ == "__main__":
    unittest.main()
