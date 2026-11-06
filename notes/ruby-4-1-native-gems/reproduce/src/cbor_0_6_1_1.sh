#!/bin/bash
# Update 2026-11-06: cbor 0.6.1.1 (released 2026-11-05) under Bundler.
# Prints RUBY, INSTALL rc, REQUIRE_RUN rc, a round trip, and removed symbols left undefined in its shared objects.
set -u
W=/work/C0611-$ARM; rm -rf "$W"; mkdir -p "$W"; cd "$W"
export HOME="$W/home" BUNDLE_PATH="$W/bundle" BUNDLE_APP_CONFIG="$W/.bundle"; mkdir -p "$HOME"
printf 'source "https://rubygems.org"\ngem "cbor", "0.6.1.1"\n' > Gemfile
echo "RUBY $(ruby -e 'print RUBY_DESCRIPTION')"
bundle install --jobs 4 > install.txt 2>&1; echo "INSTALL rc=$?"; tail -3 install.txt
bundle exec ruby -e '
require "cbor"
v = {"a" => [1, 2.5, "x", nil, true]}
b = v.to_cbor
spec = Gem.loaded_specs["cbor"]
puts "CBOR #{spec.version} bytes=#{b.bytesize} roundtrip=#{CBOR.decode(b) == v}"
puts "SO #{Dir.glob(File.join(spec.full_gem_path, "**", "*.so")).join(" ")}"
' > run.txt 2>&1; echo "REQUIRE_RUN rc=$?"; head -20 run.txt
n=0; for so in $(sed -n 's/^SO //p' run.txt); do n=$((n + $(nm -D --undefined-only "$so" | awk '{print $NF}' | grep -c -x -F -f /src/data/removed.txt || true))); done
echo "REMOVED_UNDEFINED $n"
