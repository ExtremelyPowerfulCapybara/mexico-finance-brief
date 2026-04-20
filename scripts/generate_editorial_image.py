# scripts/generate_editorial_image.py
# ─────────────────────────────────────────────
#  CLI for the editorial image generation + deduplication subsystem.
#
#  Usage (from repo root):
#    python scripts/generate_editorial_image.py \
#      --issue-date 2026-04-15 \
#      --story-slug mexico-energy-reform \
#      --category energy \
#      --main-subject "oil refinery towers at dusk" \
#      --environment "flat industrial horizon, overcast sky" \
#      --composition "wide establishing shot, subject dominant left" \
#      --color-system "warm amber-rust tones on metal"
#
#  Optional flags:
#    --context             Editorial context (headline, event)
#    --novelty-request     Manual novelty directive
#    --variation-code      e.g. B-2-ii-gamma
#    --concept-tag         Override inferred concept tag
#    --subject-family      Override registry-selected subject family
#    --composition-preset  Override registry-selected composition preset
#    --force-novelty-level {0,1,2,3}  Apply escalation from first attempt
#    --max-retries         Default 3
#    --text-threshold      Default 0.82
#    --phash-threshold     Default 8
#    --output-dir          Directory for generated PNGs
#    --db-path             SQLite DB path
#    --dry-run             Print full prompt breakdown; skip generation
#    --show-similarity-debug  Print per-phase similarity scores after generation
#    --list-presets        Print category presets and exit
#    --list-registry-options [CATEGORY]  Print registry allowed values and exit
# ─────────────────────────────────────────────

import argparse
import json
import os
import sys
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def cmd_list_presets() -> None:
    from lib.image_prompt_builder import CATEGORY_PRESETS
    print("\n-- Category presets --------------------------------------------------\n")
    for cat, preset in CATEGORY_PRESETS.items():
        print(f"[{cat}]")
        for k, v in preset.items():
            print(f"  --{k.replace('_', '-')}: {v}")
        print()


def cmd_list_registry_options(category_filter: Optional[str] = None) -> None:
    from lib.image_registry import load_registry
    registry = load_registry()
    categories = (registry.get("categories") or {})
    if category_filter:
        if category_filter not in categories:
            print(f"Unknown category: {category_filter}. Known: {list(categories.keys())}")
            return
        categories = {category_filter: categories[category_filter]}
    print("\n-- Registry options --------------------------------------------------\n")
    for cat, cat_data in categories.items():
        print(f"[{cat}]")
        print(f"  default_color_system: {cat_data.get('default_color_system', '')}")
        print(f"  allowed_concepts:         {cat_data.get('allowed_concepts', [])}")
        print(f"  allowed_subject_families: {cat_data.get('allowed_subject_families', [])}")
        print(f"  allowed_compositions:     {cat_data.get('allowed_compositions', [])}")
        print()


def cmd_dry_run(args) -> None:
    from lib.image_prompt_builder import (
        build_image_prompt,
        infer_concept_tag,
        resolve_variation_code,
        suggest_novelty_request,
    )
    from lib.image_registry import select_prompt_components
    from lib.image_history_store import get_recent_by_category

    db_path = args.db_path or None

    # Load recent history (so dry-run works with no DB)
    recent_history = []
    candidate_count = 0
    try:
        recent_history = get_recent_by_category(args.category, limit=15, db_path=db_path)
        candidate_count = len(recent_history)
    except Exception:
        pass

    # Select prompt components from registry
    components = select_prompt_components(
        category=args.category,
        recent_history=recent_history,
        concept_tag=args.concept_tag,
        subject_family=getattr(args, "subject_family", None),
        composition_preset=getattr(args, "composition_preset", None),
        excluded_combos=[],
    )

    # Resolve values: explicit args take precedence over registry selection
    resolved_main_subject = components.get("main_subject") or args.main_subject
    resolved_composition = components.get("composition") or args.composition
    resolved_color_system = components.get("color_system") or args.color_system

    resolved_concept_tag = components.get("concept_tag") or args.concept_tag or infer_concept_tag(args.category, args.main_subject)
    resolved_subject_family = components.get("subject_family")
    resolved_composition_preset = components.get("composition_preset")

    # Determine sources for display
    ct_source = "[override]" if args.concept_tag else "[registry-selected]"
    sf_source = "[override]" if getattr(args, "subject_family", None) else "[registry-selected]"
    cp_source = "[override]" if getattr(args, "composition_preset", None) else "[registry-selected]"

    variation_text = resolve_variation_code(args.variation_code)

    # Resolve novelty: manual > force_novelty_level > auto from registry
    novelty = args.novelty_request
    novelty_source = None
    if novelty is not None:
        novelty_source = "[manual]"
    elif args.force_novelty_level is not None:
        novelty = suggest_novelty_request(
            args.category, [], escalation_level=args.force_novelty_level
        )
        novelty_source = f"[forced level {args.force_novelty_level}]"
    elif components.get("novelty_request"):
        novelty = components["novelty_request"]
        novelty_source = "[auto]"
    else:
        novelty_source = "[none]"

    prompt = build_image_prompt(
        category=args.category,
        main_subject=resolved_main_subject,
        environment=args.environment,
        composition=resolved_composition,
        color_system=resolved_color_system,
        context=args.context,
        novelty_request=novelty,
        variation_code=args.variation_code,
    )

    print("\n-- Dry-run breakdown --------------------------------------------------\n")
    print(f"Category:                    {args.category}")
    print(f"Concept tag:                 {resolved_concept_tag}  {ct_source}")
    print(f"Subject family:              {resolved_subject_family or '(none)'}  {sf_source}")
    print(f"Composition preset:          {resolved_composition_preset or '(none)'}  {cp_source}")
    print(f"Color system:                {resolved_color_system}")
    if novelty:
        print(f"Novelty directive:           {novelty_source} {novelty}")
    print(f"Same-category combos compared: {candidate_count}")
    print(f"Excluded combos:             0")
    print(f"Text threshold:              {args.text_threshold}")
    print(f"Phash threshold:             {args.phash_threshold}")
    print(f"\nFull prompt ({len(prompt)} chars):\n")
    print(prompt)


def cmd_generate(args) -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    from lib.image_generator import generate_editorial_image

    result = generate_editorial_image(
        issue_date=args.issue_date,
        story_slug=args.story_slug,
        category=args.category,
        main_subject=args.main_subject,
        environment=args.environment,
        composition=args.composition,
        color_system=args.color_system,
        context=args.context,
        novelty_request=args.novelty_request,
        variation_code=args.variation_code,
        concept_tag=args.concept_tag,
        force_novelty_level=args.force_novelty_level,
        max_retries=args.max_retries,
        text_threshold=args.text_threshold,
        phash_threshold=args.phash_threshold,
        output_dir=args.output_dir,
        db_path=args.db_path,
        subject_family=getattr(args, "subject_family", None),
        composition_preset=getattr(args, "composition_preset", None),
    )

    printable = {k: v for k, v in result.items() if k != "similarity"}
    print("\n-- Result ----------------------------------------------------------")
    print(json.dumps(printable, indent=2, ensure_ascii=False))

    if args.show_similarity_debug:
        sim = result["similarity"]
        print("\n-- Similarity debug ---------------------------------------------------")
        print(f"  text_similarity:              {sim['text_similarity']:.4f}")
        print(f"  text_risky:                   {sim['text_risky']}")
        print(f"  category_min_phash_distance:  {sim['category_min_phash_distance']}")
        print(f"  global_min_phash_distance:    {sim['global_min_phash_distance']}")
        print(f"  min_phash_distance:           {sim['min_phash_distance']}")
        print(f"  image_flagged:                {sim['image_flagged']}")
        print(f"  rejection_reason:             {sim.get('rejection_reason')}")
    else:
        sim = result["similarity"]
        print(
            f"\nSimilarity: text={sim['text_similarity']:.3f} "
            f"(risky={sim['text_risky']}), "
            f"phash_dist={sim['min_phash_distance']}, "
            f"image_flagged={sim['image_flagged']}"
        )

    print(f"Concept tag:          {result['concept_tag']}")
    print(f"Subject family:       {result.get('subject_family', '(none)')}")
    print(f"Composition preset:   {result.get('composition_preset', '(none)')}")
    print(f"Regenerations used:   {result['regeneration_count']}")
    print(f"Saved to:             {result['image_path']}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a deduplicated editorial image for a newsletter issue.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--list-presets", action="store_true",
                        help="Print category preset suggestions and exit.")

    # Required for generation
    parser.add_argument("--issue-date",   help="Issue date YYYY-MM-DD")
    parser.add_argument("--story-slug",   help="Short slug identifying the story")
    parser.add_argument("--category",     help="Category (energy, macro_inflation, etc.)")
    parser.add_argument("--main-subject", help="Main subject description")
    parser.add_argument("--environment",  help="Environment/setting description")
    parser.add_argument("--composition",  help="Composition instruction")
    parser.add_argument("--color-system", help="Color accent system description")

    # Optional generation parameters
    parser.add_argument("--context",               default=None)
    parser.add_argument("--novelty-request",       default=None)
    parser.add_argument("--variation-code",        default=None)
    parser.add_argument("--concept-tag",           default=None,
                        help="Override inferred concept tag")
    parser.add_argument("--subject-family", default=None,
                        help="Override registry-selected subject family (e.g. tanker)")
    parser.add_argument("--composition-preset", default=None,
                        help="Override registry-selected composition preset (e.g. elevated_wide)")
    parser.add_argument("--list-registry-options", nargs="?", const="",
                        metavar="CATEGORY",
                        help="Print registry allowed values per category and exit")
    parser.add_argument("--force-novelty-level",   type=int, default=None,
                        choices=[0, 1, 2, 3],
                        help="Apply this escalation level from attempt 0")
    parser.add_argument("--max-retries",           type=int, default=3)
    parser.add_argument("--text-threshold",        type=float, default=0.82,
                        help="Text similarity threshold (default 0.82)")
    parser.add_argument("--phash-threshold",       type=int, default=8,
                        help="Phash distance threshold (default 8)")
    parser.add_argument("--output-dir",            default=None)
    parser.add_argument("--db-path",               default=None)
    parser.add_argument("--dry-run",               action="store_true",
                        help="Print full prompt breakdown; skip API call")
    parser.add_argument("--show-similarity-debug", action="store_true",
                        help="Print per-phase similarity scores after generation")

    args = parser.parse_args()

    if args.list_registry_options is not None:
        cmd_list_registry_options(args.list_registry_options or None)
        return

    if args.list_presets:
        cmd_list_presets()
        return

    # Fill defaults for dry-run if some required fields are missing
    if args.dry_run:
        args.category     = args.category     or "[CATEGORY]"
        args.main_subject = args.main_subject or "[MAIN SUBJECT]"
        args.environment  = args.environment  or "[ENVIRONMENT]"
        args.composition  = args.composition  or "[COMPOSITION]"
        args.color_system = args.color_system or "[COLOR SYSTEM]"
        cmd_dry_run(args)
        return

    required = ["issue_date", "story_slug", "category", "main_subject",
                "environment", "composition", "color_system"]
    missing = [f"--{r.replace('_', '-')}" for r in required if not getattr(args, r, None)]
    if missing:
        parser.error(f"Required: {', '.join(missing)}")

    cmd_generate(args)


if __name__ == "__main__":
    main()
