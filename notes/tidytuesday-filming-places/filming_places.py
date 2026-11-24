"""Plot the Nov 24, 2026 TidyTuesday filming locations release.

Run with Python 3.11+ and matplotlib 3.10.8. Keep style/ alongside
this file. Pass --data to read the three released CSVs from a local folder.
"""

import argparse
import csv
import io
import json
import os
from collections import Counter
from pathlib import Path
from urllib.request import urlopen

os.environ.setdefault("MPLBACKEND", "Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import Rectangle

PIN = "4a0165750d641152637f067e8f14856b366c048a"
SOURCE = f"https://raw.githubusercontent.com/rfordatascience/tidytuesday/{PIN}/data/2026/2026-11-24"
KIT = Path(__file__).resolve().parent / "style"
GROUPS = {"film": "Films", "tv": "TV series"}
BINS = ("1", "2", "3–4", "5+")


def read_csv(name, data):
    if data is not None:
        raw = (data / name).read_bytes()
    else:
        with urlopen(f"{SOURCE}/{name}", timeout=30) as response:
            raw = response.read()
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"), newline="")))
    if not rows or any(None in row or None in row.values() for row in rows):
        raise ValueError(f"{name}: missing rows or irregular CSV fields")
    return rows


def distribution(productions, locations, links):
    types = {}
    for row in productions:
        title_id, kind = row["production_id"], row["kind"]
        if not title_id.strip() or not row["title"].strip() or kind not in GROUPS:
            raise ValueError(f"Missing title or unsupported type: {title_id!r}, {kind!r}")
        if title_id in types:
            problem = "Ambiguous type" if types[title_id] != kind else "Duplicate title ID"
            raise ValueError(f"{problem}: {title_id}")
        types[title_id] = kind

    place_ids = {row["location_id"] for row in locations}
    if any(not place_id.strip() for place_id in place_ids) or len(place_ids) != len(locations):
        raise ValueError("Missing or duplicate place ID")

    pairs = {(row["production_id"], row["location_id"]) for row in links}
    per_title = Counter()
    per_place = Counter()
    for title_id, place_id in pairs:
        if title_id not in types or place_id not in place_ids:
            raise ValueError(f"Missing or unknown link key: {title_id!r}, {place_id!r}")
        per_title[title_id] += 1
        per_place[place_id] += 1

    if set(per_title) != set(types):
        raise ValueError("Some titles have no valid place link")
    if any(per_title[row["production_id"]] != int(row["n_locations"]) for row in productions):
        raise ValueError("Title counts differ from the release totals")
    if any(per_place[row["location_id"]] != int(row["n_productions"]) for row in locations):
        raise ValueError("Place counts differ from the release totals")

    counts = {kind: Counter() for kind in GROUPS}
    for title_id, count in per_title.items():
        counts[types[title_id]][min(count, 5)] += 1
    bins = {
        kind: (c[1], c[2], c[3] + c[4], c[5])
        for kind, c in counts.items()
    }
    if any(sum(values) == 0 for values in bins.values()):
        raise ValueError("Both title types must be present")

    audit = {
        "productions": len(productions),
        "locations": len(locations),
        "link_rows": len(links),
        "unique_pairs": len(pairs),
        "duplicate_pairs": len(links) - len(pairs),
        "counts": {kind: dict(zip(BINS, values)) for kind, values in bins.items()},
        "blank_fields": {
            name: {key: sum(not row[key].strip() for row in rows) for key in rows[0]}
            for name, rows in (
                ("productions", productions), ("locations", locations), ("links", links)
            )
        },
    }
    return bins, audit


def percentage(count, total):
    return 100 * count / total


def render(bins, output):
    import sys

    sys.path.insert(0, str(KIT))
    import oa_chart

    sheet = oa_chart.use()
    colors = oa_chart.TOKENS["color"]
    film, series = sheet["series"][:2]
    totals = {kind: sum(counts) for kind, counts in bins.items()}
    width, height = 390, 476
    fig = plt.figure(figsize=(width / 72, height / 72), facecolor=colors["ground"], dpi=216)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set(xlim=(0, width), ylim=(height, 0))
    ax.axis("off")

    def label(x, y, value, size, color, font="DMSans-Regular", align="left"):
        face = FontProperties(fname=KIT / "fonts" / "ttf" / f"{font}.ttf", size=size)
        ax.text(x, y, value, fontproperties=face, color=color, va="center", ha=align)

    paper, blue, muted = (colors[key] for key in ("paper", "blue", "muted_on_ground"))
    ink, gray = sheet["text"], sheet["label"]
    mono = "DMMono-Medium"

    label(23, 29, "FILMING LOCATIONS IN WIKIDATA", 10.5, muted, mono)
    label(21, 59, "Most titles have one", 27, paper, "Syne-SemiBold")
    label(21, 87, "recorded place", 27, blue, "Syne-SemiBold")

    ax.add_patch(Rectangle((14, 112), 362, 274, facecolor=sheet["background"], linewidth=0))
    for x, (kind, color) in zip((25, 204), zip(GROUPS, (film, series))):
        ax.add_patch(Rectangle((x, 125), 10, 10, facecolor=color, linewidth=0))
        label(x + 16, 130, f"{GROUPS[kind]}  {totals[kind]:,}", 13, ink, "DMSans-SemiBold")

    label(25, 162, "Places", 12, gray, "DMSans-SemiBold")
    label(85, 151, "Within-group share and title count", 11, gray)
    plot_x, plot_width = 85, 169
    for tick in (0, 25, 50, 75):
        x = plot_x + plot_width * tick / 75
        ax.plot((x, x), (173, 376), color=sheet["grid"], linewidth=0.65, zorder=2)
        label(x, 165, f"{tick}%", 10.5, gray, mono, align="center")

    for index, group in enumerate(BINS):
        y = 196 + index * 50
        label(25, y + 9, group, 14, ink, mono)
        for offset, (kind, color) in enumerate(zip(GROUPS, (film, series))):
            count = bins[kind][index]
            share = percentage(count, totals[kind])
            bar_length = plot_width * share / 75
            center = y + offset * 18
            ax.add_patch(Rectangle(
                (plot_x, center - 5), bar_length, 10,
                facecolor=color, edgecolor=ink, linewidth=0.4, zorder=3,
            ))
            label(plot_x + bar_length + 6, center, f"{share:.1f}% · {count:,}", 11.5, ink, mono)

    label(23, 404, "Titles with at least one linked place.", 12, paper)
    label(23, 420, "Links describe places. Scene details and full", 12, paper)
    label(23, 435, "shooting histories are outside this dataset.", 12, paper)
    label(23, 452, "MOVIE SCENE MAP / WIKIDATA", 9.5, muted, mono)
    label(23, 465, "TIDYTUESDAY · 24 NOV 2026", 9.5, muted, mono)

    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    for item in ax.texts:
        bbox = item.get_window_extent(renderer)
        if not (fig.bbox.fully_contains(*bbox.p0) and fig.bbox.fully_contains(*bbox.p1)):
            raise ValueError(f"Label outside image: {item.get_text()}")
    with plt.rc_context({"savefig.bbox": None}):
        fig.savefig(output, facecolor=colors["ground"])
    plt.close(fig)


def describe(bins):
    lines = []
    for kind, counts in bins.items():
        total = sum(counts)
        values = ", ".join(
            f"{group}: {count:,} ({percentage(count, total):.1f}%)"
            for group, count in zip(BINS, counts)
        )
        lines.append(f"{GROUPS[kind]} ({total:,} titles) — {values}.")
    return (
        "Horizontal bars compare distinct recorded filming places per title. "
        "One place is most common in both groups. "
        + " ".join(lines)
        + " Each percentage uses titles of that type with at least one linked place. "
        "The Wikidata links describe places attached to productions. "
        "Scene details and complete shooting histories are outside these data."
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path)
    parser.add_argument("--output", type=Path, default=Path("filming-places.png"))
    args = parser.parse_args()
    bins, audit = distribution(
        read_csv("productions.csv", args.data),
        read_csv("locations.csv", args.data),
        read_csv("production_locations.csv", args.data),
    )
    render(bins, args.output)
    args.output.with_suffix(".alt.txt").write_text(describe(bins) + "\n", encoding="utf-8")
    print(json.dumps(audit, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
