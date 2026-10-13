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
Each entry follows the Google Vertex AI Generative AI schema options:
- `model`: Model name (e.g., `Gemini 3.8 Flash`)
- `type`: Supported modalities (e.g., `Text, Image, Video, Audio`)
- `region`: Cloud region availability (e.g., `Global` or `Non-global`)
- `price_per_1m_input_lte_200k`: Rate per 1M tokens for prompts <= 200K
- `price_per_1m_input_gt_200k`: Rate per 1M tokens for prompts > 200K
- `price_per_1m_cached_input_lte_200k`: Rate per 1M cached prompt tokens <= 200K
- `price_per_1m_cached_input_gt_200k`: Rate per 1M cached prompt tokens > 200K
- `price_per_1m_output_lte_200k`: Rate per 1M output tokens <= 200K
- `price_per_1m_output_gt_200k`: Rate per 1M output tokens > 200K
- `rates`: standard `[uncached_input, cached_input, output]` summary
- `verified_at`: ISO date (`YYYY-MM-DD`) when verified against documentation
- `expires_at`: ISO date (`YYYY-MM-DD`) if introductory / promotional pricing has an end date

### Primary Endpoint for Google Models:
When looking up or verifying pricing for Gemini and Google models, the agent **MUST** first check this official endpoint:
`https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing?hl=en#googlemodels`

### Introductory Pricing & Expiration Mechanic:
If the model listing on the pricing page includes an introductory period or expiration (for example:
`Gemini 3.8 Flash* through December 31, 2026`), the agent **MUST**:
1. Store the promotional rates as current effective rates.
2. Record the expiration date in `expires_at` (e.g., `"2026-12-31"`).
3. If `token_metrics.py` encounters an expired model (`[ERROR] Expired Model Pricing`), the agent must re-check the pricing endpoint, update the standard post-expiration rates, and regenerate.

### Workflow When Encountering Missing Models:
If the command fails with `[ERROR] Missing Model Pricing: Pricing not found for model ...`:
1. Do **NOT** invent or guess the price.
2. Look up the official pricing:
   - For Google / Gemini models: Prioritize `https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing?hl=en#googlemodels`.
   - For Anthropic models: Prioritize `anthropic.com/pricing`.
   - For OpenAI models: Prioritize `openai.com/api/pricing`.
3. Extract the exact official rates per 1M tokens (tier <= 200K, cached reads, outputs, and any expiration).
4. Add the entry to `model_pricing.json` (both locally and in `~/.gemini/antigravity-cli/skills/token-metrics/model_pricing.json`).
5. Re-run `token_metrics.py` to regenerate the accurate metrics.

### Verifying Updated Pricing & Price Cuts:
If the user mentions or asks to verify updated pricing/price cuts, check the official vendor pricing page, update the rates and `expires_at` in `model_pricing.json` along with the updated `verified_at` date, and regenerate the metrics.




