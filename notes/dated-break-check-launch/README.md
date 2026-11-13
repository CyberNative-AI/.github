# A CI check for breaks that come on a date, not with a commit

On 19 November 2026, `postgres:latest` is due to become PostgreSQL 19. A Compose file that says `image: postgres` and has PostgreSQL 18 data in its volume stops starting the next time the container is recreated on the new image. Nothing in the repository changes that day. No version bump, no Dependabot pull request and no failing test warns you first.

[Dated break check](https://cybernative.ai/go/dated-break-check/launch-note/) is a GitHub Action for this kind of break: an image tag that moves, an API, model or data feed that shuts down, a runner that is retired. Run on a clone of [docker/awesome-compose](https://github.com/docker/awesome-compose) on 13 November, it printed:

```
2026-11-19  in 6 days                 Hits this repository      postgres:latest becomes 19  spring-postgres/compose.yaml:11
```

- **On pull requests** it puts a warning on the line, with the date, the days left and a link to what to check and, where we have one, a tested fix.
- **Every Monday** it fails the run when a date that hits the repository is 14 days away or fewer, so GitHub's own failed-run notice reaches you. A date added to the calendar that week reaches you with no change on your side.
- **Nothing from your repository is sent.** The step makes two GET requests for public calendar files, and `data: bundled` turns those off. No account, token or email address.

The dates come from our [Breakage Calendar](https://cybernative.ai/breakage-calendar/). On 13 November it had 29 upcoming dates that a repository's files can show, from 16 November to 30 April 2027, including PHP 8.6 images dropping pecl (19 November) and `node:latest` becoming Node 27 (22 April 2027).

It does not replace endoflife.date for runtime end-of-life, Renovate digest pinning, or the AI model retirement scanners, which cover models better than we do. The [README](https://github.com/CyberNative-AI/dated-break-check#what-else-does-this-and-when-to-use-it-instead) says where each one is stronger, including Last Call, the closest Action to this one.

Setup is one workflow file: [copy it from the README](https://github.com/CyberNative-AI/dated-break-check#setup). A wrong or missing date is an issue on the repository.

## How we counted

The run output above is from the Action's own `src/run.mjs` on a shallow clone of docker/awesome-compose at commit `30f4b7f6`. The date counts come from [`reproduce/count_dates.py`](reproduce/count_dates.py), run on the calendar's published [`entries.json`](https://cybernative.ai/breakage-calendar/entries.json) and [`signatures.json`](https://cybernative.ai/breakage-calendar/check/signatures.json), and Last Call's [`sunsets.json`](https://lastcall.dev/api/sunsets.json), all read on 13 November 2026:

```
python3 reproduce/count_dates.py entries.json signatures.json sunsets.json 2026-11-13
```

Its first line reads `upcoming with a repository search: 29; AI-model rows: 9; others: 20`, and its last line reads `in Last Call: 1 of 20`. That Last Call match was checked by hand, by searching Last Call's titles for each of the 20 events; the script records the result rather than computing it. The one match is OpenAI's Evals shutdown on 30 November. Last Call also lists Azure App Service ending Node 22 support on 30 April 2027; we did not count it, because it is Azure's date for its own service, not the Node.js end of life.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents.
