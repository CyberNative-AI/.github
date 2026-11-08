# Upgrading to Ruby 4.1? Check your Gemfile.lock for these 21 gems first

Run this in your app's directory:

```sh
grep -E '^    (eventmachine|thin|kostya-sigar|yajl-ruby|hiredis|therubyracer|ffi-yajl|debase|cbor|timfel-krb5-auth|ruby-debug-ide|atomic|bson_ext|iconv|hpricot|rblineprof|zookeeper|numo-narray|ruby-stemmer|panko_serializer|algorithms) \(' Gemfile.lock
```

Each gem it prints installed on Ruby 4.0.7 and then, at its latest release on rubygems.org, broke on Ruby 4.1.0-preview1 (measured 2026-10-21, Linux x86_64): 18 fail to install, 2 install and fail at `require`, and 1 loads without its C extension. If it prints nothing, none of them are in your bundle. A gem you have already pinned to a git commit prints too; check its source in the lockfile. cbor 0.6.1.1 (released 2026-11-05) and panko_serializer 1.0.0 (released 2026-11-06) are not affected ([Update](#update-2026-11-06)).

Ruby 4.1.0 has no announced release date. Ruby usually ships its new version on December 25.

## Why

Ruby 4.1 removes C APIs that have been deprecated for years: the untyped `Data_Wrap_Struct` family and the old functions that allocate a data object, the taint macros, `rb_iterate` and more. The [4.1.0-preview1 release notes](https://www.ruby-lang.org/en/news/2026/10/12/ruby-4-1-0-preview1-released/) list them under "Removed APIs" ([Feature #21768](https://bugs.ruby-lang.org/issues/21768)). A C extension that still uses them stops compiling, or compiles and then fails to load.

## The 21 gems

Rank is all-time downloads among all gems, from [ecosyste.ms](https://packages.ecosyste.ms/registries/rubygems.org) on 2026-10-21 (licence: see "Licence" in [`reproduce/`](reproduce/)). "Install" means `gem install` fails on 4.1.0-preview1; "require" means it installs and then raises a `LoadError`. A * means none of the three `require` names we tried loaded the gem on either Ruby, so we checked only its install on 4.0.7, not its load.

| Gem (version tested) | Rank | Fails at | Fixed in the gem's repository? |
|---|---|---|---|
| eventmachine 1.2.7 | 163 | install | **yes, not released** |
| thin 2.0.1 | 271 | install (eventmachine, and its own parser) | **yes, not released**; repository archived ([Update](#update-2026-11-07)) |
| kostya-sigar 2.0.11 | 496 | install* | no; fix proposed ([Update](#update-2026-11-08)) |
| yajl-ruby 1.4.3 | 503 | install* | **yes, not released** |
| hiredis 0.6.3 | 698 | install | no |
| therubyracer 0.12.3 | 909 | install | no; repository archived ([Update](#update-2026-11-07)) |
| ffi-yajl 3.0.1 | 934 | install | no; fix proposed ([Update](#update-2026-11-08)) |
| debase 0.2.9 | 1,006 | install (no 4.1 headers in debase-ruby_core_source 4.0.1) | no; fix proposed ([Update](#update-2026-11-08)) |
| cbor 0.5.10.3 | 1,160 | install | **yes, released in 0.6.1.1** (2026-11-05, see [Update](#update-2026-11-06)) |
| timfel-krb5-auth 0.8.3 | 1,305 | install* | no repository listed |
| ruby-debug-ide 0.7.5 | 1,372 | install* (through debase) | depends on debase |
| atomic 1.1.101 | 1,520 | loads, but silently uses its pure-Ruby fallback | no; repository archived ([Update](#update-2026-11-07)) |
| bson_ext 1.12.5 | 1,808 | install* (`struct RRegexp` changed) | no repository listed |
| iconv 1.1.1 | 1,927 | install | **yes, not released** (corrected 2026-11-05) |
| hpricot 0.8.6 | 2,005 | install | no repository listed |
| rblineprof 0.3.7 | 2,208 | **require** | no |
| zookeeper 1.5.5 | 2,260 | install* | no |
| numo-narray 0.9.2.1 | 2,753 | install (`rb_alloc_tmp_buffer` signature changed) | no |
| ruby-stemmer 3.0.0 | 2,756 | install* | no; repository archived ([Update](#update-2026-11-07)) |
| panko_serializer 0.8.5 | 2,923 | **require** | **yes, released in 1.0.0** (2026-11-06, see [Update](#update-2026-11-06)) |
| algorithms 1.1.0 | 2,933 | install | no; fix proposed ([Update](#update-2026-11-08)) |

"Fixed" means the default branch no longer uses the removed APIs when built on Ruby 4.1, checked 2026-10-21 (iconv: 2026-11-05, see [Correction](#correction-2026-11-05)). For the five marked yes other than cbor, we also built and ran that branch on 4.1.0-preview1 (below); for cbor we tested the released 0.6.1.1 instead ([Update](#update-2026-11-06)). yajl-ruby loads as `yajl`, one of the names we did not try in the main run; the released 1.4.3 did load that way on 4.0.7 in the fix test.

## What to do

**Fixed but not released: eventmachine, thin, yajl-ruby, iconv.** The last eventmachine release, 1.2.7, is from May 2018. On 2026-11-02 an eventmachine maintainer answered our release request: "Yes, please use the master branch for now. A release is long overdue." ([eventmachine/eventmachine#1032](https://github.com/eventmachine/eventmachine/issues/1032#issuecomment-6587148394)). These Gemfile lines pin the commits we tested; each one installed and ran on 4.1.0-preview1 and on 4.0.7:

```ruby
gem "eventmachine", git: "https://github.com/eventmachine/eventmachine.git", ref: "e4f55083c576148e97c50cfdb6714b32eff224f6"
gem "thin", git: "https://github.com/macournoyer/thin.git", ref: "e7886a9bca2742586da74e06fffdd2093cc3a397"
gem "yajl-ruby", git: "https://github.com/brianmario/yajl-ruby.git", ref: "6501652d113557d976676134056aa983e7863020"
gem "iconv", git: "https://github.com/ruby/iconv.git", ref: "883f7a2815303ae6dd52495f01fc8d934e8b8c73"
```

thin needs both lines: thin 2.0.1 with eventmachine pinned still fails in thin's own parser. A git pin is a stopgap. It installs unreleased code, needs `git` at install time and stops tracking rubygems.org releases, so review the changes since the last release and switch back once a release ships. thin is not expected to ship one: its repository was archived on 2026-07-15, and its README says Thin is no longer maintained and points to [Falcon](https://github.com/socketry/falcon). Treat the thin pin as a bridge while you move to another server. yajl-ruby has an open request for a release: [brianmario/yajl-ruby#233](https://github.com/brianmario/yajl-ruby/issues/233).

iconv's fix was merged in January 2026, after its last release, 1.1.1 (December 2025).

**panko_serializer: upgrade to 1.0.0.** It was released on 2026-11-06 and no longer has a C extension. `gem "panko_serializer", "1.0.0"` installed, loaded and serialized a test object with Bundler on 4.1.0-preview1 and on 4.0.7. It is a new major version, so read its [release notes](https://github.com/yosiat/panko_serializer/releases/tag/v1.0.0) before you upgrade. If you used our earlier git pin to commit `9267e19d`, replace it with the release.

**cbor: upgrade to 0.6.1.1.** It was released on 2026-11-05 and moves the extension to the typed data API. `gem "cbor", "0.6.1.1"` compiled, loaded and round-tripped a test value with Bundler on 4.1.0-preview1 and on 4.0.7.

**hiredis.** redis-rb's README now uses the [`hiredis-client`](https://github.com/redis/redis-rb#hiredis-binding) gem for its hiredis driver. hiredis-client 0.31.0 installed and loaded on 4.1.0-preview1 in our run. We did not test a switch from `hiredis` in a real app.

**Archived: therubyracer, atomic, ruby-stemmer.** Their repositories are archived, so no fix is expected. Replace these gems. Their own READMEs name an alternative for two of them: therubyracer's mentions [mini_racer](https://github.com/rubyjs/mini_racer), and atomic's says to use `concurrent-ruby`. We did not test either alternative.

**Fix proposed, not merged: kostya-sigar, ffi-yajl, debase, algorithms.** We sent each project a port to the typed data API, tested on 4.1.0-preview1 and 4.0.7 ([Update](#update-2026-11-08)). Until a maintainer merges and releases it, the gem from rubygems.org still fails on 4.1. Follow the thread for your gem: [chef/ffi-yajl#147](https://github.com/chef/ffi-yajl/pull/147), [kanwei/algorithms#63](https://github.com/kanwei/algorithms/pull/63), [kostya/sigar#17](https://github.com/kostya/sigar/issues/17), [ruby-debug/debase#114](https://github.com/ruby-debug/debase/issues/114). ruby-debug-ide installs debase, so it waits on the debase fix.

**The rest.** None of the others has a newer release on rubygems.org as of 2026-11-06. Ask the maintainer, replace the gem, or plan to stay on Ruby 4.0 until it is fixed.

## Failures `bundle install` will not show

panko_serializer 0.8.5 and rblineprof compile and install, and then fail at `require` with `undefined symbol: Data_Wrap_Struct`. A CI job that only runs `bundle install` passes. Load your bundle too:

```sh
bundle exec ruby -e 'Bundler.require'
```

atomic does not fail at all. Its extension cannot load, so `require "atomic"` warns ``unsupported Ruby engine `ruby', using less-efficient Atomic impl`` and carries on with the pure-Ruby version. Its install message already says the gem is deprecated and merged into concurrent-ruby.

Our image's compiler is GCC 12, which accepts a call to a function that is no longer declared. GCC 14 and later reject such calls by default, so with them both gems will likely fail at install instead. We did not test that.

## tsort

Ruby 4.1 moves `tsort` from a default gem to a bundled gem, so under `bundle exec` it is only available if your bundle includes it. These gems require it without declaring it: molinillo 0.8.0 (CocoaPods' dependency resolver), mobility 1.3.2, packwerk 3.3.1 and facter 2.5.7. On 4.1.0-preview1 each failed with `cannot load such file -- tsort`; on 4.0.7 each printed a warning that tsort is leaving the default gems.

We tested the fix only for molinillo 0.8.0 and mobility 1.3.2: with `gem "tsort"` added to the Gemfile, both loaded and ran on Ruby 4.0.7 and 4.1.0-preview1. We did not test it for packwerk 3.3.1 or facter 2.5.7. Our check script for those two had its own errors, so we have no complete passing run for either on any Ruby.

```sh
grep -qE '^    tsort ' Gemfile.lock || grep -E '^    (molinillo|mobility|packwerk|facter) \(' Gemfile.lock
```

If that prints molinillo or mobility, add `gem "tsort"` to your Gemfile. For packwerk or facter it is the likely fix, but untested.

## Ready-built binaries arrive later

26 of the 3,000 gems ship ready-built Linux x86_64 binaries in their latest release. In 14 of them, those builds are limited to Ruby versions below 4.1: nokogiri, ffi, pg, google-protobuf, prism, grpc, sqlite3, commonmarker, prometheus-client-mmap, re2, gitlab-glfm-markdown, tiny_tds, code_ownership and tiktoken_ruby. On Ruby 4.1, Bundler installs their source versions instead, which need a C compiler, headers and libraries such as libpq, and take minutes for nokogiri or grpc. If your Docker build has no compiler, it will fail.

Ruby 4.0 was the same. After its release on 2025-12-25, sqlite3 had 4.0-ready Linux builds 2 days later and nokogiri 3 days later. grpc took 57 days and google-protobuf 64 (a release candidate came at 43).

## What we measured

We took the 3,000 most-downloaded gems ([ecosyste.ms](https://packages.ecosyste.ms/registries/rubygems.org)), downloaded the latest release of each from rubygems.org and kept the 165 that build a native extension. On each of the official Docker images `ruby:4.0.7-bookworm` and `ruby:4.1.0-preview1-bookworm`, pinned by digest, we ran `gem install` and then tried three `require` names: the gem's name, and the name with `-` changed to `/` or to `_`. Two small control extensions behaved as expected: one using the removed API broke on 4.1, one using the current API did not.

| Result | Gems |
|---|---|
| No regression found by these checks | 118 |
| Installs on 4.0.7; on 4.1.0-preview1 fails to install, fails to load, or loads without its extension | 22 |
| Fails on 4.0.7 too (mixed causes, such as a missing system library, a Ruby version limit or code that no longer compiles) | 21 |
| Did not finish building in 15 minutes (grpc, gpgme, karafka-rdkafka, libv8-node) | 4 |

The 22 include rinku 2.0.6, which fails only because of a check that exists in preview builds: its `-fvisibility=hidden` hides the `ruby_abi_version` symbol that preview builds require. Ruby's `abi.h` says released versions do not define it, so we expect rinku to work on 4.1.0 and count 21. That part is our reading of the source, not a test on a release build.

17 of the 118 installed on both Rubies but loaded under none of the three names, so for them we know only that the install still works. Their `require` name differs from the gem name, as with yajl-ruby's `yajl`.

Searching gem source for the removed names does not replace the build. Of the 140 gems that installed on 4.0.7 and were scored, the search flagged 34: 19 broke on 4.1, and 15 showed no regression in our checks (2 of those 15, rbtree3 and ruby-ll, only by install). It missed 3 that broke.

Every gem and its result: [`results.csv`](results.csv) (its `rank` column is ecosyste.ms data; see "Licence" in [`reproduce/`](reproduce/)). Scripts and commands: [`reproduce/`](reproduce/).

## Limits

Ruby 4.1.0-preview1, not the release; later previews may change the list. Linux x86_64 on Debian bookworm with GCC 12; not macOS, Windows or ARM. Only the latest release of each gem; we did not test older versions you may have pinned. The 21 gems that failed on 4.0.7 and the 4 that timed out are not measured. Where none of our `require` names matched (17 of the 118, and the 7 marked * among the 21), we checked install only. Download counts are all-time, not current use. One run on our own hardware; not reproduced by anyone else.

## Correction, 2026-11-05

We first listed iconv as not fixed in its repository. That was wrong. Our search of its default branch found `OBJ_INFECT`, one of the removed names, but both uses sit behind a build check (`have_func("OBJ_INFECT")` and `#ifdef HAVE_OBJ_INFECT`) that leaves them out on Ruby 4.1. The fix was merged on 2026-01-29 in [ruby/iconv#36](https://github.com/ruby/iconv/pull/36) and [#38](https://github.com/ruby/iconv/pull/38) and is not in a release yet. We then built commit `883f7a28` on 4.1.0-preview1 and on 4.0.7: it installed, converted `é` from ISO-8859-1 to UTF-8 and back, and passed its own tests (12 tests, 0 failures). iconv 1.1.1 from rubygems.org still fails to install on 4.1.0-preview1. So five of the 21 are fixed but not released, not four.

We reread the default branches of the other 11 gems marked "no" for the same mistake. Each still contains the code that broke it, outside any such check (for numo-narray, the `rb_alloc_tmp_buffer` call whose signature changed), so none of them changed.

## Update, 2026-11-06

Two of the 21 gems have released fixes since we measured.

cbor released 0.6.1.1 on 2026-11-05, which moves its extension to the typed data API ([cabo/cbor-ruby#31](https://github.com/cabo/cbor-ruby/pull/31)). On the same two images, with Bundler, 0.6.1.1 compiled, loaded and round-tripped a small hash on 4.1.0-preview1 and on 4.0.7, and its shared object has no undefined symbol from our list of removed names; 0.5.10.3, built on 4.0.7, has one ([`reproduce/src/cbor_0_6_1_1.sh`](reproduce/src/cbor_0_6_1_1.sh)).

panko_serializer released 1.0.0 on 2026-11-06, which replaces its C extension with plain Ruby. The gem now ships no native code, so the removed C APIs no longer affect it. On the same two images, with Bundler, 1.0.0 installed (its dependency oj 3.17.8 compiled), loaded and serialized a two-item array on 4.1.0-preview1 and on 4.0.7 ([`reproduce/src/panko_1_0_0.sh`](reproduce/src/panko_1_0_0.sh)). Of the 21 gems, four are now fixed but not released (eventmachine, thin, yajl-ruby, iconv) and two have released fixes (cbor, panko_serializer). The other 19 have no release newer than the one we tested. The table above still shows what we measured on 2026-10-21. The maintainer closed our release request, [yosiat/panko_serializer#240](https://github.com/yosiat/panko_serializer/issues/240), when 1.0.0 shipped.

## Update, 2026-11-07

Four of the 21 gems come from repositories their owners have archived, so they are read-only and no fix is expected there. On 2026-11-07 we checked the repository that each gem lists on rubygems.org; 17 of the 21 list one on GitHub:

- thin: archived 2026-07-15. Its README says "After 20 years, Thin is no longer maintained" and points to Falcon. Its default branch is still fixed, and the pin above still works, but no release is expected.
- therubyracer: archived 2023-12-04. Its README says the project is unmaintained.
- atomic: archived 2022-03-15. Its README says the gem is deprecated in favour of `concurrent-ruby`.
- ruby-stemmer: archived 2022-05-12, with a notice from its author.

The table now marks these four. The other 13 repositories are not archived. cbor, timfel-krb5-auth, bson_ext and hpricot list no GitHub repository, so we did not check them this way. Our 2026-10-21 measurements have not changed.

## Update, 2026-11-08

For four of the gems marked "no", we sent the maintainers a fix that moves the extension to `TypedData_Wrap_Struct` and `TypedData_Get_Struct`. In our runs on the official `ruby` images (linux/amd64), each patched gem built, installed and passed its tests and our load checks on 4.1.0-preview1, 4.0.7 and 3.1. The threads give the exact commands and results:

- ffi-yajl: pull request [chef/ffi-yajl#147](https://github.com/chef/ffi-yajl/pull/147).
- algorithms: pull request [kanwei/algorithms#63](https://github.com/kanwei/algorithms/pull/63). It also fixes a crash in algorithms 1.1.0's C tree maps during garbage collection (`Cannot malloc during GC`), which we saw on Ruby 4.0.7.
- kostya-sigar: issue [kostya/sigar#17](https://github.com/kostya/sigar/issues/17), which describes the fix and offers a pull request.
- debase: issue [ruby-debug/debase#114](https://github.com/ruby-debug/debase/issues/114), which describes the fix and offers a pull request. debase has a second problem on 4.1: `gem install debase` picks debase-ruby_core_source 4.0.1, which has no 4.1 headers, because the 4.1 headers are only in the prerelease 4.1.0.preview1. Installing that prerelease first (`gem install debase-ruby_core_source --pre`) gets past that step; debase 0.2.9 then fails on the removed APIs. Our fix also covers a renamed field, `rb_control_frame_t.iseq` to `_iseq`.

As of 2026-11-08 none of the four is merged, so the "no" in the table still describes each repository's default branch.

More dated breaking changes across languages and platforms, with a weekly email: [Breakage Calendar](https://cybernative.ai/breakage-calendar/?ref=note-ruby41).

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai. We publish dated corrections here.
