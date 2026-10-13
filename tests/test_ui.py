"""Unit tests for UI rendering."""

import io
import unittest
from pathlib import Path
from unittest.mock import patch
from antigravity_metrics.ui import render_summary_card, render_conversation_list


class TestUI(unittest.TestCase):
    def setUp(self):
        self.sample_data = {
            "title": "Test Session",
            "token_metrics": {
                "input_tokens": 1000,
                "output_tokens": 200,
                "cache_read_tokens": 500,
                "total_billable_tokens": 1200,
                "cache_hit_rate_pct": 33.3,
            },
            "financial_metrics": {
                "estimated_cost_usd": 0.05,
                "cache_savings_usd": 0.01,
                "savings_discount_pct": 16.6,
            },
            "step_counts": {
                "USER_INPUT": 1,
                "PLANNER_RESPONSE": 2,
                "GENERIC": 1,
            },
            "active_model": {
                "display_name": "Gemini 3.8 Flash",
                "effort": "Medium",
            },
            "model_breakdown": {
                "Gemini 3.8 Flash (Medium)": {
                    "turns": 2,
                    "total_tokens": 1200,
                    "estimated_cost_usd": 0.05,
                }
            },
        }

    def test_render_summary_card(self):
        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            render_summary_card(self.sample_data)
            output = mock_stdout.getvalue()

            self.assertIn("Token & Cost Summary", output)
            self.assertIn("Test Session", output)
            self.assertIn("ESTIMATED COST", output)
            self.assertIn("ACTIVE MODEL", output)
            self.assertIn("TOKEN USAGE", output)
            self.assertIn("CACHE EFFICIENCY", output)
            self.assertIn("ACTIVITY", output)

    def test_render_summary_card_with_model_breakdown(self):
        data = dict(self.sample_data)
        data["model_breakdown"] = {
            "Gemini 3.8 Flash (Medium)": {
                "turns": 2,
                "total_tokens": 1200,
                "estimated_cost_usd": 0.05,
            },
            "Gemini 3.8 Pro": {
                "turns": 1,
                "total_tokens": 800,
                "estimated_cost_usd": 0.08,
            },
        }

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            render_summary_card(data)
            output = mock_stdout.getvalue()

            self.assertIn("BREAKDOWN BY MODEL", output)
            self.assertIn("Gemini 3.8 Pro", output)

    @patch("antigravity_metrics.parser.get_conversation_metadata")
    def test_render_conversation_list(self, mock_get_meta):
        mock_get_meta.return_value = {
            "title": "Sample Conversation",
            "step_count": 5,
            "status": "COMPLETED",
        }
        convs = [("conv-123456789", Path("/dummy/path"), 1700000000.0)]
        app_dir = Path("/dummy/app_dir")

        with patch("sys.stdout", new_callable=io.StringIO) as mock_stdout:
            render_conversation_list(convs, app_dir)
            output = mock_stdout.getvalue()

            self.assertIn("Recent Conversations", output)
            self.assertIn("conv-123", output)
            self.assertIn("Sample Conversation", output)


if __name__ == "__main__":
    unittest.main()
