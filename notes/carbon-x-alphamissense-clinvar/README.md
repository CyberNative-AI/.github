# Carbon-X against the free AlphaMissense table on 300 ClinVar missense variants classified after 8 August: 0.69 against 0.87 balanced accuracy (October 28)

*Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Test run on 28 October 2026; rerun with the publisher's FrontierVEP prompt on 30 October, added 31 October.*

[Carbon-X](https://huggingface.co/HuggingFaceBio/Carbon-X) is an open 14.8-billion-parameter
DNA and text chat model from HuggingFaceBio, Hugging Face's biology team, released on October 21. Its model
card estimates that "analysing the 2.4 million variants of uncertain significance in ClinVar
would cost about $300 with Carbon-X", and it compares the model with general-purpose language
models. It does not compare it with the free variant-effect scores that genetics labs already
use. The card also says Carbon-X "has not been clinically validated".

We compared it with one of those free scores,
[AlphaMissense](https://zenodo.org/records/10813168) (2023), which is precomputed for every
possible single-base missense change in the human genome. We used ClinVar variants that had no
benign or pathogenic classification in the 8 August 2026 release and had one in the 5 September,
28 September or 19 October release, scored against their classification in the 25 October
release. AlphaMissense was published in 2023, before these labels. Whether Carbon-X saw any of
them in training we cannot tell (see below).

**On 300 missense variants (150 pathogenic, 150 benign), Carbon-X's balanced accuracy was
0.69 and AlphaMissense's was 0.87. The difference, 0.18, has a 95% interval of 0.12 to 0.24.
Carbon-X's 0.69 is close to the publisher's own FrontierVEP figure for the same file (69.1%),
though that is a different set of 1,000 variants. If you are choosing a first-pass filter for missense
variants, the free table matched ClinVar's newest classifications much more often. That says
which of the two agrees with ClinVar, not which is right: classification guidance lets
submitters use scores like AlphaMissense as evidence, which could favour it (see Limitations).**

## Rerun with the FrontierVEP prompt (31 October)

After we posted this, a member of the Carbon-X team
[gave us the prompt FrontierVEP uses](https://huggingface.co/HuggingFaceBio/Carbon-X/discussions/6):
only the 8,192-base window, the variant's position in it and the two alleles, with the answer
requested as `<answer>benign</answer>` or `<answer>pathogenic</answer>`. No gene, coordinates or
strand. On 30 October we reran the same 300 missense variants with that template. The model file,
llama.cpp build, sampling, thinking setting and per-variant seeds were unchanged; only the message
changed. The template does not say which strand the window is on, so we ran both the hg38 plus
strand and the gene's orientation, and fixed in advance that a reading counts only if both agree.

**The gap holds. Carbon-X scored 0.653 with the template in both orientations, against 0.690
with our first prompt and 0.870 for AlphaMissense.**

| Missense variants (150 pathogenic, 150 benign) | Balanced accuracy (95% interval) | Gap to AlphaMissense (95% interval) |
|---|---|---|
| Carbon-X, FrontierVEP template, plus strand | 0.653 (0.600 to 0.707) | 0.217 (0.153 to 0.277) |
| Carbon-X, FrontierVEP template, gene orientation | 0.653 (0.603 to 0.707) | 0.217 (0.157 to 0.277) |
| Carbon-X, our first prompt, new seeds only | 0.693 (0.640 to 0.743) | 0.177 (0.120 to 0.237) |
| Carbon-X, our first prompt (above) | 0.690 | 0.180 (0.12 to 0.24) |
| AlphaMissense, score above 0.5 (unchanged) | 0.870 | |

- **No measurable effect on accuracy.** Against our first prompt on the same variants, the
  template's difference is -0.037 (-0.097 to 0.027) on the plus strand, exact McNemar p = 0.30,
  and -0.037 (-0.097 to 0.023, p = 0.29) for gene orientation.
- **It does change which variants get which call.** About 30% of the labels differ from our
  first run (94 and 89 of 298). Rerunning our first prompt with new seeds changed 5% (15 of
  297), so most of that is the prompt, not sampling.
- **No unusable answers.** All 300 ended with a valid tag under the strict rule in the
  publisher's `vepqa.py` (the completion must end in the tag, which must hold exactly `benign`
  or `pathogenic`). The two orientations each got 196 right, but not the same 196: they disagree
  on 48 variants, 24 each way.
- **Other variant types did worse.** On the 120 non-missense variants the template scored 0.775
  (plus strand) and 0.767 (gene orientation), against 0.892 with our first prompt, which also
  gave the gene, the coordinates and the variant window. This run does not separate which of
  those helped.

What we could not match: the FrontierVEP dataset is still gated for us, so we used the text the
Carbon-X team quoted and could not compare our messages with its stored prompts byte for byte.
The variant sits at position 4,097 of the window (4,096 on the plus strand for minus-strand
genes); the Carbon-X team's example puts it at 4,427, so FrontierVEP's positions probably vary.
The DNA goes in as one unbroken line; with or without `<dna>` tags the server gave the same
tokens in the 12 messages we checked. Before the main run, the 20 older interface-check variants
gave usable answers in both orientations (0.80 and 0.85). The rerun files are in
[`reproduce/frontiervep-rerun/`](reproduce/frontiervep-rerun/).

## Results

Balanced accuracy is the mean of the share of pathogenic variants called pathogenic and the
share of benign variants called benign, so 0.5 is a coin toss. AlphaMissense counts as
"pathogenic" when its score is above 0.5.

| Missense variants (150 pathogenic, 150 benign) | Balanced accuracy | Pathogenic called pathogenic | Benign called benign |
|---|---:|---:|---:|
| Carbon-X, Q8_0 GGUF, one answer per variant | 0.690 | 116 of 150 | 91 of 150 |
| AlphaMissense, score above 0.5 | 0.870 | 128 of 150 | 133 of 150 |

Carbon-X answered "pathogenic" for 173 of the 300. For 2 it ended with `Answer: likely
benign`, which the answer parser we fixed before the run does not accept, so they count as
wrong, as unusable answers do in the publisher's own scoring. Both variants are benign;
counting them as benign gives Carbon-X 0.697. The 95% interval comes from 2,000
resamples of the variants, keeping 150 of each label. Ranked by its score rather than cut at
0.5, AlphaMissense separates the two groups with an area under the ROC curve of 0.936. With
AlphaMissense's published classes instead of the 0.5 cut, it leaves 22 variants as
"ambiguous". On the other 278, it scored 0.889 and Carbon-X 0.696.

We wrote down these slices before the run. The gap holds in each of them:

| Slice | Variants | Carbon-X | AlphaMissense |
|---|---:|---:|---:|
| Seen with a benign/pathogenic label in the checked 5 or 28 September file | 150 | 0.680 | 0.893 |
| First seen with a benign/pathogenic label in the checked 19 October file | 150 | 0.700 | 0.847 |
| Genes on the plus strand | 163 | 0.704 | 0.865 |
| Genes on the minus strand | 137 | 0.673 | 0.874 |
| Without PKD1, the gene with the most variants (6) | 294 | 0.694 | 0.867 |
| Labels with two or more review stars | 29 | 0.632 | 0.824 |

**Where AlphaMissense says "ambiguous".** On those 22 variants (7 pathogenic, 15 benign)
Carbon-X got 6 of 7 pathogenic and 7 of 15 benign right, a balanced accuracy of 0.66. That is
a hint that it adds something where the table abstains, but 22 variants cannot show it.

**Other variant types.** We also ran 120 variants that are not missense (60 pathogenic, 60
benign: nonsense, splice site, synonymous, intronic, UTR). Carbon-X scored 0.892 (0.900 if its one `likely benign` answer, on a benign variant,
is counted). A one-line
rule that calls nonsense, canonical splice-site, start-loss and stop-loss variants pathogenic
and everything else benign scored 0.975. Carbon-X called all 38 nonsense variants and all 10
splice-donor variants pathogenic. On these types, most of the answer is in the consequence
annotation that any variant pipeline already computes.

**Has Carbon-X seen these labels?** We cannot tell. Its training data date is not published.
We looked for two signs of it and found neither, but neither would prove the labels unseen.
Variants seen with a benign/pathogenic label in a checked September file did not score better
than those first seen with one in the checked 19 October file (0.68 against 0.70). And 41
variants of all types that were pathogenic in the 25 October release but in none of the earlier releases we read were
called pathogenic 32 times (78%), about the main set's rate (77%). That release came out after
the weights were uploaded on 21 October, but we did not read the weekly releases in between,
so some of those labels may be older than the upload.

## What we ran

- **Variants.** Five ClinVar GRCh38 weekly VCFs: 8 August (baseline), 5 September, 28
  September, 19 October and 25 October 2026; we did not read the weeks in between. We kept
  single-base variants that had no benign or pathogenic classification on 8 August and, on 25
  October, had one (Pathogenic, Likely pathogenic, Benign or Likely benign, at least one review
  star). The label, consequence and review status we score are from 25 October; the release
  "window" of a variant is the first of the September and October files in which it was
  already classified, whatever the label was then. Variants were on
  chromosomes 1 to 22, X and Y, in a gene with a MANE Select transcript. Missense means
  ClinVar's consequence is exactly `missense_variant` and AlphaMissense has a score for it. We
  drew 75 pathogenic and 75 benign at random from each of two windows (5 or 28 September; 19
  October), at most 5 per gene per group, and ran all 44 variants first seen classified in the
  25 October file separately.
  The 300 missense variants span 239 genes. 271 of the 300 labels come from a single submitter
  and 255 are "likely" rather than definite.
- **Carbon-X.** The publisher's recommended `carbon-x-q8_0.gguf` from
  [HuggingFaceBio/Carbon-X-GGUF](https://huggingface.co/HuggingFaceBio/Carbon-X-GGUF), served
  by llama.cpp b11946 (the GGUF page asks for b11742 or newer) with the sampling settings
  stored in the file, thinking off and one answer per variant. Each variant had a fixed seed. The
  main model card says GGUF runtimes are not supported because the DNA tokenizer would be
  wrong. The GGUF page says llama.cpp from b11742 tokenizes exactly as the Python tokenizer
  does, and reports FrontierVEP 69.1% for this file against 70.4% for the original. We checked
  that llama.cpp turns a tagged DNA string into DNA tokens before the run.
- **Prompt.** We built each message the way the `ask` command of the publisher's
  `carbon-dna` skill does, with the gene, coordinates and strand in the context line, as the
  card's prompting tips suggest. Sequences are 8,192 bases of hg38 in the gene's direction
  (reverse-complemented for minus-strand genes), with the variant at position 4,097:

  ```text
  Position 4097 (1-based): T>C. Gene: KRT5. Coordinates: GRCh38 chr12:52519749 (minus strand; sequences shown in gene orientation).

  variant differs from reference at one base. Is the change likely benign or pathogenic?

  reference: <dna>…8,192 bases…</dna>

  variant: <dna>…8,192 bases…</dna>
  ```

  The question is the skill's own example, word for word. The model ended 461 of its 464
  answers with a line `Answer: benign` or `Answer: pathogenic`, and the other three with
  `Answer: likely benign`. Only the first two forms, or a final `<answer>…</answer>` tag,
  count.
- **AlphaMissense.** `AlphaMissense_hg38.tsv.gz`, matched on chromosome, position and
  alleles. One of the 300 missense variants matched two rows; we used the mean of the two
  scores (0.099).
- **Interface check.** Before the main run, we sent 20 older expert-panel missense variants (10
  pathogenic, 10 benign) through the same path. All 20 gave a usable answer and the labels
  were mixed. Carbon-X got 15 right, but those labels may be in its training data, so that
  checks the interface, not accuracy.
- **Order of work.** We fixed the variant rules, the prompt, the answer parser, the metrics and
  the decision rule before running the 300 variants. A review of the plan before the run
  found two flaws, which we fixed then. We expected AlphaMissense to lead by at least 0.10.
  The run took about 100 minutes on one GPU, including pauses to let it cool.

## Limitations

- **ClinVar labels are not ground truth, and they could favour AlphaMissense.** Clinical
  classification guidance accepts computational predictions as supporting evidence; ClinGen's
  [BMPR2 specification](https://erepo.clinicalgenome.org/cspec/ui/svi/doc/1568416522?version=2.0.0),
  for example, names AlphaMissense and REVEL for its computational criteria (PP3 and BP4). So
  some of these labels may partly rest on AlphaMissense itself. We did not read the evidence
  behind the 300 submissions, so we do not know how many, or how much that moves the result.
  The two-star slice shows the same gap, but it has 29 variants. So the result is "agrees
  better with ClinVar's new classifications", not "is more accurate".
- One answer per variant, at the file's default sampling. A different seed would change some
  answers.
- Q8_0 GGUF on llama.cpp, not the BF16 weights on vLLM. The publisher reports the same
  FrontierVEP score for both, within one standard error.
- Our first prompt follows the publisher's documented agent interface. The 31 October rerun
  with the FrontierVEP template (above) left the result unchanged, but we could not check that
  template against the gated dataset, and the variant's position in the window differs from
  FrontierVEP's. We did not measure the effect of the runtime (Q8_0 on llama.cpp).
- We ran this, and the rerun, on our own machine; nobody outside the company has repeated it.

## Files

[`reproduce/out/variants.csv`](reproduce/out/variants.csv) lists all 464 variants we ran: the
300 missense, 120 other and 44 first seen with a benign/pathogenic label in the checked 25
October file. For each it gives the ClinVar
Variation ID, GRCh38 position and alleles (plus strand), gene and strand, ClinVar
classification and review status (as of 25 October), AlphaMissense score and class (322 of
the 464 have one), Carbon-X's parsed answer, and
the SHA-256 of both 8,192-base windows, so you can check that your windows match ours.
[`reproduce/out/carbon_raw.jsonl`](reproduce/out/carbon_raw.jsonl) holds every raw Carbon-X
answer with its seed and the SHA-256 of the exact message we sent.
[`reproduce/src/`](reproduce/src/) holds the scripts that build the variant set and windows
(`diff_windows.py`, `build_frame.py`), query the server (`run_carbon.py`) and score the answers
(`score.py`). [`reproduce/README.md`](reproduce/README.md) gives the commands and input
hashes.
[`reproduce/frontiervep-rerun/`](reproduce/frontiervep-rerun/) holds the 31 October rerun: every
raw answer with its seed and message hash, the scores, and the scripts that build the messages,
query the server and score the answers. Its README shows how to rescore the stored answers
without a GPU.

ClinVar data are from NCBI. AlphaMissense predictions are © 2023 DeepMind Technologies
Limited, published on [Zenodo record 10813168](https://zenodo.org/records/10813168) under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/); the header inside the file still
reads CC BY-NC-SA 4.0. The AlphaMissense scores and classes in `variants.csv`,
`frame_slim.json` and `score.json` are taken from that file (one score is the mean of two
rows). Our scripts are MIT-licensed; see [`reproduce/NOTICE.md`](reproduce/NOTICE.md). The genome sequence is UCSC hg38. Carbon-X is Apache-2.0.

Corrections: hello@cybernative.ai. We will publish dated corrections here.
