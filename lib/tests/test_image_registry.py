# lib/tests/test_image_registry.py
import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

try:
    import yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

pytestmark = pytest.mark.skipif(not _YAML_AVAILABLE, reason="pyyaml not installed")


MINIMAL_REGISTRY = {
    "categories": {
        "energy": {
            "default_color_system": "warm amber",
            "allowed_concepts": ["industrial_cluster", "pipeline_infrastructure"],
            "allowed_subject_families": ["refinery", "pipeline"],
            "allowed_compositions": ["left_weighted", "right_weighted"],
        }
    },
    "subject_family_templates": {
        "refinery": "oil refinery towers at dusk",
        "pipeline": "pipeline network traversing open terrain",
    },
    "composition_templates": {
        "left_weighted": "subject offset to left third, open space right",
        "right_weighted": "subject offset to right third, open space left",
    },
    "concept_templates": {
        "industrial_cluster": "oil refinery towers and industrial chimneys",
        "pipeline_infrastructure": "industrial pipeline network",
    },
}


@pytest.fixture
def registry_file(tmp_path):
    import yaml
    path = str(tmp_path / "registry.yaml")
    with open(path, "w") as f:
        yaml.dump(MINIMAL_REGISTRY, f)
    return path


# ── load_registry ─────────────────────────────────────────────────────────────

def test_load_registry_returns_dict(registry_file):
    from lib.image_registry import load_registry
    data = load_registry(registry_file)
    assert isinstance(data, dict)
    assert "categories" in data


def test_load_registry_missing_file_returns_empty_dict():
    from lib.image_registry import load_registry
    data = load_registry("/nonexistent/path/registry.yaml")
    assert data == {}


def test_load_registry_parses_categories(registry_file):
    from lib.image_registry import load_registry
    data = load_registry(registry_file)
    assert "energy" in data["categories"]
    energy = data["categories"]["energy"]
    assert energy["allowed_concepts"] == ["industrial_cluster", "pipeline_infrastructure"]
    assert energy["allowed_subject_families"] == ["refinery", "pipeline"]
    assert energy["allowed_compositions"] == ["left_weighted", "right_weighted"]


# ── select_prompt_components — return shape ──────────────────────────────────

def test_select_returns_required_keys(registry_file):
    from lib.image_registry import select_prompt_components
    result = select_prompt_components("energy", [], registry_path=registry_file)
    for key in (
        "concept_tag", "subject_family", "composition_preset",
        "main_subject", "composition", "color_system", "novelty_request",
    ):
        assert key in result, f"Missing key: {key}"


def test_select_picks_from_allowed_pools(registry_file):
    from lib.image_registry import select_prompt_components
    result = select_prompt_components("energy", [], registry_path=registry_file)
    assert result["concept_tag"] in ["industrial_cluster", "pipeline_infrastructure"]
    assert result["subject_family"] in ["refinery", "pipeline"]
    assert result["composition_preset"] in ["left_weighted", "right_weighted"]


def test_select_resolves_subject_family_template(registry_file):
    from lib.image_registry import select_prompt_components
    result = select_prompt_components(
        "energy", [],
        subject_family="refinery",
        registry_path=registry_file,
    )
    assert result["main_subject"] == "oil refinery towers at dusk"


def test_select_resolves_composition_template(registry_file):
    from lib.image_registry import select_prompt_components
    result = select_prompt_components(
        "energy", [],
        composition_preset="left_weighted",
        registry_path=registry_file,
    )
    assert result["composition"] == "subject offset to left third, open space right"


def test_select_returns_color_system(registry_file):
    from lib.image_registry import select_prompt_components
    result = select_prompt_components("energy", [], registry_path=registry_file)
    assert result["color_system"] == "warm amber"


# ── select_prompt_components — explicit overrides ────────────────────────────

def test_concept_tag_override_respected(registry_file):
    from lib.image_registry import select_prompt_components
    result = select_prompt_components(
        "energy", [],
        concept_tag="pipeline_infrastructure",
        registry_path=registry_file,
    )
    assert result["concept_tag"] == "pipeline_infrastructure"


def test_subject_family_override_respected(registry_file):
    from lib.image_registry import select_prompt_components
    result = select_prompt_components(
        "energy", [],
        subject_family="pipeline",
        registry_path=registry_file,
    )
    assert result["subject_family"] == "pipeline"


def test_composition_preset_override_respected(registry_file):
    from lib.image_registry import select_prompt_components
    result = select_prompt_components(
        "energy", [],
        composition_preset="right_weighted",
        registry_path=registry_file,
    )
    assert result["composition_preset"] == "right_weighted"


# ── select_prompt_components — excluded_combos ───────────────────────────────

def test_excluded_combos_avoided(registry_file):
    from lib.image_registry import select_prompt_components
    from itertools import product
    # All combos: 2 concepts x 2 subjects x 2 comps = 8
    all_combos = list(product(
        ["industrial_cluster", "pipeline_infrastructure"],
        ["refinery", "pipeline"],
        ["left_weighted", "right_weighted"],
    ))
    # Exclude all but one
    target = ("pipeline_infrastructure", "refinery", "right_weighted")
    excluded = [c for c in all_combos if c != target]
    result = select_prompt_components(
        "energy", [],
        excluded_combos=excluded,
        registry_path=registry_file,
    )
    assert (result["concept_tag"], result["subject_family"], result["composition_preset"]) == target


def test_excluded_combos_relaxed_when_all_excluded(registry_file):
    from lib.image_registry import select_prompt_components
    from itertools import product
    # Exclude all possible combos -- function should not raise
    all_combos = list(product(
        ["industrial_cluster", "pipeline_infrastructure"],
        ["refinery", "pipeline"],
        ["left_weighted", "right_weighted"],
    ))
    result = select_prompt_components(
        "energy", [],
        excluded_combos=all_combos,
        registry_path=registry_file,
    )
    # Should return something valid despite all excluded
    assert result["concept_tag"] in ["industrial_cluster", "pipeline_infrastructure"]


# ── select_prompt_components — anti-repetition scoring ───────────────────────

def test_scoring_avoids_most_recent_combo(registry_file):
    from lib.image_registry import select_prompt_components
    # If one combo appeared 5 times in recent history, avoid it
    overused_triple = {
        "concept_tag": "industrial_cluster",
        "subject_family": "refinery",
        "composition_preset": "left_weighted",
    }
    recent_history = [overused_triple.copy() for _ in range(5)]
    # Run 30 trials; overused combo should be selected rarely
    results = [
        select_prompt_components("energy", recent_history, registry_path=registry_file)
        for _ in range(30)
    ]
    overused_count = sum(
        1 for r in results
        if r["concept_tag"] == "industrial_cluster"
        and r["subject_family"] == "refinery"
        and r["composition_preset"] == "left_weighted"
    )
    # With 8 alternatives equally scored at 0, the overused combo (score=5) should rarely appear
    assert overused_count < 5


def test_no_history_returns_valid_result(registry_file):
    from lib.image_registry import select_prompt_components
    result = select_prompt_components("energy", [], registry_path=registry_file)
    assert result["concept_tag"]
    assert result["subject_family"]
    assert result["composition_preset"]


# ── select_prompt_components — auto-novelty ──────────────────────────────────

def test_auto_novelty_generated_when_subject_family_overused(registry_file):
    from lib.image_registry import select_prompt_components
    # 3+ appearances of same subject_family in last 8 triggers auto novelty
    recent_history = [
        {"concept_tag": "industrial_cluster", "subject_family": "refinery", "composition_preset": "left_weighted"},
        {"concept_tag": "industrial_cluster", "subject_family": "refinery", "composition_preset": "right_weighted"},
        {"concept_tag": "pipeline_infrastructure", "subject_family": "refinery", "composition_preset": "left_weighted"},
    ]
    # Force selection of a non-refinery subject to guarantee overuse is detectable
    result = select_prompt_components(
        "energy", recent_history,
        subject_family="pipeline",  # force non-refinery selection
        registry_path=registry_file,
    )
    # novelty_request should mention avoiding "refinery"
    assert result["novelty_request"] is not None
    assert "refinery" in result["novelty_request"]


def test_no_auto_novelty_when_history_empty(registry_file):
    from lib.image_registry import select_prompt_components
    result = select_prompt_components("energy", [], registry_path=registry_file)
    assert result["novelty_request"] is None


def test_no_auto_novelty_when_no_overuse(registry_file):
    from lib.image_registry import select_prompt_components
    # Only 2 appearances of same combo -- below threshold of 3
    recent_history = [
        {"concept_tag": "industrial_cluster", "subject_family": "refinery", "composition_preset": "left_weighted"},
        {"concept_tag": "industrial_cluster", "subject_family": "refinery", "composition_preset": "left_weighted"},
    ]
    result = select_prompt_components("energy", recent_history, registry_path=registry_file)
    assert result["novelty_request"] is None


# ── select_prompt_components — unknown category fallback ─────────────────────

def test_unknown_category_returns_valid_result(registry_file):
    from lib.image_registry import select_prompt_components
    result = select_prompt_components("unknown_category", [], registry_path=registry_file)
    # Should not raise; must return the required keys
    for key in ("concept_tag", "subject_family", "composition_preset", "main_subject",
                 "composition", "color_system", "novelty_request"):
        assert key in result


def test_empty_registry_returns_valid_result():
    from lib.image_registry import select_prompt_components
    import tempfile, os
    import yaml
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({}, f)
        path = f.name
    try:
        result = select_prompt_components("energy", [], registry_path=path)
        for key in ("concept_tag", "subject_family", "composition_preset", "main_subject",
                     "composition", "color_system", "novelty_request"):
            assert key in result
    finally:
        os.unlink(path)
