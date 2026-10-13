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

The summary card automatically displays the model breakdown whenever multiple models are used.

## Command Line Options
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py` : Clean TUI summary card for active conversation (default)
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --latest` : Analyze latest active conversation
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --conv <id>` : Analyze a specific conversation by ID
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --list` : List recent conversations
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --json` : Output raw JSON metrics
- `python ~/.gemini/antigravity-cli/skills/token-metrics/token_metrics.py --set-source <openrouter|github>` : Set default fallback pricing source

---

## Configuration (`config.json`)

User preference is stored in `config.json` alongside `token_metrics.py`:
```json
{
  "pricing_source": "openrouter"
}
```

### Initial Setup When Run by an Agent:
If `config.json` is missing or does not have `"pricing_source"` defined, the agent **MUST** prompt the user using `ask_question`:
- **Question**: "How would you like to retrieve model pricing data when models are missing or pricing updates are needed?"
- **Options**:
  1. `(Recommended) Query OpenRouter API (Fast JSON endpoint for real-time rates)`
  2. `Auto-sync via GitHub repository (git pull / fetch latest verified model_pricing.json)`
  3. `Scrape official Google Vertex AI documentation (Agent web lookup)`

Save their selection (`"openrouter"`, `"github"`, or `"vertex"`) into `config.json`.

---

## Price Retrieval Workflows by Source

### Option 1: OpenRouter API Query (Default & Baked-in)
Queries OpenRouter without author restrictions (supporting Google, Anthropic, OpenAI, Meta, etc.):
```
https://openrouter.ai/api/v1/models?q=<MODEL_NAME>&output_modalities=text
```
From the returned JSON, rate fields are extracted and converted to per-1M tokens:
- `price_per_1m_input`: `pricing.prompt * 1_000_000`
- `price_per_1m_cached`: `pricing.input_cache_read * 1_000_000`
- `price_per_1m_output`: `pricing.completion * 1_000_000`
- Persisted directly to `model_pricing.json`.

### Option 2: Auto-sync via GitHub (`git pull` / fetch)
Fetch or pull the latest maintained `model_pricing.json` directly from the repository:
```bash
git -C <repo_dir> pull origin main
```
Or download the latest verified raw JSON from:
`https://raw.githubusercontent.com/GoudaCouda/antigravity-metrics/main/model_pricing.json`
and update local `model_pricing.json`.

### Option 3: Google Vertex AI Docs (Agent Web Lookup Only)
Only available when run via an AI agent session:
Endpoint:
`https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing?hl=en#googlemodels`
Parse the table for the requested model name, noting any introductory period dates.

---

## Model Pricing Schema

Model rates are stored in `model_pricing.json` (located alongside `token_metrics.py`):
```json
{
  "gemini-3.8-flash": {
    "model": "Google: Gemini 3.8 Flash",
    "rates": [0.75, 0.075, 3.75],
    "verified_at": "2026-10-13",
    "expires_at": null
  }
}
```
- `model`: Display name
- `rates`: `[uncached_input, cached_input, output]` in USD per 1M tokens
- `verified_at`: ISO date (`YYYY-MM-DD`) when verified against documentation
- `expires_at`: ISO date (`YYYY-MM-DD`) if introductory / promotional pricing has an end date (null otherwise).

---

## Error Handling Workflow
If `token_metrics.py` exits with an error (`[ERROR] Missing Model Pricing`):
1. Check `config.json`. If missing or invalid, trigger `ask_question`.
2. Query the chosen source to fetch and update `model_pricing.json`.
3. Sync `model_pricing.json` to both local and `~/.gemini/antigravity-cli/skills/token-metrics/model_pricing.json`.
4. Re-run `token_metrics.py` without extra flags.
