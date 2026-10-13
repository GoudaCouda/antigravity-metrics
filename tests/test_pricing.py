"""Unit tests for model pricing lookup and normalization."""

import unittest
from antigravity_metrics.pricing import (
    normalize_model_name,
    parse_model_string,
    resolve_model_rates,
    MissingModelPricingError,
)


class TestPricing(unittest.TestCase):
    def test_normalize_model_name(self):
        self.assertEqual(normalize_model_name("Gemini 3.8 Flash"), "gemini-3.8-flash")
        self.assertEqual(normalize_model_name("Google: Gemini 3.8 Flash"), "gemini-3.8-flash")
        self.assertEqual(normalize_model_name("Claude Sonnet 4.6"), "claude-sonnet-4.6")
        self.assertEqual(normalize_model_name("OpenAI: gpt-oss-120b"), "gpt-oss-120b")

    def test_parse_model_string(self):
        base, effort = parse_model_string("Gemini 3.8 Flash (Medium)")
        self.assertEqual(base, "Gemini 3.8 Flash")
        self.assertEqual(effort, "Medium")

        base_no_effort, effort_empty = parse_model_string("Claude Sonnet 4.6")
        self.assertEqual(base_no_effort, "Claude Sonnet 4.6")
        self.assertEqual(effort_empty, "")

    def test_resolve_known_model(self):
        canonical, rates, info = resolve_model_rates("Gemini 3.8 Flash", auto_sync=False)
        self.assertEqual(canonical, "gemini-3.8-flash")
        self.assertEqual(rates, (0.75, 0.075, 3.75))

    def test_missing_model_without_sync(self):
        with self.assertRaises(MissingModelPricingError):
            resolve_model_rates("NonExistentModel9999", auto_sync=False)


if __name__ == "__main__":
    unittest.main()
