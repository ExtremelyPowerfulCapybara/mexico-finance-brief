"""
Tests for display hierarchy changes in renderer.py.

Run from bot/ directory:
  python tests/test_display_hierarchy.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from renderer import _narrative_thread, FONT_SERIF, TEXT_LIGHT

def test_narrative_thread_empty_returns_empty():
    """Empty text must return empty string."""
    assert _narrative_thread("") == ""
    assert _narrative_thread(None) == ""

def test_narrative_thread_has_hilo_label():
    """Rendered output must include HILO DEL DÍA label."""
    html = _narrative_thread("La Fed y el peso recalibran el ciclo.")
    assert "HILO DEL D" in html, "Must include 'HILO DEL DÍA' label"

def test_narrative_thread_uses_serif_font():
    """Pull quote text must use the serif font for italic style."""
    html = _narrative_thread("La Fed y el peso recalibran el ciclo.")
    assert FONT_SERIF in html, "Pull quote text must use FONT_SERIF"

def test_narrative_thread_centered():
    """Pull quote must be center-aligned."""
    html = _narrative_thread("La Fed y el peso recalibran el ciclo.")
    assert "text-align:center" in html.replace(" ", ""), "Pull quote must be centered"

def test_narrative_thread_no_left_border():
    """Old border-left style must not appear."""
    html = _narrative_thread("La Fed y el peso recalibran el ciclo.")
    assert "border-left" not in html, "Old border-left style must not appear"

def test_narrative_thread_text_present():
    """The supplied text must appear in the output."""
    html = _narrative_thread("La Fed y el peso recalibran el ciclo.")
    assert "La Fed y el peso recalibran el ciclo." in html

if __name__ == "__main__":
    tests = [
        test_narrative_thread_empty_returns_empty,
        test_narrative_thread_has_hilo_label,
        test_narrative_thread_uses_serif_font,
        test_narrative_thread_centered,
        test_narrative_thread_no_left_border,
        test_narrative_thread_text_present,
    ]
    passed = 0
    for t in tests:
        try:
            t()
            print(f"  PASS  {t.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"  FAIL  {t.__name__}: {e}")
    print(f"\n{passed}/{len(tests)} passed")
