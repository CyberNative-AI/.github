# Third-party material

This folder contains no audio and no model weights. Two kinds of third-party text are included. Neither is covered by
the MIT license in `LICENSE`; each keeps the license below.

## LibriSpeech reference transcripts

- **What is included:** the reference transcript (`ref` field) and utterance id of 305 utterances from LibriSpeech
  test-clean: 300 in `results/raw/manifest-speech.jsonl` (repeated in `results/raw/manifest-main.jsonl`) and 5 in
  `results/raw/manifest-pilot.jsonl`. `protocol/PROTOCOL.md` quotes one of the pilot transcripts. The models'
  transcripts of these utterances (speech rows in `results/raw/*.jsonl` and `results/diag-posthoc.json`) largely
  repeat the same text.
- **Source:** LibriSpeech ASR corpus, OpenSLR resource SLR12, <https://www.openslr.org/12/>, by Vassil Panayotov,
  Guoguo Chen, Daniel Povey and Sanjeev Khudanpur ("Librispeech: an ASR corpus based on public domain audio books",
  ICASSP 2015). The corpus is built from LibriVox audiobook recordings.
- **License:** Creative Commons Attribution 4.0 International (CC BY 4.0),
  <https://creativecommons.org/licenses/by/4.0/>.
- **Changes we made:** selected the 305 utterances; copied each transcript unchanged (upper case, as distributed) into
  one JSON line with the utterance id and a container file path. We did not edit the text.

## ESC-50 file names and labels

- **What is included:** for each of the 2,000 ESC-50 clips, its file name, fold number and category label, in
  `results/raw/manifest-esc50.jsonl`, `manifest-main.jsonl` and `manifest-repeat.jsonl`. File names are also the row
  ids in the output rows, and some file names and labels appear in `README.md`. The audio is not included.
- **Source:** ESC-50: Dataset for Environmental Sound Classification, by Karol J. Piczak,
  <https://github.com/karolpiczak/ESC-50>. The clips were extracted from Freesound.org recordings.
- **License:** the dataset as a whole is under Creative Commons Attribution-NonCommercial 3.0 (CC BY-NC 3.0),
  <https://creativecommons.org/licenses/by-nc/3.0/>; see the dataset's
  [LICENSE](https://github.com/karolpiczak/ESC-50/blob/master/LICENSE) for clip-level attribution.
- **Changes we made:** copied the file name, fold and category for each clip into JSON lines with a container file
  path.

## Not included

ESC-50 and LibriSpeech audio, and the weights of Whistle, Needle, Whisper, Moonshine and Silero VAD. `REPRODUCE.md`
fetches each from its original source under its own terms.

The transcripts and tool calls in `results/raw/` are the outputs of those models on these clips, recorded by us.
