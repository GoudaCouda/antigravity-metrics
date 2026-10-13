"""Unit tests for pricing persistence and sync mechanisms."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock
from antigravity_metrics.sync import save_pricing_entry, fetch_from_openrouter


class TestSync(unittest.TestCase):
    def test_save_pricing_entry(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_pricing_file = Path(tmpdir) / "model_pricing.json"
            with patch("antigravity_metrics.sync.get_pricing_file_path", return_value=fake_pricing_file):
                entry = {
                    "model": "Test Model",
                    "rates": [1.0, 0.1, 2.0],
                    "verified_at": "2026-10-13",
                    "expires_at": None,
                }
                save_pricing_entry("test-model", entry)
                self.assertTrue(fake_pricing_file.exists())

                import json
                with open(fake_pricing_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.assertIn("test-model", data)
                self.assertEqual(data["test-model"]["rates"], [1.0, 0.1, 2.0])

    @patch("urllib.request.urlopen")
    def test_fetch_from_openrouter_mock(self, mock_urlopen):
        mock_response = MagicMock()
        mock_payload = {
            "data": [
                {
                    "id": "vendor/test-model-4",
                    "name": "Vendor Test Model 4",
                    "pricing": {
                        "prompt": "0.000001",      # $1.00 / 1M
                        "completion": "0.000005",  # $5.00 / 1M
                        "input_cache_read": "0.0000002", # $0.20 / 1M
                    },
                }
            ]
        }
        import json
        mock_response.read.return_value = json.dumps(mock_payload).encode("utf-8")
        mock_response.__enter__.return_value = mock_response
        mock_urlopen.return_value = mock_response

        res = fetch_from_openrouter("test-model-4")
        self.assertIsNotNone(res)
        self.assertEqual(res["rates"], [1.0, 0.2, 5.0])
        self.assertEqual(res["model"], "Vendor Test Model 4")


if __name__ == "__main__":
    unittest.main()
