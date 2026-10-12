# ⚡ antigravity-metrics

> Modern, real-time token telemetry, prompt cache efficiency, and multi-model cost inspector for **Google Antigravity**.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Rich](https://img.shields.io/badge/TUI-Rich-cyan.svg)](https://github.com/Textualize/rich)
[![Antigravity](https://img.shields.io/badge/Antigravity-Plugin%20%7C%20Skill-blueviolet.svg)](#-installation)

`antigravity-metrics` provides real-time financial attribution, prompt cache hit-rate visualization, and per-model consumption breakdowns for active and historical Antigravity conversations.

---

## 📸 Sample Output

### Real-Time Session Summary Card
```text
╭────────────────────── ⚡ Token & Cost Summary ──────────────────────╮
│                                                                     │
│  ESTIMATED COST                ACTIVE MODEL                         │
│  $1.19                         Gemini 3.8 Flash (Medium)            │
│                                                                     │
│  TOKEN USAGE                   CACHE EFFICIENCY                     │
│  • Input:   960,167            • Hit Rate: 90.6% [█████████░]       │
│  • Output:  145,433            • Reused:   9,278,501 tok            │
│  • Total:   1,105,600          • Savings:  $3.55 (75% off)          │
│  ─────────────────────────────────────────────────────────────────  │
│  BREAKDOWN BY MODEL                                                 │
│   • Gemini 3.8 Flash (Medium)     $0.2539  97 turns · 937,339 tok   │
│   • Claude Sonnet 4.6 (Thinking)  $0.9350   9 turns · 168,261 tok   │
│  ─────────────────────────────────────────────────────────────────  │
│  ACTIVITY                                                           │
│  • User turns:     10              • Avg output/turn: 1,372 tok     │
│  • Planner turns:  106             • Avg input/turn:  96,016 tok    │
│  • Tool actions:   96              • Cost/turn:       $0.0112       │
│                                                                     │
╰────────────────────────── ID: a42a22e0... ──────────────────────────╯
```

### Detailed Per-Model Breakdown (`--models`)
```text
                                   ⚡ Per-Model Metrics Breakdown
╭──────────────────────────┬────────────┬────────────┬────────────┬───────────┬──────────┬───────╮
│ Model / Tier             │       Cost │      Input │      Cache │    Output │ Hit Rate │ Turns │
├──────────────────────────┼────────────┼────────────┼────────────┼───────────┼──────────┼───────┤
│ Gemini 3.8 Flash (Medium)│    $0.2539 │    960,167 │  9,278,501 │   145,433 │    90.6% │    97 │
│ Claude Sonnet 4.6 (Think)│    $0.9350 │    168,261 │  1,420,100 │    32,100 │    89.4% │     9 │
╰──────────────────────────┴────────────┴────────────┴────────────┴───────────┴──────────┴───────╯
```

---

## ✨ Features

- **🎯 Zero-Config Active Session Detection**: Automatically targets your currently running Antigravity conversation without needing session UUIDs.
- **⚡ Prompt Cache Tracking**: Measures uncached input tokens vs. cached reads, displays an inline wide bar (`[█████████░]`), and calculates exact dollar savings.
- **🔄 Multi-Model Switching Attribution**: Seamlessly tracks when a conversation switches models (e.g. Gemini 3.8 Flash ➔ Claude Sonnet 4.6 ➔ GPT-OSS 120B) and attributes exact tokens, turns, and costs to each model individually.
- **📊 Activity Telemetry**: Tracks user turns, planner iterations, tool executions, average generation length per turn, and cost per turn.
- **📑 Conversation History Table**: List all recent sessions (`--list`) with live status indicators (`● Active`, `○ Idle`), step counts, and active models.
- **🤖 JSON Export**: Pipe machine-readable metrics into CI/CD, logging, or dashboards with `--json`.

---

## 🚀 Installation

You can install and use `antigravity-metrics` either as a **native Antigravity Skill / Plugin** or as a **standalone CLI tool**.

### Option A: Install as an Antigravity Plugin / Skill

To invoke metrics natively in your chat sessions via the `/token-metrics` slash command:

#### Linux / macOS
```bash
git clone https://github.com/GoudaCouda/antigravity-metrics.git ~/.gemini/antigravity-cli/skills/token-metrics
```

#### Windows (PowerShell)
```powershell
git clone https://github.com/GoudaCouda/antigravity-metrics.git "$HOME\.gemini\antigravity-cli\skills\token-metrics"
```

Once installed, simply type:
```text
/token-metrics
```
inside any Antigravity conversation!

---

### Option B: Install as a Standalone CLI Tool

Install globally in your Python environment:

```bash
# Clone and install via pip
git clone https://github.com/GoudaCouda/antigravity-metrics.git
cd antigravity-metrics
pip install -e .

# Or directly with pip
pip install git+https://github.com/GoudaCouda/antigravity-metrics.git
```

This registers two commands in your system PATH:
```bash
antigravity-metrics
# or
token-metrics
```

#### Quick Standalone Run (No Installation Required)
```bash
python token_metrics.py
```

---

## 🛠 Usage & CLI Flags

| Command | Description |
| :--- | :--- |
| `antigravity-metrics` | Show clean summary card for the current active conversation |
| `antigravity-metrics --models` | Output dedicated per-model metrics breakdown table |
| `antigravity-metrics --latest` | Inspect the most recently active session |
| `antigravity-metrics --conv <id>` | Inspect a specific conversation by ID or UUID |
| `antigravity-metrics --list` | List recent conversations with model, steps, and status |
| `antigravity-metrics --json` | Output structured raw JSON for pipelines or monitoring |

---

## 💰 Supported Model Pricing Table

Rates per 1M tokens (Standard API list pricing):

| Model Family | Direct Input | Cache Read | Output |
| :--- | :---: | :---: | :---: |
| **Gemini 3.8 / 3.7 / 3.5 / 2.5 Flash** | $0.075 | $0.01875 | $0.300 |
| **Gemini 3.8 / 3.1 / 2.5 / 1.5 Pro** | $1.250 | $0.31250 | $5.000 |
| **Claude Sonnet 4.6 / 3.7 / 3.5** | $3.000 | $0.30000 | $15.000 |
| **Claude 3.5 Haiku** | $0.800 | $0.08000 | $4.000 |
| **Claude 3 Opus** | $15.000 | $1.50000 | $75.000 |
| **GPT-4o** | $2.500 | $1.25000 | $10.000 |
| **GPT-4o mini** | $0.150 | $0.07500 | $0.600 |
| **GPT-OSS 120B** | $0.150 | $0.03750 | $0.600 |
| **o3-mini** | $1.100 | $0.55000 | $4.400 |
| **o1** | $15.000 | $7.50000 | $60.000 |

---

## 📄 License

MIT © [Austin (GoudaCouda)](https://github.com/GoudaCouda)
