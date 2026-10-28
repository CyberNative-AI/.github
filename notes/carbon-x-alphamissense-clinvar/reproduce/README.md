# Reproducing the Carbon-X and AlphaMissense comparison

Python 3.12, standard library only. Building the variant set needs no GPU but holds the
needed hg38 chromosomes in memory, so allow several gigabytes. Running Carbon-X needs a GPU
that holds the 15.8 GB Q8_0 file.

## Inputs

Download these and check them against `out/hashes.json` (SHA-256):

- ClinVar GRCh38 VCFs `clinvar_20260808.vcf.gz`, `clinvar_20260905.vcf.gz`,
  `clinvar_20260928.vcf.gz`, `clinvar_20261019.vcf.gz` and `clinvar_20261025.vcf.gz` from
  https://ftp.ncbi.nlm.nih.gov/pub/clinvar/vcf_GRCh38/weekly/ (older weeks move to
  `archive_2.0/2026/`)
- `AlphaMissense_hg38.tsv.gz` from https://zenodo.org/records/10813168
- `hg38.fa.gz` from https://hgdownload.soe.ucsc.edu/goldenPath/hg38/bigZips/
- `MANE.GRCh38.v1.5.summary.txt.gz` from
  https://ftp.ncbi.nlm.nih.gov/refseq/MANE/MANE_human/release_1.5/
- `carbon-x-q8_0.gguf` from https://huggingface.co/HuggingFaceBio/Carbon-X-GGUF
- llama.cpp release b11946 (any build from b11742 supports the Carbon-X DNA tokenizer)

## Commands

```sh
# 1. New definitive labels since 8 August, with the first checked file containing a benign/pathogenic classification
python3 -I src/diff_windows.py clinvar_20260808.vcf.gz clinvar_20260905.vcf.gz \
  clinvar_20260928.vcf.gz clinvar_20261019.vcf.gz clinvar_20261025.vcf.gz new_labels.jsonl

# 2. Sample the variants, cut the 8,192-base windows, join AlphaMissense
#    (also writes the 20 interface-check variants)
python3 -I src/build_frame.py new_labels.jsonl hg38.fa.gz AlphaMissense_hg38.tsv.gz \
  MANE.GRCh38.v1.5.summary.txt.gz clinvar_20260808.vcf.gz frame.jsonl controls_frame.jsonl

# 3. Serve Carbon-X and ask it about every variant
llama-server -m carbon-x-q8_0.gguf -ngl 99 -c 16384 --parallel 1 --host 127.0.0.1 --port 18731 &
python3 -I src/run_carbon.py frame.jsonl carbon_raw.jsonl 18731

# 4. Score
python3 -I src/score.py frame.jsonl carbon_raw.jsonl score.json
```

`frame.jsonl` holds the full windows (about 7.9 MB), so we publish `out/frame_slim.json`
instead: the same rows without the sequences, with the SHA-256 of each window. Your rebuilt
windows should match those hashes, and each Carbon-X record in `out/carbon_raw.jsonl` carries
the SHA-256 of the exact message, so you can check that you sent the same prompt.

To rescore our stored answers without a GPU or any download, scoring needs no sequences:

```sh
python3 -I -c 'import json; [print(json.dumps(r, sort_keys=True)) for r in json.load(open("out/frame_slim.json"))]' > frame.jsonl
python3 -I src/score.py frame.jsonl out/carbon_raw.jsonl score.json
cmp score.json out/score.json
```

On our machine this reproduces `out/score.json` byte for byte.

`run_carbon.py` is the script we ran, with one change: our GPU's identifier is replaced by the
`CARBON_GPU` environment variable (default `0`), which only feeds the optional pause when the
card reaches 83 °C. `score.py` differs from ours only in its first comment line. The other
scripts are unchanged.

## Files in `out/`

- `variants.csv`: one row per variant, readable without the scripts (see the note's Files
  section for the columns). The `set` column is `missense` (the 300 in the main result),
  `other` (the 120 other variant types) or `new_25_october` (the 44 classified in the 25
  October file and in none of the earlier files we read). `first_release_seen_classified` is
  the first of the 5 September, 28 September, 19 October and 25 October files in which the
  variant had a benign or pathogenic classification; we did not read the weeks in between.
  The label, consequence and review status are from the 25 October file.
- `frame_slim.json` (the variant set as the scripts see it, without sequences) and
  `score.json` use the scripts' field names: `first_window_end` is the
  same release date, `group` its window (`W0905_0928`, `W1019`, `W1025`), and `STRICT` marks
  the 44 variants of the 25 October file. AlphaMissense fields are absent for 142 of the 464
  variants (all 120 `other`, and 22 of the 44), and `am_rows` counts the matching rows whose
  scores were averaged.
- `carbon_raw.jsonl`: every Carbon-X answer, with seed, message hash, timing and token counts.
- `score.json`: the parsed answer for every variant and the result tables in the note.
- `hashes.json`: SHA-256 of every input file and of the llama.cpp release archives we used.
