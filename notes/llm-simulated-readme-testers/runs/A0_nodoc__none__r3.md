1. Unclear prerequisites and hosting assumptions. The README likely never states the PHP version, required extensions (openssl, curl, json, mbstring), that the host must allow .htaccess overrides and URL rewriting, or that HTTPS must work on a dedicated subdomain root. A user on shared hosting finds out only after getting 404s or 500 errors.

2. Keypair generation is unexplained. "Fill in a keypair" gives no exact openssl command, key type or size, or format (PEM, newlines, one-line escaped form in .env). First-time users often paste the wrong key format, leave out line breaks, or mix up public and private keys. This is the step most likely to stop a first-time install.

3. Configuration details are vague. It is unclear which values in the example .env are required, what format the username, domain and password take, and whether the file must be renamed to .env. It may also not say where it has to be placed, or whether the web server can serve it. Users who leave .env in the web root publicly exposed may leak their private key and password.

4. Security of the secret files is not covered. A single-file app in the web root puts the .env file, private key and password next to publicly reachable files. The README may not explain how to block direct access to them (.htaccess rules that nginx ignores), set file permissions, or choose a strong password.

5. Fediverse discovery is a black box. A new user does not know that the bot is found through WebFinger (/.well-known/webfinger), an actor document, inbox and outbox endpoints, and correct content-type headers. When the bot doesn't show up in Mastodon search, there is no checklist or test URL to find out which piece failed.

6. No verification steps. The README probably lacks a short "how do I know it works" sequence, such as curl commands for the actor URL and WebFinger, and a sample post that should appear. Without expected outputs, users can't tell success from silent failure.

7. API usage is hard to follow. The Python examples may assume the user already knows the endpoint path, authentication method (header or token, versus password), payload format, and the required libraries or Python version. The README may not show error responses or a minimal curl equivalent for people who don't use Python.

8. Federation behavior is not explained. Users don't know whether followers are supported, how follow requests are accepted, whether posts are delivered to followers' servers, or whether the bot signs requests with HTTP Signatures. They also don't learn about limits such as no replies, media, edits or deletes. Expectations about what "a bot" can do go unmet.

9. The nginx instructions are weak. The .htaccess file does nothing under nginx, so rewrite rules, PHP-FPM routing, and blocking of dotfiles must be translated by hand. Users who follow the Apache-oriented main path and then switch to nginx often get broken routing and exposed files.

10. The Docker section lacks detail. Users may not know how to pass the .env file and keys into the container, which ports to map, how to put TLS in front of it, or where state is stored. The text may also not make clear that the Docker path still needs a public HTTPS domain for federation to work.

11. Persistence and state are unexplained. It isn't clear where followers, posts or logs are stored (files, SQLite, or nothing), whether the web server can write to that location, or how to back it up and migrate it. Permission errors on write are a common cause of failure.

12. Changing the domain or username later is a hazard. In ActivityPub the actor ID is effectively permanent, and other servers cache keys and profiles. A README that doesn't warn about this leads users to experiment with a throwaway name and then lose their followers or end up with a broken identity.

13. Troubleshooting guidance is missing. There is no list of common failure modes: PHP error logs, wrong keys, a clock that has drifted (signature validation fails), a CDN or Cloudflare rewriting headers, a 301 redirect from http to https, and blocklisted domains. Users stay stuck and open issues instead.

14. Operational and legal context is absent. First-time users may not be told about update and upgrade procedure, how to rotate keys, spam and abuse risks, the need to label the account as a bot, rate limits, and the license. Linking to the actual ActivityPub and WebFinger specs would also help readers who are new to the protocol.
