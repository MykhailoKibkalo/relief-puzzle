"""Збирає «Рельєфний пазл.app» — значок для запуску подвійним кліком.

Запуск:
    uv run python make_app.py

Застосунок запам'ятовує шлях до цієї теки. Якщо теку перенесено,
запустіть скрипт ще раз. Сам .app можна тримати де завгодно: на
робочому столі, у «Програмах», у Dock.
"""

from __future__ import annotations

import plistlib
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

from i18n import _, get_lang
from puzzle import jigsaw_polygons

ROOT = Path(__file__).resolve().parent
NAMES = {"uk": "Рельєфний пазл", "en": "Relief Puzzle"}  # значок називається мовою застосунку

LAUNCHER = """#!/bin/bash
# Запускає вікно «Рельєфного пазла». Згенеровано make_app.py.
PROJ="__PROJ__"
LOG="$HOME/Library/Logs/relief-puzzle.log"
export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$PATH"

fail() {
  /usr/bin/osascript -e "display alert \\"Relief Puzzle\\" message \\"$1\\"" >/dev/null 2>&1
  exit 1
}

cd "$PROJ" 2>/dev/null || fail "Не знайдено теку програми / App folder not found: $PROJ. Запустіть у ній make_app.py ще раз / Run make_app.py in it again."
if [ ! -x .venv/bin/python ]; then
  command -v uv >/dev/null || fail "Не знайдено uv / uv not found: brew install uv"
  uv sync >>"$LOG" 2>&1 || fail "Не вдалося встановити залежності / Could not install dependencies: $LOG"
fi
exec .venv/bin/python app.py >>"$LOG" 2>&1
"""


def draw_icon(size: int = 1024) -> Image.Image:
    """Деталь пазла кольору слонової кістки в коричневій рамці на сірому тлі."""
    ss = 4  # малюємо вчетверо більше й зменшуємо: так краї гладкі
    full = size * ss
    img = Image.new("RGBA", (full, full), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    m, r, inset = 100 * ss, 185 * ss, 62 * ss
    d.rounded_rectangle([m, m, full - m, full - m], r, fill=(107, 74, 54, 255))
    d.rounded_rectangle([m + inset, m + inset, full - m - inset, full - m - inset], r - inset, fill=(198, 202, 208, 255))

    piece = jigsaw_polygons(3.0, 3.0, 3, 3, tab=0.22, jitter=0.02, seed=5, samples=40)[(1, 1)]
    c = (piece.min(0) + piece.max(0)) / 2
    scale = 560 * ss / max(np.ptp(piece, axis=0))
    pts = [((x - c[0]) * scale + full / 2, (c[1] - y) * scale + full / 2) for x, y in piece]

    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).polygon([(x + 10 * ss, y + 18 * ss) for x, y in pts], fill=(30, 34, 40, 150))
    img.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(14 * ss)))
    ImageDraw.Draw(img).polygon(pts, fill=(239, 230, 210, 255))

    # Відблиск згори зліва й тінь знизу справа дають деталі об'єм.
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).polygon(pts, fill=255)
    inside = np.asarray(mask) / 255
    grad = np.fromfunction(lambda y, x: (x + y) / (2 * full), (full, full))
    for color, weight in (((255, 255, 255, 190), np.clip(1.6 - 3.0 * grad, 0, 1)), ((120, 98, 70, 170), np.clip(3.0 * grad - 1.4, 0, 1))):
        edge = Image.new("RGBA", img.size, (0, 0, 0, 0))
        ImageDraw.Draw(edge).line(pts + pts[:1], fill=color, width=10 * ss, joint="curve")
        edge.putalpha(Image.fromarray((np.asarray(edge)[..., 3] * weight * inside).astype(np.uint8)))
        img.alpha_composite(edge.filter(ImageFilter.GaussianBlur(2 * ss)))
    return img.resize((size, size), Image.Resampling.LANCZOS)


def build_icns(dest: Path):
    with tempfile.TemporaryDirectory() as tmp:
        iconset = Path(tmp) / "icon.iconset"
        iconset.mkdir()
        base = draw_icon()
        for px in (16, 32, 128, 256, 512):
            base.resize((px, px), Image.Resampling.LANCZOS).save(iconset / f"icon_{px}x{px}.png")
            base.resize((px * 2, px * 2), Image.Resampling.LANCZOS).save(iconset / f"icon_{px}x{px}@2x.png")
        subprocess.run(["iconutil", "-c", "icns", str(iconset), "-o", str(dest)], check=True)


def build(lang: str | None = None) -> Path:
    """Збирає значок із назвою потрібною мовою і прибирає значок з іншою назвою."""
    name = NAMES[lang or get_lang()]
    app = ROOT / f"{name}.app"
    for other in NAMES.values():
        if (ROOT / f"{other}.app").exists():
            shutil.rmtree(ROOT / f"{other}.app")
    macos, resources = app / "Contents" / "MacOS", app / "Contents" / "Resources"
    macos.mkdir(parents=True)
    resources.mkdir()

    launcher = macos / "launcher"
    launcher.write_text(LAUNCHER.replace("__PROJ__", str(ROOT)), encoding="utf-8")
    launcher.chmod(0o755)
    build_icns(resources / "icon.icns")
    with open(app / "Contents" / "Info.plist", "wb") as f:
        plistlib.dump(
            {
                "CFBundleName": name,
                "CFBundleDisplayName": name,
                "CFBundleIdentifier": "local.relief-puzzle",
                "CFBundleExecutable": "launcher",
                "CFBundleIconFile": "icon",
                "CFBundlePackageType": "APPL",
                "CFBundleShortVersionString": "0.1",
                "CFBundleVersion": "1",
                "LSMinimumSystemVersion": "11.0",
                "NSHighResolutionCapable": True,
            },
            f,
        )
    subprocess.run(["touch", str(app)], check=False)  # щоб Finder перечитав іконку
    return app


def main():
    print(_("Готово: {path}").format(path=build()))


if __name__ == "__main__":
    main()
