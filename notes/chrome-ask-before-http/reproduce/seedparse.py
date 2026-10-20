"""Decode the ask-before-HTTP study from a Chrome variations seed (VariationsSeed protobuf; field numbers from
Chromium components/variations/proto/study.proto). Fetch a seed with:
  curl -o seed.bin 'https://clientservices.googleapis.com/chrome-variations/seed?osname=win&channel=stable&milestone=155'
Usage: python3 -I seedparse.py seed.bin [...]"""
import sys
CHANNEL = {0: 'CANARY', 1: 'DEV', 2: 'BETA', 3: 'STABLE'}
PLATFORM = {0: 'WINDOWS', 1: 'MAC', 2: 'LINUX', 3: 'CHROMEOS', 4: 'ANDROID', 5: 'IOS'}
def varint(b, i):
    r = s = 0
    while True:
        c = b[i]; i += 1; r |= (c & 0x7f) << s; s += 7
        if c < 0x80: return r, i
def fields(b):
    i, out = 0, []
    while i < len(b):
        k, i = varint(b, i); f, t = k >> 3, k & 7
        if t == 0: v, i = varint(b, i)
        elif t == 2: n, i = varint(b, i); v = b[i:i + n]; i += n
        elif t == 1: v = b[i:i + 8]; i += 8
        elif t == 5: v = b[i:i + 4]; i += 4
        else: raise ValueError(f'wire type {t}')
        out.append((f, t, v))
    return out
def studies(path, needle=b'HttpsFirstBalancedModeAutoEnable'):
    """Yield {name, groups: [(name, weight, enabled_features)], min, max, channels, platforms, other_filter_fields} per matching study."""
    for f, t, v in fields(open(path, 'rb').read()):
        if f != 2 or t != 2 or needle not in v: continue   # VariationsSeed.study = 2
        s = {'name': '', 'groups': [], 'min': None, 'max': None, 'channels': [], 'platforms': [], 'other_filter_fields': []}
        for sf, st, sv in fields(v):
            if sf == 1: s['name'] = sv.decode()                     # Study.name
            elif sf == 9:                                            # Study.experiment
                g = {a: c for a, d, c in fields(sv) if a in (1, 2)}
                feats = [fc.decode() for a, d, c in fields(sv) if a == 12 for fa, fd, fc in fields(c) if fa == 1]
                s['groups'].append((g[1].decode(), g.get(2, 0), feats))
            elif sf == 10:                                           # Study.filter
                for a, d, c in fields(sv):
                    if a == 2: s['min'] = c.decode()
                    elif a == 3: s['max'] = c.decode()
                    elif a == 4: s['channels'].append(CHANNEL.get(c, c))
                    elif a == 5: s['platforms'].append(PLATFORM.get(c, c))
                    else: s['other_filter_fields'].append(a)  # country, locale, form factor, ... (none = applies to all)
        yield s
if __name__ == '__main__':
    for p in sys.argv[1:]:
        for s in studies(p): print(p, s)
