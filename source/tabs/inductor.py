import math
import tkinter as tk
from tkinter import ttk
from data import COLOR_CODE, DIGIT_COLORS, TOLERANCE_COLORS, get_theory
from drawing import draw_inductor, draw_transformer, draw_combo_diagram
from widgets import (TheoryPanel, ScrollableFrame, format_value, parse_value, parse_value_list,
                      series_sum, parallel_combo, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ACCENT)
from charts import TimeChartTab, ParamField, inductor_signals
from combos import MixedBuilderPanel
from solver import FormulaSolverPanel, inductor_formulas
from symbols import SymbolGallery
from i18n import t

ACCENT_C = ACCENT["inductor"]


class InductorTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1, minsize=380)
        self.columnconfigure(1, weight=1, minsize=360)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=t("inductor.tab_title"), font=FONT_H1,
                  style="TabTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 6))

        left = ttk.Frame(self, style="Tab.TFrame")
        left.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        right = ttk.Frame(self, style="Card.TFrame")
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        nb = ttk.Notebook(left)
        nb.grid(row=0, column=0, sticky="nsew")

        color_tab = ttk.Frame(nb, style="Card.TFrame")
        reactance_tab = FormulaSolverPanel(nb, inductor_formulas(), ACCENT_C)
        coupling_tab = ttk.Frame(nb, style="Card.TFrame")
        transformer_tab = ttk.Frame(nb, style="Card.TFrame")
        combo_tab = ttk.Frame(nb, style="Card.TFrame")
        nb.add(color_tab, text=t("inductor.subtab.color"))
        nb.add(reactance_tab, text=t("solver.tab"))
        nb.add(coupling_tab, text=t("inductor.subtab.coupling"))
        nb.add(transformer_tab, text=t("inductor.subtab.transformer"))
        nb.add(combo_tab, text=t("inductor.subtab.combo"))

        self._build_color(color_tab)
        self._build_coupling(coupling_tab)
        self._build_transformer(transformer_tab)
        self._build_combo_section(combo_tab)

        chart_tab = TimeChartTab(
            nb, ACCENT_C,
            dc_fields=[
                ParamField("l", t("inductor.chart.dc_field_l"), "10m"),
                ParamField("resistance", t("inductor.chart.dc_field_r"), "100"),
                ParamField("voltage", t("inductor.chart.dc_field_v"), "5"),
            ],
            ac_fields=[
                ParamField("l", t("inductor.chart.dc_field_l"), "10m"),
                ParamField("amplitude", t("resistor.chart.ac_field_amp"), "5"),
                ParamField("frequency", t("common.frequency"), "1000"),
            ],
            signal_fn=inductor_signals,
            dc_note=t("inductor.chart.dc_note"),
            ac_note=t("inductor.chart.ac_note"),
            title=t("inductor.chart.title"),
        )
        nb.add(chart_tab, text=t("inductor.subtab.chart"))

        right_scroll = ScrollableFrame(right, style="Card.TFrame")
        right_scroll.grid(row=0, column=0, sticky="nsew")
        SymbolGallery(right_scroll.body, "inductor", accent=ACCENT_C).pack(fill="x", pady=(0, 8))
        theory = TheoryPanel(right_scroll.body, get_theory("inductor"), accent=ACCENT_C)
        theory.pack(fill="both", expand=True)

    # ---- color code -----------------------------------------------------
    def _build_color(self, parent):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(parent, text=t("inductor.color_intro"),
                  font=FONT_BODY, wraplength=420, style="CardBody.TLabel")\
            .grid(row=0, column=0, columnspan=4, sticky="w", **pad)

        self.band_row_frame = ttk.Frame(parent, style="Card.TFrame")
        self.band_row_frame.grid(row=1, column=0, columnspan=4, sticky="w", padx=16, pady=6)
        labels = [t("resistor.band.digit1"), t("resistor.band.digit2"),
                  t("resistor.band.multiplier"), t("resistor.band.tolerance")]
        options = [DIGIT_COLORS, DIGIT_COLORS, list(COLOR_CODE.keys()), TOLERANCE_COLORS]
        self.band_vars = []
        for i, (label, opts) in enumerate(zip(labels, options)):
            colf = ttk.Frame(self.band_row_frame, style="Card.TFrame")
            colf.grid(row=0, column=i, padx=6)
            ttk.Label(colf, text=label, font=("Segoe UI", 8), style="CardBody.TLabel").pack()
            var = tk.StringVar(value=opts[0])
            cb = ttk.Combobox(colf, textvariable=var, values=opts, state="readonly", width=8)
            cb.pack()
            cb.bind("<<ComboboxSelected>>", lambda e: self._update_color())
            self.band_vars.append(var)

        self.ind_canvas = tk.Canvas(parent, width=460, height=180, bg="#fdfaf3", highlightthickness=0)
        self.ind_canvas.grid(row=2, column=0, columnspan=4, padx=16, pady=6)

        self.ind_result = tk.StringVar()
        ttk.Label(parent, textvariable=self.ind_result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=3, column=0, columnspan=4, sticky="w", padx=16, pady=(0, 12))
        self._update_color()

    def _update_color(self):
        colors = [v.get() for v in self.band_vars]
        draw_inductor(self.ind_canvas, colors)
        try:
            d1, d2, mult_color, tol_color = colors
            base = COLOR_CODE[d1]["digit"] * 10 + COLOR_CODE[d2]["digit"]
            mult = COLOR_CODE[mult_color]["multiplier"]
            uh = base * mult
            tol = COLOR_CODE[tol_color]["tolerance"]
            henries = uh * 1e-6
            self.ind_result.set(f"{t('inductor.inductance_prefix')} {format_value(henries, 'H')}  ( {uh:g} µH )  ±{tol}%")
        except Exception:
            self.ind_result.set(f"{t('inductor.inductance_prefix')} -")

    # ---- reactance --------------------------------------------------
    def _build_reactance(self, parent):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(parent, text=t("inductor.reactance_ind"), font=FONT_BODY,
                  style="CardBody.TLabel").grid(row=0, column=0, sticky="w", **pad)
        self.xl_ind = tk.StringVar(value="10m")
        ttk.Entry(parent, textvariable=self.xl_ind, width=10).grid(row=0, column=1, sticky="w", **pad)

        ttk.Label(parent, text=t("common.frequency"), font=FONT_BODY,
                  style="CardBody.TLabel").grid(row=1, column=0, sticky="w", **pad)
        self.xl_freq = tk.StringVar(value="1000")
        ttk.Entry(parent, textvariable=self.xl_freq, width=10).grid(row=1, column=1, sticky="w", **pad)

        ttk.Button(parent, text=t("inductor.calc_xl"), command=self._calc_reactance)\
            .grid(row=2, column=0, columnspan=2, pady=8)

        self.xl_result = tk.StringVar()
        ttk.Label(parent, textvariable=self.xl_result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", padx=16)
        self._calc_reactance()

    def _calc_reactance(self):
        try:
            l = parse_value(self.xl_ind.get())
            f = float(self.xl_freq.get())
            xl = 2 * math.pi * f * l
            self.xl_result.set(f"XL = 2πfL = {format_value(xl, 'Ω')}")
        except Exception:
            self.xl_result.set(t("inductor.enter_valid_lf"))

    # ---- magnetic coupling ------------------------------------------
    def _build_coupling(self, parent):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(parent, text=t("inductor.coupling_intro"),
                  font=FONT_BODY, wraplength=420, style="CardBody.TLabel")\
            .grid(row=0, column=0, columnspan=2, sticky="w", **pad)

        fields = [(t("inductor.l1"), "10m"), (t("inductor.l2"), "10m"), (t("inductor.mutual_m"), "5m")]
        self.coupling_vars = []
        for i, (label, default) in enumerate(fields):
            ttk.Label(parent, text=label, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=i + 1, column=0, sticky="w", **pad)
            var = tk.StringVar(value=default)
            ttk.Entry(parent, textvariable=var, width=12).grid(row=i + 1, column=1, sticky="w", **pad)
            self.coupling_vars.append(var)

        ttk.Button(parent, text=t("inductor.calc_k"), command=self._calc_coupling)\
            .grid(row=4, column=0, columnspan=2, pady=8)

        self.coupling_result = tk.StringVar()
        ttk.Label(parent, textvariable=self.coupling_result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=5, column=0, columnspan=2, sticky="w", padx=16)
        self._calc_coupling()

    def _calc_coupling(self):
        try:
            l1 = parse_value(self.coupling_vars[0].get())
            l2 = parse_value(self.coupling_vars[1].get())
            m = parse_value(self.coupling_vars[2].get())
            k = m / math.sqrt(l1 * l2)
            note = ""
            if abs(k) > 1:
                note = f"  {t('inductor.not_possible')}"
            elif k < 0:
                # |k| still describes coupling tightness; the sign reflects
                # winding/dot-convention polarity (whether the two coils'
                # reference directions add or oppose), not an invalid input.
                note = f"  {t('inductor.negative_k_note')}"
            self.coupling_result.set(f"k = M/√(L1·L2) = {k:.3f}{note}")
        except Exception:
            self.coupling_result.set(t("inductor.enter_valid_l1l2m"))

    # ---- transformer --------------------------------------------------
    def _build_transformer(self, parent):
        pad = {"padx": 16, "pady": 6}
        self.tx_canvas = tk.Canvas(parent, width=460, height=200, bg="#fdfaf3", highlightthickness=0)
        self.tx_canvas.grid(row=0, column=0, columnspan=4, padx=16, pady=6)
        draw_transformer(self.tx_canvas)

        fields = [(t("inductor.primary_turns"), "100"), (t("inductor.secondary_turns"), "50"),
                  (t("inductor.primary_voltage"), "230")]
        self.tx_vars = []
        for i, (label, default) in enumerate(fields):
            ttk.Label(parent, text=label, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=i + 1, column=0, sticky="w", **pad)
            var = tk.StringVar(value=default)
            ttk.Entry(parent, textvariable=var, width=12).grid(row=i + 1, column=1, sticky="w", **pad)
            self.tx_vars.append(var)

        ttk.Button(parent, text=t("common.calculate"), command=self._calc_transformer)\
            .grid(row=4, column=0, columnspan=2, pady=8)

        self.tx_result = tk.StringVar()
        ttk.Label(parent, textvariable=self.tx_result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left", wraplength=420)\
            .grid(row=5, column=0, columnspan=4, sticky="w", padx=16, pady=(0, 12))
        self._calc_transformer()

    def _calc_transformer(self):
        try:
            np_ = float(self.tx_vars[0].get())
            ns = float(self.tx_vars[1].get())
            vp = float(self.tx_vars[2].get())
            ratio = np_ / ns
            vs = vp / ratio
            kind = t("inductor.step_down") if ratio > 1 else (t("inductor.step_up") if ratio < 1 else t("inductor.step_neutral"))
            self.tx_result.set(f"{t('inductor.turns_ratio')} = {ratio:.3f} : 1\n"
                                f"{t('inductor.secondary_voltage')} = {vs:.3f} V\n({kind})")
        except Exception:
            self.tx_result.set(t("inductor.enter_valid_turns"))

    # ---- series / parallel --------------------------------------------
    def _build_combo_section(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        inner_nb = ttk.Notebook(parent)
        inner_nb.grid(row=0, column=0, sticky="nsew")
        quick_tab = ttk.Frame(inner_nb, style="Card.TFrame")
        mixed_tab = MixedBuilderPanel(inner_nb, kind="inductor", accent=ACCENT_C)
        inner_nb.add(quick_tab, text=t("combos.subtab.quicklist"))
        inner_nb.add(mixed_tab, text=t("combos.subtab.mixed"))
        self._build_combo(quick_tab)

    def _build_combo(self, parent):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(parent, text=t("inductor.combo_title"), font=FONT_H2,
                  foreground=ACCENT_C, style="CardSub.TLabel")\
            .grid(row=0, column=0, columnspan=2, sticky="w", **pad)
        ttk.Label(parent, text=t("inductor.combo_instructions"),
                  font=FONT_BODY, style="CardBody.TLabel", justify="left")\
            .grid(row=1, column=0, columnspan=2, sticky="w", padx=16)

        self.combo_input = tk.StringVar(value="10m, 4.7m, 22m")
        entry = ttk.Entry(parent, textvariable=self.combo_input, width=40)
        entry.grid(row=2, column=0, sticky="w", padx=16, pady=6)
        entry.bind("<Return>", lambda e: self._calc_combo())
        ttk.Button(parent, text=t("common.calculate"), command=self._calc_combo)\
            .grid(row=2, column=1, sticky="w", padx=(6, 16))

        self.combo_mode = tk.StringVar(value="series")
        mode_row = ttk.Frame(parent, style="Card.TFrame")
        mode_row.grid(row=3, column=0, columnspan=2, sticky="w", padx=16, pady=4)
        ttk.Radiobutton(mode_row, text=t("common.show_series"), value="series", variable=self.combo_mode,
                        command=self._calc_combo).pack(side="left", padx=(0, 12))
        ttk.Radiobutton(mode_row, text=t("common.show_parallel"), value="parallel", variable=self.combo_mode,
                        command=self._calc_combo).pack(side="left")

        self.combo_canvas = tk.Canvas(parent, width=460, height=200, bg="#fdfaf3", highlightthickness=0)
        self.combo_canvas.grid(row=4, column=0, columnspan=2, padx=16, pady=10)

        self.combo_result = tk.StringVar()
        ttk.Label(parent, textvariable=self.combo_result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left", wraplength=420)\
            .grid(row=5, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 16))
        self._calc_combo()

    def _calc_combo(self):
        try:
            values = parse_value_list(self.combo_input.get())
        except Exception:
            self.combo_result.set(t("inductor.combo_invalid"))
            return
        draw_combo_diagram(self.combo_canvas, values, self.combo_mode.get(), "inductor")
        try:
            s = series_sum(values)
            p = parallel_combo(values)
            self.combo_result.set(
                f"{t('common.series_total')}:    L = L1+L2+...  =  {format_value(s, 'H')}\n"
                f"{t('common.parallel_total')}:  1/L = 1/L1+1/L2+...  =  {format_value(p, 'H')}"
            )
        except Exception as exc:
            self.combo_result.set(f"{t('common.could_not_compute')}: {exc}")
