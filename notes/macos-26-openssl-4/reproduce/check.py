"""Check the tables and totals in ../README.md against the raw output in results/.

python3 check.py   # exits 0 if every claim matches, 1 otherwise
"""
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
failures = []


def expect(cond, what):
    print(("ok   " if cond else "FAIL ") + what)
    if not cond:
        failures.append(what)


for label in ("macos-latest", "macos-26"):
    out = (HERE / "results" / f"probe-{label}.txt").read_text(encoding="utf-8")
    expect("ProductVersion:\t\t26.6.2" in out and "ImageVersion=20261013.0424.1" in out, f"{label}: macOS 26.6.2, image 20261013.0424.1")
    expect("OpenSSL 3.6.5" in out.split("## fixtures")[0].split("which -a openssl:")[1].splitlines()[3], f"{label}: default openssl is 3.6.5")
    expect("pbeWithSHA1And40BitRC2-CBC" in out, f"{label}: fixture .p12 is RC2-40-CBC")
    gates = re.findall(r"openssl=(\S+ \S+) .*?gate='(.*?)' LEGACY_FLAG='(.*?)'\n  cert read rc=(\d), key read rc=(\d)", out)
    table = {(v, g): (flag, int(a), int(b)) for v, g, flag, a, b in gates}
    want = {
        ("OpenSSL 3.6.5", "^OpenSSL 3"): ("-legacy", 0, 0),
        ("OpenSSL 3.6.5", "^OpenSSL [3-9]"): ("-legacy", 0, 0),
        ("OpenSSL 4.0.3", "^OpenSSL 3"): ("", 1, 1),
        ("OpenSSL 4.0.3", "^OpenSSL [3-9]"): ("-legacy", 0, 0),
        ("LibreSSL 3.3.6", "^OpenSSL 3"): ("", 0, 0),
        ("LibreSSL 3.3.6", "^OpenSSL [3-9]"): ("", 0, 0),
    }
    expect(table == want, f"{label}: version-check table (6 rows)")
    expect("Algorithm (RC2-40-CBC : 0), Properties (<null>)" in out, f"{label}: OpenSSL 4 error text")
    expect(re.search(r"openssl@4/bin/openssl version -e\n  version: Unknown option: -e\n.*\n  \[rc=1\]", out) is not None, f"{label}: version -e exits 1 on 4.0.3")
    expect(out.count('MODULESDIR: "/opt/homebrew/Cellar/openssl@') == 2, f"{label}: version -m works on 3.6.5 and 4.0.3")
    expect("AES-256-CBC" in out and "MAC: sha256" in out, f"{label}: OpenSSL 4 export without -legacy is AES-256-CBC, SHA-256 MAC")
    imports = re.findall(r"security import (\S+) .*\n((?:  .*\n)*?)  \[rc=(\d)\]", out)
    expect([(f, int(rc)) for f, _, rc in imports] == [("legacy.p12", 0), ("o3.p12", 1), ("o4.p12", 1)], f"{label}: security import accepts only the -legacy export")
    expect(out.count("MAC verification failed during PKCS12 import (wrong password?)") == 2, f"{label}: import error text")
    tls = re.findall(r"  (\S+) (srv\S*\.crt): (\d) key-identifier extensions\n    handshake (OK|FAIL)(?:: (.*))?", out)
    expect(tls == [("3.6.5", "srv.crt", "2", "OK", ""), ("3.6.5", "srv-fixed.crt", "2", "OK", ""),
                   ("4.0.3", "srv.crt", "0", "FAIL", "Missing Authority Key Identifier"), ("4.0.3", "srv-fixed.crt", "2", "OK", "")],
           f"{label}: key-identifier table")
    expect("python 3.15.0 OpenSSL 4.0.3" in out, f"{label}: runner python3 is 3.15.0 on OpenSSL 4.0.3")
    expect("include/openssl -> ../Cellar/openssl@4/4.0.3/include/openssl" in out and "lib/libssl.dylib -> ../Cellar/openssl@4/4.0.3/lib/libssl.dylib" in out
           and "pkg-config openssl: 4.0.3" in out, f"{label}: headers, libssl and pkg-config are 4.0.3")

sig = (HERE / "results" / "signing-step-macos-latest.txt").read_text(encoding="utf-8")
rows = re.findall(r"gate='(.*?)' \| (\S+ \S+) \| step rc=(\d) \| identities in keychain: (\d)", sig)
expect(rows == [("^OpenSSL 3", "OpenSSL 3.6.5", "0", "1"), ("^OpenSSL 3", "OpenSSL 4.0.3", "1", "0"), ("^OpenSSL 3", "LibreSSL 3.3.6", "0", "1"),
                ("^OpenSSL [3-9]", "OpenSSL 3.6.5", "0", "1"), ("^OpenSSL [3-9]", "OpenSSL 4.0.3", "0", "1"), ("^OpenSSL [3-9]", "LibreSSL 3.3.6", "0", "1")],
       "signing step: only '^OpenSSL 3' on 4.0.3 fails and imports nothing")

lin = (HERE / "results" / "linux-python-check.txt").read_text(encoding="utf-8")
expect("python 3.13.16" in lin and "P 4.0.3 leaf.pem SSLCertVerificationError" in lin and "Missing Authority Key Identifier" in lin
       and "P 3.6.5 leaf.pem OK" in lin, "Linux Python 3.13.16: same key-identifier result")

s = json.loads((HERE / "results" / "replay-summary.json").read_text(encoding="utf-8"))
c = s["invocation_classes"]
bare = c["SAME"] + c["UNTESTED"] + c["STDOUT_CHANGE"] + c["FILE_CHANGE"] + c["BREAK"]
tested = bare - c["UNTESTED"]
expect(s["E_active_codebases"] == 1027, "1,027 repositories")
expect(bare == 2202, "2,202 plain openssl calls")
expect(tested == 2031 and round(100 * tested / bare) == 92, "2,031 run (92%)")
expect((c["SAME"], c["STDOUT_CHANGE"], c["FILE_CHANGE"], c["BREAK"]) == (1825, 139, 66, 1), "1,825 same, 139 printed, 66 file, 1 failed")

sys.exit(1 if failures else 0)
