"""Дві мови: українська (рядки в коді) й англійська (таблиця нижче).

    from i18n import _
    print(_("Результат: {path}").format(path=out))

Мова: явно задана для запиту (застосунок) -> змінна RELIEF_PUZZLE_LANG ->
збережене налаштування -> мова системи.
"""

from __future__ import annotations

import contextvars
import os
import subprocess
import sys
from functools import lru_cache

_current: contextvars.ContextVar[str | None] = contextvars.ContextVar("lang", default=None)


@lru_cache(maxsize=1)
def system_lang() -> str:
    value = ""
    if sys.platform == "darwin":
        try:
            out = subprocess.run(["defaults", "read", "-g", "AppleLanguages"], capture_output=True, text=True, timeout=2).stdout
            value = out.split('"')[1] if '"' in out else ""
        except (OSError, subprocess.SubprocessError, IndexError):
            value = ""
    value = value or os.environ.get("LC_ALL") or os.environ.get("LC_MESSAGES") or os.environ.get("LANG") or ""
    return "uk" if value.lower().startswith("uk") else "en"


def get_lang() -> str:
    lang = _current.get() or os.environ.get("RELIEF_PUZZLE_LANG")
    if lang not in ("uk", "en"):
        import settings

        lang = settings.load()["lang"] or system_lang()
    return lang


def set_lang(lang: str | None):
    """Мова для поточного потоку (один запит до застосунку)."""
    _current.set(lang if lang in ("uk", "en") else None)


def _(text: str) -> str:
    return EN.get(text, text) if get_lang() == "en" else text


EN = {
    # --- спільне ---
    "Рельєфний пазл": "Relief Puzzle",
    "Карта висот: {path}  ({w}×{h} px)": "Height map: {path}  ({w}×{h} px)",
    # --- puzzle.py ---
    "Рельєфний 3D-пазл: карта висот → деталі пазла → плити для друку (3MF).":
        "Relief 3D puzzle: height map → puzzle pieces → print plates (3MF).",
    "Деталь у рядку {row}, стовпці {col} розпалася на {n} частин. Зробіть деталі більшими або зменште зазор.":
        "The piece in row {row}, column {col} split into {n} parts. Make the pieces larger or reduce the gap.",
    "Деталь у рядку {row}, стовпці {col} вийшла некоректною. Зробіть деталі більшими.":
        "The piece in row {row}, column {col} came out invalid. Make the pieces larger.",
    "Деталь {w}×{h} мм не влазить на стіл {bed} мм. Зробіть деталі меншими або стіл більшим.":
        "A {w}×{h} mm part does not fit the {bed} mm bed. Make the pieces smaller or the bed larger.",
    "Плита {n}: {count} шт.": "Plate {n}: {count} pcs",
    "карта висот (PNG/TIFF, біле = високо)": "height map (PNG/TIFF, white = high)",
    "тека результату": "output folder",
    "розмір": "size",
    "розріз": "cut",
    "друк": "printing",
    "рамка": "frame",
    "ширина пазла, мм (висота — за пропорцією)": "puzzle width, mm (height follows the aspect ratio)",
    "орієнтовний розмір деталі, мм": "approximate piece size, mm",
    "кількість стовпців (замість --piece)": "number of columns (instead of --piece)",
    "кількість рядків (замість --piece)": "number of rows (instead of --piece)",
    "товщина основи, мм": "base thickness, mm",
    "висота рельєфу над основою, мм": "relief height above the base, mm",
    "інвертувати карту висот": "invert the height map",
    "згладжування рельєфу, мм": "relief smoothing, mm",
    "зазор між сусідніми деталями, мм": "gap between neighbouring pieces, mm",
    "радіус округлення кутів, мм": "corner rounding radius, mm",
    "фаска знизу деталей проти «слонячої ноги», мм (0 = без фаски)": "bottom chamfer against elephant's foot, mm (0 = none)",
    "розмір замка (частка деталі)": "tab size (fraction of the piece)",
    "випадковість форми замків": "tab shape randomness",
    "номер малюнка розрізу": "cut pattern number",
    "розмір столу, мм (A1 mini = 180)": "bed size, mm (A1 mini = 180)",
    "відступ від краю столу, мм": "margin from the bed edge, mm",
    "відстань між деталями на плиті, мм": "spacing between parts on the plate, mm",
    "крок сітки рельєфу, мм": "relief grid step, mm",
    "допуск спрощення сітки, мм (0 = вимкнути)": "mesh simplification tolerance, mm (0 = off)",
    "додати рамку-піддон": "add a frame tray",
    "товщина дна рамки, мм": "frame floor thickness, mm",
    "ширина бортика, мм": "rim width, mm",
    "висота бортика над дном, мм": "rim height above the floor, mm",
    "зазор між пазлом і бортиком, мм": "gap between the puzzle and the rim, mm",
    "ЗАЗОРИ": "GAPS",
    "замість пазла згенерувати тест посадки (список зазорів через кому)": "generate a fit test instead of a puzzle (comma-separated gaps)",
    "потрібна карта висот (або --fit-test)": "a height map is required (or --fit-test)",
    "Тест посадки: зазори {gaps} мм, {n} деталей": "Fit test: gaps {gaps} mm, {n} pieces",
    "Пазл {w}×{h} мм, {cols}×{rows} = {n} деталей (~{pw}×{ph} мм), товщина {a}–{b} мм":
        "Puzzle {w}×{h} mm, {cols}×{rows} = {n} pieces (~{pw}×{ph} mm), {a}–{b} mm thick",
    "Плит: {n} з деталями": "Plates: {n} with pieces",
    " + {n} з рамкою ({k} секц.)": " + {n} with the frame ({k} sections)",
    "Трикутників: {n} млн": "Triangles: {n} M",
    "Результат: {path}": "Output: {path}",
    # --- heightmap.py ---
    "Картинка → карта висот для рельєфу (нейромережа Depth Anything V2).":
        "Picture → height map for a relief (Depth Anything V2 neural network).",
    "куди зберегти карту висот (PNG, 16 біт)": "where to save the height map (16-bit PNG)",
    "large — найкраща якість; small — для комерційного використання": "large: best quality; small: for commercial use",
    "роздільність детального проходу (коротка сторона, px)": "resolution of the detailed pass (short side, px)",
    "лише один прохід, без злиття грубого й детального": "single pass, no coarse/fine fusion",
    "0..1: стиснути великі перепади глибини (барельєфний ефект)": "0..1: compress large depth steps (bas-relief effect)",
    "0..1: усе, що нижче, стає плоским тлом": "0..1: everything below becomes a flat background",
    "<1 піднімає середні висоти, >1 притискає": "<1 lifts mid heights, >1 pushes them down",
    "підсилення дрібних деталей": "fine detail boost",
    "радіус деталей (частка розміру картинки)": "detail radius (fraction of the image size)",
    "0..2: додати мікрофактуру з яскравості картинки (0 = вимкнути)": "0..2: add micro-texture from image brightness (0 = off)",
    "обрізати картинку (частки 0..1), напр. 0.25,0.2,0.72,0.82": "crop the picture (fractions 0..1), e.g. 0.25,0.2,0.72,0.82",
    "інвертувати (далеке стане високим)": "invert (far becomes high)",
    "обмеження довшої сторони карти висот, px": "limit for the longer side of the height map, px",
    "Прев'ю:      {path}": "Preview:    {path}",
    # --- mesh2height.py ---
    "3D-модель рельєфу (STL/OBJ/PLY/GLB) → карта висот.": "Relief 3D model (STL/OBJ/PLY/GLB) → height map.",
    "розмір довшої сторони карти висот, px": "longer side of the height map, px",
    "вісь висоти рельєфу": "relief height axis",
    "узяти протилежний бік моделі": "use the opposite side of the model",
    "повернути результат": "rotate the result",
    "мм: відкинути нижню частину (товщину підкладки)": "mm: drop the bottom part (backing thickness)",
    "У файлі немає поверхні (жодного трикутника).": "The file has no surface (no triangles).",
    "вісь висоти {axis}": "height axis {axis}",
    " (тильний бік)": " (back side)",
    "Модель: {w}×{h} мм, висота рельєфу {r} мм, {note}": "Model: {w}×{h} mm, relief height {r} mm, {note}",
    "Для масштабу 1:1:  puzzle.py {path} --width {w} --relief {r}": "For 1:1 scale:  puzzle.py {path} --width {w} --relief {r}",
    # --- app.py ---
    "Вікно застосунку «Рельєфний пазл».": "The Relief Puzzle app window.",
    "відкрити у браузері, а не в окремому вікні": "open in the browser instead of a separate window",
    "лише запустити сервер (для перевірки)": "only start the server (for testing)",
    "Не вдалося прочитати зображення. Спробуйте PNG або JPEG.": "Could not read the image. Try PNG or JPEG.",
    "Формат «{ext}» не підтримується. Підійдуть PNG, JPEG, WebP, TIFF, STL, OBJ, PLY, GLB.":
        "The “{ext}” format is not supported. PNG, JPEG, WebP, TIFF, STL, OBJ, PLY and GLB work.",
    "Виходить {n} деталей — це забагато. Зробіть деталі більшими або пазл меншим.":
        "That makes {n} pieces, which is too many. Make the pieces larger or the puzzle smaller.",
    "Внутрішня помилка: {e}": "Internal error: {e}",
    "Файл порожній.": "The file is empty.",
    "Спершу оберіть картинку, карту висот або 3D-модель.": "Choose a picture, a height map or a 3D model first.",
    "Файл не знайдено. Створіть файли ще раз.": "File not found. Create the files again.",
    "Цю програму не знайдено в теці «Програми».": "That app was not found in Applications.",
    "Не вдалося зв'язатися з GitHub. Перевірте інтернет і спробуйте ще раз.":
        "Could not reach GitHub. Check your internet connection and try again.",
    "Цю копію встановлено не через git. Завантажте нову версію зі сторінки на GitHub.":
        "This copy was not installed with git. Download the new version from the GitHub page.",
    "Оновити автоматично не вдалося: {detail}": "Automatic update failed: {detail}",
    "Довідка": "Help",
    "Налаштування…": "Settings…",
    "Про програму": "About",
    "Перевірити оновлення": "Check for updates",
    "Сторінка на GitHub": "GitHub page",
    # --- make_app.py ---
    "Збирає значок застосунку для запуску подвійним кліком.": "Builds the app icon you can launch with a double click.",
    "Готово: {path}": "Done: {path}",
}
