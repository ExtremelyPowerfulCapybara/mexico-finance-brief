# bot/image_gen.py
# ─────────────────────────────────────────────
#  Generates a hero image prompt for an issue.
#  Pure function — no API calls, no side effects.
#
#  Inputs:  digest dict (bilingual, from summarizer)
#  Outputs: visual metadata dict for digest JSON
# ─────────────────────────────────────────────

from prompt_map import PROMPT_TEMPLATES, PROMPT_VARIANT_SUBJECTS, _BASE

TEMPLATE_VERSION = "v1"


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
