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

# An SBOM has to say what it describes, and Trivy names one after its scan target:
# left alone, both SBOMs below describe a thing called "requirements.txt" with no
# version, and every consumer that reads the root component as a package — Ketryx,
# Dependency-Track, GitHub's dependency graph — lists the scan target as if it were
# a dependency. Trivy has no flag for it, but `trivy convert` takes the name from
# ArtifactName, so set that and the per-target name to the project first. One
# rewrite, both formats.
read -r PROJECT_NAME PROJECT_VERSION <<<"$(uv version)"
if [[ -z "$PROJECT_NAME" || -z "$PROJECT_VERSION" ]]; then
    echo "Could not read the project name and version from 'uv version'" >&2
    exit 1
fi

# `.Results` is null, not empty, when a project has no dependencies at all.
SCAN_NAMED=$(mktemp)
jq --arg name "$PROJECT_NAME" \
    '.ArtifactName = $name | .Results = ((.Results // []) | map(.Target = $name))' \
    "$AUDIT_PROD_JSON" > "$SCAN_NAMED" || exit 1

trivy convert --format cyclonedx --output "$SBOM_CYCLONEDX" "$SCAN_NAMED" --quiet || exit 1
trivy convert --format spdx --output "$SBOM_SPDX" "$SCAN_NAMED" --quiet || exit 1
rm -f "$SCAN_NAMED"

# Two things `trivy convert` still cannot express, both only in CycloneDX:
#   - the root component's version, which it emits for container images and never
#     for a filesystem scan;
#   - the scan target, which it repeats as a second, purl-less component that the
#     packages hang off. Renaming it above only moved the problem: it would now be
#     a second component with the project's own name. Drop it and let the packages
#     hang off the root directly.
# No purl on the root: `pkg:pypi/...` would claim we publish to PyPI, and we publish
# to aignx-private-registry. Name and version identify the released subject, which
# is all CycloneDX asks of a root component.
jq --arg version "$PROJECT_VERSION" '
      (.components // []) as $components
    | (.dependencies // []) as $dependencies
    | (.metadata.component."bom-ref") as $root
    | ([$components[] | select(.type == "application" and (has("purl") | not)) | ."bom-ref"]) as $targets
    | ([$dependencies[] | select(.ref as $r | $targets | index($r)) | .dependsOn[]?]) as $packages
    | .metadata.component += {version: $version}
    | .components = ($components | map(select(."bom-ref" as $r | ($targets | index($r)) | not)))
    | .dependencies = ($dependencies | map(select(.ref as $r | ($targets | index($r)) | not))
                                     | map(if .ref == $root then .dependsOn = $packages else . end))
' "$SBOM_CYCLONEDX" > "$SBOM_CYCLONEDX.tmp" || exit 1
mv "$SBOM_CYCLONEDX.tmp" "$SBOM_CYCLONEDX"

# Trivy mints `pkg:pypi/<name>@<version>` for every pip package, which for our own
# packages is a false provenance claim: they are on aignx-private-registry and not
# on PyPI. A scanner resolving that purl either finds nothing or, worse, finds a
# public package that merely shares the name. purl's answer is the repository_url
# qualifier, and uv.lock records the registry each package actually resolved from.
# Only non-PyPI packages get it: qualifying the rest would stop their purls matching
# public vulnerability databases, which is the whole point of having them.
REGISTRIES=$(uv run python -c '
import json, pathlib, tomllib
lock = pathlib.Path("uv.lock")
packages = tomllib.loads(lock.read_text(encoding="utf-8")).get("package", []) if lock.is_file() else []
print(json.dumps({
    package["name"]: package["source"]["registry"]
    for package in packages
    if "pypi.org" not in package.get("source", {}).get("registry", "pypi.org")
}))
') || exit 1

# `bom-ref` is left alone on purpose: it is an opaque identifier that the dependency
# graph refers to, and trivy happens to spell it like the purl. Rewriting it here
# would mean rewriting every edge that points at it.
jq --argjson registries "$REGISTRIES" '
      .components |= map(
          if .purl and $registries[.name]
          then .purl += "?repository_url=" + $registries[.name]
          else . end)
' "$SBOM_CYCLONEDX" > "$SBOM_CYCLONEDX.tmp" || exit 1
mv "$SBOM_CYCLONEDX.tmp" "$SBOM_CYCLONEDX"
pretty_json "$SBOM_CYCLONEDX"

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
