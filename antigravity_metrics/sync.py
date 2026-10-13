"""Dynamic model pricing discovery and synchronization (OpenRouter API & GitHub sync)."""

import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime
from typing import Any, Dict, Optional
from .config import get_pricing_file_path


def fetch_from_openrouter(model_name: str) -> Optional[Dict[str, Any]]:
    """Fetches real-time model pricing from OpenRouter API without author restrictions."""
    try:
        q = urllib.parse.quote(model_name)
        url = f"https://openrouter.ai/api/v1/models?q={q}&output_modalities=text"
        req = urllib.request.Request(url, headers={"User-Agent": "antigravity-token-metrics/1.0"})
        with urllib.request.urlopen(req, timeout=6) as response:
            payload = json.loads(response.read().decode("utf-8"))
            data = payload.get("data", [])
            if not data:
                return None

            # Prefer standard model over batch endpoint
            best_match = next((item for item in data if not item.get("id", "").endswith(":batch")), data[0])

            pricing = best_match.get("pricing", {})
            prompt_cost = float(pricing.get("prompt", 0.0))
            completion_cost = float(pricing.get("completion", 0.0))
            cache_read_cost = float(pricing.get("input_cache_read", 0.0) or pricing.get("input_audio_cache", 0.0) or 0.0)

            # Convert per-token costs to per-1M tokens
            price_per_1m_input = round(prompt_cost * 1_000_000, 4)
            price_per_1m_output = round(completion_cost * 1_000_000, 4)
            price_per_1m_cached = (
                round(cache_read_cost * 1_000_000, 4)
                if cache_read_cost > 0
                else round(price_per_1m_input * 0.10, 4)
            )

            return {
                "model": best_match.get("name", model_name),
                "rates": [price_per_1m_input, price_per_1m_cached, price_per_1m_output],
                "verified_at": datetime.now().strftime("%Y-%m-%d"),
                "expires_at": None,
            }
    except Exception:
        return None


def sync_from_github() -> Optional[Dict[str, Any]]:
    """Syncs verified model pricing definitions directly from upstream GitHub."""
    url = "https://raw.githubusercontent.com/GoudaCouda/antigravity-metrics/main/model_pricing.json"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "antigravity-token-metrics/1.0"})
        with urllib.request.urlopen(req, timeout=6) as response:
            data = json.loads(response.read().decode("utf-8"))
            if data and isinstance(data, dict):
                save_all_pricing(data)
                return data
    except Exception as e:
        print(f"[WARN] Failed to sync pricing from GitHub: {e}", file=sys.stderr)
    return None


def save_pricing_entry(key: str, entry: Dict[str, Any]) -> None:
    """Updates or adds a single model entry in model_pricing.json."""
    target_path = get_pricing_file_path()
    try:
        current_data = {}
        if target_path.exists():
            with open(target_path, "r", encoding="utf-8") as f:
                current_data = json.load(f)

        current_data[key] = {
            "model": entry.get("model", key),
            "rates": [float(entry["rates"][0]), float(entry["rates"][1]), float(entry["rates"][2])],
            "verified_at": entry.get("verified_at"),
            "expires_at": entry.get("expires_at"),
        }

        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(current_data, f, indent=2)
    except Exception as e:
        print(f"[WARN] Failed to save {key} to {target_path}: {e}", file=sys.stderr)


def save_all_pricing(data: Dict[str, Any]) -> None:
    """Saves the complete pricing table to model_pricing.json."""
    target_path = get_pricing_file_path()
    try:
        with open(target_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[WARN] Failed to write pricing table to {target_path}: {e}", file=sys.stderr)
