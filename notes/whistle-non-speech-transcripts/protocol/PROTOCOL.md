> Public copy. Internal tracking IDs, team names, host paths and internal follow-up routing were removed or reworded. Methods, arms, data, metrics and the decision rule are unchanged. The protocol was frozen before the main run.

# Does a 17 MB on-device ASR model stay silent on real non-speech audio?

Status: DRAFT (freeze = FROZEN.sha256 over PROTOCOL.md, run.py, manifest.py, score.py)
Risk tier 0/1 (public data, public Apache-2.0/MIT models, CPU, network none during runs).

## Why now
Cactus Compute released Whistle on 2026-09-30 (HF `Cactus-Compute/whistle`, sha ca528760, 16.9 MB `.cact`;
`cactus-needle` 3.2.2 on PyPI 2026-10-14). It targets smart-home, wearables and microcontrollers, and its card says:
"silence returns an empty transcript rather than an invented sentence". The same engine feeds the transcript to Needle
for tool calls (card: `needle --model needle3.cact --model whistle.cact --tools tools.json --audio clip.wav`).
The vendor test `test_silence_is_an_empty_transcript` checks only `[0.0]*16000` (digital zeros).
Whisper inventing text on non-speech audio is a documented failure (Koenecke et al. 2024; Barański et al. 2025).
For an always-listening device the job is "do not invent a command from household noise". The standard substitute is a
voice-activity detector (Silero VAD, ~2 MB, MIT) in front of the recognizer.
No issue on cactus-compute/needle reports non-speech behaviour (GitHub search 2026-10-15: 6 Whistle issues, none).

## Question and hypotheses
Q: On real non-speech recordings, how often does Whistle emit a non-empty transcript, compared with Whisper tiny gated by
Silero VAD (the strongest cheap substitute) and with the vendor's own comparators?
H_support: Whistle's built-in rejection matches a VAD gate, so a device builder can skip the VAD.
H_change: Whistle invents text on a material share of non-speech clips; builders still need a VAD.

## Data (public; hashes recorded)
- Non-speech: ESC-50 (github karoldvl/ESC-50 master.zip, sha256 805afc61…a79ce; CC BY-NC 3.0), all 2,000 5-s clips,
  50 classes, resampled 44.1→16 kHz with soxr HQ. Audio is not redistributed; results cite clip filenames.
- Synthetic (seed 13918): digital zeros 1/5/30 s; white noise −90/−60/−40/−20 dBFS; pink −40/−20 dBFS (5 s), pink −40 dBFS 30 s;
  60 Hz and 50 Hz hum with harmonics at −30 dBFS.
- Speech positive control: LibriSpeech test-clean (openslr 12, sha256 39fde525…6c23; CC BY 4.0), 300 utterances drawn with
  random.Random(13918) from 2,620. The 5 pilot utterances are outside the 300.

## Arms (all CPU, python:3.12-slim, venv: torch 2.11.0+cpu, no NVIDIA packages, `--network none`)
- W_en: `needle.Whistle().transcribe(audio, language="en")` — exactly the vendor's `compare` setting. PRIMARY.
- W_auto: `transcribe(audio)` — product default (language detection over 7 languages).
- T_tiny / T_base: openai-whisper 20250625 `model.transcribe(audio, language="en", fp16=False)` — the vendor's compare
  setting; `torch.manual_seed(0)` before each clip (temperature fallback samples).
- M_tiny: moonshine-voice 0.1.5 tiny-streaming, `transcribe_without_streaming` — the vendor's compare setting.
- VAD: silero-vad 6.2.3 `get_speech_timestamps` at defaults. V = VAD∘T_tiny: empty if VAD returns no segment, else the T_tiny
  text. W+V = VAD∘W_en (secondary).
- TOOL_W_en / TOOL_T_tiny: every non-empty transcript is sent to the vendor's own
  `needle.environments.smart_home` tools and SYSTEM (`Needle(tools=TOOLS, system=SYSTEM, stateless=True).complete(text)`).
  Positive control: the environment's own TEST_CASES.
Telemetry off (NEEDLE_TELEMETRY=0, DO_NOT_TRACK=1) and network none. Preflight prints "no nvidia devices" and cuda False.

## Metric
A transcript is FALSE on a non-speech clip if it has ≥1 word after normalization: whisper `EnglishTextNormalizer` for
English-forced arms (it removes bracketed/parenthesized annotations such as "(laughs)" and punctuation);
`BasicTextNormalizer` for W_auto. FTR(arm) = FALSE clips / 2,000 ESC-50 clips; an errored clip counts as FALSE. Wilson 95% intervals.
Paired comparison W_en vs V on the same clips: exact two-sided McNemar.
Sensitivity frame (pre-registered, not primary): exclude six vocal-tract classes (laughing, crying_baby, coughing, sneezing,
breathing, snoring) → 1,760 clips (scorer asserts the count).

## Decision rule (primary: does Whistle alone need a VAD in front of it? all 2,000 ESC-50 clips)
Primary comparison = W_en ungated vs W+V (same recognizer behind Silero VAD); amended before freeze after a design
review: comparing with VAD∘Whisper-tiny would mix recognizer quality with the gate's effect.
FALSE_W = clips where W_en emits ≥1 word (an errored clip counts as FALSE). R = FALSE_W clips on which VAD finds no
segment (what a VAD in front would remove).
- SUPPORTED: Wilson 95% upper bound of FTR_W ≤ 2.0% (Whistle alone rarely invents text, so a VAD adds at most ~2 pp).
- CHANGE: FTR_W ≥ 5.0% and R ≥ 60 clips (3 pp) and R ≥ 0.5 × FALSE_W (a VAD in front removes most of it).
- otherwise DESCRIPTIVE (includes "Whistle invents text but a default VAD does not remove it").
Secondary reference (no verdict): V = VAD∘T_tiny ("cheap stack") vs W_en with exact two-sided McNemar.
Literal claim check (reported separately, not part of the verdict): W_en empty on the three digital-zero clips.

## Validity gates (any failure → INVALID, reported as such)
1. W_en and T_tiny non-empty on ≥98% of the 300 speech utterances, and corpus WER ≤ 15% (EnglishTextNormalizer, jiwer).
2. VAD finds ≥1 segment on ≥95% of the 300 speech utterances (a gate that drops speech would make V meaningless).
3. Error fraction ≤ 2% per arm and per set (ESC-50 and speech separately) for W_en, T_tiny and VAD (run.py `MAX_ERR_FRAC` also flags it). Primary counts an errored clip as FALSE; a sensitivity line drops errored clips. An arm interrupted by its runtime ceiling is
   INCONCLUSIVE, not a failure; the verdict needs W_en, T_tiny and VAD complete.
4. Repeat: W_en, T_tiny and VAD re-run on 200 ESC-50 clips (random.Random(13918) sample); identical text on ≥99%.
Tool arm validity (secondary only): ≥90% of smart_home `positive` TEST_CASES return ≥1 call.

## Secondary outputs (descriptive, no verdict)
FTR for W_auto, T_tiny, T_base, M_tiny, W+V; per-class and per-category FTR; synthetic-clip results; tool calls per
2,000 clips from W_en and T_tiny transcripts (raw and at confidence ≥ 0.4, the harness example gate), against a baseline of
tool calls on the 300 LibriSpeech (non-command speech) transcripts; latency per clip.
Pilot (API/timing only, not in any frame): 2 synthetic clips + 5 held-out utterances; every arm empty on zeros_5s and
pink −20 dBFS; smart_home positive controls 17/18 with a call; one pilot utterance ("Look closely at life.") produced
`start_robot_vacuum(dock)` at confidence 0.23.

## Resources, limits, aborts
$0. Host CPU, one container, 6 CPUs, 8 GB, swap off, network none, max runtime 4 h; resumable
(run.py skips ids already written). No GPU: default runc runtime, no `--gpus`, CPU-only torch. Data and outputs in a local
work directory. Teardown: `--rm` containers; none left.

## Consequences
- CHANGE → publish the measured finding; consider one GitHub issue on cactus-compute/needle (issues open;
  no CONTRIBUTING/AGENTS policy found) with clip IDs and a VAD recommendation.
- SUPPORTED → publish "claim holds beyond digital silence" as a useful negative; no issue.
- DESCRIPTIVE → record the numbers; no outside action.

## Limitations (known before the run)
ESC-50 is curated, 5-s, often zero-padded; no music, TV or speech-adjacent audio; English-forced primary; x86 Linux engine
build, not ARM devices; openai-whisper rather than whisper.cpp; Silero defaults untuned; executed on our host, not
independently reproduced.
