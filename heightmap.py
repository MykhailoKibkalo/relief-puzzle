"""Картинка -> карта висот для рельєфу (нейромережа Depth Anything V2).

Запуск:
    uv run python heightmap.py cat.jpg -o cat_height.png

Результат — 16-бітний PNG (біле = високо) і прев'ю з підсвіткою поруч.
Карту висот можна підправити в будь-якому графічному редакторі, а потім
передати в puzzle.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps
from scipy import ndimage
from scipy.fft import dctn, idctn

from i18n import _

MODELS = {
    # small — Apache-2.0 (можна комерційно); base/large — CC-BY-NC-4.0 (лише некомерційно)
    "small": "depth-anything/Depth-Anything-V2-Small-hf",
    "base": "depth-anything/Depth-Anything-V2-Base-hf",
    "large": "depth-anything/Depth-Anything-V2-Large-hf",
}


_LOADED: dict[str, tuple] = {}


def _load(model_name: str):
    """Модель вантажиться один раз і лишається в пам'яті (важливо для застосунку)."""
    if model_name not in _LOADED:
        import torch
        from transformers import AutoImageProcessor, AutoModelForDepthEstimation

        device = "mps" if torch.backends.mps.is_available() else ("cuda" if torch.cuda.is_available() else "cpu")
        processor = AutoImageProcessor.from_pretrained(MODELS[model_name])
        model = AutoModelForDepthEstimation.from_pretrained(MODELS[model_name]).to(device).eval()
        _LOADED[model_name] = (processor, model, device)
    return _LOADED[model_name]


def estimate_depth(img: Image.Image, model_name: str, sizes: list[int]) -> list[np.ndarray]:
    """Відносна глибина (більше = ближче) для кожної роздільності зі списку."""
    import torch

    processor, model, device = _load(model_name)

    def run(arr: np.ndarray) -> np.ndarray:
        inputs = processor(images=Image.fromarray(arr), return_tensors="pt", do_resize=False)
        with torch.no_grad():
            depth = model(pixel_values=inputs["pixel_values"].to(device)).predicted_depth
        return depth[0].float().cpu().numpy().astype(np.float64)

    out = []
    patch = 14
    for size in sizes:
        scale = size / min(img.size)
        w = max(patch, round(img.width * scale / patch) * patch)
        h = max(patch, round(img.height * scale / patch) * patch)
        arr = np.asarray(img.resize((w, h), Image.Resampling.LANCZOS))
        padded = np.pad(arr, ((patch, patch), (patch, patch), (0, 0)), mode="reflect")
        # Модель бачить картинку клітинками 14×14 px, і ця сітка проступає в рельєфі.
        # Усереднюємо кілька проходів зі зсувом на пів клітинки та дзеркальним відбиттям.
        acc, ref = np.zeros((h, w)), None
        variants = [(ox, oy, flip) for flip in (False, True) for ox, oy in ((0, 0), (7, 7), (7, 0), (0, 7))]
        for ox, oy, flip in variants:
            win = padded[oy : oy + h + patch, ox : ox + w + patch]
            d = run(win[:, ::-1] if flip else win)
            d = d[:, ::-1] if flip else d
            d = d[patch - oy : patch - oy + h, patch - ox : patch - ox + w]
            if ref is None:
                ref = d
            else:  # проходи можуть відрізнятися масштабом і зсувом — вирівнюємо
                k, b = np.polyfit(d.ravel()[::13], ref.ravel()[::13], 1)
                d = k * d + b
            acc += d
        depth = torch.from_numpy(acc / len(variants))[None, None]
        depth = torch.nn.functional.interpolate(depth, size=(img.height, img.width), mode="bicubic", align_corners=False)
        out.append(depth[0, 0].numpy())
    return out


def fuse(coarse: np.ndarray, fine: np.ndarray, sigma: float) -> np.ndarray:
    """Загальна форма — з грубого проходу, дрібні деталі — з детального."""
    a = np.vstack([fine.ravel(), np.ones(fine.size)]).T
    k, b = np.linalg.lstsq(a[::17], coarse.ravel()[::17], rcond=None)[0]
    fine = k * fine + b
    return ndimage.gaussian_filter(coarse, sigma) + fine - ndimage.gaussian_filter(fine, sigma)


def _norm(a: np.ndarray, lo: float = 0.5, hi: float = 99.8) -> np.ndarray:
    p, q = np.percentile(a, [lo, hi])
    return np.clip((a - p) / max(q - p, 1e-9), 0.0, 1.0)


def _poisson(gx: np.ndarray, gy: np.ndarray) -> np.ndarray:
    """Поверхня за полем нахилів (розв'язок рівняння Пуассона, краї вільні)."""
    h, w = gy.shape[0] + 1, gx.shape[1] + 1
    div = np.zeros((h, w))
    div[:, :-1] += gx
    div[:, 1:] -= gx
    div[:-1, :] += gy
    div[1:, :] -= gy
    lam = (2 * np.cos(np.pi * np.arange(h) / h) - 2)[:, None] + (2 * np.cos(np.pi * np.arange(w) / w) - 2)[None, :]
    lam[0, 0] = 1.0
    f = dctn(div, type=2, norm="ortho") / lam
    f[0, 0] = 0.0
    return idctn(f, type=2, norm="ortho")


def bas_relief(depth: np.ndarray, flatten: float) -> np.ndarray:
    """Глибина -> барельєф 0..1.

    Справжня глибина сцени погано лягає в кілька міліметрів: майже весь запас висоти
    з'їдає перепад «предмет — тло», а на форму самого предмета нічого не лишається.
    Тому круті перепади послаблюються, пологі лишаються як є, і поверхня збирається
    назад із нахилів. Так роблять класичні барельєфи: об'єм сплющено, деталі збережено.
    """
    d = _norm(depth)
    if flatten <= 0:
        return d
    beta = 1.0 - 0.65 * min(flatten, 1.0)
    gx, gy = np.diff(d, axis=1), np.diff(d, axis=0)
    cy, cx = np.gradient(ndimage.gaussian_filter(d, 1.5))
    steep = np.hypot(cx, cy)
    ref = max(float(np.percentile(steep, 75)), 1e-6)
    keep = np.minimum(1.0, (np.maximum(steep, 1e-9) / ref) ** (beta - 1.0))
    return _norm(_poisson(gx * (keep[:, 1:] + keep[:, :-1]) / 2, gy * (keep[1:, :] + keep[:-1, :]) / 2))


def shape_relief(depth: np.ndarray | None, *, floor: float, gamma: float, detail: float, detail_radius: float, flatten: float,
                 texture: float = 0.0, gray: np.ndarray | None = None, base: np.ndarray | None = None, smooth: float = 0.0) -> np.ndarray:
    """`base` — готовий результат bas_relief (щоб не рахувати його щоразу, коли рухають інший повзунок)."""
    h = bas_relief(depth, flatten) if base is None else base
    size = max(h.shape)
    if floor > 0:
        h = np.clip((h - floor) / (1.0 - floor), 0.0, 1.0)
    if gamma != 1.0:
        h = h**gamma
    subject = h  # форма до підсилення: за нею визначаємо, де предмет, а де тло
    if detail > 0:
        # Підсилюємо лише дрібні нерівності. На великих сходинках (край пелюстки, силует)
        # звичайне підсилення дало б валик з одного боку й канавку з другого, тому добавку обмежено.
        fine = h - ndimage.gaussian_filter(h, size * detail_radius)
        h = h + detail * np.clip(fine, -0.012, 0.012)
        h = np.clip(h, 0.0, None)
        h = h / max(np.percentile(h, 99.9), 1e-9)
    if texture > 0 and gray is not None:
        # Мікрофактура (шерсть, пір'я, луска) з яскравості картинки: світле = вище.
        # Це не справжня геометрія, а імітація, тому підмішуємо потроху і лише на самому
        # предметі: на тлі (вода, стіна, розмите листя) вона перетворюється на шум.
        g = ndimage.gaussian_filter(gray, 0.8)
        fine = g - ndimage.gaussian_filter(g, size * 0.004)
        fine = np.clip(fine / max(np.percentile(np.abs(fine), 99), 1e-9), -1.0, 1.0)
        ground = np.percentile(subject, 25)  # рівень тла: нижня чверть висот
        on_subject = np.clip((ndimage.gaussian_filter(subject, size * 0.004) - ground - 0.08) / 0.15, 0.0, 1.0)
        h = h + texture * 0.05 * fine * on_subject
    if smooth > 0:
        h = ndimage.gaussian_filter(h, smooth * size * 0.003)
    return np.clip(h, 0.0, 1.0)


def hillshade_preview(h: np.ndarray, path: Path, relief_ratio: float = 0.03):
    """Швидкий рендер: як виглядатиме рельєф під боковим світлом."""
    z = h * relief_ratio * h.shape[1]
    gy, gx = np.gradient(z)
    normal = np.dstack([-gx, -gy, np.ones_like(z)])
    normal /= np.linalg.norm(normal, axis=2, keepdims=True)
    light = np.array([-0.55, -0.55, 0.63])
    shade = np.clip(normal @ (light / np.linalg.norm(light)), 0, 1)
    shade = 0.25 + 0.75 * shade
    rgb = np.dstack([shade * 236, shade * 226, shade * 205]).astype(np.uint8)
    Image.fromarray(rgb).save(path)


def load_image(path: Path, max_size: int = 3000) -> Image.Image:
    img = ImageOps.exif_transpose(Image.open(path))
    if img.mode in ("RGBA", "LA", "P"):
        rgba = img.convert("RGBA")
        img = Image.alpha_composite(Image.new("RGBA", rgba.size, (255, 255, 255, 255)), rgba)
    img = img.convert("RGB")
    if max(img.size) > max_size:
        img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
    return img


def image_depth(img: Image.Image, model: str = "large", res: int = 1036, fuse_passes: bool = True) -> np.ndarray:
    """Глибина картинки: грубий прохід дає загальну форму, детальний — дрібниці."""
    if not fuse_passes or res <= 518:
        depth = estimate_depth(img, model, [res])[0]
    else:
        coarse, fine = estimate_depth(img, model, [518, res])
        depth = fuse(coarse, fine, sigma=max(img.size) * 0.02)
    # Дрібніше за клітинку моделі (14 px) справжньої інформації немає — лише шум сітки.
    return denoise(ndimage.gaussian_filter(depth, 0.3 * 14 * min(img.size) / res))


def denoise(depth: np.ndarray) -> np.ndarray:
    """Прибирає дрібний шум глибини, не розмиваючи краї предметів.

    На рівному тлі (вода, стіна, небо) нейромережа дає ледь помітну рябь. Після
    барельєфного стиснення вона стає видимою «шкіркою». Медіана знімає поодинокі
    викиди, а самокерований фільтр вирівнює площини й пологі схили, лишаючи сходинки.
    """
    lo, hi = np.percentile(depth, [0.5, 99.8])
    span = max(hi - lo, 1e-9)
    d = (depth - lo) / span
    size = max(d.shape)
    d = ndimage.median_filter(d, 2 * min(round(size * 0.003), 4) + 1)
    r = max(2, round(size * 0.005))
    box = lambda a: ndimage.uniform_filter(a, 2 * r + 1, mode="nearest")  # noqa: E731
    mean = box(d)
    var = np.maximum(box(d * d) - mean * mean, 0.0)
    a = var / (var + 1e-4)
    return (box(a) * d + box(mean - a * mean)) * span + lo


def main():
    ap = argparse.ArgumentParser(
        description=_("Картинка → карта висот для рельєфу (нейромережа Depth Anything V2)."),
        epilog="uv run python heightmap.py cat.jpg -o cat_height.png",
    )
    ap.add_argument("image", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=None, help=_("куди зберегти карту висот (PNG, 16 біт)"))
    ap.add_argument("--model", choices=MODELS, default="large", help=_("large — найкраща якість; small — для комерційного використання"))
    ap.add_argument("--res", type=int, default=1036, help=_("роздільність детального проходу (коротка сторона, px)"))
    ap.add_argument("--no-fuse", action="store_true", help=_("лише один прохід, без злиття грубого й детального"))
    ap.add_argument("--flatten", type=float, default=0.6, help=_("0..1: стиснути великі перепади глибини (барельєфний ефект)"))
    ap.add_argument("--floor", type=float, default=0.0, help=_("0..1: усе, що нижче, стає плоским тлом"))
    ap.add_argument("--gamma", type=float, default=1.0, help=_("<1 піднімає середні висоти, >1 притискає"))
    ap.add_argument("--detail", type=float, default=0.6, help=_("підсилення дрібних деталей"))
    ap.add_argument("--detail-radius", type=float, default=0.006, help=_("радіус деталей (частка розміру картинки)"))
    ap.add_argument("--texture", type=float, default=0.5, help=_("0..2: додати мікрофактуру з яскравості картинки (0 = вимкнути)"))
    ap.add_argument("--crop", type=str, default=None, metavar="L,T,R,B", help=_("обрізати картинку (частки 0..1), напр. 0.25,0.2,0.72,0.82"))
    ap.add_argument("--smooth", type=float, default=0.0, help=_("0..1: згладити готовий рельєф (прибирає шум, але й дрібні деталі)"))
    ap.add_argument("--invert", action="store_true", help=_("інвертувати (далеке стане високим)"))
    ap.add_argument("--max-size", type=int, default=3000, help=_("обмеження довшої сторони карти висот, px"))
    args = ap.parse_args()

    img = load_image(args.image, args.max_size)
    depth = image_depth(img, args.model, args.res, fuse_passes=not args.no_fuse)
    if args.invert:
        depth = -depth
    if args.crop:
        # Обрізаємо вже після оцінки глибини: модель краще розуміє сцену цілком.
        l, t, r, b = (float(v) for v in args.crop.split(","))
        box = (round(l * img.width), round(t * img.height), round(r * img.width), round(b * img.height))
        depth = depth[box[1] : box[3], box[0] : box[2]]
        img = img.crop(box)

    gray = np.asarray(img.convert("L"), dtype=np.float64) / 255.0
    h = shape_relief(depth, floor=args.floor, gamma=args.gamma, detail=args.detail,
                     detail_radius=args.detail_radius, flatten=args.flatten, texture=args.texture, gray=gray, smooth=args.smooth)

    out = args.out or args.image.with_name(args.image.stem + "_height.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((h * 65535).astype(np.uint16)).save(out)
    preview = out.with_name(out.stem + "_preview.png")
    hillshade_preview(h, preview)
    print(_("Карта висот: {path}  ({w}×{h} px)").format(path=out, w=h.shape[1], h=h.shape[0]))
    print(_("Прев'ю:      {path}").format(path=preview))


if __name__ == "__main__":
    main()
