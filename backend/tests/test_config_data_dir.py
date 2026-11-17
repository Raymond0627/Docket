"""Tests for the stable data directory used by the packaged (frozen) app.

The packaged app must keep its data (settings.json, rules.json, docket.db,
outputs, temp_intake) OUT of the exe/build folder, because PyInstaller wipes
that folder on every rebuild.
"""
import importlib
import sys
from pathlib import Path


def _enter_frozen(monkeypatch, tmp_path):
    """Simulate running as the packaged exe with cwd = exe folder."""
    exe_dir = tmp_path / "exe_dir"
    exe_dir.mkdir(parents=True, exist_ok=True)
    appdata = tmp_path / "AppData"
    monkeypatch.setenv("LOCALAPPDATA", str(appdata))
    monkeypatch.chdir(exe_dir)
    # sys.frozen / sys._MEIPASS are managed here (not via monkeypatch) because
    # the module must be reloaded with them removed during teardown.
    saved = {}
    for attr in ("frozen", "_MEIPASS"):
        saved[attr] = (hasattr(sys, attr), getattr(sys, attr, None))
    sys.frozen = True
    sys._MEIPASS = str(tmp_path / "_meipass")
    import backend.config as config
    importlib.reload(config)
    return config, exe_dir, appdata, saved


def _exit_frozen(config, saved=None):
    """Restore the module to its normal (non-frozen) state."""
    for attr in ("frozen", "_MEIPASS"):
        existed, value = (saved or {}).get(attr, (False, None))
        if existed:
            setattr(sys, attr, value)
        elif hasattr(sys, attr):
            delattr(sys, attr)
    importlib.reload(config)


def test_frozen_user_dir_is_stable_appdata_dir(monkeypatch, tmp_path):
    import backend.config as config
    cfg, exe_dir, appdata, saved = _enter_frozen(monkeypatch, tmp_path)
    try:
        assert cfg.USER_DIR == appdata / "Docket", (
            f"frozen USER_DIR must be the stable data dir, got {cfg.USER_DIR}"
        )
        assert cfg.USER_DIR.is_dir()
        assert cfg.USER_DIR != exe_dir
        assert cfg.SETTINGS_FILE == cfg.USER_DIR / "settings.json"
        assert cfg.DB_FILE == cfg.USER_DIR / "docket.db"
    finally:
        _exit_frozen(cfg, saved)


def test_frozen_migrates_legacy_data_files(monkeypatch, tmp_path):
    import backend.config as config
    cfg, exe_dir, appdata, saved = _enter_frozen(monkeypatch, tmp_path)
    try:
        # Legacy data sitting next to the exe must be copied to the data dir
        (exe_dir / "settings.json").write_text(
            '{"gemini_api_key": "legacy-key"}', encoding="utf-8"
        )
        (exe_dir / "docket.db").write_bytes(b"legacy-db-bytes")
        importlib.reload(cfg)

        assert (cfg.USER_DIR / "settings.json").read_text(encoding="utf-8") == (
            '{"gemini_api_key": "legacy-key"}'
        )
        assert (cfg.USER_DIR / "docket.db").read_bytes() == b"legacy-db-bytes"
    finally:
        _exit_frozen(cfg, saved)


def test_frozen_migration_never_overwrites_existing_data(monkeypatch, tmp_path):
    import backend.config as config
    cfg, exe_dir, appdata, saved = _enter_frozen(monkeypatch, tmp_path)
    try:
        (cfg.USER_DIR / "settings.json").write_text(
            '{"current": true}', encoding="utf-8"
        )
        (exe_dir / "settings.json").write_text('{"stale": true}', encoding="utf-8")
        importlib.reload(cfg)

        assert (cfg.USER_DIR / "settings.json").read_text(encoding="utf-8") == (
            '{"current": true}'
        ), "migration must never overwrite existing data"
    finally:
        _exit_frozen(cfg, saved)


def test_resolve_data_path_frozen_relative_anchors_to_data_dir(monkeypatch, tmp_path):
    import backend.config as config
    cfg, exe_dir, appdata, saved = _enter_frozen(monkeypatch, tmp_path)
    try:
        assert cfg.resolve_data_path("./Docket_Output") == (
            cfg.USER_DIR / "Docket_Output"
        ).resolve()
        assert cfg.resolve_data_path("./temp_intake") == (
            cfg.USER_DIR / "temp_intake"
        ).resolve()
        # absolute paths are respected as-is
        abs_p = tmp_path / "elsewhere" / "out"
        assert cfg.resolve_data_path(str(abs_p)) == abs_p.resolve()
    finally:
        _exit_frozen(cfg, saved)


def test_resolve_data_path_non_frozen_keeps_cwd_behavior(monkeypatch, tmp_path):
    """Dev runs (python desktop.py) keep today's cwd-relative behavior."""
    import backend.config as config
    _exit_frozen(config)
    monkeypatch.chdir(tmp_path)
    assert config.resolve_data_path("./Docket_Output") == (
        tmp_path / "Docket_Output"
    ).resolve()
    abs_p = tmp_path / "abs" / "out"
    assert config.resolve_data_path(str(abs_p)) == abs_p.resolve()
