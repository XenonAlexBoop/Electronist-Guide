"""
tabs/ac_circuits.py - Signals > AC Circuits & Phasors sub-tab.

Two inner pages:
  - Passive AC Circuits: series RC / RL / RLC networks -> impedance,
    phase angle, current, power factor, P/Q/S, and a phasor diagram.
  - AC Power Systems: single-phase, two-phase, and three-phase (Star/Delta)
    supplies -> line/phase relationships, total P/Q/S, and a phasor
    diagram that can be animated (continuously rotated) over time.
"""
import math
import numpy as np
import tkinter as tk
from tkinter import ttk

from charts import MplChartFrame, PLOT_BG
from widgets import parse_value, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ScrollableFrame, TheoryPanel
from data import get_theory
from i18n import t
from tabs.ac_waveform import ACWaveformPanel

ACCENT_C = "#277DA1"
V_PHASOR_COLOR = "#c9622a"
I_PHASOR_COLOR = "#277DA1"
PHASE_COLORS = ["#c9622a", "#2A9D8F", "#6A4C93"]


# ---------------------------------------------------------------------------
# Shared phasor-diagram renderer. `phasors` is a list of dicts:
#   {label, angle (rad), length (arbitrary units), color, group ("V"/"I")}
# Lengths are normalized independently per group so V and I (different
# physical units) both render at a legible, comparable scale.
# ---------------------------------------------------------------------------
def draw_phasor_diagram(fig, phasors, title=""):
    fig.clear()
    ax = fig.add_subplot(111)
    ax.set_facecolor(PLOT_BG)
    ax.set_aspect("equal")
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)

    for r in (0.5, 1.0):
        circle = plt_circle(r)
        ax.plot(circle[0], circle[1], color="#ddd", linewidth=1, zorder=0)
    ax.axhline(0, color="#ccc", linewidth=1, zorder=0)
    ax.axvline(0, color="#ccc", linewidth=1, zorder=0)

    groups = {}
    for p in phasors:
        groups.setdefault(p["group"], []).append(p)

    for group, items in groups.items():
        max_len = max((abs(p["length"]) for p in items), default=1.0) or 1.0
        for p in items:
            norm = 0.95 * abs(p["length"]) / max_len
            x = norm * math.cos(p["angle"])
            y = norm * math.sin(p["angle"])
            ax.annotate("", xy=(x, y), xytext=(0, 0),
                        arrowprops=dict(arrowstyle="-|>", color=p["color"], linewidth=2.2,
                                        mutation_scale=16))
            lx, ly = x * 1.14, y * 1.14
            ax.text(lx, ly, p["label"], color=p["color"], fontsize=10, fontweight="bold",
                    ha="center", va="center")

    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    if title:
        ax.set_title(title, fontsize=10, color="#555")
    fig.tight_layout()


def plt_circle(r, n=100):
    theta = np.linspace(0, 2 * np.pi, n)
    return r * np.cos(theta), r * np.sin(theta)


# ---------------------------------------------------------------------------
# Passive AC Circuits (RC / RL / RLC series)
# ---------------------------------------------------------------------------
CIRCUIT_KEYS = [("RC", "ac.circuit.rc"), ("RL", "ac.circuit.rl"), ("RLC", "ac.circuit.rlc")]


class PassiveACPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._ready = False

        left_wrap = ttk.Frame(self, style="Card.TFrame")
        left_wrap.grid(row=0, column=0, sticky="nsew")
        left_wrap.columnconfigure(0, weight=1)
        left_wrap.rowconfigure(0, weight=1)
        left_scroll = ScrollableFrame(left_wrap, style="Card.TFrame")
        left_scroll.grid(row=0, column=0, sticky="nsew")

        right = ttk.Frame(self, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self._build_controls(left_scroll.body)
        self._build_output(right)
        self._ready = True
        self._compute()

    def _build_controls(self, parent):
        pad = {"padx": 16, "pady": 6}
        parent.columnconfigure(0, weight=1)

        ttk.Label(parent, text=t("ac.passive.intro"), font=FONT_BODY, wraplength=380,
                  justify="left", style="CardBody.TLabel").grid(row=0, column=0, sticky="w", **pad)

        self._circuit_labels = [t(key) for _, key in CIRCUIT_KEYS]
        self._circuit_kinds = [k for k, _ in CIRCUIT_KEYS]
        ttk.Label(parent, text=t("ac.passive.circuit_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=1, column=0, sticky="w", padx=16)
        self.circuit_var = tk.StringVar(value=self._circuit_labels[2])
        cb = ttk.Combobox(parent, textvariable=self.circuit_var, values=self._circuit_labels,
                           state="readonly", width=12)
        cb.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))
        cb.bind("<<ComboboxSelected>>", lambda e: self._on_circuit_change())

        self.r_var = tk.StringVar(value="100")
        self.l_var = tk.StringVar(value="10m")
        self.c_var = tk.StringVar(value="100n")
        self.freq_var = tk.StringVar(value="1000")
        self.v_var = tk.StringVar(value="10")

        self.r_row = self._field_row(parent, 3, t("ac.passive.r_label"), self.r_var)
        self.l_row = self._field_row(parent, 5, t("ac.passive.l_label"), self.l_var)
        self.c_row = self._field_row(parent, 7, t("ac.passive.c_label"), self.c_var)
        self._field_row(parent, 9, t("ac.passive.freq_label"), self.freq_var)
        self._field_row(parent, 11, t("ac.passive.vsource_label"), self.v_var)

        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=13, column=0, sticky="ew", padx=16, pady=8)

        ttk.Label(parent, text=t("ac.passive.results_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=14, column=0, sticky="w", padx=16)

        self.result_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.result_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left", wraplength=420)\
            .grid(row=15, column=0, sticky="w", padx=16, pady=(4, 16))

        self._on_circuit_change(simulate=False)

    def _field_row(self, parent, row, label, var):
        lbl = ttk.Label(parent, text=label, font=FONT_BODY, style="CardBody.TLabel")
        lbl.grid(row=row, column=0, sticky="w", padx=16, pady=(6, 0))
        entry = ttk.Entry(parent, textvariable=var, width=14)
        entry.grid(row=row + 1, column=0, sticky="w", padx=16)
        entry.bind("<KeyRelease>", lambda e: self._compute())
        return (lbl, entry)

    def _on_circuit_change(self, simulate=True):
        kind = self._circuit_kinds[self._circuit_labels.index(self.circuit_var.get())]
        show_l = kind in ("RL", "RLC")
        show_c = kind in ("RC", "RLC")
        for w in self.l_row:
            (w.grid() if show_l else w.grid_remove())
        for w in self.c_row:
            (w.grid() if show_c else w.grid_remove())
        if simulate:
            self._compute()

    def _build_output(self, parent):
        ttk.Label(parent, text=t("ac.passive.diagram_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, sticky="w", padx=16, pady=(16, 6))
        self.chart = MplChartFrame(parent, with_toolbar=False)
        self.chart.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

    def _compute(self):
        if not self._ready:
            return
        kind = self._circuit_kinds[self._circuit_labels.index(self.circuit_var.get())]
        try:
            r = parse_value(self.r_var.get())
            l = parse_value(self.l_var.get()) if kind in ("RL", "RLC") else 0.0
            c = parse_value(self.c_var.get()) if kind in ("RC", "RLC") else None
            f = parse_value(self.freq_var.get())
            v = parse_value(self.v_var.get())
        except Exception:
            self.result_var.set(t("ac.passive.invalid"))
            return
        if r <= 0 or f <= 0 or v <= 0:
            self.result_var.set(t("ac.passive.invalid"))
            return

        w = 2 * math.pi * f
        xl = w * l if l else 0.0
        xc = (1 / (w * c)) if c else 0.0
        x = xl - xc
        z = complex(r, x)
        z_mag = abs(z)
        theta = math.atan2(x, r)
        i_peak = v / z_mag
        pf = r / z_mag
        s = v * i_peak / 2
        p = s * pf
        q = s * math.sin(theta)

        lines = [
            f"{t('ac.passive.impedance_label')} {z_mag:.4g} Ω",
            f"{t('ac.passive.phase_label')} {math.degrees(theta):+.2f}°",
            f"{t('ac.passive.current_label')} {i_peak:.4g} A",
            f"{t('ac.passive.pf_label')} {pf:.3f}",
            f"{t('ac.passive.power_p')} {p:.4g} W",
            f"{t('ac.passive.power_q')} {q:.4g} VAR",
            f"{t('ac.passive.power_s')} {s:.4g} VA",
        ]
        self.result_var.set("\n".join(lines))

        phasors = [
            {"label": "V", "angle": 0.0, "length": v, "color": V_PHASOR_COLOR, "group": "V"},
            {"label": "I", "angle": -theta, "length": i_peak, "color": I_PHASOR_COLOR, "group": "I"},
        ]
        draw_phasor_diagram(self.chart.fig, phasors)
        self.chart.redraw()


# ---------------------------------------------------------------------------
# AC Power Systems (single / two-phase / three-phase Y / three-phase Delta)
# ---------------------------------------------------------------------------
SYSTEM_KEYS = [
    ("single", "ac.system.single"),
    ("two_phase", "ac.system.two_phase"),
    ("three_star", "ac.system.three_star"),
    ("three_delta", "ac.system.three_delta"),
]


class PowerSystemsPanel(ttk.Frame):
    ANIM_INTERVAL_MS = 60
    ANIM_STEP_RAD = 0.12

    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.rowconfigure(0, weight=1)
        self._ready = False
        self._rotation = 0.0
        self._anim_job = None
        self._last_phasors = []
        self._wave_freq = 50.0
        self._wave_angles = []
        self._wave_phi = 0.0

        left_wrap = ttk.Frame(self, style="Card.TFrame")
        left_wrap.grid(row=0, column=0, sticky="nsew")
        left_wrap.columnconfigure(0, weight=1)
        left_wrap.rowconfigure(0, weight=1)
        left_scroll = ScrollableFrame(left_wrap, style="Card.TFrame")
        left_scroll.grid(row=0, column=0, sticky="nsew")

        phasor_col = ttk.Frame(self, style="Card.TFrame")
        phasor_col.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        phasor_col.columnconfigure(0, weight=1)
        phasor_col.rowconfigure(1, weight=1)

        wave_col = ttk.Frame(self, style="Card.TFrame")
        wave_col.grid(row=0, column=2, sticky="nsew", padx=(6, 0))
        wave_col.columnconfigure(0, weight=1)
        wave_col.rowconfigure(1, weight=1)

        self._build_controls(left_scroll.body)
        self._build_output(wave_col, phasor_col)
        self._ready = True
        self._compute()

        self.bind("<Destroy>", self._on_destroy)

    def _build_controls(self, parent):
        pad = {"padx": 16, "pady": 6}
        parent.columnconfigure(0, weight=1)

        ttk.Label(parent, text=t("ac.power.intro"), font=FONT_BODY, wraplength=380,
                  justify="left", style="CardBody.TLabel").grid(row=0, column=0, sticky="w", **pad)

        self._sys_labels = [t(key) for _, key in SYSTEM_KEYS]
        self._sys_kinds = [k for k, _ in SYSTEM_KEYS]
        ttk.Label(parent, text=t("ac.power.system_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=1, column=0, sticky="w", padx=16)
        self.system_var = tk.StringVar(value=self._sys_labels[2])
        cb = ttk.Combobox(parent, textvariable=self.system_var, values=self._sys_labels,
                           state="readonly", width=22)
        cb.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))
        cb.bind("<<ComboboxSelected>>", lambda e: self._compute())

        self.vphase_var = tk.StringVar(value="230")
        self.iphase_var = tk.StringVar(value="5")
        self.pfangle_var = tk.StringVar(value="30")
        self.freq_var = tk.StringVar(value="50")

        for row, (label, var) in enumerate([
            (t("ac.power.vphase_label"), self.vphase_var),
            (t("ac.power.iphase_label"), self.iphase_var),
            (t("ac.power.pf_angle_label"), self.pfangle_var),
            (t("ac.power.freq_label"), self.freq_var),
        ]):
            base = 3 + row * 2
            ttk.Label(parent, text=label, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=base, column=0, sticky="w", padx=16, pady=(6, 0))
            entry = ttk.Entry(parent, textvariable=var, width=14)
            entry.grid(row=base + 1, column=0, sticky="w", padx=16)
            entry.bind("<KeyRelease>", lambda e: self._compute())

        self.animate_var = tk.BooleanVar(value=False)
        chk = ttk.Checkbutton(parent, text=t("ac.power.animate_toggle"), variable=self.animate_var,
                               command=self._on_animate_toggle)
        chk.grid(row=11, column=0, sticky="w", padx=16, pady=(8, 8))

        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=12, column=0, sticky="ew", padx=16, pady=6)

        ttk.Label(parent, text=t("ac.power.results_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=13, column=0, sticky="w", padx=16)
        self.result_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.result_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left", wraplength=420)\
            .grid(row=14, column=0, sticky="w", padx=16, pady=(4, 16))

    def _build_output(self, wave_col, phasor_col):
        ttk.Label(wave_col, text=t("ac.power.waveform_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, sticky="w", padx=16, pady=(16, 6))
        self.wave_chart = MplChartFrame(wave_col, with_toolbar=False)
        self.wave_chart.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 4))
        ttk.Label(wave_col, text=t("ac.power.wave_note"), font=("Segoe UI", 8), foreground="#777",
                  style="CardBody.TLabel", wraplength=320).grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))

        ttk.Label(phasor_col, text=t("ac.power.diagram_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, sticky="w", padx=16, pady=(16, 6))
        self.chart = MplChartFrame(phasor_col, with_toolbar=False)
        self.chart.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

    def _on_animate_toggle(self):
        if self.animate_var.get():
            self._tick()
        elif self._anim_job is not None:
            self.after_cancel(self._anim_job)
            self._anim_job = None

    def _on_destroy(self, _event):
        if self._anim_job is not None:
            try:
                self.after_cancel(self._anim_job)
            except Exception:
                pass
            self._anim_job = None

    def _tick(self):
        self._rotation = (self._rotation + self.ANIM_STEP_RAD) % (2 * math.pi)
        self._redraw_phasors()
        self._redraw_waveform()
        self._anim_job = self.after(self.ANIM_INTERVAL_MS, self._tick)

    def _compute(self):
        if not self._ready:
            return
        kind = self._sys_kinds[self._sys_labels.index(self.system_var.get())]
        try:
            vp = parse_value(self.vphase_var.get())
            ip = parse_value(self.iphase_var.get())
            phi = math.radians(float(self.pfangle_var.get()))
        except Exception:
            self.result_var.set(t("ac.power.invalid"))
            return
        if vp <= 0 or ip <= 0:
            self.result_var.set(t("ac.power.invalid"))
            return
        try:
            freq = parse_value(self.freq_var.get())
            if freq <= 0:
                freq = 50.0
        except Exception:
            freq = 50.0

        cos_phi = math.cos(phi)
        sin_phi = math.sin(phi)

        if kind == "single":
            v_line, i_line = vp, ip
            n_phases, angles = 1, [0.0]
            p_total = vp * ip * cos_phi
        elif kind == "two_phase":
            v_line, i_line = vp * math.sqrt(2), ip
            n_phases, angles = 2, [0.0, -math.pi / 2]
            p_total = n_phases * vp * ip * cos_phi
        elif kind == "three_star":
            v_line, i_line = vp * math.sqrt(3), ip
            n_phases, angles = 3, [0.0, -2 * math.pi / 3, -4 * math.pi / 3]
            p_total = n_phases * vp * ip * cos_phi
        else:  # three_delta
            v_line, i_line = vp, ip * math.sqrt(3)
            n_phases, angles = 3, [0.0, -2 * math.pi / 3, -4 * math.pi / 3]
            p_total = n_phases * vp * ip * cos_phi

        q_total = n_phases * vp * ip * sin_phi
        s_total = n_phases * vp * ip

        lines = [
            f"{t('ac.power.vline_label')} {v_line:.4g} V",
            f"{t('ac.power.iline_label')} {i_line:.4g} A",
            f"{t('ac.power.ptotal_label')} {p_total:.4g} W",
            f"{t('ac.power.qtotal_label')} {q_total:.4g} VAR",
            f"{t('ac.power.stotal_label')} {s_total:.4g} VA",
        ]
        self.result_var.set("\n".join(lines))

        phasors = []
        for idx, ang in enumerate(angles):
            color = PHASE_COLORS[idx % len(PHASE_COLORS)]
            phasors.append({"label": f"V{idx + 1}", "angle": ang, "length": vp,
                             "color": color, "group": "V"})
            phasors.append({"label": f"I{idx + 1}", "angle": ang - phi, "length": ip,
                             "color": color, "group": "I"})
        self._last_phasors = phasors
        self._wave_freq = freq
        self._wave_angles = angles
        self._wave_phi = phi
        self._redraw_phasors()
        self._redraw_waveform()

    def _redraw_phasors(self):
        if not self._last_phasors:
            return
        rotated = [dict(p, angle=p["angle"] + self._rotation) for p in self._last_phasors]
        draw_phasor_diagram(self.chart.fig, rotated)
        self.chart.redraw()

    def _redraw_waveform(self):
        if not self._wave_angles:
            return
        freq = self._wave_freq
        period = 1.0 / freq
        w = 2 * math.pi * freq
        t_arr = np.linspace(0, period, 500)
        frac = (self._rotation / (2 * math.pi)) % 1.0
        cursor_t = frac * period

        fig = self.wave_chart.fig
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_facecolor(PLOT_BG)
        for idx, ang in enumerate(self._wave_angles):
            color = PHASE_COLORS[idx % len(PHASE_COLORS)]
            # Use sin() here (not cos()) so the waveform's height matches the
            # phasor diagram's vertical (y) component at every instant - the
            # two views are drawn from the same y = length*sin(angle) formula,
            # so tracing the cursor dot to the arrow tip's height lines up.
            v_curve = np.sin(w * t_arr + ang)
            i_curve = 0.6 * np.sin(w * t_arr + ang - self._wave_phi)
            ax.plot(t_arr, v_curve, color=color, linewidth=2, label=f"V{idx + 1}")
            ax.plot(t_arr, i_curve, color=color, linewidth=1.3, linestyle="--")
            v_now = math.sin(w * cursor_t + ang)
            i_now = 0.6 * math.sin(w * cursor_t + ang - self._wave_phi)
            ax.plot([cursor_t], [v_now], marker="o", color=color, markersize=7, zorder=5)
            ax.plot([cursor_t], [i_now], marker="o", color=color, markersize=6,
                    markerfacecolor="white", markeredgewidth=1.5, zorder=5)
        ax.axvline(cursor_t, color="#999", linestyle=":", linewidth=1.2)
        ax.set_ylim(-1.35, 1.35)
        ax.set_xlim(0, period)
        ax.set_xlabel(t("common.time_s"))
        ax.set_yticks([])
        ax.grid(True, alpha=0.2)
        ax.legend(loc="upper right", fontsize=7, ncol=len(self._wave_angles))
        fig.tight_layout()
        self.wave_chart.redraw()


class ACCircuitsTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=t("ac.tab_title"), font=FONT_H1, style="TabTitle.TLabel")\
            .grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 6))

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=(0, 10))

        waveform_page = ACWaveformPanel(nb)
        passive_page = PassiveACPanel(nb)
        power_page = PowerSystemsPanel(nb)
        theory_scroll = ScrollableFrame(nb, style="Card.TFrame")
        TheoryPanel(theory_scroll.body, get_theory("ac_circuits"), accent=ACCENT_C)\
            .pack(fill="both", expand=True)
        nb.add(waveform_page, text=t("acw.tab"))
        nb.add(passive_page, text=t("ac.subtab.passive"))
        nb.add(power_page, text=t("ac.subtab.power"))
        nb.add(theory_scroll, text=t("common.learn"))
