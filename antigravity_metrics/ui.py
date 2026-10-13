"""Terminal User Interface (TUI) renderers using Rich with dynamic terminal size detection."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

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


def get_terminal_width(default: int = 80) -> int:
    """Safely retrieves terminal column width."""
    try:
        return max(40, shutil.get_terminal_size((default, 24)).columns)
    except Exception:
        return default


def render_summary_card(data: Dict[str, Any]) -> None:
    """Renders the responsive TUI token and cost summary card without wrapping."""
    if not RICH_AVAILABLE:
        import json
        print(json.dumps(data, indent=2))
        return

    term_width = get_terminal_width(80)
    card_width = max(48, min(term_width, 76))
    pad_h = 2 if card_width >= 66 else 1
    col_pad = 4 if card_width >= 66 else 2
    col_w = max(18, (card_width - (pad_h * 2) - col_pad - 4) // 2)

    console = Console(width=term_width, force_terminal=True, legacy_windows=False, safe_box=False)

    tm = data.get("token_metrics", {})
    fm = data.get("financial_metrics", {})
    sc = data.get("step_counts", {})
    ami = data.get("active_model", {})
    model_breakdown = data.get("model_breakdown", {})

    convo_title = data.get("title", "Active Session").strip()
    cost = fm.get("estimated_cost_usd", 0.0)
    savings = fm.get("cache_savings_usd", 0.0)
    savings_pct = fm.get("savings_discount_pct", 0.0)
    hit_rate = tm.get("cache_hit_rate_pct", 0.0)

    model_name = ami.get("display_name", "Gemini 3.8 Flash")
    effort = ami.get("effort", "")
    effort_tag = f"({effort})" if effort else ""

    cost_str = f"${cost:.4f}" if cost < 1.0 else f"${cost:.2f}"
    savings_str = f"${savings:.4f}" if savings < 1.0 else f"${savings:.2f}"

    # Grid columns with dynamic widths based on terminal size
    grid = Table.grid(padding=(0, col_pad))
    grid.add_column("Col1", min_width=col_w)
    grid.add_column("Col2", min_width=col_w)

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

    # 2. Token Usage & Cache Efficiency
    tokens_text = Text()
    tokens_text.append("TOKEN USAGE\n", style="bold dim")
    tokens_text.append("• Input:   ", style="dim")
    tokens_text.append(f"{tm.get('input_tokens', 0):,}\n", style="bold white")
    tokens_text.append("• Output:  ", style="dim")
    tokens_text.append(f"{tm.get('output_tokens', 0):,}\n", style="bold white")
    tokens_text.append("• Total:   ", style="dim")
    tokens_text.append(f"{tm.get('total_billable_tokens', 0):,}", style="bold cyan")

    bar_len = 10 if card_width >= 66 else 6
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

    # 3. Model breakdown section if multiple models used
    if len(model_breakdown) > 1:
        main.add_row(Rule(style="dim"))
        main.add_row(Text("BREAKDOWN BY MODEL", style="bold dim"))
        mb_table = Table(box=None, show_header=False, padding=(0, 1), expand=True)
        mb_table.add_column("Model", style="bold yellow", ratio=3, overflow="ellipsis", no_wrap=True)
        mb_table.add_column("Cost", justify="right", style="bold green", min_width=8, no_wrap=True)
        mb_table.add_column("Turns", justify="right", style="dim white", min_width=8, no_wrap=True)
        mb_table.add_column("Tokens", justify="right", style="dim", min_width=12, no_wrap=True)
        for mk, mb in model_breakdown.items():
            mb_cost = mb["estimated_cost_usd"]
            mb_cost_str = f"${mb_cost:.4f}" if mb_cost < 1.0 else f"${mb_cost:.2f}"
            mb_table.add_row(
                f"• {mk}",
                mb_cost_str,
                f"{mb['turns']} turns",
                f"· {mb['total_tokens']:,} tok",
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

    act_grid = Table.grid(padding=(0, col_pad), expand=True)
    act_grid.add_column("Left", min_width=col_w)
    act_grid.add_column("Right", min_width=col_w)

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

    max_title_len = max(15, card_width - 32)
    display_title = convo_title if len(convo_title) <= max_title_len else f"{convo_title[:max_title_len - 3]}..."
    panel = Panel(
        main,
        title="[bold cyan]⚡ Token & Cost Summary[/bold cyan]",
        subtitle=f"[dim]{display_title}[/dim]",
        box=box.ROUNDED,
        border_style="cyan",
        padding=(1, pad_h),
        width=card_width,
        expand=False,
    )

    console.print()
    console.print(panel)
    console.print()


def render_conversation_list(
    convs: List[Tuple[str, Path, float]],
    app_dir: Path,
) -> None:
    """Renders a responsive formatted list of recent Antigravity conversations."""
    if not RICH_AVAILABLE:
        for cid, _, _ in convs[:10]:
            print(cid)
        return

    from .parser import get_conversation_metadata

    term_width = get_terminal_width(80)
    console = Console(width=term_width, force_terminal=True, legacy_windows=False, safe_box=False)

    max_title_len = max(15, term_width - 38)
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
    table.add_column("Steps", justify="right", style="bold magenta", width=6, no_wrap=True)
    table.add_column("Title", style="white", overflow="ellipsis", no_wrap=True)

    for cid, _, mtime in convs[:10]:
        dt = datetime.fromtimestamp(mtime).strftime("%m-%d %H:%M")
        meta = get_conversation_metadata(app_dir, cid)
        is_running = "RUNNING" in meta.get("status", "").upper()
        status_symbol = "[bold green]●[/]" if is_running else "[dim]○[/]"
        short_id = f"{cid[:8]}…"

        table.add_row(
            status_symbol,
            short_id,
            dt,
            str(meta.get("step_count", 0)),
            meta.get("title", "Active Session")[:max_title_len],
        )

    console.print()
    console.print(table)
    console.print()
