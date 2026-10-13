"""Write specs.jsonl: otp-version inputs for the parity check against setup-beam's own code.

Every builds.txt entry (with and without OTP-/v prefixes and trailing parts), the shapes real
workflows use, node-semver range syntax, and seeded random combinations. Each spec is checked
loose and strict. Deterministic: rerunning gives the same file.
"""
import json, os, random

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")

keys = set()
for osv in ("24.04", "26.04"):
    with open(os.path.join(DATA, f"otp-builds-ubuntu-{osv}.txt")) as f:
        keys |= {line.split(" ")[0] for line in f if line.strip()}

SEEN = ['20', '20.0', '20.3', '21', '21.0', '21.3', '22', '22.0', '22.3', '23', '23.0', '23.2', '23.2.6', '23.3', '24', '24.0', '24.0.0', '24.1', '24.1.3', '24.2', '24.3', '24.3.4.17', '24.x', '25', '25.0', '25.1', '25.1.2', '25.3', '25.3.2', '25.3.2.11', '25.x', '26', '26.0', '26.0-rc1', '26.0.2', '26.0.x', '26.1.2', '26.1.x', '26.2', '26.2.2', '26.2.5', '26.2.5.2', '26.2.5.8', '26.x', '27', '27.0', '27.0.1', '27.1', '27.2', '27.2.1', '27.2.2', '27.2.4', '27.3', '27.3.4', '27.3.4.11', '27.3.4.6', '27.x', '28', '28.0', '28.1', '28.1.1', '28.2', '28.3', '28.3.1', '28.4.1', '28.5', '28.x', '29', '29.0', '29.0.1', '29.0.2', '29.0.6', '29.1.1', '29.x', '> 0', 'latest', 'maint-28', 'maint-29', 'master']  # otp-version values in the October 13 sample
HANDPICKED = ['21.3', '24.3', '25', '25.3', '25.3.2.7', '26', '26.0-rc3', '26.2.3', '26.x', '27.0', '27.3.4.3', '28', 'OTP-25.0', 'latest', 'maint-27', 'master', '~> 26.2']

specs = set(SEEN) | set(HANDPICKED)
for k in keys:
    bare = k[4:] if k.startswith("OTP-") else k
    specs |= {k, bare, "v" + bare, "OTP-v" + bare, bare + ".0", bare + ".x"}
    parts = bare.split("-")[0].split(".")
    for n in range(1, len(parts) + 1):
        specs.add(".".join(parts[:n]))
for major in range(17, 32):
    for tail in ("", ".x", ".x.x", ".*", ".0", ".1", ".2", ".3", ".0.0", ".3.4", ".2.5", ".0-rc1", ".0-rc3",
                 ".0-rc.1", ".0.0-rc1", "-rc1", ".1.1", ".99", ".3.4.17", ".3.2.21", ".2.5.21", ".3.4.18"):
        specs.add(f"{major}{tail}")
    for op in ("^", "~", "~>", "~> ", ">=", ">", "<", "<=", "=", ">= ", "< "):
        for tail in ("", ".0", ".2", ".3.4", ".x"):
            specs.add(f"{op}{major}{tail}")
    specs |= {f"{major} - {major + 1}", f"{major}.1 - {major}.3", f">={major} <{major + 2}",
              f"{major} || {major + 2}", f"^{major} || ~{major + 1}.1", f">{major}.x <={major + 2}.x",
              f"{major}.0.0 - {major}.x", f"<{major}.0.0-0", f"maint-{major}", f"OTP-{major}",
              f"OTP-{major}.x", f"v{major}.x", f"{major}.0.0+build", f"0{major}", f"{major}.01",
              f"{major}.3.4.17.1", f"{major}.3.4.17.1.2", f"{major}.x.x.x"}
specs |= {"latest", "nightly", "main", "master", "maint", "*", "x", "X", "", " ", "26.0-rc", "foo",
          "otp-25", "OTP25", "25-otp", "a25", "b26", "v", "vv25", "=25", "==25", "25 26", ">= 0.0.0",
          ">=0.0.0", "<0.0.0", "||", "25 ||", "|| 26", "~", "^", "-", "26.0-rc1 || 27", "1.2.3 - 2",
          "<=25.3.2.21", ">25.3.2.20", "25.3.2.2", "24.3.4.1", "24.3.4.10", "domain", "maintenance",
          "27.3.4.3", "25.3.2.7", "latest-27", "26.x || 27.x", "~25.3.2.21", "^25.3.2.21", "26.2.x",
          "27.0-rc3 - 27", "*.x", "x.25", "25.3.x.1", "v1", "1.0.0", "0", "0.0.0", "1"}
rnd = random.Random(20261013)
atoms = sorted(specs)
for _ in range(1500):
    a, b = rnd.choice(atoms), rnd.choice(atoms)
    specs.add(rnd.choice([f"{a} || {b}", f"{a} {b}", f"{a} - {b}", f">={a}", f"~{a}", f"^{a}"]).strip())

with open(os.path.join(HERE, "specs.jsonl"), "w") as f:
    for s in sorted(specs):
        for strict in (False, True):
            f.write(json.dumps({"spec": s, "strict": strict}) + "\n")
print(len(specs), "specs,", 2 * len(specs), "lines")
