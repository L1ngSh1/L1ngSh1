# Dashboard maintenance

`generate_dashboard.py` builds `assets/research-dashboard.svg` from public GitHub API data. The generated card is repository-owned, contains no fabricated values, and keeps the profile layout usable when third-party stat services are unavailable.

## Local update

```bash
python3 scripts/generate_dashboard.py
```

The script defaults to `L1ngSh1`; set `GITHUB_USERNAME` only to render another profile. Unauthenticated requests are sufficient for occasional local runs. Set `GITHUB_TOKEN` only when needed to increase the API rate limit; never commit a token.

## Automated update

`.github/workflows/update-dashboard.yml` runs once per day and on manual dispatch. It uses the repository owner as `GITHUB_USERNAME`, generates the SVG, and commits only when metrics changed.

The workflow needs `contents: write`. If the repository restricts workflow write access, enable it under **Settings → Actions → General → Workflow permissions** or run the script locally.
