"""Generate reports/ATTRIBUTIONS.md from PyPI metadata and installed package files."""

import importlib.metadata
import json
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

_PYPI_URL = "https://pypi.org/pypi/{name}/{version}/json"
_TIMEOUT = 15
_WORKERS = 20


def _own_package_name() -> str:
    pyproject = Path("pyproject.toml")
    if pyproject.exists():
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        return data.get("project", {}).get("name", "")
    return ""


def _fetch_pypi(name: str, version: str) -> dict[str, str]:
    url = _PYPI_URL.format(name=name, version=version)
    try:
        with urlopen(url, timeout=_TIMEOUT) as resp:  # ruff: ignore[suspicious-url-open-usage]
            info = json.loads(resp.read())["info"]
        project_urls: dict[str, str] = info.get("project_urls") or {}
        return {
            "Author": info.get("author") or info.get("author_email") or "",
            "Description": info.get("summary") or "",
            "License": info.get("license_expression") or info.get("license") or "UNKNOWN",
            "Maintainer": info.get("maintainer") or info.get("maintainer_email") or "",
            "Name": info.get("name") or name,
            "URL": (
                project_urls.get("Homepage")
                or project_urls.get("Source")
                or project_urls.get("Repository")
                or info.get("home_page")
                or ""
            ),
            "Version": info.get("version") or version,
        }
    except (URLError, json.JSONDecodeError, KeyError, OSError):
        return {}


def _read_dist_file(dist: importlib.metadata.Distribution, prefixes: tuple[str, ...]) -> str:
    location = Path(str(dist.locate_file("")))
    for f in dist.files or []:
        fname = Path(f.name).name.upper()
        if any(fname.startswith(p.upper()) for p in prefixes):
            try:
                return Path(str(location / f)).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
    return ""


def _installed_metadata(name: str) -> dict[str, str]:
    try:
        dist = importlib.metadata.Distribution.from_name(name)
        meta = dist.metadata
        return {
            "Author": meta.get("Author") or meta.get("Author-email") or "",
            "Description": meta.get("Summary") or "",
            "License": meta.get("License") or "UNKNOWN",
            "LicenseText": _read_dist_file(dist, ("LICENSE", "LICENCE", "COPYING")),
            "Maintainer": meta.get("Maintainer") or meta.get("Maintainer-email") or "",
            "Name": meta.get("Name") or name,
            "NoticeText": _read_dist_file(dist, ("NOTICE",)),
            "URL": meta.get("Home-page") or "",
            "Version": meta.get("Version") or "",
        }
    except importlib.metadata.PackageNotFoundError:
        return {}


def _collect(name: str, version: str) -> dict[str, str]:
    installed = _installed_metadata(name)
    pypi = _fetch_pypi(name, version)
    merged = {**installed, **pypi}  # PyPI wins on metadata fields
    merged["LicenseText"] = installed.get("LicenseText", "")  # license text only from local files
    merged["NoticeText"] = installed.get("NoticeText", "")
    return merged


def _format_attribution(pkg: dict[str, str]) -> str:
    name = pkg.get("Name", "Unknown")
    version = pkg.get("Version", "Unknown")
    license_name = pkg.get("License", "Unknown")
    authors = pkg.get("Author", "")
    maintainers = pkg.get("Maintainer", "")
    url = pkg.get("URL", "")
    description = pkg.get("Description", "")

    out = f"## {name} ({version}) - {license_name}\n\n"
    if description:
        out += f"{description}\n\n"
    if url:
        out += f"* URL: {url}\n"
    if authors and authors != "UNKNOWN":
        out += f"* Author(s): {authors}\n"
    if maintainers and maintainers != "UNKNOWN":
        out += f"* Maintainer(s): {maintainers}\n"
    out += "\n"

    license_text = pkg.get("LicenseText", "")
    if license_text and license_text != "UNKNOWN":
        out += "### License Text\n\n"
        out += f"```\n{license_text.replace('```', '~~~')}\n```\n\n"

    notice_text = pkg.get("NoticeText", "")
    if notice_text and notice_text != "UNKNOWN":
        out += "### Notice\n\n"
        out += f"```\n{notice_text.replace('```', '~~~')}\n```\n\n"

    return out


def main() -> None:
    """Generate reports/ATTRIBUTIONS.md from PyPI metadata and installed package files."""
    own_name = _own_package_name().lower()

    seen: set[str] = set()
    packages: list[tuple[str, str]] = []
    for dist in importlib.metadata.distributions():
        name = dist.metadata.get("Name") or ""
        if not name or name.lower() == own_name or name.lower() in seen:
            continue
        seen.add(name.lower())
        packages.append((name, dist.metadata.get("Version") or ""))

    results: dict[str, dict[str, str]] = {}
    with ThreadPoolExecutor(max_workers=_WORKERS) as executor:
        futures = {executor.submit(_collect, name, version): name for name, version in packages}
        for future in as_completed(futures):
            pkg_name = futures[future]
            try:
                results[pkg_name] = future.result()
            except Exception as exc:  # ruff: ignore[blind-except]
                print(f"Warning: failed to collect {pkg_name}: {exc}", file=sys.stderr)

    content = "# Attributions\n\n"
    content += "[//]: # (This file is generated by mise run attributions)\n\n"
    content += "This project includes code from the following third-party open source projects:\n\n"
    for pkg in sorted(results.values(), key=lambda p: p.get("Name", "").casefold()):
        content += _format_attribution(pkg)
    content = content.rstrip() + "\n"

    Path("reports").mkdir(exist_ok=True)
    Path("reports/ATTRIBUTIONS.md").write_text(content, encoding="utf-8")
    print(f"Generated reports/ATTRIBUTIONS.md ({len(results)} packages)")


if __name__ == "__main__":
    main()
