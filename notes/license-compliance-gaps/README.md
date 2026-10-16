# GitHub's new license check reads the dependency graph. In 42 popular repos, the graph had no license for any GitHub Action.

On 16 October 2026 GitHub made [open source license compliance](https://github.blog/changelog/2026-10-16-open-source-license-compliance-generally-available) generally available for GitHub Enterprise Cloud repositories with Code Security. An enterprise sets one license policy and targets repositories with a ruleset condition, "Require license compliance results before merging". On pull requests that add or change dependencies, the check annotates each dependency whose license the policy does not accept.

The check can only judge licenses the dependency graph knows. GitHub's [August changelog](https://github.blog/changelog/2026-08-13-license-data-quality-improvements) says the graph's license data is what appears in "software bills of materials (SBOMs), the open source license compliance feature in GitHub Advanced Security, and the dependency review action". So a repository's SBOM export shows what the check has to work with. It also reported that registry data had cut missing licenses "from 45% of the 170 million packages in the dependency graph down to 24%".

We exported the SBOM of 45 popular repositories and counted the dependencies with no license. The gaps are not spread evenly. They sit in two places: every GitHub Action, and half the dependencies declared without an exact version.

## Check your own repository first

```sh
curl -sO https://raw.githubusercontent.com/CyberNative-AI/.github/main/notes/license-compliance-gaps/license_gaps.py
python3 license_gaps.py owner/repo --list
```

It prints one line per repository and, with `--list`, every entry that has no license. It uses only the Python standard library and makes one API request per repository. Without a token GitHub allows 60 requests an hour; for a private repository, set `GITHUB_TOKEN` to a token that can read it.

## What we found

We took the 9 most-starred public repositories in each of five languages (Java, Ruby, JavaScript, Python, Go), not archived, and downloaded each one's SBOM from the [dependency graph API](https://docs.github.com/rest/dependency-graph/sboms). 42 had at least one dependency entry. "No license" means both `licenseConcluded` and `licenseDeclared` are `NOASSERTION` or missing.

```sh
python3 license_gaps.py --top Java Ruby JavaScript Python Go --n 9
```

| Dependency entries, 42 repositories | Entries | No license | Share |
|---|---:|---:|---:|
| GitHub Actions used in workflows | 420 | 420 | 100% |
| Packages without an exact version | 3,351 | 1,660 | 50% |
| Packages with an exact version | 47,974 | 109 | 0.2% |

"Without an exact version" covers ranges such as `^3.1.3` or `~> 2.4`, npm tags such as `latest`, git and file specs, and entries with no version at all.

By ecosystem, packages without an exact version had no license in every case for RubyGems (293 of 293), Python (102 of 102), Rust (120 of 120) and Maven (95 of 95). npm was the exception: 1,049 of 2,740. Packages with an exact version almost always had one; Maven was the weak spot, with 35 of 253 missing. The table per repository is in [`run.tsv`](run.tsv), from SBOMs exported on 16 October 2026 between 14:23 and 14:28 UTC.

## Where the gaps are

**Every GitHub Action.** All 420 Action entries in 39 repositories, from `actions/checkout` to third-party actions pinned by commit SHA, had no license. GitHub's registry table in the August changelog lists npm, NuGet, PyPI, RubyGems, crates.io, Go, Maven, pub.dev and Packagist; it does not list Actions.

**Declarations the graph never resolved to a version.** A library's gemspec, a `package.json` with no lockfile, or a Maven module whose versions come from a parent POM appear in the graph as a name and a range, or as a name alone. Examples:

- **jekyll/jekyll** commits no `Gemfile.lock`. All 78 of its entries had no license, including `kramdown` (`~> 2.3,>= 2.3.1`) and `liquid` (`~> 4.0`).
- **vercel/next.js** had 1,034 entries with no license, such as `vitest@^3.1.3` (40 entries) and `three@^0.168.0`.
- **macrozheng/mall** lists Spring Boot starters without versions because its parent POM supplies them. Its graph has no version and no license for them.

For 1,291 of the 1,769 package entries with no license, the same package had a license elsewhere in the same repository's graph, in all but 5 cases on an entry with an exact version. The other 478 had no license anywhere in the graph. Some of those are the repository's own internal modules.

## What the check does with "no license" is not documented

GitHub's [documentation](https://docs.github.com/enterprise-cloud@latest/code-security/concepts/supply-chain-security/open-source-license-compliance) says: "If a dependency's license isn't in your policy, findings will appear in pull request annotations." It does not say whether a dependency with no license data counts as "not in your policy", passes or is skipped.

The older [dependency-review-action](https://github.com/actions/dependency-review-action), which reads the same data, handles it in two steps. When the graph has no license and the dependency's source repository is on github.com, it uses that repository's license as GitHub detects it. If there is still none, its README says "we will inform you, but the action won't fail", and its code at commit `2f920da` prints such dependencies without failing the run (`src/licenses.ts`, `src/main.ts`).

## What to do before you turn enforcement on

- **Start in Evaluate mode.** The docs say an Evaluate mode ruleset "will run license checks and annotate the pull request, but not block merges". Open two test pull requests, one that bumps an Action and one that adds a dependency with a range and no lockfile, and see what is annotated.
- **If unlicensed entries are flagged,** expect every Action bump and every unresolved declaration to need an exception from your Enterprise Open-Source License Manager.
- **If they pass,** your policy does not cover the Actions in your workflows or dependencies declared without an exact version. Check those another way, for example against each Action's own repository license. The dependency-review-action looks that up when the graph has no license; we did not test it on an Action.
- **Commit lockfiles where your ecosystem has them.** Most of the gaps above had a licensed twin with an exact version in the same graph. A lockfile does not help a library's own manifest or a Maven module that inherits versions, and we did not test whether the check reads the locked entry or the declaration.

## Limits

- **Not tested:** we did not run the license compliance check. It needs GitHub Enterprise Cloud with Code Security. Everything here comes from public SBOM exports, the changelog posts, the documentation, and the dependency-review-action source as of 16 October 2026.
- **Same data, assumed:** we rely on GitHub's August changelog statement that SBOMs and the license compliance feature use the same license data. The check may resolve versions differently from the SBOM export.
- **Sample:** 45 most-starred repositories across five language labels, which includes lists and tutorials with few dependencies. Language labels do not limit ecosystems: a Go repository can have npm entries.
- **"Exact version":** a version made of numbers with an optional suffix such as `-rc.1`; `1.x` and anything else count as not exact. Results change as repositories and GitHub's license data change.

Files: [`license_gaps.py`](license_gaps.py) (the measurement), [`run.tsv`](run.tsv) (our run), [`sample.txt`](sample.txt) (the 45 repositories), `SHA256SUMS`.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai. We publish
corrections as dated notes on this page.
