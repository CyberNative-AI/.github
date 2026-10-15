# Edits from the study files

This folder was copied from the study's working directory and then edited. The edits remove internal identifiers and
host paths, correct one prior-art citation, add a reproduction section, remove contributor data and contact details,
leave out the two targeted large wikis, and append dated corrections. The frozen
protocol was committed before the main run; the copies here no longer match that commit's bytes because of the
edits listed below. No count, class or verdict was changed.

## Text and code

| File | Original sha256 | Published sha256 |
|---|---|---|
| `AMENDMENT-01.md` | `edd08233aa1d824223273fdcc0225c82a909cde780bef46ba8a06689011d55d7` | `7f07cb3a970077dd2b1a0ae49ca2d43c72e195f59ed481a5becb2db40cfd4ee7` |
| `AMENDMENT-02.md` | `9f398bef1fea5200f2c323922309487758cd77d37e9d28c958237ca69d69208b` | `6f6412487ffadbb90365d230013271035fcb7fa73df716e1d2c5985c8adb78ba` |
| `FORECAST.md` | `8b8ef8fdb03556d4fe4d27f93f73045490ca75da1f67a0d1973687c3cf15ef81` | `4389109c1868dbd340fc94febd47e8aa5536d0e38fc71922eceed034343cab28` |
| `PROTOCOL.md` | `461a89fcbc8ceb3f1539b7725a76bb932225f8b16c3f355726903e9365edd296` | `6bf94e39d84a9e3d8f47db64ac5ac28c0d6caa4ec7f0bb975a0816bc9c8abee0` |
| `RESULT.md` | `86d2a6d8252219dd6265f85aa0f5155eddd97b8ee7af31e7375e62eda2fc196b` | `70040d6eedd921d617134f47a0de29502683f651ade64bd7b094c19497c980c6` |
| `src/common.py` | `d66778adf573ff068858f38e19619357a542796a0a6054c6e9bfda7496ca7c8c` | `e04b1d70efca990622ae46e2bf09f9bf57531b50eb9738ac3095959c4c1a7746` |
| `src/compare.py` | `cea5cbd2e91f92ec252fd32e0a1ad23b85bbd83a72e5abb8f3cab17539a6216f` | `c51757a177887f8512cb2d73e422a8c8c22b5cb930fc1325acc062f383287c01` |
| `src/control.py` | `02b4166bb19346fd9b2eb408e500f4b2364cdb1affc82b7b8ecf52538c90951b` | `0156740c21a1b78138f76c48e66670c9c78f76197acad27bbcb7b387212bc0c9` |
| `src/coverage.py` | `5654b458f06f08da9f294dda50b2a7a56baba1590785587ef6f04e39b32d19b4` | `73e43f4a3ba6f257f62761701a2f3cc9b38a11129cb110ed248559780add5dbe` |
| `src/extract.py` | `100208eeb6dcc34da54d5574063c11dcc9401d7ded88340b06c295398de1eafc` | `864deb79d518049331bb00738ea7b4cd209e1fc4f4a30753b4c33870a9d169f7` |
| `src/fetch.py` | `a17e95d7e88f7de0fe563c1891cb3cf91a4bfcad9466ee603d01061bb9fb0abc` | `bf0681d27fc042b2597bcedfe921248b4296268beeed8e95664e407ce0b47825` |
| `src/rcfetch.py` | `64a650fb59c29c8be57ac65e31b5efc8e1ad3c3230093f065783f4bef4075396` | `53f69cb37d2ce8de0dcc0b4169067bfb194893855a39aa3aaa9564fa38543060` |
| `src/run_all.py` | `30251a17d2578fc3e4651b347cb3e7c98f7b16c4ed6e63fd3693a5b243360d75` | `19cf8ce7c31f16399488afd2650de83b877a005b01e9e491a31b40ffa338f28c` |
| `src/signature.py` | `76389813ac4add8b8d17efaca1370578049cfebd2e0dafcfada61241559b924b` | `6e70d11126d4a7438adddc06498e8fb8e951636c1ea72842652ac22173d5cc6f` |

- `PROTOCOL.md`: internal study ID, owner and tracker references removed; host path replaced by "a local work
  directory"; the internal routing sentence in section 10 replaced by a neutral one; forecaster description reworded.
  Two dated notes appended, without changing the frozen text: in section 1, the sunset page's last legacy edition
  in scope is 20261201 (1 December 2026); in section 7, the download cap and the 6-hour wall time are not enforced
  in code.
- `FORECAST.md`: internal study ID removed (also inside the quoted draft title, which is otherwise verbatim);
  forecaster description reworded. The quoted draft's sha256 refers to the unedited draft.
- `AMENDMENT-01.md`: internal study ID removed; a dated correction appended to the T410405 sentence.
- `AMENDMENT-02.md`: internal study ID removed; machine memory size removed.
- `RESULT.md`: internal study ID removed; the T410405 attribution corrected (that task is about spaces versus
  underscores in titles, resolved 2026-03-02; our differences are localized versus canonical namespace prefixes);
  the title-style count definition stated (5 of the counted rows are timing-class); contributor wording neutral
  ("AI agent"); "Reproduce" replaced by the offline recompute command and the full-rerun notes; data and license
  section added. Dated updates (2026-10-15) appended without rewriting the frozen lines: the targeted wikis are not
  in this package; the last legacy edition is 20261201; the reproduction section names the offline recompute as the
  supported operation and corrects an earlier claim that the full rerun was bounded. The second-agent rerun line
  (6 sampled wikis and the positive control, same code, about one hour after the main comparison) is reworded for a
  public reader.
- `src/common.py`: internal study ID removed from the docstring; the hard-coded host work directory replaced by the
  `DUMPS_WORK` environment variable (default `./work` next to `src/`).
- Collection scripts (`src/run_all.py`, `fetch.py`, `rcfetch.py`, `compare.py`, `control.py`, `coverage.py`,
  `signature.py`): a paragraph at the top of each docstring labels it historical and says its download and time
  limits are not enforced. No code changed.
- `src/extract.py`: a docstring note that full-rerun extraction records contain contributor fields. No code changed.
- `src/tally.py` is new: it regenerates `evidence/tallies.json`, which was first written by hand from the same
  evidence. Its output equals the first tallies in content (the first file lacked a trailing newline).

## Files left out

The two targeted large wikis are not part of this package; their files are not copied: `evidence/compare/current/enwiktionary.diffs.jsonl.gz`, `evidence/compare/current/enwiktionary.json`, `evidence/rc/enwiktionary.json.gz`, `evidence/compare/current/mgwiktionary.diffs.jsonl.gz`, `evidence/compare/current/mgwiktionary.json`, `evidence/rc/mgwiktionary.json.gz`.
`evidence/summary.json` already listed them as having no comparison, and `evidence/tallies.json` lists them under
`targeted` as empty, so no count changes.

## Contributor data removed

The published comparison evidence contains no user names, user IDs, IP addresses or page text. Rows whose differing
field is `user`, `uid` or `ip` record only the field name, not the values. A full rerun is different:
`src/extract.py` writes each revision's contributor user name, user ID and IP address (`user`, `uid`, `ip`) into
its local extraction records under `DUMPS_WORK`. Redact those records before sharing them. Contributor data
remained in three places in the published evidence and is removed here:

1. Page titles in the User (2) and User talk (3) namespaces, which contain user names: set to `null` in the
   comparison records (`evidence/compare/**`, `pilot/`, matched by namespace number) and in the recent-changes
   rows (`evidence/rc/*.json.gz`, matched by every local name, alias and gendered form of those namespaces, read
   from each wiki's API). Redirect targets in those namespaces, including targets behind interwiki or language
   prefixes such as `m:User:` or `w:en:User:`, are replaced by `[user-namespace title removed]`, so the record still
   counts as a redirect. Titles in any namespace that contain a user namespace after such a prefix are set to `null`.
   Page IDs, revision IDs and namespace numbers are kept.
2. Edit summaries in `evidence/signatures.jsonl` (move summaries name users and, in one case, link a former user
   name to its renamed account). Each `comment` is replaced by `comment_move_summary`, the boolean that
   `src/tally.py` derives from it.
3. Contact details: any title, redirect target or recent-changes field containing an e-mail address, in every
   namespace, is set to `null` (redirect targets become `[title removed: contact details]`).

Counts removed: {"comments": 143, "contact_titles": 0, "event_titles": 0, "rc_targets": 5, "rc_titles": 414, "record_redirect_targets": 644, "record_titles": 17872, "user_chain_titles": 0}. Titles in other namespaces can still contain a user name without a namespace prefix (for
example a project page named after a user); they are kept, because they are part of the public page title on the
live wiki.

Gzip files here are rewritten with a fixed timestamp, so their bytes differ from the originals even where no
title was removed.
