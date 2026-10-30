"""Offline theme, responsive routing and generator regression checks."""
from collections import Counter
import importlib.util
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("generate_light_assets", ROOT / "scripts/generate_light_assets.py")
themes = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(themes)
NS = {"s": "http://www.w3.org/2000/svg"}


def contrast(foreground, background):
    def luminance(color):
        channels = [int(color[i:i+2], 16) / 255 for i in (1, 3, 5)]
        channels = [c/12.92 if c <= .04045 else ((c+.055)/1.055)**2.4 for c in channels]
        return sum(c*w for c, w in zip(channels, (.2126, .7152, .0722)))
    values = sorted((luminance(foreground), luminance(background)))
    return (values[1]+.05)/(values[0]+.05)


class SvgThemeTests(unittest.TestCase):
    def test_all_16_light_panels_are_current_valid_and_self_contained(self):
        sources = sorted((ROOT / "assets").glob("*.svg"))
        self.assertEqual(len(sources), 16)
        self.assertEqual(len(list((ROOT / "assets/light").glob("*.svg"))), 16)
        for source in sources:
            with self.subTest(panel=source.name):
                svg = (ROOT / "assets/light" / source.name).read_text()
                self.assertEqual(svg, themes.render_light_svg(source.read_text()))
                root = ET.fromstring(svg)
                original = ET.parse(source).getroot()
                self.assertEqual(root.attrib, original.attrib)
                self.assertIsNone(root.find(".//s:script", NS))
                self.assertIsNone(root.find(".//s:image", NS))
                ids = {e.attrib["id"] for e in root.iter() if "id" in e.attrib}
                for e in root.iter():
                    if "href" in e.attrib:
                        self.assertTrue(e.attrib["href"].startswith("#"))
                        self.assertIn(e.attrib["href"][1:], ids)

    def test_geometry_text_fonts_and_animation_timing_are_preserved(self):
        for source in (ROOT / "assets").glob("*.svg"):
            before, after = ET.fromstring(source.read_text()), ET.fromstring(themes.render_light_svg(source.read_text()))
            self.assertEqual(len(list(before.iter())), len(list(after.iter())))
            for a, b in zip(before.iter(), after.iter()):
                self.assertEqual(a.tag, b.tag)
                for key, value in a.attrib.items():
                    if key not in {"fill", "stroke", "color", "stop-color", "values", "style"}:
                        self.assertEqual(value, b.attrib[key])
                if a.tag.endswith(("}text", "}tspan", "}title")) or a.attrib.get("id") == "identity-font":
                    self.assertEqual(a.text, b.text)

    def test_featured_brand_artwork_is_unchanged(self):
        for name in ("stack.svg", "stack-mobile.svg"):
            source = (ROOT / "assets" / name).read_text()
            self.assertEqual(themes.FEATURED.findall(source), themes.FEATURED.findall(themes.render_light_svg(source)))

    def test_light_text_and_console_accents_have_contrast(self):
        for background in ("#FFFFFF", "#FAFBFC", "#F6F8FA"):
            for token in ("#E6EDF3", "#C9D1D9", "#8B949E", "#6E7681", "#D29922", "#3FB950", "#DA3633", "#58A6FF"):
                self.assertGreaterEqual(contrast(themes.LIGHT_COLORS[token], background), 4.5, (token, background))

    def test_readme_picture_source_order_and_paths(self):
        pictures = re.findall(r"<picture>(.*?)</picture>", (ROOT / "README.md").read_text(), re.S)
        self.assertEqual(len(pictures), 12)
        for block in pictures:
            sources = re.findall(r'<source media="([^"]+)" srcset="([^"]+)"', block)
            fallback = re.search(r'<img src="([^"]+)"', block)[1]
            name = Path(fallback).name
            mobile = name.replace(".svg", "-mobile.svg")
            self.assertEqual(sources, [
                ("(prefers-color-scheme: dark) and (max-width: 600px)", f"assets/{mobile}"),
                ("(prefers-color-scheme: dark)", f"assets/{name}"),
                ("(max-width: 600px)", f"assets/light/{mobile}"),
            ])
            self.assertEqual(fallback, f"assets/light/{name}")
            for path in [p for _, p in sources] + [fallback]:
                self.assertTrue((ROOT / path).is_file(), path)

    def test_mapping_covers_animation_and_gradient_not_id_substrings(self):
        sample = '<stop stop-color="#0d1117"/><animate values="#8B949E;#3FB950"/><use href="#0D1117-node"/>'
        self.assertIn('href="#0D1117-node"', themes.render_light_svg(sample))
        self.assertIn('stop-color="#FFFFFF"', themes.render_light_svg(sample))
        self.assertIn('values="#57606A;#1A7F37"', themes.render_light_svg(sample))

    def test_generation_is_idempotent(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "panel.svg"
            source.write_text('<svg fill="#0D1117"/>')
            self.assertTrue(themes.write_light_asset(source))
            target = source.parent / "light" / source.name
            timestamp = target.stat().st_mtime_ns
            self.assertFalse(themes.write_light_asset(source))
            self.assertEqual(timestamp, target.stat().st_mtime_ns)
            self.assertEqual(source.read_text(), '<svg fill="#0D1117"/>')

    def test_telemetry_update_refreshes_light_assets_without_network(self):
        # Exercise the real entry point with fixed API fixtures, not live account data.
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            spec = importlib.util.spec_from_file_location("theme_telemetry_fixture", ROOT / "scripts/generate_github_telemetry.py")
            telemetry = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = telemetry
            spec.loader.exec_module(telemetry)
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with patch.multiple(telemetry, ROOT=root, OUTPUT=root/"assets/github-telemetry.svg", MOBILE_OUTPUT=root/"assets/github-telemetry-mobile.svg"), patch.dict("os.environ", {"GITHUB_TOKEN": "fixture-not-a-credential"}), patch.object(telemetry, "rest_get", return_value={"login": "fixture", "public_repos": 2, "followers": 3}), patch.object(telemetry, "fetch_repositories", return_value=[]), patch.object(telemetry, "fetch_language_bytes", return_value=Counter({"Python": 3})), patch.object(telemetry, "fetch_contributions", return_value=telemetry.ContributionStats(7, 1, 2, "Oct 30")):
                    self.assertEqual(telemetry.main(), 0)
                for name in ("github-telemetry.svg", "github-telemetry-mobile.svg"):
                    self.assertEqual((root/"assets/light"/name).read_text(), themes.render_light_svg((root/"assets"/name).read_text()))
        finally:
            sys.path.pop(0)


if __name__ == "__main__":
    unittest.main()
