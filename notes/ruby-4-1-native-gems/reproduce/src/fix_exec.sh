#!/bin/bash
# post-decision fix test (exploratory, after CONTINUE): does the upstream default-branch HEAD (pinned SHA) build+load on
# the same image, and does declaring tsort fix arm R? Each case: Gemfile, bundle install, bundle exec ruby -e <smoke>.
# Released-version rows are in-harness negative controls (expected to fail on 4.1.0-preview1, pass on 4.0.7).
set -u; OUT=/work/FIX-$ARM; mkdir -p $OUT; ruby -v > $OUT/ruby-v.txt
while IFS='|' read -r id gemlines code; do
  d=$OUT/$id; mkdir -p $d/app; cd $d/app
  printf 'source "https://rubygems.org"\n%b\n' "$gemlines" > Gemfile
  export BUNDLE_PATH=$d/bundle HOME=$d
  timeout -k 10 1200 bundle install > $d/install.log 2>&1; echo $? > $d/install.rc
  timeout -k 5 300 bundle exec ruby -e "$code; puts 'SMOKE_OK'" > $d/run.log 2>&1; echo $? > $d/run.rc
  cp Gemfile Gemfile.lock $d/ 2>/dev/null; rm -rf $d/bundle
done <<'LIST'
em-rel|gem "eventmachine", "1.2.7"|require "eventmachine"; EM.run { EM.add_timer(0.05) { EM.stop } }
em-head|gem "eventmachine", git: "https://github.com/eventmachine/eventmachine.git", ref: "e4f55083c576148e97c50cfdb6714b32eff224f6"|require "eventmachine"; EM.run { EM.add_timer(0.05) { EM.stop } }
thin-head|gem "eventmachine", git: "https://github.com/eventmachine/eventmachine.git", ref: "e4f55083c576148e97c50cfdb6714b32eff224f6"\ngem "thin", git: "https://github.com/macournoyer/thin.git", ref: "e7886a9bca2742586da74e06fffdd2093cc3a397"|require "thin"; Thin::HttpParser.new; puts Thin::VERSION::STRING
thin-rel-emhead|gem "eventmachine", git: "https://github.com/eventmachine/eventmachine.git", ref: "e4f55083c576148e97c50cfdb6714b32eff224f6"\ngem "thin", "2.0.1"|require "thin"; Thin::HttpParser.new; puts Thin::VERSION::STRING
yajl-rel|gem "yajl-ruby", "1.4.3"|require "yajl"; p Yajl::Parser.parse(%q({"a":[1,2]}))
yajl-head|gem "yajl-ruby", git: "https://github.com/brianmario/yajl-ruby.git", ref: "6501652d113557d976676134056aa983e7863020"|require "yajl"; p Yajl::Parser.parse(%q({"a":[1,2]}))
panko-rel|gem "panko_serializer", "0.8.5"|require "panko_serializer"; p Panko::VERSION
panko-head|gem "panko_serializer", git: "https://github.com/yosiat/panko_serializer.git", ref: "9267e19d779a05eae16ce0a2b2e36c3907c22e75"|require "panko_serializer"; p Panko::VERSION
molinillo-tsort|gem "molinillo", "0.8.0"\ngem "tsort"|require "molinillo"; Molinillo::DependencyGraph.new
mobility-tsort|gem "mobility", "1.3.2"\ngem "tsort"|require "mobility"
LIST
echo DONE > $OUT/DONE
