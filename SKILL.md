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

## Model Pricing Configuration & Web Lookup Workflow
Model rates are stored strictly in `model_pricing.json` (located alongside `token_metrics.py`).
Rates are configured per 1M tokens as an array of three floats: `[uncached_input, cached_input, output]`.

### Workflow When Encountering Missing Models:
If the command fails with `[ERROR] Missing Model Pricing: Pricing not found for model ...`:
1. Do **NOT** invent or guess the price.
2. Use web search tools to locate official pricing documentation for that specific model:
   - For Google / Gemini models: Prioritize `ai.google.dev/pricing` or Google Vertex AI pricing docs.
   - For Anthropic models: Prioritize `anthropic.com/pricing`.
   - For OpenAI models: Prioritize `openai.com/api/pricing`.
3. Extract the exact official rates per 1M tokens:
   - Uncached prompt / input tokens ($/1M)
   - Cached prompt reads ($/1M)
   - Output / generation tokens ($/1M)
4. Add the entry to `model_pricing.json` (in both `~/.gemini/antigravity-cli/skills/token-metrics/model_pricing.json` and the local repo if working in it).
5. Re-run `token_metrics.py` to regenerate the accurate metrics.


