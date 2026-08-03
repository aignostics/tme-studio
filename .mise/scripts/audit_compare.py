r"""Compare a current Trivy audit JSON against a baseline.

Detects new vulnerabilities and new license violations introduced by a PR.
Exits 0 when no new findings are detected, 1 otherwise.

Usage:
    uv run .mise/scripts/audit_compare.py \
        --current  reports/audit.json \
        --baseline reports/audit-baseline.json \
        [--config  pyproject.toml] \
        [--scope   "Production"] \
        [--no-license-check]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any


def _vuln_ids(audit: dict[str, Any]) -> set[str]:
    ids: set[str] = set()
    for result in audit.get("Results") or []:
        for vuln in result.get("Vulnerabilities") or []:
            vid = vuln.get("VulnerabilityID")
            if isinstance(vid, str) and vid:
                ids.add(vid)
    return ids


def _spdx_tokens(expression: str) -> list[str]:
    """Extract individual license identifiers from an SPDX expression.

    Handles compound expressions such as 'Apache-2.0 AND MIT' or
    'MPL-2.0 AND (Apache-2.0 OR MIT)' by stripping parentheses and
    splitting on AND/OR/WITH operators only, preserving multi-word
    license names like 'Python Software Foundation License'.

    Returns:
        List of individual license identifier strings.
    """
    cleaned = re.sub(r"[()]", " ", expression)
    tokens = re.split(r"\s+(?:AND|OR|WITH)\s+", cleaned)
    return [t.strip() for t in tokens if t.strip()]


def _license_violations(audit: dict[str, Any], allowed: frozenset[str], ignored_pkgs: frozenset[str]) -> set[str]:
    violations: set[str] = set()
    for result in audit.get("Results") or []:
        for pkg in result.get("Packages") or []:
            name = pkg.get("Name", "")
            version = pkg.get("Version", "")
            if name.lower() in ignored_pkgs or f"{name}@{version}".lower() in ignored_pkgs:
                continue
            for lic in pkg.get("Licenses") or []:
                if isinstance(lic, str) and not all(t.lower() in allowed for t in _spdx_tokens(lic)):
                    violations.add(f"{name}@{version}: {lic}")
    return violations


def compare_audits(
    current: dict[str, Any],
    baseline: dict[str, Any] | None,
    allowed_licenses: frozenset[str],
    ignored_pkgs: frozenset[str] = frozenset(),
) -> tuple[set[str], set[str], set[str], set[str]]:
    """Return (new_vulnerabilities, new_license_violations, existing_vulnerabilities, existing_license_violations).

    new_* contains findings present in current but absent from baseline.
    existing_* contains findings present in both current and baseline.
    When baseline is None every finding in current is treated as new and existing_* are empty.
    """
    current_vulns = _vuln_ids(current)
    baseline_vulns = _vuln_ids(baseline) if baseline is not None else set()
    new_vulns = current_vulns - baseline_vulns
    existing_vulns = current_vulns & baseline_vulns

    current_violations = _license_violations(current, allowed_licenses, ignored_pkgs)
    baseline_violations = (
        _license_violations(baseline, allowed_licenses, ignored_pkgs) if baseline is not None else set()
    )
    new_violations = current_violations - baseline_violations
    existing_violations = current_violations & baseline_violations

    return new_vulns, new_violations, existing_vulns, existing_violations


def _load_audit_config(config_path: Path) -> tuple[frozenset[str], frozenset[str]]:
    """Load allowed_licenses and ignored_packages from [tool.audit] in a TOML file.

    Both sets are empty if the section or file is absent.

    Returns:
        Tuple of (allowed_licenses, ignored_packages) as lowercased frozensets.
    """
    if not config_path.exists():
        return frozenset(), frozenset()
    with config_path.open("rb") as f:
        data = tomllib.load(f)
    audit = data.get("tool", {}).get("audit", {})
    allowed = frozenset(s.lower() for s in audit.get("allowed_licenses", []))
    ignored = frozenset(s.lower() for s in audit.get("ignored_packages", []))
    return allowed, ignored


def _report_vulns(new_vulns: set[str], existing_vulns: set[str], *, has_baseline: bool, header: str) -> int:
    print(f"=== {header} ===")
    if new_vulns:
        print("New vulnerabilities introduced by this PR:" if has_baseline else "Vulnerabilities found:")
        for vid in sorted(new_vulns):
            print(f"  {vid}")
    else:
        print("No new vulnerabilities introduced." if has_baseline else "No vulnerabilities found.")
    if existing_vulns:
        print("Pre-existing vulnerabilities (not introduced by this PR):")
        for vid in sorted(existing_vulns):
            print(f"  {vid}")
    return 0 if not new_vulns else 1


def _report_licenses(
    new_violations: set[str],
    existing_violations: set[str],
    *,
    has_baseline: bool,
    header: str,
) -> int:
    print(f"=== {header} ===")
    if new_violations:
        print("New license violations introduced by this PR:" if has_baseline else "License violations found:")
        for v in sorted(new_violations):
            print(f"  {v}")
    else:
        print("No new license violations introduced." if has_baseline else "All licenses are compliant.")
    if existing_violations:
        print("Pre-existing license violations (not introduced by this PR):")
        for v in sorted(existing_violations):
            print(f"  {v}")
    return 0 if not new_violations else 1


def main(argv: list[str] | None = None) -> int:
    """Entry point for CLI use.

    Returns:
        0 if no new findings, 1 if new findings were detected.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--current", required=True, type=Path)
    parser.add_argument("--baseline", type=Path, default=None)
    parser.add_argument(
        "--config", type=Path, default=Path("pyproject.toml"), help="TOML file with [tool.audit] section"
    )
    parser.add_argument("--scope", default="", help="Label prefixed to section headers (e.g. 'Production')")
    parser.add_argument(
        "--no-license-check",
        action="store_true",
        default=False,
        help="Skip license compliance check entirely (use for dev-only scans)",
    )
    args = parser.parse_args(argv)

    current = json.loads(args.current.read_text())
    baseline = json.loads(args.baseline.read_text()) if args.baseline and args.baseline.exists() else None
    allowed, ignored_pkgs = _load_audit_config(args.config)
    check_licenses = bool(allowed) and not args.no_license_check

    new_vulns, new_violations, existing_vulns, existing_violations = compare_audits(
        current, baseline, allowed, ignored_pkgs
    )

    scope = f"{args.scope}: " if args.scope else ""
    has_baseline = baseline is not None
    exit_code = _report_vulns(
        new_vulns, existing_vulns, has_baseline=has_baseline, header=f"{scope}Vulnerability Check"
    )

    if check_licenses:
        print()
        exit_code |= _report_licenses(
            new_violations, existing_violations, has_baseline=has_baseline, header=f"{scope}License Compliance Check"
        )

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
