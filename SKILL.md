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

> [!IMPORTANT]
> **Default Execution**: Always run `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py` directly without `--models` or other extra flags. The summary card automatically displays the model breakdown whenever multiple models are used. Do **NOT** run `--models`.

## Command Line Options
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py` : Clean TUI summary card for active conversation (default)
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --latest` : Analyze latest active conversation
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --conv <id>` : Analyze a specific conversation by ID
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --list` : List recent conversations
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --json` : Output raw JSON metrics

---

## Initial Setup & User Pricing Source Preference

Whenever token metrics is run for the first time in an environment (or when no pricing source preference has been configured yet), the agent **MUST** prompt the user using the `ask_question` tool:

- **Question**: "How would you like to retrieve model pricing data when models are missing or pricing updates are needed?"
- **Options**:
  1. `(Recommended) Query OpenRouter API (Fast JSON endpoint for real-time rates)`
  2. `Auto-sync via GitHub repository (git pull / fetch latest verified model_pricing.json)`
  3. `Scrape official Google Vertex AI documentation (Authoritative, but slow to query)`

Once selected, save the choice in a lightweight configuration file (`pricing_config.json`) alongside `token_metrics.py`.

---

## Price Retrieval Workflows by Source

### Option 1: OpenRouter API Query (Bake directly into script or query)
`token_metrics.py` now bakes this fetcher directly in. It queries OpenRouter without author restrictions (supporting models from Google, Anthropic, OpenAI, Meta, etc.):
```
https://openrouter.ai/api/v1/models?q=<MODEL_NAME>&output_modalities=text
```
For example, for `Gemini 3.8 Flash`:
`https://openrouter.ai/api/v1/models?q=Gemini%203.8%20Flash&output_modalities=text`

From the returned JSON, only the necessary rate fields are extracted and converted to per-1M tokens:
- `price_per_1m_input`: `pricing.prompt * 1_000_000`
- `price_per_1m_cached`: `pricing.input_cache_read * 1_000_000`
- `price_per_1m_output`: `pricing.completion * 1_000_000`
- Persisted automatically to `model_pricing.json`.

### Option 2: Auto-sync via GitHub (`git pull` / fetch)
Fetch or pull the latest maintained `model_pricing.json` directly from the repository:
```bash
git -C <repo_dir> pull origin main
```
Or download the latest verified raw JSON from:
`https://raw.githubusercontent.com/GoudaCouda/antigravity-metrics/main/model_pricing.json`
and update local `model_pricing.json`.

### Option 3: Google Vertex AI Docs (Official Documentation)
Endpoint:
`https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing?hl=en#googlemodels`
Parse the table for the requested model name, noting any introductory period dates.

---

## Model Pricing Schema & Expiration Mechanic

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
- `expires_at`: ISO date (`YYYY-MM-DD`) if introductory / promotional pricing has an end date (e.g., `Gemini 3.8 Flash* through December 31, 2026` -> `"2026-12-31"`).

---

## Workflow When Encountering Missing or Expired Models
If `token_metrics.py` fails with `[ERROR] Missing Model Pricing` (exit code 2) or `[ERROR] Expired Model Pricing` (exit code 3):
1. Do **NOT** invent or guess the price.
2. Read `pricing_config.json` to check the user's preferred source (or ask with `ask_question` if not yet configured).
3. Query the selected source:
   - If OpenRouter: query endpoint, extract prompt/cache/completion per-1M values, and write to `model_pricing.json`.
   - If GitHub sync: run `git pull` or fetch `raw.githubusercontent.com/.../model_pricing.json`.
   - If Vertex docs: read the official Vertex pricing URL.
4. Save the entry to `model_pricing.json` (both in the repo and in `~/.gemini/antigravity-cli/skills/token-metrics/model_pricing.json`).
5. Re-run `token_metrics.py` without extra flags.
