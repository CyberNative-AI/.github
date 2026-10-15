# Amendment 02 (append-only, 2026-10-15): memory-lean comparison path for very large wikis

Reason: enwiktionary has about 11M pages per side. The frozen `load()` keeps one full dict per record for both sides, which risks exhausting the memory of one machine. This is an implementation change only. The difference definitions, classes, live confirmation, adjudication and verdict rules are unchanged.

Change (src/compare.py): when either side has more than 3,000,000 revisions, `load_lean()` makes two passes. Pass 1 keeps an 8-byte BLAKE2b hash of the compared fields (`rid`, `text_sha1`, `tdel`, all META_FIELDS) per key, with first occurrence winning as in `load()`. It also accumulates the integrity counters, duplicates and the maximum timestamp. Pass 2 loads full records only for keys whose hashes differ or that exist on one side only. `classify()` receives the wiki-wide maximum timestamps explicitly, so SNAPSHOT_LAG is computed as before.

Equivalence check, run before use, with no live calls: on elwiktionary (1.74M pages) and fiwiktionary (0.82M pages), the lean path gives the identical ordered list of (key, type, class) differences (267 and 1,353), identical page counts and identical integrity counters, compared with the frozen full-path outputs.
