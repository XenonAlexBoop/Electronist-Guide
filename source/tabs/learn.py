"""
learn.py - the "Learn" sub-tab used by every component page (v6.2).

The reference material (schematic symbols + theory/formulas) used to sit in a
permanent right-hand column that ate ~45 % of the screen.  It now lives in
its own sub-tab so the calculators and simulators get the full width.

    learn_page(parent, accent, theory="resistor", symbols="resistor")
    learn_page(parent, accent, theory=["basics", "kirchhoff"])   # side by side
"""
from tkinter import ttk

from data import get_theory
from widgets import TheoryPanel, ScrollableFrame
from symbols import SymbolGallery


def learn_page(parent, accent, theory, symbols=None, extra=None):
    """Build the Learn page.  `theory` is a key or a list of keys, `symbols`
    an optional SymbolGallery family, `extra(parent)` an optional builder for
    additional reference material shown in the right column."""
    keys = [theory] if isinstance(theory, str) else list(theory)
    f = ttk.Frame(parent, style="Tab.TFrame")
    f.rowconfigure(0, weight=1)

    col = 0
    for i, key in enumerate(keys):
        sf = ScrollableFrame(f, style="Card.TFrame")
        sf.grid(row=0, column=col, sticky="nsew", padx=(0 if col == 0 else 5, 5))
        f.columnconfigure(col, weight=3, uniform="learn")
        TheoryPanel(sf.body, get_theory(key), accent=accent).pack(fill="both", expand=True)
        col += 1

    if symbols or extra:
        sf = ScrollableFrame(f, style="Card.TFrame")
        sf.grid(row=0, column=col, sticky="nsew", padx=(5, 0))
        f.columnconfigure(col, weight=2, uniform="learn")
        if symbols:
            SymbolGallery(sf.body, symbols, accent=accent).pack(fill="x", pady=(0, 8))
        if extra:
            extra(sf.body)
    elif len(keys) == 1:
        # a lone theory panel stretched over 1900 px makes for very long lines;
        # keep it at a comfortable reading width
        ttk.Frame(f, style="Tab.TFrame").grid(row=0, column=1, sticky="nsew")
        f.columnconfigure(1, weight=1, uniform="learn")
    return f
