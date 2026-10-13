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


> /token-metrics
────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────
esc to cancel                                                                      accept-edits · Gemini  Flash · medium

● Ran (python -c " import os os.environ['NO_COLOR'] = '1' import subprocess, sys res = subproces...) (ctrl+o to expand)


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

---

## ✨ Features

- **🎯 Zero-Config Active Session Detection**: Automatically targets your currently running Antigravity conversation without needing session UUIDs.
- **⚡ Prompt Cache Tracking**: Measures uncached input tokens vs. cached reads, displays an inline wide bar (`[█████████░]`), and calculates exact dollar savings.
- **🔄 Multi-Model Switching **: Seamlessly tracks when a conversation switches models (e.g. Gemini 3.8 Flash ➔ Claude Sonnet 4.6 ➔ GPT-OSS 120B) and attributes exact tokens, turns, and costs to each model individually.
- **📊 Activity Stats**: Tracks user turns, planner iterations, tool executions, average generation length per turn, and cost per turn.
- **📑 Conversation History Table**: List all recent sessions (`--list`) with live status indicators (`● Active`, `○ Idle`), step counts, and active models.
- **🤖 JSON Export**: Pipe machine-readable metrics into CI/CD, logging, or dashboards with `--json`.

---

## 🚀 Installation

You can install and use `antigravity-metrics` either as a **native Antigravity Skill / Plugin** or as a **standalone CLI tool**.

### Option A: Install as an Antigravity Skill (Recommended)

To invoke metrics natively in your chat sessions via the `/token-metrics` slash command in **both the Antigravity IDE and `agy` CLI**, install directly into the global configuration directory (`~/.gemini/config/skills/token_metrics`):

#### Quick 1-Line Install to Global Config Location

Streams directly from GitHub into memory and extracts without creating temporary archive files:

**Linux / macOS:**
```bash
mkdir -p ~/.gemini/config/skills/token_metrics && curl -sSL https://github.com/GoudaCouda/antigravity-metrics/releases/latest/download/token-metrics.tar.gz | tar -xz -C ~/.gemini/config/skills/token_metrics
```

**Windows (PowerShell):**
```powershell
New-Item -ItemType Directory -Path "$HOME\.gemini\config\skills\token_metrics" -Force; curl.exe -sSL https://github.com/GoudaCouda/antigravity-metrics/releases/latest/download/token-metrics.tar.gz | tar.exe -xz -C "$HOME\.gemini\config\skills\token_metrics"
```

#### Alternative: Install via Git Clone

**Linux / macOS:**
```bash
git clone https://github.com/GoudaCouda/antigravity-metrics.git ~/.gemini/config/skills/token_metrics
```

**Windows (PowerShell):**
```powershell
git clone https://github.com/GoudaCouda/antigravity-metrics.git "$HOME\.gemini\config\skills\token_metrics"
```

Once installed, simply type:
```text
/token-metrics
```
inside any Antigravity conversation (IDE or CLI)!

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

---

## 🛠 Usage & CLI Flags

| Command | Description |
| :--- | :--- |
| `antigravity-metrics` | Show clean summary card for the current active conversation |
| `antigravity-metrics --latest` | Inspect the most recently active session |
| `antigravity-metrics --conv <id>` | Inspect a specific conversation by ID or UUID |
| `antigravity-metrics --list` | List recent conversations with model, steps, and status |
| `antigravity-metrics --json` | Output structured raw JSON for pipelines or monitoring |


## 📄 License

MIT © [GoudaCouda](https://github.com/GoudaCouda)
