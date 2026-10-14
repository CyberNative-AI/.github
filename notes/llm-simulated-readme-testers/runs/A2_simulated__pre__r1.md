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

## PROBLEMS

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
