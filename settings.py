"""Налаштування застосунку, що зберігаються між запусками (мова, стіл принтера, нейромережа)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

DEFAULTS = {"lang": None, "bed": 180.0, "model": "large"}


def config_dir() -> Path:
    override = os.environ.get("RELIEF_PUZZLE_CONFIG_DIR")
    if override:
        return Path(override)
    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / "relief-puzzle"
    return Path(os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config") / "relief-puzzle"


def load() -> dict:
    data = dict(DEFAULTS)
    try:
        saved = json.loads((config_dir() / "settings.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        saved = {}
    if saved.get("lang") in ("uk", "en"):
        data["lang"] = saved["lang"]
    if saved.get("model") in ("large", "small"):
        data["model"] = saved["model"]
    try:
        data["bed"] = min(max(float(saved.get("bed", data["bed"])), 100.0), 500.0)
    except (TypeError, ValueError):
        pass
    return data


def save(changes: dict) -> dict:
    data = load()
    data.update({k: v for k, v in changes.items() if k in DEFAULTS})
    path = config_dir() / "settings.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return load()
