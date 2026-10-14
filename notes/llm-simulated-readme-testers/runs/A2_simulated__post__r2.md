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

## PROBLEMS

1. The README never says how to obtain the files. The Quickstart says "Upload `index.php`, `.htaccess`, `.env.example` to your subdomain" but gives no download or clone instruction, and does not mention that `tools/` exists in the repo and is needed before upload.

2. The Quickstart and the Set Up steps disagree on order. The Quickstart says "Upload `index.php`, `.htaccess`, `.env.example`" then "Rename `.env.example` to `.env`", but Set Up says rename first and then "Upload `index.php`, `.htaccess`, and `.env`". Neither says whether to rename locally or on the server.

3. The Quickstart is misleadingly short. "Edit `.env` and follow the instructions inside it" hides the real prerequisites: generating an RSA key pair and a password hash, which need a browser tool and PHP.

4. "Generate locally by opening `tools/rsa_key_generator.html` on your computer" does not say where that file is relative to the upload, or whether the page produces keys that already have the newlines escaped. The comment "Newlines must be replaced with "\n"" leaves a non-technical user to convert multi-line keys by hand. No alternative such as an `openssl` command is given, and the example shows `BEGIN RSA PRIVATE KEY` headers whose required format is not explained.

5. Password generation assumes PHP is installed locally: "Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`" and "`php tools/generate_password.php 'Y0ur_p4s5w0rd'`". Users on shared hosting or Windows may have no local PHP, and the single-quote form fails in PowerShell. There is no browser-based or hosted alternative.

6. The `.env.example` text does not warn that a password hash contains `$` characters, which can be interpolated by some `.env` parsers, nor how to quote it in `PASSWORD=""`.

7. It is unclear what to put in the API's `"password"` field. `.env` holds a hash, while the examples use `"your-password-here"`. The README never says to use the original plaintext password rather than the hash.

8. The statement "The password is encrypted when you send it and never stored on your server" is misleading. The password is sent in the POST body, protected only by HTTPS, and the server stores a hash in `.env`. This blurs what protects the password.

9. The "Optional Fields" in `.env.example` are filled with live example values (for example `SUMMARY`, `BIRTHDAY`, `PROFILE_VALUE_3`, `PROFILE_VALUE_4` pointing at `https://example.com/tag/ActivityBot`). The file does not say what happens if a user leaves them, deletes the lines, or sets them blank, so people may publish a profile with someone else's links.

10. "`AVATAR`... Should be a relative URl without leading slash. For example "icon.jpg"" does not say relative to what, or where the image should be uploaded. Set Up step 8 ("upload an avatar and banner image... Edit `.env` to include the image locations") repeats the gap, and it doesn't mention running the "Update Account" call afterward so followers see the change.

11. Set Up step 2 says "If you prefer, you can edit `index.php` and place the details in there." It does not say which variables, in what format, or the security trade-off of keeping a private key in the script.

12. Dotfile handling is not addressed. `.env` and `.htaccess` are hidden or hard to rename in Finder, Windows Explorer and some FTP and file-manager tools, and the README gives no workaround.

13. "PHP 8.5 (We live in the future now.)" gives no guidance on how to check or select a PHP version on a host, or what happens on older versions. Most shared hosts and Linux distributions do not ship 8.5, and "This should include the following extensions by default" is vague, since cURL and OpenSSL availability differs by build. The cURL link points to a PHP 8.5 release-notes feature section, not install instructions.

14. The Raspberry Pi and "any modern web server" claim ("It will run on shared hosts, a Raspberry Pi") gives no guidance on home hosting: obtaining a domain or HTTPS certificate, port forwarding or dynamic DNS. "HTTPS certificate (Let's Encrypt is fine.)" says how to get one nowhere.

15. Apache prerequisites are missing. The README calls Apache "the default set up" but never says that `.htaccess` needs `mod_rewrite` and `AllowOverride`, nor whether `.htaccess` protects `.env` and `data/`. It never tells the user to check that `https://test.example.com/.env` is not publicly downloadable, even though the private key lives there.

16. The subdomain requirement is not explained. "Your account lives on *your* website's subdomain" and "It will not work in a subdirectory" leave open whether an apex domain or a dedicated domain works. The FAQ ("Every bot needs its own domain name") adds to the confusion.

17. The webfinger check is vague. "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details" gives no sample output and does not say whether the `?resource=acct:...` query is needed. It offers no help if the page returns an error.

18. "Check your `data/logs/` directory to see if the follow request was received correctly" does not say that this directory is created by the script at run time, that the web server user must have write access to it, or what a correct log entry looks like. Write permissions are only hinted at in README_caddy.md ("You may have to adjust the permissions...").

19. "Follow your user" assumes the reader already has a Fediverse account to search from and follow with. The Set Up never says that a fresh bot's posts only reach followers.

20. There is no troubleshooting section. Errors are not explained anywhere, including how to see PHP errors. `php_errors.log` appears only inside the Caddyfile.

21. Set Up ends at "check logs" and never shows a first post. The "Check it has worked" section says "Check social media to see if the message appears" without saying that a follower is needed first, and the Python examples never print `r.status_code` or `r.text`, so a user cannot tell success from failure.

22. The Python section's "Requirements" ("a modern version of Python and... the popular Python Requests library") gives no install command. The Debugging snippet uses `requests_toolbelt`, which is not listed. There is no `curl` example for non-Python users.

23. "You can send HTML. See `$allowed_elements` to see which ones are supported" refers to a variable inside `index.php` with no pointer to where it is or to a list.

24. The alt-text mechanism in "Post Images and Other Media" is undocumented. `files = [("1",("This is the alt text", open("red.png", "rb")))]` puts alt text where a filename would normally go, and the text never says so. The "multiple images" example uses the same position for the strings "red", "green" and so on without comment.

25. "Delete Post" and "Update / Edit Post" say "You will need the ID of your post", but there is no instruction for finding the `guid`.

26. The location example has latitude and longitude swapped: `"longitude": 40.77563, "latitude": -73.97474`. The place named, "John Lennon Memorial", is in New York, so 40.77 is the latitude and -73.97 the longitude.

27. The Features list promises "Unfollow accounts", "Block accounts", "Unblock accounts", "Allow quote posts", "Attach videos" and "Attach audio", but the API section has no example for unfollow, block, unblock or quote posts, and the media section only mentions audio and video in one sentence.

28. The "Migrate Accounts" text is confusing. "Once your new acount is set up, go to your new account and follow its procedure for moving followers to it" uses "new account" for two different things. The `.env.example` asks for a full URL in `NEW_NAME` (`https://new.example/users/username`) but the API example uses `"user": "@new@example.com"`, and the two formats are not reconciled. There is also a typo, "acount".

29. The Docker instructions are incomplete and have copy-paste errors. The compose fragment has no `services:` header, no `ports:` mapping for users without Traefik, and an `environment:` key with only a commented-out value. The comment "Internal port for postiz" refers to another project, and the hostnames `your.host.com` and `you.host.com` differ. It doesn't say where `index.php`, `.htaccess` and `.env` go inside the mounted directory, and says nothing about how TLS works without Traefik.

30. The Docker nginx config says it is "a mixture of the nginx config from README_nginx.md and the documentation from ServerSideUp" but doesn't list the differences, such as `fastcgi_pass 127.0.0.1:9000` against a socket. It does not say whether it replaces or collides with the image's default server, and does not cover file ownership for `data/` in the container.

31. The nginx and Caddy pages install PHP in a way that can fail. `sudo apt-get install php php-curl` commonly pulls in Apache on Debian and Ubuntu, `php8.5-fpm` is not in standard repositories (no PPA or repo is mentioned), the OpenSSL extension is not listed, and the socket path `/var/run/php/php8.5-fpm.sock` is hard-coded to one version.

32. README_nginx.md only has `listen 80;`, although the main README requires HTTPS. It does not say where to put the config, how to test it (`nginx -t`) or reload, and does not say how to continue with the main Set Up afterward. The comment "I don't THINK these are needed but computers are oh so very confusing" leaves the user unsure which commented lines to enable. The block is labelled `bash` rather than `nginx`.

33. The Caddyfile blocks `/.env` and `/php_errors.log` but not `/data`, whereas the nginx pages block `^/(.env|data)`. A Caddy user can leave log files public. The nginx rule is also an unescaped regex that matches any path starting with `/env` or `/data`, such as `/database`.

34. The "To test the config" step in README_nginx.md and README_caddy.md has no expected output. `$_GET["path"]` is undefined when `test.php` is visited directly, so the user sees a PHP warning and can't tell success from failure. Nothing tells them to delete `test.php` afterwards, and the Caddy page does not link back to the main Set Up steps.

35. The structure and wording have small errors that cost trust. "Set Up" is a sub-heading of "Minimum Requirements". The list numbering runs "0." then "1." repeatedly. "Lenny" appears in the Introduction, probably meaning Lemmy. "URl", "URls" and "acount" appear as typos. In `.env.example`, one comment uses `#` rather than `#;` ("#	This is the joined date of your bot."), and `MAX_LOGS=2048` is unquoted while `PAGE_SIZE="1000"` is quoted, with no explanation.

36. The AI policy FAQ says "AI was not used at any stage... LLMs were not used to write, design, or test anything", but the repository file list includes `AGENTS.md`, a file normally used to instruct AI coding agents. I could not see its contents, so this may be a legitimate or stale file, but the apparent conflict should be checked or explained.
