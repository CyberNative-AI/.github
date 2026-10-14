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

# PROBLEMS

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
