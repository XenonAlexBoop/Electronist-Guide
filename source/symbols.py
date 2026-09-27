"""
symbols.py - Standard schematic symbols drawn on a tk.Canvas.

Every two-terminal symbol (resistor, capacitor, inductor, diode, battery...)
is drawn between two terminal points (x1, y1) -> (x2, y2) in ANY direction,
so the same function works for horizontal, vertical or diagonal placement.
The body is centred between the terminals and lead wires fill the rest.

Resistors follow the globally selected drawing standard:
    IEC 60617 (Europe / Romania)  -> rectangle
    ANSI / IEEE 315 (USA)         -> zig-zag
The choice is switched from the app header (see main.py) and every tab is
rebuilt, so all schematics in the app update at once.

Also provides SymbolGallery: a small card that shows the correct symbols
for a component family (used at the top of each component tab).
"""
import math
import tkinter as tk
from tkinter import ttk

from i18n import t

SYM_COLOR = "#1f2a44"
LABEL_COLOR = "#1f2a44"
VALUE_COLOR = "#555555"
CANVAS_BG = "#fdfaf3"

_STYLE = {"value": "IEC"}
_listeners = []


def get_style():
    return _STYLE["value"]


def set_style(style):
    if style not in ("IEC", "ANSI") or style == _STYLE["value"]:
        return
    _STYLE["value"] = style
    for cb in list(_listeners):
        cb()


def on_style_change(cb):
    _listeners.append(cb)


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------
class _Frame:
    """Local coordinate frame for a two-terminal symbol.
    a = distance along the terminal-to-terminal axis (0 = centre)
    b = perpendicular offset (negative b = 'above' for a left-to-right symbol)."""

    def __init__(self, x1, y1, x2, y2):
        self.x1, self.y1, self.x2, self.y2 = x1, y1, x2, y2
        dx, dy = x2 - x1, y2 - y1
        self.length = math.hypot(dx, dy) or 1.0
        self.ux, self.uy = dx / self.length, dy / self.length
        self.nx, self.ny = -self.uy, self.ux
        self.cx, self.cy = (x1 + x2) / 2, (y1 + y2) / 2

    def p(self, a, b=0.0):
        return (self.cx + a * self.ux + b * self.nx, self.cy + a * self.uy + b * self.ny)

    def pts(self, seq):
        out = []
        for a, b in seq:
            out.extend(self.p(a, b))
        return out


def _leads(canvas, f, half, color, width):
    """Wires from each terminal to the body edges (at a = +/- half)."""
    ax, ay = f.p(-half)
    bx, by = f.p(half)
    canvas.create_line(f.x1, f.y1, ax, ay, fill=color, width=width, capstyle="round")
    canvas.create_line(bx, by, f.x2, f.y2, fill=color, width=width, capstyle="round")


def _label(canvas, f, label, value, s, offset=None, side=-1):
    """Place the name (e.g. R1) and value (e.g. 4.7 kΩ) beside the symbol."""
    if not label and not value:
        return
    off = (offset if offset is not None else 20) * s
    horizontal = abs(f.ux) >= abs(f.uy)
    fs_l = max(7, round(9 * s))
    fs_v = max(7, round(8 * s))
    if horizontal:
        # above (side=-1) or below (side=+1) the body
        y = f.cy + side * off
        if side < 0:
            if value:
                canvas.create_text(f.cx, y, text=value, font=("Segoe UI", fs_v), fill=VALUE_COLOR, anchor="s")
                y -= fs_v + 6
            if label:
                canvas.create_text(f.cx, y, text=label, font=("Segoe UI", fs_l, "bold"), fill=LABEL_COLOR, anchor="s")
        else:
            if label:
                canvas.create_text(f.cx, y, text=label, font=("Segoe UI", fs_l, "bold"), fill=LABEL_COLOR, anchor="n")
                y += fs_l + 6
            if value:
                canvas.create_text(f.cx, y, text=value, font=("Segoe UI", fs_v), fill=VALUE_COLOR, anchor="n")
    else:
        x = f.cx + (off if side > 0 else -off)
        anchor = "w" if side > 0 else "e"
        if label and value:
            canvas.create_text(x, f.cy - 8 * s, text=label, font=("Segoe UI", fs_l, "bold"),
                               fill=LABEL_COLOR, anchor=anchor)
            canvas.create_text(x, f.cy + 8 * s, text=value, font=("Segoe UI", fs_v),
                               fill=VALUE_COLOR, anchor=anchor)
        else:
            canvas.create_text(x, f.cy, text=label or value, font=("Segoe UI", fs_l, "bold"),
                               fill=LABEL_COLOR, anchor=anchor)


def _arrow_across(canvas, f, s, color):
    """Diagonal arrow through the body = 'variable/adjustable' marker."""
    x0, y0 = f.p(-18 * s, 14 * s)
    x1, y1 = f.p(18 * s, -16 * s)
    canvas.create_line(x0, y0, x1, y1, fill=color, width=max(1, 1.5 * s), arrow="last",
                       arrowshape=(8 * s, 10 * s, 3 * s))


# ---------------------------------------------------------------------------
# Passive two-terminal symbols
# ---------------------------------------------------------------------------
def resistor(canvas, x1, y1, x2, y2, label=None, value=None, s=1.0, color=SYM_COLOR,
             width=2, style=None, variant="fixed", label_side=-1, label_offset=None):
    """variant: fixed | variable | pot | ntc | ldr"""
    style = style or get_style()
    f = _Frame(x1, y1, x2, y2)
    half = min(22 * s, f.length / 2 - 2)
    hh = 8 * s
    _leads(canvas, f, half, color, width)
    if style == "ANSI":
        n = 6
        seq = [(-half, 0)]
        for i in range(n):
            a = -half + (i + 0.5) * (2 * half / n)
            seq.append((a, -hh if i % 2 == 0 else hh))
        seq.append((half, 0))
        canvas.create_line(*f.pts(seq), fill=color, width=width, joinstyle="miter")
    else:
        canvas.create_polygon(*f.pts([(-half, -hh), (half, -hh), (half, hh), (-half, hh)]),
                              fill="", outline=color, width=width)
    if variant == "variable":
        _arrow_across(canvas, f, s, color)
    elif variant == "pot":
        x0, y0 = f.p(0, -26 * s)
        xa, ya = f.p(0, -hh - 1)
        canvas.create_line(x0, y0, xa, ya, fill=color, width=width, arrow="last",
                           arrowshape=(8 * s, 10 * s, 4 * s))
    elif variant == "ntc":
        pts = f.pts([(-24 * s, 16 * s), (-30 * s, 16 * s)])
        canvas.create_line(*f.pts([(-24 * s, 16 * s), (20 * s, -16 * s)]), fill=color, width=max(1, 1.5 * s))
        canvas.create_line(*pts, fill=color, width=max(1, 1.5 * s))
        tx, ty = f.p(26 * s, 14 * s)
        canvas.create_text(tx, ty, text="-t°", font=("Segoe UI", max(6, round(7 * s))), fill=color)
    elif variant == "ldr":
        for da in (-8, 6):
            xs, ys = f.p(da * s - 14 * s, -30 * s)
            xe, ye = f.p(da * s - 2 * s, -hh - 3 * s)
            canvas.create_line(xs, ys, xe, ye, fill=color, width=max(1, 1.5 * s), arrow="last",
                               arrowshape=(6 * s, 8 * s, 3 * s))
    _label(canvas, f, label, value, s, offset=label_offset, side=label_side)


def capacitor(canvas, x1, y1, x2, y2, label=None, value=None, s=1.0, color=SYM_COLOR,
              width=2, variant="fixed", label_side=-1, label_offset=None):
    """variant: fixed | polarized | variable"""
    f = _Frame(x1, y1, x2, y2)
    gap = 4 * s
    plate = 14 * s
    _leads(canvas, f, gap, color, width)
    pw = max(2, 3 * s)
    canvas.create_line(*f.pts([(-gap, -plate), (-gap, plate)]), fill=color, width=pw)
    if variant == "polarized":
        # curved negative plate + "+" marker by the straight plate
        seq = []
        for i in range(13):
            b = -plate + i * (2 * plate / 12)
            a = gap + 4 * s * (1 - (b / plate) ** 2) * 0 + 4 * s * ((b / plate) ** 2)
            seq.append((a, b))
        canvas.create_line(*f.pts(seq), fill=color, width=pw, smooth=True)
        px, py = f.p(-gap - 8 * s, -plate + 2 * s)
        canvas.create_text(px, py, text="+", font=("Segoe UI", max(7, round(10 * s)), "bold"), fill=color)
    else:
        canvas.create_line(*f.pts([(gap, -plate), (gap, plate)]), fill=color, width=pw)
    if variant == "variable":
        _arrow_across(canvas, f, s, color)
    _label(canvas, f, label, value, s, offset=(label_offset if label_offset is not None else 22), side=label_side)


def inductor(canvas, x1, y1, x2, y2, label=None, value=None, s=1.0, color=SYM_COLOR,
             width=2, core=None, variable=False, loops=4, label_side=-1, label_offset=None):
    """core: None (air) | 'iron' (solid lines) | 'ferrite' (dashed lines)"""
    f = _Frame(x1, y1, x2, y2)
    half = min(24 * s, f.length / 2 - 2)
    _leads(canvas, f, half, color, width)
    r = half / loops
    seq = []
    for i in range(loops):
        ca = -half + r + i * 2 * r
        for k in range(13):
            ang = math.pi - k * math.pi / 12
            seq.append((ca + r * math.cos(ang), -r * math.sin(ang)))
    canvas.create_line(*f.pts(seq), fill=color, width=width, smooth=False)
    if core:
        dash = (4, 3) if core == "ferrite" else None
        for off in (-r - 5 * s, -r - 9 * s):
            kw = {"dash": dash} if dash else {}
            canvas.create_line(*f.pts([(-half, off), (half, off)]), fill=color, width=max(1, 1.5 * s), **kw)
    if variable:
        _arrow_across(canvas, f, s, color)
    _label(canvas, f, label, value, s,
           offset=(label_offset if label_offset is not None else (30 if core else 20)), side=label_side)


def component(canvas, kind, x1, y1, x2, y2, label=None, value=None, s=1.0, **kw):
    """Dispatch by component kind ('resistor' / 'capacitor' / 'inductor')."""
    if kind == "capacitor":
        return capacitor(canvas, x1, y1, x2, y2, label, value, s, **kw)
    if kind == "inductor":
        return inductor(canvas, x1, y1, x2, y2, label, value, s, **kw)
    return resistor(canvas, x1, y1, x2, y2, label, value, s, **kw)


PREFIX_BY_KIND = {"resistor": "R", "capacitor": "C", "inductor": "L"}


# ---------------------------------------------------------------------------
# Semiconductors
# ---------------------------------------------------------------------------
def diode(canvas, x1, y1, x2, y2, label=None, value=None, s=1.0, color=SYM_COLOR, width=2,
          variant="std", fill=None, label_side=-1):
    """Anode at (x1,y1), cathode at (x2,y2).
    variant: std | zener | schottky | led | photo | varicap"""
    f = _Frame(x1, y1, x2, y2)
    half = 11 * s
    hh = 11 * s
    _leads(canvas, f, half, color, width)
    canvas.create_polygon(*f.pts([(-half, -hh), (-half, hh), (half, 0)]),
                          fill=fill if fill else color, outline=color, width=width)
    bar = [(half, -hh), (half, hh)]
    if variant == "zener":
        seq = [(half - 5 * s, -hh - 4 * s), (half, -hh), (half, hh), (half + 5 * s, hh + 4 * s)]
        canvas.create_line(*f.pts(seq), fill=color, width=width)
    elif variant == "schottky":
        seq = [(half + 5 * s, -hh + 5 * s), (half + 5 * s, -hh), (half, -hh), (half, hh),
               (half - 5 * s, hh), (half - 5 * s, hh - 5 * s)]
        canvas.create_line(*f.pts(seq), fill=color, width=width)
    else:
        canvas.create_line(*f.pts(bar), fill=color, width=width)
    if variant == "varicap":
        canvas.create_line(*f.pts([(half + 5 * s, -hh), (half + 5 * s, hh)]), fill=color, width=width)
    if variant in ("led", "photo"):
        for da in (-4, 6):
            if variant == "led":
                xs, ys = f.p(da * s, -hh - 3 * s)
                xe, ye = f.p(da * s + 10 * s, -hh - 17 * s)
            else:
                xs, ys = f.p(da * s + 10 * s, -hh - 17 * s)
                xe, ye = f.p(da * s, -hh - 3 * s)
            canvas.create_line(xs, ys, xe, ye, fill=color, width=max(1, 1.5 * s), arrow="last",
                               arrowshape=(6 * s, 8 * s, 3 * s))
    _label(canvas, f, label, value, s, offset=24, side=label_side)


def _circle(canvas, cx, cy, r, color, width):
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline=color, width=width)


def _devlabels(canvas, pts, s):
    fs = ("Segoe UI", max(6, round(8 * s)), "bold")
    for x, y, txt in pts:
        canvas.create_text(x, y, text=txt, font=fs, fill=VALUE_COLOR)


def bjt(canvas, cx, cy, s=1.0, npn=True, color=SYM_COLOR, width=2, labels=True, fy=1, circle=True):
    """Bipolar transistor. Base lead on the left (tip at cx-36s, cy).
    fy=+1: collector up (tip cx+12s, cy-36s), emitter down (cy+36s).
    fy=-1: mirrored vertically (emitter up, collector down) - used for PNP
    stages drawn with the emitter on the positive rail.
    NPN arrow points OUT of the emitter, PNP arrow points IN (towards base)."""
    Y = lambda d: cy + fy * d * s  # noqa: E731
    if circle:
        _circle(canvas, cx + 4 * s, cy, 22 * s, color, width)
    bar_x = cx - 6 * s
    canvas.create_line(bar_x, cy - 13 * s, bar_x, cy + 13 * s, fill=color, width=max(2, 3.5 * s))
    canvas.create_line(cx - 36 * s, cy, bar_x, cy, fill=color, width=width)            # base lead
    ex = cx + 12 * s
    canvas.create_line(bar_x, Y(-6), ex, Y(-18), fill=color, width=width)              # collector
    canvas.create_line(ex, Y(-18), ex, Y(-36), fill=color, width=width)
    ashape = (9 * s, 11 * s, 4 * s)
    if npn:
        canvas.create_line(bar_x, Y(6), ex, Y(18), fill=color, width=width, arrow="last", arrowshape=ashape)
    else:
        canvas.create_line(ex, Y(18), bar_x + 1, Y(6), fill=color, width=width, arrow="last", arrowshape=ashape)
    canvas.create_line(ex, Y(18), ex, Y(36), fill=color, width=width)                  # emitter
    if labels:
        _devlabels(canvas, [(cx - 32 * s, cy - 9 * s, "B"), (ex + 9 * s, Y(-31), "C"),
                            (ex + 9 * s, Y(31), "E")], s)


def mosfet(canvas, cx, cy, s=1.0, nch=True, enhancement=True, color=SYM_COLOR, width=2, labels=True,
           fy=1, circle=True):
    """MOSFET, body tied to source. Gate lead on the left (tip cx-36s, gate y),
    drain up / source down for fy=+1 (mirrored for fy=-1).
    Enhancement = broken channel (3 segments), depletion = solid channel.
    Body arrow points IN for N-channel, OUT for P-channel."""
    Y = lambda d: cy + fy * d * s  # noqa: E731
    if circle:
        _circle(canvas, cx + 4 * s, cy, 24 * s, color, width)
    gx = cx - 10 * s
    chx = cx - 3 * s
    dx = cx + 12 * s
    canvas.create_line(cx - 36 * s, Y(12), gx, Y(12), fill=color, width=width)       # gate lead (source side)
    canvas.create_line(gx, cy - 13 * s, gx, cy + 13 * s, fill=color, width=width)    # gate plate
    thick = max(2, 3.5 * s)
    if enhancement:
        for a, b in ((-15, -7), (-4, 4), (7, 15)):
            canvas.create_line(chx, cy + a * s, chx, cy + b * s, fill=color, width=thick)
    else:
        canvas.create_line(chx, cy - 15 * s, chx, cy + 15 * s, fill=color, width=thick)
    canvas.create_line(chx, Y(-11), dx, Y(-11), fill=color, width=width)             # drain stub
    canvas.create_line(dx, Y(-11), dx, Y(-38), fill=color, width=width)
    canvas.create_line(chx, Y(11), dx, Y(11), fill=color, width=width)               # source stub
    canvas.create_line(dx, Y(11), dx, Y(38), fill=color, width=width)
    canvas.create_line(dx, cy, dx, Y(11), fill=color, width=width)                   # body = source
    ashape = (8 * s, 10 * s, 4 * s)
    if nch:
        canvas.create_line(dx, cy, chx + 2, cy, fill=color, width=width, arrow="last", arrowshape=ashape)
    else:
        canvas.create_line(chx + 1, cy, dx, cy, fill=color, width=width, arrow="last", arrowshape=ashape)
    if labels:
        _devlabels(canvas, [(cx - 32 * s, Y(12) - 9 * s, "G"), (dx + 9 * s, Y(-32), "D"),
                            (dx + 9 * s, Y(32), "S")], s)


def jfet(canvas, cx, cy, s=1.0, nch=True, color=SYM_COLOR, width=2, labels=True, fy=1, circle=True):
    """JFET: gate lead with arrow on the source side; arrow points IN (towards
    the channel) for N-channel and OUT for P-channel."""
    Y = lambda d: cy + fy * d * s  # noqa: E731
    if circle:
        _circle(canvas, cx + 2 * s, cy, 22 * s, color, width)
    chx = cx - 2 * s
    dx = cx + 10 * s
    canvas.create_line(chx, cy - 15 * s, chx, cy + 15 * s, fill=color, width=max(2, 3.5 * s))
    gy = Y(9)
    ashape = (9 * s, 11 * s, 4 * s)
    if nch:
        canvas.create_line(cx - 36 * s, gy, chx - 1, gy, fill=color, width=width, arrow="last", arrowshape=ashape)
    else:
        canvas.create_line(cx - 36 * s, gy, chx, gy, fill=color, width=width)
        canvas.create_line(chx, gy, cx - 16 * s, gy, fill=color, width=width, arrow="last", arrowshape=ashape)
    canvas.create_line(chx, Y(-10), dx, Y(-10), dx, Y(-36), fill=color, width=width)
    canvas.create_line(chx, Y(10), dx, Y(10), dx, Y(36), fill=color, width=width)
    if labels:
        _devlabels(canvas, [(cx - 32 * s, gy - 9 * s, "G"), (dx + 9 * s, Y(-30), "D"),
                            (dx + 9 * s, Y(30), "S")], s)


def device_terminals(family, cx, cy, s=1.0, fy=1):
    """Terminal tip coordinates of a device symbol drawn at (cx, cy):
    returns dict  control -> (x, y), top -> (x, y), bottom -> (x, y), with
    names (B/G, C/D, E/S)."""
    Y = lambda d: cy + fy * d * s  # noqa: E731
    if family == "bjt":
        return {"B": (cx - 36 * s, cy), "C": (cx + 12 * s, Y(-36)), "E": (cx + 12 * s, Y(36))}
    if family == "mosfet":
        return {"G": (cx - 36 * s, Y(12)), "D": (cx + 12 * s, Y(-38)), "S": (cx + 12 * s, Y(38))}
    return {"G": (cx - 36 * s, Y(9)), "D": (cx + 10 * s, Y(-36)), "S": (cx + 10 * s, Y(36))}


def opamp(canvas, cx, cy, s=1.0, color=SYM_COLOR, width=2, supplies=False, fill=""):
    """Triangle with inverting (-) on top, non-inverting (+) below, output right."""
    left, right = cx - 30 * s, cx + 30 * s
    top, bot = cy - 32 * s, cy + 32 * s
    canvas.create_polygon(left, top, left, bot, right, cy, fill=fill, outline=color, width=width)
    fs = ("Segoe UI", max(8, round(12 * s)), "bold")
    canvas.create_text(left + 9 * s, cy - 14 * s, text="−", font=fs, fill=color)
    canvas.create_text(left + 9 * s, cy + 14 * s, text="+", font=fs, fill=color)
    canvas.create_line(left - 18 * s, cy - 14 * s, left, cy - 14 * s, fill=color, width=width)
    canvas.create_line(left - 18 * s, cy + 14 * s, left, cy + 14 * s, fill=color, width=width)
    canvas.create_line(right, cy, right + 18 * s, cy, fill=color, width=width)
    if supplies:
        fs2 = ("Segoe UI", max(6, round(7 * s)))
        canvas.create_line(cx, cy - 16 * s, cx, cy - 34 * s, fill=color, width=width)
        canvas.create_line(cx, cy + 16 * s, cx, cy + 34 * s, fill=color, width=width)
        canvas.create_text(cx + 4 * s, cy - 34 * s, text="+V", font=fs2, anchor="w", fill=VALUE_COLOR)
        canvas.create_text(cx + 4 * s, cy + 34 * s, text="−V", font=fs2, anchor="w", fill=VALUE_COLOR)


# ---------------------------------------------------------------------------
# Sources, ground, misc.
# ---------------------------------------------------------------------------
def cell(canvas, x1, y1, x2, y2, label=None, value=None, s=1.0, color=SYM_COLOR, width=2, cells=1,
         label_side=-1):
    """Battery: terminal 1 = positive (long plate), terminal 2 = negative."""
    f = _Frame(x1, y1, x2, y2)
    pitch = 8 * s
    half = (cells * 2 - 1) * pitch / 2
    _leads(canvas, f, half, color, width)
    for i in range(cells):
        a_long = -half + i * 2 * pitch
        a_short = a_long + pitch
        canvas.create_line(*f.pts([(a_long, -14 * s), (a_long, 14 * s)]), fill=color, width=width)
        canvas.create_line(*f.pts([(a_short, -7 * s), (a_short, 7 * s)]), fill=color, width=max(3, 4 * s))
    px, py = f.p(-half - 7 * s, -16 * s)
    canvas.create_text(px, py, text="+", font=("Segoe UI", max(7, round(9 * s)), "bold"), fill=color)
    _label(canvas, f, label, value, s, offset=26, side=label_side)


def dc_source(canvas, cx, cy, s=1.0, color=SYM_COLOR, width=2, label=None, vertical=True):
    r = 16 * s
    _circle(canvas, cx, cy, r, color, width)
    fs = ("Segoe UI", max(7, round(10 * s)), "bold")
    if vertical:
        canvas.create_text(cx, cy - 7 * s, text="+", font=fs, fill=color)
        canvas.create_text(cx, cy + 7 * s, text="−", font=fs, fill=color)
    if label:
        canvas.create_text(cx - r - 6 * s, cy, text=label, font=("Segoe UI", max(7, round(9 * s)), "bold"),
                           fill=LABEL_COLOR, anchor="e")


def ac_source(canvas, cx, cy, s=1.0, color=SYM_COLOR, width=2, label=None):
    r = 16 * s
    _circle(canvas, cx, cy, r, color, width)
    seq = []
    for k in range(25):
        x = cx - 10 * s + k * (20 * s / 24)
        seq.extend((x, cy - 6 * s * math.sin(2 * math.pi * k / 24)))
    canvas.create_line(*seq, fill=color, width=max(1, 1.5 * s), smooth=True)
    if label:
        canvas.create_text(cx - r - 6 * s, cy, text=label, font=("Segoe UI", max(7, round(9 * s)), "bold"),
                           fill=LABEL_COLOR, anchor="e")


def ground(canvas, x, y, s=1.0, color=SYM_COLOR, width=2):
    for i, dx in enumerate((12, 8, 4)):
        yy = y + i * 5 * s
        canvas.create_line(x - dx * s, yy, x + dx * s, yy, fill=color, width=width)


def node(canvas, x, y, s=1.0, color=SYM_COLOR):
    r = 3.5 * s
    canvas.create_oval(x - r, y - r, x + r, y + r, fill=color, outline="")


def terminal(canvas, x, y, s=1.0, color=SYM_COLOR, label=None, anchor="s", dy=-8):
    r = 4 * s
    canvas.create_oval(x - r, y - r, x + r, y + r, fill="white", outline=color, width=2)
    if label:
        canvas.create_text(x, y + dy * s, text=label, font=("Segoe UI", max(7, round(9 * s)), "bold"),
                           fill=LABEL_COLOR, anchor=anchor)


def wire(canvas, *coords, color=SYM_COLOR, width=2):
    canvas.create_line(*coords, fill=color, width=width, capstyle="round", joinstyle="round")


def current_arrow(canvas, x1, y1, x2, y2, text=None, color="#c62828", s=1.0, text_side=-1):
    """A small arrow drawn next to a wire to show current direction/value."""
    canvas.create_line(x1, y1, x2, y2, fill=color, width=2, arrow="last", arrowshape=(8 * s, 10 * s, 4 * s))
    if text:
        f = _Frame(x1, y1, x2, y2)
        horizontal = abs(f.ux) >= abs(f.uy)
        if horizontal:
            canvas.create_text(f.cx, f.cy + text_side * 10 * s, text=text, fill=color,
                               font=("Segoe UI", max(7, round(8 * s)), "bold"),
                               anchor="s" if text_side < 0 else "n")
        else:
            canvas.create_text(f.cx + (8 * s if text_side > 0 else -8 * s), f.cy, text=text, fill=color,
                               font=("Segoe UI", max(7, round(8 * s)), "bold"),
                               anchor="w" if text_side > 0 else "e")


def transformer(canvas, cx, cy, s=1.0, color=SYM_COLOR, width=2):
    inductor(canvas, cx - 14 * s, cy - 30 * s, cx - 14 * s, cy + 30 * s, s=s, color=color, width=width)
    # secondary drawn mirrored (bumps facing the core)
    inductor(canvas, cx + 14 * s, cy + 30 * s, cx + 14 * s, cy - 30 * s, s=s, color=color, width=width)
    for dx in (-3, 3):
        canvas.create_line(cx + dx * s, cy - 26 * s, cx + dx * s, cy + 26 * s, fill=color, width=max(1, 1.5 * s))


# ---------------------------------------------------------------------------
# Gallery widget
# ---------------------------------------------------------------------------
def _h(fn, **kw):
    """Wrap a two-terminal symbol so the gallery can draw it horizontally."""
    def draw(canvas, cx, cy, s):
        fn(canvas, cx - 50 * s, cy, cx + 50 * s, cy, s=s, **kw)
    return draw


def gallery_items(family):
    """Symbol list for each component family: (draw_fn, caption_key)."""
    if family == "resistor":
        return [
            (_h(resistor, style="IEC"), "sym.res_iec"),
            (_h(resistor, style="ANSI"), "sym.res_ansi"),
            (_h(resistor, variant="variable"), "sym.res_variable"),
            (_h(resistor, variant="pot"), "sym.res_pot"),
            (_h(resistor, variant="ntc"), "sym.res_ntc"),
            (_h(resistor, variant="ldr"), "sym.res_ldr"),
        ]
    if family == "capacitor":
        return [
            (_h(capacitor), "sym.cap_fixed"),
            (_h(capacitor, variant="polarized"), "sym.cap_polarized"),
            (_h(capacitor, variant="variable"), "sym.cap_variable"),
        ]
    if family == "inductor":
        return [
            (_h(inductor), "sym.ind_air"),
            (_h(inductor, core="iron"), "sym.ind_iron"),
            (_h(inductor, core="ferrite"), "sym.ind_ferrite"),
            (_h(inductor, variable=True), "sym.ind_variable"),
            (lambda c, x, y, s: transformer(c, x, y, s=s), "sym.transformer"),
        ]
    if family == "diode":
        return [
            (_h(diode), "sym.diode"),
            (_h(diode, variant="zener"), "sym.zener"),
            (_h(diode, variant="schottky"), "sym.schottky"),
            (_h(diode, variant="led", fill="#e53935"), "sym.led"),
            (_h(diode, variant="photo"), "sym.photodiode"),
            (_h(diode, variant="varicap"), "sym.varicap"),
        ]
    if family == "bjt":
        return [
            (lambda c, x, y, s: bjt(c, x, y, s=s, npn=True), "sym.npn"),
            (lambda c, x, y, s: bjt(c, x, y, s=s, npn=False), "sym.pnp"),
        ]
    if family == "mosfet":
        return [
            (lambda c, x, y, s: mosfet(c, x, y, s=s, nch=True), "sym.nmos_enh"),
            (lambda c, x, y, s: mosfet(c, x, y, s=s, nch=False), "sym.pmos_enh"),
            (lambda c, x, y, s: mosfet(c, x, y, s=s, nch=True, enhancement=False), "sym.nmos_dep"),
            (lambda c, x, y, s: mosfet(c, x, y, s=s, nch=False, enhancement=False), "sym.pmos_dep"),
        ]
    if family == "jfet":
        return [
            (lambda c, x, y, s: jfet(c, x, y, s=s, nch=True), "sym.njfet"),
            (lambda c, x, y, s: jfet(c, x, y, s=s, nch=False), "sym.pjfet"),
        ]
    if family == "opamp":
        return [
            (lambda c, x, y, s: opamp(c, x, y, s=s), "sym.opamp"),
            (lambda c, x, y, s: opamp(c, x, y, s=s, supplies=True), "sym.opamp_supply"),
        ]
    if family == "battery":
        return [
            (_h(cell), "sym.cell"),
            (_h(cell, cells=3), "sym.battery"),
            (lambda c, x, y, s: dc_source(c, x, y, s=s), "sym.dc_source"),
            (lambda c, x, y, s: ac_source(c, x, y, s=s), "sym.ac_source"),
            (lambda c, x, y, s: ground(c, x, y - 6 * s, s=s), "sym.ground"),
        ]
    return []


class SymbolGallery(ttk.Frame):
    """Card with a responsive grid of the standard schematic symbols for a
    component family (with captions), shown at the top of component tabs."""
    CELL_W = 150
    CELL_H = 100

    def __init__(self, parent, family, accent="#334155"):
        super().__init__(parent, style="Card.TFrame")
        self.items = gallery_items(family)
        self.accent = accent
        self.columnconfigure(0, weight=1)
        tk.Frame(self, bg=accent, height=6).grid(row=0, column=0, sticky="ew")
        ttk.Label(self, text=t("sym.gallery_title"), font=("Segoe UI", 12, "bold"),
                  style="CardSub.TLabel", foreground=accent)\
            .grid(row=1, column=0, sticky="w", padx=16, pady=(10, 0))
        hint = ttk.Label(self, text=t("sym.gallery_hint").format(style=get_style()), font=("Segoe UI", 8),
                         style="CardBody.TLabel", wraplength=300, justify="left")
        hint.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 4))
        self.bind("<Configure>", lambda e: hint.configure(wraplength=max(160, e.width - 40)), add="+")
        self.canvas = tk.Canvas(self, height=self.CELL_H, bg=CANVAS_BG, highlightthickness=0, width=300)
        self.canvas.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 12))
        self._cols = 0
        self.canvas.bind("<Configure>", self._on_resize)

    def _on_resize(self, event):
        cols = max(1, int(event.width // self.CELL_W))
        cols = min(cols, len(self.items)) or 1
        if cols == self._cols and abs(event.width - getattr(self, "_w", 0)) < 3 and self.canvas.find_all():
            return
        self._cols = cols
        self._w = event.width
        self._draw(event.width)

    def _draw(self, width):
        c = self.canvas
        c.delete("all")
        cols = self._cols
        rows = math.ceil(len(self.items) / cols)
        c.configure(height=rows * self.CELL_H)
        cell_w = width / cols
        for i, (fn, key) in enumerate(self.items):
            r, col = divmod(i, cols)
            cx = col * cell_w + cell_w / 2
            cy = r * self.CELL_H + 40
            try:
                fn(c, cx, cy, 0.8)
            except Exception:
                pass
            c.create_text(cx, r * self.CELL_H + self.CELL_H - 12, text=t(key),
                          font=("Segoe UI", 8), fill="#444")
