#!/usr/bin/env python3
"""Generate a repository-owned GitHub telemetry SVG from public API data."""

from __future__ import annotations

import html
import json
import os
from collections import Counter
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "research-dashboard.svg"
API = "https://api.github.com"
COLORS = ["#DA3633", "#D29922", "#3FB950", "#8B949E", "#6E7681"]


def api_get(path: str) -> object:
    token = os.environ.get("GITHUB_TOKEN", "")
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "yuze-profile-dashboard",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(f"{API}{path}", headers=headers)
    with urlopen(request, timeout=20) as response:
        return json.load(response)


def safe_int(value: object) -> int:
    return value if isinstance(value, int) else 0


def text(value: object) -> str:
    return html.escape(str(value), quote=True)


def build_svg(username: str, profile: dict[str, object], repos: list[dict[str, object]]) -> str:
    visible = [repo for repo in repos if not repo.get("fork")]
    stars = sum(safe_int(repo.get("stargazers_count")) for repo in visible)
    forks = sum(safe_int(repo.get("forks_count")) for repo in visible)
    languages = Counter(
        str(repo["language"])
        for repo in visible
        if isinstance(repo.get("language"), str) and repo["language"]
    )
    language_total = sum(languages.values()) or 1
    top_languages = languages.most_common(5)

    segments: list[str] = []
    labels: list[str] = []
    cursor = 0.0
    for index, (language, count) in enumerate(top_languages):
        width = 760 * count / language_total
        segments.append(
            f'<rect x="{32 + cursor:.1f}" y="225" width="{width:.1f}" height="10" '
            f'fill="{COLORS[index]}"/>'
        )
        labels.append(
            f'<circle cx="{42 + index * 150}" cy="264" r="4" fill="{COLORS[index]}"/>'
            f'<text x="{52 + index * 150}" y="268" fill="#8B949E" font-size="13">'
            f'{text(language)} {count / language_total:.0%}</text>'
        )
        cursor += width

    if not top_languages:
        segments.append('<rect x="32" y="225" width="760" height="10" fill="#30363D"/>')
        labels.append('<text x="32" y="268" fill="#8B949E" font-size="13">NO LANGUAGE DATA</text>')

    login = text(profile.get("login", username))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="300" viewBox="0 0 1200 300" role="img" aria-labelledby="title desc">
  <title id="title">GitHub telemetry for {login}</title>
  <desc id="desc">Public repository, follower, star, fork, and language summary generated from GitHub data.</desc>
  <defs><style>.mono {{ font-family: ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,Liberation Mono,monospace; }}</style></defs>
  <rect width="1200" height="300" rx="14" fill="#0D1117"/>
  <rect x="1" y="1" width="1198" height="298" rx="13" fill="none" stroke="#30363D"/>
  <g class="mono">
    <text x="32" y="39" fill="#8B949E" font-size="14" letter-spacing=".8">GITHUB TELEMETRY / {login}</text>
    <text x="1168" y="39" text-anchor="end" fill="#3FB950" font-size="14">SYNCED</text>
    <path d="M32 60H1168" stroke="#30363D"/>
    <g fill="#8B949E" font-size="13" letter-spacing=".6"><text x="32" y="94">PUBLIC REPOS</text><text x="262" y="94">FOLLOWERS</text><text x="492" y="94">STARS</text><text x="722" y="94">FORKS</text></g>
    <g fill="#E6EDF3" font-size="34" font-weight="700"><text x="32" y="139">{safe_int(profile.get("public_repos"))}</text><text x="262" y="139">{safe_int(profile.get("followers"))}</text><text x="492" y="139">{stars}</text><text x="722" y="139">{forks}</text></g>
    <path d="M242 78V150M472 78V150M702 78V150M932 78V150" stroke="#30363D"/>
    <text x="32" y="194" fill="#8B949E" font-size="13" letter-spacing=".6">REPOSITORY LANGUAGE DISTRIBUTION</text>
    {''.join(segments)}
    {''.join(labels)}
  </g>
</svg>
'''


def main() -> int:
    username = os.environ.get("GITHUB_USERNAME", "").strip()
    if not username or username == "YOUR_GITHUB_USERNAME":
        raise SystemExit("Set GITHUB_USERNAME to a real GitHub account name.")
    try:
        profile_data = api_get(f"/users/{username}")
        repo_data = api_get(f"/users/{username}/repos?per_page=100&sort=updated")
    except (HTTPError, URLError, TimeoutError) as error:
        raise SystemExit(f"GitHub API request failed: {error}") from error
    if not isinstance(profile_data, dict) or not isinstance(repo_data, list):
        raise SystemExit("GitHub API returned an unexpected response shape.")
    svg = build_svg(username, profile_data, repo_data)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(svg, encoding="utf-8")
    print(f"Updated {OUTPUT.relative_to(ROOT)} for {username}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
