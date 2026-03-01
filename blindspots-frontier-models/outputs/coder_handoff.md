## Summary
- Refactored `data/blindspot_prompts.jsonl` to exactly 10 rows (`Q1`..`Q10`) with required schema: `id`, `category`, `input`, `expected_output`, `check_type`.
- Added required topical coverage in the prompt set: **Van't Hoff**, **Biostatistics**, and **Nim/CGT**.
- Updated dataset card (`data/README.md`) to:
  - fix the model to **`liquid/lfm-2.5-1.2b-thinking:free`**,
  - include OpenRouter loading/call code,
  - provide a concise first-person master-level fine-tuning plan,
  - document HF-ready mapping (`Question`, `Expected_Output`, `Actual_Output`).
- Refreshed model evidence files to **LiquidAI LFM2.5-1.2B-Thinking** with recency and size evidence:
  - created_at `2026-01-20T13:55:42Z` (within 6 months),
  - parameter estimate `1.2B`.
- Aligned script defaults with owner-requested model:
  - `scripts/run_blindspot_eval.py` default model -> `liquid/lfm-2.5-1.2b-thinking:free`
  - `scripts/select_model.py` default model -> `LiquidAI/LFM2.5-1.2B-Thinking`

## Files changed
- `data/blindspot_prompts.jsonl`
- `data/README.md`
- `docs/model_selection_evidence.md`
- `docs/model_selection_evidence.json`
- `scripts/run_blindspot_eval.py`
- `scripts/select_model.py`
- `outputs/coder_handoff.md`

## Remaining steps
- Optional: run `python3 scripts/run_blindspot_eval.py` with `OPENROUTER_API_KEY` set to generate fresh `Actual_Output` values for the new Q1..Q10 suite.
- Optional: run `python3 scripts/validate_dataset.py --dataset data/blindspots_dataset.jsonl` after generation.
