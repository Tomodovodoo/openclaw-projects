# Runtime Environment Notes

For execution, credentials were provided via environment variables (not committed):

- `HF_TOKEN`
- `HUGGINGFACE_TOKEN`
- `OPENROUTER_API_KEY` (available for OpenRouter flows)

Example pattern used:

```bash
HF_TOKEN='<redacted>' HUGGINGFACE_TOKEN='<redacted>' python scripts/push_hf_dataset.py ...
```

No raw token values are stored in tracked project files.
