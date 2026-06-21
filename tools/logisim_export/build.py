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


def finish():
    """Clean up the Logisim export for a crisp white-paper look:
      - boost contrast (Logisim draws floating wires in faint grey ~128; a gamma
        curve darkens those to readable near-black while keeping pure black
        components, white background and blue pins intact),
      - auto-crop to content so nothing is clipped,
      - downscale very large sheets."""
    import numpy as np
    from PIL import Image, ImageChops
    PAD = 30
    GAMMA = 2.1
    lut = (((np.arange(256) / 255.0) ** GAMMA) * 255.0).astype(np.float32)
    for f in sorted(glob.glob(WORK + "/out/*.png")):
        name = os.path.basename(f)
        a = np.asarray(Image.open(f).convert("RGB")).astype(np.uint8)
        out = lut[a].astype("uint8")              # per-channel gamma -> darker wires
        img = Image.fromarray(out, "RGB")
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bbox = ImageChops.difference(img, bg).getbbox()       # content box (incl. labels)
        if bbox:
            l, t, r, b = bbox
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
