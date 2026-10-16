#!/bin/sh
# Runs inside rust:1-slim-trixie (linux/amd64), with this directory mounted at /w and an
# output directory at /out. Optional $1: a toolchain to install with rustup first (1.99.1).
set -eu
if [ -n "${1:-}" ]; then
  rustup toolchain install "$1" --profile minimal >/dev/null 2>&1
  rustup default "$1" >/dev/null
fi
V=$(rustc -V | cut -d' ' -f2); O=/out/$V; mkdir -p "$O"
rustc -vV > "$O/rustc-vV.txt"
cp -r /w /tmp/src; cd /tmp/src
T=/tmp/t

build() { # $1 = name, rest = env assignments for the release profile
  n=$1; shift
  env "$@" CARGO_TARGET_DIR=$T/$n cargo build --release -q
}
shapes() { # $1 = lib dir, $2 = label, $3 = gcc opt
  gcc -"$3" caller.c -L"$1" -lflagcheck -o "$1/caller_$3"
  echo "== $2, C caller gcc -$3"
  LD_LIBRARY_PATH="$1" "$1/caller_$3"
}

{ # 1. Which shapes return a false that is not 0/1
  build default
  shapes $T/default/release "release lib" O0
  shapes $T/default/release "release lib" O2
  CARGO_TARGET_DIR=$T/debug cargo build -q
  shapes $T/debug/debug "debug lib" O2
} > "$O/shapes.txt" 2>&1

{ # 2. Does the rustc version survive stripping and static linking?
  build strip CARGO_PROFILE_RELEASE_STRIP=true
  build lto CARGO_PROFILE_RELEASE_STRIP=true CARGO_PROFILE_RELEASE_LTO=fat \
    CARGO_PROFILE_RELEASE_CODEGEN_UNITS=1 CARGO_PROFILE_RELEASE_PANIC=abort
  gcc -O2 caller.c $T/default/release/libflagcheck.a -o $T/caller_static
  cp $T/caller_static $T/caller_static_stripped; strip --strip-all $T/caller_static_stripped
  objcopy --remove-section .comment $T/strip/release/libflagcheck.so $T/no-comment.so
  for f in $T/default/release/libflagcheck.so $T/strip/release/libflagcheck.so \
           $T/lto/release/libflagcheck.so $T/default/release/libflagcheck.a \
           $T/caller_static $T/caller_static_stripped $T/no-comment.so; do
    echo "## ${f#$T/}"
    echo "readelf -p .comment:"; readelf -p .comment "$f" 2>&1 | grep -E 'rustc version|GCC:' | sed 's/^ *\[ *[0-9a-f]*\] */  /' | sort -u || true
    sh /w/scripts/check-binary.sh "$f" | sed 1d
  done
  echo "## the stripped static C program and the LTO+strip lib still misbehave?"
  $T/caller_static_stripped | tail -1
  shapes $T/lto/release "lto+strip lib" O2 | tail -1
  echo "## exported functions nm -D still lists after strip = true"
  nm -D --defined-only $T/strip/release/libflagcheck.so | grep -c ' T ' || true
  echo "## objdump of two exported functions (release lib before strip)"
  for fn in is_flag_set is_odd; do
    objdump -d --no-show-raw-insn --disassemble=$fn $T/default/release/libflagcheck.so | grep -A6 "<$fn>:" || true
  done
} > "$O/binary-checks.txt" 2>&1
mkdir -p "$O/libs"; cp $T/default/release/libflagcheck.so "$O/libs/"
