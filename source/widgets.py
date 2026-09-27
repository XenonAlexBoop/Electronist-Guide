"""
widgets.py - Small reusable UI building blocks shared by every tab:
 - a collapsible-feeling "Theory" panel (what it is / how it works / formulas)
 - value formatting helpers (engineering notation with unit prefixes)
"""
import tkinter as tk
from tkinter import ttk
from data import SI_PREFIXES
from i18n import t

FONT_H1 = ("Segoe UI", 18, "bold")
FONT_H2 = ("Segoe UI", 12, "bold")
FONT_BODY = ("Segoe UI", 10)
FONT_MONO = ("Consolas", 12, "bold")


class ScrollableFrame(ttk.Frame):
    """A vertically-scrollable container. Put content inside `.body`
    (a plain ttk.Frame) instead of the ScrollableFrame itself.

    The scrollbar only appears once the content is actually taller than
    the visible area - it's a safety net for small windows/short content
    lists, not a default fixture, so it stays out of the way when a tab's
    content already fits. Mouse-wheel scrolling works while the pointer
    is over the content.
    """

    def __init__(self, parent, style="Tab.TFrame", **kw):
        super().__init__(parent, style=style, **kw)
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        bg = ttk.Style(self).lookup(style, "background") or None
        # width/height=1 here is deliberate and load-bearing: without an
        # explicit starting size, a Tk Canvas's own *requested* size is
        # derived from its content's bounding box, which includes this
        # scrollable body. That creates a feedback loop wherever content
        # inside reacts to available width (e.g. label wraplength): a
        # narrower wrap -> narrower content request -> canvas requests
        # less width -> even narrower wrap next pass, spiraling the whole
        # panel down to a sliver. Pinning an explicit (tiny) starting size
        # makes the geometry manager (grid, with sticky+weight below) the
        # sole authority over this canvas's size instead.
        self._canvas = tk.Canvas(self, highlightthickness=0, bd=0, bg=bg)
        self._vsb = ttk.Scrollbar(self, orient="vertical", command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=self._vsb.set)
        self._canvas.grid(row=0, column=0, sticky="nsew")

        self.body = ttk.Frame(self._canvas, style=style)
        self._window = self._canvas.create_window((0, 0), window=self.body, anchor="nw")

        self.body.bind("<Configure>", self._on_body_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind("<Enter>", self._bind_mousewheel)
        self._canvas.bind("<Leave>", self._unbind_mousewheel)
        self._vsb_visible = False

    def _on_body_configure(self, _event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        self._update_scrollbar_visibility()

    def _on_canvas_configure(self, event):
        # The body must never be wider than the visible viewport - if it
        # is, the excess simply sits outside the canvas with no way to
        # reach it (there's only a vertical scrollbar). Match the
        # viewport width exactly; any flexible content inside (charts,
        # wrapped labels) will shrink to fit, same as it did before this
        # frame existed.
        self._canvas.itemconfigure(self._window, width=event.width)
        self._update_scrollbar_visibility()

    def _update_scrollbar_visibility(self):
        bbox = self._canvas.bbox("all")
        if not bbox:
            return
        content_h = bbox[3] - bbox[1]
        visible_h = self._canvas.winfo_height()
        needed = content_h > visible_h
        if needed and not self._vsb_visible:
            self._vsb.grid(row=0, column=1, sticky="ns")
            self._vsb_visible = True
        elif not needed and self._vsb_visible:
            self._vsb.grid_forget()
            self._vsb_visible = False

    def _bind_mousewheel(self, _event):
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self._canvas.bind_all("<Button-4>", self._on_mousewheel)
        self._canvas.bind_all("<Button-5>", self._on_mousewheel)

    def _unbind_mousewheel(self, _event):
        self._canvas.unbind_all("<MouseWheel>")
        self._canvas.unbind_all("<Button-4>")
        self._canvas.unbind_all("<Button-5>")

    def _on_mousewheel(self, event):
        if not self._vsb_visible:
            return
        if event.num == 4:
            delta = -1
        elif event.num == 5:
            delta = 1
        else:
            delta = -1 if event.delta > 0 else 1
        self._canvas.yview_scroll(delta, "units")

ACCENT = {
    "resistor": "#c9622a",
    "capacitor": "#2E5EAA",
    "inductor": "#B8860B",
    "diode": "#c62828",
    "transistor": "#5b3fa0",
    "opamp": "#1f6a5f",
    "battery": "#8a6d00",
    "basics": "#334155",
    "digital": "#0d7d5f",
}


def format_value(value, unit):
    """Format a raw numeric value into engineering notation, e.g. 4700 -> '4.7 kΩ'."""
    if value is None:
        return "-"
    prefixes = [("G", 1e9), ("M", 1e6), ("k", 1e3), ("", 1),
                ("m", 1e-3), ("µ", 1e-6), ("n", 1e-9), ("p", 1e-12)]
    av = abs(value)
    if av == 0:
        return f"0 {unit}"
    for sym, factor in prefixes:
        if av >= factor:
            scaled = value / factor
            return f"{scaled:g} {sym}{unit}"
    scaled = value / prefixes[-1][1]
    return f"{scaled:g} {prefixes[-1][0]}{unit}"


def parse_value(text, default_unit=""):
    """Parse a string like '4.7k', '10 uF', '220n' into a float in base units."""
    text = text.strip().replace(" ", "")
    if not text:
        raise ValueError("empty value")
    i = len(text)
    while i > 0 and not (text[i - 1].isdigit() or text[i - 1] == "."):
        i -= 1
    number_part = text[:i]
    suffix = text[i:]
    value = float(number_part)
    # strip a trailing unit letter (e.g. 'F', 'H', 'ohm') leaving just the prefix
    prefix = ""
    if suffix:
        if suffix[0] in SI_PREFIXES:
            prefix = suffix[0]
        elif suffix[0].lower() == "r":  # e.g. "4k7" style handled elsewhere
            prefix = ""
    factor = SI_PREFIXES.get(prefix, 1)
    return value * factor


def parse_value_list(text, default_unit=""):
    """Parse a comma/space separated list of values like '100, 4.7k, 2.2k' into floats."""
    if not text or not text.strip():
        raise ValueError("empty list")
    tokens = [tok for tok in text.replace(",", " ").split() if tok]
    return [parse_value(tok, default_unit) for tok in tokens]


def series_sum(values):
    return sum(values)


def parallel_combo(values):
    if any(v == 0 for v in values):
        raise ValueError("value of 0 is not valid in a parallel combination")
    return 1 / sum(1 / v for v in values)


def combine_pair(a, b, physical_mode, kind):
    """Combine two values that are physically in series or parallel, respecting
    each component type's formula convention (capacitors invert series/parallel)."""
    if kind == "capacitor":
        if physical_mode == "series":
            return parallel_combo([a, b])
        return series_sum([a, b])
    if physical_mode == "series":
        return series_sum([a, b])
    return parallel_combo([a, b])


class TheoryPanel(ttk.Frame):
    """A styled panel showing 'What is it', 'How it works', and key formulas.

    All text (the what/how paragraphs and every formula line) wraps
    responsively to the panel's actual rendered width, recomputed on
    every resize - rather than a fixed guess in pixels. A fixed guess
    either clips long text at whatever width the window happens to be
    (formulas cut off mid-line) or leaves a large dead gap of unused
    space (short/narrow windows), and this app's formula set has grown
    too long and varied for any single fixed number to work everywhere.
    """

    def __init__(self, parent, theory: dict, accent="#334155"):
        super().__init__(parent, style="Card.TFrame")
        self.columnconfigure(0, weight=1)
        self._wrap_labels = []  # (label, extra_indent_px) pairs kept in sync on resize
        self._last_wrap_w = 0

        header = tk.Frame(self, bg=accent, height=6)
        header.grid(row=0, column=0, sticky="ew")

        title = ttk.Label(self, text=f"📘  {theory['title']} — {t('common.learn')}", font=FONT_H1,
                           style="CardTitle.TLabel", wraplength=560, justify="left")
        title.grid(row=1, column=0, sticky="w", padx=16, pady=(12, 6))
        self._wrap_labels.append((title, 40))

        what = ttk.Label(self, text=t("common.what"), font=FONT_H2, style="CardSub.TLabel")
        what.grid(row=2, column=0, sticky="w", padx=16, pady=(6, 0))
        what_txt = ttk.Label(self, text=theory["what"], font=FONT_BODY, wraplength=560,
                              justify="left", style="CardBody.TLabel")
        what_txt.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 8))
        self._wrap_labels.append((what_txt, 32))

        how = ttk.Label(self, text=t("common.how"), font=FONT_H2, style="CardSub.TLabel")
        how.grid(row=4, column=0, sticky="w", padx=16, pady=(6, 0))
        how_txt = ttk.Label(self, text=theory["how"], font=FONT_BODY, wraplength=560,
                             justify="left", style="CardBody.TLabel")
        how_txt.grid(row=5, column=0, sticky="w", padx=16, pady=(0, 8))
        self._wrap_labels.append((how_txt, 32))

        row = 6
        if "dc_formulas" in theory and "ac_formulas" in theory:
            row = self._formula_section(row, t("common.dc_formulas"), theory["dc_formulas"], accent)
            row = self._formula_section(row, t("common.ac_formulas"), theory["ac_formulas"], accent)
        else:
            row = self._formula_section(row, t("common.key_formulas"), theory["formulas"], accent)

        self.bind("<Configure>", self._on_resize)

    def _formula_section(self, row, heading, formulas, accent):
        ttk.Label(self, text=heading, font=FONT_H2, style="CardSub.TLabel")\
            .grid(row=row, column=0, sticky="w", padx=16, pady=(6, 4))
        row += 1
        formula_frame = ttk.Frame(self, style="Card.TFrame")
        formula_frame.grid(row=row, column=0, sticky="ew", padx=16, pady=(0, 10))
        formula_frame.columnconfigure(0, weight=1)
        # Name on its own line, formula indented underneath and wrapped to
        # the panel's own width - a fixed two-column side-by-side layout
        # can't wrap the formula without knowing how wide the name column
        # ended up, so this sidesteps that instead of guessing.
        for i, (name, formula) in enumerate(formulas):
            ttk.Label(formula_frame, text=f"• {name}:", font=FONT_BODY,
                      style="CardBody.TLabel").grid(row=i * 2, column=0, sticky="w", pady=(3, 0))
            f_lbl = ttk.Label(formula_frame, text=formula, font=FONT_MONO, foreground=accent,
                               style="CardFormula.TLabel", justify="left")
            f_lbl.grid(row=i * 2 + 1, column=0, sticky="w", padx=(18, 0), pady=(0, 3))
            self._wrap_labels.append((f_lbl, 50))
        return row + 1

    # Reserve room for the vertical scrollbar that appears once this panel's
    # content (now much longer, with many more formulas) grows taller than
    # the visible area. The scrollbar claims real pixels from the same
    # width this panel is told it has, and it can appear/disappear after
    # the fact as content changes - so we always budget for it rather than
    # risk a wrap computed just before it shows up and steals ~18px back.
    _SCROLLBAR_RESERVE = 24

    def _on_resize(self, event):
        # Only the width matters for wrapping, and only meaningfully-sized
        # changes are worth a re-layout pass (avoids redundant work while a
        # window is mid-drag).
        if abs(event.width - self._last_wrap_w) < 8:
            return
        self._last_wrap_w = event.width
        for label, indent in self._wrap_labels:
            new_wrap = max(160, event.width - indent - self._SCROLLBAR_RESERVE)
            label.configure(wraplength=new_wrap)


def section_label(parent, text, accent):
    lbl = ttk.Label(parent, text=text, font=FONT_H2, foreground=accent, style="CardSub.TLabel")
    return lbl


def labeled_row(parent, label_text, widget_factory, row, col=0, **grid_kwargs):
    """Places a label and a widget (created by widget_factory(parent)) side by side."""
    ttk.Label(parent, text=label_text, font=FONT_BODY).grid(row=row, column=col, sticky="w",
                                                              padx=(0, 8), pady=4)
    w = widget_factory(parent)
    w.grid(row=row, column=col + 1, sticky="ew", pady=4, **grid_kwargs)
    return w
