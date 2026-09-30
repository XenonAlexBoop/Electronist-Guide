"""
uikit.py - Small UI building blocks shared by the v6 pages (diode lab,
op-amp lab, filter lab, AC phasors, modulation):

  Segmented   - a row of toggle buttons (one active), easier to scan than a
                drop-down when there are only a handful of choices
  ParamForm   - label / entry / unit rows (+ optional slider), with values
                parsed from engineering notation (4.7k, 100n, 2u2 ...)
  Tile        - a coloured result "tile" (big value + small caption)
  section     - an accent-coloured section heading
"""
import math
import tkinter as tk
from tkinter import ttk

from widgets import parse_value, debounce, FONT_H2, FONT_BODY

CARD = "#FFFFFF"
INK = "#1f2a44"
MUTED = "#5b6475"
SOFT = "#eef1f6"


def section(parent, text, accent, pady=(12, 4), **pack):
    lab = ttk.Label(parent, text=text, font=FONT_H2, foreground=accent, style="CardSub.TLabel")
    lab.pack(anchor="w", padx=pack.get("padx", 16), pady=pady)
    return lab


def note(parent, text, wrap=430, padx=16, pady=(0, 6), italic=False, color=None):
    lab = ttk.Label(parent, text=text, font=("Segoe UI", 9, "italic" if italic else "normal"),
                    style="CardBody.TLabel", wraplength=wrap, justify="left")
    if color:
        lab.configure(foreground=color)
    lab.pack(anchor="w", padx=padx, pady=pady)
    return lab


class Segmented(tk.Frame):
    """Toggle-button row. options: list of (key, text). Calls command(key)."""

    def __init__(self, parent, options, variable, command=None, accent="#1f6a5f", wrap=0, font_size=9,
                 bg=CARD):
        super().__init__(parent, bg=bg)
        self.var = variable
        self.command = command
        self.accent = accent
        self.buttons = {}
        for i, (key, text) in enumerate(options):
            b = tk.Label(self, text=text, font=("Segoe UI", font_size, "bold"), padx=10, pady=5,
                         cursor="hand2", bd=1, relief="solid")
            r, c = (i // wrap, i % wrap) if wrap else (0, i)
            b.grid(row=r, column=c, padx=(0, 3), pady=(0, 3), sticky="ew")
            b.bind("<Button-1>", lambda _e, k=key: self.select(k))
            self.buttons[key] = b
        self._paint()

    def select(self, key, fire=True):
        self.var.set(key)
        self._paint()
        if fire and self.command:
            self.command(key)

    def _paint(self):
        cur = self.var.get()
        for k, b in self.buttons.items():
            if k == cur:
                b.configure(bg=self.accent, fg="white", highlightbackground=self.accent)
            else:
                b.configure(bg=SOFT, fg=INK)


class ParamForm(ttk.Frame):
    """fields: list of dicts {key, label, default, unit, slider:(lo, hi, log?)}.
    on_change() is called (debounced) whenever a value changes."""

    def __init__(self, parent, fields, on_change, label_width=22, entry_width=9):
        super().__init__(parent, style="Card.TFrame")
        self.vars = {}
        self.on_change = on_change
        self._deb = debounce(self, lambda: on_change(), 180)
        self.columnconfigure(1, weight=0)
        self.columnconfigure(3, weight=1)
        self._sliders = {}
        self._ints = {f["key"] for f in fields if f.get("int")}
        for r, f in enumerate(fields):
            ttk.Label(self, text=f["label"], font=FONT_BODY, style="CardBody.TLabel",
                      width=max(label_width, len(f["label"]) + 1),
                      anchor="w").grid(row=r, column=0, sticky="w", pady=2)
            v = tk.StringVar(value=str(f["default"]))
            e = ttk.Entry(self, textvariable=v, width=entry_width)
            e.grid(row=r, column=1, sticky="w", pady=2)
            e.bind("<KeyRelease>", lambda _e, k=f["key"]: self._typed(k))
            e.bind("<Return>", lambda _e: on_change())
            ttk.Label(self, text=f.get("unit", ""), font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=r, column=2, sticky="w", padx=(4, 8))
            self.vars[f["key"]] = v
            if f.get("slider"):
                lo, hi, lg = (list(f["slider"]) + [False])[:3]
                s = ttk.Scale(self, from_=0, to=1000, orient="horizontal", length=150)
                s.grid(row=r, column=3, sticky="ew", pady=2)
                self._sliders[f["key"]] = (s, lo, hi, lg)
                s.configure(command=lambda pos, k=f["key"]: self._slid(k, pos))
                self._sync_slider(f["key"])
        self._lock = False

    # slider <-> entry mapping -------------------------------------------
    def _to_pos(self, key, val):
        s, lo, hi, lg = self._sliders[key]
        if lg:
            val = max(val, lo)
            return 1000 * (math.log10(val) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
        return 1000 * (val - lo) / (hi - lo)

    def _from_pos(self, key, pos):
        s, lo, hi, lg = self._sliders[key]
        p = float(pos) / 1000
        if lg:
            return 10 ** (math.log10(lo) + p * (math.log10(hi) - math.log10(lo)))
        return lo + p * (hi - lo)

    def _sync_slider(self, key):
        if key not in self._sliders:
            return
        try:
            v = parse_value(self.vars[key].get())
        except Exception:
            return
        self._lock = True
        try:
            self._sliders[key][0].set(max(0, min(1000, self._to_pos(key, v))))
        finally:
            self._lock = False

    def _slid(self, key, pos):
        if getattr(self, "_lock", False):
            return
        v = self._from_pos(key, pos)
        self.vars[key].set(str(int(round(v))) if key in self._ints else _nice(v))
        self._deb()

    def _typed(self, key):
        self._sync_slider(key)
        self._deb()

    # -------------------------------------------------------------------
    def get(self, key):
        return parse_value(self.vars[key].get())

    def values(self):
        return {k: parse_value(v.get()) for k, v in self.vars.items()}

    def set(self, key, value):
        self.vars[key].set(value if isinstance(value, str) else _nice(value))
        self._sync_slider(key)


def _nice(v):
    """Short engineering-notation text for an entry field."""
    if v == 0:
        return "0"
    av = abs(v)
    for sym, f in (("G", 1e9), ("M", 1e6), ("k", 1e3), ("", 1), ("m", 1e-3), ("u", 1e-6), ("n", 1e-9), ("p", 1e-12)):
        if av >= f * 0.99999:
            x = v / f
            txt = f"{x:.3g}"
            return txt + sym
    return f"{v:.3g}"


nice = _nice


class Tile(tk.Frame):
    """Result tile: small caption over a big value."""

    def __init__(self, parent, caption, accent, width=130):
        super().__init__(parent, bg=SOFT, highlightthickness=0, width=width)
        tk.Frame(self, bg=accent, height=3).pack(fill="x")
        self.cap = tk.Label(self, text=caption, font=("Segoe UI", 8), fg=MUTED, bg=SOFT, anchor="w")
        self.cap.pack(fill="x", padx=8, pady=(4, 0))
        self.val = tk.Label(self, text="–", font=("Consolas", 12, "bold"), fg=INK, bg=SOFT, anchor="w")
        self.val.pack(fill="x", padx=8, pady=(0, 6))

    def set(self, text, warn=False):
        self.val.configure(text=text, fg="#c62828" if warn else INK)


class TileRow(tk.Frame):
    def __init__(self, parent, captions, accent, per_row=4):
        super().__init__(parent, bg=CARD)
        self.tiles = {}
        for i, (key, cap) in enumerate(captions):
            tl = Tile(self, cap, accent)
            tl.grid(row=i // per_row, column=i % per_row, padx=(0, 6), pady=(0, 6), sticky="nsew")
            self.tiles[key] = tl
        for c in range(per_row):
            self.columnconfigure(c, weight=1, uniform="tiles")

    def set(self, key, text, warn=False):
        self.tiles[key].set(text, warn)


def eng(v, unit, digits=3):
    """Format with SI prefix: eng(0.0047, 'F') -> '4.7 mF'."""
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "–"
    if v == 0:
        return f"0 {unit}"
    av = abs(v)
    for sym, f in (("T", 1e12), ("G", 1e9), ("M", 1e6), ("k", 1e3), ("", 1), ("m", 1e-3), ("µ", 1e-6),
                   ("n", 1e-9), ("p", 1e-12), ("f", 1e-15)):
        if av >= f * 0.99999:
            return f"{v / f:.{digits}g} {sym}{unit}"
    return f"{v:.{digits}g} {unit}"


# ---------------------------------------------------------------------------
# v6.3 layout helpers
class FitCanvas(tk.Canvas):
    """A canvas that shows a drawing made for a fixed "design size"
    (base_w x base_h) scaled to the space it is given: coordinates, line
    widths and font sizes grow together (between kmin and kmax) and the
    picture is centred.  Use .show(fn) where fn() draws on the canvas at
    design size (it may call canvas.delete("all") itself)."""

    def __init__(self, parent, base_w, base_h, kmin=0.7, kmax=1.8, bg="#fdfaf3", height=None, **kw):
        super().__init__(parent, width=base_w, height=height or base_h, bg=bg,
                         highlightthickness=0, **kw)
        self.base_w, self.base_h = base_w, base_h
        self.kmin, self.kmax = kmin, kmax
        self._fn = None
        self.k = 1.0
        self.ox = self.oy = 0.0
        self._size = (0, 0)
        self.bind("<Configure>", debounce(self, self._on_resize, 60))

    def _on_resize(self, e=None):
        size = (self.winfo_width(), self.winfo_height())
        if size == self._size:
            return
        self._size = size
        self.refresh()

    def show(self, fn):
        self._fn = fn
        self.refresh()

    def refresh(self):
        if self._fn is None:
            return
        self.delete("all")
        self._fn()
        w, h = self.winfo_width(), self.winfo_height()
        if w < 20 or h < 20:
            w, h = self.base_w, self.base_h
        k = max(self.kmin, min(self.kmax, w / self.base_w, h / self.base_h))
        self.k = k
        self.ox = (w - self.base_w * k) / 2
        self.oy = (h - self.base_h * k) / 2
        if abs(k - 1) > 1e-3:
            self.scale("all", 0, 0, k, k)
            for item in self.find_all():
                typ = self.type(item)
                try:
                    if typ == "text":
                        f = list(self.tk.splitlist(self.itemcget(item, "font")))
                        if len(f) >= 2:
                            size = int(f[1])
                            f[1] = str(int(round(size * k)) if size > 0 else int(round(size * k)))
                            self.itemconfigure(item, font=tuple(f))
                        wd = float(self.itemcget(item, "width") or 0)
                        if wd:
                            self.itemconfigure(item, width=wd * k)
                    elif typ in ("line", "rectangle", "oval", "polygon", "arc"):
                        wd = float(self.itemcget(item, "width") or 1)
                        self.itemconfigure(item, width=max(1.0, wd * (1 + (k - 1) * 0.75)))
                        if typ == "line" and self.itemcget(item, "arrow") != "none":
                            shp = [float(v) for v in self.tk.splitlist(self.itemcget(item, "arrowshape"))]
                            self.itemconfigure(item, arrowshape=tuple(v * k for v in shp))
                except (tk.TclError, ValueError):
                    pass
        self.move("all", self.ox, self.oy)

    def to_design(self, x, y):
        """Canvas (pixel) coordinates -> design coordinates (for clicks)."""
        return (x - self.ox) / self.k, (y - self.oy) / self.k


def two_columns(parent, left_min=460, left_weight=1, right_weight=2, gap=18, pady=(10, 10)):
    """Return (left, right) frames laid out side by side in `parent` (grid)."""
    from widgets import ScrollableFrame
    parent.columnconfigure(0, weight=1)
    parent.rowconfigure(0, weight=1)
    sf = ScrollableFrame(parent, style="Card.TFrame", fill_height=True)
    sf.grid(row=0, column=0, sticky="nsew")
    parent = sf.body
    parent.columnconfigure(0, weight=left_weight, minsize=left_min, uniform="2col")
    parent.columnconfigure(1, weight=right_weight, uniform="2col")
    parent.rowconfigure(0, weight=1)
    left = ttk.Frame(parent, style="Card.TFrame")
    left.grid(row=0, column=0, sticky="nsew", padx=(16, gap // 2), pady=pady)
    right = ttk.Frame(parent, style="Card.TFrame")
    right.grid(row=0, column=1, sticky="nsew", padx=(gap // 2, 16), pady=pady)
    return left, right
