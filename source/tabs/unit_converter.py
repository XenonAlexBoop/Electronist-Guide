"""
tabs/unit_converter.py - Unit Converter (reworked in v5.2).

Sub-tabs
  1. Converter   - pick a category, type one value, see it in EVERY unit of
                   that category at once; click a row to continue from it.
                   Includes an "Electrical (SI prefixes)" category that
                   replaces the old prefix converter, plus nonlinear ones
                   (temperature, frequency/period/wavelength, wire gauge).
  2. dB & levels - linked fields: type in any one of W, dBm, dBW, Vrms,
                   Vpeak, Vpp, dBV, dBu, dBµV and the others follow (for a
                   chosen impedance); plus ratio <-> dB and a quick table.
  3. Number systems - linked DEC/HEX/OCT/BIN/ASCII fields with a clickable
                   bit grid, bit width and signed (two's complement) mode.
  4. ADC / DAC   - the ADC/DAC code calculator.
"""
import math
import tkinter as tk
from tkinter import ttk

from data import UNIT_PREFIXES, FULL_SI_PREFIXES
from widgets import ScrollableFrame, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, parse_value, debounce
from tabs.base_converter import AdcDacPanel
from i18n import t, get_language

ACCENT_C = "#2E5EAA"
C0 = 299792458.0


def _L(en, ro):
    return {"en": en, "ro": ro}


def _tr(d):
    return d.get(get_language(), d["en"]) if isinstance(d, dict) else d


def fmt_num(v):
    """Readable number: plain for 1e-4..1e9, scientific otherwise."""
    if v is None or (isinstance(v, float) and (math.isnan(v) or math.isinf(v))):
        return "—"
    if v == 0:
        return "0"
    a = abs(v)
    if 1e-4 <= a < 1e9:
        s = f"{v:.10g}"
        if "e" in s:
            s = f"{v:.6e}"
        return s
    m, e = f"{v:.6e}".split("e")
    m = m.rstrip("0").rstrip(".")
    return f"{m} × 10^{int(e)}"


def lin(f):
    """Unit that is a plain factor of the base unit."""
    return (lambda v: v * f, lambda b: b / f)


# ---------------------------------------------------------------------------
# Categories: (key, name, [(unit symbol, unit description, (to_base, from_base)), ...])
# ---------------------------------------------------------------------------
def _awg_to_d(n):
    return 0.127e-3 * 92 ** ((36 - n) / 39)


def _d_to_awg(d):
    return 36 - 39 * math.log(d / 0.127e-3, 92)


CATEGORIES = [
    ("length", _L("Length", "Lungime"), [
        ("m", _L("metre", "metru"), lin(1)), ("km", _L("kilometre", "kilometru"), lin(1e3)),
        ("cm", _L("centimetre", "centimetru"), lin(1e-2)), ("mm", _L("millimetre", "milimetru"), lin(1e-3)),
        ("µm", _L("micrometre", "micrometru"), lin(1e-6)), ("nm", _L("nanometre", "nanometru"), lin(1e-9)),
        ("mil", _L("thou (1/1000 in, PCB)", "mil (1/1000 in, PCB)"), lin(25.4e-6)),
        ("in", _L("inch", "țol"), lin(0.0254)), ("ft", _L("foot", "picior"), lin(0.3048)),
        ("yd", _L("yard", "yard"), lin(0.9144)), ("mi", _L("mile", "milă"), lin(1609.344)),
        ("nmi", _L("nautical mile", "milă marină"), lin(1852)), ("Å", _L("ångström", "ångström"), lin(1e-10))]),
    ("area", _L("Area", "Arie"), [
        ("m²", _L("square metre", "metru pătrat"), lin(1)), ("cm²", "", lin(1e-4)), ("mm²", "", lin(1e-6)),
        ("km²", "", lin(1e6)), ("ha", _L("hectare", "hectar"), lin(1e4)), ("in²", "", lin(0.0254 ** 2)),
        ("ft²", "", lin(0.3048 ** 2)), ("acre", _L("acre", "acru"), lin(4046.8564224)),
        ("cmil", _L("circular mil (wire)", "circular mil (conductor)"), lin(math.pi / 4 * (25.4e-6) ** 2)),
        ("kcmil", _L("thousand circular mils", "mii de circular mil"), lin(1000 * math.pi / 4 * (25.4e-6) ** 2))]),
    ("volume", _L("Volume", "Volum"), [
        ("m³", "", lin(1)), ("L", _L("litre", "litru"), lin(1e-3)), ("mL", "", lin(1e-6)),
        ("cm³", "", lin(1e-6)), ("mm³", "", lin(1e-9)), ("in³", "", lin(0.0254 ** 3)), ("ft³", "", lin(0.3048 ** 3)),
        ("gal (US)", "", lin(3.785411784e-3)), ("gal (UK)", "", lin(4.54609e-3)), ("fl oz (US)", "", lin(29.5735295625e-6))]),
    ("mass", _L("Mass", "Masă"), [
        ("kg", "", lin(1)), ("g", "", lin(1e-3)), ("mg", "", lin(1e-6)), ("t", _L("tonne", "tonă"), lin(1e3)),
        ("lb", _L("pound", "livră"), lin(0.45359237)), ("oz", _L("ounce", "uncie"), lin(0.028349523125)),
        ("gr", _L("grain", "gran"), lin(64.79891e-6))]),
    ("time", _L("Time", "Timp"), [
        ("s", "", lin(1)), ("ms", "", lin(1e-3)), ("µs", "", lin(1e-6)), ("ns", "", lin(1e-9)), ("ps", "", lin(1e-12)),
        ("min", "", lin(60)), ("h", "", lin(3600)), ("day", _L("day", "zi"), lin(86400)),
        ("week", _L("week", "săptămână"), lin(604800)), ("year", _L("year (365.25 d)", "an (365,25 z)"), lin(31557600))]),
    ("freq", _L("Frequency / period / wavelength", "Frecvență / perioadă / lungime de undă"), [
        ("Hz", "", lin(1)), ("kHz", "", lin(1e3)), ("MHz", "", lin(1e6)), ("GHz", "", lin(1e9)),
        ("rpm", _L("revolutions per minute", "rotații pe minut"), lin(1 / 60)),
        ("rad/s", _L("angular frequency ω", "pulsație ω"), lin(1 / (2 * math.pi))),
        ("T (s)", _L("period T = 1/f", "perioadă T = 1/f"), (lambda v: 1 / v, lambda b: 1 / b)),
        ("T (ms)", "", (lambda v: 1 / (v * 1e-3), lambda b: 1 / b / 1e-3)),
        ("T (µs)", "", (lambda v: 1 / (v * 1e-6), lambda b: 1 / b / 1e-6)),
        ("T (ns)", "", (lambda v: 1 / (v * 1e-9), lambda b: 1 / b / 1e-9)),
        ("λ (m)", _L("wavelength in vacuum λ = c/f", "lungime de undă în vid λ = c/f"),
         (lambda v: C0 / v, lambda b: C0 / b)),
        ("λ (cm)", "", (lambda v: C0 / (v * 1e-2), lambda b: C0 / b / 1e-2))]),
    ("temp", _L("Temperature", "Temperatură"), [
        ("°C", "Celsius", (lambda v: v + 273.15, lambda b: b - 273.15)),
        ("K", "Kelvin", lin(1)),
        ("°F", "Fahrenheit", (lambda v: (v - 32) * 5 / 9 + 273.15, lambda b: (b - 273.15) * 9 / 5 + 32)),
        ("°R", "Rankine", lin(5 / 9))]),
    ("energy", _L("Energy / battery capacity", "Energie / capacitate baterie"), [
        ("J", "", lin(1)), ("kJ", "", lin(1e3)), ("MJ", "", lin(1e6)), ("mWh", "", lin(3.6)), ("Wh", "", lin(3600)),
        ("kWh", "", lin(3.6e6)), ("cal", "", lin(4.184)), ("kcal", "", lin(4184)),
        ("eV", _L("electron-volt", "electron-volt"), lin(1.602176634e-19)), ("BTU", "", lin(1055.05585))]),
    ("power", _L("Power", "Putere"), [
        ("W", "", lin(1)), ("mW", "", lin(1e-3)), ("µW", "", lin(1e-6)), ("kW", "", lin(1e3)), ("MW", "", lin(1e6)),
        ("hp", _L("mechanical horsepower", "cal-putere mecanic"), lin(745.69987158)),
        ("CP", _L("metric horsepower", "cal-putere metric"), lin(735.49875)),
        ("BTU/h", "", lin(0.29307107)),
        ("dBm", _L("decibel-milliwatt", "decibel-miliwatt"), (lambda v: 1e-3 * 10 ** (v / 10), lambda b: 10 * math.log10(b / 1e-3))),
        ("dBW", "", (lambda v: 10 ** (v / 10), lambda b: 10 * math.log10(b)))]),
    ("pressure", _L("Pressure", "Presiune"), [
        ("Pa", "", lin(1)), ("kPa", "", lin(1e3)), ("MPa", "", lin(1e6)), ("bar", "", lin(1e5)),
        ("mbar", "", lin(100)), ("atm", "", lin(101325)), ("psi", "", lin(6894.757293168)),
        ("mmHg", "", lin(133.322387415)), ("inHg", "", lin(3386.389))]),
    ("charge", _L("Electric charge", "Sarcină electrică"), [
        ("C", _L("coulomb (A·s)", "coulomb (A·s)"), lin(1)), ("mC", "", lin(1e-3)), ("µC", "", lin(1e-6)),
        ("nC", "", lin(1e-9)), ("Ah", "", lin(3600)), ("mAh", "", lin(3.6)),
        ("e", _L("elementary charges", "sarcini elementare"), lin(1.602176634e-19))]),
    ("magnetic", _L("Magnetic flux density", "Inducție magnetică"), [
        ("T", "tesla", lin(1)), ("mT", "", lin(1e-3)), ("µT", "", lin(1e-6)), ("nT", "", lin(1e-9)),
        ("G", "gauss", lin(1e-4)), ("mG", "", lin(1e-7))]),
    ("angle", _L("Angle", "Unghi"), [
        ("°", _L("degree", "grad sexagesimal"), lin(math.pi / 180)), ("rad", "radian", lin(1)),
        ("grad", _L("gradian", "grad centesimal"), lin(math.pi / 200)), ("′", _L("arc minute", "minut de arc"), lin(math.pi / 10800)),
        ("″", _L("arc second", "secundă de arc"), lin(math.pi / 648000)), ("turn", _L("turn", "rotație"), lin(2 * math.pi))]),
    ("speed", _L("Speed", "Viteză"), [
        ("m/s", "", lin(1)), ("km/h", "", lin(1 / 3.6)), ("mph", "", lin(0.44704)), ("kn", _L("knot", "nod"), lin(1852 / 3600)),
        ("ft/s", "", lin(0.3048)), ("c", _L("speed of light", "viteza luminii"), lin(C0))]),
    ("data", _L("Data size", "Dimensiune date"), [
        ("bit", "", lin(1)), ("B", _L("byte", "octet"), lin(8)), ("kB", "10³ B", lin(8e3)), ("MB", "10⁶ B", lin(8e6)),
        ("GB", "10⁹ B", lin(8e9)), ("TB", "10¹² B", lin(8e12)), ("KiB", "2¹⁰ B", lin(8 * 1024)),
        ("MiB", "2²⁰ B", lin(8 * 1024 ** 2)), ("GiB", "2³⁰ B", lin(8 * 1024 ** 3)), ("TiB", "2⁴⁰ B", lin(8 * 1024 ** 4))]),
    ("rate", _L("Data rate", "Debit de date"), [
        ("bit/s", "", lin(1)), ("kbit/s", "", lin(1e3)), ("Mbit/s", "", lin(1e6)), ("Gbit/s", "", lin(1e9)),
        ("B/s", "", lin(8)), ("kB/s", "", lin(8e3)), ("MB/s", "", lin(8e6)), ("GB/s", "", lin(8e9))]),
    ("awg", _L("Wire gauge (AWG)", "Diametru conductor (AWG)"), [
        ("AWG", _L("American Wire Gauge", "American Wire Gauge"), (_awg_to_d, _d_to_awg)),
        ("Ø mm", _L("diameter", "diametru"), lin(1e-3)),
        ("Ø in", "", lin(0.0254)),
        ("mm²", _L("cross-section", "secțiune"), (lambda v: math.sqrt(4 * v * 1e-6 / math.pi),
                                                  lambda d: math.pi * d * d / 4 * 1e6)),
        ("kcmil", "", (lambda v: math.sqrt(v * 1000) * 25.4e-6, lambda d: (d / 25.4e-6) ** 2 / 1000)),
        ("Ω/m (Cu)", _L("copper resistance at 20 °C", "rezistența cuprului la 20 °C"),
         (lambda v: math.sqrt(4 * 1.724e-8 / (math.pi * v)), lambda d: 1.724e-8 / (math.pi * d * d / 4)))]),
]

ELEC_QUANTITIES = [("V", _L("voltage", "tensiune")), ("A", _L("current", "curent")), ("Ω", _L("resistance", "rezistență")),
                   ("F", _L("capacitance", "capacitate")), ("H", _L("inductance", "inductanță")),
                   ("W", _L("power", "putere")), ("Hz", _L("frequency", "frecvență")), ("S", _L("conductance", "conductanță")),
                   ("C", _L("charge", "sarcină")), ("J", _L("energy", "energie")), ("s", _L("time", "timp")),
                   ("m", _L("length", "lungime"))]

_PREFIX_NAME = {"p": "pico", "n": "nano", "µ": "micro", "m": "milli", "": "", "k": "kilo", "M": "mega",
                "G": "giga", "T": "tera", "f": "femto", "a": "atto", "P": "peta", "E": "exa"}


class UnitConverterTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text=t("uc.tab_title"), font=FONT_H1, style="TabTitle.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))
        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))
        nb.add(SmartConverterPanel(nb), text=t("uc2.tab.convert"))
        nb.add(LevelsPanel(nb), text=t("uc2.tab.levels"))
        nb.add(NumberPanel(nb), text=t("uc2.tab.numbers"))
        adc = ttk.Frame(nb, style="Card.TFrame")
        sf = ScrollableFrame(adc, style="Card.TFrame")
        sf.pack(fill="both", expand=True)
        sf.body.columnconfigure(0, weight=1)
        AdcDacPanel(sf.body).grid(row=0, column=0, sticky="nsew")
        nb.add(adc, text=t("uc2.tab.adc"))


def _scroll_page(parent):
    wrap = ttk.Frame(parent, style="Card.TFrame")
    wrap.columnconfigure(0, weight=1)
    wrap.rowconfigure(0, weight=1)
    sf = ScrollableFrame(wrap, style="Card.TFrame")
    sf.grid(row=0, column=0, sticky="nsew")
    sf.body.columnconfigure(0, weight=1)
    return wrap, sf.body


# ---------------------------------------------------------------------------
# 1. Smart converter
# ---------------------------------------------------------------------------
class SmartConverterPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        wrap, body = _scroll_page(self)
        wrap.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(1, weight=1)

        ttk.Label(body, text=t("uc2.convert_intro"), font=FONT_BODY, style="CardBody.TLabel", wraplength=900,
                  justify="left").grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 8))

        # category list
        left = ttk.Frame(body, style="Card.TFrame")
        left.grid(row=1, column=0, sticky="nsw", padx=(16, 10), pady=(0, 16))
        ttk.Label(left, text=t("uc2.category"), font=("Segoe UI", 10, "bold"), style="CardBody.TLabel")\
            .pack(anchor="w")
        self.cats = [("elec", _L("Electrical (SI prefixes)", "Electrice (prefixe SI)"), None)] + CATEGORIES
        self.cat_list = tk.Listbox(left, height=len(self.cats), width=34, font=("Segoe UI", 10), activestyle="none",
                                   selectbackground=ACCENT_C, selectforeground="white", exportselection=False,
                                   highlightthickness=1, relief="flat")
        for _, name, _u in self.cats:
            self.cat_list.insert("end", "  " + _tr(name))
        self.cat_list.pack(anchor="w", pady=(4, 0))
        self.cat_list.bind("<<ListboxSelect>>", lambda e: self._on_category())

        # input + results
        right = ttk.Frame(body, style="Card.TFrame")
        right.grid(row=1, column=1, sticky="nsew", padx=(0, 16), pady=(0, 16))
        right.columnconfigure(0, weight=1)
        self.title_var = tk.StringVar()
        ttk.Label(right, textvariable=self.title_var, font=FONT_H2, foreground=ACCENT_C, style="CardTitle.TLabel")\
            .grid(row=0, column=0, sticky="w")
        inp = ttk.Frame(right, style="Card.TFrame")
        inp.grid(row=1, column=0, sticky="w", pady=(6, 4))
        ttk.Label(inp, text=t("uc2.value"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self.val_var = tk.StringVar(value="1")
        e = ttk.Entry(inp, textvariable=self.val_var, width=16, font=FONT_MONO)
        e.pack(side="left", padx=6)
        e.bind("<KeyRelease>", lambda ev: self._update())
        self.qty_var = tk.StringVar()
        self.qty_cb = ttk.Combobox(inp, textvariable=self.qty_var, state="readonly", width=16)
        self.qty_cb.bind("<<ComboboxSelected>>", lambda ev: self._on_qty())
        self.unit_var = tk.StringVar()
        self.unit_cb = ttk.Combobox(inp, textvariable=self.unit_var, state="readonly", width=14, font=("Segoe UI", 10))
        self.unit_cb.pack(side="left", padx=4)
        self.unit_cb.bind("<<ComboboxSelected>>", lambda ev: self._update())
        self.full_si = tk.BooleanVar(value=False)
        self.full_cb = ttk.Checkbutton(inp, text=t("uc.full_si_toggle"), variable=self.full_si,
                                       command=self._on_qty)
        self.hint_var = tk.StringVar()
        ttk.Label(right, textvariable=self.hint_var, font=("Segoe UI", 8), foreground="#777",
                  style="CardBody.TLabel").grid(row=2, column=0, sticky="w")
        self.best_var = tk.StringVar()
        ttk.Label(right, textvariable=self.best_var, font=("Consolas", 14, "bold"), foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=3, column=0, sticky="w", pady=(6, 4))

        tv_wrap = ttk.Frame(right, style="Card.TFrame")
        tv_wrap.grid(row=4, column=0, sticky="nsew")
        self.tree = ttk.Treeview(tv_wrap, columns=("unit", "value", "desc"), show="headings", height=13,
                                 selectmode="browse")
        self.tree.heading("unit", text=t("uc2.col_unit"))
        self.tree.heading("value", text=t("uc2.col_value"))
        self.tree.heading("desc", text=t("uc2.col_desc"))
        self.tree.column("unit", width=110, anchor="w", stretch=False)
        self.tree.column("value", width=260, anchor="e", stretch=False)
        self.tree.column("desc", width=280, anchor="w")
        self.tree.tag_configure("src", background="#dbeafe")
        self.tree.tag_configure("best", foreground="#0b6b3a")
        self.tree.pack(fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._on_row)
        ttk.Label(right, text=t("uc2.row_hint"), font=("Segoe UI", 8), foreground="#777",
                  style="CardBody.TLabel").grid(row=5, column=0, sticky="w", pady=(4, 0))

        self._units = []
        self._mute = False
        self.cat_list.selection_set(0)
        self._on_category()

    # --- helpers ---
    def _cat(self):
        sel = self.cat_list.curselection()
        return self.cats[sel[0] if sel else 0]

    def _elec_units(self):
        q = ELEC_QUANTITIES[[_tr(n) + f" ({s})" for s, n in ELEC_QUANTITIES].index(self.qty_var.get())][0] \
            if self.qty_var.get() else "V"
        pre = FULL_SI_PREFIXES if self.full_si.get() else UNIT_PREFIXES
        out = []
        for sym, name, f in pre:
            out.append((sym + q, (_PREFIX_NAME.get(sym, name) + " " if sym else "") + f"(× {f:g})", lin(f)))
        return out

    def _on_category(self):
        key, name, units = self._cat()
        self.title_var.set(_tr(name))
        if key == "elec":
            labels = [_tr(n) + f" ({s})" for s, n in ELEC_QUANTITIES]
            self.qty_cb.configure(values=labels)
            if self.qty_var.get() not in labels:
                self.qty_var.set(labels[0])
            self.qty_cb.pack(side="left", padx=4, before=self.unit_cb)
            self.full_cb.pack(side="left", padx=8)
            self.hint_var.set(t("uc2.elec_hint"))
            self._on_qty()
            return
        self.qty_cb.pack_forget()
        self.full_cb.pack_forget()
        self._units = units
        self.unit_cb.configure(values=[u[0] for u in units])
        self.unit_var.set(units[0][0])
        self.hint_var.set(t("uc2.hint_" + key) if t("uc2.hint_" + key) != "uc2.hint_" + key else t("uc2.hint"))
        self._update()

    def _on_qty(self):
        self._units = self._elec_units()
        vals = [u[0] for u in self._units]
        self.unit_cb.configure(values=vals)
        if self.unit_var.get() not in vals:
            # start from the plain unit (prefix factor 1)
            self.unit_var.set(next(u[0] for u in self._units if abs(u[2][0](1) - 1) < 1e-12))
        self._update()

    def _update(self):
        if self._mute:
            return
        self.tree.delete(*self.tree.get_children())
        try:
            raw = self.val_var.get().replace(",", ".").strip()
            v = parse_value(raw) if self._cat()[0] == "elec" else float(raw.replace(" ", ""))
        except Exception:
            self.best_var.set(t("uc.invalid_value"))
            return
        src = next((u for u in self._units if u[0] == self.unit_var.get()), self._units[0])
        try:
            base = src[2][0](v)
        except Exception:
            self.best_var.set("—")
            return
        best = None
        for sym, desc, (to_b, from_b) in self._units:
            try:
                val = from_b(base)
            except Exception:
                val = float("nan")
            tags = ["src"] if sym == src[0] else []
            if self._cat()[0] == "elec" and isinstance(val, float) and 1 <= abs(val) < 1000 and best is None:
                best = (sym, val)
                tags.append("best")
            self.tree.insert("", "end", iid=sym, values=(sym, fmt_num(val), _tr(desc)), tags=tags)
        if self._cat()[0] == "elec" and best:
            self.best_var.set(f"= {best[1]:.6g} {best[0]}")
        else:
            self.best_var.set(f"{fmt_num(v)} {src[0]}")

    def _on_row(self, _e):
        sel = self.tree.selection()
        if not sel or sel[0] == self.unit_var.get():
            return
        vals = self.tree.item(sel[0], "values")
        txt = vals[1].replace(" × 10^", "e")
        if txt == "—":
            return
        self._mute = True
        self.val_var.set(txt)
        self.unit_var.set(sel[0])
        self._mute = False
        self._update()


# ---------------------------------------------------------------------------
# 2. dB & signal levels (linked fields)
# ---------------------------------------------------------------------------
class LevelsPanel(ttk.Frame):
    FIELDS = [
        ("w", "P (W)", "uc2.lv.w"), ("dbm", "dBm", "uc2.lv.dbm"), ("dbw", "dBW", "uc2.lv.dbw"),
        ("vrms", "V rms", "uc2.lv.vrms"), ("vpk", "V peak", "uc2.lv.vpk"), ("vpp", "V p-p", "uc2.lv.vpp"),
        ("dbv", "dBV", "uc2.lv.dbv"), ("dbu", "dBu", "uc2.lv.dbu"), ("dbuv", "dBµV", "uc2.lv.dbuv"),
    ]

    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        wrap, body = _scroll_page(self)
        wrap.grid(row=0, column=0, sticky="nsew")
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        self._mute = False

        ttk.Label(body, text=t("uc2.lv.intro"), font=FONT_BODY, style="CardBody.TLabel", wraplength=900,
                  justify="left").grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 8))

        # --- absolute levels ---
        lv = ttk.Frame(body, style="Card.TFrame")
        lv.grid(row=1, column=0, sticky="nw", padx=16)
        ttk.Label(lv, text=t("uc2.lv.abs_title"), font=FONT_H2, foreground=ACCENT_C, style="CardTitle.TLabel")\
            .grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        ttk.Label(lv, text=t("uc2.lv.impedance"), font=FONT_BODY, style="CardBody.TLabel").grid(row=1, column=0, sticky="w")
        self.r_var = tk.StringVar(value="50")
        rf = ttk.Frame(lv, style="Card.TFrame")
        rf.grid(row=1, column=1, columnspan=2, sticky="w", pady=2)
        re_ = ttk.Entry(rf, textvariable=self.r_var, width=8, font=FONT_MONO)
        re_.pack(side="left")
        re_.bind("<KeyRelease>", lambda e: self._recalc(self._last))
        ttk.Label(rf, text="Ω", font=FONT_BODY, style="CardBody.TLabel").pack(side="left", padx=(3, 8))
        for r in ("50", "75", "600", "1M"):
            ttk.Button(rf, text=r, width=4, style="Small.TButton",
                       command=lambda r=r: (self.r_var.set(r), self._recalc(self._last))).pack(side="left", padx=1)
        self.vars = {}
        for i, (key, lab, desc) in enumerate(self.FIELDS, start=2):
            ttk.Label(lv, text=lab, font=("Segoe UI", 10, "bold"), style="CardBody.TLabel", width=8)\
                .grid(row=i, column=0, sticky="w", pady=2)
            v = tk.StringVar()
            e = ttk.Entry(lv, textvariable=v, width=18, font=FONT_MONO)
            e.grid(row=i, column=1, sticky="w", pady=2)
            e.bind("<KeyRelease>", lambda ev, k=key: self._recalc(k))
            ttk.Label(lv, text=t(desc), font=("Segoe UI", 8), foreground="#777", style="CardBody.TLabel")\
                .grid(row=i, column=2, sticky="w", padx=8)
            self.vars[key] = v
        self.lv_note = tk.StringVar()
        ttk.Label(lv, textvariable=self.lv_note, font=("Segoe UI", 8), foreground="#a15c00", style="CardBody.TLabel",
                  wraplength=460, justify="left").grid(row=20, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # --- ratios ---
        rt = ttk.Frame(body, style="Card.TFrame")
        rt.grid(row=1, column=1, sticky="nw", padx=16)
        ttk.Label(rt, text=t("uc2.lv.ratio_title"), font=FONT_H2, foreground=ACCENT_C, style="CardTitle.TLabel")\
            .grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 6))
        self.rvars = {}
        for i, (key, lab) in enumerate((("db", "dB"), ("pr", t("uc2.lv.pratio")), ("vr", t("uc2.lv.vratio")),
                                         ("pct", t("uc2.lv.vpct"))), start=1):
            ttk.Label(rt, text=lab, font=("Segoe UI", 10, "bold"), style="CardBody.TLabel")\
                .grid(row=i, column=0, sticky="w", pady=2)
            v = tk.StringVar()
            e = ttk.Entry(rt, textvariable=v, width=16, font=FONT_MONO)
            e.grid(row=i, column=1, sticky="w", pady=2, padx=6)
            e.bind("<KeyRelease>", lambda ev, k=key: self._ratio(k))
            self.rvars[key] = v
        ttk.Label(rt, text=t("uc2.lv.ratio_note"), font=("Segoe UI", 8), foreground="#777", style="CardBody.TLabel",
                  wraplength=380, justify="left").grid(row=6, column=0, columnspan=3, sticky="w", pady=(4, 8))
        tv = ttk.Treeview(rt, columns=("db", "p", "v"), show="headings", height=11)
        for c, key, w in (("db", "db.table.db", 70), ("p", "db.table.power_ratio", 120), ("v", "db.table.voltage_ratio", 120)):
            tv.heading(c, text=t(key))
            tv.column(c, width=w, anchor="center")
        for db in (-40, -20, -10, -6, -3, 0, 3, 6, 10, 20, 40):
            tv.insert("", "end", values=(f"{db:+d}" if db else "0", f"× {10 ** (db / 10):.4g}", f"× {10 ** (db / 20):.4g}"))
        tv.grid(row=7, column=0, columnspan=3, sticky="w")
        tv.bind("<<TreeviewSelect>>", lambda e: self._pick_db(tv))

        self._last = "dbm"
        self.vars["dbm"].set("0")
        self._recalc("dbm")
        self.rvars["db"].set("3")
        self._ratio("db")

    def _r(self):
        return max(1e-12, parse_value(self.r_var.get().replace(",", ".")))

    def _recalc(self, src):
        if self._mute:
            return
        self._last = src
        try:
            x = float(parse_value(self.vars[src].get().replace(",", "."))) if src in ("w", "vrms", "vpk", "vpp") \
                else float(self.vars[src].get().replace(",", "."))
            r = self._r()
        except Exception:
            return
        # everything through P (W) and Vrms
        if src == "w":
            p = x
        elif src == "dbm":
            p = 1e-3 * 10 ** (x / 10)
        elif src == "dbw":
            p = 10 ** (x / 10)
        else:
            vr = {"vrms": x, "vpk": x / math.sqrt(2), "vpp": x / (2 * math.sqrt(2)),
                  "dbv": 10 ** (x / 20), "dbu": 0.7745966692 * 10 ** (x / 20), "dbuv": 1e-6 * 10 ** (x / 20)}[src]
            p = vr * vr / r
        if p <= 0:
            return
        vr = math.sqrt(p * r)
        out = {"w": p, "dbm": 10 * math.log10(p / 1e-3), "dbw": 10 * math.log10(p), "vrms": vr,
               "vpk": vr * math.sqrt(2), "vpp": vr * 2 * math.sqrt(2), "dbv": 20 * math.log10(vr),
               "dbu": 20 * math.log10(vr / 0.7745966692), "dbuv": 20 * math.log10(vr / 1e-6)}
        self._mute = True
        for k, v in out.items():
            if k == src:
                continue
            if k in ("w", "vrms", "vpk", "vpp"):
                self.vars[k].set(_eng(v, "W" if k == "w" else "V"))
            else:
                self.vars[k].set(f"{v:.3f}")
        self._mute = False
        self.lv_note.set(t("uc2.lv.note").format(r=_eng(r, "Ω")))

    def _ratio(self, src):
        try:
            x = float(self.rvars[src].get().replace(",", "."))
        except Exception:
            return
        if src == "db":
            db = x
        elif src == "pr":
            if x <= 0:
                return
            db = 10 * math.log10(x)
        elif src == "vr":
            if x <= 0:
                return
            db = 20 * math.log10(x)
        else:
            if x <= 0:
                return
            db = 20 * math.log10(x / 100)
        vals = {"db": f"{db:.4g}", "pr": f"{10 ** (db / 10):.6g}", "vr": f"{10 ** (db / 20):.6g}",
                "pct": f"{100 * 10 ** (db / 20):.4g}"}
        for k, v in vals.items():
            if k != src:
                self.rvars[k].set(v)

    def _pick_db(self, tv):
        sel = tv.selection()
        if sel:
            self.rvars["db"].set(tv.item(sel[0], "values")[0].replace("+", ""))
            self._ratio("db")


def _eng(v, unit):
    if v == 0:
        return "0"
    for sym, f in (("T", 1e12), ("G", 1e9), ("M", 1e6), ("k", 1e3), ("", 1), ("m", 1e-3), ("µ", 1e-6),
                   ("n", 1e-9), ("p", 1e-12), ("f", 1e-15)):
        if abs(v) >= f:
            return f"{v / f:.5g}{sym}"
    return f"{v:.4g}"


# ---------------------------------------------------------------------------
# 3. Number systems with a bit grid
# ---------------------------------------------------------------------------
class NumberPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        wrap, body = _scroll_page(self)
        wrap.grid(row=0, column=0, sticky="nsew")
        self._mute = False
        self.value = 0xA5

        ttk.Label(body, text=t("uc2.nb.intro"), font=FONT_BODY, style="CardBody.TLabel", wraplength=900,
                  justify="left").grid(row=0, column=0, sticky="w", padx=16, pady=(12, 8))
        cfg = ttk.Frame(body, style="Card.TFrame")
        cfg.grid(row=1, column=0, sticky="w", padx=16)
        ttk.Label(cfg, text=t("uc2.nb.width"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self.bits = tk.IntVar(value=8)
        for b in (8, 16, 32, 64):
            ttk.Radiobutton(cfg, text=f"{b}-bit", value=b, variable=self.bits, command=self._refresh)\
                .pack(side="left", padx=4)
        self.signed = tk.BooleanVar(value=False)
        ttk.Checkbutton(cfg, text=t("uc2.nb.signed"), variable=self.signed, command=self._refresh)\
            .pack(side="left", padx=(16, 0))

        grid = ttk.Frame(body, style="Card.TFrame")
        grid.grid(row=2, column=0, sticky="w", padx=16, pady=(8, 4))
        self.fields = {}
        rows = [("dec", t("uc2.nb.dec"), 10), ("hex", t("uc2.nb.hex"), 16), ("oct", t("uc2.nb.oct"), 8),
                ("bin", t("uc2.nb.bin"), 2), ("ascii", t("uc2.nb.ascii"), None)]
        for i, (key, lab, base) in enumerate(rows):
            ttk.Label(grid, text=lab, font=("Segoe UI", 10, "bold"), style="CardBody.TLabel", width=18)\
                .grid(row=i, column=0, sticky="w", pady=2)
            v = tk.StringVar()
            e = ttk.Entry(grid, textvariable=v, width=72 if key == "bin" else 30, font=("Consolas", 12))
            e.grid(row=i, column=1, sticky="w", pady=2)
            e.bind("<KeyRelease>", lambda ev, k=key: self._from_field(k))
            self.fields[key] = v
        self.err = tk.StringVar()
        ttk.Label(body, textvariable=self.err, foreground="#b91c1c", style="CardBody.TLabel")\
            .grid(row=3, column=0, sticky="w", padx=16)

        ttk.Label(body, text=t("uc2.nb.bits_title"), font=FONT_H2, foreground=ACCENT_C, style="CardTitle.TLabel")\
            .grid(row=4, column=0, sticky="w", padx=16, pady=(8, 2))
        self.cv = tk.Canvas(body, height=140, bg="white", highlightthickness=0)
        self.cv.grid(row=5, column=0, sticky="ew", padx=16)
        body.columnconfigure(0, weight=1)
        self.cv.bind("<Button-1>", self._click_bit)
        self.cv.bind("<Configure>", debounce(self.cv, lambda *a: self._draw_bits(), 100))
        tools = ttk.Frame(body, style="Card.TFrame")
        tools.grid(row=6, column=0, sticky="w", padx=16, pady=(6, 4))
        for lab, fn in ((t("uc2.nb.clear"), lambda v, n: 0), (t("uc2.nb.all1"), lambda v, n: (1 << n) - 1),
                        (t("uc2.nb.invert"), lambda v, n: ~v & ((1 << n) - 1)),
                        ("<< 1", lambda v, n: (v << 1) & ((1 << n) - 1)), (">> 1", lambda v, n: v >> 1),
                        ("+1", lambda v, n: (v + 1) & ((1 << n) - 1)), ("−1", lambda v, n: (v - 1) & ((1 << n) - 1))):
            ttk.Button(tools, text=lab, style="Small.TButton",
                       command=lambda fn=fn: self._op(fn)).pack(side="left", padx=2)
        self.info = tk.StringVar()
        ttk.Label(body, textvariable=self.info, font=("Consolas", 10, "bold"), foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left").grid(row=7, column=0, sticky="w", padx=16, pady=(6, 16))
        self._refresh()

    def _mask(self):
        return (1 << self.bits.get()) - 1

    def _signed_val(self):
        n = self.bits.get()
        v = self.value & self._mask()
        return v - (1 << n) if self.signed.get() and v >> (n - 1) else v

    def _op(self, fn):
        self.value = fn(self.value & self._mask(), self.bits.get()) & self._mask()
        self._refresh()

    def _from_field(self, key):
        if self._mute:
            return
        txt = self.fields[key].get().strip().replace(" ", "").replace("_", "")
        self.err.set("")
        if not txt:
            return
        try:
            if key == "ascii":
                v = 0
                for ch in self.fields[key].get()[: self.bits.get() // 8]:
                    v = (v << 8) | (ord(ch) & 0xFF)
            else:
                base = {"dec": 10, "hex": 16, "oct": 8, "bin": 2}[key]
                for pre in ("0x", "0X", "0b", "0B", "0o", "0O"):
                    if txt.startswith(pre):
                        txt = txt[2:]
                v = int(txt, base)
            n = self.bits.get()
            if key == "dec" and v < 0:
                if v < -(1 << (n - 1)):
                    raise OverflowError
                v &= self._mask()
            elif v > self._mask():
                raise OverflowError
        except OverflowError:
            self.err.set(t("uc2.nb.overflow").format(n=self.bits.get()))
            return
        except ValueError:
            self.err.set(t("uc2.nb.invalid"))
            return
        self.value = v
        self._refresh(skip=key)

    def _refresh(self, skip=None):
        v = self.value & self._mask()
        self.value = v
        n = self.bits.get()
        self._mute = True
        grp = lambda s, k: " ".join(s[max(0, i - k):i] for i in range(len(s), 0, -k)[::-1])  # noqa: E731
        vals = {
            "dec": str(self._signed_val()),
            "hex": grp(f"{v:0{n // 4}X}", 4),
            "oct": f"{v:o}",
            "bin": grp(f"{v:0{n}b}", 4),
            "ascii": "".join(chr(b) if 32 <= b < 127 else "·" for b in v.to_bytes(n // 8, "big")),
        }
        for k, s in vals.items():
            if k != skip:
                self.fields[k].set(s)
        self._mute = False
        sv = self._signed_val()
        uns = v
        self.info.set(
            f"{t('uc2.nb.unsigned')}: {uns}    {t('uc2.nb.signed_val')}: "
            f"{v - (1 << n) if v >> (n - 1) else v}    {t('uc2.nb.range')}: "
            f"{'−' + str(1 << (n - 1)) + ' … ' + str((1 << (n - 1)) - 1) if self.signed.get() else '0 … ' + str((1 << n) - 1)}\n"
            f"{t('uc2.nb.ones')}: {bin(v).count('1')}    MSB = bit {n - 1}    "
            f"{t('uc2.nb.bytes')}: {' '.join(f'{b:02X}' for b in v.to_bytes(n // 8, 'big'))}   "
            f"(little-endian: {' '.join(f'{b:02X}' for b in v.to_bytes(n // 8, 'little'))})")
        _ = sv
        self._draw_bits()

    def _bit_geo(self):
        n = self.bits.get()
        W = max(self.cv.winfo_width(), 500)
        per_row = min(n, 32)
        rows = n // per_row
        gap = 6
        cell = min(34, (W - 20 - gap * (per_row // 4 - 1)) / per_row)
        return n, per_row, rows, cell, gap

    def _draw_bits(self):
        c = self.cv
        c.delete("all")
        n, per_row, rows, cell, gap = self._bit_geo()
        v = self.value
        for r in range(rows):
            for j in range(per_row):
                bit = n - 1 - (r * per_row + j)
                x = 10 + j * cell + (j // 4) * gap
                y = 22 + r * (cell + 30)
                on = (v >> bit) & 1
                sign = self.signed.get() and bit == n - 1
                fill = ("#b91c1c" if sign else ACCENT_C) if on else "white"
                c.create_rectangle(x, y, x + cell - 3, y + cell - 3, fill=fill, outline="#94a3b8",
                                   tags=("bit", f"b{bit}"))
                c.create_text(x + (cell - 3) / 2, y + (cell - 3) / 2, text=str(on), fill="white" if on else "#555",
                              font=("Consolas", 11 if cell > 22 else 8, "bold"), tags=(f"b{bit}",))
                c.create_text(x + (cell - 3) / 2, y - 8, text=str(bit), fill="#777",
                              font=("Segoe UI", 7 if cell > 18 else 6))
                if bit % 4 == 0 and cell > 14:
                    weight = f"2^{bit}"
                    c.create_text(x + (cell - 3) / 2, y + cell + 6, text=weight, fill="#999", font=("Segoe UI", 6))
        c.configure(height=22 + rows * (cell + 30))

    def _click_bit(self, e):
        n, per_row, rows, cell, gap = self._bit_geo()
        for r in range(rows):
            y = 22 + r * (cell + 30)
            if not (y <= e.y <= y + cell):
                continue
            for j in range(per_row):
                x = 10 + j * cell + (j // 4) * gap
                if x <= e.x <= x + cell:
                    bit = n - 1 - (r * per_row + j)
                    self.value ^= 1 << bit
                    self._refresh()
                    return
