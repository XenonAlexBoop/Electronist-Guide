"""
tabs/battery_panel.py - Batteries > Pack calculator (v6.3).

S cells in series x P strings in parallel ("3S2P"), with chemistry presets.
Gives nominal / full / empty voltage, capacity, energy, runtime, C-rate,
voltage sag and heat from the internal resistance, draws the pack and plots
the expected discharge curve.
"""
import tkinter as tk
from tkinter import ttk

import numpy as np

from i18n import t, register
from uikit import ParamForm, TileRow, FitCanvas, Segmented, two_columns, section, note, eng
from charts import MplChartFrame
import symbols as sym

register({
    "bp.title": ("Battery pack", "Pachet de baterii"),
    "bp.chem": ("Chemistry:", "Chimie:"),
    "bp.s": ("Cells in series (S)", "Celule în serie (S)"),
    "bp.p": ("Strings in parallel (P)", "Ramuri în paralel (P)"),
    "bp.v": ("Nominal cell voltage", "Tensiunea nominală a celulei"),
    "bp.cap": ("Cell capacity", "Capacitatea celulei"),
    "bp.load": ("Load current", "Curentul de sarcină"),
    "bp.rint": ("Cell internal resistance", "Rezistența internă a celulei"),
    "bp.vnom": ("Pack voltage (nominal)", "Tensiunea pachetului (nominală)"),
    "bp.vrange": ("Full → empty", "Plin → descărcat"),
    "bp.captot": ("Pack capacity", "Capacitatea pachetului"),
    "bp.energy": ("Energy", "Energie"),
    "bp.runtime": ("Runtime (estimate)", "Autonomie (estimare)"),
    "bp.crate": ("C-rate per cell", "Rata C pe celulă"),
    "bp.sag": ("Voltage sag under load", "Căderea de tensiune sub sarcină"),
    "bp.heat": ("Heat in the cells", "Căldură în celule"),
    "bp.cells": ("{n} cells", "{n} celule"),
    "bp.curve": ("Discharge curve at this load (estimate)", "Curba de descărcare la această sarcină (estimare)"),
    "bp.note": ("Series adds voltage, parallel adds capacity; energy (Wh) grows with every cell either way. "
                "Real runtime is shorter at high C-rates, in the cold and as cells age - treat it as an upper "
                "bound. Keep lithium cells above their cut-off voltage.",
                "Serie adună tensiunea, paralel adună capacitatea; energia (Wh) crește cu fiecare celulă în ambele "
                "cazuri. Autonomia reală e mai mică la rate C mari, la frig și pe măsură ce celulele îmbătrânesc - "
                "consider-o o limită superioară. Nu descărca celulele cu litiu sub tensiunea minimă."),
    "bp.custom": ("Custom", "Personalizat"),
    "bp.ocv": ("open circuit", "în gol"),
    "bp.ch.liion": ("Li-ion", "Li-ion"), "bp.ch.lifepo4": ("LiFePO4", "LiFePO4"), "bp.ch.nimh": ("NiMH", "NiMH"),
    "bp.ch.alk": ("Alkaline", "Alcalină"), "bp.ch.pb": ("Lead-acid", "Plumb-acid"),
})

# chemistry: (label, nominal V, SOC->V curve points (soc, V))
CHEM = {
    "liion": ("Li-ion", 3.7, [(0, 3.0), (0.05, 3.3), (0.1, 3.45), (0.2, 3.58), (0.5, 3.72), (0.8, 3.95),
                              (0.95, 4.1), (1, 4.2)], "2500m", "50m"),
    "lifepo4": ("LiFePO4", 3.2, [(0, 2.5), (0.05, 2.9), (0.1, 3.1), (0.2, 3.2), (0.8, 3.3), (0.95, 3.4),
                                 (1, 3.6)], "3000m", "30m"),
    "nimh": ("NiMH", 1.2, [(0, 1.0), (0.05, 1.1), (0.15, 1.18), (0.8, 1.26), (0.95, 1.35), (1, 1.42)],
             "2000m", "30m"),
    "alk": ("Alkaline", 1.5, [(0, 0.9), (0.2, 1.1), (0.5, 1.25), (0.8, 1.4), (1, 1.6)], "2500m", "150m"),
    "pb": ("Lead-acid", 2.0, [(0, 1.75), (0.2, 1.93), (0.5, 2.0), (0.8, 2.07), (1, 2.12)], "7", "5m"),
}


class BatteryPackPanel(ttk.Frame):
    def __init__(self, parent, accent):
        super().__init__(parent, style="Card.TFrame")
        self.accent = accent
        left, right = two_columns(self, left_min=460)
        section(left, t("bp.title"), accent, padx=4, pady=(4, 6))
        row = ttk.Frame(left, style="Card.TFrame")
        row.pack(fill="x", padx=4, pady=(0, 8))
        ttk.Label(row, text=t("bp.chem"), style="CardBody.TLabel").pack(side="left", padx=(0, 6))
        self.chem = tk.StringVar(value="liion")
        Segmented(row, [(k, t("bp.ch." + k)) for k in CHEM], self.chem, command=self._on_chem,
                  accent=accent, wrap=3).pack(side="left")
        self.form = ParamForm(left, [
            {"key": "s", "label": t("bp.s"), "default": "3", "unit": "", "slider": (1, 24, False), "int": True},
            {"key": "p", "label": t("bp.p"), "default": "2", "unit": "", "slider": (1, 10, False), "int": True},
            {"key": "v", "label": t("bp.v"), "default": "3.7", "unit": "V"},
            {"key": "cap", "label": t("bp.cap"), "default": "2500m", "unit": "Ah", "slider": (0.1, 100, True)},
            {"key": "i", "label": t("bp.load"), "default": "1", "unit": "A", "slider": (0.01, 50, True)},
            {"key": "r", "label": t("bp.rint"), "default": "50m", "unit": "Ω"},
        ], self.update_all, label_width=28)
        self.form.pack(fill="x", padx=4)
        self.tiles = TileRow(left, [("vnom", t("bp.vnom")), ("vrange", t("bp.vrange")),
                                    ("cap", t("bp.captot")), ("energy", t("bp.energy")),
                                    ("run", t("bp.runtime")), ("crate", t("bp.crate")),
                                    ("sag", t("bp.sag")), ("heat", t("bp.heat"))], accent, per_row=2)
        self.tiles.pack(fill="x", padx=4, pady=(12, 6))
        note(left, t("bp.note"), wrap=450, padx=4)

        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=3)
        right.rowconfigure(2, weight=2)
        self.cv = FitCanvas(right, 560, 300, kmin=0.5, kmax=1.5)
        self.cv.grid(row=0, column=0, sticky="nsew")
        ttk.Label(right, text=t("bp.curve"), font=("Segoe UI", 10, "bold"), foreground=accent,
                  style="CardSub.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 2))
        self.chart = MplChartFrame(right, figsize=(6.0, 2.4), with_toolbar=False)
        self.chart.grid(row=2, column=0, sticky="nsew")
        self.chart.canvas.get_tk_widget().configure(height=200)
        self.after(30, self.update_all)

    def _on_chem(self, key):
        _, vnom, _, cap, r = CHEM[key]
        self.form.set("v", vnom)
        self.form.set("cap", cap)
        self.form.set("r", r)
        self.update_all()

    def update_all(self):
        try:
            v = self.form.values()
        except Exception:
            return
        S, P = max(1, int(round(v["s"]))), max(1, int(round(v["p"])))
        vc, cap, i, rc = v["v"], max(v["cap"], 1e-9), max(v["i"], 0.0), max(v["r"], 0.0)
        curve = CHEM[self.chem.get()][2]
        k = vc / CHEM[self.chem.get()][1]          # scale the curve if the user typed another nominal V
        vfull, vempty = curve[-1][1] * k * S, curve[0][1] * k * S
        vnom = vc * S
        captot = cap * P
        energy = vnom * captot
        run_h = captot / i if i > 0 else float("inf")
        crate = (i / P) / cap
        rpack = rc * S / P
        sag = i * rpack
        heat = i * i * rpack
        T = self.tiles
        T.set("vnom", f"{vnom:.3g} V  ({S}S{P}P)")
        T.set("vrange", f"{vfull:.3g} → {vempty:.3g} V")
        T.set("cap", eng(captot, "Ah"))
        T.set("energy", eng(energy, "Wh"))
        if run_h == float("inf"):
            T.set("run", "∞")
        elif run_h >= 1:
            T.set("run", f"{run_h:.2f} h")
        else:
            T.set("run", f"{run_h * 60:.1f} min")
        T.set("crate", f"{crate:.2f} C", warn=crate > 2)
        T.set("sag", eng(sag, "V"), warn=sag > 0.1 * vnom)
        T.set("heat", eng(heat, "W"))
        self.cv.show(lambda: self._draw(S, P, vc, vnom))
        self._plot(curve, k, S, rpack, i, run_h)

    def _draw(self, S, P, vc, vnom):
        c = self.cv
        W, H = 560, 300
        s_show, p_show = min(S, 8), min(P, 5)
        x0, x1 = 80, W - 80
        y0, y1 = 40, H - 60
        span = (x1 - x0) / s_show
        rowh = (y1 - y0) / max(1, p_show - 1) if p_show > 1 else 0
        sc = max(0.55, min(1.5, span / 60, (rowh / 50) if p_show > 1 else 1.5))
        ys = [y0 + j * rowh for j in range(p_show)] if p_show > 1 else [(y0 + y1) / 2]
        for j, y in enumerate(ys):
            for i in range(s_show):
                sym.cell(c, x0 + i * span, y, x0 + (i + 1) * span, y,
                         label=(f"{vc:g} V" if (j == 0 and i == 0) else None), s=sc)
            if S > s_show:
                c.create_text((x0 + x1) / 2, y + 22 * sc, text=f"… {S} ×", font=("Segoe UI", 8), fill="#666")
        if p_show > 1:
            sym.wire(c, x0, ys[0], x0, ys[-1])
            sym.wire(c, x1, ys[0], x1, ys[-1])
            for y in ys:
                sym.node(c, x0, y)
                sym.node(c, x1, y)
        ymid = (ys[0] + ys[-1]) / 2
        sym.wire(c, x0, ymid, x0 - 40, ymid)
        sym.wire(c, x1, ymid, x1 + 40, ymid)
        sym.terminal(c, x0 - 40, ymid)
        sym.terminal(c, x1 + 40, ymid)
        c.create_text(x0 - 48, ymid, text="+", anchor="e", font=("Segoe UI", 14, "bold"), fill="#c62828")
        c.create_text(x1 + 48, ymid, text="−", anchor="w", font=("Segoe UI", 14, "bold"), fill="#1f2a44")
        if P > p_show:
            c.create_text((x0 + x1) / 2, y1 + 18, text=f"… {P} ∥", font=("Segoe UI", 8), fill="#666")
        c.create_text(W / 2, H - 20, text=f"{S}S{P}P  ·  {t('bp.cells').format(n=S * P)}  ·  {vnom:.3g} V",
                      font=("Segoe UI", 11, "bold"), fill=self.accent)

    def _plot(self, curve, k, S, rpack, i, run_h):
        fig = self.chart.fig
        fig.clear()
        ax = fig.add_subplot(111)
        soc = np.array([p[0] for p in curve])
        vv = np.array([p[1] for p in curve]) * k * S
        x = np.linspace(0, 1, 200)
        v_ocv = np.interp(1 - x, soc, vv)
        v_load = v_ocv - i * rpack
        if np.isfinite(run_h) and run_h > 0:
            tt = x * run_h
            xlabel = "t (h)" if run_h >= 1 else "t (min)"
            if run_h < 1:
                tt = tt * 60
        else:
            tt, xlabel = x * 100, "%"
        ax.plot(tt, v_ocv, color="#999", lw=1, ls="--", label=t("bp.ocv"))
        ax.plot(tt, v_load, color=self.accent, lw=2, label=f"@ {eng(i, 'A')}")
        ax.set_xlabel(xlabel, fontsize=9)
        ax.set_ylabel("V", fontsize=9)
        ax.tick_params(labelsize=8)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8)
        try:
            fig.tight_layout(pad=0.6)
        except Exception:
            pass
        self.chart.redraw()
