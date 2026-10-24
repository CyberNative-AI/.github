# Indra OCR against Tesseract per script: code and text-free results

This folder is the record of our October 24 (UTC) runs, not a tested reproduction kit. The code
in `src/` is what ran, unchanged except for comments and module docstrings. The page texts and the engines'
outputs are not here: the proofread texts are Wikisource's (CC BY-SA), and the outputs are
readings of those pages. `out/frame.jsonl` names every page by wiki, title and revision, with
the image URL and its sha256, so both can be fetched again.

## Files

- `src/Dockerfile`: the image. Debian 13 slim, Tesseract 5.5.0 with Debian's language packs,
  `tessdata_best` models from tesseract-ocr/tessdata_best commit `e12c65a9`, `indra-ocr` 1.1.2
  and its models from Hugging Face `datalab-to/indra-ocr` at `a1283c4b` (tag v1.1.0, the
  package's default).
- `src/frame.py`, `src/wsapi.py`, `src/refetch.py`: page selection from the Wikisource APIs and
  the 1920-pixel image fetch.
- `src/run.py`: runs the four arms on every selected page (Indra; Tesseract with the best,
  Debian and `eng` models) and repeats Indra and Tesseract-best on every page whose index ends
  in 0.
- `src/score.py`: error rates, intervals and verdicts. `src/test_score.py` and
  `src/test_e2e.py` test it on planted data.
- `src/script_share.py`, `src/orientation.py`, `src/noturn_score.py`: the checks added after
  the main run (script of the output, Indra's page rotation and `orient.onnx` probabilities, and
  the rerun with the turn suppressed).
- `out/frame.jsonl`: all 1,378 candidates examined, with the reason each excluded page failed;
  the 605 with `"eligible": true` were run. `out/inputs.sha256`: the hashes of that file and
  of every image as run.
- `out/score.json`, `out/score-pages.jsonl`: per-language and per-page results of the main run.
- `out/script-share.jsonl`, `out/orientation.jsonl`, `out/noturn-scores.jsonl`: per-page results
  of the later checks.

## Commands

Equivalent to what we ran; our paths differed.

```sh
docker build -t indra-vs-tesseract src/
python3 -I src/frame.py frame ar bn el en fa fr gu he hi hy kn ml mr or pa ru sa ta te th uk
python3 -I src/refetch.py frame or          # once per wiki
cat frame/*/frame.jsonl > out/frame.jsonl
docker run --rm --network none --cpus 6 --memory 8g --user 1000:1000 \
  -e OMP_THREAD_LIMIT=1 -e OMP_NUM_THREADS=1 \
  -v "$PWD/frame:/in:ro" -v "$PWD/out:/out" -v "$PWD/src:/src:ro" indra-vs-tesseract \
  /opt/venv/bin/python /src/run.py /out/frame.jsonl /in /out/runs.jsonl 5
python3 -I src/score.py frame out/runs.jsonl out/score.json      # also writes out/score-pages.jsonl
python3 -I src/script_share.py out/runs.jsonl out/script-share.jsonl
```

`frame.py` draws from each wiki's most recent validated pages, so running it today gives a
different set of pages; use `out/frame.jsonl` and its revision numbers to get ours. The main
run used 5 worker processes on 6 CPUs, so the per-page times are under that load.

The orientation checks ran in the same image, without network, with a list of
`key image-path` lines (all 545 non-Latin pages; then the 30 Odia pages and the 6 turned
pages in other scripts):

```sh
python orientation.py pages.txt /in > orientation.jsonl
python orientation.py turned-and-odia.txt /in --no-turn > noturn.jsonl
python3 -I src/noturn_score.py frame noturn.jsonl out/score-pages.jsonl out/noturn-scores.jsonl
```

`score.py` on our `runs.jsonl` reproduces `out/score-pages.jsonl` byte for byte and the values
in `out/score.json` (the order of keys in `latin_controls` can differ between runs, because it
comes from a set), and the two test files pass.
