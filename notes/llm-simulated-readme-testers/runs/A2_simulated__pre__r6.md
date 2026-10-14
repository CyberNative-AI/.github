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

# PROBLEMS

1. There is no instruction on how to obtain the software. The Set Up section starts with hosting and then 'Edit the `index.php` file...' without saying where to download or clone it. The repository link appears only under 'Feedback' and inside `.env.example`.

2. Credentials can go in two places, with no recommendation or precedence rule: 'Edit the `index.php` file to add a username, password, and keypair.' and 'If you prefer, you can rename `.env.example` to `.env` and place the details in there.' The README does not say how to edit `index.php` (which variables), nor what happens if both are set.

3. The README Set Up never mentions generating the key pair or the password hash. Those tools are named only in `.env.example`, so a reader following only the README doesn't know what a keypair is or where to get one.

4. `.env.example` points to a file that does not exist: 'Generate locally by opening `tools/rsa_keys.html`'. The file in the repository is `tools/rsa_key_generator.html`.

5. The `.env` key format is unclear: 'Newlines must be replaced with "\n"'. It doesn't say whether the key generator tool already does this, or how to do it by hand.

6. The password flow is not explained. `.env.example` says PASSWORD must be generated with `password_hash( "Y0ur_p4s5w0rd", PASSWORD_DEFAULT );` while every API example sends `"password": "your-password-here"`. Nothing says you send the plaintext password to the API and store only the hash in the config.

7. Generating the password hash assumes a local PHP command line ('php tools/generate_password.php'), which hosting-only or Windows users may not have. No alternative is offered, and the README never lists it as a prerequisite.

8. The requirement 'PHP 8.5 (We live in the future now.)' is not available on many shared hosts or stock distributions. The README says nothing about how to check the PHP version, whether older versions work, or where to get 8.5 (README_nginx's `sudo apt-get install php8.5-fpm` also does not mention a repository).

9. Requirements are incomplete. Only the OpenSSL extension is listed ('This is usually installed by default.'), but README_nginx installs `php-curl`, and the Debugging section needs `requests_toolbelt`. The README doesn't list required PHP extensions, nor Apache `mod_rewrite` and `AllowOverride` for `.htaccess` to work.

10. The main README never says it assumes Apache. It talks about `.htaccess` only, while README_nginx.md is titled 'Using Nginx instead of Apache'. A reader on another web server won't know until they reach the FAQ.

11. The line 'Docker, Node, MongoDB, Wayland, GLaDOS, React, LLM, Adobe Creative Cloud, Maven (absolutely none of these!)' is under 'Minimum Requirements' and contradicts the FAQ that offers Docker instructions. A joke in a requirements list makes it unclear whether Docker is supported.

12. `.htaccess` and `.env` are hidden dotfiles that many FTP clients, file managers, and Windows Explorer hide or refuse to rename. The README says 'rename `.env.example` to `.env`' and 'Upload `index.php` and `.htaccess`' with no warning about this.

13. `.env.example` ships with sample values (REALNAME, SUMMARY with a link to the author's repository, BIRTHDAY, PROFILE_NAME_1 to PROFILE_VALUE_4, and USERNAME="example"). The README doesn't say that these will appear on the live profile unless edited or blanked.

14. Setup step on avatar and banner is incomplete: 'Optionally, upload an avatar and banner image to make the user look nice.' It doesn't say that the `AVATAR` and `BANNER` settings must be filled in with a relative path, nor the size limits that are documented only in `.env.example`.

15. The root-directory instruction is ambiguous: 'Upload `index.php` and `.htaccess` to the *root* directory of your domain... It will not work in a subdirectory.' On shared hosts the subdomain's document root may be a subfolder or `public_html`. The README doesn't say to point the subdomain's document root at the upload folder, or whether a bare domain works.

16. The webfinger check is not verifiable: 'Visit `https://test.example.com/.well-known/webfinger` and check that it shows a JSON file with your user's details.' No example output is shown, and real WebFinger lookups normally need a `resource` parameter. There is no guidance for what to do on a blank page, 404, or 500.

17. The search step uses a placeholder handle: 'search for your user: `@username@test.example.com`'. It doesn't say that `username` is the `USERNAME` setting, nor that the domain must be exactly your subdomain.

18. Directory and permission information is missing. 'Check your `/data/logs/` directory to see if the follow request was received correctly' never says the directory is created automatically, whether the web user must be able to write to it, or what a correct log looks like. It also gives no troubleshooting for the common failure where nothing is logged.

19. The "How this works" list uses inconsistent paths: `/data/logs`, `/data/followers`, `/data/inbox` but `/posts` and `/quotes` with no `/data` prefix. Readers can't tell which folders must be writable, or which to protect.

20. The README does not say that `.env`, `data/`, and the private key are protected on Apache, or how to verify that. The nginx configs deny `.env` and `data` explicitly, but the Apache path is silent, and the private key sits in the web root.

21. The README mentions inbox storage: 'Messages sent to your inbox are saved as .json in the `/data/inbox` directory.' This conflicts with the feature list ('Receive messages (other than follows, unfollows, and quote requests)' is not supported) and with the FAQ 'Why doesn't this store replies?'.

22. The API section is Python-only: 'All the examples here use Python 3 - but you can use whichever language you want'. There is no curl example and no description of the endpoint, field names, or content type for other languages. The Requirements text assumes `requests` is installed without showing how.

23. API examples never show or explain the response (status code, body, returned post ID or URL). Readers can't tell success from failure, except by 'Check social media'.

24. Delete and edit say 'You will need the ID of your post' without saying where to find the `guid` (response, website, log, or file name).

25. The 'Add a Location' example has the coordinates swapped: `"longitude": 40.77563, "latitude": -73.97474, "place": "John Lennon Memorial"`. 40.77 is the latitude and -73.97 the longitude for that place.

26. Alt text for images is passed in the filename slot of the files tuple (`("1",("This is the alt text", open("red.png", "rb")))`) with no explanation. The multi-image example uses names such as "red" and doesn't say whether those are alt text. File size and format limits are not given, and the files are never closed.

27. 'You can send HTML. Only formatting elements are allowed.' doesn't say which elements.

28. Features in the list have no usage instructions: unfollow, block, unblock, showing followers, viewing hashtags, quote posts, audio/video specifics ('in the same way'), and bridging to Bluesky (only a `DID` field appears in `.env.example`). Only Follow, Move, and a few posting options are documented.

29. The migration instructions are vague and inconsistent. 'follow its procedure for migrating away' and 'Once your new acount is set up, go to your new account...' are unspecific (and contain a typo). The Move example uses `"user": "@new@example.com"` while `NEW_NAME` requires a full account URL. It doesn't say whether `/action/update` is needed afterward.

30. The Update Account section says changes to the profile need an update call, but Set Up never mentions it, so someone who edits `.env` after the first follow won't know to run it.

31. The README_nginx instructions are fragmentary: 'requires php8.5-fpm which is a thing that passes requests to PHP'. `apt-get install php php-curl` may install Apache and a different PHP version. There is no TLS or certbot guidance (the config has only `listen 80;`), and no site enabling, `nginx -t`, reload, or file ownership steps.

32. The nginx config includes uncertain advice: 'I don't THINK these are needed but computers are oh so very confusing'. It uses `include fastcgi.conf`, while README_docker uses `include fastcgi_params`. The reader can't tell which approach is correct.

33. The nginx test step is under-specified: 'to test the config, make a file `test.php`'. It doesn't say what output counts as success (`$_GET["path"]` will be undefined when the file is served directly), and doesn't say to delete the file afterward.

34. README_docker.md is not a complete configuration. The Compose snippet has no `services:` header and has an empty `environment:` with only a commented line. It also uses placeholder paths, and doesn't state which files go in the mounted folder or that the second block must be saved as `activity-bot.conf`.

35. README_docker.md has copy-paste inconsistencies: `Host(`your.host.com`)` versus `server_name you.host.com;`, and the label comment 'Internal port for postiz', which belongs to a different project.

36. The Docker instructions assume Traefik for reachability. There is no `ports:` mapping, TLS setup, or alternative for non-Traefik users, so the reader has no way to expose the bot over HTTPS. Nothing is said about file ownership and write permissions for the container user, or where `data/` ends up on the host.

37. Minor formatting issues that cause confusion. The Set Up list starts at `0.` and then repeats `1.`, with inconsistent sub-bullet indentation. There is a misplaced code span in 'an `.htaccess file`'. The nginx config block is labeled `bash`.
