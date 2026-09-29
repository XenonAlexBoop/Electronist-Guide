"""
tabs/rf_simulator.py - "Multiport RF Simulator" subtab (RF & Microwave
group). Integrates the RF circuit builder engine (see the `rf` package)
into the application's existing tab / notebook / i18n architecture.

Architecture (matches rf/__init__.py docstring):

    Circuit Builder -> Shared Circuit / Network Model -> RF Network
    Solver -> Frequency Sweep -> Shared S-Parameter Dataset -> Virtual
    VNA / Smith Chart / S-Parameter Results (all reading the same data).

The frequency-sweep controls and the SIMULATE button live once, at the
top of this tab, shared by every inner view below - there is exactly one
circuit, one sweep and one S-parameter dataset for the whole subtab.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from i18n import t
from widgets import FONT_H1, FONT_H2, FONT_BODY, TheoryPanel, ScrollableFrame
from data import get_theory

from rf.simstate import SimulationState
from rf.builder import RFBuilderView
from i18n import register

register({
    "rb.auto": ("Auto-simulate on every change", "Simulare automată la fiecare modificare"),
})
from rf.vna_view import RFVNAView
from rf.smith_view import SmithChartView
from rf.results_view import ResultsView

ACCENT_C = "#2A9D8F"


class RFSimulatorTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.sim_state = SimulationState()
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        title = ttk.Label(self, text=t("rf.tab_title"), font=FONT_H1, style="TabTitle.TLabel")
        title.grid(row=0, column=0, sticky="w", padx=20, pady=(16, 0))

        subtitle = ttk.Label(self, text=t("rf.tab_subtitle"), style="CardBody.TLabel",
                              wraplength=1100, justify="left")
        subtitle.grid(row=1, column=0, sticky="w", padx=20, pady=(2, 6))

        self._build_sweep_bar()
        self._build_inner_notebook()

    # ------------------------------------------------------------------
    def _build_sweep_bar(self):
        bar = ttk.Frame(self, style="Card.TFrame")
        bar.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 10))

        def field(label_key, default):
            f = ttk.Frame(bar, style="Card.TFrame")
            f.pack(side="left", padx=(10, 4), pady=8)
            ttk.Label(f, text=t(label_key), style="CardBody.TLabel").pack(anchor="w")
            var = tk.StringVar(value=str(default))
            e = ttk.Entry(f, textvariable=var, width=10)
            e.pack(anchor="w")
            e.bind("<Return>", lambda _e: self._on_simulate())
            e.bind("<FocusOut>", lambda _e: self._on_circuit_changed())
            return var

        self.f_start_var = field("rf.sweep.start", "1")
        ttk.Label(bar, text=t("rf.axis.ghz"), style="CardBody.TLabel").pack(side="left")
        self.f_stop_var = field("rf.sweep.stop", "3")
        ttk.Label(bar, text=t("rf.axis.ghz"), style="CardBody.TLabel").pack(side="left")
        self.n_points_var = field("rf.sweep.points", "201")

        self.simulate_btn = tk.Button(bar, text=t("rf.sweep.simulate"), font=("Segoe UI", 11, "bold"),
                                       bg="#1f2a44", fg="white", activebackground="#334166",
                                       activeforeground="white", relief="flat", padx=18, pady=8,
                                       command=self._on_simulate)
        self.simulate_btn.pack(side="left", padx=20, pady=8)

        self.auto_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(bar, text=t("rb.auto"), variable=self.auto_var,
                        command=lambda: self._on_circuit_changed()).pack(side="left", padx=(0, 10))
        self.status_lbl = ttk.Label(bar, text=t("rf.sweep.not_simulated"), style="CardBody.TLabel",
                                    wraplength=600, justify="left")
        self.status_lbl.pack(side="left", padx=(10, 10))

    def _build_inner_notebook(self):
        nb = ttk.Notebook(self)
        nb.grid(row=3, column=0, sticky="nsew", padx=20, pady=(0, 16))

        self.builder_view = RFBuilderView(nb, self.sim_state, on_change=self._on_circuit_changed,
                                          on_sweep=self._set_sweep)
        nb.add(self.builder_view, text=t("rf.subtab.circuit_builder"))

        self.vna_view = RFVNAView(nb, self.sim_state)
        nb.add(self.vna_view, text=t("rf.subtab.vna"))

        self.smith_view = SmithChartView(nb, self.sim_state)
        nb.add(self.smith_view, text=t("rf.subtab.smith"))

        self.results_view = ResultsView(nb, self.sim_state)
        nb.add(self.results_view, text=t("rf.subtab.results"))

        from tabs.learn import learn_page
        from widgets import lazy_tab
        lazy_tab(nb, t("common.learn"), lambda p: learn_page(p, ACCENT_C, "rf", extra=lambda b: __import__("tabs.learn_extras", fromlist=["x"]).rf_gallery(b, ACCENT_C).pack(fill="x")))

    # ------------------------------------------------------------------
    def _set_sweep(self, f1_ghz, f2_ghz):
        self.f_start_var.set(f"{f1_ghz:g}")
        self.f_stop_var.set(f"{f2_ghz:g}")

    def _on_circuit_changed(self):
        if getattr(self, "auto_var", None) is not None and self.auto_var.get():
            self._on_simulate(silent=True)
        else:
            self.status_lbl.configure(text=t("rf.sweep.changed"))
            self.builder_view.set_stale(True)

    def _on_simulate(self, silent=False):
        try:
            f_start = float(self.f_start_var.get()) * 1e9
            f_stop = float(self.f_stop_var.get()) * 1e9
            n_points = int(float(self.n_points_var.get()))
        except ValueError:
            if silent:
                self.status_lbl.configure(text=t("rf.error.invalid_sweep"))
            else:
                messagebox.showerror(t("rf.error.title"), t("rf.error.invalid_sweep"))
            return

        self.sim_state.sweep["f_start"] = f_start
        self.sim_state.sweep["f_stop"] = f_stop
        self.sim_state.sweep["n_points"] = n_points

        try:
            self.sim_state.simulate()
        except ValueError as exc:
            if not silent:
                messagebox.showerror(t("rf.error.title"), str(exc))
            self.status_lbl.configure(text="⚠ " + str(exc))
            self.builder_view.set_stale(True)
            return
        except Exception as exc:          # singular matrix etc. - never crash the editor
            self.status_lbl.configure(text="⚠ " + str(exc))
            self.builder_view.set_stale(True)
            return
        self.builder_view.set_stale(False)
        self.status_lbl.configure(text=t("rf.sweep.ok").format(
            n=self.sim_state.result.n_ports(), pts=n_points))
