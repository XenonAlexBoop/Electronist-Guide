"""
tabs/resistive_divider.py - Resistors > Voltage Divider sub-tab.

A clear, solve-for-anything resistive divider calculator:
  * full schematic with every part named (R1, R2, R3, R4, RL), node
    voltages and branch currents written directly on the drawing,
  * one row per quantity with a "solve for" selector - any of Vin, R1, R2,
    R3, R4, RL or Vout can be the unknown,
  * optional 2nd stage (R3/R4) and optional load resistor RL,
  * a per-resistor table (voltage, current, power) and
  * an E-series designer that finds the best standard R1/R2 pair.
"""
import math
import tkinter as tk
from tkinter import ttk

from widgets import parse_value, format_value, ScrollableFrame, FONT_H2, FONT_BODY, FONT_MONO, debounce, cap_width
import symbols as sym
from solver import Formula, Var, solve_for
from i18n import t

ACCENT_C = "#8854d0"
I_COLOR = "#c62828"

E_SERIES = {
    "E6": [1.0, 1.5, 2.2, 3.3, 4.7, 6.8],
    "E12": [1.0, 1.2, 1.5, 1.8, 2.2, 2.7, 3.3, 3.9, 4.7, 5.6, 6.8, 8.2],
    "E24": [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1,
            5.6, 6.2, 6.8, 7.5, 8.2, 9.1],
    "E96": [1.00, 1.02, 1.05, 1.07, 1.10, 1.13, 1.15, 1.18, 1.21, 1.24, 1.27, 1.30, 1.33, 1.37, 1.40, 1.43,
            1.47, 1.50, 1.54, 1.58, 1.62, 1.65, 1.69, 1.74, 1.78, 1.82, 1.87, 1.91, 1.96, 2.00, 2.05, 2.10,
            2.15, 2.21, 2.26, 2.32, 2.37, 2.43, 2.49, 2.55, 2.61, 2.67, 2.74, 2.80, 2.87, 2.94, 3.01, 3.09,
            3.16, 3.24, 3.32, 3.40, 3.48, 3.57, 3.65, 3.74, 3.83, 3.92, 4.02, 4.12, 4.22, 4.32, 4.42, 4.53,
            4.64, 4.75, 4.87, 4.99, 5.11, 5.23, 5.36, 5.49, 5.62, 5.76, 5.90, 6.04, 6.19, 6.34, 6.49, 6.65,
            6.81, 6.98, 7.15, 7.32, 7.50, 7.68, 7.87, 8.06, 8.25, 8.45, 8.66, 8.87, 9.09, 9.31, 9.53, 9.76],
}


def _par(a, b):
    if a == float("inf"):
        return b
    if b == float("inf"):
        return a
    return a * b / (a + b)


def solve_network(Vin, R1, R2, R3=None, R4=None, RL=None):
    """Node voltages and branch currents of the (1- or 2-stage, optionally
    loaded) divider.  Returns a dict."""
    inf = float("inf")
    rl = RL if RL else inf
    if R3 is not None:
        zb = _par(R4, rl)
        za = _par(R2, R3 + zb)
        va = Vin * za / (R1 + za)
        vb = va * zb / (R3 + zb)
        vout = vb
        i3 = (va - vb) / R3
        i4 = vb / R4
    else:
        za = _par(R2, rl)
        va = Vin * za / (R1 + za)
        vb = None
        vout = va
        i3 = i4 = None
    i1 = (Vin - va) / R1
    i2 = va / R2
    il = vout / RL if RL else None
    return {"va": va, "vb": vb, "vout": vout, "i1": i1, "i2": i2, "i3": i3, "i4": i4, "il": il,
            "rin": R1 + za, "pin": Vin * i1}


class ResistiveDividerPanel(ttk.Frame):
    FIELDS = ["Vin", "R1", "R2", "R3", "R4", "RL", "Vout"]

    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        scroll = ScrollableFrame(self, style="Card.TFrame")
        scroll.grid(row=0, column=0, sticky="nsew")
        body = scroll.body
        body.columnconfigure(0, weight=1)
        self._ready = False

        ttk.Label(body, text=t("vd.intro"), font=FONT_BODY, style="CardBody.TLabel", wraplength=620,
                  justify="left").grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))

        opts = ttk.Frame(body, style="Card.TFrame")
        opts.grid(row=1, column=0, sticky="w", padx=16, pady=(2, 4))
        self.stage2 = tk.BooleanVar(value=False)
        self.loaded = tk.BooleanVar(value=False)
        ttk.Checkbutton(opts, text=t("vd.opt_stage2"), variable=self.stage2,
                        command=self._on_options).pack(side="left", padx=(0, 16))
        ttk.Checkbutton(opts, text=t("vd.opt_load"), variable=self.loaded,
                        command=self._on_options).pack(side="left")

        self.canvas = tk.Canvas(body, height=270, bg=sym.CANVAS_BG, highlightthickness=0)
        self.canvas.grid(row=2, column=0, sticky="ew", padx=16, pady=6)
        self._cw = 0
        self.canvas.bind("<Configure>", debounce(self.canvas, self._on_canvas, 100))

        # ---- inputs ----
        ttk.Label(body, text=t("vd.inputs_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=3, column=0, sticky="w", padx=16, pady=(6, 0))
        ttk.Label(body, text=t("vd.inputs_hint"), font=("Segoe UI", 9), style="CardBody.TLabel",
                  wraplength=620, justify="left").grid(row=4, column=0, sticky="w", padx=16)
        form = ttk.Frame(body, style="Card.TFrame")
        form.grid(row=5, column=0, sticky="w", padx=16, pady=6)
        self.form = form
        defaults = {"Vin": "12", "R1": "10k", "R2": "4.7k", "R3": "10k", "R4": "10k", "RL": "100k", "Vout": ""}
        units = {"Vin": "V", "Vout": "V"}
        self.solve_for = tk.StringVar(value="Vout")
        self.vars, self.entries, self.rows = {}, {}, {}
        hdr = ("Segoe UI", 8, "bold")
        for c, key in enumerate(("solver.col_solve", "solver.col_symbol", "solver.col_quantity", "solver.col_value")):
            ttk.Label(form, text=t(key), font=hdr, style="CardBody.TLabel").grid(row=0, column=c, sticky="w", padx=(0, 8))
        for r, key in enumerate(self.FIELDS, start=1):
            rb = ttk.Radiobutton(form, variable=self.solve_for, value=key, command=self._on_solve_change)
            lb = ttk.Label(form, text=key, font=("Consolas", 11, "bold"), foreground=ACCENT_C,
                           style="CardFormula.TLabel")
            ds = ttk.Label(form, text=t(f"vd.field.{key}"), font=FONT_BODY, style="CardBody.TLabel")
            var = tk.StringVar(value=defaults[key])
            en = ttk.Entry(form, textvariable=var, width=12)
            en.bind("<KeyRelease>", lambda e: self._compute())
            un = ttk.Label(form, text=units.get(key, "Ω"), font=FONT_BODY, style="CardBody.TLabel")
            widgets = (rb, lb, ds, en, un)
            for c, w in enumerate(widgets):
                w.grid(row=r, column=c, sticky="w", padx=(0, 8), pady=1)
            self.vars[key], self.entries[key], self.rows[key] = var, en, widgets

        self.summary = tk.StringVar()
        ttk.Label(body, textvariable=self.summary, font=FONT_MONO, foreground=ACCENT_C, style="CardFormula.TLabel",
                  justify="left", wraplength=640).grid(row=6, column=0, sticky="w", padx=16, pady=(6, 4))

        # ---- per-resistor table ----
        cols = ("el", "r", "v", "i", "p")
        self.table = ttk.Treeview(body, columns=cols, show="headings", height=6)
        for col, key, wd in zip(cols, ("vd.col_element", "vd.col_resistance", "vd.col_voltage",
                                       "vd.col_current", "vd.col_power"), (90, 110, 110, 110, 110)):
            self.table.heading(col, text=t(key))
            self.table.column(col, width=wd, anchor="center")
        self.table.grid(row=7, column=0, sticky="ew", padx=16, pady=(4, 10))

        ttk.Label(body, text=t("vd.formulas"), font=("Consolas", 10), style="CardBody.TLabel",
                  justify="left", wraplength=640).grid(row=8, column=0, sticky="w", padx=16, pady=(0, 8))

        # ---- E-series designer ----
        ttk.Separator(body, orient="horizontal").grid(row=9, column=0, sticky="ew", padx=16, pady=8)
        ttk.Label(body, text=t("vd.design_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=10, column=0, sticky="w", padx=16)
        ttk.Label(body, text=t("vd.design_intro"), font=("Segoe UI", 9), style="CardBody.TLabel",
                  wraplength=620, justify="left").grid(row=11, column=0, sticky="w", padx=16)
        dz = ttk.Frame(body, style="Card.TFrame")
        dz.grid(row=12, column=0, sticky="w", padx=16, pady=6)
        self.d_vin = tk.StringVar(value="12")
        self.d_vout = tk.StringVar(value="3.3")
        self.d_i = tk.StringVar(value="1m")
        self.d_series = tk.StringVar(value="E24")
        for c, (lbl, var, wd) in enumerate(((t("vd.field.Vin"), self.d_vin, 8), (t("vd.design_target"), self.d_vout, 8),
                                            (t("vd.design_current"), self.d_i, 8))):
            ttk.Label(dz, text=lbl, font=FONT_BODY, style="CardBody.TLabel").grid(row=0, column=c * 2, sticky="w", padx=(0, 4))
            ttk.Entry(dz, textvariable=var, width=wd).grid(row=0, column=c * 2 + 1, sticky="w", padx=(0, 12))
        ttk.Label(dz, text=t("vd.design_series"), font=FONT_BODY, style="CardBody.TLabel").grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(dz, textvariable=self.d_series, values=list(E_SERIES), state="readonly", width=6)\
            .grid(row=1, column=1, sticky="w", pady=4)
        ttk.Button(dz, text=t("vd.design_find"), command=self._design).grid(row=1, column=2, columnspan=2, sticky="w", pady=4)
        self.d_table = ttk.Treeview(body, columns=("r1", "r2", "vout", "err", "i"), show="headings", height=5)
        for col, key in zip(("r1", "r2", "vout", "err", "i"), ("vd.d_r1", "vd.d_r2", "vd.d_vout", "vd.d_err", "vd.d_i")):
            self.d_table.heading(col, text=t(key))
            self.d_table.column(col, width=100, anchor="center")
        self.d_table.grid(row=13, column=0, sticky="ew", padx=16)
        ttk.Button(body, text=t("vd.design_apply"), command=self._apply_design)\
            .grid(row=14, column=0, sticky="w", padx=16, pady=(6, 16))
        self._designs = []

        self._ready = True
        self._on_options()

    # ------------------------------------------------------------------
    def _active_fields(self):
        f = ["Vin", "R1", "R2"]
        if self.stage2.get():
            f += ["R3", "R4"]
        if self.loaded.get():
            f.append("RL")
        return f + ["Vout"]

    def _on_options(self):
        active = self._active_fields()
        for key, widgets in self.rows.items():
            for w in widgets:
                (w.grid() if key in active else w.grid_remove())
        if self.solve_for.get() not in active:
            self.solve_for.set("Vout")
        self._on_solve_change()

    def _on_solve_change(self):
        unknown = self.solve_for.get()
        for k, e in self.entries.items():
            e.configure(state="readonly" if k == unknown else "normal")
        self._compute()

    def _on_canvas(self, event):
        if abs(event.width - self._cw) > 8:
            self._cw = event.width
            self._compute()

    # ------------------------------------------------------------------
    def _formula(self):
        stage2, loaded = self.stage2.get(), self.loaded.get()

        def fn(Vin, R1, R2, R3=None, R4=None, RL=None):
            return solve_network(Vin, R1, R2, R3 if stage2 else None, R4 if stage2 else None,
                                 RL if loaded else None)["vout"]
        vars_ = [Var(k, k, (k, k), "", "") for k in self._active_fields()]
        return Formula(("", ""), "", "Vout", fn, vars_)

    def _values(self):
        unknown = self.solve_for.get()
        vals = {}
        for k in self._active_fields():
            if k == unknown:
                continue
            vals[k] = parse_value(self.vars[k].get())
            if vals[k] <= 0 and k != "Vin":
                raise ValueError
        return unknown, vals

    def _compute(self):
        if not self._ready:
            return
        try:
            unknown, vals = self._values()
        except Exception:
            self.summary.set(t("common.enter_valid_values"))
            return
        sols = solve_for(self._formula(), unknown, vals)
        if not sols:
            self.summary.set(t("vd.no_solution").format(x=unknown))
            self.vars[unknown].set("")
            self._draw(None, None)
            return
        vals[unknown] = sols[0]
        self.vars[unknown].set(f"{sols[0]:.5g}")
        stage2, loaded = self.stage2.get(), self.loaded.get()
        res = solve_network(vals["Vin"], vals["R1"], vals["R2"], vals.get("R3") if stage2 else None,
                            vals.get("R4") if stage2 else None, vals.get("RL") if loaded else None)
        self._draw(vals, res)
        self._fill_table(vals, res)

        unit = "V" if unknown in ("Vin", "Vout") else "Ω"
        lines = [f"{t('vd.solved')} {unknown} = {format_value(float(f'{sols[0]:.5g}'), unit)}"]
        lines.append(f"Vout / Vin = {res['vout'] / vals['Vin']:.4f}     "
                     f"({20 * math.log10(max(res['vout'] / vals['Vin'], 1e-12)):.2f} dB)")
        rin, pin = float(f"{res['rin']:.4g}"), float(f"{res['pin']:.4g}")
        lines.append(f"{t('vd.rin')} = {format_value(rin, 'Ω')}")
        lines.append(f"{t('vd.pin')} = {format_value(pin, 'W')}")
        if stage2:
            lines.append(f"V_A = {format_value(res['va'], 'V')}")
        if loaded:
            unl = solve_network(vals["Vin"], vals["R1"], vals["R2"], vals.get("R3") if stage2 else None,
                                vals.get("R4") if stage2 else None, None)["vout"]
            drop = (unl - res["vout"]) / unl * 100 if unl else 0
            lines.append(t("vd.load_effect").format(unl=format_value(unl, "V"), ld=format_value(res["vout"], "V"),
                                                    pct=f"{drop:.2f}"))
        self.summary.set("\n".join(lines))

    def _fill_table(self, vals, res):
        for r in self.table.get_children():
            self.table.delete(r)
        rows = [("R1", vals["R1"], vals["Vin"] - res["va"], res["i1"]),
                ("R2", vals["R2"], res["va"], res["i2"])]
        if self.stage2.get():
            rows += [("R3", vals["R3"], res["va"] - res["vb"], res["i3"]),
                     ("R4", vals["R4"], res["vb"], res["i4"])]
        if self.loaded.get():
            rows.append(("RL", vals["RL"], res["vout"], res["il"]))
        for name, r, v, i in rows:
            self.table.insert("", "end", values=(name, format_value(r, "Ω"), format_value(v, "V"),
                                                 format_value(i, "A"), format_value(v * i, "W")))
        self.table.insert("", "end", values=(t("vd.source"), format_value(res["rin"], "Ω"),
                                             format_value(vals["Vin"], "V"), format_value(res["i1"], "A"),
                                             format_value(res["pin"], "W")))

    # ------------------------------------------------------------------
    def _draw(self, vals, res):
        c = self.canvas
        c.delete("all")
        w = cap_width(c, max(self._cw or 520, 420), 980)
        stage2, loaded = self.stage2.get(), self.loaded.get()
        top, bot = 70, 225
        src_x = 48
        cols = 2 + (2 if stage2 else 0) + (1 if loaded else 0)
        right = w - 50
        xa = src_x + (right - src_x) * (0.52 if not stage2 else 0.36)
        xb = src_x + (right - src_x) * 0.74 if stage2 else None
        x_out = right
        x_rl = right - 36 if loaded else None

        def fv(x, u):
            return format_value(float(f"{x:.4g}"), u) if x is not None else "?"

        # source
        sym.wire(c, src_x, top, src_x, (top + bot) / 2 - 16)
        sym.wire(c, src_x, (top + bot) / 2 + 16, src_x, bot)
        sym.dc_source(c, src_x, (top + bot) / 2)
        c.create_text(src_x + 22, (top + bot) / 2, anchor="w", font=("Segoe UI", 9, "bold"),
                      fill=sym.LABEL_COLOR, text=f"Vin\n{fv(vals['Vin'], 'V') if vals else ''}")
        # R1
        r1_x0 = src_x + 30
        sym.wire(c, src_x, top, r1_x0, top)
        sym.resistor(c, r1_x0, top, xa, top, label="R1",
                     value=fv(vals["R1"], "Ω") if vals else None)
        sym.node(c, xa, top)
        # R2
        sym.resistor(c, xa, top, xa, bot, label="R2", value=fv(vals["R2"], "Ω") if vals else None,
                     label_side=-1, label_offset=16)
        sym.node(c, xa, bot)
        last_x = xa
        if stage2:
            sym.resistor(c, xa, top, xb, top, label="R3", value=fv(vals["R3"], "Ω") if vals else None)
            sym.node(c, xb, top)
            sym.resistor(c, xb, top, xb, bot, label="R4", value=fv(vals["R4"], "Ω") if vals else None,
                         label_side=-1, label_offset=16)
            sym.node(c, xb, bot)
            last_x = xb
        # output wire (+ load)
        sym.wire(c, last_x, top, x_out, top)
        sym.terminal(c, x_out, top, label="Vout", anchor="s", dy=-10)
        bottom_end = last_x
        if loaded:
            sym.node(c, x_rl, top)
            sym.resistor(c, x_rl, top, x_rl, bot, label="RL", value=fv(vals["RL"], "Ω") if vals else None,
                         label_side=-1, label_offset=16)
            bottom_end = x_rl
        # ground rail
        sym.wire(c, src_x, bot, bottom_end, bot)
        sym.ground(c, src_x, bot + 4)
        c.create_text(bottom_end + 6, bot, anchor="w", text="0 V", font=("Segoe UI", 8), fill="#777")

        if not vals or not res:
            return
        # node voltages
        c.create_text(xa + 6, top + 8, anchor="nw", fill=ACCENT_C, font=("Segoe UI", 9, "bold"),
                      text=("V_A = " if stage2 else "Vout = ") + fv(res["va"], "V"))
        if stage2:
            c.create_text(xb + 6, top + 8, anchor="nw", fill=ACCENT_C, font=("Segoe UI", 9, "bold"),
                          text="Vout = " + fv(res["vb"], "V"))
        # currents
        sym.current_arrow(c, src_x + 4, top - 12, src_x + 26, top - 12, text=f"I1 {fv(res['i1'], 'A')}",
                          color=I_COLOR, text_side=-1)
        sym.current_arrow(c, xa - 12, bot - 44, xa - 12, bot - 16, text=f"I2 {fv(res['i2'], 'A')}",
                          color=I_COLOR, text_side=-1)
        if stage2:
            sym.current_arrow(c, xb - 12, bot - 44, xb - 12, bot - 16, text=f"I4 {fv(res['i4'], 'A')}",
                              color=I_COLOR, text_side=-1)
            c.create_text((xa + xb) / 2, top + 26, text=f"I3 {fv(res['i3'], 'A')}", fill=I_COLOR,
                          font=("Segoe UI", 8, "bold"))
        if loaded:
            sym.current_arrow(c, x_rl + 12, bot - 44, x_rl + 12, bot - 16, text=f"IL {fv(res['il'], 'A')}",
                              color=I_COLOR, text_side=1)

    # ------------------------------------------------------------------
    def _design(self):
        for r in self.d_table.get_children():
            self.d_table.delete(r)
        try:
            vin = parse_value(self.d_vin.get())
            vout = parse_value(self.d_vout.get())
            itarget = parse_value(self.d_i.get()) if self.d_i.get().strip() else None
        except Exception:
            return
        if not (0 < vout < vin):
            self.d_table.insert("", "end", values=(t("vd.design_bad"), "", "", "", ""))
            return
        series = E_SERIES[self.d_series.get()]
        values = [m * 10 ** d for d in range(0, 7) for m in series]
        cands = []
        for r1 in values:
            ideal_r2 = r1 * vout / (vin - vout)
            # nearest standard values around the ideal R2
            for r2 in values:
                if r2 < ideal_r2 / 1.3 or r2 > ideal_r2 * 1.3:
                    continue
                v = vin * r2 / (r1 + r2)
                err = (v - vout) / vout * 100
                i = vin / (r1 + r2)
                cur_pen = abs(math.log10(i / itarget)) if itarget else 0
                cands.append((abs(err) + 0.5 * cur_pen, r1, r2, v, err, i))
        cands.sort()
        self._designs = cands[:8]
        for _, r1, r2, v, err, i in self._designs:
            self.d_table.insert("", "end", values=(format_value(r1, "Ω"), format_value(r2, "Ω"),
                                                   format_value(float(f"{v:.4g}"), "V"), f"{err:+.2f} %",
                                                   format_value(float(f"{i:.3g}"), "A")))

    def _apply_design(self):
        if not self._designs:
            return
        sel = self.d_table.selection()
        idx = self.d_table.index(sel[0]) if sel else 0
        _, r1, r2, _, _, _ = self._designs[idx]
        self.stage2.set(False)
        self.loaded.set(False)
        self.vars["Vin"].set(self.d_vin.get())
        self.vars["R1"].set(format_value(r1, "").replace(" ", ""))
        self.vars["R2"].set(format_value(r2, "").replace(" ", ""))
        self.solve_for.set("Vout")
        self._on_options()
