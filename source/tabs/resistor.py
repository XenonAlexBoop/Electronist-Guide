import tkinter as tk
from tkinter import ttk
from data import (COLOR_CODE, DIGIT_COLORS, MULTIPLIER_COLORS, TOLERANCE_COLORS,
                   TEMPCO_COLORS, get_theory)
from drawing import draw_resistor, draw_combo_diagram, draw_color_chart
from uikit import FitCanvas, two_columns
from widgets import (TheoryPanel, ScrollableFrame, format_value, parse_value, parse_value_list,
                      series_sum, parallel_combo, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ACCENT)
from combos import MixedBuilderPanel
from .resistive_divider import ResistiveDividerPanel
from solver import FormulaSolverPanel, resistor_formulas
from symbols import SymbolGallery
from i18n import t
from widgets import lazy_tab
from .smd_panel import SmdCodePanel
from .learn import learn_page

ACCENT_C = ACCENT["resistor"]


class ResistorTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1, minsize=380)
        self.columnconfigure(1, weight=1, minsize=360)
        self.rowconfigure(1, weight=1)

        title = ttk.Label(self, text=t("resistor.tab_title"), font=FONT_H1,
                           style="TabTitle.TLabel")
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 6))

        left = ttk.Frame(self, style="Tab.TFrame")
        left.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

        nb = ttk.Notebook(left)
        nb.grid(row=0, column=0, sticky="nsew")

        color_tab = ttk.Frame(nb, style="Card.TFrame")
        combo_tab = ttk.Frame(nb, style="Card.TFrame")
        divider_tab = ResistiveDividerPanel(nb)
        solver_tab = FormulaSolverPanel(nb, resistor_formulas(), ACCENT_C)
        nb.add(color_tab, text=t("resistor.subtab.color"))
        lazy_tab(nb, t("smd.subtab"), lambda p: SmdCodePanel(p, "resistor", ACCENT_C))
        nb.add(solver_tab, text=t("solver.tab"))
        nb.add(combo_tab, text=t("resistor.subtab.combo"))
        nb.add(divider_tab, text=t("resistor.subtab.divider"))

        self._build_calculator(color_tab)
        self._build_combo_section(combo_tab)

        lazy_tab(nb, t("common.learn"), lambda p: learn_page(p, ACCENT_C, "resistor", "resistor", extra=lambda b: __import__("tabs.learn_extras", fromlist=["x"]).resistor_refs(b, ACCENT_C)))

    # ------------------------------------------------------------------
    def _build_calculator(self, parent):
        # v6.3: inputs on the left, a large drawing + the colour-code chart on the right
        left, right = two_columns(parent, left_min=480)
        pad = {"padx": 4, "pady": 6}
        ttk.Label(left, text=t("resistor.color_to_value"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", **pad)

        ttk.Label(left, text=t("resistor.num_bands"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=1, column=0, sticky="w", padx=4)
        self.band_count = tk.IntVar(value=4)
        band_selector = ttk.Combobox(left, textvariable=self.band_count, values=[4, 5, 6],
                                     state="readonly", width=5)
        band_selector.grid(row=1, column=1, sticky="w", pady=6)
        band_selector.bind("<<ComboboxSelected>>", lambda e: self._rebuild_band_selectors())

        self.band_row_frame = ttk.Frame(left, style="Card.TFrame")
        self.band_row_frame.grid(row=2, column=0, columnspan=4, sticky="w", padx=0, pady=6)
        self.band_vars = []

        self.result_var = tk.StringVar(value=f"{t('resistor.resistance_prefix')} -")
        self.range_var = tk.StringVar(value="")
        ttk.Label(left, textvariable=self.result_var, font=("Consolas", 17, "bold"), foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=3, column=0, columnspan=4, sticky="w", padx=4, pady=(14, 2))
        ttk.Label(left, textvariable=self.range_var, font=FONT_BODY, style="CardBody.TLabel",
                  wraplength=420, justify="left").grid(row=4, column=0, columnspan=4, sticky="w", padx=4, pady=(0, 10))

        ttk.Separator(left, orient="horizontal").grid(row=5, column=0, columnspan=4, sticky="ew", padx=4, pady=12)

        ttk.Label(left, text=t("resistor.value_to_color"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=6, column=0, columnspan=4, sticky="w", padx=4)
        ttk.Label(left, text=t("resistor.enter_resistance"), font=FONT_BODY,
                  style="CardBody.TLabel").grid(row=7, column=0, columnspan=4, sticky="w", padx=4, pady=4)
        row = ttk.Frame(left, style="Card.TFrame")
        row.grid(row=8, column=0, columnspan=4, sticky="w", padx=4)
        self.target_value = tk.StringVar()
        entry = ttk.Entry(row, textvariable=self.target_value, width=16)
        entry.pack(side="left")
        entry.bind("<Return>", lambda e: self._value_to_color())
        ttk.Button(row, text=t("common.convert"), command=self._value_to_color).pack(side="left", padx=(8, 0))

        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=2)
        right.rowconfigure(1, weight=3)
        self.canvas = FitCanvas(right, 460, 160, kmax=1.7)
        self.canvas.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        self.chart = FitCanvas(right, 560, 300, kmax=1.5, bg="#ffffff")
        self.chart.grid(row=1, column=0, sticky="nsew")

        self._rebuild_band_selectors()

    def _rebuild_band_selectors(self):
        for child in self.band_row_frame.winfo_children():
            child.destroy()
        self.band_vars = []
        n = self.band_count.get()
        labels = self._band_labels(n)
        options = self._band_options(n)
        defaults = {4: ["Yellow", "Violet", "Red", "Gold"],
                    5: ["Yellow", "Violet", "Black", "Brown", "Brown"],
                    6: ["Yellow", "Violet", "Black", "Brown", "Brown", "Red"]}[n]
        for i, (label, opts) in enumerate(zip(labels, options)):
            col_frame = ttk.Frame(self.band_row_frame, style="Card.TFrame")
            per = 4 if n <= 4 else 3        # v6.4: 5/6 bands wrap to a 2nd row instead of running off
            col_frame.grid(row=i // per, column=i % per, padx=(0, 10), pady=(0, 6), sticky="w")
            ttk.Label(col_frame, text=label, font=("Segoe UI", 8), style="CardBody.TLabel").pack(anchor="w")
            var = tk.StringVar(value=defaults[i] if defaults[i] in opts else opts[0])
            cb = ttk.Combobox(col_frame, textvariable=var, values=opts, state="readonly", width=9)
            cb.pack()
            cb.bind("<<ComboboxSelected>>", lambda e: self._color_to_value())
            self.band_vars.append(var)
        self._color_to_value()

    @staticmethod
    def _band_labels(n):
        if n == 4:
            return [t("resistor.band.digit1"), t("resistor.band.digit2"),
                    t("resistor.band.multiplier"), t("resistor.band.tolerance")]
        if n == 5:
            return [t("resistor.band.digit1"), t("resistor.band.digit2"), t("resistor.band.digit3"),
                    t("resistor.band.multiplier"), t("resistor.band.tolerance")]
        return [t("resistor.band.digit1"), t("resistor.band.digit2"), t("resistor.band.digit3"),
                t("resistor.band.multiplier"), t("resistor.band.tolerance"), t("resistor.band.tempco")]

    @staticmethod
    def _band_options(n):
        digit_opts = DIGIT_COLORS
        mult_opts = list(COLOR_CODE.keys())
        tol_opts = TOLERANCE_COLORS
        tempco_opts = TEMPCO_COLORS
        if n == 4:
            return [digit_opts, digit_opts, mult_opts, tol_opts]
        if n == 5:
            return [digit_opts, digit_opts, digit_opts, mult_opts, tol_opts]
        return [digit_opts, digit_opts, digit_opts, mult_opts, tol_opts, tempco_opts]

    # ------------------------------------------------------------------
    def _color_to_value(self):
        colors = [v.get() for v in self.band_vars]
        n = len(colors)
        self.canvas.show(lambda: draw_resistor(self.canvas, colors))
        nd = 2 if n <= 4 else 3
        hl = {"digit": colors[:nd], "multiplier": colors[nd:nd + 1], "tolerance": colors[nd + 1:nd + 2],
              "tempco": colors[nd + 2:nd + 3]}
        self.chart.show(lambda: draw_color_chart(self.chart, hl, tempco=True))
        try:
            if n <= 4:
                digits = colors[:2]
                mult_color = colors[2]
                tol_color = colors[3]
            else:
                digits = colors[:3]
                mult_color = colors[3]
                tol_color = colors[4]
            digit_str = "".join(str(COLOR_CODE[d]["digit"]) for d in digits)
            base = int(digit_str)
            mult = COLOR_CODE[mult_color]["multiplier"]
            ohms = base * mult
            tol = COLOR_CODE[tol_color]["tolerance"]
            self.result_var.set(f"{t('resistor.resistance_prefix')} {format_value(ohms, 'Ω')}  ±{tol}%")
            lo = ohms * (1 - tol / 100)
            hi = ohms * (1 + tol / 100)
            range_txt = f"{t('resistor.range_prefix')} {format_value(lo, 'Ω')} – {format_value(hi, 'Ω')}"
            if n == 6:
                tempco = COLOR_CODE[colors[5]]["tempco"]
                range_txt += f"   |   {t('resistor.tempco_prefix')} {tempco} ppm/K"
            self.range_var.set(range_txt)
        except Exception:
            self.result_var.set(f"{t('resistor.resistance_prefix')} -")
            self.range_var.set("")

    def _value_to_color(self):
        try:
            ohms = parse_value(self.target_value.get())
        except Exception:
            self.result_var.set(t("resistor.invalid_value"))
            return
        mult_list = sorted(
            [(name, v["multiplier"]) for name, v in COLOR_CODE.items() if v["multiplier"] is not None],
            key=lambda x: x[1])
        best = None
        for name, mult in mult_list:
            base = ohms / mult
            if 9.5 <= base <= 99.5:
                best = (name, mult, round(base))
                break
        if best is None:
            name, mult = min(mult_list, key=lambda nm: abs(ohms / nm[1] - 50) if ohms / nm[1] > 0 else 1e18)
            best = (name, mult, round(ohms / mult))
        mult_name, mult, base = best
        base = max(10, min(99, base))
        d1, d2 = base // 10, base % 10
        digit_lookup = {v["digit"]: name for name, v in COLOR_CODE.items() if v["digit"] is not None}
        c1, c2 = digit_lookup[d1], digit_lookup[d2]
        colors = [c1, c2, mult_name, "Gold"]
        self.band_count.set(4)
        self._rebuild_band_selectors()
        for var, col in zip(self.band_vars, colors):
            var.set(col)
        self._color_to_value()

    # ------------------------------------------------------------------
    def _build_combo_section(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        inner_nb = ttk.Notebook(parent)
        inner_nb.grid(row=0, column=0, sticky="nsew")
        quick_tab = ttk.Frame(inner_nb, style="Card.TFrame")
        mixed_tab = MixedBuilderPanel(inner_nb, kind="resistor", accent=ACCENT_C)
        inner_nb.add(quick_tab, text=t("combos.subtab.quicklist"))
        inner_nb.add(mixed_tab, text=t("combos.subtab.mixed"))
        from combos import QuickComboPanel
        QuickComboPanel(quick_tab, "resistor", ACCENT_C, t("resistor.combo_title"),
                        t("resistor.combo_instructions"), "220, 470, 1k").pack(fill="both", expand=True)

    def _build_combo(self, parent):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(parent, text=t("resistor.combo_title"), font=FONT_H2,
                  foreground=ACCENT_C, style="CardSub.TLabel")\
            .grid(row=0, column=0, columnspan=2, sticky="w", **pad)
        ttk.Label(parent, text=t("resistor.combo_instructions"), font=FONT_BODY, style="CardBody.TLabel",
                  justify="left").grid(row=1, column=0, columnspan=2, sticky="w", padx=16)

        self.combo_input = tk.StringVar(value="220, 470, 1k")
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
            self.combo_result.set(t("resistor.combo_invalid"))
            return
        draw_combo_diagram(self.combo_canvas, values, self.combo_mode.get(), "resistor")
        try:
            s = series_sum(values)
            p = parallel_combo(values)
            self.combo_result.set(
                f"{t('common.series_total')}:    R = R1+R2+...  =  {format_value(s, 'Ω')}\n"
                f"{t('common.parallel_total')}:  1/R = 1/R1+1/R2+...  =  {format_value(p, 'Ω')}"
            )
        except Exception as exc:
            self.combo_result.set(f"{t('common.could_not_compute')}: {exc}")
