"""
tabs/ac_waveform.py - Signals > AC Circuits > "AC Quantities" sub-tab.

Everything about ONE periodic AC signal, from whatever the user knows:
  * amplitude (maximum/peak value), peak-to-peak, effective (RMS), average
    (rectified / half-period) value -> enter any one, get all the others,
  * frequency, period or angular frequency -> enter any one, get the others
    (time <-> frequency conversion), plus wavelength,
  * instantaneous value v(t) at any moment t, and the reverse: the moments
    when the signal reaches a given value,
  * DC offset / true average, form factor, crest factor, AC ripple,
  * a rectifier + filter-capacitor ripple calculator, and a ripple
    calculator from measured Vmax / Vmin.
Works for sine, square, triangle, sawtooth, half-wave and full-wave
rectified sine.
"""
import math
import numpy as np
import tkinter as tk
from tkinter import ttk

from charts import MplChartFrame, PLOT_BG, eng_scale
from widgets import parse_value, format_value, ScrollableFrame, FONT_H2, FONT_BODY, FONT_MONO
from i18n import t

ACCENT_C = "#277DA1"
WAVES = ["sine", "square", "triangle", "sawtooth", "half_rect", "full_rect"]

# ratio of each quantity to the amplitude A for the pure (offset-free) wave
#            Vpp/A   Vrms/A        Vavg_rect/A   (mean of |v| over a period)
RATIOS = {
    "sine":      (2.0, 1 / math.sqrt(2), 2 / math.pi),
    "square":    (2.0, 1.0, 1.0),
    "triangle":  (2.0, 1 / math.sqrt(3), 0.5),
    "sawtooth":  (2.0, 1 / math.sqrt(3), 0.5),
    "half_rect": (1.0, 0.5, 1 / math.pi),
    "full_rect": (1.0, 1 / math.sqrt(2), 2 / math.pi),
}

FORMULA_TEXT = {
    "sine": "v(t) = Vmax·sin(ωt + φ)\nVrms = Vmax/√2 ≈ 0.707·Vmax\nVavg = 2·Vmax/π ≈ 0.637·Vmax\nVpp = 2·Vmax",
    "square": "v(t) = ±Vmax\nVrms = Vmax\nVavg = Vmax\nVpp = 2·Vmax",
    "triangle": "Vrms = Vmax/√3 ≈ 0.577·Vmax\nVavg = Vmax/2\nVpp = 2·Vmax",
    "sawtooth": "Vrms = Vmax/√3 ≈ 0.577·Vmax\nVavg = Vmax/2\nVpp = 2·Vmax",
    "half_rect": "Vdc = Vmax/π ≈ 0.318·Vmax\nVrms = Vmax/2\nVpp = Vmax",
    "full_rect": "Vdc = 2·Vmax/π ≈ 0.637·Vmax\nVrms = Vmax/√2\nVpp = Vmax",
}


def wave_value(kind, A, ph, offset=0.0):
    """Instantaneous value for phase angle ph (radians, any real value)."""
    x = np.mod(ph, 2 * np.pi) / (2 * np.pi)  # 0..1 within the period
    if kind == "sine":
        v = A * np.sin(ph)
    elif kind == "square":
        v = np.where(x < 0.5, A, -A)
    elif kind == "triangle":
        v = np.where(x < 0.25, 4 * A * x, np.where(x < 0.75, 2 * A - 4 * A * x, 4 * A * x - 4 * A))
    elif kind == "sawtooth":
        v = np.where(x < 0.5, 2 * A * x, 2 * A * x - 2 * A)
    elif kind == "half_rect":
        v = np.where(x < 0.5, A * np.sin(ph), 0.0)
    else:  # full_rect
        v = A * np.abs(np.sin(ph))
    return v + offset


class ACWaveformPanel(ttk.Frame):
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
        ls = ScrollableFrame(left_wrap, style="Card.TFrame")
        ls.grid(row=0, column=0, sticky="nsew")
        left = ls.body

        right = ttk.Frame(self, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        self._build_controls(left)
        self.chart = MplChartFrame(right, figsize=(5.6, 3.6))
        self.chart.grid(row=0, column=0, sticky="nsew", padx=10, pady=(10, 4))
        rs = ScrollableFrame(right, style="Card.TFrame")
        rs.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
        right.rowconfigure(1, weight=1)
        self._build_ripple(rs.body)
        self._ready = True
        self._compute()
        self._ripple()
        self._ripple_meas()

    # ------------------------------------------------------------------
    def _row(self, parent, r, label, var, width=12, unit=None):
        ttk.Label(parent, text=label, font=FONT_BODY, style="CardBody.TLabel").grid(row=r, column=0, sticky="w", pady=2)
        e = ttk.Entry(parent, textvariable=var, width=width)
        e.grid(row=r, column=1, sticky="w", pady=2, padx=6)
        e.bind("<KeyRelease>", lambda ev: self._compute())
        if unit:
            ttk.Label(parent, text=unit, font=FONT_BODY, style="CardBody.TLabel").grid(row=r, column=2, sticky="w")
        return e

    def _build_controls(self, p):
        p.columnconfigure(0, weight=1)
        ttk.Label(p, text=t("acw.intro"), font=FONT_BODY, style="CardBody.TLabel", wraplength=440,
                  justify="left").grid(row=0, column=0, sticky="w", padx=16, pady=(12, 6))

        g = ttk.Frame(p, style="Card.TFrame")
        g.grid(row=1, column=0, sticky="w", padx=16)
        ttk.Label(g, text=t("acw.waveform"), font=FONT_BODY, style="CardBody.TLabel").grid(row=0, column=0, sticky="w")
        self._wave_labels = [t(f"acw.wave.{w}") for w in WAVES]
        self.wave_var = tk.StringVar(value=self._wave_labels[0])
        cb = ttk.Combobox(g, textvariable=self.wave_var, values=self._wave_labels, state="readonly", width=24)
        cb.grid(row=0, column=1, columnspan=2, sticky="w", padx=6, pady=2)
        cb.bind("<<ComboboxSelected>>", lambda e: self._compute())

        ttk.Label(g, text=t("acw.quantity"), font=FONT_BODY, style="CardBody.TLabel").grid(row=1, column=0, sticky="w")
        self._qty_labels = [t("acw.qty.voltage"), t("acw.qty.current")]
        self.qty_var = tk.StringVar(value=self._qty_labels[0])
        qcb = ttk.Combobox(g, textvariable=self.qty_var, values=self._qty_labels, state="readonly", width=12)
        qcb.grid(row=1, column=1, sticky="w", padx=6, pady=2)
        qcb.bind("<<ComboboxSelected>>", lambda e: self._compute())

        # amplitude: enter ANY one of the 4
        ttk.Label(p, text=t("acw.known_amp"), font=FONT_H2, foreground=ACCENT_C, style="CardSub.TLabel")\
            .grid(row=2, column=0, sticky="w", padx=16, pady=(10, 2))
        a = ttk.Frame(p, style="Card.TFrame")
        a.grid(row=3, column=0, sticky="w", padx=16)
        self._amp_keys = ["max", "pp", "rms", "avg"]
        self._amp_labels = [t(f"acw.amp.{k}") for k in self._amp_keys]
        self.amp_kind = tk.StringVar(value=self._amp_labels[2])
        acb = ttk.Combobox(a, textvariable=self.amp_kind, values=self._amp_labels, state="readonly", width=30)
        acb.grid(row=0, column=0, columnspan=3, sticky="w", pady=2)
        acb.bind("<<ComboboxSelected>>", lambda e: self._compute())
        self.amp_val = tk.StringVar(value="230")
        self._row(a, 1, t("acw.value"), self.amp_val)

        # time base: enter ANY one of f / T / ω
        ttk.Label(p, text=t("acw.known_time"), font=FONT_H2, foreground=ACCENT_C, style="CardSub.TLabel")\
            .grid(row=4, column=0, sticky="w", padx=16, pady=(10, 2))
        tb = ttk.Frame(p, style="Card.TFrame")
        tb.grid(row=5, column=0, sticky="w", padx=16)
        self._time_keys = ["f", "T", "w"]
        self._time_labels = [t(f"acw.time.{k}") for k in self._time_keys]
        self.time_kind = tk.StringVar(value=self._time_labels[0])
        tcb = ttk.Combobox(tb, textvariable=self.time_kind, values=self._time_labels, state="readonly", width=30)
        tcb.grid(row=0, column=0, columnspan=3, sticky="w", pady=2)
        tcb.bind("<<ComboboxSelected>>", lambda e: self._compute())
        self.time_val = tk.StringVar(value="50")
        self._row(tb, 1, t("acw.value"), self.time_val)

        # extras
        ttk.Label(p, text=t("acw.extras"), font=FONT_H2, foreground=ACCENT_C, style="CardSub.TLabel")\
            .grid(row=6, column=0, sticky="w", padx=16, pady=(10, 2))
        ex = ttk.Frame(p, style="Card.TFrame")
        ex.grid(row=7, column=0, sticky="w", padx=16)
        self.phase_val = tk.StringVar(value="0")
        self.offset_val = tk.StringVar(value="0")
        self.t_val = tk.StringVar(value="2.5m")
        self.target_val = tk.StringVar(value="100")
        self._row(ex, 0, t("acw.phase"), self.phase_val, unit="°")
        self._row(ex, 1, t("acw.offset"), self.offset_val)
        self._row(ex, 2, t("acw.instant_t"), self.t_val, unit="s")
        self._row(ex, 3, t("acw.find_value"), self.target_val)

        ttk.Label(p, text=t("acw.results"), font=FONT_H2, foreground=ACCENT_C, style="CardSub.TLabel")\
            .grid(row=8, column=0, sticky="w", padx=16, pady=(10, 2))
        self.table = ttk.Treeview(p, columns=("q", "sym", "val"), show="headings", height=17)
        for col, key, wd in (("q", "acw.col_quantity", 210), ("sym", "acw.col_symbol", 70), ("val", "acw.col_value", 150)):
            self.table.heading(col, text=t(key))
            self.table.column(col, width=wd, anchor="w" if col == "q" else "center")
        self.table.grid(row=9, column=0, sticky="ew", padx=16)
        self.formula_var = tk.StringVar()
        ttk.Label(p, textvariable=self.formula_var, font=("Consolas", 10), foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left").grid(row=10, column=0, sticky="w", padx=16, pady=(8, 2))
        self.msg = tk.StringVar()
        ttk.Label(p, textvariable=self.msg, font=("Segoe UI", 9), style="CardBody.TLabel", wraplength=440,
                  justify="left").grid(row=11, column=0, sticky="w", padx=16, pady=(2, 16))

    # ------------------------------------------------------------------
    def _compute(self):
        if not self._ready:
            return
        wave = WAVES[self._wave_labels.index(self.wave_var.get())]
        is_v = self.qty_var.get() == self._qty_labels[0]
        u = "V" if is_v else "A"
        q = "V" if is_v else "I"
        try:
            known = parse_value(self.amp_val.get())
            tv = parse_value(self.time_val.get())
            phase_deg = float(self.phase_val.get().replace(",", ".") or 0)
            offset = parse_value(self.offset_val.get()) if self.offset_val.get().strip() else 0.0
            if known <= 0 or tv <= 0:
                raise ValueError
        except Exception:
            self.msg.set(t("common.enter_valid_values"))
            return
        pp_r, rms_r, avg_r = RATIOS[wave]
        akey = self._amp_keys[self._amp_labels.index(self.amp_kind.get())]
        A = {"max": known, "pp": known / pp_r, "rms": known / rms_r, "avg": known / avg_r}[akey]
        tkey = self._time_keys[self._time_labels.index(self.time_kind.get())]
        f = {"f": tv, "T": 1 / tv, "w": tv / (2 * math.pi)}[tkey]
        T = 1 / f
        w = 2 * math.pi * f
        phi = math.radians(phase_deg)

        # exact statistics of the actual signal (incl. offset) from 1 period
        n = 200000
        ph = np.linspace(0, 2 * np.pi, n, endpoint=False)
        vs = wave_value(wave, A, ph, offset)
        vmax, vmin = float(vs.max()), float(vs.min())
        mean = float(vs.mean())
        scale_ref = max(abs(vmax), abs(vmin), 1e-300)
        if abs(mean) < 1e-9 * scale_ref:
            mean = 0.0  # remove floating-point noise (e.g. -1.7e-14 for a pure sine)
        rms = float(np.sqrt(np.mean(vs ** 2)))
        rect_avg = float(np.mean(np.abs(vs)))
        ac_rms = float(np.sqrt(max(rms ** 2 - mean ** 2, 0.0)))
        vpp = vmax - vmin
        crest = max(abs(vmax), abs(vmin)) / rms if rms else float("nan")
        form = rms / rect_avg if rect_avg else float("nan")
        out_f = 2 * f if wave == "full_rect" else f

        rows = []
        fv = lambda x, unit=u: format_value(float(f"{x:.5g}"), unit)  # noqa: E731
        rows.append((t("acw.r.amplitude"), f"{q}max", fv(A)))
        rows.append((t("acw.r.max"), f"{q}max", fv(vmax)))
        rows.append((t("acw.r.min"), f"{q}min", fv(vmin)))
        rows.append((t("acw.r.pp"), f"{q}pp", fv(vpp)))
        rows.append((t("acw.r.rms"), f"{q}rms / {q}ef", fv(rms)))
        rows.append((t("acw.r.avg_rect"), f"{q}avg", fv(rect_avg)))
        rows.append((t("acw.r.mean"), f"{q}dc", fv(mean)))
        rows.append((t("acw.r.ac_rms"), f"{q}ac", fv(ac_rms)))
        rows.append((t("acw.r.ripple_factor"), "γ", f"{ac_rms / abs(mean) * 100:.2f} %" if abs(mean) > 1e-12 else "—"))
        rows.append((t("acw.r.form"), "kf", f"{form:.4f}"))
        rows.append((t("acw.r.crest"), "kv", f"{crest:.4f}"))
        rows.append((t("acw.r.freq"), "f", format_value(float(f"{f:.6g}"), "Hz")))
        rows.append((t("acw.r.period"), "T", format_value(float(f"{T:.6g}"), "s")))
        rows.append((t("acw.r.omega"), "ω", f"{w:.6g} rad/s"))
        if wave in ("full_rect", "half_rect"):
            rows.append((t("acw.r.out_freq"), "f_out", format_value(out_f, "Hz")))
        rows.append((t("acw.r.lambda"), "λ = c/f", format_value(float(f"{3e8 / f:.4g}"), "m")))

        # instantaneous value at t
        t_txt = self.t_val.get().strip()
        tt = None
        if t_txt:
            try:
                tt = parse_value(t_txt)
                vt = float(wave_value(wave, A, w * tt + phi, offset))
                rows.append((t("acw.r.instant").format(t=format_value(tt, "s")), f"{q.lower()}(t)", fv(vt)))
                rows.append((t("acw.r.angle"), "ωt+φ", f"{math.degrees(w * tt + phi) % 360:.2f}°"))
            except Exception:
                tt = None
        # moments when value is reached
        hits = []
        g_txt = self.target_val.get().strip()
        if g_txt:
            try:
                target = parse_value(g_txt)
                tgrid = np.linspace(0, T, 20001)
                vg = wave_value(wave, A, w * tgrid + phi, offset) - target
                for k in range(len(tgrid) - 1):
                    if vg[k] == 0 or (vg[k] < 0) != (vg[k + 1] < 0):
                        a0, a1 = vg[k], vg[k + 1]
                        tz = tgrid[k] + (tgrid[k + 1] - tgrid[k]) * (a0 / (a0 - a1) if a1 != a0 else 0)
                        if not hits or tz - hits[-1] > T * 1e-4:
                            hits.append(tz)
                txt = ", ".join(format_value(float(f"{h:.4g}"), "s") for h in hits[:4]) if hits else t("acw.never")
                rows.append((t("acw.r.when").format(v=fv(target)), "t", txt))
            except Exception:
                pass

        for r in self.table.get_children():
            self.table.delete(r)
        for r in rows:
            self.table.insert("", "end", values=r)
        self.formula_var.set(FORMULA_TEXT[wave] + "\nT = 1/f,   f = 1/T,   ω = 2πf = 2π/T")
        note = t("acw.note_amp")
        if wave in ("half_rect", "full_rect"):
            note += "\n" + t("acw.note_rect")
        self.msg.set(note)
        self._plot(wave, A, f, phi, offset, vmax, vmin, rms, mean, rect_avg, tt, hits, u)

    def _plot(self, wave, A, f, phi, offset, vmax, vmin, rms, mean, rect_avg, tt, hits, u):
        T = 1 / f
        tf, tp = eng_scale(np.array([2 * T]))
        tarr = np.linspace(0, 2 * T, 2000)
        v = wave_value(wave, A, 2 * np.pi * f * tarr + phi, offset)
        fig = self.chart.fig
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_facecolor(PLOT_BG)
        ax.plot(tarr / tf, v, color="#c9622a", linewidth=2)
        ax.axhline(0, color="#333", linewidth=1)
        ax.axhline(vmax, color="#6A4C93", linestyle="--", linewidth=1)
        ax.axhline(rms, color="#2A9D8F", linestyle="--", linewidth=1.2)
        ax.axhline(mean, color="#888", linestyle=":", linewidth=1.2)
        ax.text(2 * T / tf, vmax, f" max {vmax:.4g}", va="bottom", ha="right", fontsize=8, color="#6A4C93")
        ax.text(2 * T / tf, rms, f" rms {rms:.4g}", va="bottom", ha="right", fontsize=8, color="#2A9D8F")
        ax.text(0, mean, f" dc {mean:.4g}", va="bottom", ha="left", fontsize=8, color="#666")
        if vmin < 0 or vmin < vmax:
            ax.axhline(vmin, color="#6A4C93", linestyle="--", linewidth=0.8, alpha=0.6)
        # period bracket
        ytop = vmax + 0.12 * (vmax - vmin or 1)
        ax.annotate("", xy=(T / tf, ytop), xytext=(0, ytop),
                    arrowprops=dict(arrowstyle="<->", color="#1f2a44"))
        ax.text(T / 2 / tf, ytop, f"T = {format_value(float(f'{T:.4g}'), 's')}", ha="center", va="bottom", fontsize=8)
        # Vpp bracket
        xpp = 1.9 * T / tf
        ax.annotate("", xy=(xpp, vmax), xytext=(xpp, vmin), arrowprops=dict(arrowstyle="<->", color="#c62828"))
        ax.text(xpp, (vmax + vmin) / 2, " pp", color="#c62828", fontsize=8, va="center")
        if tt is not None:
            vt = float(wave_value(wave, A, 2 * np.pi * f * tt + phi, offset))
            if 0 <= tt <= 2 * T:
                ax.plot([tt / tf], [vt], "o", color="#277DA1", markersize=7)
                ax.annotate(f"v(t)={vt:.4g}", (tt / tf, vt), textcoords="offset points", xytext=(6, 6),
                            fontsize=8, color="#277DA1")
        for h in hits[:4]:
            ax.axvline(h / tf, color="#277DA1", alpha=0.25, linewidth=1)
        ax.set_ylim(vmin - 0.15 * (vmax - vmin or 1), ytop + 0.18 * (vmax - vmin or 1))
        ax.set_xlim(0, 2 * T / tf)
        ax.set_xlabel(f"{t('chart.time_axis')} ({tp}s)")
        ax.set_ylabel(f"{t('acw.chart_y')} ({u})")
        ax.grid(True, alpha=0.25)
        fig.tight_layout()
        self.chart.redraw()

    # ------------------------------------------------------------------
    def _build_ripple(self, p):
        p.columnconfigure(0, weight=1)
        ttk.Label(p, text=t("acw.rip_title"), font=FONT_H2, foreground=ACCENT_C, style="CardSub.TLabel")\
            .grid(row=0, column=0, sticky="w", pady=(6, 2))
        ttk.Label(p, text=t("acw.rip_intro"), font=("Segoe UI", 9), style="CardBody.TLabel", wraplength=440,
                  justify="left").grid(row=1, column=0, sticky="w")
        g = ttk.Frame(p, style="Card.TFrame")
        g.grid(row=2, column=0, sticky="w", pady=4)
        self._rip_types = [t("acw.rip_half"), t("acw.rip_full")]
        self.rip_type = tk.StringVar(value=self._rip_types[1])
        ttk.Label(g, text=t("acw.rip_rect"), font=FONT_BODY, style="CardBody.TLabel").grid(row=0, column=0, sticky="w")
        rcb = ttk.Combobox(g, textvariable=self.rip_type, values=self._rip_types, state="readonly", width=24)
        rcb.grid(row=0, column=1, columnspan=2, sticky="w", padx=6, pady=2)
        rcb.bind("<<ComboboxSelected>>", lambda e: self._ripple())
        self.rip_vars = {}
        fields = [("vrms", t("acw.rip_vrms"), "12", "V"), ("f", t("acw.rip_f"), "50", "Hz"),
                  ("vd", t("acw.rip_vd"), "0.7", "V"), ("il", t("acw.rip_il"), "500m", "A"),
                  ("c", t("acw.rip_c"), "2200u", "F")]
        for r, (k, lbl, d, un) in enumerate(fields, start=1):
            ttk.Label(g, text=lbl, font=FONT_BODY, style="CardBody.TLabel").grid(row=r, column=0, sticky="w", pady=1)
            var = tk.StringVar(value=d)
            e = ttk.Entry(g, textvariable=var, width=10)
            e.grid(row=r, column=1, sticky="w", padx=6)
            e.bind("<KeyRelease>", lambda ev: self._ripple())
            ttk.Label(g, text=un, font=FONT_BODY, style="CardBody.TLabel").grid(row=r, column=2, sticky="w")
            self.rip_vars[k] = var
        self.rip_solve_c = tk.BooleanVar(value=False)
        ttk.Checkbutton(g, text=t("acw.rip_solve_c"), variable=self.rip_solve_c, command=self._ripple)\
            .grid(row=6, column=0, columnspan=2, sticky="w", pady=(4, 0))
        self.rip_target = tk.StringVar(value="1")
        e = ttk.Entry(g, textvariable=self.rip_target, width=10)
        e.grid(row=6, column=2, sticky="w")
        e.bind("<KeyRelease>", lambda ev: self._ripple())
        self.rip_result = tk.StringVar()
        ttk.Label(p, textvariable=self.rip_result, font=("Consolas", 10, "bold"), foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left").grid(row=3, column=0, sticky="w", pady=(4, 8))

        ttk.Separator(p, orient="horizontal").grid(row=4, column=0, sticky="ew", pady=6)
        ttk.Label(p, text=t("acw.meas_title"), font=FONT_H2, foreground=ACCENT_C, style="CardSub.TLabel")\
            .grid(row=5, column=0, sticky="w")
        m = ttk.Frame(p, style="Card.TFrame")
        m.grid(row=6, column=0, sticky="w", pady=4)
        self.m_max = tk.StringVar(value="16.2")
        self.m_min = tk.StringVar(value="14.8")
        for r, (lbl, var) in enumerate(((t("acw.meas_max"), self.m_max), (t("acw.meas_min"), self.m_min))):
            ttk.Label(m, text=lbl, font=FONT_BODY, style="CardBody.TLabel").grid(row=r, column=0, sticky="w")
            e = ttk.Entry(m, textvariable=var, width=10)
            e.grid(row=r, column=1, sticky="w", padx=6, pady=1)
            e.bind("<KeyRelease>", lambda ev: self._ripple_meas())
        self.meas_result = tk.StringVar()
        ttk.Label(p, textvariable=self.meas_result, font=("Consolas", 10, "bold"), foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left").grid(row=7, column=0, sticky="w", pady=(4, 12))

    def _ripple(self):
        try:
            v = {k: parse_value(var.get()) for k, var in self.rip_vars.items()}
        except Exception:
            self.rip_result.set(t("common.enter_valid_values"))
            return
        full = self.rip_type.get() == self._rip_types[1]
        k = 2 if full else 1
        n_d = 2 if full else 1  # bridge: 2 diodes conduct in series
        vpk_in = v["vrms"] * math.sqrt(2)
        vpk = vpk_in - n_d * v["vd"]
        fr = k * v["f"]
        try:
            if self.rip_solve_c.get():
                vr = parse_value(self.rip_target.get())
                c = v["il"] / (fr * vr)
                self.rip_vars["c"].set(format_value(float(f"{c:.4g}"), "").replace(" ", ""))
            else:
                c = v["c"]
                vr = v["il"] / (fr * c)
        except Exception:
            self.rip_result.set(t("common.enter_valid_values"))
            return
        vdc = vpk - vr / 2
        vmin = vpk - vr
        vr_rms = vr / (2 * math.sqrt(3))
        gamma = vr_rms / vdc * 100 if vdc > 0 else float("nan")
        lines = [
            f"Vmax (in)   = √2·Vrms = {vpk_in:.4g} V",
            f"Vmax (out)  = {vpk:.4g} V   ({n_d}×Vd)",
            f"f ripple    = {format_value(fr, 'Hz')}",
            f"Vr (pp)     = I/(f·C) = {vr:.4g} V",
            f"C           = {format_value(float(f'{c:.4g}'), 'F')}",
            f"Vmin        = {vmin:.4g} V",
            f"Vdc (avg)   ≈ Vmax − Vr/2 = {vdc:.4g} V",
            f"Vr (rms)    = Vr/(2√3) = {vr_rms:.4g} V",
            f"γ = Vr,rms/Vdc = {gamma:.2f} %",
        ]
        if vmin <= 0:
            lines.append(t("acw.rip_warn"))
        self.rip_result.set("\n".join(lines))

    def _ripple_meas(self):
        try:
            vmax = parse_value(self.m_max.get())
            vmin = parse_value(self.m_min.get())
        except Exception:
            self.meas_result.set(t("common.enter_valid_values"))
            return
        vpp = vmax - vmin
        vdc = (vmax + vmin) / 2
        vr_rms = vpp / (2 * math.sqrt(3))
        pct = vpp / vdc * 100 if vdc else float("nan")
        self.meas_result.set(
            f"Vr (pp) = Vmax − Vmin = {vpp:.4g} V\n"
            f"Vdc ≈ (Vmax + Vmin)/2 = {vdc:.4g} V\n"
            f"{t('acw.meas_pct')} = Vpp/Vdc = {pct:.2f} %\n"
            f"γ ≈ Vr,rms/Vdc = {vr_rms / vdc * 100 if vdc else float('nan'):.2f} %   ({t('acw.meas_tri')})")
