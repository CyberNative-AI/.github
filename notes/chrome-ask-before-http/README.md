# Chrome's ask-before-HTTP default: about 4,450 popular sites now stop a first-time visitor

Chrome now asks before it opens a public site over plain HTTP. In October 2025 Google
[announced](https://security.googleblog.com/2025/10/https-by-default.html) that "with the
release of Chrome 154 in October 2026" it would turn on "Always Use Secure Connections" by
default. Chrome then asks "for the user's permission before the first access to any public
site without HTTPS".

That announcement did not say how many sites would trigger the prompt. We counted. The Chrome
UX Report's public list of the 1 million origins Chrome users visit most (September 2026)
contains 7,748 `http://` origins. **About 4,450 of them (4,110 to 4,780) stop a first-time visitor with the
prompt.** Two kinds of site get through without a prompt: those whose HTTPS works, which
Chrome upgrades silently, and those on a non-default port such as `http://host:8080`.

## When it reached users

Google switched it on from its servers, not in the code. Google's public configuration for
stable Chrome, which we read once, on October 20, turns the setting on for 100% of desktop
Chrome from version 154 on Windows, macOS and Linux, and from 155 on Android. One reading does
not show when Google first switched it on. Chrome 157, due on stable on November 3, builds the
same default into the code
([change 8543331](https://chromium-review.googlesource.com/c/chromium/src/+/8543331)).

So for most people nothing new happens on November 3. It matters where Chrome does not apply
Google's server-side configuration, for example where an administrator has set the
[`ChromeVariations`](https://chromeenterprise.google/policies/#ChromeVariations) policy to
"Enable variations concerning critical fixes only" or "Disable all variations". Those browsers
should get the prompt with Chrome 157. We did not test that case.

## What it stops

We opened each origin in Chrome 155 and in Chrome 157, both on their built-in defaults, with a
fresh profile every time. Chrome 155's built-in default has the prompt off; Chrome 157's has it
on, the same setting Google's servers already turn on for stable Chrome.

| HTTP origins in the top 1 million | opened over HTTP in Chrome 155 | stopped by the prompt in Chrome 157 |
|---|---|---|
| top 100,000 (all 502) | 300 | 278 (93%) |
| the rest (500 at random of 7,246) | 322 | 288 (89%) |

Scaled to the whole list: **about 4,450 of the top 1 million origins**. The range 4,110 to
4,780 is the sum of 95% intervals for the two groups.

The prompt does not appear for:

- **Non-default ports.** All 33 origins on a port such as `:8080` that opened over HTTP in
  Chrome 155 opened again in Chrome 157 with no prompt. On the default port, 566 of 589 were
  stopped.
- **Sites whose HTTPS works.** Chrome loads them over HTTPS without asking. 22 origins that
  opened over HTTP in 155 opened over HTTPS in 157.
- Local IP addresses, single-label names and non-unique names such as `staging.local`, per
  [Google's adoption guide](https://chromium.googlesource.com/chromium/src/+/main/docs/security/ask-before-http/ask-before-http-adoption-guide.md).
  Our sample had none of these, so we did not test them.

This counts sites that stop a **new or occasional visitor**. Chrome remembers the decision for
15 days and renews it on every visit, so a person who uses an HTTP site regularly may see the
prompt only once. It is not a count of warnings per person, and the prompt can be clicked
through.

## If you run a site

Serve it over HTTPS on port 443, including every step of any redirect chain. Google's
[adoption guide](https://chromium.googlesource.com/chromium/src/+/main/docs/security/ask-before-http/ask-before-http-adoption-guide.md)
covers the details.

## If you manage Chrome for other people

For named internal HTTP sites, use the
[`HttpAllowlist`](https://chromeenterprise.google/policies/#HttpAllowlist) policy. List every
host a user passes through: in our test, an entry for one exact host did not cover a redirect
to a different host, and the visit ended on an error page. Patterns such as `[*.]example.com`
cover subdomains.

To turn the setting off for everyone the policy applies to, use
[`HttpsOnlyMode`](https://chromeenterprise.google/policies/#HttpsOnlyMode). On Linux, for
example, in `/etc/opt/chrome/policies/managed/https.json`:

```json
{ "HttpsOnlyMode": "disallowed" }
```

In Chrome 157 with this policy, 0 of 30 stopped origins we tested again were stopped: 29 opened
over HTTP and 1 ended on an error page. This also removes the protection for every other HTTP
site, so the allowlist is the narrower fix.

## How we measured

- Chrome for Testing 155.0.8059.84 and 157.0.8103.6 for Linux, headless, with
  `--disable-field-trial-config`. Without that flag, Chrome for Testing applies test
  configuration that already has the prompt on in 155.
- One fresh profile per origin, a link navigation to the origin's root, up to 30 seconds to
  load. An origin counts as stopped when the navigation ends with `net::ERR_BLOCKED_BY_CLIENT`,
  which is what the prompt returns. Control sites behaved as expected before and after each run:
  `http.badssl.com` and `httpforever.com` opened over HTTP in 155 and were stopped in 157;
  `example.com` opened over HTTPS in both.
- The list is [zakird/crux-top-lists](https://github.com/zakird/crux-top-lists)
  `data/global/202609.csv.gz`. It groups origins into rank buckets, not exact ranks. We took
  every HTTP origin in the buckets up to 100,000 and 500 at random from the 500,000 and
  1,000,000 buckets.
- 196 of the 1,002 origins (19.6%) did not answer from our network in Chrome 155, even after a
  retry. We counted those origins as not stopped. We do not know how many would be stopped from
  another network, so the effect of reachability on the estimate is unknown.
- Run on October 20 on our own machine. Two earlier runs that day were void under our own rule
  because a control site behaved inconsistently; their estimates were 4,729 and 4,744. The
  result has not been independently reproduced.

[`reproduce/`](reproduce/) has the counts behind every number here, the scripts that loaded
and scored the origins, and a decoder for Google's configuration with our October 20 read. We
do not publish which origins were stopped. Many are small organisations' and public
offices' pages, and naming them adds nothing.

## Limits

- Linux only. We did not test Windows, macOS or Android builds, or real users' browsers.
- One network location. The list shows where Chrome users go; it is not a count of every HTTP
  site.
- Pages that mobile carriers and Wi-Fi login portals serve over HTTP appear in the list. We did
  not test those flows separately.
- Google's configuration is a reading from October 20 and can change at any time.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections:
hello@cybernative.ai. We will publish dated corrections here.
