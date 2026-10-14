# Simulated walkthroughs of the ActivityBot README

## Person 1: Priya, illustrator, non-technical, cPanel shared hosting

"A bot that posts my daily sketches, nice. I already pay for hosting at `priya-art.example`. The intro says 'create a subdomain', so I make `bot.priya-art.example` in cPanel. Quickstart says upload three files, rename `.env.example` to `.env`, edit it. Fine.

I scroll to 'Minimum Requirements'. 'PHP 8.5 (We live in the future now.)' My cPanel PHP selector tops out at 8.3. Is the README wrong, or is my host just old? There's no 'what if my host is older' note, and a few paragraphs earlier it said it 'will run on shared hosts'. I email support and they say 8.5 is 'coming'. Let's pretend they enable it.

Now the `.env`. It says I must 'Generate locally by opening `tools/rsa_key_generator.html`'. What tools folder? I downloaded one file and the quickstart only named three. I go back to the repo and find it. I open it in my browser, get two big blocks of text, and the comment says 'Newlines must be replaced with "\n"'. Do I do that by hand? Does the page already do it? I paste them in and hope.

Then PASSWORD: 'Generate with `password_hash(...)`' or 'run on the command line `php tools/generate_password.php`'. I don't have PHP on my laptop, and I don't know what a command line is. I'm stuck here for a long time. The hash starts with `$2y$...` and I'm not sure whether the dollar signs are safe inside the quotes.

I finally upload. My File Manager hides dotfiles, so I can't see `.htaccess` or `.env` after uploading and I don't know if they arrived. The README says 'root directory of your subdomain'. cPanel put the subdomain in `public_html/bot`. Is that the root? Probably.

I visit `/.well-known/webfinger` and get an error, or maybe a blank page. The README says it 'shows a JSON file with your user's details' but gives no example of what it should look like. I have no idea whether blank means broken, and there's nothing about where errors go. I give up for the night."

## Person 2: Marcus, junior backend developer, $6 Ubuntu VPS, nginx

"I'll go with nginx since I have it already. The main README says 'upload'. I'm on a VPS, so I clone the repo. README_nginx says 'Requires `php8.5-fpm`'. The first command is `sudo apt-get install php php-curl`. On my Ubuntu that installs the default PHP (8.3) and pulls in Apache, which grabs port 80. Then `sudo apt-get install php8.5-fpm`: 'Unable to locate package'. There's no mention of a third-party repo, and `php-curl` was for the wrong version anyway.

After sorting that out with an external PPA, I paste the nginx config. Where does it go? `sites-available`? Do I symlink it? The doc doesn't say. It also says `listen 80;` and nothing about TLS, yet the main README insists on HTTPS and then tells me to test at `https://test.example.com/test.php`. I run certbot on my own, and hope it rewrites the config properly.

I copy files into `/var/www/test.example.com/`. Do I copy `.htaccess`? It's an Apache file. The doc doesn't say to skip it, so I copy it anyway. `.env`: I've now put a private key in my web root. The nginx block has `location ~ ^/(.env|data)` which I assume protects it, but I'm never told to check it. I curl `/.env` myself.

For the test it says to make `test.php` that echoes `$_GET["path"]`. I hit `/test.php`. nginx sees a real file so it never goes through the rewrite, so `path` is undefined and I get a PHP warning, not 'Path is...' with a value. Is that a pass or a failure? And should I delete this file afterwards? There's no instruction to.

Then `/.well-known/webfinger` returns 500. The `data/` dir can't be created because `www-data` doesn't own the folder. The nginx README says nothing about permissions (the Caddy one at least mentions it). I `chown` and it works."

## Person 3: Sofia, homelab enthusiast, Docker Compose with Traefik

"README_docker is titled 'Rough Docker Instructions' and it says 'Documenting what I had to do'. OK, so I'm on my own a bit. The compose snippet is just a service fragment, with no `services:` header or network, and `environment:` has only a comment under it. I'm not sure that's valid.

The volumes: one folder mapped to `/var/www/html/public`. I assume I put `index.php` and `.env` there, but the Docker doc never says that or points back to the main set-up. The second volume is an nginx conf that I need to create from the 'nginx config' section below, but nothing says to copy it into a file and name it `activity-bot.conf`. Does that conflict with the image's default server on port 8080? No idea.

The Traefik labels have a comment 'Internal port for postiz', which is obviously pasted from a different project, so should I trust the port? The label uses `Host(\`your.host.com\`)` and the nginx config says `server_name you.host.com;`, two different placeholders. I need both to match my domain. If I weren't using Traefik, how would I get HTTPS? 'Optional... ymmv' is all I get.

It starts. The bot can't write `data/` because the container user doesn't own my bind mount. Nothing in the Docker doc mentions permissions or the container's user ID. I fix it on my own. Also there's no `docker compose up -d` and no 'how do I check it's working', so I fall back to the main README's webfinger step."

## Person 4: Tomás, security-minded sysadmin, Raspberry Pi at home, Caddy

"The README says it runs on 'a Raspberry Pi'. Raspberry Pi OS ships an older PHP than 8.5. README_caddy says `sudo apt-get install php8.5-fpm`, which won't exist in the stock repos. Again no third-party repo mentioned.

I don't trust a browser page to generate my private key. Is there an `openssl` command equivalent? The README doesn't say what key size or format the app expects (`BEGIN RSA PRIVATE KEY` vs `BEGIN PRIVATE KEY`), so I can't do it by hand with confidence.

I look at the Caddyfile. It blocks `/.env` and `/php_errors.log` but not `/data`, which is where the logs go. The nginx example blocks `^/(.env|data)`. So is Caddy leaking `data/logs/` and anything else in `data/`? I add a block of my own. Also nobody explains what `php_errors.log` is or where PHP writes it. It's mentioned only here.

HTTPS: Caddy handles it automatically, but the doc never says so, and my Pi is behind a home router with a changing IP. Port forwarding, dynamic DNS and certificates aren't mentioned, even though the README says 'HTTPS certificate (Let's Encrypt is fine.)'. I sort this out on my own.

The `test.php` check has the same flaw I'd expect: `$_GET["path"]` is empty when you request the file directly. I'm not clear whether the output is supposed to verify the `try_files` fallback. I use `/anything` instead and see if index.php answers."

## Person 5: Aisha, experienced Python developer and long-time Mastodon user, managed Apache VPS, moving from an existing account

"Apache and PHP 8.5 are already set up. Quickstart: upload, rename, edit. I get the keys and hash on my own machine. The README then says to 'Follow your user' and check `data/logs/`. What should I see? File names? A JSON body? 'received correctly' isn't defined.

I want to migrate my old account, so I put `OLD_NAME` in `.env`. 'Once your new ActivityBot is set up, go to your old account and follow its procedure for migrating away.' On Mastodon that means setting an alias on the new account first. Does `OLD_NAME` do the alias? I assume so, though it isn't stated.

I write the Python. `password` here is plain text, but the `.env` holds a hash. The README never says to send the plain one, and it says 'The password is encrypted when you send it', which isn't true of a plain form POST. Presumably it means TLS. Then `requests` isn't given an install command, and `requests_toolbelt` for debugging isn't listed anywhere.

Posting works. I try the location example: `"longitude": 40.77563, "latitude": -73.97474`. That's latitude 40.7, longitude -73.9, so the values are swapped, and I get New York pinned in Antarctica-ish nonsense (or rejected). Alt text: `files = [("1",("This is the alt text", open("red.png", "rb")))]`. The alt text is in the filename slot. That's clever, but nothing says so, and I'd never guess it. For deletion I need 'the ID of your post'. Where do I get a guid? Not explained. I try to unfollow and block, which are in the feature list, but only `Follow` and `Move` have examples; I read `index.php` to find the action names. Same for `$allowed_elements`, which is a variable in source I have to go find.

Finally the AI policy says LLMs were not used 'to write, design, or test anything', but the repo has an `AGENTS.md` file at the root. If I want to send a patch, I need to 'attest that you are a human'. There's no mechanism, and there's no mention of `CONTRIBUTING.md` or how to run the tests in `tests/`."

# PROBLEMS

1. The Quickstart and Set Up disagree on order and contents. Quickstart says "Upload `index.php`, `.htaccess`, `.env.example` to your subdomain" and then rename on the server, while Set Up says "Rename `.env.example` to `.env`" first and then upload `.env`. Quickstart also omits the HTTPS certificate that Set Up step 0 requires, and it never mentions generating keys or a password.
2. Key generation is a hidden prerequisite. `.env.example` says "Generate locally by opening `tools/rsa_key_generator.html` on your computer", but neither Quickstart nor Set Up mentions the `tools/` directory, how to obtain it, or that someone who only downloads `index.php` won't have it. There is no `openssl` alternative, no stated key size or format, and no explanation of what the page does with the private key.
3. The newline handling for keys is unclear. "Newlines must be replaced with "\n"" does not say whether the generator page already outputs the escaped form or whether the user must do it by hand, and no worked example is given.
4. The password hash step assumes PHP on the user's own machine and command-line access. "Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`" and "`php tools/generate_password.php 'Y0ur_p4s5w0rd'`" give no option for someone without PHP CLI. Nothing says whether the `$` characters in the hash are safe inside the double quotes in `.env`.
5. The README does not say which password goes where. `.env` holds a hash, while the API examples use `"password": "your-password-here"`, and the doc never states that the plain-text password is what you send.
6. "The password is encrypted when you send it and never stored on your server" is misleading or unexplained. The examples send the password as a plain form field, so it is protected only if HTTPS is in use, and the README does not say that. It also does not explain that the server stores a hash.
7. "PHP 8.5 (We live in the future now.)" conflicts with the claims "It will run on shared hosts, a Raspberry Pi, or any modern web server" and "You can FTP these files onto any host and be guaranteed they'll run." Many shared hosts and Raspberry Pi OS or stock Linux repos don't offer 8.5, and there is no advice on checking the version or what to do if it isn't available.
8. The extension requirement is ambiguous. "This should include the following extensions by default" does not say what to do if cURL or OpenSSL are missing, and the cURL link points at a PHP 8.5 release-notes anchor ("persistent-curl-share-handles") that has nothing to do with enabling the extension.
9. Both the nginx and Caddy READMEs tell users to run `sudo apt-get install php php-curl` and then `sudo apt-get install php8.5-fpm`. On stock Debian/Ubuntu, `php8.5-fpm` is not in the default repositories (no repo or PPA is mentioned), `php-curl` installs for the distro's default PHP rather than 8.5, and the `php` metapackage may pull in Apache and conflict with nginx or Caddy.
10. "Upload ... to the *root* directory of your subdomain. For example `test.example.com/`" is ambiguous on hosts where the document root is a folder such as `public_html/bot`. It conflates the URL root with the filesystem folder.
11. Dotfiles (`.htaccess`, `.env`, `.env.example`) are hard to see, rename and upload in many file managers, FTP clients and operating systems. The README gives no hint about showing hidden files or verifying that they arrived.
12. The README never says how to obtain the files (git clone, release archive or single-file download) or which version to use.
13. "If you prefer, you can edit `index.php` and place the details in there." gives no location, variable names or format in `index.php`.
14. Apache requirements are unstated. The default setup relies on `.htaccess`, yet requirements don't mention `mod_rewrite`, `AllowOverride`, or what to do on hosts that ignore `.htaccess` ("Apache or similar" is the only hint).
15. There is no check that the secrets are protected. The private key sits in `.env` under the web root, and the README never tells the user to confirm that `/.env` and `/data/` return an error, nor does it warn that a non-Apache setup leaves them exposed.
16. The Caddy config blocks only `path /.env` and `path /php_errors.log`. Unlike the nginx config's `location ~ ^/(.env|data)`, it does not block `/data`, where logs are written. Neither the nginx nor Docker configs block `/php_errors.log`, and `php_errors.log` is never explained anywhere.
17. The nginx and Caddy READMEs omit the practical deployment steps. They don't say where the config goes, how to enable and reload it, or where to copy the files. nginx has no TLS (`listen 80;`) although the README requires HTTPS and tests over `https://`, and nothing is said about certificates (certbot or otherwise) for nginx.
18. File-permission guidance is missing or vague. The nginx README has none and Caddy only says "You may have to adjust the permissions of the directory ActivityBot is installed in, and/or the permissions of the directories it creates on the first run" without naming users or commands. Docker also says nothing about the container user and bind-mounted `data/`.
19. The `test.php` check does not test what it claims. It echoes `$_GET["path"]`, but requesting `https://test.example.com/test.php` directly passes no `path`, so the user sees an undefined-key warning or an empty value. It does not exercise the rewrite rules, and nothing says what the expected output is or tells the user to delete the file afterwards.
20. The nginx config contains a hedge that undermines trust: "I don't THINK these are needed but computers are oh so very confusing." The user can't tell whether to uncomment those lines. The nginx example uses a unix socket while the Docker example uses `127.0.0.1:9000`, with no explanation of the difference.
21. README_docker.md is explicitly "Rough Docker Instructions." and is not a complete procedure. It is a fragment with no `services:` header, no `docker compose up`, no explanation of which files go into the mounted `public` folder, and no instruction to save the nginx section as `activity-bot.conf`. `environment:` contains only a comment, which may be invalid or confusing.
22. The Docker doc has copy-paste leftovers and inconsistencies: "# Internal port for postiz" (a different project), `Host(\`your.host.com\`)` versus `server_name you.host.com;`. The relationship between the mounted conf and the image's own default nginx config is not explained. HTTPS is only addressed through the "optional" Traefik labels, so non-Traefik users have no TLS guidance.
23. The Set Up list is numbered "0." followed by repeated "1." items, which renders oddly and makes it hard to say "I'm at step 5". Set Up and Other Servers are also nested under the "Minimum Requirements" heading.
24. Step 4, "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details", gives no sample output. WebFinger normally expects a `resource=` query, so a bare visit may differ from what users expect. There is no troubleshooting for blank pages, 404s, 500s or PHP source shown as text.
25. Steps 5 to 7 are vague. "Check your `data/logs/` directory to see if the follow request was received correctly" doesn't say where `data/` is, that it is created on first run, what file names to look for, or what a correct entry looks like. It also doesn't say what to do if the follow doesn't appear.
26. No troubleshooting or common-failure section exists at all (instance can't find the user, cached failures, wrong PHP version, permissions, blocked routes).
27. The Set Up ends without a first post. Posting is only covered later in the API section, which is not linked from the final step. "Check social media to see if the message appears" does not say that only followers will see it or what to do if it doesn't.
28. Non-programmers have no way to post. The only interface is the HTTP API, with examples only in Python. There are no `curl` examples or field reference table, and "you can use whichever language you want" leaves non-Python users to infer parameter names from Python snippets.
29. The API requirements are incomplete. "have installed the popular Python Requests library" has no install command, and the Debugging section imports `requests_toolbelt`, which is not listed in the requirements.
30. The API examples show no responses. `r` is never inspected, so users don't know what success or failure looks like, what status codes are returned, or how to obtain the post ID that is needed for later calls.
31. Deleting and editing require "the ID of your post" (`guid`), but nothing says where to find it. Likewise "See `$allowed_elements` to see which ones are supported" refers to a variable in `index.php` without saying where.
32. The location example has swapped coordinates: `"longitude": 40.77563, "latitude": -73.97474` for the John Lennon Memorial in New York. 40.77 is a latitude and -73.97 is a longitude, so a user copying the example will be misled.
33. The alt-text mechanism is undocumented. In `files = [("1",("This is the alt text", open("red.png", "rb")))]` the alt text is placed in the filename slot of the tuple, and nothing says so. The multi-file example has the same pattern with "red", "green", etc. Audio and video are covered only by "You can also post audio and video in the same way", with no size, format or field details.
34. Several advertised features have no usage documentation. The feature list names unfollow, block, unblock, quote posts and moving followers, but only `Follow` and `Move` appear under `action/users`. The other action names and parameters are not given.
35. The profile and avatar guidance is unclear. Step 8, "Optionally, upload an avatar and banner image... Edit `.env` to include the image locations", does not say where to upload them or that the user must then call `action/update` to tell followers. The `.env.example` text says only "Should be a relative URl without leading slash", with no base given. "maximum of 2MB, 400x400" does not say whether the size is exact or a maximum.
36. The optional profile fields in `.env.example` ship with live example values (including a mention of the author's account and a link to the project source). The README doesn't say they are published as-is unless changed or blanked, or whether removing them is allowed.
37. The `.env.example` is internally inconsistent. One comment line starts with `#` instead of `#;` ("#	This is the joined date of your bot."), `MAX_LOGS=2048` is unquoted while `PAGE_SIZE="1000"` is quoted, and the file never says whether quoting matters. There are also typos such as "URl" (several times) and "acount" ("Once your new acount is set up").
38. The Migrate Accounts text is confusing. For moving away it says to add `NEW_NAME`, "Once your new acount is set up, go to your new account and follow its procedure for moving followers to it", and then to send a Move request. It does not clearly state the order of steps, whether an alias is needed, or what `OLD_NAME` does on the other side.
39. The Bluesky/BridgyFed item is advertised ("Bridge to BlueSky with your domain name via Bridgy Fed") but not documented. `.env.example` just says "If you have bridged this bot to BSky. Add your DID here", with no steps for the bridging itself or the order of setup.
40. "Lenny" in the introduction ("Misskey, Lenny, and hundreds of other services") appears to be a typo for Lemmy, which could confuse someone searching for it.
41. The subdomain and domain advice is inconsistent. The introduction and Set Up tell users to create a subdomain, but the FAQ says "Every bot needs its own domain name" and then "you should create free subdomains". There is no help for people who do not already own a domain or website.
42. The disk-space claims conflict. Minimum requirements say "100MB free disk space (ActivityPub is a very "chatty" protocol. Expect lots of logs.)" while the FAQ says the disk "Probably not" fills up. The relationship to `MAX_LOGS` and to uploaded media is not explained.
43. The AI policy says "AI was not used at any stage of the construction of this software. LLMs were not used to write, design, or test anything", yet the repository contains an `AGENTS.md` file. The README does not explain it, which looks contradictory to a reader.
44. Contributor guidance is thin. `CONTRIBUTING.md` and the `tests/` directory are not mentioned or linked from the README, there are no instructions for running the tests, and "you must attest that you are a human and wrote the code yourself" does not say how or where to attest.
45. There is no information on maintenance. Nothing covers backing up the private key and `data/` (losing the key loses the account identity), upgrading to a new version of `index.php`, or removing the bot.
46. The Docker, nginx and Caddy guides each assume a different set of host details (Linux, apt, systemd, Debian paths). Windows, IIS and other hosting situations are not addressed, and the "Apache or similar" label for the default setup doesn't say what "similar" includes.
