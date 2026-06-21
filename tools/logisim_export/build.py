#!/usr/bin/env python3
"""Generate the circuit figures from RV32I_CPU.circ — authentic Logisim look.

Pipeline:
  1. Compile and run Export.java, which uses Logisim-Evolution's OWN renderer
     (the File > Export Image code path) plus the canvas grid to rasterise every
     subcircuit to PNG — i.e. exactly what the Logisim editor canvas shows.
  2. Auto-crop each image to its content (so pin labels are never clipped) and
     downscale very large sheets.

Requires: a JDK (uses the one bundled with the VS Code Java extension if present,
else `javac`/`java` on PATH) and the Logisim-Evolution app jar.
"""
import glob
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "../.."))
CIRC = os.path.join(REPO, "RV32I_CPU.circ")
DST = os.path.join(REPO, "docs/images")
JAR = "/Applications/Logisim-evolution.app/Contents/app/logisim-evolution-4.1.0-all.jar"
WORK = "/tmp/limg"           # space-free working dir
MAXD = 2800
SCALE = "3.0"

# locate a JDK (bundled VS Code Java extension, else PATH)
_cands = glob.glob(os.path.expanduser(
    "~/.antigravity/extensions/redhat.java-*/jre/*/bin")) + \
    glob.glob(os.path.expanduser("~/.vscode/extensions/redhat.java-*/jre/*/bin"))
JBIN = next((c for c in _cands if os.path.exists(os.path.join(c, "javac"))), None)
JAVAC = os.path.join(JBIN, "javac") if JBIN else "javac"
JAVA = os.path.join(JBIN, "java") if JBIN else "java"


def render_exports():
    os.makedirs(WORK + "/out", exist_ok=True)
    shutil.copy(os.path.join(HERE, "Export.java"), WORK + "/Export.java")
    shutil.copy(CIRC, WORK + "/cpu.circ")
    subprocess.run([JAVAC, "-cp", JAR, "Export.java"], cwd=WORK, check=True)
    subprocess.run([JAVA, "-cp", JAR + ":.", "Export", "cpu.circ", "out", SCALE],
                   cwd=WORK, check=True)


# refined dark-slate theme (clean, not neon)
BG   = (13, 19, 32)      # dark slate canvas
GRID = (32, 44, 64)      # subtle dot grid
COMP = (228, 234, 244)   # components / gates / text  (soft white)
WIRE = (122, 150, 184)   # wires / buses              (cool steel)
PIN  = (240, 184, 80)    # input / output pins        (warm amber)


def finish():
    """Recolour each white Logisim export to a clean dark-slate theme.

    Logisim draws components in black, floating wires in grey(~128), the canvas
    dot-grid in light grey(~216) and pins in blue. We classify every pixel by
    those source tones and paint it on a dark slate canvas; line brightness
    tracks the source ink so anti-aliased edges fade into the background with no
    halos. Then auto-crop to content and downscale very large sheets."""
    import numpy as np
    from PIL import Image
    PAD = 30
    bg = np.array(BG, np.float32)
    for f in sorted(glob.glob(WORK + "/out/*.png")):
        name = os.path.basename(f)
        a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        g = (R + G + B) / 3.0
        is_pin = (B > R + 45) & (B > G + 45)
        ink = np.clip((255.0 - g) / 255.0, 0, 1)                 # darkness of source
        out = np.tile(bg, a.shape[:2] + (1,))

        def blend(mask, target, weight):
            t = np.array(target, np.float32)
            wgt = (mask * weight)[..., None]
            return out * (1 - wgt) + t * wgt

        comp = (~is_pin) & (g < 90)
        wire = (~is_pin) & (g >= 90) & (g < 196)
        grid = (~is_pin) & (g >= 196) & (g < 250)
        out = blend(grid, GRID, np.clip((250.0 - g) / 54.0, 0, 1) * 0.7)
        out = blend(wire, WIRE, ink)
        out = blend(comp, COMP, ink)
        out = blend(is_pin, PIN, np.clip(ink * 1.4, 0, 1))
        img = Image.fromarray(np.clip(out, 0, 255).astype("uint8"), "RGB")

        # crop to content: anything that differs from the flat background
        diff = np.abs(np.asarray(img).astype(np.int16) - BG).sum(2)
        ys, xs = np.where(diff > 18)
        if len(xs):
            l, r, t, b = xs.min(), xs.max(), ys.min(), ys.max()
            img = img.crop((max(0, l - PAD), max(0, t - PAD),
                            min(img.width, r + PAD), min(img.height, b + PAD)))
        w, h = img.size
        if max(w, h) > MAXD:
            s = MAXD / max(w, h)
            img = img.resize((int(w * s), int(h * s)), Image.LANCZOS)
        img.save(os.path.join(DST, name))
        print("saved", name, img.size)


if __name__ == "__main__":
    if not os.path.exists(JAR):
        sys.exit("Logisim-Evolution jar not found at " + JAR)
    render_exports()
    finish()
    print("DONE ->", DST)
