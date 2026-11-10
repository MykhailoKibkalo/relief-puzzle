import * as THREE from './vendor/three.module.min.js';

// ---------------------------------------------------------------------------
// Мови
// ---------------------------------------------------------------------------

const T = {
  uk: {
    'app.title': 'Рельєфний пазл',
    'menu.title': 'Меню',
    'close': 'Закрити',
    'unit.mm': 'мм',
    'exact': 'точне значення',

    'src.title': 'Зображення',
    'src.none': 'Файл ще не обрано',
    'src.pick': 'Обрати файл',
    'src.example': 'Спробувати на прикладі',
    'kind.aria': 'Як читати зображення',
    'kind.photo': 'Картинка',
    'kind.heightmap': 'Карта висот',
    'kind.hint.photo': 'Глибину оцінила нейромережа. Якщо це готова карта висот, перемкніть.',
    'kind.hint.heightmap': 'Біле вважається високим, чорне — низьким.',
    'kind.hint.mesh': 'Рельєф знято з 3D‑моделі. Ширину й висоту рельєфу взято з неї, їх можна змінити.',

    'shape.title': 'Рельєф',
    'shape.invert': 'Обернути: далеке зробити високим',
    'puzzle.title': 'Пазл',
    'fit.hint': 'Не знаєте, який зазор підійде вашому принтеру?',
    'fit.make': 'Створити тест посадки',
    'tray': 'Додати рамку',
    'reseed': 'Інший малюнок розрізу',
    'more': 'Додатково',
    'make': 'Створити файли для друку',

    'f.texture': 'Фактура поверхні',
    'f.detail': 'Чіткість деталей',
    'f.flatten': 'Вирівняти великі перепади',
    'f.floor': 'Рівне тло',
    'f.puff': 'Опуклість',
    'f.width': 'Ширина пазла',
    'f.piece': 'Розмір деталі',
    'f.relief': 'Висота рельєфу',
    'f.base': 'Товщина основи',
    'f.clearance': 'Зазор між деталями',
    'f.chamfer': 'Фаска знизу деталей',
    'f.tab': 'Розмір замків',

    'invite.text': 'Перетягніть сюди картинку, карту висот або 3D‑модель',
    'invite.sub': 'Підійдуть PNG, JPEG, WebP, TIFF, STL, OBJ, PLY і GLB.',
    'canvas.aria': 'Перегляд пазла. Тягніть мишею, щоб повернути.',
    'cam.aria': 'Кут огляду',
    'cam.tilt': 'Під кутом',
    'cam.top': 'Зверху',
    'drop': 'Відпустіть файл',
    'readout': '{w} × {h} мм, {c} × {r} = {pieces}, товщина {a}–{b} мм',

    'results.aria': 'Файли для друку',
    'reveal': 'Показати у Finder',
    'res.title': 'Файли готові: {plates} з деталями',
    'res.title.tray': ' і {n} з рамкою',
    'res.note': 'Кожна плита — окремий файл. Відкрийте її в слайсері, оберіть профіль друку й надішліть на принтер.',
    'res.fit.title': 'Тест посадки готовий',
    'res.fit.note': 'П’ять пар деталей із зазорами 0,10, 0,15, 0,20, 0,25 і 0,30 мм. Кількість крапок на деталі — номер пари. Яка пара складається щільно, але без зусилля, той зазор і поставте.',
    'plate.name': 'Плита {n}',
    'plate.section': 'секція рамки',
    'plate.open': 'Відкрити плиту {n} у {app}',
    'n.pieces': ['деталь', 'деталі', 'деталей'],
    'n.plates': ['плита', 'плити', 'плит'],
    'n.sections': ['секція рамки', 'секції рамки', 'секцій рамки'],

    'busy.mesh': 'Перетворюю 3D‑модель на карту висот.',
    'busy.image': 'Читаю зображення. Для картинки нейромережа оцінює глибину, це триває до пів хвилини.',
    'busy.depth': 'Нейромережа оцінює глибину, це триває до пів хвилини.',
    'busy.depth.again': 'Нейромережа оцінює глибину заново.',
    'busy.heightmap': 'Читаю карту висот.',
    'busy.example': 'Відкриваю приклад.',
    'busy.make': 'Ріжу рельєф на деталі й розкладаю по плитах.',
    'busy.fit': 'Створюю тест посадки.',
    'done.relief': 'Рельєф готовий. Налаштуйте пазл і створіть файли.',
    'done.updated': 'Рельєф оновлено.',
    'done.example': 'Це приклад: барельєф бізона. Налаштуйте пазл і створіть файли.',
    'done.make': 'Файли створено.',
    'done.fit': 'Тест посадки створено.',
    'err.server': 'Застосунок не відповідає. Закрийте вікно й відкрийте його знову.',
    'err.code': 'Не вдалося виконати дію (код {code}).',

    'tab.settings': 'Налаштування',
    'tab.about': 'Про програму',
    'tab.updates': 'Оновлення',
    'set.lang': 'Мова',
    'set.bed': 'Розмір столу принтера',
    'set.bed.hint': 'Bambu Lab A1 mini — 180 мм; A1, P1S і X1C — 256 мм.',
    'set.model': 'Нейромережа для картинок',
    'set.model.large': 'Точна (не для продажу виробів)',
    'set.model.small': 'Проста (можна для продажу)',
    'set.model.hint': 'Точна модель має некомерційну ліцензію CC BY‑NC 4.0, проста — Apache 2.0.',
    'set.out': 'Тека з файлами для друку',
    'set.log': 'Журнал роботи',
    'set.log.open': 'Відкрити журнал',
    'about.version': 'Версія {v}',
    'about.desc': 'Перетворює картинку або 3D‑модель на рельєфний пазл для 3D‑друку: ріже рельєф на деталі із зазором і розкладає їх по плитах принтера.',
    'about.github': 'Сторінка на GitHub',
    'about.issue': 'Повідомити про помилку',
    'about.license': 'Ліцензія MIT: програма безкоштовна, код відкритий.',
    'about.credits': 'Використано Depth Anything V2, Manifold, Three.js і pywebview.',
    'upd.current': 'Встановлено версію {v}.',
    'upd.check': 'Перевірити оновлення',
    'upd.checking': 'Перевіряю.',
    'upd.latest': 'У вас найновіша версія.',
    'upd.available': 'Доступна версія {v}.',
    'upd.install': 'Оновити',
    'upd.open': 'Відкрити сторінку завантаження',
    'upd.installing': 'Оновлюю.',
    'upd.done': 'Оновлено до версії {v}. Закрийте застосунок і відкрийте його знову.',
  },
  en: {
    'app.title': 'Relief Puzzle',
    'menu.title': 'Menu',
    'close': 'Close',
    'unit.mm': 'mm',
    'exact': 'exact value',

    'src.title': 'Image',
    'src.none': 'No file chosen yet',
    'src.pick': 'Choose file',
    'src.example': 'Try the example',
    'kind.aria': 'How to read the image',
    'kind.photo': 'Picture',
    'kind.heightmap': 'Height map',
    'kind.hint.photo': 'Depth was estimated by a neural network. If this is already a height map, switch over.',
    'kind.hint.heightmap': 'White is high, black is low.',
    'kind.hint.mesh': 'The relief was taken from the 3D model. Width and relief height come from it; you can change them.',

    'shape.title': 'Relief',
    'shape.invert': 'Invert: make far areas high',
    'puzzle.title': 'Puzzle',
    'fit.hint': 'Not sure which gap suits your printer?',
    'fit.make': 'Create a fit test',
    'tray': 'Add a frame',
    'reseed': 'Another cut pattern',
    'more': 'More options',
    'make': 'Create print files',

    'f.texture': 'Surface texture',
    'f.detail': 'Detail sharpness',
    'f.flatten': 'Flatten large steps',
    'f.floor': 'Flat background',
    'f.puff': 'Fullness',
    'f.width': 'Puzzle width',
    'f.piece': 'Piece size',
    'f.relief': 'Relief height',
    'f.base': 'Base thickness',
    'f.clearance': 'Gap between pieces',
    'f.chamfer': 'Bottom chamfer',
    'f.tab': 'Tab size',

    'invite.text': 'Drop a picture, a height map or a 3D model here',
    'invite.sub': 'PNG, JPEG, WebP, TIFF, STL, OBJ, PLY and GLB all work.',
    'canvas.aria': 'Puzzle preview. Drag to rotate.',
    'cam.aria': 'Viewing angle',
    'cam.tilt': 'Angled',
    'cam.top': 'Top',
    'drop': 'Drop the file',
    'readout': '{w} × {h} mm, {c} × {r} = {pieces}, {a}–{b} mm thick',

    'results.aria': 'Print files',
    'reveal': 'Show in Finder',
    'res.title': 'Files ready: {plates} with pieces',
    'res.title.tray': ' and {n} with the frame',
    'res.note': 'Each plate is a separate file. Open it in your slicer, pick a print profile and send it to the printer.',
    'res.fit.title': 'Fit test ready',
    'res.fit.note': 'Five pairs of pieces with gaps of 0.10, 0.15, 0.20, 0.25 and 0.30 mm. The number of dots on a piece is the pair number. Use the gap of the pair that goes together snugly without force.',
    'plate.name': 'Plate {n}',
    'plate.section': 'frame section',
    'plate.open': 'Open plate {n} in {app}',
    'n.pieces': ['piece', 'pieces'],
    'n.plates': ['plate', 'plates'],
    'n.sections': ['frame section', 'frame sections'],

    'busy.mesh': 'Converting the 3D model to a height map.',
    'busy.image': 'Reading the image. For a picture, a neural network estimates depth; this takes up to half a minute.',
    'busy.depth': 'A neural network is estimating depth; this takes up to half a minute.',
    'busy.depth.again': 'Estimating depth again.',
    'busy.heightmap': 'Reading the height map.',
    'busy.example': 'Opening the example.',
    'busy.make': 'Cutting the relief into pieces and arranging them on plates.',
    'busy.fit': 'Creating the fit test.',
    'done.relief': 'The relief is ready. Adjust the puzzle and create the files.',
    'done.updated': 'Relief updated.',
    'done.example': 'This is the example: a bison bas-relief. Adjust the puzzle and create the files.',
    'done.make': 'Files created.',
    'done.fit': 'Fit test created.',
    'err.server': 'The app is not responding. Close the window and open it again.',
    'err.code': 'The action failed (code {code}).',

    'tab.settings': 'Settings',
    'tab.about': 'About',
    'tab.updates': 'Updates',
    'set.lang': 'Language',
    'set.bed': 'Printer bed size',
    'set.bed.hint': 'Bambu Lab A1 mini is 180 mm; A1, P1S and X1C are 256 mm.',
    'set.model': 'Neural network for pictures',
    'set.model.large': 'Accurate (not for selling prints)',
    'set.model.small': 'Basic (fine for selling prints)',
    'set.model.hint': 'The accurate model is licensed CC BY‑NC 4.0 (non‑commercial); the basic one is Apache 2.0.',
    'set.out': 'Folder with print files',
    'set.log': 'Log file',
    'set.log.open': 'Open log',
    'about.version': 'Version {v}',
    'about.desc': 'Turns a picture or a 3D model into a relief jigsaw puzzle for 3D printing: cuts the relief into pieces with a gap and arranges them on printer plates.',
    'about.github': 'GitHub page',
    'about.issue': 'Report a problem',
    'about.license': 'MIT license: free and open source.',
    'about.credits': 'Built with Depth Anything V2, Manifold, Three.js and pywebview.',
    'upd.current': 'Version {v} is installed.',
    'upd.check': 'Check for updates',
    'upd.checking': 'Checking.',
    'upd.latest': 'You have the latest version.',
    'upd.available': 'Version {v} is available.',
    'upd.install': 'Update',
    'upd.open': 'Open the download page',
    'upd.installing': 'Updating.',
    'upd.done': 'Updated to version {v}. Close the app and open it again.',
  },
};

let lang = (navigator.language || 'en').toLowerCase().startsWith('uk') ? 'uk' : 'en';

function t(key, vars) {
  let s = T[lang][key] ?? T.uk[key] ?? key;
  for (const [k, v] of Object.entries(vars || {})) s = s.replaceAll(`{${k}}`, v);
  return s;
}

/** «3 деталі» / «3 pieces»: число з правильною формою слова. */
function count(n, key) {
  const forms = T[lang][key];
  let form;
  if (lang === 'uk') {
    const a = Math.abs(n) % 100, b = a % 10;
    form = a > 10 && a < 20 ? forms[2] : b === 1 ? forms[0] : b >= 2 && b <= 4 ? forms[1] : forms[2];
  } else {
    form = n === 1 ? forms[0] : forms[1];
  }
  return `${n} ${form}`;
}

const $ = (id) => document.getElementById(id);
const fmt = (v, d = 1) => Number(v).toLocaleString(lang === 'uk' ? 'uk-UA' : 'en-US', { maximumFractionDigits: d });
const clamp = (v, lo, hi) => Math.min(Math.max(v, lo), hi);

// ---------------------------------------------------------------------------
// Сервер
// ---------------------------------------------------------------------------

async function api(path, opts = {}) {
  const headers = { 'X-Token': window.TOKEN, 'X-Lang': lang };
  let body = opts.body;
  if (opts.json !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(opts.json);
  }
  let r;
  try {
    r = await fetch('/api/' + path, { method: 'POST', headers, body });
  } catch {
    throw new Error(t('err.server'));
  }
  if (!r.ok) {
    let message = t('err.code', { code: r.status });
    try { message = (await r.json()).error || message; } catch { /* тіло не JSON */ }
    throw new Error(message);
  }
  return r;
}

// ---------------------------------------------------------------------------
// Сцена: гіпсовий рельєф на фотофоні
// ---------------------------------------------------------------------------

class Stage {
  constructor(canvas, host) {
    this.canvas = canvas;
    this.host = host;
    this.renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
    this.renderer.toneMappingExposure = 1.05;

    this.scene = new THREE.Scene();
    this.camera = new THREE.PerspectiveCamera(30, 1, 1, 8000);
    this.camera.up.set(0, 0, 1);
    this.target = new THREE.Vector3(0, 0, 2);
    this.view = { theta: -0.3, phi: 0.74, dist: 420 };

    const sky = new THREE.HemisphereLight(0xffffff, 0x8f959d, 0.62);
    sky.position.set(0, 0, 1);
    // Основне світло падає низько згори зліва: так рельєф читається найкраще.
    const key = new THREE.DirectionalLight(0xfff0d8, 3.9);
    key.position.set(-0.8, 0.7, 0.36);
    const fill = new THREE.DirectionalLight(0xdbe6ff, 0.3);
    fill.position.set(0.8, -0.6, 0.7);
    this.scene.add(sky, key, fill);

    this.ivory = new THREE.MeshStandardMaterial({
      color: 0xefe6d2, roughness: 0.86, metalness: 0,
      polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1,
    });
    this.brown = new THREE.MeshStandardMaterial({ color: 0x6b4a36, roughness: 0.72, metalness: 0 });
    this.seam = new THREE.LineBasicMaterial({ color: 0x3a2b1f, transparent: true, opacity: 0.62 });
    this.shadowMat = new THREE.MeshBasicMaterial({
      map: Stage.shadowTexture(), transparent: true, depthWrite: false, opacity: 0.5, toneMapped: false,
    });

    this.parts = { surface: null, walls: null, lines: null, tray: null, shadow: null };
    this.W = 170; this.H = 128; this.base = 2.4; this.relief = 5;
    this.hm = null; this.outlines = []; this.tray = null;

    this.bindPointer();
    new ResizeObserver(() => this.resize()).observe(host);
    this.resize();
  }

  static shadowTexture() {
    const c = document.createElement('canvas');
    c.width = c.height = 256;
    const g = c.getContext('2d');
    g.shadowColor = 'rgba(20, 24, 30, 0.9)';
    g.shadowBlur = 34;
    g.fillStyle = 'rgba(20, 24, 30, 0.9)';
    g.fillRect(52, 52, 152, 152);
    return new THREE.CanvasTexture(c);
  }

  bindPointer() {
    let drag = null;
    const c = this.canvas;
    c.addEventListener('pointerdown', (e) => { drag = { x: e.clientX, y: e.clientY }; c.setPointerCapture(e.pointerId); });
    c.addEventListener('pointermove', (e) => {
      if (!drag) return;
      this.view.theta -= (e.clientX - drag.x) * 0.006;
      this.view.phi = clamp(this.view.phi - (e.clientY - drag.y) * 0.006, 0.001, 1.46);
      drag = { x: e.clientX, y: e.clientY };
      this.onOrbit?.();
      this.draw();
    });
    const end = () => { drag = null; };
    c.addEventListener('pointerup', end);
    c.addEventListener('pointercancel', end);
    c.addEventListener('wheel', (e) => {
      e.preventDefault();
      this.view.dist = clamp(this.view.dist * Math.exp(e.deltaY * 0.0012), this.fitDist * 0.25, this.fitDist * 2.5);
      this.draw();
    }, { passive: false });
  }

  resize() {
    const w = Math.max(1, this.host.clientWidth), h = Math.max(1, this.host.clientHeight);
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.fit();
  }

  footprint() {
    const tr = this.tray;
    const pad = tr ? 2 * (tr.clearance + tr.rim) : 0;
    return [this.W + pad, this.H + pad];
  }

  fit() {
    const [w, h] = this.footprint();
    const fovV = THREE.MathUtils.degToRad(this.camera.fov);
    const fovH = 2 * Math.atan(Math.tan(fovV / 2) * this.camera.aspect);
    this.fitDist = (0.5 * Math.hypot(w, h)) / Math.sin(Math.min(fovV, fovH) / 2) * 0.88;
    this.view.dist = this.fitDist;
    this.draw();
  }

  setView(name) {
    Object.assign(this.view, name === 'top' ? { theta: 0, phi: 0.001 } : { theta: -0.3, phi: 0.74 });
    this.fit();
  }

  setSurface(hm, hw, hh) {
    this.hm = hm; this.hw = hw; this.hh = hh;
  }

  setPuzzle(W, H, outlines) {
    const resized = W !== this.W || H !== this.H;
    this.W = W; this.H = H; this.outlines = outlines;
    this.rebuild();
    if (resized) this.fit();
  }

  setThickness(base, relief) {
    this.base = base; this.relief = relief;
    this.rebuild();
  }

  setTray(tray) {
    const changed = !!tray !== !!this.tray;
    this.tray = tray;
    this.rebuildTray();
    if (changed) this.fit(); else this.draw();
  }

  drop(name) {
    const obj = this.parts[name];
    if (!obj) return;
    this.scene.remove(obj);
    obj.traverse((o) => o.geometry?.dispose());
    this.parts[name] = null;
  }

  heightAt(x, y) {
    const { hm, hw, hh } = this;
    const u = clamp(x / this.W, 0, 1) * (hw - 1), v = clamp(1 - y / this.H, 0, 1) * (hh - 1);
    const i = Math.min(Math.floor(u), hw - 2), j = Math.min(Math.floor(v), hh - 2);
    const fu = u - i, fv = v - j, q = j * hw + i;
    const top = hm[q] * (1 - fu) + hm[q + 1] * fu, bot = hm[q + hw] * (1 - fu) + hm[q + hw + 1] * fu;
    return this.base + this.relief * (top * (1 - fv) + bot * fv) / 65535;
  }

  rebuild() {
    if (!this.hm) return;
    const { hm, hw, hh, W, H, base, relief } = this;
    this.drop('surface'); this.drop('walls'); this.drop('lines');

    // Верхня поверхня: сітка з висотами.
    const pos = new Float32Array(hw * hh * 3);
    for (let j = 0, k = 0, q = 0; j < hh; j++) {
      const y = (0.5 - j / (hh - 1)) * H;
      for (let i = 0; i < hw; i++, k += 3, q++) {
        pos[k] = (i / (hw - 1) - 0.5) * W;
        pos[k + 1] = y;
        pos[k + 2] = base + relief * hm[q] / 65535;
      }
    }
    const idx = new Uint32Array((hw - 1) * (hh - 1) * 6);
    for (let j = 0, n = 0; j < hh - 1; j++) {
      for (let i = 0; i < hw - 1; i++) {
        const a = j * hw + i, b = a + 1, c = a + hw, d = c + 1;
        idx[n++] = c; idx[n++] = d; idx[n++] = b;
        idx[n++] = c; idx[n++] = b; idx[n++] = a;
      }
    }
    const top = new THREE.BufferGeometry();
    top.setAttribute('position', new THREE.BufferAttribute(pos, 3));
    top.setIndex(new THREE.BufferAttribute(idx, 1));
    top.computeVertexNormals();
    this.parts.surface = new THREE.Mesh(top, this.ivory);

    // Бокові стінки: обхід краю проти годинникової стрілки (якщо дивитися згори).
    const ring = [];
    for (let i = 0; i < hw; i++) ring.push((hh - 1) * hw + i);
    for (let j = hh - 2; j >= 0; j--) ring.push(j * hw + hw - 1);
    for (let i = hw - 2; i >= 0; i--) ring.push(i);
    for (let j = 1; j < hh; j++) ring.push(j * hw);
    const side = new Float32Array((ring.length - 1) * 18);
    for (let s = 0, k = 0; s < ring.length - 1; s++) {
      const p = ring[s] * 3, q = ring[s + 1] * 3;
      const px = pos[p], py = pos[p + 1], pz = pos[p + 2], qx = pos[q], qy = pos[q + 1], qz = pos[q + 2];
      side.set([px, py, 0, qx, qy, 0, qx, qy, qz, px, py, 0, qx, qy, qz, px, py, pz], k);
      k += 18;
    }
    const walls = new THREE.BufferGeometry();
    walls.setAttribute('position', new THREE.BufferAttribute(side, 3));
    walls.computeVertexNormals();
    this.parts.walls = new THREE.Mesh(walls, this.ivory);

    // Шви між деталями лягають на поверхню рельєфу.
    const seg = [];
    for (const poly of this.outlines) {
      for (let k = 0, n = poly.length; k < n; k++) {
        const a = poly[k], b = poly[(k + 1) % n];
        seg.push(a[0] - W / 2, a[1] - H / 2, this.heightAt(a[0], a[1]) + 0.04,
                 b[0] - W / 2, b[1] - H / 2, this.heightAt(b[0], b[1]) + 0.04);
      }
    }
    const lines = new THREE.BufferGeometry();
    lines.setAttribute('position', new THREE.BufferAttribute(new Float32Array(seg), 3));
    this.parts.lines = new THREE.LineSegments(lines, this.seam);

    this.scene.add(this.parts.surface, this.parts.walls, this.parts.lines);
    this.rebuildTray();
  }

  rebuildTray() {
    this.drop('tray'); this.drop('shadow');
    const [fw, fh] = this.footprint();
    const tr = this.tray;
    if (tr) {
      const g = new THREE.Group();
      const iw = this.W + 2 * tr.clearance, ih = this.H + 2 * tr.clearance;
      const box = (w, h, d, x, y, z) => {
        const m = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), this.brown);
        m.position.set(x, y, z);
        g.add(m);
      };
      box(fw, fh, tr.floor, 0, 0, -tr.floor / 2);
      box(tr.rim, fh, tr.rimHeight, -(iw + tr.rim) / 2, 0, tr.rimHeight / 2);
      box(tr.rim, fh, tr.rimHeight, (iw + tr.rim) / 2, 0, tr.rimHeight / 2);
      box(iw, tr.rim, tr.rimHeight, 0, -(ih + tr.rim) / 2, tr.rimHeight / 2);
      box(iw, tr.rim, tr.rimHeight, 0, (ih + tr.rim) / 2, tr.rimHeight / 2);
      this.parts.tray = g;
      this.scene.add(g);
    }
    // М'яка тінь під виробом, трохи зсунута від світла.
    const k = 256 / 152;
    const shadow = new THREE.Mesh(new THREE.PlaneGeometry(fw * k, fh * k), this.shadowMat);
    shadow.position.set(fw * 0.018, -fh * 0.03, tr ? -tr.floor - 0.06 : -0.06);
    this.parts.shadow = shadow;
    this.scene.add(shadow);
    this.draw();
  }

  draw() {
    if (this.pending) return;
    this.pending = requestAnimationFrame(() => {
      this.pending = 0;
      const { theta, phi, dist } = this.view, s = Math.sin(phi);
      this.camera.position.set(
        this.target.x + dist * s * Math.sin(theta),
        this.target.y - dist * s * Math.cos(theta),
        this.target.z + dist * Math.cos(phi),
      );
      this.camera.lookAt(this.target);
      this.renderer.render(this.scene, this.camera);
    });
  }
}

// ---------------------------------------------------------------------------
// Поля керування
// ---------------------------------------------------------------------------

const FIELDS = {
  texture:   { group: 'shape', min: 0, max: 2, step: 0.05, value: 0.5, kinds: ['photo'] },
  detail:    { group: 'shape', min: 0, max: 1.5, step: 0.05, value: 0.6, kinds: ['photo'] },
  flatten:   { group: 'shape', min: 0, max: 1, step: 0.05, value: 0, kinds: ['photo'] },
  floor:     { group: 'shape', min: 0, max: 0.8, step: 0.01, value: 0, kinds: ['photo', 'heightmap', 'mesh'] },
  puff:      { group: 'shape', min: -1, max: 1, step: 0.05, value: 0, kinds: ['photo', 'heightmap', 'mesh'] },

  width:     { group: 'puzzle', unit: true, min: 60, max: 600, step: 1, value: 170, on: 'layout' },
  piece:     { group: 'puzzle', unit: true, min: 14, max: 60, step: 1, value: 24, on: 'layout' },
  relief:    { group: 'puzzle', unit: true, min: 1, max: 15, step: 0.1, value: 5, on: 'surface' },
  base:      { group: 'puzzle', unit: true, min: 1.2, max: 6, step: 0.1, value: 2.4, on: 'surface' },
  clearance: { group: 'puzzle', unit: true, min: 0.05, max: 0.4, step: 0.01, value: 0.2, on: 'layout' },

  chamfer:   { group: 'more', unit: true, min: 0, max: 0.6, step: 0.05, value: 0.3 },
  tab:       { group: 'more', min: 0.14, max: 0.26, step: 0.01, value: 0.2, on: 'layout' },
};
const TRAY = { rim: 6, clearance: 0.4, floor: 1.2 };

const values = {};
let seed = 1;
let source = { kind: 'blank' };
let layout = null;
let config = { slicers: [], version: '', out: '', can_update: false };
let settings = { lang, bed: 180, model: 'large' };
let lastResult = null;   // { summary, kind: 'puzzle' | 'fit' }
let lastStatus = null;   // { key, vars, cls } або { text, cls }
let busy = 0;

function buildFields() {
  for (const [key, f] of Object.entries(FIELDS)) {
    values[key] = f.value;
    const el = document.createElement('div');
    el.className = 'field';
    el.dataset.key = key;
    el.innerHTML = `
      <div class="field-head">
        <label for="f-${key}"></label>
        <span class="value"><input type="number" id="n-${key}">${f.unit ? '<span data-i18n="unit.mm"></span>' : ''}</span>
      </div>
      <input type="range" id="f-${key}">`;
    document.querySelector(`[data-fields="${f.group}"]`).append(el);
    const range = el.querySelector('input[type=range]'), num = el.querySelector('input[type=number]');
    for (const input of [range, num]) Object.assign(input, { min: f.min, max: f.max, step: f.step, value: f.value });
    range.addEventListener('input', () => { num.value = range.value; values[key] = +range.value; changed(key); });
    num.addEventListener('change', () => {
      const v = clamp(Number.isFinite(+num.value) ? +num.value : f.value, f.min, f.max);
      num.value = range.value = v; values[key] = v; changed(key);
    });
  }
}

function setValue(key, v) {
  const f = FIELDS[key];
  v = clamp(v, f.min, f.max);
  values[key] = v;
  $('f-' + key).value = v;
  $('n-' + key).value = v;
}

const shapeParams = () => ({
  texture: values.texture, detail: values.detail, flatten: values.flatten, floor: values.floor,
  gamma: 2 ** -values.puff, invert: $('invert').checked,
});
const puzzleParams = () => ({
  width: values.width, piece: values.piece, relief: values.relief, base: values.base,
  clearance: values.clearance, bed: settings.bed, chamfer: values.chamfer, tab: values.tab,
  tray: $('tray').checked, seed,
});
const trayShape = () => ($('tray').checked
  ? { ...TRAY, rimHeight: values.base + Math.min(values.relief * 0.4, 2) }
  : null);

// ---------------------------------------------------------------------------
// Стан і статус
// ---------------------------------------------------------------------------

function renderStatus() {
  const s = lastStatus;
  $('status').textContent = !s ? '' : s.key ? t(s.key, s.vars) : s.text;
  $('status').className = 'status ' + (s?.cls || '');
}
function setStatus(key, cls = '', vars) {
  lastStatus = key ? { key, vars, cls } : null;
  renderStatus();
}
function fail(e) {
  lastStatus = { text: e.message, cls: 'bad' };
  renderStatus();
}

function refreshButtons() {
  const idle = busy === 0;
  $('make').disabled = !idle || source.kind === 'blank';
  for (const id of ['pick', 'example', 'fit', 'model']) $(id).disabled = !idle;
  for (const r of document.querySelectorAll('input[name=kind]')) r.disabled = !idle;
}

async function work(key, fn) {
  busy++;
  setStatus(key, 'busy');
  refreshButtons();
  try {
    await fn();
  } catch (e) {
    fail(e);
  } finally {
    busy--;
    refreshButtons();
  }
}

const debounce = (fn, ms) => {
  let timer;
  return () => { clearTimeout(timer); timer = setTimeout(fn, ms); };
};

// ---------------------------------------------------------------------------
// Оновлення перегляду
// ---------------------------------------------------------------------------

let stage;
let shapeSeq = 0, layoutSeq = 0;

async function refreshShape() {
  const mine = ++shapeSeq;
  const r = await api('shape', { json: shapeParams() });
  const buf = await r.arrayBuffer();
  if (mine !== shapeSeq) return;
  stage.setSurface(new Uint16Array(buf), +r.headers.get('X-Width'), +r.headers.get('X-Height'));
  await refreshLayout();
}

async function refreshLayout() {
  const mine = ++layoutSeq;
  const r = await (await api('layout', { json: puzzleParams() })).json();
  if (mine !== layoutSeq) return;
  layout = r;
  stage.base = values.base; stage.relief = values.relief;
  stage.tray = trayShape();
  stage.setPuzzle(r.width, r.height, r.outlines);
  updateReadout();
  if (lastStatus?.cls === 'bad') setStatus(null);
}

const shapeSoon = debounce(() => refreshShape().catch(fail), 160);
const layoutSoon = debounce(() => refreshLayout().catch(fail), 110);

function updateReadout() {
  if (!layout) return;
  $('readout').textContent = t('readout', {
    w: fmt(layout.width, 0), h: fmt(layout.height, 0), c: layout.cols, r: layout.rows,
    pieces: count(layout.cols * layout.rows, 'n.pieces'),
    a: fmt(values.base), b: fmt(values.base + values.relief),
  });
}

function changed(key) {
  hideResults();
  const f = FIELDS[key];
  if (f.group === 'shape') return shapeSoon();
  if (f.on === 'layout') return layoutSoon();
  if (f.on === 'surface') {
    stage.tray = trayShape();
    stage.setThickness(values.base, values.relief);
    updateReadout();
  }
}

// ---------------------------------------------------------------------------
// Джерело
// ---------------------------------------------------------------------------

function renderSource() {
  const blank = source.kind === 'blank';
  $('source-name').textContent = blank ? t('src.none') : source.name;
  $('source-name').classList.toggle('loaded', !blank);
  $('kind-hint').hidden = blank;
  $('kind-hint').textContent = blank ? '' : t('kind.hint.' + source.kind);
}

function applySource(info) {
  source = info;
  const blank = info.kind === 'blank';
  renderSource();
  $('invite').hidden = !blank;
  $('shape-group').hidden = blank;
  $('kind').hidden = !(info.kind === 'photo' || info.kind === 'heightmap');
  for (const r of document.querySelectorAll('input[name=kind]')) r.checked = r.value === info.kind;
  for (const [key, f] of Object.entries(FIELDS)) {
    if (f.group === 'shape') document.querySelector(`.field[data-key="${key}"]`).hidden = !f.kinds.includes(info.kind);
  }
  if (info.suggest) {
    setValue('width', Math.round(info.suggest.width));
    setValue('relief', Math.round(info.suggest.relief * 10) / 10);
  }
  hideResults();
  refreshButtons();
}

const isMesh = (name) => /\.(stl|obj|ply|glb|gltf|off)$/i.test(name);

function loadFile(file) {
  return work(isMesh(file.name) ? 'busy.mesh' : 'busy.image', async () => {
    const info = await (await api('source?name=' + encodeURIComponent(file.name), { body: file })).json();
    applySource(info);
    await refreshShape();
    setStatus('done.relief');
  });
}

function reload(payload, busyKey) {
  return work(busyKey, async () => {
    applySource(await (await api('kind', { json: payload })).json());
    await refreshShape();
    setStatus('done.updated');
  });
}

// ---------------------------------------------------------------------------
// Файли для друку
// ---------------------------------------------------------------------------

function hideResults() {
  lastResult = null;
  if (!$('results').hidden) $('results').hidden = true;
  // «Файли створено» більше не правда, щойно щось змінили.
  if (lastStatus?.key === 'done.make' || lastStatus?.key === 'done.fit') setStatus(null);
}

function plateCard(p, bed) {
  const cls = p.kind === 'tray' ? 'tray' : 'piece';
  const polys = p.outlines
    .map((pts) => `<polygon class="${cls}" points="${pts.map(([x, y]) => `${x},${(bed - y).toFixed(2)}`).join(' ')}"/>`)
    .join('');
  const what = p.kind === 'tray'
    ? (p.count === 1 ? t('plate.section') : count(p.count, 'n.sections'))
    : count(p.count, 'n.pieces');
  const name = t('plate.name', { n: p.index });
  const card = document.createElement('div');
  card.className = 'plate-card';
  card.innerHTML = `
    <svg class="plate" viewBox="0 0 ${bed} ${bed}" role="img" aria-label="${name}: ${what}">${polys}</svg>
    <p class="plate-name">${name}</p>
    <p class="plate-count">${what}</p>
    <div class="plate-open"></div>`;
  const open = card.querySelector('.plate-open');
  for (const s of config.slicers) {
    const b = document.createElement('button');
    b.type = 'button';
    b.className = 'btn';
    b.textContent = s.name;
    b.setAttribute('aria-label', t('plate.open', { n: p.index, app: s.name }));
    b.addEventListener('click', () => api('open', { json: { path: p.file, app: s.id } }).catch(fail));
    open.append(b);
  }
  return card;
}

function renderResults() {
  if (!lastResult) return;
  const { summary: s, kind } = lastResult;
  let title, note;
  if (kind === 'fit') {
    title = t('res.fit.title');
    note = t('res.fit.note');
  } else {
    title = t('res.title', { plates: count(s.piece_plates, 'n.plates') });
    if (s.tray_plates) title += t('res.title.tray', { n: s.tray_plates });
    note = config.slicers.length ? t('res.note') : '';
  }
  $('results-title').textContent = title;
  $('results-note').hidden = !note;
  $('results-note').textContent = note;
  $('plates').replaceChildren(...s.plates.map((p) => plateCard(p, s.bed)));
  $('results').hidden = false;
}

function make() {
  return work('busy.make', async () => {
    const summary = await (await api('generate', { json: puzzleParams() })).json();
    lastResult = { summary, kind: 'puzzle' };
    renderResults();
    setStatus('done.make');
  });
}

function makeFitTest() {
  return work('busy.fit', async () => {
    const summary = await (await api('fit-test', { json: puzzleParams() })).json();
    lastResult = { summary, kind: 'fit' };
    renderResults();
    setStatus('done.fit');
  });
}

// ---------------------------------------------------------------------------
// Меню: налаштування, відомості, оновлення
// ---------------------------------------------------------------------------

let update = null;   // { key, vars, text, cls, newer, canInstall }

function selectTab(name) {
  for (const r of document.querySelectorAll('input[name=tab]')) r.checked = r.value === name;
  for (const s of document.querySelectorAll('.menu-body')) s.hidden = s.dataset.tab !== name;
}

function openMenu(tab) {
  if (tab) selectTab(tab);
  if (!$('menu').open) $('menu').showModal();
}
window.openMenu = openMenu;   // викликається також із системного меню

function renderMenu() {
  for (const r of document.querySelectorAll('input[name=lang]')) r.checked = r.value === lang;
  $('bed').value = settings.bed;
  $('model').value = settings.model;
  $('out-path').textContent = config.out;
  $('log-row').hidden = !config.has_log;
  $('about-version').textContent = t('about.version', { v: config.version });
  $('upd-current').textContent = t('upd.current', { v: config.version });
  const u = update;
  $('upd-status').textContent = !u ? '' : u.key ? t(u.key, u.vars) : u.text;
  $('upd-status').className = 'status ' + (u?.cls || '');
  $('upd-install').hidden = !(u?.newer && u.canInstall);
  $('upd-open').hidden = !(u?.newer && !u.canInstall);
}

async function saveSettings(changes) {
  Object.assign(settings, changes);
  try {
    settings = await (await api('settings', { json: changes })).json();
  } catch (e) {
    fail(e);
  }
}

async function checkUpdates() {
  update = { key: 'upd.checking', cls: 'busy' };
  renderMenu();
  try {
    const r = await (await api('update-check')).json();
    update = r.newer
      ? { key: 'upd.available', vars: { v: r.latest }, newer: true, canInstall: r.can_install }
      : { key: 'upd.latest' };
  } catch (e) {
    update = { text: e.message, cls: 'bad' };
  }
  renderMenu();
}

async function installUpdate() {
  update = { key: 'upd.installing', cls: 'busy' };
  renderMenu();
  try {
    const r = await (await api('update-install')).json();
    config.version = r.version;
    update = { key: 'upd.done', vars: { v: r.version } };
  } catch (e) {
    update = { text: e.message, cls: 'bad' };
  }
  renderMenu();
}

// ---------------------------------------------------------------------------
// Переклад сторінки
// ---------------------------------------------------------------------------

function applyI18n() {
  document.documentElement.lang = lang;
  document.title = t('app.title');
  for (const el of document.querySelectorAll('[data-i18n]')) el.textContent = t(el.dataset.i18n);
  for (const el of document.querySelectorAll('[data-i18n-aria]')) el.setAttribute('aria-label', t(el.dataset.i18nAria));
  for (const key of Object.keys(FIELDS)) {
    document.querySelector(`label[for="f-${key}"]`).textContent = t('f.' + key);
    $('n-' + key).setAttribute('aria-label', `${t('f.' + key)}, ${t('exact')}`);
  }
  renderSource();
  updateReadout();
  renderStatus();
  renderResults();
  renderMenu();
}

// ---------------------------------------------------------------------------
// Запуск
// ---------------------------------------------------------------------------

async function start() {
  buildFields();
  stage = new Stage($('view'), $('viewport'));
  stage.onOrbit = () => { for (const r of document.querySelectorAll('input[name=cam]')) r.checked = false; };
  applyI18n();

  $('pick').addEventListener('click', () => $('file').click());
  $('file').addEventListener('change', (e) => {
    const f = e.target.files[0];
    e.target.value = '';
    if (f) loadFile(f);
  });
  $('example').addEventListener('click', () => work('busy.example', async () => {
    applySource(await (await api('example')).json());
    await refreshShape();
    setStatus('done.example');
  }));
  for (const r of document.querySelectorAll('input[name=kind]')) {
    r.addEventListener('change', () => reload({ kind: r.value }, r.value === 'photo' ? 'busy.depth' : 'busy.heightmap'));
  }
  $('invert').addEventListener('change', () => { hideResults(); shapeSoon(); });
  $('tray').addEventListener('change', () => { hideResults(); stage.setTray(trayShape()); });
  $('reseed').addEventListener('click', () => { seed++; hideResults(); layoutSoon(); });
  for (const r of document.querySelectorAll('input[name=cam]')) r.addEventListener('change', () => stage.setView(r.value));
  $('make').addEventListener('click', make);
  $('fit').addEventListener('click', makeFitTest);
  $('reveal').addEventListener('click', () => lastResult && api('open', { json: { path: lastResult.summary.out, app: 'finder' } }).catch(fail));

  // Меню.
  $('menu-btn').addEventListener('click', () => openMenu());
  $('menu-close').addEventListener('click', () => $('menu').close());
  $('menu').addEventListener('click', (e) => { if (e.target === $('menu')) $('menu').close(); });
  for (const r of document.querySelectorAll('input[name=tab]')) r.addEventListener('change', () => selectTab(r.value));
  for (const r of document.querySelectorAll('input[name=lang]')) {
    r.addEventListener('change', () => { lang = r.value; applyI18n(); saveSettings({ lang }); });
  }
  $('bed').addEventListener('change', () => {
    const bed = clamp(Number.isFinite(+$('bed').value) ? +$('bed').value : 180, 100, 500);
    $('bed').value = bed;
    hideResults();
    saveSettings({ bed });
  });
  $('model').addEventListener('change', async () => {
    await saveSettings({ model: $('model').value });
    if (source.kind === 'photo') { $('menu').close(); reload({ kind: 'photo' }, 'busy.depth.again'); }
  });
  $('open-out').addEventListener('click', () => api('open', { json: { target: 'out' } }).catch(fail));
  $('open-log').addEventListener('click', () => api('open', { json: { target: 'log' } }).catch(fail));
  for (const b of document.querySelectorAll('[data-url]')) {
    b.addEventListener('click', () => api('open-url', { json: { which: b.dataset.url } }).catch(fail));
  }
  $('upd-check').addEventListener('click', checkUpdates);
  $('upd-install').addEventListener('click', installUpdate);

  // Файл можна кинути будь-куди у вікно.
  let depth = 0;
  const hasFiles = (e) => e.dataTransfer && [...e.dataTransfer.types].includes('Files');
  window.addEventListener('dragenter', (e) => { if (hasFiles(e)) { e.preventDefault(); depth++; $('dropping').hidden = false; } });
  window.addEventListener('dragover', (e) => { if (hasFiles(e)) e.preventDefault(); });
  window.addEventListener('dragleave', () => { depth = Math.max(0, depth - 1); if (!depth) $('dropping').hidden = true; });
  window.addEventListener('drop', (e) => {
    e.preventDefault();
    depth = 0;
    $('dropping').hidden = true;
    const f = e.dataTransfer?.files?.[0];
    if (f && busy === 0) loadFile(f);
  });

  try {
    config = await (await api('config')).json();
    settings = config.settings;
    lang = settings.lang;
    $('example').hidden = !config.example;
    applyI18n();
    applySource(config.source);
    await refreshShape();
  } catch (e) {
    fail(e);
  }
}

start();
