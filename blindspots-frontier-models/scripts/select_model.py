#!/usr/bin/env python3
"""Select and document model evidence for blind-spot evaluation."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import sys
import urllib.request


HF_API_MODEL = "https://huggingface.co/api/models/{model_id}"
HF_RAW_README = "https://huggingface.co/{model_id}/raw/main/README.md"


def fetch_json(url: str) -> dict:
    with urllib.request.urlopen(url) as response:
        return json.load(response)


def fetch_text(url: str) -> str:
    with urllib.request.urlopen(url) as response:
        return response.read().decode("utf-8", errors="replace")


def extract_release_date(readme: str) -> str | None:
    for line in readme.splitlines():
        if "Release Date" in line:
            # Example: - **Release Date**: October 28, 2025
            match = re.search(r"Release Date\*\*:\s*(.+)", line)
            if match:
                return match.group(1).strip()
    return None


def extract_param_count_b(model_id: str, readme: str) -> float | None:
    # Prefer explicit value in model id (e.g. 1b)
    id_match = re.search(r"([0-9]+(?:\.[0-9]+)?)b", model_id.lower())
    if id_match:
        return float(id_match.group(1))

    # Fallback to README mentions like "1B Dense"
    card_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*[Bb]", readme)
    if card_match:
        return float(card_match.group(1))

    return None


def looks_like_base_or_general_model(model_id: str, readme: str) -> bool:
    """Heuristic for base/general models when exact labels vary.

    Cloud catalogs often expose a mixed naming scheme. We treat models as
    base/general when they are not clearly instruction/chat fine-tunes.
    """

    lower_id = model_id.lower()
    lower_card = readme.lower()

    if "base" in lower_id or "base model" in lower_card:
        return True

    tune_markers = ("instruct", "chat", "-it", " it ", "finetune", "fine-tune", "sft", "dpo", "rlhf")
    if any(marker in lower_id for marker in tune_markers):
        return False

    card_tune_markers = (
        "instruction-tuned",
        "instruction tuned",
        "chat model",
        "assistant model",
        "finetuned",
        "fine-tuned",
    )
    if any(marker in lower_card for marker in card_tune_markers):
        return False

    return True


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="ibm-granite/granite-4.0-1b-base")
    parser.add_argument("--out-json", default="docs/model_selection_evidence.json")
    parser.add_argument("--out-md", default="docs/model_selection_evidence.md")
    args = parser.parse_args()

    model_id = args.model_id
    metadata = fetch_json(HF_API_MODEL.format(model_id=model_id))
    readme = fetch_text(HF_RAW_README.format(model_id=model_id))

    created_at = metadata.get("createdAt")
    last_modified = metadata.get("lastModified")
    created_dt = dt.datetime.fromisoformat(created_at.replace("Z", "+00:00")) if created_at else None
    now = dt.datetime.now(dt.timezone.utc)

    recent_cutoff = now - dt.timedelta(days=183)
    within_6_months = bool(created_dt and created_dt >= recent_cutoff)

    param_b = extract_param_count_b(model_id=model_id, readme=readme)
    in_param_range = bool(param_b is not None and 0.6 <= param_b <= 6.0)

    is_base_or_general = looks_like_base_or_general_model(model_id=model_id, readme=readme)
    release_date = extract_release_date(readme)

    evidence = {
        "model_id": model_id,
        "model_url": f"https://huggingface.co/{model_id}",
        "created_at": created_at,
        "last_modified": last_modified,
        "release_date_from_card": release_date,
        "pipeline_tag": metadata.get("pipeline_tag"),
        "license_tags": [t for t in metadata.get("tags", []) if str(t).startswith("license:")],
        "parameter_billions_estimate": param_b,
        "checks": {
            "is_recent_within_6_months_by_created_at": within_6_months,
            "in_param_range_0_6_to_6_billion": in_param_range,
            "looks_like_base_or_general_model": is_base_or_general,
        },
        "recent_cutoff_utc": recent_cutoff.isoformat(),
        "evaluated_at_utc": now.isoformat(),
    }

    out_json = pathlib.Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(evidence, indent=2) + "\n", encoding="utf-8")

    out_md = pathlib.Path(args.out_md)
    out_md.parent.mkdir(parents=True, exist_ok=True)
    md = f"""# Model Selection Evidence

- **Model**: `{model_id}`
- **URL**: https://huggingface.co/{model_id}
- **Created at (HF API)**: {created_at}
- **Last modified (HF API)**: {last_modified}
- **Release date (model card)**: {release_date}
- **Estimated parameter size**: {param_b}B
- **Pipeline tag**: {metadata.get("pipeline_tag")}
- **License tags**: {', '.join(evidence['license_tags']) if evidence['license_tags'] else 'N/A'}

## Eligibility Checks
- Recent (<= ~6 months by `createdAt`): **{within_6_months}**
- Parameter range 0.6B–6B: **{in_param_range}**
- Base/general intent (name/card heuristics): **{is_base_or_general}**

## Snippet from model card

> {next((line.strip() for line in readme.splitlines() if 'Release Date' in line), 'Release Date line not found.')}

> {next((line.strip() for line in readme.splitlines() if 'text generation' in line.lower() or 'general' in line.lower()), 'General-purpose line not found.')}
"""
    out_md.write_text(md, encoding="utf-8")

    print(json.dumps(evidence, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
