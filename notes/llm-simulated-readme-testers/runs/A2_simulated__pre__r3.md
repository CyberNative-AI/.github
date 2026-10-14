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

# PROBLEMS

1. The README never says where to get the software (clone, zip, release page). The only repository link appears in `.env.example` and the Feedback section.
2. The PHP requirement "[PHP 8.5](https://www.php.net/releases/8.5/en.php) (We live in the future now.)" gives no minimum that is really needed, no fallback for hosts stuck on older PHP, and no way to check what version the host offers.
3. The requirements list only "The OpenSSL Extension", but `README_nginx.md` installs `php-curl` as well, and nothing says which extensions the code actually needs. It also never states that Apache with `mod_rewrite` and `.htaccess` overrides is required (the nginx page's title, "Using Nginx instead of Apache", is the only hint).
4. The joke requirement "Docker, Node, MongoDB, Wayland, GLaDOS, React, LLM, Adobe Creative Cloud, Maven (absolutely none of these!)" contradicts the FAQ that offers a Docker setup, and some readers will not know it is a joke.
5. The Set Up list is numbered "0." then "1." repeatedly, so the steps cannot be referred to or counted, and starting at 0 is confusing.
6. Step 0, "Set up a new sub-domain on your web host and make sure it has an HTTPS certificate.", gives no instructions for creating the subdomain, DNS records, pointing its document root, or getting the certificate. It also does not say whether the bot can live on a main domain.
7. "Upload `index.php` and `.htaccess` to the *root* directory of your domain... It will not work in a subdirectory." is ambiguous on shared hosting, where a new subdomain's document root is often a folder inside another site, and "root directory" is never defined.
8. "Edit the `index.php` file to add a username, password, and keypair." does not say which lines to edit, what format each value takes, or how to produce a keypair. It also offers the `.env` option without saying which one wins or which is recommended.
9. The README never mentions the helper tools in `tools/`, so a reader of the main steps does not learn that key and password generators exist or whether the `tools/` directory should be uploaded.
10. `.env.example` says "Generate locally by opening `tools/rsa_keys.html`", but the file in the repository is `tools/rsa_key_generator.html`.
11. 'Newlines must be replaced with "\n"' does not say how, with what tool, or whether the generator page already outputs the single-line form. It also does not say which key format (the example shows "BEGIN RSA PRIVATE KEY") the generator produces or the code expects, nor warn that the private key must be kept secret and backed up.
12. The password instructions ("Generate with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );`" or `php tools/generate_password.php 'Y0ur_p4s5w0rd'`) assume PHP on the local machine and POSIX quoting, give no non-PHP alternative, and never say that the hash goes in the config while the plain password goes in the API calls ("your-password-here"). They also do not say whether `$` characters in a hash need single quotes in `.env`.
13. The files `.env` and `.htaccess` are dotfiles that Finder, Explorer and many FTP clients hide, and the README never warns about this, how to rename `.env.example` on those systems, or how to confirm they uploaded.
14. "Optionally, upload an avatar and banner image to make the user look nice." does not say where to put them, what to name them, or that the `AVATAR`, `BANNER` and `FAVICON` values in `.env` must be set to relative paths (and the size and format limits are only in `.env.example`).
15. Step 5, "Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details.", shows no example of correct output and does not describe failure symptoms or how to diagnose them.
16. Steps 6 and 7 ("search for your user: `@username@test.example.com`", "Follow your user.") do not say whether the bot auto-accepts, what to expect if the search finds nothing, or that remote servers may cache or reject a first lookup.
17. Step 8, "Check your `/data/logs/` directory to see if the follow request was received correctly.", does not say how to view it (FTP, SSH), what a good log looks like, or what to do if it is empty. It never mentions that PHP needs write permission to create `/data`, `/posts` and `/quotes`, which is a common failure on shared hosts, nginx and Docker.
18. "How this works" saves posts to `/posts` and quotes to `/quotes` but followers, inbox and logs under `/data/...`, with no explanation of the inconsistent locations. The README also does not say whether `/data` and `.env` are protected from download under Apache, or how to test that.
19. The inbox is stored ("Messages sent to your inbox are saved as .json in the `/data/inbox` directory."), yet the feature list says "Receive messages (other than follows, unfollows, and quote requests)" is not supported and the FAQ is titled "Why doesn't this store replies?", so it is unclear what is stored.
20. Several advertised features have no usage section at all: "Unfollow accounts", "Block accounts", "Unblock accounts", "Show followers", "Allow quote posts", "View hashtags posted by the bot", and "Bridge to BlueSky with your domain name via Bridgy Fed" (only a `DID` field in `.env.example`). The full list of endpoints and fields is not given.
21. The API section says "This assumes you have a modern version of Python and have installed the popular Python Requests library" with no install command and no curl or other-language example, and the Debugging snippet's `from requests_toolbelt.utils import dump` needs a separate package not mentioned.
22. The API examples never show or describe the response (`r` is not printed), so a user cannot tell success from failure. "Check social media to see if the message appears." only works once someone follows the bot, which is not stated.
23. The Delete and Update/Edit sections say "You will need the ID of your post:" but never say where the `guid` can be found (response, log, URL, or the site). The edit example posts to `action/send` with a `guid`, the same endpoint as a new post, without explaining that.
24. The location example, `"longitude": 40.77563, "latitude": -73.97474`, has the values swapped: 40.77563 is the latitude and -73.97474 the longitude of that place, so copying it puts the pin in the wrong spot.
25. "You can send HTML. Only formatting elements are allowed." does not list which elements are allowed. Meanwhile the feature list says "Accurate support for converting user's text to HTML" is missing, without explaining the effect on plain text posts.
26. The Migrate Accounts section is vague. "go to your old account and follow its procedure for migrating away" gives no concrete steps, the `OLD_NAME` and `NEW_NAME` URL formats appear only in `.env.example`, the text mixes "new account" for different things, and it contains the typo "Once your new acount is set up".
27. The Licence section says "if you modify this code and let other people interact with it over a computer network, you must release the source code", while Step 1 tells users to edit `index.php` with their private key and password. The README does not warn against publishing that file or recommend `.env` for secrets, and it does not clarify what counts as modification.
28. `README_nginx.md` begins with `sudo apt-get install php php-curl`, which typically installs the default PHP version (and may pull in Apache) before a separate `php8.5-fpm` install. It does not say that 8.5 packages may need a third-party repository, nor tell the user to install nginx.
29. The nginx example uses only `listen 80;` and the Requirements demand HTTPS, with no TLS or certbot guidance. It also omits where to put the config, reloading nginx, the `root` directory contents to upload (including whether `.htaccess` is still needed) and file ownership for writable data.
30. The nginx test ("make a file `test.php`... attempt to access it on test.example.com/test.php.") does not exercise the rewrite rule, does not say what output means success, and leaves a script that echoes `$_GET["path"]` unescaped, without telling the user to delete it. The comment "I don't THINK these are needed but computers are oh so very confusing" leaves the reader unsure about the correct config.
31. `README_docker.md` gives a fragment, not a full compose file, and never says which files go into the mounted `/var/www/html/public` folder. It never says to save the "nginx config" block as `activity-bot.conf`, which the second volume expects.
32. The Docker page has inconsistent or copy-pasted values: `you.host.com`, `your.host.com` and `test.example.com` for the same placeholder, and the comment "Internal port for postiz" in a ActivityBot config. It also gives no way to get HTTPS without Traefik and does not mention write permissions for the container user on the mounted folder.
