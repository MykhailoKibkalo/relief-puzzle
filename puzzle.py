"""Рельєфний 3D-пазл: карта висот -> деталі пазла -> плити для друку (3MF).

Запуск:
    uv run python puzzle.py heightmap.png --width 240 --piece 24 --tray

Вхід — карта висот у відтінках сірого (біле = високо). Отримати її з
картинки можна через heightmap.py, з 3D-моделі — через mesh2height.py.
Те саме, але з вікном і переглядом: app.py.
"""

from __future__ import annotations

import argparse
import math
import uuid
import zipfile
from dataclasses import dataclass, field, fields
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, JoinType, Manifold, Mesh
from PIL import Image
from scipy import ndimage

from i18n import _


@dataclass
class Options:
    # розмір
    width: float = 170.0  # ширина пазла, мм (висота — за пропорцією)
    piece: float = 24.0  # орієнтовний розмір деталі, мм
    cols: int | None = None
    rows: int | None = None
    base: float = 2.4  # товщина основи, мм
    relief: float = 5.0  # висота рельєфу над основою, мм
    smooth: float = 0.0  # згладжування рельєфу, мм
    # розріз
    clearance: float = 0.2  # зазор між сусідніми деталями, мм
    corner: float = 0.3  # радіус округлення кутів, мм
    chamfer: float = 0.3  # фаска знизу проти «слонячої ноги», мм
    tab: float = 0.2  # розмір замка (частка деталі)
    jitter: float = 0.04  # випадковість форми замків
    seed: int = 1
    # друк
    bed: float = 180.0  # розмір столу, мм (A1 mini = 180)
    margin: float = 4.0  # відступ від краю столу, мм
    gap: float = 2.0  # відстань між деталями на плиті, мм
    res: float = 0.2  # крок сітки рельєфу, мм
    simplify: float = 0.01  # допуск спрощення сітки, мм
    # рамка
    tray: bool = False
    tray_floor: float = 1.2  # товщина дна рамки, мм
    tray_rim: float = 6.0  # ширина бортика, мм
    tray_rim_height: float | None = None  # висота бортика над дном, мм
    tray_clearance: float = 0.4  # зазор між пазлом і бортиком, мм

    @property
    def usable(self) -> float:
        return self.bed - 2 * self.margin

    @property
    def rim_height(self) -> float:
        return self.tray_rim_height or (self.base + min(self.relief * 0.4, 2.0))


# ----------------------------------------------------------------------------
# Пазловий контур
# ----------------------------------------------------------------------------


def _bezier(p0, p1, p2, p3, n):
    t = np.linspace(0.0, 1.0, n)[:, None]
    return (
        (1 - t) ** 3 * p0
        + 3 * (1 - t) ** 2 * t * p1
        + 3 * (1 - t) * t**2 * p2
        + t**3 * p3
    )


class EdgeLine:
    """Одна лінія розрізу (через увесь пазл), що складається із сегментів із замками.

    Кожен сегмент — три кубічні криві Безьє: підхід, «голівка» замка, відхід.
    Сусідні сегменти стикуються з неперервною дотичною.
    """

    def __init__(self, rng: np.random.Generator, tab: float, jitter: float, samples: int, alternate: bool = False):
        self.rng = rng
        self.t = tab / 2.0
        self.j = jitter
        self.samples = samples
        self.alternate = alternate  # замки строго по черзі: назовні, всередину, назовні…
        self.flip = False
        self.e = rng.uniform(-jitter, jitter) if jitter else 0.0
        self._next()

    def _next(self):
        old = self.flip
        self.flip = (not old) if self.alternate else bool(self.rng.random() > 0.5)
        self.a = -self.e if self.flip == old else self.e
        j = self.j
        self.b, self.c, self.d, self.e = (self.rng.uniform(-j, j, 4) if j else np.zeros(4))

    def segment(self) -> np.ndarray:
        """Точки сегмента в одиничних координатах: (уздовж 0..1, упоперек)."""
        t, a, b, c, d, e = self.t, self.a, self.b, self.c, self.d, self.e
        s = -1.0 if self.flip else 1.0
        pts = np.array(
            [
                (0.0, 0.0),
                (0.2, a),
                (0.5 + b + d, -t + c),
                (0.5 - t + b, t + c),
                (0.5 - 2 * t + b - d, 3 * t + c),
                (0.5 + 2 * t + b - d, 3 * t + c),
                (0.5 + t + b, t + c),
                (0.5 + b + d, -t + c),
                (0.8, e),
                (1.0, 0.0),
            ]
        )
        pts[:, 1] *= s
        n = self.samples
        curve = np.vstack(
            [
                _bezier(pts[0], pts[1], pts[2], pts[3], n)[:-1],
                _bezier(pts[3], pts[4], pts[5], pts[6], n)[:-1],
                _bezier(pts[6], pts[7], pts[8], pts[9], n),
            ]
        )
        self._next()
        return curve


def jigsaw_polygons(
    width: float,
    height: float,
    cols: int,
    rows: int,
    *,
    tab: float = 0.2,
    jitter: float = 0.04,
    seed: int = 1,
    samples: int = 14,
    tabs_x: int = 1,
    tabs_y: int = 1,
    alternate: bool = False,
    square: bool = False,
) -> dict[tuple[int, int], np.ndarray]:
    """Контури деталей (проти годинникової стрілки) без зазору.

    Ключ — (рядок, стовпець); рядок 0 — нижній (вісь Y спрямована вгору).
    `tabs_x`/`tabs_y` — скільки замків на одному ребрі клітинки вздовж X і Y.
    `square` — замок має пропорції свого відрізка шва, а не всієї клітинки: так довгий
    шов рамки отримує ряд нормальних замків, а не один дрібний чи розтягнутий.
    """
    rng = np.random.default_rng(seed)
    cw, ch = width / cols, height / rows

    def edge(line: EdgeLine | None, n: int) -> np.ndarray:
        """Ребро клітинки в одиничних координатах (уздовж 0..1, упоперек у частках відрізка)."""
        if line is None:
            return np.array([(0.0, 0.0), (1.0, 0.0)])
        parts = []
        for q in range(n):
            u = line.segment()
            part = np.column_stack([(q + u[:, 0]) / n, u[:, 1] / n])
            parts.append(part if q == n - 1 else part[:-1])
        return np.vstack(parts)

    # Горизонтальні лінії y = k*ch: сегмент i іде зліва направо.
    hseg: dict[tuple[int, int], np.ndarray] = {}
    for k in range(rows + 1):
        line = EdgeLine(rng, tab, jitter, samples, alternate) if 0 < k < rows else None
        for i in range(cols):
            u = edge(line, tabs_x)
            hseg[(k, i)] = np.column_stack([(i + u[:, 0]) * cw, k * ch + u[:, 1] * (cw if square else ch)])

    # Вертикальні лінії x = i*cw: сегмент k іде знизу вгору.
    vseg: dict[tuple[int, int], np.ndarray] = {}
    for i in range(cols + 1):
        line = EdgeLine(rng, tab, jitter, samples, alternate) if 0 < i < cols else None
        for k in range(rows):
            u = edge(line, tabs_y)
            vseg[(i, k)] = np.column_stack([i * cw + u[:, 1] * (ch if square else cw), (k + u[:, 0]) * ch])

    polys = {}
    for k in range(rows):
        for i in range(cols):
            bottom = hseg[(k, i)]
            right = vseg[(i + 1, k)]
            top = hseg[(k + 1, i)][::-1]
            left = vseg[(i, k)][::-1]
            polys[(k, i)] = np.vstack([bottom[:-1], right[:-1], top[:-1], left[:-1]])
    return polys


def grid_for(width: float, height: float, o: Options) -> tuple[int, int]:
    """Кількість стовпців і рядків деталей."""
    return (o.cols or max(2, round(width / o.piece)), o.rows or max(2, round(height / o.piece)))


def piece_outlines(width: float, height: float, cols: int, rows: int, o: Options, *, jitter: float | None = None):
    """Контури деталей уже із зазором і округленими кутами: {(рядок, стовпець): (переріз, точки)}."""
    polys = jigsaw_polygons(width, height, cols, rows, tab=o.tab, jitter=o.jitter if jitter is None else jitter, seed=o.seed)
    out = {}
    for (k, i), poly in polys.items():
        cs = CrossSection([poly])
        # Зазор: кожна деталь відступає на половину. Плюс округлення опуклих кутів.
        cs = cs.offset(-(o.clearance / 2.0 + o.corner), JoinType.Round, circular_segments=24)
        if o.corner > 0:
            cs = cs.offset(o.corner, JoinType.Round, circular_segments=24)
        contours = cs.to_polygons()
        if len(contours) != 1:
            raise RuntimeError(
                _("Деталь у рядку {row}, стовпці {col} розпалася на {n} частин. Зробіть деталі більшими або зменште зазор.")
                .format(row=rows - k, col=i + 1, n=len(contours))
            )
        out[(k, i)] = (cs, np.asarray(contours[0]))
    return out


# ----------------------------------------------------------------------------
# Геометрія
# ----------------------------------------------------------------------------


def heightfield_solid(xs: np.ndarray, ys: np.ndarray, z: np.ndarray, z_bottom: float = -1.0) -> Manifold:
    """Замкнене тіло під поверхнею z(x, y) на прямокутній сітці."""
    n, m = len(xs), len(ys)
    gx, gy = np.meshgrid(xs, ys)
    top = np.column_stack([gx.ravel(), gy.ravel(), z.ravel()])
    corners = np.array(
        [
            (xs[0], ys[0], z_bottom),
            (xs[-1], ys[0], z_bottom),
            (xs[-1], ys[-1], z_bottom),
            (xs[0], ys[-1], z_bottom),
        ]
    )
    verts = np.vstack([top, corners])
    sw, se, ne, nw = (n * m + q for q in range(4))

    idx = np.arange(n * m).reshape(m, n)
    a, b = idx[:-1, :-1].ravel(), idx[:-1, 1:].ravel()
    c, d = idx[1:, 1:].ravel(), idx[1:, :-1].ravel()
    tris = [np.column_stack([a, b, c]), np.column_stack([a, c, d])]

    def fan(apex, ring, last):
        # Стінка: віяло від нижнього кута `apex` по верхньому ребру `ring`,
        # потім замикальний трикутник до другого нижнього кута `last`.
        r0, r1 = ring[:-1], ring[1:]
        tris.append(np.column_stack([np.full(len(r0), apex), r0, r1]))
        tris.append(np.array([[apex, ring[-1], last]]))

    fan(se, idx[0, ::-1], sw)  # південна стінка (нормаль -y)
    fan(ne, idx[::-1, -1], se)  # східна (+x)
    fan(nw, idx[-1, :], ne)  # північна (+y)
    fan(sw, idx[:, 0], nw)  # західна (-x)
    tris.append(np.array([[sw, ne, se], [sw, nw, ne]]))  # дно

    mesh = Mesh(
        vert_properties=np.ascontiguousarray(verts, dtype=np.float32),
        tri_verts=np.ascontiguousarray(np.vstack(tris), dtype=np.uint32),
    )
    return Manifold(mesh)


@dataclass
class Part:
    name: str
    verts: np.ndarray  # (N, 3), у координатах зібраного пазла
    tris: np.ndarray  # (M, 3)
    outline: np.ndarray  # (K, 2) контур для прев'ю
    offset: np.ndarray = field(default_factory=lambda: np.zeros(2))  # зсув на плиті
    plate: int = 0

    @property
    def bounds(self):
        return self.verts[:, :2].min(axis=0), self.verts[:, :2].max(axis=0)


def manifold_to_part(name: str, solid: Manifold, outline: np.ndarray) -> Part:
    mesh = solid.to_mesh()
    return Part(name, np.asarray(mesh.vert_properties)[:, :3].astype(np.float64), np.asarray(mesh.tri_verts), outline)


@dataclass
class Relief:
    """Карта висот у міліметрах на рівномірній сітці (Y спрямована вгору)."""

    z: np.ndarray  # (ny, nx), абсолютна висота поверхні над дном деталі
    width: float
    height: float

    @classmethod
    def from_height(cls, h: np.ndarray, o: Options) -> "Relief":
        """`h` — висоти 0..1, рядок 0 = верх картинки."""
        arr = np.asarray(h, dtype=np.float64)
        height = o.width * arr.shape[0] / arr.shape[1]
        nx, ny = round(o.width / o.res) + 1, round(height / o.res) + 1
        # Згладжуємо перед зменшенням, щоб не було аліасингу.
        sigma = max(0.0, (arr.shape[1] / nx - 1.0) / 2.0)
        if sigma > 0:
            arr = ndimage.gaussian_filter(arr, sigma)
        zoomed = np.asarray(
            Image.fromarray(arr.astype(np.float32), mode="F").resize((nx, ny), Image.Resampling.BICUBIC),
            dtype=np.float64,
        )
        if o.smooth > 0:
            zoomed = ndimage.gaussian_filter(zoomed, o.smooth / o.res)
        zoomed = np.clip(zoomed, 0.0, 1.0)[::-1]  # рядок 0 = низ
        return cls(o.base + o.relief * zoomed, o.width, height)

    @classmethod
    def from_image(cls, path: Path, o: Options, invert: bool = False) -> "Relief":
        return cls.from_height(load_heightmap(path, invert), o)

    def crop_solid(self, lo, hi) -> Manifold:
        ny, nx = self.z.shape
        dx, dy = self.width / (nx - 1), self.height / (ny - 1)
        i0 = max(int(math.floor(lo[0] / dx)) - 1, 0)
        i1 = min(int(math.ceil(hi[0] / dx)) + 1, nx - 1)
        j0 = max(int(math.floor(lo[1] / dy)) - 1, 0)
        j1 = min(int(math.ceil(hi[1] / dy)) + 1, ny - 1)
        z = self.z[j0 : j1 + 1, i0 : i1 + 1]
        xs = np.arange(i0, i1 + 1) * dx
        ys = np.arange(j0, j1 + 1) * dy
        # Виносимо крайні вузли за межі пазла, щоб грані не збігалися з контуром.
        pad = 1.0
        xs[0] -= pad if i0 == 0 else 0.0
        xs[-1] += pad if i1 == nx - 1 else 0.0
        ys[0] -= pad if j0 == 0 else 0.0
        ys[-1] += pad if j1 == ny - 1 else 0.0
        return heightfield_solid(xs, ys, z)


def load_heightmap(path: Path, invert: bool = False) -> np.ndarray:
    """Карта висот із файлу: значення 0..1, рядок 0 = верх."""
    img = Image.open(path)
    if img.mode not in ("I;16", "I", "F", "L"):
        img = img.convert("L")
    arr = np.asarray(img, dtype=np.float64)
    arr = (arr - arr.min()) / max(float(np.ptp(arr)), 1e-9)
    return 1.0 - arr if invert else arr


def piece_cutter(cs: CrossSection, zmax: float, chamfer: float) -> Manifold:
    """Призма за контуром деталі з фаскою знизу.

    Фаска компенсує «слонячу ногу» (розплющений перший шар), через яку деталі
    інакше заклинюють. Робиться сходинками по 1/3 висоти: слайсер однаково
    ріже модель на шари.
    """
    body = cs.extrude(zmax)
    if chamfer <= 0:
        return body
    steps = 3
    step = chamfer / steps
    cutter = body.translate([0, 0, chamfer])
    for k in range(steps):
        inset = chamfer * (1 - (k + 0.5) / steps)
        slab = cs.offset(-inset, JoinType.Round, circular_segments=24).extrude(step + 1e-3)
        cutter += slab.translate([0, 0, k * step])
    return cutter


def cut_pieces(relief: Relief, cols: int, rows: int, o: Options, *, jitter: float | None = None, prefix: str = "") -> list[Part]:
    zmax = float(relief.z.max()) + 1.0
    parts = []
    for (k, i), (cs, outline) in piece_outlines(relief.width, relief.height, cols, rows, o, jitter=jitter).items():
        lo, hi = outline.min(axis=0), outline.max(axis=0)
        solid = relief.crop_solid(lo, hi) ^ piece_cutter(cs, zmax, o.chamfer)
        if o.simplify > 0:
            solid = solid.simplify(o.simplify)
        if solid.is_empty() or len(solid.decompose()) != 1:
            raise RuntimeError(
                _("Деталь у рядку {row}, стовпці {col} вийшла некоректною. Зробіть деталі більшими.").format(row=rows - k, col=i + 1)
            )
        parts.append(manifold_to_part(f"{prefix}r{rows - 1 - k:02d}c{i:02d}", solid, outline))
    return parts


def make_tray(width: float, height: float, o: Options) -> list[Part]:
    """Рамка-піддон. Якщо не влазить на плиту — ріжеться на секції із замками."""
    rim, clearance, floor, rim_height = o.tray_rim, o.tray_clearance, o.tray_floor, o.rim_height
    inner_w, inner_h = width + 2 * clearance, height + 2 * clearance
    outer_w, outer_h = inner_w + 2 * rim, inner_h + 2 * rim
    r = min(3.0, rim * 0.6)
    outer = CrossSection.square([outer_w - 2 * r, outer_h - 2 * r]).translate([r, r]).offset(r, JoinType.Round, circular_segments=48)
    inner = CrossSection.square([inner_w, inner_h]).translate([rim, rim])
    tray = outer.extrude(floor + rim_height) - inner.extrude(rim_height + 1.0).translate([0, 0, floor])

    # Шви секцій: ряд замків, як у самому пазлі, але приблизно вдвічі більших.
    tab = 0.26
    pitch = max(40.0, 2.0 * o.piece)  # орієнтовна відстань між замками, мм
    reach = 0.45 * pitch  # наскільки щонайбільше замок виступає за шов

    def tabs(length: float) -> int:
        return max(1, math.ceil(length / (1.15 * pitch)))

    def split(size: float) -> int:
        n = 1
        while n == 1 and size > o.usable or n > 1 and size / n + (2 if n > 2 else 1) * reach > o.usable:
            n += 1
        return n

    nx, ny = split(outer_w), split(outer_h)
    shift = np.array([rim + clearance, rim + clearance])
    if nx == 1 and ny == 1:
        outline = np.asarray(outer.to_polygons()[0]) - shift
        return [manifold_to_part("tray", tray.translate([-shift[0], -shift[1], 0]), outline)]

    polys = jigsaw_polygons(
        outer_w, outer_h, nx, ny, tab=tab, jitter=0.0, seed=o.seed + 1000, samples=20, alternate=True, square=True,
        tabs_x=tabs(outer_w / nx), tabs_y=tabs(outer_h / ny),
    )
    parts = []
    for (k, i), poly in polys.items():
        cs = CrossSection([poly]).offset(-0.08, JoinType.Round, circular_segments=24)
        solid = tray ^ cs.extrude(floor + rim_height + 1.0).translate([0, 0, -0.5])
        solid = solid.translate([-shift[0], -shift[1], 0])
        outline = np.asarray((cs ^ outer).to_polygons()[0]) - shift
        parts.append(manifold_to_part(f"tray_r{ny - 1 - k}c{i}", solid, outline))
    return parts


# ----------------------------------------------------------------------------
# Розкладка по плитах
# ----------------------------------------------------------------------------


def pack(parts: list[Part], usable: float, gap: float, first_plate: int = 0) -> int:
    """Полична розкладка (FFDH). Повертає кількість використаних плит."""
    sizes = []
    for p in parts:
        lo, hi = p.bounds
        w, h = hi - lo
        if w > usable or h > usable:
            raise RuntimeError(
                _("Деталь {w}×{h} мм не влазить на стіл {bed} мм. Зробіть деталі меншими або стіл більшим.")
                .format(w=f"{w:.0f}", h=f"{h:.0f}", bed=f"{usable:.0f}")
            )
        sizes.append((w, h))
    order = sorted(range(len(parts)), key=lambda q: -sizes[q][1])
    plates: list[list[list]] = []  # плита -> полиці [y, висота, зайнята ширина]
    for q in order:
        w, h = sizes[q]
        placed = False
        for pi, shelves in enumerate(plates):
            for shelf in shelves:
                if shelf[2] + w <= usable and h <= shelf[1]:
                    x, y = shelf[2], shelf[0]
                    shelf[2] += w + gap
                    placed = True
                    break
            if not placed:
                top = shelves[-1][0] + shelves[-1][1] + gap
                if top + h <= usable:
                    shelves.append([top, h, w + gap])
                    x, y, placed = 0.0, top, True
            if placed:
                break
        if not placed:
            plates.append([[0.0, h, w + gap]])
            pi, x, y = len(plates) - 1, 0.0, 0.0
        lo = parts[q].bounds[0]
        parts[q].offset = np.array([x, y]) - lo
        parts[q].plate = first_plate + pi
    return len(plates)


def center_plates(parts: list[Part], bed: float):
    """Центрує вміст кожної плити на столі."""
    for plate in sorted({p.plate for p in parts}):
        group = [p for p in parts if p.plate == plate]
        lo = np.min([p.bounds[0] + p.offset for p in group], axis=0)
        hi = np.max([p.bounds[1] + p.offset for p in group], axis=0)
        shift = (bed - (hi - lo)) / 2.0 - lo
        for p in group:
            p.offset = p.offset + shift


# ----------------------------------------------------------------------------
# Експорт
# ----------------------------------------------------------------------------

_CONTENT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    "</Types>"
)
_RELS = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
    '<Relationship Target="/3D/3dmodel.model" Id="rel0" '
    'Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>'
    "</Relationships>"
)


def write_3mf(path: Path, parts: list[Part]):
    chunks = [
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<model unit="millimeter" xml:lang="en-US" '
        'xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02">\n'
        '<metadata name="Application">relief-puzzle</metadata>\n<resources>\n'
    ]
    for oid, p in enumerate(parts, start=1):
        v = p.verts.copy()
        v[:, :2] += p.offset
        chunks.append(f'<object id="{oid}" name="{p.name}" type="model"><mesh><vertices>\n')
        chunks.append("\n".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in v.tolist()))
        chunks.append("\n</vertices><triangles>\n")
        chunks.append("\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in p.tris.tolist()))
        chunks.append("\n</triangles></mesh></object>\n")
    chunks.append("</resources>\n<build>\n")
    chunks.extend(f'<item objectid="{oid}"/>\n' for oid in range(1, len(parts) + 1))
    chunks.append("</build>\n</model>\n")
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("[Content_Types].xml", _CONTENT_TYPES)
        zf.writestr("_rels/.rels", _RELS)
        zf.writestr("3D/3dmodel.model", "".join(chunks))


_PROJECT_TYPES = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="model" ContentType="application/vnd.ms-package.3dmanufacturing-3dmodel+xml"/>'
    "</Types>"
)
_MODEL_HEAD = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<model unit="millimeter" xml:lang="en-US" xmlns="http://schemas.microsoft.com/3dmanufacturing/core/2015/02" '
    'xmlns:BambuStudio="http://schemas.bambulab.com/package/2021" '
    'xmlns:p="http://schemas.microsoft.com/3dmanufacturing/production/2015/06" requiredextensions="p">\n'
)


def write_project(path: Path, groups: dict[int, list[Part]], bed: float, names: dict[int, str], config: str, version: str):
    """Один проєкт Bambu Studio / OrcaStudio з усіма плитами одразу.

    Формат повторює те, що зберігає сам Bambu Studio: кожна деталь — окремий вкладений
    файл, у головному файлі — посилання на них і положення, а в model_settings.config —
    перелік плит. Плити слайсер розкладає сіткою з кроком 1,2 розміру столу; саме в ці
    місця й ставимо деталі.
    """
    order = sorted(groups)
    cols = math.ceil(math.sqrt(len(order)))
    stride = bed * 1.2
    files: dict[str, str] = {}
    wrappers, items, rels, objects_cfg, plates_cfg = [], [], [], [], []
    oid = 0
    for index, plate in enumerate(order):
        row, col = divmod(index, cols)
        ox, oy = col * stride, -row * stride
        instances = []
        for part in groups[plate]:
            oid += 1
            mesh_id, wrap_id = 2 * oid - 1, 2 * oid
            v = part.verts.copy()
            v[:, :2] += part.offset
            centre = (v.min(axis=0) + v.max(axis=0)) / 2.0  # слайсер тримає сітку довкола центру об'єкта
            v -= centre
            sub = f"3D/Objects/object_{oid}.model"
            files[sub] = "".join([
                _MODEL_HEAD,
                '<metadata name="BambuStudio:3mfVersion">1</metadata>\n<resources>\n',
                f'<object id="{mesh_id}" p:UUID="{uuid.uuid4()}" type="model"><mesh><vertices>\n',
                "\n".join(f'<vertex x="{x:.4f}" y="{y:.4f}" z="{z:.4f}"/>' for x, y, z in v.tolist()),
                "\n</vertices><triangles>\n",
                "\n".join(f'<triangle v1="{a}" v2="{b}" v3="{c}"/>' for a, b, c in part.tris.tolist()),
                "\n</triangles></mesh></object>\n</resources>\n</model>\n",
            ])
            rels.append(f'<Relationship Target="/{sub}" Id="rel-{oid}" Type="http://schemas.microsoft.com/3dmanufacturing/2013/01/3dmodel"/>')
            wrappers.append(
                f'<object id="{wrap_id}" p:UUID="{uuid.uuid4()}" type="model"><components>'
                f'<component p:path="/{sub}" objectid="{mesh_id}" p:UUID="{uuid.uuid4()}" transform="1 0 0 0 1 0 0 0 1 0 0 0"/>'
                "</components></object>"
            )
            items.append(
                f'<item objectid="{wrap_id}" p:UUID="{uuid.uuid4()}" '
                f'transform="1 0 0 0 1 0 0 0 1 {centre[0] + ox:.4f} {centre[1] + oy:.4f} {centre[2]:.4f}" printable="1"/>'
            )
            objects_cfg.append(
                f'  <object id="{wrap_id}">\n    <metadata key="name" value="{part.name}"/>\n    <metadata key="extruder" value="1"/>\n'
                f'    <part id="{mesh_id}" subtype="normal_part">\n      <metadata key="name" value="{part.name}"/>\n'
                '      <metadata key="matrix" value="1 0 0 0 0 1 0 0 0 0 1 0 0 0 0 1"/>\n    </part>\n  </object>\n'
            )
            instances.append(
                f'    <model_instance>\n      <metadata key="object_id" value="{wrap_id}"/>\n'
                f'      <metadata key="instance_id" value="0"/>\n      <metadata key="identify_id" value="{1000 + oid}"/>\n    </model_instance>\n'
            )
        plates_cfg.append(
            f'  <plate>\n    <metadata key="plater_id" value="{index + 1}"/>\n    <metadata key="plater_name" value="{names.get(plate, "")}"/>\n'
            '    <metadata key="locked" value="false"/>\n' + "".join(instances) + "  </plate>\n"
        )

    model = "".join([
        _MODEL_HEAD,
        f'<metadata name="Application">BambuStudio-{version or "02.00.00.00"}</metadata>\n<metadata name="BambuStudio:3mfVersion">1</metadata>\n',
        "<resources>\n", "\n".join(wrappers), "\n</resources>\n",
        f'<build p:UUID="{uuid.uuid4()}">\n', "\n".join(items), "\n</build>\n</model>\n",
    ])
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        zf.writestr("[Content_Types].xml", _PROJECT_TYPES)
        zf.writestr("_rels/.rels", _RELS.replace('Id="rel0"', 'Id="rel-1"'))
        zf.writestr("3D/3dmodel.model", model)
        zf.writestr("3D/_rels/3dmodel.model.rels",
                    '<?xml version="1.0" encoding="UTF-8"?>\n<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                    + "".join(rels) + "</Relationships>")
        for name, text in files.items():
            zf.writestr(name, text)
        zf.writestr("Metadata/model_settings.config",
                    '<?xml version="1.0" encoding="UTF-8"?>\n<config>\n' + "".join(objects_cfg) + "".join(plates_cfg) + "</config>\n")
        zf.writestr("Metadata/project_settings.config", config)


def save_previews(out: Path, relief: Relief | None, pieces: list[Part], plates: dict[int, list[Part]], bed: float):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Зібраний пазл: рельєф під боковим світлом (згори зліва) + лінії розрізу.
    if relief is not None:
        w, h = relief.width, relief.height
        fig, ax = plt.subplots(figsize=(10, 10 * h / w), dpi=150)
        step = max(1, relief.z.shape[1] // 1600)
        z = relief.z[::step, ::step]
        dx = w / (z.shape[1] - 1)
        gy, gx = np.gradient(z, dx)  # рядок 0 = низ, тож gy — похідна вздовж Y угору
        normal = np.dstack([-gx, -gy, np.ones_like(z)])
        normal /= np.linalg.norm(normal, axis=2, keepdims=True)
        light = np.array([-0.55, 0.55, 0.63])
        shade = 0.25 + 0.75 * np.clip(normal @ (light / np.linalg.norm(light)), 0, 1)
        rgb = np.dstack([shade * 236, shade * 226, shade * 205]).astype(np.uint8)
        ax.imshow(rgb, extent=(0, w, 0, h), origin="lower")
        for p in pieces:
            ring = np.vstack([p.outline, p.outline[:1]])
            ax.plot(ring[:, 0], ring[:, 1], color="#3a2a1a", lw=0.5, alpha=0.8)
        ax.set_axis_off()
        fig.subplots_adjust(0, 0, 1, 1)
        fig.savefig(out / "preview_assembled.png")
        plt.close(fig)

    # Розкладка по плитах.
    n = len(plates)
    ncol = min(n, 4)
    nrow = math.ceil(n / ncol)
    fig, axes = plt.subplots(nrow, ncol, figsize=(4 * ncol, 4.2 * nrow), dpi=110, squeeze=False)
    for ax in axes.ravel():
        ax.set_axis_off()
    for ax, (plate, group) in zip(axes.ravel(), sorted(plates.items())):
        ax.add_patch(plt.Rectangle((0, 0), bed, bed, fc="#f3f1ec", ec="#555", lw=1))
        for p in group:
            ring = np.vstack([p.outline, p.outline[:1]]) + p.offset
            is_tray = p.name.startswith("tray")
            ax.fill(ring[:, 0], ring[:, 1], fc="#b08968" if is_tray else "#e9dcc3", ec="#3a2a1a", lw=0.6)
        ax.set_xlim(-4, bed + 4)
        ax.set_ylim(-4, bed + 4)
        ax.set_aspect("equal")
        ax.set_title(_("Плита {n}: {count} шт.").format(n=plate + 1, count=len(group)), fontsize=10)
    fig.tight_layout()
    fig.savefig(out / "preview_plates.png")
    plt.close(fig)


# ----------------------------------------------------------------------------
# Повний цикл
# ----------------------------------------------------------------------------


def _export(out: Path, o: Options, relief: Relief | None, pieces: list[Part], tray: list[Part], previews: bool) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    for old in list(out.glob("plate_*.3mf")) + list(out.glob("all_plates.3mf")):
        old.unlink()

    n_piece_plates = pack(pieces, o.usable, o.gap)
    n_tray_plates = pack(tray, o.usable, o.gap, first_plate=n_piece_plates) if tray else 0
    everything = pieces + tray
    center_plates(everything, o.bed)

    groups: dict[int, list[Part]] = {}
    for p in everything:
        groups.setdefault(p.plate, []).append(p)
    plates = []
    for plate, group in sorted(groups.items()):
        kind = "tray" if group[0].name.startswith("tray") else "pieces"
        path = out / f"plate_{plate + 1:02d}_{kind}.3mf"
        write_3mf(path, group)
        plates.append(
            {
                "index": plate + 1,
                "kind": kind,
                "file": str(path.resolve()),
                "count": len(group),
                "triangles": int(sum(len(p.tris) for p in group)),
                "outlines": [np.round(p.outline + p.offset, 2).tolist() for p in group],
            }
        )
    names, counters = {}, {"pieces": 0, "tray": 0}
    for entry in plates:
        counters[entry["kind"]] += 1
        label = _("Рамка {n}") if entry["kind"] == "tray" else _("Деталі {n}")
        names[entry["index"] - 1] = label.format(n=counters[entry["kind"]])
    # Єдиний проєкт з усіма плитами — якщо встановлено Bambu Studio, з якого можна взяти налаштування друку.
    project = None
    try:
        import bambu

        config = bambu.project_settings(o.bed)
        if config:
            project = out / "all_plates.3mf"
            write_project(project, groups, o.bed, names, config, bambu.version())
    except Exception:  # єдиний проєкт — зручність, а не необхідність: окремі плити вже записано
        project = None
    if previews:
        save_previews(out, relief, pieces if relief is not None else [], groups, o.bed)
    return {
        "out": str(out.resolve()),
        "project": str(project.resolve()) if project else None,
        "bed": o.bed,
        "pieces": len(pieces),
        "piece_plates": n_piece_plates,
        "tray_plates": n_tray_plates,
        "tray_parts": len(tray),
        "triangles": int(sum(p["triangles"] for p in plates)),
        "plates": plates,
    }


def generate(relief: Relief, out: Path, o: Options, *, previews: bool = True) -> dict:
    """Ріже рельєф на деталі, розкладає по плитах і пише 3MF. Повертає зведення."""
    cols, rows = grid_for(relief.width, relief.height, o)
    pieces = cut_pieces(relief, cols, rows, o)
    tray = make_tray(relief.width, relief.height, o) if o.tray else []
    summary = _export(out, o, relief, pieces, tray, previews)
    summary.update(width=relief.width, height=relief.height, cols=cols, rows=rows, thickness=[o.base, o.base + o.relief])
    return summary


def generate_fit_test(out: Path, o: Options, gaps: list[float], *, previews: bool = True) -> dict:
    """Тест посадки: пари деталей із різним зазором. Кількість крапок = номер пари."""
    cell = o.piece
    w, h = 2 * cell, cell
    nx, ny = round(w / o.res) + 1, round(h / o.res) + 1
    gx, gy = np.meshgrid(np.linspace(0, w, nx), np.linspace(0, h, ny))
    parts = []
    for n, gap in enumerate(gaps, start=1):
        z = np.full((ny, nx), o.base)
        for side in (0.25, 0.75):  # крапки на обох деталях пари
            for q in range(n):
                cx = w * side + (q - (n - 1) / 2) * 2.6
                z = np.maximum(z, o.base + 0.8 * np.clip(1.3 - np.hypot(gx - cx, gy - h * 0.22) / 0.9, 0, 1))
        variant = Options(**{**vars(o), "clearance": gap})
        parts += cut_pieces(Relief(z, w, h), 2, 1, variant, jitter=0.0, prefix=f"gap{gap:.2f}_")
    summary = _export(out, o, None, parts, [], previews)
    summary.update(gaps=gaps)
    return summary


def main():
    d = Options()
    ap = argparse.ArgumentParser(
        description=_("Рельєфний 3D-пазл: карта висот → деталі пазла → плити для друку (3MF)."),
        epilog="uv run python puzzle.py heightmap.png --width 240 --piece 24 --tray",
    )
    ap.add_argument("heightmap", nargs="?", type=Path, help=_("карта висот (PNG/TIFF, біле = високо)"))
    ap.add_argument("-o", "--out", type=Path, default=None, help=_("тека результату"))
    g = ap.add_argument_group(_("розмір"))
    g.add_argument("--width", type=float, default=d.width, help=_("ширина пазла, мм (висота — за пропорцією)"))
    g.add_argument("--piece", type=float, default=d.piece, help=_("орієнтовний розмір деталі, мм"))
    g.add_argument("--cols", type=int, default=None, help=_("кількість стовпців (замість --piece)"))
    g.add_argument("--rows", type=int, default=None, help=_("кількість рядків (замість --piece)"))
    g.add_argument("--base", type=float, default=d.base, help=_("товщина основи, мм"))
    g.add_argument("--relief", type=float, default=d.relief, help=_("висота рельєфу над основою, мм"))
    g.add_argument("--invert", action="store_true", help=_("інвертувати карту висот"))
    g.add_argument("--smooth", type=float, default=d.smooth, help=_("згладжування рельєфу, мм"))
    g = ap.add_argument_group(_("розріз"))
    g.add_argument("--clearance", type=float, default=d.clearance, help=_("зазор між сусідніми деталями, мм"))
    g.add_argument("--corner", type=float, default=d.corner, help=_("радіус округлення кутів, мм"))
    g.add_argument("--chamfer", type=float, default=d.chamfer, help=_("фаска знизу деталей проти «слонячої ноги», мм (0 = без фаски)"))
    g.add_argument("--tab", type=float, default=d.tab, help=_("розмір замка (частка деталі)"))
    g.add_argument("--jitter", type=float, default=d.jitter, help=_("випадковість форми замків"))
    g.add_argument("--seed", type=int, default=d.seed, help=_("номер малюнка розрізу"))
    g = ap.add_argument_group(_("друк"))
    g.add_argument("--bed", type=float, default=d.bed, help=_("розмір столу, мм (A1 mini = 180)"))
    g.add_argument("--margin", type=float, default=d.margin, help=_("відступ від краю столу, мм"))
    g.add_argument("--gap", type=float, default=d.gap, help=_("відстань між деталями на плиті, мм"))
    g.add_argument("--res", type=float, default=d.res, help=_("крок сітки рельєфу, мм"))
    g.add_argument("--simplify", type=float, default=d.simplify, help=_("допуск спрощення сітки, мм (0 = вимкнути)"))
    g = ap.add_argument_group(_("рамка"))
    g.add_argument("--tray", action="store_true", help=_("додати рамку-піддон"))
    g.add_argument("--tray-floor", type=float, default=d.tray_floor, help=_("товщина дна рамки, мм"))
    g.add_argument("--tray-rim", type=float, default=d.tray_rim, help=_("ширина бортика, мм"))
    g.add_argument("--tray-rim-height", type=float, default=None, help=_("висота бортика над дном, мм"))
    g.add_argument("--tray-clearance", type=float, default=d.tray_clearance, help=_("зазор між пазлом і бортиком, мм"))
    ap.add_argument("--fit-test", metavar=_("ЗАЗОРИ"), nargs="?", const="0.10,0.15,0.20,0.25,0.30", default=None,
                    help=_("замість пазла згенерувати тест посадки (список зазорів через кому)"))
    args = ap.parse_args()
    o = Options(**{f.name: getattr(args, f.name) for f in fields(Options)})

    if args.fit_test:
        gaps = [float(g) for g in args.fit_test.split(",")]
        s = generate_fit_test(args.out or Path("out/fit_test"), o, gaps)
        print(_("Тест посадки: зазори {gaps} мм, {n} деталей").format(gaps=args.fit_test, n=s["pieces"]))
    else:
        if not args.heightmap:
            ap.error(_("потрібна карта висот (або --fit-test)"))
        relief = Relief.from_image(args.heightmap, o, args.invert)
        s = generate(relief, args.out or Path("out") / args.heightmap.stem, o)
        print(_("Пазл {w}×{h} мм, {cols}×{rows} = {n} деталей (~{pw}×{ph} мм), товщина {a}–{b} мм").format(
            w=f"{s['width']:.0f}", h=f"{s['height']:.0f}", cols=s["cols"], rows=s["rows"], n=s["pieces"],
            pw=f"{s['width'] / s['cols']:.1f}", ph=f"{s['height'] / s['rows']:.1f}", a=f"{o.base:.1f}", b=f"{o.base + o.relief:.1f}"))
    line = _("Плит: {n} з деталями").format(n=s["piece_plates"])
    if s["tray_parts"]:
        line += _(" + {n} з рамкою ({k} секц.)").format(n=s["tray_plates"], k=s["tray_parts"])
    print(line)
    print(_("Трикутників: {n} млн").format(n=f"{s['triangles'] / 1e6:.2f}"))
    if s.get("project"):
        print(_("Усі плити одним проєктом для Bambu Studio: {path}").format(path=s["project"]))
    print(_("Результат: {path}").format(path=s["out"]))


if __name__ == "__main__":
    main()
