"""Check saved input-loss evidence without importing tokenizer libraries."""
import hashlib
import json
from pathlib import Path
import sys


def check(path):
    data = json.loads(Path(path).read_text())
    assert len(data["rows"]) == 10
    assert [r["rank"] for r in data["rows"]] == list(range(1, 11))
    assert len({r["repo"] for r in data["rows"]}) == 10
    assert [r["rank"] for r in data["rows"] if r["configured_cap"] is None] == [2, 7]
    for r in data["rows"]:
        if r["configured_cap"] is None:
            assert r["controls"] == []
            continue
        assert r["special_tokens_count"] == 2 and r["truncation_side"] == "right"
        flags = [False, True, True, False] if r["rank"] == 1 else [False, True, False]
        assert [c["identical_input_ids"] for c in r["controls"]] == flags
        for c in r["controls"]:
            full, cut = c["full"]["input_ids"], c["cut"]["input_ids"]
            assert len(full) == len(cut) == 2 and full[0] != full[1]
            assert (cut[0] == cut[1]) == c["identical_input_ids"]
            for i in range(2):
                assert len(full[i]) == c["prefix_words"]+3
                assert len(cut[i]) == min(len(full[i]), c["cap"])
                expected = full[i][:c["cap"]-1] + full[i][-1:] if len(full[i]) > c["cap"] else full[i]
                assert cut[i] == expected
                assert c["cut"]["attention_mask"][i] == [1] * len(cut[i])
                digest = hashlib.sha256(json.dumps(cut[i], separators=(",", ":")).encode()).hexdigest()
                assert digest == c["cut_hashes"][i]
    print("PASS: 10 rows; 7 new models/21 controls; 1 reused model/4 controls; 2 N/A rows")


if __name__ == "__main__":
    check(sys.argv[1])
