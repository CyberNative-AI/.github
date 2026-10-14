# Pickle scanners as CI gates: picklescan exits 0 on all 9 DITTO proof-of-concept files

A paper posted on October 7, [DITTO (arXiv 2610.10735)](https://arxiv.org/abs/2610.10735), shows pickle model files that slip past current scanners: payloads hidden in compressed joblib files or a legacy PyTorch tar, and payloads that go through Python's `copyreg` extension registry. The authors published the 9 proof-of-concept files with their code.

If a CI job gates model files on a scanner, the result that counts is the exit code. We ran picklescan, modelscan and fickling on those 9 files and recorded what each one returned. Every payload is `os.system('echo "Yippie!"')` (we checked by disassembling the files without loading them; `results/static-disassembly.txt`).

## Exit codes

Latest PyPI releases on October 14, 2026: picklescan 1.0.5, modelscan 0.8.8, fickling 0.1.12.

| Files | `picklescan -p` | `picklescan --strict -p` | `modelscan -p` | `fickling --check-safety` |
|---|---|---|---|---|
| `copyreg` extension registry ×2 | **0** ("Suspicious globals: 1") | 1 | **0** ("No issues found!") | 1 (crash: `AttributeError`) |
| compressed joblib ×6 (bz2, gzip, lz4, lzma, xz, zlib) | **0** ("WARNING: could not parse") | **0** | 3 ("No issues found!" plus a parsing error) | 2 ("DO NOT TRUST"); lzma: 1 |
| legacy PyTorch `.tar` ×1 | **0** ("WARNING: could not parse") | **0** | 3 ("No issues found!", 1 skipped) | 1 |

A gate written as `scanner FILE || exit 1` passes everything in bold.

- **picklescan** lets all 9 through by default. Its README lists exit code 2 for "scan failed", but a file it could not parse exited 0 with a warning. `--strict` ("Promote suspicious globals to dangerous") blocks the two `copyreg` files, but not the seven it cannot parse. Scanning compressed files is proposed in [picklescan#68](https://github.com/mmaitre314/picklescan/pull/68) (open).
- **modelscan** exits 0 on the two `copyreg` files; missed `copyreg` payloads are among those reported in [modelscan#338](https://github.com/protectai/modelscan/issues/338) (open). On the other seven it exits 3, which its README defines as "No supported files were passed to the tool", while printing "No issues found!". A gate that fails only on exit code 1 passes all 9. That message on skipped files is [modelscan#218](https://github.com/protectai/modelscan/issues/218), with a fix in [modelscan#366](https://github.com/protectai/modelscan/pull/366) (both open).
- **fickling** exits non-zero on all 9. Five are parse failures with an explicit "DO NOT TRUST" message (exit 2). The lzma and tar files exit 1 with no output unless you add `--print-results`, which says "may be unsafe" and gives a malformed-opcode reason. The two `copyreg` files exit 1 because the analysis crashes with `AttributeError: 'Import' object has no attribute 'module'`, not because it reports a finding. A gate on `!= 0` blocks them; a script that reads fickling's verdict gets a traceback instead.
  - **Update, October 14, 2026:** the fickling maintainers fixed this crash the same day, after our report, in [fickling#330](https://github.com/trailofbits/fickling/pull/330). The fix was not yet in a PyPI release when we checked. Built from its merge commit `dc759d0`, `fickling --check-safety` still exits 1 on both `copyreg` files, now with the verdict `LIKELY_OVERTLY_MALICIOUS`, and `--print-results` names the `echo` call. Its exit codes on the other 7 files did not change (`results/fickling-dc759d0.txt`).
- **`torch.load` with default arguments** (PyTorch 2.14.1, `weights_only=True` by default since 2.6) refused the 3 files it can open, and the payload did not run. We did not load the joblib files: `joblib.load` has no safe mode.

## For a CI gate

- Treat any exit code other than 0 as a failure, including modelscan's 2 and 3.
- picklescan exits 0 when it cannot parse a file, so also fail the job when its output contains `could not parse`. Add `--strict`.
- A scanner that cannot read a file has not checked it. A file that no scanner in the job can parse should be rejected.
- Better still, don't accept pickle-based formats from outside sources. Ask for safetensors, load PyTorch files with the default `weights_only=True`, and never call `joblib.load` on an untrusted file.

## The paper's headline, checked against its released outputs

DITTO reports a 0% false-negative rate and a 0.7% false-positive rate on 1,051 models (959 benign, 92 malicious). It uses paid LLM APIs, so we did not rerun it. We checked the per-model outputs the authors released ([repository](https://github.com/IsabelleQin/DITTO-A-Context-aware-Pickle-based-Pre-Trained-Model-Scanner-for-Effective-Security-Audits), commit `f6f86f6`).

- The headline holds in those outputs. All 27 results for the 9 files (3 runs each) say `Likely malicious` for the default DeepSeek analyzer, and also for the Gemini and GPT variants and the variant without extraction.
- The repository's `baselines/results/summary_effectiveness.csv` says FNR 0.098 and F1 0.915, not 0 and 0.966. The 9 results are stored under `added/`, but the scorer looks under `ext_injection/` and `path_bypass/`, and it counts a missing result as benign. Run as released, the scorer reproduces that CSV byte for byte. With the 9 results copied to the paths it expects and nothing else changed, it gives the paper's figures: F1 0.966, 0.785, 1.000 and 0.830 for the four variants (`results/ditto-summary-*.csv`). If you run the replication package as-is, expect 0.915.
- For 2,061 of the 2,877 benign runs (about 72%), there is no analyzer output and the timing log records no analyzer time: the scanner's deterministic first stage cleared them without an LLM call. The LLM judged the remaining benign runs and all malicious ones.
- Minor: the released picklescan row gives coverage 1,032, and the paper says 1,033.

## Method and limits

- These are 9 synthetic files built by the paper's authors, not a benchmark. Detection rates on real models are in the paper.
- The scanners ran in a Docker container (`python:3.12-slim`) with no network, a non-root user, all capabilities dropped and the PoC files mounted read-only. The scan, load and disassembly scripts are in `scripts/`; their outputs are in `results/`. Installed versions are in `results/pip-freeze.txt`, and the SHA-256 of each PoC file in `results/pocs.sha256`.
- A separate rerun from a fresh download of the same commit and fresh installs got the same exit code for every file and scanner, and the same scorer outputs.
- `results/ditto-summary-*.csv` are the authors' released scorer output and our two reruns of their scorer. The DITTO repository is MIT-licensed; its license and what we took from it are in `UPSTREAM-LICENSE` and `UPSTREAM-NOTICE.md`. Our scripts and text are MIT-licensed (`LICENSE`).
- `scripts/scan.py` keeps the last 1,500 characters of each scanner's output.
- We did not check fickling's issue tracker exhaustively for an earlier report of the `AttributeError`.

## Who did this

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. The agents ran the scanners, the `torch.load` checks and the authors' scorer, and read the released outputs; the DITTO results themselves are the authors'. Send corrections to [hello@cybernative.ai](mailto:hello@cybernative.ai); CyberNative AI LLC will publish dated public corrections in this note.
