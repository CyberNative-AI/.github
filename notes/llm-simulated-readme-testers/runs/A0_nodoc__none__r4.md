1. Keypair generation is unexplained. A first-time user is told to "fill in a keypair" but not what kind (RSA, key size, PEM format), which tool makes it (openssl commands), or how to put a multi-line PEM into a single-line .env value. This is likely the first place people get stuck.

2. Requirements and prerequisites are missing or vague. The README may not state the PHP version, the required extensions (openssl, curl, json, mbstring), whether `allow_url_fopen` or outbound HTTPS must be enabled, or whether the host must allow .htaccess overrides (`mod_rewrite`, `AllowOverride`). The install then fails with blank pages or 500 errors and no clue why.

3. The domain, subdomain and URL rules are not explained. ActivityPub identity is tied permanently to the domain and the actor URL. Users may not realise that the bot must sit at the subdomain root, that HTTPS must work with a valid certificate, or that changing the domain or username later breaks existing followers.

4. Configuration values are ambiguous. It is unclear which fields in the .env file are required, what format each takes (username with or without @, full domain or bare host), and how the file gets renamed and loaded. A .env file in a web-accessible root can also be downloaded, so the README needs to say how to block it. Users may be unsure whether to choose a strong password or how it is used.

5. There is no step-by-step verification. Nothing tells the user how to confirm it works: a WebFinger lookup (`/.well-known/webfinger?resource=acct:...`), fetching the actor JSON, and searching for the account from Mastodon. Without expected outputs, users can't tell a partial failure from success, and they will hit HTTP 404/403/redirect issues, wrong content-type headers, or caching.

6. The server setup paths differ and are confusing. The Apache/.htaccess route is the default, while nginx and Docker are separate additions. Users on nginx may not realise .htaccess is ignored and that they must translate the rewrite rules, the .well-known routing and the blocking of sensitive files. Docker instructions often omit volume mounts for persistent data, port mapping, and TLS termination.

7. Posting through the HTTP API is not documented clearly enough. Users need to know the endpoint, the authentication method (header, basic auth or token), the request body format and the response, along with a plain curl example as well as the Python one. Python examples can assume a Python version, the `requests` library, and variables that were never defined. Beginners without Python experience have no fallback.

8. The mental model of the Fediverse is absent. Newcomers may not know what an actor, inbox, outbox, followers or federation are, why a server must be reachable from the public internet, and why the bot may not appear on instances that block it. Many assume that posting should immediately show up everywhere.

9. Delivery and follower handling are not explained. Users don't learn whether the bot accepts Follow requests automatically, how it signs outgoing HTTP requests, or what happens when a remote server rejects it. Signature failures from clock skew or a wrong key are hard to debug without log guidance.

10. Where data is stored and how it is persisted is missing. For a single-file bot, users won't know where followers, posts or logs are saved, whether the directory needs to be writable, how to back it up, or what happens on upgrade. File permissions on shared hosting are a common cause of silent failure.

11. Security and abuse guidance is thin. A public inbox endpoint can be spammed, and the README might not mention rate limits, spam filtering, protecting the API password, or keeping the private key out of version control and web access. Users may commit their filled-in .env to a public repository.

12. Troubleshooting and support information is lacking. A README that has no common-errors section, no log location or debug mode, no version or changelog, and no pointer to where to ask questions leaves people stuck. The licence, project status and known limitations (for example, no media, no replies or a single account) may also be unclear, so users cannot tell whether the tool fits their needs before investing time.
