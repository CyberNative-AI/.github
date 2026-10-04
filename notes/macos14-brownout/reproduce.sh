#!/usr/bin/env bash
# A read-only comparison of one public setup-uv workflow at pinned revisions.
set -euo pipefail

if [[ $# -ne 1 || -z "$1" ]]; then
  printf 'Usage: bash reproduce.sh OUTPUT_DIRECTORY\n' >&2
  exit 2
fi

for required in curl rg; do
  command -v "$required" >/dev/null || { printf 'Missing command: %s\n' "$required" >&2; exit 2; }
done

output_dir=$1
if [[ -e "$output_dir" ]]; then
  printf 'Choose a new output directory; this path already exists.\n' >&2
  exit 2
fi
mkdir -p -- "$output_dir/before/.github/workflows" "$output_dir/after/.github/workflows"

curl -fsS --max-time 30 \
  'https://raw.githubusercontent.com/astral-sh/setup-uv/a96208bed1fb5efb8da349c9bcc6cc58af9e7d74/.github/workflows/test.yml' \
  -o "$output_dir/before/.github/workflows/test.yml"
curl -fsS --max-time 30 \
  'https://raw.githubusercontent.com/astral-sh/setup-uv/51fdd265d38a27ffcbca0da885510bc6fcc0ff55/.github/workflows/test.yml' \
  -o "$output_dir/after/.github/workflows/test.yml"

for revision in before after; do
  printf '%s\n' "$revision"
  (
    cd -- "$output_dir/$revision"
    search_status=0
    rg -n --hidden --glob '*.yml' --glob '*.yaml' \
      '\bmacos-14(-large|-xlarge)?\b' .github/workflows || search_status=$?
    case "$search_status" in
      0) ;;
      1) printf 'No literal matches in the downloaded workflow.\n' ;;
      *) exit "$search_status" ;;
    esac
  )
done
