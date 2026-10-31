# Rerun with the FrontierVEP prompt (30 October 2026)

The same 300 missense and 120 other variants as the first run, asked again with the FrontierVEP
template that the Carbon-X team quoted on
[HuggingFaceBio/Carbon-X discussion #6](https://huggingface.co/HuggingFaceBio/Carbon-X/discussions/6).
Model file, llama.cpp build, sampling, thinking setting and per-variant seeds are the first
run's (see [`../README.md`](../README.md) for inputs and hashes). Results are in the note's
"Rerun with the FrontierVEP prompt" section.

Arms, as named in the files:

- `F_plus`: template, window on the hg38 plus strand. Minus-strand genes get the reverse
  complement of the first run's window, so the variant sits at 4,096 and the alleles are the
  VCF REF/ALT.
- `F_gene`: template, the first run's gene-oriented window (variant at 4,097). For plus-strand
  genes the message is identical to `F_plus`, so we sent it once and the scorer reuses that
  answer.
- `C_reseed`: the first run's message, byte for byte, with a new seed, to show how many labels
  change from sampling alone.
- `C_orig`: the first run's stored answers (`../out/carbon_raw.jsonl`), re-parsed with its
  parser.

Template answers are parsed with the rule in the publisher's `vepqa.py`: the completion must end
with `<answer>…</answer>`, and the text inside, stripped and casefolded, must be exactly
`benign` or `pathogenic`. Anything else counts as wrong. Before the main run, the 20
interface-check variants went through both template arms (`out/fvep_ctrl_raw.jsonl`).

## Rescore the stored answers (no GPU, no download)

From this folder, with Python 3.12 and the standard library:

```sh
mkdir -p first/out
python3 -I -c 'import json,sys; [print(json.dumps(r, sort_keys=True)) for r in json.load(open(sys.argv[1]))]' ../out/frame_slim.json > first/out/frame.jsonl
python3 -I -c 'import json,sys; [print(json.dumps(r, sort_keys=True)) for r in json.load(open(sys.argv[1]))]' out/controls_frame_slim.json > first/out/controls_frame.jsonl
cp ../out/carbon_raw.jsonl first/out/carbon_raw.jsonl
cp out/first_run_ctrl_raw.jsonl first/out/ctrl_raw.jsonl
python3 -I src/score_fvep.py first out/fvep_raw.jsonl out/fvep_ctrl_raw.jsonl out/tokcheck.json score.json
cmp score.json out/score.json
python3 -I src/secondary_o.py score.json secondary_o.json
cmp secondary_o.json out/secondary_o.json
```

On our machine both `cmp` lines report no difference.

## Run it again

Build `frame.jsonl` and `controls_frame.jsonl` with the full windows as in
[`../README.md`](../README.md) (steps 1 and 2), put them in one folder, then:

```sh
llama-server -m carbon-x-q8_0.gguf -ngl 99 -c 16384 --parallel 1 --host 127.0.0.1 --port 18731 &
FRAME_DIR=<that folder> python3 -I src/tokcheck.py 18731 tokcheck.json
FRAME_DIR=<that folder> python3 -I src/run_fvep.py ctrl fvep_ctrl_raw.jsonl 18731
FRAME_DIR=<that folder> python3 -I src/run_fvep.py main fvep_raw.jsonl 18731
```

`src/check_messages.py <folder containing out/frame.jsonl, out/controls_frame.jsonl, out/carbon_raw.jsonl, out/ctrl_raw.jsonl> check.json`
checks, without a GPU, that every message builds and that the copied first-run message
reproduces the first run's message hashes. Each record in `out/fvep_raw.jsonl` carries the
SHA-256 of the exact message, so you can check that you sent the same text.

## Files

- `out/fvep_raw.jsonl`: every answer (300 `C_reseed`, 420 `F_plus`, 206 `F_gene`), with arm,
  seed, message hash, timing and token counts. `stratum` starts with `M` (missense) or `O`
  (other types).
- `out/fvep_ctrl_raw.jsonl`: the 20 interface-check variants, both template arms (32 records,
  as above).
- `out/score.json`: the parsed answer of every arm for every variant (`F_plus_L` and `F_gene_L`
  re-parse the template answers with the first run's parser; the labels are the same) and the
  result tables.
- `out/secondary_o.json`: intervals and paired tests for the 120 other-type variants, computed
  from `score.json` after the run.
- `out/tokcheck.json`: the tokenizer check (6 variants, both template arms, with and without
  `<dna>` tags: identical ids, 1,365 six-base tokens plus one tail token per window).
- `out/controls_frame_slim.json` and `out/first_run_ctrl_raw.jsonl`: the 20 interface-check
  variants without sequences and the first run's answers for them, which the scorer needs.

Script changes from the run: comments name runs by date instead of our internal labels;
`run_fvep.py` and `tokcheck.py` read the frame folder from `FRAME_DIR` instead of a fixed path,
and `run_fvep.py` reads the GPU for the optional 83 °C pause from `CARBON_GPU` (default `0`).
Licences: [`../NOTICE.md`](../NOTICE.md).
