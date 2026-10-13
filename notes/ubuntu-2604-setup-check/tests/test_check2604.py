"""Fixture tests for check2604.py: python3 -m unittest discover -s tests (from the tool dir)."""
import os, sys, tempfile, textwrap, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import check2604 as c  # noqa: E402

DATA = c.Data(os.path.join(HERE, "data"), refresh=False)  # 2026-10-12 snapshot


def run(workflow, files=None, full=False):
    with tempfile.TemporaryDirectory() as d:
        os.makedirs(os.path.join(d, ".github", "workflows"))
        with open(os.path.join(d, ".github", "workflows", "ci.yml"), "w") as f:
            f.write(textwrap.dedent(workflow))
        for name, body in (files or {}).items():
            if body.startswith("->"):  # symlink fixture
                os.symlink(body[2:], os.path.join(d, name))
                continue
            with open(os.path.join(d, name), "w") as f:
                f.write(body)
        res = c.check_repo(DATA, d)
        return res if full else [(st, spec, where) for st, _a, spec, where, _s in res]


def statuses(res):
    return sorted((spec, st) for st, spec, _ in res)


class Python(unittest.TestCase):
    def test_matrix_versions(self):
        r = run("""
            jobs:
              t:
                runs-on: ubuntu-latest
                strategy:
                  matrix:
                    python-version: [3.8, "3.9", "3.10", 3.11, 3.10, "3.12.4", "3.12.14", "3.x"]
                steps:
                  - uses: actions/setup-python@v6
                    with:
                      python-version: ${{ matrix.python-version }}
            """)
        self.assertEqual(statuses(r), sorted([
            ("3.8", "BREAK"), ("3.9", "BREAK"), ("3.10", "OK"), ("3.11", "OK"),
            ("3.1", "ALREADY"),  # unquoted 3.10 is the number 3.1
            ("3.12.4", "BREAK"), ("3.12.14", "OK"), ("3.x", "OK")]))

    def test_other_os_and_pinned_runner_ignored(self):
        r = run("""
            jobs:
              a:
                runs-on: ${{ matrix.os }}
                strategy:
                  matrix:
                    os: [ubuntu-latest, windows-latest, ubuntu-24.04, macos-latest]
                    py: ["3.9"]
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "${{ matrix.py }}"}
              b:
                runs-on: ubuntu-22.04
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "3.8"}
              c:
                runs-on: [self-hosted, ubuntu-latest]
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "3.8"}
            """)
        self.assertEqual(len(r), 1)
        self.assertIn("os=ubuntu-latest", r[0][2])
        self.assertEqual(r[0][0], "BREAK")

    def test_include_exclude(self):
        r = run("""
            jobs:
              t:
                runs-on: ${{ matrix.os }}
                strategy:
                  matrix:
                    os: [ubuntu-latest, macos-latest]
                    python: ["3.9", "3.13"]
                    exclude:
                      - {os: ubuntu-latest, python: "3.9"}
                    include:
                      - {os: ubuntu-latest, python: "3.8", experimental: true}
                      - {python: "3.13", extra: x}
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "${{ matrix.python }}"}
            """)
        self.assertEqual(statuses(r), [("3.13", "OK"), ("3.8", "BREAK")])
        self.assertTrue(any("extra=x" in w for _, _, w in r))

    def test_unresolvable_is_unknown_never_ok(self):
        r = run("""
            on: {workflow_call: {inputs: {py: {type: string}}}}
            jobs:
              a:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "${{ inputs.py }}"}
              b:
                runs-on: ubuntu-latest
                strategy:
                  matrix: ${{ fromJSON(needs.x.outputs.m) }}
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "${{ matrix.py }}"}
              c:
                runs-on: ${{ inputs.os }}
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "3.12"}
              d:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "3.9 garbage"}
            """)
        self.assertEqual([st for st, _, _ in r], ["UNKNOWN"] * 4)

    def test_container_job_not_affected(self):
        r = run("""
            jobs:
              t:
                runs-on: ubuntu-latest
                container: python:3.8
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "3.8"}
            """)
        self.assertEqual([st for st, _, _ in r], ["NA"])

    def test_version_files(self):
        r = run("""
            jobs:
              a:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/checkout@v5
                  - uses: actions/setup-python@v5
              b:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version-file: pyproject.toml}
              c:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version-file: missing.txt}
            """, {".python-version": "3.11.9\n", "pyproject.toml": '[project]\nname="x"\nrequires-python=">=3.9,<3.13"\n'})
        self.assertEqual([st for st, _, _ in r], ["BREAK", "OK", "UNKNOWN"])

    def test_env_and_conditions(self):
        r = run("""
            env: {PY: "3.9"}
            jobs:
              t:
                runs-on: ${{ matrix.os }}
                continue-on-error: ${{ matrix.experimental }}
                strategy:
                  matrix:
                    os: [ubuntu-latest, windows-latest]
                    experimental: [true]
                steps:
                  - uses: actions/setup-python@v5
                    if: matrix.os == 'windows-latest'
                    with: {python-version: "3.8"}
                  - uses: actions/setup-python@v5
                    if: runner.os == 'Linux'
                    with: {python-version: "${{ env.PY }}"}
                  - uses: actions/setup-python@v5
                    if: github.event_name == 'push'
                    with: {python-version: "pypy3.9"}
            """)
        self.assertEqual(statuses(r), [("3.9", "BREAK"), ("pypy3.9", "NA")])

    def test_continue_on_error_flagged(self):
        full = run("""
            jobs:
              t:
                runs-on: ubuntu-latest
                continue-on-error: ${{ matrix.experimental }}
                strategy:
                  matrix:
                    py: ["3.9"]
                    experimental: [true, false]
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "${{ matrix.py }}"}
            """, full=True)
        self.assertEqual(sorted(x[4] for x in full), [False, True])

    def test_prerelease_and_freethreaded(self):
        r = run("""
            jobs:
              t:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "3.15", allow-prereleases: true}
                  - uses: actions/setup-python@v5
                    with: {python-version: "3.13t"}
            """)
        self.assertEqual([st for st, _, _ in r], ["OK", "OK"])

    def test_symlink_outside_checkout_not_read(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as f:
            f.write("3.9\n")
        try:
            r = run("""
                jobs:
                  t:
                    runs-on: ubuntu-latest
                    steps:
                      - uses: actions/setup-python@v5
                        with: {python-version-file: .python-version}
                """, {".python-version": "->" + f.name})
        finally:
            os.unlink(f.name)
        self.assertEqual([st for st, _, _ in r], ["UNKNOWN"])

    def test_cache_before_manifest(self):
        # hosted image serves a cached build first: '3.12' is 3.12.14 on 26.04, 3.12.15 on 24.04
        self.assertEqual(c.resolve_python(DATA, "3.12", "26.04"), "3.12.14")
        self.assertEqual(c.resolve_python(DATA, "3.12", "24.04"), "3.12.15")
        self.assertEqual(c.resolve_python(DATA, "3.12", "26.04", arch="arm64"), "3.12.15")

    def test_nested_matrix_and_mixed_conditions(self):
        r = run("""
            jobs:
              t:
                runs-on: ${{ matrix.plat.image }}
                continue-on-error: ${{ matrix.py == '3.15' || false }}
                if: github.event_name == 'push' && matrix.plat.name != 'win'
                strategy:
                  matrix:
                    plat: [{name: lin, image: ubuntu-latest}, {name: win, image: ubuntu-latest}]
                    py: ["3.9"]
                    pair: [["3.8", "x"]]
                steps:
                  - uses: actions/setup-python@v5
                    if: ${{ matrix.plat['name'] == 'LIN' && github.ref == 'refs/heads/main' }}
                    with: {python-version: "${{ matrix.py }}"}
                  - uses: actions/setup-python@v5
                    with: {python-version: "${{ matrix.PAIR[0] }}"}
                  - uses: actions/setup-python@v5
                    if: matrix.py == '3.9' || matrix.py == '3.8'
                    with: {python-version: "3.12"}
            """, full=True)
        self.assertEqual(sorted((x[0], x[2]) for x in r), [("BREAK", "3.8"), ("BREAK", "3.9"), ("UNKNOWN", "")])
        self.assertTrue(all("plat.name" not in x[3] and "name=win" not in x[3] for x in r))
        self.assertEqual({x[4] for x in r if x[0] == "BREAK"}, {None})

    def test_include_does_not_extend_added_combinations(self):
        # GitHub's documented example: {fruit: banana, animal: cat} stays apart from the added {fruit: banana}
        combos = c.expand_matrix({"matrix": {
            "fruit": ["apple", "pear"], "animal": ["cat", "dog"],
            "include": [{"color": "green"}, {"color": "pink", "animal": "cat"}, {"fruit": "apple", "shape": "circle"},
                        {"fruit": "banana"}, {"fruit": "banana", "animal": "cat"}]}})
        self.assertEqual(sorted(combos, key=lambda x: sorted(x.items())), sorted([
            {"fruit": "apple", "animal": "cat", "color": "pink", "shape": "circle"},
            {"fruit": "apple", "animal": "dog", "color": "green", "shape": "circle"},
            {"fruit": "pear", "animal": "cat", "color": "pink"},
            {"fruit": "pear", "animal": "dog", "color": "green"},
            {"fruit": "banana"}, {"fruit": "banana", "animal": "cat"}], key=lambda x: sorted(x.items())))

    def test_or_fallback(self):
        r = run("""
            on: {workflow_call: {inputs: {os: {type: string}}}}
            jobs:
              a:
                runs-on: ${{ matrix.os || 'ubuntu-latest' }}
                strategy:
                  matrix:
                    py: ["3.9", "3.12"]
                    include:
                      - {py: "3.8", os: ubuntu-22.04}
                      - {py: "3.8", os: ""}  # a separate combination, as in GitHub's matrix docs
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "${{ matrix.py }}"}
              b:
                runs-on: ["${{ matrix.combo.os || 'ubuntu-latest' }}"]
                strategy:
                  matrix:
                    combo: [{py: "3.10"}, {py: "3.8", os: windows-latest}, {py: "3.11", os: ubuntu-latest}]
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "${{ matrix.combo.py || '3.7' }}"}
              c:
                runs-on: ${{ inputs.os || 'ubuntu-latest' }}
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "3.12"}
              d:
                runs-on: ${{ matrix.os == 'win' || 'ubuntu-latest' }}
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "3.12"}
              e:
                runs-on: ubuntu-latest
                steps:
                  - uses: actions/setup-python@v5
                    with: {python-version: "${{ env.PY || '3.12' }}"}
            """)
        got = sorted((where.split(":")[1].split("[")[0], spec, st) for st, spec, where in r)
        self.assertEqual(got, [
            ("a", "3.12", "OK"), ("a", "3.8", "BREAK"), ("a", "3.9", "BREAK"),  # "" is falsy too
            ("b", "3.10", "OK"), ("b", "3.11", "OK"),
            ("c", "", "UNKNOWN"), ("d", "", "UNKNOWN"), ("e", "", "UNKNOWN")])

    def test_bad_yaml_is_unknown(self):
        r = run("jobs: [unclosed\n")
        self.assertEqual([st for st, _, _ in r], ["UNKNOWN"])


class Ruby(unittest.TestCase):
    def test_ruby_versions(self):
        r = run("""
            jobs:
              t:
                runs-on: ubuntu-latest
                strategy:
                  matrix:
                    ruby: ["3.4.2", "3.4", "2.7", "3.1", ruby, "4.0", head, "jruby-9.4"]
                steps:
                  - uses: ruby/setup-ruby@v1
                    with: {ruby-version: "${{ matrix.ruby }}"}
            """)
        got = dict((sp, st) for st, sp, _ in r)
        self.assertEqual(got["3.4.2"], "BREAK")
        self.assertEqual(got["3.4"], "OK")
        self.assertEqual(got["2.7"], "BREAK")
        self.assertEqual(got["3.1"], "BREAK")
        self.assertEqual(got["ruby"], "OK")
        self.assertEqual(got["4.0"], "OK")
        self.assertEqual(got[""], "UNKNOWN")  # head: separate asset repository
        self.assertIn(got["jruby-9.4"], ("OK", "BREAK"))

    def test_ruby_version_file(self):
        r = run("""
            jobs:
              t:
                runs-on: ubuntu-latest
                steps:
                  - uses: ruby/setup-ruby@v1
                    with: {bundler-cache: true}
            """, {".ruby-version": "ruby-3.3.0\n"})
        self.assertEqual([(st, sp) for st, sp, _ in r], [("BREAK", "ruby-3.3.0")])

    def test_ruby_explicit_version_file_input(self):
        r = run("""
            jobs:
              t:
                runs-on: ubuntu-latest
                steps:
                  - uses: ruby/setup-ruby@v1
                    with: {ruby-version: .ruby-version}
                  - uses: ruby/setup-ruby@v1
                    with: {ruby-version: .tool-versions}
            """, {".ruby-version": "3.4.11\n", ".tool-versions": "nodejs 24.1.0\nruby 3.2.2\n"})
        self.assertEqual([(st, sp) for st, sp, _ in r], [("OK", "3.4.11"), ("BREAK", "3.2.2")])

    def test_ruby_no_version(self):
        r = run("""
            jobs:
              t:
                runs-on: ubuntu-latest
                steps:
                  - uses: ruby/setup-ruby@v1
            """)
        self.assertEqual([st for st, _, _ in r], ["UNKNOWN"])


if __name__ == "__main__":
    unittest.main()
