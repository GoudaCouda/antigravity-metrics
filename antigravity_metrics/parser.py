"""Single-pass Antigravity transcript parser and session resolver."""

import json
import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from .pricing import parse_model_string, resolve_model_rates

# Regex pattern for model switches in transcript
_SETTINGS_CHANGE_PATTERN = re.compile(
    r"<USER_SETTINGS_CHANGE>.*?"
    r"Model Selection[`]?\s+from\s+.*?to\s+[`]?([^\r\n`<>]+?)"
    r"(?:`|\.\s*(?:No need|(?=</USER_SETTINGS_CHANGE>)|$))"
    r".*?</USER_SETTINGS_CHANGE>",
    re.IGNORECASE | re.DOTALL,
)


def get_conversation_metadata(app_dir: Path, conv_id: str) -> Dict[str, Any]:
    """Retrieves session metadata (title, status, step_count) from SQLite database."""
    db_path = app_dir / "conversation_summaries.db"
    meta = {
        "title": "Active Session",
        "step_count": 0,
        "status": "CASCADE_RUN_STATUS_RUNNING",
    }
    if not db_path.exists():
        return meta

    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT title, step_count, status
            FROM conversation_summaries
            WHERE conversation_id = ?
            """,
            (conv_id,),
        )
        row = cur.fetchone()
        if row:
            meta["title"] = row[0] or meta["title"]
            meta["step_count"] = row[1] or 0
            meta["status"] = row[2] or "CASCADE_RUN_STATUS_IDLE"
        conn.close()
    except Exception:
        pass
    return meta


def find_conversations(brain_dir: Path) -> List[Tuple[str, Path, float]]:
    """Discovers sessions by searching brain_dir for transcript.jsonl files."""
    convs = []
    if not brain_dir.exists():
        return convs

    for p in brain_dir.iterdir():
        if p.is_dir() and not p.name.startswith("."):
            log_file = p / ".system_generated" / "logs" / "transcript.jsonl"
            if log_file.exists():
                try:
                    convs.append((p.name, p, log_file.stat().st_mtime))
                except OSError:
                    continue

    convs.sort(key=lambda x: x[2], reverse=True)
    return convs


def get_active_or_latest_conversation(app_dir: Path, brain_dir: Path) -> Optional[str]:
    """Finds currently running or most recently modified conversation."""
    db_path = app_dir / "conversation_summaries.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT conversation_id FROM conversation_summaries
                ORDER BY (status = 'CASCADE_RUN_STATUS_RUNNING') DESC, last_modified_time DESC
                LIMIT 1
                """
            )
            row = cur.fetchone()
            conn.close()
            if row and (brain_dir / row[0]).exists():
                return row[0]
        except Exception:
            pass

    convs = find_conversations(brain_dir)
    return convs[0][0] if convs else None


def parse_conversation(
    conv_id: str,
    conv_dir: Path,
    app_dir: Path,
) -> Dict[str, Any]:
    """
    Parses a conversation's transcript.jsonl in a single streaming pass.
    Tracks model transitions, token consumption, and per-model costs on the fly.
    """
    log_path = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
    if not log_path.exists():
        return {}

    db_meta = get_conversation_metadata(app_dir, conv_id)

    step_counts = {
        "USER_INPUT": 0,
        "PLANNER_RESPONSE": 0,
        "GENERIC": 0,
        "SYSTEM_MESSAGE": 0,
    }

    direct_input = 0
    cache_read = 0
    output_tokens = 0
    reasoning_tokens = 0
    total_estimated_cost = 0.0
    total_baseline_cost = 0.0

    current_model_str = "Gemini 3.8 Flash (Medium)"
    model_breakdown: Dict[str, Dict[str, Any]] = {}

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            try:
                data = json.loads(line)
            except Exception:
                continue

            stype = data.get("type", "GENERIC")
            step_counts[stype] = step_counts.get(stype, 0) + 1

            if stype == "USER_INPUT":
                content = data.get("content", "")
                m = _SETTINGS_CHANGE_PATTERN.search(content)
                if m:
                    current_model_str = m.group(1).strip().rstrip(".")

            inp = data.get("input_tokens") or 0
            cache = data.get("cache_read_tokens") or 0
            out = data.get("output_tokens") or 0
            reas = data.get("reasoning_tokens") or 0

            direct_input += inp
            cache_read += cache
            output_tokens += out
            reasoning_tokens += reas

            if stype == "PLANNER_RESPONSE":
                base, effort = parse_model_string(current_model_str)
                canonical_key, rates, info = resolve_model_rates(base)
                p_in, p_cache, p_out = rates

                step_cost = (
                    (inp / 1_000_000.0) * p_in
                    + (cache / 1_000_000.0) * p_cache
                    + (out / 1_000_000.0) * p_out
                )
                step_baseline = (
                    ((inp + cache) / 1_000_000.0) * p_in
                    + (out / 1_000_000.0) * p_out
                )

                total_estimated_cost += step_cost
                total_baseline_cost += step_baseline

                # Track per-model aggregation
                if current_model_str not in model_breakdown:
                    model_breakdown[current_model_str] = {
                        "name": base,
                        "effort": effort,
                        "canonical_key": canonical_key,
                        "input_tokens": 0,
                        "cache_read_tokens": 0,
                        "output_tokens": 0,
                        "total_tokens": 0,
                        "estimated_cost_usd": 0.0,
                        "baseline_cost_usd": 0.0,
                        "turns": 0,
                    }

                mb = model_breakdown[current_model_str]
                mb["input_tokens"] += inp
                mb["cache_read_tokens"] += cache
                mb["output_tokens"] += out
                mb["total_tokens"] += (inp + out)
                mb["estimated_cost_usd"] += step_cost
                mb["baseline_cost_usd"] += step_baseline
                mb["turns"] += 1

    # Finalize per-model metrics
    for mb in model_breakdown.values():
        mb_tot_in = mb["input_tokens"] + mb["cache_read_tokens"]
        mb["cache_hit_rate_pct"] = (
            round((mb["cache_read_tokens"] / mb_tot_in * 100.0), 1) if mb_tot_in > 0 else 0.0
        )
        mb["savings_usd"] = max(0.0, mb["baseline_cost_usd"] - mb["estimated_cost_usd"])

    total_gross = direct_input + cache_read + output_tokens
    total_uncached = direct_input + output_tokens
    total_inputs = direct_input + cache_read
    cache_hit_rate = (cache_read / total_inputs * 100.0) if total_inputs > 0 else 0.0
    cache_savings = max(0.0, total_baseline_cost - total_estimated_cost)
    savings_pct = (cache_savings / total_baseline_cost * 100.0) if total_baseline_cost > 0 else 0.0

    active_base, active_effort = parse_model_string(current_model_str)
    try:
        active_canonical, _, _ = resolve_model_rates(active_base, auto_sync=False)
    except Exception:
        active_canonical = active_base.lower().replace(" ", "-")

    return {
        "conversation_id": conv_id,
        "title": db_meta.get("title", "Active Session"),
        "status": db_meta.get("status", "CASCADE_RUN_STATUS_RUNNING"),
        "active_model": {
            "full_name": current_model_str,
            "display_name": active_base,
            "effort": active_effort,
            "canonical_key": active_canonical,
        },
        "model_breakdown": model_breakdown,
        "step_counts": step_counts,
        "token_metrics": {
            "input_tokens": direct_input,
            "cache_read_tokens": cache_read,
            "output_tokens": output_tokens,
            "total_billable_tokens": total_uncached,
            "gross_tokens": total_gross,
            "cache_hit_rate_pct": round(cache_hit_rate, 1),
        },
        "financial_metrics": {
            "estimated_cost_usd": total_estimated_cost,
            "cost_without_cache_usd": total_baseline_cost,
            "cache_savings_usd": cache_savings,
            "savings_discount_pct": round(savings_pct, 1),
        },
    }
