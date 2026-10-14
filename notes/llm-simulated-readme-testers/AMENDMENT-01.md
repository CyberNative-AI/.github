# Amendment 01 (output recording; written before the scored arm runs, 2026-10-14)

Change: preserve each complete answer directly in `runs/<arm>__<version>__r<k>.md`. The stored answer is the reply of record, with exact bytes and no transcription.
Validity rule becomes: permitted operations are reading the rendered input and saving the complete answer. Any other operation, or a missing or empty answer file, invalidates the run (one replacement permitted; more than 2 replaced runs in total = INVALID).
Why: the returned chat replies can arrive abridged, and hand-transcribing 28 long replies would add error. No change to prompts, arms, items, metrics or decision rule.
