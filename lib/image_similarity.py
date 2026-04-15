# lib/image_similarity.py
# ─────────────────────────────────────────────
#  Text similarity: TF-IDF cosine via scikit-learn.
#  Image similarity: perceptual hashing (phash) via imagehash.
#
#  Two-phase comparison:
#    Phase 1 — recent CATEGORY records (last 15 by default)
#    Phase 2 — recent GLOBAL records (last 50 by default)
#
#  Rejection logic:
#    phash distance < threshold (either phase) → image_flagged = True → flagged = True
#    text similarity > threshold               → text_risky = True  (not a rejection)
#
#  accepted_prompt field is preferred for text comparison;
#  falls back to revised_prompt, then prompt_sent.
# ─────────────────────────────────────────────

from typing import Dict, List, Optional

import numpy as np

DEFAULT_TEXT_THRESHOLD: float = 0.82
DEFAULT_PHASH_THRESHOLD: int = 8


def compute_phash(image_path: str) -> Optional[str]:
    """Compute perceptual hash for an image. Returns hex string or None on failure."""
    try:
        import imagehash
        from PIL import Image
        return str(imagehash.phash(Image.open(image_path)))
    except Exception as exc:
        print(f"  [similarity] phash failed for '{image_path}': {exc}")
        return None


def phash_distance(hash_a: str, hash_b: str) -> int:
    """
    Hamming distance between two phash hex strings.
    0 = identical, 64 = maximally different. Returns 64 on parse failure.
    """
    try:
        import imagehash
        return imagehash.hex_to_hash(hash_a) - imagehash.hex_to_hash(hash_b)
    except Exception:
        return 64


def compute_text_similarity(prompt: str, corpus: List[str]) -> float:
    """
    Maximum TF-IDF cosine similarity between `prompt` and any text in `corpus`.
    Returns 0.0 if corpus is empty.
    """
    if not corpus:
        return 0.0
    try:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity as sk_cosine
        documents = [prompt] + corpus
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1)
        matrix = vectorizer.fit_transform(documents)
        sims = sk_cosine(matrix[0:1], matrix[1:]).flatten()
        return float(np.max(sims))
    except Exception as exc:
        print(f"  [similarity] text similarity error: {exc}")
        return 0.0


def _best_text(record: Dict) -> str:
    """Extract best available prompt text from a history record."""
    return (
        record.get("accepted_prompt")
        or record.get("revised_prompt")
        or record.get("prompt_sent")
        or ""
    )


def _min_phash_vs_records(new_phash: str, records: List[Dict]) -> int:
    """Return minimum Hamming distance between new_phash and all stored hashes."""
    min_dist = 64
    for r in records:
        stored = r.get("image_phash")
        if stored:
            min_dist = min(min_dist, phash_distance(new_phash, stored))
    return min_dist


def check_against_history(
    prompt: str,
    image_path: Optional[str],
    category_records: List[Dict],
    global_records: List[Dict],
    text_threshold: float = DEFAULT_TEXT_THRESHOLD,
    phash_threshold: int = DEFAULT_PHASH_THRESHOLD,
) -> Dict:
    """
    Two-phase similarity check.

    Phase 1: compare against category_records (same category, last 15)
    Phase 2: compare against global_records (all categories, last 50)

    IMAGE similarity is the sole rejection criterion (flagged = image_flagged).
    TEXT similarity above threshold sets text_risky=True but does NOT reject.

    Returns:
        text_similarity          float  — max cosine vs all records combined
        text_risky               bool   — True if text_similarity > text_threshold
        category_min_phash_distance  int
        global_min_phash_distance    int
        min_phash_distance       int    — min of both phases
        image_similarity         float  — 1 - (min_phash_distance / 64)
        image_flagged            bool   — True if min_phash_distance < threshold
        rejection_reason         str|None — "phash_too_close_category" | "phash_too_close_global" | None
        flagged                  bool   — True only if image_flagged
        new_phash                str    — phash of the new image (if computed)
    """
    result: Dict = {
        "text_similarity": 0.0,
        "text_risky": False,
        "category_min_phash_distance": 64,
        "global_min_phash_distance": 64,
        "min_phash_distance": 64,
        "image_similarity": 0.0,
        "image_flagged": False,
        "rejection_reason": None,
        "flagged": False,
    }

    # Text similarity — combined corpus (category + global)
    all_records = category_records + global_records
    corpus = [_best_text(r) for r in all_records if _best_text(r)]
    if corpus:
        text_sim = compute_text_similarity(prompt, corpus)
        result["text_similarity"] = text_sim
        result["text_risky"] = text_sim > text_threshold

    # Perceptual hash — two-phase
    if image_path:
        new_phash = compute_phash(image_path)
        if new_phash:
            result["new_phash"] = new_phash

            cat_dist = _min_phash_vs_records(new_phash, category_records)
            glob_dist = _min_phash_vs_records(new_phash, global_records)
            result["category_min_phash_distance"] = cat_dist
            result["global_min_phash_distance"] = glob_dist
            result["min_phash_distance"] = min(cat_dist, glob_dist)
            result["image_similarity"] = 1.0 - (result["min_phash_distance"] / 64.0)

            if cat_dist < phash_threshold:
                result["image_flagged"] = True
                result["rejection_reason"] = "phash_too_close_category"
            elif glob_dist < phash_threshold:
                result["image_flagged"] = True
                result["rejection_reason"] = "phash_too_close_global"

    result["flagged"] = result["image_flagged"]
    return result
