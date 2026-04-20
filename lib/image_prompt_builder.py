# lib/image_prompt_builder.py
# ─────────────────────────────────────────────────────────────────────────────
#  Builds image prompts for the editorial deduplication system.
#
#  Block assembly order (never reorder):
#    1. style_master  (fixed, stable)
#    2. category_block
#    3. context_block (if provided)
#    4. variation_block (if variation_code provided)
#    5. novelty_block (if novelty_request provided — always last)
# ─────────────────────────────────────────────────────────────────────────────

from typing import Dict, List, Optional

PROMPT_MASTER_VERSION = "v1"

STYLE_MASTER = (
    "Premium editorial illustration for a high-end financial and geopolitical newsletter, "
    "hand-drawn ink and graphite style with refined linework and subtle cross-hatching, "
    "expressive but controlled linework with slightly varied line weight and subtle human imperfection, "
    "monochrome base with controlled muted color accents (approximately 20-25%), "
    "slightly textured paper background, "
    "{MAIN_SUBJECT} placed in {ENVIRONMENT}, "
    "{COMPOSITION}, "
    "asymmetrical layout with intentional visual balance, "
    "main subject clearly dominant in the foreground, "
    "minimal and elegant composition with strong negative space, "
    "realistic proportions and believable detail, "
    "calm and sophisticated atmosphere with subtle economic or geopolitical tension, "
    "modern whitepaper-inspired editorial aesthetic with a distinctive contemporary edge, "
    "restrained and mature tone, "
    "color accents concentrated primarily on the main subject using {COLOR_SYSTEM}, "
    "background color extremely subdued and desaturated, "
    "background with moderate detail but softened edges and lower contrast using atmospheric perspective, "
    "subtle narrative quality suggesting broader context, "
    "soft grounded baseline anchoring the composition, "
    "not painterly, not cinematic, not glossy, not photorealistic, not 3D render, not infographic, "
    "no bright colors, no neon, no cyberpunk, no exaggerated lighting, no dramatic action, "
    "no explosions, no clutter, no text, no logos, no watermark."
)

CATEGORY_BLOCKS: Dict[str, str] = {
    "energy": (
        "Category domain: oil and gas infrastructure, refineries, pipelines, "
        "offshore platforms, or industrial energy facilities with physical gravitas"
    ),
    "shipping_geopolitics": (
        "Category domain: port infrastructure, container yards, cargo vessels, "
        "maritime chokepoints, or strategic waterways"
    ),
    "trade_supply_chain": (
        "Category domain: logistics hubs, customs checkpoints, warehouses, "
        "industrial transit corridors, or supply chain infrastructure"
    ),
    "macro_inflation": (
        "Category domain: central bank architecture, empty trading floors, "
        "institutional financial settings, or monetary symbols"
    ),
    "policy_institutional": (
        "Category domain: government buildings, legislative chambers, "
        "institutional facades, or state apparatus settings"
    ),
    "markets_finance": (
        "Category domain: financial district architecture, stock exchanges, "
        "data-driven trading environments, or capital market settings"
    ),
}

# ── Variation code components ─────────────────────────────────────────────────
# Format: [COMPOSITION]-[FOREGROUND]-[BACKGROUND]-[COLOR]
# Example: B-2-ii-gamma

COMPOSITION_PRESETS: Dict[str, str] = {
    "A": "centered symmetrical framing, subject anchored at the optical center",
    "B": "asymmetric left-weighted composition, subject offset to the left third, open space right",
    "C": "asymmetric right-weighted composition, subject offset to the right third, open space left",
    "D": "diagonal tension line through the frame, subject at the upper or lower intersection",
    "E": "split-frame composition, foreground element and background element in visual dialogue",
}

FOREGROUND_PRESETS: Dict[str, str] = {
    "1": "single dominant foreground subject, all other elements clearly subordinate",
    "2": "two foreground elements in visual tension, neither fully dominant, balanced dual weight",
    "3": "scattered foreground elements suggesting multiplicity or systemic complexity",
    "4": "foreground element framing a deeper secondary subject, frame-within-frame structure",
}

BACKGROUND_PRESETS: Dict[str, str] = {
    "i":   "minimal background, near-empty space with faint texture or horizon only",
    "ii":  "moderate background detail, recognizable environment softened by atmospheric perspective",
    "iii": "rich background, layered architectural or industrial elements receding into distance",
    "iv":  "complex background, multiple receding planes suggesting depth and systemic scale",
}

COLOR_PRESETS: Dict[str, str] = {
    "alpha":   "warm muted earth tones on the subject — ochre, rust, or aged-paper warmth",
    "beta":    "cool muted accents on the subject — slate blue, steel gray, or faded teal",
    "gamma":   "fully desaturated — no color accents, pure graphite and ink monochrome",
    "delta":   "sepia-tinted warm monochrome, aged document aesthetic with amber undertones",
    "epsilon": "graphite with single restrained accent — one hue only, used sparingly on key detail",
}

CATEGORY_PRESETS: Dict[str, Dict[str, str]] = {
    "energy": {
        "main_subject": "oil refinery towers and storage tanks with slow industrial exhaust rising",
        "environment":  "flat industrial horizon at dusk, overcast sky, distant gas flares",
        "composition":  "wide establishing shot, subject dominant left, open sky right",
        "color_system": "warm amber-rust tones on metal surfaces, cool gray background",
    },
    "shipping_geopolitics": {
        "main_subject": "stacked shipping containers at a deep-water port, crane silhouettes overhead",
        "environment":  "calm harbor water, low overcast sky, distant coastline",
        "composition":  "converging perspective lines leading to a distant cargo vessel",
        "color_system": "steel blue accents on container markings, muted rust on crane structures",
    },
    "trade_supply_chain": {
        "main_subject": "a deserted customs checkpoint or sealed cargo gate, barrier arm raised",
        "environment":  "long industrial road extending to horizon, flat terrain, harsh midday light",
        "composition":  "central vanishing point, subject slightly off-axis",
        "color_system": "muted ochre on road markings, cool gray on barrier and infrastructure",
    },
    "macro_inflation": {
        "main_subject": "central bank building exterior, stone columns and carved inscriptions",
        "environment":  "empty stone plaza, overcast sky, no figures",
        "composition":  "low angle, subject monumental in foreground, sky dominant in background",
        "color_system": "warm stone tones on architecture, cool gray sky and deep shadows",
    },
    "policy_institutional": {
        "main_subject": "government building facade with national flags, closed heavy ceremonial doors",
        "environment":  "empty plaza with long shadow geometry, overcast diffuse light",
        "composition":  "frontal near-symmetrical framing broken by slight camera offset",
        "color_system": "muted flag accent colors, predominantly graphite and stone gray",
    },
    "markets_finance": {
        "main_subject": "financial district tower atrium viewed from below, glass and steel geometry",
        "environment":  "interior architectural space, receding perspective, diffuse ambient light",
        "composition":  "upward diagonal vanishing point, strong perspective, open upper frame",
        "color_system": "cool steel blue on glass surfaces, warm amber on structural elements",
    },
}

# ── Concept tag inference ─────────────────────────────────────────────────────
# Maps (category, subject keyword) -> concept_tag.
# First matching keyword wins. Falls back to "{category}_general".

_CONCEPT_KEYWORD_MAP: Dict[str, Dict[str, str]] = {
    "energy": {
        "refinery": "industrial_cluster",
        "tower":    "industrial_cluster",
        "chimney":  "industrial_cluster",
        "flare":    "industrial_cluster",
        "pipeline": "pipeline_infrastructure",
        "valve":    "pipeline_infrastructure",
        "pipe":     "pipeline_infrastructure",
        "offshore": "offshore_platform",
        "platform": "offshore_platform",
        "rig":      "offshore_platform",
        "storage":  "storage_facility",
        "tank":     "storage_facility",
    },
    "shipping_geopolitics": {
        "container": "container_logistics",
        "crane":     "container_logistics",
        "vessel":    "maritime_passage",
        "ship":      "maritime_passage",
        "tanker":    "maritime_passage",
        "port":      "port_infrastructure",
        "harbor":    "port_infrastructure",
        "dock":      "port_infrastructure",
        "strait":    "maritime_chokepoint",
        "channel":   "maritime_chokepoint",
    },
    "trade_supply_chain": {
        "checkpoint": "restriction_barrier",
        "barrier":    "restriction_barrier",
        "gate":       "restriction_barrier",
        "customs":    "restriction_barrier",
        "warehouse":  "logistics_hub",
        "depot":      "logistics_hub",
        "road":       "transit_corridor",
        "highway":    "transit_corridor",
    },
    "macro_inflation": {
        "bank":        "institutional_facade",
        "central":     "institutional_facade",
        "column":      "institutional_facade",
        "inscription": "institutional_facade",
        "trading":     "trading_floor",
        "floor":       "trading_floor",
        "ticker":      "market_data_display",
        "screen":      "market_data_display",
    },
    "policy_institutional": {
        "government":  "government_building",
        "parliament":  "government_building",
        "congress":    "government_building",
        "flag":        "government_building",
        "chamber":     "legislative_chamber",
        "legislature": "legislative_chamber",
        "plaza":       "empty_plaza",
        "steps":       "monumental_steps",
    },
    "markets_finance": {
        "atrium":    "financial_atrium",
        "tower":     "financial_atrium",
        "exchange":  "exchange_floor",
        "trading":   "exchange_floor",
        "terminal":  "data_terminal",
        "screen":    "data_terminal",
        "district":  "capital_flow_map",
        "skyline":   "capital_flow_map",
    },
}


def infer_concept_tag(category: str, main_subject: str) -> str:
    """
    Derive a concept_tag from category + main_subject using keyword matching.
    Returns "{category}_general" if no keyword matches.
    """
    subject_lower = main_subject.lower()
    for keyword, tag in _CONCEPT_KEYWORD_MAP.get(category, {}).items():
        if keyword in subject_lower:
            return tag
    return f"{category}_general"


# ── Variation resolver ────────────────────────────────────────────────────────

def resolve_variation_code(code: Optional[str]) -> Optional[str]:
    """
    Translate a variation code like 'B-2-ii-gamma' into readable prompt instructions.
    Returns None for empty, None, or malformed codes.
    Unknown component keys are silently skipped.
    """
    if not code:
        return None
    parts = [p.strip() for p in code.split("-")]
    if len(parts) != 4:
        return None
    comp_key, fg_key, bg_key, color_key = parts
    instructions = []
    if comp_key in COMPOSITION_PRESETS:
        instructions.append(f"Composition: {COMPOSITION_PRESETS[comp_key]}")
    if fg_key in FOREGROUND_PRESETS:
        instructions.append(f"Foreground hierarchy: {FOREGROUND_PRESETS[fg_key]}")
    if bg_key in BACKGROUND_PRESETS:
        instructions.append(f"Background density: {BACKGROUND_PRESETS[bg_key]}")
    if color_key in COLOR_PRESETS:
        instructions.append(f"Color emphasis: {COLOR_PRESETS[color_key]}")
    return "; ".join(instructions) if instructions else None


# ── Novelty suggestion ────────────────────────────────────────────────────────

def suggest_novelty_request(
    category: str,
    recent_history: List[Dict],
    escalation_level: int = 1,
    concept_tag_freq: Optional[Dict[str, int]] = None,
    subject_family_freq: Optional[Dict[str, int]] = None,
    composition_freq: Optional[Dict[str, int]] = None,
) -> str:
    """
    Generate a novelty request. Escalation levels 0-3:

    0 = minor composition tweaks (auto-applied on first generation if no manual novelty set)
    1 = composition + hierarchy change (first retry)
    2 = subject arrangement + metaphor shift; concept/subject/composition-aware (second retry)
    3 = full conceptual shift — new metaphor, new structure, new environment (third retry)

    Frequency dicts (concept_tag_freq, subject_family_freq, composition_freq) add avoidance
    clauses for any value appearing 3+ times.
    """
    n = len(recent_history)
    label = category.replace("_", " ")

    # Build concept avoidance clause (overused concept tags, threshold: 3+)
    concept_clause = ""
    if concept_tag_freq:
        overused = [tag for tag, count in concept_tag_freq.items() if count >= 3]
        if overused:
            tag_list = " or ".join(f'"{t.replace("_", " ")}"' for t in overused[:3])
            concept_clause = f" Explicitly avoid repeating visual metaphors such as {tag_list}."

    # Build subject avoidance clause (overused subject families, threshold: 3+)
    subject_clause = ""
    if subject_family_freq:
        overused_sf = [sf for sf, count in subject_family_freq.items() if count >= 3]
        if overused_sf:
            sf_list = " or ".join(f'"{s.replace("_", " ")}"' for s in overused_sf[:2])
            subject_clause = f" Do not use {sf_list} as the dominant subject."

    # Build composition avoidance clause (overused compositions, threshold: 3+)
    comp_clause = ""
    if composition_freq:
        overused_cp = [cp for cp, count in composition_freq.items() if count >= 3]
        if overused_cp:
            cp_list = " or ".join(f'"{c.replace("_", " ")}"' for c in overused_cp[:2])
            comp_clause = f" Avoid {cp_list} layout."

    # At level 3, also mention the most recently used subject_family and composition_preset
    most_recent_clause = ""
    if escalation_level >= 3 and recent_history:
        latest = recent_history[0]
        latest_sf = latest.get("subject_family")
        latest_cp = latest.get("composition_preset")
        parts = []
        if latest_sf:
            parts.append(f'"{latest_sf.replace("_", " ")}" as main subject')
        if latest_cp:
            parts.append(f'"{latest_cp.replace("_", " ")}" composition')
        if parts:
            most_recent_clause = f" Most recent image used {' and '.join(parts)} — use neither."

    if escalation_level == 0:
        return (
            f"Apply minor compositional variation relative to recent {label} images. "
            "Adjust framing, subject placement, or implied depth — keep the general metaphor."
        )
    if escalation_level == 1:
        return (
            f"Avoid repeating visual metaphors from the last {min(n, 4)} {label} images. "
            "Introduce a different foreground subject and spatial relationship."
            + concept_clause + subject_clause + comp_clause
        )
    if escalation_level == 2:
        return (
            f"Avoid resemblance to the last {min(n, 6)} {label} images. "
            "Change foreground object count, composition balance, and dominant visual metaphor. "
            "Use a different environmental setting and implied time of day."
            + concept_clause + subject_clause + comp_clause
        )
    # Level 3+
    return (
        f"Strong novelty required: avoid any resemblance to the last {min(n, 8)} {label} images "
        "and the 4 most recent global images across all categories. "
        "Use a completely different foreground subject, opposite compositional balance, "
        "new spatial hierarchy, and a distinct environmental context. "
        "If recent images used exterior settings, use interior. "
        "If recent images used horizontal framing, use strong vertical emphasis."
        + concept_clause + subject_clause + comp_clause + most_recent_clause
    )


# ── Main assembler ────────────────────────────────────────────────────────────

def build_image_prompt(
    category: str,
    main_subject: str,
    environment: str,
    composition: str,
    color_system: str,
    context: Optional[str] = None,
    novelty_request: Optional[str] = None,
    variation_code: Optional[str] = None,
) -> str:
    """
    Assemble the final image prompt.

    Block order (fixed — do not reorder):
        1. style_master    — fixed visual identity, subject placeholders filled
        2. category_block  — domain anchor for the editorial category
        3. context_block   — optional editorial context (headline, event)
        4. variation_block — optional variation code instructions
        5. novelty_block   — optional novelty directive (always last)
    """
    prompt = STYLE_MASTER.format(
        MAIN_SUBJECT=main_subject,
        ENVIRONMENT=environment,
        COMPOSITION=composition,
        COLOR_SYSTEM=color_system,
    )

    category_hint = CATEGORY_BLOCKS.get(category, "")
    if category_hint:
        prompt += f" {category_hint}."

    if context:
        prompt += f" Editorial context: {context}."

    variation_text = resolve_variation_code(variation_code)
    if variation_text:
        prompt += f" Variation instructions: {variation_text}."

    if novelty_request:
        prompt += f" Novelty directive: {novelty_request}"

    return prompt
