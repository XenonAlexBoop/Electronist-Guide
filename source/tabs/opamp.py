import tkinter as tk
from tkinter import ttk
from data import get_theory
from drawing import draw_opamp
from widgets import TheoryPanel, ScrollableFrame, parse_value, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ACCENT
from i18n import t
from symbols import SymbolGallery

ACCENT_C = ACCENT["opamp"]


class OpAmpTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1, minsize=380)
        self.columnconfigure(1, weight=1, minsize=360)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=t("opamp.tab_title"), font=FONT_H1, style="TabTitle.TLabel")\
            .grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 6))

        left = ttk.Frame(self, style="Card.TFrame")
        left.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        right = ttk.Frame(self, style="Tab.TFrame")
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        self._build_calculator(left)
        right_scroll = ScrollableFrame(right, style="Card.TFrame")
        right_scroll.grid(row=0, column=0, sticky="nsew")
        SymbolGallery(right_scroll.body, "opamp", accent=ACCENT_C).pack(fill="x", pady=(0, 8))
        theory = TheoryPanel(right_scroll.body, get_theory("opamp"), accent=ACCENT_C)
        theory.pack(fill="both", expand=True)

    def _build_calculator(self, parent):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(parent, text=t("opamp.configuration"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=0, column=0, sticky="w", **pad)
        self.mode = tk.StringVar(value=t("opamp.inverting"))
        self._inv_label = t("opamp.inverting")
        self._noninv_label = t("opamp.noninverting")
        cb = ttk.Combobox(parent, textvariable=self.mode,
                           values=[self._inv_label, self._noninv_label], state="readonly", width=14)
        cb.grid(row=0, column=1, sticky="w", **pad)
        cb.bind("<<ComboboxSelected>>", lambda e: self._calc())

        self.canvas = tk.Canvas(parent, width=460, height=220, bg="#fdfaf3", highlightthickness=0)
        self.canvas.grid(row=1, column=0, columnspan=2, padx=16, pady=6)

        fields = [(t("opamp.rin"), "1k"), (t("opamp.rf"), "10k"), (t("opamp.vin"), "1"),
                  (t("opamp.vplus"), "15"), (t("opamp.vminus"), "-15")]
        self.vars = []
        for i, (label, default) in enumerate(fields):
            ttk.Label(parent, text=label, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=i + 2, column=0, sticky="w", **pad)
            var = tk.StringVar(value=default)
            entry = ttk.Entry(parent, textvariable=var, width=10)
            entry.grid(row=i + 2, column=1, sticky="w", **pad)
            entry.bind("<KeyRelease>", lambda e: self._calc())
            self.vars.append(var)

        self.result = tk.StringVar()
        ttk.Label(parent, textvariable=self.result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left", wraplength=420)\
            .grid(row=7, column=0, columnspan=2, sticky="w", padx=16, pady=(6, 12))
        self._calc()

    def _calc(self):
        try:
            rin = parse_value(self.vars[0].get())
            rf = parse_value(self.vars[1].get())
            vin = float(self.vars[2].get())
            v_plus = float(self.vars[3].get())
            v_minus = float(self.vars[4].get())
            draw_opamp(self.canvas, mode="inverting" if self.mode.get() == self._inv_label else "noninverting")
            if self.mode.get() == self._inv_label:
                gain = -(rf / rin)
                formula = "Vout = -(Rf/Rin) × Vin"
            else:
                gain = 1 + (rf / rin)
                formula = "Vout = (1 + Rf/Rin) × Vin"
            vout_ideal = gain * vin
            lo, hi = min(v_plus, v_minus), max(v_plus, v_minus)
            vout_actual = max(lo, min(hi, vout_ideal))
            lines = [formula, f"{t('opamp.gain')} = {gain:.3f}",
                     f"{t('opamp.vout_ideal')} = {vout_ideal:.3f} V"]
            if abs(vout_actual - vout_ideal) > 1e-9:
                lines.append(f"{t('opamp.vout_actual')} = {vout_actual:.3f} V")
                lines.append(t("opamp.clip_warning"))
            else:
                lines.append(t("opamp.assumption"))
            self.result.set("\n".join(lines))
        except Exception:
            self.result.set(t("opamp.enter_valid"))
