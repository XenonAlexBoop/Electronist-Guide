import math
import tkinter as tk
from tkinter import ttk
from data import get_theory
from widgets import parse_value, format_value, ScrollableFrame, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ACCENT
from i18n import t
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


class OhmsLawPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1, minsize=380)
        self.columnconfigure(1, weight=1, minsize=360)
        self.rowconfigure(0, weight=1)

        left_wrap = ttk.Frame(self, style="Card.TFrame")
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        left_wrap.columnconfigure(0, weight=1)
        left_wrap.rowconfigure(0, weight=1)
        right = ttk.Frame(self, style="Tab.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        left_scroll = ScrollableFrame(left_wrap, style="Card.TFrame")
        left_scroll.grid(row=0, column=0, sticky="nsew")
        left = left_scroll.body

        self._build_calculator(left)
        self._build_live_simulator(left)
        from widgets import TheoryPanel
        right_scroll = ScrollableFrame(right, style="Card.TFrame")
        right_scroll.grid(row=0, column=0, sticky="nsew")
        theory = TheoryPanel(right_scroll.body, get_theory("basics"), accent=ACCENT_C)
        theory.pack(fill="both", expand=True)

    def _build_calculator(self, parent):
        pad = {"padx": 16, "pady": 6}
        ttk.Label(parent, text=t("basics.ohms_triangle_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, columnspan=3, sticky="w", **pad)

        self.canvas = tk.Canvas(parent, width=280, height=240, bg="#fdfaf3", highlightthickness=0)
        self.canvas.grid(row=1, column=0, rowspan=4, padx=16, pady=6)
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
        ttk.Label(parent, text=t("basics.peak_voltage"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=9, column=0, sticky="w", padx=16)
        self.peak_var = tk.StringVar(value="325")
        entry = ttk.Entry(parent, textvariable=self.peak_var, width=10)
        entry.grid(row=9, column=1, columnspan=2, sticky="w")
        entry.bind("<KeyRelease>", lambda e: self._rms())
        self.rms_result = tk.StringVar()
        ttk.Label(parent, textvariable=self.rms_result, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=10, column=0, columnspan=3, sticky="w", padx=16, pady=(4, 14))
        self._rms()

    def _draw_triangle(self):
        c = self.canvas
        c.delete("all")
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
            self.rms_result.set(f"Vrms = Vpeak / √2 = {rms:.2f} V")
        except Exception:
            self.rms_result.set("")

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

        self._sync_live_sliders()
        self._on_live_lock_change()

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
