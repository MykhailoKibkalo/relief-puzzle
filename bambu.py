"""Налаштування друку для єдиного проєкту Bambu Studio.

Проєкт із кількома плитами Bambu Studio відкриває лише тоді, коли всередині є набір
налаштувань друку (Metadata/project_settings.config). Возити чужі профілі в репозиторії
не хочеться, а запускати сам слайсер із застосунку ненадійно. Тому налаштування
складаються з файлів пресетів, які вже лежать у користувача: беремо принтер, профіль
друку й пластик, обрані в Bambu Studio зараз, розгортаємо успадкування й зливаємо в один
файл — так само, як це робить слайсер, коли зберігає проєкт.

Працює лише на macOS зі встановленим Bambu Studio. Якщо щось не так — повертає None,
і тоді пазл зберігається тільки окремими файлами плит.
"""

from __future__ import annotations

import json
import plistlib
import re
from pathlib import Path

APP = Path("/Applications/BambuStudio.app")
SYSTEM = APP / "Contents" / "Resources" / "profiles" / "BBL"
USER = Path.home() / "Library" / "Application Support" / "BambuStudio"

# Якщо в Bambu Studio обрано принтер з іншим столом — типові пресети за розміром столу.
FALLBACK = {
    180: ("Bambu Lab A1 mini 0.4 nozzle", "0.20mm Standard @BBL A1M", "Bambu PLA Basic @BBL A1M"),
    256: ("Bambu Lab A1 0.4 nozzle", "0.20mm Standard @BBL A1", "Bambu PLA Basic @BBL A1"),
}
# Службові поля пресетів, яким не місце в налаштуваннях проєкту.
PRESET_ONLY = {"type", "name", "from", "inherits", "setting_id", "instantiation", "include", "description", "version",
               "filament_id", "base_id", "user_id", "updated_time", "is_custom_defined",
               "compatible_printers", "compatible_printers_condition", "compatible_prints", "compatible_prints_condition"}


def version() -> str:
    try:
        with open(APP / "Contents" / "Info.plist", "rb") as f:
            return str(plistlib.load(f).get("CFBundleShortVersionString", ""))
    except OSError:
        return ""


def _selected() -> tuple[str, str, str] | None:
    """Пресети принтера, друку й пластику, обрані в Bambu Studio зараз."""
    try:
        text = (USER / "BambuStudio.conf").read_text(encoding="utf-8", errors="replace")
        presets = json.loads(re.sub(r"\n#.*$", "", text.strip(), flags=re.S)).get("presets", {})
        return presets["machine"], presets["process"], presets["filaments"][0]
    except (OSError, ValueError, KeyError, IndexError):
        return None


def _find(kind: str, name: str) -> Path | None:
    """Файл пресета: спершу серед користувацьких, потім серед системних."""
    for root in sorted(USER.glob("user/*")):
        for path in (root / kind).rglob("*.json"):
            if path.stem == name:
                return path
    path = SYSTEM / kind / f"{name}.json"
    return path if path.exists() else None


def _flatten(kind: str, name: str) -> dict | None:
    """Пресет разом з усім, що він успадковує."""
    chain, current = [], name
    while current:
        path = _find(kind, current)
        if path is None or len(chain) > 20:
            return None
        data = json.loads(path.read_text(encoding="utf-8"))
        chain.append(data)
        current = data.get("inherits") or ""
    merged: dict = {}
    for data in reversed(chain):
        merged.update(data)
    return merged


def _bed_size(machine: dict) -> float | None:
    try:
        xs = [float(p.split("x")[0]) for p in machine["printable_area"]]
        return max(xs) - min(xs)
    except (KeyError, ValueError, IndexError):
        return None


def project_settings(bed: float) -> str | None:
    """Текст Metadata/project_settings.config для столу `bed` або None, якщо скласти його не вдалося."""
    if not SYSTEM.exists():
        return None
    for names in (_selected(), FALLBACK.get(round(bed))):
        if not names:
            continue
        machine, process, filament = (_flatten(kind, name) for kind, name in zip(("machine", "process", "filament"), names))
        # Плити розкладено під стіл `bed`, тож і принтер у проєкті має бути з таким самим столом.
        if machine and process and filament and abs((_bed_size(machine) or 0) - bed) <= 1.0:
            break
    else:
        return None

    config: dict = {}
    for preset in (process, filament, machine):
        config.update({k: v for k, v in preset.items() if k not in PRESET_ONLY})
    config.update({
        "name": "project_settings",
        "from": "project",
        "version": version() or str(machine.get("version", "")),
        "printer_settings_id": names[0],
        "print_settings_id": names[1],
        "filament_settings_id": [names[2]],
        "filament_ids": [str(filament.get("filament_id", ""))],
        "filament_colour": ["#EFE6D2"],
        "inherits_group": ["", "", ""],
        "different_settings_to_system": ["", "", ""],
    })
    return json.dumps(config, ensure_ascii=False, indent=4)
