"""Share of letters in the wiki's expected script, per page and arm (written after the run).

Usage: python -I src/script_share.py RUNS_JSONL OUT_JSONL
Counts alphabetic characters by the first word of their Unicode name (ORIYA, SINHALA, LATIN, ...)
in the first-run output of Indra (I) and Tesseract with tessdata_best (TB). Writes one line per
page: key, n letters, expected-script share and the two most common scripts for each arm.
"""
import json, sys, unicodedata
from collections import Counter

EXPECTED = {"ar": "ARABIC", "fa": "ARABIC", "he": "HEBREW", "th": "THAI", "bn": "BENGALI",
            "hi": "DEVANAGARI", "mr": "DEVANAGARI", "sa": "DEVANAGARI", "gu": "GUJARATI",
            "pa": "GURMUKHI", "kn": "KANNADA", "ml": "MALAYALAM", "te": "TELUGU", "ta": "TAMIL",
            "hy": "ARMENIAN", "el": "GREEK", "ru": "CYRILLIC", "uk": "CYRILLIC", "or": "ORIYA",
            "en": "LATIN", "fr": "LATIN"}


def scripts(text):
    c = Counter()
    for ch in text:
        if ch.isalpha():
            name = unicodedata.name(ch, "")
            if name:
                c[name.split()[0]] += 1
    return c


def main():
    rows = {}
    for line in open(sys.argv[1], encoding="utf-8"):
        r = json.loads(line)
        if str(r["rep"]) != "0" or r["arm"] not in ("I", "TB") or not r.get("ok"):
            continue
        c = scripts(r["text"])
        n = sum(c.values())
        row = rows.setdefault(r["key"], {"key": r["key"], "lang": r["lang"]})
        row[r["arm"]] = {"letters": n,
                         "expected_share": round(c[EXPECTED[r["lang"]]] / n, 4) if n else 0.0,
                         "top": c.most_common(2)}
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        for k in sorted(rows):
            f.write(json.dumps(rows[k], ensure_ascii=False) + "\n")


if __name__ == "__main__":
    main()
