"""Count input tokens omitted by an embedding configuration; never load weights."""
import argparse
import json
from pathlib import Path

from huggingface_hub import hf_hub_download
from transformers import AutoTokenizer


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("repo")
    p.add_argument("revision", help="full model commit hash")
    p.add_argument("corpus", help="JSONL with one prepared input string per line")
    p.add_argument("--local", help="use previously downloaded config/tokenizer files")
    args = p.parse_args()
    config = Path(args.local)/"sentence_bert_config.json" if args.local else Path(hf_hub_download(args.repo, "sentence_bert_config.json", revision=args.revision))
    cap = json.loads(config.read_text())["max_seq_length"]
    tok = AutoTokenizer.from_pretrained(args.local or args.repo, revision=args.revision,
                                       local_files_only=bool(args.local), trust_remote_code=False)
    records = cut_inputs = omitted_tokens = total_tokens = 0
    with Path(args.corpus).open(encoding="utf-8") as f:
        for line in f:
            text = json.loads(line)
            if not isinstance(text, str):
                raise ValueError("each JSONL record must be a prepared input string")
            full = tok(text, truncation=False)["input_ids"]
            cut = tok(text, truncation=True, max_length=cap)["input_ids"]
            lost = len(full)-len(cut)
            records += 1
            cut_inputs += lost > 0
            omitted_tokens += lost
            total_tokens += len(full)
    print(json.dumps(dict(records=records, configured_cap=cap, cut_inputs=cut_inputs,
                          omitted_tokens=omitted_tokens, input_tokens_with_specials=total_tokens,
                          special_tokens_per_input=tok.num_special_tokens_to_add(pair=False))))


if __name__ == "__main__":
    main()
