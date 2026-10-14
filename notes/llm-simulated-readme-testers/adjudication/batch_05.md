=== CRITIQUE U3552 START ===
1. The README tells you to configure credentials by editing `index.php` ("Edit the `index.php` file to add a username, password, and keypair."), but it never says where in the file, what format, or how to generate the password hash and keys there. The `.env` alternative is mentioned only as an aside ("If you prefer, you can rename `.env.example` to `.env`"). The two routes are not reconciled, and it is unclear which one wins if both are used or which is recommended.

2. The key generator is named inconsistently. `.env.example` says "Generate locally by opening `tools/rsa_keys.html`", but the file list shows `tools/rsa_key_generator.html`. A first-time user following the instructions literally will not find the file. The README Set Up section never mentions key generation or the tools directory at all.

3. The PHP requirement looks wrong or at least very hard to meet: "PHP 8.5 ... (We live in the future now.)". The README and both nginx docs pin 8.5, so users on common shared hosts (the stated audience: "You can FTP these files onto any host") will likely fail the requirement. It is not stated whether older versions work, what the real minimum is, or which language features need 8.5.

4. The password setup is incomplete and contradictory. `.env.example` says `PASSWORD` must be a hash made with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );` or `php tools/generate_password.php 'Y0ur_p4s5w0rd'`. The README API examples use `"password": "your-password-here"` and never say that the plaintext is sent while the hash is stored. The README Set Up never mentions generating a hash. Users without command-line PHP have no alternative.

5. Quoting and escaping for `.env` values are underspecified. `KEY_PRIVATE` must be a single line with "Newlines must be replaced with "\n"", but there is no instruction on how to do the conversion, and the example values have "..." placeholders. A hash containing `$` characters inside double quotes may be mangled by some `.env` parsers. The `.env.example` header comment is also incomplete about a bare `USERNAME` ("Do not include an "@"") and about whether values need quotes.

6. The Set Up steps are numbered inconsistently ("0.", then "1." repeated for every step), so the steps render in a confusing order and cannot be referred to. Step 0 is also a prerequisite (a subdomain and certificate), not a step. The file list and instructions give no explicit statement of which files to upload (`.env.example` says to upload "index.php and .htaccess", the README says to upload `.env` too).

7. The `.env.example` header says "At a minimum, you must provide KEY_PRIVATE, KEY_PUBLIC, PASSWORD, and USERNAME", but the other fields, such as `BIRTHDAY`, `LANGUAGE` and `PAGE_SIZE`, have placeholder values that will silently be used if left unchanged. For example `SUMMARY` links to the author's repository and `PROFILE_NAME_3` mentions the author's account. A user who only fills in the mandatory fields will publish a bot whose profile contains the example metadata. It should say which optional fields are safe to leave as is.

8. The directory layout is contradictory. The README says "Log files are saved as .txt in the `/data/logs` directory", but "Post files are saved as .json in the `/posts` directory" and "Quote acceptance and stamps ... in the `/quotes` directory" are not under `/data`. It does not explain whether the web server user needs write permission to create these folders, nor what permissions to set. The setup step "Check your `/data/logs/` directory" assumes it exists, and there is no troubleshooting if the folder is missing.

9. There are no steps for anything that goes wrong. The webfinger check ("check that it shows a JSON file with your user's details") has no example of the expected output or the failure cases (404, PHP source shown, `.htaccess` not honoured because `AllowOverride` or `mod_rewrite` is off). The README does not mention that Apache with `mod_rewrite` and `.htaccess` support is needed. It only says "Minimum Requirements" with PHP and OpenSSL.

10. Security guidance is missing for the Apache path. `.env` holds the private key and password hash, but the README never says to make sure `.env` and `/data` are not publicly downloadable under Apache. Only the nginx configs include `location ~ ^/(.env|data) { deny all; ... }`. Users should be told to verify that `https://test.example.com/.env` returns an error. It also does not discuss that API requests send the password in plain POST data and need HTTPS.

11. The "Minimum Requirements" list contains a joke bullet ("Docker, Node, MongoDB, Wayland, GLaDOS, React, LLM, Adobe Creative Cloud, Maven (absolutely none of these!)") inside the requirements list. Yet the project ships a Docker README and nginx instructions. A skimming reader can mistake it for a list of requirements. The "100MB free disk space" figure is also unexplained next to the FAQ's "Probably not" about disk use.

12. The README contradicts itself on which features exist. It lists "🔏 Verify cryptographic signatures, including RFC 9421" as supported while "❌ Sign messages with RFC 9421 Signatures" is not. It lists "Receive messages (other than follows, unfollows, and quote requests)" as unsupported while the same README describes saving "Messages sent to your inbox ... in the `/data/inbox` directory". It lists "✏️ Edit Posts" and "🔄 Update profile information" with API semantics that differ from the examples (editing posts uses the same `/action/send` endpoint with a `guid`, with no explanation).

13. The API documentation has gaps. The "Requirements" section says only "a modern version of Python" and the Requests library, with no explanation of how to obtain the `guid` needed for delete and update ("You will need the ID of your post" with no instruction on where to find it). The documented parameter names are never listed in one place, and `"action": "Follow"` and `"Move"` use different capitalisation conventions than the other endpoints. The location example uses `"longitude": 40.77563, "latitude": -73.97474`, which are swapped (40.77 is the latitude of New York and -73.97 its longitude), which would put the post in the wrong place. The debugging snippet needs an unmentioned extra library (`requests_toolbelt`).

14. The migration section is confusing. It says to add `NEW_NAME` and then "send a Move request", but the `.env.example` comment says to POST to the "action/users" endpoint and the README example uses `"user": "@new@example.com"` while `NEW_NAME` expects a full URL like "https://new.example/users/username". The README never explains the order of operations, and the `OLD_NAME`/`NEW_NAME` names are not self-explanatory. The "Update Account" section says to tell followers but does not say when it is needed.

15. The nginx documentation is thin and inconsistent. `README_nginx.md` starts with an unexplained sentence ("requires php8.5-fpm which is a thing that passes requests to PHP"). `sudo apt-get install php php-curl` followed by `php8.5-fpm` will not work on distributions that do not package 8.5 without adding a third-party repository, which is not mentioned. The sample config listens on port 80 only, even though HTTPS is a hard requirement. The commented note "I don't THINK these are needed but computers are oh so very confusing" undermines trust, and the file ends with a test of `test.php` that tells the user to leave a PHP file on the server without telling them to delete it.

16. The Docker README says it is "Rough Docker Instructions" and has problems a first-time user will hit. The compose snippet has an `environment:` key with only a comment under it (invalid or empty YAML value), a stray `// Increase performance` comment style, and a Traefik comment "Internal port for postiz" copied from another project. The volume mounts `/var/www/html/public` and `/etc/nginx/conf.d/activity-bot.conf` but never say that the nginx config is the block below and must be saved as that file. The nginx block uses `server_name you.host.com` while the compose label uses `your.host.com`. `fastcgi_pass 127.0.0.1:9000` may not match the image's PHP-FPM socket. The image tag `serversideup/php:8.5-fpm-nginx-alpine` is not explained. Nothing says where `.env` goes or how to give it to the container.

17. The README's front matter does not say who the project is for or what it is: "ActivityBot" versus "A single file ActivityPub Bot Server" and the repository path "gitlab.com/edent/activity-bot". There is no one-paragraph explanation of ActivityPub or the Fediverse for newcomers, and no screenshot or example of the output. The emoji-only feature list is long (over 40 items) and mixes capabilities with implementation details, so a first-time reader cannot tell what the minimum viable use looks like.

18. Several URLs or details look wrong or placeholder-like. The funding text says "From 2026-08, this project was funded" under "grant agreement № 101135429" (the date and grant number should be checked), `.env.example` has a comment line starting `#	This is the joined date` rather than `#;`, `PAGE_SIZE="1000"` is quoted while `MAX_LOGS=2048` is not, and the README says logs keep "2,048" files by default while the file list and README do not say what happens to older logs. "URl" is a repeated typo for "URL". The README references an `AGENTS.md`, `CONTRIBUTING.md` and `tests/` directory in the file list that a first-time user is not told about, and the AI policy and funding sections come before any troubleshooting or support information.
=== CRITIQUE U3552 END ===

=== CRITIQUE U3920 START ===
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
=== CRITIQUE U3920 END ===

=== CRITIQUE U1834 START ===
1. The README never says how to obtain the files. The Quickstart says "Upload `index.php`, `.htaccess`, `.env.example` to your subdomain" but gives no download or clone instruction, and does not mention that `tools/` exists in the repo and is needed before upload.

2. The Quickstart and the Set Up steps disagree on order. The Quickstart says "Upload `index.php`, `.htaccess`, `.env.example`" then "Rename `.env.example` to `.env`", but Set Up says rename first and then "Upload `index.php`, `.htaccess`, and `.env`". Neither says whether to rename locally or on the server.

3. The Quickstart is misleadingly short. "Edit `.env` and follow the instructions inside it" hides the real prerequisites: generating an RSA key pair and a password hash, which need a browser tool and PHP.

4. "Generate locally by opening `tools/rsa_key_generator.html` on your computer" does not say where that file is relative to the upload, or whether the page produces keys that already have the newlines escaped. The comment "Newlines must be replaced with "\n"" leaves a non-technical user to convert multi-line keys by hand. No alternative such as an `openssl` command is given, and the example shows `BEGIN RSA PRIVATE KEY` headers whose required format is not explained.

5. Password generation assumes PHP is installed locally: "Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`" and "`php tools/generate_password.php 'Y0ur_p4s5w0rd'`". Users on shared hosting or Windows may have no local PHP, and the single-quote form fails in PowerShell. There is no browser-based or hosted alternative.

6. The `.env.example` text does not warn that a password hash contains `$` characters, which can be interpolated by some `.env` parsers, nor how to quote it in `PASSWORD=""`.

7. It is unclear what to put in the API's `"password"` field. `.env` holds a hash, while the examples use `"your-password-here"`. The README never says to use the original plaintext password rather than the hash.

8. The statement "The password is encrypted when you send it and never stored on your server" is misleading. The password is sent in the POST body, protected only by HTTPS, and the server stores a hash in `.env`. This blurs what protects the password.

9. The "Optional Fields" in `.env.example` are filled with live example values (for example `SUMMARY`, `BIRTHDAY`, `PROFILE_VALUE_3`, `PROFILE_VALUE_4` pointing at `https://example.com/tag/ActivityBot`). The file does not say what happens if a user leaves them, deletes the lines, or sets them blank, so people may publish a profile with someone else's links.

10. "`AVATAR`... Should be a relative URl without leading slash. For example "icon.jpg"" does not say relative to what, or where the image should be uploaded. Set Up step 8 ("upload an avatar and banner image... Edit `.env` to include the image locations") repeats the gap, and it doesn't mention running the "Update Account" call afterward so followers see the change.

11. Set Up step 2 says "If you prefer, you can edit `index.php` and place the details in there." It does not say which variables, in what format, or the security trade-off of keeping a private key in the script.

12. Dotfile handling is not addressed. `.env` and `.htaccess` are hidden or hard to rename in Finder, Windows Explorer and some FTP and file-manager tools, and the README gives no workaround.

13. "PHP 8.5 (We live in the future now.)" gives no guidance on how to check or select a PHP version on a host, or what happens on older versions. Most shared hosts and Linux distributions do not ship 8.5, and "This should include the following extensions by default" is vague, since cURL and OpenSSL availability differs by build. The cURL link points to a PHP 8.5 release-notes feature section, not install instructions.

14. The Raspberry Pi and "any modern web server" claim ("It will run on shared hosts, a Raspberry Pi") gives no guidance on home hosting: obtaining a domain or HTTPS certificate, port forwarding or dynamic DNS. "HTTPS certificate (Let's Encrypt is fine.)" says how to get one nowhere.

15. Apache prerequisites are missing. The README calls Apache "the default set up" but never says that `.htaccess` needs `mod_rewrite` and `AllowOverride`, nor whether `.htaccess` protects `.env` and `data/`. It never tells the user to check that `https://test.example.com/.env` is not publicly downloadable, even though the private key lives there.

16. The subdomain requirement is not explained. "Your account lives on *your* website's subdomain" and "It will not work in a subdirectory" leave open whether an apex domain or a dedicated domain works. The FAQ ("Every bot needs its own domain name") adds to the confusion.

17. The webfinger check is vague. "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details" gives no sample output and does not say whether the `?resource=acct:...` query is needed. It offers no help if the page returns an error.

18. "Check your `data/logs/` directory to see if the follow request was received correctly" does not say that this directory is created by the script at run time, that the web server user must have write access to it, or what a correct log entry looks like. Write permissions are only hinted at in README_caddy.md ("You may have to adjust the permissions...").

19. "Follow your user" assumes the reader already has a Fediverse account to search from and follow with. The Set Up never says that a fresh bot's posts only reach followers.

20. There is no troubleshooting section. Errors are not explained anywhere, including how to see PHP errors. `php_errors.log` appears only inside the Caddyfile.

21. Set Up ends at "check logs" and never shows a first post. The "Check it has worked" section says "Check social media to see if the message appears" without saying that a follower is needed first, and the Python examples never print `r.status_code` or `r.text`, so a user cannot tell success from failure.

22. The Python section's "Requirements" ("a modern version of Python and... the popular Python Requests library") gives no install command. The Debugging snippet uses `requests_toolbelt`, which is not listed. There is no `curl` example for non-Python users.

23. "You can send HTML. See `$allowed_elements` to see which ones are supported" refers to a variable inside `index.php` with no pointer to where it is or to a list.

24. The alt-text mechanism in "Post Images and Other Media" is undocumented. `files = [("1",("This is the alt text", open("red.png", "rb")))]` puts alt text where a filename would normally go, and the text never says so. The "multiple images" example uses the same position for the strings "red", "green" and so on without comment.

25. "Delete Post" and "Update / Edit Post" say "You will need the ID of your post", but there is no instruction for finding the `guid`.

26. The location example has latitude and longitude swapped: `"longitude": 40.77563, "latitude": -73.97474`. The place named, "John Lennon Memorial", is in New York, so 40.77 is the latitude and -73.97 the longitude.

27. The Features list promises "Unfollow accounts", "Block accounts", "Unblock accounts", "Allow quote posts", "Attach videos" and "Attach audio", but the API section has no example for unfollow, block, unblock or quote posts, and the media section only mentions audio and video in one sentence.

28. The "Migrate Accounts" text is confusing. "Once your new acount is set up, go to your new account and follow its procedure for moving followers to it" uses "new account" for two different things. The `.env.example` asks for a full URL in `NEW_NAME` (`https://new.example/users/username`) but the API example uses `"user": "@new@example.com"`, and the two formats are not reconciled. There is also a typo, "acount".

29. The Docker instructions are incomplete and have copy-paste errors. The compose fragment has no `services:` header, no `ports:` mapping for users without Traefik, and an `environment:` key with only a commented-out value. The comment "Internal port for postiz" refers to another project, and the hostnames `your.host.com` and `you.host.com` differ. It doesn't say where `index.php`, `.htaccess` and `.env` go inside the mounted directory, and says nothing about how TLS works without Traefik.

30. The Docker nginx config says it is "a mixture of the nginx config from README_nginx.md and the documentation from ServerSideUp" but doesn't list the differences, such as `fastcgi_pass 127.0.0.1:9000` against a socket. It does not say whether it replaces or collides with the image's default server, and does not cover file ownership for `data/` in the container.

31. The nginx and Caddy pages install PHP in a way that can fail. `sudo apt-get install php php-curl` commonly pulls in Apache on Debian and Ubuntu, `php8.5-fpm` is not in standard repositories (no PPA or repo is mentioned), the OpenSSL extension is not listed, and the socket path `/var/run/php/php8.5-fpm.sock` is hard-coded to one version.

32. README_nginx.md only has `listen 80;`, although the main README requires HTTPS. It does not say where to put the config, how to test it (`nginx -t`) or reload, and does not say how to continue with the main Set Up afterward. The comment "I don't THINK these are needed but computers are oh so very confusing" leaves the user unsure which commented lines to enable. The block is labelled `bash` rather than `nginx`.

33. The Caddyfile blocks `/.env` and `/php_errors.log` but not `/data`, whereas the nginx pages block `^/(.env|data)`. A Caddy user can leave log files public. The nginx rule is also an unescaped regex that matches any path starting with `/env` or `/data`, such as `/database`.

34. The "To test the config" step in README_nginx.md and README_caddy.md has no expected output. `$_GET["path"]` is undefined when `test.php` is visited directly, so the user sees a PHP warning and can't tell success from failure. Nothing tells them to delete `test.php` afterwards, and the Caddy page does not link back to the main Set Up steps.

35. The structure and wording have small errors that cost trust. "Set Up" is a sub-heading of "Minimum Requirements". The list numbering runs "0." then "1." repeatedly. "Lenny" appears in the Introduction, probably meaning Lemmy. "URl", "URls" and "acount" appear as typos. In `.env.example`, one comment uses `#` rather than `#;` ("#	This is the joined date of your bot."), and `MAX_LOGS=2048` is unquoted while `PAGE_SIZE="1000"` is quoted, with no explanation.

36. The AI policy FAQ says "AI was not used at any stage... LLMs were not used to write, design, or test anything", but the repository file list includes `AGENTS.md`, a file normally used to instruct AI coding agents. I could not see its contents, so this may be a legitimate or stale file, but the apparent conflict should be checked or explained.
=== CRITIQUE U1834 END ===

=== CRITIQUE U9530 START ===
PROBLEMS
1. The Python examples use the Requests library but never show how to install it with pip inside a virtual environment.
2. The feature list is long; some emoji do not render on older terminals' fonts, but the list is otherwise clear.
3. The key generator tool is mentioned and its filename matches the repository file list, so that step looks fine.
4. There is no screenshot of what the bot's web page looks like.
5. The Docker README assumes the reader already has Docker Compose installed.
6. The licence section's AGPL explanation may worry some commercial users.
7. The migration section links to external limitations instead of summarising them.
8. The debugging snippet requires requests_toolbelt, which is not mentioned in the requirements.
=== CRITIQUE U9530 END ===

=== CRITIQUE U3837 START ===
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
=== CRITIQUE U3837 END ===

=== CRITIQUE U3721 START ===
1. The Requirements list "PHP 8.5 (We live in the future now.)" with no minimum-supported older version. Many shared hosts and distribution repos don't offer 8.5, and the README doesn't say whether older PHP works or how to get 8.5.
2. The Requirements never name the web server needs for the default Apache path (mod_rewrite, `AllowOverride` so `.htaccess` is honoured, write permission on the web root or `data/`). They also omit PHP extensions beyond OpenSSL; README_nginx.md installs `php-curl` with no explanation. The line "Docker, Node, MongoDB, Wayland, GLaDOS, React, LLM, Adobe Creative Cloud, Maven (absolutely none of these!)" tells readers what isn't needed but not what is.
3. Set Up step 1, "Edit the `index.php` file to add a username, password, and keypair.", doesn't say which variables or lines to edit, what format they take, or how to generate a keypair or password hash. It offers `.env` as an alternative without saying which wins if both are filled in.
4. `.env.example` says "Generate locally by opening `tools/rsa_keys.html`", but the file in the repository is `tools/rsa_key_generator.html`. The `tools/` directory is never mentioned in the README. There is no guidance on key format (for example the `BEGIN RSA PRIVATE KEY` header versus the `BEGIN PRIVATE KEY` header openssl produces by default) or on whether the browser tool is safe to use for a private key.
5. The instruction "Newlines must be replaced with "\n"" doesn't say how to do that, or what the generator tool outputs, so non-technical users must hand-edit a multi-line key.
6. The password flow is confusing. `.env.example` says PASSWORD is a hash ("Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`"), but every API example sends `"password": "your-password-here"`. Nowhere is it said that the plain password goes in the POST while only the hash goes in the config.
7. Generating the hash requires a local PHP CLI (`php tools/generate_password.php 'Y0ur_p4s5w0rd'`), which readers on shared hosting or Windows may lack; the single-quote syntax also fails in Windows cmd. A resulting hash contains `$` characters, and there is no guidance on quoting it in `.env` (the example uses double quotes).
8. `.env.example` says to rename the file and upload it, but dotfiles are hidden in many FTP clients and file managers. Nothing tells users how to verify the upload worked.
9. "Upload `index.php` and `.htaccess` to the *root* directory of your domain" doesn't explain what the root is on hosts such as cPanel where a subdomain sits in a subfolder. The same instruction says to upload `.htaccess` even for the nginx/Docker routes, where it is irrelevant, and no note says to skip it.
10. Step 4, "Optionally, upload an avatar and banner image to make the user look nice.", omits that `AVATAR`, `BANNER`, and `FAVICON` must also be set in the config, as relative paths with no leading slash, and that there are size and format limits (documented only in `.env.example`).
11. Step 5, "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details.", gives no example of the expected output. A bare webfinger URL normally needs a `resource=acct:...` query, and nothing says what an error means or how to debug a failure.
12. Step 6 uses `@username@test.example.com` without saying that "username" is the `USERNAME` value. Step 7 ("Follow your user.") never says whether the follow is auto-accepted or what a correct result looks like.
13. Step 8, "Check your `/data/logs/` directory to see if the follow request was received correctly.", assumes file access and doesn't say what a correct log entry looks like, whether the directory is auto-created, or that it must be writable.
14. There is no troubleshooting section. Common failure causes (HTTPS misconfiguration, rewrite not working, `.htaccess` ignored, CDN or bot-protection blocking, unwritable data directory) are not mentioned.
15. The "How this works" directories are inconsistent: "Post files are saved as .json in the `/posts` directory" and "Quote acceptance and stamps are saved as .json in the `/quotes` directory" lack the `/data` prefix that logs, followers, and inbox use. It is unclear which paths are under the web root and which need protecting.
16. There is no instruction to verify that `.env` and `/data` are not publicly downloadable on Apache, even though `.env` holds the private key and password hash. The nginx guidance has a `location ~ ^/(.env|data)` block, but the README never tells Apache users to check.
17. The feature list contradicts itself: it says the bot cannot "Receive messages (other than follows, unfollows, and quote requests)", but "How this works" says "Messages sent to your inbox are saved as .json in the `/data/inbox` directory." The 40-item list also sits before setup instructions, burying the install path.
18. The formatting "`.htaccess file`" (backticks around two words) is wrong, and the numbering starts at "0." and then repeats "1." for every later step. Typos include "acount" ("Once your new acount is set up") and inconsistent "URl". These are minor but erode trust in the instructions.
19. The API section assumes Python with `requests`, but gives no `pip install requests`, and the Debugging snippet imports `requests_toolbelt`, which is not mentioned as a dependency. There is no curl or non-Python example despite "you can use whichever language you want".
20. No API example shows a response, status code, or error format. Users can't tell whether `r` indicates success. This also makes "Check it has worked" unreliable: "Check social media to see if the message appears." doesn't say that the post won't show anywhere until someone follows the bot.
21. The API docs cover only Post, Follow, DM, media, Delete, Edit, Content Warning, Reply, Hashtags, Location, Update, and Move. Listed features (Unfollow, Block, Unblock, Show followers, View hashtags) have no usage documentation or the valid `action` values. "You can send HTML. Only formatting elements are allowed." doesn't say which elements.
22. For Delete and Edit, "You will need the ID of your post:" doesn't say where the `guid` comes from (the send response, the log, the posts directory?).
23. The media example `files = [("1",("This is the alt text", open("red.png", "rb")))]` puts alt text where a filename normally goes, without explaining it. File size, type, and count limits are given only loosely ("a maximum of one audio file, or one video file, or up to four image files") and nothing states the bot's own limits.
24. The location example `"longitude": 40.77563, "latitude": -73.97474` looks swapped: 40.77 is New York's latitude and -73.97 its longitude. Copying the example would place the post in the wrong spot.
25. Migration instructions are muddled. The two paragraphs describe "go to your old account and follow its procedure" and "go to your new account and follow its procedure for moving followers to it", and the order of steps, and when to POST the Move, is unclear. `OLD_NAME` and `NEW_NAME` are said to go in ".env" even for readers who configured `index.php`.
26. The FAQ says "By default, this software only keeps the most recent 2,048 log files. You can adjust this if you want", without naming `MAX_LOGS`. `.env.example` warns that "Logs can fill up *fast*... they can exhaust your file limits", which is in tension with the FAQ's "Probably not."
27. README_nginx.md opens with "requires php8.5-fpm which is a thing that passes requests to PHP" and installs with `sudo apt-get install php php-curl` (which may pull in Apache and conflict with nginx on port 80). `php8.5-fpm` isn't in default Debian/Ubuntu repositories and no third-party repository is mentioned.
28. The nginx config has only `listen 80;` although the README requires HTTPS, and it gives no TLS or certbot guidance. It never says to enable the site, create the root directory, set its ownership, or reload nginx. The commented-out lines "#     I don't THINK these are needed but computers are oh so very confusing" leave the reader unsure what's required.
29. The nginx README's config lacks the dotfile deny block ("# Deny access to . files, for security") and the `.well-known` location that the Docker config includes. The two configs differ without explanation, and the shorter one leaves `.htaccess` and similar files readable.
30. The nginx test step ("make a file `test.php`... and attempt to access it on test.example.com/test.php") gives no expected output, and visiting it directly leaves `$_GET["path"]` undefined. It also doesn't say to delete the test file afterwards.
31. README_docker.md is a log rather than a procedure ("Rough Docker Instructions", "Documenting what I had to do"). The compose snippet lacks a `services:` parent and a `ports:` mapping, has an `environment:` key containing only a comment, and has no `docker compose up` step.
32. README_docker.md never says to save the nginx section as `activity-bot.conf` (the mounted file `/path/to/your/docker/stuff/activity-bot.conf`), or to place `index.php`, `.env`, and the other files in the mounted directory. It doesn't say whether `.htaccess` is needed, or how the config interacts with the image's built-in default server on port 8080.
33. README_docker.md has copy-paste leftovers and inconsistencies: "# Internal port for postiz" (a different project) and `server_name you.host.com` versus ``Host(`your.host.com`)``. It doesn't cover file ownership for the container's PHP user, or HTTPS for readers who don't use Traefik, even though the main README requires an HTTPS certificate.
34. The README mentions that patches require attesting to being human, but doesn't link `CONTRIBUTING.md`, which exists in the repository, so contributors have no pointer to the actual process.
=== CRITIQUE U3721 END ===
