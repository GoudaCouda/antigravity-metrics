"""Model pricing lookup, normalization, and rate resolution."""

import re
from datetime import datetime
from typing import Any, Dict, Optional, Tuple
from .config import get_pricing_file_path, load_user_config
from .sync import fetch_from_openrouter, save_pricing_entry, sync_from_github


class MissingModelPricingError(Exception):
    """Raised when a model cannot be resolved locally or via fallback sync."""
    def __init__(self, model_name: str, normalized_name: str):
        self.model_name = model_name
        self.normalized_name = normalized_name
        super().__init__(
            f"Pricing not found for model '{model_name}' (normalized: '{normalized_name}').\n"
            f"Please verify model availability or add it to model_pricing.json."
        )


def normalize_model_name(name: str) -> str:
    """Normalizes model names into canonical hyphenated lowercase strings."""
    norm = name.lower().strip()
    # Strip common leading vendor tags if present (e.g. google:, anthropic:)
    norm = re.sub(r"^(google|anthropic|openai):\s*", "", norm)
    norm = re.sub(r"[\s_]+", "-", norm)
    return norm.strip("-")


def parse_model_string(raw: str) -> Tuple[str, str]:
    """Splits 'Model Name (Effort)' into ('Model Name', 'Effort')."""
    raw = raw.strip().rstrip(".")
    m = re.match(r"^(.*?)\s*\((.*?)\)$", raw)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return raw, ""


def load_model_pricing() -> Dict[str, Dict[str, Any]]:
    """Loads model pricing from model_pricing.json."""
    pricing_path = get_pricing_file_path()
    if not pricing_path.exists():
        return {}

    try:
        import json
        with open(pricing_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        table: Dict[str, Dict[str, Any]] = {}
        for k, v in data.items():
            if isinstance(v, (list, tuple)) and len(v) == 3:
                table[k] = {
                    "model": k,
                    "rates": (float(v[0]), float(v[1]), float(v[2])),
                    "verified_at": None,
                    "expires_at": None,
                }
            elif isinstance(v, dict):
                rates = v.get("rates")
                if rates and isinstance(rates, (list, tuple)) and len(rates) == 3:
                    table[k] = {
                        "model": v.get("model", k),
                        "rates": (float(rates[0]), float(rates[1]), float(rates[2])),
                        "verified_at": v.get("verified_at"),
                        "expires_at": v.get("expires_at"),
                    }
        return table
    except Exception:
        return {}


# Runtime cached table
_CACHED_PRICING_TABLE: Optional[Dict[str, Dict[str, Any]]] = None


def get_pricing_table(reload: bool = False) -> Dict[str, Dict[str, Any]]:
    """Retrieves or refreshes the cached pricing table."""
    global _CACHED_PRICING_TABLE
    if _CACHED_PRICING_TABLE is None or reload:
        _CACHED_PRICING_TABLE = load_model_pricing()
    return _CACHED_PRICING_TABLE


def resolve_model_rates(
    base_name: str,
    auto_sync: bool = True,
) -> Tuple[str, Tuple[float, float, float], Dict[str, Any]]:
    """
    Resolves model rates (price_per_1m_input, price_per_1m_cached, price_per_1m_output).
    If a model is not found, dynamically queries OpenRouter/GitHub to seamlessly
    support newly introduced Antigravity models.
    """
    table = get_pricing_table()
    norm = normalize_model_name(base_name)
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Exact or partial match in local table
    for key, info in table.items():
        if key == norm or key in norm or norm in key:
            expires_at = info.get("expires_at")
            if expires_at and expires_at < today_str and auto_sync:
                # Expired promotional pricing: attempt refresh
                refreshed = fetch_from_openrouter(base_name)
                if refreshed:
                    save_pricing_entry(key, refreshed)
                    table[key] = refreshed
                    return key, refreshed["rates"], refreshed
            return key, info["rates"], info

    # 2. Dynamic auto-sync if model is missing
    if auto_sync:
        cfg = load_user_config()
        source = cfg.get("pricing_source", "openrouter").lower()

        if source == "openrouter":
            fetched = fetch_from_openrouter(base_name)
            if fetched:
                save_pricing_entry(norm, fetched)
                table[norm] = fetched
                return norm, fetched["rates"], fetched
        elif source in ("github", "git"):
            if sync_from_github():
                table = get_pricing_table(reload=True)
                for key, info in table.items():
                    if key == norm or key in norm or norm in key:
                        return key, info["rates"], info

    raise MissingModelPricingError(base_name, norm)
