# Ruff upgrades change which checks run

Review the rule selection along with the version. In these two small examples, Ruff 0.16.0 catches a shared-list bug that 0.15.0 accepts, and accepts a lambda assignment that 0.15.0 flags.

[Ruff's July 23 release announcement](https://astral.sh/blog/ruff-v0.16.0) explains the expanded defaults and the rules removed from that selection. We read the announcement and ran this comparison on October 6, 2026; this is a migration example for those pinned releases.

## A new failure can reveal a real bug

[`mutable_default.py`](mutable_default.py) starts with:

```python
def add_tag(tag, tags=[]):
    tags.append(tag)
    return tags
```

Call it twice without supplying `tags`, and both calls return the same list. The included Python run prints:

```text
['first', 'second'] ['first', 'second'] True
```

With isolated default settings, Ruff 0.15.0 returns no diagnostic; 0.16.0 reports [`B006`](https://docs.astral.sh/ruff/rules/mutable-argument-default/). The rule documentation explains why mutable defaults persist across calls and also describes intentional reuse. Decide whether the sharing fits the function before changing it.

Here the example should start a fresh list on each call. [`mutable_default_fixed.py`](mutable_default_fixed.py) uses `None` as the default and creates the list inside the function. Its output is:

```text
['first'] ['second'] False
```

That version passes the tested 0.16.0 defaults.

## A new pass can mean a removed check

[`lambda_alias.py`](lambda_alias.py) contains:

```python
tagger = lambda value: value.upper()
```

Ruff 0.15.0 reports [`E731`](https://docs.astral.sh/ruff/rules/lambda-assignment/); 0.16.0's defaults return no diagnostic. E731 is a style rule. Its absence does not establish a behavior change in this expression.

If your project wants to retain that check, add it to the new defaults:

```sh
/path/to/ruff-0.16.0 check --isolated --no-cache --extend-select E731 lambda_alias.py mutable_default.py
```

This reports E731 for the lambda assignment and B006 for the shared-list default. Restoring the old selection with `--select E4,E7,E9,F` also restores E731, but leaves this B006 example unflagged. Choose the checks you want to keep, then review the newly enabled ones. [Ruff's configuration documentation](https://docs.astral.sh/ruff/configuration/) explains `select`, `extend-select` and configuration precedence; an existing explicit selection can change what an upgrade enables.

## Rerun the comparison

Download this directory and provide separately installed Ruff 0.15.0 and 0.16.0 executables:

```sh
python3 check.py --before /path/to/ruff-0.15.0 --after /path/to/ruff-0.16.0
```

[`check.py`](check.py) verifies the versions, asserts nine lint results, executes both Python examples and prints JSON. It uses `--isolated --no-cache` to exclude project configuration and Ruff's cache; it does not fix files. [`result.json`](result.json) is our recorded output, and [`binary-provenance.json`](binary-provenance.json) lists the official PyPI wheels and their verified SHA-256 hashes.

Scope: synthetic Python examples, official Linux x86-64 binaries and these two exact Ruff releases. We did not audit a whole project, other platforms or later patch releases. Review your own configuration and diagnostics before adopting the migration advice.

AI-written note from CyberNative AI LLC. Questions or corrections: hello@cybernative.ai.
