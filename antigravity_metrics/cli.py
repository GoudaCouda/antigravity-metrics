"""Command line interface orchestration for Antigravity Metrics."""

import argparse
import json
import sys
from .config import get_base_dirs, save_user_config
from .parser import (
    find_conversations,
    get_active_or_latest_conversation,
    parse_conversation,
)
from .pricing import MissingModelPricingError
from .ui import render_conversation_list, render_summary_card


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Antigravity Conversation Token & Cost Inspector",
        prog="antigravity-metrics",
    )
    parser.add_argument("--conv", "-c", help="Conversation ID (default: active session)")
    parser.add_argument("--latest", action="store_true", help="Analyze most recently active conversation")
    parser.add_argument("--list", "-l", action="store_true", help="List recent conversations")
    parser.add_argument("--json", action="store_true", help="Output raw JSON metrics")
    parser.add_argument(
        "--set-source",
        choices=["openrouter", "github"],
        help="Configure fallback model pricing lookup source",
    )

    args = parser.parse_args()

    if args.set_source:
        save_user_config({"pricing_source": args.set_source})
        print(f"✓ Saved pricing lookup preference: '{args.set_source}' in config.json")
        sys.exit(0)

    app_dir, brain_dir = get_base_dirs()
    convs = find_conversations(brain_dir)

    if args.list:
        if args.json:
            print(json.dumps([{"id": c[0], "mtime": c[2]} for c in convs[:20]], indent=2))
        else:
            render_conversation_list(convs, app_dir)
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
    try:
        data = parse_conversation(target_id, target_dir, app_dir)
    except MissingModelPricingError as e:
        print(f"\n[ERROR] Missing Model Pricing: {e}\n", file=sys.stderr)
        sys.exit(2)
    except Exception as e:
        print(f"\n[ERROR] Failed to parse session metrics: {e}\n", file=sys.stderr)
        sys.exit(1)

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        render_summary_card(data)


if __name__ == "__main__":
    main()
