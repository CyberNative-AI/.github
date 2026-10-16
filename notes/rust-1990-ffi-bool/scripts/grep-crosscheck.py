# Independent check of scripts/find-bool-exports.sh: finds the same signatures by matching
# brackets instead of a regular expression. Usage: python3 scripts/grep-crosscheck.py DIR
import re, sys, pathlib
ABIS = {None, "C", "system", "sysv64", "C-unwind", "system-unwind", "sysv64-unwind"}
def strip_comments(s):
    s = re.sub(r'/\*.*?\*/', lambda m: re.sub(r'[^\n]', ' ', m.group()), s, flags=re.S)
    return re.sub(r'(?m)//.*$', lambda m: ' ' * len(m.group()), s)
def scan(path):
    s = strip_comments(path.read_text(errors="replace"))
    out = []
    for m in re.finditer(r'\bextern\b', s):
        i = m.end(); rest = s[i:]
        am = re.match(r'\s*(?:"([^"]*)")?\s*fn\b', rest)
        if not am: continue
        abi = am.group(1)
        if abi not in ABIS: continue
        j = i + am.end()
        nm = re.match(r'\s*\w*\s*', s[j:]); j += nm.end()
        if s[j] == '<':
            d = 0
            while True:
                d += {'<': 1, '>': -1}.get(s[j], 0); j += 1
                if d == 0: break
            j += len(re.match(r'\s*', s[j:]).group())
        if s[j] != '(': continue
        d = 0
        while True:
            d += {'(': 1, ')': -1}.get(s[j], 0); j += 1
            if d == 0: break
        rm = re.match(r'\s*->\s*', s[j:])
        if not rm: continue
        k = j + rm.end(); d = 0; t = ''
        while k < len(s):
            c = s[k]
            if d == 0 and (c in '{;,)' or s.startswith('where', k)): break
            d += {'<': 1, '(': 1, '[': 1, '>': -1, ')': -1, ']': -1}.get(c, 0); t += c; k += 1
        if t.strip() == 'bool':
            out.append((str(path), s.count('\n', 0, m.start()) + 1))
    return out
root = pathlib.Path(sys.argv[1])
for p in sorted(root.rglob('*.rs')):
    for f, l in scan(p): print(f"{f}:{l}")
