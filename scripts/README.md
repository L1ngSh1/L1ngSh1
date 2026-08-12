# GitHub telemetry maintenance

`generate_github_telemetry.py` builds `assets/github-telemetry.svg` entirely from GitHub's REST and GraphQL APIs. The generated card combines repository metrics, the one-year contribution calendar, activity streaks, and an account-wide repository-language pie chart without third-party stats services.

## Local update

```bash
GITHUB_TOKEN="$(gh auth token)" python3 scripts/generate_github_telemetry.py
```

The script defaults to `L1ngSh1`; set `GITHUB_USERNAME` to render another account. A token is required because contribution-calendar data is retrieved through GitHub GraphQL. The token is read from the environment and is never written to the SVG.

## Data definitions

- **Stars / forks:** totals across the account's public owner repositories.
- **Total contributions:** `contributionCalendar.totalContributions` for the trailing 365-day window.
- **Current streak:** consecutive contribution days ending today or yesterday; otherwise zero.
- **Longest streak:** longest consecutive run in the trailing 365-day calendar.
- **Language composition:** byte counts from each public repository's `/languages` endpoint, aggregated account-wide. The top five languages are shown; remaining languages are merged into `OTHER`.

## Automated update

`.github/workflows/update-github-telemetry.yml` runs at `00:00` and `12:00` UTC and supports `workflow_dispatch`. It uses the repository owner as `GITHUB_USERNAME`. The generator avoids rewriting identical content, and the workflow commits only when `assets/github-telemetry.svg` has a real diff.

The workflow requires `contents: write` permission.
