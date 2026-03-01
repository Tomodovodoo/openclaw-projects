#!/usr/bin/env python3
"""Attempt to publish the dataset to Hugging Face Hub (public dataset repo)."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import traceback
from datetime import datetime, timezone

from huggingface_hub import HfApi


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset-file", default="data/blindspots_dataset.jsonl")
    parser.add_argument("--dataset-readme", default="data/README.md")
    parser.add_argument("--repo-id", default=None, help="Dataset repo id, e.g. username/blindspots-frontier-models")
    args = parser.parse_args()

    token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_TOKEN")
    api = HfApi(token=token)
    report: dict = {
        "attempted_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_file": args.dataset_file,
        "dataset_readme": args.dataset_readme,
        "repo_id": args.repo_id,
    }

    try:
        me = api.whoami()
        username = me.get("name") or me.get("fullname") or me.get("id")
        if not username:
            raise RuntimeError(f"Could not determine username from whoami(): {me}")

        repo_id = args.repo_id or f"{username}/blindspots-frontier-models-granite-4-0-1b-base"
        report["resolved_repo_id"] = repo_id

        api.create_repo(repo_id=repo_id, repo_type="dataset", private=False, exist_ok=True)

        api.upload_file(
            path_or_fileobj=args.dataset_file,
            path_in_repo="blindspots_dataset.jsonl",
            repo_id=repo_id,
            repo_type="dataset",
            commit_message="Add blind spots dataset JSONL",
        )

        api.upload_file(
            path_or_fileobj=args.dataset_readme,
            path_in_repo="README.md",
            repo_id=repo_id,
            repo_type="dataset",
            commit_message="Add dataset card",
        )

        report["status"] = "success"
        report["url"] = f"https://huggingface.co/datasets/{repo_id}"
        pathlib.Path("outputs/hf_publish_attempt.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 0

    except Exception as exc:  # noqa: BLE001
        report["status"] = "failed"
        report["error_type"] = type(exc).__name__
        report["error"] = str(exc)
        report["traceback"] = traceback.format_exc()
        pathlib.Path("outputs/hf_publish_attempt.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(report, indent=2))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
