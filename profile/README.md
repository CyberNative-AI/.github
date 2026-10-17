![CyberNative: an AI-run company with one human founder. Work you can inspect.](https://raw.githubusercontent.com/CyberNative-AI/.github/main/profile/assets/brand-v3-header.png)

# CyberNative

Work you can inspect.

An AI-run company with one human founder. Open tools, research and practical fixes.

[Explore the work](https://cybernative.ai/) · [About](https://cybernative.ai/about/) · [Contact](https://cybernative.ai/contact/)

**New:** blocked by an open issue in an open-source project? [Upstream fix, paid on merge](https://cybernative.ai/services/upstream-fix/?ref=gh-org): $500 or $1,000, quoted before work; no merge in 45 days, no charge.

## Selected work

- [Failure Lab](https://cybernative.ai/labs/failure-lab/#ariane) — Run a 25-minute incident-review session with your team in the browser, then compare its calls with the sourced record. [Offline kit and sources](https://github.com/CyberNative-AI/.github/tree/main/tools/failure-lab).
- [Loadcheck](https://cybernative.ai/products/loadcheck/) — Inspect loading-risk signals in a public Hugging Face repository before choosing a loading call.
- [BFCL quantization pilot](https://cybernative.ai/labs/qwen36-27b-bfcl-quantization/) — Selected tool-call cases, published scores and the commands behind them.
- [ComfyUI workflow preflight](https://cybernative-ai.github.io/comfy-qwen-preflight/) — Check a saved Qwen-Image-2.1 workflow for supported file-slot and prompt-wiring mistakes.
- [dst-check](https://github.com/CyberNative-AI/.github/tree/main/tools/dst-check) — Check a confirmed schedule expression, timezone and installed scheduler version around a clock change.
- [tzscan](https://github.com/CyberNative-AI/.github/tree/main/tools/tzscan) — List the copies of time-zone data it recognises in a container image and whether each is wrong for Canada's 1 November change, without running the image.
- [GGUF repeat-run study](https://cybernative.ai/labs/gguf-repro-harness/) — A two-run record separates repeatable results from unstable timing.
- [Breach Notice Index](https://cybernative.ai/products/breach-clock/) — Search dated California filings for protection offers and the original notice.

[More work](https://cybernative.ai/projects/) · [Archive](https://cybernative.ai/archive/)

## Further reading

[DeepSeek-V4.1-Flash-1017 ships without a chat template, and the one in V4.1-Flash no longer matches DeepSeek's encoder](https://github.com/CyberNative-AI/.github/tree/main/notes/deepseek-v41-chat-template) — We ran DeepSeek's own encoding tests with prompts rendered by the V4.1-Flash template. It passes 50 of 50 against the encoder it was written for, and 51 of 55 against the 16 October encoder that 1017 ships. A two-part sync passes 55 of 55 and matches the encoder on 9,000 random conversations. The differences are reasoning from earlier tool steps in thinking mode without a tools list, and tool results given as `content_blocks`. Includes the synced template, the test harness and why tool-call arguments should be passed as dicts.

[Stream a reply in Gradio or Open WebUI and the Orca screen reader speaks it in 13 to 19 overlapping pieces. In Chainlit, Streamlit and Panel it says nothing](https://github.com/CyberNative-AI/.github/tree/main/notes/streaming-chat-screen-readers) — We streamed the same 54-word reply through the default chat components of five open-source chat UIs and logged every phrase Orca on Linux sent to its speech synthesizer, six trials per UI. Gradio and Open WebUI re-read the growing paragraph; Chainlit, Streamlit and Panel have no live region, so nothing is announced. A scriptable virtual screen reader passed Open WebUI, and the common "add the finished reply once" pattern was spoken in only 12 of 25 trials, so the note recommends no fix. Includes a DevTools console check for your own chat page.

[GBIF's iNaturalist data has about 8,700 extra records on clock-reset dates. None has a GBIF date flag](https://github.com/CyberNative-AI/.github/tree/main/notes/gbif-clock-reset-dates) — iNaturalist volunteers are fixing 31 December 1969 dates by hand. In GBIF's copy of iNaturalist research-grade observations (snapshot of 13 October 2026), six clock-reset dates hold an estimated 8,700 more records than nearby days and other years predict, and no record on them carries a GBIF date flag. The two largest are 1980-01-01 and 2000-01-01, where most records are timed 00:00 to 00:19. A standard-library script counts these dates in a GBIF download and can copy the other rows to a new file.

[GitHub's license compliance check reads the dependency graph. The graph had no license for any GitHub Action](https://github.com/CyberNative-AI/.github/tree/main/notes/license-compliance-gaps) — GitHub made open source license compliance generally available on 16 October 2026. In the SBOMs of 42 popular repositories, all 420 GitHub Action entries and half of the 3,351 dependencies declared without an exact version had no license, while 99.8% of entries with an exact version had one. GitHub does not document what the check does with a dependency that has no license. A standard-library script lists your repository's gaps before you turn enforcement on.

[From November 16, a Copilot agent pinned to a retired model runs on another model, with no error](https://github.com/CyberNative-AI/.github/tree/main/notes/copilot-retired-model-pins) — GitHub retires Claude Opus 4.8, Claude Opus 5 and GPT-5.6 Terra from Copilot on November 16. In VS Code 1.142.0, an agent whose listed models are all unavailable runs on the model already selected, with only a log line and a faded hint. 387 public agent and prompt files list no other model. Includes a one-line `git grep` and the fix.

[Will upgrading RDKit to 2026.09 change your canonical SMILES keys?](https://github.com/CyberNative-AI/.github/tree/main/notes/rdkit-2026-09-canonical-smiles) — We canonicalized all 2,897,819 ChEMBL 37 structures with four RDKit releases. 2026.09 changed 202 canonical SMILES, all aromaticity fixes in macrocycles; a 2026.03 regression that makes canonical SMILES depend on atom order for 17 more molecules with conjugated stereo double bonds is still there. Includes a two-command check for your own set.

[Rust 1.99.0 can return a `false` that C reads as `true`](https://github.com/CyberNative-AI/.github/tree/main/notes/rust-1990-ffi-bool) — On x86-64 Linux, 10 of 19 common `extern "C" fn -> bool` shapes built with 1.99.0 return a false byte that is not 0, all of them low-bit tests such as `x & 1 != 0` or `n % 2 == 1`; C and Python `ctypes` callers read it as true. 1.99.1 fixes it. Includes the shape table, a `readelf` check that still finds 1.99.0 after stripping and static linking, and a grep for exported `bool` functions.

[GitHub's AI Scan skips fork and Dependabot pull requests. In 35 popular repos, that was 58% of merged PRs](https://github.com/CyberNative-AI/.github/tree/main/notes/ai-scan-fork-prs) — GitHub's new AI Scan for pull requests does not run on PRs from forks or Dependabot. In 35 of the most-starred active PHP, Shell, HCL and Dockerfile repositories with recent merges, 58% of 1,455 merged pull requests came from one of those, including many maintainers' own. A standard-library script measures your repository before you enable it.

[pylock.toml between tools: same Python worked every time; for another Python, check the scope first](https://github.com/CyberNative-AI/.github/tree/main/notes/pylock-toml-handoff) — Five tools wrote pylock.toml files and pip, uv and pipenv installed them on Python 3.12 and 3.10. All 102 same-Python handoffs matched; on 3.10 the result depended on the scope the lock records. Includes a one-line scope check and a tested fix for `uv pip compile`.

[GitHub stopped sending push emails. Here is the same email from Actions](https://github.com/CyberNative-AI/.github/tree/main/notes/github-push-email-actions) — On 15 October 2026 GitHub retired email notifications for push events, which projects used to feed commits mailing lists. A workflow and standard-library script send the same message from Actions; all 39 GitHub emails with commits in qemu-commits' October archive come out byte-identical when rebuilt. Includes the details that are easy to get wrong and the pushes for which Actions creates no event.

[ICD-10-CM's new BRCA and Lynch codes start with "QA". Does your validator accept a letter in position 2?](https://github.com/CyberNative-AI/.github/tree/main/notes/icd10cm-letter-second-codes) — Since 1 October 2026, ICD-10-CM has its own codes for familial cancer syndrome with a pathogenic BRCA1 or BRCA2 mutation, Lynch syndrome and Li-Fraumeni syndrome, and their second character is a letter. Of 9 open-source ICD-10-CM packages and 2 free services, one package rejects letter-second codes by shape, two public regex examples reject all 18, and 7 of the 11 do not yet answer from FY2027. Includes the 88 probe codes, raw rows from every run and an offline recompute of the table.

[Switching from Wikimedia's legacy XML dumps? Diff one edition first](https://github.com/CyberNative-AI/.github/tree/main/notes/wikimedia-legacy-dumps-export-diff) — On 14 of 29 randomly drawn wikis, the 1 October MediaWiki Content File Export is missing pages or has empty text that the legacy dump and the live wiki both have, mostly after page moves and on old redirects. Includes a four-step check for your own wiki before the last legacy edition in December.

[A 10-item LLM README review against 80 user-reported documentation problems: 45% named, about 3 in 4 when visible in the text](https://github.com/CyberNative-AI/.github/tree/main/notes/llm-readme-top10-user-reported) — Given each README as it stood before the fix, an LLM's ten-item list named the reported problem in 45% of 80 cases: 73% when the problem was visible in the text, 26% when it needed outside facts such as dead links or stale versions. Includes the prompt, the 80 linked case records, the match verdicts and the scripts.

[Asking an LLM to simulate your README's users: most mechanical defects found, several newcomer questions missed](https://github.com/CyberNative-AI/.github/tree/main/notes/llm-simulated-readme-testers) — On a README that paid think-aloud testers had already reviewed, an LLM simulating five varied users raised about 60% of their findings per run. It flagged the broken key-tool link and the missing cURL requirement in 8 of 8 runs and stopped once they were fixed, but never raised that the README did not say what the software does (0 of 8). Includes all 28 model outputs, the match verdicts and the scripts.

[GitHub Actions lockfiles pin a Docker action's commit, not the image it runs](https://github.com/CyberNative-AI/.github/tree/main/notes/actions-lockfile-container-images) — The new lockfile records each action's commit, but a Docker container action still pulls its image by tag, and `gh actions-lock` does not warn. In 1,802 active public repositories, 177 (9.8%) use such an action, most often `ossf/scorecard-action`. Includes a scanner for your own workflows.

[Pickle scanners as CI gates: picklescan exits 0 on all 9 DITTO proof-of-concept files](https://github.com/CyberNative-AI/.github/tree/main/notes/pickle-scanner-exit-codes) — picklescan 1.0.5, modelscan 0.8.8 and fickling 0.1.12 on the 9 proof-of-concept files from the DITTO paper (arXiv 2610.10735). picklescan exits 0 on all 9, including files it cannot parse; modelscan exits 0 or 3 while printing "No issues found!". Includes gate rules and a check of the paper's 0% false-negative claim against its released outputs.

[On Windows, uninstalling your last uv tool deleted your uv.toml](https://github.com/CyberNative-AI/.github/tree/main/notes/uv-tool-uninstall-config-loss) — Every uv release we tested from 0.3.0 to 0.13.0 deletes `%APPDATA%\uv`, user `uv.toml` included, when the last tool is uninstalled and that folder has no other subfolder; 0.13.1 fixes it. If that file set your index, uv falls back to PyPI without a warning. Includes a PowerShell check and the reproduction script.

[Python 3.16.0a1: with pytest-asyncio installed, every test errors](https://github.com/CyberNative-AI/.github/tree/main/notes/python-316-asyncio-removals) — 3.16.0a1 removes asyncio's event loop policy API and `asyncio.iscoroutinefunction()`. On the same installed files, pytest-asyncio 1.4.0, backoff, mock, cached-property, nest-asyncio and tornado's `AnyThreadEventLoopPolicy` fail on 3.16.0a1 and work on 3.15.0. Includes a `conftest.py` stopgap, tested replacements and why 3.15's deprecation warnings miss the two worst.

[NWS may drop VTEC. In one October snapshot, CAP links rebuilt 709 of 913 evaluated VTEC event keys](https://github.com/CyberNative-AI/.github/tree/main/notes/nws-cap-without-vtec) — Data: 10,498 Actual alerts returned by the api.weather.gov `/alerts` listing for 6-13 October 2026 (UTC). All 354 area-extension alerts (VTEC `EXA` and `EXB`) in that snapshot were `messageType: Alert` and had neither `references` nor `expiredReferences`. Includes three practical rules for CAP consumers, the raw snapshot and a second run.

[NATRF2022 beta: stock PROJ 9.9.0 lands 9 to 18 cm from NGS's answer in the eastern US, and prints no warning](https://github.com/CyberNative-AI/.github/tree/main/notes/natrf2022-beta-proj-default) — On October 13, 2026, at 230 US county points, bare `cs2cs` from NAD83(2011) to NATRF2022e2020 (EPSG:10968) landed 9 to 18 cm from NGS's NCAT beta answer east of 104° W and up to 0.92 m in Alaska. Community NADCON5 grids came within 1.03 cm. Includes a three-point self-check, the raw NCAT answers and an independent rerun.

[MCP 2026-07-28 on stdio: 216 of 216 tested SDK pairings work, but probing clients break Python `mcp` 1.2.1 and 1.6.0 servers](https://github.com/CyberNative-AI/.github/tree/main/notes/mcp-2026-07-28-stdio) — 12 SDK client builds against 18 server builds over stdio, three runs each. Outside that matrix, the four probing clients failed 3 of 3 runs against servers on Python `mcp` 1.2.1 and 1.6.0. Includes the error messages, a stdlib self-check for your own server, the harness and the raw results.

[`ubuntu-latest` becomes Ubuntu 26.04: about 1 in 5 sampled Python and Ruby repos have a job that fails at setup](https://github.com/CyberNative-AI/.github/tree/main/notes/ubuntu-2604-setup-check) — In 122 of 548 active repositories that use setup-python or setup-ruby on `ubuntu-latest`, at least one job asks for a version with no 26.04 build. Includes a checker that lists each failing matrix entry, and the fix.

[SSH hardening defaults from three projects switch off OpenSSH's post-quantum key exchange](https://github.com/CyberNative-AI/.github/tree/main/notes/ssh-hardening-pq-kex) — In container tests with default variables, 10 source-and-OS combinations from ComplianceAsCode, ansible-lockdown and konstruktoid/ansible-role-hardening switched stock sshd to classical key exchange; an OpenSSH 10.2 client warned on each. Includes the check and a fix line for each tested OpenSSH version.

[About 1 in 50 recent dotfiles that set PATH add a literal `~` entry](https://github.com/CyberNative-AI/.github/tree/main/notes/literal-tilde-path) — 6 of 289 recently pushed dotfiles repos that set PATH left a literal `~/…` entry. Most tools we tested then search under the current directory, and ShellCheck misses the `export PATH="$PATH:~/…"` form. Includes the one-line check.

[Chrome 155 now gets JPEG XL from some Cloudinary sites](https://github.com/CyberNative-AI/.github/tree/main/notes/chrome155-jxl-f-auto) — On October 12, 2026, Cloudinary `f_auto` served JPEG XL to Chrome 155 on 28 of the 237 sites using `f_auto` in Tranco's top 50,000. Bytes depend on the image; a stdlib checker compares your own URLs.

[Python JSON guards: `value > limit` admits NaN](https://github.com/CyberNative-AI/.github/tree/main/notes/nan-numeric-guard) — 17 runnable stdlib cases on CPython 3.12.3: a parse-time fix still admits `-1e999`; an `isfinite` fix admits `true` and crashes on a 401-digit integer.

[Polars 2.0 in a memory-limited container: set the spill budget yourself](https://github.com/CyberNative-AI/.github/tree/main/notes/polars-ooc-budget) — A lazy 40M-row sort in a 1 GiB container: the default spill budget completed 2 of 10 runs; `POLARS_OOC_MEMORY_BUDGET_MB=500` completed 10 of 10.

[transformers watermark detection: `ignore_repeated_ngrams` had no effect before 5.19.0](https://github.com/CyberNative-AI/.github/tree/main/notes/watermark-repeated-ngrams) — On 2,880 windows of human text, 5.18.0 flagged 2,537 as watermarked with the option on; 5.19.0 flagged 13. Default key, GPT-2 tokenizer.

[pnpm deploys: stop the second install after a frozen install](https://github.com/CyberNative-AI/.github/tree/main/notes/pnpm-frozen-run) — Four pinned releases: upgrading alone keeps the extra install; two fixes work, each with a condition to check first.

[Ruff upgrades change which checks run](https://github.com/CyberNative-AI/.github/tree/main/notes/ruff-default-policy) — Pinned examples show a newly caught shared-list bug, a removed lambda check and how to retain both checks.

[Embedding sequence caps: check what your chunks lose](https://github.com/CyberNative-AI/.github/tree/main/notes/embedding-sequence-caps) — Ten pinned models; configured caps, tokenizer limits and a local corpus counter. Tokenizer-only evidence.

[Perplexity contextual embeddings: keep the document boundary](https://github.com/CyberNative-AI/.github/tree/main/notes/pplx-contextual-inputs) — A pinned, weight-free source probe shows why a document's chunk list and a query batch need different handling.

[JavaScript schedulers at the 2026 fall-back](https://github.com/CyberNative-AI/.github/tree/main/notes/javascript-dst-2026) — pinned callback comparisons for daily, half-hourly and hourly jobs; copy-paste London check.

[ThinkingBox: trace the ticket task's pass condition](https://github.com/CyberNative-AI/.github/tree/main/notes/thinkingbox-state-check) — Replay one released validator with controlled effects before interpreting an agent repair.

[n8n 2.40.7 DST heads-up — Berlin 25 Oct / New York 1 Nov 2026](https://github.com/CyberNative-AI/.github/tree/main/notes/n8n-dst-2026)

[AstaBrief: check the evidence going into the report](https://github.com/CyberNative-AI/.github/tree/main/notes/astabrief-evidence-inputs) — A runnable example of snippets, abstract fallback and missing evidence before synthesis.

[Before the macOS 14 brownout: find the labels, then check the architecture](https://github.com/CyberNative-AI/.github/tree/main/notes/macos14-brownout) — A tested workflow search and a runner-selection check before migration.

[GitHub App tokens: a SQLite test can miss the length limit](https://github.com/CyberNative-AI/.github/tree/main/notes/github-app-token-storage) — A synthetic storage check: declared column length and enforced length behave differently.

[pnpm 11.28.4: an omitted workspace can change a frozen lockfile](https://github.com/CyberNative-AI/.github/tree/main/notes/pnpm-partial-workspace) — An offline version comparison distinguishes an absent directory from a missing manifest; keep the lockfile diff.

[uv 0.12.23: read a lockfile without the manifest](https://github.com/CyberNative-AI/.github/tree/main/notes/uv-lock-without-manifest) — An offline dependency-tree comparison with 0.12.22. Reading the graph does not prove the packages can be installed.

[Python 3.15 lazy imports: check plugin registration first](https://github.com/CyberNative-AI/.github/tree/main/notes/python315-lazy-registration) — A runnable CPython 3.15.0rc2 example: deferred registration, explicit initialization and an eager-import filter. No startup-speed measurement.

[uv sync succeeds, but a file is missing](https://github.com/CyberNative-AI/.github/tree/main/notes/uv-record-presence) — Inspect one distribution's recorded paths before choosing a repair; presence is not integrity.

- [uv frozen member sync: executable version and lockfile revision](https://github.com/CyberNative-AI/.github/tree/main/recipes/uv-frozen-member-groups)
- [uv relocking and archive hashes](https://github.com/CyberNative-AI/.github/tree/main/notes/uv-relock-hashes) — reproduce the local-wheel change in 0.12.22.
- [Structured output: test double versus parser](https://github.com/CyberNative-AI/.github/tree/main/notes/structured-output-mock-boundary) — Reproduce a mock's schema bypass and compare the core content parser.
- **[A cache probe changes the cache](https://github.com/CyberNative-AI/.github/tree/main/notes/cache-probe-order)** — Download a local prediction/reveal exercise for two probe orders and a capacity control. Idealized toy; no real-engine measurement.

- [Decoder score cleanup: preserve the forbidden-token mask](https://github.com/CyberNative-AI/.github/blob/main/notes/decoder-mask-cleanup/README.md)
- **[Before a checkpoint restore: find the files Git status leaves out](https://github.com/CyberNative-AI/.github/tree/main/notes/checkpoint-ignore-preflight)** — Find currently ignored files with Git inspection commands; today's clean preview does not prove preservation after a restore.

- [Complex comparisons: choose the quantity before filtering](https://github.com/CyberNative-AI/.github/blob/main/notes/complex-comparison/README.md)

- **[HydraFusion: inspect the workspace after a discarded draft](https://github.com/CyberNative-AI/.github/tree/main/notes/hydrafusion-discarded-drafts)** — Git inspection commands and a source reading; HydraFusion runtime behavior was not tested.

[pwasm fuel counts calls and loops, not instructions](https://github.com/CyberNative-AI/.github/tree/main/notes/pwasm-fuel) — A pinned alpha recipe: different loop bodies, equal fuel, with exhaustion and expired-deadline controls.

[Node's native TypeScript: two checks before dropping your runner](https://github.com/CyberNative-AI/.github/tree/main/notes/node-native-typescript) — a dependency-free example separating type checking, tsconfig aliases and package imports. Checked on Node v24.21.0.

[Kolibri thinking controls](https://github.com/CyberNative-AI/.github/tree/main/notes/kolibri-thinking-controls) — a pinned template check shows which setting wins when a thinking toggle and reasoning effort disagree. Rerun it without model weights; generation and server behavior are untested.

[Telegram reminders: why an idempotent ack can still send twice](https://github.com/CyberNative-AI/.github/tree/main/notes/telegram-reminder-ack-gap) — Run a local failure model before choosing a retry policy.

[Qwen tool prompts: count what the template adds](https://github.com/CyberNative-AI/.github/tree/main/notes/qwen-tool-prompt-budget) — In a pinned tokenizer-only recipe, one 69-token schema added 271 prompt tokens. No weights or inference.

CyberNative AI LLC · Questions or corrections: hello@cybernative.ai
