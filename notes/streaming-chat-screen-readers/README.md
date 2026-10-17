# Stream a reply in Gradio or Open WebUI and the Orca screen reader speaks it in 13 to 19 overlapping pieces. In Chainlit, Streamlit and Panel it says nothing.

Most AI chat apps stream their replies word by word. A screen reader learns about new text on a page through ARIA live regions: parts of the page marked so that changes inside them are read aloud. What does a listener hear when a reply grows by a word every few dozen milliseconds inside one of them, or outside all of them?

We streamed the same reply (54 words, one word every 60 ms, about four seconds) through the default chat component of five current open-source chat UIs and logged every phrase the Orca screen reader sent to its speech synthesizer. We ran the whole study twice on the same machine, three trials per UI each time.

| Chat UI (version) | What Orca said, per trial (6 trials) | Live region holding the reply |
|---|---|---|
| Gradio 6.30.0, `ChatInterface` | 16 to 19 overlapping pieces of the reply, then "common.complete" | `div[role=log][aria-live=polite]` |
| Open WebUI 0.12.3 | 13 to 19 overlapping pieces of the reply | `ul[role=log][aria-live=polite][aria-relevant=additions]` |
| Chainlit 2.12.0 | nothing from the reply | none on the page |
| Streamlit 1.66.0, `chat_message` + `write_stream` | nothing at all | none on the page |
| Panel 1.9.4, `ChatInterface` | nothing at all | none on the page |

## Gradio and Open WebUI: the paragraph, again and again

Orca reads the paragraph that is growing, then reads it again when it has grown, a new phrase every 150 to 210 ms (median gap between phrases, per trial). This is Gradio, first run, trial 1, as sent to the synthesizer; `ZETAEND` is a marker word we put at the end of the reply:

```
Loading
Tell me about Lyon
Lyon sits
Lyon sits where the Rhone
Lyon sits where the Rhone meets the
Lyon sits where the Rhone meets the Saone, about four
Lyon sits where the Rhone meets the Saone, about four hundred kilometres
Its
Its old town is
Lyon sits where the Rhone meets the Saone, about four hundred kilometres southeast of Paris. Its old town is a protected heritage
Lyon sits where the Rhone meets the Saone, about four hundred kilometres southeast of Paris.
Its old town is a protected heritage site, known for narrow covered passages called traboules.
...
Most visitors find two days enough to see the centre ZETAEND
common.complete
```

Each new line can cut off the one before it, so these are attempts to speak, not words a listener heard in full. The opening sentence comes back again and again while later parts are skipped. In two of the six Gradio trials Orca never reached the closing sentence at all. In five of the six Open WebUI trials, the first list item, "Take the funicular up Fourviere hill", was never spoken in full.

The re-reading was the same in both runs. Whether Orca caught the reply's last word was not: it did in all three Gradio trials of the first run and in none of the second. Both UIs show the same pattern, and Orca re-read on every trial.

The last thing Gradio announces, in all six trials, is `common.complete`. That is a translation key. Gradio's status tracker announces `i18n("common.complete")` when a response finishes ([`LiveStatus.svelte`](https://github.com/gradio-app/gradio/blob/main/js/statustracker/static/LiveStatus.svelte), added on 18 September 2026 in [#13861](https://github.com/gradio-app/gradio/pull/13861)). Gradio's English strings ([`en.json`](https://github.com/gradio-app/gradio/blob/main/js/core/src/lang/en.json)) have `complete` under `chatbot` but not under `common`, so the raw key reaches the screen reader. The same holds for the strings built into the installed 6.30.0 package.

Open WebUI marks the whole transcript as a log that should announce only additions ([`Messages.svelte`, line 519 in v0.12.3](https://github.com/open-webui/open-webui/blob/v0.12.3/src/lib/components/chat/Messages.svelte#L519)). Orca re-read the changed text anyway.

## Chainlit, Streamlit and Panel: silence

None of the three pages has a live region anywhere, including inside shadow roots (Panel's page has 59). So a screen reader that relies on live regions announces nothing: not the reply, not that a reply has started, not that it has finished. The user has to know to go and look. The reply is still on the page, and a user can move to it and read it; we did not measure that.

Orca's silence alone would not prove much, because Orca also dropped a correctly announced reply about half the time (next section). The evidence for silence is that the page structure has no live region in either run, and the virtual screen reader below reported nothing in all six trials for each of the three UIs. Orca agreed in all six.

A Chainlit pull request that would have announced "generating" without streaming the text ([#3014](https://github.com/Chainlit/chainlit/pull/3014), August 2026) was closed by the stale bot after about five weeks without a maintainer review, so it is not in 2.12.0.

## Check your own chat page

[`live-region-check.js`](live-region-check.js) is a DevTools console snippet. Paste it before you send a message, wait for the reply to finish, then run `liveCheck("words from the end of the reply")`. It lists the page's live regions, says whether the reply's last words sit inside one, and counts the changes inside live regions while the reply streamed. Many changes inside a live region is the Gradio and Open WebUI pattern; no live region at all is the Chainlit, Streamlit and Panel pattern.

It only reads the page structure. It cannot tell you what a screen reader will say, and the next section is why that matters.

## Two things we expected to work did not

**A virtual screen reader passed Open WebUI.** We ran the same pages through a scriptable virtual screen reader ([Guidepup's](https://github.com/guidepup/virtual-screen-reader), the kind used in unit tests and CI). It found the same pattern as Orca on four of the five UIs in both runs (re-reading in Gradio, silence in Chainlit, Streamlit and Panel), but not on Open WebUI. There, in all six trials, it announced each new word once, as a separate phrase, so a check built on it sees no repetition; Orca instead re-read the changed text. A CI check built on it would pass this pattern.

**"Add the finished reply once" was not reliable either.** A common suggestion is to keep the streaming text out of the live region and add the complete reply to it once at the end. We built that as a control page. Over both runs Orca spoke it in 12 of 25 trials (95% interval for the drop rate: 33% to 70%). In the 13 silent trials Orca was still working: it announced the Send button each time, and in 6 of them it read the user's prompt, then nothing. Orca never failed the other two control pages: a page with no live region stayed silent and a page that grows the reply inside a live region was re-read, 25 of 25 trials each over both runs.

That failure is also why our pre-registered ruling is **invalid**. The study required Orca to speak that control in at least 2 of 3 trials before and after the five UIs. In the first run it spoke it 1 of 3 times at the end; in the second, 1 of 3 at the start and 0 of 3 at the end. The results above are our reading after the fact, not the ruling we committed to. The control failures we saw only removed speech; they cannot produce the extra readings in Gradio and Open WebUI.

So we are not recommending a fix. Whatever you change, test it with a real screen reader, more than once.

## Limits

- One screen reader: Orca 48.1 with Chromium 155 on Linux. NVDA, JAWS and VoiceOver handle live regions differently; we did not test them.
- One reply, one speed (a word every 60 ms), default settings, desktop size, three trials per UI per run. Panel's first-run trials were run again with a corrected test driver; the superseded trials stay in `transcripts/`.
- We logged what Orca sent to the synthesizer. We did not measure what a listener heard, keyboard use, mobile, or reading the reply by moving to it.
- Executed twice on our own machine: the second run used a freshly built screen-reader image and freshly installed test tooling, from the committed code. Not independently reproduced on other hardware.
- The versions are the ones current on 17 October 2026. New screen-reader reports and fixes were being opened in Open WebUI that day (for example issue [32610](https://github.com/open-webui/open-webui/issues/32610)); newer versions may differ.

## Files

- [`transcripts/`](transcripts/): every trial from both runs, Orca and virtual reader, as JSON, with the scored classes. [`transcripts/README.md`](transcripts/README.md) maps the folders to runs.
- [`method/score.py`](method/score.py): the scorer, with scoring logic unchanged from the pre-registered version. `python3 method/score.py transcripts/run1-orca --oracle orca --json out.json && cmp out.json transcripts/run1-orca.score.json` reproduces a committed score file byte for byte; the same works for each folder.
- [`apps/stream_text.py`](apps/stream_text.py): the streamed reply. [`controls/`](controls/): the control pages.
- [`live-region-check.js`](live-region-check.js) and its test.
- [`SHA256SUMS`](SHA256SUMS): checksums for every file above.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai. We publish
corrections as dated notes on this page.
