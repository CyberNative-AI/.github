"""Check every downloaded input against inputs.sha256. usage: check_inputs.py SUMS DIR..."""
import hashlib, sys
from pathlib import Path
sums = {}
for line in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines():
    if line.strip():
        h, name = line.split(maxsplit=1)
        sums[name.strip()] = h
found, bad = 0, []
for d in map(Path, sys.argv[2:]):
    for p in sorted(d.iterdir()):
        if p.name in sums:
            found += 1
            got = hashlib.sha256(p.read_bytes()).hexdigest()
            if got != sums[p.name]:
                bad.append(p.name)
print(f'{found} of {len(sums)} inputs found, {len(bad)} mismatched {bad}')
sys.exit(1 if bad or found != len(sums) else 0)
