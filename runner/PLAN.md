# Green runner — plan for cross-model review

One workstream. One-shot. No factory.

## Green (this slice)

```
python -m runner
```

1. Scout read-only, or use fixtures if no keys / no local dump
2. Draft exactly one buyer-facing promise
3. Score it
4. Write `receipts/latest.md` (+ `.json`)
5. Exit

Development boots with **zero secrets**. This slice does **not** call xAI, Gumroad, or Supabase.

Paper-win (record hit/miss only; do not ping):

1. ≥5 sourced non-fixture signals
2. ≥3 pain/intent clues (not hype)
3. score >60, medium+ confidence, source URLs
4. promise still makes sense after reading the sources

If any gate fails: write **miss** and exit.

## This diff

- `--signals path.json` — optional local read-only dump (no HTTP)
- Receipt records `scout_mode`: `fixtures` or `local_file`
- Default `python -m runner` is unchanged: fixtures → miss

## Red (do not build)

- first post
- listing
- dollar
- buyer conversation
- deploy / n8n / Railway / Pinterest / Gumroad publish / ads / MailerLite / auto-post / prod Supabase / SQLite-boot-as-the-product
- merge `molly-improvements-20260203`
