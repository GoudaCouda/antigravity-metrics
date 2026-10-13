"""Unit tests for transcript parsing and cost calculation."""

import json
import tempfile
import unittest
from pathlib import Path
from antigravity_metrics.parser import parse_conversation


class TestParser(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.conv_dir = Path(self.temp_dir.name)
        self.logs_dir = self.conv_dir / ".system_generated" / "logs"
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_file = self.logs_dir / "transcript.jsonl"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_single_pass_parsing_and_model_switch(self):
        # Write sample transcript lines with a model switch
        lines = [
            # Turn 1: Gemini 3.8 Flash
            {
                "type": "USER_INPUT",
                "content": "Hello! <USER_SETTINGS_CHANGE>\nModel Selection from Gemini 2.5 to Gemini 3.8 Flash (Medium).\n</USER_SETTINGS_CHANGE>",
            },
            {
                "type": "PLANNER_RESPONSE",
                "input_tokens": 100_000,
                "cache_read_tokens": 50_000,
                "output_tokens": 10_000,
            },
            # Turn 2: Model switch to Claude Sonnet 4.6
            {
                "type": "USER_INPUT",
                "content": "<USER_SETTINGS_CHANGE>\nModel Selection from Gemini 3.8 Flash to Claude Sonnet 4.6.\n</USER_SETTINGS_CHANGE> Switch model",
            },
            {
                "type": "PLANNER_RESPONSE",
                "input_tokens": 50_000,
                "cache_read_tokens": 150_000,
                "output_tokens": 5_000,
            },
        ]

        with open(self.transcript_file, "w", encoding="utf-8") as f:
            for item in lines:
                f.write(json.dumps(item) + "\n")

        fake_app_dir = Path(self.temp_dir.name)
        result = parse_conversation("test-conv-id", self.conv_dir, fake_app_dir)

        tm = result["token_metrics"]
        fm = result["financial_metrics"]
        mb = result["model_breakdown"]

        # Total tokens
        self.assertEqual(tm["input_tokens"], 150_000)
        self.assertEqual(tm["cache_read_tokens"], 200_000)
        self.assertEqual(tm["output_tokens"], 15_000)
        self.assertEqual(tm["gross_tokens"], 365_000)

        # Cache hit rate: 200k / (150k + 200k) = 200 / 350 = 57.1%
        self.assertAlmostEqual(tm["cache_hit_rate_pct"], 57.1, places=1)

        # Both models in breakdown
        self.assertIn("Gemini 3.8 Flash (Medium)", mb)
        self.assertIn("Claude Sonnet 4.6", mb)

        # Turn 1 cost (Gemini: 0.75 in, 0.075 cache, 3.75 out per 1M)
        # 100k * 0.75/1M = 0.075
        # 50k * 0.075/1M = 0.00375
        # 10k * 3.75/1M = 0.0375
        # Turn 1 total = 0.11625
        gemini_cost = mb["Gemini 3.8 Flash (Medium)"]["estimated_cost_usd"]
        self.assertAlmostEqual(gemini_cost, 0.11625, places=5)

        # Turn 2 cost (Claude: 3.0 in, 0.3 cache, 15.0 out per 1M)
        # 50k * 3.0/1M = 0.15
        # 150k * 0.3/1M = 0.045
        # 5k * 15.0/1M = 0.075
        # Turn 2 total = 0.27
        claude_cost = mb["Claude Sonnet 4.6"]["estimated_cost_usd"]
        self.assertAlmostEqual(claude_cost, 0.27, places=5)

        total_cost = fm["estimated_cost_usd"]
        self.assertAlmostEqual(total_cost, 0.11625 + 0.27, places=5)


if __name__ == "__main__":
    unittest.main()
