"""Рельєфний пазл — застосунок із вікном.

Запуск:
    uv run python app.py             # окреме вікно
    uv run python app.py --browser   # у браузері

Усередині — маленький локальний сервер (лише 127.0.0.1) і сторінка зі static/.
Уся геометрія рахується тими самими функціями, що й у puzzle.py.
"""

from __future__ import annotations

import argparse
import json
import re
import secrets
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import tomllib
import traceback
import urllib.request
import webbrowser
from dataclasses import asdict, fields
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, quote, unquote, urlparse

import numpy as np
from PIL import Image

import settings
from i18n import _, get_lang, set_lang
from puzzle import Options, Relief, generate, generate_fit_test, grid_for, load_heightmap, piece_outlines

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
OUT_ROOT = ROOT / "out"
EXAMPLES = ROOT / "examples"
try:
    GALLERY = json.loads((EXAMPLES / "gallery.json").read_text(encoding="utf-8"))
except (OSError, ValueError):
    GALLERY = []
WINDOW = None  # вікно pywebview, якщо застосунок запущено у власному вікні
LOG = Path.home() / "Library" / "Logs" / "relief-puzzle.log"

REPO = "MykhailoKibkalo/relief-puzzle"
REPO_URL = f"https://github.com/{REPO}"
URLS = {"repo": REPO_URL, "issues": REPO_URL + "/issues", "download": REPO_URL + "#readme"}

MESH_EXT = {".stl", ".obj", ".ply", ".glb", ".gltf", ".off"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff", ".bmp"}
SLICERS = {
    "bambu": ("Bambu Studio", Path("/Applications/BambuStudio.app")),
    "orca": ("OrcaStudio", Path("/Applications/OrcaStudio.app")),
    "orcaslicer": ("OrcaSlicer", Path("/Applications/OrcaSlicer.app")),
}
MIME = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
        ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon"}
PREVIEW_PX = 560  # довша сторона рельєфу в 3D-перегляді
TOKEN = secrets.token_urlsafe(24)
NO_LOCK = {"open", "open_url", "update_check", "update_install", "settings"}  # не чіпають рельєф, тож не чекають на нього


def read_version(text: str | None = None) -> str:
    try:
        data = tomllib.loads(text) if text is not None else tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
        return str(data["project"]["version"])
    except (OSError, KeyError, ValueError):
        return "0"


def version_key(v: str) -> tuple:
    return tuple(int(x) for x in re.findall(r"\d+", v))


class UserError(Exception):
    """Помилка, текст якої можна показати людині як є."""


class Session:
    """Стан одного відкритого вікна: завантажений файл і поточний рельєф."""

    def __init__(self):
        self.lock = threading.Lock()
        self.tmp = Path(tempfile.mkdtemp(prefix="relief-puzzle-"))
        self.shape_params: dict = {}
        self.reset()

    def reset(self):
        self.file: Path | None = None
        self.name = ""
        self.kind = "blank"  # blank | photo | heightmap | mesh
        self.depth = None
        self.gray = None
        self.raw = np.zeros((300, 400))
        self.height = self.raw
        self.suggest = None
        self.base = None  # (ключ, барельєф): кеш найповільнішого кроку

    # -- джерело ---------------------------------------------------------------

    def load(self, path: Path, name: str, kind: str = "auto"):
        ext = path.suffix.lower()
        self.depth = self.gray = None
        self.suggest = None
        self.base = None
        if ext in MESH_EXT:
            from mesh2height import mesh_to_height

            h, w_mm, h_mm, relief_mm, note = mesh_to_height(path, px=2000)
            self.raw, self.kind = h, "mesh"
            self.suggest = {"width": round(w_mm, 1), "relief": round(relief_mm, 1)}
        elif ext in IMAGE_EXT:
            try:
                probe = Image.open(path)
                probe.load()
            except Exception as e:
                raise UserError(_("Не вдалося прочитати зображення. Спробуйте PNG або JPEG.")) from e
            if kind == "auto":
                looks = probe.mode in ("I;16", "I", "F") or re.search(r"height|depth|hmap|висот|глибин", name.lower())
                kind = "heightmap" if looks else "photo"
            if kind == "heightmap":
                arr = load_heightmap(path)
                if max(arr.shape) > 3000:
                    step = int(np.ceil(max(arr.shape) / 3000))
                    arr = arr[::step, ::step]
                self.raw, self.kind = arr, "heightmap"
            else:
                from heightmap import image_depth, load_image

                img = load_image(path, 2400)
                self.depth = image_depth(img, settings.load()["model"])
                self.gray = np.asarray(img.convert("L"), dtype=np.float64) / 255.0
                self.kind = "photo"
        else:
            raise UserError(_("Формат «{ext}» не підтримується. Підійдуть PNG, JPEG, WebP, TIFF, STL, OBJ, PLY, GLB.").format(ext=ext or name))
        self.file, self.name = path, name
        self.shape(self.shape_params)  # поточний рельєф завжди відповідає завантаженому файлу

    # -- рельєф ----------------------------------------------------------------

    def shape(self, p: dict) -> np.ndarray:
        self.shape_params = p
        invert = bool(p.get("invert"))
        floor = _num(p, "floor", 0.0, 0.0, 0.9)
        gamma = _num(p, "gamma", 1.0, 0.2, 5.0)
        if self.kind == "photo":
            from heightmap import bas_relief, shape_relief

            flatten = _num(p, "flatten", 0.6, 0.0, 1.0)
            if self.base is None or self.base[0] != (invert, flatten):
                self.base = ((invert, flatten), bas_relief(-self.depth if invert else self.depth, flatten))
            h = shape_relief(
                None,
                base=self.base[1],
                floor=floor,
                gamma=gamma,
                detail=_num(p, "detail", 0.6, 0.0, 3.0),
                detail_radius=0.006,
                flatten=flatten,
                texture=_num(p, "texture", 0.5, 0.0, 3.0),
                gray=self.gray,
                smooth=_num(p, "smooth", 0.0, 0.0, 1.0),
            )
        else:
            h = 1.0 - self.raw if invert else self.raw
            if floor > 0:
                h = np.clip((h - floor) / (1.0 - floor), 0.0, 1.0)
            if gamma != 1.0:
                h = h**gamma
            smooth = _num(p, "smooth", 0.0, 0.0, 1.0)
            if smooth > 0:
                from scipy import ndimage

                h = ndimage.gaussian_filter(h, smooth * max(h.shape) * 0.003)
        self.height = h
        return h

    def preview(self) -> tuple[bytes, int, int]:
        h = self.height
        scale = PREVIEW_PX / max(h.shape)
        w, hh = max(2, round(h.shape[1] * scale)), max(2, round(h.shape[0] * scale))
        small = Image.fromarray(h.astype(np.float32), mode="F").resize((w, hh), Image.Resampling.BOX if scale < 1 else Image.Resampling.BILINEAR)
        data = (np.clip(np.asarray(small), 0.0, 1.0) * 65535).astype("<u2")
        return data.tobytes(), w, hh

    def out_dir(self) -> Path:
        stem = re.sub(r"[^\w\-]+", "_", Path(self.name).stem, flags=re.UNICODE).strip("_") or "puzzle"
        return OUT_ROOT / stem


def _num(p: dict, key: str, default: float, lo: float, hi: float) -> float:
    try:
        v = float(p.get(key, default))
    except (TypeError, ValueError):
        return default
    return min(max(v, lo), hi) if np.isfinite(v) else default


_LIMITS = {
    "width": (40, 1200), "piece": (12, 120), "base": (0.8, 10), "relief": (0.4, 30), "clearance": (0.0, 1.0),
    "corner": (0.0, 2.0), "chamfer": (0.0, 1.0), "tab": (0.12, 0.3), "jitter": (0.0, 0.08), "bed": (100, 500),
    "margin": (0, 30), "gap": (0.5, 10), "tray_floor": (0.6, 5), "tray_rim": (3, 30), "tray_clearance": (0.1, 2),
}


def options_from(p: dict) -> Options:
    """Параметри з вікна -> Options. Усе чуже відкидаємо, числа затискаємо в розумні межі."""
    o = Options()
    o.bed = settings.load()["bed"]
    for f in fields(Options):
        if f.name not in p or p[f.name] is None:
            continue
        if f.name in _LIMITS:
            setattr(o, f.name, _num(p, f.name, getattr(o, f.name), *_LIMITS[f.name]))
        elif f.name == "seed":
            o.seed = int(_num(p, "seed", 1, 0, 2**31 - 1))
        elif f.name == "tray":
            o.tray = bool(p["tray"])
    # Для великих пазлів сітку робимо грубішою, щоб файли не розбухали.
    o.res = max(0.2, o.width / 1600)
    return o


def layout(session: Session, o: Options) -> dict:
    hpx, wpx = session.height.shape
    height = o.width * hpx / wpx
    cols, rows = grid_for(o.width, height, o)
    if cols * rows > 800:
        raise UserError(_("Виходить {n} деталей — це забагато. Зробіть деталі більшими або пазл меншим.").format(n=cols * rows))
    outlines = piece_outlines(o.width, height, cols, rows, o)
    return {
        "width": o.width,
        "height": height,
        "cols": cols,
        "rows": rows,
        "outlines": [np.round(pts, 2).tolist() for cs, pts in outlines.values()],
        "rim_height": o.rim_height,
    }


def current_settings() -> dict:
    s = settings.load()
    s["lang"] = s["lang"] or get_lang()
    return s


def rename_app(lang: str):
    """Назва застосунку перекладається разом з інтерфейсом: заголовок вікна — одразу, значок — якщо це безпечно."""
    set_lang(lang)
    try:
        if WINDOW is not None:
            WINDOW.title = _("Рельєфний пазл")
    except Exception:
        pass
    if WINDOW is None:
        return  # у браузері значок не чіпаємо: перейменовує лише сам застосунок
    try:
        import make_app

        wanted = ROOT / f"{make_app.NAMES[lang]}.app"
        others = [ROOT / f"{n}.app" for n in make_app.NAMES.values() if n != make_app.NAMES[lang]]
        if wanted.exists() or not any(p.exists() for p in others):
            return  # значок уже правильний або його тут не збирали
        dock = subprocess.run(["defaults", "read", "com.apple.dock", "persistent-apps"], capture_output=True, text=True, timeout=5).stdout
        if any(p.exists() and (p.name in dock or quote(p.name) in dock) for p in others):
            return  # значок закріплено в Dock: перейменування зламало б закріплення
        make_app.build(lang)
    except Exception:
        traceback.print_exc()


SESSION = Session()


class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *args):  # тиша в консолі
        pass

    # -- відповіді --------------------------------------------------------------

    def _send(self, status: int, body: bytes, ctype: str, extra: dict | None = None):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for k, v in (extra or {}).items():
            self.send_header(k, str(v))
        self.end_headers()
        self.wfile.write(body)

    def _json(self, obj, status: int = 200):
        self._send(status, json.dumps(obj, ensure_ascii=False).encode(), "application/json; charset=utf-8")

    def _local(self) -> bool:
        host = (self.headers.get("Host") or "").split(":")[0]
        return host in ("127.0.0.1", "localhost")

    # -- GET --------------------------------------------------------------------

    def do_GET(self):
        if not self._local():
            return self._json({"error": "forbidden"}, 403)
        path = unquote(urlparse(self.path).path)
        if path == "/":
            html = (STATIC / "index.html").read_text(encoding="utf-8").replace("__TOKEN__", TOKEN)
            return self._send(200, html.encode(), MIME[".html"])
        for prefix, folder in (("/static/", STATIC), ("/examples/thumbs/", EXAMPLES / "thumbs")):
            if path.startswith(prefix):
                target = (folder / path[len(prefix):]).resolve()
                if target.is_file() and target.is_relative_to(folder):
                    return self._send(200, target.read_bytes(), MIME.get(target.suffix, "application/octet-stream"))
        self._json({"error": "not found"}, 404)

    # -- POST -------------------------------------------------------------------

    def do_POST(self):
        if not self._local() or self.headers.get("X-Token") != TOKEN:
            return self._json({"error": "forbidden"}, 403)
        set_lang(self.headers.get("X-Lang"))
        url = urlparse(self.path)
        query = {k: v[0] for k, v in parse_qs(url.query).items()}
        body = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        name = url.path.removeprefix("/api/").replace("-", "_")
        handler = getattr(self, "api_" + name, None)
        if not url.path.startswith("/api/") or handler is None:
            return self._json({"error": "not found"}, 404)
        try:
            if name in NO_LOCK:
                result = handler(query, body)
            else:
                with SESSION.lock:
                    result = handler(query, body)
        except (UserError, RuntimeError) as e:
            return self._json({"error": str(e)}, 400)
        except Exception as e:  # несподіване: показуємо суть, деталі — в консоль
            traceback.print_exc()
            return self._json({"error": _("Внутрішня помилка: {e}").format(e=e)}, 500)
        if isinstance(result, tuple):
            return self._send(200, *result)
        self._json(result)

    # -- загальне ---------------------------------------------------------------

    def api_config(self, query, body):
        return {
            "defaults": asdict(Options()),
            "slicers": [{"id": k, "name": name} for k, (name, path) in SLICERS.items() if path.exists()],
            "gallery": [{"id": g["id"], "uk": g["uk"], "en": g["en"], "author": g["author"], "thumb": f"/examples/thumbs/{g['id']}.jpg"} for g in GALLERY],
            "source": self._source_info(),  # щоб після перезавантаження сторінки вікно знало, що вже відкрито
            "settings": current_settings(),
            "version": read_version(),
            "can_update": (ROOT / ".git").exists() and shutil.which("git") is not None,
            "out": str(OUT_ROOT).replace(str(Path.home()), "~", 1),
            "has_log": LOG.exists(),
        }

    def api_settings(self, query, body):
        p = json.loads(body or b"{}")
        changes = {}
        if p.get("lang") in ("uk", "en"):
            changes["lang"] = p["lang"]
        if p.get("model") in ("large", "small"):
            changes["model"] = p["model"]
        if "bed" in p:
            changes["bed"] = _num(p, "bed", 180.0, 100.0, 500.0)
        settings.save(changes)
        if "lang" in changes:
            rename_app(changes["lang"])
        return current_settings()

    def api_open(self, query, body):
        p = json.loads(body or b"{}")
        if p.get("target") == "out":
            OUT_ROOT.mkdir(parents=True, exist_ok=True)
            target = OUT_ROOT
        elif p.get("target") == "log":
            target = LOG
        else:
            target = Path(str(p.get("path", ""))).resolve()
            if not target.is_relative_to(OUT_ROOT.resolve()):
                target = Path("/nonexistent")
        if not target.exists():
            raise UserError(_("Файл не знайдено. Створіть файли ще раз."))
        app = p.get("app", "finder")
        if app == "finder":
            cmd = ["open", str(target)] if target.is_dir() or target == LOG else ["open", "-R", str(target)]
        elif app in SLICERS and SLICERS[app][1].exists():
            cmd = ["open", "-a", str(SLICERS[app][1]), str(target)]
        else:
            raise UserError(_("Цю програму не знайдено в теці «Програми»."))
        subprocess.run(cmd, check=False)
        return {"ok": True}

    def api_open_url(self, query, body):
        which = json.loads(body or b"{}").get("which")
        if which in URLS:  # лише наші власні адреси
            webbrowser.open(URLS[which])
        return {"ok": which in URLS}

    # -- оновлення --------------------------------------------------------------

    def api_update_check(self, query, body):
        try:
            req = urllib.request.Request(f"https://raw.githubusercontent.com/{REPO}/main/pyproject.toml", headers={"User-Agent": "relief-puzzle"})
            with urllib.request.urlopen(req, timeout=8) as r:
                latest = read_version(r.read().decode("utf-8"))
        except Exception as e:
            raise UserError(_("Не вдалося зв'язатися з GitHub. Перевірте інтернет і спробуйте ще раз.")) from e
        current = read_version()
        return {
            "current": current,
            "latest": latest,
            "newer": version_key(latest) > version_key(current),
            "can_install": (ROOT / ".git").exists() and shutil.which("git") is not None,
        }

    def api_update_install(self, query, body):
        if not (ROOT / ".git").exists() or shutil.which("git") is None:
            raise UserError(_("Цю копію встановлено не через git. Завантажте нову версію зі сторінки на GitHub."))
        r = subprocess.run(["git", "-C", str(ROOT), "pull", "--ff-only"], capture_output=True, text=True, timeout=180)
        if r.returncode != 0:
            lines = (r.stderr or r.stdout).strip().splitlines()
            raise UserError(_("Оновити автоматично не вдалося: {detail}").format(detail=lines[-1] if lines else r.returncode))
        uv = shutil.which("uv")
        if uv:  # нові залежності, якщо з'явилися
            subprocess.run([uv, "sync"], cwd=ROOT, capture_output=True, timeout=900)
        return {"version": read_version()}

    # -- джерело й рельєф -------------------------------------------------------

    def api_source(self, query, body):
        name = Path(query.get("name") or "file").name
        if not body:
            raise UserError(_("Файл порожній."))
        path = SESSION.tmp / ("source" + Path(name).suffix.lower())
        path.write_bytes(body)
        SESSION.load(path, name, query.get("kind", "auto"))
        return self._source_info()

    def api_example(self, query, body):
        wanted = json.loads(body or b"{}").get("id")
        entry = next((g for g in GALLERY if g["id"] == wanted), GALLERY[0] if GALLERY else None)
        path = EXAMPLES / f"{entry['id']}_height.png" if entry else None
        if path is None or not path.exists():
            raise UserError(_("Файл не знайдено. Створіть файли ще раз."))
        SESSION.load(path, f"{entry['id']}.png", "heightmap")
        return self._source_info()

    def api_kind(self, query, body):
        p = json.loads(body or b"{}")
        if SESSION.file is None or SESSION.kind == "mesh":
            return self._source_info()
        SESSION.load(SESSION.file, SESSION.name, p.get("kind") or SESSION.kind)
        return self._source_info()

    def _source_info(self):
        h = SESSION.raw if SESSION.depth is None else SESSION.depth
        return {"kind": SESSION.kind, "name": SESSION.name, "px": [int(h.shape[1]), int(h.shape[0])], "suggest": SESSION.suggest}

    def api_shape(self, query, body):
        SESSION.shape(json.loads(body or b"{}"))
        data, w, h = SESSION.preview()
        return data, "application/octet-stream", {"X-Width": w, "X-Height": h}

    def api_layout(self, query, body):
        return layout(SESSION, options_from(json.loads(body or b"{}")))

    # -- файли для друку --------------------------------------------------------

    def api_generate(self, query, body):
        if SESSION.kind == "blank":
            raise UserError(_("Спершу оберіть картинку, карту висот або 3D-модель."))
        o = options_from(json.loads(body or b"{}"))
        layout(SESSION, o)  # ті самі перевірки, що й у перегляді
        return generate(Relief.from_height(SESSION.height, o), SESSION.out_dir(), o, previews=False)

    def api_fit_test(self, query, body):
        o = options_from(json.loads(body or b"{}"))
        return generate_fit_test(OUT_ROOT / "fit_test", o, [0.10, 0.15, 0.20, 0.25, 0.30], previews=False)


def main():
    ap = argparse.ArgumentParser(description=_("Вікно застосунку «Рельєфний пазл»."))
    ap.add_argument("--browser", action="store_true", help=_("відкрити у браузері, а не в окремому вікні"))
    ap.add_argument("--no-open", action="store_true", help=_("лише запустити сервер (для перевірки)"))
    ap.add_argument("--port", type=int, default=0)
    args = ap.parse_args()

    # Щоб тимчасові файли прибиралися й тоді, коли процес зупиняють ззовні.
    signal.signal(signal.SIGTERM, lambda *a: sys.exit(0))
    server = ThreadingHTTPServer(("127.0.0.1", args.port), Handler)
    server.daemon_threads = True
    url = f"http://127.0.0.1:{server.server_address[1]}/"
    threading.Thread(target=server.serve_forever, daemon=True).start()
    try:
        if args.browser or args.no_open:
            print(url, flush=True)
            if not args.no_open:
                webbrowser.open(url)
            threading.Event().wait()
        else:
            import webview
            from webview.menu import Menu, MenuAction, MenuSeparator

            global WINDOW
            WINDOW = window = webview.create_window(_("Рельєфний пазл"), url, width=1360, height=880, min_size=(980, 640), background_color="#C9CCD1")

            def show(tab: str):
                return lambda: window.evaluate_js(f"window.openMenu && window.openMenu('{tab}')")

            menu = [
                Menu(_("Довідка"), [
                    MenuAction(_("Налаштування…"), show("settings")),
                    MenuAction(_("Про програму"), show("about")),
                    MenuAction(_("Перевірити оновлення"), show("updates")),
                    MenuSeparator(),
                    MenuAction(_("Сторінка на GitHub"), lambda: webbrowser.open(REPO_URL)),
                ])
            ]
            webview.start(menu=menu)
    except KeyboardInterrupt:
        pass
    finally:
        server.shutdown()
        shutil.rmtree(SESSION.tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
