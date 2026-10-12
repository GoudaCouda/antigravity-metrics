---
name: token-metrics
description: Analyze conversation token consumption, prompt cache hit rate, and estimated model pricing with an ANSI TUI breakdown.
---

# Token and Cost Metrics Skill

Inspects real-time token consumption, prompt cache efficiency, and model pricing estimates for Antigravity conversations. Automatically tracks and breaks down metrics by specific model when models are switched during a session.

## CLI Usage
Run the standalone script from any working directory:
```bash
python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py
```

## Options
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py` : Clean TUI summary card for active conversation
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --models` : Detailed per-model metrics breakdown table
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --latest` : Analyze latest active conversation
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --conv <id>` : Analyze a specific conversation by ID
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --list` : List recent conversations
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --json` : Output raw JSON metrics (including model breakdown)
