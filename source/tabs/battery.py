import tkinter as tk
from tkinter import ttk
from data import get_theory
from drawing import draw_battery
from widgets import TheoryPanel, ScrollableFrame, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ACCENT
from i18n import t
from symbols import SymbolGallery
from widgets import lazy_tab
from .learn import learn_page
from i18n import register

register({"battery.subtab.calc": ("Pack calculator", "Calculator baterie")})

ACCENT_C = ACCENT["battery"]


class BatteryTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1, minsize=380)
        self.columnconfigure(1, weight=1, minsize=360)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=t("battery.tab_title"), font=FONT_H1,
                  style="TabTitle.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 6))

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        from .battery_panel import BatteryPackPanel
        calc = BatteryPackPanel(nb, ACCENT_C)
        nb.add(calc, text=t("battery.subtab.calc"))
        lazy_tab(nb, t("common.learn"), lambda p: learn_page(p, ACCENT_C, "battery", "battery", extra=lambda b: __import__("tabs.learn_extras", fromlist=["x"]).battery_refs(b, ACCENT_C)))

    def _build_calculator(self, parent):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(parent, text=t("battery.arrangement"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=0, column=0, sticky="w", **pad)
        self._series_label = t("common.series")
        self._parallel_label = t("common.parallel")
        self.arrangement = tk.StringVar(value=self._series_label)
        cb = ttk.Combobox(parent, textvariable=self.arrangement,
                           values=[self._series_label, self._parallel_label], state="readonly", width=10)
        cb.grid(row=0, column=1, sticky="w", **pad)
        cb.bind("<<ComboboxSelected>>", lambda e: self._calc())

        self.canvas = tk.Canvas(parent, width=460, height=180, bg="#fdfaf3", highlightthickness=0)
        self.canvas.grid(row=1, column=0, columnspan=2, padx=16, pady=6)

        fields = [(t("battery.num_cells"), "3"), (t("battery.voltage_per_cell"), "3.7"),
                  (t("battery.capacity_per_cell"), "2000"), (t("battery.load_current"), "500")]
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
            .grid(row=6, column=0, columnspan=2, sticky="w", padx=16, pady=(6, 12))
        self._calc()

    def _calc(self):
        try:
            n = int(self.vars[0].get())
            v_cell = float(self.vars[1].get())
            cap_cell = float(self.vars[2].get())
            load = float(self.vars[3].get())
            series = self.arrangement.get() == self._series_label
            draw_battery(self.canvas, count=min(n, 8), series=series)
            if series:
                v_total = v_cell * n
                cap_total = cap_cell
            else:
                v_total = v_cell
                cap_total = cap_cell * n
            runtime_h = cap_total / load if load > 0 else float("inf")
            energy_wh = v_total * (cap_total / 1000.0)
            self.result.set(
                f"{t('battery.total_voltage')}: {v_total:.2f} V\n"
                f"{t('battery.total_capacity')}: {cap_total:.0f} mAh\n"
                f"{t('battery.energy_estimate')}: {energy_wh:.2f} Wh\n"
                f"{t('battery.runtime_estimate')} {load:.0f} mA {t('battery.load')}: "
                f"{runtime_h:.2f} {t('battery.hours')}\n"
                f"{t('battery.runtime_disclaimer')}"
            )
        except Exception:
            self.result.set(t("battery.enter_valid"))
