import numpy as np
import tkinter as tk
from widgets import is_shown
from tkinter import ttk
from data import get_theory
from drawing import draw_diode, draw_bridge_4diode
from widgets import TheoryPanel, ScrollableFrame, parse_value, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ACCENT
from charts import (MplChartFrame, diode_dc_curve, diode_rectifier,
                     four_diode_bridge_signals, V_COLOR, I_COLOR, PLOT_BG, include_zero)
from i18n import t
from widgets import lazy_tab
from symbols import SymbolGallery

ACCENT_C = ACCENT["diode"]


def _diode_types():
    return [
        (t("diode.type.silicon"), "0.6 - 0.7 V", t("diode.use.rectification")),
        (t("diode.type.germanium"), "0.2 - 0.3 V", t("diode.use.radios")),
        (t("diode.type.schottky"), "0.2 - 0.4 V", t("diode.use.fast_switch")),
        (t("diode.type.zener"), "varies (Vz)", t("diode.use.regulation")),
        (t("diode.type.red_led"), "1.8 - 2.2 V", t("diode.use.indicators")),
        (t("diode.type.green_led"), "2.0 - 3.2 V", t("diode.use.indicators")),
        (t("diode.type.blue_led"), "2.8 - 3.4 V", t("diode.use.lighting")),
    ]


class DiodeTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1, minsize=380)
        self.columnconfigure(1, weight=1, minsize=360)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=t("diode.tab_title"), font=FONT_H1, style="TabTitle.TLabel")\
            .grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 6))

        left = ttk.Frame(self, style="Tab.TFrame")
        left.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        right = ttk.Frame(self, style="Tab.TFrame")
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        nb = ttk.Notebook(left)
        nb.grid(row=0, column=0, sticky="nsew")
        calc_tab = ttk.Frame(nb, style="Card.TFrame")
        nb.add(calc_tab, text=t("diode.subtab.calc"))
        self._build_calculator(calc_tab)

        def framed(builder):
            def make(parent):
                f = ttk.Frame(parent, style="Card.TFrame")
                builder(f)
                return f
            return make
        lazy_tab(nb, t("diode.subtab.chart"), framed(self._build_chart))
        lazy_tab(nb, t("diode.subtab.bridge4"), framed(self._build_bridge4))

        right_scroll = ScrollableFrame(right, style="Card.TFrame")
        right_scroll.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        SymbolGallery(right_scroll.body, "diode", accent=ACCENT_C).pack(fill="x", pady=(0, 8))
        theory = TheoryPanel(right_scroll.body, get_theory("diode"), accent=ACCENT_C)
        theory.pack(fill="both", expand=True)

        table = self._build_table(right)
        table.grid(row=1, column=0, sticky="nsew")

    def _build_calculator(self, parent):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(parent, text=t("diode.led_calc_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", **pad)

        self.canvas = tk.Canvas(parent, width=460, height=180, bg="#fdfaf3", highlightthickness=0)
        self.canvas.grid(row=1, column=0, columnspan=2, padx=16, pady=6)

        fields = [(t("diode.supply_voltage"), "9"), (t("diode.forward_voltage"), "2"),
                  (t("diode.desired_current"), "20")]
        self.vars = []
        for i, (label, default) in enumerate(fields):
            ttk.Label(parent, text=label, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=i + 2, column=0, sticky="w", **pad)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(parent, textvariable=var, width=10)
            entry.grid(row=i + 2, column=1, sticky="w", **pad)
            entry.bind("<KeyRelease>", lambda e: self._calc())
            self.vars.append(var)

        colors = ["#ff4444", "#43a047", "#1e88e5", "#fdd835", "#ffffff"]
        self.led_color = tk.StringVar(value=colors[0])
        color_row = ttk.Frame(parent, style="Card.TFrame")
        color_row.grid(row=5, column=0, columnspan=2, sticky="w", padx=16, pady=4)
        ttk.Label(color_row, text=t("diode.led_color"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        for c in colors:
            b = tk.Button(color_row, bg=c, width=2, relief="ridge",
                          command=lambda c=c: self._set_color(c))
            b.pack(side="left", padx=2)

        self.result = tk.StringVar()
        ttk.Label(parent, textvariable=self.result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left", wraplength=420)\
            .grid(row=6, column=0, columnspan=2, sticky="w", padx=16, pady=(6, 12))
        self._calc()

    def _set_color(self, c):
        self.led_color.set(c)
        self._calc()

    def _calc(self):
        draw_diode(self.canvas, is_led=True, led_color=self.led_color.get())
        try:
            vs = float(self.vars[0].get())
            vf = float(self.vars[1].get())
            i_ma = float(self.vars[2].get())
            i = i_ma / 1000
            if vs <= vf:
                self.result.set(t("diode.supply_must_exceed"))
                return
            r = (vs - vf) / i
            p = i ** 2 * r
            self.result.set(f"{t('diode.resistor_result')} = {r:.1f} Ω\n"
                             f"{t('diode.power_result')}: {p*1000:.1f} mW")
        except Exception:
            self.result.set(t("common.enter_valid_numbers"))

    def _build_table(self, parent):
        frame = ttk.Frame(parent, style="Card.TFrame")
        header = tk.Frame(frame, bg=ACCENT_C, height=6)
        header.pack(fill="x")
        ttk.Label(frame, text=t("diode.table_title"), font=FONT_H2, wraplength=320,
                  justify="left", style="CardSub.TLabel").pack(anchor="w", padx=16, pady=(10, 6))
        table = ttk.Treeview(frame, columns=("type", "vf", "use"), show="headings", height=7)
        table.heading("type", text=t("diode.table.type"))
        table.heading("vf", text=t("diode.table.vf"))
        table.heading("use", text=t("diode.table.use"))
        table.column("type", width=78)
        table.column("vf", width=68)
        table.column("use", width=165)
        for row in _diode_types():
            table.insert("", "end", values=row)
        table.pack(fill="x", padx=16, pady=(0, 16))
        return frame

    # ------------------------------------------------------------------
    def _build_chart(self, parent):
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        controls = ttk.Frame(parent, style="Card.TFrame")
        controls.grid(row=0, column=0, sticky="ns", padx=(16, 8), pady=16)

        ttk.Label(controls, text=t("diode.chart.title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(controls, text=t("common.mode"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=1, column=0, sticky="w", pady=4)
        self.mode = tk.StringVar(value="AC")
        mode_cb = ttk.Combobox(controls, textvariable=self.mode, values=["AC", "DC"],
                                state="readonly", width=8)
        mode_cb.grid(row=1, column=1, sticky="w", pady=4)
        mode_cb.bind("<<ComboboxSelected>>", lambda e: self._rebuild_fields())

        self.field_frame = ttk.Frame(controls, style="Card.TFrame")
        self.field_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=6)
        self.field_vars = {}

        ttk.Button(controls, text=t("common.simulate"), command=self._simulate)\
            .grid(row=3, column=0, columnspan=2, pady=(10, 6), sticky="ew")

        self.note_var = tk.StringVar()
        ttk.Label(controls, textvariable=self.note_var, font=("Segoe UI", 9), foreground=ACCENT_C,
                  style="CardBody.TLabel", wraplength=220, justify="left")\
            .grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))

        chart_wrap = ttk.Frame(parent, style="Card.TFrame")
        chart_wrap.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        self.chart = MplChartFrame(chart_wrap)
        self.chart.pack(fill="both", expand=True)

        self._rebuild_fields()

    def _rebuild_fields(self):
        for child in self.field_frame.winfo_children():
            child.destroy()
        self.field_vars = {}
        if self.mode.get() == "DC":
            fields = [("is_amps", t("diode.chart.dc_field_is"), "1e-12"),
                      ("n", t("diode.chart.dc_field_n"), "1.8")]
        else:
            fields = [("vf", t("diode.chart.ac_field_vf"), "0.7"),
                      ("amplitude", t("diode.chart.ac_field_amp"), "5"),
                      ("frequency", t("common.frequency"), "60"),
                      ("r_load", t("diode.chart.ac_field_rload"), "1000")]
        for i, (key, label, default) in enumerate(fields):
            ttk.Label(self.field_frame, text=label, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=i, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=default)
            ttk.Entry(self.field_frame, textvariable=var, width=10).grid(row=i, column=1, pady=3, padx=(6, 0))
            self.field_vars[key] = var
        self._simulate()

    def _simulate(self):
        try:
            kwargs = {key: parse_value(var.get()) for key, var in self.field_vars.items()}
        except Exception:
            self.note_var.set(t("common.enter_valid_values"))
            return

        self.chart.clear()
        ax = self.chart.fig.add_subplot(111)
        ax.set_facecolor(PLOT_BG)

        if self.mode.get() == "DC":
            v, i = diode_dc_curve(**kwargs)
            ax.plot(v, i * 1000, color=V_COLOR, linewidth=2)
            ax.set_xlabel(t("diode.chart.dc_xlabel"))
            ax.set_ylabel(t("diode.chart.dc_ylabel"))
            ax.set_title(t("diode.chart.dc_title"), fontsize=11)
            ax.grid(True, alpha=0.25)
            include_zero(ax, axis="y")
            include_zero(ax, axis="x")
            note = t("diode.chart.dc_note")
        else:
            t_arr, vin, vout, i = diode_rectifier(**kwargs)
            ax1 = ax
            ax1.plot(t_arr, vin, color=V_COLOR, linewidth=1.5, label=t("diode.chart.legend_vin"))
            ax1.plot(t_arr, vout, color="#2A9D8F", linewidth=2, label=t("diode.chart.legend_vout"))
            ax1.set_xlabel(t("common.time_s"))
            ax1.set_ylabel(t("common.voltage"))
            ax1.legend(loc="upper right", fontsize=8)
            ax1.set_title(t("diode.chart.ac_title"), fontsize=11)
            ax1.grid(True, alpha=0.25)
            include_zero(ax1)
            note = t("diode.chart.ac_note")

        self.chart.fig.tight_layout()
        self.chart.redraw()
        self.note_var.set(note)

    # ------------------------------------------------------------------
    def _build_bridge4(self, parent):
        """4-diode bridge: animated schematic (which diode pair conducts in each
        half-cycle), live results, and the smoothing-capacitor option. The load
        value only matters once a capacitor is fitted (without it the output
        waveform is just |Vin| - 2Vf whatever the load), so RL and C are only
        shown after the capacitor is switched on."""
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        sf = ScrollableFrame(parent, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body
        body.columnconfigure(1, weight=1)

        ttk.Label(body, text=t("diode.bridge4.title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 2))
        intro = ttk.Label(body, text=t("diode.bridge4.intro"), font=FONT_BODY, style="CardBody.TLabel",
                          justify="left", wraplength=800)
        intro.grid(row=1, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 8))
        body.bind("<Configure>", lambda e: intro.configure(wraplength=max(300, e.width - 40)), add="+")

        left = ttk.Frame(body, style="Card.TFrame")
        left.grid(row=2, column=0, sticky="nw", padx=(16, 8))
        self.b4_canvas = tk.Canvas(left, width=400, height=250, bg="#fdfaf3", highlightthickness=0)
        self.b4_canvas.grid(row=0, column=0, columnspan=3, pady=(0, 8))
        self.b4_phase_var = tk.StringVar()
        ttk.Label(left, textvariable=self.b4_phase_var, font=("Segoe UI", 9, "bold"), foreground="#d97706",
                  style="CardBody.TLabel").grid(row=1, column=0, columnspan=3, sticky="w")

        fields = [("amplitude", t("diode.bridge.amplitude"), "12"),
                  ("frequency", t("diode.bridge.frequency"), "50"),
                  ("vf", t("diode.bridge.vf"), "0.7")]
        self.b4_vars = {}
        for i, (key, label, default) in enumerate(fields):
            ttk.Label(left, text=label, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=2 + i, column=0, sticky="w", pady=2)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(left, textvariable=var, width=10)
            entry.grid(row=2 + i, column=1, sticky="w", pady=2, padx=(6, 0))
            entry.bind("<KeyRelease>", lambda e: self._simulate_bridge4())
            self.b4_vars[key] = var

        self.b4_cap_on = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text=t("diode.bridge.add_cap_chk"), variable=self.b4_cap_on,
                        command=self._toggle_bridge4_cap).grid(row=5, column=0, columnspan=3, sticky="w", pady=(8, 2))
        self.b4_cap_row = ttk.Frame(left, style="Card.TFrame")
        self.b4_cap_var = tk.StringVar(value="1000u")
        self.b4_rl_var = tk.StringVar(value="100")
        for r, (lbl, var) in enumerate(((t("diode.bridge.cap_value"), self.b4_cap_var),
                                        (t("diode.bridge.rload"), self.b4_rl_var))):
            ttk.Label(self.b4_cap_row, text=lbl, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=r, column=0, sticky="w", pady=2)
            e = ttk.Entry(self.b4_cap_row, textvariable=var, width=10)
            e.grid(row=r, column=1, sticky="w", padx=(6, 0), pady=2)
            e.bind("<KeyRelease>", lambda ev: self._simulate_bridge4())
        ttk.Label(self.b4_cap_row, text=t("diode.bridge.rl_hint"), font=("Segoe UI", 8), foreground="#777",
                  style="CardBody.TLabel", wraplength=360, justify="left").grid(row=2, column=0, columnspan=2, sticky="w")

        self.b4_result = tk.StringVar()
        ttk.Label(left, textvariable=self.b4_result, font=("Consolas", 10, "bold"), foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left").grid(row=7, column=0, columnspan=3, sticky="w", pady=(8, 2))
        self.b4_note = tk.StringVar()
        ttk.Label(left, textvariable=self.b4_note, font=("Segoe UI", 9), style="CardBody.TLabel",
                  wraplength=390, justify="left").grid(row=8, column=0, columnspan=3, sticky="w", pady=(4, 12))

        chart_wrap = ttk.Frame(body, style="Card.TFrame")
        chart_wrap.grid(row=2, column=1, sticky="nsew", padx=(8, 16))
        self.b4_chart = MplChartFrame(chart_wrap, figsize=(6.0, 4.6))
        self.b4_chart.pack(fill="both", expand=True)

        self._b4_phase = 0
        self._b4_after = None
        self._simulate_bridge4()
        self._b4_animate()

    def _b4_animate(self):
        try:
            if not self.b4_canvas.winfo_exists():
                return
        except tk.TclError:
            return
        if not is_shown(self.b4_canvas):
            self._b4_after = self.b4_canvas.after(500, self._b4_animate)
            return
        self._b4_phase ^= 1
        self._draw_bridge4()
        self._b4_after = self.b4_canvas.after(1300, self._b4_animate)

    def _toggle_bridge4_cap(self):
        if self.b4_cap_on.get():
            self.b4_cap_row.grid(row=6, column=0, columnspan=3, sticky="w", pady=(0, 4))
        else:
            self.b4_cap_row.grid_remove()
        self._simulate_bridge4()

    def _draw_bridge4(self):
        import symbols as sym
        c = self.b4_canvas
        c.delete("all")
        pos = self._b4_phase == 0
        cap = self.b4_cap_on.get()
        on_col, off_col = "#d97706", "#9aa3b2"
        cx, cy, r = 190, 125, 70
        L, T, R, B = (cx - r, cy), (cx, cy - r), (cx + r, cy), (cx, cy + r)
        # diodes: (anode, cathode, name, conducts on positive half?)
        diodes = [(L, T, "D1", True), (R, T, "D2", False), (B, L, "D3", False), (B, R, "D4", True)]
        for (a, k, name, on_pos) in diodes:
            active = on_pos == pos
            col = on_col if active else off_col
            sym.diode(c, a[0], a[1], k[0], k[1], s=0.8, color=col, fill=col if active else "")
            mx, my = (a[0] + k[0]) / 2, (a[1] + k[1]) / 2
            dx = -16 if mx < cx else 16
            dy = -12 if my < cy else 12
            c.create_text(mx + dx, my + dy, text=name, font=("Segoe UI", 9, "bold"), fill=col)
        for p in (L, T, R, B):
            sym.node(c, p[0], p[1])
        # AC source on the left: top to L, bottom around to R
        sx = 40
        wire = lambda *pts, col=sym.SYM_COLOR: sym.wire(c, *pts, color=col, width=2 if col == sym.SYM_COLOR else 3)  # noqa
        a_col = on_col
        wire(sx, cy - 16, sx, cy - r - 25, L[0] - 30, cy - r - 25, L[0] - 30, cy, L[0], cy,
             col=a_col if pos else sym.SYM_COLOR)
        wire(sx, cy + 16, sx, cy + r + 25, R[0], cy + r + 25, R[0], cy, col=a_col if not pos else sym.SYM_COLOR)
        sym.ac_source(c, sx, cy)
        c.create_text(sx - 20, cy, text="~Vin", anchor="e", font=("Segoe UI", 8, "bold"), fill=sym.LABEL_COLOR)
        # load side: T -> right rail, B -> right rail
        xr = cx + r + 90
        wire(T[0], T[1], T[0], cy - r - 10, xr, cy - r - 10, col=a_col)
        wire(B[0], B[1], B[0], cy + r + 10, xr, cy + r + 10, col=a_col)
        if cap:
            xc = xr - 40
            sym.node(c, xc, cy - r - 10)
            sym.node(c, xc, cy + r + 10)
            sym.wire(c, xc, cy - r - 10, xc, cy - 14)
            sym.capacitor(c, xc, cy - 14, xc, cy + 14, variant="polarized", s=0.9, label="C", label_side=-1)
            sym.wire(c, xc, cy + 14, xc, cy + r + 10)
            load_lbl = "RL"
        else:
            load_lbl = t("diode.bridge.load_generic")
        sym.resistor(c, xr, cy - r - 10, xr, cy + r + 10, label=load_lbl, s=0.9, label_side=1)
        c.create_text(xr + 14, cy - r - 10, text="+", font=("Segoe UI", 12, "bold"), fill="#c62828")
        c.create_text(xr + 14, cy + r + 10, text="−", font=("Segoe UI", 12, "bold"), fill=sym.SYM_COLOR)
        # current through the load is always downward (+ to -)
        sym.current_arrow(c, xr + 26, cy - 20, xr + 26, cy + 20, color=on_col)
        self.b4_phase_var.set(t("diode.bridge.phase_pos") if pos else t("diode.bridge.phase_neg"))

    def _simulate_bridge4(self):
        try:
            kw = {key: parse_value(var.get()) for key, var in self.b4_vars.items()}
            cap = parse_value(self.b4_cap_var.get()) if self.b4_cap_on.get() else None
            rl = parse_value(self.b4_rl_var.get()) if self.b4_cap_on.get() else 1000.0
            if kw["amplitude"] <= 0 or kw["frequency"] <= 0 or rl <= 0 or (cap is not None and cap <= 0):
                raise ValueError
        except Exception:
            self.b4_note.set(t("common.enter_valid_values"))
            return
        self._draw_bridge4()
        f = kw["frequency"]
        vp, vf = kw["amplitude"], kw["vf"]
        tt = np.linspace(0, 4 / f, 8000)
        vin = vp * np.sin(2 * np.pi * f * tt)
        raw = np.clip(np.abs(vin) - 2 * vf, 0, None)
        vpk = max(vp - 2 * vf, 0.0)
        lines = [f"Vin peak       = {vp:.3g} V   ({vp / np.sqrt(2):.3g} V rms)",
                 f"Vout peak      = Vp − 2·Vf = {vpk:.3g} V",
                 f"PIV per diode  ≈ {max(vp - vf, 0):.3g} V",
                 f"Output pulses  = 2·f = {2 * f:g} Hz"]
        if cap is None:
            vout = raw
            lines.insert(2, f"Vdc (average)  = 2·Vpk/π ≈ {2 * vpk / np.pi:.3g} V")
            lines.append(f"Ripple (p-p)   = {vpk:.3g} V  (100 %)")
        else:
            vout = np.zeros_like(raw)
            dt = tt[1] - tt[0]
            for k in range(1, len(tt)):
                decay = vout[k - 1] * np.exp(-dt / (rl * cap))
                vout[k] = raw[k] if raw[k] >= decay else decay
            last = tt >= 2 / f
            vmax, vmin = float(vout[last].max()), float(vout[last].min())
            vdc = float(vout[last].mean())
            iload = vdc / rl
            charging = (raw >= vout - 1e-9) & (raw > 0)
            dvdt = np.gradient(vout, dt)
            i_diode = np.where(charging, cap * dvdt + vout / rl, 0.0)
            ipk = float(i_diode[last].max())
            cond = float(charging[last].mean()) * 100
            lines.insert(2, f"Vdc (average)  ≈ {vdc:.3g} V    I load ≈ {iload * 1e3:.3g} mA")
            lines.append(f"Ripple (p-p)   = {vmax - vmin:.3g} V  ({(vmax - vmin) / vdc * 100 if vdc else 0:.1f} %)"
                         f"   formula ≈ I/(2fC) = {iload / (2 * f * cap):.3g} V")
            lines.append(f"Diode peak I   ≈ {ipk:.3g} A   (conducts {cond:.0f} % of the time)")
        self.b4_result.set("\n".join(lines))
        self.b4_note.set(t("diode.bridge4.note_smoothed") if cap else t("diode.bridge4.note"))

        fig = self.b4_chart.fig
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_facecolor(PLOT_BG)
        tm = tt * 1e3
        ax.plot(tm, vin, color=V_COLOR, lw=1.2, alpha=0.8, label=t("diode.bridge.legend_vin"))
        if cap is not None:
            ax.plot(tm, raw, color="#999999", lw=1.1, ls=":", label=t("diode.bridge.legend_vout_before"))
            ax.fill_between(tm, vout, vmin, where=tt >= 2 / f, color="#2A9D8F", alpha=0.12)
        ax.plot(tm, vout, color="#2A9D8F", lw=2.2,
                label=t("diode.bridge.legend_vout_smoothed") if cap else t("diode.bridge.legend_vout"))
        ax.axhline(0, color="#333", lw=1)
        # shade which diode pair conducts
        half = 1 / (2 * f)
        for k in range(8):
            if k % 2 == 1:
                ax.axvspan(k * half * 1e3, (k + 1) * half * 1e3, color="#d97706", alpha=0.05, lw=0)
        for k, lab in ((0, "D1+D4"), (1, "D2+D3")):
            ax.text((k + 0.5) * half * 1e3, vp * 1.1, lab, fontsize=7, color="#b45309", ha="center", va="bottom")
        ax.set_ylim(-vp * 1.15, vp * 1.25)
        ax.set_xlabel("t (ms)")
        ax.set_ylabel("V")
        ax.set_ylim(-vp * 1.18, vp * 1.18)
        ax.grid(True, alpha=0.25)
        ax.legend(loc="lower right", fontsize=8)
        ax.set_title(t("diode.bridge.chart_title"), fontsize=11)
        fig.tight_layout()
        self.b4_chart.redraw()
