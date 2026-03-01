# Blind Spots of Frontier Models — Granite 4.0 1B Base

I tested the base model **`ibm-granite/granite-4.0-1b-base`**.

- Model card: https://huggingface.co/ibm-granite/granite-4.0-1b-base
- Size: ~1B params (within 0.6B–6B)
- HF created date: 2025-10-07 (within the last 6 months at run time)
- Modality: text-generation LLM

## What is in this Hugging Face dataset repo

- `README.md` (this file)
- `blindspots_dataset.jsonl` (main 10-row dataset)
- `blindspots_q1_q10_table.csv` (compact table view)
- `all_results.jsonl` (full run with parsed + raw outputs)
- `eval_summary.json` (aggregate metrics)
- `granite_blindspots_colab.ipynb` (Colab notebook)
- `model_selection_evidence.md` (recency/base-model evidence)

## How I loaded and evaluated the model

I loaded the model with `transformers` and ran a fixed 10-question blind-spot suite.

### Environment variables

```bash
export HF_TOKEN="<your_hf_token>"
```

### Repro command (host / Colab / GPU VM)

```bash
python scripts/run_blindspot_eval_hf.py \
  --model-id ibm-granite/granite-4.0-1b-base \
  --max-new-tokens 80 \
  --device auto \
  --dataset-mode all
```

### Minimal loading code

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

model_id = "ibm-granite/granite-4.0-1b-base"
tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)
```

## Parsing note (important)

I corrected output parsing so that only the final answer span is compared, not echoed follow-up dialogue (`User:` / `Assistant:` turns).

- `model_output` stores the cleaned answer.
- `raw_model_output` is preserved in `all_results.jsonl` for audit.
- `notes` and `is_correct` are aligned to the cleaned answer.

## Results summary

- Total datapoints: 10
- Correct: 2 (`Q3`, `Q6`)
- Mistakes: 8

Main blind spots:
1. numerical reasoning drift (Van’t Hoff, Bayes PPV, log-odds, Hardy-Weinberg),
2. symbolic/game-theory mistake on Nim xor state,
3. verbose explanation instead of constrained concise format.

## Dataset schema

Rows in `blindspots_dataset.jsonl` contain:
- `id`
- `category`
- `input`
- `expected_output`
- `model_output`
- `notes`
- `is_correct`
- `model_id`

## Fine-tuning plan (concise)

If I fine-tuned this model, I would target concise-answer + stop-control behavior.

- **Data:** short quantitative reasoning, exact-format tasks, anti-overgeneration pairs.
- **Assembly:** mine observed failures, add paraphrase/perturbation variants, then add verified domain data (math, biostat, chemistry, CGT).
- **Scale:**
  - pilot: ~5k–10k curated SFT examples,
  - stronger run: ~30k–60k mixed SFT + preference pairs.

Goal: preserve reasoning while improving final-answer termination and exact-format compliance.
