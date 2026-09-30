"""
tabs/transformer_panel.py - Inductors > Transformer sub-tab (v6.3).

Ideal transformer with a load: turns ratio, secondary voltage and current,
primary current, power and the impedance the source "sees".  Left: inputs
with sliders + result tiles.  Right: the transformer drawn with its values
(coil sizes follow the turns ratio) and the primary / secondary waveforms.
"""
import math
import tkinter as tk
from tkinter import ttk

import numpy as np

from i18n import t, register
from uikit import ParamForm, TileRow, FitCanvas, two_columns, section, note, eng
from charts import MplChartFrame
import symbols as sym

register({
    "tx.title": ("Ideal transformer", "Transformator ideal"),
    "tx.np": ("Primary turns Np", "Spire primar Np"),
    "tx.ns": ("Secondary turns Ns", "Spire secundar Ns"),
    "tx.vp": ("Primary voltage Vp (RMS)", "Tensiune primar Vp (RMS)"),
    "tx.f": ("Frequency", "Frecvență"),
    "tx.rl": ("Load resistance RL (0 = no load)", "Rezistența de sarcină RL (0 = fără sarcină)"),
    "tx.ratio": ("Turns ratio Np : Ns", "Raport de spire Np : Ns"),
    "tx.vs": ("Secondary voltage Vs", "Tensiune secundar Vs"),
    "tx.is": ("Secondary current Is", "Curent secundar Is"),
    "tx.ip": ("Primary current Ip", "Curent primar Ip"),
    "tx.p": ("Power (in = out)", "Putere (intrare = ieșire)"),
    "tx.zin": ("Load seen from primary", "Sarcina văzută din primar"),
    "tx.kind": ("Type", "Tip"),
    "tx.up": ("step-up", "ridicător"),
    "tx.down": ("step-down", "coborâtor"),
    "tx.iso": ("1 : 1 isolation", "izolare 1 : 1"),
    "tx.rules": ("Vs / Vp = Ns / Np\nIs / Ip = Np / Ns\nZin = (Np / Ns)² · RL",
                 "Vs / Vp = Ns / Np\nIs / Ip = Np / Ns\nZin = (Np / Ns)² · RL"),
    "tx.explain": ("Voltage scales with the turns ratio and current with its inverse, so power is the same on "
                   "both sides (ideal part). That is why a step-down transformer delivers MORE current than it "
                   "draws, and why a load looks (Np/Ns)² times bigger from the primary - the basis of "
                   "impedance matching (audio output transformers, RF baluns).",
                   "Tensiunea se scalează cu raportul de spire, iar curentul cu inversul lui, deci puterea este "
                   "aceeași pe ambele părți (piesă ideală). De aceea un transformator coborâtor livrează MAI mult "
                   "curent decât absoarbe, iar o sarcină pare de (Np/Ns)² ori mai mare din primar - baza adaptării "
                   "de impedanță (transformatoare audio, balunuri RF)."),
    "tx.wave": ("Primary and secondary voltage", "Tensiunea din primar și din secundar"),
})

ACCENT = "#B8860B"
P_COL = "#B8860B"
S_COL = "#2A9D8F"


class TransformerPanel(ttk.Frame):
    def __init__(self, parent, accent=ACCENT):
        super().__init__(parent, style="Card.TFrame")
        self.accent = accent
        left, right = two_columns(self, left_min=440)
        section(left, t("tx.title"), accent, padx=4, pady=(4, 6))
        self.form = ParamForm(left, [
            {"key": "np", "label": t("tx.np"), "default": "100", "unit": "", "slider": (1, 2000, True)},
            {"key": "ns", "label": t("tx.ns"), "default": "50", "unit": "", "slider": (1, 2000, True)},
            {"key": "vp", "label": t("tx.vp"), "default": "230", "unit": "V", "slider": (1, 1000, True)},
            {"key": "f", "label": t("tx.f"), "default": "50", "unit": "Hz", "slider": (1, 100000, True)},
            {"key": "rl", "label": t("tx.rl"), "default": "100", "unit": "Ω"},
        ], self.update_all, label_width=30)
        self.form.pack(fill="x", padx=4)
        self.tiles = TileRow(left, [("ratio", t("tx.ratio")), ("kind", t("tx.kind")),
                                    ("vs", t("tx.vs")), ("is", t("tx.is")),
                                    ("ip", t("tx.ip")), ("p", t("tx.p")),
                                    ("zin", t("tx.zin"))], accent, per_row=2)
        self.tiles.pack(fill="x", padx=4, pady=(12, 6))
        tk.Label(left, text=t("tx.rules"), font=("Consolas", 10, "bold"), fg=accent, bg="#ffffff",
                 anchor="w", justify="left", wraplength=440).pack(fill="x", padx=4, pady=(4, 4))
        note(left, t("tx.explain"), wrap=440, padx=4)

        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=3)
        right.rowconfigure(2, weight=2)
        self.cv = FitCanvas(right, 560, 280, kmax=1.6)
        self.cv.grid(row=0, column=0, sticky="nsew")
        ttk.Label(right, text=t("tx.wave"), font=("Segoe UI", 10, "bold"), foreground=accent,
                  style="CardSub.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 2))
        self.chart = MplChartFrame(right, figsize=(6.0, 2.4), with_toolbar=False)
        self.chart.grid(row=2, column=0, sticky="nsew")
        self.chart.canvas.get_tk_widget().configure(height=200)
        self.after(30, self.update_all)

    # ------------------------------------------------------------------
    def _calc(self):
        v = self.form.values()
        np_, ns, vp, f, rl = max(v["np"], 1e-9), max(v["ns"], 1e-9), v["vp"], max(v["f"], 1e-9), v["rl"]
        n = np_ / ns
        vs = vp / n
        is_ = vs / rl if rl > 0 else 0.0
        ip = is_ / n
        return dict(np=np_, ns=ns, vp=vp, f=f, rl=rl, n=n, vs=vs, is_=is_, ip=ip, p=vs * is_,
                    zin=n * n * rl if rl > 0 else float("inf"))

    def update_all(self):
        try:
            r = self._calc()
        except Exception:
            return
        T = self.tiles
        T.set("ratio", f"{r['n']:.3g} : 1")
        T.set("kind", t("tx.down") if r["n"] > 1.0001 else t("tx.up") if r["n"] < 0.9999 else t("tx.iso"))
        T.set("vs", eng(r["vs"], "V"))
        T.set("is", eng(r["is_"], "A") if r["rl"] > 0 else "–")
        T.set("ip", eng(r["ip"], "A") if r["rl"] > 0 else "–")
        T.set("p", eng(r["p"], "W") if r["rl"] > 0 else "–")
        T.set("zin", eng(r["zin"], "Ω") if r["rl"] > 0 else "∞")
        self.cv.show(lambda: self._draw(r))
        self._plot(r)

    def _draw(self, r):
        c = self.cv
        W, H = 560, 280
        cx, cy = W / 2, H / 2 + 6
        # core
        c.create_rectangle(cx - 12, cy - 95, cx + 12, cy + 95, fill="#8a8a8a", outline="#4d4d4d", width=2)
        c.create_line(cx - 4, cy - 95, cx - 4, cy + 95, fill="#6d6d6d")
        c.create_line(cx + 4, cy - 95, cx + 4, cy + 95, fill="#6d6d6d")
        # coils: bump count follows the turns (2..12), both spanning the same height
        tot = max(r["np"], r["ns"])
        nb_p = int(round(2 + 10 * r["np"] / tot))
        nb_s = int(round(2 + 10 * r["ns"] / tot))
        top, bot = cy - 80, cy + 80

        def coil(x_spine, nb, side, color):
            step = (bot - top) / nb
            for i in range(nb):
                y0 = top + i * step
                if side < 0:
                    c.create_arc(x_spine - 22, y0, x_spine + 22, y0 + step, start=90, extent=180,
                                 style="arc", outline=color, width=4)
                else:
                    c.create_arc(x_spine - 22, y0, x_spine + 22, y0 + step, start=270, extent=180,
                                 style="arc", outline=color, width=4)

        xp, xs = cx - 40, cx + 40
        coil(xp, nb_p, -1, P_COL)
        coil(xs, nb_s, +1, S_COL)
        # primary side: AC source
        sx = 70
        sym.wire(c, xp, top, sx, top, sx, cy - 20)
        sym.wire(c, xp, bot, sx, bot, sx, cy + 20)
        sym.ac_source(c, sx, cy)
        c.create_text(sx - 26, cy, text=f"Vp\n{eng(r['vp'], 'V')}", anchor="e", font=("Segoe UI", 9, "bold"),
                      fill=P_COL, justify="right")
        # secondary: load
        lx = W - 80
        sym.wire(c, xs, top, lx, top)
        sym.wire(c, xs, bot, lx, bot)
        if r["rl"] > 0:
            sym.resistor(c, lx, top, lx, bot, label="RL", value=eng(r["rl"], "Ω"))
        else:
            sym.terminal(c, lx, top, label="")
            sym.terminal(c, lx, bot, label="")
        c.create_text(lx + 22, cy + 38, text=f"Vs\n{eng(r['vs'], 'V')}", anchor="w", font=("Segoe UI", 9, "bold"),
                      fill=S_COL)
        # currents
        if r["rl"] > 0:
            sym.current_arrow(c, sx + 40, top - 1, sx + 90, top - 1, text=f"Ip = {eng(r['ip'], 'A')}",
                              color=P_COL)
            sym.current_arrow(c, lx - 90, top - 1, lx - 40, top - 1, text=f"Is = {eng(r['is_'], 'A')}",
                              color=S_COL)
        c.create_text(xp - 30, bot + 18, text=f"Np = {r['np']:g}", font=("Segoe UI", 9, "bold"), fill=P_COL)
        c.create_text(xs + 30, bot + 18, text=f"Ns = {r['ns']:g}", font=("Segoe UI", 9, "bold"), fill=S_COL)
        c.create_text(cx, top - 26, text=f"{r['n']:.3g} : 1", font=("Segoe UI", 11, "bold"), fill="#1f2a44")

    def _plot(self, r):
        fig = self.chart.fig
        fig.clear()
        ax = fig.add_subplot(111)
        tt = np.linspace(0, 2 / r["f"], 400)
        k = math.sqrt(2)
        ax.plot(tt * 1e3, k * r["vp"] * np.sin(2 * np.pi * r["f"] * tt), color=P_COL, lw=2, label="vp(t)")
        ax.plot(tt * 1e3, k * r["vs"] * np.sin(2 * np.pi * r["f"] * tt), color=S_COL, lw=2, label="vs(t)")
        ax.axhline(0, color="#999", lw=0.8)
        ax.set_xlabel("t (ms)", fontsize=9)
        ax.set_ylabel("V", fontsize=9)
        ax.tick_params(labelsize=8)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="upper right")
        try:
            fig.tight_layout(pad=0.6)
        except Exception:
            pass
        self.chart.redraw()
