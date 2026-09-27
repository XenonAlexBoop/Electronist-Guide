"""
rf/results_view.py - S-Parameter Results: the full N x N S-matrix at a
user-selected frequency point, read directly from the shared simulation
dataset (no recomputation).
"""
import numpy as np
import tkinter as tk
from tkinter import ttk

from i18n import t
from widgets import FONT_H2, FONT_BODY, FONT_MONO


class ResultsView(ttk.Frame):
    def __init__(self, parent, sim_state):
        super().__init__(parent, style="Tab.TFrame")
        self.sim_state = sim_state
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        intro = ttk.Label(self, text=t("rf.results.intro"), style="CardBody.TLabel",
                           wraplength=1100, justify="left")
        intro.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))

        top = ttk.Frame(self, style="Tab.TFrame")
        top.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))
        ttk.Label(top, text=t("rf.results.frequency"), style="TabTitle.TLabel").pack(side="left")
        self.freq_scale = ttk.Scale(top, from_=0, to=1, orient="horizontal",
                                     command=self._on_scale)
        self.freq_scale.pack(side="left", fill="x", expand=True, padx=10)
        self.freq_label = ttk.Label(top, text="-", style="TabTitle.TLabel", font=FONT_MONO)
        self.freq_label.pack(side="left", padx=(10, 0))

        self.summary = ttk.Label(self, text="", style="CardBody.TLabel")
        self.summary.grid(row=2, column=0, sticky="w", padx=16)

        table_wrap = ttk.Frame(self, style="Card.TFrame")
        table_wrap.grid(row=3, column=0, sticky="nsew", padx=16, pady=12)
        table_wrap.columnconfigure(0, weight=1)
        table_wrap.rowconfigure(0, weight=1)

        columns = ("param", "mag", "db", "phase")
        self.tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=18)
        for c, key, w in (("param", "rf.results.col_param", 100),
                          ("mag", "rf.results.col_mag", 130),
                          ("db", "rf.results.col_db", 130),
                          ("phase", "rf.results.col_phase", 130)):
            self.tree.heading(c, text=t(key))
            self.tree.column(c, width=w, minwidth=70, anchor="center", stretch=True)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb = ttk.Scrollbar(table_wrap, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")

        sim_state.on_result(lambda _r: self.refresh())
        self.refresh()

    def _on_scale(self, _val):
        self._rebuild_table()

    def refresh(self):
        result = self.sim_state.result
        if result is None:
            self.freq_scale.configure(from_=0, to=1)
            self.freq_scale.set(0)
            self.freq_label.configure(text="-")
            self.summary.configure(text=t("rf.results.no_data"))
            self.tree.delete(*self.tree.get_children())
            return
        n = len(result.freqs_hz)
        self.freq_scale.configure(from_=0, to=n - 1)
        self.freq_scale.set(0)
        self.summary.configure(text=t("rf.results.n_ports_note").format(n=result.n_ports()))
        self._rebuild_table()

    def _rebuild_table(self):
        result = self.sim_state.result
        self.tree.delete(*self.tree.get_children())
        if result is None:
            return
        idx = int(round(self.freq_scale.get()))
        idx = max(0, min(idx, len(result.freqs_hz) - 1))
        f_hz = result.freqs_hz[idx]
        self.freq_label.configure(text=f"{f_hz/1e9:.4f} GHz")

        for out_p in result.port_numbers:
            for in_p in result.port_numbers:
                s = result.s_at(out_p, in_p, idx)
                mag = abs(s)
                db = 20 * np.log10(max(mag, 1e-15))
                phase = np.angle(s, deg=True)
                self.tree.insert("", "end", values=(
                    f"S{out_p}{in_p}", f"{mag:.4f}", f"{db:.2f}", f"{phase:.2f}"))
