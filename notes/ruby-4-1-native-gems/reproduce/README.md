# Ruby 4.1 native gems: reproduction

These are the scripts we ran on 2026-10-21, with only their local storage paths changed to `gems/` and `work/`. The installs need network access to rubygems.org, and the fix tests also clone from GitHub. Gem builds run arbitrary code from each gem's `extconf.rb`, so run them only in throwaway containers as shown, never on your own machine.

Images, pinned by digest (`data/images.txt`):

- `ruby:4.0.7-bookworm`: `ruby@sha256:6a41409902453ca21a68e1a63239f206728ec6d549d56163e99c347eef7c439a`
- `ruby:4.1.0-preview1-bookworm`: `ruby@sha256:c8df226103e1281b0e2e4b56c44ef065e91731980a12889681c11df71c2a9dcb`

```sh
A40=ruby@sha256:6a41409902453ca21a68e1a63239f206728ec6d549d56163e99c347eef7c439a
A41=ruby@sha256:c8df226103e1281b0e2e4b56c44ef065e91731980a12889681c11df71c2a9dcb
```

## 1. The gem list

`data/frame.jsonl` is our list from 2026-10-21: the top 3,000 gems by all-time downloads from ecosyste.ms, with the latest stable version and its platforms from the rubygems.org API. `python3 src/frame.py 3000` rebuilds it, with today's ranks and versions.

```sh
mkdir gems
python3 src/native.py        # downloads each latest ruby-platform .gem, keeps the 165 native ones in gems/ (95 MB)
```

## 2. Build and load every gem on both Rubies

`src/run_arm.sh` first builds the two control extensions in `controls/`: `cyba_untyped` uses the removed `Data_Make_Struct`/`Data_Get_Struct`, `cyba_typed` uses the TypedData API. Then `src/run_one.sh` runs, for each gem: `gem install` from the local `.gem` file (15-minute limit), three `require` attempts (`name`, `name` with `-` as `/`, and with `-` as `_`), and `nm -D --undefined-only` on the gem's shared objects.

```sh
mkdir work
for arm in A40 A41; do
  img=$([ $arm = A40 ] && echo "$A40" || echo "$A41")
  docker run --rm -e ARM=$arm --cpus 4 --memory 8g --memory-swap 8g --pids-limit 4096 \
    -v "$PWD/gems:/gems:ro" -v "$PWD:/src:ro" -v "$PWD/work:/work" "$img" timeout -k 10 10800 bash /src/src/run_arm.sh
done
python3 src/score.py         # writes data/score.json and prints the counts
```

Each arm took about 30 minutes on 4 CPUs. Each `gem install` stops after 15 minutes, each `require` after 2, and the whole arm after 3 hours. The container runs as root, so files in `work/` are owned by root.

`score.py` decides each gem's outcome:

- **ENV**: fails to install, or installs but does not load, on 4.0.7 (in our run, system libraries missing from the image).
- **TIMEOUT**: either install hit the 15-minute limit.
- **BREAK**: works on 4.0.7, and on 4.1.0-preview1 fails to install, stops loading, or has a shared object with an undefined removed symbol (`data/removed.txt`: identifiers in 4.0.7's public headers that are gone from 4.1.0-preview1's).
- **OK**: everything else. A gem none of whose three `require` names loads on either Ruby counts as OK if it installs on both.

Causes were then checked by hand against `work/A41/res/<gem>/install.log`: thin and ruby-debug-ide fail because a dependency (eventmachine, debase) fails, and rinku fails only on preview builds (see the note).

## 3. The source search

```sh
python3 src/static_scan.py   # writes data/static.jsonl: removed identifiers found in each gem's C/C++ sources
```

## 4. Ready-built binaries

```sh
python3 src/arm_p.py         # writes data/arm_p.json from data/frame.jsonl
```

## 5. tsort and the tested fixes

`src/r_exec.sh` bundles one gem at a time and requires it. `src/fix_exec.sh` bundles the git-pinned commits from the note, the released versions as a check, and molinillo and mobility with `gem "tsort"`. Run each with `ARM=A40` and `ARM=A41`:

```sh
for arm in A40 A41; do
  img=$([ $arm = A40 ] && echo "$A40" || echo "$A41")
  docker run --rm -e ARM=$arm --cpus 2 --memory 4g --memory-swap 4g --pids-limit 2048 -v "$PWD:/src:ro" -v "$PWD/work:/work" "$img" timeout -k 10 5400 bash /src/src/r_exec.sh
  docker run --rm -e ARM=$arm --cpus 4 --memory 6g --memory-swap 6g --pids-limit 2048 -v "$PWD:/src:ro" -v "$PWD/work:/work" "$img" timeout -k 10 10800 bash /src/src/fix_exec.sh
done
```

Each `bundle install` stops after 15 minutes (20 in `fix_exec.sh`) and each smoke test after 5. Results are in `work/R-<arm>/<gem>/` and `work/FIX-<arm>/<case>/` (`install.rc`, `run.rc`, logs, `Gemfile.lock`). Two smoke tests in these scripts are wrong on both Rubies and do not change the results: thin's last statement, `Thin::VERSION::STRING`, raises a TypeError after `require "thin"` and `Thin::HttpParser.new` have succeeded, and the cocoapods probe never loads Molinillo.

## Licence

The files in this folder are MIT-licensed (see `LICENSE`). `data/frame.jsonl` holds public package metadata from ecosyste.ms and rubygems.org.
