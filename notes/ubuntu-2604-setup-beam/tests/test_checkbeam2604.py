"""Fixture tests for checkbeam2604.py against the October 13 builds.txt lists in tests/data.

python3 -m unittest discover -s tests     (no network: refs come from the built-in table)
"""
import contextlib, io, json, os, shutil, sys, tempfile, textwrap, unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.dont_write_bytecode = True
import checkbeam2604 as c  # noqa: E402


def data_dir():
    d = tempfile.mkdtemp()
    for osv in c.OSES:
        shutil.copy(os.path.join(HERE, "data", f"otp-builds-ubuntu-{osv}.txt"), d)
    return d


class Base(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dir = data_dir()
        cls.data = c.Data(cls.dir, refresh=False, offline=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.dir)

    def repo(self, workflow, files=None):
        root = tempfile.mkdtemp()
        self.addCleanup(shutil.rmtree, root)
        os.makedirs(os.path.join(root, ".github", "workflows"))
        with open(os.path.join(root, ".github", "workflows", "ci.yml"), "w") as f:
            f.write(textwrap.dedent(workflow))
        for name, text in (files or {}).items():
            with open(os.path.join(root, name), "w") as f:
                f.write(text)
        return root

    def check(self, workflow, files=None):
        return [(st, spec, where.split(": ", 1)[1]) for st, act, spec, where, soft
                in c.check_repo(self.data, self.repo(workflow, files)) if st != "NA"]

    def step(self, with_, uses="erlef/setup-beam@v1"):
        """One setup-beam step; `with_` values are YAML scalars as written in a workflow."""
        flow = ", ".join(f"{k}: {v}" for k, v in with_.items())
        return self.check(f"""
            on: push
            jobs:
              t:
                runs-on: ubuntu-latest
                steps:
                  - uses: {uses}
                    with: {{{flow}}}
            """)


class Resolution(Base):
    def test_otp_25_breaks(self):
        self.assertEqual(self.step({"otp-version": "'25'"}),
                         [("BREAK", "25", "otp-version: 24.04->OTP-25.3.2.21 26.04->None")])

    def test_otp_24_x_breaks(self):
        self.assertEqual(self.step({"otp-version": "24.x"})[0][:2], ("BREAK", "24.x"))

    def test_otp_27_ok(self):
        self.assertEqual(self.step({"otp-version": "'27'"}),
                         [("OK", "27", "otp-version: 24.04->OTP-27.3.4.18 26.04->OTP-27.3.4.18")])

    def test_old_otp_already(self):
        self.assertEqual(self.step({"otp-version": "'22'"}), [("ALREADY", "22", "otp-version: 24.04->None")])

    def test_rc_only_on_2404(self):
        self.assertEqual(self.step({"otp-version": "26.0-rc1"})[0][:2], ("BREAK", "26.0-rc1"))

    def test_strict(self):
        self.assertEqual(self.step({"otp-version": "27.3.4.3", "version-type": "strict"})[0][0], "OK")
        self.assertEqual(self.step({"otp-version": "25.3.2.7", "version-type": "strict"})[0][0], "BREAK")
        self.assertEqual(self.step({"otp-version": "'27'", "version-type": "strict"})[0][0], "ALREADY")

    def test_yaml_float_is_stringified_like_the_runner(self):
        self.assertEqual(self.step({"otp-version": "25.0"})[0][:2], ("BREAK", "25"))

    def test_latest_and_branches(self):
        self.assertEqual(self.step({"otp-version": "latest"})[0][0], "OK")
        self.assertEqual(self.step({"otp-version": "maint-25"})[0][0], "BREAK")
        self.assertEqual(self.step({"otp-version": "master"})[0][0], "OK")

    def test_action_error_is_already(self):
        self.assertEqual(self.step({"otp-version": "'*'"}), [("ALREADY", "*", "otp-version: 24.04->ERROR Cannot read properties of null")])

    def test_handpicked_specs(self):
        """The 17 specs resolved with setup-beam's own code (tests/parity holds the full corpus)."""
        want = {("25", False): ("OTP-25.3.2.21", None), ("25.3", False): ("OTP-25.3.2.21", None),
                ("24.3", False): ("OTP-24.3.4.17", None), ("26", False): ("OTP-26.2.5.21", "OTP-26.2.5.21"),
                ("26.x", False): ("OTP-26.2.5.21", "OTP-26.2.5.21"), ("27.0", False): ("OTP-27.0.1", "OTP-27.0.1"),
                ("28", False): ("OTP-28.5.0.7", "OTP-28.5.0.7"), ("latest", False): ("OTP-29.1.1", "OTP-29.1.1"),
                ("25.3.2.7", True): ("OTP-25.3.2.7", None), ("27.3.4.3", True): ("OTP-27.3.4.3", "OTP-27.3.4.3"),
                ("26.0-rc3", False): ("OTP-26.0-rc3", None), ("OTP-25.0", False): ("OTP-25.0.4", None),
                ("21.3", False): (None, None), ("maint-27", False): ("maint-27", "maint-27"),
                ("master", False): ("master", "master"), ("~> 26.2", False): ("OTP-26.2.5.21", "OTP-26.2.5.21"),
                ("26.2.3", False): ("OTP-26.2.3", "OTP-26.2.3")}
        for (spec, strict), exp in want.items():
            got = tuple(c.resolve_otp(self.data, spec, strict, osv) for osv in c.OSES)
            self.assertEqual(got, exp, spec)

    def test_non_ascii_spec_is_unknown(self):
        self.assertEqual(self.step({"otp-version": "'２５'"})[0][0], "UNKNOWN")


class Refs(Base):
    def test_old_tag_breaks_for_every_otp(self):
        self.assertEqual(self.step({"otp-version": "'27'"}, uses="erlef/setup-beam@v1.20.4"),
                         [("BREAK", "27", "erlef/setup-beam@v1.20.4 does not know the 26.04 image (v1.24.1 or later does)")])

    def test_both_causes(self):
        r = self.step({"otp-version": "'25'"}, uses="erlef/setup-beam@v1.24.0")
        self.assertEqual(r[0][0], "BREAK")
        self.assertIn("26.04 image", r[0][2])
        self.assertIn("26.04->None", r[0][2])

    def test_current_refs_ok(self):
        for ref in ("v1", "v1.24", "v1.24.1", "main", "54075bcc5e249e4758d363f27d099f55d843f124", "54075bc"):
            self.assertEqual(self.step({"otp-version": "'27'"}, uses=f"erlef/setup-beam@{ref}")[0][0], "OK", ref)

    def test_release_sha_and_short_sha(self):
        for ref in ("fc68ffb90438ef2936bbb3251622353b3dcb2f93", "fc68ffb"):
            self.assertEqual(self.step({"otp-version": "'27'"}, uses=f"erlef/setup-beam@{ref}")[0][0], "BREAK", ref)

    def test_ref_without_2404_support_is_already(self):
        self.assertEqual(self.step({"otp-version": "'27'"}, uses="erlef/setup-beam@v1.16")[0][0], "ALREADY")

    def test_unplaced_sha_offline_is_unknown(self):
        r = self.step({"otp-version": "'27'"}, uses="erlef/setup-beam@566deebc640988a494af16ecdf6f820fe0d3fea4")
        self.assertEqual(r[0][0], "UNKNOWN")

    def test_looked_up_ref_from_cache(self):
        d = data_dir()
        self.addCleanup(shutil.rmtree, d)
        with open(os.path.join(d, "setup-beam-refs.json"), "w") as f:
            json.dump({"566deeb": ["ubuntu22", "ubuntu24"], "gone": None}, f)
        data = c.Data(d, refresh=False, offline=True)
        root = self.repo("""
            on: push
            jobs:
              t:
                runs-on: ubuntu-latest
                steps:
                  - uses: erlef/setup-beam@566deeb
                    with: {otp-version: '27'}
                  - uses: erlef/setup-beam@gone
                    with: {otp-version: '27'}
            """)
        self.assertEqual([x[0] for x in c.check_repo(data, root)], ["BREAK", "UNKNOWN"])

    def test_otp_false(self):
        self.assertEqual(self.step({"otp-version": "false", "gleam-version": "'1.12'"})[0][0], "OK")
        self.assertEqual(self.step({"otp-version": "false", "gleam-version": "'1.12'"},
                                   uses="erlef/setup-beam@v1.18.2")[0][0], "UNKNOWN")


class Inputs(Base):
    WF = """
        on: push
        jobs:
          t:
            runs-on: ubuntu-latest
            steps:
              - uses: erlef/setup-beam@v1
                with:
                  version-type: {vt}
                  version-file: {vf}
                  {extra}
        """

    def test_tool_versions_strict(self):
        r = self.check(self.WF.format(vt="strict", vf=".tool-versions", extra=""),
                       {".tool-versions": "elixir 1.14.5-otp-25\nerlang 25.3.2.21\n"})
        self.assertEqual(r, [("BREAK", "25.3.2.21", ".tool-versions: 24.04->OTP-25.3.2.21 26.04->None")])

    def test_tool_versions_last_erlang_line_wins(self):
        r = self.check(self.WF.format(vt="strict", vf=".tool-versions", extra=""),
                       {".tool-versions": "erlang 25.3.2.21\nerlang ref:v27.3.4.3\n"})
        self.assertEqual(r[0][:2], ("OK", "27.3.4.3"))

    def test_mise_toml(self):
        r = self.check(self.WF.format(vt="strict", vf="mise.toml", extra=""),
                       {"mise.toml": '[tools]\nerlang = { version = "24.3.4.17" }\n'})
        self.assertEqual(r[0][:2], ("BREAK", "24.3.4.17"))

    def test_version_file_needs_strict(self):
        r = self.check(self.WF.format(vt="loose", vf=".tool-versions", extra=""), {".tool-versions": "erlang 25.3.2.21\n"})
        self.assertEqual(r[0][0], "ALREADY")

    def test_input_and_file_both_set(self):
        r = self.check(self.WF.format(vt="strict", vf=".tool-versions", extra="otp-version: '27'"),
                       {".tool-versions": "erlang 25.3.2.21\n"})
        self.assertEqual(r[0][0], "ALREADY")

    def test_missing_version_file_unknown(self):
        self.assertEqual(self.check(self.WF.format(vt="strict", vf=".tool-versions", extra=""))[0][0], "UNKNOWN")

    def test_no_otp_version_already(self):
        self.assertEqual(self.step({"elixir-version": "'1.17'"}), [("ALREADY", "", "no otp-version")])

    def test_expression_unknown(self):
        self.assertEqual(self.step({"otp-version": "${{ inputs.otp }}"})[0][0], "UNKNOWN")

    def test_imageos_override_unknown(self):
        r = self.check("""
            on: push
            jobs:
              t:
                runs-on: ubuntu-latest
                env: {ImageOS: ubuntu24}
                steps:
                  - uses: erlef/setup-beam@v1
                    with: {otp-version: '25'}
            """)
        self.assertEqual(r[0][0], "UNKNOWN")


class Workflows(Base):
    def test_include_only_matrix_keeps_every_entry(self):
        r = self.check("""
            on: push
            jobs:
              t:
                runs-on: ${{ matrix.os || 'ubuntu-latest' }}
                strategy:
                  matrix:
                    include:
                      - {otp: '25', elixir: '1.14'}
                      - {otp: '25', elixir: '1.14', os: ubuntu-24.04}
                      - {otp: '27', elixir: '1.17'}
                steps:
                  - uses: erlef/setup-beam@v1
                    with: {otp-version: '${{ matrix.otp }}', elixir-version: '${{ matrix.elixir }}'}
            """)
        self.assertEqual([x[:2] for x in r], [("BREAK", "25"), ("OK", "27")])

    def test_not_ubuntu_latest_or_container(self):
        r = self.check("""
            on: push
            jobs:
              a:
                runs-on: ubuntu-24.04
                steps: [{uses: erlef/setup-beam@v1, with: {otp-version: '25'}}]
              b:
                runs-on: ubuntu-latest
                container: hexpm/elixir:1.14.5-erlang-25.3.2.21-ubuntu-jammy-20250714
                steps: [{uses: erlef/setup-beam@v1, with: {otp-version: '25'}}]
            """)
        self.assertEqual(r, [])

    def test_other_setup_actions_unknown(self):
        r = self.check("""
            on: push
            jobs:
              t:
                runs-on: ubuntu-latest
                steps: [{uses: actions/setup-elixir@v1, with: {otp-version: '25'}}]
            """)
        self.assertEqual(r[0][0], "UNKNOWN")

    def test_setup_elixir_old_name_is_checked(self):
        self.assertEqual(self.step({"otp-version": "'25'"}, uses="erlef/setup-elixir@v1")[0][0], "BREAK")

    def test_main_output_exit_and_json(self):
        root = self.repo("""
            on: push
            jobs:
              t:
                runs-on: ubuntu-latest
                continue-on-error: true
                steps: [{uses: erlef/setup-beam@v1, with: {otp-version: '25'}}]
            """)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = c.main(["--data", self.dir, "--offline", root])
        self.assertEqual(rc, 1)
        self.assertEqual(out.getvalue(), "BREAK    setup-beam    25         .github/workflows/ci.yml:t: "
                         "otp-version: 24.04->OTP-25.3.2.21 26.04->None (continue-on-error)\n")
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            c.main(["--data", self.dir, "--offline", "--json", root])
        f = json.loads(out.getvalue())["findings"][0]
        self.assertEqual((f["status"], f["action"], f["spec"], f["continueOnError"]), ("BREAK", "setup-beam", "25", True))
        ok = self.repo("""
            on: push
            jobs:
              t:
                runs-on: ubuntu-latest
                steps: [{uses: erlef/setup-beam@v1, with: {otp-version: '27'}}]
            """)
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(c.main(["--data", self.dir, "--offline", ok]), 0)

    def test_example_repository(self):
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            rc = c.main(["--data", self.dir, "--offline", os.path.join(HERE, "..", "example")])
        self.assertEqual(rc, 1)
        self.assertEqual([line.split()[0] for line in out.getvalue().splitlines()], ["BREAK", "OK", "OK", "BREAK", "OK"])


if __name__ == "__main__":
    unittest.main()
