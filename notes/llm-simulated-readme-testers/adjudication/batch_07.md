=== CRITIQUE U2940 START ===
## Simulation 1: Maya, hobbyist, cPanel shared hosting, no command-line experience

"I own example.com on a shared host and want a little bot that posts colour swatches. Quickstart: create a subdomain, upload three files, rename one. Easy."

"Subdomain... in cPanel I can add one, but it asks for a 'document root' and the README never says what to put there. I'll accept the default. Now, 'upload index.php, .htaccess, .env.example'. Where do I get those? There's no download link or 'Clone/Download ZIP' instruction. I find the repository page and download a ZIP."

"I upload via the file manager. I can't see .htaccess or .env.example because dotfiles are hidden. Eventually I find a 'show hidden files' setting. The Quickstart says rename .env.example to .env on the server, but the 'Set Up' section says rename it first and then upload .env. Which one? I do the Set Up version, so now I have two sets of instructions."

"Now 'follow the instructions inside it'. The file says the keys come from `tools/rsa_key_generator.html`. I never uploaded `tools/`, and the Set Up section doesn't mention it. I open it from the ZIP on my laptop. It gives me a private key and a public key. The file says 'Newlines must be replaced with \n'. Replace how? In my text editor? Do I paste them on one line? I do it by hand, one line each, and hope."

"Then PASSWORD: 'Generate with password_hash("Y0ur_p4s5w0rd", PASSWORD_DEFAULT);' I don't have PHP on my laptop. 'You can also run on the command line php tools/generate_password.php'. Same problem. I give up and look for an online bcrypt tool, which I'm not sure is acceptable or secure, and I don't know whether the result must be bcrypt. The hash is full of `$` signs and I don't know whether to keep the quotes."

"I never touch REALNAME and SUMMARY. I later learn my bot's bio says 'Get the source code!' and links to someone else's repository, because the example values are the defaults. There's also an example mention of another person's account in my profile fields."

"I visit /.well-known/webfinger. I get a 500 error or a blank page. Is it my PHP version? I look at Minimum Requirements: 'PHP 8.5 (We live in the future now.)' My host only offers 8.3. That is the end of the road for me and nothing tells me what to do. Is there a way to check my version? Does the README say what happens on older PHP? No. There's also nothing on where PHP errors go."

## Simulation 2: Dan, Linux hobbyist, Raspberry Pi at home, nginx

"The README says it runs on 'a Raspberry Pi', so I'm using one at home. But there are no Pi-specific steps. Step 0 says 'Create a new subdomain on your web host and make sure it has an HTTPS certificate.' I don't have a web host. I have a Pi behind a home router. I need DNS, a dynamic DNS record, port forwarding and a certificate. None of it is covered, so I sort it out myself."

"Other Servers: nginx. 'Requires php8.5-fpm'. I run `sudo apt-get install php php-curl`. On my Raspberry Pi OS this installs a different PHP (8.2) and pulls in Apache, which grabs port 80. Then `apt-get install php8.5-fpm` says package not found because 8.5 isn't in my distro's repositories. The docs don't mention adding a third-party repository. Even if I add one, `php-curl` was installed for the default PHP, not 8.5, so the cURL extension would be missing for the FPM version that actually runs the bot."

"The config is in a code block labelled `bash`. Where do I put it? sites-available? conf.d? Do I symlink it? Do I reload nginx? Not stated. It also says `listen 80;` only, with no TLS block. But the README says HTTPS is required. I add certbot myself. I also have to create /var/www/test.example.com and give www-data write access, because the bot makes a `data/` folder on first run. The nginx page doesn't say that. The Caddy page does mention permissions, but the nginx one doesn't."

"'To test the config, make a file test.php' that echoes `$_GET["path"]`. I open /test.php. The file exists, so nginx serves it directly and never goes through the @rewrite rule. `path` is undefined and I get a PHP warning. It tells me PHP works but doesn't test the rewrite. It also doesn't say to delete test.php afterwards."

"Webfinger: I visit /.well-known/webfinger without a `resource=` parameter. I'm told to 'check that it shows a JSON file with your user's details', but I don't know what a pass or fail looks like. Then I search for my bot from Mastodon and follow it. 'Check your data/logs/ directory'. Which file should be there, and what does a correct entry look like? Nothing says."

## Simulation 3: Priya, DevOps engineer, Docker and Traefik homelab

"I'll use README_docker.md. It starts with 'Rough Docker Instructions.' and 'Documenting what I had to do'. Reassuring, not."

"The compose snippet is a fragment: no `services:` key, no network, no example of the top of the file. `environment:` has only a commented-out line, so it's an empty key, which compose may reject. The comment uses `//`, which isn't valid comment syntax in YAML or in a shell. The Traefik label says 'Internal port for postiz', clearly copied from another project. I adapt it, but the placeholders vary across the document: `your.host.com`, `you.host.com`, and elsewhere `test.example.com`."

"The volume mounts `/path/to/your/docker/stuff/activity-bot/` to `/var/www/html/public`. The doc never says which files go in that folder (index.php, .env, .htaccess?), whether `.htaccess` is even used with nginx, or that `data/` will be created inside it. The container runs as an unprivileged user, so my bind mount needs the right ownership. Nothing says so. The nginx file is mounted into `/etc/nginx/conf.d/`, but the image already ships a default server on 8080. Will mine conflict? It says it is 'a mixture of the nginx config from README_nginx.md and the documentation from ServerSideUp', but doesn't say how to confirm that it replaces the default, and doesn't link to the ServerSideUp page it borrowed from."

"There's no command to start anything (`docker compose up -d`?), no way to confirm it works, and no mention of where the main README's Set Up steps fit in. I assume I follow the main README for .env and keys. The .env.example tells me to 'rename this file to .env and upload it', which isn't a Docker action. The `$` characters in the bcrypt hash worry me: do I need to escape them for compose or for the env parser? Not covered. And if I'm not using Traefik, who terminates HTTPS? The doc says the Traefik part 'is optional' but never says what to use instead."

## Simulation 4: Tom, VPS user, Debian, Caddy

"Caddy is my default, so README_caddy.md. 'Requires php8.5-fpm'. The same apt block as nginx: `php php-curl`, then `php8.5-fpm`. Debian 12 doesn't have 8.5. It also drags in Apache via the `php` metapackage, which conflicts with Caddy on ports 80 and 443. Nothing tells me about that or about adding a repository."

"The Caddyfile: `root * /var/www/test.example.com` and a socket path hard-coded to `php8.5-fpm.sock`. I have to replace both. The `@blocked` matcher blocks `/.env` and `/php_errors.log`, but the nginx config also blocks `data`, and the Caddy one doesn't. I notice that, so my logs (and the folder where it keeps other state) might be browsable at /data/logs/. Nothing in the doc says that's a risk. I add a `/data*` block myself. Where is `php_errors.log` coming from? It is not mentioned in the main README."

"I'm fairly comfortable with Caddy but even I can't tell why the `handle /post` block uses `uri query path post`, and the config has no comments explaining what each block is for, unlike the nginx one. Anyway I reload Caddy. Same `test.php` test, with the same weakness: it proves PHP works, not the routing, and prints an 'undefined array key' warning."

"The Caddy page says I 'may have to adjust the permissions' because Caddy and PHP run as different users. That is as specific as it gets. Which user does PHP-FPM run as? Which directory needs writing? I do `chown` on the webroot to www-data and move on. Webfinger works, Mastodon finds my bot, and I follow it. `data/logs/` has files, but I can't tell which entry means 'follow accepted'."

## Simulation 5: Sam, Python developer, Windows laptop, FTP to managed Apache hosting

"I mostly want to use the API. My host has PHP 8.5 and Apache, so server setup should be fine. First problem: I'm on Windows. Windows Explorer won't let me rename `.env.example` to `.env`. I use my FTP client. Then I notice the Quickstart says upload .env.example and rename it on the server, so the file with the private key sits on my server under a guessable name until I rename it."

"Password: no PHP on my machine, same as Maya. I find a bcrypt generator and paste the hash. In the Windows terminal, the `php tools/generate_password.php 'Y0ur_p4s5w0rd'` example with single quotes wouldn't work in cmd.exe anyway."

"Setup works. Now the API. 'The password is encrypted when you send it and never stored on your server.' But my Python code sends `"password": "your-password-here"` as a plain form field over HTTPS. So is it hashed, encrypted or neither? And is that the plain-text password I hashed, or the hash itself? The README never says, so I try the plain-text one. It works."

"Requirements: 'Python Requests library'. The `Debugging` section imports `requests_toolbelt`, which isn't mentioned in Requirements, so I get ImportError and have to pip install it. For a post with an image I use the example. `files = [("1",("This is the alt text", open("red.png", "rb")))]`. That tuple looks like a filename slot, not alt text, so I'm unsure whether this is right. The second example uses `("red", ...)` for four images and doesn't say whether 'red' is a filename or alt text."

"Location example: `"longitude": 40.77563, "latitude": -73.97474`. Those are swapped (40.77 N, -73.97 W is New York) and the post puts the pin in the wrong place. Then I try to delete the post. 'You will need the ID of your post.' Where do I find it? The example GUID is made up. I find it in the HTML of the website view. Also, 'See `$allowed_elements` to see which ones are supported': in which file? I search `index.php`. I want to change the avatar. Step 8 says 'Edit .env to include the image locations.' The .env says 'Should be a relative URl without leading slash'. Relative to what? I upload it, edit .env, and the profile on Mastodon doesn't change until I find the 'Update Account' section a long way further down, which isn't mentioned in the Set Up steps."
=== CRITIQUE U2940 END ===

=== CRITIQUE U1205 START ===
PROBLEMS
1. The README opens with a very long feature list and a "doesn't do" list, and the actual setup steps only appear much later, so a beginner has to scroll a long way to find where to start.
2. The .env comments tell you to open `tools/rsa_keys.html`, but the file in the repository is called `rsa_key_generator.html`, so the name doesn't match.
3. Telling the reader to "rename .env.example to .env" gives no help on how or where to do it, for example on Windows where the extension and dotfiles are hidden or where you do it on the computer versus on the server.
4. There's no guidance for a non-developer on how to run `password_hash(...)` or `php tools/generate_password.php`, such as where to type it, whether PHP must be installed, or what to do if it isn't.
5. The Minimum Requirements list ends with a joke line (Docker, GLaDOS and so on), and requiring PHP 8.5 gives no way to check what the host runs, which could confuse a newcomer.
6. In the .env example, some values are in double quotes (USERNAME, PAGE_SIZE) and others are bare (MAX_LOGS), and nothing says whether you should keep quotes around your own values.
7. The numbered Set Up steps are short and in a sensible order, and the webfinger check, with a description of what you should see, is a helpful way to know it worked.
8. "Check your `/data/logs/` directory" is ambiguous: it could mean the server's top-level root or a folder inside the website's own directory.
9. The "How this works" section is confusing and not useful for someone just setting up; it describes rewrite rules and file locations rather than anything to do.
10. The API examples all use `"password": "your-password-here"`, and it's unclear whether that should be the plain password or the generated hash.
=== CRITIQUE U1205 END ===

=== CRITIQUE U8550 START ===
1. The Quickstart and Set Up disagree on the order of rename and upload. Quickstart says "Upload `index.php`, `.htaccess`, `.env.example` to your subdomain" and then "Rename `.env.example` to `.env`", while Set Up says "Rename `.env.example` to `.env`" first and then upload `.env`. A reader cannot tell if the two orders are equivalent.

2. The Quickstart omits required prerequisites. It says only "Edit `.env` and follow the instructions inside it", but the inside instructions need local key generation and a password hash, which means a download of `tools/` files and possibly a local PHP install. It also never says that `tools/` is not to be uploaded.

3. Nowhere does the documentation say where to get the files or how to deal with dotfiles. `.htaccess` and `.env` are hidden by default in Finder, Windows Explorer, and many FTP clients, and renaming to a name that starts with a dot is blocked or warned about on some systems. No hint is given.

4. The hosting requirement is unclear to people who lack a PHP host. The intro says "Your account lives on *your* website's subdomain" and "Create a subdomain", but doesn't say that the subdomain must be served by something that executes PHP, nor how to get a "free subdomain" (the FAQ's wording). It also doesn't explain that creating a DNS record alone is insufficient.

5. "PHP 8.5 (We live in the future now.)" is a very strict requirement. The intro says it "will run on shared hosts... or any modern web server", yet many shared hosts only offer older PHP versions, and the doc doesn't say whether 8.3/8.4 work, or how to check the host's version. The joke replaces the explanation.

6. The extension requirement is vague. "This should include the following extensions by default" does not say how to verify they are present or enabled, and the cURL link points to a PHP 8.5 release-notes section ("persistent-curl-share-handles"), not to install or enable instructions.

7. The `.htaccess` dependency is not stated. The default set up "assumes Apache or similar", but the requirements don't list mod_rewrite or `AllowOverride`, and they don't warn that on hosts where `.htaccess` is ignored, routing will break and `.env` could be exposed.

8. There is no step to confirm that secrets are not publicly served. Neither README says to request `https://test.example.com/.env` or `/data/` and confirm a 403/404, even though `.env` contains `KEY_PRIVATE` and `data/` contains logs.

9. The Caddy config protects less than the nginx and Docker configs. The Caddy `@blocked` matcher lists only `path /.env` and `path /php_errors.log`, whereas the nginx and Docker configs deny `^/(.env|data)`. `/data` is left exposed under Caddy, and `php_errors.log` is mentioned nowhere else.

10. Key generation instructions are thin. "Generate locally by opening `tools/rsa_key_generator.html` on your computer" doesn't say how to get the file, what the output looks like, or whether it is safe and offline. "Newlines must be replaced with "\n"" does not say whether the generator already does it, how to do it by hand, or what happens if a line break remains.

11. The accepted key format is not stated for people who generate keys another way. The example shows `-----BEGIN RSA PRIVATE KEY-----` for the private key and `-----BEGIN PUBLIC KEY-----` for the public key, but does not say whether a PKCS#8 `BEGIN PRIVATE KEY` or other key sizes are accepted.

12. The password step presumes a local PHP CLI. "Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`" and "run on the command line `php tools/generate_password.php 'Y0ur_p4s5w0rd'`" assume PHP is installed locally, which contradicts a shared-host user's likely setup. No alternative (for example using the hosting's PHP, or a web tool) is given.

13. Password handling is ambiguous. The hash goes in `.env` inside double quotes, and a bcrypt hash contains `$` characters, with no advice about quoting or escaping. It's also not stated that the API's `"password": "your-password-here"` is the plain-text password, not the hash.

14. The security claim about the API password is confusing. "The password is encrypted when you send it and never stored on your server" conflicts with the stored hash in `.env`, and "encrypted" presumably only means HTTPS transport. The statement should say what actually happens.

15. The `.env.example` comment syntax is unexplained and inconsistent. Every comment uses `#;`, but the BIRTHDAY description starts with a bare `#` ("`#	This is the joined date of your bot.`"). Users do not know whether `#;` is required or how the file is parsed (and quoting differs, for example `PAGE_SIZE="1000"` versus `MAX_LOGS=2048`).

16. Default optional values go live if left unchanged. The "Optional Fields" in `.env.example` contain sample values (a display name, a bio with a link, four sample profile fields including a mention of another account and a placeholder hashtag URL), but the docs never say to replace or blank them, or what happens if the profile fields are blank.

17. "If you prefer, you can edit `index.php` and place the details in there." gives no location in `index.php`, no variable names, and no statement of which source wins when both exist.

18. The webfinger check is probably incomplete. "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details" has no `?resource=acct:username@test.example.com` query, and webfinger endpoints usually require one. A reader may see an error and believe setup failed.

19. Step 7 relies on an unexplained directory and gives no expected result. "Check your `data/logs/` directory to see if the follow request was received correctly" does not say that the directory is created on first run, where it sits relative to the web root, what a correct log entry looks like, whether the follow is auto-accepted, or what to do if it is empty.

20. There is no troubleshooting section. The setup has several silent failure points (rewrites, permissions, PHP version, HTTPS, Mastodon search caching, a server not publicly reachable), and the docs give no way to diagnose them.

21. File permissions and ownership are only mentioned in the Caddy file ("You may have to adjust the permissions..."). The main README, nginx and Docker files don't say that the web user must be able to create `data/` and write logs, which is especially important for Docker bind mounts.

22. The Set Up ends at a follow request, and the first real post requires the Python API section. There's no "send your first post" step within Set Up, no non-Python (curl or similar) example despite "you can use whichever language", and no reference for endpoints, parameters or responses. Examples assign `r` but never show how to confirm success.

23. Python prerequisites are underspecified. The "Requirements" say only "a modern version of Python" and the `requests` library, and the debugging snippet needs `requests_toolbelt`, which isn't listed.

24. Step 8, "Optionally, upload an avatar and banner image... Edit `.env` to include the image locations", doesn't say where to upload the images (the web root?) or that `action/update` must be called afterwards for followers to see the change; the latter is only described much later under "Update Account".

25. The location example has latitude and longitude swapped. `"longitude": 40.77563, "latitude": -73.97474` has values that match New York's latitude and longitude the other way round, and the example is for "John Lennon Memorial", so a copying user would put the post in the wrong place.

26. The media examples hide the alt-text mechanism. `files = [("1",("This is the alt text", open("red.png", "rb")))]` uses the file-name slot for alt text, with keys "1" to "4" unexplained. "You can also post audio and video in the same way" gives no field name, format or size limits, and the avatar/banner limits are only in `.env.example`.

27. Delete and edit examples need a `guid` but the README never says where to get it. "You will need the ID of your post" has no pointer to the website page, the send response, or logs.

28. "You can send HTML. See `$allowed_elements` to see which ones are supported." names a variable without naming the file, and the reader must search `index.php` for it.

29. The migration section is unclear. `.env.example` says `OLD_NAME`/`NEW_NAME` take a full account URL ("https://example.social/users/username"), but the Move example uses `"user": "@new@example.com"`, a handle. "Once your new acount is set up" is also confusing in the "move away" paragraph, since the "new account" is not the ActivityBot one.

30. The nginx README includes a hedge in place of guidance: "I don't THINK these are needed but computers are oh so very confusing." followed by commented directives. The reader cannot tell if the `fastcgi_params` variants are necessary. The block is labelled `bash`, not nginx, and the config listens only on port 80 with no TLS despite "HTTPS certificate" being a requirement.

31. The nginx and Caddy READMEs are missing the surrounding steps: where to put `index.php` and `.env`, whether `.htaccess` is needed, how to enable the site and reload, how to install the web server and get a certificate, and how to name the files. They also share the install snippet `sudo apt-get install php php-curl` followed by `php8.5-fpm`, which assumes a repository carrying 8.5 and installs the default `php` metapackage, which can pull in Apache on Debian/Ubuntu.

32. The `test.php` check in the nginx and Caddy READMEs does not test the rewrite it claims to. Because `test.php` exists as a real file, it never goes via `index.php?path=`, so `echo $_GET["path"];` throws an undefined-key warning. The files also never say to delete `test.php` afterwards.

33. The Docker README is a rough fragment. The compose snippet has no `services:` parent, `environment:` has only a commented line (an empty key), the Traefik label comment says "Internal port for postiz" (copied from another project), and it is not stated that the second code block must be saved as `activity-bot.conf` or how it interacts with the image's default site on 8080.

34. Placeholder hostnames vary across the files: `test.example.com`, `your.host.com`, and `you.host.com`. The Docker README also says "the Traefik stuff is optional, especially if you're not using Traefik" but gives no non-Traefik route for publishing port 8080 and obtaining HTTPS.

35. Home or self-hosted setups lack guidance. The intro says it runs on "a Raspberry Pi", but there is nothing on DNS, port forwarding, dynamic IPs, a certificate, or on the server being publicly reachable for other servers to fetch webfinger and deliver follows.

36. The FAQ and the docs do not tie the 2,048-log limit to its setting. "You can adjust this if you want to keep more or fewer" does not name `MAX_LOGS`, and the README says only "Expect lots of logs" with a 100MB disk requirement without relating the two.

37. Small typos and inconsistencies reduce trust: "Lenny" in the intro (probably Lemmy), "URl" in several places, "acount", and the Set Up list uses a "0." start with repeated "1." numbering in the source.
=== CRITIQUE U8550 END ===

=== CRITIQUE U4300 START ===
1. The README never says where to get the project files (no download or clone instruction), so the Set Up section starts with files the reader doesn't have yet.
2. The PHP requirement "PHP 8.5 (We live in the future now.)" gives no hint whether older versions work, how to check the host's version, or what fails on 8.3. Shared-host users have no way to know whether to continue.
3. The requirements never state which web server is needed. The README implies Apache with `.htaccess` (mod_rewrite, `AllowOverride`) only by calling README_nginx.md "Using Nginx instead of Apache". No required PHP extensions beyond OpenSSL are listed, even though README_nginx.md installs `php-curl`.
4. The line "Docker, Node, MongoDB, Wayland, GLaDOS, React, LLM, Adobe Creative Cloud, Maven (absolutely none of these!)" sits in the requirements list but is a joke, and it contradicts the later Docker FAQ answer. A literal reader may think Docker is forbidden or that the list is incomplete.
5. Set Up step 1, "Edit the `index.php` file to add a username, password, and keypair.", doesn't say where in the file, what format the values take, or how to create a keypair or password hash. The generator tools are mentioned only in `.env.example`.
6. `.env.example` says "Generate locally by opening `tools/rsa_keys.html`", but the file in the repository is `tools/rsa_key_generator.html`.
7. There are two competing configuration routes, editing `index.php` or renaming `.env.example` to `.env`. The README never says which is preferred, whether they can be mixed, or which takes precedence. Meanwhile `.env.example` says "Then rename this file to .env and upload it along with index.php and .htaccess".
8. The requirement that private and public keys have newlines replaced with "\n" ("Newlines must be replaced with "\n"") doesn't say whether the key generator already outputs that form, and doesn't say whether the same rule applies when pasting into `index.php`.
9. The README does not make clear that the `PASSWORD` setting holds a hash, while the API examples' `"password": "your-password-here"` must be the plaintext. Quoting rules for a hash containing `$` characters in `.env` are not described either.
10. Dotfiles (`.env`, `.htaccess`) are hidden in Finder, Explorer, FTP clients and cPanel's File Manager. Nothing warns about this or explains renaming `.env.example` on Windows, so users may upload without the files or not see them to check.
11. "Upload `index.php` and `.htaccess` to the *root* directory of your domain." doesn't explain what "root" means on shared hosting, for example the sub-domain's document root versus `public_html`.
12. Set Up step 4, "Optionally, upload an avatar and banner image", doesn't tell the user to set `AVATAR`, `BANNER` and `FAVICON`, or to use the relative-path format that `.env.example` requires ("Should be a relative URl without leading slash.").
13. The webfinger check, "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details", gives no `?resource=acct:...` query and no example of the expected output. A bare visit may return an error that a newcomer will read as failure.
14. The Set Up list uses "0." and then repeats "1." for every later step, so numbering is wrong and can render inconsistently. Step 0 also sits outside the main sequence.
15. Directory locations are described inconsistently and without writability instructions. "Check your `/data/logs/` directory", "`/posts` directory", "`/data/followers`" and "`/quotes` directory" have leading slashes that look like filesystem or server roots, mix `data/` and top-level folders, and never say they are created automatically or need write permission by the web server user.
16. The README says the bot can't "Receive messages (other than follows, unfollows, and quote requests)" and the FAQ explains why it doesn't store replies, but "How this works" says "Messages sent to your inbox are saved as .json in the `/data/inbox` directory." These statements conflict or at least confuse.
17. Set Up ends with following the bot and reading logs. It has no troubleshooting guidance (what a healthy log looks like, what to do if nothing appears, how to view logs without shell access) and no explicit first-post step before the API section.
18. The API section's "Requirements" ("a modern version of Python and have installed the popular Python Requests library") gives no install command. The Debugging section later needs `requests_toolbelt`, which is not listed as a requirement.
19. None of the API examples show or describe the response (success status, body, error codes), and `r` is never inspected, so users can't tell whether a call worked.
20. The media example `files = [("1",("This is the alt text", open("red.png", "rb")))]` places alt text where a filename would normally go without explaining it. The multi-image example reuses that slot for values like "red", which look like filenames, not alt text.
21. The location example `"longitude": 40.77563, "latitude": -73.97474` has the values swapped (those numbers are a New York latitude and longitude). Copying it puts the post in the wrong place.
22. Delete and edit say "You will need the ID of your post" but never say where to find it (logs, `/posts` folder, a response field). Edit also reuses `/action/send` with a `guid`, which is not explained.
23. The feature list promises unfollow, block, unblock, show followers, view hashtags, and "Update profile information", but only follow, move and update have API examples. There are no action names or parameters for the rest. "You can send HTML. Only formatting elements are allowed." doesn't list which elements.
24. Account migration is confusing. `.env.example` asks for the "full account URl" (for example `https://new.example/users/username`), while the Move example sends `"user": "@new@example.com"`. The order of steps is unclear, "Once your new acount is set up" has a typo, and no checks are given that migration worked.
25. README_nginx.md says to run `sudo apt-get install php php-curl` and then `php8.5-fpm`, with no note that the `php` metapackage may install Apache and that PHP 8.5 is not in stock Debian or Ubuntu repositories. It lists `php-curl`, which the README never requires.
26. README_nginx.md provides only `listen 80;`, even though HTTPS is mandatory in the main README, and says nothing about TLS, where to save the config, enabling the site, testing with `nginx -t`, reloading nginx, or file ownership. It includes the hedge "I don't THINK these are needed but computers are oh so very confusing" over alternative fastcgi lines.
27. The nginx test file `test.php` has no stated expected output (a direct request will not have `$_GET["path"]` set), and there is no instruction to remove it afterward.
28. README_docker.md is a fragment. The compose snippet has no `services:` key, `environment:` contains only a commented-out line, and the comment "Internal port for postiz" is copied from another project. `Host(`your.host.com`)` and `server_name you.host.com;` differ and need matching.
29. README_docker.md doesn't say where `index.php`, `.htaccess` and `.env` go in the mounted directory, what to name and where to put the nginx file, how to start the stack, how to make `data/` writable by the container user, or how to get HTTPS without Traefik. It also doesn't mention the image's own default server on the same port.
30. Minor formatting and consistency slips add friction: "`.htaccess file`" has the backticks around the word "file", `.env.example` has one comment line missing the `;` marker ("#	This is the joined date of your bot."), and "URl" is used throughout for URL.
=== CRITIQUE U4300 END ===

=== CRITIQUE U1339 START ===
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
=== CRITIQUE U1339 END ===
