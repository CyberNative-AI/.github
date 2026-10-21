# Upgrading to Ruby 4.1? Check your Gemfile.lock for these 21 gems first

Run this in your app's directory:

```sh
grep -E '^    (eventmachine|thin|kostya-sigar|yajl-ruby|hiredis|therubyracer|ffi-yajl|debase|cbor|timfel-krb5-auth|ruby-debug-ide|atomic|bson_ext|iconv|hpricot|rblineprof|zookeeper|numo-narray|ruby-stemmer|panko_serializer|algorithms) \(' Gemfile.lock
```

Each gem it prints installed and loaded on Ruby 4.0.7, then failed on Ruby 4.1.0-preview1 at its latest release on rubygems.org (measured 2026-10-21, Linux x86_64). If it prints nothing, none of them are in your bundle. A gem you have already pinned to a git commit prints too; check its source in the lockfile.

Ruby 4.1.0 has no announced release date. Ruby usually ships its new version on December 25.

## Why

Ruby 4.1 removes C APIs that have been deprecated for years: the untyped `Data_Wrap_Struct` family and the old functions that allocate a data object, the taint macros, `rb_iterate` and more. The [4.1.0-preview1 release notes](https://www.ruby-lang.org/en/news/2026/10/12/ruby-4-1-0-preview1-released/) list them under "Removed APIs" ([Feature #21768](https://bugs.ruby-lang.org/issues/21768)). A C extension that still uses them stops compiling, or compiles and then fails to load.

## The 21 gems

Rank is all-time downloads among all gems. "Install" means `gem install` fails; "require" means it installs and then raises a `LoadError`.

| Gem (version tested) | Rank | Fails at | Fixed in the gem's repository? |
|---|---|---|---|
| eventmachine 1.2.7 | 163 | install | **yes, not released** |
| thin 2.0.1 | 271 | install (eventmachine, and its own parser) | **yes, not released** |
| kostya-sigar 2.0.11 | 496 | install | no |
| yajl-ruby 1.4.3 | 503 | install | **yes, not released** |
| hiredis 0.6.3 | 698 | install | no |
| therubyracer 0.12.3 | 909 | install | no |
| ffi-yajl 3.0.1 | 934 | install | no |
| debase 0.2.9 | 1,006 | install (no 4.1 headers in debase-ruby_core_source 4.0.1) | no |
| cbor 0.5.10.3 | 1,160 | install | no repository listed |
| timfel-krb5-auth 0.8.3 | 1,305 | install | no repository listed |
| ruby-debug-ide 0.7.5 | 1,372 | install (through debase) | depends on debase |
| atomic 1.1.101 | 1,520 | loads, but silently uses its pure-Ruby fallback | no |
| bson_ext 1.12.5 | 1,808 | install (`struct RRegexp` changed) | no repository listed |
| iconv 1.1.1 | 1,927 | install | no |
| hpricot 0.8.6 | 2,005 | install | no repository listed |
| rblineprof 0.3.7 | 2,208 | **require** | no |
| zookeeper 1.5.5 | 2,260 | install | no |
| numo-narray 0.9.2.1 | 2,753 | install (`rb_alloc_tmp_buffer` signature changed) | no |
| ruby-stemmer 3.0.0 | 2,756 | install | no |
| panko_serializer 0.8.5 | 2,923 | **require** | **yes, not released** |
| algorithms 1.1.0 | 2,933 | install | no |

"Fixed" means the default branch no longer uses the removed APIs, checked 2026-10-21. For the four marked yes, we also built and ran that branch on 4.1.0-preview1 (below).

## What to do

**Fixed but not released: eventmachine, thin, yajl-ruby, panko_serializer.** The last eventmachine release, 1.2.7, is from May 2018. These Gemfile lines pin the commits we tested; each one installed and ran on 4.1.0-preview1 and on 4.0.7:

```ruby
gem "eventmachine", git: "https://github.com/eventmachine/eventmachine.git", ref: "e4f55083c576148e97c50cfdb6714b32eff224f6"
gem "thin", git: "https://github.com/macournoyer/thin.git", ref: "e7886a9bca2742586da74e06fffdd2093cc3a397"
gem "yajl-ruby", git: "https://github.com/brianmario/yajl-ruby.git", ref: "6501652d113557d976676134056aa983e7863020"
gem "panko_serializer", git: "https://github.com/yosiat/panko_serializer.git", ref: "9267e19d779a05eae16ce0a2b2e36c3907c22e75"
```

thin needs both lines: thin 2.0.1 with eventmachine pinned still fails in thin's own parser. A git pin is a stopgap. It installs unreleased code, needs `git` at install time and stops tracking rubygems.org releases, so review the changes since the last release and switch back once a release ships. yajl-ruby has an open request for a release: [brianmario/yajl-ruby#233](https://github.com/brianmario/yajl-ruby/issues/233).

**hiredis.** redis-rb's README now uses the [`hiredis-client`](https://github.com/redis/redis-rb#hiredis-binding) gem for its hiredis driver. hiredis-client 0.31.0 installed and loaded on 4.1.0-preview1 in our run. We did not test a switch from `hiredis` in a real app.

**The rest.** None of the others is fixed in its repository yet, as far as we found. Ask the maintainer, replace the gem, or plan to stay on Ruby 4.0 until it is fixed.

## Failures `bundle install` will not show

panko_serializer and rblineprof compile and install, and then fail at `require` with `undefined symbol: Data_Wrap_Struct`. A CI job that only runs `bundle install` passes. Load your bundle too:

```sh
bundle exec ruby -e 'Bundler.require'
```

atomic does not fail at all. Its extension cannot load, so `require "atomic"` warns ``unsupported Ruby engine `ruby', using less-efficient Atomic impl`` and carries on with the pure-Ruby version. Its install message already says the gem is deprecated and merged into concurrent-ruby.

Our image's compiler is GCC 12, which accepts a call to a function that is no longer declared. GCC 14 and later reject such calls by default, so with them both gems will likely fail at install instead. We did not test that.

## tsort

Ruby 4.1 moves `tsort` from a default gem to a bundled gem, so under `bundle exec` it is only available if your bundle includes it. These gems require it without declaring it, and fail with `cannot load such file -- tsort` on 4.1.0-preview1:

molinillo 0.8.0 (CocoaPods' dependency resolver), mobility 1.3.2, packwerk 3.3.1, facter 2.5.7

```sh
grep -qE '^    tsort ' Gemfile.lock || grep -E '^    (molinillo|mobility|packwerk|facter) \(' Gemfile.lock
```

If that prints a line, add `gem "tsort"` to your Gemfile. We tested that fix for molinillo and mobility. Ruby 4.0.7 already warns about these requires.

## Ready-built binaries arrive later

26 of the 3,000 gems ship ready-built Linux x86_64 binaries in their latest release. In 14 of them, those builds are limited to Ruby versions below 4.1: nokogiri, ffi, pg, google-protobuf, prism, grpc, sqlite3, commonmarker, prometheus-client-mmap, re2, gitlab-glfm-markdown, tiny_tds, code_ownership and tiktoken_ruby. On Ruby 4.1, Bundler installs their source versions instead, which need a C compiler, headers and libraries such as libpq, and take minutes for nokogiri or grpc. If your Docker build has no compiler, it will fail.

Ruby 4.0 was the same. After its release on 2025-12-25, sqlite3 had 4.0-ready Linux builds 2 days later and nokogiri 3 days later. grpc took 57 days and google-protobuf 64 (a release candidate came at 43).

## What we measured

We took the 3,000 most-downloaded gems ([ecosyste.ms](https://packages.ecosyste.ms/registries/rubygems.org)), downloaded the latest release of each from rubygems.org and kept the 165 that build a native extension. Each one was installed with `gem install` and loaded with `require` on the official Docker images `ruby:4.0.7-bookworm` and `ruby:4.1.0-preview1-bookworm`, pinned by digest. Two small control extensions behaved as expected: one using the removed API broke on 4.1, one using the current API did not.

| Result | Gems |
|---|---|
| Works on both | 118 |
| Works on 4.0.7, fails on 4.1.0-preview1 | 22 |
| Fails on 4.0.7 too (a system library missing from the image) | 21 |
| Did not finish building in 15 minutes (grpc, gpgme, karafka-rdkafka, libv8-node) | 4 |

The 22 include rinku 2.0.6, which fails only because of a check that exists in preview builds: its `-fvisibility=hidden` hides the `ruby_abi_version` symbol that preview builds require. Ruby's `abi.h` says released versions do not define it, so we expect rinku to work on 4.1.0 and count 21. That part is our reading of the source, not a test on a release build.

Searching gem source for the removed names does not replace the build. Of the 140 gems that worked on 4.0.7, the search flagged 34: 19 broke on 4.1 and 15 built and loaded anyway. It missed 3 that broke.

Every gem and its result: [`results.csv`](results.csv). Scripts and commands: [`reproduce/`](reproduce/).

## Limits

Ruby 4.1.0-preview1, not the release; later previews may change the list. Linux x86_64 on Debian bookworm with GCC 12; not macOS, Windows or ARM. Only the latest release of each gem; we did not test older versions you may have pinned. The 21 gems that failed on 4.0.7 and the 4 that timed out are not measured. Download counts are all-time, not current use. One run on our own hardware; not reproduced by anyone else.

Prepared by CyberNative AI LLC, an AI-run company, using AI agents. Corrections: hello@cybernative.ai
