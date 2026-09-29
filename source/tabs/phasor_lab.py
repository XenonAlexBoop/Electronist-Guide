"""
tabs/phasor_lab.py - v6 AC pages:

  PhasorLabPanel   series / parallel / mixed RLC circuits: rotating phasors
                   linked to the waveforms (the projection of each rotating
                   arrow IS the instantaneous value), element voltages or
                   branch currents added tip-to-tail, impedance & power
                   triangles, and a frequency sweep with resonance, Q and BW.
  PFCorrectionPanel  power triangle of a load and the capacitor that corrects
                   its power factor to a target (before / after).
"""
import math
import numpy as np
import tkinter as tk
from tkinter import ttk
from matplotlib.gridspec import GridSpec

import symbols as sym
from charts import MplChartFrame, PLOT_BG
from widgets import ScrollableFrame, FONT_BODY, is_shown
from uikit import Segmented, ParamForm, TileRow, note, eng
from i18n import t, register, tr


class cmath:
    """cmath.phase / cmath.exp without importing cmath (keeps the frozen exe's
    module list unchanged)."""
    @staticmethod
    def phase(z):
        return math.atan2(z.imag, z.real)

    @staticmethod
    def exp(z):
        return complex(math.cos(z.imag), math.sin(z.imag)) * math.exp(z.real)

ACCENT_C = "#277DA1"
COL = {"R": "#c9622a", "L": "#B8860B", "C": "#2E5EAA", "RL": "#8a6d00", "LC": "#6A4C93",
       "V": "#1f2a44", "I": "#c62828"}

register({
    "pl.tab": ("Phasor Lab", "Laborator fazori"),
    "pl.pf": ("Power & PF correction", "Putere și compensare"),
    "pl.3ph": ("3-phase systems", "Sisteme trifazate"),
    "pl.pick": ("Circuit", "Circuit"),
    "pl.c.s_rc": ("Series RC", "RC serie"), "pl.c.s_rl": ("Series RL", "RL serie"),
    "pl.c.s_rlc": ("Series RLC", "RLC serie"), "pl.c.p_rc": ("Parallel RC", "RC paralel"),
    "pl.c.p_rl": ("Parallel RL", "RL paralel"), "pl.c.p_rlc": ("Parallel RLC", "RLC paralel"),
    "pl.c.tank": ("Real coil ‖ C (tank)", "Bobină reală ‖ C (circuit oscilant)"),
    "pl.c.r_lc": ("R + (L ‖ C)", "R + (L ‖ C)"),
    "pl.src": ("Source", "Sursă"),
    "pl.vrms": ("Voltage (RMS)", "Tensiune (efectivă)"),
    "pl.f": ("Frequency", "Frecvență"),
    "pl.view": ("View", "Vizualizare"),
    "pl.v.rot": ("Rotating phasors", "Fazori rotitori"),
    "pl.v.tri": ("Z & power triangles", "Triunghiurile Z și puteri"),
    "pl.v.sweep": ("Frequency sweep", "Baleiaj în frecvență"),
    "pl.play": ("▶ Rotate", "▶ Rotește"),
    "pl.pause": ("❚❚ Pause", "❚❚ Pauză"),
    "pl.angle": ("ωt", "ωt"),
    "pl.t.z": ("Impedance |Z|", "Impedanța |Z|"),
    "pl.t.phi": ("Phase φ (V vs I)", "Faza φ (V față de I)"),
    "pl.t.i": ("Current (RMS)", "Curent (efectiv)"),
    "pl.t.pf": ("Power factor", "Factor de putere"),
    "pl.t.p": ("Active P", "Activă P"),
    "pl.t.q": ("Reactive Q", "Reactivă Q"),
    "pl.t.s": ("Apparent S", "Aparentă S"),
    "pl.t.f0": ("Resonance f0", "Rezonanța f0"),
    "pl.lead": ("leading (capacitive)", "capacitiv (înainte)"),
    "pl.lag": ("lagging (inductive)", "inductiv (în urmă)"),
    "pl.unity": ("unity (resistive)", "unitar (rezistiv)"),
    "pl.elems": ("Element values (RMS)", "Valori pe elemente (efective)"),
    "pl.x.series": ("Series circuit: the SAME current flows through every part, so I is the reference (0°). "
                    "Each element's voltage is an arrow: V_R in phase with I, V_L 90° ahead, V_C 90° behind. "
                    "Added tip-to-tail they make the source voltage — that is why V_L and V_C can each be "
                    "bigger than the supply near resonance.",
                    "Circuit serie: ACELAȘI curent trece prin toate elementele, deci I e referința (0°). Tensiunea "
                    "fiecărui element e o săgeată: V_R în fază cu I, V_L cu 90° înainte, V_C cu 90° în urmă. Puse "
                    "cap la coadă dau tensiunea sursei — de aceea V_L și V_C pot fi fiecare mai mari decât "
                    "alimentarea lângă rezonanță."),
    "pl.x.parallel": ("Parallel circuit: every branch sees the SAME voltage, so V is the reference (0°). Each "
                      "branch current is an arrow: I_R in phase, I_C 90° ahead, I_L 90° behind. Added tip-to-tail "
                      "they make the supply current — at resonance I_L and I_C cancel and the supply only "
                      "delivers I_R.",
                      "Circuit paralel: fiecare ramură are ACEEAȘI tensiune, deci V e referința (0°). Curentul "
                      "fiecărei ramuri e o săgeată: I_R în fază, I_C cu 90° înainte, I_L cu 90° în urmă. Puse cap "
                      "la coadă dau curentul sursei — la rezonanță I_L și I_C se anulează și sursa dă doar I_R."),
    "pl.x.rot": ("Each arrow rotates at ω. Its height (projection on the vertical axis) at any instant is the "
                 "instantaneous value — follow the dotted lines to the waveform on the right.",
                 "Fiecare săgeată se rotește cu ω. Înălțimea ei (proiecția pe axa verticală) în orice moment este "
                 "valoarea instantanee — urmărește liniile punctate până la forma de undă din dreapta."),
    "pl.ax.deg": ("ωt (degrees)", "ωt (grade)"),
    "pl.ax.v": ("Voltage (V)", "Tensiune (V)"),
    "pl.ax.i": ("Current (A)", "Curent (A)"),
    "pl.ztri": ("Impedance triangle", "Triunghiul impedanțelor"),
    "pl.stri": ("Power triangle", "Triunghiul puterilor"),
    "pl.sweep.z": ("|Z| and phase vs frequency", "|Z| și faza în funcție de frecvență"),
    "pl.sweep.i": ("Supply current vs frequency", "Curentul sursei în funcție de frecvență"),
    "pl.bw": ("BW", "Bandă"),
    # PF correction
    "pf.intro": ("Motors, transformers and fluorescent ballasts draw a lagging (inductive) current: part of it "
                 "only sloshes energy back and forth (Q) but still heats the cables and is billed on big "
                 "installations. A capacitor in parallel supplies that reactive current locally.",
                 "Motoarele, transformatoarele și balasturile iau un curent inductiv: o parte din el doar "
                 "plimbă energia înainte și înapoi (Q), dar tot încălzește cablurile și se facturează la "
                 "consumatorii mari. Un condensator în paralel furnizează local acel curent reactiv."),
    "pf.v": ("Supply voltage (RMS)", "Tensiunea rețelei (efectivă)"),
    "pf.f": ("Frequency", "Frecvență"),
    "pf.p": ("Load active power P", "Puterea activă a sarcinii P"),
    "pf.pf1": ("Present power factor", "Factorul de putere actual"),
    "pf.pf2": ("Target power factor", "Factorul de putere dorit"),
    "pf.t.c": ("Capacitor needed", "Condensator necesar"),
    "pf.t.qc": ("Capacitor reactive power", "Puterea reactivă a condensatorului"),
    "pf.t.i1": ("Current before", "Curent înainte"),
    "pf.t.i2": ("Current after", "Curent după"),
    "pf.t.s1": ("S before", "S înainte"),
    "pf.t.s2": ("S after", "S după"),
    "pf.t.save": ("Line current reduction", "Reducerea curentului de linie"),
    "pf.t.loss": ("Cable loss reduction (I²R)", "Reducerea pierderilor în cablu (I²R)"),
    "pf.before": ("before", "înainte"), "pf.after": ("after", "după"),
})

CIRCUITS = {
    "s_rc": ("s", ["R", "C"]), "s_rl": ("s", ["R", "L"]), "s_rlc": ("s", ["R", "L", "C"]),
    "p_rc": ("p", ["R", "C"]), "p_rl": ("p", ["R", "L"]), "p_rlc": ("p", ["R", "L", "C"]),
    "tank": ("p", [("s", ["R", "L"]), "C"]),
    "r_lc": ("s", ["R", ("p", ["L", "C"])]),
}
ORDER = ["s_rc", "s_rl", "s_rlc", "p_rc", "p_rl", "p_rlc", "tank", "r_lc"]


def _uses(node, out=None):
    out = set() if out is None else out
    if isinstance(node, str):
        out.add(node)
    else:
        for c in node[1]:
            _uses(c, out)
    return out


def _name(node):
    if isinstance(node, str):
        return node
    return ("" if node[0] == "s" else "") + "".join(_name(c) for c in node[1])


def _z(node, P, w):
    if isinstance(node, str):
        if node == "R":
            return complex(P["r"], 0)
        if node == "L":
            return complex(0, w * P["l"])
        return complex(0, -1 / (w * P["c"]))
    zs = [_z(c, P, w) for c in node[1]]
    if node[0] == "s":
        return sum(zs)
    y = sum(1 / z if abs(z) > 1e-15 else 1e15 for z in zs)
    return 1 / y if abs(y) > 1e-18 else complex(1e18, 0)


class PhasorLabPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        accent = ACCENT_C
        self.accent = accent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body

        pick = ttk.Frame(body, style="Card.TFrame")
        pick.pack(fill="x", padx=16, pady=(12, 0))
        self.circ = tk.StringVar(value="s_rlc")
        Segmented(pick, [(k, t("pl.c." + k)) for k in ORDER], self.circ, lambda k: self._on_circuit(),
                  accent=accent, wrap=4).pack(anchor="w")

        top = ttk.Frame(body, style="Card.TFrame")
        top.pack(fill="both", expand=True, padx=16, pady=(8, 12))
        top.columnconfigure(1, weight=1)
        left = ttk.Frame(top, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nw")
        right = ttk.Frame(top, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(16, 0))

        self.canvas = tk.Canvas(left, width=420, height=200, bg=sym.CANVAS_BG, highlightthickness=0)
        self.canvas.pack(anchor="w")
        self.form = ParamForm(left, [
            dict(key="v", label=t("pl.vrms"), default="230", unit="V", slider=(1, 400)),
            dict(key="f", label=t("pl.f"), default="50", unit="Hz", slider=(1, 100e3, True)),
            dict(key="r", label="R", default="47", unit="Ω", slider=(1, 10e3, True)),
            dict(key="l", label="L", default="220m", unit="H", slider=(1e-5, 10, True)),
            dict(key="c", label="C", default="33u", unit="F", slider=(1e-9, 1e-3, True)),
        ], self.update_all, label_width=16)
        self.form.pack(anchor="w", pady=(6, 0))
        self.tiles = TileRow(left, [("z", t("pl.t.z")), ("phi", t("pl.t.phi")), ("i", t("pl.t.i")),
                                    ("pf", t("pl.t.pf")), ("p", t("pl.t.p")), ("q", t("pl.t.q")),
                                    ("s", t("pl.t.s")), ("f0", t("pl.t.f0"))], accent, per_row=2)
        self.tiles.pack(fill="x", pady=(8, 0))
        ttk.Label(left, text=t("pl.elems"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel")\
            .pack(anchor="w", pady=(8, 0))
        self.elem_txt = ttk.Label(left, text="", font=("Consolas", 10), style="CardBody.TLabel", justify="left")
        self.elem_txt.pack(anchor="w")
        self.explain = note(left, "", wrap=420, padx=0, pady=(8, 4))

        vrow = ttk.Frame(right, style="Card.TFrame")
        vrow.pack(anchor="w", fill="x")
        self.view = tk.StringVar(value="rot")
        Segmented(vrow, [(k, t("pl.v." + k)) for k in ("rot", "tri", "sweep")], self.view,
                  lambda k: self.update_all(), accent=accent, font_size=10).pack(side="left")
        self.play_btn = ttk.Button(vrow, text=t("pl.play"), style="Small.TButton", command=self._toggle)
        self.play_btn.pack(side="left", padx=(16, 6))
        ttk.Label(vrow, text=t("pl.angle"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self.ang = ttk.Scale(vrow, from_=0, to=720, orient="horizontal", length=220, command=self._on_angle)
        self.ang.set(60)
        self.ang.pack(side="left", padx=6)
        self.chart = MplChartFrame(right, figsize=(7.4, 4.8), with_toolbar=False)
        self.chart.pack(fill="both", expand=True, pady=(6, 0))
        self.view_note = note(right, t("pl.x.rot"), wrap=700, padx=0, pady=(4, 0), italic=True)
        self._playing = False
        self._on_circuit()

    # ------------------------------------------------------------------
    def _on_circuit(self):
        key = self.circ.get()
        top, _ = CIRCUITS[key]
        self.explain.configure(text=t("pl.x.series") if top == "s" else t("pl.x.parallel"))
        self.update_all()

    def _solve(self, P, w):
        key = self.circ.get()
        tree = CIRCUITS[key]
        Vs = complex(P["v"], 0)
        Z = _z(tree, P, w)
        I = Vs / Z
        parts = []   # (label, V, I) of each top-level child
        elems = {}

        def walk(node, V, Ic):
            if isinstance(node, str):
                elems[node] = (V, Ic)
                return
            for c in node[1]:
                zc = _z(c, P, w)
                if node[0] == "s":
                    walk(c, Ic * zc, Ic)
                else:
                    walk(c, V, V / zc if abs(zc) > 1e-15 else 0)
        for c in tree[1]:
            zc = _z(c, P, w)
            if tree[0] == "s":
                parts.append((_name(c), I * zc, I))
            else:
                parts.append((_name(c), Vs, Vs / zc))
        walk(tree, Vs, I)
        return tree, Z, I, parts, elems

    def update_all(self, *_):
        try:
            P = self.form.values()
            if P["f"] <= 0 or P["r"] <= 0 or P["l"] <= 0 or P["c"] <= 0:
                return
        except Exception:
            return
        w = 2 * math.pi * P["f"]
        tree, Z, I, parts, elems = self._solve(P, w)
        self.P, self.tree, self.Z, self.I, self.parts = P, tree, Z, I, parts
        phi = math.degrees(cmath.phase(Z))
        S = P["v"] * abs(I)
        pf = math.cos(math.radians(phi))
        tl = self.tiles
        tl.set("z", f"{eng(abs(Z), 'Ω')} ∠{phi:+.1f}°")
        state = t("pl.unity") if abs(phi) < 0.5 else (t("pl.lag") if phi > 0 else t("pl.lead"))
        tl.set("phi", f"{phi:+.1f}°")
        tl.tiles["phi"].cap.configure(text=f"{t('pl.t.phi')} · {state}")
        tl.set("i", eng(abs(I), "A"))
        tl.set("pf", f"{pf:.3f}")
        tl.set("p", eng(S * pf, "W"))
        tl.set("q", eng(S * math.sin(math.radians(phi)), "var"))
        tl.set("s", eng(S, "VA"))
        uses = _uses(tree)
        if "L" in uses and "C" in uses:
            tl.set("f0", eng(1 / (2 * math.pi * math.sqrt(P["l"] * P["c"])), "Hz"))
        else:
            tl.set("f0", "—")
        lines = []
        for k in ("R", "L", "C"):
            if k in elems:
                V, Ie = elems[k]
                lines.append(f"{k}: V = {eng(abs(V), 'V'):>9} ∠{math.degrees(cmath.phase(V)):+6.1f}°   "
                             f"I = {eng(abs(Ie), 'A'):>9} ∠{math.degrees(cmath.phase(Ie)) if abs(Ie) > 0 else 0:+6.1f}°")
        self.elem_txt.configure(text="\n".join(lines))
        self._draw_schematic()
        v = self.view.get()
        self.view_note.configure(text=t("pl.x.rot") if v == "rot" else "")
        if v == "rot":
            self._build_rot()
        elif v == "tri":
            self._triangles(P, Z, I)
        else:
            self._sweep(P)

    # ------------------------------------------------------------------
    def _build_rot(self):
        fig = self.chart.fig
        fig.clear()
        gs = GridSpec(1, 2, figure=fig, width_ratios=[1, 1.5], wspace=0.05)
        self.ax_p = fig.add_subplot(gs[0])
        self.ax_w = fig.add_subplot(gs[1])
        series = self.tree[0] == "s"
        self._series = series
        # quantities: voltages (series) or currents (parallel); reference = the common one
        if series:
            self._parts = [(f"V_{x[0]}", x[1], COL.get(x[0], "#555")) for x in self.parts]
            self._total = ("V", complex(self.P["v"], 0), COL["V"])
            self._ref = ("I", self.I, COL["I"])
        else:
            self._parts = [(f"I_{x[0]}", x[2], COL.get(x[0], "#555")) for x in self.parts]
            self._total = ("I", self.I, COL["I"])
            self._ref = ("V", complex(self.P["v"], 0), COL["V"])
        # express everything relative to the reference so the reference sits at 0° when ωt = 0
        ref_ang = cmath.phase(self._ref[1])
        rot = cmath.exp(-1j * ref_ang)
        self._parts = [(l, z * rot, c) for l, z, c in self._parts]
        self._total = (self._total[0], self._total[1] * rot, self._total[2])
        self._ref = (self._ref[0], self._ref[1] * rot, self._ref[2])
        mags = [abs(z) for _, z, _ in self._parts] + [abs(self._total[1])]
        acc, reach = 0j, abs(self._total[1])
        for _, z, _ in self._parts:
            acc += z
            reach = max(reach, abs(acc))
        self._scale = max(max(mags), 1e-12)
        self._reach = reach / self._scale
        ax = self.ax_p
        lim = 1.15 * max(1.0, self._reach)
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal")
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        th = np.linspace(0, 2 * np.pi, 200)
        ax.plot(np.cos(th), np.sin(th), color="#e2e2e2", lw=1)
        ax.axhline(0, color="#ddd", lw=0.8)
        ax.axvline(0, color="#ddd", lw=0.8)
        ax.set_facecolor(PLOT_BG)
        # waveform axis (values normalised the same way; label in real units)
        axw = self.ax_w
        axw.set_facecolor(PLOT_BG)
        deg = np.linspace(0, 720, 721)
        rad = np.radians(deg)
        for l, z, c in self._parts:
            axw.plot(deg, (abs(z) / self._scale) * np.sin(rad + cmath.phase(z)), color=c, lw=1.2, alpha=0.8,
                     label=l)
        l, z, c = self._total
        axw.plot(deg, (abs(z) / self._scale) * np.sin(rad + cmath.phase(z)), color=c, lw=2.4, label=l)
        l, z, c = self._ref
        axw.plot(deg, 0.35 * np.sin(rad + cmath.phase(z)), color=c, lw=1.2, ls="--",
                 label=tr(f"{l} (ref., scaled)", f"{l} (ref., scalat)"))
        axw.set_xlim(0, 720)
        axw.set_ylim(-lim, lim)
        axw.set_xticks([0, 90, 180, 270, 360, 450, 540, 630, 720])
        axw.tick_params(labelsize=7)
        axw.set_yticks([])
        axw.grid(True, alpha=0.25)
        axw.set_xlabel(t("pl.ax.deg"), fontsize=8)
        axw.legend(fontsize=7, loc="upper right", ncol=2)
        unit = "V" if series else "A"
        axw.set_title(tr("peak of largest = ", "vârful celui mai mare = ") + eng(self._scale * math.sqrt(2), unit), fontsize=8, color="#666")
        self._dyn = []
        self.cursor = axw.axvline(0, color="#1f2a44", lw=1)
        fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.12)
        self._update_rot()

    def _update_rot(self):
        if self.view.get() != "rot":
            return
        a = math.radians(float(self.ang.get()))
        for art in self._dyn:
            try:
                art.remove()
            except Exception:
                pass
        self._dyn = []
        ax, axw = self.ax_p, self.ax_w
        e = cmath.exp(1j * a)
        x0 = 0j
        for l, z, c in self._parts:
            v = z / self._scale * e
            self._dyn.append(ax.annotate("", xy=(v.real + x0.real, v.imag + x0.imag), xytext=(x0.real, x0.imag),
                                         arrowprops=dict(arrowstyle="-|>", color=c, lw=2, mutation_scale=14)))
            mid = x0 + v / 2
            self._dyn.append(ax.text(mid.real, mid.imag, " " + l, color=c, fontsize=8, fontweight="bold"))
            x0 = x0 + v
        l, z, c = self._total
        v = z / self._scale * e
        self._dyn.append(ax.annotate("", xy=(v.real, v.imag), xytext=(0, 0),
                                     arrowprops=dict(arrowstyle="-|>", color=c, lw=3, mutation_scale=18)))
        self._dyn.append(ax.text(v.real * 1.08, v.imag * 1.08, l, color=c, fontsize=10, fontweight="bold"))
        l, z, c = self._ref
        v = 0.35 * z / abs(z) * e if abs(z) else 0
        self._dyn.append(ax.annotate("", xy=(v.real, v.imag), xytext=(0, 0),
                                     arrowprops=dict(arrowstyle="-|>", color=c, lw=1.5, ls="--",
                                                     mutation_scale=12)))
        # projections
        deg = float(self.ang.get())
        self.cursor.set_xdata([deg, deg])
        for lab, z, c in self._parts + [self._total]:
            y = (z / self._scale * e).imag
            self._dyn.append(axw.plot([deg], [y], "o", color=c, ms=5)[0])
            self._dyn.append(axw.axhline(y, color=c, lw=0.6, ls=":", alpha=0.8))
        vt = (self._total[1] / self._scale * e)
        self._dyn.append(ax.axhline(vt.imag, color=self._total[2], lw=0.6, ls=":", alpha=0.8))
        self.chart.redraw()

    def _on_angle(self, _v):
        if getattr(self, "_parts", None) is not None and self.view.get() == "rot":
            self._update_rot()

    def _toggle(self):
        self._playing = not self._playing
        self.play_btn.configure(text=t("pl.pause") if self._playing else t("pl.play"))
        if self._playing:
            if self.view.get() != "rot":
                self.view.set("rot")
                self.update_all()
            self._tick()

    def _tick(self):
        if not self._playing:
            return
        try:
            if not is_shown(self):
                self._playing = False
                self.play_btn.configure(text=t("pl.play"))
                return
        except tk.TclError:
            return
        self.ang.set((float(self.ang.get()) + 6) % 720)
        self.after(70, self._tick)

    # ------------------------------------------------------------------
    def _triangles(self, P, Z, I):
        fig = self.chart.fig
        fig.clear()
        a1 = fig.add_subplot(121)
        a2 = fig.add_subplot(122)
        R, X = Z.real, Z.imag
        self._tri(a1, R, X, abs(Z), "R", "X", "|Z|", "Ω", t("pl.ztri"))
        S = P["v"] * abs(I)
        phi = cmath.phase(Z)
        self._tri(a2, S * math.cos(phi), S * math.sin(phi), S, "P", "Q", "S", "", t("pl.stri"),
                  units=("W", "var", "VA"))
        fig.subplots_adjust(left=0.04, right=0.98, top=0.9, bottom=0.08, wspace=0.15)
        self.chart.redraw()

    @staticmethod
    def _tri(ax, a, b, h, la, lb, lh, unit, title, units=None):
        units = units or (unit, unit, unit)
        ax.set_facecolor(PLOT_BG)
        m = max(abs(a), abs(b), 1e-12)
        x, y = a / m, b / m
        ax.fill([0, x, x], [0, 0, y], color="#277DA1", alpha=0.08)
        ax.plot([0, x], [0, 0], color=COL["R"], lw=3)
        ax.plot([x, x], [0, y], color=COL["L"] if b >= 0 else COL["C"], lw=3)
        ax.plot([0, x], [0, y], color=COL["V"], lw=3)
        ax.text(x / 2, -0.06 if y >= 0 else 0.06, f"{la} = {eng(a, units[0])}", ha="center",
                va="top" if y >= 0 else "bottom", fontsize=9, color=COL["R"])
        ax.text(x + 0.03, y / 2, f"{lb} = {eng(b, units[1])}", ha="left", va="center", fontsize=9,
                color=COL["L"] if b >= 0 else COL["C"])
        ax.text(x / 2 - 0.05, y / 2 + (0.05 if y >= 0 else -0.05), f"{lh} = {eng(h, units[2])}", ha="right",
                va="bottom" if y >= 0 else "top", fontsize=9, color=COL["V"], rotation=0)
        ang = math.degrees(math.atan2(b, a))
        ax.text(0.12, 0.03 if y >= 0 else -0.03, f"φ = {ang:+.1f}°", fontsize=9,
                va="bottom" if y >= 0 else "top")
        ax.set_xlim(-0.35, 1.5)
        ax.set_ylim(min(-0.25, y - 0.25), max(0.25, y + 0.25))
        ax.set_aspect("equal", adjustable="box")
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.set_title(title, fontsize=10)

    def _sweep(self, P):
        fig = self.chart.fig
        fig.clear()
        uses = _uses(self.tree)
        if "L" in uses and "C" in uses:
            fc = 1 / (2 * math.pi * math.sqrt(P["l"] * P["c"]))
        elif "C" in uses:
            fc = 1 / (2 * math.pi * P["r"] * P["c"])
        else:
            fc = P["r"] / (2 * math.pi * P["l"])
        f = np.logspace(math.log10(fc) - 2, math.log10(fc) + 2, 600)
        Z = np.array([_z(self.tree, P, 2 * math.pi * x) for x in f])
        I = P["v"] / np.abs(Z)
        a1 = fig.add_subplot(211)
        a2 = fig.add_subplot(212, sharex=a1)
        a1.loglog(f, np.abs(Z), color=COL["V"], lw=2, label="|Z|")
        a1b = a1.twinx()
        a1b.semilogx(f, np.degrees(np.angle(Z)), color=COL["L"], lw=1.3, ls="--")
        a1b.set_ylabel("φ (°)", fontsize=8, color=COL["L"])
        a1b.set_ylim(-95, 95)
        a1b.tick_params(labelsize=7)
        a1.set_ylabel("|Z| (Ω)", fontsize=8)
        a2.semilogx(f, I, color=COL["I"], lw=2)
        a2.set_ylabel(t("pl.ax.i"), fontsize=8)
        a2.set_xlabel("f (Hz)", fontsize=8)
        a1.set_title(t("pl.sweep.z"), fontsize=9)
        for a in (a1, a2):
            a.set_facecolor(PLOT_BG)
            a.grid(True, alpha=0.25, which="both")
            a.tick_params(labelsize=7)
            a.axvline(P["f"], color=ACCENT_C, lw=1.2)
        if "L" in uses and "C" in uses:
            for a in (a1, a2):
                a.axvline(fc, color="#888", ls=":", lw=1)
            a2.text(fc, I.max(), f" f0 = {eng(fc, 'Hz')}", fontsize=8, va="top")
            # bandwidth from the current (series) or from |Z| (parallel)
            curve = I if self.tree[0] == "s" else np.abs(Z)
            lvl = curve.max() / math.sqrt(2)
            above = curve >= lvl
            idx = np.where(above[:-1] != above[1:])[0]
            if len(idx) >= 2:
                f1, f2 = f[idx[0]], f[idx[-1]]
                tgt = a2 if self.tree[0] == "s" else a1
                tgt.axvspan(f1, f2, color="#2e9d44", alpha=0.1)
                q = fc / (f2 - f1)
                tgt.text(f2, lvl, f"  {t('pl.bw')} = {eng(f2 - f1, 'Hz')}, Q ≈ {q:.3g}", fontsize=8, color="#2e7d32")
        a1.tick_params(labelbottom=False)
        fig.subplots_adjust(left=0.1, right=0.9, top=0.93, bottom=0.1, hspace=0.12)
        self.chart.redraw()

    # ------------------------------------------------------------------
    def _draw_schematic(self):
        cv = self.canvas
        cv.delete("all")
        key = self.circ.get()
        P = self.P
        vals = {"R": eng(P["r"], "Ω"), "L": eng(P["l"], "H"), "C": eng(P["c"], "F")}
        kind = {"R": "resistor", "L": "inductor", "C": "capacitor"}
        top, bot = 45, 165
        sym.ac_source(cv, 40, 105)
        sym.wire(cv, 40, 89, 40, top)
        sym.wire(cv, 40, 121, 40, bot)
        cv.create_text(40, 185, text=f"{eng(P['v'], 'V')} {eng(P['f'], 'Hz')}", font=("Segoe UI", 8), fill="#555")
        tree = CIRCUITS[key]
        if tree[0] == "s" and all(isinstance(c, str) for c in tree[1]):
            els = tree[1]
            n = len(els)
            x0, x1 = 60, 380
            seg = (x1 - x0) / n
            sym.wire(cv, 40, top, x0, top)
            for i, e in enumerate(els):
                sym.component(cv, kind[e], x0 + i * seg + 8, top, x0 + (i + 1) * seg - 8, top, label=e,
                              value=vals[e], color=COL[e])
                sym.wire(cv, x0 + i * seg, top, x0 + i * seg + 8, top)
                sym.wire(cv, x0 + (i + 1) * seg - 8, top, x0 + (i + 1) * seg, top)
            sym.wire(cv, x1, top, 400, top, 400, bot, 40, bot)
        elif tree[0] == "p" and all(isinstance(c, str) for c in tree[1]):
            els = tree[1]
            xs = [150 + i * 95 for i in range(len(els))]
            sym.wire(cv, 40, top, xs[-1], top)
            sym.wire(cv, 40, bot, xs[-1], bot)
            for x, e in zip(xs, els):
                sym.node(cv, x, top)
                sym.node(cv, x, bot)
                sym.component(cv, kind[e], x, top, x, bot, label=e, value=vals[e], label_side=1, color=COL[e])
        elif key == "tank":
            sym.wire(cv, 40, top, 330, top)
            sym.wire(cv, 40, bot, 330, bot)
            x = 170
            mid = (top + bot) / 2
            sym.node(cv, x, top)
            sym.node(cv, x, bot)
            sym.resistor(cv, x, top, x, mid, label="R", value=vals["R"], label_side=1, color=COL["R"])
            sym.inductor(cv, x, mid, x, bot, label="L", value=vals["L"], label_side=1, color=COL["L"])
            sym.capacitor(cv, 300, top, 300, bot, label="C", value=vals["C"], label_side=1, color=COL["C"])
            sym.node(cv, 300, top)
            sym.node(cv, 300, bot)
            cv.create_text(x - 14, mid, text=tr("coil", "bobină"), anchor="e", font=("Segoe UI", 8, "italic"), fill="#888")
        elif key == "r_lc":
            sym.wire(cv, 40, top, 70, top)
            sym.resistor(cv, 70, top, 170, top, label="R", value=vals["R"], color=COL["R"])
            sym.wire(cv, 170, top, 330, top)
            sym.wire(cv, 40, bot, 330, bot)
            sym.node(cv, 230, top)
            sym.node(cv, 230, bot)
            sym.inductor(cv, 230, top, 230, bot, label="L", value=vals["L"], label_side=1, color=COL["L"])
            sym.capacitor(cv, 320, top, 320, bot, label="C", value=vals["C"], label_side=1, color=COL["C"])
            sym.node(cv, 320, top)
            sym.node(cv, 320, bot)
        cv.create_text(410, 190, text=f"I = {eng(abs(self.I), 'A')} rms", anchor="e", font=("Consolas", 9, "bold"),
                       fill=COL["I"])


# ===========================================================================
class PFCorrectionPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        accent = ACCENT_C
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body
        note(body, t("pf.intro"), wrap=1000, pady=(12, 6))
        top = ttk.Frame(body, style="Card.TFrame")
        top.pack(fill="both", expand=True, padx=16, pady=(0, 12))
        top.columnconfigure(1, weight=1)
        left = ttk.Frame(top, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nw")
        right = ttk.Frame(top, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        self.form = ParamForm(left, [
            dict(key="v", label=t("pf.v"), default="230", unit="V", slider=(100, 690)),
            dict(key="f", label=t("pf.f"), default="50", unit="Hz", slider=(50, 60)),
            dict(key="p", label=t("pf.p"), default="5k", unit="W", slider=(100, 100e3, True)),
            dict(key="pf1", label=t("pf.pf1"), default="0.7", unit="", slider=(0.3, 1)),
            dict(key="pf2", label=t("pf.pf2"), default="0.95", unit="", slider=(0.5, 1)),
        ], self.update_all, label_width=26)
        self.form.pack(anchor="w")
        self.tiles = TileRow(left, [("c", t("pf.t.c")), ("qc", t("pf.t.qc")), ("i1", t("pf.t.i1")),
                                    ("i2", t("pf.t.i2")), ("s1", t("pf.t.s1")), ("s2", t("pf.t.s2")),
                                    ("save", t("pf.t.save")), ("loss", t("pf.t.loss"))], accent, per_row=2)
        self.tiles.pack(fill="x", pady=(10, 0))
        self.canvas = tk.Canvas(left, width=400, height=170, bg=sym.CANVAS_BG, highlightthickness=0)
        self.canvas.pack(anchor="w", pady=(10, 0))
        self.chart = MplChartFrame(right, figsize=(7.0, 4.8), with_toolbar=False)
        self.chart.pack(fill="both", expand=True)
        self.update_all()

    def update_all(self, *_):
        try:
            P = self.form.values()
        except Exception:
            return
        v, f, p = P["v"], P["f"], P["p"]
        pf1 = min(max(P["pf1"], 0.05), 1.0)
        pf2 = min(max(P["pf2"], 0.05), 1.0)
        phi1, phi2 = math.acos(pf1), math.acos(pf2)
        q1, q2 = p * math.tan(phi1), p * math.tan(phi2)
        qc = q1 - q2
        c = qc / (2 * math.pi * f * v * v) if qc > 0 else 0
        s1, s2 = p / pf1, p / pf2
        i1, i2 = s1 / v, s2 / v
        tl = self.tiles
        tl.set("c", eng(c, "F") if c > 0 else "—")
        tl.set("qc", eng(qc, "var"))
        tl.set("i1", eng(i1, "A"))
        tl.set("i2", eng(i2, "A"))
        tl.set("s1", eng(s1, "VA"))
        tl.set("s2", eng(s2, "VA"))
        tl.set("save", f"{(1 - i2 / i1) * 100:.0f} %")
        tl.set("loss", f"{(1 - (i2 / i1) ** 2) * 100:.0f} %")
        fig = self.chart.fig
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_facecolor(PLOT_BG)
        m = max(p, q1)
        ax.fill([0, p, p], [0, 0, q1], color="#c62828", alpha=0.06)
        ax.plot([0, p], [0, 0], color=COL["R"], lw=3)
        ax.plot([p, p], [0, q1], color=COL["L"], lw=3)
        ax.plot([0, p], [0, q1], color="#c62828", lw=2.5, label=f"S {t('pf.before')} = {eng(s1, 'VA')}")
        ax.plot([0, p], [0, q2], color="#2e9d44", lw=2.5, label=f"S {t('pf.after')} = {eng(s2, 'VA')}")
        ax.annotate("", xy=(p, q2), xytext=(p, q1),
                    arrowprops=dict(arrowstyle="-|>", color=COL["C"], lw=2.5, mutation_scale=16))
        ax.text(p * 1.02, (q1 + q2) / 2, f"Qc = −{eng(qc, 'var')}\n" + tr("(capacitor)", "(condensator)"), color=COL["C"], fontsize=9,
                va="center")
        ax.text(p / 2, -0.04 * m, f"P = {eng(p, 'W')}", ha="center", va="top", color=COL["R"], fontsize=9)
        ax.text(p * 0.42, q1 * 0.3, f"φ1 = {math.degrees(phi1):.1f}°", color="#c62828", fontsize=9)
        ax.text(p * 0.55, q2 * 0.5 - 0.02 * m, f"φ2 = {math.degrees(phi2):.1f}°", color="#2e9d44", fontsize=9)
        ax.set_xlim(-0.05 * m, p * 1.45)
        ax.set_ylim(-0.12 * m, max(q1, 0.2 * m) * 1.15)
        ax.set_aspect("equal", adjustable="box")
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ax.spines.values():
            s.set_visible(False)
        ax.legend(fontsize=9, loc="upper left")
        ax.set_title(t("pl.stri"), fontsize=10)
        fig.subplots_adjust(left=0.02, right=0.98, top=0.93, bottom=0.03)
        self.chart.redraw()
        cv = self.canvas
        cv.delete("all")
        top, bot = 40, 140
        sym.ac_source(cv, 40, 90)
        sym.wire(cv, 40, 74, 40, top, 330, top)
        sym.wire(cv, 40, 106, 40, bot, 330, bot)
        cv.create_text(60, 90, text=f"{eng(v, 'V')}\n{eng(f, 'Hz')}", anchor="w", font=("Segoe UI", 8), fill="#555")
        sym.node(cv, 200, top)
        sym.node(cv, 200, bot)
        sym.capacitor(cv, 200, top, 200, bot, label="C", value=eng(c, "F"), label_side=1, color=COL["C"])
        mid = (top + bot) / 2
        sym.resistor(cv, 320, top, 320, mid, label="R", label_side=1)
        sym.inductor(cv, 320, mid, 320, bot, label="L", label_side=1)
        cv.create_text(350, 160, text=tr("load ", "sarcină ") + f"{eng(p, 'W')}, PF {pf1:.2f}", anchor="e", font=("Segoe UI", 8),
                       fill="#555")
        cv.create_text(120, 25, text=f"I: {eng(i1, 'A')} → {eng(i2, 'A')}", font=("Consolas", 9, "bold"),
                       fill="#2e9d44")
