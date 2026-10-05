"""Measure tokenizer input loss at configured, pinned SentenceTransformer caps."""
import hashlib
import json
from pathlib import Path
import sys

import transformers
from transformers import AutoTokenizer


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, separators=(",", ":")).encode()).hexdigest()


def main(root, admission):
    root = Path(root)
    table = json.loads(Path(admission).read_text())
    result = []
    for row in table["rows"]:
        repo, cap = row["repo"], row["configured_cap"]
        item = dict(row)
        if cap is None:
            item.update(test="N/A: no configured SentenceTransformer cap", controls=[])
        elif row["rank"] == 1:
            old = json.loads((root / "minilm-reused.json").read_text())
            assert old["configured_cap"] == cap
            assert old["tokenizer_model_max_length"] == row["tokenizer_model_max_length"]
            item.update(test="reused accepted same-revision result", controls=old["rows"],
                        tokenizer_class=old["tokenizer_class"], special_tokens_count=2,
                        truncation_side="right", reused_sha256=fingerprint(old))
        else:
            local = root / "sources" / repo.replace("/", "--")
            tok = AutoTokenizer.from_pretrained(local, local_files_only=True, trust_remote_code=False)
            assert tok.model_max_length == row["tokenizer_model_max_length"]
            assert tok.truncation_side == "right"
            special = tok.num_special_tokens_to_add(pair=False)
            assert special == 2
            assert len(tok.encode("a", add_special_tokens=False)) == 1
            tails = [w for w in ["cat", "dog", "yes", "no", "red", "blue"]
                     if len(tok.encode(w, add_special_tokens=False)) == 1][:2]
            assert len(tails) == 2
            controls = []
            for label, prefix, limit, identical in [
                ("suffix-retained-at-boundary", cap-special-1, cap, False),
                ("suffix-removed-one-beyond", cap-special, cap, True),
                ("explicit-one-token-larger-control", cap-special, cap+1, False),
            ]:
                texts = ["a " * prefix + tail for tail in tails]
                full = dict(tok(texts, truncation=False))
                cut = dict(tok(texts, truncation=True, max_length=limit))
                assert full["input_ids"][0] != full["input_ids"][1]
                assert (cut["input_ids"][0] == cut["input_ids"][1]) == identical
                for i in range(2):
                    assert len(full["input_ids"][i]) == prefix+special+1
                    expected = full["input_ids"][i][:limit-1] + full["input_ids"][i][-1:] if len(full["input_ids"][i]) > limit else full["input_ids"][i]
                    assert cut["input_ids"][i] == expected
                    assert cut["attention_mask"][i] == [1] * len(cut["input_ids"][i])
                controls.append(dict(name=label, prefix_words=prefix, tails=tails, cap=limit,
                                     full=full, cut=cut, identical_input_ids=identical,
                                     cut_hashes=[fingerprint(ids) for ids in cut["input_ids"]]))
            item.update(test="executed tokenizer only", controls=controls,
                        tokenizer_class=type(tok).__name__, special_tokens_count=special,
                        truncation_side=tok.truncation_side)
        result.append(item)
    payload = dict(transformers=transformers.__version__, rows=result,
                   newly_executed_models=7, reused_models=1, not_applicable_models=2)
    path = root / "work" / "sequence-caps-result.json"
    path.write_text(json.dumps(payload, indent=2)+"\n")
    # Verify actual JSON persistence rather than treating a passed in-memory run as delivery.
    saved = json.loads(path.read_text())
    assert saved == payload
    print(json.dumps({k:v for k,v in payload.items() if k != "rows"}))
    for row in result:
        print(row["rank"], row["repo"], row["configured_cap"], row["test"],
              [c["identical_input_ids"] for c in row["controls"]])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
