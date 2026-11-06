#!/bin/bash
# Update 2026-11-06: panko_serializer 1.0.0 (released that day) under Bundler.
# Prints RUBY, INSTALL rc, REQUIRE_RUN rc, the gem's extensions and a serialized test array.
set -u
W=/work/P100-$ARM; rm -rf "$W"; mkdir -p "$W"; cd "$W"
export HOME="$W/home" BUNDLE_PATH="$W/bundle" BUNDLE_APP_CONFIG="$W/.bundle"; mkdir -p "$HOME"
printf 'source "https://rubygems.org"\ngem "panko_serializer", "1.0.0"\n' > Gemfile
echo "RUBY $(ruby -e 'print RUBY_DESCRIPTION')"
bundle install --jobs 4 > install.txt 2>&1; echo "INSTALL rc=$?"; tail -3 install.txt
bundle exec ruby -e '
require "panko_serializer"
Thing = Struct.new(:id, :name)
class ThingSerializer < Panko::Serializer
  attributes :id, :name
end
s = Panko::ArraySerializer.new([Thing.new(1, "a"), Thing.new(2, "b")], each_serializer: ThingSerializer).to_json
spec = Gem.loaded_specs["panko_serializer"]
puts "PANKO #{Panko::VERSION} extensions=#{spec.extensions.inspect} so_files=#{Dir.glob(File.join(spec.full_gem_path, "**", "*.so")).size}"
puts "JSON #{s}"
' > run.txt 2>&1; echo "REQUIRE_RUN rc=$?"; head -20 run.txt
grep -E '^ +(panko_serializer|oj|activesupport) ' Gemfile.lock
