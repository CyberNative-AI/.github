#!/bin/sh
# Usage: run_cases.sh ENVS_DIR [CASES_TSV]   (ENVS_DIR/<venv>/bin/python per case; see cases.tsv)
# Per case: normal, all, and all with the cases.tsv names kept eager; 2 repeats each.
envs=$1; here=$(dirname "$0"); cases=${2:-$here/cases.tsv}
grep -v "^#" "$cases" | while IFS="$(printf '\t')" read -r case pkg eager; do
  venv=${pkg%%==*}
  for arm in normal all filter; do
    mode=$arm; [ "$arm" = filter ] && mode=all
    for rep in 1 2; do
      if [ "$arm" = filter ]; then e=$eager; else e=; fi
      out=$(cd /tmp && LAZY_EAGER=$e PYTHONHASHSEED=0 timeout 60 "$envs/$venv/bin/python" -X lazy_imports=$mode -W ignore "$here/check.py" "$case" 2>/dev/null | tail -1)
      printf '%s\t%s\t%s\t%s\t%s\n' "$case" "$arm" "${e:--}" "$rep" "$out"
    done
  done
done
