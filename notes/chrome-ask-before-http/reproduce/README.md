# Reproduce: Chrome's ask-before-HTTP default and the top 1 million origins

| file | what it is |
|---|---|
| `counts.json` | Aggregate counts from the October 20 run: per group, how each origin behaved in Chrome 155 → Chrome 157; by port; by rank bucket; control sites; the `HttpsOnlyMode=disallowed` retest. No origin names except the public control sites. |
| `check.py` | Recomputes every number in the note from `counts.json`. Given seed files, also checks Google's configuration. |
| `seedparse.py` | Decodes the ask-before-HTTP study from a Chrome variations seed. |
| `seed-reads-20261020.txt` | Our decoded read of the stable seeds for Windows, macOS, Linux and Android, milestones 154–157, with the SHA-256 of each seed. |
| `nav.mjs` | The loader: one fresh Chrome profile per origin, raw DevTools protocol, records how the navigation ended. |
| `sample.py`, `score.py` | How the sample was drawn and how each origin was classified and scaled to the whole list. |

## Check the numbers

```sh
python3 -I check.py
```

Prints one `PASS` line per number and exits 0.

## Check Google's configuration yourself

```sh
curl -o seed.bin 'https://clientservices.googleapis.com/chrome-variations/seed?osname=win&channel=stable&milestone=155'
python3 -I check.py seed.bin
```

`osname` can be `win`, `mac`, `linux` or `android`. A `PASS` line shows the study, the share of
browsers it enables the feature for (100 of 100 on October 20), its version range, channel and
platform. Google can change this configuration at any time.

## Run the test again

You need the two Chrome for Testing builds (155.0.8059.84 and 157.0.8103.6, linux64), Node 22
or later, and the list `data/global/202609.csv.gz` from
[zakird/crux-top-lists](https://github.com/zakird/crux-top-lists).

1. Make a working folder with `src/` (copy `sample.py`, `score.py`, `nav.mjs` into it) and
   `raw/crux-202609.csv.gz`.
2. `python3 -I src/sample.py` writes `out/sample.txt` and `out/sample-meta.json`: every HTTP
   origin in the rank buckets up to 100,000, plus 500 at random from the rest (seed 15015).
   Our October 20 run used the same top group and a different random 500, which we do not
   publish because it would name individual sites.
3. Run the loader once per Chrome build, each with `--disable-field-trial-config`:

   ```sh
   EXTRA_FLAGS=--disable-field-trial-config node src/nav.mjs /path/to/chrome-155/chrome a155 out/sample.txt out/a155.jsonl 8
   EXTRA_FLAGS=--disable-field-trial-config node src/nav.mjs /path/to/chrome-157/chrome a157 out/sample.txt out/a157.jsonl 8
   ```

   The loader starts Chrome with `--no-sandbox`, so run it inside a container or a throwaway
   machine. It writes one JSON line per origin. We ran origins that failed once more and kept
   the later line.
4. `python3 -I src/score.py out/a155.jsonl out/a157.jsonl > out/score.json`

Load `http://http.badssl.com`, `http://httpforever.com` and `http://example.com` before and
after: the first two should open over HTTP in 155 and be stopped in 157; the third should open
over HTTPS in both. If they don't, the run is not comparable.

For the policy retest, put `{"HttpsOnlyMode": "disallowed"}` in a `.json` file in the managed
policy folder your build reads (for Google Chrome on Linux, `/etc/opt/chrome/policies/managed/`),
confirm at `chrome://policy` that it applies, and load stopped origins again in 157.

Your network will reach a different set of sites than ours did (19.6% of ours did not answer),
so expect the counts to move a little.
