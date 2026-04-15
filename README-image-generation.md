# Editorial Image Generation — README

A self-contained subsystem for **The Opening Bell** newsletter that generates editorial images
with automatic deduplication across issues, using perceptual hashing and prompt similarity.

---

## Overview

The system prevents repeated images by:
1. **Concept tagging** — each image is tagged with a visual metaphor label (e.g. `industrial_cluster`). Overused tags are detected and avoided in novelty directives.
2. **Two-phase image similarity** — phash compared against recent same-category images (last 15) then all recent global images (last 50). Only image similarity triggers rejection.
3. **Text monitoring** — TF-IDF cosine similarity flags risky prompts but does not reject on its own. The `accepted_prompt` (revised_prompt when available) is always used for comparison.
4. **Automatic escalation** — levels 0–3. Level 0 = minor tweak; level 3 = full conceptual shift. Escalation advances on each failed attempt.
5. **Attempt tracking** — every API call is logged in `generation_attempts` with accepted/rejected status and rejection reason.

---

## File Structure

```
lib/
  image_prompt_builder.py   # Prompt assembly, variation resolver, concept tagging, escalation 0-3
  image_history_store.py    # SQLite: image_history + generation_attempts tables
  image_similarity.py       # Two-phase phash + TF-IDF comparison
  image_generator.py        # Pipeline orchestrator with deduplication loop
  tests/
    test_image_prompt_builder.py
    test_image_history_store.py
    test_image_similarity.py
    test_image_generator.py

scripts/
  generate_editorial_image.py   # CLI entry point

data/
  image_history.db          # SQLite DB (auto-created on first run)
```

---

## Setup

Install dependencies:
```bash
pip install -r requirements.txt
```

New packages required: `imagehash`, `scikit-learn` (added to `requirements.txt`).

Set your OpenAI API key:
```bash
export OPENAI_API_KEY=sk-...
```

Or create a `bot/.env` file and it will be loaded automatically by the CLI.

---

## Quick Start

```bash
python scripts/generate_editorial_image.py \
  --issue-date 2026-04-15 \
  --story-slug mexico-energy-reform \
  --category energy \
  --main-subject "oil refinery towers at dusk" \
  --environment "flat industrial horizon, overcast sky" \
  --composition "wide establishing shot, subject dominant left" \
  --color-system "warm amber-rust tones on metal"
```

---

## CLI Reference

### Required flags (for generation)

| Flag | Description |
|------|-------------|
| `--issue-date` | Issue date in YYYY-MM-DD format |
| `--story-slug` | Short identifier for the story (used in filename) |
| `--category` | Editorial category (see `--list-presets` for options) |
| `--main-subject` | Main subject description |
| `--environment` | Environment/setting |
| `--composition` | Composition instruction |
| `--color-system` | Color accent system |

### Optional flags

| Flag | Default | Description |
|------|---------|-------------|
| `--context` | None | Editorial context (headline, event) injected into prompt |
| `--novelty-request` | None | Manual novelty directive (overrides auto-escalation) |
| `--variation-code` | None | Variation code e.g. `B-2-ii-gamma` |
| `--concept-tag` | inferred | Override inferred concept tag |
| `--force-novelty-level` | None | Apply escalation level {0,1,2,3} from attempt 0 |
| `--max-retries` | 3 | Maximum regeneration attempts on phash rejection |
| `--text-threshold` | 0.82 | TF-IDF cosine threshold for text risk flag |
| `--phash-threshold` | 8 | Hamming distance threshold for image rejection |
| `--output-dir` | `generated_images/` | Directory for generated PNGs |
| `--db-path` | `data/image_history.db` | SQLite DB path |
| `--dry-run` | — | Print prompt breakdown, skip API call |
| `--show-similarity-debug` | — | Print per-phase similarity scores after generation |
| `--list-presets` | — | Print category preset suggestions and exit |

---

## Concept Tags

Each generated image is assigned a **concept tag** — a short visual metaphor label that identifies what type of scene was depicted. Examples:

| Category | Concept tag | Subject keywords |
|----------|-------------|------------------|
| energy | `industrial_cluster` | refinery, tower, chimney, flare |
| energy | `pipeline_infrastructure` | pipeline, valve, pipe |
| energy | `offshore_platform` | offshore, platform, rig |
| shipping_geopolitics | `container_logistics` | container, crane |
| shipping_geopolitics | `port_infrastructure` | port, harbor, dock |
| trade_supply_chain | `restriction_barrier` | checkpoint, barrier, gate, customs |
| macro_inflation | `institutional_facade` | bank, central, column, inscription |
| markets_finance | `financial_atrium` | atrium, tower |

Concept tags are inferred automatically from `main_subject` via keyword matching. Use `--concept-tag` to override.

When the same concept tag appears 3 or more times in recent category history, the novelty directive at escalation level 2+ explicitly names the overused tags to avoid.

---

## Variation Codes

Format: `[COMPOSITION]-[FOREGROUND]-[BACKGROUND]-[COLOR]`

Example: `B-2-ii-gamma`

| Component | Keys | Examples |
|-----------|------|---------|
| Composition | A–E | A=centered, B=left-weighted, C=right-weighted, D=diagonal, E=split-frame |
| Foreground | 1–4 | 1=single subject, 2=dual tension, 3=scattered, 4=frame-within-frame |
| Background | i–iv | i=minimal, ii=moderate, iii=rich, iv=complex |
| Color | alpha–epsilon | alpha=warm earth, beta=cool slate, gamma=monochrome, delta=sepia, epsilon=single accent |

---

## Escalation Levels

| Level | Trigger | Directive |
|-------|---------|-----------|
| 0 | First attempt (optional) | Minor framing/placement variation |
| 1 | First retry (phash rejected) | Different foreground subject and spatial relationship |
| 2 | Second retry | New environmental setting, different metaphor; concept-aware |
| 3 | Third retry | Full conceptual shift — new subject, opposite balance, new environment |

---

## Database Schema

Two SQLite tables in `data/image_history.db`:

**`image_history`** — one row per accepted generation:
`id`, `created_at`, `issue_date`, `story_slug`, `category`, `prompt_master_version`, `prompt_sent`, `revised_prompt`, `accepted_prompt`, `variation_code`, `novelty_request`, `concept_tag`, `image_path`, `image_phash`, `similarity_score_text`, `similarity_score_image`, `regeneration_count`, `notes`

**`generation_attempts`** — one row per API call (including rejected):
`id`, `parent_image_id`, `created_at`, `prompt_sent`, `revised_prompt`, `accepted`, `rejection_reason`, `image_phash`, `similarity_score_text`, `similarity_score_image`

---

## Environment Variables

| Variable | Description |
|----------|-------------|
| `OPENAI_API_KEY` | Required for generation |
| `OPENAI_IMAGE_MODEL` | Default: `gpt-image-1` |
| `OPENAI_IMAGE_SIZE` | Default: `1024x1024` |
| `OPENAI_IMAGE_QUALITY` | Default: `medium` |
| `OPENAI_USE_RESPONSES_API` | `true` (default) uses Responses API; `false` uses Images API directly |
| `OPENAI_RESPONSES_MODEL` | Default: `gpt-4o` |
| `IMAGE_HISTORY_DB` | Override default DB path |

---

## Running Tests

```bash
python -m pytest lib/tests/ -v
```

Expected: 64 tests pass (13 store + 24 builder + 16 similarity + 11 generator).
