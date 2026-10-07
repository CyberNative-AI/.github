#!/usr/bin/env bash
# Compare what `pnpm run` does right after `pnpm install --frozen-lockfile`,
# outside CI, with autoDedupe enabled. Follows the reproduction in pnpm/pnpm#16583.
#
# usage: bash check.sh /path/to/pnpm-A [/path/to/pnpm-B ...]  > result.json
#
# Each case runs in a fresh temporary project, HOME and store; CI is unset.
# Needs network access to the npm registry (installs is-number 7.0.0 and 6.0.0).
set -uo pipefail

json_escape() { python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))'; }

isolate() {  # isolate <dir>: fresh project dir with its own HOME and store
  rm -rf "$1"; mkdir -p "$1/home" "$1/p"
  export HOME="$1/home" XDG_CONFIG_HOME="$1/home/.config" XDG_DATA_HOME="$1/home/.data" \
         XDG_CACHE_HOME="$1/home/.cache" XDG_STATE_HOME="$1/home/.state"
  unset CI GITHUB_ACTIONS pnpm_config_frozen_lockfile
  cd "$1/p"
}

write_project() {  # write_project <opt-in: yes|no>
  printf 'autoDedupe: true\n' > pnpm-workspace.yaml
  if [ "$1" = yes ]; then printf 'lockfile:\n  includeResolutionSettings: true\n' >> pnpm-workspace.yaml; fi
  cat > package.json <<'J'
{
  "name": "repro",
  "private": true,
  "scripts": { "postinstall": "echo POSTINSTALL", "hello": "echo hello" },
  "devDependencies": { "is-number": "7.0.0" }
}
J
}

# Case "deploy": a dependency changes (simulated git pull), then
#   pnpm install --frozen-lockfile && pnpm run hello
# Reports how many times the postinstall script ran during `pnpm run`.
deploy_case() {  # deploy_case <pnpm> <opt-in yes|no> <frozen env on run: yes|no>
  local P=$1 OPT=$2 ENVRUN=$3 W
  W=$(mktemp -d); isolate "$W"; write_project "$OPT"
  if ! "$P" install >/dev/null 2>&1; then echo '"first_install_failed"'; cd /; rm -rf "$W"; return; fi
  cp package.json package.v1.json; cp pnpm-lock.yaml lock.v1.yaml
  "$P" add -D is-number@6.0.0 >/dev/null 2>&1
  cp package.json package.v2.json; cp pnpm-lock.yaml lock.v2.yaml
  cp package.v1.json package.json; cp lock.v1.yaml pnpm-lock.yaml; "$P" install >/dev/null 2>&1
  cp package.v2.json package.json; cp lock.v2.yaml pnpm-lock.yaml
  local F R L0 L1
  F=$("$P" install --frozen-lockfile 2>&1)
  L0=$(sha256sum pnpm-lock.yaml | cut -d' ' -f1)
  if [ "$ENVRUN" = yes ]; then R=$(pnpm_config_frozen_lockfile=true "$P" run hello 2>&1)
  else R=$("$P" run hello 2>&1); fi
  L1=$(sha256sum pnpm-lock.yaml | cut -d' ' -f1)
  printf '{"postinstall_runs_during_frozen_install": %s, "postinstall_runs_during_pnpm_run": %s, "script_ran": %s, "lockfile_changed_by_run": %s}' \
    "$(grep -c 'postinstall: POSTINSTALL' <<<"$F")" "$(grep -c 'postinstall: POSTINSTALL' <<<"$R")" \
    "$(grep -qx 'hello' <<<"$R" && echo true || echo false)" "$([ "$L0" = "$L1" ] && echo false || echo true)"
  cd /; rm -rf "$W"
}

# Case "parse": a project whose pnpm-workspace.yaml contains the opt-in setting and
# whose package.json pins "packageManager": "pnpm@12.10.1". Plain `pnpm install`.
parse_case() {  # parse_case <pnpm>
  local P=$1 W OUT CODE
  W=$(mktemp -d); isolate "$W"; write_project yes
  python3 - <<'PY'
import json; p=json.load(open("package.json")); p["packageManager"]="pnpm@12.10.1"
json.dump(p, open("package.json","w"), indent=2)
PY
  OUT=$("$P" install 2>&1); CODE=$?
  printf '{"exit_code": %s, "workspace_yaml_parse_error": %s, "pnpm_version_that_installed": %s}' "$CODE" \
    "$(grep -q 'expected string scalar' <<<"$OUT" && echo true || echo false)" \
    "$(grep -o 'using pnpm v[0-9.]*' <<<"$OUT" | tail -1 | sed 's/using pnpm v//' | json_escape)"
  cd /; rm -rf "$W"
}

# Case "drift": package.json gains a dependency that pnpm-lock.yaml does not record.
# Records the exit code of `pnpm install --frozen-lockfile`, then runs
# `pnpm run` with pnpm_config_frozen_lockfile=true. Does the script still run,
# and can it load the new dependency?
drift_case() {  # drift_case <pnpm>
  local P=$1 W R CODE
  W=$(mktemp -d); isolate "$W"; write_project no
  python3 - <<'PY2'
import json; p=json.load(open("package.json"))
p["scripts"]["hello"]="node -e \"try{require('is-odd');console.log('is-odd loaded')}catch(e){console.log('is-odd missing')}\""
json.dump(p, open("package.json","w"), indent=2)
PY2
  "$P" install >/dev/null 2>&1
  python3 - <<'PY2'
import json; p=json.load(open("package.json")); p["devDependencies"]["is-odd"]="3.0.1"
json.dump(p, open("package.json","w"), indent=2)
PY2
  "$P" install --frozen-lockfile >/dev/null 2>&1; local FCODE=$?
  R=$(pnpm_config_frozen_lockfile=true "$P" run hello 2>&1); CODE=$?
  printf '{"frozen_install_exit_code": %s, "run_exit_code": %s, "warned_install_failed": %s, "script_output": %s}' "$FCODE" "$CODE" \
    "$(grep -q 'The install that runs before scripts failed' <<<"$R" && echo true || echo false)" \
    "$(grep -E '^is-odd (loaded|missing)$' <<<"$R" | json_escape)"
  cd /; rm -rf "$W"
}

echo '{'
echo '  "conditions": "Linux; CI unset; autoDedupe: true; fresh HOME and store per case; postinstall counted by its output line",'
first=1
for P in "$@"; do
  P=$(realpath "$P"); V=$(cd / && "$P" --version)
  [ $first = 1 ] || echo ','; first=0
  printf '  "%s": {\n' "$V"
  printf '    "sha256": "%s",\n' "$(sha256sum "$P" | cut -d' ' -f1)"
  printf '    "deploy_default": %s,\n' "$(deploy_case "$P" no no)"
  printf '    "deploy_opt_in_includeResolutionSettings": %s,\n' "$(deploy_case "$P" yes no)"
  printf '    "deploy_default_with_frozen_env_on_run": %s,\n' "$(deploy_case "$P" no yes)"
  printf '    "opt_in_yaml_with_packageManager_pin": %s,\n' "$(parse_case "$P")"
  printf '    "stale_lockfile_with_frozen_env_on_run": %s\n' "$(drift_case "$P")"
  printf '  }'
done
echo; echo '}'
