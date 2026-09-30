"""
tabs/led_calc.py - Diodes > LED Resistor Calc (v6.3).

Series resistor for one LED: exact value, the next standard (E12) value
above it and what current that really gives, power in the resistor and the
LED, a suitable resistor rating, and a chart of LED current against the
resistor so you can see how forgiving the choice is.
"""
import math
import tkinter as tk
from tkinter import ttk

import numpy as np

from i18n import t, register
from uikit import ParamForm, TileRow, FitCanvas, two_columns, section, note, eng
from charts import MplChartFrame
import smd_codes as sc
import symbols as sym

register({
    "ledc.title": ("LED series-resistor calculator", "Calculator rezistor serie pentru LED"),
    "ledc.vs": ("Supply voltage Vs", "Tensiunea de alimentare Vs"),
    "ledc.vf": ("LED forward voltage Vf", "Tensiunea directă a LED-ului Vf"),
    "ledc.if": ("Desired LED current If", "Curentul dorit prin LED If"),
    "ledc.colour": ("LED colour (sets a typical Vf):", "Culoarea LED-ului (setează un Vf tipic):"),
    "ledc.r": ("Exact resistor", "Rezistor exact"),
    "ledc.e12": ("Use (next E12 up)", "Folosește (următorul E12)"),
    "ledc.iact": ("Real current with it", "Curentul real cu el"),
    "ledc.pr": ("Resistor power", "Puterea pe rezistor"),
    "ledc.rating": ("Resistor rating", "Puterea nominală"),
    "ledc.pled": ("LED power", "Puterea pe LED"),
    "ledc.eff": ("Efficiency (LED / total)", "Randament (LED / total)"),
    "ledc.low": ("Vs must be larger than Vf", "Vs trebuie să fie mai mare decât Vf"),
    "ledc.chart": ("LED current vs resistor", "Curentul prin LED în funcție de rezistor"),
    "ledc.why": ("R = (Vs − Vf) / If. Pick the next standard value ABOVE the exact one so the current "
                 "stays at or below what you asked for. The chart shows how the current falls as R grows - "
                 "with a small headroom (Vs close to Vf) a small change of Vf changes the current a lot.",
                 "R = (Vs − Vf) / If. Alege valoarea standard imediat PESTE cea exactă, astfel încât curentul să "
                 "rămână cel mult cât ai cerut. Graficul arată cum scade curentul când R crește - cu o rezervă mică "
                 "(Vs apropiat de Vf) o mică schimbare a lui Vf schimbă mult curentul."),
})

LED_TYPES = [("#e53935", 2.0), ("#fb8c00", 2.1), ("#fdd835", 2.1), ("#43a047", 2.2),
             ("#00c853", 3.0), ("#1e88e5", 3.1), ("#f5f5f5", 3.1), ("#8e24aa", 3.3)]
RATINGS = [0.125, 0.25, 0.5, 1, 2, 3, 5]


def _blend(c1, c2, a):
    """Mix colour c1 into c2 with weight a (0..1)."""
    r1, g1, b1 = (int(c1[i:i + 2], 16) for i in (1, 3, 5))
    r2, g2, b2 = (int(c2[i:i + 2], 16) for i in (1, 3, 5))
    return "#%02x%02x%02x" % tuple(int(x2 + (x1 - x2) * a) for x1, x2 in ((r1, r2), (g1, g2), (b1, b2)))


class LedResistorPanel(ttk.Frame):
    def __init__(self, parent, accent):
        super().__init__(parent, style="Card.TFrame")
        self.accent = accent
        self.color = LED_TYPES[0][0]
        left, right = two_columns(self, left_min=440)
        section(left, t("ledc.title"), accent, padx=4, pady=(4, 6))
        self.form = ParamForm(left, [
            {"key": "vs", "label": t("ledc.vs"), "default": "9", "unit": "V", "slider": (1, 48, True)},
            {"key": "vf", "label": t("ledc.vf"), "default": "2", "unit": "V", "slider": (1.2, 4, False)},
            {"key": "if", "label": t("ledc.if"), "default": "20m", "unit": "A", "slider": (0.001, 0.35, True)},
        ], self.update_all, label_width=26)
        self.form.pack(fill="x", padx=4)
        row = ttk.Frame(left, style="Card.TFrame")
        row.pack(fill="x", padx=4, pady=(10, 4))
        ttk.Label(row, text=t("ledc.colour"), style="CardBody.TLabel").pack(side="left")
        for col, vf in LED_TYPES:
            b = tk.Label(row, bg=col, width=3, relief="ridge", bd=2, cursor="hand2")
            b.pack(side="left", padx=2)
            b.bind("<Button-1>", lambda _e, c=col, v=vf: self._pick(c, v))
        self.tiles = TileRow(left, [("r", t("ledc.r")), ("e12", t("ledc.e12")),
                                    ("iact", t("ledc.iact")), ("pr", t("ledc.pr")),
                                    ("rating", t("ledc.rating")), ("pled", t("ledc.pled")),
                                    ("eff", t("ledc.eff"))], accent, per_row=2)
        self.tiles.pack(fill="x", padx=4, pady=(12, 6))
        note(left, t("ledc.why"), wrap=440, padx=4)

        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=3)
        right.rowconfigure(2, weight=2)
        self.cv = FitCanvas(right, 520, 260, kmax=1.6)
        self.cv.grid(row=0, column=0, sticky="nsew")
        ttk.Label(right, text=t("ledc.chart"), font=("Segoe UI", 10, "bold"), foreground=accent,
                  style="CardSub.TLabel").grid(row=1, column=0, sticky="w", pady=(10, 2))
        self.chart = MplChartFrame(right, figsize=(6.0, 2.4), with_toolbar=False)
        self.chart.grid(row=2, column=0, sticky="nsew")
        self.chart.canvas.get_tk_widget().configure(height=200)
        self.after(30, self.update_all)

    def _pick(self, col, vf):
        self.color = col
        self.form.set("vf", vf)
        self.update_all()

    def update_all(self):
        try:
            v = self.form.values()
        except Exception:
            return
        vs, vf, i = v["vs"], v["vf"], max(v["if"], 1e-6)
        T = self.tiles
        if vs <= vf:
            for k in ("r", "e12", "iact", "pr", "rating", "pled", "eff"):
                T.set(k, "–")
            T.set("r", t("ledc.low"), warn=True)
            self.cv.show(lambda: self._draw(vs, vf, None, None))
            return
        r = (vs - vf) / i
        e12 = sc.nearest_series(r, sc.E12)
        if e12 < r * 0.999:     # next value up
            cands = sorted(m / 10 * d for d in (10 ** math.floor(math.log10(r)), 10 ** (math.floor(math.log10(r)) + 1))
                           for m in sc.E12)
            e12 = next(c for c in cands if c >= r * 0.999)
        ia = (vs - vf) / e12
        pr = ia * ia * e12
        rating = next((x for x in RATINGS if x >= 2 * pr), RATINGS[-1])
        pled = vf * ia
        T.set("r", eng(r, "Ω"))
        T.set("e12", eng(e12, "Ω"))
        T.set("iact", eng(ia, "A"))
        T.set("pr", eng(pr, "W"), warn=pr > 0.25)
        T.set("rating", (f"1/{round(1 / rating)} W" if rating < 1 else f"{rating:g} W") + "  (≥ 2×)")
        T.set("pled", eng(pled, "W"))
        T.set("eff", f"{100 * vf / vs:.0f} %")
        self.cv.show(lambda: self._draw(vs, vf, e12, ia))
        self._plot(vs, vf, r, e12, ia)

    def _draw(self, vs, vf, r, i):
        c = self.cv
        W, H = 520, 260
        x0, x1, ytop, ybot = 90, 440, 60, 210
        # source
        sym.wire(c, x0, ytop, x0, (ytop + ybot) / 2 - 18)
        sym.wire(c, x0, (ytop + ybot) / 2 + 18, x0, ybot)
        sym.dc_source(c, x0, (ytop + ybot) / 2)
        c.create_text(x0 - 26, (ytop + ybot) / 2, text=f"Vs\n{vs:g} V", anchor="e",
                      font=("Segoe UI", 10, "bold"), fill="#1f2a44", justify="right")
        # resistor on top
        sym.wire(c, x0, ytop, 150, ytop)
        sym.resistor(c, 150, ytop, 300, ytop, label="R", value=eng(r, "Ω") if r else "?")
        sym.wire(c, 300, ytop, x1, ytop, x1, 100)
        # LED going down on the right (with a glow when current flows)
        if i:
            for rr, a in ((38, 0.18), (28, 0.32), (20, 0.5)):
                c.create_oval(x1 - rr, 135 - rr, x1 + rr, 135 + rr, fill=_blend(self.color, "#fdfaf3", a),
                              outline="")
        sym.diode(c, x1, 100, x1, 170, variant="led", fill=self.color, label="LED", value=f"Vf = {vf:g} V",
                  label_side=-1)
        sym.wire(c, x1, 170, x1, ybot, x0, ybot)
        if i:
            sym.current_arrow(c, 330, ytop - 1, 390, ytop - 1, text=f"I = {eng(i, 'A')}")
            c.create_text(225, ytop + 30, text=f"V_R = {vs - vf:.3g} V", font=("Segoe UI", 9, "bold"),
                          fill="#c62828")

    def _plot(self, vs, vf, r, e12, ia):
        fig = self.chart.fig
        fig.clear()
        ax = fig.add_subplot(111)
        rr = np.logspace(math.log10(r) - 0.5, math.log10(r) + 0.5, 200)
        ax.plot(rr, (vs - vf) / rr * 1e3, color=self.accent, lw=2, label="Vf")
        for dv, ls in ((-0.2, "--"), (0.2, ":")):
            ax.plot(rr, np.clip(vs - (vf + dv), 0, None) / rr * 1e3, color=self.accent, lw=1, ls=ls,
                    label=f"Vf {dv:+.1f} V")
        ax.plot([e12], [ia * 1e3], "o", color="#1f2a44", ms=7, zorder=5)
        ax.annotate(f"E12 {eng(e12, 'Ω')}", (e12, ia * 1e3), xytext=(8, 8), textcoords="offset points", fontsize=8)
        ax.set_xscale("log")
        try:
            from matplotlib.ticker import EngFormatter
            ax.xaxis.set_major_formatter(EngFormatter(unit="Ω", sep=" "))
        except Exception:
            pass
        ax.set_xlabel("R", fontsize=9)
        ax.set_ylabel("I (mA)", fontsize=9)
        ax.tick_params(labelsize=8)
        ax.grid(alpha=0.3, which="both")
        ax.legend(fontsize=8)
        try:
            fig.tight_layout(pad=0.6)
        except Exception:
            pass
        self.chart.redraw()
