=== CRITIQUE U3972 START ===
1. **No instructions for obtaining the software.** The Set Up section starts at "0. Set up a new sub-domain" and never says how to get the files (clone, ZIP, release), which files to upload, or whether `tools/` and `tests/` should be uploaded.

2. **PHP 8.5 requirement is not actionable.** "[PHP 8.5](https://www.php.net/releases/8.5/en.php) (We live in the future now.)" gives no way to check the host's version, no statement of what fails on older PHP, and no guidance on obtaining 8.5 on common hosts, Debian/Ubuntu or a Raspberry Pi. The nginx doc's `sudo apt-get install php php-curl` and `sudo apt-get install php8.5-fpm` assume a repository that stock distributions do not provide.

3. **Requirements are incomplete and inconsistent.** The list names PHP and "The [OpenSSL Extension]" only, but README_nginx.md installs `php-curl`. It also never states that the Apache path needs Apache, `mod_rewrite`, and `AllowOverride` so that `.htaccess` is honoured, and it does not say what to do on LiteSpeed or other hosts.

4. **Joke requirement line hides real information.** "Docker, Node, MongoDB, Wayland, GLaDOS, React, LLM, Adobe Creative Cloud, Maven (absolutely none of these!)" mixes real tools with jokes, and Docker is then offered as an option in the FAQ. Newcomers cannot tell which items are jokes, and the tone of "Because I hate you and want you to suffer" may put off non-technical readers.

5. **Setup instructions are buried under the wrong heading and numbering.** "### Set Up" sits inside "## Minimum Requirements", after a long feature list, and the steps are numbered "0." then repeated "1." items. The reader cannot tell the true step order or count.

6. **Step 1 does not say where or how to edit `index.php`.** "Edit the `index.php` file to add a username, password, and keypair." does not name the variables or location in the file, and does not say which source wins if both `index.php` and `.env` are populated.

7. **README never explains how to generate keys or the password.** The key and password tools are mentioned only in `.env.example`; the Set Up steps do not link to `tools/rsa_key_generator.html` or `tools/generate_password.php`.

8. **Wrong filename for the key generator.** `.env.example` says "Generate locally by opening `tools/rsa_keys.html`", but the repository file is `tools/rsa_key_generator.html`.

9. **Key formatting is unclear.** "Newlines must be replaced with "\n"" does not say whether the generator tool does this automatically, or how to do it by hand for a 27-line key.

10. **Password generation requires local PHP, and the API password type is ambiguous.** "Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`" and `php tools/generate_password.php` assume a PHP CLI that many shared-hosting users lack. The README never states that `.env` holds a hash while the API examples' `"password": "your-password-here"` must be the plain password, and gives no advice on quoting a hash containing `$`.

11. **Inconsistent comment syntax in `.env.example`.** Nearly every comment starts with `#;`, but the line `#	This is the joined date of your bot.` starts with `#` only, which may be parsed differently if the file is read INI-style. There is no statement of the file format or parser rules.

12. **Dotfile handling is not addressed.** Instructions to rename `.env.example` to `.env` and upload `.htaccess` do not warn that Windows, cPanel and FTP clients hide or reject dotfiles.

13. **Ambiguous deployment directory.** "Upload `index.php` and `.htaccess` to the *root* directory of your domain. For example `test.example.com/`." does not say that this means the document root configured for the subdomain, which is often a different folder from the account home or `public_html`.

14. **Secrets protection not explained or verified.** The README never says that `.htaccess` is what stops `.env` and `/data` being downloaded, or how to test that. The private key lives in a web-root file. The nginx files add a deny rule, but there is no check step.

15. **Writable directories and permissions are not mentioned.** The bot has to create `/data/logs`, `/data/followers`, `/data/inbox`, `/posts`, and `/quotes`, but nothing says the web user needs write access or whether the folders are auto-created. This is likely to bite Docker bind mounts and VPS users.

16. **Inconsistent directory layout.** "Log files are saved as .txt in the `/data/logs` directory." and "Post files are saved as .json in the `/posts` directory." and "`/quotes` directory" put some data under `/data` and some at the top level, with no explanation, and `/posts` is publicly served while `/data` is blocked.

17. **Avatar and banner step is incomplete.** "Optionally, upload an avatar and banner image to make the user look nice." does not say where to put them, what filename to use, or that `AVATAR`/`BANNER`/`FAVICON` in `.env` must be set to the relative path.

18. **Webfinger check lacks expected output and the right URL.** "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details." gives no sample output, does not mention the `resource` query parameter normally used, and offers no troubleshooting for 404, blank page or 500.

19. **Placeholders are not mapped to the user's values.** `@username@test.example.com`, `test.example.com`, and `"your-password-here"` are never tied explicitly to the `USERNAME` setting, the user's own subdomain, and their password, and in Docker docs the placeholders vary (`your.host.com`, `you.host.com`).

20. **Follow-and-log verification is unreachable or vague.** "Check your `/data/logs/` directory to see if the follow request was received correctly." assumes file access, does not say what a correct entry looks like, and gives no guidance for failure (no follow arrives, signature fails, no log directory).

21. **No troubleshooting section anywhere.** There is no guidance on enabling PHP error display, reading Apache/nginx error logs, or the usual causes of failure (rewrite not active, wrong document root, permissions, PHP version, HTTPS issues).

22. **API prerequisites are vague.** "This assumes you have a modern version of Python and have installed the popular Python Requests library" has no minimum version or install command. The debugging snippet's `from requests_toolbelt.utils import dump` needs another package that is not listed.

23. **API examples do not show success or failure.** None of the snippets print `r.status_code` or `r.text`, and the docs never describe the expected response, so users cannot tell if the call worked. "Check it has worked" only suggests checking social media or the site root.

24. **Location example has latitude and longitude swapped.** `"longitude": 40.77563, "latitude": -73.97474` uses New York's latitude as longitude and vice versa. Both values are valid in either field, so no validation error will reveal it.

25. **Post IDs are not explained.** "You will need the ID of your post:" (delete and edit) does not say where to find the `guid`, and the edit example posts to `/action/send` while delete uses `/action/delete` without noting the difference.

26. **Media upload format is opaque.** `files = [("1",("This is the alt text", open("red.png", "rb")))]` hides alt text in the filename slot without saying so, and there are no file-type, size, or count limits beyond the final paragraph about servers.

27. **Many advertised features have no usage documentation.** The feature list claims unfollow, block, unblock, show followers, quote posts, hashtag views, and profile updates (partly), but the API section documents only post, follow, DM, media, delete, edit, content warning, reply, hashtags, location, update, and move.

28. **Account migration instructions are inconsistent and incomplete.** `OLD_NAME`/`NEW_NAME` are described in `.env.example` as a "full account URl" (e.g. `https://new.example/users/username`), but the Move request uses `"user": "@new@example.com"`. The text has a typo ("acount") and does not say that the new account must set an alias first.

29. **Docker guide is not a runnable procedure.** README_docker.md lacks a `docker compose up` command, does not say to save the nginx block as `activity-bot.conf`, does not say where `index.php`, `.htaccess` and `.env` go in the mounted directory, and does not mention ownership or permissions for the container user.

30. **Docker compose snippet has copy-paste leftovers and gaps.** "# Internal port for postiz" is from another project, `entrypoints: web-secure` and `certresolver: letsencrypt` are setup-specific, "ymmv" leaves non-Traefik users without a `ports:` mapping or TLS plan, and `environment:` is left with only a commented-out line.

31. **Docker nginx block may conflict with the image's own default server.** "# Default server definition" with `listen 8080` is mounted into `conf.d` without saying whether it replaces or collides with the image's built-in site config.

32. **nginx guide omits installation context.** README_nginx.md does not say where the config file goes, how to enable and reload it, or how to add HTTPS (the config only has `listen 80`). `sudo apt-get install php php-curl` also pulls in Apache on Debian/Ubuntu, which can clash with nginx, and the guide does not warn about it.

33. **nginx comment undermines confidence in a required directive.** "I don't THINK these are needed but computers are oh so very confusing" leaves the user unsure whether the commented-out `fastcgi_params` and related lines matter, and `/var/run/php/php8.5-fpm.sock` is distribution-specific.

34. **nginx test step is incomplete.** "to test the config, make a file `test.php`" does not say where to create it, what output to expect, or that it should be deleted afterwards.

35. **No guidance on local testing or HTTPS prerequisites.** The docs require a public HTTPS subdomain but give no way to try the bot locally before going live, no note about stability of the domain and keys (changing either later breaks the account's identity), and no backup advice.

36. **Tone and wording create friction for first-time readers.** Sentences like "Because I hate you and want you to suffer." and "Dunno. Try it and find out." in the FAQs, plus undefined terms (sub-domain, webfinger, keypair, root directory), make the docs harder for non-experts, and the "Check it has worked" section sits inside the API chapter instead of the setup path.
=== CRITIQUE U3972 END ===

=== CRITIQUE U2813 START ===
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
=== CRITIQUE U2813 END ===

=== CRITIQUE U3723 START ===
# Simulated first-time setups of ActivityBot

## Person 1: Priya, illustrator, non-technical, cheap shared cPanel hosting, Windows laptop

"I want a little bot that posts my daily sketch. The Quickstart is four lines, nice. 'Create a subdomain' - OK, cPanel has that. 'Upload `index.php`, `.htaccess`, `.env.example`' - I can't see `.htaccess` in my file explorer. I had to turn on hidden files. Then 'Rename `.env.example` to `.env`', but the Set Up section says rename *first*, fill it in, and then upload `.env`. Which one do I do? Do I edit it on the server or locally?

I open the file. 'Generate locally by opening `tools/rsa_key_generator.html`'. I only have three files from the Quickstart. I download the whole repo and find it. It makes two long blocks, and now I'm told 'Newlines must be replaced with "\n"'. How? By hand? I did it in Notepad with find and replace and I'm not sure I got it right. Then 'PASSWORD' needs `password_hash(...)`, which is PHP, and I don't have PHP on my laptop. `php tools/generate_password.php` - what is `php`? I'm stuck for an hour and nearly quit.

My host's PHP selector tops out at 8.3. The README says 'PHP 8.5 (We live in the future now.)' and nothing about what happens on 8.3. Does it work? Will it break? I leave the PHP version alone and hope. I visit `/.well-known/webfinger` and get an error page (or maybe a blank page). The README says it should show JSON, but not what to do if it doesn't. Is it the PHP version, `.htaccess` being ignored, or my `.env`? No idea. I stop."

## Person 2: Sam, sysadmin, Ubuntu VPS, wants nginx

"Fine, I'll use the nginx page. 'Requires `php8.5-fpm`' - Ubuntu's repos don't ship 8.5 and it doesn't say which third-party repo. I run `sudo apt-get install php php-curl` as instructed and it pulls in Apache, which grabs port 80 so nginx won't start. Nothing mentioned installing nginx at all, or where the config file goes, or enabling the site and reloading. I sort that out.

I paste the config. It listens on port 80 only, while the main README says an HTTPS certificate is required and the test URL is `https://...`. I run certbot on my own. The deny rule `location ~ ^/(.env|data)` has unescaped dots, so it also matches paths like `/database`, and `deny all;` followed by `return 404;` is redundant and confusing. The comment 'I don't THINK these are needed but computers are oh so very confusing' doesn't inspire confidence about the commented-out lines.

I create `test.php` as described. Visiting it shows 'Path is...' plus a PHP warning about an undefined key, so I can't tell whether that's success. It also doesn't say to delete `test.php` after. Then step 7 says 'Check your `data/logs/` directory' - but who creates `data/`? PHP-FPM runs as www-data and my web root is owned by me. The nginx page says nothing about permissions (the Caddy page does). I chown it by trial and error."

## Person 3: Dana, homelab enthusiast, Docker and Traefik on a NAS

"README_docker.md calls itself 'Rough Docker Instructions', and it is. The compose block is a fragment: no `services:` key, no `ports:` for people not using Traefik. How would I reach it without Traefik? The volume `/path/to/your/docker/stuff/activity-bot/:/var/www/html/public` - presumably that's where I put `index.php`, `.htaccess`, `.env`, but it doesn't say so. The second volume points to `activity-bot.conf`, which I have to realise is the nginx config in the next section; no one tells me to save it under that name. The `environment:` key is left with only a comment under it, which may be an invalid empty mapping in compose.

Copy-paste leftovers: '# Internal port for postiz' (what's postiz?), `your.host.com` in the Traefik rule but `you.host.com` in `server_name`. The entrypoint `web-secure` is specific to someone's setup. The nginx config here uses `fastcgi_pass 127.0.0.1:9000` while the other page uses a socket. Does my conf in `conf.d` replace the image's default server or clash with it on port 8080? No explanation. I also can't confirm `serversideup/php:8.5-fpm-nginx-alpine` is a tag that exists; the README doesn't link to it. I get it going after reading the image's docs myself."

## Person 4: Jo, Raspberry Pi at home, Caddy, residential internet

"The intro says it runs on a Raspberry Pi, but I find no Pi-specific setup. I take the Caddy page. It doesn't say how to install Caddy, where the Caddyfile lives, or how to reload. It also doesn't mention that to get a certificate I need DNS pointing to my home IP and ports 80/443 forwarded; the main README says only 'HTTPS certificate (Let's Encrypt is fine.)'. Raspberry Pi OS also doesn't have `php8.5-fpm` in its default repos, and `apt-get install php` there pulls in Apache again.

Reading the Caddyfile: it blocks `/.env` and `/php_errors.log` only. The nginx pages also block `data`, which holds the logs. Caddy leaves `data/` open? I add a block myself, but a less careful person wouldn't. `php_errors.log` appears nowhere else in the docs. Then 'You may have to adjust the permissions... as Caddy and PHP often run as different users' - which users, what commands? I use `test.php` and see a warning about an undefined array key; is it working? I assume yes."

## Person 5: Lena, data scientist, strong Python, new to PHP and the Fediverse

"I'll use Apache on a small VPS, following the main README; it says 'The default set up assumes Apache or similar' but never mentions enabling `mod_rewrite` or `AllowOverride All`, or how to run PHP (mod_php or FPM). My `.htaccess` is ignored at first and `.env` is publicly readable, with the private key inside. The README never warns me about that.

I do the setup, but step 5, 'search for your user', needs a Fediverse account. I don't have one, and there's no pointer on how to get one. `/.well-known/webfinger` with no `?resource=` returns an error for me instead of 'a JSON file with your user's details'. I try with `?resource=acct:name@domain` and it works.

I move on to the API. 'Requirements' says I should have Requests installed, but not how, and the Debugging section needs `requests_toolbelt`, which isn't mentioned. The examples say `"password": "your-password-here"` - is that the hash I put in `.env` or the plain password? The text says it's 'encrypted when you send it and never stored'. The location example has `"longitude": 40.77563, "latitude": -73.97474` and I recognise those as swapped (that's roughly New York, latitude first). For Delete and Edit I need the `guid`: 'You will need the ID of your post' - from where? 'See `$allowed_elements`' - in which file? I can't find unfollow, block, unblock or the quote-post option in the API section, though the Features list claims them. The image example uses the alt text as the file's 'name' in a tuple, which is not explained, and I'd never guess it. I spend a while reading `index.php` to fill these gaps."
=== CRITIQUE U3723 END ===

=== CRITIQUE U5302 START ===
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
=== CRITIQUE U5302 END ===

=== CRITIQUE U8803 START ===
1. The requirement "[PHP 8.5](https://www.php.net/releases/8.5/en.php) (We live in the future now.)" gives no help checking the installed version, no advice for hosts that only offer older PHP, and no statement of what happens on 8.3 or 8.4. Shared-hosting users cannot tell whether they can proceed.

2. The "Minimum Requirements" list only names the OpenSSL extension and does not say that the cURL extension (installed in `README_nginx.md` via `php-curl`) or other PHP extensions are needed. It also never names the web server, nor Apache's `mod_rewrite` / `AllowOverride` requirement that makes the `.htaccess` work.

3. The Set Up section never says how to obtain the files (download, clone, release archive) and never says which files to upload and which to leave off the server. `tools/`, `tests/`, `AGENTS.md` and the other repository files are not mentioned, and `tools/` is never described.

4. The README says "Edit the `index.php` file to add a username, password, and keypair" without saying where in the file to edit or which variables to change. It then offers `.env` as an alternative without saying which one wins if both are set, or what format index.php expects.

5. `.env.example` tells the user to generate keys by "opening `tools/rsa_keys.html`", but the file in the repository is `tools/rsa_key_generator.html`. The README itself never explains the keypair step at all.

6. "Newlines must be replaced with "\n"" gives no method for doing the replacement and no description of what the key generator outputs (PKCS#1 or PKCS#8, single line or multi-line). It does not say whether the tool works offline, which matters for a private key.

7. The password instructions ("Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`" or `php tools/generate_password.php`) assume a local PHP installation, which the README never requires, and offer no alternative. Nothing states that `PASSWORD` holds a hash while the API examples send the plain text as `"your-password-here"`, and nothing warns about `$` characters in the hash inside a `.env` value.

8. The mandatory/optional split in `.env.example` leaves the sample values ambiguous. The sample `SUMMARY`, `PROFILE_NAME_1` to `PROFILE_VALUE_4` link to the author's repository, licence and social account, and nothing says to replace or blank them. It is also unclear whether empty profile fields are acceptable.

9. Set Up step 3 ("Optionally, upload an avatar and banner image") does not say where to put the images or that `AVATAR`/`BANNER` must also be set in `.env`. It also repeats limits (2MB, 400x400, 1500x500) that appear only in `.env.example`.

10. "Upload `index.php` and `.htaccess` to the *root* directory of your domain" is ambiguous on hosts where the subdomain's document root is a subfolder, and does not distinguish the document root from the account home directory. It also does not warn that dotfiles (`.htaccess`, `.env`) are hidden by many FTP clients and file managers.

11. The README never says whether the `.htaccess` blocks web access to `.env` and `/data`, although the nginx and Docker configs explicitly deny them. Apache users storing a private key in the web root cannot tell whether it is exposed.

12. The docs never say that the PHP process needs write permission to create and write `data/`, `posts/` and `quotes/`, whether these directories are created automatically, or who should own them. Silent write failures would leave the user with no logs and no explanation.

13. Directory locations are described inconsistently and with leading slashes: "Log files are saved as .txt in the `/data/logs` directory" and "Post files are saved as .json in the `/posts` directory" versus `/data/followers`, `/data/inbox` and `/quotes`. It is unclear what these paths are relative to, and why only some sit under `/data`.

14. For users with no domain or host, "Set up a new sub-domain on your web host" is the only guidance. The FAQ says "you should create free subdomains" but gives no provider or method. Nothing addresses people with an existing site on the apex domain, or hosts that cannot create a subdomain or only offer a subdirectory.

15. Step 5, "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details", gives no example of the expected output. WebFinger normally expects a `resource=` query, so a bare visit may well return an error. There is no guidance on what an error means.

16. Step 6 uses `@username@test.example.com` without saying that `username` is the `USERNAME` setting, and says nothing on whether the account name is fixed once it has followers. Step 7, "Follow your user", does not say whether the bot auto-accepts or what the follower should see on success.

17. Step 8 ("Check your `/data/logs/` directory to see if the follow request was received correctly") does not explain how to read the directory without shell or FTP access. It does not say what a correct log entry looks like or what to do if the folder is empty.

18. The README has no troubleshooting section. The only "Debugging" section covers dumping Python `requests` traffic, not server-side errors, PHP error logs, a failing webfinger, a follow that stays pending, or federation not working.

19. Numbered list formatting in Set Up ("0." followed by repeated "1.") and the stray backtick placement in "an `.htaccess file`" make the steps harder to follow. The step count is also unclear when rendered.

20. The "Using the API" examples are Python only. The "Requirements" paragraph gives no install command for Requests, and the "Debugging" example imports `requests_toolbelt`, which is not listed as a requirement. There is no curl example despite "you can use whichever language you want".

21. The README does not state that `"password"` in the examples is the plain-text password rather than the hashed `PASSWORD` value from `.env`. The placeholder `"your-password-here"` is not enough to settle this.

22. None of the "Post a message" or other examples show the response, so readers cannot see what success looks like or find the post's URL. Yet "Delete Post" and "Update / Edit Post" say only "You will need the ID of your post" without saying where the `guid` comes from.

23. The alt-text mechanism in `files = [("1",("This is the alt text", open("red.png", "rb")))]` is not explained: the second tuple element normally holds a filename, and nothing says it is used as alt text. The multi-image example reuses it as "red", "green", etc., and neither example closes the files nor states size or format limits. "You can also post audio and video in the same way" gives no example, formats or size limits.

24. In the location example, `"longitude": 40.77563, "latitude": -73.97474` appear to be swapped, since 40.77563 N / 73.97474 W is New York. Both values are valid numbers, so copying this would silently place a post at the wrong location.

25. "You can send HTML. Only formatting elements are allowed." does not say which elements or attributes are allowed, and what happens to disallowed ones. This sits next to a feature list that claims autolinking and a "doesn't do" list saying HTML conversion is not accurate.

26. The feature list advertises "Unfollow accounts", "Block accounts", "Unblock accounts", "Show followers", "View hashtags posted by the bot" and "Allow quote posts" but gives no usage example for any of them. It also never lists the valid `action` values, and their exact spelling or case.

27. The README contradicts itself about incoming data. The "doesn't do yet" list says "Receive messages (other than follows, unfollows, and quote requests)" and the FAQ says it doesn't store replies, while "How this works" says "Messages sent to your inbox are saved as .json in the `/data/inbox` directory".

28. The migration section is unclear. `.env.example` says to enter the "full account URl" (for example `https://new.example/users/username`) for `OLD_NAME`/`NEW_NAME`, but the Move example posts `"user": "@new@example.com"`. The README does not state the order of operations or whether the Update action is needed after editing `.env`, and "acount" is misspelt.

29. Disk-usage guidance is inconsistent. The requirements say "Expect lots of logs" and `.env.example` warns that logs "can exhaust your file limits", while the FAQ says "Probably not" for filling the disk. The README never mentions `MAX_LOGS` by name, even where it tells users they can adjust the limit.

30. Nginx and Docker users are not told in Set Up that the `.htaccess` flow does not apply to them. The only pointers sit at the bottom of the FAQ ("Can I use nginx?", "Can I use Docker?"), long after the Apache-oriented steps.

31. `README_nginx.md` runs `sudo apt-get install php php-curl` followed by `php8.5-fpm`, which installs two different PHP versions on stock Debian/Ubuntu. It does not mention that 8.5 is not in the default repositories, so a third-party repository is needed. It also never says to install nginx, or how to enable the site and reload.

32. The nginx example places a `map` block directly above `server {}` in a code block, without saying it must go in the `http` context, which breaks configurations pasted into a server block. It listens only on port 80 although HTTPS is required, and gives no TLS or certbot guidance. It never says where `.env` goes, or which user should own `/var/www/test.example.com/`.

33. The `README_nginx.md` test file ("make a file `test.php`" and "attempt to access it on test.example.com/test.php") would print an empty or warning-laden path because the request is not rewritten. It does not say what a correct result looks like, and it does not say to delete the file afterward. The comment "I don't THINK these are needed but computers are oh so very confusing" leaves the user unsure which fastcgi settings to keep.

34. The deny rule `location ~ ^/(.env|data)` has an unescaped dot and no trailing boundary, so it also matches paths like `/database`, and it appears after the PHP location in both nginx files. It would also not protect `.php` files under `data/`. `README_nginx.md` does not carry the dotfile deny rule that the Docker config adds.

35. The `README_docker.md` compose snippet is not a complete file: no `services:` key, and an `environment:` key containing only a comment. It has no `ports:` mapping for non-Traefik users and no certificate or HTTPS guidance without Traefik. It leaves the `.env` and `index.php` placement inside the bind mount unspecified, and says nothing about permissions or user IDs on that mount.

36. The Docker files contain copy-paste leftovers and inconsistencies: the label comment "Internal port for postiz", the host `your.host.com` in the labels versus `you.host.com` in `server_name`, and a "Default server definition" listening on 8080 without saying whether it must replace the image's own default site.
=== CRITIQUE U8803 END ===

=== CRITIQUE U3579 START ===
## Five simulated users following the README

### 1. Priya, hobbyist, cheap shared cPanel hosting (Apache), no command-line experience

"A bot on the Fediverse that posts one poem a day. Nice. The feature list is long and cheerful. I skim to find where to start... there's a heading called 'Minimum Requirements' and then, inside it, 'Set Up'. Odd place for it, but fine."

"PHP 8.5, 'We live in the future now.' Ha. How do I know what my host runs? It doesn't say. I look in cPanel: the highest option is 8.3. Am I stuck? Is 8.3 okay? Nothing says what actually breaks on an older version, and nothing says how to check."

"Step 0: a subdomain. Done, and the HTTPS certificate appears after a while. Step 1: 'Edit the `index.php` file to add a username, password, and keypair.' Where in the file? I open it and it's thousands of lines. Alternatively rename `.env.example` to `.env`. That sounds easier. But the repo hasn't told me how to get the files in the first place. Git clone? Download ZIP? I click around GitLab until I find a download button."

"I open `.env.example`. It says to generate keys by opening `tools/rsa_keys.html`. There's no such file; there's `tools/rsa_key_generator.html`. I guess. It generates keys. The file says 'Newlines must be replaced with "\n"'. Does the tool already do that? I paste the key into the file and it's multi-line, so I hand-edit 27 lines into one, hoping I got it right."

"Password: 'Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`' or run `php tools/generate_password.php`. I don't have PHP on my laptop. Is there a web page for this? No. I give up and put my plain password into PASSWORD. Probably wrong, but nothing tells me it would be."

"Rename `.env.example` to `.env`. Windows Explorer complains about a name with no base name. cPanel's file manager hides dotfiles, so I can't even see `.htaccess` or `.env` after uploading until I find a 'show hidden files' checkbox. Nothing in the README warns me."

"Upload to 'the *root* directory of your domain.' Is that my home folder, `public_html`, or the folder cPanel made for the subdomain? I upload to `public_html` and nothing happens on the subdomain because it points at a different folder."

"After I fix that, I visit `/.well-known/webfinger` and get an error. Is that failure or normal? The README says it should show 'a JSON file with your user's details' but not what that looks like, and doesn't say it might need a `?resource=` query. I have no troubleshooting section, and I can't see logs because I don't know if PHP errors are shown."

### 2. Marcus, sysadmin, Ubuntu VPS, nginx, comfortable with the shell

"I'll skip Apache. The FAQ says 'Can I use nginx? Sure, read README_nginx.md.' Fine. The requirement list says PHP 8.5 and the OpenSSL extension. The nginx doc says `sudo apt-get install php php-curl` then `php8.5-fpm`. Wait, curl was never mentioned as a requirement. And Ubuntu's own repos don't have 8.5. Do I need the Sury PPA? Not mentioned. Also the `php` metapackage drags in Apache on Debian and Ubuntu, which will fight nginx for port 80. The doc doesn't warn me."

"The nginx config: it listens on port 80 only. I need HTTPS (the main README insists on it) but there's no `listen 443 ssl` or certbot hint. Where does this file go: sites-available? conf.d? Do I symlink and reload? It isn't said. The `map` block is at the top, outside `server`, which only works in `http` context. I know that, but a less experienced person would not."

"In the PHP block: 'I don't THINK these are needed but computers are oh so very confusing'. Not exactly reassuring; I can't tell whether `include fastcgi.conf` is right on my distro, and the socket path `/var/run/php/php8.5-fpm.sock` is distro specific."

"Test step: 'to test the config, make a file `test.php`'... and 'attempt to access it on test.example.com/test.php.' Where do I make it? What should I see? It doesn't say, and doesn't say to delete it after. Then I look at the main README's setup step 'Check your `/data/logs/` directory' and notice the 'How this works' list puts logs in `/data/logs` but posts in `/posts` and quotes in `/quotes`, not under `/data`. The nginx config denies `.env` and `/data` but serves `/posts`. Is that deliberate? Which directories need to be writable by the php-fpm user? Nothing says. I run it and the follow request fails silently because the web user can't create `data/`."

### 3. Dana, non-technical illustrator, Windows, FTP-only budget host

"I read the feature list: avatar, banner, content warnings. Lovely. Requirements: 'Docker, Node, MongoDB, Wayland, GLaDOS... (absolutely none of these!)' I don't know most of those, and I can't tell which jokes are real requirements. Then the FAQ says 'Because I hate you and want you to suffer.' Is this person angry at me? I'd like warmer words for a first-timer."

"The setup uses 'sub-domain', 'webfinger', 'keypair', 'root directory'. No definitions. Step 4 says 'Optionally, upload an avatar and banner image to make the user look nice.' Upload where, and under what name? `.env.example` says set `AVATAR` to a 'relative URl without leading slash'. But the README step doesn't mention setting that. I upload `avatar.png` and my bot still has the default image."

"I fill `.env`, keep the quotes, and leave the line `#	This is the joined date of your bot.` untouched. That line is the only comment that begins `#` instead of `#;`. If the file is parsed in an INI style, I imagine this could be read as a setting or cause an error. I can't know, and nothing says which comment style is safe."

"I get to 'Follow your user' on a Mastodon account and then 'Check your `/data/logs/` directory'. I only have FTP; the folder isn't there. Maybe it appears later? Maybe permissions? There's no 'what you should see', and no 'if nothing is there, try this'."

### 4. Tomas, homelab person, Docker and Traefik, comfortable with compose

"README_docker.md is titled 'Rough Docker Instructions.' OK, I'll adapt. The compose snippet mounts a folder to `/var/www/html/public` and an nginx conf to `/etc/nginx/conf.d/activity-bot.conf`. The nginx block below doesn't say 'save this as activity-bot.conf'; I infer it. It does say 'This is a mixture of the nginx config...' but it never says that this is the file to mount."

"The compose snippet has `environment:` followed only by a commented-out line. Empty key. Will compose accept it? I'll delete it. The label says '# Internal port for postiz', which is copied from another project and confuses me for a moment. 'Optional Traefik config, ymmv' leaves me to guess: `entrypoints: web-secure` and `certresolver: letsencrypt` are names from the author's own setup, not mine. If I don't use Traefik there's no `ports:` mapping, so 8080 isn't reachable at all, and no TLS advice."

"The nginx block says `# Default server definition` and `listen 8080`. The serversideup image already ships its own default server on 8080. Will mine conflict? Not explained. Placeholders also drift: `your.host.com` in compose and `you.host.com` in the nginx block, `test.example.com` everywhere else."

"No `docker compose up -d` command, no word on where `index.php`, `.htaccess`, and `.env` go in the mounted directory, and no note on file ownership. The image runs as an unprivileged user, so writing `data/` into my bind mount will fail unless I chown. I find that out from an empty log folder. Also `.htaccess` is pointless under nginx, which isn't said."

### 5. Aiko, Python data engineer, Raspberry Pi at home behind a Cloudflare tunnel, Apache

"I mostly want the API. Setup first. PHP 8.5 on Raspberry Pi OS: not available in the stock repo, no pointer. I get it from a third-party source. Apache needs `mod_rewrite` and `AllowOverride All` for `.htaccess` to do anything. The Minimum Requirements list says PHP, OpenSSL, HTTPS, disk. It never says Apache, `mod_rewrite` or `AllowOverride`, and the nginx file's title only hints at it ('instead of Apache'). Without it, every route 404s."

"Now the API. 'This assumes you have a modern version of Python and have installed the popular Python Requests library.' Which Python version? No `pip install requests`. The examples all say `"password": "your-password-here"`. Is this the plain password or the hash I put in `.env`? I assume plain. It's never stated. The examples don't print `r.status_code` or `r.text`, so after the post call I don't know whether it worked. 'Check it has worked' says to look at social media or visit the site root."

"The debug snippet imports `requests_toolbelt`, which isn't in the requirements. The location example: `"longitude": 40.77563, "latitude": -73.97474`. Those numbers are the other way round; 40.77 N, -73.97 is New York, which is latitude 40.77 and longitude -73.97, so I'd be pinning a post to Antarctica without any validation error (both numbers are valid in either field). The edit example says 'You will need the ID of your post' but not where to find the guid, and it posts to `/action/send` while delete uses `/action/delete`."

"Migration: 'Once your new acount is set up' (typo), and `NEW_NAME` is a 'full account URl' like `https://new.example/users/username`, but the Move request uses `"user": "@new@example.com"`. Different formats for the same account; I have to guess whether either is accepted. And the feature list advertises unfollow, block, unblock, show followers, quote posts, and viewing hashtags, but the API section only documents follow and move, so I can't tell the parameter names."

---
=== CRITIQUE U3579 END ===
