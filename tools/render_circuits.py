#!/usr/bin/env python3
"""Faithful schematic renderer for a Logisim-Evolution .circ file.

Parses every <circuit> and emits an SVG that reproduces the real component
positions, wiring and labels stored in the file. Wires carry the exact
topology; components are drawn as labelled blocks coloured by category; pins,
tunnels and text annotations are reproduced. The output is a clean, readable
schematic view of each subcircuit of the RV32I CPU.
"""
import xml.etree.ElementTree as ET
import html
import os
import sys

SRC = sys.argv[1] if len(sys.argv) > 1 else "project2 1.circ"
OUT = sys.argv[2] if len(sys.argv) > 2 else "docs/images"
os.makedirs(OUT, exist_ok=True)

# ---- palette -------------------------------------------------------------
BG = "#0d1117"
GRID = "#161b22"
WIRE = "#58a6ff"
WIRE_BUS = "#bc8cff"
TEXT = "#e6edf3"
SUB = "#8b949e"

# category -> (fill, stroke)
CAT = {
    "sub":   ("#1f6feb", "#79c0ff"),   # nested subcircuits
    "mem":   ("#8957e5", "#d2a8ff"),   # ROM / RAM / Register
    "alu":   ("#bb8009", "#f0c674"),   # arithmetic
    "mux":   ("#1a7f37", "#56d364"),   # plexers
    "gate":  ("#6e7681", "#b1bac4"),   # logic gates
    "wiring":("#30363d", "#8b949e"),   # splitter / bit extender / constant
    "io":    ("#9e6a03", "#e3b341"),
}

def cat(name):
    n = name.lower()
    if name in SUBCIRCUITS:
        return "sub"
    if name in ("ROM", "RAM", "Register", "Counter", "Register File"):
        return "mem"
    if name in ("Adder", "Subtractor", "Multiplier", "Divider", "Comparator",
                "Shifter", "Negator", "Bit Adder"):
        return "alu"
    if name in ("Multiplexer", "Demultiplexer", "Decoder", "Encoder",
                "Priority Encoder", "Bit Selector"):
        return "mux"
    if "gate" in n or name in ("NOT Gate", "Buffer", "Controlled Buffer"):
        return "gate"
    if name in ("Splitter", "Bit Extender", "Constant", "Pull Resistor"):
        return "wiring"
    return "wiring"

# nice short labels for common components
ABBR = {
    "Multiplexer": "MUX", "Demultiplexer": "DEMUX", "Bit Extender": "EXT",
    "Subtractor": "SUB", "Comparator": "CMP", "Constant": "const",
    "AND Gate": "AND", "OR Gate": "OR", "NOT Gate": "NOT", "XOR Gate": "XOR",
    "NAND Gate": "NAND", "NOR Gate": "NOR", "Decoder": "DEC",
}

tree = ET.parse(SRC)
root = tree.getroot()
SUBCIRCUITS = {c.get("name") for c in root.findall("circuit")}


def attrs(el):
    return {a.get("name"): (a.get("val") if a.get("val") is not None else a.text)
            for a in el.findall("a")}


def parse_pt(s):
    s = s.strip("()")
    x, y = s.split(",")
    return int(x), int(y)


def comp_box(name, label, width):
    """Return (w, h) for a component block."""
    txt = label or ABBR.get(name, name)
    base = max(46, 9 * len(txt) + 16)
    if name in SUBCIRCUITS:
        return max(150, base), 64
    if name in ("ROM", "RAM"):
        return 132, 78
    if name == "Register":
        return 84, 56
    if name == "Splitter":
        return 26, 70
    if name in ("Constant", "Bit Extender", "Tunnel"):
        return 64, 30
    if "Gate" in name:
        return 60, 44
    if name in ("Adder", "Subtractor", "Comparator", "Shifter",
                "Multiplexer", "Decoder"):
        return 78, 56
    return base, 50


def render(circ):
    name = circ.get("name")
    comps = circ.findall("comp")
    wires = circ.findall("wire")
    if not comps and not wires:
        return None

    xs, ys = [], []
    for w in wires:
        for p in (w.get("from"), w.get("to")):
            x, y = parse_pt(p)
            xs.append(x); ys.append(y)
    boxes = []
    for c in comps:
        a = attrs(c)
        loc = c.get("loc")
        if not loc:
            continue
        lx, ly = parse_pt(loc)
        nm = c.get("name")
        label = a.get("label", "")
        w, h = comp_box(nm, label if nm in ("Tunnel",) else label, a.get("width"))
        # anchor: most Logisim comps anchor at an east/output port; center the box to the west
        cx, cy = lx - w // 2, ly - h // 2
        boxes.append((nm, label, a, cx, cy, w, h, lx, ly))
        xs += [cx, cx + w]; ys += [cy, cy + h]

    if not xs:
        return None
    pad = 60
    minx, maxx = min(xs) - pad, max(xs) + pad
    miny, maxy = min(ys) - pad, max(ys) + pad
    W, H = maxx - minx, maxy - miny

    out = []
    out.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="{minx} {miny} {W} {H}" '
               f'width="{W}" height="{H}" font-family="SFMono-Regular,Consolas,monospace">')
    out.append(f'<rect x="{minx}" y="{miny}" width="{W}" height="{H}" fill="{BG}"/>')
    # subtle grid
    out.append('<g opacity="0.5">')
    g0x = (minx // 50) * 50
    g0y = (miny // 50) * 50
    x = g0x
    while x < maxx:
        out.append(f'<line x1="{x}" y1="{miny}" x2="{x}" y2="{maxy}" stroke="{GRID}" stroke-width="1"/>')
        x += 50
    y = g0y
    while y < maxy:
        out.append(f'<line x1="{minx}" y1="{y}" x2="{maxx}" y2="{y}" stroke="{GRID}" stroke-width="1"/>')
        y += 50
    out.append('</g>')

    # title
    out.append(f'<text x="{minx+22}" y="{miny+34}" fill="{TEXT}" font-size="26" '
               f'font-weight="700">{html.escape(name)}</text>')
    out.append(f'<text x="{minx+22}" y="{miny+56}" fill="{SUB}" font-size="13">'
               f'RV32I CPU &#183; Logisim-Evolution schematic</text>')

    # wires (draw under components)
    out.append('<g stroke-linecap="round">')
    for w in wires:
        x1, y1 = parse_pt(w.get("from"))
        x2, y2 = parse_pt(w.get("to"))
        out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" '
                   f'stroke="{WIRE}" stroke-width="2.4" opacity="0.85"/>')
    out.append('</g>')
    # connection dots at wire junctions
    from collections import Counter
    endpoints = Counter()
    for w in wires:
        endpoints[w.get("from")] += 1
        endpoints[w.get("to")] += 1
    for p, n in endpoints.items():
        if n >= 3:
            x, y = parse_pt(p)
            out.append(f'<circle cx="{x}" cy="{y}" r="3.2" fill="{WIRE}"/>')

    # components
    for nm, label, a, cx, cy, w, h, lx, ly in boxes:
        if nm == "Tunnel":
            lbl = a.get("label", "")
            tw = max(40, 8 * len(lbl) + 14)
            out.append(f'<rect x="{lx-tw//2}" y="{ly-13}" width="{tw}" height="26" rx="13" '
                       f'fill="#21262d" stroke="#444c56" stroke-width="1.2"/>')
            out.append(f'<text x="{lx}" y="{ly+4}" fill="#7ee787" font-size="12" '
                       f'text-anchor="middle">{html.escape(lbl)}</text>')
            continue
        if nm == "Text":
            txt = a.get("text", "")
            out.append(f'<text x="{lx}" y="{ly}" fill="{SUB}" font-size="13">'
                       f'{html.escape(txt[:60])}</text>')
            continue
        if nm == "Pin":
            is_out = a.get("output") == "true"
            fill, stroke = ("#bf3989", "#ff7bbf") if is_out else ("#238636", "#56d364")
            out.append(f'<rect x="{cx}" y="{cy}" width="{w}" height="{h}" rx="6" '
                       f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
            t = label or ("out" if is_out else "in")
            out.append(f'<text x="{lx-w//2+w//2}" y="{ly+5}" fill="#fff" font-size="13" '
                       f'font-weight="600" text-anchor="middle">{html.escape(t)}</text>')
            continue

        fill, stroke = CAT[cat(nm)]
        txt = label or ABBR.get(nm, nm)
        rx = 10 if nm in SUBCIRCUITS else 6
        out.append(f'<rect x="{cx}" y="{cy}" width="{w}" height="{h}" rx="{rx}" '
                   f'fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
        fs = 14 if nm in SUBCIRCUITS else 12
        weight = 700 if nm in SUBCIRCUITS else 500
        out.append(f'<text x="{cx+w//2}" y="{cy+h//2+5}" fill="#fff" font-size="{fs}" '
                   f'font-weight="{weight}" text-anchor="middle">{html.escape(txt)}</text>')
        if nm in SUBCIRCUITS:
            out.append(f'<text x="{cx+w//2}" y="{cy+h-9}" fill="#cfe2ff" font-size="9" '
                       f'text-anchor="middle">subcircuit</text>')

    out.append('</svg>')
    return "\n".join(out)


index = []
for circ in root.findall("circuit"):
    svg = render(circ)
    if svg is None:
        continue
    fn = circ.get("name").replace(" ", "_") + ".svg"
    with open(os.path.join(OUT, fn), "w") as f:
        f.write(svg)
    index.append(fn)
    print("wrote", fn)
print("\n%d diagrams ->" % len(index), OUT)
