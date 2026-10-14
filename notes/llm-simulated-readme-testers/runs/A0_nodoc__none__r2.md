1. Generating and formatting the keypair is unclear. A first-time user won't know which key type or size ActivityPub servers expect (usually RSA 2048 or larger, PEM format). They also won't know how to put a multi-line PEM into a single-line .env value (escaped newlines versus quotes), and a malformed key makes signing fail silently.

2. The README doesn't say what "upload to the root of a subdomain" means in practice. Users don't know whether the bot's actor ID, WebFinger and inbox URLs are tied to that exact hostname. They also don't know that the hostname is effectively permanent once other servers have seen the account, so moving or renaming it later breaks followers.

3. The .htaccess and URL-rewriting requirements are easy to get wrong. If mod_rewrite is disabled, AllowOverride is off, or the host isn't Apache (nginx, LiteSpeed, shared hosts that ignore .htaccess), the routes for /.well-known/webfinger, /inbox and /actor return 404. The user gets no clear error and doesn't know how to test.

4. Secrets and configuration handling are confusing. The .env file may be publicly downloadable if the web server serves dotfiles, which would leak the private key and password. Users also need to know to copy the example file, rename it, and set permissions. If the README doesn't warn about this, they can expose credentials.

5. Prerequisites are not stated up front. A first-time user needs to know the minimum PHP version and required extensions (openssl, curl, json, mbstring), and whether outbound HTTPS requests are allowed on their host. Without this list they hit cryptic fatal errors or blank pages.

6. There is no verification path after setup. Users have no simple way to confirm that it works, such as fetching the actor JSON with curl, doing a WebFinger lookup, or searching for the account from Mastodon. They can't tell a misconfiguration from federation simply being slow or blocked.

7. Fediverse concepts and terminology are assumed. Terms like actor, inbox/outbox, WebFinger, HTTP Signatures, followers and federation are used without explanation. Newcomers don't understand why the bot needs a keypair or why the username and domain together form its handle (@user@domain).

8. The HTTP API for posting is under-documented. The Python examples may not cover authentication (how the password is sent, header versus body), request and response formats, error codes, or limits. Users don't know how to post from other languages or how to handle failures. Python dependencies and version requirements for the examples may also be missing.

9. The nginx and Docker instructions are treated as secondary and can be incomplete. nginx has no .htaccess equivalent, so users must translate the rewrite rules themselves. Docker users need to know about volumes, persistent data, TLS termination and environment variable passing, and they may follow a mix of steps meant for different setups.

10. HTTPS and certificate requirements aren't spelled out. Fediverse servers require valid HTTPS, so self-signed certificates, plain HTTP, or a misconfigured redirect or proxy (wrong scheme or host headers) cause failed federation. Users on a typical host may not know how to enable Let's Encrypt or check that the certificate chain is valid.

11. Where data is stored and how persistence works is unclear for a single-file bot. Users aren't told where followers, posts or logs are kept, whether that location is writable, or how to back up and migrate. File permission errors on shared hosting then appear as silent failures.

12. Expectations about features and federation behavior are not set. Users don't know whether the bot handles follows, accepts or rejects requests, delivers to followers' inboxes, or supports media, replies and deletions. They also don't know why posts may not appear on some instances (blocks, delays, authorized-fetch requirements).

13. There is little troubleshooting guidance. No list of common errors, no instructions for enabling debug logging, and no pointer to where to ask for help. Beginners get stuck and abandon the project.

14. Security and abuse considerations are missing. Users aren't told to use a strong password, rotate keys, restrict API access (for example by IP or token), or rate-limit it. They also aren't told that a publicly reachable posting endpoint can be abused if it's left unprotected.

15. Basic project information is hard to find: the license, the version and update process, how to upgrade a single file without losing configuration, and how to uninstall or delete the account from the Fediverse.
