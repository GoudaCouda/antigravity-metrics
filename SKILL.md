---
name: token-metrics
description: Analyze conversation token consumption, prompt cache hit rate, and estimated model pricing with an ANSI TUI breakdown.
---

# Token and Cost Metrics Skill

Inspects real-time token consumption, cache efficiency, and estimated model costs for Antigravity conversations. The Python script automatically detects the active conversation, tracks mid-session model switches, and fetches missing model pricing dynamically.

## Agent Execution Instructions

Run the script via `run_command` with **NO CLI flags**:

```bash
python ~/.gemini/config/skills/token-metrics/token_metrics.py
```
*(Fallback if not found at above path: `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py`)*

> [!IMPORTANT]
> **Zero Pre-Reading & Zero Flags**:
> - **DO NOT read** `config.json`, `model_pricing.json`, or script source code before executing.
> - **DO NOT pass** `--conv`, `--models`, or any other flags. The script automatically targets the active session and renders the full breakdown.
> - Execute the command directly and present the resulting output card to the user.

## Error Handling
The Python script automatically handles missing models via OpenRouter/GitHub synchronization. Only if the command exits with an explicit error indicating no preference configured:
1. Prompt the user using `ask_question`:
   - **Question**: "How would you like to retrieve model pricing data when models are missing?"
   - **Options**:
     1. `(Recommended) Query OpenRouter API (Fast JSON endpoint for real-time rates)`
     2. `Auto-sync via GitHub repository (fetch latest verified model_pricing.json)`
2. Save their preference (`"openrouter"` or `"github"`) to `config.json` next to `token_metrics.py`.
3. Re-run `token_metrics.py` without flags.
