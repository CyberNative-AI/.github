Third-party material in this folder

This folder's own files (protocol, prompts, match rules, analysis scripts, verdict structure, results and notes) are Copyright 2026 CyberNative AI LLC and MIT-licensed (see LICENSE). Two kinds of third-party text appear inside them. Neither is relicensed by this folder, and the MIT license does not apply to it.

1. ActivityBot documentation (AGPL-3.0)

The model outputs (runs/*.md, repeated in adjudication/batch_*.md and adjudication/spotcheck_*.md), the adjudication quotes (adjudication/verdicts_*.json, adjudication/spotcheck_*), the match rules (GROUND_TRUTH.json, adjudication/BRIEF.md), the positive controls (controls/) and the notes (PROTOCOL.md, RESULTS.md, rerun/RERUN.md) contain short passages of the ActivityBot documentation (README.md, README_docker.md, README_nginx.md, README_caddy.md and .env.example at commits fd68596346075f9e74c4fe2026c97b7816eef545 and 92089ff3155720eed88bf3aaf3ae3def81de79e0 of https://gitlab.com/edent/activity-bot). Those passages are Copyright Terence Eden and remain under the GNU Affero General Public License v3.0, whose text is retained unchanged in UPSTREAM-LICENSE (the project's agpl-3.0.txt, identical at both commits). They appear as quotations inside critique and scoring.

No ActivityBot documentation files or code are bundled. The full documentation text given to the model (package/pre.md, package/post.md and the rendered prompts) is not included; src/build_package.py and src/render_prompts.py rebuild it from a clone of the public repository at the two commits above, and package/manifest.json and prompts/rendered/SHA256SUMS record its SHA-256 hashes.

2. Blog post "I paid people to try and follow my README" (CC BY-SA 4.0)

GROUND_TRUTH.json reproduces the bullet list from "I paid people to try and follow my README" by Terence Eden (11 October 2026), https://shkspr.mobi/blog/2026/10/i-paid-people-to-try-and-follow-my-readme/ (doi 10.59350/41s5v-7q247), in its "human" fields for H01-H11 and R01. PROTOCOL.md, RESULTS.md, rerun/RERUN.md and prompts/A2_simulated.txt quote short phrases from the same post. The post is licensed under the Creative Commons Attribution-ShareAlike 4.0 International License, https://creativecommons.org/licenses/by-sa/4.0/. The excerpts are reproduced without changes to their wording (quotation marks and apostrophes may be typed as plain ASCII characters) and remain under CC BY-SA 4.0. The match rules written next to them are our own operationalisation, not the author's words.

No endorsement by Terence Eden is claimed.
