# OpenRouter Key and Model Call Schemes

## API key scheme

Use an environment variable, not a hardcoded key:

```bash
export OPENROUTER_API_KEY="sk-or-v1-REPLACE_ME"
```

Required header:

- `Authorization: Bearer $OPENROUTER_API_KEY`

Recommended headers:

- `HTTP-Referer: https://your-app.example`
- `X-Title: Blindspots Frontier Models`

Base endpoint:

- `POST https://openrouter.ai/api/v1/chat/completions`

Minimal request shape:

```json
{
  "model": "<openrouter-model-id>",
  "messages": [
    {"role": "user", "content": "hi"}
  ],
  "max_tokens": 64
}
```

## Models you listed (correct OpenRouter IDs)

1. `stepfun/step-3.5-flash:free`
2. `arcee-ai/trinity-large-preview:free`
3. `upstage/solar-pro-3:free`
4. `liquid/lfm-2.5-1.2b-thinking:free`
5. `liquid/lfm-2.5-1.2b-instruct:free`
6. `nvidia/nemotron-3-nano-30b-a3b:free`
7. `arcee-ai/trinity-mini:free`
8. `nvidia/nemotron-nano-12b-v2-vl:free`
9. `qwen/qwen3-vl-30b-a3b-thinking`
10. `qwen/qwen3-vl-235b-a22b-thinking`
11. `qwen/qwen3-next-80b-a3b-instruct:free`
12. `nvidia/nemotron-nano-9b-v2:free`
13. `google/gemma-3n-e2b-it:free`
14. `google/gemma-3n-e4b-it:free`
15. `qwen/qwen3-4b:free`
16. `mistralai/mistral-small-3.1-24b-instruct:free`
17. `google/gemma-3-4b-it:free`
18. `google/gemma-3-12b-it:free`
19. `google/gemma-3-27b-it:free`
20. `meta-llama/llama-3.3-70b-instruct:free`
21. `meta-llama/llama-3.2-3b-instruct:free`
22. `nousresearch/hermes-3-llama-3.1-405b:free`

## Per-model call scheme (curl)

Template:

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -H "HTTP-Referer: https://your-app.example" \
  -H "X-Title: Blindspots Frontier Models" \
  -d '{
    "model": "MODEL_ID_HERE",
    "messages": [{"role":"user","content":"Say hi in one short sentence."}],
    "max_tokens": 80,
    "include_reasoning": false
  }'
```

### 1) StepFun Step 3.5 Flash (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"stepfun/step-3.5-flash:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80,"include_reasoning":false}'
```

### 2) Arcee Trinity Large Preview (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"arcee-ai/trinity-large-preview:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80,"include_reasoning":false}'
```

### 3) Upstage Solar Pro 3 (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"upstage/solar-pro-3:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 4) Liquid LFM2.5 1.2B Thinking (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"liquid/lfm-2.5-1.2b-thinking:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80,"include_reasoning":false}'
```

### 5) Liquid LFM2.5 1.2B Instruct (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"liquid/lfm-2.5-1.2b-instruct:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 6) NVIDIA Nemotron 3 Nano 30B A3B (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-3-nano-30b-a3b:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80,"include_reasoning":false}'
```

### 7) Arcee Trinity Mini (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"arcee-ai/trinity-mini:free","messages":[{"role":"user","content":"hi"}],"max_tokens":120,"include_reasoning":false}'
```

### 8) NVIDIA Nemotron Nano 12B V2 VL (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-nano-12b-v2-vl:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 9) Qwen3 VL 30B A3B Thinking

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen/qwen3-vl-30b-a3b-thinking","messages":[{"role":"user","content":"hi"}],"max_tokens":120,"include_reasoning":false}'
```

### 10) Qwen3 VL 235B A22B Thinking

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen/qwen3-vl-235b-a22b-thinking","messages":[{"role":"user","content":"hi"}],"max_tokens":120,"include_reasoning":false}'
```

### 11) Qwen3 Next 80B A3B Instruct (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen/qwen3-next-80b-a3b-instruct:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 12) NVIDIA Nemotron Nano 9B V2 (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"nvidia/nemotron-nano-9b-v2:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80,"include_reasoning":false}'
```

### 13) Google Gemma 3n 2B (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemma-3n-e2b-it:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 14) Google Gemma 3n 4B (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemma-3n-e4b-it:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 15) Qwen3 4B (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"qwen/qwen3-4b:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 16) Mistral Small 3.1 24B (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"mistralai/mistral-small-3.1-24b-instruct:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 17) Google Gemma 3 4B (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemma-3-4b-it:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 18) Google Gemma 3 12B (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemma-3-12b-it:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 19) Google Gemma 3 27B (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"google/gemma-3-27b-it:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 20) Meta Llama 3.3 70B Instruct (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"meta-llama/llama-3.3-70b-instruct:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 21) Meta Llama 3.2 3B Instruct (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"meta-llama/llama-3.2-3b-instruct:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

### 22) Nous Hermes 3 405B Instruct (free)

```bash
curl -s https://openrouter.ai/api/v1/chat/completions \
  -H "Authorization: Bearer $OPENROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"nousresearch/hermes-3-llama-3.1-405b:free","messages":[{"role":"user","content":"hi"}],"max_tokens":80}'
```

## Notes

- If you get HTTP `429`, retry with backoff or switch to another free model.
- For some `thinking` models, set `include_reasoning: false` if you only want visible assistant text.
- Do not commit real API keys to git.
