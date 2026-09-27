"""
tabs/unit_converter.py - Standalone top-level tab for converting values.
An inner notebook holds two sub-tabs:
  - Prefix Converter: SI magnitude prefixes (pico ... tera), unit-agnostic
  - dB / Ratios: power/voltage ratio <-> dB, and dBm/dBW absolute levels
"""
import math
import tkinter as tk
from tkinter import ttk

from data import UNIT_PREFIXES, FULL_SI_PREFIXES
from widgets import format_value, ScrollableFrame, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO
from tabs.db_calculator import DbCalculatorPanel
from tabs.base_converter import NumberSystemsTab
from i18n import t

ACCENT_C = "#2E5EAA"

_NAME_KEYS = {
    "p": "uc.prefix.pico", "n": "uc.prefix.nano", "µ": "uc.prefix.micro",
    "m": "uc.prefix.milli", "": "uc.prefix.base", "k": "uc.prefix.kilo",
    "M": "uc.prefix.mega", "G": "uc.prefix.giga", "T": "uc.prefix.tera",
    "q": "uc.prefix.quecto", "r": "uc.prefix.ronto", "y": "uc.prefix.yocto",
    "z": "uc.prefix.zepto", "a": "uc.prefix.atto", "f": "uc.prefix.femto",
    "P": "uc.prefix.peta", "E": "uc.prefix.exa", "Z": "uc.prefix.zetta",
    "Y": "uc.prefix.yotta", "R": "uc.prefix.ronna", "Q": "uc.prefix.quetta",
}


class UnitConverterTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=t("uc.tab_title"), font=FONT_H1, style="TabTitle.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))

        prefix_page = PrefixConverterPanel(nb)
        db_page = DbCalculatorPanel(nb)
        base_page = NumberSystemsTab(nb)
        nb.add(prefix_page, text=t("uc.subtab.prefix"))
        nb.add(db_page, text=t("uc.subtab.db"))
        nb.add(base_page, text=t("uc.subtab.base"))


class PrefixConverterPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left_wrap = ttk.Frame(self, style="Card.TFrame")
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        left_wrap.columnconfigure(0, weight=1)
        left_wrap.rowconfigure(0, weight=1)
        right_wrap = ttk.Frame(self, style="Card.TFrame")
        right_wrap.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        right_wrap.columnconfigure(0, weight=1)
        right_wrap.rowconfigure(0, weight=1)

        left_scroll = ScrollableFrame(left_wrap, style="Card.TFrame")
        left_scroll.grid(row=0, column=0, sticky="nsew")
        self._build_calculator(left_scroll.body)

        right_scroll = ScrollableFrame(right_wrap, style="Card.TFrame")
        right_scroll.grid(row=0, column=0, sticky="nsew")
        self._build_reference(right_scroll.body)

    # ------------------------------------------------------------------
    def _active_prefixes(self):
        return FULL_SI_PREFIXES if getattr(self, "full_si_var", None) and self.full_si_var.get() else UNIT_PREFIXES

    def _prefix_labels(self):
        return [f"{t(_NAME_KEYS[sym])} ({sym or '-'})" for sym, _name, _factor in self._active_prefixes()]

    def _build_calculator(self, parent):
        pad = {"padx": 16, "pady": 6}
        parent.columnconfigure(0, weight=1)

        header = tk.Frame(parent, bg=ACCENT_C, height=6)
        header.grid(row=0, column=0, sticky="ew")

        ttk.Label(parent, text=t("uc.intro"), font=FONT_BODY, wraplength=420,
                  justify="left", style="CardBody.TLabel").grid(row=1, column=0, sticky="w", **pad)

        self.full_si_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(parent, text=t("uc.full_si_toggle"), variable=self.full_si_var,
                         command=self._on_full_si_toggle).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 6))

        labels = self._prefix_labels()

        ttk.Label(parent, text=t("uc.value_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=3, column=0, sticky="w", padx=16)
        self.value_var = tk.StringVar(value="1")
        entry = ttk.Entry(parent, textvariable=self.value_var, width=16)
        entry.grid(row=4, column=0, sticky="w", padx=16, pady=(0, 8))
        entry.bind("<KeyRelease>", lambda e: self._convert())

        ttk.Label(parent, text=t("uc.from_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=5, column=0, sticky="w", padx=16)
        self.from_var = tk.StringVar(value=labels[4])  # base unit
        self.from_cb = ttk.Combobox(parent, textvariable=self.from_var, values=labels,
                                     state="readonly", width=22)
        self.from_cb.grid(row=6, column=0, sticky="w", padx=16, pady=(0, 8))
        self.from_cb.bind("<<ComboboxSelected>>", lambda e: self._convert())

        ttk.Button(parent, text=t("uc.swap"), command=self._swap)\
            .grid(row=7, column=0, sticky="w", padx=16, pady=(0, 8))

        ttk.Label(parent, text=t("uc.to_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=8, column=0, sticky="w", padx=16)
        self.to_var = tk.StringVar(value=labels[6])  # mega, an arbitrary useful default
        self.to_cb = ttk.Combobox(parent, textvariable=self.to_var, values=labels,
                                   state="readonly", width=22)
        self.to_cb.grid(row=9, column=0, sticky="w", padx=16, pady=(0, 8))
        self.to_cb.bind("<<ComboboxSelected>>", lambda e: self._convert())

        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=10, column=0, sticky="ew", padx=16, pady=8)

        ttk.Label(parent, text=t("uc.result_label"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=11, column=0, sticky="w", padx=16)
        self.result_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.result_var, font=("Consolas", 16, "bold"),
                  foreground=ACCENT_C, style="CardFormula.TLabel")\
            .grid(row=12, column=0, sticky="w", padx=16, pady=(2, 10))

        ttk.Label(parent, text=t("uc.best_fit_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=13, column=0, sticky="w", padx=16)
        self.best_fit_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.best_fit_var, font=FONT_MONO, foreground="#555",
                  style="CardFormula.TLabel").grid(row=14, column=0, sticky="w", padx=16, pady=(2, 16))

        self._convert()

    def _on_full_si_toggle(self):
        labels = self._prefix_labels()
        self.from_cb.configure(values=labels)
        self.to_cb.configure(values=labels)
        base_label = next((l for l in labels if l.endswith("(-)")), labels[0])
        if self.from_var.get() not in labels:
            self.from_var.set(base_label)
        if self.to_var.get() not in labels:
            self.to_var.set(base_label)
        self._convert()
        self._refresh_reference()

    def _swap(self):
        f, t_ = self.from_var.get(), self.to_var.get()
        self.from_var.set(t_)
        self.to_var.set(f)
        self._convert()

    def _factor_for_label(self, label):
        labels = self._prefix_labels()
        idx = labels.index(label)
        prefixes = self._active_prefixes()
        return prefixes[idx][0], prefixes[idx][2]

    def _convert(self):
        try:
            value = float(self.value_var.get())
        except ValueError:
            self.result_var.set(t("uc.invalid_value"))
            self.best_fit_var.set("")
            return
        _from_sym, from_factor = self._factor_for_label(self.from_var.get())
        to_sym, to_factor = self._factor_for_label(self.to_var.get())
        base_value = value * from_factor
        converted = base_value / to_factor
        self.result_var.set(f"{converted:g} {to_sym}")
        self.best_fit_var.set(format_value(base_value, ""))

    # ------------------------------------------------------------------
    def _build_reference(self, parent):
        parent.columnconfigure(0, weight=1)
        header = tk.Frame(parent, bg=ACCENT_C, height=6)
        header.grid(row=0, column=0, sticky="ew")

        ttk.Label(parent, text=f"📘 {t('uc.quick_ref_title')}", font=FONT_H1,
                  style="CardTitle.TLabel").grid(row=1, column=0, sticky="w", padx=16, pady=(12, 10))

        columns = ("prefix", "symbol", "factor", "example")
        self._ref_tree_parent = parent
        self.ref_tree = ttk.Treeview(parent, columns=columns, show="headings",
                                      height=len(FULL_SI_PREFIXES))
        self.ref_tree.heading("prefix", text=t("uc.table.prefix"))
        self.ref_tree.heading("symbol", text=t("uc.table.symbol"))
        self.ref_tree.heading("factor", text=t("uc.table.factor"))
        self.ref_tree.heading("example", text=t("uc.table.example"))
        self.ref_tree.column("prefix", width=90)
        self.ref_tree.column("symbol", width=70, anchor="center")
        self.ref_tree.column("factor", width=110, anchor="center")
        self.ref_tree.column("example", width=140, anchor="center")
        self.ref_tree.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))

        self._refresh_reference()

    def _refresh_reference(self):
        self.ref_tree.delete(*self.ref_tree.get_children())
        for sym, name_key, factor in self._active_prefixes():
            name = t(_NAME_KEYS[sym])
            factor_txt = f"10^{round(math.log10(factor))}" if factor != 1 else "1"
            example = f"{factor:g} × base" if factor != 1 else "1 × base"
            self.ref_tree.insert("", "end", values=(name, sym or "-", factor_txt, example))
