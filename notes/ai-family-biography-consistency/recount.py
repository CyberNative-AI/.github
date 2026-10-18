"""Recount every figure in the note from posts.csv and items.csv in this folder.

Usage: python3 recount.py
Standard library only; no network.
"""
import csv
from collections import Counter
from math import sqrt
from pathlib import Path

here = Path(__file__).parent
posts = list(csv.DictReader(open(here / "posts.csv", encoding="utf-8")))
items = list(csv.DictReader(open(here / "items.csv", encoding="utf-8")))


def wilson(k, n, z=1.96):
    p = k / n
    mid = (p + z * z / (2 * n)) / (1 + z * z / n)
    half = z * sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)
    return f"{k}/{n} = {100 * p:.0f}% (95% Wilson CI {100 * (mid - half):.0f}-{100 * (mid + half):.0f}%)"


yes = lambda rows, col: sum(r[col] == "yes" for r in rows)
real = [r for r in items if r["real_contradiction"] == "yes"]
intro = [r for r in real if r["source"].startswith("introduced")]
rejected = [r for r in items if r["real_contradiction"] == "no"]
judged = [p for p in posts if p["notes_have_own_conflict"] != "not judged"]
matched = [p for p in posts if p["notes_match_post"] != "no"]
hit = {r["post"] for r in intro}

print("posts", len(posts))
print("biography has an introduced contradiction:", wilson(yes(posts, "biography_has_introduced"), len(posts)))
print("... a material one:", wilson(yes(posts, "biography_has_introduced_material"), len(posts)))
print("without the post whose notes match no part of it:",
      f"{yes(matched, 'biography_has_introduced')}/{len(matched)}")
print(f"flagged biography items {len(items)}: real {len(real)} (introduced {len(intro)}, "
      f"copied from notes {len(real) - len(intro)}), not upheld {len(rejected)}")
print("checking-pass precision:", f"{len(real)}/{len(items)} = {100 * len(real) / len(items):.0f}%")
print("introduced, by kind:", dict(Counter(r["kind"] for r in intro).most_common()))
print("plain request found:", f"{yes(intro, 'plain_request_found')}/{len(intro)} items,",
      f"{len({r['post'] for r in intro if r['plain_request_found'] == 'yes'})}/{len(hit)} posts")
print("missed:", [r["quote_1"] for r in intro if r["plain_request_found"] == "no"])
print("notes with their own conflict:", f"{yes(judged, 'notes_have_own_conflict')}/{len(judged)} judged")
by_model = Counter(p["biography_model"] for p in posts)
print("by model:", {m: f"{yes([p for p in posts if p['biography_model'] == m], 'biography_has_introduced')}/{n}"
                    for m, n in sorted(by_model.items())})
census = [r for r in rejected if any(w in r["reviewer_note"].lower() for w in ("census", "ship list", "record"))]
print(f"not upheld that restate a census or passenger-list record: {len(census)}/{len(rejected)},",
      f"most from one post: {Counter(r['post'] for r in census).most_common(1)}")
print("longest excerpt:", max(len(r[q].split()) for r in items for q in ("quote_1", "quote_2")), "words")
