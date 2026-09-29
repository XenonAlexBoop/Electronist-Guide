"""
tabs/opamp.py - Op-amp page: the circuit lab (v6) plus the Learn material.
"""
from tkinter import ttk
from data import get_theory
from widgets import TheoryPanel, ScrollableFrame, lazy_tab, FONT_H1, ACCENT
from i18n import t
from symbols import SymbolGallery
from .opamp_lab import OpAmpLabPanel

ACCENT_C = ACCENT["opamp"]


class OpAmpTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text=t("opamp.tab_title"), font=FONT_H1, style="TabTitle.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))
        holder = ttk.Frame(self, style="Tab.TFrame")
        holder.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        holder.columnconfigure(0, weight=1)
        holder.rowconfigure(0, weight=1)
        nb = ttk.Notebook(holder)
        nb.grid(row=0, column=0, sticky="nsew")
        lab = OpAmpLabPanel(nb, ACCENT_C)
        nb.add(lab, text=t("oa.lab"))
        lazy_tab(nb, t("common.learn"), self._learn)

    @staticmethod
    def _learn(parent):
        from .learn import learn_page
        return learn_page(parent, ACCENT_C, "opamp", "opamp")
