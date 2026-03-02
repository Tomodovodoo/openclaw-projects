# HF minimal cleanup — final scrutiny (2026-03-02)

**Overall:** **FAIL** (local git working tree not clean)

Dataset under review:
- Local: `blindspots-frontier-models/data/blindspots_dataset.jsonl`
- HF: https://huggingface.co/datasets/Tomodovodoo/blindspots-frontier-models-granite-4-0-1b-base

## Checklist

| # | Check | Result | Evidence |
|---:|---|---|---|
| 1 | Local `blindspots_dataset.jsonl` has **10 rows** | PASS | `wc -l data/blindspots_dataset.jsonl` → `10` |
| 2 | `expected_output` / `notes` alignment sane (spot-check all rows) | PASS | Programmatic scan: all incorrect rows’ `notes` include the exact `expected_output`, and correct rows have “matched expected output”. See per-row excerpt below. |
| 3 | `model_id` is **`ibm-granite/granite-4.0-1b-base`** in all dataset rows | PASS | `Counter({'ibm-granite/granite-4.0-1b-base': 10})` |
| 4 | HF dataset repo is minimal: only `README.md` + `blindspots_dataset.jsonl` (+ `.gitattributes`) | PASS | HF API `siblings`: `['.gitattributes', 'README.md', 'blindspots_dataset.jsonl']` |
| 5 | HF splits endpoint reports single split `train` | PASS | `{'splits': [{'config': 'default', 'split': 'train'}], 'pending': [], 'failed': []}` |
| 6 | Git branch is `main` tracking `origin/main` and **clean** | **FAIL** | `git branch -vv` shows `* main ... [origin/main]`, but `git status --porcelain` is non-empty (details below). |

## Evidence details

### 1) Local row count
```bash
cd /home/server/openclaw-projects/blindspots-frontier-models
wc -l data/blindspots_dataset.jsonl
# 10 data/blindspots_dataset.jsonl
```

### 2) `expected_output` / `notes` alignment (spot-check all 10 rows)
Per-row excerpt (id → expected/model/is_correct/notes):

```
Q1  expected=0.63   model=0.30   is_correct=False  notes="mismatch (expected: '0.63')"
Q2  expected=7.34   model=0.03   is_correct=False  notes="mismatch (expected: '7.34')"
Q3  expected=0.40   model=0.40   is_correct=True   notes="matched expected output"
Q4  expected=0.27   model=0.95   is_correct=False  notes="mismatch (expected: '0.27')"
Q5  expected=0.764  model=0.67   is_correct=False  notes="mismatch (expected: '0.764')"
Q6  expected=remove 1  model=remove 1  is_correct=True  notes="matched expected output"
Q7  expected=(1,4,5)  model=(3,4,5)  is_correct=False  notes="mismatch (expected: '(1,4,5)')"
Q8  expected=Any move makes xor nonzero, so the opponent can restore zero.
    is_correct=False  notes includes that exact expected sentence.
Q9  expected=1.386  model=0.693  is_correct=False  notes="mismatch (expected: '1.386')"
Q10 expected=0.32   model=0.80   is_correct=False  notes="mismatch (expected: '0.32')"
```

### 3) `model_id` consistency (local)
```text
Counter({'ibm-granite/granite-4.0-1b-base': 10})
```

(Also verified remotely)
```bash
curl -sL https://huggingface.co/datasets/Tomodovodoo/blindspots-frontier-models-granite-4-0-1b-base/resolve/main/blindspots_dataset.jsonl \
 | grep -o '"model_id": "[^\"]\+"' | sort | uniq -c
# 10 "model_id": "ibm-granite/granite-4.0-1b-base"
```

### 4) HF repo contents minimal (remote)
Hugging Face Hub API endpoint:
- https://huggingface.co/api/datasets/Tomodovodoo/blindspots-frontier-models-granite-4-0-1b-base

Extracted:
```text
siblings: ['.gitattributes', 'README.md', 'blindspots_dataset.jsonl']
lastModified: 2026-03-02T00:39:15.000Z
```

### 5) HF splits endpoint
Endpoint:
- https://datasets-server.huggingface.co/splits?dataset=Tomodovodoo/blindspots-frontier-models-granite-4-0-1b-base

Response excerpt:
```json
{
  "splits": [
    {"config": "default", "split": "train"}
  ],
  "pending": [],
  "failed": []
}
```

### 6) Git status (local) — **not clean**
Repo top-level is `/home/server/openclaw-projects`.

```bash
cd /home/server/openclaw-projects
git branch -vv
# * main 1626fe2 [origin/main] ...

git status --porcelain=v1
# M  blindspots-frontier-models/data/README.md
# ?? blindspots-frontier-models/outputs/double_scrutiny_post_trim.json
# ?? blindspots-frontier-models/outputs/scrutinizer_hf_minimal.md
```

## Required fix to reach PASS
- Commit and push (or revert/remove) the above local changes so `git status --porcelain` is empty on `main` tracking `origin/main`.
