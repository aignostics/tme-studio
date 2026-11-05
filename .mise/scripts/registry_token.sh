# shellcheck shell=sh
# Sourced by mise (`[env] _.source` in mise.toml) on every prompt and task: hands uv the
# private Artifact Registry token from gcloud (user login, else application default
# credentials). A password already set (CI) is left alone.
#
# Never fails, and never sets an empty password: a failing sourced script breaks mise's
# whole environment, and an empty password stops uv from falling back to keyring.
if [ -z "${UV_INDEX_AIGNX_PRIVATE_REGISTRY_PASSWORD:-}" ]; then
  _registry_token="$(gcloud auth print-access-token 2> /dev/null ||
    gcloud auth application-default print-access-token 2> /dev/null)" || _registry_token=""
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
