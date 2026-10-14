PROBLEMS
1. The README opens with a very long feature list and a "doesn't do" list, and the actual setup steps only appear much later, so a beginner has to scroll a long way to find where to start.
2. The .env comments tell you to open `tools/rsa_keys.html`, but the file in the repository is called `rsa_key_generator.html`, so the name doesn't match.
3. Telling the reader to "rename .env.example to .env" gives no help on how or where to do it, for example on Windows where the extension and dotfiles are hidden or where you do it on the computer versus on the server.
4. There's no guidance for a non-developer on how to run `password_hash(...)` or `php tools/generate_password.php`, such as where to type it, whether PHP must be installed, or what to do if it isn't.
5. The Minimum Requirements list ends with a joke line (Docker, GLaDOS and so on), and requiring PHP 8.5 gives no way to check what the host runs, which could confuse a newcomer.
6. In the .env example, some values are in double quotes (USERNAME, PAGE_SIZE) and others are bare (MAX_LOGS), and nothing says whether you should keep quotes around your own values.
7. The numbered Set Up steps are short and in a sensible order, and the webfinger check, with a description of what you should see, is a helpful way to know it worked.
8. "Check your `/data/logs/` directory" is ambiguous: it could mean the server's top-level root or a folder inside the website's own directory.
9. The "How this works" section is confusing and not useful for someone just setting up; it describes rewrite rules and file locations rather than anything to do.
10. The API examples all use `"password": "your-password-here"`, and it's unclear whether that should be the plain password or the generated hash.
