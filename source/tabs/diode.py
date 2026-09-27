import tkinter as tk
from tkinter import ttk
from data import get_theory
from drawing import draw_diode, draw_bridge_4diode
from widgets import TheoryPanel, ScrollableFrame, parse_value, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ACCENT
from charts import (MplChartFrame, diode_dc_curve, diode_rectifier,
                     four_diode_bridge_signals, V_COLOR, I_COLOR, PLOT_BG, include_zero)
from i18n import t
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
        chart_tab = ttk.Frame(nb, style="Card.TFrame")
        bridge4_tab = ttk.Frame(nb, style="Card.TFrame")
        nb.add(calc_tab, text=t("diode.subtab.calc"))
        nb.add(chart_tab, text=t("diode.subtab.chart"))
        nb.add(bridge4_tab, text=t("diode.subtab.bridge4"))

        self._build_calculator(calc_tab)
        self._build_chart(chart_tab)
        self._build_bridge4(bridge4_tab)

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
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        controls = ttk.Frame(parent, style="Card.TFrame")
        controls.grid(row=0, column=0, sticky="ns", padx=(16, 8), pady=16)

        ttk.Label(controls, text=t("diode.bridge4.title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel", wraplength=280, justify="left")\
            .grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))
        ttk.Label(controls, text=t("diode.bridge4.intro"), font=("Segoe UI", 9), wraplength=280,
                  justify="left", style="CardBody.TLabel").grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.b4_canvas = tk.Canvas(controls, width=280, height=210, bg="#fdfaf3", highlightthickness=0)
        self.b4_canvas.grid(row=2, column=0, columnspan=2, pady=(0, 10))

        fields = [("amplitude", t("diode.bridge.amplitude"), "12"),
                  ("frequency", t("diode.bridge.frequency"), "60"),
                  ("vf", t("diode.bridge.vf"), "0.7"),
                  ("r_load", t("diode.bridge.rload"), "1000")]
        self.b4_vars = {}
        for i, (key, label, default) in enumerate(fields):
            ttk.Label(controls, text=label, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=3 + i, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(controls, textvariable=var, width=10)
            entry.grid(row=3 + i, column=1, pady=3, padx=(6, 0))
            entry.bind("<KeyRelease>", lambda e: self._simulate_bridge4())
            self.b4_vars[key] = var

        self.b4_cap_on = False
        self.b4_cap_var = tk.StringVar(value="100u")
        self.b4_cap_btn = ttk.Button(controls, text=t("diode.bridge.add_cap"), command=self._toggle_bridge4_cap)
        self.b4_cap_btn.grid(row=7, column=0, columnspan=2, sticky="ew", pady=(6, 4))

        self.b4_cap_row = ttk.Frame(controls, style="Card.TFrame")
        ttk.Label(self.b4_cap_row, text=t("diode.bridge.cap_value"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=0, column=0, sticky="w")
        cap_entry = ttk.Entry(self.b4_cap_row, textvariable=self.b4_cap_var, width=10)
        cap_entry.grid(row=0, column=1, padx=(6, 0))
        cap_entry.bind("<KeyRelease>", lambda e: self._simulate_bridge4())
        # not gridded yet — shown only when cap is toggled on

        self.b4_note = tk.StringVar()
        ttk.Label(controls, textvariable=self.b4_note, font=("Segoe UI", 9), foreground=ACCENT_C,
                  style="CardBody.TLabel", wraplength=280, justify="left")\
            .grid(row=9, column=0, columnspan=2, sticky="w", pady=(10, 0))

        chart_wrap = ttk.Frame(parent, style="Card.TFrame")
        chart_wrap.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        self.b4_chart = MplChartFrame(chart_wrap)
        self.b4_chart.pack(fill="both", expand=True)

        self._simulate_bridge4()

    def _toggle_bridge4_cap(self):
        self.b4_cap_on = not self.b4_cap_on
        if self.b4_cap_on:
            self.b4_cap_row.grid(row=8, column=0, columnspan=2, sticky="w", pady=(0, 4))
            self.b4_cap_btn.configure(text=t("diode.bridge.remove_cap"))
        else:
            self.b4_cap_row.grid_remove()
            self.b4_cap_btn.configure(text=t("diode.bridge.add_cap"))
        self._simulate_bridge4()

    def _simulate_bridge4(self):
        try:
            kwargs = {key: parse_value(var.get()) for key, var in self.b4_vars.items()}
            cap_val = parse_value(self.b4_cap_var.get()) if self.b4_cap_on else None
        except Exception:
            self.b4_note.set(t("common.enter_valid_values"))
            return

        draw_bridge_4diode(self.b4_canvas, w=280, h=210, show_cap=self.b4_cap_on,
                            cap_label=self.b4_cap_var.get() if self.b4_cap_on else "")

        t_arr, vin, vout, i, vout_raw = four_diode_bridge_signals(cap=cap_val, **kwargs)

        self.b4_chart.clear()
        ax = self.b4_chart.fig.add_subplot(111)
        ax.set_facecolor(PLOT_BG)
        ax.plot(t_arr, vin, color=V_COLOR, linewidth=1.5, label=t("diode.bridge.legend_vin"))
        if self.b4_cap_on:
            ax.plot(t_arr, vout_raw, color="#999999", linewidth=1.3, linestyle=":",
                    label=t("diode.bridge.legend_vout_before"))
        vout_label = t("diode.bridge.legend_vout_smoothed") if self.b4_cap_on else t("diode.bridge.legend_vout")
        ax.plot(t_arr, vout, color="#2A9D8F", linewidth=2, label=vout_label)
        ax.set_xlabel(t("common.time_s"))
        ax.set_ylabel(t("common.voltage"))
        ax.legend(loc="upper right", fontsize=8)
        ax.set_title(t("diode.bridge.chart_title"), fontsize=11)
        ax.grid(True, alpha=0.25)
        include_zero(ax)
        self.b4_chart.fig.tight_layout()
        self.b4_chart.redraw()
        self.b4_note.set(t("diode.bridge4.note_smoothed") if self.b4_cap_on else t("diode.bridge4.note"))
