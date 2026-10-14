=== CRITIQUE U3984 START ===
## Simulation 1: Priya, hobbyist writer, cPanel shared host, no command-line experience

"Cute idea, a bot at `colours.mysite.com`. Quickstart says create a subdomain, upload three files, rename one. Easy. I make the subdomain in cPanel. It puts the folder at `public_html/bot`. Hang on, later it says 'root directory of your subdomain' and 'It will not work in a subdirectory.' Is `public_html/bot` the root? I think so, because that's what the subdomain points at, but I'm not sure.

Now Minimum Requirements. PHP 8.5? My host's PHP selector tops out at 8.3. I don't know if my host will ever offer 8.5. The README doesn't say what happens on 8.3, so I can't tell whether it's a hard requirement or a 'nice to have'. I'm also told the extensions 'should' be included by default. I have no idea how to check. I'll carry on and hope.

I download the repo zip. I can't see `.htaccess` or `.env.example` in my Finder because they start with a dot. The README never mentions that. I turn on hidden files after some googling. The Quickstart says to upload `.env.example` and rename it. The Set Up section says rename it first, then upload. The `.env.example` comments say rename and then upload. Which order? It doesn't matter much, but it makes me doubt myself.

Inside `.env`, I must 'Generate locally by opening `tools/rsa_key_generator.html` on your computer.' The README never mentioned a `tools` folder. I find it, double-click, and it makes two keys. Now 'Newlines must be replaced with "\n"'. Did the page already do that? Do I do it myself? What does a correct value look like? The example just has '...' in the middle. I paste what I got and hope.

Then the password: `password_hash(...)` or `php tools/generate_password.php`. I don't have PHP on my laptop. I'm stuck. I find an online bcrypt generator, but the README doesn't say that's acceptable or which algorithm to pick. The hash has `$` signs in it and I'm not sure if I should wrap it in the double quotes or not.

I upload and visit `.well-known/webfinger`. I get a blank page or a 500. Nothing in the README says what to do about that. It doesn't mention `.htaccess` needing mod_rewrite or AllowOverride. I give up and email my host."

## Simulation 2: Marcus, experienced sysadmin, Ubuntu 24.04 VPS, nginx

"I'll go with the nginx README. It says 'Requires `php8.5-fpm`' and then shows `sudo apt-get install php php-curl`. On Ubuntu, the `php` meta-package pulls in Apache. I don't want Apache on a box that's running nginx. Also, stock Ubuntu 24.04 has no `php8.5-fpm`. I need a third-party repo, and the doc doesn't say so. It also doesn't say this is Debian/Ubuntu-only, nor does it give `php8.5-curl`. I add the PPA myself and install only the fpm and curl packages.

The config: there's a `map` block at the top and a `server` block. `map` is only valid in the `http` context, so it must go in its own file in `conf.d` while the server block goes in sites-available. The README doesn't say where either goes, nor does it say to run `nginx -t` and reload. I know how, but a beginner wouldn't.

The server only has `listen 80;`. The main README says it must have HTTPS and the examples use `https://`. There's no TLS block and no mention of certbot. I run certbot myself.

The deny rule is `location ~ ^/(.env|data)`. The `.` is unescaped and there's no trailing anchor, so it also catches `/database` or `/dataset.html`. It's fine for me but sloppy. Also, `.htaccess` isn't blocked. I'll add that.

The 'test' step: make `test.php`, which echoes `$_GET["path"]`, and visit it. If I go directly to `/test.php` there's no `path` parameter, so I get a PHP warning about an undefined key, and the doc doesn't tell me what correct output looks like. It also doesn't test the rewrite rules at all, and it never tells me to delete the file.

After that, where do I go? Back to step 3 of Set Up? The README_nginx doesn't say.

I fix the permissions on the web root by hand, since www-data has to create `data/`. The main README never mentions this, and nginx's README doesn't either. Only the Caddy README hints at it."

## Simulation 3: Lena, Raspberry Pi at home, Caddy, some Linux experience

"The intro says it'll run on a Raspberry Pi. Exciting. But nothing in the README covers a Pi behind a home router: no port forwarding, no dynamic DNS, no 'you need a public domain pointing at your home IP'. Step 0 says 'Create a new subdomain on your web host.' I don't have a web host. I sort it out myself.

The Caddy README says `sudo apt-get install php php-curl` and `php8.5-fpm`. Raspberry Pi OS ships PHP 8.2 or so. Nothing about how to get 8.5. I eventually find a repo. I also have no instructions to install Caddy itself. I assume it's already there.

The Caddyfile has `path /.env` and `path /php_errors.log` blocked. But `data/`, which holds the logs, isn't blocked, unlike in the nginx config. Is that deliberate? Are the logs public? I add a block for `/data/*`. Also `.htaccess` is sitting on the server and the Caddyfile doesn't care. That's fine, but there's no statement of what the `.htaccess` does that I now have to replicate by hand.

'You may have to adjust the permissions of the directory ActivityBot is installed in...' Which user? Which directory? I figure out `www-data` and `chown`, but it's a guess.

The Caddy test is the same `test.php` trick. I get a warning about `path`. I don't know if that's success.

Then back in the main README: 'Check your `data/logs/` directory'. Where is that? Relative to the web root, I guess, created on first request. Nobody says that."

## Simulation 4: Tomasz, homelab Docker/Traefik user

"README_docker.md starts with 'Rough Docker Instructions.' Okay, lowered expectations. There's a compose service fragment, no `services:` wrapper and no full file, but fine. The volume `/path/to/your/docker/stuff/activity-bot/` is mounted at `/var/www/html/public`. The doc never says that's where I put `index.php` and `.env`. Then `/path/to/your/docker/stuff/activity-bot.conf` is mounted into nginx's conf.d. I infer this is the nginx config below, but it's never stated.

There's no `ports:` entry. If I'm not using Traefik, how do I reach port 8080? The Traefik label says `# Internal port for postiz`. That's a copy-paste from another project. Is 8080 right here? The nginx config does `listen 8080`, so yes. But it makes me doubt the rest.

Placeholders: `your.host.com` in the label and `you.host.com` in the nginx config. If I replace only one, the router will match but nginx's `server_name` won't (although nginx will still serve as the default server).

`environment:` is empty except for a commented-out line, and the comment uses `//`. It's fine in YAML as it's after a `#`, but a null `environment:` can trip up some compose versions. I delete the key.

The doc says 'a mixture of the nginx config from README_nginx.md' and ServerSideUp's docs. So it's not clear which differences are deliberate.

Permissions: ServerSideUp images run as a particular uid and need write access to the mounted folder to create `data/`. No mention. First request returns a 500 until I `chown`. Then the log folder appears.

TLS is only mentioned via Traefik. The main README says HTTPS is required, but this doc never says how HTTPS is expected to be done if you're not using Traefik.

I also notice the main README says 'There is no need for Composer, Docker, Node...' while there's a whole Docker README. Mildly funny, mildly confusing."

## Simulation 5: Aisha, data scientist on macOS with Python, Apache on a small VPS

"I'm comfortable with Python and a cloud VPS with Apache, so I take the default path. I don't have PHP locally, though, and I'm on a Mac. I need to generate a password hash. `php tools/generate_password.php` fails because I have no PHP CLI. The `.env.example` says 'You can also run on the command line...' and the other option is `password_hash(...)`, which also needs PHP. I install PHP via Homebrew just for this, which feels like overkill given 'There is no need for Composer...'.

On the server, Apache is fine, but PHP 8.5 isn't in the default repos. I eventually get it. I upload `index.php`, `.htaccess`, `.env`. The webfinger URL: I visit `https://test.example.com/.well-known/webfinger` with no `resource` parameter. I get some JSON, I think. I don't know whether it's the right JSON because the README doesn't show an example. Real WebFinger clients pass `?resource=acct:...`. I try that too.

I search for `@username@test.example.com` on Mastodon. Do I literally type 'username' or my USERNAME value? I assume mine. I follow the bot. Then I check `data/logs/`. There are many files. Nothing says what a correct follow looks like, nor whether the bot sends an Accept back automatically.

Now the API. Examples use Python `requests`. The post example doesn't print `r`, so I don't know if it worked. 'Check social media to see if the message appears.' It doesn't appear on my main account. Oh, I'm following the bot only after step 6, and the doc never says messages go to followers only. I did follow it. I wait. I finally print `r.status_code` and `r.text`. Does the bot's API want the plain password or the hash? The examples say `your-password-here`, and 'The password is encrypted when you send it and never stored' suggests something clever happens, but I assume plain text over HTTPS.

I try an image post. The tuple `("This is the alt text", open("red.png", "rb"))` puts the alt text in the filename slot. That's unusual. Field names '1', '2' are never explained.

I try to post a location with the example values: `"longitude": 40.77563, "latitude": -73.97474`. Those look swapped; 40.77 is New York's latitude. My pin lands in Antarctica.

I want to unfollow or block someone. The Features list says it can, but the API section only has Follow and Move. I read the source.

Finally, the debug snippet needs `requests_toolbelt`, which isn't in the Requirements section."
=== CRITIQUE U3984 END ===

=== CRITIQUE U9940 START ===
# Simulated first-time users of the ActivityBot README

Five people, each following the documentation from the top. Their reactions are narrated in their own voice.

---

## 1. Priya, florist, no coding background, cheap shared hosting with a cPanel File Manager

"I own `priyaflowers.example` and want a little bot posting a flower of the day. The README says it 'will run on shared hosts', so good.

Quickstart: create a subdomain, upload three files. Which files, from where? I can't find a Download button in what I was given, so I'm guessing I need the whole repository. I get a ZIP and upload `index.php`, `.htaccess` and `.env.example`. cPanel doesn't show `.htaccess` or `.env.example` until I tick 'show hidden files'. Nobody warned me about that.

Then I open Set Up and it says rename `.env.example` to `.env` first and upload `.env`. The Quickstart said upload `.env.example` and rename it. Which is it? I do the Quickstart version, and now I'm not sure I did it right.

Requirements: 'PHP 8.5 (We live in the future now.)' Funny, but my host's PHP selector tops out at 8.3. Is 8.4 okay? Does it say what breaks? No. I have no way to tell if I'm doomed. I find a version dropdown, pick the highest, and hope.

Now `.env`. It says generate keys by 'opening `tools/rsa_key_generator.html` on your computer'. The Quickstart never said to download the `tools` folder. I open it, get two big blocks of text, and the file says 'Newlines must be replaced with "\n"'. Do I do that by hand? Does the tool do it? I paste each key into one long line, swapping newlines for `\n` by hand, and it takes ages.

Then `PASSWORD`: 'Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`' Where do I type that? Or 'run on the command line `php tools/generate_password.php ...`'. I don't have PHP on my laptop and the requirements never said I'd need it. I give up and ask my nephew.

There's a lot of other stuff in `.env` too: 'A single file ActivityPub Bot Server' as the bot's name, a bio linking to the source, four profile fields mentioning someone called Edent on Mastodon. Do I delete those? If I leave them, will my florist bot advertise someone else's account? It doesn't say.

I upload the three files and visit `/.well-known/webfinger`. I get an error page. I'm told to 'check that it shows a JSON file' but not what it should look like, or what to do if it doesn't. No troubleshooting section at all."

---

## 2. Marcus, front-end JavaScript developer on Windows, rents an Ubuntu VPS with nginx

"I know my way round a terminal, but PHP isn't my thing. 'There is no need for Composer, Docker, Node...' Great, that's my kind of project. Hmm, 'Wayland, GLaDOS'? Cute.

The default is Apache, so I click the nginx link. `sudo apt-get install php php-curl`. On Ubuntu the `php` metapackage drags in Apache2, which grabs port 80 and fights with my nginx. Then `sudo apt-get install php8.5-fpm` says 'Unable to locate package'. There's no mention of a PPA or third-party repo, and the README main page says PHP 8.5 is just a requirement. Do I compile it?

I get 8.5 from a PPA after some searching. I paste the nginx config, which has `listen 80;` only. The main README says I need an HTTPS cert. Nothing here says how to add TLS (certbot, a 443 block), so I figure it out myself.

Where do the files go? `root /var/www/test.example.com/;` I have to guess that I `mkdir` it, upload `index.php` and `.env` there, and fix ownership for `www-data`. Nothing says to enable the site or reload nginx either. And do I still upload `.htaccess`? The nginx page doesn't say which of the main steps still apply, such as the `.env` setup and the key generation.

On Windows, `php tools/generate_password.php 'Y0ur_p4s5w0rd'` single quotes don't work in cmd.exe. The `$` characters in the resulting hash inside `PASSWORD="..."`: will the loader expand them? No hint whether single quotes are safer.

The test step: 'make a file `test.php`' that echoes `$_GET["path"]`. I visit `/test.php` and see 'Path is...' plus a PHP warning about an undefined key. Is that success? The page doesn't say what I should see. And I'm never told to delete `test.php` afterwards. Also, I now notice the nginx deny rule covers `.env` and `data`, but nothing tells me to try fetching `/.env` to confirm my private key isn't downloadable."

---

## 3. Dana, homelab hobbyist on a Raspberry Pi 5, Docker Compose plus Traefik

"The README says it runs on a Raspberry Pi. Good. I click the Docker readme. It's titled 'Rough Docker Instructions.' and opens with 'Documenting what I had to do'. So not really instructions.

The compose snippet starts at `activity-bot:` with no `services:` parent, no network, and no `ports:`. If I don't use Traefik there's no way to reach it. The text says 'the Traefik stuff is optional, especially if you're not using Traefik', which doesn't tell me what to use instead. The comment `# Internal port for postiz` is clearly copied from another project. The `environment:` key only contains a commented-out line.

Volumes: `/path/to/your/docker/stuff/activity-bot/` mounts onto `/var/www/html/public`. What should be in that folder? `index.php`, `.htaccess`, `.env`? Then the nginx config goes in `conf.d/activity-bot.conf`, but it's labeled 'Default server definition' and also `listen 8080`. The image already ships its own default server on 8080. Do I replace theirs or do they conflict? Not said.

Placeholders are all over the place: Traefik says `your.host.com`, nginx says `you.host.com`, everything else says `test.example.com`. I have to work out they are the same thing.

I bring it up. The app can't create `data/` because the mounted directory is owned by me, not by the container's PHP user. The Caddy page warns about this ('You may have to adjust the permissions'), but the Docker page doesn't. There's no `docker compose up` command and no verification step. And I wonder: the `.env` sits inside the web root, protected only by `location ~ ^/(.env|data)`. That regex has an unescaped dot. Fine, but it relies on me trusting it."

---

## 4. Tomasz, backend Java developer, experienced Linux admin, uses Caddy on a Debian VPS

"Caddy handles HTTPS for me automatically, good. The Caddy page is shorter. Same install block as nginx: `sudo apt-get install php php-curl` again pulls Apache2, which on my box binds to port 80 before Caddy starts. And `php8.5-fpm` isn't in Debian stable without an external repo. The page doesn't mention that.

It doesn't tell me to install Caddy itself, or where the Caddyfile goes, or to reload. Fine, I know that. I note the config blocks `/.env` and `/php_errors.log`, but not `/data`. The nginx and Docker versions block `data`. So on Caddy the log files, which contain follower URLs and request details, may be served publicly. Is that intended? I'd have no way to know. The `php_errors.log` file is also never mentioned in the main README as a place to look when something breaks.

I paste the config. `try_files {path} /index.php?path={path}`: `{path}` includes the leading slash, while the nginx config passes `$1` without it. Does `index.php` handle both? I can't tell, so I test it.

Test step: same `test.php`. Same unexplained warning for `$_GET["path"]`. 'Caddy and PHP often run as different users': I chown things until the first-run directories get created. No example of what the correct ownership is. Then I visit webfinger and it works, but I'd like a documented expected output to compare against."

---

## 5. Aiko, Mastodon power user and Python hobbyist, managed Apache hosting, moving an old account

"I'm comfortable with Python and `requests`. The README's Quickstart is fine for me. I set `OLD_NAME` to the full URL of my old account. The `.env` comment says 'full account URl', and the README migration section also mentions `OLD_NAME`, but in the API example for moving away, `user` is `@new@example.com`, a different format from `NEW_NAME` (full URL). Which do I give?

My host runs Apache, but does `.htaccess` work? It needs `mod_rewrite` and `AllowOverride` enabled, and the README never lists those. Webfinger returns a 404 until I ask support to enable overrides.

Following the account: works. I check `data/logs/`, but where is that? I only have SFTP. It says the directory is the place to check, but it never says it appears after the first run, or what a successful follow log looks like. Does the bot auto-accept follows? Unclear.

Setup is done, but now what? There's no 'send your first post' step in Set Up. I find the API section. 'The password is encrypted when you send it and never stored on your server.' But I just put a hash in `.env`, so something is stored. And is it 'encrypted' or just sent as a form field over HTTPS? I assume I use the plain password in the API and the hash in `.env`, but the docs never say so. The requirements for the API say I need Requests, with a link to `https://python-requests.org/`, which I'm not sure is the right site, and there's no `pip install` line.

I try the location example: `"longitude": 40.77563, "latitude": -73.97474` for John Lennon Memorial in New York. Those numbers are swapped. 40.77 is the latitude and -73.97 the longitude, so my post lands in the wrong place or fails validation.

Delete and edit need 'the ID of your post'. Where do I get it? `r` is never printed in any example. I look at my site's page and guess. For HTML: 'See `$allowed_elements`'. That's a PHP variable. Which file? I grep `index.php`.

I also see Unfollow, Block and Unblock are in the Features list but there's no example or `action` value. Image alt text is passed as the 'filename' in `("This is the alt text", open("red.png","rb"))`, which I'd never have guessed. I try Debugging: `requests_toolbelt` isn't a Requests dependency and isn't listed anywhere."

---
=== CRITIQUE U9940 END ===

=== CRITIQUE U3059 START ===
1. The requirement is PHP 8.5 ("[PHP 8.5](https://www.php.net/releases/8.5/en.php) (We live in the future now.)"), which most shared hosts and distro packages will not offer yet. This conflicts with the claim that it "will run on shared hosts, a Raspberry Pi, or any modern web server". The docs never say whether older PHP versions work, and the same "php8.5-fpm" package name is hard-coded in the nginx and Caddy guides. A user on PHP 8.2 or 8.3 cannot tell whether to give up or try.

2. The Quickstart and Set Up disagree about what to upload and when to rename. Quickstart says "Upload `index.php`, `.htaccess`, `.env.example` to your subdomain" and then "Rename `.env.example` to `.env`". Set Up says to rename first and then upload `index.php`, `.htaccess`, and `.env`. The `.env.example` header says "rename this file to .env and upload it". Dotfiles are often hidden in file managers and FTP clients, so the order matters. Also, the numbered list in Set Up starts at "0." and then repeats "1." for every later step.

3. The most error-prone step is generating the RSA keys, and the README never mentions it. The `.env.example` comment says "Generate locally by opening `tools/rsa_key_generator.html` on your computer", but the Quickstart and Set Up never tell the user to do this. The Quickstart only lists uploading files, and users who only upload the three files will hit missing keys. Someone who downloads only the three named files will not have `tools/` at all. There is also no hint on how to turn the generated PEM into a single line with `\n` ("Newlines must be replaced with "\n""), or on whether the HTML tool does this for them. It is also unclear whether the tool is safe to use offline, and the key is described as "Generate locally" with no mention of keeping the private key secret.

4. The password setup is confusing and conflicts with the API docs. `.env.example` says to generate it with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );` or `php tools/generate_password.php 'Y0ur_p4s5w0rd'`. This assumes PHP CLI is installed locally, which is not stated as a requirement, and the user has to put the hash (not the plain password) in `.env`. The README then says "The password is encrypted when you send it and never stored on your server". The API examples send `"password": "your-password-here"` in a form POST. No text explains that this is the plain password, not the hash, or that "encrypted" depends on HTTPS. The hash contains `$` characters that may be expanded or mangled inside double-quoted values in `.env`, and nothing warns about that.

5. The `.env` instructions point the user in a circle. The README says "Edit `.env` and follow the instructions inside it", and `.env.example` says "At a minimum, you must provide KEY_PRIVATE, KEY_PUBLIC, PASSWORD, and USERNAME", but it also says "Mandatory Fields. Without these, ActivityBot won't work." `.env` is hidden by default on many systems, so a first-time user may not find it after renaming. Also, the `.env.example` header says to upload it "along with index.php and .htaccess" but never mentions `tools/`, which holds the key generator and password script the file depends on.

6. Hosting assumptions are vague. The README says the bot lives on a subdomain and "It will not work in a subdirectory", but the `.env.example` has no domain setting. It is not stated how the domain is detected, what happens behind a proxy, or whether `.htaccess` needs `mod_rewrite` and `AllowOverride` enabled. "Apache or similar" in "The default set up assumes Apache or similar" is not specific. "Create a subdomain" is also not explained for users unfamiliar with DNS and hosting control panels (document root, DNS records, TLS issuance).

7. The README says "This should include the following extensions by default: PHP cURL ... OpenSSL", and links to a release-notes page about "persistent-curl-share-handles" rather than an installation guide. Many installs do not enable cURL by default. There is no check command such as `php -m` and no statement about other needed extensions (mbstring, json, fileinfo, gd or exif for images). The second of these links does not explain what the extension is for.

8. The first verification step is under-specified. "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details" gives no example of the expected output. WebFinger normally needs a `?resource=acct:...` query, so a bare visit may return an error or empty response even when the setup is correct. There is also no troubleshooting section: no list of common errors, no mention of `php_errors.log` (which the Caddy config blocks but the README never explains), and no way to turn on error output.

9. The follow-up step "Check your `data/logs/` directory to see if the follow request was received correctly" gives no explanation of what a successful log looks like. It also does not say that this directory is created by the script on first run and needs write permission, which is mentioned only in the Caddy guide ("You may have to adjust the permissions of the directory ActivityBot is installed in"). On shared hosts, a user who never gets a `data/` directory has no clue why. The README should state that PHP must be able to write to the install directory.

10. Placeholder inconsistency in the examples: the README uses `@username@test.example.com`, but `.env.example` has `USERNAME="example"` and an instruction to use no "@" and no domain. The README example domain `test.example.com` is used for both a subdomain and the Python API calls, so it is not clear what to substitute. Hosting-specific text also uses `your.host.com`, `you.host.com`, and `test.example.com` in different files.

11. The API section depends on unstated assumptions. "Requirements" says only "a modern version of Python and ... the popular Python Requests library", with no install command (`pip install requests`). The debugging example uses `requests_toolbelt`, which is not mentioned in Requirements. The README never says what the API returns on success or failure (status codes, JSON body), so the user cannot tell a working post from a failed one except by checking social media. The post-image example `files = [("1",("This is the alt text", open("red.png", "rb")))]` uses the tuple's first element as alt text, which is an odd convention (normally it is the file name) and is not explained.

12. The README points to an unlisted source of truth. "See `$allowed_elements` to see which ones are supported" refers to a variable inside `index.php` without saying where or giving the list. Other behaviour (e.g. "Autolink URls, hashtags, and @ mentions", size limits for uploads, supported media types) is left for the user to read from code. The README is also silent on how `.env` values interact with the "If you prefer, you can edit `index.php` and place the details in there" option, and which takes priority.

13. The location example is likely wrong. `"longitude": 40.77563, "latitude": -73.97474` is New York, where latitude is about 40.8 and longitude about -74.0, so the values are swapped. A user copying it will place the post in the wrong spot (or in Antarctica/Asia depending on validation). Likewise, the Python snippets show `data` with `"DM": "@user@whatever.tld"` and `"action": "Follow"` without saying which fields are optional or case-sensitive.

14. The Docker guide is explicitly rough ("Rough Docker Instructions", "Documenting what I had to do"). It is not a complete setup: it shows a compose fragment (not a full file), uses `server_name you.host.com`, and has a Traefik comment that says "Internal port for postiz", which is copied from another project. The environment block has only a commented `PHP_OPCACHE_ENABLE: "1"   // Increase performance` using `//`, which is not valid YAML comment syntax, so the compose file would fail or treat the line wrongly. It also leaves `environment:` empty, which is invalid or at best null. Docker users are never told where `.env` goes or what the volume should contain. The nginx volume path `/etc/nginx/conf.d/activity-bot.conf` is set up, but the nginx config in the same file listens on 8080 and passes to `127.0.0.1:9000`, which may not match the image.

15. The nginx and Caddy guides are partial. Both start with `sudo apt-get install php php-curl` and then install `php8.5-fpm`, which on Debian or Ubuntu needs a third-party repository that is never named (the OpenSSL extension is not installed explicitly either). The nginx config listens only on port 80 with no HTTPS block, although HTTPS is a stated requirement (ActivityPub servers will not federate without it). The Caddy file hard-codes `/var/www/test.example.com` and `php8.5-fpm.sock`. The README says nothing about firewalls or restarting nginx after the edit. The test step creates `test.php` and tells the user to "access it at `https://test.example.com/test.php`", but never says to delete the file afterward (it echoes request input via `$_GET["path"]` unescaped). The comment "I don't THINK these are needed but computers are oh so very confusing." in the nginx config undermines confidence.

16. Security guidance is missing for the Apache path. The nginx and Caddy configs block `.env` and `data` ("location ~ ^/(.env|data) { deny all; ... }"), which suggests those are sensitive (private key, password hash, logs). The main README says nothing about this, so users should be told to confirm `https://test.example.com/.env` returns 403/404 after upload. The Apache `.htaccess` content is not shown so this cannot be checked. Also, the Caddy block lists `/php_errors.log`, but this file appears nowhere else.

17. Several quirks in `.env.example` may trip users. One comment line is missing its semicolon ("#	This is the joined date of your bot."), which suggests a custom parser with its own comment rules that is not documented. Values like `AVATAR` are "a relative URl without leading slash" but it is unclear what they are relative to, and whether uploaded images go in the web root. `BIRTHDAY` needs RFC 3339 without telling the user how to produce one. The `PROFILE_VALUE_*` entries contain HTML with single quotes inside double-quoted strings, and it is not said how to include quotes or `$` safely. `MAX_LOGS=2048` is unquoted while `PAGE_SIZE="1000"` is quoted, with no explanation. "Any positive integer." Still no explanation of what happens with an invalid value. Also, `NEW_NAME` says "You will then need to POST a move message to the "action/users" endpoint", which is not explained until much later.

18. The README tone and structure make scanning hard for newcomers. Jokes that read as hostile or flippant ("Because I hate you and want you to suffer", "GLaDOS", "Wayland", "We live in the future now") can obscure real requirements. The Features list is long and appears before the install section, and the Quickstart is a four-line bullet list that skips all the key steps (keys, password, username). The Missing Features list includes items like "Receive replies or private messages" which matter for expectations but sit far from the intro. The "Minimum Requirements" section has a child "Set Up" heading at the same level as the others, so it appears to be part of requirements.

19. The licence and project-policy text may surprise contributors and users, and is not placed where it will be seen. The AI policy states "If you want to submit a patch, you must attest that you are a human and wrote the code yourself", but `CONTRIBUTING.md` and `AGENTS.md` are in the file list and not shown, so first-time contributors cannot tell how that attestation is made or whether the files agree. The AGPL notice ("you **must** release the source code") may matter to anyone who modifies the bot, and is only at the bottom. The sample bot in the `SUMMARY` field also links to a GitLab repo while the README refers to Mastodon for contact; the correct canonical repository location should be stated once.

20. Minor accuracy and polish issues. The Funding section says the project "was funded" "From 2026-08", but the grant number is given as 101135429, which looks like a Horizon Europe number rather than an NGI0 Commons Fund agreement, so readers cannot trust it without checking. The text has inconsistent capitalisation ("URl", "URls", "acount" in "Once your new acount is set up", "Licence" vs "licenced"), and a missing hyphen in "Out-Of-Band". "Update / Edit Post" posts to `/action/send` with a `guid`, while "Delete Post" uses `/action/delete`, and the docs never explain where to find the `guid` ("You will need the ID of your post"). The `tests/` directory is in the file list but there are no instructions for running the tests or even saying what is needed (PHPUnit version).
=== CRITIQUE U3059 END ===

=== CRITIQUE U4159 START ===
1. The README never says where to get the files or how to download them. It lists no clone or release-zip step, yet the setup depends on files such as `tools/rsa_key_generator.html` and `tools/generate_password.php`.
2. The order of "rename" and "upload" is inconsistent. The Quickstart says "Upload `index.php`, `.htaccess`, `.env.example` to your subdomain" then "Rename `.env.example` to `.env`", whereas Set Up and `.env.example` say to rename first and then upload ("Then rename this file to .env and upload it along with index.php and .htaccess").
3. Dotfiles (`.htaccess`, `.env`, `.env.example`) are hidden by most file managers, Finder and FTP clients, and the docs never warn about it or explain how to reveal or upload them.
4. The PHP requirement, "[PHP 8.5](...) (We live in the future now.)", is very new and absent from most shared hosts, Raspberry Pi OS and stock Debian/Ubuntu repos. There's no guidance on how to check your version, how to get 8.5, or whether older versions work. The sentence "This should include the following extensions by default" is vague, with no way to verify, and the cURL link points to a release-notes anchor rather than extension docs.
5. The Intro says it "will run on shared hosts, a Raspberry Pi, or any modern web server". The setup instructions don't cover shared-host specifics (PHP selector, cPanel subdomain folders), nor a home Pi: domain/DNS, dynamic IP, port forwarding, and an HTTPS certificate are all missing.
6. "Create a new subdomain on your web host" assumes the reader has a web host and a domain. There's no explanation of how to create the subdomain, and the "HTTPS certificate (Let's Encrypt is fine.)" line says nothing on how to get one.
7. "Upload ... to the *root* directory of your subdomain ... It will not work in a subdirectory." is ambiguous on shared hosts, where the subdomain's document root is itself a subdirectory such as `public_html/name`.
8. `.env.example` says "Generate locally by opening `tools/rsa_key_generator.html` on your computer." The README never mentions the `tools` folder, and the key generator's output is not described (does it already produce the `\n` form?). The instruction "Newlines must be replaced with "\n"" doesn't say how or show a real example, since the sample value is "-----BEGIN RSA PRIVATE KEY-----\n...\n-----END RSA PRIVATE KEY-----". Nor does it warn that the file contains a private key.
9. Generating the password hash requires PHP on the user's own computer: "Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`" or `php tools/generate_password.php`. Non-PHP users have no alternative. There's also no advice on quoting the hash, which contains `$` characters, inside `PASSWORD=""`.
10. The distinction between the hash stored in `.env` and the plaintext used in API calls is never made. The examples all use `"password": "your-password-here"`. The sentence "The password is encrypted when you send it and never stored on your server" is misleading (it's sent in plaintext over HTTPS, and a hash is stored) and conflicts with the hash in `.env`.
11. "If you prefer, you can edit `index.php` and place the details in there." gives no location, format, or tradeoffs, and contradicts the stated need for `.env`.
12. `.env.example` has inconsistent comment markers: the line "#	This is the joined date of your bot." lacks the `;` that all other comment lines use. No statement says what parser or format `.env` follows, so the `#;` convention is unexplained.
13. "@username@test.example.com" is ambiguous placeholder text: it isn't clear that `username` means the user's `USERNAME` value, and no real example is shown.
14. The webfinger check says to "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details." The doc shows no example of expected output, doesn't say that real clients pass `?resource=acct:...`, and gives no troubleshooting for a blank page, 404 or 500.
15. The Apache path never states its own requirements or failure modes: it depends on `.htaccess` being honoured (mod_rewrite, AllowOverride) and on `.env` and `data/` being protected. Users on Apache have no way to verify that `.env` isn't downloadable.
16. "Check your `data/logs/` directory to see if the follow request was received correctly." never says where `data/` is, that it is created on first request, that the web server's user needs write permission, or what a correct log looks like. Only the Caddy README alludes to directories "it creates on the first run".
17. There is no troubleshooting section anywhere, and nothing says whether the bot automatically sends an Accept after a follow or how to confirm it.
18. The step "Optionally, upload an avatar and banner image ... Edit `.env` to include the image locations" doesn't say that you then need to call `/action/update` to propagate changes to followers (this appears only much later). The meaning of "relative URl without leading slash" (relative to what?) is also unclear.
19. The README headings are confusing. "Set Up" is nested under "Minimum Requirements", the numbered list starts at "0." and then every item is "1.", and there is a second "Requirements" heading under "Using the API", which can break anchors and numbering when rendered.
20. The "Missing Features" and "Features" lists don't match the documentation. Features such as unfollow, block, unblock, quote posts and video/audio have no API examples, and the Bridgy Fed / Bluesky bridge and the `DID` field are only mentioned as features with no setup steps. The URLs of the generated website pages (followers, hashtags) aren't given.
21. The API section's "You can send HTML. See `$allowed_elements` to see which ones are supported." points to a variable without saying that it lives in `index.php`.
22. "Check social media to see if the message appears." is vague. It doesn't say that only followers will see it, nor how to confirm success. None of the examples print or interpret `r`, so users can't tell if a call worked.
23. The API is explained only by Python examples despite "you can use whichever language you want". There's no parameter reference, no endpoint list, no response codes, and no curl example. Alt text is passed as the filename in `files = [("1",("This is the alt text", open("red.png", "rb")))]`, and the meaning of the field names "1", "2" etc. is unexplained.
24. For editing or deleting, "You will need the ID of your post:" doesn't say where to find the `guid`.
25. The location example has latitude and longitude swapped: `"longitude": 40.77563, "latitude": -73.97474, "place": "John Lennon Memorial"`. 40.77 is a latitude and -73.97 a longitude, so copying it would misplace the post.
26. The Debugging snippet uses `requests_toolbelt`, which is not listed in "Requirements" (only Python and Requests are).
27. Account migration text is inconsistent. `.env.example` wants a full URL ("For example "https://new.example/users/username"") while the API example uses `"user": "@new@example.com"`. "Once your new acount is set up" has a typo and is ambiguous between the new ActivityBot and the new account elsewhere. It's also unclear whether `/action/update` is needed after editing `OLD_NAME` or `NEW_NAME`.
28. Typos and inconsistencies: "Lenny" (presumably Lemmy), "acount", and "URl" (repeated in `.env.example` and the README).
29. Disk and log guidance contradicts itself. The requirement says "100MB free disk space (ActivityPub is a very "chatty" protocol. Expect lots of logs.)" and `.env.example` warns "Logs can fill up *fast*", while the FAQ answers "Will this fill up my disk?" with "Probably not."
30. The sentence "There is no need for Composer, Docker, Node, MongoDB, Wayland, GLaDOS, React, LLM, Adobe Creative Cloud, or Maven." is a joke list that reads oddly next to a full Docker guide and to the later need for Python, `requests` and local PHP for setup. It adds noise to the requirements.
31. The nginx and Caddy docs say "sudo apt-get install php php-curl" and "Requires `php8.5-fpm`". They assume Debian/Ubuntu without saying so, and omit `apt-get update` and the third-party repo needed for 8.5. The `php` meta-package may pull in Apache, which conflicts with nginx/Caddy. `php-curl` is installed unversioned alongside a versioned fpm.
32. README_nginx.md and README_caddy.md don't say where the config goes (conf.d vs sites-enabled, Caddyfile location), that the `map` block must be at the `http` level, or that you must test the config and reload the server. Caddy installation itself isn't covered.
33. The nginx config says only `listen 80;` and has no HTTPS configuration, although the main README requires HTTPS and all examples use `https://`.
34. The deny rules differ between guides without explanation. Caddy blocks `path /.env` and `path /php_errors.log` but not `data/`, while nginx's `location ~ ^/(.env|data)` blocks `.env` and `data` but not `php_errors.log` or `.htaccess`. The nginx regex has an unescaped `.` and no anchor after the name, so it matches unrelated paths such as `/database`.
35. "To test the config, make a file `test.php`" ... "Then access it at `https://test.example.com/test.php`" gives no expected output. Visiting `test.php` directly leaves `$_GET["path"]` undefined, so it produces a warning. The test doesn't exercise the rewrite rules, doesn't tell the user to delete `test.php`, and doesn't say what to do next.
36. The Caddy doc's "You may have to adjust the permissions of the directory ActivityBot is installed in, and/or the permissions of the directories it creates on the first run, as Caddy and PHP often run as different users" is vague: no user names, no commands, and the same issue applies to nginx and Docker but is not mentioned there.
37. README_docker.md is explicitly "Rough Docker Instructions." It gives only a service fragment, not a full compose file, with no `docker compose up` step and no `ports:` mapping for non-Traefik users. It doesn't say that the first volume holds `index.php` and `.env` or that the second mount is the nginx config below it.
38. The Docker doc has copy-paste leftovers and inconsistent placeholders: "traefik.http.services.activitybot.loadbalancer.server.port: 8080 # Internal port for postiz", `Host(`your.host.com`)` versus `server_name you.host.com;`, and an empty `environment:` key. The container's file ownership and write access to `data/` are not covered, and HTTPS is covered only via Traefik.
39. The Docker doc says its nginx config is "a mixture of the nginx config from README_nginx.md and the documentation from ServerSideUp", but doesn't say what was changed or why, so it's hard to keep the two in sync.
40. The README's "What is your AI policy?" states that "AI was not used at any stage", yet the repository contains an `AGENTS.md` file. Nothing explains its purpose, which could confuse readers or contributors. Also, `CONTRIBUTING.md` exists but the README's "submit a patch" paragraph doesn't link to it.
=== CRITIQUE U4159 END ===

=== CRITIQUE U5102 START ===
# Simulated first-time setups of ActivityBot

Five people with different backgrounds and hosting situations follow the README from the top. The narration is mine, written in each person's voice. It is a simulation, not observed behaviour.

---

## 1. Priya, hobbyist blogger on cPanel shared hosting

*Background: runs a WordPress blog, uses FTP and the cPanel file manager, has never edited PHP.*

"A bot that follows me on Mastodon, nice. Requirements: PHP 8.5. I have no idea what mine is. Is it in cPanel somewhere? My host's PHP selector tops out at 8.3, so I'm already stuck. 'We live in the future now' is funny, but it doesn't help me. Do I email support? Is 8.3 enough? I'll try anyway.

"Step 0, new subdomain. cPanel has a Subdomains page, so I make `bot.myblog.com`. It created a folder inside `public_html`. Is that the 'root directory of your domain'? I think so. Autoinstalled HTTPS shows up after a while. Fine.

"Step 1: 'Edit the `index.php` file to add a username, password, and keypair.' Where do I get a keypair? Nothing here says. There's a `.env.example`, so I open that. It says to open `tools/rsa_keys.html`, and there's no such file. I find `tools/rsa_key_generator.html`, so I guess that's it. Where did I even get these files? The README never said to download anything. I clicked 'Download ZIP' on a hunch.

"The key tool gives me a block of text. The env file says 'Newlines must be replaced with "\n"'. Replace how? In Notepad? There are also two different keys, and I paste them both into long single-line strings. I hope that's right.

"PASSWORD: generate with `password_hash(...)` or `php tools/generate_password.php`. I don't have PHP on my laptop. cPanel has a Terminal, but I'm scared of it. I end up pasting my plain password into PASSWORD, because the Python examples later say 'your-password-here'. That is probably wrong, but nothing tells me.

"I rename `.env.example` to `.env`. My Mac Finder won't show files starting with a dot. I upload through cPanel with 'show hidden files' on. I leave the other settings alone, and that includes the profile fields that point to somebody else's website and Mastodon account. Hopefully those just get ignored?

"Step 5: I open `/.well-known/webfinger` in the browser and get an error page (or maybe empty JSON). Is that right? It says to 'check that it shows a JSON file with your user's details,' and I have no idea what correct looks like. No troubleshooting. I'm stuck. I go and read the host's error log, which I'd never open normally."

## 2. Marcus, backend developer with an Ubuntu VPS and nginx

*Background: comfortable with Linux, systemd and nginx; knows Python; has never run an ActivityPub server.*

"The README says Apache `.htaccess`, but I run nginx. Nothing in the Set Up section mentions nginx. I only find `README_nginx.md` by reading the FAQ at the bottom. OK.

"`sudo apt-get install php php-curl`, then `php8.5-fpm`. On Ubuntu 24.04 that gives me PHP 8.3, and `php8.5-fpm` doesn't exist in the default repos. I need a third-party PPA, and the docs say nothing about it. Also, the first line installs the default PHP and the second installs 8.5 specifically. Are both needed? And `php-curl` is installed here, but the main README's requirements only mention OpenSSL. Which extensions do I actually need?

"The nginx block starts with a `map`. I paste the whole thing into `sites-available`, and `nginx -t` says `map` isn't allowed here. It has to live in the `http` context, and the doc doesn't say so. There's also no mention of enabling the site or reloading. `listen 80` with no TLS, but the README told me HTTPS is mandatory, so I bolt on certbot myself.

"`root /var/www/test.example.com/;` I create it, then upload `index.php` and `.env`. The `.env` has no obvious home, and it ends up in the web root. At least the nginx config denies `^/(.env|data)`. That regex has an unescaped dot, and it also catches `/database` and anything starting with `data`. Fine for me, but sloppy. And `/posts` and `/quotes` aren't denied, so I assume they're public on purpose.

"The test PHP file only echoes `$_GET['path']`. Visiting `/test.php` doesn't go through the rewrite, so `path` isn't set, and I get a warning or a blank value. Is that success? The comment 'I don't THINK these are needed but computers are oh so very confusing' doesn't inspire confidence in the fastcgi settings, though it works. Nothing says to delete `test.php` afterward.

"Follow step 8, 'Check your `/data/logs/`'. Is that the filesystem root or relative to my web root? It's relative. Which user needs write access? www-data, obviously, but the docs never say so. If I hadn't chown'd things, nothing would be written and I'd have no idea why."

## 3. Dana, homelab and Docker enthusiast with Traefik

*Background: runs 30 containers on a home server, writes compose files for fun, little PHP knowledge.*

"I skip straight to `README_docker.md`. It's titled 'Rough Docker Instructions' and it's honest about that. The compose snippet isn't a full file (no `services:`, partial indentation), and it has an `environment:` key with nothing under it except a comment. Will that validate? Probably not.

"The volume mounts `/path/to/your/docker/stuff/activity-bot/` to the web root. It doesn't say what goes into that folder: `index.php`, `.env`, and which of the others? It doesn't say anything about `.htaccess` being unnecessary either. I'd have guessed.

"The Traefik labels are 'optional', but I don't use Traefik. The snippet has no `ports:` mapping, so I'm unsure how to reach it. And the comment 'Internal port for postiz' was clearly copied from a different project's config, which makes me wonder what else was. The domain placeholder in the labels is `your.host.com`, but the nginx config says `you.host.com`.

"The nginx file is mounted into `conf.d`. The block says 'Default server definition' and listens on 8080, the same port the image's own default site uses. Do I have to delete or override the image default? Unknown. It also contains a `map` block at the top level, which is fine in `conf.d`, but nothing explains that.

"The `.env` setup lives in the main README, and I have to piece that together. And persistence: all the data (`data/`, `posts/`) ends up in my bind mount, along with the private key in `.env`. The container user must be able to write to the mount, and the host folder permissions are never mentioned. I mount it as root-owned, and the logs silently fail."

## 4. Tomás, artist with no coding experience and no hosting

*Background: runs a portfolio on a website builder, owns a domain through a registrar, no server, no command line.*

"I'd love an art bot. 'Set up a new sub-domain on your web host.' I don't have a web host, only a Squarespace-style site on my own domain. The FAQ says 'you should create free subdomains,' but where? Which providers? How would I know they support PHP 8.5 and `.htaccess`? I could point a subdomain at my existing site, but that doesn't give me PHP. I give up on hosting and ask a friend for space on theirs.

"They give me a folder on a shared server. The setup says the bot 'will not work in a subdirectory.' Mine is a subdirectory. We ask for a proper subdomain.

"Then the posting section: 'Requirements. This assumes you have a modern version of Python and have installed the popular Python Requests library.' I don't know what installing that means, and no command is given. It says I could use another language, but the examples aren't copy-pasteable in anything else, not even a `curl` line. So I can't send my first post.

"The image example: `files = [("1",("This is the alt text", open("red.png", "rb")))]`. I don't know why the alt text is where a file name should be, and the text doesn't explain it. I also don't know the file size or format limits.

"I wanted to delete a post: 'You will need the ID of your post.' Where do I find it? No instructions. After sending a post, `r` isn't printed anywhere in the examples, so I wouldn't even see the ID."

## 5. Aiko, security-conscious sysadmin on Debian with Apache

*Background: runs hardened servers, `AllowOverride None` by default, wary of secrets in the web root, prefers curl.*

"The requirements list HTTPS, OpenSSL and 100MB, then a joke list of things I don't need (Docker, Node, GLaDOS...). It doesn't list Apache `mod_rewrite` or `AllowOverride`, so the `.htaccess` will be ignored on my box unless I know to change the vhost. Nothing says so. It also doesn't say whether `.env`, `data/` or the logs are blocked on Apache. The nginx and Docker configs explicitly deny `.env` and `data`, which strongly suggests the `.htaccess` does too. I have to open it to find out, because the README is silent. My private key is going into a file inside the web root, so I want a straight answer.

"Key generation: 'Generate locally by opening `tools/rsa_keys.html`.' The file is called something else, and I'm asked to trust a browser-based tool with my private key. The doc doesn't say whether the tool runs entirely offline, or that `openssl genrsa` would work. And it gives no hint of what key format the bot expects. The example has 'BEGIN RSA PRIVATE KEY', but the tool may produce PKCS#8.

"The password hash: `$2y$10$...` inside double quotes in a `.env` file. Some env parsers expand `$`. The docs don't mention quoting rules, nor which parser is used.

"The API is shown only in Python. I translate to curl myself, guess that the form fields are url-encoded, and wonder whether `your-password-here` is the plain password or the hash. It's the plain one, but the document never states it.

"Reading further: 'How this works' says messages sent to your inbox are saved in `/data/inbox`, but the 'doesn't do yet' list says it doesn't receive messages, and the FAQ says it doesn't store replies. I can't tell what actually ends up on my disk, which matters to me. The FAQ says disk filling is unlikely, while `.env.example` warns logs 'can exhaust your file limits' and the requirements say to 'Expect lots of logs.' I set `MAX_LOGS` low and hope it works."

---
=== CRITIQUE U5102 END ===

=== CRITIQUE U6737 START ===
# Simulated first-run walkthroughs of the ActivityBot README

## Person 1: Maya, hobby blogger on cheap shared cPanel hosting (FTP and file manager, almost no PHP knowledge)

"A bot on the Fediverse in one file, great. Requirements: PHP 8.5. Let me check cPanel... the selector tops out at 8.3. 'We live in the future now' is cute, but is 8.3 enough? I'll try anyway and hope.

Set Up step 0, a subdomain. Fine. Step 1: 'Edit the index.php file to add a username, password, and keypair.' Where? What is a keypair? I open index.php and see code, not a form. I do see a .env.example, so I'll use that. The file says 'Generate locally by opening `tools/rsa_keys.html`'. There is no such file in the download, only `rsa_key_generator.html`. The page makes two blobs of text. The .env wants them on one line with '\n' in place of newlines. I don't know how to do that in Notepad.

For PASSWORD it wants a hash. I need PHP on my own laptop to run `php tools/generate_password.php`, and I don't have PHP. The README said none of this. I find the `password_hash(...)` line, but I can't run it anywhere. I paste my plain password in instead and hope.

I rename to .env, but my file manager hides dotfiles, and FTP shows nothing after upload. Did it upload? The README says to upload index.php and .htaccess to the 'root directory of your domain'. cPanel put my subdomain in a subfolder. Is that the root or not?

I visit /.well-known/webfinger and get a 400 or an empty error. The README says I should see 'a JSON file with your user's details', but it never says what the URL needs or what the JSON looks like. I give up for the night."

## Person 2: Raj, sysadmin on an Ubuntu VPS with nginx and certbot

"Skipping the .htaccess part, since the FAQ points to README_nginx.md. The Set Up still says 'Upload `index.php` and `.htaccess`', so is .htaccess pointless on nginx? Nobody says.

README_nginx.md: `sudo apt-get install php php-curl` pulls in Apache on my box and tries to grab port 80. Then `php8.5-fpm` isn't in the Ubuntu repos. It needs a third-party PPA, and nothing says so. The page opens with 'requires php8.5-fpm which is a thing that passes requests to PHP', which is not a requirement statement. `php-curl` wasn't in the README's requirements either. Do I need it?

The config only has `listen 80;`, yet the main README demands HTTPS. I add certbot myself. Nothing says to symlink into sites-enabled or reload nginx, but I know that. The root is `/var/www/test.example.com/`, and nothing says who should own it or that PHP-FPM needs write access to create `data/`. The dotfile-deny block that the Docker config has ('Deny access to . files, for security') is missing here, so `.htaccess` and `.git` are exposed. The comment '#     I don't THINK these are needed but computers are oh so very confusing' doesn't inspire confidence.

For the test file, `test.php` echoes `$_GET["path"]`. Browsing to it directly gives an undefined-index warning, and nothing says what success looks like. I remove it and carry on.

I hit `/.env` to make sure it's blocked, which the docs never tell me to do. It is blocked by the config, so fine. Webfinger works once I read the code to find the `resource=` parameter."

## Person 3: Leah, homelab enthusiast with Docker Compose and Traefik

"README_docker.md opens with 'Rough Docker Instructions' and 'Documenting what I had to do'. It is a diary, not a procedure.

The compose snippet starts at `activity-bot:` with no `services:` parent. The `environment:` key contains only a comment, which is null and might make compose complain. The Traefik label says '# Internal port for postiz', which was copied from another project. The volume `/path/to/your/docker/stuff/activity-bot.conf` is mounted, but the nginx config appears in the next section with no 'save this as activity-bot.conf'. Nothing says to copy index.php, .htaccess, and .env into the mounted `activity-bot/` folder. I have no `ports:` mapping and no `docker compose up` step.

The compose file uses 'your.host.com' and the nginx file uses 'you.host.com' for `server_name`. Typo or two different things? The image already ships a default server on 8080, so does my conf replace it or collide with it? The image runs PHP as a non-root user, and I have to guess the host folder permissions so it can create `data/`. HTTPS is a hard requirement, but without Traefik the doc gives me nothing about certs.

I also had to dig for .env: the main README's step for index.php edits versus .env tells me nothing about how Docker passes it. I assume the file sits in the mounted folder."

## Person 4: Tom, Python data scientist on a Windows laptop with a managed Apache host (PHP 8.2 only)

"I just want my scripts to post results. The Python API examples look easy. First I have to set up the server, though.

The README says 'PHP 8.5' and the host offers 8.2. The Requirements never say whether older PHP works. The Requirements also don't mention Apache's mod_rewrite or `AllowOverride`, which the `.htaccess` needs. I assume it's fine.

The password confusion hits me hard. `.env.example` says PASSWORD is a hash made with `php tools/generate_password.php 'Y0ur_p4s5w0rd'`. I have no PHP locally, and single quotes don't work in Windows cmd. Then every API example sends `"password": "your-password-here"`. Is that the plain password or the hash? The README doesn't say. I try the hash and get a 401-ish response. Then I try the plain one, which works. I only guessed.

In my first script I check `r` and get a response object with no printed content. The README never shows what a success or failure response looks like, so I can't tell. The 'Requirements' section says 'a modern version of Python' and the Requests library, but not `pip install requests` or `requests_toolbelt`, which the Debugging section imports. I would also like a curl example.

The image example: `files = [("1",("This is the alt text", open("red.png", "rb")))]`. Why is alt text sitting where a filename goes? Surprising and never explained. For location, the example has `"longitude": 40.77563, "latitude": -73.97474`, and those look swapped, since 40.77 is New York's latitude. I post a delete example, and the README says 'You will need the ID of your post', but never says where the guid comes from."

## Person 5: Dana, Mastodon power user on an Apache VPS behind Cloudflare, migrating an existing account

"I have an old account and want to move followers. Reading the feature list first: 40 bullets before I see how to install. Then the 'doesn't do' list says 'Receive messages (other than follows, unfollows, and quote requests)', but 'How this works' says messages sent to your inbox are saved in `/data/inbox`. Which one is it?

The 'How this works' directories are inconsistent. Logs, followers, and inbox live under `/data/...`, but posts are in `/posts` and quotes in `/quotes` with no `/data` prefix. Is that right? I assume the data folder needs to be writable, but no step says so.

Following the steps, I get webfinger working, then search for '@username@test.example.com'. Is 'username' literally the placeholder or my USERNAME value? The README never ties them together. I follow the account and nothing happens. The README says 'Check your `/data/logs/` directory to see if the follow request was received correctly', but doesn't say how a correct request looks, or whether follows are auto-accepted. Cloudflare's bot protection might be blocking servers calling my inbox. Nothing mentions that, and there's no troubleshooting section anywhere.

Migration: I add OLD_NAME to the .env as told ('Once your new ActivityBot is set up, go to your old account and follow its procedure'). Then the 'moving away' paragraph says 'Once your new acount is set up, go to your new account and follow its procedure for moving followers to it', which is the same steps stated in confusing order. It never says which comes first or when to run the Move POST. For the avatar, step 4 says to upload an image, but `AVATAR=""` in .env needs a value, and the step never says so.

For first posts, 'Check it has worked' says to 'Check social media to see if the message appears'. With zero followers it won't appear anywhere obvious. I only learn that by trial and error."

---
=== CRITIQUE U6737 END ===
