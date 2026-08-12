#!/usr/bin/env python3
"""Generate a first-party GitHub telemetry console as a self-contained SVG."""

from __future__ import annotations

import html
import json
import math
import os
from collections import Counter
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from typing import Iterable
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets" / "github-telemetry.svg"
REST_API = "https://api.github.com"
GRAPHQL_API = "https://api.github.com/graphql"
DEFAULT_USERNAME = "L1ngSh1"
MAX_PRIMARY_LANGUAGES = 5
COLORS = ["#DA3633", "#D29922", "#3FB950", "#8B949E", "#E6EDF3", "#30363D"]
LANGUAGE_COLORS = {"Python": "#DA3633", "Java": "#D29922", "HTML": "#3FB950"}


@dataclass(frozen=True)
class ContributionStats:
    total: int
    current_streak: int
    longest_streak: int
    last_active: str


def request_json(url: str, token: str, payload: dict[str, object] | None = None) -> object:
    headers = {
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {token}",
        "User-Agent": "L1ngSh1-github-telemetry",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    body = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    request = Request(url, data=body, headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def rest_get(path: str, token: str, params: dict[str, object] | None = None) -> object:
    query = f"?{urlencode(params)}" if params else ""
    return request_json(f"{REST_API}{path}{query}", token)


def fetch_repositories(username: str, token: str) -> list[dict[str, object]]:
    repositories: list[dict[str, object]] = []
    page = 1
    while True:
        result = rest_get(
            f"/users/{username}/repos",
            token,
            {"per_page": 100, "page": page, "sort": "updated", "type": "owner"},
        )
        if not isinstance(result, list):
            raise ValueError("GitHub repositories response is not a list")
        repositories.extend(repo for repo in result if isinstance(repo, dict))
        if len(result) < 100:
            return repositories
        page += 1


def fetch_language_bytes(repositories: Iterable[dict[str, object]], token: str) -> Counter[str]:
    totals: Counter[str] = Counter()
    for repository in repositories:
        full_name = repository.get("full_name")
        if not isinstance(full_name, str) or not full_name:
            continue
        result = rest_get(f"/repos/{full_name}/languages", token)
        if not isinstance(result, dict):
            raise ValueError(f"Language response for {full_name} is not an object")
        for language, byte_count in result.items():
            if isinstance(language, str) and isinstance(byte_count, int) and byte_count > 0:
                totals[language] += byte_count
    return totals


def collapse_languages(language_bytes: Counter[str]) -> list[tuple[str, int]]:
    ordered = language_bytes.most_common()
    primary = ordered[:MAX_PRIMARY_LANGUAGES]
    remainder = sum(count for _, count in ordered[MAX_PRIMARY_LANGUAGES:])
    if remainder:
        primary.append(("OTHER", remainder))
    return primary


def integer_percentages(values: list[int]) -> list[int]:
    total = sum(values)
    if total <= 0:
        return [0 for _ in values]
    raw = [value * 100 / total for value in values]
    floors = [math.floor(value) for value in raw]
    remainder = 100 - sum(floors)
    order = sorted(range(len(raw)), key=lambda index: (raw[index] - floors[index], values[index]), reverse=True)
    for index in order[:remainder]:
        floors[index] += 1
    return floors


def calculate_streaks(days: Iterable[dict[str, object]], today: date) -> tuple[int, int, str]:
    counts: dict[date, int] = {}
    for day in days:
        raw_date = day.get("date")
        count = day.get("contributionCount")
        if isinstance(raw_date, str) and isinstance(count, int):
            counts[date.fromisoformat(raw_date)] = count

    active_days = sorted(day for day, count in counts.items() if count > 0)
    if not active_days:
        return 0, 0, "—"

    longest = 1
    run = 1
    for previous, current in zip(active_days, active_days[1:]):
        if current == previous + timedelta(days=1):
            run += 1
            longest = max(longest, run)
        else:
            run = 1

    last = active_days[-1]
    current = 0
    if last >= today - timedelta(days=1):
        current = 1
        cursor = last - timedelta(days=1)
        while counts.get(cursor, 0) > 0:
            current += 1
            cursor -= timedelta(days=1)

    return current, longest, f"{last.strftime('%b')} {last.day}"


def fetch_contributions(username: str, token: str, now: datetime | None = None) -> ContributionStats:
    now = now or datetime.now(timezone.utc)
    start = datetime.combine(now.date() - timedelta(days=365), time.min, tzinfo=timezone.utc)
    query = """
      query($login: String!, $from: DateTime!, $to: DateTime!) {
        user(login: $login) {
          contributionsCollection(from: $from, to: $to) {
            contributionCalendar {
              totalContributions
              weeks {
                contributionDays { date contributionCount }
              }
            }
          }
        }
      }
    """
    result = request_json(
        GRAPHQL_API,
        token,
        {
            "query": query,
            "variables": {
                "login": username,
                "from": start.isoformat().replace("+00:00", "Z"),
                "to": now.isoformat().replace("+00:00", "Z"),
            },
        },
    )
    if not isinstance(result, dict) or result.get("errors"):
        raise ValueError(f"GitHub GraphQL request failed: {result.get('errors') if isinstance(result, dict) else result}")
    try:
        calendar = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]
        weeks = calendar["weeks"]
        total = calendar["totalContributions"]
    except (KeyError, TypeError) as error:
        raise ValueError("GitHub contribution response has an unexpected shape") from error
    days = [day for week in weeks for day in week.get("contributionDays", [])]
    current, longest, last_active = calculate_streaks(days, now.date())
    return ContributionStats(int(total), current, longest, last_active)


def escaped(value: object) -> str:
    return html.escape(str(value), quote=True)


def pie_markup(languages: list[tuple[str, int]]) -> tuple[str, str]:
    if not languages:
        return "", '<text x="282" y="336" fill="#8B949E" font-size="13">NO LANGUAGE DATA</text>'

    total = sum(count for _, count in languages)
    percentages = integer_percentages([count for _, count in languages])
    radius = 72
    start_angle = -math.pi / 2
    reserved_colors = {LANGUAGE_COLORS[name] for name, _ in languages if name in LANGUAGE_COLORS}
    used_colors: set[str] = set()
    segments: list[str] = []
    legends: list[str] = []
    for index, ((language, count), percentage) in enumerate(zip(languages, percentages)):
        fraction = count / total
        color = LANGUAGE_COLORS.get(language)
        if color is None or color in used_colors:
            color = next(
                candidate for candidate in COLORS
                if candidate not in used_colors and candidate not in reserved_colors
            )
        used_colors.add(color)
        end_angle = start_angle + 2 * math.pi * fraction
        if fraction >= 0.999999:
            segments.append(f'<circle cx="160" cy="326" r="{radius}" fill="{color}"/>')
        else:
            start_x = 160 + radius * math.cos(start_angle)
            start_y = 326 + radius * math.sin(start_angle)
            end_x = 160 + radius * math.cos(end_angle)
            end_y = 326 + radius * math.sin(end_angle)
            large_arc = 1 if fraction > 0.5 else 0
            segments.append(
                f'<path d="M160 326 L{start_x:.2f} {start_y:.2f} '
                f'A{radius} {radius} 0 {large_arc} 1 {end_x:.2f} {end_y:.2f} Z" '
                f'fill="{color}" stroke="#0D1117" stroke-width="1.5" stroke-linejoin="round"/>'
            )
        column = index % 2
        row = index // 2
        x = 284 + column * 150
        y = 287 + row * 38
        legends.append(
            f'<circle cx="{x}" cy="{y - 4}" r="4" fill="{color}"/>'
            f'<text x="{x + 12}" y="{y}" fill="#8B949E" font-size="13">'
            f'{escaped(language)} <tspan fill="#E6EDF3">{percentage}%</tspan></text>'
        )
        start_angle = end_angle
    return "".join(segments), "".join(legends)


def build_svg(
    username: str,
    profile: dict[str, object],
    repositories: list[dict[str, object]],
    language_bytes: Counter[str],
    contributions: ContributionStats,
) -> str:
    stars = sum(int(repo.get("stargazers_count", 0) or 0) for repo in repositories)
    forks = sum(int(repo.get("forks_count", 0) or 0) for repo in repositories)
    languages = collapse_languages(language_bytes)
    pie, legend = pie_markup(languages)
    login = escaped(profile.get("login") or username)
    metrics = [
        ("PUBLIC REPOS", int(profile.get("public_repos", 0) or 0)),
        ("FOLLOWERS", int(profile.get("followers", 0) or 0)),
        ("STARS", stars),
        ("FORKS", forks),
        ("TOTAL CONTRIBUTIONS", contributions.total),
    ]
    metric_labels: list[str] = []
    metric_values: list[str] = []
    separators: list[str] = []
    column_width = 1136 / 5
    for index, (label, value) in enumerate(metrics):
        x = 32 + index * column_width
        metric_labels.append(f'<text x="{x:.1f}" y="102">{label}</text>')
        metric_values.append(f'<text x="{x:.1f}" y="145">{value:,}</text>')
        if index:
            separator_x = 32 + index * column_width - 18
            separators.append(f'M{separator_x:.1f} 82V158')

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="470" viewBox="0 0 1200 470" role="img" aria-labelledby="title desc">
  <title id="title">GitHub telemetry console for {login}</title>
  <desc id="desc">A first-party GitHub observability console showing repositories, followers, stars, forks, yearly contributions, language composition, and activity streaks.</desc>
  <defs>
    <style>
      .mono {{ font-family: ui-monospace,SFMono-Regular,Menlo,Monaco,Consolas,Liberation Mono,monospace; }}
      @media (prefers-reduced-motion: reduce) {{ * {{ animation: none !important; }} }}
    </style>
  </defs>
  <rect width="1200" height="470" rx="14" fill="#0D1117"/>
  <rect x="1" y="1" width="1198" height="468" rx="13" fill="none" stroke="#30363D"/>
  <g class="mono">
    <text x="32" y="39" fill="#8B949E" font-size="14" letter-spacing=".8">GITHUB TELEMETRY / {login.upper()}</text>
    <circle cx="1079" cy="34" r="4" fill="#3FB950"/>
    <text x="1091" y="39" fill="#3FB950" font-size="14" letter-spacing=".8">SYNCED</text>
    <text x="1168" y="58" text-anchor="end" fill="#8B949E" font-size="10" letter-spacing=".7">AUTO-SYNC / 12H</text>
    <path d="M32 68H1168" stroke="#30363D"/>

    <g fill="#8B949E" font-size="12" letter-spacing=".55">{''.join(metric_labels)}</g>
    <g fill="#E6EDF3" font-size="31" font-weight="700">{''.join(metric_values)}</g>
    <path d="{' '.join(separators)}" stroke="#30363D"/>
    <path d="M32 180H1168" stroke="#30363D"/>

    <rect x="32" y="210" width="548" height="228" rx="8" fill="none" stroke="#30363D"/>
    <text x="54" y="242" fill="#8B949E" font-size="13" letter-spacing=".7">LANGUAGE COMPOSITION</text>
    <circle cx="160" cy="326" r="72" fill="#30363D"/>
    {pie}
    {legend}

    <rect x="604" y="210" width="564" height="228" rx="8" fill="none" stroke="#30363D"/>
    <circle cx="628" cy="238" r="4" fill="#DA3633"/>
    <text x="642" y="242" fill="#8B949E" font-size="13" letter-spacing=".7">ACTIVITY STREAK</text>
    <path d="M792 278V386M980 278V386" stroke="#30363D"/>
    <g fill="#8B949E" font-size="11" letter-spacing=".6" text-anchor="middle">
      <text x="698" y="300">CURRENT STREAK</text>
      <text x="886" y="300">LONGEST STREAK</text>
      <text x="1074" y="300">LAST ACTIVE</text>
    </g>
    <g fill="#E6EDF3" font-size="34" font-weight="700" text-anchor="middle">
      <text x="698" y="353">{contributions.current_streak}</text>
      <text x="886" y="353">{contributions.longest_streak}</text>
      <text x="1074" y="353" font-size="25">{escaped(contributions.last_active)}</text>
    </g>
    <g fill="#8B949E" font-size="10" letter-spacing=".5" text-anchor="middle">
      <text x="698" y="378">DAYS</text>
      <text x="886" y="378">DAYS / 1Y</text>
      <text x="1074" y="378">UTC</text>
    </g>
  </g>
</svg>
'''


def write_if_changed(path: Path, content: str) -> bool:
    if path.exists() and path.read_text(encoding="utf-8") == content:
        print(f"Unchanged {path.relative_to(ROOT)}")
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    print(f"Updated {path.relative_to(ROOT)}")
    return True


def main() -> int:
    username = os.environ.get("GITHUB_USERNAME", DEFAULT_USERNAME).strip() or DEFAULT_USERNAME
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        raise SystemExit("GITHUB_TOKEN is required for contribution and language telemetry.")
    try:
        profile = rest_get(f"/users/{username}", token)
        repositories = fetch_repositories(username, token)
        language_bytes = fetch_language_bytes(repositories, token)
        contributions = fetch_contributions(username, token)
    except (HTTPError, URLError, TimeoutError, ValueError) as error:
        raise SystemExit(f"GitHub telemetry request failed: {error}") from error
    if not isinstance(profile, dict):
        raise SystemExit("GitHub profile response is not an object.")
    svg = build_svg(username, profile, repositories, language_bytes, contributions)
    write_if_changed(OUTPUT, svg)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
