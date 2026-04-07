# bot/tests/test_telegram_handler.py
import os
import json
import shutil
import tempfile
import pytest
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


def _make_test_env(tmp):
    """Return (digest_dir, archive_dir, tmp_images_dir) under tmp."""
    digest_dir  = os.path.join(tmp, "digests")
    archive_dir = os.path.join(tmp, "docs")
    tmp_img_dir = os.path.join(tmp, "tmp_images")
    for d in (digest_dir, archive_dir, tmp_img_dir):
        os.makedirs(d, exist_ok=True)
    return digest_dir, archive_dir, tmp_img_dir


def _write_digest(digest_dir, issue_date, visual):
    data = {"digest": {}, "visual": visual}
    path = os.path.join(digest_dir, f"{issue_date}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f)
    return path


def _make_fake_png(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)  # minimal fake PNG header


# ── _handle_select tests ──────────────────────

def test_handle_select_copies_file_and_updates_digest():
    from telegram_handler import _handle_select

    with tempfile.TemporaryDirectory() as tmp:
        digest_dir, archive_dir, tmp_img_dir = _make_test_env(tmp)

        cand_path = os.path.join(tmp_img_dir, "2026-04-07", "r1_opt2.png")
        _make_fake_png(cand_path)

        visual = {
            "hero_options": {"opt1": "p1", "opt2": "p2", "opt3": "p3"},
            "hero_image_candidates": {
                "opt1": os.path.join(tmp_img_dir, "2026-04-07", "r1_opt1.png"),
                "opt2": cand_path,
                "opt3": os.path.join(tmp_img_dir, "2026-04-07", "r1_opt3.png"),
            },
            "hero_image": None,
        }
        digest_path = _write_digest(digest_dir, "2026-04-07", visual)

        with patch("telegram_handler.DIGEST_DIR", digest_dir), \
             patch("telegram_handler.ARCHIVE_DIR", archive_dir), \
             patch("telegram_handler._answer_callback"), \
             patch("telegram_handler.rerender"):
            _handle_select("tok", "cb123", "2026-04-07", "opt2")

        # Verify published image exists
        dst = os.path.join(archive_dir, "images", "2026-04-07.png")
        assert os.path.exists(dst), "Selected image must be copied to docs/images/"

        # Verify digest state
        with open(digest_path, encoding="utf-8") as f:
            saved = json.load(f)
        v = saved["visual"]
        assert v["hero_selected"] == "opt2"
        assert v["hero_image"] == "/images/2026-04-07.png"


def test_handle_select_rejects_already_locked():
    from telegram_handler import _handle_select

    with tempfile.TemporaryDirectory() as tmp:
        digest_dir, archive_dir, _ = _make_test_env(tmp)
        visual = {"hero_image": "/images/2026-04-07.png"}
        _write_digest(digest_dir, "2026-04-07", visual)

        mock_answer = MagicMock()
        with patch("telegram_handler.DIGEST_DIR", digest_dir), \
             patch("telegram_handler.ARCHIVE_DIR", archive_dir), \
             patch("telegram_handler._answer_callback", mock_answer):
            _handle_select("tok", "cb123", "2026-04-07", "opt2")

        mock_answer.assert_called_once_with("tok", "cb123", "Already locked.")


def test_handle_select_does_not_delete_src_before_copy_verified():
    """src file must still exist (not deleted) if copy fails."""
    from telegram_handler import _handle_select

    with tempfile.TemporaryDirectory() as tmp:
        digest_dir, archive_dir, tmp_img_dir = _make_test_env(tmp)

        cand_path = os.path.join(tmp_img_dir, "2026-04-07", "r1_opt1.png")
        _make_fake_png(cand_path)

        visual = {
            "hero_image_candidates": {"opt1": cand_path, "opt2": "missing.png", "opt3": "missing.png"},
            "hero_image": None,
        }
        _write_digest(digest_dir, "2026-04-07", visual)

        # Simulate copy failure by making archive_dir/images a file (not a dir)
        images_dst = os.path.join(archive_dir, "images")
        open(images_dst, "w").close()  # images is a file, makedirs will fail

        with patch("telegram_handler.DIGEST_DIR", digest_dir), \
             patch("telegram_handler.ARCHIVE_DIR", archive_dir), \
             patch("telegram_handler._answer_callback"):
            _handle_select("tok", "cb123", "2026-04-07", "opt1")

        # Source file must NOT have been deleted
        assert os.path.exists(cand_path), "Source tmp candidate must not be deleted if copy fails"


# ── _handle_regenerate tests ──────────────────

def test_handle_regenerate_increments_counters():
    from telegram_handler import _handle_regenerate

    with tempfile.TemporaryDirectory() as tmp:
        digest_dir, archive_dir, _ = _make_test_env(tmp)
        visual = {
            "hero_options": {"opt1": "p1", "opt2": "p2", "opt3": "p3"},
            "hero_image": None,
            "hero_generation_round": 1,
            "hero_regenerations_used": 0,
            "hero_image_candidates": {},
        }
        digest_path = _write_digest(digest_dir, "2026-04-07", visual)

        mock_answer = MagicMock()
        mock_gen = MagicMock(return_value={"opt1": "/p/r2_opt1.png", "opt2": "/p/r2_opt2.png", "opt3": "/p/r2_opt3.png"})

        with patch("telegram_handler.DIGEST_DIR", digest_dir), \
             patch("telegram_handler.ARCHIVE_DIR", archive_dir), \
             patch("telegram_handler._answer_callback", mock_answer), \
             patch("telegram_handler.generate_image_candidates", mock_gen), \
             patch("telegram_handler._send_candidate_photos"), \
             patch("telegram_handler._send_control_message"):
            _handle_regenerate("tok", "cb123", "2026-04-07")

        with open(digest_path, encoding="utf-8") as f:
            saved = json.load(f)

        v = saved["visual"]
        assert v["hero_generation_round"] == 2
        assert v["hero_regenerations_used"] == 1


def test_handle_regenerate_blocks_at_limit():
    from telegram_handler import _handle_regenerate

    with tempfile.TemporaryDirectory() as tmp:
        digest_dir, archive_dir, _ = _make_test_env(tmp)
        visual = {
            "hero_options": {"opt1": "p1", "opt2": "p2", "opt3": "p3"},
            "hero_image": None,
            "hero_generation_round": 3,
            "hero_regenerations_used": 2,  # at limit
        }
        _write_digest(digest_dir, "2026-04-07", visual)

        mock_answer = MagicMock()
        with patch("telegram_handler.DIGEST_DIR", digest_dir), \
             patch("telegram_handler.ARCHIVE_DIR", archive_dir), \
             patch("telegram_handler._answer_callback", mock_answer):
            _handle_regenerate("tok", "cb123", "2026-04-07")

        mock_answer.assert_called_once_with("tok", "cb123", "No more regenerations allowed.")


def test_handle_regenerate_rejects_already_locked():
    from telegram_handler import _handle_regenerate

    with tempfile.TemporaryDirectory() as tmp:
        digest_dir, archive_dir, _ = _make_test_env(tmp)
        visual = {"hero_image": "/images/2026-04-07.png"}
        _write_digest(digest_dir, "2026-04-07", visual)

        mock_answer = MagicMock()
        with patch("telegram_handler.DIGEST_DIR", digest_dir), \
             patch("telegram_handler.ARCHIVE_DIR", archive_dir), \
             patch("telegram_handler._answer_callback", mock_answer):
            _handle_regenerate("tok", "cb123", "2026-04-07")

        mock_answer.assert_called_once_with("tok", "cb123", "Already locked.")
