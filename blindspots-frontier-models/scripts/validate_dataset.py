#!/usr/bin/env python3
"""Validate blind-spot dataset structure and minimum size."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys


REQUIRED_FIELDS = ["id", "category", "input", "expected_output", "model_output", "notes"]


def read_jsonl(path: pathlib.Path) -> list[dict]:
    rows = []
    for ln, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON on line {ln}: {exc}") from exc
    return rows


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", default="data/blindspots_dataset.jsonl")
    parser.add_argument("--min-records", type=int, default=10)
    parser.add_argument("--min-categories", type=int, default=8)
    args = parser.parse_args()

    dataset_path = pathlib.Path(args.dataset)
    if not dataset_path.exists():
        print(f"ERROR: dataset not found: {dataset_path}")
        return 1

    rows = read_jsonl(dataset_path)
    errors: list[str] = []

    if len(rows) < args.min_records:
        errors.append(f"record count {len(rows)} < required minimum {args.min_records}")

    categories = {row.get("category") for row in rows}
    if len(categories) < args.min_categories:
        errors.append(f"category diversity {len(categories)} < required minimum {args.min_categories}")

    for idx, row in enumerate(rows, start=1):
        missing = [f for f in REQUIRED_FIELDS if f not in row or row[f] in (None, "")]
        if missing:
            errors.append(f"row {idx} missing required fields: {missing}")

    report = {
        "dataset": str(dataset_path),
        "record_count": len(rows),
        "unique_categories": len(categories),
        "required_fields": REQUIRED_FIELDS,
        "min_records": args.min_records,
        "min_categories": args.min_categories,
        "status": "ok" if not errors else "failed",
        "errors": errors,
    }

    pathlib.Path("outputs/validation_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))

    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
