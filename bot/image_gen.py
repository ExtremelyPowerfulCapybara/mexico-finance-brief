# bot/image_gen.py
# ─────────────────────────────────────────────
#  Hero image metadata and generation for an issue.
#
#  generate_hero_prompt() -- pure, no side effects.
#  generate_hero_image()  -- calls OpenAI, writes PNG
#                            to docs/images/, updates DB.
#
#  Inputs:  digest dict (bilingual, from summarizer)
#  Outputs: visual metadata dict for digest JSON
# ─────────────────────────────────────────────

import json
import os

from prompt_map import PROMPT_TEMPLATES, PROMPT_VARIANT_SUBJECTS, _BASE

TEMPLATE_VERSION = "v1"

# Three compositional framings applied to a story-specific subject.
# Tuple: (prompt_template, short label for Telegram caption)
_VARIANT_COMPOSITIONS = [
    ("{subject}, wide establishing shot, environmental context visible", "Wide shot"),
    ("close-up of {subject}, isolated detail, shallow depth of field", "Close-up"),
    ("{subject}, low angle with strong perspective and architectural framing", "Low angle"),
]


def _strip_article(text: str) -> str:
    """Strip a leading indefinite article for display captions."""
    for prefix in ("a ", "an "):
        if text.lower().startswith(prefix):
            return text[len(prefix):]
    return text


def generate_hero_prompt(digest: dict) -> dict:
    """
    Derive hero image metadata from the lead story.

    Tag and headline come from digest["es"]["stories"][0].
    Sentiment label comes from digest["en"]["sentiment"]["label_en"]
    to keep English content in the English block.
    Falls back at each step.
    """
    digest_es = digest.get("es", {})
    digest_en = digest.get("en", digest_es)

    stories  = digest_es.get("stories", [])
    lead     = stories[0] if stories else {}

    tag      = lead.get("tag", "Macro")
    headline = lead.get("headline", "")

    # Sentiment: read label_en from EN block; fall back to ES block; then default
    sent_en  = digest_en.get("sentiment", {})
    sent_es  = digest_es.get("sentiment", {})
    mood     = sent_en.get("label_en") or sent_es.get("label_en") or "Cautious"

    template = PROMPT_TEMPLATES.get(tag, PROMPT_TEMPLATES["Macro"])
    prompt   = template.format(headline=headline, sentiment=mood)

    # Generate 3 compositional variants; opt1 matches the default prompt above.
    variant_subjects = PROMPT_VARIANT_SUBJECTS.get(tag, PROMPT_VARIANT_SUBJECTS["Macro"])
    hero_options = {}
    for i, subject in enumerate(variant_subjects[:3], start=1):
        hero_options[f"opt{i}"] = _BASE.format(
            subject=subject,
            headline=headline,
            sentiment=mood,
        )

    # Concise captions derived from variant subjects — no new LLM call.
    # Strip leading indefinite article and capitalize for mobile-friendly display.
    def _caption(subject: str) -> str:
        for prefix in ("a ", "an "):
            if subject.lower().startswith(prefix):
                subject = subject[len(prefix):]
                break
        return subject[:1].upper() + subject[1:]

    hero_option_summaries = {
        f"opt{i+1}": _caption(subject)
        for i, subject in enumerate(variant_subjects[:3])
    }

    return {
        "hero_category":         tag,
        "hero_category_source":  "lead_story",
        "hero_prompt_template":  template,
        "hero_prompt_version":   TEMPLATE_VERSION,
        "hero_prompt":           prompt,
        "hero_options":          hero_options,
        "hero_option_summaries": hero_option_summaries,
        "hero_selected":         None,
    }


# Maps Claude story tags to CATEGORY_PRESETS keys in lib/image_prompt_builder.py.
# Unknown tags fall back to "macro_inflation".
TAG_TO_PRESET: dict = {
    "Macro":    "macro_inflation",
    "FX":       "macro_inflation",
    "México":   "macro_inflation",
    "Tasas":    "macro_inflation",
    "Comercio": "trade_supply_chain",
    "Mercados": "markets_finance",
    "Energía":  "energy",
    "Política": "policy_institutional",
}


def extract_visual_keywords(story: dict, category: str) -> dict:
    """
    Call Claude Haiku to extract story-specific visual elements for image generation.
    Returns dict with 'main_subject' and 'environment', or {} on any failure.
    """
    import anthropic
    import config

    headline = story.get("headline", "")
    body = story.get("body", "")
    if not headline:
        return {}

    prompt = (
        "You are an art director for a high-end financial newsletter. "
        "Given the story below, describe a specific visual scene for an editorial illustration.\n\n"
        f"Category: {category}\n"
        f"Headline: {headline}\n"
        f"Summary: {body}\n\n"
        "Respond with JSON only, no explanation:\n"
        "{\n"
        '  "main_subject": "dominant foreground visual element, 10-15 words, specific to this story",\n'
        '  "environment": "setting or background context, 10-15 words, specific to this story"\n'
        "}\n\n"
        "Style constraints: hand-drawn ink illustration, no people, no text in image, no flags or logos."
    )

    try:
        client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=150,
            messages=[{"role": "user", "content": prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        return json.loads(text)
    except Exception as exc:
        print(f"  [image_gen] Keyword extraction failed: {exc}")
        return {}


def generate_hero_image(digest: dict, issue_date: str, output_dir: str) -> dict:
    """
    Extends generate_hero_prompt() to actually produce a PNG via OpenAI.

    Saves image to output_dir/{issue_date}_hero.png.
    Sets visual["hero_image"] to the public URL on success.
    On SKIP_IMAGE=true or any generation error, returns visual without hero_image.
    """
    from lib.image_generator import generate_editorial_image
    from lib.image_prompt_builder import CATEGORY_PRESETS
    import config

    visual = generate_hero_prompt(digest)

    if config.SKIP_IMAGE:
        return visual

    tag = visual.get("hero_category", "Macro")
    preset_key = TAG_TO_PRESET.get(tag, "macro_inflation")
    preset = CATEGORY_PRESETS[preset_key]

    digest_es = digest.get("es", digest)
    stories = digest_es.get("stories", [])
    lead = stories[0] if stories else {}
    context = lead.get("headline", "")

    keywords = extract_visual_keywords(lead, preset_key)
    main_subject = keywords.get("main_subject") or preset["main_subject"]
    environment = keywords.get("environment") or preset["environment"]

    # If Haiku returned a story-specific subject, rebuild hero_options so Telegram
    # candidates use story-specific prompts and labels instead of the static lookup.
    if keywords.get("main_subject"):
        digest_en = digest.get("en", digest_es)
        mood = (
            digest_en.get("sentiment", {}).get("label_en")
            or digest_es.get("sentiment", {}).get("label_en")
            or "Cautious"
        )
        new_options = {}
        new_summaries = {}
        for i, (comp_tmpl, comp_label) in enumerate(_VARIANT_COMPOSITIONS, start=1):
            subject_with_comp = comp_tmpl.format(subject=main_subject)
            new_options[f"opt{i}"] = _BASE.format(
                subject=subject_with_comp,
                headline=context,
                sentiment=mood,
            )
            caption = _strip_article(main_subject)
            new_summaries[f"opt{i}"] = f"{caption[:1].upper()}{caption[1:]} — {comp_label}"
        visual["hero_options"] = new_options
        visual["hero_option_summaries"] = new_summaries

    try:
        result = generate_editorial_image(
            issue_date=issue_date,
            story_slug="hero",
            category=preset_key,
            main_subject=main_subject,
            environment=environment,
            composition=preset["composition"],
            color_system=preset["color_system"],
            context=context,
            output_dir=output_dir,
        )
        filename = os.path.basename(result["image_path"])
        visual["hero_image"] = f"{config.ASSET_BASE_URL.rstrip('/')}/images/{filename}"
    except Exception as exc:
        print(f"  [image_gen] Hero image generation failed: {exc}")

    return visual
