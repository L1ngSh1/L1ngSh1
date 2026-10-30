# GitHub telemetry maintenance

`generate_github_telemetry.py` builds the responsive dark pair `assets/github-telemetry.svg` and `assets/github-telemetry-mobile.svg`, plus matching light variants under `assets/light/` entirely from GitHub's REST and GraphQL APIs. The desktop card combines repository metrics, activity streaks, and an account-wide repository-language pie chart; the mobile card presents the same data in a legible vertical layout without third-party stats services.

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

`.github/workflows/update-github-telemetry.yml` runs at `00:00` and `12:00` UTC and supports `workflow_dispatch`. It uses the repository owner as `GITHUB_USERNAME`. The generator avoids rewriting identical content, and the workflow commits only when any responsive/theme telemetry asset has a real diff.

The workflow requires `contents: write` permission.

## SVG themes

The existing `assets/*.svg` panels are the canonical dark artwork. The 16 light
variants in `assets/light/` are derived with a semantic palette (white/slate
surfaces, dark text, stronger accents), not an inversion filter. Original-color
featured logos, geometry, embedded fonts, labels and animation timing are retained.
Vendored `assets/stack-icons/` are source artwork, not standalone README panels.

After editing any canonical panel, regenerate and test:

```bash
python3 scripts/generate_light_assets.py
python3 -m unittest discover -s tests -p 'test_svg_themes.py' -v
```

`generate_stack.py` and `generate_github_telemetry.py` also refresh their own light
variants. The telemetry workflow commits all four outputs together.

README pictures select dark/mobile first, dark/desktop second, light/mobile third,
and use light/desktop as the fallback. This preserves the 600px breakpoint while
using GitHub's supported `<picture>` + `prefers-color-scheme` mechanism:
https://github.blog/changelog/2022-08-15-specify-theme-context-for-images-in-markdown-ga/
