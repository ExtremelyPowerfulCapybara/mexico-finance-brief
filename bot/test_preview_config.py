# bot/test_preview_config.py
import importlib
import os
import sys


def _reload_config(preview: bool):
    """Set PREVIEW_MODE and reload config, return the module."""
    if preview:
        os.environ["PREVIEW_MODE"] = "true"
    else:
        os.environ.pop("PREVIEW_MODE", None)
    if "config" in sys.modules:
        del sys.modules["config"]
    import config
    return config


def test_default_paths_do_not_contain_preview():
    cfg = _reload_config(preview=False)
    assert "preview" not in cfg.DIGEST_DIR
    assert "preview" not in cfg.ARCHIVE_DIR
    assert cfg.DIGEST_DIR.endswith("digests")
    assert cfg.ARCHIVE_DIR.endswith("docs")


def test_preview_mode_switches_to_preview_subfolders():
    cfg = _reload_config(preview=True)
    assert cfg.DIGEST_DIR.endswith("digests/preview") or cfg.DIGEST_DIR.endswith("digests\\preview")
    assert cfg.ARCHIVE_DIR.endswith("docs/preview") or cfg.ARCHIVE_DIR.endswith("docs\\preview")


def test_preview_subfolders_are_children_of_repo_root():
    cfg = _reload_config(preview=True)
    import pathlib
    repo_root = pathlib.Path(cfg.REPO_ROOT)
    assert pathlib.Path(cfg.DIGEST_DIR).parent == repo_root / "digests"
    assert pathlib.Path(cfg.ARCHIVE_DIR).parent == repo_root / "docs"


if __name__ == "__main__":
    test_default_paths_do_not_contain_preview()
    test_preview_mode_switches_to_preview_subfolders()
    test_preview_subfolders_are_children_of_repo_root()
    print("All tests passed.")
