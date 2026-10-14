## Simulated users

### 1. Priya, blogger on cPanel shared hosting (Mac, FTP client, no command line)

"Great, I have a shared host and the README says it runs on shared hosts. Quickstart: create a subdomain, fine, cPanel does that. 'Upload `index.php`, `.htaccess`, `.env.example`', then 'Rename `.env.example` to `.env`'. Hmm, the full Set Up section says rename first and upload `.env`. Which is it? Does it matter?

Where do I even get these files? I'll download the repo zip. On my Mac, `.htaccess` and `.env.example` have vanished because dotfiles are hidden. I find them with Cmd+Shift+. and upload. Renaming to `.env` in Finder gives me a scary 'names that begin with a dot are reserved' warning. Nothing warned me.

I open `.env`. 'Generate locally by opening `tools/rsa_key_generator.html` on your computer.' OK, that's in the zip. A page opens and gives me two big blocks. The comment says 'Newlines must be replaced with "\n"'. Do I do that by hand? The generator output has real line breaks. Do I paste it between the quotes after removing every line break? What if I miss one? I do it and hope.

Password: 'Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`' or 'run `php tools/generate_password.php`'. I have no PHP on my Mac and no idea where to run this. My host has a PHP version selector but no terminal. Stuck for twenty minutes. I eventually find an online PHP sandbox, which feels wrong for a password. I paste a hash starting with `$2y$10$...` inside double quotes. Is the `$` a problem? No idea.

PHP version: 'PHP 8.5'. My cPanel selector tops out at 8.3. 'We live in the future now.' Not helpful. Is 8.3 okay? The doc doesn't say. I try anyway.

I leave the 'optional' fields alone. Did I just publish a bio that says 'Get the source code' and profile fields mentioning someone's Mastodon handle? Probably.

I visit `https://test.example.com/.well-known/webfinger` and get an error or blank page. Am I supposed to add something to the URL? The README says it 'shows a JSON file with your user's details'. I don't know whether the failure is `.htaccess` not working, PHP being too old, or the missing query string. There's no troubleshooting section. I give up for the day."

### 2. Marcus, Python developer with an Ubuntu VPS running nginx

"I'll skip Quickstart and go to README_nginx.md. 'Requires `php8.5-fpm`.' The commands are `sudo apt-get install php php-curl` then `php8.5-fpm`. Ubuntu's repos don't have 8.5 by default, so I need a third-party PPA. The doc doesn't mention it. Also the `php` metapackage pulls in Apache on Ubuntu, which grabs port 80 and fights nginx. Nice. I stop Apache and remove it.

The nginx config has `listen 80` only. The main README says HTTPS is a requirement. There are no certbot steps, and no mention of `sites-available`, `nginx -t` or a reload. I know this, but not everyone does. The code block is labelled `bash`, though it's nginx config. I find 'I don't THINK these are needed but computers are oh so very confusing.' above commented-out directives. Comforting. Do I need `fastcgi_split_path_info` or not?

Where do I put the files? `root /var/www/test.example.com/;` implies copying `index.php`, `.env`, and presumably not `.htaccess`. Nobody says whether `.htaccess` is irrelevant on nginx. Also nobody says the web user must be able to write to the root to create `data/`. That's only hinted at in the Caddy doc.

I make `test.php` as instructed and visit it. It prints 'Path is...' plus an 'Undefined array key' warning, since a real file never goes through the `@rewrite` path. So this test doesn't test the rewrite. I now have no idea whether the rewrite works, and I should delete `test.php` afterwards, which isn't said.

Keys: I'll just use `openssl` instead of the HTML tool. Which key format does the app expect? The example shows `BEGIN RSA PRIVATE KEY` for the private and `BEGIN PUBLIC KEY` for the public. Modern openssl emits `BEGIN PRIVATE KEY` by default. I generate it the old way with `-traditional` to be safe. The docs don't say whether either works.

I send a test post using the Python snippet. The README says to install `requests`. OK. Nothing in the README says what a successful response looks like. I print `r.text` myself. Debugging needs `requests_toolbelt`, which isn't listed under Requirements."

### 3. Tomasz, homelab user with a Raspberry Pi, Docker, Traefik, and a router at home

"'It will run on... a Raspberry Pi.' Perfect. I read README_docker.md. 'Rough Docker Instructions.' Right.

The compose snippet starts at `activity-bot:` with no `services:` parent, so I need to place it myself. `environment:` has only a commented-out line under it, so the key is empty. Will compose reject that? Mine complains on my version, so I delete the key. The Traefik label says 'Internal port for postiz'. That's a copy-paste from another project. The domain is `your.host.com`, the nginx config uses `you.host.com`, and the main README uses `test.example.com`. Three placeholders for one thing. 'The Traefik stuff is optional, especially if you're not using Traefik.' Without Traefik, how do I publish port 8080 and get HTTPS? Not covered.

The compose volumes mount `/path/to/your/docker/stuff/activity-bot/` and `activity-bot.conf`. Nobody says that the second code block should be saved as `activity-bot.conf`, or that `index.php`, `.env` and `.htaccess` go into the first directory. I guess. This image already ships a default nginx site on 8080. Will mine conflict? The config is described as 'a mixture' of two sources. It says 'Rough' at the top. I don't trust it.

Permissions: in the container PHP runs as an image user. Will it be able to create `data/` on a bind mount owned by my host user? The Docker README doesn't mention it. The Caddy README says 'adjust the permissions'. The Docker one doesn't.

Then the bigger problem. My Pi is behind my home router with a dynamic IP. For Mastodon to reach `/.well-known/webfinger`, I need DNS, port forwarding, and a TLS cert. README says it 'will run on a Raspberry Pi' but says nothing on making it reachable from the Internet. I know how, but the 'Quickstart' reader wouldn't.

I get it up. Step 7, 'Check your `data/logs/` directory'. Where's that? Inside the container, in the mounted folder under `public/`? I find it eventually. What does a good log look like? No example."

### 4. Jun, experienced sysadmin using Caddy on Debian

"I read README_caddy.md carefully, because I care about what is exposed. 'Requires `php8.5-fpm`' and the same `apt-get install php php-curl`, same repository problem as above. Debian stable doesn't have PHP 8.5 without Sury. Not stated.

The Caddyfile blocks `/.env` and `/php_errors.log`. Where does `php_errors.log` come from? It appears nowhere else in the docs. The nginx and Docker configs deny `^/(.env|data)`. The Caddy one doesn't block `/data`. So logs, which include incoming activity, are publicly readable on Caddy, and maybe the post data too. Is that intentional? I add `path /data/*` myself, but a less careful reader will leave it open. The main README never says that `data/` and `.env` must not be served, never says what `.htaccess` does for Apache, and never tells me to check that `https://test.example.com/.env` returns 403. That file holds the private signing key. With Apache and a host that has `AllowOverride None`, `.htaccess` silently does nothing and the key is public.

The Caddy `handle /post { route { uri query path post ...` block and `{uri}` placeholders are cryptic and I have to check the Caddy docs to see what they do. The root and `php_fastcgi` lines are declared after the handles. I assume order doesn't matter due to directive ordering but I would not call this obvious. Also the test step: `test.php` goes in the root, and visiting it gives an undefined-index warning. It tests PHP, not routing.

Step 'Visit `https://test.example.com/.well-known/webfinger`'. With no `resource=acct:` query I get an error, or a 400. The README says to 'check that it shows a JSON file with your user's details', which probably only happens with a `?resource=acct:example@test.example.com` parameter. I add it and it works."

### 5. Aisha, small-business owner with a domain and a Squarespace or GitHub Pages site (no PHP hosting)

"I've got `mybrand.com` on Squarespace. The intro says 'Your account lives on your website's subdomain. If you have a website called `example.com`, you can create a subdomain.' OK so I create `bot.mybrand.com`. But where does that run? The README says to 'Upload `index.php`' to my subdomain. Squarespace can't run PHP. Nowhere does it say that you need a host which executes PHP, or point to a few options. 'Create a subdomain' sounds like a DNS record to me, which gives me a domain that points nowhere. The FAQ says 'you should create free subdomains'. How?

'Minimum requirements: PHP 8.5, cURL, OpenSSL, HTTPS certificate.' I don't know how to check any of them. 'This should include the following extensions by default': what does that mean, 'should'? The cURL link goes to a PHP release-notes page about persistent curl share handles. Not an install guide. 'There is no need for Composer, Docker, Node, MongoDB, Wayland, GLaDOS, React, LLM, Adobe Creative Cloud, or Maven.' That makes me laugh, and doesn't help me know what I do need.

I buy cheap shared hosting. The rest of my day goes like Priya's. In the end I want to post something. The only way to post is Python, with a library I don't have. 'All the examples here use Python 3 - but you can use whichever language you want.' I'm not a coder. No curl example, no web form, and no list of parameters. I see 'Post a message' with `"password": "your-password-here"`. Is that the hash I put in `.env`, or the plain password that I hashed? It's the plain one, I guess. But the README says 'The password is encrypted when you send it and never stored on your server.' Encrypted how? And the `.env` stores a hash. So 'never stored' seems false, or at least confusing.

Then in step 8 I add an avatar. 'Edit `.env` to include the image locations.' Upload to where? `.env.example` says 'a relative URl without leading slash. For example "icon.jpg"'. So the same folder as `index.php`? And nothing says I must then call `action/update` (described much later under 'Update Account') for followers to see it."

---

## PROBLEMS

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
