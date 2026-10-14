=== CRITIQUE U9845 START ===
# Simulated first-run walkthroughs of the ActivityBot README

## 1. Priya, hobbyist artist on cheap cPanel shared hosting (non-technical)

"A bot that posts my daily sketch prompt. Lovely. Where do I download this? The README starts with a feature list and never says. I'll guess the repo page has a zip.

Requirements: 'PHP 8.5 (We live in the future now.)' Ha. But my host's PHP dropdown tops out at 8.3. Is that a no? Does it work on older PHP? It doesn't say. I'll try anyway.

Step 0, subdomain. I find 'Subdomains' in cPanel and make `bot.mysite.art`. It made a folder inside public_html. Step 2 says 'It will not work in a subdirectory.' Is this a subdirectory? I have no idea whether 'root directory of your domain' means that folder.

Step 1, 'Edit the index.php file to add a username, password, and keypair.' Where in the file? What's a keypair? What do I put for the password? I give up on index.php and use the .env route. I rename `.env.example` to `.env` on my Mac and it vanishes from Finder. Then the FTP client doesn't show `.htaccess` either. Did it upload?

The .env says to generate keys 'locally by opening `tools/rsa_keys.html`'. There's no such file. There's a `rsa_key_generator.html`. OK, I open that. It gives me two blocks of text with line breaks, and the .env says 'Newlines must be replaced with "\n"'. Replace how, by hand? I paste and hope.

Password: 'Generate with `password_hash(...)`' or 'php tools/generate_password.php'. I don't have PHP on my laptop. Do I put the hash in the .env, and then send the plain password from the API? Nothing says.

I upload and visit `/.well-known/webfinger`. I get an error page or a blank page. The README only says 'check that it shows a JSON file with your user's details' and gives no example, so I can't tell what is wrong. I'm stuck."

## 2. Marcus, sysadmin with an Ubuntu VPS running nginx

"I'll skip Apache and read README_nginx.md. It starts with 'requires php8.5-fpm which is a thing that passes requests to PHP', then `sudo apt-get install php php-curl`. On Ubuntu `php` pulls in Apache, which will fight nginx for port 80, and it installs the distro's default PHP, not 8.5. `php8.5-fpm` isn't in the stock repos, so I need a third-party PPA. The page says none of this.

Nobody told me to install nginx, either. I assume I have it. php-curl is installed here but the main README requires only OpenSSL. Which extensions are really needed?

The config has `listen 80;` and nothing for TLS, but the README says HTTPS is required and ActivityPub servers will insist on it. I add certbot myself. The page doesn't say where the config goes (sites-available?), when to reload, or that the files should be owned by www-data so the app can write `/data`. The commented-out lines say 'I don't THINK these are needed but computers are oh so very confusing', so I don't know if the author tested without them.

The test advice is to create a `test.php` and 'attempt to access it on test.example.com/test.php.' That hits the `\.php$` block directly and never exercises the `@rewrite` path. With no `?path=` it just prints 'Path is...'. It doesn't say what success looks like. It also echoes `$_GET` unescaped and nobody says to delete the file afterwards.

Main README step 2 still tells me to upload `.htaccess`. Is it needed on nginx? Not stated."

## 3. Jun, homelab hobbyist with Docker and Traefik

"README_docker.md is titled 'Rough Docker Instructions', which is honest at least. The snippet is a fragment of a compose file, without `services:` or networks. Fine, I can wrap it.

The volume `/path/to/your/docker/stuff/activity-bot/:/var/www/html/public`: what goes in that folder? Presumably `index.php`, `.env`, and maybe `.htaccess`, but it never says. The second volume maps `activity-bot.conf`, and the next section is just headed 'nginx config'. It never says to save that block as `activity-bot.conf`.

Placeholders disagree: `you.host.com` in nginx, `your.host.com` in Traefik, `test.example.com` in the main README. There's a comment 'Internal port for postiz', which looks pasted from another project, so I double-check that 8080 really is right.

I don't run Traefik. The doc says it's optional, but then how does my container get HTTPS? Port 8080 is plain HTTP. Nothing covers that. Does the container user have write permission on the mounted folder for `/data` and `/posts`? Not mentioned. The main README's Requirements bullet 'Docker, Node, MongoDB... (absolutely none of these!)' directly contradicts the FAQ offering Docker, which is just confusing. I also can't tell if the serversideup image has the PHP extensions the app needs."

## 4. Amara, Python data journalist on a Windows laptop with Apache hosting

"Setup goes through, mostly, after I stumble on the key page. Now the API. 'This assumes you have a modern version of Python and have installed the popular Python Requests library.' No `pip install requests` is given, which is fine for me. But the Debugging section imports `requests_toolbelt`, and that's mentioned nowhere above it.

I copy the first example with 'your-password-here'. Is that the plaintext password, or the hash I put in `.env`? I guess plaintext. The response `r` is never printed or described, so I can't tell whether a post succeeded. 'Check social media to see if the message appears' is useless because my bot has no followers yet. Following the bot was step 7 of setup, and I skipped it.

I try the location example: `"longitude": 40.77563, "latitude": -73.97474`. Those look swapped, since 40.77 is the latitude of New York. I post it and the pin lands in the ocean.

For edit and delete, 'You will need the ID of your post' but there's nothing on where to get the guid. The response? The logs? A URL? The feature list also claims unfollowing, blocking, unblocking and showing followers, yet there's no example for any of them. On Windows the `php tools/generate_password.php 'Y0ur_p4s5w0rd'` single quotes don't work in cmd either. 'You can send HTML. Only formatting elements are allowed.' Which ones?"

## 5. Tom, existing Mastodon user and open-source developer on an Apache VPS who deploys by git push

"I want to move my followers from my old account and bridge to Bluesky. Moving first: the README says to add an `OLD_NAME` to the `.env`, but the format (a full account URL like `https://example.social/users/username`) is only in `.env.example`. It also says 'Once your new acount is set up, go to your old account and follow its procedure' (typo, and vague). The move-away instructions say 'your new account' where I think they mean the other account.

The Bluesky bridge is listed under features, but there are no steps in the README, only a `DID` field in `.env.example`.

I read the Licence. 'If you modify this code and let other people interact with it over a computer network, you must release the source code.' Step 1 told me to edit `index.php` with my private key and password. If I commit that and publish the fork, I've leaked my keys. If I don't, am I breaking the AGPL? Nothing warns me or says to use `.env` for that reason. I use `.env` and add it to `.gitignore` myself.

I check 'How this works': posts are in `/posts`, followers in `/data/followers`, quotes in `/quotes`. Why are some under `/data` and some not? And the inbox is stored in `/data/inbox`, yet the feature list says it can't receive messages and the FAQ is about why it 'doesn't store replies'. I can't tell what is saved.

I also want to check that `.env` and `/data` aren't publicly downloadable. For nginx there's a deny rule; for Apache the README says nothing about it or how to verify it.

Finally I follow the bot from Mastodon and then look in `/data/logs/` over SSH. There's no example of a good log line, and if nothing shows up there's no troubleshooting at all."
=== CRITIQUE U9845 END ===

=== CRITIQUE U2291 START ===
# Simulated first-time users of the ActivityBot README

## 1. Maya: WordPress blogger, macOS, cPanel shared host (Apache)

"Fine, a single PHP file. Where do I get it, though? The README never says. I'll search for the project and download a zip from the repository.

Requirements: 'PHP 8.5'. My cPanel's MultiPHP manager tops out at 8.3. Do I need 8.5 exactly, or does 8.3 work? It doesn't say. I'll try 8.3 and hope.

Step 1: 'Edit the index.php file to add a username, password, and keypair.' Where in the file? What's a keypair? How do I make one? The README doesn't say. There's a `.env.example` that mentions `tools/rsa_keys.html`, but my download only has `tools/rsa_key_generator.html`. Okay, I guess that's it. I paste the keys with real line breaks, and then notice the `.env.example` says newlines must be '\n'. I don't know whether that applies to index.php too.

I rename `.env.example` to `.env`. Finder tells me names starting with a dot are hidden, and cPanel's File Manager hides them unless I tick 'show hidden files'. I upload to `public_html/`, but my domain is a sub-domain, so which folder is its 'root directory'? I guess the sub-domain's document root.

Webfinger: I visit `/.well-known/webfinger` and get an error page about a missing resource. Is that broken or expected? I can't tell. I give up for the night."

## 2. Tomas: sysadmin, Ubuntu VPS, nginx

"I'll skip Apache. README_nginx.md. `sudo apt-get install php php-curl`. On Debian and Ubuntu the `php` metapackage can pull in Apache, which grabs port 80 and fights nginx. Then `php8.5-fpm`: not in the stock Ubuntu repos, so I need a third-party PPA. Nothing mentions that. I also notice curl was never listed as a requirement, so why am I installing it?

The config has `listen 80;` but the main README says HTTPS is required. It doesn't say how to add TLS, where to save the file, how to enable the site, or when to run `nginx -t` and reload. The `fastcgi.conf` vs `fastcgi_params` comment ('I don't THINK these are needed...') doesn't inspire confidence.

The test: 'attempt to access it on test.example.com/test.php'. What should I see? `$_GET["path"]` will be undefined on a direct hit, so I'll probably see a warning or an empty value. Is that success? Should I delete test.php afterwards? Unclear.

Then the bot needs to write `data/`, `posts/` and `quotes/`. Nobody says www-data must own or be able to write them. The follow request fails silently, and I only find out by reading error logs."

## 3. Priya: homelab Docker user with Traefik

"README says 'Docker ... (absolutely none of these!)' and then the FAQ says 'If you must', so Docker is okay but unloved. README_docker.md is titled 'Rough Docker Instructions'.

The compose snippet is a fragment with no `services:` key, and `environment:` has only a commented-out line, so it's empty. The Traefik label comment says 'Internal port for postiz', copied from another project. The router host is `your.host.com` but the nginx file says `server_name you.host.com;`. I have to realise they must match.

I'm told to mount a directory at `/var/www/html/public` and a conf file at `/etc/nginx/conf.d/activity-bot.conf`. I'm never told to put index.php, .htaccess and `.env` in that directory. I'm never told to save the nginx block under that file name. The directory must be writable by the container user for logs. That's not mentioned. There's no `docker compose up -d`, no HTTPS advice if I don't use Traefik, and the image's own default server may also listen on 8080.

I get a 502 and have no troubleshooting notes."

## 4. Jordan: Windows, FileZilla, small free host, moving from an old Mastodon account

"I want to migrate my followers, so I read the `.env.example`: 'OLD_NAME' wants 'the full account URl' like `https://example.social/users/username`. The README's Migrate section says add an `OLD_NAME` and then 'follow its procedure for migrating away', with no details of what the old server needs from me.

Hidden files again: FileZilla doesn't show `.htaccess` or `.env` unless I turn on 'force showing hidden files'. When I rename `.env.example` to `.env` on Windows, Explorer complains about a nameless extension.

The README says to edit index.php or use .env, which gives two competing configuration routes, and then 'Then rename this file to .env and upload it' in the example file implies .env is the main route. Which one wins if I do both?

`AVATAR` should be a 'relative URl without leading slash'. The README just says 'Optionally, upload an avatar and banner image'. It doesn't tell me to set `AVATAR` and `BANNER`, so I wonder if my upload does anything.

Step 8: 'Check your `/data/logs/` directory'. On my host I can't tell whether `/data/logs/` means server root or the site folder. It also doesn't say the folder is created automatically."

## 5. Aisha: Python data journalist who wants to post from a script

"Setup done by a colleague, so I go straight to 'Using the API'. 'Requirements' says I need Python and Requests, with no install command. Fine, I know `pip install requests`.

The first snippet uses `"password": "your-password-here"`. Is that the plaintext password or the hash that went into `PASSWORD`? I assume plaintext, but the README never says so. Posting works, but I get no clue about what a success or failure response looks like, because `r` is never inspected.

Image upload: `files = [("1",("This is the alt text", open("red.png", "rb")))]`. The alt text sits where the filename normally goes. The README doesn't explain this trick. In the multi-image example, 'red', 'green' look like names, not alt text.

Location: `"longitude": 40.77563, "latitude": -73.97474`. Those are New York coordinates with the values swapped. If I copy it, my post lands in Antarctica.

Delete and edit want 'the ID of your post'. Where do I get it? Not stated. Editing uses `/action/send` again, which is not obvious. The feature list promises unfollow, block, unblock and show followers, but there are no examples or action names. Debugging needs `requests_toolbelt`, which isn't in Requirements."
=== CRITIQUE U2291 END ===

=== CRITIQUE U4143 START ===
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
=== CRITIQUE U4143 END ===

=== CRITIQUE U8128 START ===
# Simulated first-run walkthroughs of the ActivityBot README

## Person 1: Rosa, a librarian on cheap cPanel shared hosting (Windows laptop, no SSH, FTP and file manager only)

"I want a little bot that posts a book of the day. I've made a subdomain in cPanel and turned on HTTPS. Good, step 0 is done.

Step 1 says 'Edit the index.php file to add a username, password, and keypair.' Where do I get the file? I can't find a download or clone instruction anywhere. I eventually find the repository link under 'Feedback' and download a zip. Now I open index.php in Notepad. It's long and I can't tell where to put a keypair. What's a keypair? The sub-bullet says I can rename `.env.example` to `.env` instead. That sounds easier, but which one is recommended, and what if I do both?

I open `.env.example` and it says to generate keys by opening `tools/rsa_keys.html`. There's no such file. There's `tools/rsa_key_generator.html`, so I guess that's it. I open it, it makes two blocks of text, and the .env wants them with newlines replaced by `\n`. Does the tool do that? I paste what I get and hope.

PASSWORD wants a hash from `password_hash(...)` or `php tools/generate_password.php`. I don't have PHP on my laptop. Can I do this on the host? Nothing says so. I'm stuck for an hour and finally find an online bcrypt generator. I don't know if that's compatible.

I rename the file to `.env`, but Windows complains and the cPanel file manager hides dotfiles. I can't tell whether `.htaccess` uploaded. Then I notice the .env.example is full of someone else's sample bio and profile fields. Do those go live if I don't delete them?

Minimum requirements say PHP 8.5. cPanel offers 8.2 and 8.3 only. Is 8.5 really required? I have no idea whether it will fail or just warn.

I visit `/.well-known/webfinger` and get a blank page or an error. The README says 'check that it shows a JSON file with your user's details' but doesn't show what that looks like or what to do if it doesn't. I give up for the day."

## Person 2: Marcus, an experienced sysadmin with an Ubuntu VPS running nginx and certbot

"I skim the README. Requirements look fine, but 'The OpenSSL Extension (This is usually installed by default.)' is all it says about extensions. README_nginx installs `php-curl`, so curl apparently matters too. Why isn't it in the requirements?

Page title: 'Using Nginx instead of Apache'. The main README never says Apache is assumed, so I'm now wondering what `.htaccess` is for.

`sudo apt-get install php php-curl` pulls in the default PHP and, on Debian and Ubuntu, Apache as well. That's the opposite of what I want. Then `sudo apt-get install php8.5-fpm` fails because stock Ubuntu doesn't ship 8.5, and no repository or PPA is mentioned. The 'php' I just installed is also a different version from the fpm package.

The nginx config listens on 80 only. The README says HTTPS is mandatory. No TLS block or certbot hint is given. I also need to know the site-enable step, `nginx -t`, and who owns the web root. The config has a commented-out note saying 'I don't THINK these are needed but computers are oh so very confusing', which doesn't inspire confidence. It also includes `fastcgi.conf` while the Docker doc uses `fastcgi_params`, so which is right?

The nginx doc never says where `index.php` and `.env` go beyond the `root` line, never mentions the writable `data` directory, and the 'to test the config' step uses `test.php` with `$_GET["path"]`. If the file exists, nginx serves it directly and `path` is unset, so I'd get an undefined-key warning and wouldn't know if that's good or bad. It also doesn't say to delete test.php afterward.

I get it running, but I had to guess about permissions for the web user writing `/data/logs`."

## Person 3: Dana, a homelab user running Docker Compose behind Traefik

"The README's requirements list says 'Docker, Node, MongoDB, ... (absolutely none of these!)', and then the FAQ says 'If you must' about Docker. Funny, but is Docker supported or not? I go to README_docker.md.

It says 'Rough Docker Instructions'. The compose snippet starts mid-file, with no `services:` header. The volume path `/path/to/your/docker/stuff/activity-bot/` is mounted to `/var/www/html/public`. Which files go in that folder: `index.php`, `.env`, `.htaccess`? Not said. The second mount is `activity-bot.conf`, but nothing says that this is the nginx config from the section below, and the section below has `server_name you.host.com` while the Traefik label has `your.host.com`. The `environment:` key has only a commented-out line, which leaves it empty. I'm not sure Compose accepts that. The Traefik comment says 'Internal port for postiz', which is copy-pasted from some other project.

I don't use Traefik. There is no `ports:` mapping and no TLS advice, so as written I can't reach the container or get HTTPS. The config is also 'a mixture' of two sources and I can't tell what is essential.

File ownership: the image runs as a non-root user, and nothing says the bot needs to write `data/` and posts folders. After starting, my first POST gives a 500 and I can't find logs because I don't know where `data/logs` is inside my mounted folder."

## Person 4: Wei, a JavaScript developer who wants to post from a GitHub Actions job (no Python)

"The setup works after a lot of poking, so now the API. 'All the examples here use Python 3 - but you can use whichever language you want.' Okay, but there's no curl or raw HTTP description: form-encoded or multipart? Which fields are required? I read the Python and infer `application/x-www-form-urlencoded`.

The example password is `your-password-here`. But the .env password is a hash that I generated with `password_hash`. So do I send the plaintext in POST and the server verifies against the hash? That's never said, and I almost paste the hash.

Posting works. I want to delete a test post: 'You will need the ID of your post'. Where do I get it? Nothing says it's returned in the response or visible somewhere. The Python examples don't print `r.status_code` or `r.text`, so I don't know what success looks like.

I try the location example. The values are `"longitude": 40.77563, "latitude": -73.97474`. That's the Lennon memorial, so the numbers are swapped. Longitude can't be 40.77 for New York. I send them as is and my pin lands in Asia.

For images the alt text is the filename slot of the tuple: `("1",("This is the alt text", open("red.png", "rb")))`. That's weird for any non-Python user, and the README never explains it. 'You can send HTML. Only formatting elements are allowed.' Which ones?

I also want to unfollow, block, or list followers. The feature list promises those, but the API section only shows Follow. I read the source instead."

## Person 5: Aisha, a developer who is moving followers from an old account, running Apache on a Raspberry Pi behind a tunnel

"I have Apache on a Pi, so the README matches. But `.htaccess` rewriting needs `mod_rewrite` and `AllowOverride All`, and neither is mentioned. My first request returns a 404 for everything. After enabling both, the paths work.

HTTPS is terminated by my tunnel, which is fine with 'HTTPS certificate' I guess.

I want to bring followers from my old account. 'Migrate Accounts' says to add an `OLD_NAME` to the `.env` file. The `.env.example` says it must be a full account URL, such as an https://.../users/name form, and the README doesn't repeat that. Then: 'Once your new ActivityBot is set up, go to your old account and follow its procedure for migrating away.' What procedure? It varies by server, and I need to know whether to call `/action/update` first.

The section for moving away is worse. 'Once your new acount is set up, go to your new account and follow its procedure for moving followers to it. Then you will need to send a Move request to your ActivityBot.' The example uses `"user": "@new@example.com"`, but `NEW_NAME` needs a full URL. Two formats for the same thing.

Also, I'm worried. The private key is in `.env` in the web root. Does `.htaccess` block it? The nginx configs deny `.env` and `data`, but the README never says Apache does, or how to verify that `https://.../.env` returns a 403 or 404. Same for `/data/followers` and `/data/inbox`."
=== CRITIQUE U8128 END ===

=== CRITIQUE U3141 START ===
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
=== CRITIQUE U3141 END ===

=== CRITIQUE U9207 START ===
1. The set-up text conflicts on where the configuration lives. `.env.example` says "Then rename this file to .env and upload it along with index.php and .htaccess", while the README says "Edit the `index.php` file to add a username, password, and keypair" and treats `.env` as an option ("If you prefer, you can rename `.env.example` to `.env`"). The README never says where in `index.php` the values go.
2. The README's set-up steps never mention generating a keypair or a password hash. That information exists only in `.env.example` and is not referenced from the README. The README also never explains what a keypair is for or that the identity depends on it, and never says to back up or protect the private key.
3. `.env.example` says "Generate locally by opening `tools/rsa_keys.html`", but the file listed in the repository is `tools/rsa_key_generator.html`. Neither document says whether the generator's output already has newlines escaped as `\n`, as the example requires.
4. The password flow is ambiguous. `.env` needs a hash ("Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`"), but every API example uses `"password": "your-password-here"` without saying that this is the plain password. Generating the hash assumes a local PHP install that is not listed in the requirements. The example also does not say how to quote a hash containing `$` characters.
5. "PHP 8.5 (We live in the future now.)" is a hard requirement most shared hosts cannot meet. It conflicts with the FAQ claim "everything supports PHP. You can FTP these files onto any host and be guaranteed they'll run." The README also never says that Apache with `mod_rewrite` and `.htaccess` overrides is required. Only the OpenSSL extension is listed, although README_nginx.md installs `php-curl`.
6. The README does not warn that `.env` and `.htaccess` are hidden dotfiles that FTP clients and file managers often hide or skip. It also does not say that `.env` and `data` must not be web-readable on Apache, or whether `.htaccess` handles that.
7. The numbered Set Up list starts at "0." and every following item is "1.", which renders as a confusing numbered list. Step "Optionally, upload an avatar and banner image" does not mention that `AVATAR`, `BANNER` and `FAVICON` in `.env` must be set to the file paths.
8. The webfinger check says only "check that it shows a JSON file with your user's details". It gives no example of expected output, no query string such as `?resource=acct:...`, and no troubleshooting advice if it fails. The README has no troubleshooting section at all.
9. "Check your `/data/logs/` directory" reads like an absolute path; it is relative to the web root. The "How this works" list mixes `/data/logs`, `/data/followers`, `/data/inbox` with `/posts` and `/quotes`, which sit outside `/data`. Nothing says that the web server's PHP user needs write permission to create them.
10. The README contradicts itself on receiving messages. The "doesn't do yet" list says "Receive messages (other than follows, unfollows, and quote requests)", but "How this works" says "Messages sent to your inbox are saved as .json in the `/data/inbox` directory."
11. The feature list advertises unfollow, block, unblock, show followers, view hashtags, quote posts and "Update profile information", but the API section documents only follow, move, send, delete, edit, update and a few options. The `action` values for the missing operations, the URL for viewing hashtags or followers, and how quote requests are handled are not documented.
12. The API section requires Python and Requests, plus `requests_toolbelt` for the Debugging snippet, which is not listed ("This assumes you have a modern version of Python and have installed the popular Python Requests library"). That sits oddly with the claim that people don't want to set up a Python VENV. No curl or language-neutral example is given. No response format or status codes are described, so the examples never show how to tell success from failure.
13. Several API details are unexplained. For `You will need the ID of your post:`, no source for the GUID is given. In the image examples the tuple's first value is alt text in one example and a bare colour name in another, and the numeric field names `"1"`, `"2"` are not explained. "You can send HTML. Only formatting elements are allowed." does not list which elements.
14. The location example appears to swap coordinates: `"longitude": 40.77563, "latitude": -73.97474`. The first value is a latitude and the second a longitude for the place named.
15. The Migrate section is confusing and inconsistent. It has the typo "acount". It tells users to go "to your new account" and then to "send a Move request to your ActivityBot". `.env.example` shows `NEW_NAME` as a full URL such as "https://new.example/users/username", but the example request uses `"user": "@new@example.com"`. The order of steps between old and new servers is unclear.
16. README_nginx.md installs software with `sudo apt-get install php php-curl` followed by `sudo apt-get install php8.5-fpm`. On common distributions `php8.5-fpm` is not in the default repositories and `php` pulls in Apache, which conflicts with nginx on port 80. Neither is mentioned. It also does not say where to save the config, how to enable the site, or to reload nginx. The config listens only on port 80 and gives no HTTPS step, even though HTTPS is a stated requirement.
17. The nginx page's test instructions ("make a file `test.php`" and "attempt to access it") do not state the expected output or tell the reader to delete `test.php` afterwards. They also do not say that `.htaccess` should be skipped on nginx. The deny rule `location ~ ^/(.env|data)` has an unescaped dot and does not cover `posts` or `quotes`. The comment "I don't THINK these are needed but computers are oh so very confusing" leaves readers unsure of the config's correctness.
18. README_docker.md is a fragment. The compose snippet has no `services:` parent, an `environment:` key containing only a comment, and a Traefik label comment "Internal port for postiz" copied from another project. It has no `ports:` for users without Traefik and no TLS instructions for them. The domain placeholders differ (`your.host.com` versus `you.host.com`).
19. README_docker.md never says where to save the nginx config for the bind mount `/path/to/your/docker/stuff/activity-bot.conf`, or what to put into the mounted `public` folder (`index.php`, `.env`, possibly `.htaccess`). It does not explain how this custom server block interacts with the image's built-in nginx configuration. The main README's requirements say "Docker ... (absolutely none of these!)", which conflicts with offering a Docker path.
20. The README's top-level framing is "a single PHP file - and an `.htaccess file`" (misplaced backticks). In practice the setup needs `.env` and key and password generation tools too. The `.env.example` comments warn "Logs can fill up *fast*... they can exhaust your file limits", while the FAQ answers "Will this fill up my disk?" with "Probably not." The two messages sit awkwardly together.
21. There is no local-testing path. Neither the README nor the other docs say whether the bot can be tried on localhost or without a public domain, or that federation requires a public HTTPS domain. The documents also say nothing about the identity being tied to the domain and `USERNAME`, so first-time users do not learn that changing either later could break the account.
=== CRITIQUE U9207 END ===
