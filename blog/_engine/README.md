# SCV123 Blog Drafting Engine

Turns the 17 cards in the SCV123.com homepage deck into full standalone blog posts at `/blog/<slug>.html`.

This engine **drafts**. It does not deploy. Connor reviews every draft before any HTML is copied into `/blog/` or pushed to Netlify.

---

## Files

| File | Purpose |
|------|---------|
| `cards.json` | The 17 extracted cards (id, slug, title, hook, target keyword, meta description). Source of truth for what gets drafted. |
| `template.html` | The page shell. Jinja-style placeholders: `{{title}}`, `{{body}}`, `{{meta_description}}`, `{{slug}}`, `{{published_date}}`, `{{published_date_display}}`, `{{target_keyword}}`. Matches the existing `/blog/ai-is-replacing-everything.../index.html` style. |
| `prompt-template.md` | The full prompt sent to Claude. Voice rules cite mempalace standing-orders. The first half (system) is prompt-cached; the second half (task) is per-card. |
| `draft.py` | Python runner. Drafts ONE card. Writes `drafts/<slug>.md` (raw) and `drafts/<slug>.html` (templated). Verifies output for em dashes and banned phrases before writing the HTML. |
| `draft-all.sh` | Loops cards 1..17 with a 2-second delay between API calls. |

Output lands in `drafts/` (created on first run). Nothing is written outside `_engine/`.

---

## Setup

```bash
cd ~/dev/scv123.com/blog/_engine

# one time
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...   # add to ~/.zshrc to persist

# optional, make scripts executable
chmod +x draft.py draft-all.sh
```

---

## Usage

### Draft one card

```bash
python3 draft.py 1                    # card #1, default model (sonnet 4.6)
python3 draft.py 7 --model opus       # card #7, opus 4.7
python3 draft.py 3 --dry-run          # print full prompt, do not call API
python3 draft.py 1 --date 2026-05-15  # override published date
```

### Draft all 17

```bash
./draft-all.sh                        # default model
./draft-all.sh claude-opus-4-7        # override model
START=8 END=12 ./draft-all.sh         # subset
```

### Output location

```
_engine/drafts/the-percentage-tradition.md
_engine/drafts/the-percentage-tradition.html
... (17 of each)
```

---

## Cost estimate

Math for a full 17-card run at Sonnet 4.6 pricing ($3 / MTok input, $15 / MTok output, cache reads $0.30 / MTok):

- System prompt (voice + brand + facts): ~1,400 tokens, cached after first call
- Per-card task prompt: ~600 tokens
- Output per post: 1200-1800 words ≈ 1,800-2,700 tokens. Budget 2,500.

Total per run:
- Cache write (card 1 only): 1,400 input tokens × $3.75/MTok = $0.005
- Cache reads (cards 2-17): 16 × 1,400 × $0.30/MTok = $0.007
- Per-card task input: 17 × 600 × $3/MTok = $0.031
- Output: 17 × 2,500 × $15/MTok = $0.638

**Estimated total: $0.68 per full 17-card run on Sonnet 4.6.** Opus 4.7 is roughly 5x that ($3.40).

A second pass at any failed card is pennies.

---

## Voice + brand rules (enforced)

Pulled from `~/local-memory/mempalace/standing-orders.md`:

- No em dashes. Ever. (`draft.py` greps for `—` and `–` and fails the run.)
- Banned phrases (also enforced by grep): `as an AI`, `delve`, `navigate`, `tapestry`, `landscape`, `embark on a journey`, `in today's world`, `unlock`, `leverage` (as verb), `robust`, `seamless`, `synergy`, `ever-evolving`, `in conclusion`, `moreover`, `furthermore`.
- Word count: 1200-1800 (enforced).
- Brand lockup: `$17,000 flat`, `Sellers Only Agent`, `SCV123.com`, `sellersonlyagent.com`. Never `GHL` or `GoHighLevel`.

If a draft fails verification, the `.md` is saved for inspection and the `.html` is NOT written. Re-run the same card to redraft.

---

## Manual review checklist (CONNOR DOES THIS BEFORE COMMIT)

After each `.html` lands in `drafts/`, before copying to `/blog/`:

1. **Voice match.** Read out loud. Does it sound like Connor or like a marketing intern?
2. **Factual accuracy** on CA real estate law. Specifically: commission negotiability (B&P 10140.6), NAR settlement claims, dual agency state count, DRE license number, SYNC Brokerage.
3. **No em dashes.** Script catches them, but verify with a fresh eye anyway. Watch for em dashes hiding in pasted quotes.
4. **Internal links make sense.** Each cross-link should land on a post whose topic actually overlaps. No stuffing.
5. **CTA flow.** Final paragraph should set up the homepage savings calculator. Template adds the actual CTA box pointing to `/#form-section`.
6. **SCV-specific numbers** are present and current ($745K median, 56 DOM, 21.7% 5-yr appreciation, 2.1 months supply).
7. **SEO meta + schema render correctly** in browser preview.

---

## Workflow (recommended)

```bash
# 1. Draft one to feel the voice
python3 draft.py 1
open drafts/the-percentage-tradition.html

# 2. Iterate prompt-template.md until card #1 is clean

# 3. Draft the full batch
./draft-all.sh

# 4. Review all 17 in browser

# 5. Approved drafts get copied (NOT auto-moved):
#    cp drafts/<slug>.html ~/dev/scv123.com/blog/<slug>.html
#    Then deploy via netlify-mcp (manual, per standing orders)
```

**Connor approves before any HTML is copied into `/blog/` or pushed to Netlify.** Per standing-orders.md rule 2: manual deploys only. Per rule 12: blog posts get pulled from Netlify to GitHub after deploy, never reverse.

---

## Re-extracting cards

If the card deck on `index.html` changes, re-extract by hand or regenerate `cards.json` from the `var cards=[...]` block on lines 325-343 of `/Users/macv/dev/scv123.com/index.html`.

---

## Model notes

Default is `claude-sonnet-4-6`. Per Connor's CCD setup the available aliases in this engine:

- `sonnet` -> `claude-sonnet-4-6` (default, recommended)
- `opus` -> `claude-opus-4-7` (use for tricky cards like #12 NAR settlement or #14 6% myth where nuance matters)
- `haiku` -> `claude-haiku-4-6` (cost-only experiments, voice quality drops)
