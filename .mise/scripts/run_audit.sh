#!/usr/bin/env bash
# Usage:
#   mise run audit                                              # strict: any vuln or illegal prod license fails
#   mise run audit --baseline <path> --baseline-all <path>    # PR diff: only new findings fail
#   bash .mise/scripts/run_audit.sh --scan-only               # produce scan JSONs, skip SBOM and comparison
set -uo pipefail

BASELINE=""
BASELINE_ALL=""
SCAN_ONLY=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --baseline)     BASELINE="$2";     shift 2 ;;
    --baseline-all) BASELINE_ALL="$2"; shift 2 ;;
    --scan-only)    SCAN_ONLY=1;       shift ;;
    *) echo "Unknown argument: $1" >&2; exit 2 ;;
  esac
done

AUDIT_PROD_JSON="reports/audit-prod.json"
AUDIT_ALL_JSON="reports/audit-all.json"
SBOM_CYCLONEDX="reports/sbom.json"
SBOM_SPDX="reports/sbom.spdx"

mkdir -p reports

pretty_json() { jq . "$1" > "$1.tmp" && mv "$1.tmp" "$1"; }

# Requirements exports are scan input only, not artifacts: drop them however we exit.
# They live in the project root because trivy records the scanned path in the report,
# and baselines are compared against those paths.
SCAN_DIR_DEV=$(mktemp -d)
trap 'rm -rf requirements.txt requirements-dev.txt "$SCAN_DIR_DEV"' EXIT

uv export --all-extras --format requirements-txt --no-dev --output-file requirements.txt --quiet
uv export --all-extras --format requirements-txt --output-file requirements-dev.txt --quiet

# Trivy's pip analyzer only triggers on files named "requirements.txt".
# Copy dev requirements to a temp dir under that name for the all-packages scan.
cp requirements-dev.txt "$SCAN_DIR_DEV/requirements.txt"

# Scan 1: production packages — vuln + license (source for SBOMs and prod compliance)
trivy fs requirements.txt \
    --list-all-pkgs --scanners vuln,license \
    --ignorefile .trivyignore \
    --format json --output "$AUDIT_PROD_JSON" \
    --quiet
pretty_json "$AUDIT_PROD_JSON"

# Scan 2: all packages including dev — vuln only (license compliance does not apply to dev-only deps)
trivy fs "$SCAN_DIR_DEV/requirements.txt" \
    --list-all-pkgs --scanners vuln \
    --ignorefile .trivyignore \
    --format json --output "$AUDIT_ALL_JSON" \
    --quiet
pretty_json "$AUDIT_ALL_JSON"

[[ "$SCAN_ONLY" -eq 1 ]] && exit 0

# SBOM outputs derived from prod scan — no re-scan needed
trivy convert --format cyclonedx --output "$SBOM_CYCLONEDX" "$AUDIT_PROD_JSON" --quiet
pretty_json "$SBOM_CYCLONEDX"
trivy convert --format spdx --output "$SBOM_SPDX" "$AUDIT_PROD_JSON" --quiet

exit_code=0

PROD_ARGS=(--current "$AUDIT_PROD_JSON" --scope "Production")
[[ -n "$BASELINE" ]] && PROD_ARGS+=(--baseline "$BASELINE")
uv run .mise/scripts/audit_compare.py "${PROD_ARGS[@]}" || exit_code=1

# In PR mode without a dev baseline, skip: treating all dev vulns as "new" would block PRs on pre-existing issues.
if [[ -z "$BASELINE" ]] || [[ -n "$BASELINE_ALL" ]]; then
    echo ""
    ALL_ARGS=(--current "$AUDIT_ALL_JSON" --scope "All packages (incl. dev)" --no-license-check)
    [[ -n "$BASELINE_ALL" ]] && ALL_ARGS+=(--baseline "$BASELINE_ALL")
    uv run .mise/scripts/audit_compare.py "${ALL_ARGS[@]}" || exit_code=1
fi

exit "$exit_code"
