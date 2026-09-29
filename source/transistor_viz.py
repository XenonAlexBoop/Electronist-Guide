"""
transistor_viz.py - Junction Visualizer for BJT / MOSFET / JFET (N and P).

Layout
  * Cross-section: doped regions, depletion regions (with their fixed ion
    charges), inversion channel / pinch-off, and one animated particle
    stream per physical current path (electrons = filled blue dots,
    holes = open red rings). The number of particles in a stream grows
    with the logarithm of that current, so both nA leakage and amps of
    breakdown current stay visible.
  * Symbol: the real schematic symbol with the conventional current of
    every terminal (arrow direction + value).
  * Region map: BJT -> Vbe/Vbc bias plane (drag the dot); FETs -> ID-VDS
    output curve with the operating point.
  * Wide-range sliders (all four BJT regions + both breakdowns, MOSFET
    sub-threshold / reverse / body diode / avalanche / oxide stress, JFET
    gate conduction / reversed channel / breakdown) and one-click presets.
Everything shown comes from transistor_models - no hand-tuned visuals.
"""
import math
import time
import random
import tkinter as tk
from widgets import is_shown
from tkinter import ttk

import transistor_models as tm
import symbols as sym
from widgets import format_value, parse_value, FONT_BODY, FONT_H2, FONT_MONO, debounce, cap_width
from i18n import t

TICK_MS = 40
BG = "#fdfaf3"
N_FILL, P_FILL = "#bcd7f5", "#f6c6cf"
N_FILL_HEAVY, P_FILL_HEAVY = "#9cc3ef", "#f0a9b7"
DEP_FILL = "#f7f3e6"
METAL = "#8d8d8d"
OXIDE = "#f3dc86"
E_COLOR = "#1d4ed8"
H_COLOR = "#dc2626"
I_ARROW = "#d97706"
MAX_PARTICLES = 420


def _rate(i):
    """Particles per second for a current of magnitude i (A)."""
    i = abs(i)
    if i < 1e-10:
        return 0.0
    return min(48.0, 1.5 + 6.0 * math.log10(i / 1e-10))


def _fmt_i(i):
    if abs(i) < 1e-12:
        return "0 A"
    return format_value(float(f"{i:.3g}"), "A")


class _Poly:
    """Polyline path parameterised by 0..1 of its length."""

    def __init__(self, pts):
        self.pts = pts
        self.seg = []
        total = 0.0
        for (x1, y1), (x2, y2) in zip(pts, pts[1:]):
            d = math.hypot(x2 - x1, y2 - y1)
            self.seg.append(d)
            total += d
        self.length = max(total, 1.0)

    def at(self, p):
        target = p * self.length
        for ((x1, y1), (x2, y2)), d in zip(zip(self.pts, self.pts[1:]), self.seg):
            if target <= d or d == 0:
                f = 0 if d == 0 else target / d
                return x1 + (x2 - x1) * f, y1 + (y2 - y1) * f
            target -= d
        return self.pts[-1]


class _Flow:
    """One stream of carriers. path_fn(u) -> _Poly for a jitter u in [-1, 1]
    (or pos_fn(p, u) -> (x, y) for paths whose shape depends on position)."""

    def __init__(self, key, carrier, current, path_fn=None, pos_fn=None, length=300.0, speed=90.0, fade=False):
        self.key, self.carrier, self.current = key, carrier, current
        self.path_fn, self.pos_fn = path_fn, pos_fn
        self.length, self.speed, self.fade = length, speed, fade
        self.rate = _rate(current)


# ---------------------------------------------------------------------------
class PiecewiseSlider(ttk.Frame):
    """Slider whose travel is split into linear segments so that e.g. the
    0.4-0.9 V forward region of a junction gets as much room as -60..0 V."""

    def __init__(self, parent, label, unit, segments, value, command, accent):
        super().__init__(parent, style="Card.TFrame")
        self.segments = segments      # [(u, v), ...] u from 0 to 1, v increasing
        self.command = command
        self.unit = unit
        self._mute = False
        self.columnconfigure(1, weight=1)
        ttk.Label(self, text=label, font=FONT_BODY, style="CardBody.TLabel", width=26)\
            .grid(row=0, column=0, sticky="w")
        self.pos = tk.DoubleVar()
        self.scale = ttk.Scale(self, from_=0, to=1000, variable=self.pos, orient="horizontal",
                               command=self._on_scale)
        self.scale.grid(row=0, column=1, sticky="ew", padx=6)
        self.txt = tk.StringVar()
        e = ttk.Entry(self, textvariable=self.txt, width=8, font=FONT_MONO, foreground=accent)
        e.grid(row=0, column=2)
        e.bind("<Return>", self._on_entry)
        e.bind("<FocusOut>", self._on_entry)
        ttk.Label(self, text=unit, font=FONT_BODY, style="CardBody.TLabel").grid(row=0, column=3, padx=(3, 0))
        lo, hi = segments[0][1], segments[-1][1]
        ticks = ttk.Label(self, text=f"{lo:g} … {hi:g} {unit}", font=("Segoe UI", 7), foreground="#888",
                          style="CardBody.TLabel")
        ticks.grid(row=1, column=1, sticky="w", padx=6)
        self.value = value
        self.set(value, fire=False)

    def _u2v(self, u):
        s = self.segments
        for (u0, v0), (u1, v1) in zip(s, s[1:]):
            if u <= u1:
                return v0 + (v1 - v0) * (u - u0) / (u1 - u0 or 1)
        return s[-1][1]

    def _v2u(self, v):
        s = self.segments
        v = max(s[0][1], min(s[-1][1], v))
        for (u0, v0), (u1, v1) in zip(s, s[1:]):
            if v <= v1:
                return u0 + (u1 - u0) * (v - v0) / (v1 - v0 or 1)
        return 1.0

    def _on_scale(self, _):
        if self._mute:
            return
        v = self._u2v(self.pos.get() / 1000)
        span = abs(self.segments[-1][1] - self.segments[0][1])
        step = 0.01 if abs(v) < 2 else (0.05 if span < 40 else 0.1)
        v = round(v / step) * step
        self.value = v
        self.txt.set(f"{v:.2f}")
        self.command()

    def _on_entry(self, _=None):
        try:
            self.set(float(self.txt.get().replace(",", ".")))
        except ValueError:
            self.txt.set(f"{self.value:.2f}")

    def set(self, v, fire=True):
        lo, hi = self.segments[0][1], self.segments[-1][1]
        v = max(lo, min(hi, v))
        self.value = v
        self._mute = True
        self.pos.set(self._v2u(v) * 1000)
        self._mute = False
        self.txt.set(f"{v:.2f}")
        if fire:
            self.command()

    def get(self):
        return self.value


def _continuity_map(width_fn, n=160, min_w=0.12):
    """Current continuity: the same number of carriers per second must pass
    every cross-section, so where the conducting path is narrow they move
    faster (v ~ 1/width). Returns f(p) -> x fraction (0..1) such that a
    particle advancing p at constant rate spends time proportional to the
    local width at each x."""
    ws = [max(min_w, width_fn(i / n)) for i in range(n + 1)]
    cum = [0.0]
    for a, b in zip(ws, ws[1:]):
        cum.append(cum[-1] + (a + b) / 2)
    tot = cum[-1] or 1.0
    cum = [c / tot for c in cum]

    def f(p):
        p = max(0.0, min(1.0, p))
        lo, hi = 0, n
        while hi - lo > 1:
            mid = (lo + hi) // 2
            if cum[mid] <= p:
                lo = mid
            else:
                hi = mid
        span = cum[hi] - cum[lo] or 1e-9
        return (lo + (p - cum[lo]) / span) / n
    return f


def _mirror(segments):
    return [(1 - u, -v) for u, v in reversed(segments)]


# ---------------------------------------------------------------------------
class JunctionVisualizer(ttk.Frame):
    def __init__(self, parent, family, polarity, accent):
        super().__init__(parent, style="Card.TFrame")
        self.family = family
        self.ntype = polarity.upper().startswith("N")
        self.accent = accent
        self.sgn = 1.0 if self.ntype else -1.0
        self.particles = []
        self.flows = {}
        self._after = None
        self._rng = random.Random(7)
        self._state = None
        self._geo = None
        self.columnconfigure(0, weight=1)

        ttk.Label(self, text=t(f"jv.intro.{family}"), font=FONT_BODY, style="CardBody.TLabel", wraplength=900,
                  justify="left").grid(row=0, column=0, sticky="w", padx=16, pady=(10, 4))

        # presets
        pre = ttk.Frame(self, style="Card.TFrame")
        pre.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 6))
        ttk.Label(pre, text=t("jv.presets"), font=("Segoe UI", 9, "bold"), style="CardBody.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=(0, 6))
        for i, (key, a, b) in enumerate(self._presets()):
            ttk.Button(pre, text=t(f"jv.region.{family}.{key}"), style="Small.TButton",
                       command=lambda a=a, b=b: self._apply_preset(a, b))\
                .grid(row=i // 4, column=1 + i % 4, sticky="w", padx=2, pady=2)

        # drawings
        row = ttk.Frame(self, style="Card.TFrame")
        row.grid(row=2, column=0, sticky="ew", padx=16)
        row.columnconfigure(0, weight=3)
        row.columnconfigure(1, weight=1)
        self.cv = tk.Canvas(row, height=330, width=560, bg=BG, highlightthickness=0)
        self.cv.grid(row=0, column=0, sticky="ew")
        self.sv = tk.Canvas(row, height=330, width=230, bg=BG, highlightthickness=0)
        self.sv.grid(row=0, column=1, sticky="ew", padx=(8, 0))
        self.cv.bind("<Configure>", debounce(self.cv, lambda *a: self._rebuild(), 100))
        self.sv.bind("<Configure>", debounce(self.sv, lambda *a: self._draw_symbol(), 100))

        legend = ttk.Label(self, text=t("jv.legend"), font=("Segoe UI", 8), foreground="#666",
                           style="CardBody.TLabel", wraplength=780, justify="left")
        legend.grid(row=3, column=0, sticky="w", padx=16, pady=(2, 4))

        # map + stats
        mid = ttk.Frame(self, style="Card.TFrame")
        mid.grid(row=4, column=0, sticky="ew", padx=16, pady=(2, 4))
        mid.columnconfigure(1, weight=1)
        self.mv = tk.Canvas(mid, width=330, height=230, bg=BG, highlightthickness=0)
        self.mv.grid(row=0, column=0, sticky="nw")
        self.mv.bind("<Button-1>", self._on_map_click)
        self.mv.bind("<B1-Motion>", self._on_map_click)
        self.cvc = None
        stats = ttk.Frame(mid, style="Card.TFrame")
        if family == "bjt":
            stats.grid(row=0, column=1, sticky="nsew", padx=(12, 0))
        else:
            # FETs: draggable VGS/VDS region map + the ID(VDS) output curve beside it
            self.cvc = tk.Canvas(mid, width=330, height=230, bg=BG, highlightthickness=0)
            self.cvc.grid(row=0, column=1, sticky="nw", padx=(10, 0))
            self.cvc.bind("<Button-1>", self._on_curve_click)
            self.cvc.bind("<B1-Motion>", self._on_curve_click)
            stats.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(6, 0))
            self._fet_map_cache = None
        stats.columnconfigure(0, weight=1)
        self.region_var = tk.StringVar()
        self.region_lbl = ttk.Label(stats, textvariable=self.region_var, font=("Segoe UI", 12, "bold"),
                                    style="CardFormula.TLabel")
        self.region_lbl.grid(row=0, column=0, sticky="w")
        self.explain_var = tk.StringVar()
        self.explain_lbl = ttk.Label(stats, textvariable=self.explain_var, font=FONT_BODY,
                                     style="CardBody.TLabel", wraplength=420, justify="left")
        self.explain_lbl.grid(row=1, column=0, sticky="w", pady=(4, 6))
        stats.bind("<Configure>", lambda e: self.explain_lbl.configure(wraplength=max(200, e.width - 10)))
        self.numbers_var = tk.StringVar()
        ttk.Label(stats, textvariable=self.numbers_var, font=("Consolas", 10, "bold"), foreground=accent,
                  style="CardFormula.TLabel", justify="left").grid(row=2, column=0, sticky="w")

        # controls
        ctl = ttk.Frame(self, style="Card.TFrame")
        ctl.grid(row=5, column=0, sticky="ew", padx=16, pady=(6, 14))
        ctl.columnconfigure(0, weight=1)
        self._build_controls(ctl)

        self.bind("<Destroy>", self._on_destroy, add="+")
        self._do_update()
        self._tick()

    # ------------------------------------------------------------------
    def _presets(self):
        s = self.sgn
        if self.family == "bjt":
            lst = [("active", 0.70, -4.3), ("saturation", 0.75, 0.65), ("cutoff", 0.0, -5.0),
                   ("reverse", -3.0, 0.70), ("weak", 0.45, -5.0), ("eb_breakdown", -8.0, -1.0),
                   ("avalanche", 0.68, -49.0)]
        elif self.family == "mosfet":
            lst = [("saturation", 4.0, 10.0), ("triode", 8.0, 1.0), ("cutoff", 0.0, 10.0),
                   ("subthreshold", 1.8, 5.0), ("reverse_channel", 6.0, -0.5), ("body_diode", 0.0, -1.0),
                   ("avalanche", 0.0, 45.0), ("oxide", 22.0, 1.0)]
        else:
            lst = [("ohmic", 0.0, 0.8), ("saturation", -1.0, 10.0), ("cutoff", -5.0, 10.0),
                   ("gate_forward", 1.0, 5.0), ("reversed", -1.0, -2.0), ("breakdown", -3.0, 40.0)]
        return [(k, s * a, s * b) for k, a, b in lst]

    def _apply_preset(self, a, b):
        if self.family == "bjt":
            self.mode_var.set("vbc")
            self._on_mode()
            self.s1.set(a, fire=False)
            self.s2.set(b)
        else:
            if self.family == "mosfet" and abs(a) > 20:
                pass
            self.s1.set(a, fire=False)
            self.s2.set(b)

    def _build_controls(self, ctl):
        s = self.sgn
        fam = self.family
        seg = lambda lst: lst if self.ntype else _mirror(lst)  # noqa: E731
        if fam == "bjt":
            v1 = "VBE" if self.ntype else "VBE"
            self.s1 = PiecewiseSlider(ctl, t("jv.vbe"), "V", seg([(0, -9), (0.3, -1), (0.5, 0.4), (1, 0.9)]),
                                      s * 0.70, self._update_state, self.accent)
            self.s1.grid(row=0, column=0, sticky="ew", pady=2)
            mrow = ttk.Frame(ctl, style="Card.TFrame")
            mrow.grid(row=1, column=0, sticky="w", pady=(4, 0))
            ttk.Label(mrow, text=t("jv.second_control"), font=("Segoe UI", 9), style="CardBody.TLabel")\
                .pack(side="left")
            self.mode_var = tk.StringVar(value="vce")
            for val, key in (("vce", "jv.mode_vce"), ("vbc", "jv.mode_vbc")):
                ttk.Radiobutton(mrow, text=t(key), value=val, variable=self.mode_var,
                                command=self._on_mode).pack(side="left", padx=6)
            self.s2_vce = PiecewiseSlider(ctl, t("jv.vce"), "V", seg([(0, -10), (0.2, 0), (0.45, 1), (1, 55)]),
                                          s * 5.0, self._update_state, self.accent)
            self.s2_vbc = PiecewiseSlider(ctl, t("jv.vbc"), "V", seg([(0, -60), (0.35, -5), (0.55, 0.3), (1, 0.9)]),
                                          s * -4.3, self._update_state, self.accent)
            self.s2 = self.s2_vce
            self.s2.grid(row=2, column=0, sticky="ew", pady=2)
            pr = ttk.Frame(ctl, style="Card.TFrame")
            pr.grid(row=3, column=0, sticky="w", pady=(6, 0))
            ttk.Label(pr, text="βF =", font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
            self.beta_var = tk.StringVar(value="150")
            e = ttk.Entry(pr, textvariable=self.beta_var, width=6)
            e.pack(side="left", padx=(4, 12))
            e.bind("<KeyRelease>", lambda ev: self._update_state())
            self.note_var = tk.StringVar()
            ttk.Label(ctl, textvariable=self.note_var, font=("Segoe UI", 8), foreground="#a15c00",
                      style="CardBody.TLabel", wraplength=800, justify="left").grid(row=4, column=0, sticky="w")
        elif fam == "mosfet":
            self.s1 = PiecewiseSlider(ctl, t("jv.vgs"), "V", seg([(0, -25), (0.15, -5), (0.8, 10), (1, 25)]),
                                      s * 4.0, self._update_state, self.accent)
            self.s2 = PiecewiseSlider(ctl, t("jv.vds"), "V", seg([(0, -2), (0.2, 0), (0.45, 2), (0.8, 30), (1, 50)]),
                                      s * 10.0, self._update_state, self.accent)
            self.s1.grid(row=0, column=0, sticky="ew", pady=2)
            self.s2.grid(row=1, column=0, sticky="ew", pady=2)
            pr = ttk.Frame(ctl, style="Card.TFrame")
            pr.grid(row=2, column=0, sticky="w", pady=(6, 0))
            ttk.Label(pr, text=t("jv.mos_type"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
            self._mos_modes = [t("jv.enhancement"), t("jv.depletion")]
            self.mos_mode = tk.StringVar(value=self._mos_modes[0])
            cb = ttk.Combobox(pr, textvariable=self.mos_mode, values=self._mos_modes, state="readonly", width=13)
            cb.pack(side="left", padx=(4, 12))
            cb.bind("<<ComboboxSelected>>", lambda e: self._on_mos_mode())
            ttk.Label(pr, text="|Vth| =", font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
            self.vth_var = tk.StringVar(value="2")
            e = ttk.Entry(pr, textvariable=self.vth_var, width=5)
            e.pack(side="left", padx=(4, 12))
            e.bind("<KeyRelease>", lambda ev: self._update_state())
            ttk.Label(pr, text="K =", font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
            self.k_var = tk.StringVar(value="0.1")
            e = ttk.Entry(pr, textvariable=self.k_var, width=6)
            e.pack(side="left", padx=(4, 2))
            e.bind("<KeyRelease>", lambda ev: self._update_state())
            ttk.Label(pr, text="A/V²", font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
            self.note_var = tk.StringVar()
            ttk.Label(ctl, textvariable=self.note_var, font=("Segoe UI", 8), foreground="#a15c00",
                      style="CardBody.TLabel", wraplength=800, justify="left").grid(row=3, column=0, sticky="w")
        else:
            self.s1 = PiecewiseSlider(ctl, t("jv.vgs"), "V", seg([(0, -8), (0.75, 0), (1, 1.5)]),
                                      s * -1.0, self._update_state, self.accent)
            self.s2 = PiecewiseSlider(ctl, t("jv.vds"), "V", seg([(0, -10), (0.2, 0), (0.45, 3), (0.8, 30), (1, 45)]),
                                      s * 10.0, self._update_state, self.accent)
            self.s1.grid(row=0, column=0, sticky="ew", pady=2)
            self.s2.grid(row=1, column=0, sticky="ew", pady=2)
            pr = ttk.Frame(ctl, style="Card.TFrame")
            pr.grid(row=2, column=0, sticky="w", pady=(6, 0))
            ttk.Label(pr, text="IDSS =", font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
            self.idss_var = tk.StringVar(value="10m")
            e = ttk.Entry(pr, textvariable=self.idss_var, width=6)
            e.pack(side="left", padx=(4, 2))
            e.bind("<KeyRelease>", lambda ev: self._update_state())
            ttk.Label(pr, text="A     |Vp| =", font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
            self.vp_var = tk.StringVar(value="4")
            e = ttk.Entry(pr, textvariable=self.vp_var, width=5)
            e.pack(side="left", padx=(4, 2))
            e.bind("<KeyRelease>", lambda ev: self._update_state())
            ttk.Label(pr, text="V", font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
            self.note_var = tk.StringVar()
            ttk.Label(ctl, textvariable=self.note_var, font=("Segoe UI", 8), foreground="#a15c00",
                      style="CardBody.TLabel", wraplength=800, justify="left").grid(row=3, column=0, sticky="w")

    def _on_mode(self):
        vbe = self.s1.get()
        if self.mode_var.get() == "vbc":
            new, old = self.s2_vbc, self.s2_vce
            new.set(vbe - old.get(), fire=False)
        else:
            new, old = self.s2_vce, self.s2_vbc
            new.set(vbe - old.get(), fire=False)
        old.grid_remove()
        new.grid(row=2, column=0, sticky="ew", pady=2)
        self.s2 = new
        self._update_state()

    def _on_mos_mode(self):
        self._update_state()

    # ------------------------------------------------------------------
    def _params(self):
        try:
            if self.family == "bjt":
                return {"beta_f": max(1.0, float(self.beta_var.get()))}
            if self.family == "mosfet":
                vth = abs(float(self.vth_var.get().replace(",", ".")))
                if self.mos_mode.get() == self._mos_modes[1]:
                    vth = -vth
                # model takes the N-equivalent threshold magnitude sign; P handled by sgn inside
                return {"vth": vth * self.sgn, "k": max(1e-6, parse_value(self.k_var.get()))}
            return {"idss": max(1e-9, parse_value(self.idss_var.get())),
                    "vp": -max(0.1, abs(float(self.vp_var.get().replace(",", "."))))}
        except Exception:
            return {}

    def _compute(self, a, b):
        p = self._params()
        if self.family == "bjt":
            return tm.bjt_state(a, b, npn=self.ntype, **p)
        if self.family == "mosfet":
            return tm.mosfet_state(a, b, nch=self.ntype, **p)
        return tm.jfet_state(a, b, nch=self.ntype, **p)

    def _bias(self):
        """(control voltage, second voltage) as the model wants them."""
        a = self.s1.get()
        if self.family == "bjt":
            if self.s2 is self.s2_vce:
                vbc = a - self.s2.get()
                lim = 0.9
                clipped = False
                if self.sgn * vbc > lim:
                    vbc = self.sgn * lim
                    clipped = True
                self._clip_note = clipped
                return a, vbc
            self._clip_note = False
            return a, self.s2.get()
        return a, self.s2.get()

    def _update_state(self):
        """Slider/entry callback: coalesce bursts of changes (dragging a slider
        fires dozens of events) into one redraw every ~50 ms."""
        if not hasattr(self, "s2"):
            return
        if getattr(self, "_pending", None) is None:
            self._pending = self.after(50, self._do_update)

    def _do_update(self):
        self._pending = None
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        a, b = self._bias()
        st = self._compute(a, b)
        self._state = st
        self._a, self._b = a, b
        self._update_text(st)
        self._rebuild()
        self._draw_symbol()
        self._draw_map()

    # ------------------------------------------------------------------
    def _update_text(self, st):
        fam = self.family
        region = st["region"]
        self.region_var.set(t("junction.operating_region") + ":  " + t(f"jv.region.{fam}.{region}"))
        colors = {"active": "#1f6a5f", "saturation": "#b3691d", "triode": "#1f6a5f", "ohmic": "#1f6a5f",
                  "cutoff": "#777", "reverse": "#6a4c93", "reverse_channel": "#6a4c93", "reversed": "#6a4c93",
                  "weak": "#777", "subthreshold": "#777", "body_diode": "#c0392b", "gate_forward": "#c0392b",
                  "eb_breakdown": "#c0392b", "avalanche": "#c0392b", "breakdown": "#c0392b"}
        self.region_lbl.configure(foreground=colors.get(region, "#333"))
        ptype = "" if self.ntype else "p."
        txt = t(f"jv.explain.{fam}.{region}")
        if not self.ntype:
            txt += "\n" + t("jv.ptype_note")
        self.explain_var.set(txt)
        a, b = self._a, self._b
        note = ""
        if fam == "bjt":
            vce = a - b
            p_w = st["ic"] * vce + st["ib"] * a
            beta = st["beta_eff"]
            bt = f"{beta:.0f}" if math.isfinite(beta) and abs(beta) < 1e5 else "—"
            self.numbers_var.set(
                f"VBE = {a:+.2f} V   VBC = {b:+.2f} V   VCE = {vce:+.2f} V\n"
                f"IB = {_fmt_i(st['ib'])}   IC = {_fmt_i(st['ic'])}   IE = {_fmt_i(st['ie'])}\n"
                f"IC/IB = {bt}      P ≈ {format_value(float(f'{p_w:.3g}'), 'W')}")
            if getattr(self, "_clip_note", False):
                note = t("jv.clip_note")
        elif fam == "mosfet":
            p_w = st["id"] * b
            self.numbers_var.set(
                f"VGS = {a:+.2f} V   VDS = {b:+.2f} V   VGD = {a - b:+.2f} V\n"
                f"ID = {_fmt_i(st['id'])}   IG = 0 A (oxide)\n"
                f"Vov = VGS − Vth = {self.sgn * st['vov']:+.2f} V      P ≈ {format_value(float(f'{p_w:.3g}'), 'W')}")
            if st["oxide_stress"]:
                note = t("jv.oxide_note")
        else:
            p_w = st["id"] * b + st["ig"] * a
            self.numbers_var.set(
                f"VGS = {a:+.2f} V   VDS = {b:+.2f} V   VGD = {a - b:+.2f} V\n"
                f"ID = {_fmt_i(st['id'])}   IG = {_fmt_i(st['ig'])}   IS = {_fmt_i(st['is'])}\n"
                f"P ≈ {format_value(float(f'{p_w:.3g}'), 'W')}")
        self.note_var.set(note)

    # ------------------------------------------------------------------
    # Cross-section geometry + flows
    # ------------------------------------------------------------------
    def _rebuild(self):
        if self._state is None:
            return
        c = self.cv
        W = cap_width(c, max(420, c.winfo_width() if c.winfo_width() > 50 else 560), 900)
        H = 330
        c.delete("static")
        c.delete("spark")
        getattr(self, f"_build_{self.family}")(c, W, H, self._state)
        # Share one particle budget between the streams in proportion to their
        # currents, so ratios such as IC : IB = beta stay visible. The budget
        # itself grows with log(current) so nA and A both remain readable.
        if self.flows:
            imax = max(abs(f.current) for f in self.flows.values())
            budget = _rate(imax)
            for f in self.flows.values():
                share = abs(f.current) / imax if imax > 0 else 0
                f.rate = max(1.2 if abs(f.current) > 1e-10 else 0.0, budget * share)
        # Every stream (and its path) may have changed: erase ALL old dots from
        # the canvas and re-seed the new streams in their steady state, so the
        # picture always matches the present bias (no frozen leftovers).
        self._reset_particles()

    def _colors(self):
        """(majority fill of 'N' regions, of 'P' regions, heavy variants) for this polarity."""
        return N_FILL, P_FILL, N_FILL_HEAVY, P_FILL_HEAVY

    def _carriers(self, c_n):
        """Map an N-device carrier ('e' or 'h') to the real carrier."""
        if self.ntype:
            return c_n
        return "h" if c_n == "e" else "e"

    def _region_fill(self, doping_n):
        """doping_n: 'N', 'N+', 'P', 'P+' as seen in the N-type device."""
        if not self.ntype:
            doping_n = doping_n.replace("N", "x").replace("P", "N").replace("x", "P")
        return {"N": N_FILL, "N+": N_FILL_HEAVY, "P": P_FILL, "P+": P_FILL_HEAVY}[doping_n], doping_n

    def _static_dots(self, c, x0, y0, x1, y1, doping, n, seed):
        rng = random.Random(seed)
        is_n = doping.startswith("N")
        for _ in range(n):
            x = rng.uniform(x0 + 5, x1 - 5)
            y = rng.uniform(y0 + 5, y1 - 5)
            if is_n:
                c.create_oval(x - 2, y - 2, x + 2, y + 2, fill="#6b8fd6", outline="", tags="static")
            else:
                c.create_oval(x - 2.2, y - 2.2, x + 2.2, y + 2.2, outline="#e07b87", width=1.2, tags="static")

    def _ions(self, c, x0, y0, x1, y1, doping, seed, step=14):
        """Fixed ionised dopants in a depletion region: + on the N side, − on the P side."""
        if x1 - x0 < 4 or y1 - y0 < 4:
            return
        is_n = doping.startswith("N")
        rng = random.Random(seed)
        y = y0 + step / 2
        while y < y1:
            x = x0 + rng.uniform(2, step)
            while x < x1 - 2:
                c.create_text(x, y, text="+" if is_n else "−", fill="#7a7a7a",
                              font=("Segoe UI", 8, "bold"), tags="static")
                x += step
            y += step

    def _terminal(self, c, x, y_from, y_to, label, anchor="s"):
        c.create_line(x, y_from, x, y_to, fill=sym.SYM_COLOR, width=2, tags="static")
        c.create_oval(x - 4, y_to - 4, x + 4, y_to + 4, fill="white", outline=sym.SYM_COLOR, width=2, tags="static")
        dy = -8 if anchor == "s" else 8
        c.create_text(x, y_to + dy, text=label, anchor=anchor, font=("Segoe UI", 11, "bold"),
                      fill=sym.SYM_COLOR, tags="static")

    def _spark(self, c, x, y, spread):
        for _ in range(6):
            x0 = x + self._rng.uniform(-spread / 3, spread / 3)
            y0 = y + self._rng.uniform(-spread, spread)
            pts = [x0, y0]
            for _ in range(3):
                x0 += self._rng.uniform(-6, 6)
                y0 += self._rng.uniform(-8, 8)
                pts += [x0, y0]
            c.create_line(*pts, fill="#f59e0b", width=2, tags="spark")

    # ---------------- BJT ----------------
    def _build_bjt(self, c, W, H, st):
        x0, x1 = 30, W - 30
        y0, y1 = 95, H - 55
        wd = x1 - x0
        xe = x0 + 0.34 * wd
        xb = xe + 0.17 * wd
        ym = (y0 + y1) / 2
        amp = (y1 - y0) * 0.36
        # fixed doped regions
        regions = [("N+", x0, xe, "jv.bjt.emitter"), ("P", xe, xb, "jv.bjt.base"), ("N", xb, x1, "jv.bjt.collector")]
        # depletion widths
        w_eb = min(90, 22 * st["dep_eb"])
        w_cb = min(0.8 * (x1 - xb), 20 * min(st["dep_cb"], 8))
        eb_l, eb_r = xe - 0.25 * w_eb, xe + 0.75 * w_eb
        cb_l, cb_r = xb - 0.3 * w_cb, xb + 0.7 * w_cb
        eb_r = min(eb_r, xb - 4)
        cb_l = max(cb_l, eb_r + 2)
        fills = []
        for dop, a, b, key in regions:
            fill, real = self._region_fill(dop)
            fills.append(real)
            c.create_rectangle(a, y0, b, y1, fill=fill, outline="", tags="static")
            c.create_text((a + b) / 2, y1 - 12, text=f"{real} {t(key)}", font=("Segoe UI", 9, "bold"),
                          fill="#333", tags="static")
        # majority carriers in neutral parts
        self._static_dots(c, x0, y0, eb_l, y1 - 24, fills[0], 26, 1)
        self._static_dots(c, eb_r, y0, cb_l, y1 - 24, fills[1], 10, 2)
        self._static_dots(c, cb_r, y0, x1, y1 - 24, fills[2], 26, 3)
        # depletion regions with fixed ions
        for (l, r, jx, left_dop, right_dop, seed) in ((eb_l, eb_r, xe, fills[0], fills[1], 4),
                                                      (cb_l, cb_r, xb, fills[1], fills[2], 5)):
            c.create_rectangle(l, y0, r, y1 - 24, fill=DEP_FILL, outline="#b9ae8a", dash=(3, 2), tags="static")
            self._ions(c, l, y0, jx, y1 - 24, left_dop, seed)
            self._ions(c, jx, y0, r, y1 - 24, right_dop, seed + 10)
            c.create_line(jx, y0, jx, y1, fill="#555", dash=(2, 3), tags="static")
        c.create_rectangle(x0, y0, x1, y1, outline="#333", width=2, tags="static")
        # contacts + terminals
        xE, xB, xC = (x0 + eb_l) / 2, (eb_r + cb_l) / 2, (cb_r + x1) / 2
        xB = min(max(xB, xe + 8), xb - 8)
        for x, lab in ((xE, "E"), (xB, "B"), (xC, "C")):
            c.create_rectangle(x - 12, y0 - 7, x + 12, y0, fill=METAL, outline="#555", tags="static")
            self._terminal(c, x, y0 - 7, 35, lab)
        # junction bias labels
        def jb(v):
            return t("jv.forward") if v > 0.3 else (t("jv.reverse") if v < -0.05 else t("jv.zero_bias"))
        c.create_text(xe, y0 - 18, text=jb(st["ve"]), font=("Segoe UI", 8), fill="#555", tags="static")
        c.create_text(xb, y0 - 18, text=jb(st["vc"]), font=("Segoe UI", 8), fill="#555", tags="static")
        self._geo = {"eb": (xe, ym, y1 - y0), "cb": (xb, ym, y1 - y0)}

        flows = {}
        E, Hh = self._carriers("e"), self._carriers("h")
        tr = st["transport"]

        def mk(pts_fn):
            return lambda u: _Poly(pts_fn(u))
        if abs(tr) > 0:
            fwd = tr > 0
            def f(u, fwd=fwd):
                pts = [(xE + u * 10, y0), (x0 + 0.35 * (xe - x0) + u * 12, ym + u * amp),
                       (xC - 0.2 * (x1 - xC) + u * 12, ym + u * amp), (xC + u * 10, y0)]
                return pts if fwd else list(reversed(pts))
            flows["tr"] = _Flow("tr", E, tr, mk(f), speed=110)
        if st["ib_f"] > 0:
            flows["ibf"] = _Flow("ibf", Hh, st["ib_f"],
                                 mk(lambda u: [(xB + u * 6, y0), (xB + u * 8, ym + u * amp * 0.6), (xE + 10 + u * 25, ym + u * amp)]),
                                 speed=70, fade=True)
        if st["ib_r"] > 0:
            flows["ibr"] = _Flow("ibr", Hh, st["ib_r"],
                                 mk(lambda u: [(xB + u * 6, y0), (xB + u * 8, ym + u * amp * 0.6), (min(x1 - 20, cb_r + 40 + u * 20), ym + u * amp)]),
                                 speed=70, fade=True)
        if st["eb_bd"] > 0:
            flows["ebbd"] = _Flow("ebbd", E, st["eb_bd"],
                                  mk(lambda u: [(xB, y0), (xB, ym + u * amp * 0.4), (xE, ym + u * amp * 0.4), (xE, y0)]),
                                  speed=120)
            self._spark(c, xe, ym, amp)
        if st["aval"] > 1e-9:
            flows["av_e"] = _Flow("av_e", E, st["aval"], mk(lambda u: [(xb + 6, ym + u * amp), (xC, ym + u * amp), (xC, y0)]),
                                  speed=120)
            flows["av_h"] = _Flow("av_h", Hh, st["aval"], mk(lambda u: [(xb - 4, ym + u * amp), (xB, ym + u * amp * 0.5), (xB, y0)]),
                                  speed=90)
            if st["aval"] > 1e-5:
                self._spark(c, xb + 0.3 * w_cb, ym, amp)
        self.flows = flows

    # ---------------- MOSFET ----------------
    def _build_mosfet(self, c, W, H, st):
        x0, x1 = 30, W - 30
        ys = 125            # silicon surface
        y1 = H - 40
        wd = x1 - x0
        sw_r = x0 + 0.27 * wd
        dw_l = x1 - 0.27 * wd
        well_bot = ys + 62
        sub_fill, sub_dop = self._region_fill("P")
        well_fill, well_dop = self._region_fill("N+")
        # depletion around the drain well and under the gate
        dep_d = min(55, 12 * min(st["dep_drain"], 6))
        vg = st["vg"]
        vth_n = st["vg"] - st["vov"]
        dep_gate = 0.0
        if vg > 0:
            dep_gate = min(34, 10 + 14 * math.sqrt(max(0.0, min(vg, max(vth_n, 0.2)))))
        c.create_rectangle(x0, ys, x1, y1, fill=sub_fill, outline="", tags="static")
        self._static_dots(c, x0, well_bot + 20, x1, y1 - 16, sub_dop, 26, 11)
        # drain depletion (around well)
        c.create_rectangle(dw_l - dep_d, ys, x1, well_bot + dep_d, fill=DEP_FILL, outline="#b9ae8a",
                           dash=(3, 2), tags="static")
        self._ions(c, dw_l - dep_d, ys + 4, dw_l, well_bot + dep_d, sub_dop, 12)
        c.create_rectangle(x0, ys, sw_r + 10, well_bot + 10, fill=DEP_FILL, outline="#b9ae8a", dash=(3, 2),
                           tags="static")
        if dep_gate > 0:
            c.create_rectangle(sw_r, ys, dw_l - dep_d, ys + dep_gate, fill=DEP_FILL, outline="#b9ae8a",
                               dash=(3, 2), tags="static")
            self._ions(c, sw_r + 10, ys + 10, dw_l - dep_d, ys + dep_gate, sub_dop, 13)
        # wells
        c.create_rectangle(x0, ys, sw_r, well_bot, fill=well_fill, outline="#555", tags="static")
        c.create_rectangle(dw_l, ys, x1, well_bot, fill=well_fill, outline="#555", tags="static")
        self._static_dots(c, x0, ys, sw_r, well_bot, well_dop, 14, 14)
        self._static_dots(c, dw_l, ys, x1, well_bot, well_dop, 14, 15)
        c.create_text((x0 + sw_r) / 2, well_bot - 10, text=f"{well_dop} {t('jv.mos.source')}", font=("Segoe UI", 8, "bold"),
                      fill="#333", tags="static")
        c.create_text((dw_l + x1) / 2, well_bot - 10, text=f"{well_dop} {t('jv.mos.drain')}", font=("Segoe UI", 8, "bold"),
                      fill="#333", tags="static")
        c.create_text((x0 + x1) / 2, y1 - 10, text=f"{sub_dop} {t('jv.mos.body')}", font=("Segoe UI", 9, "bold"),
                      fill="#333", tags="static")
        # accumulation (gate below 0 for N)
        if vg < -0.5:
            n = min(14, int(2 + abs(vg) * 1.2))
            for i in range(n):
                x = sw_r + 10 + i * (dw_l - sw_r - 20) / max(1, n - 1)
                self._carrier_static(c, x, ys + 5, self._carriers("h"))
        # inversion channel
        q_s, q_d = st["q_s"], st["q_d"]
        qref = max(4.0, q_s, q_d)
        tmax = 22.0

        def thick(frac):
            # gradual-channel approximation: q(x)^2 varies linearly along the channel
            q2 = q_s * q_s + (q_d * q_d - q_s * q_s) * frac
            return tmax * math.sqrt(max(0.0, q2)) / qref

        ch_pts_top, ch_pts_bot = [], []
        n = 30
        for i in range(n + 1):
            f = i / n
            x = sw_r + (dw_l - sw_r) * f
            ch_pts_top.append((x, ys))
            ch_pts_bot.append((x, ys + thick(f)))
        if q_s > 0 or q_d > 0:
            poly = []
            for p in ch_pts_top + list(reversed(ch_pts_bot)):
                poly += p
            ch_fill, _ = self._region_fill("N+")
            c.create_polygon(*poly, fill=ch_fill, outline="#3b6fc4" if self.ntype else "#c0506a", tags="static")
            label = t("jv.mos.channel") if min(q_s, q_d) > 0 else t("jv.mos.pinched")
            c.create_text((sw_r + dw_l) / 2, ys + max(thick(0.5), 4) + 10, text=label, font=("Segoe UI", 8),
                          fill="#333", tags="static")
        # oxide and gate
        c.create_rectangle(sw_r - 8, ys - 9, dw_l + 8, ys, fill=OXIDE, outline="#b89a2c", tags="static")
        gate_col = "#e57373" if st["oxide_stress"] else METAL
        c.create_rectangle(sw_r - 8, ys - 30, dw_l + 8, ys - 9, fill=gate_col, outline="#555", tags="static")
        c.create_text(dw_l + 12, ys - 5, text=t("jv.mos.oxide"), anchor="w", font=("Segoe UI", 7), fill="#7a6414",
                      tags="static")
        # gate charges
        ng = min(10, int(abs(vg) * 1.1))
        for i in range(ng):
            x = sw_r + (i + 0.5) * (dw_l - sw_r) / max(ng, 1)
            c.create_text(x, ys - 19, text="+" if vg > 0 else "−", font=("Segoe UI", 10, "bold"),
                          fill="#8b1a1a" if (vg > 0) == self.ntype else "#1a3d8b", tags="static")
        if st["oxide_stress"]:
            self._spark(c, (sw_r + dw_l) / 2, ys - 5, 6)
        # terminals
        xS, xD, xG = (x0 + sw_r) / 2, (dw_l + x1) / 2, (sw_r + dw_l) / 2
        for x, top, lab in ((xS, ys, "S"), (xD, ys, "D"), (xG, ys - 30, "G")):
            c.create_rectangle(x - 12, top - 7, x + 12, top, fill=METAL, outline="#555", tags="static")
            self._terminal(c, x, top - 7, 35 if lab != "G" else 45, lab)
        # body contact tied to source
        xBd = x0 + 50
        c.create_rectangle(xBd - 12, y1, xBd + 12, y1 + 6, fill=METAL, outline="#555", tags="static")
        c.create_line(xBd, y1 + 6, xBd, H - 8, x0 - 18, H - 8, x0 - 18, 60, xS, 60, fill="#777", width=1.5,
                      dash=(4, 2), tags="static")
        c.create_text(xBd + 16, y1 + 12, text=t("jv.mos.body_tied"), anchor="w", font=("Segoe UI", 7),
                      fill="#555", tags="static")

        flows = {}
        E, Hh = self._carriers("e"), self._carriers("h")
        ich = st["ich"]
        if abs(ich) > 0:
            chmap = _continuity_map(lambda fr: max(2.0, thick(fr)) / tmax)

            def pos(p, u, fwd=ich > 0):
                # source contact -> down into well -> along the channel -> drain well -> contact
                pts_x = [xS, xS, sw_r, dw_l, xD, xD]
                if not fwd:
                    p = 1 - p
                seg = p * 5
                i = min(4, int(seg))
                f = seg - i
                cy_ch = lambda fr: ys + max(2.0, thick(fr)) * (0.5 + 0.35 * u)  # noqa: E731
                ys_pts = [ys - 7, cy_ch(0), cy_ch(0), cy_ch(1), cy_ch(1), ys - 7]
                if i == 2:  # along the channel: follow its local thickness, faster where it is thin
                    f = chmap(f)
                    x = sw_r + (dw_l - sw_r) * f
                    return x, cy_ch(f)
                return (pts_x[i] + (pts_x[i + 1] - pts_x[i]) * f, ys_pts[i] + (ys_pts[i + 1] - ys_pts[i]) * f)
            flows["ch"] = _Flow("ch", E, ich, pos_fn=pos, length=(xD - xS) + 60, speed=190)
        if st["body"] > 1e-9:
            flows["bd_e"] = _Flow("bd_e", E, st["body"],
                                  lambda u: _Poly([(xD, ys - 7), (xD + u * 20, well_bot - 5),
                                                   (xD + u * 30, y1 - 20), (xBd, y1)]), speed=90)
            flows["bd_h"] = _Flow("bd_h", Hh, st["body"],
                                  lambda u: _Poly([(xBd, y1), (xD - 20 + u * 20, y1 - 30), (xD + u * 20, well_bot + 2)]),
                                  speed=70, fade=True)
        if st["aval"] > 1e-9:
            flows["av_e"] = _Flow("av_e", E, st["aval"],
                                  lambda u: _Poly([(dw_l - dep_d / 2, well_bot + u * 10), (xD, well_bot - 10), (xD, ys - 7)]),
                                  speed=120)
            flows["av_h"] = _Flow("av_h", Hh, st["aval"],
                                  lambda u: _Poly([(dw_l - dep_d / 2, well_bot + u * 10), (xBd + 30, y1 - 10), (xBd, y1)]),
                                  speed=90)
            self._spark(c, dw_l - dep_d / 2, well_bot, 20)
        self.flows = flows

    def _carrier_static(self, c, x, y, kind):
        if kind == "e":
            c.create_oval(x - 3, y - 3, x + 3, y + 3, fill=E_COLOR, outline="", tags="static")
        else:
            c.create_oval(x - 3, y - 3, x + 3, y + 3, outline=H_COLOR, width=2, fill="white", tags="static")

    # ---------------- JFET ----------------
    def _build_jfet(self, c, W, H, st):
        x0, x1 = 50, W - 50
        yt, yb = 125, 245           # channel top / bottom
        g0, g1 = x0 + 0.18 * (x1 - x0), x1 - 0.18 * (x1 - x0)
        half = (yb - yt) / 2
        ym = (yt + yb) / 2
        ch_fill, ch_dop = self._region_fill("N")
        g_fill, g_dop = self._region_fill("P+")
        vp = self._params().get("vp", -4.0)
        prof = tm.jfet_depletion_profile(st["vg"], max(-20, min(st["vd"], 40)), vp)
        n = len(prof) - 1
        c.create_rectangle(x0, yt, x1, yb, fill=ch_fill, outline="#333", width=2, tags="static")
        self._static_dots(c, x0, yt, g0, yb, ch_dop, 12, 21)
        self._static_dots(c, g1, yt, x1, yb, ch_dop, 12, 22)
        # gates
        c.create_rectangle(g0, yt - 40, g1, yt, fill=g_fill, outline="#555", tags="static")
        c.create_rectangle(g0, yb, g1, yb + 40, fill=g_fill, outline="#555", tags="static")
        self._static_dots(c, g0, yt - 40, g1, yt, g_dop, 10, 23)
        self._static_dots(c, g0, yb, g1, yb + 40, g_dop, 10, 24)
        c.create_text((g0 + g1) / 2, yt - 30, text=f"{g_dop} {t('jv.jfet.gate')}", font=("Segoe UI", 8, "bold"),
                      fill="#333", tags="static")
        c.create_text((x0 + g0) / 2, ym, text=f"{ch_dop}\n{t('jv.jfet.channel')}", font=("Segoe UI", 8, "bold"),
                      fill="#333", tags="static")

        def depth(fr):
            k = min(n, max(0, fr * n))
            i = int(k)
            j = min(n, i + 1)
            d = prof[i] + (prof[j] - prof[i]) * (k - i)
            return d * half

        top_poly, bot_poly = [g0, yt], [g0, yb]
        steps = 40
        for i in range(steps + 1):
            fr = i / steps
            x = g0 + (g1 - g0) * fr
            d = depth(fr)
            top_poly += [x, yt + d]
            bot_poly += [x, yb - d]
        top_poly += [g1, yt]
        bot_poly += [g1, yb]
        for poly in (top_poly, bot_poly):
            c.create_polygon(*poly, fill=DEP_FILL, outline="#b9ae8a", dash=(3, 2), tags="static")
        # fixed ions in the channel-side depletion
        for i in range(12):
            fr = (i + 0.5) / 12
            x = g0 + (g1 - g0) * fr
            d = depth(fr)
            yy = yt + 7
            while yy < yt + d - 4:
                c.create_text(x, yy, text="+" if ch_dop.startswith("N") else "−", fill="#7a7a7a",
                              font=("Segoe UI", 8, "bold"), tags="static")
                c.create_text(x, yb - (yy - yt), text="+" if ch_dop.startswith("N") else "−", fill="#7a7a7a",
                              font=("Segoe UI", 8, "bold"), tags="static")
                yy += 12
        pinched = max(prof) >= 0.999
        if pinched and abs(st["ich"]) > 0:
            c.create_text((g0 + g1) / 2, yb + 52, text=t("jv.jfet.pinched"), font=("Segoe UI", 8), fill="#555",
                          tags="static")
        # contacts
        c.create_rectangle(x0 - 8, yt + 20, x0, yb - 20, fill=METAL, outline="#555", tags="static")
        c.create_rectangle(x1, yt + 20, x1 + 8, yb - 20, fill=METAL, outline="#555", tags="static")
        c.create_line(x0 - 8, ym, x0 - 30, ym, x0 - 30, 45, fill=sym.SYM_COLOR, width=2, tags="static")
        c.create_line(x1 + 8, ym, x1 + 30, ym, x1 + 30, 45, fill=sym.SYM_COLOR, width=2, tags="static")
        for x, lab in ((x0 - 30, "S"), (x1 + 30, "D")):
            c.create_oval(x - 4, 41, x + 4, 49, fill="white", outline=sym.SYM_COLOR, width=2, tags="static")
            c.create_text(x, 33, text=lab, font=("Segoe UI", 11, "bold"), fill=sym.SYM_COLOR, tags="static")
        xG = (g0 + g1) / 2
        c.create_rectangle(xG - 12, yt - 47, xG + 12, yt - 40, fill=METAL, outline="#555", tags="static")
        c.create_rectangle(xG - 12, yb + 40, xG + 12, yb + 47, fill=METAL, outline="#555", tags="static")
        self._terminal(c, xG, yt - 47, 35, "G")
        c.create_line(xG, yb + 47, xG, yb + 62, g0 - 20, yb + 62, g0 - 20, 60, xG - 14, 60, fill="#777",
                      width=1.5, dash=(4, 2), tags="static")

        fan = 0.09 * (x1 - x0)     # carriers spread out gradually after leaving the neck

        def _smooth(a):
            a = max(0.0, min(1.0, a))
            return a * a * (3 - 2 * a)

        def opening(x):
            if g0 <= x <= g1:
                return max(2.5, half - depth((x - g0) / (g1 - g0)))
            if x > g1:
                edge = max(2.5, half - depth(1.0))
                return edge + (half - edge) * _smooth((x - g1) / fan)
            edge = max(2.5, half - depth(0.0))
            return edge + (half - edge) * _smooth((g0 - x) / fan)

        xmap = _continuity_map(lambda fr: opening(x0 + (x1 - x0) * fr) / half)

        flows = {}
        E, Hh = self._carriers("e"), self._carriers("h")
        ich = st["ich"]
        if abs(ich) > 0:
            def pos(p, u, fwd=ich > 0):
                if not fwd:
                    p = 1 - p
                x = x0 + (x1 - x0) * xmap(p)
                return x, ym + u * opening(x) * 0.8
            flows["ch"] = _Flow("ch", E, ich, pos_fn=pos, length=x1 - x0, speed=110)
        for key, cur, xs in (("gs", st["ig_s"], g0 + 25), ("gd", st["ig_d"], g1 - 25)):
            if cur > 1e-9:
                flows[key + "_h"] = _Flow(key + "_h", Hh, cur,
                                          lambda u, xs=xs: _Poly([(xG, yt - 40), (xs + u * 15, yt - 5), (xs + u * 15, ym)]),
                                          speed=70, fade=True)
                flows[key + "_h2"] = _Flow(key + "_h2", Hh, cur,
                                           lambda u, xs=xs: _Poly([(xG, yb + 40), (xs + u * 15, yb + 5), (xs + u * 15, ym)]),
                                           speed=70, fade=True)
        if st["bd"] > 1e-9:
            flows["bd_e"] = _Flow("bd_e", E, st["bd"], lambda u: _Poly([(g1 - 10, yt + 10 + u * 8), (x1, ym + u * 20)]),
                                  speed=120)
            flows["bd_h"] = _Flow("bd_h", Hh, st["bd"], lambda u: _Poly([(g1 - 10, yt + 5 + u * 5), (xG, yt - 40)]),
                                  speed=90)
            self._spark(c, g1 - 8, yt + 8, 10)
            self._spark(c, g1 - 8, yb - 8, 10)
        self.flows = flows

    # ------------------------------------------------------------------
    # Animation
    # ------------------------------------------------------------------
    MAX_LIFE_S = 2.2   # no carrier takes longer than this to cross the picture

    def _speed(self, f, length):
        return max(f.speed, length / self.MAX_LIFE_S)

    def _new_particle(self, f, progress):
        u = self._rng.uniform(-1, 1)
        p = {"flow": f.key, "p": progress, "u": u, "item": None}
        if f.path_fn:
            p["path"] = f.path_fn(u)
        return p

    def _reset_particles(self):
        c = self.cv
        c.delete("p")
        self.particles = []
        # steady-state seeding: rate x travel time particles spread along each path
        for f in self.flows.values():
            f.acc = 0.0
            length = f.path_fn(0.0).length if f.path_fn else f.length
            life = length / max(self._speed(f, length), 1)
            n = int(f.rate * life)
            for _ in range(n):
                if len(self.particles) >= MAX_PARTICLES:
                    return
                self.particles.append(self._new_particle(f, self._rng.uniform(0, 0.98)))

    def _tick(self):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        if not is_shown(self.cv):
            # page not visible: do no work, just check again a bit later
            self._after = self.after(300, self._tick)
            return
        t_start = time.perf_counter()
        dt = TICK_MS / 1000
        c = self.cv
        # spawn
        for f in self.flows.values():
            if len(self.particles) >= MAX_PARTICLES:
                break
            f.acc = getattr(f, "acc", 0.0) + f.rate * dt
            while f.acc >= 1:
                f.acc -= 1
                self.particles.append(self._new_particle(f, 0.0))
        # move + draw
        alive = []
        for p in self.particles:
            f = self.flows.get(p["flow"])
            if f is None:
                if p["item"]:
                    c.delete(p["item"])
                continue
            length = p["path"].length if "path" in p else f.length
            p["p"] += self._speed(f, length) * dt / max(length, 1)
            if p["p"] >= 1:
                if p["item"]:
                    c.delete(p["item"])
                continue
            x, y = p["path"].at(p["p"]) if "path" in p else f.pos_fn(p["p"], p["u"])
            r = 2.8
            if f.fade and p["p"] > 0.75:
                r = 3.2 * (1 - (p["p"] - 0.75) / 0.25) + 0.5
            if p["item"] is None:
                if f.carrier == "e":
                    p["item"] = c.create_oval(x - r, y - r, x + r, y + r, fill=E_COLOR, outline="", tags="p")
                else:
                    p["item"] = c.create_oval(x - r, y - r, x + r, y + r, fill="white", outline=H_COLOR,
                                              width=2, tags="p")
            else:
                c.coords(p["item"], x - r, y - r, x + r, y + r)
            alive.append(p)
        self.particles = alive
        # flicker sparks for breakdown regions
        if c.find_withtag("spark"):
            for it in c.find_withtag("spark"):
                c.itemconfigure(it, state="normal" if self._rng.random() > 0.35 else "hidden")
        # never ask for frames faster than this machine can draw them
        spent = int((time.perf_counter() - t_start) * 1000)
        self._after = self.after(max(TICK_MS, 2 * spent), self._tick)

    def stop(self):
        if getattr(self, "_pending", None) is not None:
            try:
                self.after_cancel(self._pending)
            except Exception:
                pass
            self._pending = None
        if self._after is not None:
            try:
                self.after_cancel(self._after)
            except Exception:
                pass
            self._after = None

    def _on_destroy(self, e):
        if e.widget is self:
            self.stop()

    # ------------------------------------------------------------------
    # Symbol with terminal currents
    # ------------------------------------------------------------------
    def _draw_symbol(self):
        st = self._state
        if st is None:
            return
        c = self.sv
        c.delete("all")
        W = max(200, c.winfo_width() if c.winfo_width() > 50 else 230)
        s = 1.7
        cx, cy = W / 2 + 22, 165
        fam = self.family
        if fam == "bjt":
            sym.bjt(c, cx, cy, s=s, npn=self.ntype)
            cur = {"B": st["ib"], "C": st["ic"], "E": -st["ie"]}     # positive = into the device
        elif fam == "mosfet":
            mode_dep = self.mos_mode.get() == self._mos_modes[1]
            sym.mosfet(c, cx, cy, s=s, nch=self.ntype, enhancement=not mode_dep)
            cur = {"G": 0.0, "D": st["id"], "S": -st["id"]}
        else:
            sym.jfet(c, cx, cy, s=s, nch=self.ntype)
            cur = {"G": st["ig"], "D": st["id"], "S": -st["is"]}
        term = sym.device_terminals(fam, cx, cy, s)
        names = list(term)
        for k, name in enumerate(names):
            x, y = term[name]
            i = cur[name]
            if k == 0:     # control terminal: horizontal lead to the left
                x_out, y_out = x - 56, y
            elif k == 1:
                x_out, y_out = x, y - 44
            else:
                x_out, y_out = x, y + 44
            c.create_line(x, y, x_out, y_out, fill=sym.SYM_COLOR, width=2)
            mag = abs(i)
            if mag > 1e-10:
                w = 1.5 + min(6, max(0, math.log10(mag / 1e-10)) * 0.7)
                mx, my = (x + x_out) / 2, (y + y_out) / 2
                dx, dy = (x - x_out), (y - y_out)
                L = math.hypot(dx, dy)
                ux, uy = dx / L, dy / L
                if i < 0:
                    ux, uy = -ux, -uy
                c.create_line(mx - ux * 14, my - uy * 14, mx + ux * 14, my + uy * 14, fill=I_ARROW, width=w,
                              arrow="last", arrowshape=(10 + w, 12 + w, 4 + w / 2))
            if k == 0:
                lx, ly, anchor = x_out - 2, y_out + 18, "w"
            elif k == 1:
                lx, ly, anchor = x_out, y_out - 8, "s"
            else:
                lx, ly, anchor = x_out, y_out + 8, "n"
            c.create_text(lx, ly, text=f"I{name} = {_fmt_i(abs(i))}", anchor=anchor, font=("Segoe UI", 8, "bold"),
                          fill="#8a4b00")
        c.create_text(W / 2, 14, text=t("jv.symbol_title"), font=("Segoe UI", 9, "bold"), fill="#555")
        c.create_text(W / 2, 318, text=t("jv.conv_current"), font=("Segoe UI", 7), fill="#777")

    # ------------------------------------------------------------------
    # Region map / output characteristic
    # ------------------------------------------------------------------
    MAP = (46, 14, 318, 196)   # plot box in the map canvas

    def _bjt_axis(self, v, is_x):
        """Piecewise axis: forward side (0..0.9) gets 35 % of the length."""
        L, T, R, B = self.MAP
        vmin = -9.0 if is_x else -60.0
        v = self.sgn * v
        if v >= 0:
            f = 0.45 + 0.55 * min(v, 0.9) / 0.9
        else:
            f = 0.45 * (1 - max(v, vmin) / vmin)
        return (L + (R - L) * f) if is_x else (B - (B - T) * f)

    def _bjt_axis_inv(self, pix, is_x):
        L, T, R, B = self.MAP
        f = (pix - L) / (R - L) if is_x else (B - pix) / (B - T)
        f = max(0.0, min(1.0, f))
        vmin = -9.0 if is_x else -60.0
        v = 0.9 * (f - 0.45) / 0.55 if f >= 0.45 else vmin * (1 - f / 0.45)
        return self.sgn * v

    def _draw_map(self):
        c = self.mv
        c.delete("all")
        L, T, R, B = self.MAP
        st = self._state
        if st is None:
            return
        if self.family == "bjt":
            X = lambda v: self._bjt_axis(v, True)  # noqa: E731
            Y = lambda v: self._bjt_axis(v, False)  # noqa: E731
            s = self.sgn
            on = 0.5
            zones = [
                ("cutoff", -7, on, -50, on, "#e5e7eb"),
                ("active", on, 0.9, -50, on, "#cfe8df"),
                ("saturation", on, 0.9, on, 0.9, "#f6dcc0"),
                ("reverse", -7, on, on, 0.9, "#e0d4ee"),
                ("eb_breakdown", -9, -7, -60, 0.9, "#f7c6c0"),
                ("avalanche", -7, 0.9, -60, -50, "#f7c6c0"),
            ]
            for key, x_a, x_b, y_a, y_b, col in zones:
                xa, xb = sorted((X(s * x_a), X(s * x_b)))
                ya, yb = sorted((Y(s * y_a), Y(s * y_b)))
                c.create_rectangle(xa, ya, xb, yb, fill=col, outline="white")
                if xb - xa > 34 and yb - ya > 16:
                    c.create_text((xa + xb) / 2, (ya + yb) / 2, text=t(f"jv.region.bjt.{key}"),
                                  font=("Segoe UI", 7, "bold"), fill="#444", width=xb - xa - 4)
            c.create_rectangle(L, T, R, B, outline="#555")
            c.create_line(X(0), T, X(0), B, fill="#999", dash=(2, 2))
            c.create_line(L, Y(0), R, Y(0), fill="#999", dash=(2, 2))
            for v in (-9, -7, -1, 0, 0.5, 0.9):
                c.create_text(X(s * v), B + 9, text=f"{s * v:g}", font=("Segoe UI", 7), fill="#555")
            for v in (-60, -50, -20, -5, 0, 0.5, 0.9):
                c.create_text(L - 4, Y(s * v), text=f"{s * v:g}", anchor="e", font=("Segoe UI", 7), fill="#555")
            c.create_text((L + R) / 2, B + 22, text="VBE (V)  →", font=("Segoe UI", 8, "bold"), fill="#333")
            c.create_text(10, (T + B) / 2, text="VBC (V)", angle=90, font=("Segoe UI", 8, "bold"), fill="#333")
            px, py = X(self._a), Y(self._b)
            c.create_oval(px - 6, py - 6, px + 6, py + 6, fill=self.accent, outline="white", width=2)
            c.create_text(R, T - 6, text=t("jv.map_hint"), anchor="e", font=("Segoe UI", 7), fill="#777")
            return
        self._draw_fet_map()
        self._draw_curve()

    # ---- FET region map (VGS on x, VDS on y, both in slider travel units) ----
    FET_COLORS = {
        "cutoff": "#e5e7eb", "subthreshold": "#eef2d0", "triode": "#f6dcc0", "ohmic": "#f6dcc0",
        "saturation": "#cfe8df", "reverse_channel": "#e0d4ee", "reversed": "#e0d4ee",
        "body_diode": "#d8c3ef", "gate_forward": "#fde6a8", "avalanche": "#f7c6c0", "breakdown": "#f7c6c0",
    }

    def _fet_region_grid(self, nx=46, ny=32):
        key = (tuple(sorted(self._params().items())), nx, ny)
        if self._fet_map_cache and self._fet_map_cache[0] == key:
            return self._fet_map_cache[1]
        grid = []
        for j in range(ny):
            row = []
            vds = self.s2._u2v((j + 0.5) / ny)
            for i in range(nx):
                vgs = self.s1._u2v((i + 0.5) / nx)
                try:
                    row.append(self._compute(vgs, vds)["region"])
                except Exception:
                    row.append("cutoff")
            grid.append(row)
        self._fet_map_cache = (key, grid)
        return grid

    def _draw_fet_map(self):
        c = self.mv
        L, T, R, B = self.MAP
        nx, ny = 46, 32
        grid = self._fet_region_grid(nx, ny)
        cw, ch = (R - L) / nx, (B - T) / ny
        cells = {}
        for j, row in enumerate(grid):
            y1 = B - j * ch
            for i, reg in enumerate(row):
                x0 = L + i * cw
                c.create_rectangle(x0, y1 - ch, x0 + cw + 0.6, y1 + 0.6,
                                   fill=self.FET_COLORS.get(reg, "#eeeeee"), outline="")
                cells.setdefault(reg, []).append((x0 + cw / 2, y1 - ch / 2))
        # oxide-stress band (|VGS| beyond the rating) hatched on top
        if self.family == "mosfet":
            vmax = tm.MOSFET_DEFAULTS["vgs_max"]
            for i in range(nx):
                if abs(self.s1._u2v((i + 0.5) / nx)) > vmax:
                    x0 = L + i * cw
                    c.create_rectangle(x0, T, x0 + cw + 0.6, B, fill="#dc2626", stipple="gray25", outline="")
        placed = []
        for reg, pts in sorted(cells.items(), key=lambda kv: -len(kv[1])):
            if len(pts) < 36:
                continue
            mx = sum(p[0] for p in pts) / len(pts)
            my = sum(p[1] for p in pts) / len(pts)
            txt = t(f"jv.region.{self.family}.{reg}")
            # try the cells nearest the centroid first, skip spots that collide with other labels
            for qx, qy in sorted(pts, key=lambda p: (p[0] - mx) ** 2 + (p[1] - my) ** 2)[::3]:
                item = c.create_text(qx, qy, text=txt, font=("Segoe UI", 7, "bold"), fill="#333", width=80)
                x0, y0, x1, y1 = c.bbox(item)
                ok = x0 >= L and x1 <= R and y0 >= T and y1 <= B and all(
                    x1 < a0 or x0 > a1 or y1 < b0 or y0 > b1 for a0, b0, a1, b1 in placed)
                if ok:
                    placed.append((x0 - 2, y0 - 1, x1 + 2, y1 + 1))
                    break
                c.delete(item)
        c.create_rectangle(L, T, R, B, outline="#555")
        u0x, u0y = self.s1._v2u(0), self.s2._v2u(0)
        c.create_line(L + (R - L) * u0x, T, L + (R - L) * u0x, B, fill="#888", dash=(2, 2))
        c.create_line(L, B - (B - T) * u0y, R, B - (B - T) * u0y, fill="#888", dash=(2, 2))
        for u, v in self.s1.segments:
            c.create_text(L + (R - L) * u, B + 9, text=f"{v:g}", font=("Segoe UI", 7), fill="#555")
        for u, v in self.s2.segments:
            c.create_text(L - 4, B - (B - T) * u, text=f"{v:g}", anchor="e", font=("Segoe UI", 7), fill="#555")
        c.create_text((L + R) / 2, B + 22, text="VGS (V)  →", font=("Segoe UI", 8, "bold"), fill="#333")
        c.create_text(10, (T + B) / 2, text="VDS (V)", angle=90, font=("Segoe UI", 8, "bold"), fill="#333")
        px = L + (R - L) * self.s1._v2u(self._a)
        py = B - (B - T) * self.s2._v2u(self._b)
        c.create_oval(px - 6, py - 6, px + 6, py + 6, fill=self.accent, outline="white", width=2)
        c.create_text(R, T - 6, text=t("jv.map_hint"), anchor="e", font=("Segoe UI", 7), fill="#777")

    def _draw_curve(self):
        """FET output characteristic ID(VDS) for the current VGS (+ neighbours)."""
        c = self.cvc
        c.delete("all")
        L, T, R, B = self.MAP
        lo, hi = self.s2.segments[0][1], self.s2.segments[-1][1]
        vgs = self._a
        n = 90
        xs = [lo + (hi - lo) * i / n for i in range(n + 1)]
        curves = []
        steps = (-2, -1, 1, 2) if self.family == "mosfet" else (-1.5, -0.75, 0.75)
        for dv in (0,) + steps:
            curves.append((dv, [self._compute(vgs + self.sgn * dv, v)["id"] for v in xs]))
        main = curves[0][1]
        ref = max(abs(self._state["id"]), max(abs(y) for y in main if True) * 0.0 + 0)
        normal = [abs(y) for v, y in zip(xs, main) if 0 <= self.sgn * v <= abs(hi) * 0.6]
        typical = max(normal + [1e-6])
        ymax = max(typical, abs(self._state["id"])) * 1.25
        ymin = -ymax if min(main) < -0.02 * ymax else -0.08 * ymax
        if not self.ntype:
            ymin, ymax = -ymax, (ymax if max(main) > 0.02 * ymax else 0.08 * ymax)
        X = lambda v: L + (R - L) * (v - lo) / (hi - lo)  # noqa: E731
        Y = lambda i: B - (B - T) * (max(ymin, min(ymax, i)) - ymin) / (ymax - ymin)  # noqa: E731
        c.create_rectangle(L, T, R, B, outline="#555", fill="white")
        c.create_line(X(0), T, X(0), B, fill="#aaa")
        c.create_line(L, Y(0), R, Y(0), fill="#aaa")
        for dv, ys in curves[1:]:
            c.create_line(*[q for v, y in zip(xs, ys) for q in (X(v), Y(y))], fill="#c7c7c7", width=1)
        c.create_line(*[q for v, y in zip(xs, main) for q in (X(v), Y(y))], fill=self.accent, width=2.5)
        px, py = X(self._b), Y(self._state["id"])
        c.create_oval(px - 6, py - 6, px + 6, py + 6, fill="#d97706", outline="white", width=2)
        for v in (lo, 0, hi):
            c.create_text(X(v), B + 9, text=f"{v:g}", font=("Segoe UI", 7), fill="#555")
        c.create_text(L - 4, Y(ymax), text=_fmt_i(ymax), anchor="e", font=("Segoe UI", 7), fill="#555")
        c.create_text(L - 4, Y(0), text="0", anchor="e", font=("Segoe UI", 7), fill="#555")
        c.create_text((L + R) / 2, B + 22, text="VDS (V)  →", font=("Segoe UI", 8, "bold"), fill="#333")
        c.create_text(10, (T + B) / 2, text="ID", angle=90, font=("Segoe UI", 8, "bold"), fill="#333")
        c.create_text(R, T - 6, text=t("jv.curve_hint").format(v=f"{vgs:+.2f}"), anchor="e",
                      font=("Segoe UI", 7), fill="#555")

    def _on_curve_click(self, e):
        L, T, R, B = self.MAP
        lo, hi = self.s2.segments[0][1], self.s2.segments[-1][1]
        v = lo + (hi - lo) * (e.x - L) / (R - L)
        self.s2.set(v)

    def _on_map_click(self, e):
        if self.family != "bjt":
            L, T, R, B = self.MAP
            ux = max(0.0, min(1.0, (e.x - L) / (R - L)))
            uy = max(0.0, min(1.0, (B - e.y) / (B - T)))
            self.s1.set(round(self.s1._u2v(ux), 2), fire=False)
            self.s2.set(round(self.s2._u2v(uy), 2))
            return
        vbe = self._bjt_axis_inv(e.x, True)
        vbc = self._bjt_axis_inv(e.y, False)
        if self.mode_var.get() != "vbc":
            self.mode_var.set("vbc")
            self._on_mode()
        self.s1.set(vbe, fire=False)
        self.s2.set(vbc)
