"""Scorer: magenta pixel counts from the saved PNGs (stdlib PNG decode) + exceptions/console -> cell outcome.
usage: python3 -I score.py OUTDIR [OUTDIR ...] > score.json   (prints a table to stderr)"""
import json, struct, sys, zlib, glob, os, collections

def png_pixels(path):
    b = open(path, 'rb').read()
    assert b[:8] == b'\x89PNG\r\n\x1a\n', path
    i, idat, w = 8, b'', None
    while i < len(b):
        n, t = struct.unpack('>I4s', b[i:i + 8]); d = b[i + 8:i + 8 + n]; i += 12 + n
        if t == b'IHDR':
            w, h, depth, ctype, _, _, inter = struct.unpack('>IIBBBBB', d)
            assert depth == 8 and ctype in (2, 6) and inter == 0, (path, depth, ctype, inter)
            bpp = 3 if ctype == 2 else 4
        elif t == b'IDAT': idat += d
    raw = zlib.decompress(idat); stride = w * bpp; prev = bytearray(stride); out = []; o = 0
    for _ in range(h):
        f = raw[o]; line = bytearray(raw[o + 1:o + 1 + stride]); o += 1 + stride
        for x in range(stride):
            a = line[x - bpp] if x >= bpp else 0; up = prev[x]; c = prev[x - bpp] if x >= bpp else 0
            if f == 1: line[x] = (line[x] + a) & 255
            elif f == 2: line[x] = (line[x] + up) & 255
            elif f == 3: line[x] = (line[x] + ((a + up) >> 1)) & 255
            elif f == 4:
                p = a + up - c; pa, pb, pc = abs(p - a), abs(p - up), abs(p - c)
                line[x] = (line[x] + (a if pa <= pb and pa <= pc else up if pb <= pc else c)) & 255
        out.append(bytes(line)); prev = line
    return w, h, bpp, out

def n_magenta(path):
    w, h, bpp, rows = png_pixels(path)
    n = 0
    for r in rows:
        for x in range(0, w * bpp, bpp):
            if r[x] >= 180 and r[x + 1] <= 90 and r[x + 2] >= 180: n += 1
    return n, w * h

def classify(rec, shots_dir):
    if rec.get('error'): return {'outcome': 'RUN_ERROR', 'n_mag': None}
    counts = [n_magenta(os.path.join(shots_dir, s['file'])) for s in rec['shots']]
    n = max(c[0] for c in counts)
    loud = bool(rec['exceptions']) or any(c['type'] in ('error', 'assert') for c in rec['console']) or any(l['level'] == 'error' for l in rec['log'])
    pr = rec.get('probe') or {}
    if rec['page'] in ('K3', 'NGPU', 'BGPU') and pr.get('gpu_adapter') is False:
        out = 'NA'
    elif n >= 4000: out = 'RENDERS'
    elif n < 400: out = 'BLANK_LOUD' if loud else 'BLANK_SILENT'
    else: out = 'PARTIAL'
    if out == 'RENDERS' and rec['page'] in ('BJS', 'BJSN'):
        warn = ' '.join(c['text'] for c in rec['console'])
        if 'is not available' in warn: out = 'RENDERS_FALLBACK'
    return {'outcome': out, 'n_mag': n, 'n_mag_by_shot': [c[0] for c in counts], 'area': counts[0][1], 'loud': loud}

def main():
    cells = collections.defaultdict(list); rows = []
    for d in sys.argv[1:]:
        for f in sorted(glob.glob(os.path.join(d, '*.jsonl'))):
            for line in open(f):
                rec = json.loads(line); c = classify(rec, d)
                row = {'dir': os.path.basename(os.path.normpath(d)), 'arm': rec['arm'], 'page': rec['page'], 'rep': rec['rep'], 'browser': rec.get('browser'), **c,
                       'exceptions': rec['exceptions'], 'console': rec['console'], 'log': rec['log'], 'probe': rec.get('probe')}
                rows.append(row); cells[(rec['page'], rec['arm'])].append(c['outcome'])
    cell = {f'{p}|{a}': (v[0] if len(set(v)) == 1 else 'UNSTABLE:' + '/'.join(v)) for (p, a), v in cells.items()}
    json.dump({'cells': cell, 'rows': rows}, sys.stdout, indent=1, sort_keys=True)
    arms = [a for a in ['C156', 'C156OT', 'C157', 'C158'] if any(k[1] == a for k in cells)]
    pages = sorted({k[0] for k in cells}, key=lambda p: (['K', 'N', 'B', 'T', 'P'].index(p[0]) if p[0] in 'KNBTP' else 9, p))
    print('page   ' + ''.join(f'{a:>18}' for a in arms), file=sys.stderr)
    for p in pages: print(f'{p:6} ' + ''.join(f"{cell.get(f'{p}|{a}', '-'):>18}" for a in arms), file=sys.stderr)

if __name__ == '__main__':
    main()
