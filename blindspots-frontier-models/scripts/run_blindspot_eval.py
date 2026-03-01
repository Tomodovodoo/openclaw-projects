#!/usr/bin/env python3
"""Run blind-spot probing prompts against an OpenRouter model and build a failure dataset."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import pathlib
import re
import time
import urllib.error
import urllib.request
from typing import Any

OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
RETRIABLE_HTTP_STATUS = {408, 409, 425, 429, 500, 502, 503, 504}


def read_jsonl(path: pathlib.Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        records.append(json.loads(line))
    return records


def write_jsonl(path: pathlib.Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_text(text: str) -> str:
    text = text.strip()
    text = text.strip('"').strip("'")
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
    if check_type == "numeric":
        m = re.search(r"-?\d+(?:\.\d+)?", pred)
        return bool(m and m.group(0) == exp)

    # Default: exact
    return pred == exp


def redact_sensitive(text: str, api_key: str | None) -> str:
    value = text
    if api_key:
        value = value.replace(api_key, "<OPENROUTER_API_KEY_REDACTED>")
    value = re.sub(r"sk-or-v1-[A-Za-z0-9_-]+", "<OPENROUTER_API_KEY_REDACTED>", value)
    return value


def _extract_text_from_content(content: Any) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content

    if isinstance(content, list):
        chunks: list[str] = []
        for part in content:
            if isinstance(part, str):
                chunks.append(part)
                continue
            if not isinstance(part, dict):
                continue

            # OpenAI/OpenRouter-style text parts
            text = part.get("text")
            if isinstance(text, str):
                chunks.append(text)
                continue

            # Fallback fields some providers emit
            for key in ("content", "value"):
                maybe = part.get(key)
                if isinstance(maybe, str):
                    chunks.append(maybe)
                    break
        return "".join(chunks)

    if isinstance(content, dict):
        for key in ("text", "content", "value"):
            maybe = content.get(key)
            if isinstance(maybe, str):
                return maybe
            if isinstance(maybe, list):
                combined = _extract_text_from_content(maybe)
                if combined:
                    return combined

    return ""


def extract_completion_text(payload: dict[str, Any]) -> str:
    choices = payload.get("choices")
    if isinstance(choices, list) and choices:
        first = choices[0]
        if isinstance(first, dict):
            message = first.get("message")
            if isinstance(message, dict):
                text = _extract_text_from_content(message.get("content"))
                if text:
                    return text.strip()
            elif isinstance(message, str):
                return message.strip()

            text = first.get("text")
            if isinstance(text, str) and text.strip():
                return text.strip()

    # Fallback for providers that return responses-style payloads.
    output = payload.get("output")
    if isinstance(output, list):
        chunks = []
        for entry in output:
            if not isinstance(entry, dict):
                continue
            chunk = _extract_text_from_content(entry.get("content"))
            if chunk:
                chunks.append(chunk)
        if chunks:
            return "".join(chunks).strip()

    for key in ("output_text", "text"):
        maybe = payload.get(key)
        if isinstance(maybe, str) and maybe.strip():
            return maybe.strip()

    return ""


def _parse_http_error_message(raw_body: str) -> str:
    body = raw_body.strip()
    if not body:
        return "empty error body"
    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        return body[:400]

    if isinstance(payload, dict):
        error_obj = payload.get("error")
        if isinstance(error_obj, dict):
            for key in ("message", "type", "code"):
                value = error_obj.get(key)
                if value:
                    return str(value)
        if error_obj:
            return str(error_obj)

    return body[:400]


def request_openrouter(
    *,
    api_url: str,
    api_key: str,
    model_id: str,
    instruction: str,
    max_tokens: int,
    temperature: float,
    top_p: float,
    timeout_seconds: int,
    max_retries: int,
    initial_backoff_seconds: float,
    http_referer: str | None,
    x_title: str | None,
) -> tuple[dict[str, Any], int]:
    body = {
        "model": model_id,
        "messages": [
            {
                "role": "system",
                "content": "You are a precise assistant. Output only the final answer with no explanation.",
            },
            {"role": "user", "content": instruction},
        ],
        "temperature": temperature,
        "top_p": top_p,
        "max_tokens": max_tokens,
        "stream": False,
        "include_reasoning": False,
    }

    payload = json.dumps(body).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    if http_referer:
        headers["HTTP-Referer"] = http_referer
    if x_title:
        headers["X-Title"] = x_title

    last_exception: Exception | None = None

    for attempt in range(1, max_retries + 2):
        req = urllib.request.Request(api_url, data=payload, headers=headers, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout_seconds) as response:
                raw = response.read().decode("utf-8", errors="replace")
            parsed = json.loads(raw)
            return parsed, attempt

        except urllib.error.HTTPError as exc:
            raw_body = exc.read().decode("utf-8", errors="replace")
            err_message = _parse_http_error_message(raw_body)
            safe_message = redact_sensitive(err_message, api_key)
            retriable = exc.code in RETRIABLE_HTTP_STATUS

            if retriable and attempt <= max_retries:
                sleep_s = initial_backoff_seconds * (2 ** (attempt - 1))
                time.sleep(sleep_s)
                continue

            raise RuntimeError(f"HTTP {exc.code}: {safe_message}") from exc

        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_exception = exc
            if attempt <= max_retries:
                sleep_s = initial_backoff_seconds * (2 ** (attempt - 1))
                time.sleep(sleep_s)
                continue
            break

    if last_exception is not None:
        safe = redact_sensitive(str(last_exception), api_key)
        raise RuntimeError(f"request failed after retries: {safe}") from last_exception
    raise RuntimeError("request failed after retries")


def ensure_non_empty_output(text: str) -> str:
    stripped = text.strip()
    return stripped if stripped else "<EMPTY_RESPONSE>"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-id", default=os.getenv("OPENROUTER_MODEL", "liquid/lfm-2.5-1.2b-thinking:free"))
    parser.add_argument("--api-key", default=os.getenv("OPENROUTER_API_KEY"))
    parser.add_argument("--api-url", default=os.getenv("OPENROUTER_API_URL", OPENROUTER_CHAT_URL))
    parser.add_argument("--http-referer", default=os.getenv("OPENROUTER_HTTP_REFERER", "https://github.com/openclaw"))
    parser.add_argument("--x-title", default=os.getenv("OPENROUTER_X_TITLE", "blindspots-frontier-models"))
    parser.add_argument("--prompts", default="data/blindspot_prompts.jsonl")
    parser.add_argument("--all-results", default="outputs/all_results.jsonl")
    parser.add_argument("--failures", default="data/blindspots_dataset.jsonl")
    parser.add_argument("--summary", default="outputs/eval_summary.json")
    parser.add_argument("--error-log", default="outputs/eval_errors.jsonl")
    parser.add_argument("--max-tokens", type=int, default=80)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--initial-backoff-seconds", type=float, default=1.5)
    parser.add_argument("--min-successful", type=int, default=1)
    parser.add_argument("--sleep-between-prompts", type=float, default=0.0)
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("Missing OPENROUTER_API_KEY (or --api-key).")

    prompts_path = pathlib.Path(args.prompts)
    prompts = read_jsonl(prompts_path)

    all_rows: list[dict[str, Any]] = []
    error_rows: list[dict[str, Any]] = []

    for prompt in prompts:
        instruction = prompt["input"]
        started = time.time()
        try:
            response_payload, attempts = request_openrouter(
                api_url=args.api_url,
                api_key=args.api_key,
                model_id=args.model_id,
                instruction=instruction,
                max_tokens=args.max_tokens,
                temperature=args.temperature,
                top_p=args.top_p,
                timeout_seconds=args.timeout_seconds,
                max_retries=args.max_retries,
                initial_backoff_seconds=args.initial_backoff_seconds,
                http_referer=args.http_referer,
                x_title=args.x_title,
            )
            completion = extract_completion_text(response_payload)
            completion = ensure_non_empty_output(completion)
            error_message = None
            finish_reason = None
            choices = response_payload.get("choices")
            if isinstance(choices, list) and choices and isinstance(choices[0], dict):
                finish_reason = choices[0].get("finish_reason")

        except Exception as exc:  # noqa: BLE001
            attempts = args.max_retries + 1
            completion = "<API_ERROR>"
            error_message = redact_sensitive(str(exc), args.api_key)
            finish_reason = "error"
            error_rows.append(
                {
                    "id": prompt.get("id"),
                    "category": prompt.get("category"),
                    "error": error_message,
                    "timestamp_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
                }
            )

        expected = prompt["expected_output"]
        check_type = prompt.get("check_type", "exact")
        ok = False if error_message else is_correct(expected=expected, predicted=completion, check_type=check_type)

        notes = (
            "matched expected output"
            if ok
            else (f"api_error: {error_message}" if error_message else f"mismatch (expected: {expected!r})")
        )

        row = {
            "id": prompt["id"],
            "category": prompt["category"],
            "input": prompt["input"],
            "expected_output": expected,
            "model_output": completion,
            "check_type": check_type,
            "is_correct": ok,
            "notes": notes,
            "model_id": args.model_id,
            "provider": "openrouter",
            "request_attempts": attempts,
            "finish_reason": finish_reason,
            "latency_ms": round((time.time() - started) * 1000, 2),
            "timestamp_unix": int(time.time()),
        }
        all_rows.append(row)

        if args.sleep_between_prompts > 0:
            time.sleep(args.sleep_between_prompts)

    failures = [
        {
            "id": r["id"],
            "category": r["category"],
            "input": r["input"],
            "expected_output": r["expected_output"],
            "model_output": r["model_output"],
            "notes": r["notes"],
            "model_id": r["model_id"],
        }
        for r in all_rows
        if not r["is_correct"]
    ]

    write_jsonl(pathlib.Path(args.all_results), all_rows)
    write_jsonl(pathlib.Path(args.failures), failures)
    if error_rows:
        write_jsonl(pathlib.Path(args.error_log), error_rows)

    category_failure_counts: dict[str, int] = {}
    for row in failures:
        category_failure_counts[row["category"]] = category_failure_counts.get(row["category"], 0) + 1

    success_count = sum(1 for r in all_rows if r["is_correct"])
    failed_count = len(failures)
    api_error_count = len(error_rows)
    successful_api_calls = len(all_rows) - api_error_count

    summary = {
        "status": "ok" if successful_api_calls >= args.min_successful else "failed",
        "provider": "openrouter",
        "model_id": args.model_id,
        "api_url": args.api_url,
        "prompt_count": len(all_rows),
        "failure_count": failed_count,
        "success_count": success_count,
        "failure_rate": round(failed_count / len(all_rows), 4) if all_rows else 0.0,
        "failure_ids": [r["id"] for r in failures],
        "category_failure_counts": category_failure_counts,
        "api_error_count": api_error_count,
        "successful_api_calls": successful_api_calls,
        "temperature": args.temperature,
        "top_p": args.top_p,
        "max_tokens": args.max_tokens,
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
    }

    summary_path = pathlib.Path(args.summary)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))

    return 0 if successful_api_calls >= args.min_successful else 2


if __name__ == "__main__":
    raise SystemExit(main())
