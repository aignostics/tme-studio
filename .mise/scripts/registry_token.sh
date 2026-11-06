# shellcheck shell=sh
# Sourced by mise (`[env] _.source` in mise.toml) on every prompt and task: hands uv the
# private Artifact Registry token from gcloud (user login, else application default
# credentials). A password already set (CI) is left alone.
#
# Never fails, and never sets an empty password: a failing sourced script breaks mise's
# whole environment, and an empty password stops uv from falling back to keyring.
#
# When gcloud is itself a mise shim, calling it loads this environment again, which sources
# this script again: without the guard every prompt forks gcloud until the machine runs out of
# processes. The guard is exported so the nested load sees it and skips the call.
if [ -z "${UV_INDEX_AIGNX_PRIVATE_REGISTRY_PASSWORD:-}" ] && [ -z "${_REGISTRY_TOKEN_FETCHING:-}" ]; then
  _registry_token="$(_REGISTRY_TOKEN_FETCHING=1 gcloud auth print-access-token 2> /dev/null ||
    _REGISTRY_TOKEN_FETCHING=1 gcloud auth application-default print-access-token 2> /dev/null)" || _registry_token=""
  if [ -n "$_registry_token" ]; then
    export UV_INDEX_AIGNX_PRIVATE_REGISTRY_PASSWORD="$_registry_token"
  else
    # Say what to do, at most once a day: this runs on every prompt.
    _registry_stamp="${XDG_CACHE_HOME:-$HOME/.cache}/mise/registry-token-hint"
    if [ -z "$(find "$_registry_stamp" -mmin -1440 2> /dev/null)" ]; then
      echo "mise: no registry token from gcloud; uv falls back to keyring. Fix: gcloud auth login --update-adc (no gcloud? mise use -g gcloud)" >&2
      mkdir -p "${_registry_stamp%/*}" 2> /dev/null && : > "$_registry_stamp" 2> /dev/null
    fi
    unset _registry_stamp
  fi
  unset _registry_token
fi
true
