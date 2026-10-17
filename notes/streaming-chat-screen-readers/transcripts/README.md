# Transcripts

One JSON file per trial. Orca files hold `speech`: each phrase Orca sent to the speech synthesizer, with a time stamp.
Virtual-reader files hold `vsr` (the virtual screen reader's spoken phrase log) and `struct` (live regions found on the page).
`<folder>.score.json` is the output of `python3 ../method/score.py <folder> --oracle orca|vsr --json <folder>.score.json`.
These public transcript copies omit test-service URLs. Speech, timing, DOM observations and scoring inputs are unchanged.

| Folder | Run | Contents |
|---|---|---|
| `run1-orca`, `run1-vsr` | first run | Gradio, Chainlit, Streamlit, control pages before the UIs (`gate1-*`). `panel-*` here is superseded: our first test driver did not search Panel's nested shadow roots deeply enough to see the reply finish, so Panel was run again with a corrected driver in `run2-*`. |
| `run2-orca`, `run2-vsr` | first run, second batch | Open WebUI, Panel, control pages (`gate2-*`, `gate3-*` after the UIs) |
| `rerun1-orca`, `rerun1-vsr` | second run | all five UIs, control pages before (`gate1-*`) and after (`gate3-*`) |
| `rerun1-extra-orca` | second run | 10 extra Orca trials of each control page (`xtra-*`, two batches of 5) |

Control pages: `silent` (reply added outside any live region), `once` (complete reply added once to a `role=log` region), `chatter` (reply grows word by word inside a polite live region).
