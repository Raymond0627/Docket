import sys
import os
import shutil
import json
from pathlib import Path
from backend.models import AppSettings, RuleDefinition

# Data files the packaged app used to store next to the exe (which PyInstaller
# wipes on every rebuild). These are migrated to the stable data dir on startup.
LEGACY_DATA_FILES = ("settings.json", "rules.json", "docket.db")

if getattr(sys, 'frozen', False):
    RESOURCE_DIR = Path(sys._MEIPASS) / "backend"
    # Stable data directory for the packaged app. Deliberately NOT the exe
    # folder and not the cwd: rebuilds must never be able to delete user data.
    USER_DIR = Path(os.environ.get("LOCALAPPDATA") or str(Path.home())) / "Docket"
    USER_DIR.mkdir(parents=True, exist_ok=True)
    # One-time migration: copy legacy files from the launch folder, but NEVER
    # overwrite anything that already exists in the data dir.
    _legacy_dir = Path.cwd()
    if _legacy_dir != USER_DIR:
        for _name in LEGACY_DATA_FILES:
            _src, _dst = _legacy_dir / _name, USER_DIR / _name
            if _src.is_file() and not _dst.exists():
                try:
                    shutil.copy2(_src, _dst)
                except OSError:
                    pass
else:
    RESOURCE_DIR = Path(__file__).resolve().parent
    USER_DIR = RESOURCE_DIR

SETTINGS_FILE = USER_DIR / "settings.json"
RULES_FILE = USER_DIR / "rules.json"
DEFAULT_RULES_FILE = RESOURCE_DIR / "rules.json"
DB_FILE = USER_DIR / "docket.db"

def load_settings() -> AppSettings:
    if SETTINGS_FILE.exists():
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return AppSettings(**data)
        except Exception:
            pass
    return AppSettings()

def save_settings(settings: AppSettings) -> None:
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings.model_dump(), f, indent=2)

def load_rules() -> list[RuleDefinition]:
    # Check user rules first
    target_file = RULES_FILE if RULES_FILE.exists() else DEFAULT_RULES_FILE
    if target_file.exists():
        try:
            with open(target_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return [RuleDefinition(**item) for item in data]
        except Exception:
            pass
    return []

def save_rules(rules: list[RuleDefinition]) -> None:
    with open(RULES_FILE, "w", encoding="utf-8") as f:
        json.dump([r.model_dump() for r in rules], f, indent=2)

def resolve_data_path(path_str) -> Path:
    """Resolve a data path (output folder, temp intake, ...).

    - Absolute paths are respected as-is.
    - In the packaged app, relative paths are anchored to the stable data dir
      (LOCALAPPDATA\\Docket) so a rebuild of the exe folder can never delete them.
    - In dev runs, relative paths keep resolving against the current working
      directory (unchanged behavior).
    """
    p = Path(path_str)
    if p.is_absolute() or not getattr(sys, "frozen", False):
        return p.resolve()
    return (USER_DIR / p).resolve()
