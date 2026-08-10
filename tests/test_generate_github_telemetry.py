import importlib.util
import sys
import unittest
from collections import Counter
from datetime import date
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "generate_github_telemetry.py"
SPEC = importlib.util.spec_from_file_location("telemetry", MODULE_PATH)
telemetry = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
sys.modules[SPEC.name] = telemetry
SPEC.loader.exec_module(telemetry)


class TelemetryTests(unittest.TestCase):
    def test_languages_keep_top_five_and_merge_other(self):
        values = Counter({"Python": 60, "Java": 20, "HTML": 10, "C++": 5, "Shell": 3, "CSS": 1, "Go": 1})
        self.assertEqual(
            telemetry.collapse_languages(values),
            [("Python", 60), ("Java", 20), ("HTML", 10), ("C++", 5), ("Shell", 3), ("OTHER", 2)],
        )
        self.assertEqual(sum(telemetry.integer_percentages([60, 20, 10, 5, 3, 2])), 100)

    def test_streaks_include_yesterday_as_current(self):
        days = [
            {"date": "2026-08-05", "contributionCount": 1},
            {"date": "2026-08-06", "contributionCount": 2},
            {"date": "2026-08-08", "contributionCount": 1},
            {"date": "2026-08-09", "contributionCount": 3},
            {"date": "2026-08-10", "contributionCount": 2},
        ]
        self.assertEqual(telemetry.calculate_streaks(days, date(2026, 8, 11)), (3, 3, "Aug 10"))

    def test_stale_activity_has_zero_current_streak(self):
        days = [{"date": "2026-08-01", "contributionCount": 1}]
        self.assertEqual(telemetry.calculate_streaks(days, date(2026, 8, 11)), (0, 1, "Aug 1"))

    def test_svg_contains_unified_metrics_and_donut(self):
        profile = {"login": "L1ngSh1", "public_repos": 8, "followers": 8}
        repos = [{"stargazers_count": 5, "forks_count": 1}]
        stats = telemetry.ContributionStats(395, 1, 6, "Aug 10")
        svg = telemetry.build_svg("L1ngSh1", profile, repos, Counter({"Python": 67, "Java": 17, "HTML": 16}), stats)
        self.assertIn("TOTAL CONTRIBUTIONS", svg)
        self.assertIn("ACTIVITY STREAK", svg)
        self.assertIn("stroke-dasharray", svg)
        self.assertIn('stroke="#DA3633"', svg)
        self.assertIn('stroke="#D29922"', svg)
        self.assertIn('stroke="#3FB950"', svg)
        self.assertNotIn("streak-stats", svg)


if __name__ == "__main__":
    unittest.main()
