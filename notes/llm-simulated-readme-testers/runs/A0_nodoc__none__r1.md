1. The README does not say what the bot can actually do or what ActivityPub/Fediverse concepts a user needs. A newcomer may not know what an actor, inbox, outbox, WebFinger or follower is, or why a bot needs its own domain. They cannot tell whether the project fits their goal before they start.

2. Prerequisites are unclear or missing. The README should list the PHP version and required extensions (OpenSSL, cURL, JSON, mbstring), the HTTPS requirement, whether Apache `mod_rewrite` and `.htaccess` overrides (`AllowOverride`) must be enabled, and whether the host must allow outbound HTTP requests. Users on shared hosts often find out too late that their host lacks one of these.

3. The README gives no clear path for generating the keypair. "Fill in a keypair" does not say which algorithm or key size to use, which command to run (for example `openssl genrsa`), what format to use (PEM, with or without headers), or how to put a multi-line key into an `.env` file. This is probably the most common place for first-time users to get stuck. Multi-line keys, stray newlines and quoting errors cause silent signature failures.

4. The configuration is under-explained. It does not say what each `.env` variable means or whether it is required. It also does not say how the password and username relate to the bot's handle (`@user@subdomain.example.com`), or whether the domain, scheme and username are fixed once the bot has been followed. Users can easily choose a weak password or a handle they cannot change later.

5. The `.env` file may be publicly downloadable. If the file sits in the web root, a missing `.htaccess` rule, or nginx and Docker setups that ignore `.htaccess`, can expose the private key and password. The README needs a prominent warning and a way to test for this.

6. The "subdomain root" requirement is not justified, and the failure case is unclear. Users may try a subdirectory such as `example.com/bot/` and get broken `/.well-known/webfinger` and actor URLs, with no clear error. Because the actor ID is baked into every federated post, changing the domain later breaks the account's identity.

7. There is no verification step after installation. The README does not say how to check that the bot works. For example, it could tell users to open the actor URL, run a WebFinger query with `curl`, search for the account from a Mastodon instance, and check the expected JSON and `Content-Type: application/activity+json`. Users cannot tell whether the setup is correct or why it is not.

8. The HTTP API is poorly documented. Users need the endpoint paths, the authentication scheme (header, Basic auth, token), the request and response formats, and the error codes. If the Python examples are the only documentation, anyone who does not use Python, or who is on a different version or dependency set, has to read the PHP source.

9. The Python examples may be hard to run. The README may not state the Python version or the packages needed (`requests`). It may not say where to put the base URL and credentials, or whether the examples are copy-paste ready. Hard-coded example domains and passwords often lead users to hit the wrong URL or send secrets in plain text.

10. The nginx and Docker instructions are an add-on and may be incomplete. The Apache-style `.htaccess` rewrites need a matching nginx `location` and `try_files` block, `.env` blocking and PHP-FPM wiring. The Docker steps need to explain how to mount `.env`, expose ports, terminate HTTPS (reverse proxy or certificates), and persist data. Users are likely to follow the main flow and find that the alternative setup does not map cleanly.

11. Storage and persistence are not explained. If the bot stores followers, posts or a queue in files or a database, the README should say where, what permissions the web server user needs, and how to back it up. Failed writes show up as an HTTP 500 or as nothing at all.

12. Federation behaviour is not set out. The README does not explain how follow requests are handled (auto-accept or not), whether posts are delivered to followers' inboxes, how HTTP signatures are verified or signed, or that other servers may cache or reject content. Users cannot tell why their posts do not appear on other instances. They also cannot tell whether clock drift, a missing `Host` header or a missing `Date` header could cause rejection.

13. Debugging help is thin. There is no troubleshooting section for common symptoms (blank page, 500 errors, "signature verification failed", 404 on WebFinger, bot not found from Mastodon) and no explanation of where logs are or how to turn on debug output. Users who hit a problem cannot help themselves and tend to give up or open vague issues.

14. Security, scope and maintenance expectations are not stated. A single public PHP file that accepts authenticated posts needs guidance on HTTPS only, password strength, rate limiting, abuse and spam risks, and which fediverse spec features are not implemented. The README also needs a licence, a version and update process, and a statement of project status. Users want to know what is safe to run and whether it will be supported.

15. The README is poorly structured and does not match what users do. Without a short quick-start, numbered steps in order, expected output after each step and a clear split between required and optional parts, users have to piece the process together. A copy-paste "minimal working setup" at the top, with the details lower down, would reduce most of the problems above.
