# HF minimal cleanup — final re-check (2026-03-02)

**Overall:** **PASS**

Dataset under review:
- HF: https://huggingface.co/datasets/Tomodovodoo/blindspots-frontier-models-granite-4-0-1b-base

## Checklist (must all be true)

| # | Requirement | Result | Evidence |
|---:|---|---|---|
| 1 | Local git is on `main` tracking `origin/main` | PASS | `git rev-parse --abbrev-ref HEAD` → `main`; upstream `origin/main` |
| 2 | Local git working tree is **clean** (incl. `git clean -nd` empty) | PASS | `git status --porcelain` empty; `git clean -nd` empty |
| 3 | Remote branches `main` and `blindspots-frontier-models-ibm-granite` point to the **same commit** | PASS | both → `6947253e4292ad50cdf72393f33500dd4682d879` |
| 4 | HF dataset repo contains only `README.md` + `blindspots_dataset.jsonl` (+ `.gitattributes`) | PASS | HF Hub API `siblings` = `['.gitattributes','README.md','blindspots_dataset.jsonl']` |
| 5 | HF **size endpoint** shows `num_rows=10` for `train` split | PASS | datasets-server `/size` → `train.num_rows: 10` |

## Evidence

### A) Git state (local)
Repo: `/home/server/openclaw-projects/blindspots-frontier-models`

```bash
git rev-parse --abbrev-ref HEAD
# main

git rev-parse --abbrev-ref --symbolic-full-name @{u}
# origin/main

git rev-parse HEAD
# 6947253e4292ad50cdf72393f33500dd4682d879

git status --porcelain=v1
# (no output)

git clean -nd
# (no output)
```

### B) Remote branch heads are identical
```bash
git ls-remote origin refs/heads/main refs/heads/blindspots-frontier-models-ibm-granite
# 6947253e4292ad50cdf72393f33500dd4682d879  refs/heads/blindspots-frontier-models-ibm-granite
# 6947253e4292ad50cdf72393f33500dd4682d879  refs/heads/main
```

### C) HF repo contents (Hub API)
Endpoint:
- https://huggingface.co/api/datasets/Tomodovodoo/blindspots-frontier-models-granite-4-0-1b-base

Extracted `siblings`:
```text
['.gitattributes', 'README.md', 'blindspots_dataset.jsonl']
```

### D) HF size endpoint (`num_rows=10` on `train`)
Endpoint:
- https://datasets-server.huggingface.co/size?dataset=Tomodovodoo/blindspots-frontier-models-granite-4-0-1b-base&config=default&split=train

Extracted split record:
```json
{
  "dataset": "Tomodovodoo/blindspots-frontier-models-granite-4-0-1b-base",
  "config": "default",
  "split": "train",
  "num_rows": 10,
  "num_columns": 8,
  "num_bytes_parquet_files": 6366,
  "num_bytes_memory": 2862,
  "estimated_num_rows": null
}
```
