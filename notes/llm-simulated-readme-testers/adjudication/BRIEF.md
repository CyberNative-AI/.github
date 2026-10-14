You are scoring documentation critiques against a fixed list of known problems. Do not use any tool except: Read the one batch file named in your task, and Write your JSON answer to the file named in your task.

The critiques are about the documentation of ActivityBot, a single-PHP-file ActivityPub bot server (README.md, .env.example, README_nginx.md, README_docker.md and possibly README_caddy.md).

For EACH critique and EACH item below, decide match = true or false.
Rule: a match requires the critique to ASSERT that this problem is present in the docs (it may use different words). Merely mentioning the topic, praising it, saying it is fine, or raising a different problem about the same file or section is NOT a match. One critique sentence can match more than one item. Judge each item independently.
For every match=true give the shortest exact quote (<= 30 words) from the critique that supports it. For match=false give quote = "".

ITEMS:
- H01: Says the key-generator file named in .env.example (tools/rsa_keys.html) does not exist / does not match the file list (tools/rsa_key_generator.html), or that the referenced tool path is wrong.
- H02: Says the instruction to rename .env.example to .env assumes the reader knows how/where to rename a file (locally vs on the server, with what tool) and needs explanation.
- H03: Notes that .env / .htaccess / .env.example are dotfiles that may be hidden or hard to create/rename/upload in file managers, FTP clients, Windows or macOS.
- H04: Says it is unclear whether the key generator (or the tools/ folder) should be opened locally, uploaded to the server, or is hosted somewhere; or warns about uploading tools/ to the public site.
- H05: Flags inconsistent or unexplained quoting of values in .env / .env.example (some quoted, some not), or unclear quoting/escaping rules for values.
- H06: Flags jokes/humour/snark in the docs (e.g. the GLaDOS/none-of-these list, 'Because I hate you', 'We live in the future now', 'Dunno', '*sigh*') as confusing, off-putting or unclear.
- H07: Names specific unexplained jargon a newcomer would not know (e.g. ActivityPub, Fediverse, WebFinger, keypair/RSA, .htaccess, subdomain, HTTPS certificate, DID, PHP-FPM).
- H08: Complains about section order/structure (e.g. setup buried after a long feature list, no quick start near the top, requirements/setup/how-it-works ordering, steps out of order).
- H09: Says the intro does not explain what the user actually gets or what it is for (e.g. a Fediverse account at your own subdomain that people on Mastodon can follow), as opposed to a feature list.
- H10: Identifies the 'How this works' section (htaccess rewriting to index.php?path=, data directories list) as confusing, too technical or not useful for users setting it up.
- H11: Notes that setup does not mention file/directory permissions or ownership, or that PHP/the web server must be able to create/write data directories (data/, posts/), or that hosts differ in this.
- C01: Says the requirements omit the PHP cURL extension (README_nginx installs php-curl but the main requirements list only OpenSSL) or the extension list is incomplete with cURL named.
- C02: Says it is unclear whether USERNAME should include the domain / full handle (user@domain).
- C03: Says REALNAME / "real" name is unclear or misleading (should it be a person's real name? it is the display name).
- C04: Says the password-hash step is unclear for non-developers: where/how to run password_hash(...) or php tools/generate_password.php (needs PHP/CLI locally; shared hosts lack a shell).
- C05: Says /data/logs/ (or /data, /posts) is ambiguous: filesystem root vs inside the site directory, or where to find the logs.
- C06: Says setup silently assumes Apache/.htaccess, or that nginx/Docker/other-server instructions are hidden (only in FAQs) or missing (e.g. Caddy).
- C07: Says 'Only formatting elements are allowed' is unclear: which HTML elements are allowed/stripped.
- C08: Says the optional avatar/banner upload step does not explain how ActivityBot finds the images (configure AVATAR/BANNER in .env) or where to put them.
- C09: Flags confusion between the two configuration methods (edit index.php vs .env) or about exactly which files to upload (e.g. conditional '.env if you use one', .htaccess).
- C10: Says PAGE_SIZE is unclear (per page of what / where).
- R01: Mentions reading the README as raw text/terminal, or that markdown/emoji rendering is assumed.

OUTPUT: a single JSON object: {"<critique id>": {"<item id>": {"match": true|false, "quote": "..."}, ...}, ...} covering every critique in the batch and all 22 item ids. No other text in the file.
