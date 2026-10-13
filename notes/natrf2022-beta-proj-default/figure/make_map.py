"""Draw the gap map: bare PROJ 9.9.0 cs2cs vs NCAT at the 230 points.

Standard library only. Reads ../out/results.json (per_point A1, the bare
`cs2cs EPSG:6318 EPSG:10968` gap in metres), ../data/frame.json (point
coordinates) and the U.S. Census Bureau 2025 cartographic boundary file
cb_2025_us_state_20m.zip in this directory. Writes natrf2022-gap-map.svg,
then re-reads that SVG and asserts that every plotted value equals
results.json and that every point sits where frame.json puts it.

    python3 -I make_map.py            # SVG + assertion
    python3 -I make_map.py --png      # also natrf2022-gap-map.png (headless Chrome, Pillow)

Projections: Albers equal-area conic on GRS80, EPSG:5070 parameters for the
lower 48 and EPSG:3338 parameters for Alaska. Both are drawn at the same scale.
"""

import json
import math
import struct
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
NOTE = HERE.parent
SVG_OUT = HERE / "natrf2022-gap-map.svg"
PNG_OUT = HERE / "natrf2022-gap-map.png"
BOUNDARIES = HERE / "cb_2025_us_state_20m.zip"
BOUNDARIES_SHA256 = "9340b6d995e971b2b4230518f4fa85e6cd9e7fe6811afabc90a6a8b1191530f6"

# Classes in metres, lower bound inclusive. Colours are one hue (OKLCH h=258)
# stepped evenly in lightness; dot size repeats the class so colour is not the
# only channel.
BREAKS = [0.12, 0.15, 0.18, 0.30, 0.60]
LABELS = ["0.09–0.12", "0.12–0.15", "0.15–0.18",
          "0.18–0.30", "0.30–0.60", "0.60 and over"]
COLOURS = ["#7facf0", "#528de4", "#2d6fcd", "#1553a8", "#073a7d", "#012352"]
RADII = [4.0, 4.5, 5.0, 7.0, 9.5, 12.5]
RING = 0.75  # half the white stroke between overlapping dots

LAND = "#ebe9e3"
BORDER = "#ffffff"
INK = "#16181d"
INK_2 = "#4b4f58"
INK_3 = "#7a7e86"
FONT = "Helvetica, Arial, 'Liberation Sans', sans-serif"

WIDTH = 760
MARGIN = 28
SCALE = (WIDTH - 2 * MARGIN) / 4_640_000  # SVG units per metre, both maps

TITLE = "Bare PROJ 9.9.0 cs2cs vs NGS’s NCAT beta"
SUBTITLE = "Horizontal gap at 230 US county points, October 13, 2026"
CAPTION = [
    "Bare cs2cs EPSG:6318 EPSG:10968 vs NCAT.",
    "Every point was more than 5 cm from NCAT.",
    "The points are Census county internal points, not survey marks.",
    "Distances are horizontal on the GRS80 ellipsoid.",
    "NCAT and its grids are beta and may change. These numbers",
    "describe their behaviour on October 13, 2026.",
]
CREDIT = [
    "Data: out/results.json in this directory. CyberNative AI LLC.",
    "Boundaries: U.S. Census Bureau, 2025 cartographic boundary file, 1:20,000,000.",
]
ALT = ("Map of the lower 48 states with Alaska below it at the same scale. Each of the "
       "230 county points is a dot whose colour and size show the horizontal gap between "
       "bare PROJ 9.9.0 cs2cs and NCAT. East of 104\u00b0 W the gap was 9 to 18 cm. "
       "West of 104\u00b0 W it was 10 to 43 cm, with the largest in San Diego County "
       "(0.428 m). In Alaska it was 14 cm to 0.92 m, with the largest in the Copper River "
       "Census Area (0.921 m). Every point was more than 5 cm from NCAT.")

# ---------------------------------------------------------------- projection
A = 6378137.0
F = 1 / 298.257222101
E2 = F * (2 - F)
E = math.sqrt(E2)


def _q(phi):
    s = math.sin(phi)
    return (1 - E2) * (s / (1 - E2 * s * s) - (1 / (2 * E)) * math.log((1 - E * s) / (1 + E * s)))


def _m(phi):
    s = math.sin(phi)
    return math.cos(phi) / math.sqrt(1 - E2 * s * s)


def albers(lat1, lat2, lat0, lon0):
    p1, p2, p0 = (math.radians(v) for v in (lat1, lat2, lat0))
    m1, m2 = _m(p1), _m(p2)
    q1, q2, q0 = _q(p1), _q(p2), _q(p0)
    n = (m1 * m1 - m2 * m2) / (q2 - q1)
    c = m1 * m1 + n * q1
    rho0 = A * math.sqrt(c - n * q0) / n

    def fwd(lat, lon):
        d = (lon - lon0 + 180) % 360 - 180  # Aleutians cross 180 degrees
        rho = A * math.sqrt(c - n * _q(math.radians(lat))) / n
        theta = n * math.radians(d)
        return rho * math.sin(theta), rho0 - rho * math.cos(theta)

    return fwd


CONUS = albers(29.5, 45.5, 23.0, -96.0)   # EPSG:5070
ALASKA = albers(55.0, 65.0, 50.0, -154.0)  # EPSG:3338

# ---------------------------------------------------------------- shapefile


def read_states(path):
    import hashlib
    raw = path.read_bytes()
    assert hashlib.sha256(raw).hexdigest() == BOUNDARIES_SHA256, "boundary file hash changed"
    with zipfile.ZipFile(path) as z:
        shp = z.read("cb_2025_us_state_20m.shp")
        dbf = z.read("cb_2025_us_state_20m.dbf")
    # dbf: header, field descriptors, then fixed-width records
    nrec, hlen, rlen = struct.unpack("<IHH", dbf[4:12])
    fields, off = [], 32
    while dbf[off] != 0x0D:
        name = dbf[off:off + 11].split(b"\0")[0].decode()
        fields.append((name, dbf[off + 16]))
        off += 32
    rows = []
    for i in range(nrec):
        rec, pos, row = dbf[hlen + i * rlen: hlen + (i + 1) * rlen], 1, {}
        for name, size in fields:
            row[name] = rec[pos:pos + size].decode("latin-1").strip()
            pos += size
        rows.append(row)
    # shp: polygon records (type 5)
    shapes, off = [], 100
    while off < len(shp):
        _, clen = struct.unpack(">II", shp[off:off + 8])
        body = shp[off + 8: off + 8 + clen * 2]
        stype = struct.unpack("<i", body[:4])[0]
        assert stype == 5, stype
        nparts, npts = struct.unpack("<ii", body[36:44])
        parts = list(struct.unpack("<%di" % nparts, body[44:44 + 4 * nparts])) + [npts]
        pts = struct.unpack("<%dd" % (2 * npts), body[44 + 4 * nparts: 44 + 4 * nparts + 16 * npts])
        rings = [[(pts[2 * k], pts[2 * k + 1]) for k in range(parts[j], parts[j + 1])]
                 for j in range(nparts)]
        shapes.append(rings)
        off += 8 + clen * 2
    assert len(shapes) == len(rows)
    return {row["STUSPS"]: rings for row, rings in zip(rows, shapes)}

# ---------------------------------------------------------------- geometry


def klass(v):
    for i, b in enumerate(BREAKS):
        if v < b:
            return i
    return len(BREAKS)


def project_rings(rings, proj, ox, oy):
    out = []
    for ring in rings:
        pts = []
        for lon, lat in ring:
            x, y = proj(lat, lon)
            pts.append((ox + x * SCALE, oy - y * SCALE))
        out.append(pts)
    return out


def path_d(rings):
    parts = []
    for ring in rings:
        kept = [ring[0]]
        for p in ring[1:]:
            if abs(p[0] - kept[-1][0]) + abs(p[1] - kept[-1][1]) >= 0.5:
                kept.append(p)
        if len(kept) < 3:
            continue
        parts.append("M" + " ".join("%.1f %.1f" % p for p in kept) + "Z")
    return "".join(parts)


def bbox(rings_list):
    xs = [p[0] for rings in rings_list for r in rings for p in r]
    ys = [p[1] for rings in rings_list for r in rings for p in r]
    return min(xs), min(ys), max(xs), max(ys)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def text(x, y, s, size, fill=INK, weight=400, anchor="start", extra=""):
    return ('<text x="%.1f" y="%.1f" font-size="%s" fill="%s" font-weight="%d" '
            'text-anchor="%s"%s>%s</text>' % (x, y, size, fill, weight, anchor, extra, esc(s)))

# ---------------------------------------------------------------- build


def build():
    results = json.loads((NOTE / "out" / "results.json").read_text(encoding="utf-8"))
    per_point = results["per_point"]
    frame = {p["id"]: p for p in json.loads((NOTE / "data" / "frame.json").read_text(encoding="utf-8"))}
    assert set(per_point) == set(frame) and len(frame) == 230
    states = read_states(BOUNDARIES)
    lower48 = [k for k in states if k not in ("AK", "HI", "PR")]
    assert len(lower48) == 49  # 48 states + DC

    # Lower 48 placement: projected bbox -> canvas
    raw48 = {k: project_rings(states[k], CONUS, 0, 0) for k in lower48}
    x0, y0, x1, y1 = bbox(raw48.values())
    top = 122
    ox48, oy48 = MARGIN - x0, top - y0
    map48 = {k: [[(x + ox48, y + oy48) for x, y in r] for r in rings] for k, rings in raw48.items()}
    b48 = bbox(map48.values())

    # Alaska at the same scale, tucked under the south-west of the lower 48
    rawak = project_rings(states["AK"], ALASKA, 0, 0)
    ax0, ay0, ax1, ay1 = bbox([rawak])
    oxak = MARGIN - ax0
    col = {}
    for rings in map48.values():
        for r in rings:
            for x, y in r:
                c = int(x // 4)
                col[c] = max(col.get(c, -1e9), y)
    need = -1e9
    for r in rawak:
        for x, y in r:
            c = int((x + oxak) // 4)
            for cc in (c - 1, c, c + 1):
                if cc in col:
                    need = max(need, col[cc] - y)
    oyak = need + 46
    mapak = [[(x + oxak, y + oyak) for x, y in r] for r in rawak]
    bak = bbox([mapak])

    def place(pid):
        p = frame[pid]
        if p["stratum"] == "AK":
            x, y = ALASKA(p["lat"], p["lon"])
            return oxak + x * SCALE, oyak - y * SCALE
        x, y = CONUS(p["lat"], p["lon"])
        return ox48 + x * SCALE, oy48 - y * SCALE

    legend_x = MARGIN
    legend_y = bak[1] + 30
    caption_y = max(bak[3] + 20, legend_y + 56 + 5 * 29 + 20) + 56
    height = math.ceil(caption_y + (len(CAPTION) - 1) * 29 + 26 + len(CREDIT) * 22 + 26)

    out = []
    out.append('<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
               'role="img" aria-labelledby="t d" font-family="%s">' % (WIDTH, height, WIDTH, height, FONT))
    out.append('<title id="t">%s</title><desc id="d">%s</desc>' % (esc(TITLE), esc(ALT)))
    out.append('<rect width="100%" height="100%" fill="#ffffff"/>')
    out.append(text(MARGIN, 50, TITLE, 31, weight=700))
    out.append(text(MARGIN, 84, SUBTITLE, 21, fill=INK_2))

    out.append('<g fill="%s" stroke="%s" stroke-width="1" stroke-linejoin="round">' % (LAND, BORDER))
    for k in sorted(map48):
        out.append('<path d="%s"/>' % path_d(map48[k]))
    out.append('<path d="%s"/>' % path_d(mapak))
    out.append("</g>")

    # 104 W, the note's east/west split, drawn across the lower 48
    m_top = CONUS(49.0, -104.0)
    m_bot = CONUS(31.33, -104.0)
    mx0, my0 = ox48 + m_top[0] * SCALE, oy48 - m_top[1] * SCALE
    mx1, my1 = ox48 + m_bot[0] * SCALE, oy48 - m_bot[1] * SCALE
    out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.5" '
               'stroke-dasharray="4 4"/>' % (mx0, my0 - 10, mx1, my1, INK_3))
    out.append(text(mx0, my0 - 17, "104\u00b0 W", 19, fill=INK_2, anchor="middle"))

    # points: smaller gaps first so the largest stay on top
    order = sorted(per_point, key=lambda k: (per_point[k]["A1"], k))
    out.append('<g stroke="#ffffff" stroke-width="1.5">')
    for pid in order:
        v = per_point[pid]["A1"]
        c = klass(v)
        x, y = place(pid)
        out.append('<circle data-id="%s" data-gap="%r" cx="%.2f" cy="%.2f" r="%s" fill="%s"/>'
                   % (pid, v, x, y, RADII[c], COLOURS[c]))
    out.append("</g>")

    # selective direct labels: the two maxima the note names (values as printed in its table)
    x, y = place("06073")
    out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.2"/>'
               % (x, y + 13, x, y + 50, INK_2))
    out.append(text(MARGIN, y + 72, "San Diego County, CA", 20, weight=700))
    out.append(text(MARGIN, y + 96, "0.428 m", 20))
    x, y = place("02066")
    out.append('<line x1="%.1f" y1="%.1f" x2="%.1f" y2="%.1f" stroke="%s" stroke-width="1.2"/>'
               % (x + 16, y - 6, x + 34, y - 6, INK_2))
    out.append(text(x + 40, y - 12, "Copper River Census Area", 20, weight=700))
    out.append(text(x + 40, y + 12, "0.921 m", 20))

    ne = ALASKA(69.6, -141.0)
    out.append(text(oxak + ne[0] * SCALE + 14, oyak - ne[1] * SCALE + 30, "Alaska,", 20, fill=INK_2, weight=700))
    out.append(text(oxak + ne[0] * SCALE + 14, oyak - ne[1] * SCALE + 54, "same scale", 20, fill=INK_2, weight=700))

    # legend, in the empty Bering Sea corner
    out.append(text(legend_x, legend_y, "Gap from NCAT", 21, weight=700))
    out.append(text(legend_x, legend_y + 25, "metres", 20, fill=INK_2))
    for i, lab in enumerate(LABELS):
        yy = legend_y + 56 + i * 29
        out.append('<circle cx="%.1f" cy="%.1f" r="%s" fill="%s"/>'
                   % (legend_x + 13, yy, RADII[i], COLOURS[i]))
        out.append(text(legend_x + 34, yy + 7, lab, 20))

    # caption: sentences from the note, then the credit
    y = caption_y
    out.append('<line x1="%d" y1="%.1f" x2="%d" y2="%.1f" stroke="#d9d7d0" stroke-width="1"/>'
               % (MARGIN, y - 32, WIDTH - MARGIN, y - 32))
    for line in CAPTION:
        out.append(text(MARGIN, y, line, 21, fill=INK_2))
        y += 29
    y += 4
    for line in CREDIT:
        out.append(text(MARGIN, y, line, 16, fill=INK_3))
        y += 22
    out.append("</svg>\n")
    SVG_OUT.write_text("\n".join(out), encoding="utf-8")
    return per_point, frame, place, height


def check(per_point, frame, place):
    root = ET.parse(SVG_OUT).getroot()
    ns = "{http://www.w3.org/2000/svg}"
    dots = [c for c in root.iter(ns + "circle") if "data-id" in c.attrib]
    ids = [c.get("data-id") for c in dots]
    assert len(ids) == len(set(ids)) == len(per_point) == 230, len(ids)
    assert set(ids) == set(per_point)
    worst = 0.0
    for c in dots:
        pid = c.get("data-id")
        v = float(c.get("data-gap"))
        assert v == per_point[pid]["A1"], (pid, v, per_point[pid]["A1"])
        k = klass(v)
        assert c.get("fill") == COLOURS[k] and float(c.get("r")) == RADII[k], pid
        assert per_point[pid]["lon"] == frame[pid]["lon"] and per_point[pid]["stratum"] == frame[pid]["stratum"]
        x, y = place(pid)
        worst = max(worst, abs(float(c.get("cx")) - x), abs(float(c.get("cy")) - y))
    assert worst <= 0.005, worst
    # every dot stays at least 30% visible under the dots drawn after it
    disc = [(float(c.get("cx")), float(c.get("cy")), float(c.get("r"))) for c in dots]
    least = 1.0
    for i, (x, y, r) in enumerate(disc):
        tot = vis = 0
        for a in range(-20, 21):
            for b in range(-20, 21):
                px, py = x + r * a / 20, y + r * b / 20
                if (px - x) ** 2 + (py - y) ** 2 > r * r:
                    continue
                tot += 1
                vis += not any((px - ox) ** 2 + (py - oy) ** 2 < (orr + RING) ** 2
                               for ox, oy, orr in disc[i + 1:])
        least = min(least, vis / tot)
    assert least >= 0.30, least
    strata = {}
    for pid in ids:
        strata[per_point[pid]["stratum"]] = strata.get(per_point[pid]["stratum"], 0) + 1
    vals = [per_point[p]["A1"] for p in ids]
    assert min(vals) >= 0.09  # first legend label starts at 0.09
    counts = [0] * len(COLOURS)
    for v in vals:
        counts[klass(v)] += 1
    print("plotted points: %d (%s)" % (len(ids), ", ".join("%s %d" % kv for kv in sorted(strata.items()))))
    print("every data-gap == results.json per_point[id].A1 exactly: yes (230/230)")
    print("every fill/radius matches its class: yes; position error max %.4f units" % worst)
    print("least visible dot: %.0f%% of its area (drawn in order of gap, largest on top)" % (100 * least))
    print("plotted min %.6f m, max %.6f m; class counts %s" % (min(vals), max(vals), counts))


def png(height):
    chrome = "google-chrome"
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "page.html"
        page.write_text('<!doctype html><html><body style="margin:0">%s</body></html>'
                        % SVG_OUT.read_text(encoding="utf-8"), encoding="utf-8")
        subprocess.run([chrome, "--headless", "--disable-gpu", "--hide-scrollbars",
                        "--force-device-scale-factor=2", "--user-data-dir=" + tmp,
                        "--window-size=%d,%d" % (WIDTH, math.ceil(height)),
                        "--screenshot=" + str(PNG_OUT), page.as_uri()],
                       check=True, shell=False, capture_output=True)
    # Size step (Pillow): map every pixel to the nearest of the 256 most frequent
    # rendered colours, no dithering. Frequent colours (background, land, ink and
    # all six class colours) map to themselves exactly.
    from PIL import Image
    im = Image.open(PNG_OUT).convert("RGB")
    common = [rgb for _, rgb in sorted(im.getcolors(maxcolors=1 << 22), reverse=True)[:256]]
    index = {}
    for _, rgb in im.getcolors(maxcolors=1 << 22):
        index[rgb] = min(range(len(common)),
                         key=lambda i: sum((a - b) ** 2 for a, b in zip(rgb, common[i])))
    raw = im.tobytes()
    out = Image.frombytes("P", im.size, bytes(index[(raw[i], raw[i + 1], raw[i + 2])]
                                              for i in range(0, len(raw), 3)))
    out.putpalette([v for rgb in common for v in rgb])
    out.save(PNG_OUT, optimize=True)
    im = Image.open(PNG_OUT).convert("RGB")
    assert im.getpixel((2, 2)) == (255, 255, 255)
    dots = [c for c in ET.parse(SVG_OUT).getroot().iter("{http://www.w3.org/2000/svg}circle")
            if "data-id" in c.attrib]
    checked = 0
    for i, c in enumerate(dots):
        x, y = float(c.get("cx")), float(c.get("cy"))
        if any(math.hypot(float(o.get("cx")) - x, float(o.get("cy")) - y) < float(o.get("r")) + RING + 1
               for o in dots[i + 1:]):
            continue  # centre under a later (larger-gap) dot
        want = tuple(int(c.get("fill")[k:k + 2], 16) for k in (1, 3, 5))
        assert im.getpixel((round(2 * x), round(2 * y))) == want, c.get("data-id")
        checked += 1
    print("PNG %dx%d: %d uncovered dot centres carry their exact class colour" % (im.size + (checked,)))


if __name__ == "__main__":
    per_point, frame, place, height = build()
    check(per_point, frame, place)
    if "--png" in sys.argv[1:]:
        png(height)
        print("wrote", PNG_OUT.name)
    print("wrote", SVG_OUT.name)
