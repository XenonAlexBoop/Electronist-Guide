"""
solver.py - "Solve for anything" formula calculator.

Each formula is written once, in its natural form  out = f(inputs).  The
panel lets the user pick ANY of its variables as the unknown: if the unknown
is the output it is computed directly, otherwise it is found numerically
(robust sign-change scan + bisection over a logarithmic range for positive
quantities, or a linear range for quantities that may be negative).
So one definition gives every rearrangement of the formula for free.

Values accept SI prefixes (4.7k, 100n, 10u, 2.2M ...).
"""
import math
import tkinter as tk
from tkinter import ttk

from widgets import parse_value, format_value, FONT_BODY, FONT_H2, FONT_MONO
from i18n import t, get_language

PI = math.pi
EPS0 = 8.8541878128e-12
MU0 = 4e-7 * math.pi


def L(en, ro):
    return ro if get_language() == "ro" else en


class Var:
    def __init__(self, key, symbol, name, unit, default, signed=False, presets=None):
        self.key = key            # python identifier used by the formula function
        self.symbol = symbol      # printed symbol, e.g. "Xc"
        self.name = name          # (en, ro)
        self.unit = unit          # base unit shown to the user ('' = dimensionless)
        self.default = default    # default text
        self.signed = signed      # may be negative / zero
        self.presets = presets    # optional [((en, ro), value_text), ...]


class Formula:
    def __init__(self, title, equation, out, fn, variables, note=None):
        self.title = title        # (en, ro)
        self.equation = equation  # display text
        self.out = out            # key of the output variable
        self.fn = fn              # fn(**values) -> out value
        self.vars = variables     # list[Var] (output first is conventional)
        self.note = note          # optional (en, ro)


# ---------------------------------------------------------------------------
# Numeric inversion
# ---------------------------------------------------------------------------
def _safe(fn, kw):
    try:
        with_np = fn(**kw)
        y = float(with_np)
        if math.isnan(y) or math.isinf(y):
            return None
        return y
    except (ZeroDivisionError, OverflowError, ValueError):
        return None


def solve_for(formula, unknown, known):
    """Return a list of solutions for `unknown` (may be empty)."""
    if unknown == formula.out:
        y = _safe(formula.fn, known)
        return [] if y is None else [y]
    target = known[formula.out]
    var = next(v for v in formula.vars if v.key == unknown)

    def g(x):
        kw = dict(known)
        kw.pop(formula.out, None)
        kw[unknown] = x
        y = _safe(formula.fn, kw)
        return None if y is None else y - target

    roots = []
    if var.signed:
        # linear scans over widening ranges (e.g. temperature change, phase)
        grids = []
        for span in (1e3, 1e6, 1e12):
            n = 4000
            grids.append([-span + 2 * span * i / n for i in range(n + 1)])
        transform = None
    else:
        n = 3000
        grids = [[-18 + 33 * i / n for i in range(n + 1)]]   # log10(x) from 1e-18 to 1e15
        transform = lambda u: 10 ** u  # noqa: E731

    for grid in grids:
        prev_u, prev_g = None, None
        for u in grid:
            x = transform(u) if transform else u
            gv = g(x)
            if gv is None:
                prev_u, prev_g = None, None
                continue
            if gv == 0:
                roots.append(x)
            elif prev_g is not None and (prev_g < 0) != (gv < 0):
                lo, hi, glo = prev_u, u, prev_g
                ok = True
                for _ in range(200):
                    mid = (lo + hi) / 2
                    gm = g(transform(mid) if transform else mid)
                    if gm is None:
                        ok = False
                        break
                    if (gm < 0) == (glo < 0):
                        lo, glo = mid, gm
                    else:
                        hi = mid
                x = transform((lo + hi) / 2) if transform else (lo + hi) / 2
                # reject sign changes caused by poles (|g| must actually be small)
                gx = g(x)
                if ok and gx is not None and abs(gx) <= 1e-6 * max(1.0, abs(target)):
                    roots.append(x)
            prev_u, prev_g = u, gv
        if roots:
            break
    uniq = []
    for r in sorted(roots):
        if not uniq or abs(r - uniq[-1]) > 1e-9 * max(1.0, abs(r)):
            uniq.append(r)
    return uniq[:4]


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
class FormulaSolverPanel(ttk.Frame):
    def __init__(self, parent, formulas, accent, intro=None):
        super().__init__(parent, style="Card.TFrame")
        self.formulas = formulas
        self.accent = accent
        self.columnconfigure(0, weight=1)

        ttk.Label(self, text=intro or t("solver.intro"), font=FONT_BODY, style="CardBody.TLabel",
                  wraplength=560, justify="left").grid(row=0, column=0, sticky="w", padx=16, pady=(12, 6))

        top = ttk.Frame(self, style="Card.TFrame")
        top.grid(row=1, column=0, sticky="w", padx=16)
        ttk.Label(top, text=t("solver.choose"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self._titles = [f"{i + 1}. {L(*f.title)}" for i, f in enumerate(formulas)]
        self.formula_var = tk.StringVar(value=self._titles[0])
        cb = ttk.Combobox(top, textvariable=self.formula_var, values=self._titles, state="readonly", width=46)
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda e: self._build_form())

        self.eq_var = tk.StringVar()
        ttk.Label(self, textvariable=self.eq_var, font=("Consolas", 15, "bold"), foreground=accent,
                  style="CardFormula.TLabel").grid(row=2, column=0, sticky="w", padx=16, pady=(12, 2))
        self.note_var = tk.StringVar()
        ttk.Label(self, textvariable=self.note_var, font=("Segoe UI", 9), style="CardBody.TLabel",
                  wraplength=560, justify="left").grid(row=3, column=0, sticky="w", padx=16)

        self.form = ttk.Frame(self, style="Card.TFrame")
        self.form.grid(row=4, column=0, sticky="w", padx=16, pady=8)

        self.result_var = tk.StringVar()
        ttk.Label(self, textvariable=self.result_var, font=FONT_MONO, foreground=accent,
                  style="CardFormula.TLabel", justify="left", wraplength=560)\
            .grid(row=5, column=0, sticky="w", padx=16, pady=(4, 4))
        ttk.Label(self, text=t("solver.hint"), font=("Segoe UI", 8), style="CardBody.TLabel",
                  foreground="#666", wraplength=560, justify="left")\
            .grid(row=6, column=0, sticky="w", padx=16, pady=(4, 16))

        self._build_form()

    def _formula(self):
        return self.formulas[self._titles.index(self.formula_var.get())]

    def _build_form(self):
        for ch in self.form.winfo_children():
            ch.destroy()
        f = self._formula()
        self.eq_var.set(f.equation)
        self.note_var.set(L(*f.note) if f.note else "")
        self.entries, self.vars = {}, {}
        self.solve_var = tk.StringVar(value=f.out)
        hdr = ("Segoe UI", 8, "bold")
        ttk.Label(self.form, text=t("solver.col_solve"), font=hdr, style="CardBody.TLabel")\
            .grid(row=0, column=0, padx=(0, 6))
        ttk.Label(self.form, text=t("solver.col_symbol"), font=hdr, style="CardBody.TLabel")\
            .grid(row=0, column=1, sticky="w")
        ttk.Label(self.form, text=t("solver.col_quantity"), font=hdr, style="CardBody.TLabel")\
            .grid(row=0, column=2, sticky="w", padx=(6, 6))
        ttk.Label(self.form, text=t("solver.col_value"), font=hdr, style="CardBody.TLabel")\
            .grid(row=0, column=3, sticky="w")
        for r, v in enumerate(f.vars, start=1):
            ttk.Radiobutton(self.form, variable=self.solve_var, value=v.key,
                            command=self._on_solve_change).grid(row=r, column=0, pady=2)
            ttk.Label(self.form, text=v.symbol, font=("Consolas", 11, "bold"), foreground=self.accent,
                      style="CardFormula.TLabel").grid(row=r, column=1, sticky="w")
            ttk.Label(self.form, text=L(*v.name), font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=r, column=2, sticky="w", padx=(6, 6))
            var = tk.StringVar(value=v.default)
            ent = ttk.Entry(self.form, textvariable=var, width=14)
            ent.grid(row=r, column=3, sticky="w", pady=2)
            ent.bind("<KeyRelease>", lambda e: self._compute())
            ttk.Label(self.form, text=v.unit, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=r, column=4, sticky="w", padx=(4, 6))
            if v.presets:
                labels = [L(*lbl) for lbl, _ in v.presets]
                pv = tk.StringVar(value=t("solver.presets"))
                pc = ttk.Combobox(self.form, textvariable=pv, values=labels, state="readonly", width=16)
                pc.grid(row=r, column=5, sticky="w")

                def _apply(_e, _pv=pv, _var=var, _v=v, _labels=labels):
                    idx = _labels.index(_pv.get())
                    _var.set(_v.presets[idx][1])
                    self._compute()
                pc.bind("<<ComboboxSelected>>", _apply)
            self.entries[v.key] = ent
            self.vars[v.key] = var
        self._on_solve_change()

    def _on_solve_change(self):
        unknown = self.solve_var.get()
        for k, ent in self.entries.items():
            ent.configure(state="readonly" if k == unknown else "normal")
        self._compute()

    def _compute(self):
        f = self._formula()
        unknown = self.solve_var.get()
        known = {}
        try:
            for v in f.vars:
                if v.key == unknown:
                    continue
                known[v.key] = parse_value(self.vars[v.key].get())
        except Exception:
            self.result_var.set(t("common.enter_valid_values"))
            return
        sols = solve_for(f, unknown, known)
        var = next(v for v in f.vars if v.key == unknown)
        if not sols:
            self.result_var.set(t("solver.no_solution").format(sym=var.symbol))
            self.vars[unknown].set("")
            return
        x = sols[0]
        self.vars[unknown].set(f"{x:.6g}")
        pretty = [self._fmt(s, var.unit) for s in sols]
        txt = f"{var.symbol} = " + ("   " + t("solver.or") + "   ").join(pretty)
        if len(sols) > 1:
            txt += "\n" + t("solver.multiple")
        self.result_var.set(txt)

    @staticmethod
    def _fmt(x, unit):
        if unit in ("", "°C", "°", "%", "rad", "1/°C", "Ω·m", "m²", "m"):
            return f"{x:.6g} {unit}".strip()
        return f"{format_value(float(f'{x:.5g}'), unit)}   ({x:.6g} {unit})".strip()


# ---------------------------------------------------------------------------
# Formula libraries
# ---------------------------------------------------------------------------
def _V(key, sym, en, ro, unit, default, **kw):
    return Var(key, sym, (en, ro), unit, default, **kw)


RESISTIVITY_PRESETS = [
    (("Silver", "Argint"), "1.59e-8"), (("Copper", "Cupru"), "1.68e-8"),
    (("Gold", "Aur"), "2.44e-8"), (("Aluminium", "Aluminiu"), "2.65e-8"),
    (("Tungsten", "Wolfram"), "5.6e-8"), (("Iron", "Fier"), "9.7e-8"),
    (("Nichrome", "Nichrom"), "1.1e-6"), (("Constantan", "Constantan"), "4.9e-7"),
]
ALPHA_PRESETS = [
    (("Copper", "Cupru"), "0.00393"), (("Aluminium", "Aluminiu"), "0.00403"),
    (("Silver", "Argint"), "0.0038"), (("Tungsten", "Wolfram"), "0.0045"),
    (("Nichrome", "Nichrom"), "0.0004"), (("Constantan", "Constantan"), "0.000008"),
]
EPSR_PRESETS = [
    (("Vacuum / air", "Vid / aer"), "1"), (("Paper", "Hârtie"), "3.5"), (("Mica", "Mică"), "6"),
    (("Glass", "Sticlă"), "7"), (("Ceramic C0G", "Ceramică C0G"), "30"),
    (("Tantalum oxide", "Oxid de tantal"), "27"), (("Aluminium oxide", "Oxid de aluminiu"), "9"),
]
MUR_PRESETS = [
    (("Air core", "Miez de aer"), "1"), (("Iron powder", "Pulbere de fier"), "75"),
    (("Ferrite (MnZn)", "Ferită (MnZn)"), "2000"), (("Ferrite (NiZn)", "Ferită (NiZn)"), "300"),
    (("Silicon steel", "Oțel electrotehnic"), "4000"),
]


def resistor_formulas():
    return [
        Formula(("Ohm's law  (V, I, R)", "Legea lui Ohm  (U, I, R)"), "V = I · R", "V",
                lambda I, R: I * R,
                [_V("V", "V", "Voltage", "Tensiune", "V", "12"),
                 _V("I", "I", "Current", "Curent", "A", "20m"),
                 _V("R", "R", "Resistance", "Rezistență", "Ω", "600")]),
        Formula(("Power from V and I", "Putere din U și I"), "P = V · I", "P",
                lambda V, I: V * I,
                [_V("P", "P", "Power", "Putere", "W", ""), _V("V", "V", "Voltage", "Tensiune", "V", "12"),
                 _V("I", "I", "Current", "Curent", "A", "0.5")]),
        Formula(("Power from I and R (Joule)", "Putere din I și R (Joule)"), "P = I² · R", "P",
                lambda I, R: I * I * R,
                [_V("P", "P", "Power", "Putere", "W", ""), _V("I", "I", "Current", "Curent", "A", "0.1"),
                 _V("R", "R", "Resistance", "Rezistență", "Ω", "100")]),
        Formula(("Power from V and R", "Putere din U și R"), "P = V² / R", "P",
                lambda V, R: V * V / R,
                [_V("P", "P", "Power", "Putere", "W", ""), _V("V", "V", "Voltage", "Tensiune", "V", "5"),
                 _V("R", "R", "Resistance", "Rezistență", "Ω", "220")]),
        Formula(("Resistance of a wire (resistivity)", "Rezistența unui conductor (rezistivitate)"),
                "R = ρ · ℓ / A", "R", lambda rho, l, A: rho * l / A,
                [_V("R", "R", "Resistance", "Rezistență", "Ω", ""),
                 _V("rho", "ρ", "Resistivity", "Rezistivitate", "Ω·m", "1.68e-8", presets=RESISTIVITY_PRESETS),
                 _V("l", "ℓ", "Length", "Lungime", "m", "10"),
                 _V("A", "A", "Cross-section area", "Aria secțiunii", "m²", "1.5e-6")],
                note=("1 mm² = 1e-6 m². Tip: type lengths in metres (\"10\"), not \"10m\" (m = milli).",
                      "1 mm² = 1e-6 m². Sfat: scrie lungimea în metri (\"10\"), nu \"10m\" (m = mili).")),
        Formula(("Resistance of a round wire (diameter)", "Rezistența unui fir rotund (diametru)"),
                "R = ρ · ℓ / (π · d² / 4)", "R", lambda rho, l, d: rho * l / (PI * d * d / 4),
                [_V("R", "R", "Resistance", "Rezistență", "Ω", ""),
                 _V("rho", "ρ", "Resistivity", "Rezistivitate", "Ω·m", "1.68e-8", presets=RESISTIVITY_PRESETS),
                 _V("l", "ℓ", "Length", "Lungime", "m", "10"),
                 _V("d", "d", "Wire diameter", "Diametrul firului", "m", "0.5e-3")]),
        Formula(("Resistance vs temperature", "Rezistența în funcție de temperatură"),
                "R_T = R₀ · (1 + α · ΔT)", "RT", lambda R0, alpha, dT: R0 * (1 + alpha * dT),
                [_V("RT", "R_T", "Resistance at T", "Rezistența la T", "Ω", ""),
                 _V("R0", "R₀", "Resistance at 20 °C", "Rezistența la 20 °C", "Ω", "100"),
                 _V("alpha", "α", "Temperature coefficient", "Coeficient de temperatură", "1/°C", "0.00393",
                    presets=ALPHA_PRESETS),
                 _V("dT", "ΔT", "Temperature change", "Variația temperaturii", "°C", "80", signed=True)]),
        Formula(("Voltage divider (unloaded)", "Divizor de tensiune (fără sarcină)"),
                "Vout = Vin · R2 / (R1 + R2)", "Vout", lambda Vin, R1, R2: Vin * R2 / (R1 + R2),
                [_V("Vout", "Vout", "Output voltage", "Tensiune de ieșire", "V", ""),
                 _V("Vin", "Vin", "Input voltage", "Tensiune de intrare", "V", "12"),
                 _V("R1", "R1", "Top resistor", "Rezistorul de sus", "Ω", "10k"),
                 _V("R2", "R2", "Bottom resistor", "Rezistorul de jos", "Ω", "4.7k")]),
        Formula(("Current divider (2 branches)", "Divizor de curent (2 ramuri)"),
                "I1 = I · R2 / (R1 + R2)", "I1", lambda I, R1, R2: I * R2 / (R1 + R2),
                [_V("I1", "I1", "Current through R1", "Curentul prin R1", "A", ""),
                 _V("I", "I", "Total current", "Curent total", "A", "100m"),
                 _V("R1", "R1", "Branch 1 resistance", "Rezistența ramurii 1", "Ω", "1k"),
                 _V("R2", "R2", "Branch 2 resistance", "Rezistența ramurii 2", "Ω", "2.2k")]),
        Formula(("Two resistors in series", "Două rezistoare în serie"), "Rs = R1 + R2", "Rs",
                lambda R1, R2: R1 + R2,
                [_V("Rs", "Rs", "Equivalent", "Echivalent", "Ω", ""),
                 _V("R1", "R1", "Resistor 1", "Rezistor 1", "Ω", "1k"), _V("R2", "R2", "Resistor 2", "Rezistor 2", "Ω", "2.2k")]),
        Formula(("Two resistors in parallel", "Două rezistoare în paralel"), "Rp = R1 · R2 / (R1 + R2)", "Rp",
                lambda R1, R2: R1 * R2 / (R1 + R2),
                [_V("Rp", "Rp", "Equivalent", "Echivalent", "Ω", ""),
                 _V("R1", "R1", "Resistor 1", "Rezistor 1", "Ω", "1k"), _V("R2", "R2", "Resistor 2", "Rezistor 2", "Ω", "2.2k")],
                note=("Tip: choose R2 as the unknown to find which resistor to add in parallel to reach a target value.",
                      "Sfat: alege R2 ca necunoscută ca să afli ce rezistor să pui în paralel pentru a obține o valoare dorită.")),
        Formula(("Conductance", "Conductanță"), "G = 1 / R", "G", lambda R: 1 / R,
                [_V("G", "G", "Conductance", "Conductanță", "S", ""), _V("R", "R", "Resistance", "Rezistență", "Ω", "470")]),
        Formula(("Energy dissipated (heat)", "Energie disipată (căldură)"), "W = P · t", "W", lambda P, time: P * time,
                [_V("W", "W", "Energy", "Energie", "J", ""), _V("P", "P", "Power", "Putere", "W", "0.25"),
                 _V("time", "t", "Time", "Timp", "s", "3600")],
                note=("1 Wh = 3600 J;  1 kWh = 3.6 MJ.", "1 Wh = 3600 J;  1 kWh = 3,6 MJ.")),
        Formula(("LED / series resistor", "Rezistor serie pentru LED"), "R = (Vs − Vf) / I", "R",
                lambda Vs, Vf, I: (Vs - Vf) / I,
                [_V("R", "R", "Series resistor", "Rezistor serie", "Ω", ""),
                 _V("Vs", "Vs", "Supply voltage", "Tensiune de alimentare", "V", "9"),
                 _V("Vf", "Vf", "LED forward voltage", "Tensiune directă LED", "V", "2", signed=True),
                 _V("I", "I", "LED current", "Curent LED", "A", "20m")]),
    ]


def capacitor_formulas():
    return [
        Formula(("Charge  Q = C·V", "Sarcină  Q = C·U"), "Q = C · V", "Q", lambda C, V: C * V,
                [_V("Q", "Q", "Charge", "Sarcină", "C", ""), _V("C", "C", "Capacitance", "Capacitate", "F", "100u"),
                 _V("V", "V", "Voltage", "Tensiune", "V", "12")]),
        Formula(("Capacitive reactance", "Reactanță capacitivă"), "Xc = 1 / (2 · π · f · C)", "Xc",
                lambda f, C: 1 / (2 * PI * f * C),
                [_V("Xc", "Xc", "Reactance", "Reactanță", "Ω", ""), _V("f", "f", "Frequency", "Frecvență", "Hz", "1k"),
                 _V("C", "C", "Capacitance", "Capacitate", "F", "100n")]),
        Formula(("Time constant τ = R·C", "Constanta de timp τ = R·C"), "τ = R · C", "tau", lambda R, C: R * C,
                [_V("tau", "τ", "Time constant", "Constanta de timp", "s", ""),
                 _V("R", "R", "Resistance", "Rezistență", "Ω", "10k"), _V("C", "C", "Capacitance", "Capacitate", "F", "100u")],
                note=("After 1τ the capacitor reaches 63.2 %, after 5τ ≈ 99.3 % (considered fully charged).",
                      "După 1τ condensatorul ajunge la 63,2 %, după 5τ ≈ 99,3 % (considerat încărcat complet).")),
        Formula(("Charging voltage at time t", "Tensiunea la încărcare la momentul t"),
                "v(t) = V · (1 − e^(−t / RC))", "v",
                lambda V, time, R, C: V * (1 - math.exp(-time / (R * C))),
                [_V("v", "v(t)", "Capacitor voltage", "Tensiunea pe condensator", "V", ""),
                 _V("V", "V", "Source voltage", "Tensiunea sursei", "V", "5"),
                 _V("time", "t", "Time", "Timp", "s", "0.5"),
                 _V("R", "R", "Resistance", "Rezistență", "Ω", "10k"), _V("C", "C", "Capacitance", "Capacitate", "F", "47u")],
                note=("Choose t as the unknown to find how long it takes to reach a voltage.",
                      "Alege t ca necunoscută ca să afli cât durează până se atinge o tensiune.")),
        Formula(("Discharging voltage at time t", "Tensiunea la descărcare la momentul t"),
                "v(t) = V₀ · e^(−t / RC)", "v",
                lambda V0, time, R, C: V0 * math.exp(-time / (R * C)),
                [_V("v", "v(t)", "Capacitor voltage", "Tensiunea pe condensator", "V", ""),
                 _V("V0", "V₀", "Initial voltage", "Tensiunea inițială", "V", "12"),
                 _V("time", "t", "Time", "Timp", "s", "1"),
                 _V("R", "R", "Resistance", "Rezistență", "Ω", "10k"), _V("C", "C", "Capacitance", "Capacitate", "F", "100u")]),
        Formula(("Charging current at time t", "Curentul de încărcare la momentul t"),
                "i(t) = (V / R) · e^(−t / RC)", "i",
                lambda V, time, R, C: (V / R) * math.exp(-time / (R * C)),
                [_V("i", "i(t)", "Current", "Curent", "A", ""), _V("V", "V", "Source voltage", "Tensiunea sursei", "V", "5"),
                 _V("time", "t", "Time", "Timp", "s", "0.05"),
                 _V("R", "R", "Resistance", "Rezistență", "Ω", "1k"), _V("C", "C", "Capacitance", "Capacitate", "F", "100u")]),
        Formula(("Stored energy", "Energie înmagazinată"), "E = ½ · C · V²", "E", lambda C, V: 0.5 * C * V * V,
                [_V("E", "E", "Energy", "Energie", "J", ""), _V("C", "C", "Capacitance", "Capacitate", "F", "1000u"),
                 _V("V", "V", "Voltage", "Tensiune", "V", "25")]),
        Formula(("Parallel-plate capacitor", "Condensator plan"), "C = ε₀ · εr · A / d", "C",
                lambda er, A, d: EPS0 * er * A / d,
                [_V("C", "C", "Capacitance", "Capacitate", "F", ""),
                 _V("er", "εr", "Relative permittivity", "Permitivitate relativă", "", "6", presets=EPSR_PRESETS),
                 _V("A", "A", "Plate area", "Aria armăturii", "m²", "1e-4"),
                 _V("d", "d", "Dielectric thickness", "Grosimea dielectricului", "m", "0.1e-3")],
                note=("ε₀ = 8.854 pF/m.  1 cm² = 1e-4 m²,  0.1 mm = 1e-4 m.",
                      "ε₀ = 8,854 pF/m.  1 cm² = 1e-4 m²,  0,1 mm = 1e-4 m.")),
        Formula(("Current through a capacitor", "Curentul printr-un condensator"), "i = C · ΔV / Δt", "i",
                lambda C, dV, dt: C * dV / dt,
                [_V("i", "i", "Current", "Curent", "A", ""), _V("C", "C", "Capacitance", "Capacitate", "F", "10u"),
                 _V("dV", "ΔV", "Voltage change", "Variația tensiunii", "V", "5", signed=True),
                 _V("dt", "Δt", "Time interval", "Interval de timp", "s", "1m")]),
        Formula(("RC cut-off frequency", "Frecvența de tăiere RC"), "fc = 1 / (2 · π · R · C)", "fc",
                lambda R, C: 1 / (2 * PI * R * C),
                [_V("fc", "fc", "Cut-off frequency", "Frecvența de tăiere", "Hz", ""),
                 _V("R", "R", "Resistance", "Rezistență", "Ω", "1k"), _V("C", "C", "Capacitance", "Capacitate", "F", "100n")]),
        Formula(("Two capacitors in series", "Două condensatoare în serie"), "Cs = C1 · C2 / (C1 + C2)", "Cs",
                lambda C1, C2: C1 * C2 / (C1 + C2),
                [_V("Cs", "Cs", "Equivalent", "Echivalent", "F", ""),
                 _V("C1", "C1", "Capacitor 1", "Condensator 1", "F", "100n"), _V("C2", "C2", "Capacitor 2", "Condensator 2", "F", "220n")]),
        Formula(("Two capacitors in parallel", "Două condensatoare în paralel"), "Cp = C1 + C2", "Cp",
                lambda C1, C2: C1 + C2,
                [_V("Cp", "Cp", "Equivalent", "Echivalent", "F", ""),
                 _V("C1", "C1", "Capacitor 1", "Condensator 1", "F", "100n"), _V("C2", "C2", "Capacitor 2", "Condensator 2", "F", "220n")]),
        Formula(("Filter capacitor for a ripple target", "Condensator de filtraj pentru un riplu dorit"),
                "Vr = I / (k · f · C)", "Vr", lambda I, k, f, C: I / (k * f * C),
                [_V("Vr", "Vr", "Ripple (peak-to-peak)", "Riplu (vârf-vârf)", "V", ""),
                 _V("I", "I", "Load current", "Curentul de sarcină", "A", "0.5"),
                 _V("k", "k", "1 = half-wave, 2 = full-wave", "1 = monoalternanță, 2 = dublă alternanță", "", "2"),
                 _V("f", "f", "Mains frequency", "Frecvența rețelei", "Hz", "50"),
                 _V("C", "C", "Capacitance", "Capacitate", "F", "2200u")]),
    ]


def inductor_formulas():
    return [
        Formula(("Inductive reactance", "Reactanță inductivă"), "XL = 2 · π · f · L", "XL",
                lambda f, Lh: 2 * PI * f * Lh,
                [_V("XL", "XL", "Reactance", "Reactanță", "Ω", ""), _V("f", "f", "Frequency", "Frecvență", "Hz", "1k"),
                 _V("Lh", "L", "Inductance", "Inductanță", "H", "10m")]),
        Formula(("Time constant τ = L/R", "Constanta de timp τ = L/R"), "τ = L / R", "tau", lambda Lh, R: Lh / R,
                [_V("tau", "τ", "Time constant", "Constanta de timp", "s", ""),
                 _V("Lh", "L", "Inductance", "Inductanță", "H", "100m"), _V("R", "R", "Resistance", "Rezistență", "Ω", "50")]),
        Formula(("Current rise at time t", "Creșterea curentului la momentul t"), "i(t) = (V / R) · (1 − e^(−t·R/L))", "i",
                lambda V, R, time, Lh: (V / R) * (1 - math.exp(-time * R / Lh)),
                [_V("i", "i(t)", "Current", "Curent", "A", ""), _V("V", "V", "Source voltage", "Tensiunea sursei", "V", "12"),
                 _V("R", "R", "Resistance", "Rezistență", "Ω", "100"), _V("time", "t", "Time", "Timp", "s", "1m"),
                 _V("Lh", "L", "Inductance", "Inductanță", "H", "100m")]),
        Formula(("Stored energy", "Energie înmagazinată"), "E = ½ · L · I²", "E", lambda Lh, I: 0.5 * Lh * I * I,
                [_V("E", "E", "Energy", "Energie", "J", ""), _V("Lh", "L", "Inductance", "Inductanță", "H", "10m"),
                 _V("I", "I", "Current", "Curent", "A", "2")]),
        Formula(("Self-induced voltage", "Tensiunea autoindusă"), "V = L · ΔI / Δt", "V",
                lambda Lh, dI, dt: Lh * dI / dt,
                [_V("V", "V", "Voltage", "Tensiune", "V", ""), _V("Lh", "L", "Inductance", "Inductanță", "H", "10m"),
                 _V("dI", "ΔI", "Current change", "Variația curentului", "A", "1", signed=True),
                 _V("dt", "Δt", "Time interval", "Interval de timp", "s", "1m")]),
        Formula(("Solenoid / coil inductance", "Inductanța unei bobine (solenoid)"), "L = μ₀ · μr · N² · A / ℓ", "Lh",
                lambda mur, N, A, l: MU0 * mur * N * N * A / l,
                [_V("Lh", "L", "Inductance", "Inductanță", "H", ""),
                 _V("mur", "μr", "Relative permeability", "Permeabilitate relativă", "", "1", presets=MUR_PRESETS),
                 _V("N", "N", "Number of turns", "Număr de spire", "", "200"),
                 _V("A", "A", "Core cross-section", "Secțiunea miezului", "m²", "1e-4"),
                 _V("l", "ℓ", "Coil length", "Lungimea bobinei", "m", "0.05")],
                note=("μ₀ = 4π·10⁻⁷ H/m. Choose N as the unknown to find how many turns you need.",
                      "μ₀ = 4π·10⁻⁷ H/m. Alege N ca necunoscută ca să afli câte spire îți trebuie.")),
        Formula(("LC resonant frequency", "Frecvența de rezonanță LC"), "f₀ = 1 / (2 · π · √(L · C))", "f0",
                lambda Lh, C: 1 / (2 * PI * math.sqrt(Lh * C)),
                [_V("f0", "f₀", "Resonant frequency", "Frecvența de rezonanță", "Hz", ""),
                 _V("Lh", "L", "Inductance", "Inductanță", "H", "10m"), _V("C", "C", "Capacitance", "Capacitate", "F", "100n")]),
        Formula(("RL cut-off frequency", "Frecvența de tăiere RL"), "fc = R / (2 · π · L)", "fc",
                lambda R, Lh: R / (2 * PI * Lh),
                [_V("fc", "fc", "Cut-off frequency", "Frecvența de tăiere", "Hz", ""),
                 _V("R", "R", "Resistance", "Rezistență", "Ω", "100"), _V("Lh", "L", "Inductance", "Inductanță", "H", "10m")]),
        Formula(("Quality factor of a coil", "Factorul de calitate al bobinei"), "Q = 2 · π · f · L / R", "Q",
                lambda f, Lh, R: 2 * PI * f * Lh / R,
                [_V("Q", "Q", "Quality factor", "Factor de calitate", "", ""), _V("f", "f", "Frequency", "Frecvență", "Hz", "100k"),
                 _V("Lh", "L", "Inductance", "Inductanță", "H", "100u"), _V("R", "R", "Series resistance", "Rezistență serie", "Ω", "2")]),
        Formula(("Mutual inductance", "Inductanță mutuală"), "M = k · √(L1 · L2)", "M",
                lambda k, L1, L2: k * math.sqrt(L1 * L2),
                [_V("M", "M", "Mutual inductance", "Inductanță mutuală", "H", ""),
                 _V("k", "k", "Coupling coefficient (0…1)", "Coeficient de cuplaj (0…1)", "", "0.9"),
                 _V("L1", "L1", "Inductance 1", "Inductanța 1", "H", "10m"), _V("L2", "L2", "Inductance 2", "Inductanța 2", "H", "40m")]),
        Formula(("Transformer voltage", "Tensiunea transformatorului"), "Vs = Vp · Ns / Np", "Vs",
                lambda Vp, Ns, Np: Vp * Ns / Np,
                [_V("Vs", "Vs", "Secondary voltage", "Tensiunea secundară", "V", ""),
                 _V("Vp", "Vp", "Primary voltage", "Tensiunea primară", "V", "230"),
                 _V("Ns", "Ns", "Secondary turns", "Spire secundar", "", "60"),
                 _V("Np", "Np", "Primary turns", "Spire primar", "", "1150")]),
        Formula(("Transformer current", "Curentul transformatorului"), "Is = Ip · Np / Ns", "Is",
                lambda Ip, Np, Ns: Ip * Np / Ns,
                [_V("Is", "Is", "Secondary current", "Curentul secundar", "A", ""),
                 _V("Ip", "Ip", "Primary current", "Curentul primar", "A", "0.2"),
                 _V("Np", "Np", "Primary turns", "Spire primar", "", "1150"),
                 _V("Ns", "Ns", "Secondary turns", "Spire secundar", "", "60")]),
        Formula(("Two inductors in series", "Două bobine în serie"), "Ls = L1 + L2", "Ls", lambda L1, L2: L1 + L2,
                [_V("Ls", "Ls", "Equivalent", "Echivalent", "H", ""),
                 _V("L1", "L1", "Inductor 1", "Bobina 1", "H", "10m"), _V("L2", "L2", "Inductor 2", "Bobina 2", "H", "22m")]),
        Formula(("Two inductors in parallel", "Două bobine în paralel"), "Lp = L1 · L2 / (L1 + L2)", "Lp",
                lambda L1, L2: L1 * L2 / (L1 + L2),
                [_V("Lp", "Lp", "Equivalent", "Echivalent", "H", ""),
                 _V("L1", "L1", "Inductor 1", "Bobina 1", "H", "10m"), _V("L2", "L2", "Inductor 2", "Bobina 2", "H", "22m")]),
    ]
