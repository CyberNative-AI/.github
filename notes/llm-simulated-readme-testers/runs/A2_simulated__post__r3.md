# Simulated walkthroughs

## 1. Priya, hobbyist poet, budget cPanel shared host, no command-line experience

"A bot that posts my poems. Quickstart is four bullets, nice. First: where do I get the files? There's no download link, no 'clone' or 'releases' mention. I find the GitLab link buried in the Feedback section and in the sample bio text. I download a zip and now there's a `tests/` folder and a `tools/` folder. Do those get uploaded? It doesn't say.

I make a subdomain in cPanel. It creates a folder inside `public_html`. The docs say 'It will not work in a subdirectory.' But my subdomain IS a folder inside my main site's folder. I'll assume that's fine.

Requirements: 'PHP 8.5'. My host's selector tops out at 8.3. 'Will run on shared hosts', it says. Does it need 8.5 really, or is that a joke like the Wayland line? I pick 8.3 and hope.

Upload `.env.example`... then rename. The file manager hides dotfiles until I find a 'show hidden files' checkbox. The docs never mention it. Quickstart says upload `.env.example` and rename on the server, Set Up says rename first and upload `.env`, and the comment inside the file says rename then upload. Which is it?

Inside the file: 'Generate locally by opening tools/rsa_key_generator.html'. OK, opened it, got two blocks of text. 'Newlines must be replaced with "\n"'. Replaced how? By hand, in a text editor? I paste it and break the quotes twice. For PASSWORD I'm told to run `password_hash(...)` or `php tools/generate_password.php`. I don't have PHP on my laptop. I give up on that and put my plain password in, which feels wrong.

Visit `/.well-known/webfinger`: I get an error about a missing resource. Is that broken or normal? No example output is shown. I can't tell. I also leave all four sample profile fields in, because nobody says they would be published as they are. Later I find my bot's bio links to someone else's source repository.

I search for my user from Mastodon: nothing. No troubleshooting section. Then 'check data/logs/'. There's no `data` folder. Does it appear after the first request? Does it need write permission? I'm stuck."

## 2. Marcus, intermediate Linux user, Raspberry Pi at home, nginx

"The intro says Raspberry Pi is fine. I choose nginx. `sudo apt-get install php php-curl` followed by `sudo apt-get install php8.5-fpm`. Raspberry Pi OS has no `php8.5-fpm` in its repositories. The doc doesn't say which third-party repository to add. Worse, the first command installs the distro's default PHP, plus possibly Apache as a dependency, which grabs port 80 while I want nginx. I end up with two PHP versions and `php-curl` for the wrong one.

I never find where the Set Up steps say to configure a web server. They assume Apache and `.htaccess`. The nginx page doesn't say whether I should skip uploading `.htaccess`.

The nginx config: `server_name test.example.com`, `root /var/www/test.example.com/`, and the socket path. It doesn't tell me what to change. It's labelled `bash` but isn't a script. Where does it go? `sites-available`? Do I symlink it? `nginx -t`? Reload? It only listens on port 80. The Requirements demand HTTPS. Nothing says how to add a certificate. It's also a home connection: nothing about DNS, a dynamic IP, port forwarding, or that Mastodon must be able to reach the Pi on 443. That's the whole difficulty for me and it's absent.

The test: make `test.php`, visit it, expect 'Path is...' plus a value. I get a PHP warning about an undefined array key, because `test.php` is served directly and never goes through the rewrite. So the test doesn't test the rewrite. It also never says to delete the file afterwards.

Also the comment 'I don't THINK these are needed but computers are oh so very confusing' makes me trust the config less. Logs: the app apparently creates `data/` on first run, but only the Caddy page mentions that and permissions. My `www-data` user can't write. I chmod 777 as a guess."

## 3. Dana, professional sysadmin, Ubuntu VPS, Caddy

"I already run Caddy. The Caddy page opens with the same apt commands as the nginx page: `php php-curl` then `php8.5-fpm`. On Ubuntu LTS, 8.5 is not in the stock archive. No PPA is mentioned. Also, `php` plus `php-curl` and `php8.5-fpm` mixes versions.

The Caddyfile: I read it properly. It blocks `/.env` and `/php_errors.log`, but not `/data`, where logs live. The nginx version blocks `^/(.env|data)`. So the two supported configs protect different files. Logs include remote actors' requests. Is `data/` meant to be public? Nobody says. The `.htaccess` for Apache presumably protects things, but the README never says what it protects, so I can't audit parity.

`php_fastcgi` and `file_server` sit outside any `handle` block, with `root *` last. I'll trust Caddy's directive ordering, but there's no explanation of the intended flow, no `caddy validate`/reload step, and no comment explaining the `/post` and `/tag/*` handlers.

'You may have to adjust the permissions of the directory... as Caddy and PHP often run as different users.' Which directory, which owner, what mode? No commands. This is the very likely first failure and it's one vague sentence.

Same `test.php` check as nginx. With `try_files` it's served directly, so `$_GET["path"]` is unset. So I can't verify the rewrite. I verify by hitting webfinger. The README says to visit `/.well-known/webfinger` bare. It needs `?resource=acct:...`; I know that, a newcomer wouldn't."

## 4. Jonas, homelab enthusiast, Docker plus Traefik

"A 'Rough Docker Instructions' file. 'Documenting what I had to do'. Honest, but it's a fragment: a service block indented as if under `services:`, with no top-level file, no network definition, no `docker compose up` command.

`environment:` is followed only by a commented-out line (`# PHP_OPCACHE_ENABLE: "1"   // Increase performance`). That leaves an empty key and uses `//` inside a YAML comment. Do I uncomment it? Compose may complain about a null mapping.

Volumes: I map a host directory to `/var/www/html/public` and a conf file into `/etc/nginx/conf.d/`. The doc never says to put `index.php` and `.env` in that host directory, that `.htaccess` is useless here, or which UID must own it. The image runs as a non-root user, and the app needs to write `data/`. I hit permission errors again. Does the conf file replace or sit beside the image's default server, which also listens on 8080?

The Traefik labels say 'Internal port for postiz', a leftover from another project. The host is `your.host.com` in labels and `you.host.com` in the nginx config, and it's `test.example.com` everywhere else. 'The Traefik stuff is optional, especially if you're not using Traefik' tells me nothing about how to terminate TLS without it, and the labels need a shared network that's never mentioned.

The nginx section says it's a mixture, with `fastcgi_pass 127.0.0.1:9000`, unlike the socket in README_nginx. Fine, but there's no statement of which parts are required. It does deny `.env` and `data`, good. It doesn't mention `php_errors.log`, which the Caddy config blocks."

## 5. Aisha, Python-literate CS student on Windows, existing Mastodon account to migrate, managed Apache host

"I code in Python, not PHP. Windows Explorer won't let me type `.env` as a name without a trailing-dot trick. Docs don't say. I get the files on the host, a subdomain, HTTPS via the host's one-click Let's Encrypt.

I want to move my Mastodon followers here, so I set `OLD_NAME`, which needs a 'full account URl' like `https://example.social/users/username`. My Mastodon instance isn't Mastodon-flavoured at that path and the docs don't say how to find the actor URL. 'Follow its procedure for migrating away' is all I get. On Mastodon that requires an alias on the new account, which isn't mentioned. Is the alias what `OLD_NAME` sets? Unclear.

Now the API. 'Requirements' says Python and Requests, but 'Debugging' imports `requests_toolbelt`, which isn't listed. The posting example doesn't print anything, so I don't know if it worked: 'Check social media to see if the message appears.' The password: 'The password is encrypted when you send it and never stored on your server.' But I put a hash in `.env`; so is the hash stored? What do I send, the plain password or the hash? The example says 'your-password-here'. I guess plain. Also, 'encrypted'? Isn't it just HTTPS?

Delete needs 'the ID of your post'. Where do I get it? Not stated. The images example puts alt text where a filename goes: `("1",("This is the alt text", open(...)))`. Is that deliberate? Key `"1"` means? The location example: `"longitude": 40.77563, "latitude": -73.97474`. Those look swapped. 40.77 is a valid latitude and -73.97 is a longitude in New York, so the pair is reversed. If I copy it, I get a wrong pin.

Features list says I can unfollow, block, unblock and allow quote posts, but there's no example for any of them. `$allowed_elements` is mentioned for HTML but I don't know where it is. Move: 'Then you will need to send a Move request to your ActivityBot' reads backwards when I'm moving away, and `NEW_NAME` wants a URL but the example sends `@new@example.com`. And after editing `.env` for the avatar, nobody told me to call Update Account."

---

# PROBLEMS

1. The docs give no download or clone source for the files. Quickstart starts with "Upload `index.php`, `.htaccess`, `.env.example` to your subdomain" but never says where to get them. It also doesn't say that `tests/` and `tools/` should not be uploaded.

2. The Quickstart, the Set Up section and `.env.example` disagree on the order and file to upload. Quickstart says "Upload `index.php`, `.htaccess`, `.env.example` to your subdomain" then "Rename `.env.example` to `.env`". Set Up says "Rename `.env.example` to `.env`" first and then upload `.env`, and the file's own header says "rename this file to .env and upload it".

3. Hidden dotfiles are never mentioned. `.htaccess` and `.env` are invisible in many file managers and FTP clients, and are awkward to rename on Windows. Nothing says to show hidden files or how to rename them.

4. The Set Up numbering is "0." followed by a run of "1." items. It is ambiguous when read as plain text and makes it hard to refer to a step.

5. "PHP 8.5 (We live in the future now.)" is presented as the minimum, and the joke leaves it unclear whether older versions really fail. It also conflicts with "It will run on shared hosts... or any modern web server", since most hosts do not offer 8.5. No check for the installed version is given.

6. "This should include the following extensions by default" is hedged and incomplete. It doesn't say what to do if an extension is missing or how to check, and it doesn't say whether other extensions (for example for image handling) are needed.

7. The requirements list says "any modern web server" and "Apache or similar", but never states the Apache needs: `mod_rewrite`, `AllowOverride`, or that `.htaccess` must be honoured. Nothing says what `.htaccess` actually does or protects.

8. The nginx and Caddy pages begin with `sudo apt-get install php php-curl` and then `sudo apt-get install php8.5-fpm`. This installs the distribution's default PHP, which may differ from 8.5 and may pull in Apache. It also never says which repository provides `php8.5-fpm`, and Raspberry Pi OS and current Ubuntu LTS do not ship it by default.

9. The Raspberry Pi and home-hosting case is advertised ("a Raspberry Pi") but has no guidance on DNS, dynamic IPs, port forwarding, reaching the server from outside, or obtaining a TLS certificate. The only certificate advice is "HTTPS certificate (Let's Encrypt is fine.)".

10. "Create a subdomain" is given without explanation. It is not stated how (DNS record versus hosting panel), what a document root is, or what to do when the host places the subdomain in a subfolder of the main site. This clashes with "It will not work in a subdirectory."

11. The key generation instructions are scattered across comments in `.env.example` ("Generate locally by opening `tools/rsa_key_generator.html` on your computer"). The Set Up steps do not mention them at all, and the file is easy to miss since it is in `tools/`. Nothing says what output to expect or how to confirm the generator works offline.

12. "Newlines must be replaced with "\n"" doesn't say how. There is no method (editor find/replace, command) and no note on whether the generator already outputs the single-line format. The sample shows `BEGIN RSA PRIVATE KEY` and `BEGIN PUBLIC KEY` headers, and it is unclear if keys with other headers are accepted.

13. Password setup assumes PHP is installed on the user's own computer. It offers "`password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`" and "`php tools/generate_password.php 'Y0ur_p4s5w0rd'`", with no alternative for users without PHP and no note that the hash contains `$` characters that may be mangled inside a double-quoted value such as `PASSWORD=""`.

14. Which password to send is never stated. `.env` holds a hash, but the API examples show "your-password-here". It should say that the plain-text password is sent. "The password is encrypted when you send it and never stored on your server" is also unclear or contradictory, since the hash is stored in `.env` and the password is only protected by HTTPS in transit.

15. `.env.example` ships sample values for optional fields, such as `SUMMARY` with a link to the project source, `REALNAME`, `BIRTHDAY` and four `PROFILE_NAME_n`/`PROFILE_VALUE_n` examples. Nothing says they will be published as the bot's profile if left in, or how to remove them.

16. The `USERNAME` line ("Do not include an "@". Do not include the domain name.") doesn't say how the domain part is derived, whether it can be changed later, or what happens to followers if it changes. The relationship to the subdomain is only implied.

17. "If you prefer, you can edit `index.php` and place the details in there." gives no location, variable names, or warning about keeping secrets in a file that is served.

18. `.env.example` mixes comment prefixes. Most lines start with `#;`, but one ("This is the joined date of your bot.") starts with a plain `#`. The `#;` convention is not explained either, and a user may not know whether it matters.

19. The webfinger check, "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details", gives no example output and omits the usual `?resource=acct:...` query. A bare visit may show an error that a newcomer would read as failure. No troubleshooting follows for 404, 500, a blank page or certificate errors.

20. No document tells the user that `data/` (and its `logs/` subfolder) is created by the software on first run and that the web server user must be able to write there. Set Up step "Check your `data/logs/` directory" assumes it exists, and the only mention of permissions is a vague line in the Caddy page: "You may have to adjust the permissions of the directory ActivityBot is installed in...". That line gives no user, mode or command.

21. "Go to Mastodon or other Fediverse site and search for your user" and "Follow your user" give no expected outcome. It is unstated whether the bot auto-accepts, what a correct log entry looks like, and how to proceed if the account cannot be found, since remote servers cache lookups.

22. The setup ends at "Follow your user" with no "post your first message" step, and the only posting method is a Python script in a later section. Users without Python have no curl or browser option. The "Requirements" subsection doesn't say where to run the code or how to install Requests.

23. The optional avatar/banner step ("Edit `.env` to include the image locations") doesn't say where to upload the files relative to the root, or that "Update Account" (the `/action/update` call, documented much later) must be run before followers see changes. `.env.example` mentions size limits only in comments.

24. The README lists "Unfollow accounts", "Block accounts", "Unblock accounts", "Allow quote posts" and "Bridge to BlueSky" under Features, but there are no usage instructions or API examples for them. The `DID` field is mentioned only in `.env.example`, and Bridgy Fed setup is not documented.

25. "You can send HTML. See `$allowed_elements` to see which ones are supported." refers to a variable inside `index.php` without saying where it is or what it contains.

26. "Debugging" uses `requests_toolbelt`, which isn't listed under Requirements, where only Python and the Requests library are. None of the examples print the response (`r.status_code`, `r.text`) or describe expected success and error responses, so users must guess whether a call worked ("Check social media to see if the message appears").

27. The Delete and Update/Edit sections say "You will need the ID of your post" but never say where to find the `guid`. The example value is shown without any source.

28. The media example `files = [("1",("This is the alt text", open("red.png", "rb")))]` puts alt text where a filename normally goes, without explanation. It doesn't explain the meaning of the keys `"1"`..`"4"`, size and format limits, or how to give alt text for several images. The audio and video case only says "in the same way", with no example.

29. The location example appears to have swapped coordinates: `"longitude": 40.77563, "latitude": -73.97474`. Those values are a latitude and a longitude respectively for the named New York place, and no valid ranges are given.

30. The Migrate Accounts section is hard to follow. "Once your new acount is set up, go to your new account and follow its procedure for moving followers to it. Then you will need to send a Move request to your ActivityBot" reads as if the direction were reversed. It omits the alias step that many servers require, and "OLD_NAME" instructions don't explain how to find an actor URL for non-Mastodon software.

31. Migration formats are inconsistent. `.env.example` asks for a full URL ("https://new.example/users/username") for `NEW_NAME`, while the API example sends `"user": "@new@example.com"`. It also isn't said whether `.env` changes need an Update Account call afterwards.

32. The disk-space messaging contradicts itself. Requirements says "100MB free disk space (ActivityPub is a very "chatty" protocol. Expect lots of logs.)" while the FAQ says "Will this fill up my disk? Probably not." `.env.example` warns that logs "can exhaust your file limits" (inodes or file counts), which the Requirements never mention.

33. The nginx and Caddy configs don't say what to substitute. `test.example.com`, `/var/www/test.example.com`, and the PHP socket path must be edited, but this is not stated. There is also no information on where the config file goes, how to enable it, how to test it (`nginx -t`, reload, `caddy validate`), or how to add HTTPS to the nginx example, which only has `listen 80;`. The nginx block is also labelled `bash`.

34. The `test.php` check on the nginx and Caddy pages ("echo $_GET["path"];") doesn't exercise the rewrite, because `.php` files are served directly. `path` is therefore unset and produces a warning or empty output. Nothing says what the expected result is or that the test file should then be deleted.

35. The Caddy and nginx examples deny different paths. Caddy blocks `/.env` and `/php_errors.log` but not `data`, whereas nginx blocks `^/(.env|data)` but not `php_errors.log`. Neither page states which paths must be protected, so users may leave logs or the private key reachable.

36. README_nginx.md contains the doubtful comment "I don't THINK these are needed but computers are oh so very confusing." followed by commented-out directives. It leaves users unsure whether the config is complete or whether to enable them.

37. The nginx and Caddy pages don't say whether `.htaccess` should be uploaded or ignored, even though Quickstart lists it as required.

38. README_docker.md is a fragment rather than instructions. There is no full compose file, no network definition, no `docker compose up` command, and no statement that `index.php` and `.env` must be placed in the mounted host directory. File ownership for the container's non-root user, which must write `data/`, is not covered.

39. In the Docker compose snippet, `environment:` contains only a commented-out line with a `//` suffix, so it is unclear whether to uncomment it or remove the key. The comment "Internal port for postiz" is a leftover from a different project.

40. The Docker page uses inconsistent hostnames: `your.host.com` in the Traefik label, `you.host.com` in the nginx `server_name`, and `test.example.com` elsewhere. It also says "the Traefik stuff is optional, especially if you're not using Traefik" without saying how to expose the container or terminate TLS otherwise, nor what shared network Traefik needs.

41. The Docker page doesn't say whether the supplied nginx config replaces or sits alongside the image's own default server, which also listens on port 8080. It doesn't explain why it uses `fastcgi_pass 127.0.0.1:9000` unlike the socket in README_nginx.md.

42. Typos and naming slips reduce trust: "Lenny" appears where the Lemmy service seems intended, "acount", and inconsistent "URl"/"URls". These are minor but appear on the very first page.
