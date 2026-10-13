"""Configuration and directory resolution for Antigravity Metrics."""

import json
import sys
from pathlib import Path
from typing import Any, Dict, Tuple

# Ensure UTF-8 console output on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def get_base_dirs() -> Tuple[Path, Path]:
    """Returns (app_dir, brain_dir) for Antigravity CLI."""
    home = Path.home()
    app_dir = home / ".gemini" / "antigravity-cli"
    brain_dir = app_dir / "brain"
    return app_dir, brain_dir


def get_pricing_file_path() -> Path:
    """Finds model_pricing.json next to the project or in skill directories."""
    local_path = Path(__file__).resolve().parent.parent / "model_pricing.json"
    if local_path.exists():
        return local_path

    home = Path.home()
    config_path = home / ".gemini" / "config" / "skills" / "token-metrics" / "model_pricing.json"
    if config_path.exists():
        return config_path

    global_path = home / ".gemini" / "antigravity-cli" / "skills" / "token-metrics" / "model_pricing.json"
    if global_path.exists():
        return global_path

    return local_path


def get_config_file_path() -> Path:
    """Finds config.json next to the project or in skill directories."""
    local_path = Path(__file__).resolve().parent.parent / "config.json"
    if local_path.exists():
        return local_path

    home = Path.home()
    config_path = home / ".gemini" / "config" / "skills" / "token-metrics" / "config.json"
    if config_path.exists():
        return config_path

    global_path = home / ".gemini" / "antigravity-cli" / "skills" / "token-metrics" / "config.json"
    if global_path.exists():
        return global_path

    return local_path


def load_user_config() -> Dict[str, Any]:
    """Loads user configuration preferences."""
    cfg_file = get_config_file_path()
    if cfg_file.exists():
        try:
            with open(cfg_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"pricing_source": "openrouter"}


def save_user_config(cfg: Dict[str, Any]) -> None:
    """Saves user configuration preferences."""
    cfg_file = get_config_file_path()
    try:
        cfg_file.parent.mkdir(parents=True, exist_ok=True)
        with open(cfg_file, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"[WARN] Failed to write config to {cfg_file}: {e}", file=sys.stderr)
