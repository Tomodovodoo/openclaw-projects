---
pretty_name: Granite 4.0 1B Base Blind Spots
task_categories:
- text-generation
language:
- en
size_categories:
- n<1K
---

# Blind Spots of Frontier Models (IBM Granite 4.0 1B Base)

**Model tested:** `ibm-granite/granite-4.0-1b-base`  
Model card: https://huggingface.co/ibm-granite/granite-4.0-1b-base

This dataset contains **10 evaluation rows** with:
- `input`
- `expected_output`
- `model_output`
- `notes`
- `is_correct`

I loaded the model with `transformers` and evaluated it using strict concise-answer prompts.

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
model_id = "ibm-granite/granite-4.0-1b-base"
tok = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)
```

### What blind spots showed up
- Numerical reasoning drift on chemistry/biostat/pop-gen prompts.
- Game-theory error on Nim xor-state.
- Sometimes verbose/over-continued generation if parsing is not strict.

### Fine-tuning direction (concise)
The expectation that a 1B base model reliably solves these questions is often too high. I would first train capability calibration: the model should estimate whether it can answer correctly, including safe abstention for overly complex prompts. Then I’d progressively train solution quality.

I would build a synthetic+curated science reasoning dataset (chemistry, biostatistics, game theory), with labels for **correct answer**, **abstain**, and **format compliance**. A practical first range is **5k–20k samples**.

### Links
- HF dataset: https://huggingface.co/datasets/Tomodovodoo/blindspots-frontier-models-granite-4-0-1b-base
- GitHub repo path: https://github.com/Tomodovodoo/openclaw-projects/tree/main/blindspots-frontier-models
