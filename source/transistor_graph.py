"""
transistor_graph.py - Transistors > "Chart / Simulate": graphical analysis.

The classic textbook way to SEE how a transistor stage works:
  1. transfer characteristic   (IC vs IB  /  ID vs VGS)  with the input swing
  2. output characteristics    (IC vs VCE /  ID vs VDS)  with the DC load line,
                                the Q point and the swing along the load line
  3. waveforms                 input and output vs time, clipped parts in red
One circuit (common-emitter / common-source stage with a collector/drain
resistor), one bias control and one input-signal control. A small input is
an amplifier; a big one clips; a square drive turns it into a switch.
Works in magnitudes (|VCE|, |ID| ...) so the P-types use the same view.
"""
import math
import numpy as np
import tkinter as tk
from tkinter import ttk

from charts import MplChartFrame, PLOT_BG
from widgets import parse_value, format_value, FONT_BODY, FONT_H2, ScrollableFrame
from i18n import t

VA = 100.0     # Early voltage (BJT)
VK = 0.08      # BJT saturation knee
LAM = 0.01     # FET channel-length modulation


def bjt_ic(ib, vce, beta):
    if ib <= 0 or vce <= 0:
        return 0.0
    return beta * ib * (1 - math.exp(-vce / VK)) * (1 + vce / VA)


def mos_id(vgs, vds, k, vth):
    vov = vgs - vth
    if vov <= 0 or vds <= 0:
        return 0.0
    if vds < vov:
        return k * (2 * vov * vds - vds * vds) * (1 + LAM * vds)
    return k * vov * vov * (1 + LAM * vds)


def jfet_id(vgs, vds, idss, vp_abs):
    vp = -vp_abs
    if vgs <= vp or vds <= 0:
        return 0.0
    vgs = min(vgs, 0.0)
    vsat = vgs - vp
    if vds < vsat:
        return idss * (2 * (1 - vgs / vp) * (vds / vp_abs) - (vds / vp) ** 2) * (1 + LAM * vds)
    return idss * (1 - vgs / vp) ** 2 * (1 + LAM * vds)


def operating_point(fn, x, vcc, r):
    """Intersection of the device curve I = fn(x, V) with the load line
    V = vcc - I*r (bisection on I)."""
    lo, hi = 0.0, vcc / r
    for _ in range(44):          # 2^-44 of full scale: far below a pixel
        mid = (lo + hi) / 2
        if fn(x, vcc - mid * r) > mid:
            lo = mid
        else:
            hi = mid
    i = (lo + hi) / 2
    return i, vcc - i * r


class GraphicalAnalysisPanel(ttk.Frame):
    def __init__(self, parent, family, polarity, accent):
        super().__init__(parent, style="Card.TFrame")
        self.family = family
        self.ntype = polarity.upper().startswith("N")
        self.accent = accent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body
        body.columnconfigure(0, weight=1)

        intro = ttk.Label(body, text=t(f"tg.intro.{family}"), font=FONT_BODY, style="CardBody.TLabel",
                          wraplength=900, justify="left")
        intro.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))
        body.bind("<Configure>", lambda e: intro.configure(wraplength=max(300, e.width - 40)), add="+")

        pre = ttk.Frame(body, style="Card.TFrame")
        pre.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 6))
        ttk.Label(pre, text=t("jv.presets"), font=("Segoe UI", 9, "bold"), style="CardBody.TLabel")\
            .pack(side="left", padx=(0, 6))
        for key in ("amp", "clip", "switch", "center"):
            ttk.Button(pre, text=t(f"tg.preset.{key}"), style="Small.TButton",
                       command=lambda k=key: self._preset(k)).pack(side="left", padx=2)

        ctl = ttk.Frame(body, style="Card.TFrame")
        ctl.grid(row=2, column=0, sticky="ew", padx=16)
        ctl.columnconfigure(1, weight=1)
        ctl.columnconfigure(4, weight=1)
        # circuit + device parameters
        if family == "bjt":
            params = [("vcc", "VCC", "12", "V"), ("r", "RC", "1k", "Ω"), ("beta", "β", "150", "")]
            self.bias_rng, self.bias_default, self.bias_unit = (0.0, 150e-6), 40e-6, "A"
            self.bias_lbl, self.sig_lbl = t("tg.bias_ib"), t("tg.sig_ib")
        elif family == "mosfet":
            params = [("vcc", "VDD", "12", "V"), ("r", "RD", "1k", "Ω"), ("k", "K", "5m", "A/V²"),
                      ("vth", "|Vth|", "2", "V")]
            self.bias_rng, self.bias_default, self.bias_unit = (0.0, 6.0), 3.4, "V"
            self.bias_lbl, self.sig_lbl = t("tg.bias_vgs"), t("tg.sig_vgs")
        else:
            params = [("vcc", "VDD", "15", "V"), ("r", "RD", "1k", "Ω"), ("idss", "IDSS", "10m", "A"),
                      ("vp", "|VP|", "4", "V")]
            self.bias_rng, self.bias_default, self.bias_unit = (-4.0, 0.0), -1.6, "V"
            self.bias_lbl, self.sig_lbl = t("tg.bias_vgs_j"), t("tg.sig_vgs")
        self.pvars = {}
        pr = ttk.Frame(ctl, style="Card.TFrame")
        pr.grid(row=0, column=0, columnspan=6, sticky="w", pady=(0, 4))
        for key, lbl, d, u in params:
            ttk.Label(pr, text=lbl + " =", font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
            v = tk.StringVar(value=d)
            e = ttk.Entry(pr, textvariable=v, width=7)
            e.pack(side="left", padx=(3, 2))
            e.bind("<KeyRelease>", lambda ev: self._schedule())
            ttk.Label(pr, text=u, font=FONT_BODY, style="CardBody.TLabel").pack(side="left", padx=(0, 12))
            self.pvars[key] = v
        ttk.Label(pr, text=t("tg.wave"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left", padx=(8, 3))
        self._waves = [t("tg.wave_sine"), t("tg.wave_square")]
        self.wave = tk.StringVar(value=self._waves[0])
        cb = ttk.Combobox(pr, textvariable=self.wave, values=self._waves, state="readonly", width=9)
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self._schedule())

        ttk.Label(ctl, text=self.bias_lbl, font=FONT_BODY, style="CardBody.TLabel", width=30)\
            .grid(row=1, column=0, sticky="w")
        self.bias = tk.DoubleVar(value=self.bias_default)
        ttk.Scale(ctl, from_=self.bias_rng[0], to=self.bias_rng[1], variable=self.bias, orient="horizontal",
                  command=lambda v: self._schedule()).grid(row=1, column=1, sticky="ew", padx=6)
        self.bias_txt = tk.StringVar()
        ttk.Label(ctl, textvariable=self.bias_txt, font=("Consolas", 10, "bold"), foreground=accent,
                  style="CardFormula.TLabel", width=11).grid(row=1, column=2, sticky="w")
        ttk.Label(ctl, text=self.sig_lbl, font=FONT_BODY, style="CardBody.TLabel", width=30)\
            .grid(row=2, column=0, sticky="w")
        span = self.bias_rng[1] - self.bias_rng[0]
        self.sig = tk.DoubleVar(value=span * 0.08)
        ttk.Scale(ctl, from_=0.0, to=span * 0.6, variable=self.sig, orient="horizontal",
                  command=lambda v: self._schedule()).grid(row=2, column=1, sticky="ew", padx=6)
        self.sig_txt = tk.StringVar()
        ttk.Label(ctl, textvariable=self.sig_txt, font=("Consolas", 10, "bold"), foreground=accent,
                  style="CardFormula.TLabel", width=11).grid(row=2, column=2, sticky="w")

        self.result = tk.StringVar()
        ttk.Label(body, textvariable=self.result, font=("Consolas", 10, "bold"), foreground=accent,
                  style="CardFormula.TLabel", justify="left").grid(row=3, column=0, sticky="w", padx=16, pady=(6, 2))
        self.chart = MplChartFrame(body, figsize=(9.5, 6.4), with_toolbar=False)
        self.chart.grid(row=4, column=0, sticky="ew", padx=16, pady=(4, 4))
        self.explain = tk.StringVar()
        ex = ttk.Label(body, textvariable=self.explain, font=FONT_BODY, style="CardBody.TLabel", wraplength=900,
                       justify="left")
        ex.grid(row=5, column=0, sticky="w", padx=16, pady=(2, 14))
        body.bind("<Configure>", lambda e: ex.configure(wraplength=max(300, e.width - 40)), add="+")
        self._pending = None
        self._draw()

    # ------------------------------------------------------------------
    def _schedule(self):
        if self._pending is None:
            self._pending = self.after(60, self._draw)

    def _p(self):
        return {k: parse_value(v.get()) for k, v in self.pvars.items()}

    def _fn(self, p):
        if self.family == "bjt":
            return lambda x, v: bjt_ic(x, v, p["beta"])
        if self.family == "mosfet":
            return lambda x, v: mos_id(x, v, p["k"], abs(p["vth"]))
        return lambda x, v: jfet_id(x, v, p["idss"], abs(p["vp"]))

    def _preset(self, key):
        try:
            p = self._p()
        except Exception:
            return
        lo, hi = self.bias_rng
        if key == "center":
            # bias that puts Q at VCE = VCC/2 (maximum symmetric swing)
            fn = self._fn(p)
            a, b = lo, hi
            for _ in range(60):
                m = (a + b) / 2
                _, v = operating_point(fn, m, p["vcc"], p["r"])
                if v > p["vcc"] / 2:
                    a = m
                else:
                    b = m
            self.bias.set((a + b) / 2)
            self.wave.set(self._waves[0])
        elif key == "amp":
            self._preset("center")
            self.sig.set((hi - lo) * 0.06)
            return
        elif key == "clip":
            self._preset("center")
            self.sig.set((hi - lo) * 0.35)
            return
        elif key == "switch":
            self.bias.set((lo + hi) / 2)
            self.sig.set((hi - lo) * 0.5)
            self.wave.set(self._waves[1])
        self._schedule()

    def _fmt_x(self, x):
        if self.family == "bjt":
            return format_value(float(f"{x:.3g}"), "A")
        return f"{x:+.2f} V" if self.family == "jfet" else f"{x:.2f} V"

    # ------------------------------------------------------------------
    def _draw(self):
        self._pending = None
        try:
            if not self.winfo_exists():
                return
            p = self._p()
            if p["vcc"] <= 0 or p["r"] <= 0:
                raise ValueError
        except Exception:
            self.result.set(t("common.enter_valid_values"))
            return
        fam = self.family
        fn = self._fn(p)
        vcc, r = p["vcc"], p["r"]
        lo, hi = self.bias_rng
        xq = self.bias.get()
        amp = self.sig.get()
        self.bias_txt.set(self._fmt_x(xq))
        self.sig_txt.set("± " + self._fmt_x(amp).lstrip("+"))
        square = self.wave.get() == self._waves[1]
        tt = np.linspace(0, 2, 260)
        s = np.sign(np.sin(2 * np.pi * tt)) if square else np.sin(2 * np.pi * tt)
        x_t = xq + amp * s
        if fam == "bjt":
            x_t = np.clip(x_t, 0, None)
        memo = {}

        def op_i(x):
            k = round(float(x), 12)
            if k not in memo:
                memo[k] = operating_point(fn, x, vcc, r)[0]
            return memo[k]
        i_t = np.array([op_i(x) for x in x_t])
        v_t = vcc - i_t * r
        iq, vq = operating_point(fn, xq, vcc, r)
        # "ideal" linear output for clip detection: small-signal slope at Q
        dx = (hi - lo) * 1e-3
        i_plus, _ = operating_point(fn, xq + dx, vcc, r)
        i_minus, _ = operating_point(fn, max(lo, xq - dx) if fam != "jfet" else xq - dx, vcc, r)
        slope = (i_plus - i_minus) / (2 * dx)
        v_lin = vcc - (iq + slope * (x_t - xq)) * r
        clipped = np.abs(v_lin - v_t) > 0.02 * vcc
        sat_v = 0.2 if fam == "bjt" else None

        fig = self.chart.fig
        fig.clear()
        try:
            fig.set_layout_engine("constrained")
        except Exception:
            pass
        gs = fig.add_gridspec(2, 2, height_ratios=[1.15, 1])
        axs = [fig.add_subplot(gs[0, 0]), fig.add_subplot(gs[0, 1]), fig.add_subplot(gs[1, :])]
        for ax in axs:
            ax.set_facecolor(PLOT_BG)
            ax.grid(True, alpha=0.25)
        cf = 1e3
        iu = "mA"
        xs_unit = 1e6 if fam == "bjt" else 1.0
        xs_lbl = "IB (µA)" if fam == "bjt" else ("VGS (V)" if self.ntype else "|VGS| (V)")
        # 1. transfer characteristic (with the load in place, i.e. what the stage really does)
        xs = np.linspace(lo, hi, 120)
        ys = [op_i(x) for x in xs]
        ax = axs[0]
        ax.plot(xs * xs_unit, np.array(ys) * cf, color=self.accent, lw=2)
        ax.axvspan((xq - amp) * xs_unit, (xq + amp) * xs_unit, color="#6A4C93", alpha=0.12)
        ax.axhspan(i_t.min() * cf, i_t.max() * cf, color="#d97706", alpha=0.12)
        ax.plot([xq * xs_unit], [iq * cf], "o", color="#d97706", ms=8)
        ax.set_xlabel(xs_lbl)
        ax.set_ylabel(("IC" if fam == "bjt" else "ID") + f" ({iu})")
        ax.set_title(t("tg.t_transfer"), fontsize=10)
        # 2. output characteristics + load line
        ax = axs[1]
        vv = np.linspace(0, vcc * 1.05, 160)
        levels = np.linspace(lo, hi, 7)[1:] if fam != "jfet" else np.linspace(lo, hi, 7)[1:]
        for lv in levels:
            ax.plot(vv, [fn(lv, v) * cf for v in vv], color="#c8c8c8", lw=1)
            yl = fn(lv, vcc) * cf
            if yl < vcc / r * cf * 1.1:
                ax.text(vcc * 1.05, yl, " " + self._fmt_x(lv), fontsize=7, color="#888", va="center",
                        clip_on=True)
        ax.plot(vv, [fn(xq, v) * cf for v in vv], color=self.accent, lw=1.5)
        ax.plot([0, vcc], [vcc / r * cf, 0], color="#1f2a44", lw=2, label=t("tg.loadline"))
        ax.plot(v_t, i_t * cf, color="#d97706", lw=5, alpha=0.6, solid_capstyle="round",
                label=t("tg.swing"))
        ax.plot([vq], [iq * cf], "o", color="#d97706", ms=9, mec="white", label="Q")
        ax.set_xlim(0, vcc * 1.2)
        ax.set_ylim(0, vcc / r * cf * 1.15)
        ax.set_xlabel("|VCE| (V)" if fam == "bjt" else "|VDS| (V)")
        ax.set_ylabel(f"({iu})")
        ax.legend(fontsize=7, loc="upper right")
        ax.set_title(t("tg.t_output"), fontsize=10)
        # 3. waveforms
        ax = axs[2]
        ax.plot(tt, v_t, color="#c9622a", lw=2, label=t("tg.vout"))
        vc = np.where(clipped, v_t, np.nan)
        ax.plot(tt, vc, color="#dc2626", lw=3.5, label=t("tg.clipped"))
        ax.axhline(vq, color="#999", lw=0.8, ls=":")
        ax.set_ylim(-0.05 * vcc, vcc * 1.08)
        ax.set_xlabel(t("tg.periods"))
        ax.set_ylabel("|VCE| (V)" if fam == "bjt" else "|VDS| (V)")
        ax2 = ax.twinx()
        ax2.plot(tt, x_t * xs_unit, color="#6A4C93", lw=1.2, ls="--", label=t("tg.input"))
        ax2.set_ylabel(xs_lbl, color="#6A4C93")
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, fontsize=7, loc="upper right")
        ax.set_title(t("tg.t_wave"), fontsize=10)
        if fig.get_layout_engine() is None:
            fig.tight_layout()
        self.chart.redraw()

        # numbers + explanation
        vswing = v_t.max() - v_t.min()
        gain_txt = ""
        if amp > 0:
            if fam == "bjt":
                rt = slope * r            # V per A of base current = transresistance
                gain_txt = f"Δ|VCE| / ΔIB ≈ {format_value(float(f'{rt:.3g}'), 'V/A')}   ({t('tg.current_gain')} ≈ {slope:.0f})"
            else:
                gain_txt = f"Av = −gm·RD ≈ {-slope * r:.2f}   (gm ≈ {format_value(float(f'{slope:.3g}'), 'S')})"
        name_v = "VCE" if fam == "bjt" else "VDS"
        name_i = "IC" if fam == "bjt" else "ID"
        self.result.set(
            f"Q:  {name_i} = {format_value(float(f'{iq:.3g}'), 'A')}   |{name_v}| = {vq:.2f} V   "
            f"(VCC/2 = {vcc / 2:.2f} V)\n"
            f"{t('tg.out_swing')}: {vswing:.2f} V p-p   {gain_txt}")
        if square and amp > 0 and v_t.min() < 0.1 * vcc and v_t.max() > 0.9 * vcc:
            key = "switch"
        elif clipped.any():
            low = (v_t < vq) & clipped
            key = "clip_sat" if low.any() and not ((v_t > vq) & clipped).any() else (
                "clip_cut" if not low.any() else "clip_both")
        elif amp == 0:
            key = "dc"
        else:
            key = "linear"
        if iq <= 1e-9:
            key = "off"
        elif vq < 0.05 * vcc:
            key = "sat" if amp == 0 else key
        self.explain.set(t(f"tg.explain.{key}"))
