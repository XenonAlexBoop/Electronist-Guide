"""
tabs/db_calculator.py - Unit Converter > dB / Ratios sub-tab.

Three small calculators:
  - Ratio -> dB: enter two values, see the result interpreted BOTH as a
    power ratio (10*log10) and a voltage/current ratio (20*log10) side by
    side, so the classic "is it 10 or 20?" question is answered directly
    rather than hidden behind a mode toggle.
  - dB -> Ratio: the reverse - enter a dB figure + a reference value, get
    the other value under both interpretations.
  - Absolute levels: dBm/dBW <-> mW/W, with a unit toggle.
Plus a static quick-reference table of "muscle memory" dB values.
"""
import math
import numpy as np
import tkinter as tk
from tkinter import ttk

from widgets import ScrollableFrame, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO
from charts import MplChartFrame, PLOT_BG, include_zero
from i18n import t

ACCENT_C = "#2E5EAA"

# (dB, power ratio, voltage/current ratio) - the classic "muscle memory" set
_REF_ROWS = [0, 1, 2, 3, 6, 10, 12, 20, 26, 40, 60]


class DbCalculatorPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._last_r2db_power_db = None
        self._last_r2db_voltage_db = None

        left_wrap = ttk.Frame(self, style="Card.TFrame")
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        left_wrap.columnconfigure(0, weight=1)
        left_wrap.rowconfigure(0, weight=1)
        right_wrap = ttk.Frame(self, style="Card.TFrame")
        right_wrap.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        right_wrap.columnconfigure(0, weight=1)
        right_wrap.rowconfigure(0, weight=1)

        left_scroll = ScrollableFrame(left_wrap, style="Card.TFrame")
        left_scroll.grid(row=0, column=0, sticky="nsew")
        self._build_ratio_to_db(left_scroll.body)
        self._build_db_to_ratio(left_scroll.body)
        self._build_absolute(left_scroll.body)

        right_scroll = ScrollableFrame(right_wrap, style="Card.TFrame")
        right_scroll.grid(row=0, column=0, sticky="nsew")
        self._build_reference(right_scroll.body)

    # ------------------------------------------------------------------
    # Ratio -> dB
    # ------------------------------------------------------------------
    def _build_ratio_to_db(self, parent):
        pad = {"padx": 16, "pady": 6}
        parent.columnconfigure(0, weight=1)

        header = tk.Frame(parent, bg=ACCENT_C, height=6)
        header.grid(row=0, column=0, sticky="ew")

        ttk.Label(parent, text=t("db.r2db_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=1, column=0, sticky="w", **pad)
        ttk.Label(parent, text=t("db.r2db_intro"), font=FONT_BODY, wraplength=420,
                  justify="left", style="CardBody.TLabel").grid(row=2, column=0, sticky="w", padx=16)

        ttk.Label(parent, text=t("db.value1_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=3, column=0, sticky="w", padx=16, pady=(8, 0))
        self.r2db_v1 = tk.StringVar(value="1")
        e1 = ttk.Entry(parent, textvariable=self.r2db_v1, width=14)
        e1.grid(row=4, column=0, sticky="w", padx=16)
        e1.bind("<KeyRelease>", lambda e: self._ratio_to_db())

        ttk.Label(parent, text=t("db.value2_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=5, column=0, sticky="w", padx=16, pady=(6, 0))
        self.r2db_v2 = tk.StringVar(value="2")
        e2 = ttk.Entry(parent, textvariable=self.r2db_v2, width=14)
        e2.grid(row=6, column=0, sticky="w", padx=16)
        e2.bind("<KeyRelease>", lambda e: self._ratio_to_db())

        ttk.Label(parent, text=t("db.as_power_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=7, column=0, sticky="w", padx=16, pady=(10, 0))
        self.r2db_power_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.r2db_power_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=8, column=0, sticky="w", padx=16, pady=(0, 4))

        ttk.Label(parent, text=t("db.as_voltage_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=9, column=0, sticky="w", padx=16)
        self.r2db_voltage_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.r2db_voltage_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=10, column=0, sticky="w", padx=16, pady=(0, 4))

        ttk.Label(parent, text=t("db.impedance_note"), font=("Segoe UI", 8), foreground="#777",
                  wraplength=420, justify="left").grid(row=11, column=0, sticky="w", padx=16, pady=(0, 16))

        self._ratio_to_db()

    def _ratio_to_db(self):
        try:
            v1 = float(self.r2db_v1.get())
            v2 = float(self.r2db_v2.get())
            if v1 <= 0 or v2 <= 0:
                raise ValueError
        except ValueError:
            self.r2db_power_var.set(t("db.invalid"))
            self.r2db_voltage_var.set("")
            return
        db_power = 10 * math.log10(v2 / v1)
        db_voltage = 20 * math.log10(v2 / v1)
        self.r2db_power_var.set(f"10×log10(V2/V1) = {db_power:.3g} dB")
        self.r2db_voltage_var.set(f"20×log10(V2/V1) = {db_voltage:.3g} dB")
        self._last_r2db_power_db = db_power
        self._last_r2db_voltage_db = db_voltage
        self._redraw_db_chart()

    # ------------------------------------------------------------------
    # dB -> Ratio
    # ------------------------------------------------------------------
    def _build_db_to_ratio(self, parent):
        row0 = 20
        pad = {"padx": 16, "pady": 6}
        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=row0, column=0, sticky="ew", padx=16, pady=(4, 10))

        ttk.Label(parent, text=t("db.db2r_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=row0 + 1, column=0, sticky="w", padx=16)
        ttk.Label(parent, text=t("db.db2r_intro"), font=FONT_BODY, wraplength=420,
                  justify="left", style="CardBody.TLabel").grid(row=row0 + 2, column=0, sticky="w", padx=16)

        ttk.Label(parent, text=t("db.db_value_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=row0 + 3, column=0, sticky="w", padx=16, pady=(8, 0))
        self.db2r_db = tk.StringVar(value="6")
        e1 = ttk.Entry(parent, textvariable=self.db2r_db, width=14)
        e1.grid(row=row0 + 4, column=0, sticky="w", padx=16)
        e1.bind("<KeyRelease>", lambda e: self._db_to_ratio())

        ttk.Label(parent, text=t("db.ref_value_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=row0 + 5, column=0, sticky="w", padx=16, pady=(6, 0))
        self.db2r_ref = tk.StringVar(value="1")
        e2 = ttk.Entry(parent, textvariable=self.db2r_ref, width=14)
        e2.grid(row=row0 + 6, column=0, sticky="w", padx=16)
        e2.bind("<KeyRelease>", lambda e: self._db_to_ratio())

        ttk.Label(parent, text=t("db.as_power_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=row0 + 7, column=0, sticky="w", padx=16, pady=(10, 0))
        self.db2r_power_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.db2r_power_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=row0 + 8, column=0, sticky="w", padx=16, pady=(0, 4))

        ttk.Label(parent, text=t("db.as_voltage_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=row0 + 9, column=0, sticky="w", padx=16)
        self.db2r_voltage_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.db2r_voltage_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=row0 + 10, column=0, sticky="w", padx=16, pady=(0, 16))

        self._db_to_ratio()

    def _db_to_ratio(self):
        try:
            db = float(self.db2r_db.get())
            ref = float(self.db2r_ref.get())
        except ValueError:
            self.db2r_power_var.set(t("db.invalid"))
            self.db2r_voltage_var.set("")
            return
        power_val = ref * (10 ** (db / 10))
        voltage_val = ref * (10 ** (db / 20))
        self.db2r_power_var.set(f"V1 × 10^(dB/10) = {power_val:.4g}")
        self.db2r_voltage_var.set(f"V1 × 10^(dB/20) = {voltage_val:.4g}")

    # ------------------------------------------------------------------
    # Absolute levels: dBm / dBW <-> mW / W
    # ------------------------------------------------------------------
    def _build_absolute(self, parent):
        row0 = 40
        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=row0, column=0, sticky="ew", padx=16, pady=(4, 10))

        ttk.Label(parent, text=t("db.abs_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=row0 + 1, column=0, sticky="w", padx=16)
        ttk.Label(parent, text=t("db.abs_intro"), font=FONT_BODY, wraplength=420,
                  justify="left", style="CardBody.TLabel").grid(row=row0 + 2, column=0, sticky="w", padx=16)

        # Power -> dBm/dBW
        ttk.Label(parent, text=t("db.power_value_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=row0 + 3, column=0, sticky="w", padx=16, pady=(10, 0))
        pw_row = ttk.Frame(parent, style="Card.TFrame")
        pw_row.grid(row=row0 + 4, column=0, sticky="w", padx=16)
        self.abs_power_var = tk.StringVar(value="1")
        pw_entry = ttk.Entry(pw_row, textvariable=self.abs_power_var, width=12)
        pw_entry.pack(side="left")
        pw_entry.bind("<KeyRelease>", lambda e: self._power_to_db())
        self.abs_power_unit = tk.StringVar(value="mW")
        unit_cb = ttk.Combobox(pw_row, textvariable=self.abs_power_unit, values=["mW", "W"],
                                state="readonly", width=5)
        unit_cb.pack(side="left", padx=(6, 0))
        unit_cb.bind("<<ComboboxSelected>>", lambda e: self._power_to_db())

        self.abs_power_result = tk.StringVar()
        ttk.Label(parent, textvariable=self.abs_power_result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=row0 + 5, column=0, sticky="w", padx=16, pady=(6, 12))

        # dBm/dBW -> Power
        ttk.Label(parent, text=t("db.db_abs_value_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=row0 + 6, column=0, sticky="w", padx=16)
        db_row = ttk.Frame(parent, style="Card.TFrame")
        db_row.grid(row=row0 + 7, column=0, sticky="w", padx=16)
        self.abs_db_var = tk.StringVar(value="30")
        db_entry = ttk.Entry(db_row, textvariable=self.abs_db_var, width=12)
        db_entry.pack(side="left")
        db_entry.bind("<KeyRelease>", lambda e: self._db_to_power())
        self.abs_db_unit = tk.StringVar(value="dBm")
        db_unit_cb = ttk.Combobox(db_row, textvariable=self.abs_db_unit, values=["dBm", "dBW"],
                                   state="readonly", width=5)
        db_unit_cb.pack(side="left", padx=(6, 0))
        db_unit_cb.bind("<<ComboboxSelected>>", lambda e: self._db_to_power())

        self.abs_db_result = tk.StringVar()
        ttk.Label(parent, textvariable=self.abs_db_result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=row0 + 8, column=0, sticky="w", padx=16, pady=(6, 16))

        self._power_to_db()
        self._db_to_power()

    def _power_to_db(self):
        try:
            val = float(self.abs_power_var.get())
            if val <= 0:
                raise ValueError
        except ValueError:
            self.abs_power_result.set(t("db.invalid"))
            return
        mw = val if self.abs_power_unit.get() == "mW" else val * 1000.0
        dbm = 10 * math.log10(mw)
        dbw = dbm - 30
        self.abs_power_result.set(f"= {dbm:.3g} dBm   |   {dbw:.3g} dBW")

    def _db_to_power(self):
        try:
            db = float(self.abs_db_var.get())
        except ValueError:
            self.abs_db_result.set(t("db.invalid"))
            return
        dbm = db if self.abs_db_unit.get() == "dBm" else db + 30
        mw = 10 ** (dbm / 10)
        self.abs_db_result.set(f"= {mw:.4g} mW   |   {mw / 1000:.4g} W")

    # ------------------------------------------------------------------
    def _build_reference(self, parent):
        parent.columnconfigure(0, weight=1)
        header = tk.Frame(parent, bg=ACCENT_C, height=6)
        header.grid(row=0, column=0, sticky="ew")

        ttk.Label(parent, text=f"📘 {t('db.quick_ref_title')}", font=FONT_H1,
                  style="CardTitle.TLabel").grid(row=1, column=0, sticky="w", padx=16, pady=(12, 4))
        ttk.Label(parent, text=t("db.quick_ref_note"), font=("Segoe UI", 9), foreground="#777",
                  style="CardBody.TLabel", wraplength=340)\
            .grid(row=2, column=0, sticky="w", padx=16, pady=(0, 10))

        columns = ("db", "power", "voltage")
        tree = ttk.Treeview(parent, columns=columns, show="headings", height=len(_REF_ROWS))
        tree.heading("db", text=t("db.table.db"))
        tree.heading("power", text=t("db.table.power_ratio"))
        tree.heading("voltage", text=t("db.table.voltage_ratio"))
        tree.column("db", width=70, anchor="center")
        tree.column("power", width=140, anchor="center")
        tree.column("voltage", width=140, anchor="center")

        for db in _REF_ROWS:
            power_ratio = 10 ** (db / 10)
            voltage_ratio = 10 ** (db / 20)
            tree.insert("", "end", values=(f"{db:+d}" if db else "0", f"×{power_ratio:.3g}", f"×{voltage_ratio:.3g}"))

        tree.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 16))

        # --- Visual: dB is a LOG scale, so the ratio it represents grows
        # exponentially, not linearly - plotting ratio (linear y-axis) against
        # dB (linear x-axis) makes that curve, and how steep it gets, obvious
        # at a glance. Dotted markers show wherever the Ratio -> dB
        # calculator above last computed a result, so the graph and the
        # numbers stay connected.
        ttk.Label(parent, text=t("db.chart_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=4, column=0, sticky="w", padx=16, pady=(8, 2))
        ttk.Label(parent, text=t("db.chart_note"), font=("Segoe UI", 9), foreground="#777",
                  style="CardBody.TLabel", wraplength=360, justify="left")\
            .grid(row=5, column=0, sticky="w", padx=16, pady=(0, 8))
        self.ref_chart = MplChartFrame(parent, figsize=(4.6, 3.3), with_toolbar=False)
        self.ref_chart.grid(row=6, column=0, sticky="w", padx=16, pady=(0, 20))
        self._redraw_db_chart()

    def _redraw_db_chart(self):
        if not hasattr(self, "ref_chart"):
            return
        fig = self.ref_chart.fig
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_facecolor(PLOT_BG)

        db_range = np.linspace(-10, 30, 400)
        power_ratio = 10 ** (db_range / 10)
        voltage_ratio = 10 ** (db_range / 20)
        ax.plot(db_range, power_ratio, color=ACCENT_C, linewidth=2, label=t("db.chart_power_legend"))
        ax.plot(db_range, voltage_ratio, color="#c9622a", linewidth=2, label=t("db.chart_voltage_legend"))
        ax.axhline(1, color="#ccc", linewidth=1)
        ax.axvline(0, color="#ccc", linewidth=1)

        if self._last_r2db_power_db is not None and -10 <= self._last_r2db_power_db <= 30:
            db = self._last_r2db_power_db
            ax.plot([db], [10 ** (db / 10)], marker="o", color=ACCENT_C, markersize=7, zorder=5)
            ax.axvline(db, color=ACCENT_C, linestyle=":", linewidth=1.2)
        if self._last_r2db_voltage_db is not None and -10 <= self._last_r2db_voltage_db <= 30:
            db = self._last_r2db_voltage_db
            ax.plot([db], [10 ** (db / 20)], marker="o", color="#c9622a", markersize=7, zorder=5)
            ax.axvline(db, color="#c9622a", linestyle=":", linewidth=1.2)

        ax.set_xlabel(t("db.chart_xlabel"), fontsize=9)
        ax.set_ylabel(t("db.chart_ylabel"), fontsize=9)
        ax.tick_params(labelsize=8)
        ax.legend(loc="upper left", fontsize=8)
        ax.grid(True, alpha=0.3)
        include_zero(ax)
        fig.subplots_adjust(left=0.16, right=0.96, top=0.95, bottom=0.16)
        self.ref_chart.redraw()
