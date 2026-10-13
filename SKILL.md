---
name: token-metrics
description: Analyze conversation token consumption, prompt cache hit rate, and estimated model pricing with an ANSI TUI breakdown.
---

# Token and Cost Metrics Skill

Inspects real-time token consumption, prompt cache efficiency, and model pricing estimates for Antigravity conversations. Automatically tracks and breaks down metrics by specific model when models are switched during a session.

## CLI Execution Rules
Always run the command cleanly without extra flags:
```bash
python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py
```
> [!IMPORTANT]
> **DO NOT** pass `--models` when running the command. The default view already provides the complete summary card and cleanly embeds the model breakdown when multiple models are used.

## Configuration & Price Lookup Source Preference
The skill maintains a user preference in `config.json` (alongside `token_metrics.py`).
If `config.json` does not exist or has not selected a preferred lookup source, the agent should use `ask_question` on first setup to ask how the user prefers missing or expired model prices to be resolved:

1. **OpenRouter API (Fast JSON - Recommended)**
   - Query endpoint:
     `https://openrouter.ai/api/v1/models?model_authors=google&q=<model_name>&output_modalities=text&providers=google-vertex`
   - Maps `pricing.prompt` * 1M, `pricing.input_cache_read` * 1M, `pricing.completion` * 1M directly into our clean schema.
2. **Auto-sync via Git / GitHub Repository**
   - Fetches latest curated `model_pricing.json` directly from `https://raw.githubusercontent.com/GoudaCouda/antigravity-metrics/main/model_pricing.json` (or runs `git pull`).
3. **Google Vertex AI Documentation (Authoritative Web Scraping)**
   - Prioritizes `https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing?hl=en#googlemodels`.

Save the chosen preference into `config.json`:
```json
{
  "pricing_source": "openrouter" // or "github", "vertex"
}
```

## Model Pricing Schema & Expiration Mechanic
Model rates are stored strictly in `model_pricing.json` (located alongside `token_metrics.py`).
Each entry follows the clean Vertex AI schema:
- `model`: Model name (e.g., `Gemini 3.8 Flash`)
- `type`: Modalities (e.g., `Text, Image, Video, Audio`)
- `region`: Cloud region (e.g., `Global`)
- `price_per_1m_input_lte_200k`: Rate per 1M tokens for prompts <= 200K
- `price_per_1m_input_gt_200k`: Rate per 1M tokens for prompts > 200K
- `price_per_1m_cached_input_lte_200k`: Rate per 1M cached prompt tokens <= 200K
- `price_per_1m_cached_input_gt_200k`: Rate per 1M cached prompt tokens > 200K
- `price_per_1m_output_lte_200k`: Rate per 1M output tokens <= 200K
- `price_per_1m_output_gt_200k`: Rate per 1M output tokens > 200K
- `rates`: `[uncached_input, cached_input, output]`
- `verified_at`: ISO date (`YYYY-MM-DD`)
- `expires_at`: ISO date (`YYYY-MM-DD`) if introductory / promotional pricing has an end date

### Handling Missing or Expired Models:
When `token_metrics.py` fails with `[ERROR] Missing Model Pricing` or `[ERROR] Expired Model Pricing`:
1. Check `config.json` for preferred `pricing_source`:
   - If `openrouter`:
     Query `https://openrouter.ai/api/v1/models?model_authors=google&q=<model_name>&output_modalities=text&providers=google-vertex` (or remove providers filter if non-Google).
     Extract prompt, input_cache_read, completion rates per 1M tokens.
   - If `github`:
     Fetch updated `model_pricing.json` from the upstream GitHub repo.
   - If `vertex`:
     Inspect `https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing?hl=en#googlemodels`.
2. Save the extracted fields into `model_pricing.json` (both locally and in `~/.gemini/antigravity-cli/skills/token-metrics/model_pricing.json`).
3. Re-run `token_metrics.py` without extra flags.





