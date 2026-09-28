"""
theme.py - light / dark mode for the whole app.

Rather than rewriting every hard-coded colour in the code base, dark mode
works as a colour *transform* applied at the few places where colours
reach Tk and matplotlib:

  * tkinter.Misc._options          - every widget option, canvas item and
                                     text tag passes through here
  * tkinter.ttk._format_optdict /
    _format_mapdict                - ttk styles, Treeview tags
  * FigureCanvasAgg.draw           - every matplotlib artist is recoloured
                                     just before a figure is rendered

The transform keeps saturated colours (accents, electrons, warning red…)
and flips the lightness of neutral and pastel colours: white cards turn
dark grey, dark text turns light, pale region fills become deep tints.
Colours that must not change (resistor colour bands, the header bar) are
wrapped in keep().
"""
import colorsys
import functools
import tkinter as tk
from tkinter import ttk

_DARK = False
_listeners = []

COLOR_KEYS = {
    "background", "bg", "foreground", "fg", "fill", "outline", "activefill", "activeoutline",
    "disabledfill", "disabledoutline", "activebackground", "activeforeground", "highlightbackground",
    "highlightcolor", "selectbackground", "selectforeground", "insertbackground", "troughcolor",
    "disabledforeground", "readonlybackground", "fieldbackground", "bordercolor", "lightcolor",
    "darkcolor", "arrowcolor", "focuscolor", "indicatorcolor", "indicatorbackground",
    "insertcolor", "selectcolor",
}

_NAMED = {
    "white": "#ffffff", "black": "#000000", "red": "#ff0000", "green": "#008000", "blue": "#0000ff",
    "gray": "#808080", "grey": "#808080", "yellow": "#ffff00", "orange": "#ffa500", "purple": "#800080",
    "lightgray": "#d3d3d3", "lightgrey": "#d3d3d3", "darkgray": "#a9a9a9", "darkgrey": "#a9a9a9",
    "gold": "#ffd700", "brown": "#a52a2a", "violet": "#ee82ee", "cyan": "#00ffff", "magenta": "#ff00ff",
    "pink": "#ffc0cb", "navy": "#000080", "silver": "#c0c0c0", "gray50": "#7f7f7f",
}


class keep(str):
    """A colour string that dark mode must leave untouched."""


def is_dark():
    return _DARK


def set_dark(flag):
    global _DARK
    flag = bool(flag)
    if flag == _DARK:
        return
    _DARK = flag
    _save_pref()
    for cb in list(_listeners):
        cb()


def toggle():
    set_dark(not _DARK)


def on_change(cb):
    _listeners.append(cb)


# ---------------------------------------------------------------------------
# colour transform
# ---------------------------------------------------------------------------
def _parse(c):
    c = c.strip()
    if c.startswith("#"):
        h = c[1:]
        if len(h) == 3:
            h = "".join(ch * 2 for ch in h)
        if len(h) == 12:            # #rrrrggggbbbb
            h = h[0:2] + h[4:6] + h[8:10]
        if len(h) != 6:
            return None
        try:
            return tuple(int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
        except ValueError:
            return None
    n = _NAMED.get(c.lower().replace(" ", ""))
    if n:
        return _parse(n)
    try:
        root = tk._default_root
        if root is not None:
            r, g, b = root.winfo_rgb(c)
            return r / 65535, g / 65535, b / 65535
    except Exception:
        pass
    return None


def transform_rgb(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r, g, b)
    if l > 0.88:
        # near-white surfaces (cards, page, canvases): neutral dark grey, a hint of the hue
        return colorsys.hls_to_rgb(h, 0.11 + (1 - l) * 0.9, s * 0.18)
    if s < 0.22 or l > 0.72 or l < 0.26:
        # neutral / pastel / very dark: flip lightness into the dark palette
        nl = 0.11 + (1 - l) * 0.80
        if s < 0.22:
            s *= 0.4
        if l > 0.72 and s >= 0.22:
            # pastel fills -> deep, slightly less saturated tints
            nl = 0.17 + (1 - l) * 0.55
            s = min(s, 0.38)
        elif l < 0.26 and s >= 0.22:
            # dark saturated (navy text, dark red…) -> light tints of the same hue
            nl = 0.80
            s = min(s, 0.6)
        l = nl
    else:
        # saturated accent: keep hue, make sure it stands out on dark grey
        l = max(l, 0.55)
    return colorsys.hls_to_rgb(h, l, s)


_OUTPUTS = set()     # colours produced by the transform (never transform twice)


@functools.lru_cache(maxsize=4096)
def _map_str(c):
    if c.lower() in _OUTPUTS:
        return c
    rgb = _parse(c)
    if rgb is None:
        return c
    r, g, b = transform_rgb(*rgb)
    out = "#%02x%02x%02x" % (round(r * 255), round(g * 255), round(b * 255))
    _OUTPUTS.add(out)
    return out


def color(c):
    """Map one colour string for the current mode."""
    if not _DARK or not isinstance(c, str) or isinstance(c, keep) or not c or c.lower() in ("none", ""):
        return c
    return _map_str(c)


def _map_value(v):
    if isinstance(v, str):
        return color(v)
    return v


# ---------------------------------------------------------------------------
# Tk / ttk hooks
# ---------------------------------------------------------------------------
_orig_options = tk.Misc._options


_EXEMPT = set()


def exempt(widget):
    """Leave this widget and all its children in their own colours (used by
    pages that already have a dark design, e.g. the RF simulator)."""
    _EXEMPT.add(str(widget))


def _is_exempt(w):
    if not _EXEMPT:
        return False
    p = str(w)
    return any(p == e or p.startswith(e + ".") for e in _EXEMPT)


def _options(self, cnf, kw=None):
    if _DARK and not _is_exempt(self):
        if kw:
            cnf = tk._cnfmerge((cnf, kw))
            kw = None
        elif cnf:
            cnf = tk._cnfmerge(cnf)
        if cnf:
            cnf = {k: (_map_value(v) if k.rstrip("_") in COLOR_KEYS else v) for k, v in cnf.items()}
    return _orig_options(self, cnf, kw)


_orig_fmt_optdict = ttk._format_optdict
_orig_fmt_mapdict = ttk._format_mapdict


def _fmt_optdict(optdict, script=False, ignore=None):
    if _DARK and optdict:
        optdict = {k: (_map_value(v) if k.lstrip("-") in COLOR_KEYS else v) for k, v in optdict.items()}
    return _orig_fmt_optdict(optdict, script, ignore)


def _fmt_mapdict(mapdict, script=False):
    if _DARK and mapdict:
        new = {}
        for opt, specs in mapdict.items():
            if opt.lstrip("-") in COLOR_KEYS:
                specs = [tuple(list(sp[:-1]) + [_map_value(sp[-1])]) for sp in specs]
            new[opt] = specs
        mapdict = new
    return _orig_fmt_mapdict(mapdict, script)


# ---------------------------------------------------------------------------
# matplotlib hook
# ---------------------------------------------------------------------------
def _mpl_map_rgba(c):
    import matplotlib.colors as mc
    try:
        r, g, b, a = mc.to_rgba(c)
    except Exception:
        return c
    r, g, b = transform_rgb(r, g, b)
    return (r, g, b, a)


def _remap_figure(fig):
    import numpy as np
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    from matplotlib.text import Text
    from matplotlib.collections import Collection

    def once(artist, key, getter, setter, mapper):
        cur = getter()
        sig = getattr(artist, "_theme_sig", {})
        try:
            cur_key = repr(np.asarray(cur).round(4).tolist()) if not isinstance(cur, str) else cur
        except Exception:
            cur_key = repr(cur)
        if sig.get(key) == cur_key:
            return
        new = mapper(cur)
        setter(new)
        after = getter()
        try:
            sig[key] = repr(np.asarray(after).round(4).tolist()) if not isinstance(after, str) else after
        except Exception:
            sig[key] = repr(after)
        artist._theme_sig = sig

    def map_one(c):
        if isinstance(c, str) and c.lower() == "none":
            return c
        return _mpl_map_rgba(c)

    def map_arr(arr):
        arr = np.asarray(arr, dtype=float)
        if arr.size == 0:
            return arr
        arr = arr.reshape(-1, 4).copy()
        for i in range(len(arr)):
            arr[i, :3] = transform_rgb(*arr[i, :3])
        return arr

    for a in fig.findobj():
        try:
            if isinstance(a, Line2D):
                once(a, "c", a.get_color, a.set_color, map_one)
                once(a, "mfc", a.get_markerfacecolor, a.set_markerfacecolor, map_one)
                once(a, "mec", a.get_markeredgecolor, a.set_markeredgecolor, map_one)
            elif isinstance(a, Text):
                once(a, "c", a.get_color, a.set_color, map_one)
                bp = a.get_bbox_patch()
                if bp is not None:
                    once(bp, "fc", bp.get_facecolor, bp.set_facecolor, map_one)
                    once(bp, "ec", bp.get_edgecolor, bp.set_edgecolor, map_one)
            elif isinstance(a, Patch):
                once(a, "fc", a.get_facecolor, a.set_facecolor, map_one)
                once(a, "ec", a.get_edgecolor, a.set_edgecolor, map_one)
            elif isinstance(a, Collection):
                once(a, "fc", a.get_facecolor, a.set_facecolor, map_arr)
                once(a, "ec", a.get_edgecolor, a.set_edgecolor, map_arr)
        except Exception:
            pass


def _install_mpl():
    try:
        from matplotlib.backends.backend_agg import FigureCanvasAgg
    except Exception:
        return
    if getattr(FigureCanvasAgg, "_theme_patched", False):
        return
    orig = FigureCanvasAgg.draw

    def draw(self, *a, **k):
        tkw = getattr(self, "get_tk_widget", None)
        if _DARK and not (tkw and _is_exempt(tkw())):
            try:
                _remap_figure(self.figure)
            except Exception:
                pass
        return orig(self, *a, **k)
    FigureCanvasAgg.draw = draw
    FigureCanvasAgg._theme_patched = True


def install():
    tk.Misc._options = _options
    ttk._format_optdict = _fmt_optdict
    ttk._format_mapdict = _fmt_mapdict
    _install_mpl()


# ---------------------------------------------------------------------------
# preference file
# ---------------------------------------------------------------------------
def _pref_path():
    import os
    base = os.environ.get("APPDATA") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "ElectronistGuide", "theme.txt")


def load_pref():
    global _DARK
    try:
        with open(_pref_path(), encoding="utf-8") as f:
            _DARK = f.read().strip() == "dark"
    except Exception:
        _DARK = False


def _save_pref():
    import os
    try:
        p = _pref_path()
        os.makedirs(os.path.dirname(p), exist_ok=True)
        with open(p, "w", encoding="utf-8") as f:
            f.write("dark" if _DARK else "light")
    except Exception:
        pass
