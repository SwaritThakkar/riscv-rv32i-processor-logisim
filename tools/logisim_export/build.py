#!/usr/bin/env python3
"""Generate the dark-theme circuit figures from RV32I_CPU.circ.

Pipeline:
  1. Compile and run Export.java, which uses Logisim-Evolution's OWN renderer
     (the File > Export Image code path) to rasterise every subcircuit to PNG
     on a white background — the authentic Logisim appearance.
  2. Recolour each export to the dark theme: invert (white->black, lines->light)
     then screen-blend a deep-navy floor so the background is navy and the
     traces stay light. Downscale very large sheets.

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
# neon "synthwave PCB" palette on near-black, finished with a glow/bloom pass
BGFLOOR = (5, 7, 16)     # deep blue-black background floor
COMP = (224, 234, 255)   # components / gates / text  (ice white)
WIRE = (34, 232, 255)    # wires / buses              (neon cyan)
PIN  = (255, 74, 158)    # input/output pins & labels (hot magenta)
GLOW = 0.6               # bloom strength

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


def darken():
    """Recolour a white-bg Logisim export to the vivid-PCB dark palette.

    Logisim draws components/text in black, wires/buses in grey(~128) and pins
    in blue. We classify each pixel by those source colours and paint it on pure
    black; brightness tracks how 'inky' the source pixel was, so anti-aliased
    edges fade smoothly into the black background (no colour halos)."""
    import numpy as np
    from PIL import Image, ImageFilter
    PAD = 30
    for f in sorted(glob.glob(WORK + "/out/*.png")):
        name = os.path.basename(f)
        a = np.asarray(Image.open(f).convert("RGB")).astype(np.float32)
        R, G, B = a[..., 0], a[..., 1], a[..., 2]
        g = (R + G + B) / 3.0
        ink = np.clip((255.0 - g) / 255.0, 0, 1)              # 0 = bg, 1 = solid ink
        is_pin = (B > R + 45) & (B > G + 45)                  # blue pins/labels
        is_wire = (~is_pin) & (g > 70) & (g < 205)            # grey wires/buses
        is_comp = (~is_pin) & (~is_wire)                      # black components/text
        elem = np.zeros(a.shape, np.float32)                  # elements on black
        for mask, col in ((is_comp, COMP), (is_wire, WIRE), (is_pin, PIN)):
            for c in range(3):
                elem[..., c] = np.where(mask, col[c] * ink, elem[..., c])
        base = Image.fromarray(np.clip(elem, 0, 255).astype("uint8"), "RGB")
        # neon bloom: add blurred copies of the bright elements back on top
        glow_s = np.asarray(base.filter(ImageFilter.GaussianBlur(4))).astype(np.float32)
        glow_l = np.asarray(base.filter(ImageFilter.GaussianBlur(13))).astype(np.float32)
        floor = np.array(BGFLOOR, np.float32)
        out = elem + GLOW * glow_s + (GLOW * 0.7) * glow_l + floor
        img = Image.fromarray(np.clip(out, 0, 255).astype("uint8"), "RGB")
        bbox = base.getbbox()
        if bbox:
            l, t, r, b = bbox
            img = img.crop((max(0, l - PAD), max(0, t - PAD),
                            min(img.width, r + PAD), min(img.height, b + PAD)))
        w, h = img.size
        if max(w, h) > MAXD:
            s = MAXD / max(w, h)
            img = img.resize((int(w * s), int(h * s)), Image.LANCZOS)
        img.save(os.path.join(DST, name))
        print("themed", name, img.size)


if __name__ == "__main__":
    if not os.path.exists(JAR):
        sys.exit("Logisim-Evolution jar not found at " + JAR)
    render_exports()
    darken()
    print("DONE ->", DST)
