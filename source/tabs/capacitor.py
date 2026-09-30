import math
import tkinter as tk
from tkinter import ttk
from data import CERAMIC_TOLERANCE, get_theory
from drawing import draw_capacitor_ceramic, draw_combo_diagram
from widgets import (TheoryPanel, ScrollableFrame, format_value, parse_value, parse_value_list,
                      series_sum, parallel_combo, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ACCENT)
from charts import TimeChartTab, ParamField, capacitor_signals
from combos import MixedBuilderPanel
from solver import FormulaSolverPanel, capacitor_formulas
from symbols import SymbolGallery
from i18n import t
from .smd_panel import SmdCodePanel
from .learn import learn_page
from widgets import lazy_tab
from uikit import FitCanvas, two_columns
from i18n import register
register({"cap.cer.title": ("3-digit code → value", "Cod din 3 cifre → valoare"),
          "cap.cer.tol_title": ("Tolerance letters (click one)", "Litere de toleranță (clic pe una)"),
          "cap.cer.common": ("Common codes (click one)", "Coduri uzuale (clic pe unul)"),
          "cap.cer.how_title": ("How to read it", "Cum se citește"),
          "cap.cer.how": ("• 1st and 2nd digit: the significant figures.\n"
                          "• 3rd digit: how many zeros follow — the value is in picofarads.\n"
                          "• A letter after the digits is the tolerance (J = ±5 %, K = ±10 %, M = ±20 %).\n"
                          "• Two digits only (e.g. 22) means the value directly in pF.\n"
                          "• Example: 473J = 47 000 pF = 47 nF, ±5 %.\n"
                          "• A separate number such as 50V or 1kV is the voltage rating.",
                          "• Cifrele 1 și 2: cifrele semnificative.\n"
                          "• Cifra 3: câte zerouri urmează — valoarea este în picofarazi.\n"
                          "• O literă după cifre este toleranța (J = ±5 %, K = ±10 %, M = ±20 %).\n"
                          "• Doar două cifre (ex. 22) înseamnă direct valoarea în pF.\n"
                          "• Exemplu: 473J = 47 000 pF = 47 nF, ±5 %.\n"
                          "• Un număr separat, ca 50V sau 1kV, este tensiunea nominală.")})

ACCENT_C = ACCENT["capacitor"]


class CapacitorTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1, minsize=380)
        self.columnconfigure(1, weight=1, minsize=360)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=t("capacitor.tab_title"), font=FONT_H1, style="TabTitle.TLabel")\
            .grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 6))

        left = ttk.Frame(self, style="Tab.TFrame")
        left.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

        nb = ttk.Notebook(left)
        nb.grid(row=0, column=0, sticky="nsew")

        ceramic = ttk.Frame(nb, style="Card.TFrame")
        nb.add(ceramic, text=t("capacitor.subtab.ceramic"))
        self._build_ceramic(ceramic)
        lazy_tab(nb, t("smd.subtab"), lambda p: SmdCodePanel(p, "capacitor", ACCENT_C))
        lazy_tab(nb, t("solver.tab"), lambda p: FormulaSolverPanel(p, capacitor_formulas(), ACCENT_C))

        def make_combo(parent):
            f = ttk.Frame(parent, style="Card.TFrame")
            self._build_combo_section(f)
            return f
        lazy_tab(nb, t("capacitor.subtab.combo"), make_combo)

        def make_chart(parent):
            return TimeChartTab(
                parent, ACCENT_C,
                dc_fields=[
                    ParamField("c", t("capacitor.chart.dc_field_c"), "100u"),
                    ParamField("resistance", t("capacitor.chart.dc_field_r"), "1000"),
                    ParamField("voltage", t("capacitor.chart.dc_field_v"), "5"),
                ],
                ac_fields=[
                    ParamField("c", t("capacitor.chart.ac_field_c"), "100n"),
                    ParamField("resistance", t("chart.series_r"), "0"),
                    ParamField("amplitude", t("resistor.chart.ac_field_amp"), "5"),
                    ParamField("frequency", t("common.frequency"), "1000"),
                ],
                signal_fn=capacitor_signals,
                dc_note=t("capacitor.chart.dc_note"),
                ac_note=t("capacitor.chart.ac_note"),
                title=t("capacitor.chart.title"),
                reactive="capacitor",
            )

        lazy_tab(nb, t("capacitor.subtab.chart"), make_chart)

        lazy_tab(nb, t("common.learn"), lambda p: learn_page(p, ACCENT_C, "capacitor", "capacitor", extra=lambda b: __import__("tabs.learn_extras", fromlist=["x"]).capacitor_refs(b, ACCENT_C)))

    # ------------------------------------------------------------------
    def _build_ceramic(self, parent):
        # v6.3: inputs + explanation left; big part drawing + clickable common codes right
        left, right = two_columns(parent, left_min=460)
        ttk.Label(left, text=t("cap.cer.title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 8))
        pad = {"padx": 4, "pady": 6}
        ttk.Label(left, text=t("capacitor.enter_code"), font=FONT_BODY,
                  style="CardBody.TLabel").grid(row=1, column=0, sticky="w", **pad)
        self.code_var = tk.StringVar(value="104")
        entry = ttk.Entry(left, textvariable=self.code_var, width=10, font=("Consolas", 12, "bold"))
        entry.grid(row=1, column=1, sticky="w", **pad)
        entry.bind("<KeyRelease>", lambda e: self._ceramic_code_to_value())
        ttk.Label(left, text=t("capacitor.tolerance_letter"), font=FONT_BODY,
                  style="CardBody.TLabel").grid(row=2, column=0, sticky="w", **pad)
        self.tol_letter = tk.StringVar(value="K")
        tol_cb = ttk.Combobox(left, textvariable=self.tol_letter,
                              values=list(CERAMIC_TOLERANCE.keys()), state="readonly", width=6)
        tol_cb.grid(row=2, column=1, sticky="w", **pad)
        tol_cb.bind("<<ComboboxSelected>>", lambda e: self._ceramic_code_to_value())

        self.ceramic_result = tk.StringVar()
        ttk.Label(left, textvariable=self.ceramic_result, font=("Consolas", 16, "bold"), foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=3, column=0, columnspan=2, sticky="w", padx=4, pady=(14, 2))
        self.ceramic_steps = tk.StringVar()
        ttk.Label(left, textvariable=self.ceramic_steps, font=FONT_MONO, style="CardBody.TLabel",
                  justify="left").grid(row=4, column=0, columnspan=2, sticky="w", padx=4, pady=(4, 12))

        ttk.Label(left, text=t("cap.cer.tol_title"), font=("Segoe UI", 10, "bold"), foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=5, column=0, columnspan=2, sticky="w", padx=4, pady=(8, 4))
        tolf = tk.Frame(left, bg="#ffffff")
        tolf.grid(row=6, column=0, columnspan=2, sticky="w", padx=4)
        self._tol_cells = {}
        for k, (letter, txt) in enumerate(CERAMIC_TOLERANCE.items()):
            cell = tk.Label(tolf, text=f"{letter}\n{txt}", font=("Segoe UI", 9), bg="#f4f6fa", fg="#1f2a44",
                            width=10, pady=3, cursor="hand2", relief="flat", bd=1)
            cell.grid(row=k // 5, column=k % 5, padx=2, pady=2, sticky="ew")
            cell.bind("<Button-1>", lambda _e, L=letter: (self.tol_letter.set(L), self._ceramic_code_to_value()))
            self._tol_cells[letter] = cell

        ttk.Label(left, text=t("cap.cer.how_title"), font=("Segoe UI", 10, "bold"), foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=7, column=0, columnspan=2, sticky="w", padx=4, pady=(18, 4))
        ttk.Label(left, text=t("cap.cer.how"), font=FONT_BODY, style="CardBody.TLabel", wraplength=460,
                  justify="left").grid(row=8, column=0, columnspan=2, sticky="w", padx=4)

        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)
        self.ceramic_canvas = FitCanvas(right, 420, 170, kmax=2.0)
        self.ceramic_canvas.grid(row=0, column=0, sticky="nsew", pady=(0, 10))
        ttk.Label(right, text=t("cap.cer.common"), font=("Segoe UI", 10, "bold"), foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=1, column=0, sticky="w", pady=(0, 4))
        grid = tk.Frame(right, bg="#ffffff")
        grid.grid(row=2, column=0, sticky="ew")
        codes = ["100", "220", "470", "101", "221", "471", "102", "222", "472",
                 "103", "223", "473", "104", "224", "474", "105", "225", "475",
                 "106", "226", "476", "151", "331", "681"]
        per = 6
        for c in range(per):
            grid.columnconfigure(c, weight=1, uniform="cc")
        self._code_cells = {}
        for k, code in enumerate(codes):
            pf = int(code[:2]) * 10 ** int(code[2])
            cell = tk.Label(grid, text=f"{code}\n{format_value(pf * 1e-12, 'F')}", font=("Consolas", 10),
                            bg="#f4f6fa", fg="#1f2a44", pady=6, cursor="hand2")
            cell.grid(row=k // per, column=k % per, padx=2, pady=2, sticky="ew")
            cell.bind("<Button-1>", lambda _e, cd=code: (self.code_var.set(cd), self._ceramic_code_to_value()))
            self._code_cells[code] = cell

        from .smd_panel import CapBandPanel
        CapBandPanel(right, ACCENT_C).grid(row=3, column=0, sticky="ew", pady=(10, 0))

        self._ceramic_code_to_value()

    def _ceramic_code_to_value(self):
        code = self.code_var.get().strip()
        self.ceramic_canvas.show(lambda: draw_capacitor_ceramic(self.ceramic_canvas, code, w=420, h=170))
        for cd, cell in getattr(self, "_code_cells", {}).items():
            cell.configure(bg="#fde7c7" if cd == code else "#f4f6fa")
        for L, cell in getattr(self, "_tol_cells", {}).items():
            cell.configure(bg="#fde7c7" if L == self.tol_letter.get() else "#f4f6fa")
        if not code.isdigit() or len(code) < 2:
            self.ceramic_result.set(t("capacitor.enter_valid_code"))
            self.ceramic_steps.set("")
            return
        if len(code) == 2:
            pf = int(code)
            steps = f"{code} = {pf} pF"
        else:
            digits, mult = code[:-1], int(code[-1])
            pf = int(digits) * (10 ** mult)
            steps = f"{digits} × 10^{mult} pF = {pf:g} pF"
        tol_txt = CERAMIC_TOLERANCE.get(self.tol_letter.get(), "")
        farads = pf * 1e-12
        self.ceramic_result.set(f"= {format_value(farads, 'F')}   {tol_txt}")
        self.ceramic_steps.set(steps + f"\n{t('capacitor.tolerance_word')}: {self.tol_letter.get()} = {tol_txt}")

    # ------------------------------------------------------------------
    def _build_reactance(self, parent):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(parent, text=t("capacitor.ac_reactance"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", **pad)

        ttk.Label(parent, text=t("capacitor.capacitance_100n"), font=FONT_BODY,
                  style="CardBody.TLabel").grid(row=1, column=0, sticky="w", **pad)
        self.xc_cap = tk.StringVar(value="100n")
        e1 = ttk.Entry(parent, textvariable=self.xc_cap, width=10)
        e1.grid(row=1, column=1, sticky="w", **pad)

        ttk.Label(parent, text=t("common.frequency"), font=FONT_BODY,
                  style="CardBody.TLabel").grid(row=2, column=0, sticky="w", **pad)
        self.xc_freq = tk.StringVar(value="1000")
        e2 = ttk.Entry(parent, textvariable=self.xc_freq, width=10)
        e2.grid(row=2, column=1, sticky="w", **pad)

        ttk.Button(parent, text=t("capacitor.calc_xc"), command=self._calc_reactance)\
            .grid(row=3, column=0, columnspan=2, pady=6)

        self.xc_result = tk.StringVar()
        ttk.Label(parent, textvariable=self.xc_result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=4, column=0, columnspan=2, sticky="w", padx=16, pady=(0, 12))

        for c in (0, 1):
            parent.columnconfigure(c, weight=1)
        self._calc_reactance()

    def _calc_reactance(self):
        try:
            c = parse_value(self.xc_cap.get())
            f = float(self.xc_freq.get())
            xc = 1 / (2 * math.pi * f * c)
            self.xc_result.set(f"Xc = 1/(2πfC) = {format_value(xc, 'Ω')}")
        except Exception:
            self.xc_result.set(t("capacitor.enter_valid_cf"))

    # ------------------------------------------------------------------
    def _build_combo_section(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        inner_nb = ttk.Notebook(parent)
        inner_nb.grid(row=0, column=0, sticky="nsew")
        quick_tab = ttk.Frame(inner_nb, style="Card.TFrame")
        mixed_tab = MixedBuilderPanel(inner_nb, kind="capacitor", accent=ACCENT_C)
        inner_nb.add(quick_tab, text=t("combos.subtab.quicklist"))
        inner_nb.add(mixed_tab, text=t("combos.subtab.mixed"))
        from combos import QuickComboPanel
        QuickComboPanel(quick_tab, "capacitor", ACCENT_C, t("capacitor.combo_title"),
                        t("capacitor.combo_instructions"), "100n, 220n, 1u").pack(fill="both", expand=True)

    def _build_combo(self, parent):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(parent, text=t("capacitor.combo_title"), font=FONT_H2,
                  foreground=ACCENT_C, style="CardSub.TLabel")\
            .grid(row=0, column=0, columnspan=2, sticky="w", **pad)
        ttk.Label(parent, text=t("capacitor.combo_instructions"), font=FONT_BODY, style="CardBody.TLabel",
                  justify="left").grid(row=1, column=0, columnspan=2, sticky="w", padx=16)

        self.combo_input = tk.StringVar(value="100n, 220n, 1u")
        entry = ttk.Entry(parent, textvariable=self.combo_input, width=40)
        entry.grid(row=2, column=0, sticky="w", padx=16, pady=6)
        entry.bind("<Return>", lambda e: self._calc_combo())
        ttk.Button(parent, text=t("common.calculate"), command=self._calc_combo)\
            .grid(row=2, column=1, sticky="w", padx=(6, 16))

        self.combo_mode = tk.StringVar(value="parallel")
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
            self.combo_result.set(t("capacitor.combo_invalid"))
            return
        draw_combo_diagram(self.combo_canvas, values, self.combo_mode.get(), "capacitor")
        try:
            # Note: for capacitors, series behaves like parallel resistors and vice versa
            s = parallel_combo(values)   # series capacitance = reciprocal sum
            p = series_sum(values)       # parallel capacitance = direct sum
            self.combo_result.set(
                f"{t('common.series_total')}:    1/C = 1/C1+1/C2+...  =  {format_value(s, 'F')}\n"
                f"{t('common.parallel_total')}:  C = C1+C2+...  =  {format_value(p, 'F')}"
            )
        except Exception as exc:
            self.combo_result.set(f"{t('common.could_not_compute')}: {exc}")
