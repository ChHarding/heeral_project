"""Automated tests for ContrastCheck's calculation and reporting rules."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import requests

import main


def solid_fill(red, green, blue):
    """Create a small Figma-style solid fill for test data."""
    return {"type": "SOLID", "color": {"r": red, "g": green, "b": blue}}


class ContrastMathTests(unittest.TestCase):
    def test_black_on_white_has_maximum_contrast(self):
        self.assertAlmostEqual(
            main.calculate_contrast_ratio((0, 0, 0), (255, 255, 255)), 21.0
        )

    def test_ratio_is_same_when_color_order_is_reversed(self):
        forward = main.calculate_contrast_ratio((20, 40, 60), (240, 240, 240))
        reverse = main.calculate_contrast_ratio((240, 240, 240), (20, 40, 60))
        self.assertAlmostEqual(forward, reverse)


class ExtractionTests(unittest.TestCase):
    def test_text_uses_nearest_solid_ancestor_background(self):
        document = {
            "type": "FRAME",
            "name": "White page",
            "fills": [solid_fill(1, 1, 1)],
            "children": [
                {
                    "type": "FRAME",
                    "name": "Blue card",
                    "fills": [solid_fill(0, 0, 1)],
                    "children": [
                        {
                            "type": "TEXT",
                            "id": "1:2",
                            "characters": "Card title",
                            "fills": [solid_fill(1, 1, 1)],
                        }
                    ],
                }
            ],
        }
        result = main.extract_text_nodes(document)[0]
        self.assertEqual(result["bg_color"], (0, 0, 255))
        self.assertEqual(result["bg_source"], "Blue card")
        self.assertIsNone(result["review_reason"])

    def test_image_background_requires_manual_review(self):
        document = {
            "type": "FRAME",
            "name": "Hero image",
            "fills": [{"type": "IMAGE"}],
            "children": [
                {
                    "type": "TEXT",
                    "id": "2:1",
                    "characters": "Welcome",
                    "fills": [solid_fill(1, 1, 1)],
                }
            ],
        }
        result = main.extract_text_nodes(document)[0]
        self.assertIn("image", result["review_reason"])

    def test_text_without_ancestor_background_requires_manual_review(self):
        result = main.extract_text_nodes(
            {
                "type": "TEXT",
                "id": "3:1",
                "characters": "No container",
                "fills": [solid_fill(0, 0, 0)],
            }
        )[0]
        self.assertEqual(
            result["review_reason"], "no supported solid ancestor background found"
        )


class ReportTests(unittest.TestCase):
    def test_duplicate_results_are_only_reported_once(self):
        result = {
            "text": "Repeated label",
            "node_id": "4:1",
            "fg_color": (0, 0, 0),
            "bg_color": (255, 255, 255),
            "bg_source": "Page",
            "review_reason": None,
        }
        lines, counts = main.build_report_lines([result, result.copy()])
        self.assertEqual(len(lines), 1)
        self.assertEqual(counts["passed"], 1)

    def test_report_is_saved_with_all_summary_categories(self):
        result = {
            "text": "Heading",
            "node_id": "5:1",
            "fg_color": (0, 0, 0),
            "bg_color": (255, 255, 255),
            "bg_source": "Page",
            "review_reason": None,
        }
        with tempfile.TemporaryDirectory() as directory:
            report_path = Path(directory) / "result.txt"
            self.assertTrue(main.write_report([result], "test-file", report_path))
            report = report_path.read_text(encoding="utf-8")
        self.assertIn("1 passed, 0 failed, 0 manual review", report)
        self.assertIn("node 5:1", report)


class InputAndErrorTests(unittest.TestCase):
    def test_file_key_is_extracted_from_design_url(self):
        self.assertEqual(
            main.parse_file_key("https://www.figma.com/design/ABC123/My-Design"),
            "ABC123",
        )

    def test_non_figma_url_is_rejected(self):
        with self.assertRaises(ValueError):
            main.parse_file_key("https://example.com/design/ABC123")

    @patch("main.requests.get")
    def test_timeout_returns_none(self, mock_get):
        mock_get.side_effect = requests.Timeout()
        self.assertIsNone(main.fetch_figma_file("ABC123", "token"))

    @patch("main.requests.get")
    def test_permission_error_returns_none(self, mock_get):
        response = Mock(status_code=403)
        error = requests.HTTPError(response=response)
        mock_get.return_value.raise_for_status.side_effect = error
        self.assertIsNone(main.fetch_figma_file("ABC123", "bad-token"))


if __name__ == "__main__":
    unittest.main()
