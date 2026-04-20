# lib/tests/test_image_prompt_builder.py
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from lib.image_prompt_builder import (
    build_image_prompt,
    resolve_variation_code,
    suggest_novelty_request,
    infer_concept_tag,
    PROMPT_MASTER_VERSION,
    CATEGORY_PRESETS,
)


# ── Prompt assembly ───────────────────────────────────────────────────────────

def test_build_image_prompt_contains_style_master_anchors():
    prompt = build_image_prompt(
        category="energy",
        main_subject="oil refinery towers",
        environment="flat industrial horizon",
        composition="wide establishing shot",
        color_system="warm amber-rust on metal",
    )
    assert "Premium editorial illustration" in prompt
    assert "hand-drawn ink and graphite" in prompt
    assert "no text, no logos, no watermark" in prompt


def test_build_image_prompt_inserts_subject():
    prompt = build_image_prompt(
        category="energy",
        main_subject="offshore drilling platform",
        environment="calm sea at dusk",
        composition="centered, symmetrical framing",
        color_system="steel blue accents",
    )
    assert "offshore drilling platform" in prompt
    assert "calm sea at dusk" in prompt
    assert "steel blue accents" in prompt


def test_build_image_prompt_includes_category_block():
    prompt = build_image_prompt(
        category="energy",
        main_subject="refinery towers",
        environment="horizon",
        composition="wide shot",
        color_system="amber",
    )
    assert "oil" in prompt.lower() or "industrial" in prompt.lower() or "refiner" in prompt.lower()


def test_build_image_prompt_appends_context():
    prompt = build_image_prompt(
        category="energy",
        main_subject="refinery towers",
        environment="horizon",
        composition="wide shot",
        color_system="amber",
        context="Pemex announces major output cut",
    )
    assert "Pemex announces major output cut" in prompt


def test_build_image_prompt_novelty_at_end():
    novelty = "Completely different direction required"
    prompt = build_image_prompt(
        category="energy",
        main_subject="refinery towers",
        environment="horizon",
        composition="wide shot",
        color_system="amber",
        novelty_request=novelty,
    )
    style_end_idx = prompt.index("no watermark")
    novelty_idx = prompt.index(novelty)
    assert novelty_idx > style_end_idx


def test_build_image_prompt_variation_code_appended():
    prompt = build_image_prompt(
        category="energy",
        main_subject="refinery towers",
        environment="horizon",
        composition="wide shot",
        color_system="amber",
        variation_code="B-2-ii-gamma",
    )
    assert "asymmetric" in prompt.lower() or "variation" in prompt.lower()


def test_build_image_prompt_no_optional_fields_leaves_no_placeholders():
    prompt = build_image_prompt(
        category="energy",
        main_subject="refinery towers",
        environment="horizon",
        composition="wide shot",
        color_system="amber",
    )
    assert "Editorial context:" not in prompt
    assert "Novelty directive:" not in prompt
    assert "Variation instructions:" not in prompt


def test_prompt_master_version_is_string():
    assert isinstance(PROMPT_MASTER_VERSION, str)
    assert len(PROMPT_MASTER_VERSION) > 0


# ── Variation code resolver ───────────────────────────────────────────────────

def test_resolve_variation_code_b_2_ii_gamma():
    result = resolve_variation_code("B-2-ii-gamma")
    assert result is not None
    assert "asymmetric" in result.lower()
    assert "two foreground" in result.lower() or "dual" in result.lower()
    assert "moderate" in result.lower()
    assert "desaturated" in result.lower()


def test_resolve_variation_code_returns_none_for_empty():
    assert resolve_variation_code("") is None
    assert resolve_variation_code(None) is None


def test_resolve_variation_code_returns_none_for_wrong_format():
    assert resolve_variation_code("B-2-ii") is None
    assert resolve_variation_code("B-2-ii-gamma-extra") is None


def test_resolve_variation_code_unknown_keys_skipped():
    result = resolve_variation_code("Z-2-ii-gamma")
    assert result is not None
    assert "moderate" in result.lower()


# ── Escalation levels 0–3 ─────────────────────────────────────────────────────

def test_suggest_novelty_level_0_is_mild():
    history = [{"category": "energy", "concept_tag": "industrial_cluster"} for _ in range(4)]
    result = suggest_novelty_request("energy", history, escalation_level=0)
    assert isinstance(result, str) and len(result) > 10


def test_suggest_novelty_level_3_is_strongest():
    history = [{"category": "energy", "concept_tag": "industrial_cluster"} for _ in range(8)]
    mild = suggest_novelty_request("energy", history, escalation_level=0)
    strong = suggest_novelty_request("energy", history, escalation_level=3)
    assert len(strong) > len(mild)


def test_suggest_novelty_empty_history():
    result = suggest_novelty_request("markets_finance", [], escalation_level=1)
    assert isinstance(result, str) and len(result) > 10


def test_suggest_novelty_concept_aware():
    """When a concept_tag is overused, the novelty request should mention it."""
    history = [
        {"category": "energy", "concept_tag": "industrial_cluster"}
        for _ in range(5)
    ]
    result = suggest_novelty_request(
        "energy",
        history,
        escalation_level=2,
        concept_tag_freq={"industrial_cluster": 5},
    )
    assert "industrial_cluster" in result or "industrial cluster" in result.lower()


def test_suggest_novelty_no_concept_freq_still_works():
    history = [{"category": "energy", "concept_tag": None} for _ in range(3)]
    result = suggest_novelty_request("energy", history, escalation_level=1)
    assert isinstance(result, str) and len(result) > 10


# ── Concept tag inference ─────────────────────────────────────────────────────

def test_infer_concept_tag_refinery():
    tag = infer_concept_tag("energy", "oil refinery towers at dusk")
    assert tag == "industrial_cluster"


def test_infer_concept_tag_pipeline():
    tag = infer_concept_tag("energy", "close-up of pipeline valves")
    assert tag == "pipeline_infrastructure"


def test_infer_concept_tag_container():
    tag = infer_concept_tag("shipping_geopolitics", "stacked containers at a port")
    assert tag == "container_logistics"


def test_infer_concept_tag_fallback():
    tag = infer_concept_tag("energy", "something completely unknown")
    assert tag == "energy_general"


def test_infer_concept_tag_returns_string():
    tag = infer_concept_tag("macro_inflation", "central bank exterior")
    assert isinstance(tag, str) and len(tag) > 0


# ── Category presets ──────────────────────────────────────────────────────────

def test_category_presets_cover_all_required_categories():
    required = {
        "energy", "shipping_geopolitics", "trade_supply_chain",
        "macro_inflation", "policy_institutional", "markets_finance",
    }
    assert required.issubset(set(CATEGORY_PRESETS.keys()))


def test_category_presets_have_required_keys():
    required_keys = {"main_subject", "environment", "composition", "color_system"}
    for cat, preset in CATEGORY_PRESETS.items():
        assert required_keys.issubset(set(preset.keys())), f"Preset for '{cat}' missing keys"


# ── New frequency parameters (subject_family_freq and composition_freq) ─────

def test_suggest_novelty_subject_family_freq_avoids_overused():
    result = suggest_novelty_request(
        "energy", [],
        escalation_level=2,
        subject_family_freq={"refinery": 4, "pipeline": 1},
    )
    assert "refinery" in result


def test_suggest_novelty_composition_freq_avoids_overused():
    result = suggest_novelty_request(
        "energy", [],
        escalation_level=2,
        composition_freq={"left_weighted": 3, "right_weighted": 1},
    )
    assert "left weighted" in result or "left_weighted" in result


def test_suggest_novelty_level3_mentions_most_recent_subject():
    from lib.image_prompt_builder import suggest_novelty_request
    # Use a recent history entry with subject_family NOT in subject_family_freq
    # so we can tell if most_recent_clause fires independently
    recent = [
        {"subject_family": "offshore_rig", "composition_preset": "elevated_wide"},
        {"subject_family": "pipeline", "composition_preset": "right_weighted"},
    ]
    result = suggest_novelty_request(
        "energy", recent,
        escalation_level=3,
        subject_family_freq={"refinery": 3},  # refinery overused, not offshore_rig
        composition_freq={},
    )
    # "refinery" should appear from subject_family_freq avoidance clause
    assert "refinery" in result
    # "offshore rig" should appear from most_recent_clause (recent_history[0])
    assert "offshore rig" in result


def test_suggest_novelty_new_params_are_optional():
    # Old call signature should still work unchanged
    result = suggest_novelty_request("energy", [], escalation_level=1)
    assert isinstance(result, str) and len(result) > 0
