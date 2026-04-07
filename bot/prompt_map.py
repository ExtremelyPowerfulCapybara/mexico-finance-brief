# bot/prompt_map.py
# ─────────────────────────────────────────────
#  Prompt templates for hero image generation.
#  Each template corresponds to one of the 8
#  Claude story tags. Fill {headline} and
#  {sentiment} at generation time via .format().
# ─────────────────────────────────────────────

_BASE = (
    "Premium editorial illustration for a high-end financial and geopolitical newsletter, "
    "hand-drawn ink and graphite style with refined linework and subtle cross-hatching, "
    "monochrome base with controlled muted color accents (20–25%), "
    "slightly textured paper background, "
    "{subject}, "
    "inspired by: {headline}, overall tone: {sentiment}, "
    "minimal composition, strong negative space, realistic proportions, "
    "calm but tense atmosphere, modern whitepaper-inspired editorial aesthetic, "
    "not photorealistic, not cinematic, no text, no logos."
)

# Three subject framings per tag for hero_options (opt1 = current default).
# Variants differ by composition, viewpoint, or emphasis — same editorial style.
PROMPT_VARIANT_SUBJECTS = {
    "Macro": [
        "a sparse government chamber or empty boardroom, muted light through tall windows",
        "a lone figure at the end of a long corridor, architectural symmetry, fading light",
        "an empty press briefing room, microphones on a bare podium, harsh overhead light",
    ],
    "FX": [
        "rows of currency exchange ticker boards, numbers blurred, deep architectural perspective",
        "a close-up of paper currency, worn edges and engraved patterns, shallow focus",
        "an empty foreign exchange trading desk, dormant screens, cable shadows on the floor",
    ],
    "México": [
        "Mexico City skyline at dusk, Torre Mayor silhouette, low clouds, empty boulevard below",
        "a colonial arcade in a Mexican city center, stone arches, receding perspective, no figures",
        "Popocatepetl silhouette at dawn, atmospheric haze, flat valley below, minimal foreground",
    ],
    "Comercio": [
        "stacked shipping containers at a port, cranes overhead, calm water, no figures",
        "a close-up of container lock mechanisms and stencilled codes, abstract texture, flat light",
        "a deserted customs checkpoint, barrier raised, long road ahead, harsh midday sun",
    ],
    "Tasas": [
        "central bank building exterior, stone columns, overcast sky, empty stone steps",
        "close-up of a marble facade inscription, deep shadow relief, monumental scale",
        "an empty meeting room with a long table, name placards face-down, diffuse window light",
    ],
    "Mercados": [
        "stock exchange trading floor, screens with data, long perspective shot, no people",
        "a close-up of a trading terminal screen edge, reflections blurred, dim ambient light",
        "an atrium of a financial district tower looking upward, glass and steel geometry",
    ],
    "Energía": [
        "oil refinery towers and storage tanks at dusk, slow smoke rising, flat horizon",
        "a close-up of industrial pipeline valves, oxidized metal, shallow depth of field",
        "offshore platform silhouette at low tide, flat sea, overcast sky, distant horizon",
    ],
    "Política": [
        "government building facade, national flags, dramatic clouds, empty plaza below",
        "a close-up of stone steps leading to heavy closed doors, shadow geometry",
        "an empty legislative chamber viewed from the gallery, tiered seats, diffuse light",
    ],
}

PROMPT_TEMPLATES = {
    "Macro": _BASE.format(
        subject="a sparse government chamber or empty boardroom, muted light through tall windows",
        headline="{headline}",
        sentiment="{sentiment}",
    ),
    "FX": _BASE.format(
        subject="rows of currency exchange ticker boards, numbers blurred, deep architectural perspective",
        headline="{headline}",
        sentiment="{sentiment}",
    ),
    "México": _BASE.format(
        subject="Mexico City skyline at dusk, Torre Mayor silhouette, low clouds, empty boulevard below",
        headline="{headline}",
        sentiment="{sentiment}",
    ),
    "Comercio": _BASE.format(
        subject="stacked shipping containers at a port, cranes overhead, calm water, no figures",
        headline="{headline}",
        sentiment="{sentiment}",
    ),
    "Tasas": _BASE.format(
        subject="central bank building exterior, stone columns, overcast sky, empty stone steps",
        headline="{headline}",
        sentiment="{sentiment}",
    ),
    "Mercados": _BASE.format(
        subject="stock exchange trading floor, screens with data, long perspective shot, no people",
        headline="{headline}",
        sentiment="{sentiment}",
    ),
    "Energía": _BASE.format(
        subject="oil refinery towers and storage tanks at dusk, slow smoke rising, flat horizon",
        headline="{headline}",
        sentiment="{sentiment}",
    ),
    "Política": _BASE.format(
        subject="government building facade, national flags, dramatic clouds, empty plaza below",
        headline="{headline}",
        sentiment="{sentiment}",
    ),
}
