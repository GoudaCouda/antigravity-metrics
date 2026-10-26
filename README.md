# antigravity-metrics

Real-time token telemetry, prompt cache efficiency, and multi-model cost tracking for Google Antigravity.

## Overview

`antigravity-metrics` inspects active and historical Antigravity conversations to display token usage, prompt cache hit rates, model switches, and estimated costs in a compact terminal card.

```text
╭────────────────────── Token & Cost Summary ────────────────────────╮
│                                                                    │
│  ESTIMATED COST                ACTIVE MODEL                        │
│  $1.19                         Gemini 3.8 Flash (Medium)           │
│                                                                    │
│  TOKEN USAGE                   CACHE EFFICIENCY                    │
│  • Input:   960,167            • Hit Rate: 90.6% [█████████░]      │
│  • Output:  145,433            • Reused:   9,278,501 tok           │
│  • Total:   1,105,600          • Savings:  $3.55 (75% off)         │
│  ────────────────────────────────────────────────────────────────  │
│  BREAKDOWN BY MODEL                                                │
│   • Gemini 3.8 Flash (Medium)     $0.2539  97 turns · 937,339 tok  │
│   • Claude Sonnet 4.6 (Thinking)  $0.9350   9 turns · 168,261 tok  │
│  ────────────────────────────────────────────────────────────────  │
│  ACTIVITY                                                          │
│  • User turns:     10              • Avg output/turn: 1,372 tok    │
│  • Planner turns:  106             • Avg input/turn:  96,016 tok   │
│  • Tool actions:   96              • Cost/turn:       $0.0112      │
│                                                                    │
╰────────────────────────── ID: a42a22e0... ─────────────────────────╯
```

## Features

- **Active Session Detection**: Automatically inspects the current conversation without requiring session IDs.
- **Cache Tracking**: Visualizes prompt cache hit rates, reused tokens, and calculated cost savings.
- **Multi-Model Breakdown**: Attributes tokens, turns, and costs per model when a session switches models.
- **Session History**: Lists recent conversations with status, steps, and active model via `--list`.
- **JSON Output**: Outputs structured JSON for scripting and pipelines via `--json`.

## Installation

### Antigravity Skill (Recommended)

Prompt your Antigravity agent (IDE or CLI) with:

```text
Please install the token-metrics skill from https://github.com/GoudaCouda/antigravity-metrics.git into ~/.gemini/config/skills/token_metrics so I can use /token-metrics.
```

Once installed, run:
```text
/token-metrics
```

### Manual Install

**Linux / macOS:**
```bash
git clone https://github.com/GoudaCouda/antigravity-metrics.git ~/.gemini/config/skills/token_metrics
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/GoudaCouda/antigravity-metrics.git "$HOME\.gemini\config\skills\token_metrics"
```

### CLI Tool

```bash
pip install git+https://github.com/GoudaCouda/antigravity-metrics.git
```

## CLI Usage

| Command | Description |
| --- | --- |
| `antigravity-metrics` | Summary card for the current conversation |
| `antigravity-metrics --latest` | Inspect the most recent session |
| `antigravity-metrics --conv <id>` | Inspect a specific conversation by ID |
| `antigravity-metrics --list` | List recent conversations |
| `antigravity-metrics --json` | Output metrics as JSON |

## License

MIT © [GoudaCouda](https://github.com/GoudaCouda)
