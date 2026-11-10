"""3D-модель рельєфу (STL/OBJ/PLY/GLB) -> карта висот.

Запуск:
    uv run python mesh2height.py relief.stl -o relief_height.png

Модель «фотографується» згори ортографічно: для кожної точки береться
найвища поверхня. Вісь висоти й лицьовий бік визначаються автоматично
(найтонший вимір; бік, де більше рельєфу), за потреби є --up і --flip.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
from PIL import Image
from scipy import ndimage

from i18n import _


def rasterize_max_z(verts: np.ndarray, tris: np.ndarray, x0: float, y0: float, cell: float, nx: int, ny: int) -> np.ndarray:
    """Ортографічний z-буфер: найвища точка сітки над центром кожної клітинки."""
    grid = np.full(nx * ny, -np.inf)
    p = verts[tris]
    px, py, pz = (p[:, :, 0] - x0) / cell, (p[:, :, 1] - y0) / cell, p[:, :, 2]
    ix0, ix1 = np.ceil(px.min(1)).astype(np.int64), np.floor(px.max(1)).astype(np.int64)
    iy0, iy1 = np.ceil(py.min(1)).astype(np.int64), np.floor(py.max(1)).astype(np.int64)
    ix0, iy0 = np.maximum(ix0, 0), np.maximum(iy0, 0)
    ix1, iy1 = np.minimum(ix1, nx - 1), np.minimum(iy1, ny - 1)
    x1, x2, x3 = px.T
    y1, y2, y3 = py.T
    det = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
    size = np.maximum(ix1 - ix0, iy1 - iy0) + 1
    ok = (ix1 >= ix0) & (iy1 >= iy0) & (np.abs(det) > 1e-12)

    k = 1
    while True:
        sel = np.flatnonzero(ok & (size <= k) & (size > k // 2))
        chunk = max(1, 3_000_000 // (k * k))
        for s in range(0, len(sel), chunk):
            c = sel[s : s + chunk]
            ar = np.arange(k)
            gx = (ix0[c][:, None] + ar)[:, None, :]  # (n, 1, k)
            gy = (iy0[c][:, None] + ar)[:, :, None]  # (n, k, 1)
            e = lambda a: a[c][:, None, None]  # noqa: E731
            l1 = (e(y2 - y3) * (gx - e(x3)) + e(x3 - x2) * (gy - e(y3))) / e(det)
            l2 = (e(y3 - y1) * (gx - e(x3)) + e(x1 - x3) * (gy - e(y3))) / e(det)
            l3 = 1.0 - l1 - l2
            eps = -1e-9
            inside = (l1 >= eps) & (l2 >= eps) & (l3 >= eps) & (gx <= e(ix1)) & (gy <= e(iy1))
            z = l1 * e(pz[:, 0]) + l2 * e(pz[:, 1]) + l3 * e(pz[:, 2])
            idx = np.broadcast_to(gy * nx + gx, inside.shape)[inside]
            np.maximum.at(grid, idx, z[inside])
        if k >= size.max():
            break
        k *= 2
    return grid.reshape(ny, nx)


def view(verts: np.ndarray, tris: np.ndarray, up: int, from_below: bool, cell: float):
    """Карта висот при погляді вздовж осі `up` (згори або знизу)."""
    a, b = [ax for ax in range(3) if ax != up]
    if up == 1:  # зберігаємо праву трійку: (z, x, y)
        a, b = 2, 0
    v = np.column_stack([verts[:, a], verts[:, b], verts[:, up]])
    if from_below:  # дивимось із протилежного боку: дзеркалимо X, щоб картинка не була відбита
        v[:, 0] *= -1
        v[:, 2] *= -1
    lo, hi = v.min(0), v.max(0)
    nx, ny = int(np.ceil((hi[0] - lo[0]) / cell)), int(np.ceil((hi[1] - lo[1]) / cell))
    z = rasterize_max_z(v, tris, lo[0] + cell / 2, lo[1] + cell / 2, cell, nx, ny)
    return z, lo, hi


def mesh_to_height(path: Path, px: int = 2400, up: str = "auto", flip: bool = False, rotate: int = 0, floor: float = 0.0):
    """Повертає (висоти 0..1 з рядком 0 угорі, ширина мм, висота мм, висота рельєфу мм, опис)."""
    import trimesh

    mesh = trimesh.load(path, force="mesh")
    verts, tris = np.asarray(mesh.vertices, dtype=np.float64), np.asarray(mesh.faces)
    if len(tris) == 0:
        raise RuntimeError(_("У файлі немає поверхні (жодного трикутника)."))
    extent = verts.max(0) - verts.min(0)
    axis = int(np.argmin(extent)) if up == "auto" else "xyz".index(up)
    plane = [extent[ax] for ax in range(3) if ax != axis]
    cell = max(plane) / px

    # Лицьовий бік — той, де рельєф різноманітніший (тильний зазвичай плоский).
    # Пробуємо обидва на грубій сітці.
    coarse = max(plane) / 300
    scores = []
    for below in (False, True):
        z = view(verts, tris, axis, below, coarse)[0]
        scores.append(np.std(z[np.isfinite(z)]))
    below = bool(np.argmax(scores)) ^ flip

    z, lo, hi = view(verts, tris, axis, below, cell)
    empty = ~np.isfinite(z)
    zmin = z[~empty].min()
    z[empty] = zmin  # поза моделлю — рівень тла
    z = z[::-1]  # рядок 0 = верх картинки
    if rotate:
        z = np.rot90(z, k=rotate // 90)

    z0 = zmin + floor
    height = float(z.max() - z0)
    h = np.clip((z - z0) / max(height, 1e-9), 0.0, 1.0)
    # Прибираємо поодинокі «дірки» растеризації на стиках трикутників.
    h = np.where(ndimage.minimum_filter(h, 3) < h - 0.2, ndimage.median_filter(h, 3), h)

    w_mm, h_mm = (hi[0] - lo[0], hi[1] - lo[1]) if rotate in (0, 180) else (hi[1] - lo[1], hi[0] - lo[0])
    note = _("вісь висоти {axis}").format(axis="xyz"[axis]) + (_(" (тильний бік)") if below else "")
    return h, float(w_mm), float(h_mm), height, note


def main():
    ap = argparse.ArgumentParser(
        description=_("3D-модель рельєфу (STL/OBJ/PLY/GLB) → карта висот."),
        epilog="uv run python mesh2height.py relief.stl -o relief_height.png",
    )
    ap.add_argument("mesh", type=Path)
    ap.add_argument("-o", "--out", type=Path, default=None, help=_("куди зберегти карту висот (PNG, 16 біт)"))
    ap.add_argument("--px", type=int, default=2400, help=_("розмір довшої сторони карти висот, px"))
    ap.add_argument("--up", choices=["x", "y", "z", "auto"], default="auto", help=_("вісь висоти рельєфу"))
    ap.add_argument("--flip", action="store_true", help=_("узяти протилежний бік моделі"))
    ap.add_argument("--rotate", type=int, choices=[0, 90, 180, 270], default=0, help=_("повернути результат"))
    ap.add_argument("--floor", type=float, default=0.0, help=_("мм: відкинути нижню частину (товщину підкладки)"))
    args = ap.parse_args()

    h, w_mm, h_mm, height, note = mesh_to_height(args.mesh, args.px, args.up, args.flip, args.rotate, args.floor)
    out = args.out or args.mesh.with_name(args.mesh.stem + "_height.png")
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray((h * 65535).astype(np.uint16)).save(out)
    print(_("Карта висот: {path}  ({w}×{h} px)").format(path=out, w=h.shape[1], h=h.shape[0]))
    print(_("Модель: {w}×{h} мм, висота рельєфу {r} мм, {note}").format(w=f"{w_mm:.1f}", h=f"{h_mm:.1f}", r=f"{height:.2f}", note=note))
    print(_("Для масштабу 1:1:  puzzle.py {path} --width {w} --relief {r}").format(path=out, w=f"{w_mm:.1f}", r=f"{height:.2f}"))


if __name__ == "__main__":
    main()
