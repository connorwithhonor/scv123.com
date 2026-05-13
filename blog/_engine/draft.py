#!/usr/bin/env python3
"""
SCV123 blog post drafting engine.

Usage:
    python3 draft.py <card_id>           # 1..17
    python3 draft.py --model opus 7      # override model
    python3 draft.py --dry-run 1         # print prompt, do not call API

Outputs (in this directory):
    drafts/<slug>.md    raw model output
    drafts/<slug>.html  templated final HTML

Env:
    ANTHROPIC_API_KEY (required)

Voice/brand system prompt is prompt-cached so repeated runs hit the cache.
After generation, the script greps for em dashes and banned phrases.
"""

import argparse
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent
CARDS_PATH = ENGINE_DIR / "cards.json"
PROMPT_PATH = ENGINE_DIR / "prompt-template.md"
TEMPLATE_PATH = ENGINE_DIR / "template.html"
DRAFTS_DIR = ENGINE_DIR / "drafts"

DEFAULT_MODEL = "claude-sonnet-4-6"
MODEL_ALIASES = {
    "sonnet": "claude-sonnet-4-6",
    "opus": "claude-opus-4-7",
    "haiku": "claude-haiku-4-6",
}

# Hard fail patterns. Case-insensitive. Word boundaries where it matters.
EM_DASH_RE = re.compile(r"—|–")  # em dash, en dash
BANNED_PATTERNS = [
    r"\bas an AI\b",
    r"\bdelve\b",
    r"\bdelving\b",
    r"\bnavigate\b",
    r"\bnavigating\b",
    r"\btapestry\b",
    r"\blandscape\b",
    r"\bembark on a journey\b",
    r"\bin today's world\b",
    r"\bin the realm of\b",
    r"\bunlock\b",
    r"\bleverage\b",  # noun ok in finance contexts, but the verb is banned
    r"\brobust\b",
    r"\bseamless\b",
    r"\bsynergy\b",
    r"\bever-evolving\b",
    r"\bin conclusion\b",
    r"\bmoreover\b",
    r"\bfurthermore\b",
    r"\bI cannot\b",
    r"\bI'm unable to\b",
]
BANNED_RE = [re.compile(p, re.IGNORECASE) for p in BANNED_PATTERNS]


def load_cards():
    with open(CARDS_PATH, "r") as f:
        return json.load(f)["cards"]


def load_prompt():
    return PROMPT_PATH.read_text()


def load_template():
    return TEMPLATE_PATH.read_text()


def get_card(card_id, cards):
    for c in cards:
        if c["id"] == card_id:
            return c
    sys.exit(f"ERROR: card id {card_id} not in cards.json")


def split_system_task(prompt_text):
    """
    Split prompt-template.md into the cacheable system block (voice + brand)
    and the per-card task block. Cut at the '## TASK PROMPT' header.
    """
    marker = "## TASK PROMPT"
    if marker not in prompt_text:
        sys.exit(f"ERROR: prompt-template.md missing '{marker}' header")
    head, tail = prompt_text.split(marker, 1)
    system = head.strip()
    task = (marker + tail).strip()
    return system, task


def render_task(task_template, card):
    return (
        task_template
        .replace("{{CARD_ID}}", str(card["id"]))
        .replace("{{CARD_TITLE}}", card["title"])
        .replace("{{CARD_HOOK}}", card["hook"])
        .replace("{{CARD_VERDICT}}", card["verdict"])
        .replace("{{TARGET_KEYWORD}}", card["target_keyword"])
        .replace("{{META_DESCRIPTION}}", card["seo_meta_description"])
    )


def verify(draft_text):
    """Return list of violations. Empty list = pass."""
    violations = []
    em = EM_DASH_RE.findall(draft_text)
    if em:
        violations.append(f"em/en dashes found: {len(em)} occurrences")
    for pat in BANNED_RE:
        hits = pat.findall(draft_text)
        if hits:
            violations.append(f"banned phrase /{pat.pattern}/: {len(hits)} occurrences")
    words = len(re.findall(r"\b\w+\b", draft_text))
    if words < 1100 or words > 1900:
        violations.append(f"word count out of band: {words} (target 1200-1800)")
    return violations


def render_template(template_text, card, body_html, published_date):
    display_date = datetime.strptime(published_date, "%Y-%m-%d").strftime("%B %d, %Y")
    return (
        template_text
        .replace("{{title}}", card["title"])
        .replace("{{slug}}", card["slug"])
        .replace("{{meta_description}}", card["seo_meta_description"])
        .replace("{{target_keyword}}", card["target_keyword"])
        .replace("{{published_date_display}}", display_date)
        .replace("{{published_date}}", published_date)
        .replace("{{body}}", body_html)
    )


def call_anthropic(model, system_text, task_text):
    try:
        import anthropic
    except ImportError:
        sys.exit("ERROR: anthropic SDK not installed. Run: pip install anthropic")
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit("ERROR: ANTHROPIC_API_KEY not set in environment")
    client = anthropic.Anthropic()
    # System block is cache-controlled so the voice/brand rules cache across all 17 calls.
    msg = client.messages.create(
        model=model,
        max_tokens=8000,
        system=[
            {
                "type": "text",
                "text": system_text,
                "cache_control": {"type": "ephemeral"},
            }
        ],
        messages=[{"role": "user", "content": task_text}],
    )
    return "".join(block.text for block in msg.content if hasattr(block, "text"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("card_id", type=int, help="card id 1..17")
    ap.add_argument("--model", default=DEFAULT_MODEL, help="model id or alias (sonnet/opus/haiku)")
    ap.add_argument("--dry-run", action="store_true", help="print prompt, do not call API")
    ap.add_argument("--date", default=datetime.now().strftime("%Y-%m-%d"),
                    help="published date YYYY-MM-DD (default: today)")
    args = ap.parse_args()

    model = MODEL_ALIASES.get(args.model, args.model)

    cards = load_cards()
    card = get_card(args.card_id, cards)
    system_text, task_template = split_system_task(load_prompt())
    task_text = render_task(task_template, card)

    if args.dry_run:
        print("=" * 80)
        print(f"MODEL: {model}")
        print(f"CARD #{card['id']}: {card['title']}  (slug: {card['slug']})")
        print("=" * 80)
        print("SYSTEM PROMPT:")
        print(system_text)
        print("=" * 80)
        print("TASK PROMPT:")
        print(task_text)
        print("=" * 80)
        return

    DRAFTS_DIR.mkdir(exist_ok=True)
    print(f"[draft] card #{card['id']} '{card['title']}' via {model}...")
    body_html = call_anthropic(model, system_text, task_text)

    md_path = DRAFTS_DIR / f"{card['slug']}.md"
    md_path.write_text(body_html)
    print(f"[draft] raw written: {md_path}")

    violations = verify(body_html)
    if violations:
        print("[VERIFY FAILED]", file=sys.stderr)
        for v in violations:
            print(f"  - {v}", file=sys.stderr)
        print(f"  raw saved at {md_path} for inspection. HTML render skipped.", file=sys.stderr)
        sys.exit(2)
    print("[verify] passed: no em dashes, no banned phrases, word count in band")

    template_text = load_template()
    final_html = render_template(template_text, card, body_html, args.date)
    html_path = DRAFTS_DIR / f"{card['slug']}.html"
    html_path.write_text(final_html)
    print(f"[draft] HTML written: {html_path}")
    print(f"[done] review before copying to /blog/")


if __name__ == "__main__":
    main()
