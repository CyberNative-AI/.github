#!/bin/sh
# Usage: scripts/check-binary.sh FILE...   (a .so, .a, .dylib-free ELF executable or object)
# Prints which rustc built each file, from two traces that usually survive release builds:
#   1. the "rustc version X.Y.Z" string rustc writes into the ELF .comment section;
#   2. the /rustc/<commit> paths that the standard library leaves in panic messages.
# Rust 1.99.0 is commit b940084d7eb6a299eb4bfeb8e34901bc051e7ac4.
# Exits 2 if a FILE is missing or unreadable.
[ $# -gt 0 ] || { echo "usage: $0 FILE..." >&2; exit 2; }
status=0
for f in "$@"; do
  if [ ! -f "$f" ] || [ ! -r "$f" ]; then
    echo "$f: not a readable file" >&2; status=2; continue
  fi
  # Pass the name as a literal path: "./" stops readelf and strings from reading
  # "-x" as an option or "@x" as a file of more arguments.
  case "$f" in /*) p=$f ;; *) p=./$f ;; esac
  c=$(readelf -p .comment "$p" 2>/dev/null | grep -o 'rustc version [^)]*)' | sort -u | paste -sd';' -)
  h=$(strings -a "$p" 2>/dev/null | grep -o '/rustc/[0-9a-f]\{40\}' | sort -u | cut -c8-19 | paste -sd' ' -)
  verdict=ok
  case "$c $h" in
    *"rustc version 1.99.0 "*|*b940084d7eb6*) verdict="BUILT WITH 1.99.0: rebuild with 1.99.1 if it exports functions returning bool" ;;
    " ") verdict="no rustc trace found (not Rust, or both traces removed)" ;;
  esac
  printf '%s\n  .comment: %s\n  std commit: %s\n  -> %s\n' "$f" "${c:-none}" "${h:-none}" "$verdict"
done
exit $status
