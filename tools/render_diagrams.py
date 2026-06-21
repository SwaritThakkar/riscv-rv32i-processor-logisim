#!/usr/bin/env python3
"""Production-grade, hand-designed schematic diagrams for the RV32I CPU.

A small SVG design system (warm "paper" palette, soft cards, pill ports,
rounded orthogonal connectors) is used to lay out clean block diagrams for the
top-level datapath and every subcircuit. Output: docs/images/*.svg
"""
import html
import os

OUT = "docs/images"
os.makedirs(OUT, exist_ok=True)

# ----------------------------------------------------------------- palette ---
# Dark "data-viz" theme matching the companion repos (deep navy ground,
# bright cyan/coral/gold/green accents, light text).
BG0     = "#070A12"   # ground
BG1     = "#0E1626"   # gradient bottom
INK     = "#F8FAFC"   # bright titles
TEXT    = "#D8DDF5"   # body text on cards
MUTE    = "#9CA3AF"   # muted captions
FAINT   = "#6B7689"   # faintest
GRID    = "#16203250"  # subtle grid lines (with alpha)
PANEL   = "#111827"
BORDER  = "#334155"
LINE    = "#64748B"   # default connector
LINE_DK = "#7C8BA1"   # arrowhead
CYAN    = "#38BDF8"   # bus / datapath
ORANGE  = "#F97316"   # control / compute
GOLD    = "#FFD34D"
GREEN   = "#6EE7B7"
ROSE    = "#F43F5E"

# kind -> (fill, border, title, sub)  — mirrors the Mermaid classDefs
KINDS = {
    "plain":   (PANEL,     "#64748B", TEXT,      MUTE),
    "primary": ("#3B2F0B", GOLD,      "#FEF3C7", "#D9C68A"),  # gold (control)
    "mem":     ("#123524", GREEN,     "#DCFCE7", "#92C9AD"),  # green (memory)
    "alu":     ("#3B1D0B", ORANGE,    "#FFEDD5", "#D9AE8A"),  # orange (compute)
    "mux":     ("#08304A", CYAN,      "#E0F2FE", "#8FC4DD"),  # cyan (select)
    "ctrl":    ("#10213A", "#60A5FA", "#DBEAFE", "#92AAC9"),  # blue (datapath)
}
PORT_IN  = ("#123524", GREEN,  "#DCFCE7")   # green
PORT_OUT = ("#3B1D0B", ORANGE, "#FFEDD5")   # orange
PORT_CLK = ("#172033", "#64748B", "#9CA3AF")  # neutral (clk/reset)
PORT_SIG = ("#4A102A", ROSE,   "#FFE4E6")   # rose (control signal)

FONT  = "Inter, 'Helvetica Neue', 'Segoe UI', system-ui, Arial, sans-serif"
MONO  = "ui-monospace, 'SF Mono', Menlo, Consolas, monospace"


# ------------------------------------------------------------- primitives ---
class Canvas:
    def __init__(self, w, h, title, subtitle):
        self.w, self.h = w, h
        self.body = []
        self.title = title
        self.subtitle = subtitle

    def add(self, s):
        self.body.append(s)

    # rounded orthogonal connector through waypoints
    def connect(self, pts, kind="data", r=12, arrow=True, width=None, dash=False):
        col = {"data": LINE, "bus": CYAN, "ctrl": ORANGE}.get(kind, LINE)
        w = width or (3.0 if kind == "bus" else 2.2 if kind == "data" else 2.0)
        d = f"M {pts[0][0]} {pts[0][1]} "
        for i in range(1, len(pts) - 1):
            x0, y0 = pts[i - 1]; x1, y1 = pts[i]; x2, y2 = pts[i + 1]
            # corner arc
            def trim(ax, ay, bx, by, rr):
                import math
                dx, dy = bx - ax, by - ay
                L = max(1e-6, (dx * dx + dy * dy) ** 0.5)
                rr = min(rr, L / 2)
                return ax + dx / L * (L - rr), ay + dy / L * (L - rr), ax + dx / L * rr, ay + dy / L * rr
            ex, ey, _, _ = trim(x0, y0, x1, y1, r)
            _, _, sx, sy = trim(x1, y1, x2, y2, r)
            d += f"L {ex:.1f} {ey:.1f} Q {x1} {y1} {sx:.1f} {sy:.1f} "
        d += f"L {pts[-1][0]} {pts[-1][1]} "
        mk = ' marker-end="url(#ar-{})"'.format("ctrl" if kind == "ctrl" else "data") if arrow else ""
        da = ' stroke-dasharray="6 5"' if dash else ""
        self.add(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{w}" '
                 f'stroke-linecap="round" stroke-linejoin="round"{da}{mk}/>')

    def card(self, x, y, w, h, title, sub=None, kind="plain", note=None, fs=16):
        fill, bd, tc, sc = KINDS[kind]
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="14" fill="{fill}" '
                 f'stroke="{bd}" stroke-width="1.6" filter="url(#soft)"/>')
        if kind == "primary":
            self.add(f'<rect x="{x}" y="{y}" width="5" height="{h}" rx="2.5" fill="{GOLD}"/>')
        cy = y + h / 2
        if sub:
            self.add(f'<text x="{x+w/2}" y="{cy-4}" text-anchor="middle" '
                     f'font-family="{FONT}" font-size="{fs}" font-weight="650" fill="{tc}">{html.escape(title)}</text>')
            self.add(f'<text x="{x+w/2}" y="{cy+16}" text-anchor="middle" '
                     f'font-family="{FONT}" font-size="11.5" fill="{sc}">{html.escape(sub)}</text>')
        else:
            self.add(f'<text x="{x+w/2}" y="{cy+5}" text-anchor="middle" '
                     f'font-family="{FONT}" font-size="{fs}" font-weight="650" fill="{tc}">{html.escape(title)}</text>')
        if note:
            self.add(f'<text x="{x+w/2}" y="{y+h+16}" text-anchor="middle" '
                     f'font-family="{MONO}" font-size="11" fill="{FAINT}">{html.escape(note)}</text>')

    def chip(self, x, y, w, h, lines, kind="plain", title=None):
        """A card containing several monospace lines (e.g. a table / op list)."""
        fill, bd, tc, sc = KINDS[kind]
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="12" fill="{fill}" '
                 f'stroke="{bd}" stroke-width="1.5" filter="url(#soft)"/>')
        ty = y + 24
        if title:
            self.add(f'<text x="{x+16}" y="{ty}" font-family="{FONT}" font-size="13" '
                     f'font-weight="700" fill="{tc}">{html.escape(title)}</text>')
            ty += 22
        for ln in lines:
            self.add(f'<text x="{x+16}" y="{ty}" font-family="{MONO}" font-size="12.5" '
                     f'fill="{TEXT}">{html.escape(ln)}</text>')
            ty += 19

    def port(self, x, y, label, kind="in", w=None, bus=False):
        if kind == "in":
            bg, bd, tx = PORT_IN
        elif kind == "out":
            bg, bd, tx = PORT_OUT
        elif kind == "ctrl" or kind == "sig":
            bg, bd, tx = PORT_SIG
        else:
            bg, bd, tx = PORT_CLK
        w = w or max(58, 9 * len(label) + 22)
        h = 30
        self.add(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="15" fill="{bg}" '
                 f'stroke="{bd}" stroke-width="1.5"/>')
        self.add(f'<text x="{x+w/2}" y="{y+19.5}" text-anchor="middle" font-family="{MONO}" '
                 f'font-size="12.5" font-weight="600" fill="{tx}">{html.escape(label)}</text>')
        return (x, y, w, h)

    def bustag(self, x, y, text):
        w = 8 * len(text) + 12
        self.add(f'<rect x="{x-w/2}" y="{y-9}" width="{w}" height="18" rx="9" '
                 f'fill="{PANEL}" stroke="{CYAN}" stroke-width="1" opacity="0.95"/>')
        self.add(f'<text x="{x}" y="{y+4}" text-anchor="middle" font-family="{MONO}" '
                 f'font-size="10.5" fill="{CYAN}">{html.escape(text)}</text>')

    def label(self, x, y, text, size=12, color=None, weight=400, anchor="start", mono=False):
        self.add(f'<text x="{x}" y="{y}" text-anchor="{anchor}" '
                 f'font-family="{MONO if mono else FONT}" font-size="{size}" '
                 f'font-weight="{weight}" fill="{color or MUTE}">{html.escape(text)}</text>')

    def render(self):
        s = []
        s.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w} {self.h}" '
                 f'width="{self.w}" height="{self.h}" font-family="{FONT}">')
        s.append('<defs>')
        s.append('<filter id="soft" x="-30%" y="-30%" width="160%" height="160%">'
                 '<feDropShadow dx="0" dy="2" stdDeviation="4" flood-color="#000000" flood-opacity="0.45"/></filter>')
        for mid, col in (("ar-data", LINE_DK), ("ar-ctrl", ORANGE)):
            s.append(f'<marker id="{mid}" markerWidth="10" markerHeight="10" refX="7.5" refY="4" '
                     f'orient="auto" markerUnits="userSpaceOnUse">'
                     f'<path d="M0,0 L8,4 L0,8 Z" fill="{col}"/></marker>')
        s.append(f'<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">'
                 f'<path d="M40 0 L0 0 0 40" fill="none" stroke="#1B2740" stroke-width="1"/></pattern>')
        s.append(f'<linearGradient id="bgg" x1="0" y1="0" x2="0.6" y2="1">'
                 f'<stop offset="0" stop-color="{BG0}"/><stop offset="1" stop-color="{BG1}"/></linearGradient>')
        s.append('</defs>')
        s.append(f'<rect width="{self.w}" height="{self.h}" fill="url(#bgg)"/>')
        s.append(f'<rect width="{self.w}" height="{self.h}" fill="url(#grid)" opacity="0.5"/>')
        # header
        s.append(f'<rect x="40" y="34" width="34" height="6" rx="3" fill="{CYAN}"/>')
        s.append(f'<text x="40" y="74" font-family="{FONT}" font-size="30" font-weight="750" '
                 f'fill="{INK}">{html.escape(self.title)}</text>')
        s.append(f'<text x="40" y="100" font-family="{FONT}" font-size="14.5" fill="{MUTE}">'
                 f'{html.escape(self.subtitle)}</text>')
        s += self.body
        s.append('</svg>')
        return "\n".join(s)


def save(canvas, name):
    with open(os.path.join(OUT, name + ".svg"), "w") as f:
        f.write(canvas.render())
    print("wrote", name + ".svg")


# helper: center-right / center-left anchor points of a card rect
def rmid_r(x, y, w, h): return (x + w, y + h / 2)
def rmid_l(x, y, w, h): return (x, y + h / 2)
def rmid_t(x, y, w, h): return (x + w / 2, y)
def rmid_b(x, y, w, h): return (x + w / 2, y + h)


# ============================================================ ARCHITECTURE ===
def diagram_architecture():
    c = Canvas(1320, 660, "RV32I Single-Cycle Datapath",
               "One instruction per clock — fetch, decode, execute, memory, write-back")
    yc = 300
    # stage band labels
    stages = [("FETCH", 60, 250), ("DECODE", 330, 250), ("EXECUTE", 640, 200),
              ("MEMORY", 900, 250), ("WRITE-BACK", 1120, 160)]
    for nm, x, w in stages:
        c.add(f'<rect x="{x}" y="150" width="{w}" height="380" rx="18" fill="#ffffff" '
              f'opacity="0.45" stroke="{BORDER}" stroke-width="1.2"/>')
        c.label(x + w / 2, 178, nm, size=12.5, color=FAINT, weight=700, anchor="middle")

    pc = (70, yc - 35, 90, 70)
    c.card(*pc, "PC", "counter", kind="ctrl")
    im = (190, yc - 45, 120, 90)
    c.card(*im, "Instruction", "Memory · ROM", kind="mem")
    cu = (345, 210, 150, 64); c.card(*cu, "Control Unit", "opcode → signals", kind="primary")
    rf = (345, yc - 50, 150, 100); c.card(*rf, "Register File", "32 × 32-bit", kind="ctrl")
    ig = (345, 430, 150, 64); c.card(*ig, "Immediate Gen", "I/S/B/U/J", kind="ctrl")
    ac = (655, 205, 150, 56); c.card(*ac, "ALU Control", "funct3 / funct7", kind="primary")
    alu = (655, yc - 50, 150, 100); c.card(*alu, "ALU", "add·sub·shift·cmp", kind="alu")
    bc = (655, 430, 150, 60); c.card(*bc, "Branch Cmp", "beq…bgeu", kind="alu")
    dm = (915, yc - 50, 150, 100); c.card(*dm, "Data Memory", "RAM · lb/sw…", kind="mem")
    wb = (1130, yc - 40, 130, 80); c.card(*wb, "Write-Back", "MUX → rd", kind="mux")

    # data connections
    c.connect([rmid_r(*pc), rmid_l(*im)], "bus")
    c.connect([rmid_r(*im), (330, yc), rmid_l(*rf)], "bus")
    c.connect([(im[0] + im[2] / 2, im[1]), (250, 242), rmid_l(*cu)], "data")
    c.connect([(im[0] + im[2] / 2, im[1] + im[3]), (250, 462), rmid_l(*ig)], "data")
    c.connect([rmid_r(*rf), (560, yc - 18), (640, yc - 18), rmid_l(*alu)], "bus")
    c.connect([rmid_r(*ig), (560, 462), (620, 462), (620, yc + 22), rmid_l(*alu)], "bus")
    c.connect([rmid_r(*rf), (575, yc + 30), (575, 460), rmid_l(*bc)], "bus")
    c.connect([rmid_r(*alu), rmid_l(*dm)], "bus")
    c.connect([(rf[0] + rf[2], rf[1] + rf[3] - 18), (880, rf[1] + rf[3] - 18),
               (880, dm[1] + 20), rmid_l(*dm)], "bus")  # store data
    c.connect([rmid_r(*alu), (875, yc), (875, yc - 30), (1110, yc - 30), rmid_t(*wb)], "bus")
    c.connect([rmid_r(*dm), rmid_l(*wb)], "bus")
    # write-back to register file
    c.connect([rmid_b(*wb), (1195, 590), (300, 590), (300, rf[1] + rf[3] - 12),
               rmid_l(rf[0], rf[1] + rf[3] - 24, 0, 0)], "bus")
    c.label(700, 610, "write-back data → rd", size=11.5, color=FAINT, anchor="middle", mono=True)
    # next-PC feedback
    c.connect([rmid_b(*ig), (420, 510), (40, 510), (40, yc), rmid_l(*pc)], "ctrl")
    c.connect([rmid_b(*bc), (730, 540), (55, 540), (55, yc + 22), (pc[0], yc + 22)], "ctrl")
    # control fan
    c.connect([rmid_t(*cu), (420, 150), (640, 150), (730, 150), rmid_t(*ac)], "ctrl", dash=True)
    c.connect([rmid_b(*ac), rmid_t(*alu)], "ctrl", dash=True)

    # legend
    lx = 920
    c.add(f'<rect x="{lx}" y="560" width="360" height="62" rx="12" fill="#ffffff" '
          f'opacity="0.7" stroke="{BORDER}"/>')
    c.add(f'<line x1="{lx+18}" y1="580" x2="{lx+52}" y2="580" stroke="{LINE_DK}" stroke-width="3"/>')
    c.label(lx + 60, 584, "data / bus", size=12, color=MUTE)
    c.add(f'<line x1="{lx+18}" y1="604" x2="{lx+52}" y2="604" stroke="{CORAL}" stroke-width="3" stroke-dasharray="6 5"/>')
    c.label(lx + 60, 608, "control signal", size=12, color=MUTE)
    c.add(f'<rect x="{lx+180}" y="572" width="16" height="16" rx="4" fill="#9B86C2"/>')
    c.label(lx + 204, 584, "32-bit bus", size=12, color=MUTE)
    save(c, "architecture")


# ==================================================================== CPU ====
def diagram_cpu():
    c = Canvas(1320, 720, "Top-Level CPU", "How the ten subcircuits are wired into the datapath")
    yc = 330
    pc = (60, yc - 35, 96, 70);  c.card(*pc, "PC", "program counter", kind="ctrl")
    p4 = (60, 150, 96, 50);      c.card(*p4, "PC + 4", kind="alu")
    npc = (60, yc + 90, 96, 56); c.card(*npc, "next-PC", "MUX", kind="mux")
    im = (200, yc - 45, 130, 90);c.card(*im, "Instruction", "Memory", kind="mem")
    cu = (380, 150, 160, 64);    c.card(*cu, "Control Unit", "opcode → ctrl", kind="primary")
    ig = (380, 250, 160, 60);    c.card(*ig, "Immediate Gen", "sign-extend", kind="ctrl")
    rf = (380, yc + 10, 160, 110);c.card(*rf, "Register File", "32 × 32-bit", kind="ctrl")
    ac = (610, 150, 150, 56);    c.card(*ac, "ALU Control", "funct3/7 → op", kind="primary")
    bt = (610, 235, 150, 50);    c.card(*bt, "PC + imm", "branch/jal target", kind="alu")
    alu = (610, yc - 5, 150, 96);c.card(*alu, "ALU", "compute", kind="alu")
    bc = (610, yc + 130, 150, 60);c.card(*bc, "Branch Cmp", "condition", kind="alu")
    dm = (830, yc - 5, 160, 96); c.card(*dm, "Data Memory", "load / store", kind="mem")
    wb = (1060, yc - 5, 140, 96);c.card(*wb, "Write-Back MUX", "ALU·mem·PC+4", kind="mux")

    c.connect([rmid_r(*pc), rmid_l(*im)], "bus")
    c.connect([rmid_t(*pc), (108, 130), rmid_l(*p4)], "bus")
    c.connect([rmid_b(*npc), (40, yc + 118), (40, yc), rmid_l(*pc)], "bus")
    c.connect([rmid_r(*p4), (180, 175), (180, yc + 100), rmid_l(*npc)], "data")
    c.connect([rmid_r(*im), (355, yc), rmid_l(*rf)], "bus")
    c.connect([(im[0]+im[2]/2, im[1]), (265, 182), rmid_l(*cu)], "data")
    c.connect([(im[0]+im[2]/2, im[1]+im[3]), (265, 280), rmid_l(*ig)], "data")
    c.connect([rmid_r(*rf), (575, yc + 40), rmid_l(*alu)], "bus")
    c.connect([rmid_r(*ig), (560, 280), (590, 280), (590, yc + 60), rmid_l(*alu)], "bus")
    c.connect([rmid_r(*ig), (565, 260), rmid_l(*bt)], "data")
    c.connect([rmid_r(*rf), (560, yc + 70), (560, yc + 160), rmid_l(*bc)], "bus")
    c.connect([rmid_r(*alu), rmid_l(*dm)], "bus")
    c.connect([(rf[0]+rf[2], rf[1]+rf[3]-20), (810, rf[1]+rf[3]-20), (810, dm[1]+18), rmid_l(*dm)], "bus")
    c.connect([rmid_t(*alu), (685, yc - 30), (1090, yc - 30), rmid_t(*wb)], "bus")
    c.connect([rmid_r(*dm), rmid_l(*wb)], "bus")
    c.connect([rmid_b(*wb), (1130, 640), (220, 640), (220, rf[1]+rf[3]-14),
               (rf[0], rf[1]+rf[3]-26)], "bus")
    c.connect([rmid_r(*bt), (790, 260), (790, yc + 230), (120, yc + 230), rmid_b(*npc)], "data")
    # control (dashed coral)
    c.connect([rmid_r(*cu), (575, 182), rmid_l(*ac)], "ctrl", dash=True)
    c.connect([rmid_b(*ac), (685, 215), rmid_t(*alu)], "ctrl", dash=True)
    c.connect([rmid_b(*bc), (700, yc + 250), (120, yc + 250), rmid_b(npc[0]+30, npc[1], 0, 0)], "ctrl", dash=True)
    c.label(660, 690, "write-back bus → register write port", size=11.5, color=FAINT, anchor="middle", mono=True)
    save(c, "CPU")


# ===================================================================== PC ====
def diagram_pc():
    c = Canvas(940, 420, "Program Counter", "Holds the address of the current instruction")
    inp = c.port(60, 180, "next_pc", "in", bus=True); c.bustag(inp[0]+inp[2]+34, 195, "32")
    rs = c.port(60, 250, "reset", "clk")
    ck = c.port(60, 305, "clk", "clk")
    mux = (320, 175, 90, 70); c.card(*mux, "MUX", "reset→0", kind="mux")
    reg = (520, 165, 150, 90); c.card(*reg, "PC Register", "32-bit, clocked", kind="ctrl")
    out = c.port(770, 200, "pc", "out"); c.bustag(out[0]-20, 215, "32")
    c.connect([(inp[0]+inp[2], 195), rmid_l(*mux)], "bus")
    c.connect([(rs[0]+rs[2], 265), (270, 265), (270, 225), rmid_b(*mux)], "ctrl")
    c.connect([rmid_r(*mux), rmid_l(*reg)], "bus")
    c.connect([(ck[0]+ck[2], 320), (470, 320), (470, reg[1]+reg[3]), rmid_b(*reg)], "data")
    c.connect([rmid_r(*reg), (out[0], 215)], "bus")
    # feedback hint
    c.connect([rmid_t(*reg), (595, 130), (270, 130), (270, 175)], "data")
    c.label(430, 120, "← next-PC fed back from datapath", size=11.5, color=FAINT, mono=True)
    save(c, "PC")


# ==================================================== INSTRUCTION MEMORY =====
def diagram_instr_mem():
    c = Canvas(980, 470, "Instruction Memory",
               "Read-only memory holding the program; addressed by the PC")
    inp = c.port(60, 210, "pc", "in"); c.bustag(inp[0]+inp[2]+18, 225, "32")
    rom = (300, 175, 170, 110); c.card(*rom, "ROM", "32-bit words", kind="mem")
    out = c.port(560, 215, "instruction", "out"); c.bustag(out[0]+out[2]+18, 230, "32")
    c.connect([(inp[0]+inp[2], 225), rmid_l(*rom)], "bus")
    c.connect([rmid_r(*rom), (out[0], 230)], "bus")
    # field breakdown
    fields = [("funct7", "31:25", "#3B1D0B", ORANGE), ("rs2", "24:20", "#123524", GREEN),
              ("rs1", "19:15", "#123524", GREEN), ("funct3", "14:12", "#3B1D0B", ORANGE),
              ("rd", "11:7", "#10213A", "#60A5FA"), ("opcode", "6:0", "#3B2F0B", GOLD)]
    fx, fy, fw = 300, 330, 540
    c.label(fx, 322, "the 32-bit instruction decomposes into fields:", size=12, color=MUTE)
    x = fx
    widths = [90, 78, 78, 86, 70, 96]
    for (nm, rng, col, bd), wbox in zip(fields, widths):
        c.add(f'<rect x="{x}" y="{fy}" width="{wbox}" height="56" rx="9" fill="{col}" '
              f'stroke="{bd}" stroke-width="1.3"/>')
        c.label(x+wbox/2, fy+24, nm, size=12.5, color=INK, weight=650, anchor="middle", mono=True)
        c.label(x+wbox/2, fy+43, rng, size=10.5, color=MUTE, anchor="middle", mono=True)
        x += wbox + 6
    save(c, "Instruction_Memory")


# ========================================================== CONTROL UNIT =====
def diagram_control():
    c = Canvas(1180, 560, "Control Unit",
               "ROM decoder: maps the 7-bit opcode to every control signal")
    inp = c.port(60, 260, "opcode", "in"); c.bustag(inp[0]+inp[2]+18, 275, "7")
    rom = (250, 215, 170, 110); c.card(*rom, "Decode ROM", "opcode → 12 bits", kind="primary")
    c.connect([(inp[0]+inp[2], 275), rmid_l(*rom)], "bus")
    sigs = ["reg_write", "alu_src", "mem_read", "mem_write",
            "mem_to_reg", "branch", "jump", "alu_op", "imm_sel"]
    x0 = 620
    n = len(sigs)
    for i, s in enumerate(sigs):
        col = "row"
        oy = 150 + i * 28
        p = c.port(x0, oy, s, "out", w=120)
        c.connect([rmid_r(*rom), (520, 270), (560, 270), (560, oy + 15), (x0, oy + 15)], "ctrl")
    # opcode legend
    c.chip(900, 150, 250, 264, [
        "0x33  R-type", "0x13  I-type ALU", "0x03  Load", "0x23  Store",
        "0x63  Branch", "0x6F  JAL", "0x67  JALR", "0x37  LUI", "0x17  AUIPC",
    ], kind="plain", title="decoded opcodes")
    save(c, "Control_Unit")


# ============================================================ ALU CONTROL ====
def diagram_alu_control():
    c = Canvas(1120, 560, "ALU Control",
               "Decodes the exact ALU operation from alu_op, funct3 and funct7")
    a = c.port(60, 190, "alu_op", "in"); c.bustag(a[0]+a[2]+16, 205, "2")
    b = c.port(60, 250, "funct3", "in"); c.bustag(b[0]+b[2]+16, 265, "3")
    d = c.port(60, 310, "funct7_5", "in"); c.bustag(d[0]+d[2]+16, 325, "1")
    rom = (280, 215, 180, 110); c.card(*rom, "ROM", "6-bit addr → 4-bit op", kind="primary")
    for p, yy in ((a, 205), (b, 265), (d, 325)):
        c.connect([(p[0]+p[2], yy), (250, yy), (250, 270), rmid_l(*rom)], "bus")
    out = c.port(560, 255, "alu_ctrl", "out"); c.bustag(out[0]+out[2]+16, 270, "4")
    c.connect([rmid_r(*rom), (out[0], 270)], "bus")
    c.chip(760, 150, 300, 300, [
        "alu_op=00  → ADD   (addr calc)",
        "alu_op=01  → SUB   (branches)",
        "alu_op=10  → decode funct3/7:",
        "   000 → ADD/SUB    100 → XOR",
        "   001 → SLL        101 → SRL/SRA",
        "   010 → SLT        110 → OR",
        "   011 → SLTU       111 → AND",
        "alu_op=11  → pass B (LUI)",
    ], kind="plain", title="alu_op decode table")
    save(c, "ALU_Control")


# ====================================================== IMMEDIATE GENERATOR ==
def diagram_imm():
    c = Canvas(1180, 600, "Immediate Generator",
               "Reassembles and sign-extends the immediate for every instruction format")
    ins = c.port(60, 220, "instruction", "in"); c.bustag(ins[0]+ins[2]+18, 235, "32")
    sel = c.port(60, 470, "imm_sel", "in"); c.bustag(sel[0]+sel[2]+16, 485, "3")
    fmts = [("I-type", "imm[11:0]"), ("S-type", "stores"),
            ("B-type", "branches"), ("U-type", "lui/auipc"), ("J-type", "jal")]
    fx = 320
    rects = []
    for i, (nm, sub) in enumerate(fmts):
        yy = 130 + i * 70
        r = (fx, yy, 170, 54); rects.append(r)
        c.card(*r, nm, sub, kind="ctrl", fs=14)
        c.connect([(ins[0]+ins[2], 235), (270, 235), (270, yy + 27), rmid_l(*r)], "data")
    mux = (640, 235, 96, 150); c.card(*mux, "MUX", "imm_sel", kind="mux")
    for r in rects:
        c.connect([rmid_r(*r), (600, r[1] + 27), (600, 310), rmid_l(*mux)], "data")
    c.connect([(sel[0]+sel[2], 485), (688, 485), rmid_b(*mux)], "ctrl")
    out = c.port(830, 295, "imm_out", "out"); c.bustag(out[0]+out[2]+16, 310, "32")
    c.connect([rmid_r(*mux), (out[0], 310)], "bus")
    c.label(960, 250, "Each format scatters the", size=12.5, color=MUTE)
    c.label(960, 270, "immediate bits differently;", size=12.5, color=MUTE)
    c.label(960, 290, "all are sign-extended to", size=12.5, color=MUTE)
    c.label(960, 310, "a full 32-bit value.", size=12.5, color=MUTE)
    save(c, "Imediate_Generator")


# =========================================================== REGISTER FILE ===
def diagram_regfile():
    c = Canvas(1180, 620, "Register File",
               "32 × 32-bit registers · two read ports, one write port · x0 hard-wired to 0")
    rs1 = c.port(60, 170, "rs1", "in"); c.bustag(rs1[0]+rs1[2]+14, 185, "5")
    rs2 = c.port(60, 225, "rs2", "in"); c.bustag(rs2[0]+rs2[2]+14, 240, "5")
    rd  = c.port(60, 300, "rd", "in"); c.bustag(rd[0]+rd[2]+14, 315, "5")
    wd  = c.port(60, 355, "write_data", "in"); c.bustag(wd[0]+wd[2]+14, 370, "32")
    we  = c.port(60, 420, "reg_write", "ctrl")
    ck  = c.port(60, 475, "clk", "clk")

    dec = (330, 295, 120, 70); c.card(*dec, "Decoder", "write enable", kind="mux")
    bank = (520, 150, 200, 320); c.card(*bank, "Register Bank", "x0..x31  (x0 = 0)", kind="ctrl")
    m1 = (800, 165, 96, 70); c.card(*m1, "read MUX", "rs1", kind="mux")
    m2 = (800, 285, 96, 70); c.card(*m2, "read MUX", "rs2", kind="mux")
    o1 = c.port(960, 185, "read_data1", "out"); c.bustag(o1[0]+o1[2]+14, 200, "32")
    o2 = c.port(960, 305, "read_data2", "out"); c.bustag(o2[0]+o2[2]+14, 320, "32")

    c.connect([(rd[0]+rd[2], 315), rmid_l(*dec)], "data")
    c.connect([(we[0]+we[2], 435), (290, 435), (290, 350), rmid_b(*dec)], "ctrl")
    c.connect([rmid_r(*dec), (490, 330), (490, 420), (bank[0], 420)], "ctrl")
    c.connect([(wd[0]+wd[2], 370), (250, 370), (250, 250), (bank[0], 250)], "bus")
    c.connect([(ck[0]+ck[2], 490), (560, 490), (560, bank[1]+bank[3]), rmid_b(*bank)], "data")
    c.connect([(rs1[0]+rs1[2], 185), (270, 185), (270, 200), (bank[0], 200)], "data")
    c.connect([(rs2[0]+rs2[2], 240), (300, 240), (300, 224), (bank[0], 224)], "data")
    c.connect([rmid_r(*bank), (760, 310), (760, 200), rmid_l(*m1)], "bus")
    c.connect([rmid_r(*bank), rmid_l(*m2)], "bus")
    c.connect([rmid_r(*m1), (o1[0], 200)], "bus")
    c.connect([rmid_r(*m2), (o2[0], 320)], "bus")
    save(c, "Register_File")


# ===================================================================== ALU ===
def diagram_alu():
    c = Canvas(1180, 640, "Arithmetic Logic Unit",
               "All RV32I integer operations; a 4-bit code selects the result")
    a = c.port(60, 230, "a", "in"); c.bustag(a[0]+a[2]+14, 245, "32")
    b = c.port(60, 360, "b", "in"); c.bustag(b[0]+b[2]+14, 375, "32")
    ctl = c.port(60, 470, "alu_ctrl", "in"); c.bustag(ctl[0]+ctl[2]+14, 485, "4")
    ops = ["ADD", "SUB", "AND", "OR", "XOR", "SLL", "SRL", "SRA", "SLT", "SLTU", "passB"]
    col_x, col_y, bw, bh = 300, 150, 110, 34
    rects = []
    for i, op in enumerate(ops):
        yy = col_y + i * 40
        r = (col_x, yy, bw, bh); rects.append((r, op))
        kind = "alu"
        fill, bd, tc, sc = KINDS[kind]
        c.add(f'<rect x="{col_x}" y="{yy}" width="{bw}" height="{bh}" rx="9" fill="{fill}" '
              f'stroke="{bd}" stroke-width="1.4"/>')
        c.label(col_x + bw / 2, yy + 22, op, size=13, color="#FFEDD5", weight=650, anchor="middle", mono=True)
        c.connect([(a[0]+a[2], 245), (250, 245), (250, yy + bh / 2), (col_x, yy + bh / 2)],
                  "data", arrow=True, width=1.6)
    mux = (560, 240, 100, 200); c.card(*mux, "MUX", "select op", kind="mux")
    for r, op in rects:
        c.connect([rmid_r(*r), (520, r[1] + r[3] / 2), (520, 340), rmid_l(*mux)],
                  "data", arrow=False, width=1.4)
    c.connect([(ctl[0]+ctl[2], 485), (610, 485), rmid_b(*mux)], "ctrl")
    res = c.port(720, 290, "result", "out"); c.bustag(res[0]+res[2]+14, 305, "32")
    c.connect([rmid_r(*mux), (res[0], 305)], "bus")
    zero = c.port(720, 380, "zero", "out")
    zc = (720, 380);
    c.connect([(mux[0]+mux[2], 420), (700, 420), (700, 395), (zero[0], 395)], "data")
    c.label(900, 250, "Each operation has its own", size=12.5, color=MUTE)
    c.label(900, 270, "functional block (adder,", size=12.5, color=MUTE)
    c.label(900, 290, "shifters, comparators…).", size=12.5, color=MUTE)
    c.label(900, 310, "The 4-bit alu_ctrl chooses", size=12.5, color=MUTE)
    c.label(900, 330, "which result leaves the MUX.", size=12.5, color=MUTE)
    c.label(900, 360, "zero flag → branch logic.", size=12.5, color=FAINT)
    save(c, "ALU")


# ========================================================= BRANCH COMPARATOR =
def diagram_branch():
    c = Canvas(1080, 520, "Branch Comparator",
               "Evaluates the six RV32I branch conditions")
    a = c.port(60, 190, "a (rs1)", "in"); c.bustag(a[0]+a[2]+14, 205, "32")
    b = c.port(60, 250, "b (rs2)", "in"); c.bustag(b[0]+b[2]+14, 265, "32")
    f = c.port(60, 320, "funct3", "in"); c.bustag(f[0]+f[2]+14, 335, "3")
    cmp = (320, 175, 150, 80); c.card(*cmp, "Comparators", "signed + unsigned", kind="alu")
    sel = (320, 300, 150, 70); c.card(*sel, "Condition MUX", "funct3 select", kind="mux")
    c.connect([(a[0]+a[2], 205), (290, 205), rmid_l(*cmp)], "bus")
    c.connect([(b[0]+b[2], 265), (290, 265), (290, 230), rmid_l(cmp[0], 210, 0, 0)], "bus")
    c.connect([(f[0]+f[2], 335), rmid_l(*sel)], "data")
    c.connect([rmid_b(*cmp), (395, 280), rmid_t(*sel)], "data")
    out = c.port(560, 320, "branch_taken", "out")
    c.connect([rmid_r(*sel), (out[0], 335)], "data")
    c.chip(760, 165, 270, 210, [
        "beq   a == b", "bne   a != b",
        "blt   a <  b   (signed)", "bge   a >= b   (signed)",
        "bltu  a <  b   (unsigned)", "bgeu  a >= b   (unsigned)",
    ], kind="plain", title="branch conditions")
    save(c, "Branch_Comparator")


# ============================================================== DATA MEMORY ==
def diagram_data_mem():
    c = Canvas(1220, 600, "Data Memory",
               "Word-addressed RAM with byte / half / word load & store support")
    addr = c.port(60, 180, "address", "in"); c.bustag(addr[0]+addr[2]+14, 195, "32")
    wd = c.port(60, 240, "write_data", "in"); c.bustag(wd[0]+wd[2]+14, 255, "32")
    f3 = c.port(60, 310, "funct3", "in"); c.bustag(f3[0]+f3[2]+14, 325, "3")
    mr = c.port(60, 375, "mem_read", "ctrl")
    mw = c.port(60, 430, "mem_write", "ctrl")
    ck = c.port(60, 485, "clk", "clk")
    align = (330, 215, 140, 70); c.card(*align, "Store Align", "byte/half/word", kind="ctrl")
    ram = (540, 200, 160, 110); c.card(*ram, "RAM", "32-bit cells", kind="mem")
    ext = (770, 215, 150, 80); c.card(*ext, "Load Extend", "sign / zero", kind="ctrl")
    out = c.port(1000, 240, "read_data", "out"); c.bustag(out[0]+out[2]+14, 255, "32")

    c.connect([(addr[0]+addr[2], 195), (300, 195), (300, 230), rmid_l(*ram)], "bus")
    c.connect([(addr[0]+addr[2], 195), (510, 195), (510, 215), (ram[0], 215)], "bus")
    c.connect([(wd[0]+wd[2], 255), rmid_l(*align)], "bus")
    c.connect([rmid_r(*align), rmid_l(*ram)], "bus")
    c.connect([rmid_r(*ram), rmid_l(*ext)], "bus")
    c.connect([rmid_r(*ext), (out[0], 255)], "bus")
    c.connect([(f3[0]+f3[2], 325), (300, 325), (300, 295), rmid_b(align[0], 215, align[2], 70)], "ctrl")
    c.connect([(f3[0]+f3[2], 325), (740, 325), (740, 295), rmid_b(*ext)], "ctrl")
    c.connect([(mw[0]+mw[2], 445), (500, 445), (500, ram[1]+ram[3]), rmid_b(ram[0], 200, ram[2], 110)], "ctrl")
    c.connect([(mr[0]+mr[2], 390), (760, 390), (760, ext[1]+ext[3]), rmid_b(*ext)], "ctrl")
    c.connect([(ck[0]+ck[2], 500), (620, 500), (620, ram[1]+ram[3]), rmid_b(ram[0]+40, 200, ram[2], 110)], "data")
    c.chip(540, 360, 480, 110, [
        "loads : lb  lh  lw  lbu  lhu   (funct3)",
        "stores: sb  sh  sw",
        "lb/lh sign-extend · lbu/lhu zero-extend",
    ], kind="plain", title="access widths")
    save(c, "Data_Memory")


# The top-level datapath (architecture / CPU) is rendered as Mermaid in the
# docs — its dense feedback routing is far cleaner with auto-layout. Here we
# emit the per-module schematics as hand-laid-out dark SVGs.
for fn in [diagram_pc, diagram_instr_mem,
           diagram_control, diagram_alu_control, diagram_imm, diagram_regfile,
           diagram_alu, diagram_branch, diagram_data_mem]:
    fn()
print("\nall diagrams written to", OUT)
