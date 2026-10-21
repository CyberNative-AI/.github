#!/bin/bash
# post-hoc arm R execution: Gemfile with one gem, bundle install, bundle exec require + touch the tsort/prism path.
set -u; OUT=/work/R-$ARM; mkdir -p $OUT; ruby -v > $OUT/ruby-v.txt
while IFS='|' read -r gem code; do
  d=$OUT/$gem; mkdir -p $d/app; cd $d/app
  printf 'source "https://rubygems.org"\ngem "%s"\n' "$gem" > Gemfile
  export BUNDLE_PATH=$d/bundle HOME=$d
  timeout -k 10 900 bundle install --quiet > $d/install.log 2>&1; echo $? > $d/install.rc
  timeout -k 5 300 bundle exec ruby -e "$code; puts 'LOADED'" > $d/run.log 2>&1; echo $? > $d/run.rc
  grep -h -E "^ *(prism|tsort|molinillo|cocoapods|net-ftp) " Gemfile.lock > $d/lock.txt 2>/dev/null
  rm -rf $d/bundle
done <<'LIST'
molinillo|require "molinillo"; Molinillo::DependencyGraph.new
cocoapods|require "cocoapods"; Molinillo::DependencyGraph.new
facter|require "facter"; require "facter/custom_facts/core/directed_graph"
mobility|require "mobility"
packwerk|require "packwerk"; Packwerk::Graph
railties|require "rails"; require "rails/test_unit/test_parser"; p defined?(Prism)
simplecov|require "simplecov"; p SimpleCov::VERSION
LIST
echo DONE > $OUT/DONE
