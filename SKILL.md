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

## Model Pricing Configuration & Web Search Fallback
Model rates are stored in `model_pricing.json` (located in the skill directory alongside `token_metrics.py`).
Rates are configured per 1M tokens as an array of three floats: `[uncached_input, cached_input, output]`.

### Agent Instructions for Missing Models:
If the agent is calculating or inspecting metrics and encounters a model that is **not** present in `model_pricing.json`:
1. Use web search tools to look up the official pricing for that model, prioritizing:
   - Official Gemini API pricing documentation (`ai.google.dev/pricing` or `cloud.google.com/vertex-ai/pricing`).
   - Official Anthropic pricing documentation (`anthropic.com/pricing`).
   - Official OpenAI pricing documentation (`openai.com/api/pricing`).
2. Extract the rates per 1M tokens for:
   - Uncached input prompts ($/1M)
   - Cached prompt reads ($/1M)
   - Output generation ($/1M)
3. Persist the new model entry directly into `model_pricing.json` (both in the local repo and `~/.gemini/antigravity-cli/skills/token-metrics/model_pricing.json`) so subsequent runs immediately use the accurate rate.
4. Execute `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py` to display the updated breakdown.

