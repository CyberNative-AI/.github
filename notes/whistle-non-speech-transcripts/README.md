# Whistle returns nothing for silence. For a dog barking, it says "Thank you."

Whistle is a 16.9 MB on-device speech-to-text model that Cactus Compute released on 30 September for phones,
wearables, smart-home devices and microcontrollers. Its [model card](https://huggingface.co/Cactus-Compute/whistle)
says "silence returns an empty transcript rather than an invented sentence", and the package's test for that feeds it one
second of digital zeros.

An always-open microphone rarely hears digital zeros. It hears the dog, the rain, the dishwasher. We ran Whistle on 2,000
recordings of everyday sounds that contain no speech, using the settings from its own `needle whistle compare` command.

**Short answer: it wrote words on 1,945 of the 2,000 clips (97.3%). 1,536 times the words were "Thank you." A free 2 MB
voice-activity detector in front of it cut the clips with words from 1,945 to 87 (95.5% fewer).**

The card's literal claim holds: Whistle returned an empty string for digital silence of 1, 5 and 30 seconds and for every
synthetic noise clip we tried. Its speech recognition was also good in our test (4.16% word error rate on 300 LibriSpeech
utterances).

## What we ran

- **Model:** Whistle from `cactus-needle` 3.2.2 (PyPI, 14 October), model revision `ca528760` on Hugging Face,
  `needle.Whistle().transcribe(audio, language="en")`, the setting `compare` uses. We also ran the product default
  (language detected). Version 3.2.3 came out on 15 October; on ten of the clips (the repro in the issue linked below)
  it gave the same text as 3.2.2.
- **Non-speech clips:** all 2,000 clips of [ESC-50](https://github.com/karolpiczak/ESC-50), 50 classes × 40 five-second
  recordings: animals, rain, wind, footsteps, door knocks, keyboards, vacuum cleaners, car horns, sirens and so on.
- **Speech control:** 300 LibriSpeech utterances, so a model that simply outputs nothing would fail.
- **Comparison:** the two models `compare` puts next to Whistle, Whisper tiny (`openai-whisper` 20250625) and Moonshine
  tiny-streaming (`moonshine-voice` 0.1.5), at their `compare` settings, plus the larger Whisper base for reference.
  Gate: Silero VAD 6.2.3 at its defaults.
- **Where:** x86-64 Linux CPU in a container with networking off. We froze the protocol and scoring script before
  the main run. A repeat of 200 clips gave identical output for every clip. A second run from a fresh install, with
  freshly downloaded packages, weights and data, gave the same text on all 2,312 clips for Whistle, Silero VAD and
  Whisper tiny.

## What we found

| Same 2,000 non-speech clips | Clips with ≥1 word |
|---|---|
| Whistle, English | **1,945 (97.3%)**, 95% CI 96.4–97.9% |
| Whistle, language detected (product default) | 1,951 (97.6%) |
| Whisper tiny | 469 (23.5%) |
| Whisper base (larger) | 636 (31.8%) |
| Moonshine tiny-streaming | **12 (0.6%)** |
| Silero VAD → Whistle | 87 (4.35%) |
| Silero VAD → Whisper tiny | 42 (2.1%) |

A larger Whisper did not help: Whisper base wrote words on more of these clips than Whisper tiny did.

Without the six classes that come from a human or animal throat (laughing, crying baby, coughing, sneezing, breathing,
snoring), Whistle still wrote words on 97.0% of the remaining 1,760 clips.

After "Thank you." the most common outputs were "I'm sorry." (53), "I don't know." (22) and "Ha ha ha!" (17), from 231
distinct non-empty strings with a median of two words. In 39 of the 50 classes every one of the 40 clips got text. The clips that
stayed empty were mostly steady machine or nature noise (vacuum cleaner 18 of 40, rain 9).

| ESC-50 clip | Sound | Whistle wrote |
|---|---|---|
| `1-100032-A-0.wav` | dog | Thank you. |
| `1-17367-A-10.wav` | rain | Thank you. |
| `1-155858-A-25.wav` | footsteps | Thank you. |
| `1-101336-A-30.wav` | door knock | Thank you. |
| `1-137-A-32.wav` | keyboard typing | Thank you. |
| `1-21896-A-35.wav` | washing machine | Thank you. |
| `1-17124-A-43.wav` | car horn | Thank you. |
| `1-260640-B-2.wav` | pig | I'm sorry. |
| `1-51805-B-33.wav` | door creak | I don't know. |
| `1-31482-A-42.wav` | siren | Thanks for watching! |

We did not resample our way into this: on 100 seeded clips, Whistle's own file path on the original 44.1 kHz files gave
text identical to our 16 kHz loader on all 100.

## Why a stray "Thank you." matters here

Whistle is built to feed a tool-calling model on the same engine. We sent every non-empty Whistle transcript from the
clips (1,951, including six that are only "Hmm." or "Mm-hmm.") to the package's own smart-home agent
(`needle.environments.smart_home`, its tools and system prompt).

**1,780 of them came back with a function call.** 1,740 were `start_robot_vacuum(action="stop")`. "Thank you." maps to that
call at a confidence of about 0.32. As a positive control, all 18 of the package's own smart-home test requests produced
a call.

The confidence score is the safety net. Cactus's
[guide to the score](https://cactuscompute.com/blog/needle-confidence) says "the engine withholds anything under 0.1;
above that the number is yours to route on", and its example acts at 0.7 or above and asks for confirmation between 0.1
and 0.7. None of the 1,780 calls in our run reached 0.7, so a client built that way would execute none of them and
would instead ask for confirmation 1,780 times (1,740 of them "stop the vacuum?"). With a 0.5 threshold, which the guide says suits a light switch, 5 would run. A client
that executes the returned `function_calls` as they stand would execute all 1,780.

The same guide says "a request no declared tool can serve returns the empty call []". In our run, "Thank you." returned a
call.

The smart-home agent was not fully deterministic. Its 32 control requests ran twice, once in each `TOOL_*.jsonl` file in
`results/raw/`. Between the two runs, 1 request flipped between a call and no call, and the same request's confidence
moved by up to 0.08. Counts near a threshold are therefore approximate. The "Thank you." call scored 0.3197 on all 1,536
such clips in one run and 0.3133 on all 38 in the other.

## What to do with an always-open microphone

1. **Gate Whistle on voice activity or a wake word.** This is the gate we measured, written as one function. It
   transcribes a clip only when Silero VAD finds speech anywhere in it:

   ```python
   import needle, torch
   from silero_vad import load_silero_vad, get_speech_timestamps

   vad = load_silero_vad()
   whistle = needle.Whistle()

   def transcribe_gated(audio):  # float32 mono, 16 kHz
       if not get_speech_timestamps(torch.from_numpy(audio), vad, sampling_rate=16000):
           return ""
       return whistle.transcribe(audio, language="en")["text"]
   ```

   With Silero's defaults it found speech in all 300 LibriSpeech utterances and cut Whistle's non-speech output from 97.3%
   to 4.35%. We did not tune it. We ran this function as printed on the ten clips in the table above and three speech
   utterances: it returned nothing for nine of the ten, the pig still came back as "I'm sorry.", and the speech came
   back in full.
2. **Route tool calls on confidence.** Do not execute `function_calls` unread. Use a threshold and confirm below it, as
   the guide describes.
3. **Test your own room.** Record a few minutes of your device's normal background and count how often a transcript
   appears.

## Limits

- Run twice by us on the same machine, the second time from a fresh install; not independently reproduced on other
  hardware.
- ESC-50 is curated five-second clips, many padded with digital silence. It has no music, TV or near-speech audio.
  A live microphone produces long stretches where Whistle's behaviour may differ.
- We tested whole-clip transcription. Whistle's streaming mode commits "the words two passes agree on", which may behave
  differently; we did not test it. We tested the x86-64 build, not ARM devices.
- Whisper ran on `openai-whisper`, not whisper.cpp. Silero ran at its defaults.
- ESC-50 audio is licensed CC BY-NC; we do not redistribute it. The evidence names clips by filename.

## Evidence in this folder

- `protocol/`: the protocol, frozen before the main run, and its two execution-only amendments.
- `scripts/`: the runner, the manifest builder, the scorer and the post-hoc file-path check.
- `results/raw/`: every output row: one JSONL file per model, two for the smart-home agent (`TOOL_W_en` on Whistle's
  transcripts, `TOOL_T_tiny` on Whisper tiny's), plus the clip manifests
  (ESC-50 filenames and labels, LibriSpeech reference transcripts, no audio). That third-party text keeps its own
  license: see [THIRD-PARTY-NOTICES.md](THIRD-PARTY-NOTICES.md).
- `results/`: the score files; `score-final.json` has every arm. `env-freeze.txt`, `inputs.sha256` and `weights.sha256`
  pin the packages, data and model.
- `results/rerun/`: the fresh-install second run's score, its row-by-row comparison with ours, and the output of the
  gate function above.
- [REPRODUCE.md](REPRODUCE.md): rescoring the published rows takes a few minutes and needs no audio. A full rerun from a
  fresh install needs ESC-50, LibriSpeech and a little over four hours of 6-CPU time; every stage runs in a container
  with CPU, memory and time limits.

We reported the result to the maintainers in [needle issue #179](https://github.com/cactus-compute/needle/issues/179).

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai.
We publish any correction here, dated.
