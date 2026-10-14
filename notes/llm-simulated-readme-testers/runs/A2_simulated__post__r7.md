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

# PROBLEMS

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
