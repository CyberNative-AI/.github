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

# PROBLEMS

1. The Quickstart and Set Up disagree on the order for the env file. Quickstart says "Upload `index.php`, `.htaccess`, `.env.example` to your subdomain" and then "Rename `.env.example` to `.env`", but Set Up says to rename and edit first, then upload `.env`.
2. There are no instructions anywhere for obtaining the files (download, clone, release ZIP). The Quickstart lists three files to upload but `.env.example` also requires `tools/rsa_key_generator.html` and optionally `tools/generate_password.php`, which the Quickstart never mentions.
3. Dotfiles (`.env`, `.env.example`, `.htaccess`) are hidden by default in FTP clients, cPanel, Finder and Windows Explorer, and the docs never say so. Renaming to a name beginning with a dot is also awkward on some systems.
4. "PHP 8.5 (We live in the future now.)" is given as the minimum with no fallback, no guidance on how to check the host's version, and no statement of what happens on 8.3 or 8.4. This conflicts with the claim "It will run on shared hosts, a Raspberry Pi, or any modern web server".
5. "This should include the following extensions by default" is vague. It doesn't say how to check that cURL and OpenSSL are enabled, and the cURL link goes to a release-notes anchor ("persistent-curl-share-handles"), not to extension documentation.
6. The nginx and Caddy pages tell users to run `sudo apt-get install php php-curl` and `sudo apt-get install php8.5-fpm`. On Debian and Ubuntu the `php` metapackage can pull in Apache, which clashes with nginx and Caddy, and `php8.5-fpm` is not in the default repositories. There's no mention of a third-party repo.
7. The Apache path never states its requirements: `.htaccess` needs `mod_rewrite` and `AllowOverride`, and `.env` protection depends on it. The README says only "The default set up assumes Apache or similar".
8. The "Other Servers" section doesn't say which of the main Set Up steps still apply (key generation, `.env`, upload, verification), whether to upload `.htaccess`, or how to enable the site and reload the server.
9. The key step says "Generate locally by opening `tools/rsa_key_generator.html` on your computer" and "Newlines must be replaced with "\n"" but does not say whether the tool does the replacement, whether it works offline, or what format it outputs. Users may convert by hand.
10. The password step needs PHP, either "`password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`" or `php tools/generate_password.php 'Y0ur_p4s5w0rd'`. The requirements never say PHP is needed on the local machine, and the single-quote command fails on Windows cmd.
11. It never says whether the stored hash, which contains `$` characters, needs particular quoting in `.env`. The same worry applies to passwords or text containing quotes.
12. `PASSWORD` in `.env` is a hash, but the API examples use `"password": "your-password-here"`. The docs never state outright that `.env` holds the hash and the API uses the plain password.
13. "The password is encrypted when you send it and never stored on your server" is inaccurate or confusing. The password is sent as a form field (protected only by HTTPS), and a hash of it is stored in `.env`.
14. The main README does not say how the domain is determined. `.env.example` says "At a minimum, you must provide KEY_PRIVATE, KEY_PUBLIC, PASSWORD, and USERNAME", with no mention of the host name or whether it is inferred from the request.
15. The default values in `.env.example` (REALNAME "A single file ActivityPub Bot Server", the SUMMARY link, the BIRTHDAY, and four sample profile fields including a mention of a real person's account) are presented as examples. The text doesn't say they will be published as-is if left alone or how to blank them.
16. `.env.example` has an inconsistent comment prefix. Every comment starts with `#;`, but one line is "#	This is the joined date of your bot." with no semicolon, which may be parsed as a setting depending on the loader. `PAGE_SIZE="1000"` is quoted while `MAX_LOGS=2048` is not, and nothing explains the format rules.
17. "If you prefer, you can edit `index.php` and place the details in there." says neither where in `index.php` nor which takes precedence if both are present.
18. Image settings say "Should be a relative URl without leading slash" without saying relative to what, where to put the file on the server, or whether "maximum ... 400x400" means exact or maximum size. Step 8 says only "Edit `.env` to include the image locations."
19. Editing `.env` after launch (avatar, banner, profile fields) does not federate on its own. Step 8 omits that you must call `/action/update`, which is described much later under "Update Account".
20. Step 4, "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details", gives no sample output, doesn't mention that real WebFinger requests use a `resource=` query, and offers no troubleshooting for an error, blank page or 404. DNS propagation and TLS issues are not mentioned.
21. Step 7, "Check your `data/logs/` directory...", doesn't say that the directory appears after the first request, what a good log entry looks like, whether follows are auto-accepted, or what to do for people with only SFTP access. There is no troubleshooting section at all.
22. Set Up ends at a follow request and never says how to publish a first post. The user has to find the API section on their own.
23. Nothing tells the user to confirm that `.env` (containing the private key) and `data/` are not publicly downloadable, even though the nginx, Caddy and Docker files include deny rules. Caddy's `@blocked` lists `path /.env` and `path /php_errors.log` but not `data`, unlike the nginx and Docker configs.
24. The paragraph "It will not work in a subdirectory" is never reconciled with users who have no subdomain, no domain or only an apex domain. It also doesn't mention that changing `USERNAME` or the keys after followers exist will break the account.
25. The Python API examples use `requests`, linked as "https://python-requests.org/", with no install command. "Debugging" uses `requests_toolbelt`, which is not mentioned anywhere else and isn't part of Requests. Non-Python users are told "you can use whichever language you want" but no `curl` or raw-HTTP example is given.
26. There is no API reference. Endpoint names, field names, the `action` values and the response format (what comes back, and how to learn a post's GUID) are scattered across examples. Features such as Unfollow, Block, Unblock and bridging to Bluesky appear in the feature list with no documented request.
27. "You will need the ID of your post" for delete and edit never says where to find the ID. No example prints the response, and edit is performed against `/action/send` with a `guid`, which is not obvious.
28. "You can send HTML. See `$allowed_elements` to see which ones are supported." refers to a PHP variable without naming the file or showing the list.
29. Alt text is supplied as the "filename" slot in `files = [("1",("This is the alt text", open("red.png", "rb")))]`, and the multiple-image example puts colour names in that slot. This convention is never explained.
30. The location example has latitude and longitude swapped: `"longitude": 40.77563, "latitude": -73.97474` (the numbers match latitude 40.77, longitude -73.97 for New York).
31. The migration instructions are ambiguous. "Once your new acount is set up, go to your new account and follow its procedure for moving followers to it" is hard to follow (and has a typo), and `NEW_NAME` expects a full URL while the Move example uses `"user": "@new@example.com"`.
32. The Docker page is not a procedure. It says "Documenting what I had to do", provides a compose fragment without `services:`, `ports:` or networks, and the Traefik line "optional, especially if you're not using Traefik" doesn't say what to do otherwise. It contains the copy-paste leftover "# Internal port for postiz" and an `environment:` key with only a comment.
33. The Docker page doesn't say what must be in the mounted folder (`index.php`, `.htaccess`, `.env`), how the supplied nginx file relates to the image's own default server on port 8080, how to fix `data/` permissions in the container, or what command and check complete the setup. The hostnames are also inconsistent (`your.host.com`, `you.host.com`, `test.example.com`).
34. The nginx config listens only on port 80 (`listen 80;`) while the main README requires HTTPS. It gives no TLS step. It also assumes `root /var/www/test.example.com/;` exists with correct ownership, and includes the leftover comment "I don't THINK these are needed but computers are oh so very confusing."
35. The `test.php` check in the nginx and Caddy pages echoes `$_GET["path"]`, which is undefined when called directly, so a warning appears. The expected output is not stated, and the pages never say to delete `test.php` afterwards.
36. The Caddy page says only that "You may have to adjust the permissions of the directory ActivityBot is installed in ..." without naming which users or what permissions. It also doesn't mention installing Caddy or applying the config.
37. The README has typos and small inconsistencies that cost trust: "Lenny" (likely Lemmy), "acount", "URl", and "Bridge to BlueSky" versus "BSky". The humorous requirements list ("Wayland, GLaDOS, ... Maven") and the answer "Because I hate you and want you to suffer" may confuse non-native readers.
38. "Set Up" is a level-3 heading nested under "Minimum Requirements", and the numbered steps start at "0." and then repeat "1." for every item, which can render oddly. A reader may lose the sequence.
39. The README mentions the "tests/" folder nowhere, so contributors cannot tell how to run them, and nothing links to `CONTRIBUTING.md` from the AI-policy section where "you must attest that you are a human" is stated. The presence of an `AGENTS.md` file alongside "AI was not used at any stage" may also raise questions (its contents were not provided, so this is unverified).
