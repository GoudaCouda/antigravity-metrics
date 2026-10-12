#!/usr/bin/env python3
"""
Antigravity Conversation Token & Cost Inspector
===============================================
A clean, modern, and instantly readable CLI tool to inspect real-time token
consumption, cache savings, and accurate model costs for Google Antigravity.
Supports per-model metrics breakdown across single and multi-model sessions.

Location:
  ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py
"""

import argparse
import json
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Reconfigure stdout for UTF-8 on Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Try importing Rich for modern TUI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich.rule import Rule
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Default Model Pricing Rates per 1M tokens: (uncached_prompt, cached_prompt, output_generation)
DEFAULT_MODEL_PRICING: Dict[str, Tuple[float, float, float]] = {
    # Gemini Flash Tier ($0.075 / $0.01875 / $0.300 per 1M)
    "gemini-3.8-flash": (0.075, 0.01875, 0.30),
    "gemini-3.7-flash": (0.075, 0.01875, 0.30),
    "gemini-3.5-flash": (0.075, 0.01875, 0.30),
    "gemini-2.5-flash": (0.075, 0.01875, 0.30),
    "gemini-1.5-flash": (0.075, 0.01875, 0.30),

    # Gemini Pro Tier ($1.25 / $0.3125 / $5.00 per 1M)
    "gemini-3.8-pro": (1.25, 0.3125, 5.00),
    "gemini-3.1-pro": (1.25, 0.3125, 5.00),
    "gemini-2.5-pro": (1.25, 0.3125, 5.00),
    "gemini-1.5-pro": (1.25, 0.3125, 5.00),

    # Anthropic Claude Tier
    "claude-sonnet-4.6": (3.00, 0.30, 15.00),
    "claude-3.7-sonnet": (3.00, 0.30, 15.00),
    "claude-3.5-sonnet": (3.00, 0.30, 15.00),
    "claude-3.5-haiku": (0.80, 0.08, 4.00),
    "claude-3-opus": (15.00, 1.50, 75.00),

    # OpenAI Tier
    "gpt-4o": (2.50, 1.25, 10.00),
    "gpt-4o-mini": (0.15, 0.075, 0.60),
    "gpt-oss-120b": (0.15, 0.0375, 0.60),
    "o3-mini": (1.10, 0.55, 4.40),
    "o1": (15.00, 7.50, 60.00),

    # Default fallback
    "default": (0.075, 0.01875, 0.30),
}


def get_pricing_file_path() -> Path:
    """Finds model_pricing.json next to this script or in the global skill directory."""
    script_dir = Path(__file__).resolve().parent
    local_path = script_dir / "model_pricing.json"
    if local_path.exists():
        return local_path

    home = Path.home()
    global_path = home / ".gemini" / "antigravity-cli" / "skills" / "token-metrics" / "model_pricing.json"
    if global_path.exists():
        return global_path

    return local_path


def load_model_pricing() -> Dict[str, Tuple[float, float, float]]:
    """Loads model pricing from model_pricing.json, falling back to built-ins."""
    table = dict(DEFAULT_MODEL_PRICING)
    p_file = get_pricing_file_path()
    if p_file.exists():
        try:
            with open(p_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                for k, v in data.items():
                    if isinstance(v, (list, tuple)) and len(v) == 3:
                        table[k] = (float(v[0]), float(v[1]), float(v[2]))
        except Exception:
            pass
    return table


# Load runtime table
MODEL_PRICING_TABLE: Dict[str, Tuple[float, float, float]] = load_model_pricing()


def get_base_dirs() -> Tuple[Path, Path]:
    home = Path.home()
    app_dir = home / ".gemini" / "antigravity-cli"
    brain_dir = app_dir / "brain"
    return app_dir, brain_dir


def parse_model_string(raw: str) -> Tuple[str, str]:
    raw = raw.strip().rstrip(".")
    m = re.match(r"^(.*?)\s*\((.*?)\)$", raw)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return raw, ""


def resolve_model_rates(base_name: str) -> Tuple[str, Tuple[float, float, float]]:
    global MODEL_PRICING_TABLE
    if not MODEL_PRICING_TABLE:
        MODEL_PRICING_TABLE = load_model_pricing()

    norm = base_name.lower().replace(" ", "-").replace("_", "-")
    for key, rates in MODEL_PRICING_TABLE.items():
        if key in norm:
            return key, rates

    if "flash" in norm:
        return "gemini-flash-tier", (0.075, 0.01875, 0.30)
    if "sonnet" in norm:
        return "claude-sonnet-tier", (3.00, 0.30, 15.00)
    if "haiku" in norm:
        return "claude-haiku-tier", (0.80, 0.08, 4.00)
    if "pro" in norm:
        return "gemini-pro-tier", (1.25, 0.3125, 5.00)
    if "gpt" in norm or "oss" in norm:
        return "gpt-oss-tier", (0.15, 0.0375, 0.60)

    return "default-tier", MODEL_PRICING_TABLE.get("default", (0.075, 0.01875, 0.30))



def get_conversation_metadata_from_db(app_dir: Path, conv_id: str) -> Dict[str, Any]:
    db_path = app_dir / "conversation_summaries.db"
    meta = {
        "title": "Active Conversation",
        "step_count": 0,
        "project_id": "default",
        "status": "CASCADE_RUN_STATUS_RUNNING",
        "parent_id": "",
    }
    if not db_path.exists():
        return meta
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute(
            """
            SELECT title, step_count, project_id, last_modified_time, status, parent_conversation_id
            FROM conversation_summaries
            WHERE conversation_id = ?
            """,
            (conv_id,),
        )
        row = cur.fetchone()
        if row:
            meta["title"] = row[0] or meta["title"]
            meta["step_count"] = row[1] or 0
            meta["project_id"] = row[2] or "default"
            meta["last_modified"] = row[3]
            meta["status"] = row[4] or "CASCADE_RUN_STATUS_IDLE"
            meta["parent_id"] = row[5] or ""
        conn.close()
    except Exception:
        pass
    return meta


def find_conversations(brain_dir: Path) -> List[Tuple[str, Path, float]]:
    convs = []
    if not brain_dir.exists():
        return convs
    for p in brain_dir.iterdir():
        if p.is_dir() and not p.name.startswith("."):
            log_file = p / ".system_generated" / "logs" / "transcript.jsonl"
            if log_file.exists():
                convs.append((p.name, p, log_file.stat().st_mtime))
    convs.sort(key=lambda x: x[2], reverse=True)
    return convs


def get_active_or_latest_conversation(app_dir: Path, brain_dir: Path) -> Optional[str]:
    db_path = app_dir / "conversation_summaries.db"
    if db_path.exists():
        try:
            conn = sqlite3.connect(db_path)
            cur = conn.cursor()
            cur.execute(
                """
                SELECT conversation_id FROM conversation_summaries
                WHERE status = 'CASCADE_RUN_STATUS_RUNNING'
                ORDER BY last_modified_time DESC LIMIT 1
                """
            )
            row = cur.fetchone()
            if row and (brain_dir / row[0]).exists():
                conn.close()
                return row[0]

            cur.execute(
                """
                SELECT conversation_id FROM conversation_summaries
                ORDER BY last_modified_time DESC LIMIT 1
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


def extract_model_events_from_transcript(log_path: Path) -> List[Tuple[int, str]]:
    pattern = re.compile(
        r"<USER_SETTINGS_CHANGE>.*?"
        r"Model Selection[`]?\s+from\s+.*?to\s+[`]?([^\r\n`<>]+?)"
        r"(?:`|\.\s*No need|\.\s*</USER_SETTINGS_CHANGE>|\.\s*$)"
        r".*?</USER_SETTINGS_CHANGE>",
        re.IGNORECASE | re.DOTALL,
    )
    events = []
    if not log_path.exists():
        return events

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                data = json.loads(line)
            except Exception:
                continue

            if data.get("type") == "USER_INPUT":
                content = data.get("content", "")
                m = pattern.search(content)
                if m:
                    raw_val = m.group(1).strip().rstrip(".")
                    step_idx = data.get("step_index", 0)
                    events.append((step_idx, raw_val))

    return events


def detect_initial_model(
    conv_id: str,
    conv_dir: Path,
    app_dir: Path,
    brain_dir: Path,
) -> str:
    log_path = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
    events = extract_model_events_from_transcript(log_path)

    if not events:
        db_meta = get_conversation_metadata_from_db(app_dir, conv_id)
        parent_id = db_meta.get("parent_id")
        if parent_id and (brain_dir / parent_id).exists():
            parent_log = brain_dir / parent_id / ".system_generated" / "logs" / "transcript.jsonl"
            events = extract_model_events_from_transcript(parent_log)

    if events:
        return events[0][1]

    return "Gemini 3.8 Flash (Medium)"


def parse_conversation(conv_id: str, conv_dir: Path, app_dir: Path, brain_dir: Path) -> Dict[str, Any]:
    log_path = conv_dir / ".system_generated" / "logs" / "transcript.jsonl"
    if not log_path.exists():
        return {}

    db_meta = get_conversation_metadata_from_db(app_dir, conv_id)
    initial_model_str = detect_initial_model(conv_id, conv_dir, app_dir, brain_dir)

    pattern = re.compile(
        r"<USER_SETTINGS_CHANGE>.*?"
        r"Model Selection[`]?\s+from\s+.*?to\s+[`]?([^\r\n`<>]+?)"
        r"(?:`|\.\s*No need|\.\s*</USER_SETTINGS_CHANGE>|\.\s*$)"
        r".*?</USER_SETTINGS_CHANGE>",
        re.IGNORECASE | re.DOTALL,
    )

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

    current_model_str = initial_model_str
    model_breakdown: Dict[str, Dict[str, Any]] = {}

    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            try:
                data = json.loads(line)
            except Exception:
                continue

            stype = data.get("type", "GENERIC")
            step_counts[stype] = step_counts.get(stype, 0) + 1

            if stype == "USER_INPUT":
                content = data.get("content", "")
                m = pattern.search(content)
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
                canonical_key, rates = resolve_model_rates(base)
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
                model_key = current_model_str
                if model_key not in model_breakdown:
                    model_breakdown[model_key] = {
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

                mb = model_breakdown[model_key]
                mb["input_tokens"] += inp
                mb["cache_read_tokens"] += cache
                mb["output_tokens"] += out
                mb["total_tokens"] += (inp + out)
                mb["estimated_cost_usd"] += step_cost
                mb["baseline_cost_usd"] += step_baseline
                mb["turns"] += 1

    # Finalize per-model metrics (hit rates, savings)
    for mk, mb in model_breakdown.items():
        mb_in = mb["input_tokens"]
        mb_cache = mb["cache_read_tokens"]
        mb_tot_in = mb_in + mb_cache
        mb["cache_hit_rate_pct"] = round((mb_cache / mb_tot_in * 100.0), 1) if mb_tot_in > 0 else 0.0
        mb_savings = max(0.0, mb["baseline_cost_usd"] - mb["estimated_cost_usd"])
        mb["savings_usd"] = mb_savings

    total_gross = direct_input + cache_read + output_tokens
    total_uncached = direct_input + output_tokens
    total_inputs = direct_input + cache_read
    cache_hit_rate = (cache_read / total_inputs * 100.0) if total_inputs > 0 else 0.0
    cache_savings = max(0.0, total_baseline_cost - total_estimated_cost)
    savings_pct = (cache_savings / total_baseline_cost * 100.0) if total_baseline_cost > 0 else 0.0

    active_base, active_effort = parse_model_string(current_model_str)
    active_canonical, _ = resolve_model_rates(active_base)

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


def render_clean_card(data: Dict[str, Any]):
    console = Console(force_terminal=True, legacy_windows=False, safe_box=False)

    tm = data.get("token_metrics", {})
    fm = data.get("financial_metrics", {})
    sc = data.get("step_counts", {})
    ami = data.get("active_model", {})
    model_breakdown = data.get("model_breakdown", {})

    cid = data.get("conversation_id", "")
    cost = fm.get("estimated_cost_usd", 0.0)
    savings = fm.get("cache_savings_usd", 0.0)
    savings_pct = fm.get("savings_discount_pct", 0.0)
    hit_rate = tm.get("cache_hit_rate_pct", 0.0)

    model_name = ami.get("display_name", "Gemini 3.8 Flash")
    effort = ami.get("effort", "")
    effort_tag = f"({effort})" if effort else ""

    # Format cost cleanly ($0.0012 or $0.0620)
    cost_str = f"${cost:.4f}" if cost < 1.0 else f"${cost:.2f}"
    savings_str = f"${savings:.4f}" if savings < 1.0 else f"${savings:.2f}"

    # Grid content
    grid = Table.grid(padding=(0, 4))
    grid.add_column("Col1", min_width=26)
    grid.add_column("Col2", min_width=28)

    # 1. Cost & Model Header
    cost_text = Text()
    cost_text.append("ESTIMATED COST\n", style="bold dim")
    cost_text.append(cost_str, style="bold green")

    model_text = Text()
    model_text.append("ACTIVE MODEL\n", style="bold dim")
    model_text.append(model_name, style="bold yellow")
    if effort_tag:
        model_text.append(f" {effort_tag}", style="magenta")

    grid.add_row(cost_text, model_text)
    grid.add_row("", "")

    # 2. Tokens & Cache
    tokens_text = Text()
    tokens_text.append("TOKEN USAGE\n", style="bold dim")
    tokens_text.append("• Input:   ", style="dim")
    tokens_text.append(f"{tm.get('input_tokens', 0):,}\n", style="bold white")
    tokens_text.append("• Output:  ", style="dim")
    tokens_text.append(f"{tm.get('output_tokens', 0):,}\n", style="bold white")
    tokens_text.append("• Total:   ", style="dim")
    tokens_text.append(f"{tm.get('total_billable_tokens', 0):,}", style="bold cyan")

    # Wide bar on the same line as Hit Rate
    bar_len = 10
    filled = int(round(hit_rate / 100.0 * bar_len))
    bar = "█" * filled + "░" * (bar_len - filled)
    bar_color = "green" if hit_rate >= 50 else ("yellow" if hit_rate > 0 else "dim")
    cache_style = "bold green" if hit_rate >= 50 else ("bold yellow" if hit_rate > 0 else "dim")

    cache_text = Text()
    cache_text.append("CACHE EFFICIENCY\n", style="bold dim")
    cache_text.append("• Hit Rate: ", style="dim")
    cache_text.append(f"{hit_rate:.1f}% ", style=cache_style)
    cache_text.append(f"[{bar}]\n", style=bar_color)
    cache_text.append("• Reused:   ", style="dim")
    cache_text.append(f"{tm.get('cache_read_tokens', 0):,} tok\n", style="dim white")
    cache_text.append("• Savings:  ", style="dim")
    cache_text.append(savings_str, style="bold cyan")
    cache_text.append(f" ({savings_pct:.0f}% off)", style="dim")

    grid.add_row(tokens_text, cache_text)

    main = Table.grid(expand=True)
    main.add_row(grid)

    # 3. Model breakdown section if session used multiple models
    if len(model_breakdown) > 1:
        main.add_row(Rule(style="dim"))
        main.add_row(Text("BREAKDOWN BY MODEL", style="bold dim"))
        mb_table = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        mb_table.add_column("Model", style="bold yellow", no_wrap=True)
        mb_table.add_column("Cost", justify="right", style="bold green")
        mb_table.add_column("Stats", justify="right", style="dim", no_wrap=True)
        for mk, mb in model_breakdown.items():
            mb_cost_str = f"${mb['estimated_cost_usd']:.4f}" if mb['estimated_cost_usd'] < 1.0 else f"${mb['estimated_cost_usd']:.2f}"
            mb_table.add_row(
                f"• {mk}",
                mb_cost_str,
                f"{mb['turns']} turns · {mb['total_tokens']:,} tok",
            )
        main.add_row(mb_table)

    # 4. Activity section
    u_in = sc.get("USER_INPUT", 0)
    p_res = sc.get("PLANNER_RESPONSE", 0)
    t_exec = sc.get("GENERIC", 0)
    total_out = tm.get("output_tokens", 0)
    total_in = tm.get("input_tokens", 0)
    avg_out = int(total_out / p_res) if p_res > 0 else 0
    avg_in = int(total_in / u_in) if u_in > 0 else 0

    main.add_row(Rule(style="dim"))
    main.add_row(Text("ACTIVITY", style="bold dim"))

    act_grid = Table.grid(padding=(0, 4), expand=True)
    act_grid.add_column("Left", min_width=26)
    act_grid.add_column("Right", min_width=28)

    left_act = Text()
    left_act.append("• User turns:     ", style="dim")
    left_act.append(f"{u_in}\n", style="bold white")
    left_act.append("• Planner turns:  ", style="dim")
    left_act.append(f"{p_res}\n", style="bold white")
    left_act.append("• Tool actions:   ", style="dim")
    left_act.append(f"{t_exec}", style="bold white")

    right_act = Text()
    right_act.append("• Avg output/turn: ", style="dim")
    right_act.append(f"{avg_out:,} tok\n", style="bold cyan")
    right_act.append("• Avg input/turn:  ", style="dim")
    right_act.append(f"{avg_in:,} tok\n", style="bold cyan")
    right_act.append("• Cost/turn:       ", style="dim")
    avg_cost = cost / p_res if p_res > 0 else 0.0
    right_act.append(f"${avg_cost:.4f}", style="bold green")

    act_grid.add_row(left_act, right_act)
    main.add_row(act_grid)

    panel = Panel(
        main,
        title="[bold cyan]⚡ Token & Cost Summary[/bold cyan]",
        subtitle=f"[dim]ID: {cid[:8]}...[/dim]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, 2),
        expand=False,
    )

    console.print()
    console.print(panel)
    console.print()


def render_model_breakdown_table(data: Dict[str, Any]):
    """Renders a dedicated detailed breakdown table for each model used."""
    console = Console(force_terminal=True, legacy_windows=False, safe_box=False)
    mb = data.get("model_breakdown", {})

    table = Table(
        box=box.ROUNDED,
        title="[bold cyan]⚡ Per-Model Metrics Breakdown[/bold cyan]",
        border_style="cyan",
        header_style="bold cyan",
        expand=False,
    )
    table.add_column("Model / Tier", style="bold yellow", min_width=24)
    table.add_column("Cost", justify="right", style="bold green", min_width=10)
    table.add_column("Input", justify="right", style="bold white", min_width=10)
    table.add_column("Cache", justify="right", style="dim", min_width=10)
    table.add_column("Output", justify="right", style="bold white", min_width=9)
    table.add_column("Hit Rate", justify="right", style="green", min_width=9)
    table.add_column("Turns", justify="right", style="bold magenta", min_width=7)

    for mk, mdata in mb.items():
        m_cost = mdata.get("estimated_cost_usd", 0.0)
        c_str = f"${m_cost:.4f}" if m_cost < 1.0 else f"${m_cost:.2f}"
        table.add_row(
            mk,
            c_str,
            f"{mdata.get('input_tokens', 0):,}",
            f"{mdata.get('cache_read_tokens', 0):,}",
            f"{mdata.get('output_tokens', 0):,}",
            f"{mdata.get('cache_hit_rate_pct', 0.0):.1f}%",
            str(mdata.get("turns", 0)),
        )

    console.print()
    console.print(table)
    console.print()


def render_rich_list(convs: List[Tuple[str, Path, float]], app_dir: Path, brain_dir: Path):
    console = Console(force_terminal=True, legacy_windows=False, safe_box=False)

    table = Table(
        box=box.ROUNDED,
        expand=False,
        title="[bold cyan]⚡ Recent Conversations[/bold cyan]",
        border_style="cyan",
        header_style="bold cyan",
    )
    table.add_column("St", justify="center", width=2, no_wrap=True)
    table.add_column("Session", style="dim cyan", width=10, no_wrap=True)
    table.add_column("Modified", style="dim white", width=12, no_wrap=True)
    table.add_column("Model", style="bold yellow", width=22, no_wrap=True)
    table.add_column("Steps", justify="right", style="bold magenta", width=6, no_wrap=True)
    table.add_column("Title", style="white", no_wrap=True)

    for cid, cdir, mtime in convs[:10]:
        dt = datetime.fromtimestamp(mtime).strftime("%m-%d %H:%M")
        meta = get_conversation_metadata_from_db(app_dir, cid)
        is_running = "RUNNING" in meta.get("status", "").upper()
        status_symbol = "[bold green]●[/]" if is_running else "[dim]○[/]"

        init_model = detect_initial_model(cid, cdir, app_dir, brain_dir)
        short_id = f"{cid[:8]}…"

        table.add_row(
            status_symbol,
            short_id,
            dt,
            init_model[:22],
            str(meta.get("step_count", 0)),
            meta.get("title", "Active Session")[:36],
        )

    console.print()
    console.print(table)
    console.print()


def main():
    parser = argparse.ArgumentParser(description="Antigravity Conversation Token & Cost Inspector")
    parser.add_argument("--conv", "-c", help="Conversation ID (default: active session)")
    parser.add_argument("--latest", action="store_true", help="Analyze most recently active conversation")
    parser.add_argument("--models", "--by-model", action="store_true", help="Show dedicated per-model metrics table")
    parser.add_argument("--list", "-l", action="store_true", help="List recent conversations")
    parser.add_argument("--json", action="store_true", help="Output raw JSON metrics")

    args = parser.parse_args()
    app_dir, brain_dir = get_base_dirs()
    convs = find_conversations(brain_dir)

    if args.list:
        if RICH_AVAILABLE and not args.json:
            render_rich_list(convs, app_dir, brain_dir)
        else:
            for cid, cdir, mtime in convs[:10]:
                meta = get_conversation_metadata_from_db(app_dir, cid)
                print(f"{cid[:8]}... {meta.get('title')}")
        sys.exit(0)

    target_id = None
    if args.conv:
        target_id = args.conv
    elif args.latest:
        target_id = convs[0][0] if convs else None
    else:
        target_id = get_active_or_latest_conversation(app_dir, brain_dir)

    if not target_id or not (brain_dir / target_id).exists():
        print(f"Error: Conversation directory not found in {brain_dir}", file=sys.stderr)
        sys.exit(1)

    target_dir = brain_dir / target_id
    data = parse_conversation(target_id, target_dir, app_dir, brain_dir)

    if args.json:
        print(json.dumps(data, indent=2))
    elif RICH_AVAILABLE:
        if args.models:
            render_model_breakdown_table(data)
        else:
            render_clean_card(data)
    else:
        print(json.dumps(data, indent=2))


if __name__ == "__main__":
    main()
