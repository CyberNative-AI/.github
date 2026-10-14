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

# PROBLEMS

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
