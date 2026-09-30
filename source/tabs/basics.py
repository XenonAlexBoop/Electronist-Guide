import math
import tkinter as tk
from tkinter import ttk
from data import get_theory
from widgets import parse_value, format_value, ScrollableFrame, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ACCENT
from i18n import t, register

register({"basics.live.iv": ("I-V line of the resistor (slope = 1/R)", "Dreapta I-U a rezistorului (panta = 1/R)")})
from tabs.kirchhoff import KirchhoffTab

ACCENT_C = ACCENT["basics"]


class BasicsTab(ttk.Frame):
    """AC/DC Basics top-level tab: an inner notebook holding the Ohm's Law
    calculator/simulator and the Kirchhoff's Laws (KVL/KCL) demos as
    separate sub-tabs."""

    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=t("basics.tab_title"), font=FONT_H1, style="TabTitle.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))

        ohms_page = OhmsLawPanel(nb)
        kirchhoff_page = KirchhoffTab(nb)
        nb.add(ohms_page, text=t("basics.subtab.ohms_law"))
        nb.add(kirchhoff_page, text=t("basics.subtab.kirchhoff"))
        from widgets import lazy_tab
        from .learn import learn_page
        lazy_tab(nb, t("common.learn"), lambda p: learn_page(p, ACCENT_C, ["basics", "kirchhoff"]))


class OhmsLawPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        left_wrap = ttk.Frame(self, style="Card.TFrame")
        left_wrap.grid(row=0, column=0, sticky="nsew", pady=10)
        left_wrap.columnconfigure(0, weight=1)
        left_wrap.rowconfigure(0, weight=1)

        left_scroll = ScrollableFrame(left_wrap, style="Card.TFrame")
        left_scroll.grid(row=0, column=0, sticky="nsew")
        left = left_scroll.body

        # v6.2: calculator and live simulator side by side (theory -> Learn tab)
        left.columnconfigure(0, weight=1, uniform="o")
        left.columnconfigure(1, weight=1, uniform="o")
        calc = ttk.Frame(left, style="Card.TFrame")
        calc.grid(row=0, column=0, sticky="nsew")
        live = ttk.Frame(left, style="Card.TFrame")
        live.grid(row=0, column=1, sticky="nsew")
        live.columnconfigure(0, weight=1)
        self._build_calculator(calc)
        self._build_live_simulator(live)

    def _build_calculator(self, parent):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(parent, text=t("basics.ohms_triangle_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", **pad)

        from uikit import FitCanvas
        self.canvas = FitCanvas(parent, 280, 240, kmax=1.35, height=300)
        self.canvas.grid(row=1, column=0, rowspan=4, padx=16, pady=6, sticky="nsew")
        parent.columnconfigure(0, weight=1)
        self._draw_triangle()

        ttk.Label(parent, text=t("basics.fill_two"), font=FONT_BODY, style="CardBody.TLabel",
                  wraplength=260, justify="left").grid(row=1, column=1, columnspan=2, sticky="w", padx=(0, 16))

        self.v_var = tk.StringVar()
        self.i_var = tk.StringVar()
        self.r_var = tk.StringVar()
        # Label and Entry each get their OWN column now (were previously
        # sharing one cell via sticky="w"/"e", which only worked as long as
        # the label text was short enough not to run into the entry box -
        # with longer label text and a narrower panel, that overlap clipped
        # the label).
        ttk.Label(parent, text=t("basics.voltage_v"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=2, column=1, sticky="w", padx=(0, 8))
        ttk.Entry(parent, textvariable=self.v_var, width=10).grid(row=2, column=2, sticky="w", padx=(0, 16))
        ttk.Label(parent, text=t("basics.current_i"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=3, column=1, sticky="w", padx=(0, 8))
        ttk.Entry(parent, textvariable=self.i_var, width=10).grid(row=3, column=2, sticky="w", padx=(0, 16))
        ttk.Label(parent, text=t("basics.resistance_r"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=4, column=1, sticky="w", padx=(0, 8))
        ttk.Entry(parent, textvariable=self.r_var, width=10).grid(row=4, column=2, sticky="w", padx=(0, 16))

        ttk.Button(parent, text=t("basics.solve"), command=self._solve)\
            .grid(row=5, column=0, columnspan=3, pady=8)

        self.result = tk.StringVar()
        ttk.Label(parent, textvariable=self.result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left", wraplength=420)\
            .grid(row=6, column=0, columnspan=3, sticky="w", padx=16, pady=(0, 10))

        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=7, column=0, columnspan=3, sticky="ew", padx=16, pady=6)

        ttk.Label(parent, text=t("basics.rms_peak_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=8, column=0, columnspan=3, sticky="w", padx=16, pady=(4, 4))
        prow = ttk.Frame(parent, style="Card.TFrame")
        prow.grid(row=9, column=0, columnspan=3, sticky="w", padx=16)
        ttk.Label(prow, text=t("basics.peak_voltage"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self.peak_var = tk.StringVar(value="325")
        entry = ttk.Entry(prow, textvariable=self.peak_var, width=10)
        entry.pack(side="left", padx=8)
        entry.bind("<KeyRelease>", lambda e: self._rms())
        self.rms_result = tk.StringVar()
        ttk.Label(parent, textvariable=self.rms_result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=10, column=0, columnspan=3, sticky="w", padx=16, pady=(4, 4))
        self.sine_cv = FitCanvas(parent, 520, 200, kmax=1.3, height=210)
        self.sine_cv.grid(row=11, column=0, columnspan=3, sticky="nsew", padx=16, pady=(4, 14))
        self._rms()

    def _draw_triangle(self):
        self.canvas.show(self._paint_triangle)

    def _paint_triangle(self):
        c = self.canvas
        cx, top = 140, 30
        p1 = (cx, top)
        p2 = (40, 200)
        p3 = (240, 200)
        c.create_polygon(p1, p2, p3, fill="", outline="#334155", width=3)
        c.create_line(60, 143, 220, 143, fill="#334155", width=2)
        c.create_text(cx, 90, text="V", font=("Segoe UI", 22, "bold"), fill=ACCENT_C)
        c.create_text(90, 170, text="I", font=("Segoe UI", 22, "bold"), fill=ACCENT_C)
        c.create_text(190, 170, text="R", font=("Segoe UI", 22, "bold"), fill=ACCENT_C)

    def _solve(self):
        vals = {}
        for key, var in (("V", self.v_var), ("I", self.i_var), ("R", self.r_var)):
            txt = var.get().strip()
            if txt:
                try:
                    vals[key] = float(txt)
                except ValueError:
                    self.result.set(f"'{txt}' {t('basics.not_valid_number')} {key}")
                    return
        if len(vals) != 2:
            self.result.set(t("basics.fill_exactly_two"))
            return
        if "V" not in vals:
            v = vals["I"] * vals["R"]
            self.v_var.set(f"{v:g}")
            self.result.set(f"V = I × R = {v:g} V")
        elif "I" not in vals:
            if vals["R"] == 0:
                self.result.set(t("basics.r_cannot_be_zero"))
                return
            i = vals["V"] / vals["R"]
            self.i_var.set(f"{i:g}")
            self.result.set(f"I = V / R = {i:g} A")
        else:
            if vals["I"] == 0:
                self.result.set(t("basics.i_cannot_be_zero"))
                return
            r = vals["V"] / vals["I"]
            self.r_var.set(f"{r:g}")
            self.result.set(f"R = V / I = {r:g} Ω")

    def _rms(self):
        try:
            peak = float(self.peak_var.get())
            rms = peak / math.sqrt(2)
            self.rms_result.set(f"Vrms = Vpeak / √2 = {rms:.2f} V      Vpp = 2·Vpeak = {2 * peak:.4g} V")
        except Exception:
            self.rms_result.set("")
            return
        self.sine_cv.show(lambda: self._paint_sine(peak, rms))

    def _paint_sine(self, peak, rms):
        c = self.sine_cv
        x0, x1, ym, a = 120, 470, 100, 80
        c.create_line(x0, ym, x1, ym, fill="#bbb")
        pts = []
        for k in range(201):
            x = x0 + (x1 - x0) * k / 200
            pts += [x, ym - a * math.sin(2 * math.pi * 1.5 * k / 200)]
        c.create_line(*pts, fill="#c0392b", width=2, smooth=True)
        yr = ym - a / math.sqrt(2)
        for y, col, txt in ((ym - a, "#1f2a44", f"Vpeak {peak:.4g} V"), (yr, ACCENT_C, f"Vrms {rms:.4g} V"),
                            (ym + a, "#1f2a44", f"−Vpeak")):
            c.create_line(x0, y, x1, y, fill=col, dash=(4, 3))
            c.create_text(x0 - 4, y, text=txt, anchor="e", font=("Segoe UI", 8, "bold"), fill=col)
        c.create_line(x1 + 8, ym - a, x1 + 8, ym + a, arrow="both", fill="#8e44ad")
        c.create_text(x1 + 12, ym, text="Vpp", anchor="w", font=("Segoe UI", 8, "bold"), fill="#8e44ad")

    # ------------------------------------------------------------------
    # Interactive Ohm's Law slider simulator: pick one quantity to "lock"
    # (it stops moving), then drag either of the other two sliders and
    # watch the third one react live, since V = I x R always has to hold.
    # Only one quantity can be locked at a time.
    # ------------------------------------------------------------------
    SLIDER_SPECS = {
        "V": {"from_": 0.0, "to": 24.0, "unit": "V", "resolution": 0.1},
        "I": {"from_": 1.0, "to": 2000.0, "unit": "mA", "resolution": 1.0},   # stored/shown in mA
        "R": {"from_": 1.0, "to": 1000.0, "unit": "Ω", "resolution": 1.0},
    }

    def _build_live_simulator(self, parent):
        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=11, column=0, columnspan=2, sticky="ew", padx=16, pady=(10, 6))

        ttk.Label(parent, text=t("basics.live.title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=12, column=0, columnspan=2, sticky="w", padx=16, pady=(4, 2))
        ttk.Label(parent, text=t("basics.live.intro"), font=FONT_BODY, wraplength=420,
                  justify="left", style="CardBody.TLabel")\
            .grid(row=13, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 10))

        # values are always stored in base SI units (V, A, Ohm) internally;
        # the I slider just displays/steps in mA for a nicer range to drag.
        self._live_values = {"V": 12.0, "I": 0.024, "R": 500.0}  # 12V, 24mA, 500ohm -> consistent
        self._live_locked = tk.StringVar(value="V")
        self._live_scales = {}
        self._live_readouts = {}
        self._live_updating = False  # re-entrancy guard while we programmatically move a slider

        grid = ttk.Frame(parent, style="Card.TFrame")
        grid.grid(row=14, column=0, columnspan=2, sticky="ew", padx=16, pady=(0, 6))
        grid.columnconfigure(2, weight=1)

        row_labels = {"V": t("basics.live.voltage"), "I": t("basics.live.current"), "R": t("basics.live.resistance")}
        for i, key in enumerate(["V", "I", "R"]):
            spec = self.SLIDER_SPECS[key]
            ttk.Radiobutton(grid, text=t("basics.live.lock"), variable=self._live_locked, value=key,
                             command=self._on_live_lock_change).grid(row=i, column=0, sticky="w", padx=(0, 6), pady=6)
            ttk.Label(grid, text=row_labels[key], font=FONT_BODY, style="CardBody.TLabel", width=11)\
                .grid(row=i, column=1, sticky="w", pady=6)
            scale = ttk.Scale(grid, from_=spec["from_"], to=spec["to"], orient="horizontal",
                               command=lambda v, k=key: self._on_live_slider(k, v))
            scale.grid(row=i, column=2, sticky="ew", padx=(6, 10), pady=6)
            self._live_scales[key] = scale
            readout = tk.StringVar()
            ttk.Label(grid, textvariable=readout, font=FONT_MONO, foreground=ACCENT_C,
                      style="CardFormula.TLabel", width=11).grid(row=i, column=3, sticky="e", pady=6)
            self._live_readouts[key] = readout

        self.live_note = tk.StringVar()
        ttk.Label(parent, textvariable=self.live_note, font=("Segoe UI", 9), foreground="#777",
                  style="CardBody.TLabel", wraplength=420, justify="left")\
            .grid(row=15, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 14))

        # v6.3: the circuit and its I-V line react to the sliders
        from uikit import FitCanvas
        from charts import MplChartFrame
        pics = ttk.Frame(parent, style="Card.TFrame")
        pics.grid(row=16, column=0, columnspan=2, sticky="nsew", padx=16, pady=(0, 14))
        pics.columnconfigure(0, weight=1, uniform="pp")
        pics.columnconfigure(1, weight=1, uniform="pp")
        self.live_cv = FitCanvas(pics, 360, 240, kmax=1.5, height=330)
        self.live_cv.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.live_chart = MplChartFrame(pics, figsize=(3.6, 2.6), with_toolbar=False)
        self.live_chart.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.live_chart.canvas.get_tk_widget().configure(height=330)

        self._sync_live_sliders()
        self._on_live_lock_change()

    def _live_pictures(self):
        if not hasattr(self, "live_cv"):
            return
        v, i, r = self._live_values["V"], self._live_values["I"], self._live_values["R"]
        import symbols as sym
        from uikit import eng

        def paint():
            c = self.live_cv
            x0, x1, y0, y1 = 70, 290, 50, 200
            sym.wire(c, x0, y0, x0, (y0 + y1) / 2 - 18)
            sym.wire(c, x0, (y0 + y1) / 2 + 18, x0, y1)
            sym.dc_source(c, x0, (y0 + y1) / 2)
            c.create_text(x0 - 24, (y0 + y1) / 2, text=f"{v:.3g} V", anchor="e", font=("Segoe UI", 11, "bold"),
                          fill="#c62828")
            sym.wire(c, x0, y0, x1, y0, x1, 85)
            sym.resistor(c, x1, 85, x1, 165, label="R", value=eng(r, "Ω"), label_side=-1)
            sym.wire(c, x1, 165, x1, y1, x0, y1)
            # arrow thickness follows the current (log scale, 1 mA .. 2 A)
            import math
            w = 1.5 + 5 * max(0.0, min(1.0, (math.log10(max(i, 1e-4)) + 3) / 3.3))
            c.create_line(120, y0 - 12, 240, y0 - 12, fill="#1f6fb2", width=w, arrow="last",
                          arrowshape=(10 + w, 12 + w, 4 + w / 2))
            c.create_text(180, y0 - 28, text=f"I = {eng(i, 'A')}", font=("Segoe UI", 11, "bold"), fill="#1f6fb2")
            c.create_text(180, 225, text=f"P = V·I = {eng(v * i, 'W')}", font=("Segoe UI", 11, "bold"),
                          fill="#8e44ad")
        self.live_cv.show(paint)
        import numpy as np
        fig = self.live_chart.fig
        fig.clear()
        ax = fig.add_subplot(111)
        vv = np.linspace(0, 24, 50)
        ax.plot(vv, vv / r * 1e3, color=ACCENT_C, lw=2, label=f"R = {r:.3g} Ω")
        ax.plot([v], [i * 1e3], "o", color="#c62828", ms=8, zorder=5)
        ax.set_xlim(0, 24)
        ax.set_ylim(0, max(50, min(2000, 24 / r * 1e3 * 1.05)))
        ax.set_xlabel("V (V)", fontsize=9)
        ax.set_ylabel("I (mA)", fontsize=9)
        ax.set_title(t("basics.live.iv"), fontsize=9)
        ax.tick_params(labelsize=8)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="upper left")
        try:
            fig.tight_layout(pad=0.6)
        except Exception:
            pass
        self.live_chart.redraw()

    def _live_display_value(self, key):
        """Slider/readout units: V in volts, I in mA, R in ohms."""
        v = self._live_values[key]
        return v * 1000.0 if key == "I" else v

    def _sync_live_sliders(self):
        """Push the internal values onto the widgets without re-triggering
        the slider callbacks (used after a computed/programmatic update)."""
        self._live_updating = True
        try:
            for key in ["V", "I", "R"]:
                disp = self._live_display_value(key)
                spec = self.SLIDER_SPECS[key]
                disp = max(spec["from_"], min(spec["to"], disp))
                self._live_scales[key].set(disp)
                unit = spec["unit"]
                self._live_readouts[key].set(f"{self._live_display_value(key):.3g} {unit}")
        finally:
            self._live_updating = False
        self._live_pictures()

    def _on_live_lock_change(self):
        locked = self._live_locked.get()
        for key, scale in self._live_scales.items():
            scale.configure(state="disabled" if key == locked else "normal")
        self.live_note.set(t("basics.live.locked_note").format(param=locked))

    def _on_live_slider(self, key, value_str):
        if self._live_updating:
            return
        locked = self._live_locked.get()
        if key == locked:
            return  # shouldn't happen (slider is disabled), but be safe

        try:
            disp_val = float(value_str)
        except ValueError:
            return
        raw_val = disp_val / 1000.0 if key == "I" else disp_val
        self._live_values[key] = raw_val

        v, i, r = self._live_values["V"], self._live_values["I"], self._live_values["R"]
        third = [k for k in ("V", "I", "R") if k not in (key, locked)][0]

        if locked == "V":
            if third == "R" and i > 0:
                self._live_values["R"] = v / i
            elif third == "I" and r > 0:
                self._live_values["I"] = v / r
        elif locked == "I":
            if third == "R" and i > 0:
                self._live_values["R"] = v / i
            elif third == "V":
                self._live_values["V"] = i * r
        else:  # locked == "R"
            if third == "I" and r > 0:
                self._live_values["I"] = v / r
            elif third == "V":
                self._live_values["V"] = i * r

        self._sync_live_sliders()
