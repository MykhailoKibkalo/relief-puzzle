# Relief Puzzle

**English** | [Українська](README.uk.md)

Turn a picture, a height map or a 3D model into a relief jigsaw puzzle you can 3D-print. The app builds the relief, cuts it into interlocking pieces with a print gap, lays the pieces out on printer plates and writes one 3MF file per plate.

![The app showing a sunflower relief cut into 35 puzzle pieces](docs/app-en.jpg)

## What it does

- **Three kinds of input.** A picture (a neural network estimates its depth), a ready height map (white is high), or a relief 3D model (STL, OBJ, PLY, GLB).
- **Live 3D preview.** Change the width, piece size, relief height or gap and the puzzle redraws at once.
- **Pieces that fit after printing.** Each piece gets an adjustable gap to its neighbours, rounded corners and a small bottom chamfer against elephant's foot.
- **Plates for your printer.** Pieces are packed onto as many plates as the bed size requires (180 mm for a Bambu Lab A1 mini by default). Every plate is a separate 3MF file.
- **A frame.** An optional tray with a rim. If it is larger than the bed, it is split into sections that join with jigsaw tabs.
- **A fit test.** Five pairs of pieces with gaps from 0.10 to 0.30 mm, so you can find the right gap for your printer before printing a whole puzzle.
- **English and Ukrainian** interface.

## Examples

<p>
  <img src="docs/sunflower-photo.jpg" width="32%" alt="Source photo: a sunflower">
  <img src="docs/sunflower-relief.jpg" width="32%" alt="The relief built from the sunflower photo">
  <img src="docs/sunflower-puzzle.jpg" width="32%" alt="The sunflower relief cut into 35 puzzle pieces">
</p>
<p>
  <img src="docs/turtle-photo.jpg" width="32%" alt="Source photo: a sea turtle seen from above">
  <img src="docs/turtle-relief.jpg" width="32%" alt="The relief built from the sea turtle photo">
  <img src="docs/turtle-puzzle.jpg" width="32%" alt="The sea turtle relief cut into 42 puzzle pieces">
</p>

In each row: the source photo, the relief built from it with the default settings, and that relief cut into a 170 mm wide puzzle.

The sunflower puzzle and the two halves of its frame, laid out on 180 mm plates:

![Four plates: two with puzzle pieces and two with frame halves](docs/plates-layout-en.jpg)

Bambu Studio estimates the first plate (20 pieces, 0.12 mm layers, 0.4 mm nozzle, A1 mini) at about 3 hours and 42 g of PLA.

The photos and the height maps made from them are in [`examples/`](examples).

## Install

You need macOS, Python 3.11 or 3.12, and [uv](https://docs.astral.sh/uv/). The app is tested on macOS with Apple Silicon.

```bash
git clone https://github.com/MykhailoKibkalo/relief-puzzle.git
cd relief-puzzle
uv sync
uv run python app.py
```

To get an icon you can double-click, run this once:

```bash
uv run python make_app.py
```

It creates `Relief Puzzle.app` in the project folder (`Рельєфний пазл.app` if the app language is Ukrainian). You can move the icon to the Dock or to Applications.

The first time you open a picture, the app downloads the depth model from Hugging Face (about 1.3 GB). Height maps and 3D models need no download.

## Using the app

1. Drop a picture, a height map or a 3D model onto the window, or click **Choose file**. **Try the example** loads the sunflower.
2. Adjust the relief and the puzzle. Drag the preview to rotate it.
3. Click **Create print files**. The plates appear at the bottom, each with buttons that open it in Bambu Studio or OrcaStudio if they are installed.

![The finished plates with buttons to open each one in a slicer](docs/plates-en.jpg)

The **Menu** button holds the settings (language, printer bed size, which neural network to use), the version, a link to this page and an update check. If you installed with `git clone`, the app can update itself from there.

![The menu with the About tab open](docs/menu-en.jpg)

### What makes a good source

- **A three-dimensional subject on a simple background** works best for pictures: a flower, an animal, a statue, a shell. The examples above are ordinary photos of this kind.
- **A relief 3D model** gives exact geometry: bas-reliefs made for CNC carving, 3D scans, or models from an image-to-3D generator.
- **A head-on photo of a shallow relief, a coin or a medal comes out almost flat.** The depth network sees it as a flat board, because it nearly is one.

The app has no cropping yet, so crop the picture to the subject before opening it. If the background comes out uneven, raise **Flat background**.

## Command line

Everything the app does is also available as scripts:

```bash
uv run python heightmap.py photo.jpg -o relief.png      # picture → height map
uv run python mesh2height.py model.stl -o relief.png    # 3D model → height map
uv run python puzzle.py relief.png --width 240 --piece 24 --tray
uv run python puzzle.py --fit-test                      # fit test only
```

The main options of `puzzle.py`:

| Option | Default | Meaning |
|---|---|---|
| `--width` | 170 | Puzzle width in mm; the height follows the aspect ratio |
| `--piece` | 24 | Approximate piece size in mm |
| `--base` | 2.4 | Thickness under the lowest point of the relief, mm |
| `--relief` | 5 | Height of the relief above the base, mm |
| `--clearance` | 0.2 | Gap between neighbouring pieces, mm |
| `--chamfer` | 0.3 | Bottom chamfer against elephant's foot, mm |
| `--bed` | 180 | Printer bed size, mm |
| `--tray` | off | Add the frame |
| `--seed` | 1 | Cut pattern number |

Run any script with `--help` for the full list. Messages follow the app language; set `RELIEF_PUZZLE_LANG=en` or `RELIEF_PUZZLE_LANG=uk` to choose.

## Printing

- **Print the fit test first.** The right gap depends on the printer and the filament. The test takes 20–30 minutes; the number of dots on a piece tells you which gap it has.
- Layers of 0.08–0.12 mm keep the stepping on gentle slopes small. Matte PLA hides layer lines best.
- Print the frame in a second colour.
- The stock Bambu Studio profiles for the A1 mini have elephant foot compensation turned off, which is why the pieces get a bottom chamfer by default.

## How it works

1. **Depth.** Depth Anything V2 runs at two resolutions: the coarse pass gives the overall shape and the fine pass adds detail. Several shifted and mirrored passes are averaged to hide the model's 14-pixel patch grid. Optionally, a little micro-texture is mixed in from the image brightness.
2. **Bas-relief.** Real depth does not fit into a few millimetres: the step between the subject and the background would use up almost all the height. So steep steps are attenuated, gentle slopes are kept, and the surface is rebuilt from the slopes. The subject's own shape gets most of the height range.
3. **Solid.** The height map becomes a height-field solid on a 0.2 mm grid.
4. **Cutting.** The cut lines are classic jigsaw tabs built from cubic Bézier curves. Each piece outline is inset by half the gap, and the piece is the intersection of the height-field solid with the extruded outline, computed with [Manifold](https://github.com/elalish/manifold).
5. **Layout.** Pieces are shelf-packed onto plates and written straight to 3MF.

## Limits

- Depth estimated from a picture captures shapes down to petals and limbs; finer detail such as fur or feathers comes out soft. The **Surface texture** control imitates it from image brightness, which is not real geometry. Shallow reliefs photographed head-on come out almost flat.
- The app window, the icon and the slicer buttons are macOS-only. The command-line scripts are plain Python and should run elsewhere, but that is untested.
- The geometry is checked: every piece is a closed solid, and the plates slice without errors in Bambu Studio 2.8. The default 0.2 mm gap has not been validated on real prints yet, so use the fit test.

## License and credits

The code is released under the [MIT license](LICENSE).

- **Depth models.** [Depth Anything V2](https://github.com/DepthAnything/Depth-Anything-V2): the Small model is Apache 2.0; the Large model, used by default, is CC BY-NC 4.0, which means non-commercial use only. If you sell prints, switch to the basic network in Menu → Settings or pass `--model small`.
- **Bundled.** [Three.js](https://threejs.org) (MIT) in `static/vendor/`.
- **Dependencies.** Manifold, trimesh, pywebview, PyTorch and Transformers, under their own licenses.
- **Jigsaw tabs.** The tab shape follows the Bézier parametrization known from [Draradech's jigsaw generator](https://github.com/Draradech/jigsaw).
- **Example photos.** [Sunflower](https://commons.wikimedia.org/wiki/File:Helianthus_annuus_-_Jardin_universitaire_Roger-Van_den_Hende,_Quebec_22.jpg) by Wilfredor and [green sea turtle](https://commons.wikimedia.org/wiki/File:Chelonia_mydas_176499106.jpg) by Zygy, both released under CC0 on Wikimedia Commons.
