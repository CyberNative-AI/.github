## Five simulated users following the README

### 1. Priya, hobbyist, cheap shared cPanel hosting (Apache), no command-line experience

"A bot on the Fediverse that posts one poem a day. Nice. The feature list is long and cheerful. I skim to find where to start... there's a heading called 'Minimum Requirements' and then, inside it, 'Set Up'. Odd place for it, but fine."

"PHP 8.5, 'We live in the future now.' Ha. How do I know what my host runs? It doesn't say. I look in cPanel: the highest option is 8.3. Am I stuck? Is 8.3 okay? Nothing says what actually breaks on an older version, and nothing says how to check."

"Step 0: a subdomain. Done, and the HTTPS certificate appears after a while. Step 1: 'Edit the `index.php` file to add a username, password, and keypair.' Where in the file? I open it and it's thousands of lines. Alternatively rename `.env.example` to `.env`. That sounds easier. But the repo hasn't told me how to get the files in the first place. Git clone? Download ZIP? I click around GitLab until I find a download button."

"I open `.env.example`. It says to generate keys by opening `tools/rsa_keys.html`. There's no such file; there's `tools/rsa_key_generator.html`. I guess. It generates keys. The file says 'Newlines must be replaced with "\n"'. Does the tool already do that? I paste the key into the file and it's multi-line, so I hand-edit 27 lines into one, hoping I got it right."

"Password: 'Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`' or run `php tools/generate_password.php`. I don't have PHP on my laptop. Is there a web page for this? No. I give up and put my plain password into PASSWORD. Probably wrong, but nothing tells me it would be."

"Rename `.env.example` to `.env`. Windows Explorer complains about a name with no base name. cPanel's file manager hides dotfiles, so I can't even see `.htaccess` or `.env` after uploading until I find a 'show hidden files' checkbox. Nothing in the README warns me."

"Upload to 'the *root* directory of your domain.' Is that my home folder, `public_html`, or the folder cPanel made for the subdomain? I upload to `public_html` and nothing happens on the subdomain because it points at a different folder."

"After I fix that, I visit `/.well-known/webfinger` and get an error. Is that failure or normal? The README says it should show 'a JSON file with your user's details' but not what that looks like, and doesn't say it might need a `?resource=` query. I have no troubleshooting section, and I can't see logs because I don't know if PHP errors are shown."

### 2. Marcus, sysadmin, Ubuntu VPS, nginx, comfortable with the shell

"I'll skip Apache. The FAQ says 'Can I use nginx? Sure, read README_nginx.md.' Fine. The requirement list says PHP 8.5 and the OpenSSL extension. The nginx doc says `sudo apt-get install php php-curl` then `php8.5-fpm`. Wait, curl was never mentioned as a requirement. And Ubuntu's own repos don't have 8.5. Do I need the Sury PPA? Not mentioned. Also the `php` metapackage drags in Apache on Debian and Ubuntu, which will fight nginx for port 80. The doc doesn't warn me."

"The nginx config: it listens on port 80 only. I need HTTPS (the main README insists on it) but there's no `listen 443 ssl` or certbot hint. Where does this file go: sites-available? conf.d? Do I symlink and reload? It isn't said. The `map` block is at the top, outside `server`, which only works in `http` context. I know that, but a less experienced person would not."

"In the PHP block: 'I don't THINK these are needed but computers are oh so very confusing'. Not exactly reassuring; I can't tell whether `include fastcgi.conf` is right on my distro, and the socket path `/var/run/php/php8.5-fpm.sock` is distro specific."

"Test step: 'to test the config, make a file `test.php`'... and 'attempt to access it on test.example.com/test.php.' Where do I make it? What should I see? It doesn't say, and doesn't say to delete it after. Then I look at the main README's setup step 'Check your `/data/logs/` directory' and notice the 'How this works' list puts logs in `/data/logs` but posts in `/posts` and quotes in `/quotes`, not under `/data`. The nginx config denies `.env` and `/data` but serves `/posts`. Is that deliberate? Which directories need to be writable by the php-fpm user? Nothing says. I run it and the follow request fails silently because the web user can't create `data/`."

### 3. Dana, non-technical illustrator, Windows, FTP-only budget host

"I read the feature list: avatar, banner, content warnings. Lovely. Requirements: 'Docker, Node, MongoDB, Wayland, GLaDOS... (absolutely none of these!)' I don't know most of those, and I can't tell which jokes are real requirements. Then the FAQ says 'Because I hate you and want you to suffer.' Is this person angry at me? I'd like warmer words for a first-timer."

"The setup uses 'sub-domain', 'webfinger', 'keypair', 'root directory'. No definitions. Step 4 says 'Optionally, upload an avatar and banner image to make the user look nice.' Upload where, and under what name? `.env.example` says set `AVATAR` to a 'relative URl without leading slash'. But the README step doesn't mention setting that. I upload `avatar.png` and my bot still has the default image."

"I fill `.env`, keep the quotes, and leave the line `#	This is the joined date of your bot.` untouched. That line is the only comment that begins `#` instead of `#;`. If the file is parsed in an INI style, I imagine this could be read as a setting or cause an error. I can't know, and nothing says which comment style is safe."

"I get to 'Follow your user' on a Mastodon account and then 'Check your `/data/logs/` directory'. I only have FTP; the folder isn't there. Maybe it appears later? Maybe permissions? There's no 'what you should see', and no 'if nothing is there, try this'."

### 4. Tomas, homelab person, Docker and Traefik, comfortable with compose

"README_docker.md is titled 'Rough Docker Instructions.' OK, I'll adapt. The compose snippet mounts a folder to `/var/www/html/public` and an nginx conf to `/etc/nginx/conf.d/activity-bot.conf`. The nginx block below doesn't say 'save this as activity-bot.conf'; I infer it. It does say 'This is a mixture of the nginx config...' but it never says that this is the file to mount."

"The compose snippet has `environment:` followed only by a commented-out line. Empty key. Will compose accept it? I'll delete it. The label says '# Internal port for postiz', which is copied from another project and confuses me for a moment. 'Optional Traefik config, ymmv' leaves me to guess: `entrypoints: web-secure` and `certresolver: letsencrypt` are names from the author's own setup, not mine. If I don't use Traefik there's no `ports:` mapping, so 8080 isn't reachable at all, and no TLS advice."

"The nginx block says `# Default server definition` and `listen 8080`. The serversideup image already ships its own default server on 8080. Will mine conflict? Not explained. Placeholders also drift: `your.host.com` in compose and `you.host.com` in the nginx block, `test.example.com` everywhere else."

"No `docker compose up -d` command, no word on where `index.php`, `.htaccess`, and `.env` go in the mounted directory, and no note on file ownership. The image runs as an unprivileged user, so writing `data/` into my bind mount will fail unless I chown. I find that out from an empty log folder. Also `.htaccess` is pointless under nginx, which isn't said."

### 5. Aiko, Python data engineer, Raspberry Pi at home behind a Cloudflare tunnel, Apache

"I mostly want the API. Setup first. PHP 8.5 on Raspberry Pi OS: not available in the stock repo, no pointer. I get it from a third-party source. Apache needs `mod_rewrite` and `AllowOverride All` for `.htaccess` to do anything. The Minimum Requirements list says PHP, OpenSSL, HTTPS, disk. It never says Apache, `mod_rewrite` or `AllowOverride`, and the nginx file's title only hints at it ('instead of Apache'). Without it, every route 404s."

"Now the API. 'This assumes you have a modern version of Python and have installed the popular Python Requests library.' Which Python version? No `pip install requests`. The examples all say `"password": "your-password-here"`. Is this the plain password or the hash I put in `.env`? I assume plain. It's never stated. The examples don't print `r.status_code` or `r.text`, so after the post call I don't know whether it worked. 'Check it has worked' says to look at social media or visit the site root."

"The debug snippet imports `requests_toolbelt`, which isn't in the requirements. The location example: `"longitude": 40.77563, "latitude": -73.97474`. Those numbers are the other way round; 40.77 N, -73.97 is New York, which is latitude 40.77 and longitude -73.97, so I'd be pinning a post to Antarctica without any validation error (both numbers are valid in either field). The edit example says 'You will need the ID of your post' but not where to find the guid, and it posts to `/action/send` while delete uses `/action/delete`."

"Migration: 'Once your new acount is set up' (typo), and `NEW_NAME` is a 'full account URl' like `https://new.example/users/username`, but the Move request uses `"user": "@new@example.com"`. Different formats for the same account; I have to guess whether either is accepted. And the feature list advertises unfollow, block, unblock, show followers, quote posts, and viewing hashtags, but the API section only documents follow and move, so I can't tell the parameter names."

---

## PROBLEMS

1. **No instructions for obtaining the software.** The Set Up section starts at "0. Set up a new sub-domain" and never says how to get the files (clone, ZIP, release), which files to upload, or whether `tools/` and `tests/` should be uploaded.

2. **PHP 8.5 requirement is not actionable.** "[PHP 8.5](https://www.php.net/releases/8.5/en.php) (We live in the future now.)" gives no way to check the host's version, no statement of what fails on older PHP, and no guidance on obtaining 8.5 on common hosts, Debian/Ubuntu or a Raspberry Pi. The nginx doc's `sudo apt-get install php php-curl` and `sudo apt-get install php8.5-fpm` assume a repository that stock distributions do not provide.

3. **Requirements are incomplete and inconsistent.** The list names PHP and "The [OpenSSL Extension]" only, but README_nginx.md installs `php-curl`. It also never states that the Apache path needs Apache, `mod_rewrite`, and `AllowOverride` so that `.htaccess` is honoured, and it does not say what to do on LiteSpeed or other hosts.

4. **Joke requirement line hides real information.** "Docker, Node, MongoDB, Wayland, GLaDOS, React, LLM, Adobe Creative Cloud, Maven (absolutely none of these!)" mixes real tools with jokes, and Docker is then offered as an option in the FAQ. Newcomers cannot tell which items are jokes, and the tone of "Because I hate you and want you to suffer" may put off non-technical readers.

5. **Setup instructions are buried under the wrong heading and numbering.** "### Set Up" sits inside "## Minimum Requirements", after a long feature list, and the steps are numbered "0." then repeated "1." items. The reader cannot tell the true step order or count.

6. **Step 1 does not say where or how to edit `index.php`.** "Edit the `index.php` file to add a username, password, and keypair." does not name the variables or location in the file, and does not say which source wins if both `index.php` and `.env` are populated.

7. **README never explains how to generate keys or the password.** The key and password tools are mentioned only in `.env.example`; the Set Up steps do not link to `tools/rsa_key_generator.html` or `tools/generate_password.php`.

8. **Wrong filename for the key generator.** `.env.example` says "Generate locally by opening `tools/rsa_keys.html`", but the repository file is `tools/rsa_key_generator.html`.

9. **Key formatting is unclear.** "Newlines must be replaced with "\n"" does not say whether the generator tool does this automatically, or how to do it by hand for a 27-line key.

10. **Password generation requires local PHP, and the API password type is ambiguous.** "Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`" and `php tools/generate_password.php` assume a PHP CLI that many shared-hosting users lack. The README never states that `.env` holds a hash while the API examples' `"password": "your-password-here"` must be the plain password, and gives no advice on quoting a hash containing `$`.

11. **Inconsistent comment syntax in `.env.example`.** Nearly every comment starts with `#;`, but the line `#	This is the joined date of your bot.` starts with `#` only, which may be parsed differently if the file is read INI-style. There is no statement of the file format or parser rules.

12. **Dotfile handling is not addressed.** Instructions to rename `.env.example` to `.env` and upload `.htaccess` do not warn that Windows, cPanel and FTP clients hide or reject dotfiles.

13. **Ambiguous deployment directory.** "Upload `index.php` and `.htaccess` to the *root* directory of your domain. For example `test.example.com/`." does not say that this means the document root configured for the subdomain, which is often a different folder from the account home or `public_html`.

14. **Secrets protection not explained or verified.** The README never says that `.htaccess` is what stops `.env` and `/data` being downloaded, or how to test that. The private key lives in a web-root file. The nginx files add a deny rule, but there is no check step.

15. **Writable directories and permissions are not mentioned.** The bot has to create `/data/logs`, `/data/followers`, `/data/inbox`, `/posts`, and `/quotes`, but nothing says the web user needs write access or whether the folders are auto-created. This is likely to bite Docker bind mounts and VPS users.

16. **Inconsistent directory layout.** "Log files are saved as .txt in the `/data/logs` directory." and "Post files are saved as .json in the `/posts` directory." and "`/quotes` directory" put some data under `/data` and some at the top level, with no explanation, and `/posts` is publicly served while `/data` is blocked.

17. **Avatar and banner step is incomplete.** "Optionally, upload an avatar and banner image to make the user look nice." does not say where to put them, what filename to use, or that `AVATAR`/`BANNER`/`FAVICON` in `.env` must be set to the relative path.

18. **Webfinger check lacks expected output and the right URL.** "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details." gives no sample output, does not mention the `resource` query parameter normally used, and offers no troubleshooting for 404, blank page or 500.

19. **Placeholders are not mapped to the user's values.** `@username@test.example.com`, `test.example.com`, and `"your-password-here"` are never tied explicitly to the `USERNAME` setting, the user's own subdomain, and their password, and in Docker docs the placeholders vary (`your.host.com`, `you.host.com`).

20. **Follow-and-log verification is unreachable or vague.** "Check your `/data/logs/` directory to see if the follow request was received correctly." assumes file access, does not say what a correct entry looks like, and gives no guidance for failure (no follow arrives, signature fails, no log directory).

21. **No troubleshooting section anywhere.** There is no guidance on enabling PHP error display, reading Apache/nginx error logs, or the usual causes of failure (rewrite not active, wrong document root, permissions, PHP version, HTTPS issues).

22. **API prerequisites are vague.** "This assumes you have a modern version of Python and have installed the popular Python Requests library" has no minimum version or install command. The debugging snippet's `from requests_toolbelt.utils import dump` needs another package that is not listed.

23. **API examples do not show success or failure.** None of the snippets print `r.status_code` or `r.text`, and the docs never describe the expected response, so users cannot tell if the call worked. "Check it has worked" only suggests checking social media or the site root.

24. **Location example has latitude and longitude swapped.** `"longitude": 40.77563, "latitude": -73.97474` uses New York's latitude as longitude and vice versa. Both values are valid in either field, so no validation error will reveal it.

25. **Post IDs are not explained.** "You will need the ID of your post:" (delete and edit) does not say where to find the `guid`, and the edit example posts to `/action/send` while delete uses `/action/delete` without noting the difference.

26. **Media upload format is opaque.** `files = [("1",("This is the alt text", open("red.png", "rb")))]` hides alt text in the filename slot without saying so, and there are no file-type, size, or count limits beyond the final paragraph about servers.

27. **Many advertised features have no usage documentation.** The feature list claims unfollow, block, unblock, show followers, quote posts, hashtag views, and profile updates (partly), but the API section documents only post, follow, DM, media, delete, edit, content warning, reply, hashtags, location, update, and move.

28. **Account migration instructions are inconsistent and incomplete.** `OLD_NAME`/`NEW_NAME` are described in `.env.example` as a "full account URl" (e.g. `https://new.example/users/username`), but the Move request uses `"user": "@new@example.com"`. The text has a typo ("acount") and does not say that the new account must set an alias first.

29. **Docker guide is not a runnable procedure.** README_docker.md lacks a `docker compose up` command, does not say to save the nginx block as `activity-bot.conf`, does not say where `index.php`, `.htaccess` and `.env` go in the mounted directory, and does not mention ownership or permissions for the container user.

30. **Docker compose snippet has copy-paste leftovers and gaps.** "# Internal port for postiz" is from another project, `entrypoints: web-secure` and `certresolver: letsencrypt` are setup-specific, "ymmv" leaves non-Traefik users without a `ports:` mapping or TLS plan, and `environment:` is left with only a commented-out line.

31. **Docker nginx block may conflict with the image's own default server.** "# Default server definition" with `listen 8080` is mounted into `conf.d` without saying whether it replaces or collides with the image's built-in site config.

32. **nginx guide omits installation context.** README_nginx.md does not say where the config file goes, how to enable and reload it, or how to add HTTPS (the config only has `listen 80`). `sudo apt-get install php php-curl` also pulls in Apache on Debian/Ubuntu, which can clash with nginx, and the guide does not warn about it.

33. **nginx comment undermines confidence in a required directive.** "I don't THINK these are needed but computers are oh so very confusing" leaves the user unsure whether the commented-out `fastcgi_params` and related lines matter, and `/var/run/php/php8.5-fpm.sock` is distribution-specific.

34. **nginx test step is incomplete.** "to test the config, make a file `test.php`" does not say where to create it, what output to expect, or that it should be deleted afterwards.

35. **No guidance on local testing or HTTPS prerequisites.** The docs require a public HTTPS subdomain but give no way to try the bot locally before going live, no note about stability of the domain and keys (changing either later breaks the account's identity), and no backup advice.

36. **Tone and wording create friction for first-time readers.** Sentences like "Because I hate you and want you to suffer." and "Dunno. Try it and find out." in the FAQs, plus undefined terms (sub-domain, webfinger, keypair, root directory), make the docs harder for non-experts, and the "Check it has worked" section sits inside the API chapter instead of the setup path.
