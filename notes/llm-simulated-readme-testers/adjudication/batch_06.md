=== CRITIQUE U7370 START ===
## Simulated users

### 1. Priya, a writer with no coding background (Mac, cPanel shared hosting)

"The Quickstart is four bullets. Good. Where do I get `index.php`, though? There is no download link, no 'Code' button mentioned, nothing. I go back to the repo page and download a ZIP.

"Subdomain: cPanel has a subdomains screen, fine. It's HTTPS, fine. Now 'Upload `index.php`, `.htaccess`, `.env.example`'. My Mac hides every file that starts with a dot. I can't see `.htaccess` or `.env.example` in Finder. After some searching I find Cmd-Shift-period. Now 'Rename `.env.example` to `.env`'. Finder complains about names starting with a dot.

"I open the .env file. 'Generate locally by opening `tools/rsa_key_generator.html`.' Which `tools` folder? I didn't upload one. I find it in the ZIP and open it in the browser. It makes two blocks of text with real line breaks. The file says 'Newlines must be replaced with "\n"'. Do I do that by hand across 25 lines for each key? Does the page already do it? I don't know.

"Next, 'Generate with `password_hash(...)`' or 'run on the command line `php tools/generate_password.php`'. I don't have PHP on my laptop. I don't know what a command line is for. I'm stuck, so I paste my plain password into `PASSWORD=""` and hope. Everything below that is example text about a colours bot. If I leave it, will my account say 'Get the source code' and have a profile field about somebody else's Mastodon handle? Do I delete the lines or leave them?

"The requirements say 'PHP 8.5 (We live in the future now.)'. My host's PHP selector tops out at 8.3. I don't know whether that kills everything or whether 8.3 is okay. I pick 8.3 and carry on.

"Set Up step 3 says upload to the 'root directory of your subdomain'. In cPanel the subdomain folder is `public_html/test`, so I upload there. Step 4: I visit `/.well-known/webfinger` and get an error page, maybe a 400 and maybe a 500. I can't tell whether that is what the page is supposed to say, and the README has no screenshot or sample output. I stop here."

### 2. Marcus, a Linux sysadmin (Ubuntu VPS, nginx, comfortable with the shell)

"I'm on nginx, so I skip to README_nginx.md. 'Requires `php8.5-fpm`' and then `apt-get install php php-curl`. On Ubuntu `php` pulls in Apache as a dependency, which I don't want next to nginx. There's no PPA mention and `php8.5-fpm` isn't in my stock repos. I add a PPA myself. Nothing says OpenSSL needs to be there, though the main README requires it.

"The nginx block only has `listen 80;`. The main README insists on HTTPS, so I add certbot and 443 myself. I paste the `map` at the top and the `server` block. Where does the file go? Sites-available? conf.d? I know, but the doc doesn't say, and it doesn't mention testing with `nginx -t` or reloading. The `fastcgi_pass` socket is hard-coded to 8.5.

"The comment 'I don't THINK these are needed but computers are oh so very confusing' makes me less sure about the config. Do I need `fastcgi_split_path_info`, or not? Maybe it's best to test it.

"The `test.php` check echoes `$_GET["path"]`. Visiting `/test.php` directly gives me an undefined-array-key warning. There's no expected output and no instruction to delete the file after testing.

"The `location ~ ^/(.env|data)` is an unescaped regex. It also matches `/envelope` and `/database`, and the data directory holds logs. It probably works for the site as shipped. I only care that I'm denying `/data` while the main README says to read `data/logs/`.

"I go back to the main README. It never says how the PHP user gets write access to the web root, so `data/` can't be created until I chown it. The Caddy doc at least hints at permissions. The nginx doc doesn't.

"Then 'Check your `data/logs/` directory' has no log example. The webfinger URL without `?resource=acct:...` may reject me. I try it and it returns something, so I assume it works."

### 3. Jun, a homelabber (Docker Compose on a VPS with Traefik)

"README_docker.md calls itself 'Rough Docker Instructions' and it is. I get a fragment starting at `activity-bot:` with no `services:` header. Fine, I know how to wrap that. `environment:` has only a commented-out line below it, which leaves an empty value, and that may fail validation in some compose versions.

"The volume `/path/to/your/docker/stuff/activity-bot/` is mounted into `/var/www/html/public`. Is that where I put `index.php`, `.htaccess` and `.env`? It never says so. `.htaccess` is useless on nginx, so should I even upload it? The second mount is a conf file I have to create from the next section. The Traefik label comment says 'Internal port for postiz', which looks pasted from another project. It says 8080, and the nginx block listens on 8080, so that part matches.

"The nginx section uses `you.host.com` while the Traefik label uses `your.host.com`. I notice only because I'm hunting for typos. It says 'mixture of the nginx config from README_nginx.md', but this block differs in places, such as `fastcgi_pass 127.0.0.1:9000`, and I'm not sure which behaviors I'm supposed to keep. I also wonder whether this clashes with the image's built-in default server.

"I don't want Traefik. There's no `ports:` mapping and nothing on getting TLS without it. The main README demands HTTPS. Permissions are not mentioned at all. What UID does the image run as, and can it write `data/`?

"I get the container up. I still have to go back to the main README for key and password generation. The password hash is full of `$` characters, and Compose or a dotenv parser may try to interpolate them inside `.env`. Nothing warns me. I also don't know whether an `.env` inside the web root is blocked. The nginx block here denies it, but I only know that because I read it."

### 4. Tomasz, a developer (Debian VPS, Caddy)

"Caddy section. The install block is the same `php php-curl` plus `php8.5-fpm` lines. Debian doesn't have 8.5 in its default repos, so I add a repo. It pulls in Apache with `php` and I have to uninstall it.

"The Caddyfile blocks `/.env` and `/php_errors.log`, but not `/data`, whereas the nginx files block `data`. The logs hold remote server addresses and request bodies. I add `path /data/*` myself. Should I? The docs don't say.

"The Caddyfile has a `redir * /post?id={uri}` rule with a `/post` handle after it. Is that correct? There's no explanation of the routing, so I can't judge it. I assume the author tested it. There's no instruction to reload Caddy or validate with `caddy validate`.

"'To test the config, make a file `test.php`.' I do. `/test.php` shows 'Path is...' and a PHP warning. Is that success? It doesn't say. After that the Caddy doc just stops. I don't know whether I should now go back to Set Up step 3, or which of the Apache-oriented steps to skip. The main Set Up step 2 mentions `.htaccess` as if it matters, and on Caddy it doesn't.

"The README says 'It will not work in a subdirectory'. My Caddy `root` is `/var/www/test.example.com`, which is the root, so fine.

"I follow my own test, request the webfinger URL and get JSON. I search from my test Mastodon account for `@username@test.example.com` and find it. I follow it and check `data/logs/`. It's there, but I have no idea what a correct log entry looks like."

### 5. Aisha, a Python developer (Windows laptop, Raspberry Pi at home, Apache)

"The README says it runs on 'a Raspberry Pi'. I have one at home, so I'll use it. But my Pi sits behind a home router. 'HTTPS certificate (Let's Encrypt is fine.)' is all it says. Nothing on port forwarding, dynamic DNS, a domain, or how to get the certificate. I do that myself. The README also never says whether Raspberry Pi OS gives me PHP 8.5, and my apt gives 8.2. I build PHP 8.5 elsewhere, which burns an evening.

"On Windows, `tools/generate_password.php` won't run because I have no PHP locally. I SSH into the Pi and run it there. The README doesn't say that's acceptable, and the quoting is bash-style single quotes, which fail in PowerShell. I also paste the hash into `.env`, and the `$` signs are a worry.

"Apache: I never see anything about `mod_rewrite`, `AllowOverride All`, or whether `.htaccess` is blocking `.env`. It's the Apache setup that the README calls the default. I enable it based on what I know, and I check that `/.env` returns 403 because the README doesn't say that is something to check.

"The API section. 'The password is encrypted when you send it and never stored on your server.' I'm using HTTPS, so the request body is encrypted in transit, but the password isn't 'encrypted' by the client. And my `.env` contains a hash, not the plaintext, so what should I put in `"your-password-here"`? The hash, or the original password? I try the original. It works.

"I try the 'Post a message' sample. There's no print of `r.status_code` or `r.text` and nothing says what a success looks like. I add prints. The check section says 'Check social media to see if the message appears', but my bot has no followers yet, so nothing appears. I eventually realise I must follow it from another account first.

"I want to edit a post. 'You will need the ID of your post.' Where do I find the guid? I dig through the page source and logs. The 'Add a Location' example uses `"longitude": 40.77563, "latitude": -73.97474`. Those are swapped. 40.77 is a latitude. I put it on a map and it lands in the sea near Antarctica. I run the 'Debugging' snippet and it fails with `ModuleNotFoundError` because `requests_toolbelt` isn't listed in Requirements.

"The Features list says I can unfollow and block accounts, but the API section has no example for either. I guess the action name, `Unfollow`, from `Follow`, and hope."

---
=== CRITIQUE U7370 END ===

=== CRITIQUE U6810 START ===
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
=== CRITIQUE U6810 END ===

=== CRITIQUE U7861 START ===
1. The main README's Quickstart and Set Up disagree with the `.env.example` header and with each other about which files to upload and where the config lives. Quickstart says "Upload `index.php`, `.htaccess`, `.env.example` to your subdomain" and then "Rename `.env.example` to `.env`", while Set Up says to rename first and then upload `index.php`, `.htaccess`, and `.env`. Renaming a file after upload is something many shared-host file managers handle awkwardly, and a leading-dot file named `.env` may be hidden or refused by an FTP client or file manager. The docs never warn about this.

2. The PHP requirement is "PHP 8.5 (We live in the future now.)". It is stated as a hard minimum with a joke and no explanation. The README also says the cURL and OpenSSL extensions "should" be included "by default", which is vague, and it claims the software "will run on shared hosts, a Raspberry Pi, or any modern web server". Most shared hosts do not offer 8.5, and a first-time user has no way to check this or to find out what happens on an older version.

3. The key generation step is the most error-prone part of setup, and the instructions are thin. `.env.example` says "Generate locally by opening `tools/rsa_key_generator.html` on your computer" and "Newlines must be replaced with "\n"". A user who only uploaded the three files from the Quickstart will not have `tools/` at all. The README never says to download or clone the repository, and it never says where the repository is hosted (the only link is in the SUMMARY example). There is also no explanation of how to convert the multi-line key into one line, or what the output of the HTML tool looks like.

4. The password step is confusing. `.env.example` says "Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`" and then "php tools/generate_password.php 'Y0ur_p4s5w0rd'". The first is a PHP function call rather than a command, and the second needs PHP on the command line, which shared-hosting users may not have. It is not stated that the hash contains `$` characters, which may need quoting or escaping in a `.env` value. The API examples use `"password": "your-password-here"`, and nothing says clearly that this is the plain password, not the hash.

5. The README states the API password "is encrypted when you send it and never stored on your server". Nothing explains how it is encrypted. All the examples POST the password in a form body, so it is protected only if HTTPS is used. The claim is misleading and should say more.

6. The README says "If you prefer, you can edit `index.php` and place the details in there", but it does not say where in `index.php` the details go or what the variable names are. The API section also tells users to "See `$allowed_elements` to see which ones are supported", which sends a user into the source code to find a variable name, with no location given.

7. The "Set Up" steps are numbered "0." followed by repeated "1." in the source, so the numbering depends on how Markdown renders. The steps also mix required and optional ones. Step 7 ("Optionally, upload an avatar and banner") comes after the verification steps, and there is no troubleshooting if the webfinger check in step 4 fails. Step 4 asks to visit `https://test.example.com/.well-known/webfinger` and "check that it shows a JSON file with your user's details", but the user is not told what correct output looks like, nor that a `resource` query parameter may be needed. Step 7 says "Check your `data/logs/` directory", but the docs never say that this directory is created on first run, nor what a successful log looks like.

8. The "Quickstart" has no example values and no mention of the HTTPS or subdomain requirements. The statement "It will not work in a subdirectory" appears only in the long Set Up section. Also, the README says the account lives at `@username@test.example.com` while `.env.example` says USERNAME must not include the domain. The README never connects the placeholder `username` to the `USERNAME` variable.

9. The `.env.example` header says "At a minimum, you must provide KEY_PRIVATE, KEY_PUBLIC, PASSWORD, and USERNAME", but the optional section has defaults that are not stated, for example the default values for REALNAME, SUMMARY and BIRTHDAY. The shipped example values (for example the SUMMARY link to the project's source and the BIRTHDAY of "2024-02-29T12:34:56Z") would go live if left unchanged. The user is not warned about that.

10. The `.env.example` comment markers are inconsistent: most lines start with `#;`, but one line reads `#	This is the joined date of your bot.` with no semicolon. This looks like a typo and may confuse anyone parsing the file. Also `AVATAR`'s comment says "Should be a relative URl without leading slash", which is unclear about what it is relative to. Does the image have to be uploaded to the site root? The `.env.example` comment uses "URl" with a lowercase L in several places.

11. The README describes the API but never says how to make the first successful call after installation. The examples hard-code `https://test.example.com/action/send`, depend on the Python `requests` library, and `Requirements` says only "a modern version of Python". A user who does not use Python gets no `curl` example. The "Check it has worked" section says to "Check social media to see if the message appears". That is unreliable for a first test, because a fresh bot has no followers.

12. Several API examples contain mistakes or ambiguities. The location example passes `"longitude": 40.77563, "latitude": -73.97474`, but these values are swapped (40.77 is latitude, -73.97 is longitude for New York). The edit example sends `guid` to `action/send`, so it is not obvious how to distinguish an edit from a new post. The "Follow an account" and "Migrate" examples share the same endpoint with different `action` values, and the list of valid actions (Follow, Unfollow, Block, Unblock, Move) is not given anywhere, even though the features list advertises unfollow, block and unblock. Alt text is passed as the filename component in the `files` tuple, which is unintuitive and not explained. The "Delete Post" and "Update" examples need a `guid` and the README never says where to find it.

13. The nginx, Caddy, and Docker pages each repeat the same commands with minor differences, and they are inconsistent. Both nginx and Caddy pages say "Requires `php8.5-fpm`" and tell the user to run `sudo apt-get install php php-curl` followed by `php8.5-fpm`. On most Debian and Ubuntu releases, `php8.5-fpm` is not in the default repositories, and the docs do not mention adding a third-party repository. The Caddy page also does not install the OpenSSL extension that the main README requires, and no page says how to install Caddy or nginx itself. The nginx config listens only on port 80 with no TLS, even though HTTPS is mandatory. The Caddy block blocks `/.env` and `/php_errors.log` but not `/data`, which holds logs, while the nginx and Docker configs block `^/(.env|data)`. That is an inconsistency which may expose data. Neither README mentions the `.htaccess` rules that Apache users get automatically, so non-Apache users are not told which protections they must replicate.

14. The Docker page is described as "Rough Docker Instructions" and is incomplete. The compose snippet has an empty `environment:` section with a commented-out entry (`# PHP_OPCACHE_ENABLE: "1"   // Increase performance`, which uses `//` as a comment in YAML, where `//` is not a comment marker), a comment saying "Internal port for postiz" (a different project), and host paths like `/path/to/your/docker/stuff/activity-bot/`. It doesn't say how `.env` is supplied, which files go in the mounted directory, what `activity-bot.conf` is (the nginx config in the second block, presumably), or how to start the container. The nginx config uses `server_name you.host.com` while the Traefik label uses `your.host.com`, and the fastcgi pass goes to `127.0.0.1:9000` inside an image that is described as nginx plus fpm, with no check that this is the right address.

15. The test snippet in both the nginx and Caddy pages (`test.php`) is only useful for verifying rewrites, and it is not stated that the user should delete the file afterwards. The Caddy test would also not work as written, because the Caddyfile only routes unknown paths through `index.php`, and reading `$_GET["path"]` on a directly requested `test.php` yields an undefined index warning. In addition, the instructions say that `.env` is "mandatory" but never explain what the server does if the file is missing or invalid, so errors during first setup are hard to diagnose. The Caddy page also mentions `/php_errors.log` without saying where that log is created.

16. The repository file list includes `AGENTS.md`, `CONTRIBUTING.md`, `agpl-3.0.txt`, `tests/` and `.gitignore`, none of which are explained. The README never says which files an end user needs to deploy and which are for development. The README's `Feedback` section points to GitLab, while the project description in the `.env.example` default SUMMARY also points to GitLab, and the README does not state where to download releases. There is no version number, changelog or upgrade instructions, so a user cannot tell how to update an existing bot without overwriting `.env` or data.

17. The "Missing Features" list and the feature list sit before the requirements and install steps. A first-time user has to scroll past roughly 80 lines of emoji bullets before reaching "Minimum Requirements". The README also contains a joke list (`There is no need for Composer, Docker, Node, MongoDB, Wayland, GLaDOS, React, LLM, Adobe Creative Cloud, or Maven`) while the Docker page then exists, which contradicts it. The joke FAQ answer "Because I hate you and want you to suffer" and the long AI policy are not setup problems but add noise and could put off some readers. The statement "Receive replies or private messages" is a limitation, yet the feature list advertises "Send direct messages to users". That may mislead users about whether the bot is one-way.

18. The disk-space and log guidance conflicts. The requirements say "100MB free disk space" and "Expect lots of logs", while the FAQ says "Probably not" to filling the disk, and `.env.example` warns that logs "can exhaust your file limits" with `MAX_LOGS=2048`. The README FAQ states "the most recent 2,048 log files" as a fixed default, but the variable is described as configurable only in the `.env` comments, and the README never names `MAX_LOGS`. Also, `PAGE_SIZE="1000"` is quoted while `MAX_LOGS=2048` is not, with no explanation of whether quoting matters.
=== CRITIQUE U7861 END ===

=== CRITIQUE U2008 START ===
1. The setup steps contradict the example config about what is required and where credentials go. README step 1 says "Edit the `index.php` file to add a username, password, and keypair", while `.env.example` says "At a minimum, you must provide KEY_PRIVATE, KEY_PUBLIC, PASSWORD, and USERNAME. Then rename this file to .env". A first-time user cannot tell which is the primary route, and the README never says whether index.php has the matching variables or which source wins if both are set.

2. The key-generation tool is named inconsistently, so the user cannot find it. `.env.example` says "Generate locally by opening `tools/rsa_keys.html`", but the file list contains `tools/rsa_key_generator.html`. The README never mentions the key tool or the password tool, so it never tells the user how to create the keypair or the password hash that step 1 asks for.

3. The PHP requirement is very likely unsatisfiable for most people, and it conflicts with the project's own claim of broad compatibility. The README requires "[PHP 8.5]... (We live in the future now.)", while the FAQ says "*everything* supports PHP. You can FTP these files onto any host and be guaranteed they'll run." Most shared hosts will not have 8.5. The README does not say whether older versions work or which 8.5 features are needed, and the joke tone hides that this is a hard requirement.

4. The README never says that the `PASSWORD` value is a hash while the API examples send plaintext. `.env.example` says "Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`", and the API examples use `"password": "your-password-here"`. A new user may put the plaintext in `.env`, or send the hash in API calls. The README should state that the API takes the original password and `.env` holds the hash. Also, `.env.example` does not tell the user to quote or escape the `$` characters in the hash.

5. The private key format instructions are easy to get wrong. `.env.example` says "Newlines must be replaced with "\n"", and the placeholder is a single quoted line. Nothing explains how to convert the output of the HTML generator, or whether the tool already outputs it in that form. A malformed key is a likely first-run failure with no documented error message.

6. Several paths and file names are inconsistent or unexplained. The "How this works" section lists `/data/logs`, `/data/followers` and `/data/inbox`, but also `/posts` and `/quotes` without the `/data` prefix. The README never says whether these directories are created automatically, which user needs write permission to the web root, or how to protect them. The nginx configs deny `^/(.env|data)` but not `/posts` or `/quotes`. The README never explains that the `.env` and data directory must be blocked on Apache (it only implies `.htaccess` does this).

7. The README tells the user to upload only "`index.php` and `.htaccess`" and then "Optionally, upload an avatar and banner". The `.env.example` header says to upload it "along with index.php and .htaccess". The step list is flat and mixes the numbering, with "0." followed by repeated "1.", which renders confusingly. The README does not say that `.htaccess` is a hidden file that some FTP clients or file managers skip, or that Apache needs `mod_rewrite` and `AllowOverride` enabled for it to work.

8. The first verification step is unlikely to work as written. "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file". Real WebFinger requires a `?resource=acct:user@domain` parameter, so the bare URL may return an error. The README does not describe the expected output or the common failures (wrong rewrite, missing HTTPS, wrong `USERNAME`).

9. The log check at the end of setup lacks guidance. "Check your `/data/logs/` directory to see if the follow request was received correctly." It does not say what a successful log looks like, what the file names look like, or what to do if the directory is missing, and the leading slash suggests the server root rather than the web root. Elsewhere logs are described as ".txt in the `/data/logs` directory", which a web user may read as a public URL.

10. The `.env.example` has comment markers that look inconsistent. Most comment lines start with `#;`, but one reads `#	This is the joined date of your bot.` with no semicolon. Depending on the `.env` parser, `#;` may not be treated as a comment. The README does not say which parser is used, whether values need quotes, or whether `MAX_LOGS=2048` (unquoted) and `PAGE_SIZE="1000"` (quoted) are handled the same way.

11. Some `.env.example` descriptions are inaccurate or confusing. `AVATAR` says "Should be a relative URl without leading slash", but the README says only "upload an avatar and banner image" and does not say where to put them or how the file name relates to the setting. `NEW_NAME` says "You will then need to POST a move message to the "action/users" endpoint", which the README shows using `"action": "Move"`, but the example does not explain that the "user" must be a full handle rather than the URL that `NEW_NAME` expects. `PROFILE_NAME_n` says there are "four extra pieces of information" but does not say whether fewer or more are allowed. `SUMMARY` and the profile examples point to the upstream author's own links and `@Edent@mastodon.social`, which a user may leave in by mistake.

12. The API documentation has gaps and likely errors. The "Update / Edit Post" example posts to `/action/send` with a `guid`, with no explanation of how it differs from creating a new post. The location example uses `"longitude": 40.77563, "latitude": -73.97474`, which are the wrong way round for New York (latitude is about 40.77, longitude about -73.97). There is no description of response codes or bodies. The README does not say how to get a post's `guid`. The API section also shows passwords in plain form fields, but says nothing about requiring HTTPS or about rate limits or lockout. The "Debugging" snippet needs `requests_toolbelt`, which the Requirements section does not list.

13. The nginx instructions are incomplete and conflict with each other. `README_nginx.md` begins "requires php8.5-fpm which is a thing that passes requests to PHP", but installs `php php-curl` (default PHP version, which may not be 8.5) alongside `php8.5-fpm`, and the install commands assume a specific Debian or Ubuntu repository that ships 8.5. It does not mention the OpenSSL extension, the `.env` upload, HTTPS and certificate setup (the config only has `listen 80;`), or how to reload nginx. The config comment "I don't THINK these are needed but computers are oh so very confusing" undermines trust in the setup, and the `test.php` check is not tied to the next step.

14. The Docker guide is labelled "Rough Docker Instructions" and leaves a user to fill in blanks. The compose snippet has a dangling `environment:` key containing only a commented-out line, which is invalid or empty YAML. It mounts the config to `/etc/nginx/conf.d/activity-bot.conf` but gives no instruction to create that file from the nginx block below. It contains a copy-paste comment, "Internal port for postiz", from another project, and uses `you.host.com` in the nginx block but `your.host.com` in the Traefik label. It does not explain where the `.env` file goes, what permissions the mounted volume needs, or how to start the container, and it uses `fastcgi_pass 127.0.0.1:9000` without saying this is correct for the image. The README says Docker is among the things you do not need, and the FAQ answers "*sigh* If you must", which discourages Docker users.

15. The README's tone and the prerequisites list are confusing at the point where precision matters. "Docker, Node, MongoDB, Wayland, GLaDOS, React, LLM, Adobe Creative Cloud, Maven (absolutely none of these!)" is a joke inside a requirements list. "Why is this built in PHP rather than...?" is answered with "Because I hate you and want you to suffer." A reader skimming for requirements may misread them, and the hostile jokes add little. The requirement "100MB free disk space" conflicts with the FAQ statement of 2,048 logs and a "chatty" protocol, with no sizing basis for the number.

16. The README opens with a long feature list before saying what the software is or what to do first, and the list contradicts itself. It lists "Verify cryptographic signatures, including RFC 9421" as supported, and "Sign messages with RFC 9421 Signatures" as not yet supported, which is a different thing but easy to misread. It also lists "Receive messages (other than follows, unfollows, and quote requests)" as not supported, while "How this works" says "Messages sent to your inbox are saved as .json in the `/data/inbox` directory", with no mention of what happens to those files or how large they get. The two lists are not linked to the setup steps, so a new user cannot tell what works out of the box.

17. Several project-level items are missing or hard to trust. There is no CHANGELOG, version number, or statement of which release the instructions apply to. The funding line says "From 2026-08, this project was funded...", with no end date, and "AGENTS.md" in the file list has no explanation in the README, which is confusing given the "AI policy" section says no AI was used. The "Will this scale" answer ("Dunno. Try it and find out.") gives no guidance, and the README never says how to run the tests in `tests/` or how to contribute beyond "send a Pull Request". `CONTRIBUTING.md` is not linked from the README.

18. The README mixes spelling and typography that look like errors and may affect copy-paste: "`.htaccess file`" with the backtick placed after "file", "URl" and "URls" with a lowercase L, "acount", and "Customisable" alongside American usage. Minor, but in a setup guide the stray backtick makes the file name render wrongly.
=== CRITIQUE U2008 END ===

=== CRITIQUE U2326 START ===
1. The README never says where to get the code or how. Neither the Quickstart nor "Set Up" has a download or clone step, yet the .env file tells you to open `tools/rsa_key_generator.html` "on your computer", which only exists in the repository. A first-time user does not know they need the whole repository (or a release archive) locally, and the only repo link is buried in the `SUMMARY` example value.

2. The Quickstart and "Set Up" contradict each other about the `.env` file. Quickstart says "Upload `index.php`, `.htaccess`, `.env.example` to your subdomain" and then "Rename `.env.example` to `.env`", which implies renaming on the server. "Set Up" says to rename first and then "Upload `index.php`, `.htaccess`, and `.env`". Neither mentions that dotfiles are hidden by default in many file managers and FTP clients and can be skipped when uploading.

3. The PHP requirement is very likely a blocker and is not explained: "PHP 8.5 (We live in the future now.)". It is stated next to the claim that it "will run on shared hosts, a Raspberry Pi, or any modern web server". It gives no way to check the host's PHP version, no statement of whether older versions work, and no fallback. The line "This should include the following extensions by default" is vague, because cURL and OpenSSL are not always enabled on shared hosts.

4. Key generation is under-specified. The .env text says "Generate locally by opening `tools/rsa_key_generator.html`" and "Newlines must be replaced with "\n"". It does not say what the page outputs, whether it already escapes newlines, which browser or key size to use, or that the private key must never be shared or committed. The placeholder `KEY_PRIVATE="-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----"` doesn't show what the finished value looks like.

5. The password step needs PHP on your own machine, which the requirements never mention. The .env file says `php tools/generate_password.php 'Y0ur_p4s5w0rd'` or `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`, but there is no note about needing the PHP CLI locally. It doesn't say the resulting hash (which contains `$` characters) goes into `PASSWORD=""` inside double quotes, and it doesn't say whether to quote or escape it. The example password is also shown in plain text.

6. Nothing tells Apache users that `.env` and `data/` (which holds your private key, hashed password and logs) are protected. The nginx and Docker configs contain `location ~ ^/(.env|data) { deny all; ...}`, but the main README only says "Upload `index.php`, `.htaccess`". It never says `.htaccess` blocks these files, or that `mod_rewrite` and `AllowOverride` must be enabled. There is no step to verify that `https://test.example.com/.env` returns an error.

7. The Caddy config protects different paths than the nginx config. It blocks `path /.env` and `path /php_errors.log` but not `data/`, so logs may be publicly readable. The nginx config blocks `.env` and `data` but not `php_errors.log`. The Caddy test also never explains how to confirm the blocks work.

8. The "Set Up" list has several unclear steps. It is numbered "0." followed by repeated "1." and sits under the "Minimum Requirements" heading. Step "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details" gives no example of the expected output. A bare WebFinger URL normally needs a `resource=` query parameter and may return an error, and there is no troubleshooting if it fails. The text also uses `@username@test.example.com` without saying that `username` is the `USERNAME` value from .env.

9. Directory creation and permissions are not covered. "Check your `data/logs/` directory to see if the follow request was received correctly" assumes that directory already exists, but it seems to be created on first run. Only the Caddy page hints at this ("permissions of the directories it creates on the first run"). The main README doesn't say the web server user needs write access, or what to do if the directory is missing.

10. The `.env` mechanism is unclear. "If you prefer, you can edit `index.php` and place the details in there" gives no location in the file or format. The domain is never configured, so a user can't tell whether the host is auto-detected or what happens behind a proxy. The "Optional Fields" defaults (`REALNAME`, `SUMMARY` linking to the project's source, `USERNAME="example"`) will be published as-is if left unchanged, and nothing says so.

11. The API section describes the password incorrectly or confusingly: "The password is encrypted when you send it and never stored on your server." It is sent as a plain form field protected only by HTTPS, and the server stores a hash. The examples use `"password": "your-password-here"` without saying that this is the plain-text password, not the hash from `.env`. Python Requests is linked, but `requests_toolbelt` (used in "Debugging") is never mentioned as needing installation.

12. The location example has the coordinates the wrong way round. `"longitude": 40.77563, "latitude": -73.97474, "place": "John Lennon Memorial"` uses what are plausibly New York's latitude and longitude values in the wrong fields. A copied example would put the post in the wrong place, or the example may be invalid.

13. Several API instructions rely on knowledge the docs don't provide. Delete and Edit need a `guid`, but nothing says where to find it. "See `$allowed_elements` to see which ones are supported" points to a variable in `index.php` with no location. In the media examples the alt text is passed as the "filename" slot of the Requests tuple (`("1",("This is the alt text", open("red.png", "rb")))`), and the numeric keys "1" to "4" are not explained. Editing uses `action/send` with `guid`, which is not obvious. No responses, status codes or error formats are documented.

14. The Docker page is described as "Rough Docker Instructions" and is not usable as written. The compose snippet has an `environment:` key containing only a commented-out line, no `ports`, and a copy-paste leftover ("Internal port for postiz"). Hosts are inconsistent (`your.host.com` vs `server_name you.host.com`). It mounts a custom `activity-bot.conf` without explaining how it interacts with the image's default nginx config. It uses `fastcgi_pass 127.0.0.1:9000` without saying why that suits this image. The text says Traefik is "optional" but never covers HTTPS otherwise, even though HTTPS is required.

15. The nginx and Caddy pages assume a Debian/Ubuntu package that most repositories don't ship. `sudo apt-get install php php-curl` installs the distribution's default PHP, not 8.5, and `php8.5-fpm` normally needs a third-party repository that isn't mentioned. On Debian and Ubuntu the `php` package can also pull in Apache, which conflicts with nginx or Caddy. The nginx config listens on port 80 only, with no HTTPS or certificate setup, even though "HTTPS certificate" is a stated requirement.

16. The nginx file contains commented-out lines with the note "I don't THINK these are needed but computers are oh so very confusing." This leaves the reader unsure which directives matter. Both web-server pages tell users to create `test.php` in the web root and never tell them to delete it afterwards.

17. The Requirements and FAQ give mixed messages about disk use. "100MB free disk space (ActivityPub is a very "chatty" protocol. Expect lots of logs.)" sits beside the FAQ "Will this fill up my disk? Probably not." and the `.env` note that logs "can exhaust your file limits". The documented `MAX_LOGS` and `PAGE_SIZE` values are quoted inconsistently (`MAX_LOGS=2048` vs `PAGE_SIZE="1000"`), and a page size of 1000 is a large default.

18. The repository layout is unexplained. `AGENTS.md`, `CONTRIBUTING.md` and `tests/` ("PHP unit tests and JSON fixtures") are never mentioned in the README, and there is no command for running the tests despite "There is no need for Composer". An `AGENTS.md` file is also at odds with the README's statement that "AI was not used at any stage", which can confuse readers. There are no upgrade, backup or uninstall instructions, and no troubleshooting section beyond API debugging.

19. The README leads with a very long feature list and then a "Missing Features" list before the requirements, which pushes setup information down. There are small errors and jokes that hurt trust, for example "Lenny" (probably Lemmy), "URl", "acount", and FAQ answers such as "Because I hate you and want you to suffer" and "Dunno. Try it and find out." Some feature entries are ambiguous, for example "Receive replies or private messages" missing next to "Send direct messages to users", and "Allow quote posts" next to "Change quote post visibility".
=== CRITIQUE U2326 END ===

=== CRITIQUE U1670 START ===
1. There is no instruction on how to obtain the software. The Set Up section starts with hosting and then 'Edit the `index.php` file...' without saying where to download or clone it. The repository link appears only under 'Feedback' and inside `.env.example`.

2. Credentials can go in two places, with no recommendation or precedence rule: 'Edit the `index.php` file to add a username, password, and keypair.' and 'If you prefer, you can rename `.env.example` to `.env` and place the details in there.' The README does not say how to edit `index.php` (which variables), nor what happens if both are set.

3. The README Set Up never mentions generating the key pair or the password hash. Those tools are named only in `.env.example`, so a reader following only the README doesn't know what a keypair is or where to get one.

4. `.env.example` points to a file that does not exist: 'Generate locally by opening `tools/rsa_keys.html`'. The file in the repository is `tools/rsa_key_generator.html`.

5. The `.env` key format is unclear: 'Newlines must be replaced with "\n"'. It doesn't say whether the key generator tool already does this, or how to do it by hand.

6. The password flow is not explained. `.env.example` says PASSWORD must be generated with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );` while every API example sends `"password": "your-password-here"`. Nothing says you send the plaintext password to the API and store only the hash in the config.

7. Generating the password hash assumes a local PHP command line ('php tools/generate_password.php'), which hosting-only or Windows users may not have. No alternative is offered, and the README never lists it as a prerequisite.

8. The requirement 'PHP 8.5 (We live in the future now.)' is not available on many shared hosts or stock distributions. The README says nothing about how to check the PHP version, whether older versions work, or where to get 8.5 (README_nginx's `sudo apt-get install php8.5-fpm` also does not mention a repository).

9. Requirements are incomplete. Only the OpenSSL extension is listed ('This is usually installed by default.'), but README_nginx installs `php-curl`, and the Debugging section needs `requests_toolbelt`. The README doesn't list required PHP extensions, nor Apache `mod_rewrite` and `AllowOverride` for `.htaccess` to work.

10. The main README never says it assumes Apache. It talks about `.htaccess` only, while README_nginx.md is titled 'Using Nginx instead of Apache'. A reader on another web server won't know until they reach the FAQ.

11. The line 'Docker, Node, MongoDB, Wayland, GLaDOS, React, LLM, Adobe Creative Cloud, Maven (absolutely none of these!)' is under 'Minimum Requirements' and contradicts the FAQ that offers Docker instructions. A joke in a requirements list makes it unclear whether Docker is supported.

12. `.htaccess` and `.env` are hidden dotfiles that many FTP clients, file managers, and Windows Explorer hide or refuse to rename. The README says 'rename `.env.example` to `.env`' and 'Upload `index.php` and `.htaccess`' with no warning about this.

13. `.env.example` ships with sample values (REALNAME, SUMMARY with a link to the author's repository, BIRTHDAY, PROFILE_NAME_1 to PROFILE_VALUE_4, and USERNAME="example"). The README doesn't say that these will appear on the live profile unless edited or blanked.

14. Setup step on avatar and banner is incomplete: 'Optionally, upload an avatar and banner image to make the user look nice.' It doesn't say that the `AVATAR` and `BANNER` settings must be filled in with a relative path, nor the size limits that are documented only in `.env.example`.

15. The root-directory instruction is ambiguous: 'Upload `index.php` and `.htaccess` to the *root* directory of your domain... It will not work in a subdirectory.' On shared hosts the subdomain's document root may be a subfolder or `public_html`. The README doesn't say to point the subdomain's document root at the upload folder, or whether a bare domain works.

16. The webfinger check is not verifiable: 'Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details.' No example output is shown, and real WebFinger lookups normally need a `resource` parameter. There is no guidance for what to do on a blank page, 404, or 500.

17. The search step uses a placeholder handle: 'search for your user: `@username@test.example.com`'. It doesn't say that `username` is the `USERNAME` setting, nor that the domain must be exactly your subdomain.

18. Directory and permission information is missing. 'Check your `/data/logs/` directory to see if the follow request was received correctly' never says the directory is created automatically, whether the web user must be able to write to it, or what a correct log looks like. It also gives no troubleshooting for the common failure where nothing is logged.

19. The "How this works" list uses inconsistent paths: `/data/logs`, `/data/followers`, `/data/inbox` but `/posts` and `/quotes` with no `/data` prefix. Readers can't tell which folders must be writable, or which to protect.

20. The README does not say that `.env`, `data/`, and the private key are protected on Apache, or how to verify that. The nginx configs deny `.env` and `data` explicitly, but the Apache path is silent, and the private key sits in the web root.

21. The README mentions inbox storage: 'Messages sent to your inbox are saved as .json in the `/data/inbox` directory.' This conflicts with the feature list ('Receive messages (other than follows, unfollows, and quote requests)' is not supported) and with the FAQ 'Why doesn't this store replies?'.

22. The API section is Python-only: 'All the examples here use Python 3 - but you can use whichever language you want'. There is no curl example and no description of the endpoint, field names, or content type for other languages. The Requirements text assumes `requests` is installed without showing how.

23. API examples never show or explain the response (status code, body, returned post ID or URL). Readers can't tell success from failure, except by 'Check social media'.

24. Delete and edit say 'You will need the ID of your post' without saying where to find the `guid` (response, website, log, or file name).

25. The 'Add a Location' example has the coordinates swapped: `"longitude": 40.77563, "latitude": -73.97474, "place": "John Lennon Memorial"`. 40.77 is the latitude and -73.97 the longitude for that place.

26. Alt text for images is passed in the filename slot of the files tuple (`("1",("This is the alt text", open("red.png", "rb")))`) with no explanation. The multi-image example uses names such as "red" and doesn't say whether those are alt text. File size and format limits are not given, and the files are never closed.

27. 'You can send HTML. Only formatting elements are allowed.' doesn't say which elements.

28. Features in the list have no usage instructions: unfollow, block, unblock, showing followers, viewing hashtags, quote posts, audio/video specifics ('in the same way'), and bridging to Bluesky (only a `DID` field appears in `.env.example`). Only Follow, Move, and a few posting options are documented.

29. The migration instructions are vague and inconsistent. 'follow its procedure for migrating away' and 'Once your new acount is set up, go to your new account...' are unspecific (and contain a typo). The Move example uses `"user": "@new@example.com"` while `NEW_NAME` requires a full account URL. It doesn't say whether `/action/update` is needed afterward.

30. The Update Account section says changes to the profile need an update call, but Set Up never mentions it, so someone who edits `.env` after the first follow won't know to run it.

31. The README_nginx instructions are fragmentary: 'requires php8.5-fpm which is a thing that passes requests to PHP'. `apt-get install php php-curl` may install Apache and a different PHP version. There is no TLS or certbot guidance (the config has only `listen 80;`), and no site enabling, `nginx -t`, reload, or file ownership steps.

32. The nginx config includes uncertain advice: 'I don't THINK these are needed but computers are oh so very confusing'. It uses `include fastcgi.conf`, while README_docker uses `include fastcgi_params`. The reader can't tell which approach is correct.

33. The nginx test step is under-specified: 'to test the config, make a file `test.php`'. It doesn't say what output counts as success (`$_GET["path"]` will be undefined when the file is served directly), and doesn't say to delete the file afterward.

34. README_docker.md is not a complete configuration. The Compose snippet has no `services:` header and has an empty `environment:` with only a commented line. It also uses placeholder paths, and doesn't state which files go in the mounted folder or that the second block must be saved as `activity-bot.conf`.

35. README_docker.md has copy-paste inconsistencies: `Host(`your.host.com`)` versus `server_name you.host.com;`, and the label comment 'Internal port for postiz', which belongs to a different project.

36. The Docker instructions assume Traefik for reachability. There is no `ports:` mapping, TLS setup, or alternative for non-Traefik users, so the reader has no way to expose the bot over HTTPS. Nothing is said about file ownership and write permissions for the container user, or where `data/` ends up on the host.

37. Minor formatting issues that cause confusion. The Set Up list starts at `0.` and then repeats `1.`, with inconsistent sub-bullet indentation. There is a misplaced code span in 'an `.htaccess file`'. The nginx config block is labeled `bash`.
=== CRITIQUE U1670 END ===
