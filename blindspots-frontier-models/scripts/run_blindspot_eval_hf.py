#!/usr/bin/env python3
"""Run blind-spot prompts against an HF model loaded locally (Colab-compatible)."""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import time
from typing import Any

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer


def read_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        rows.append(json.loads(line))
    return rows


def write_jsonl(path: pathlib.Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_text(text: str) -> str:
    text = text.strip().strip('"').strip("'")
    text = re.sub(r"\s+", " ", text)
    return text


def is_correct(expected: str, predicted: str, check_type: str) -> bool:
    exp = normalize_text(expected)
    pred = normalize_text(predicted)
    if check_type == "exact":
        return pred == exp
    if check_type == "exact_ci":
        return pred.lower() == exp.lower()
    if check_type == "contains_ci":
        return exp.lower() in pred.lower()
    return pred == exp


def extract_completion(full_text: str, prompt_text: str) -> str:
    if full_text.startswith(prompt_text):
        return full_text[len(prompt_text):].strip()
    if "Assistant:" in full_text:
        return full_text.split("Assistant:", 1)[1].strip()
    return full_text.strip()


def parse_final_answer(raw_completion: str) -> str:
    """Keep only the first final answer segment and drop echoed dialogue turns."""

    text = raw_completion.strip()

    # Remove recurring dialogue sections if the model continues the chat template.
    for marker in ("\nUser:", "\nAssistant:", "\nSystem:", "User:", "Assistant:", "System:"):
        if marker in text:
            text = text.split(marker, 1)[0].strip()

    # Keep first non-empty line as the final concise answer.
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if lines:
        text = lines[0]

    return text if text else "<EMPTY_RESPONSE>"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default="ibm-granite/granite-4.0-1b-base")
    parser.add_argument("--prompts", default="data/blindspot_prompts.jsonl")
    parser.add_argument("--all-results", default="outputs/all_results.jsonl")
    parser.add_argument("--dataset-out", default="data/blindspots_dataset.jsonl")
    parser.add_argument("--summary", default="outputs/eval_summary.json")
    parser.add_argument("--max-new-tokens", type=int, default=96)
    parser.add_argument("--device", default="auto", choices=["auto", "cpu", "cuda"])
    parser.add_argument("--dataset-mode", default="all", choices=["all", "failures"])
    args = parser.parse_args()

    prompts = read_jsonl(pathlib.Path(args.prompts))

    if args.device == "cuda":
        device = "cuda"
    elif args.device == "cpu":
        device = "cpu"
    else:
        device = "cuda" if torch.cuda.is_available() else "cpu"

    tokenizer = AutoTokenizer.from_pretrained(args.model_id)
    if tokenizer.pad_token_id is None and tokenizer.eos_token_id is not None:
        tokenizer.pad_token = tokenizer.eos_token

    model = AutoModelForCausalLM.from_pretrained(args.model_id)
    model.to(device)
    model.eval()

    rows: list[dict[str, Any]] = []
    for p in prompts:
        prompt_text = (
            "You are a precise assistant. Return only the final answer in the requested format.\n"
            f"User: {p['input']}\n"
            "Assistant:"
        )
        t0 = time.time()
        inputs = tokenizer(prompt_text, return_tensors="pt").to(device)
        with torch.no_grad():
            out = model.generate(
                **inputs,
                do_sample=False,
                max_new_tokens=args.max_new_tokens,
                pad_token_id=tokenizer.eos_token_id,
            )

        text = tokenizer.decode(out[0], skip_special_tokens=True)
        raw_completion = extract_completion(text, prompt_text)
        completion = parse_final_answer(raw_completion)

        ok = is_correct(p["expected_output"], completion, p.get("check_type", "exact"))
        rows.append(
            {
                "id": p["id"],
                "category": p["category"],
                "input": p["input"],
                "expected_output": p["expected_output"],
                "model_output": completion,
                "raw_model_output": raw_completion,
                "check_type": p.get("check_type", "exact"),
                "is_correct": ok,
                "notes": "matched expected output" if ok else f"mismatch (expected: {p['expected_output']!r})",
                "model_id": args.model_id,
                "provider": "huggingface_transformers",
                "latency_ms": round((time.time() - t0) * 1000, 2),
                "timestamp_unix": int(time.time()),
            }
        )

    failures = [r for r in rows if not r["is_correct"]]

    write_jsonl(pathlib.Path(args.all_results), rows)

    if args.dataset_mode == "failures":
        dataset_rows = failures
    else:
        dataset_rows = rows

    dataset_rows_slim = [
        {
            "id": r["id"],
            "category": r["category"],
            "input": r["input"],
            "expected_output": r["expected_output"],
            "model_output": r["model_output"],
            "notes": r["notes"],
            "is_correct": r["is_correct"],
            "model_id": r["model_id"],
        }
        for r in dataset_rows
    ]
    write_jsonl(pathlib.Path(args.dataset_out), dataset_rows_slim)

    summary = {
        "status": "ok",
        "provider": "huggingface_transformers",
        "model_id": args.model_id,
        "prompt_count": len(rows),
        "dataset_row_count": len(dataset_rows_slim),
        "dataset_mode": args.dataset_mode,
        "failure_count": len(failures),
        "success_count": len(rows) - len(failures),
        "failure_rate": round(len(failures) / len(rows), 4) if rows else 0.0,
        "failure_ids": [r["id"] for r in failures],
        "success_ids": [r["id"] for r in rows if r["is_correct"]],
        "device": device,
        "max_new_tokens": args.max_new_tokens,
    }
    pathlib.Path(args.summary).write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
