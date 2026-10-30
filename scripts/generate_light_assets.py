#!/usr/bin/env python3
"""Derive light panels from the canonical dark SVGs without changing geometry."""
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
# Semantic console colors; original-color featured logos stay untouched.
LIGHT_COLORS = {
    "#0D1117": "#FFFFFF", "#11161D": "#FAFBFC", "#161B22": "#F6F8FA",
    "#21262D": "#D8DEE4", "#30363D": "#D0D7DE", "#484F58": "#6E7781",
    "#6E7681": "#57606A", "#8B949E": "#57606A",
    "#C9D1D9": "#24292F", "#E6EDF3": "#1F2328",
    "#DA3633": "#CF222E", "#F85149": "#CF222E",
    "#D29922": "#9A6700", "#E3B341": "#9A6700",
    "#3FB950": "#1A7F37", "#238636": "#1A7F37", "#58A6FF": "#0969DA",
    "#ED8B00": "#9A6700", "#4EAA25": "#1A7F37", "#F7DF1E": "#7D6200",
    "#FCC624": "#7D6200", "#2496ED": "#0969DA", "#FF6633": "#BC4C00",
    "#F34B7D": "#BF3989", "#F05032": "#BC4C00",
}
COLOR = re.compile(r"#[0-9a-fA-F]{6}(?![\w-])")
FEATURED = re.compile(r'(<symbol id="icon-featured-[^>]+>.*?</symbol>)', re.S)


def render_light_svg(svg: str) -> str:
    """Map CSS, presentation attributes, gradient stops and SMIL color values.

    Split rather than reserialize XML to preserve fonts, paths and animations.
    Embedded brand artwork is intentionally excluded from the console palette.
    """
    parts = FEATURED.split(svg)
    for index in range(0, len(parts), 2):
        parts[index] = COLOR.sub(lambda m: LIGHT_COLORS.get(m[0].upper(), m[0]), parts[index])
    return "".join(parts).replace("A dark research console", "A light research console")


def write_light_asset(source: Path) -> bool:
    target = source.parent / "light" / source.name
    content = render_light_svg(source.read_text(encoding="utf-8"))
    if target.exists() and target.read_text(encoding="utf-8") == content:
        return False
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    return True


def main() -> None:
    sources = sorted((ROOT / "assets").glob("*.svg"))
    changed = sum(write_light_asset(source) for source in sources)
    print(f"Light SVGs: {len(sources)} checked, {changed} updated")


if __name__ == "__main__":
    main()
