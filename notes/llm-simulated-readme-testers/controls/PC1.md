PROBLEMS
1. The example config tells you to generate keys by opening `tools/rsa_keys.html`, but no file with that name is in the repository; the tools folder only has rsa_key_generator.html, so the instruction points at something that does not exist.
2. The key generator page itself is plain and unstyled; it works, but it looks unfinished.
3. Files whose names begin with a dot (.env, .htaccess) are invisible by default in Finder, Windows Explorer and many FTP clients, so a beginner may think the upload is missing files or not be able to rename the example file at all.
4. The humour ("GLaDOS", "Because I hate you and want you to suffer", "We live in the future now") reads as hostile or confusing to someone who does not share the in-jokes.
5. The opening paragraph says what the code is (a single PHP file, an ActivityPub server) but never says what the reader ends up with: an account people on Mastodon can follow, living on their own subdomain.
6. USERNAME says "Do not include an @" but a reader cannot tell whether to write just the name or name@domain.
7. "Only formatting elements are allowed" for HTML posts: which tags count as formatting elements is never listed.
8. The Python examples use the Requests library; it would be nice to also show curl.
9. The FAQ answer about scaling is a bit glib but answers the question.
10. The licence section is clear.
