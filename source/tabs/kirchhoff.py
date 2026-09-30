"""
tabs/kirchhoff.py - AC/DC Basics > Kirchhoff's Laws sub-tab.
Two small interactive demonstrations:
  - KVL: a series loop of resistors driven by one source; shows the loop
    current and verifies the sum of the voltage drops equals the source.
  - KCL: a node with several current branches (each independently marked
    "in" or "out"); one branch is solved so the node balances (sum in =
    sum out).
"""
import tkinter as tk
from tkinter import ttk

from widgets import FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ScrollableFrame, TheoryPanel
from data import get_theory
from i18n import t

ACCENT_C = "#334155"
MAX_RESISTORS = 5
MIN_RESISTORS = 2
N_BRANCHES = 4


class KirchhoffTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        left_wrap = ttk.Frame(self, style="Card.TFrame")
        left_wrap.grid(row=0, column=0, sticky="nsew", pady=0)
        left_wrap.columnconfigure(0, weight=1)
        left_wrap.rowconfigure(0, weight=1)
        left_scroll = ScrollableFrame(left_wrap, style="Card.TFrame")
        left_scroll.grid(row=0, column=0, sticky="nsew")

        # v6.2: with the theory in its own Learn tab, KVL and KCL sit side by side
        body = left_scroll.body
        body.columnconfigure(0, weight=1, uniform="k")
        body.columnconfigure(1, weight=1, uniform="k")
        kvl = ttk.Frame(body, style="Card.TFrame")
        kvl.grid(row=0, column=0, sticky="nsew")
        kcl = ttk.Frame(body, style="Card.TFrame")
        kcl.grid(row=0, column=1, sticky="nsew")
        kcl.columnconfigure(0, weight=1)
        self._build_kvl(kvl)
        self._build_kcl(kcl)

    # ------------------------------------------------------------------
    # KVL - series loop
    # ------------------------------------------------------------------
    def _build_kvl(self, parent):
        pad = {"padx": 16, "pady": 6}
        parent.columnconfigure(0, weight=1)

        header = tk.Frame(parent, bg=ACCENT_C, height=6)
        header.grid(row=0, column=0, sticky="ew")

        ttk.Label(parent, text=t("kirch.kvl_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=1, column=0, sticky="w", **pad)
        ttk.Label(parent, text=t("kirch.kvl_intro"), font=FONT_BODY, wraplength=420,
                  justify="left", style="CardBody.TLabel").grid(row=2, column=0, sticky="w", padx=16)

        ttk.Label(parent, text=t("kirch.source_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=3, column=0, sticky="w", padx=16, pady=(10, 0))
        self.kvl_source_var = tk.StringVar(value="12")
        se = ttk.Entry(parent, textvariable=self.kvl_source_var, width=12)
        se.grid(row=4, column=0, sticky="w", padx=16)
        se.bind("<KeyRelease>", lambda e: self._kvl_solve())

        self.kvl_resistor_frame = ttk.Frame(parent, style="Card.TFrame")
        self.kvl_resistor_frame.grid(row=5, column=0, sticky="ew", padx=16, pady=(8, 4))
        self.kvl_r_vars = []
        self._kvl_init_resistors()

        btn_row = ttk.Frame(parent, style="Card.TFrame")
        btn_row.grid(row=6, column=0, sticky="w", padx=16)
        ttk.Button(btn_row, text=t("kirch.add_resistor"), command=self._kvl_add_resistor)\
            .pack(side="left", padx=(0, 6))
        ttk.Button(btn_row, text=t("kirch.remove_resistor"), command=self._kvl_remove_resistor)\
            .pack(side="left")

        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=7, column=0, sticky="ew", padx=16, pady=10)

        ttk.Label(parent, text=t("kirch.current_result"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=8, column=0, sticky="w", padx=16)
        self.kvl_current_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.kvl_current_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").grid(row=9, column=0, sticky="w", padx=16, pady=(2, 8))

        ttk.Label(parent, text=t("kirch.loop_eq_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=10, column=0, sticky="w", padx=16)
        self.kvl_eq_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.kvl_eq_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", wraplength=420, justify="left")\
            .grid(row=11, column=0, sticky="w", padx=16, pady=(2, 8))
        from uikit import FitCanvas
        self.kvl_cv = FitCanvas(parent, 460, 300, kmax=1.4, height=320)
        self.kvl_cv.grid(row=12, column=0, sticky="nsew", padx=16, pady=(0, 16))

        self._kvl_solve()

    def _kvl_init_resistors(self):
        for r in (100, 220, 330):
            self._kvl_add_resistor(default=r, redraw_only=True)
        self._kvl_rebuild_grid()

    def _kvl_add_resistor(self, default=470, redraw_only=False):
        if len(self.kvl_r_vars) >= MAX_RESISTORS:
            return
        var = tk.StringVar(value=str(default))
        self.kvl_r_vars.append(var)
        if not redraw_only:
            self._kvl_rebuild_grid()
            self._kvl_solve()

    def _kvl_remove_resistor(self):
        if len(self.kvl_r_vars) <= MIN_RESISTORS:
            return
        self.kvl_r_vars.pop()
        self._kvl_rebuild_grid()
        self._kvl_solve()

    def _kvl_rebuild_grid(self):
        for child in self.kvl_resistor_frame.winfo_children():
            child.destroy()
        for i, var in enumerate(self.kvl_r_vars):
            ttk.Label(self.kvl_resistor_frame, text=t("kirch.resistor_label").format(n=i + 1),
                      font=FONT_BODY, style="CardBody.TLabel").grid(row=i, column=0, sticky="w", pady=2)
            e = ttk.Entry(self.kvl_resistor_frame, textvariable=var, width=10)
            e.grid(row=i, column=1, sticky="w", padx=(8, 0), pady=2)
            e.bind("<KeyRelease>", lambda ev: self._kvl_solve())

    def _kvl_solve(self):
        try:
            v = float(self.kvl_source_var.get())
            rs = [float(var.get()) for var in self.kvl_r_vars]
        except ValueError:
            self.kvl_current_var.set(t("kirch.invalid"))
            self.kvl_eq_var.set("")
            return
        total_r = sum(rs)
        if total_r <= 0:
            self.kvl_current_var.set(t("kirch.invalid"))
            self.kvl_eq_var.set("")
            return
        i = v / total_r
        drops = [i * r for r in rs]
        self.kvl_current_var.set(f"I = {v:g} V / {total_r:g} Ω = {i:.4g} A")

        drop_terms = " - ".join(f"{d:.3g}V" for d in drops)
        residual = v - sum(drops)
        self.kvl_eq_var.set(f"{v:g}V - ({drop_terms}) = {residual:.2g}V ≈ 0  ✓")
        if hasattr(self, "kvl_cv"):
            self.kvl_cv.show(lambda: self._paint_kvl(v, rs, drops, i))

    def _paint_kvl(self, v, rs, drops, i):
        import symbols as sym
        c = self.kvl_cv
        n = len(rs)
        x0, x1, y0, y1 = 70, 420, 60, 250
        sym.wire(c, x0, y1, x0, (y0 + y1) / 2 + 18)
        sym.wire(c, x0, (y0 + y1) / 2 - 18, x0, y0)
        sym.dc_source(c, x0, (y0 + y1) / 2)
        c.create_text(x0 - 24, (y0 + y1) / 2, text=f"{v:g} V", anchor="e", font=("Segoe UI", 10, "bold"),
                      fill="#2e7d32")
        # resistors along the top and down the right side
        span = (x1 - x0 - 30) / n
        x = x0
        sym.wire(c, x0, y0, x0 + 15, y0)
        x = x0 + 15
        cols = ["#c62828", "#ef6c00", "#8e24aa", "#1565c0", "#00838f"]
        for k, (r, d) in enumerate(zip(rs, drops)):
            sym.resistor(c, x, y0, x + span, y0, label=f"R{k + 1}", value=f"{r:g} Ω", s=min(1.0, span / 90))
            c.create_text(x + span / 2, y0 + 30, text=f"−{d:.3g} V", font=("Segoe UI", 9, "bold"),
                          fill=cols[k % len(cols)])
            x += span
        sym.wire(c, x, y0, x1, y0, x1, y1, x0, y1)
        # loop arrow
        c.create_arc(170, 110, 320, 220, start=100, extent=300, style="arc", outline="#1f6fb2", width=2)
        c.create_line(173, 150, 170, 162, fill="#1f6fb2", width=2, arrow="last")
        c.create_text(245, 165, text=f"I = {i:.3g} A", font=("Segoe UI", 10, "bold"), fill="#1f6fb2")
        # drop bar: how the source voltage is shared
        bx0, bx1, by = 60, 430, 285
        tot = sum(drops) or 1
        xx = bx0
        for k, d in enumerate(drops):
            w = (bx1 - bx0) * d / tot
            c.create_rectangle(xx, by - 9, xx + w, by + 9, fill=cols[k % len(cols)], outline="white")
            if w > 34:
                c.create_text(xx + w / 2, by, text=f"R{k + 1}", font=("Segoe UI", 8, "bold"), fill="white")
            xx += w

    # ------------------------------------------------------------------
    # KCL - node with N branches
    # ------------------------------------------------------------------
    def _build_kcl(self, parent):
        row0 = 20
        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=row0, column=0, sticky="ew", padx=16, pady=(4, 10))

        ttk.Label(parent, text=t("kirch.kcl_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=row0 + 1, column=0, sticky="w", padx=16)
        ttk.Label(parent, text=t("kirch.kcl_intro"), font=FONT_BODY, wraplength=420,
                  justify="left", style="CardBody.TLabel")\
            .grid(row=row0 + 2, column=0, sticky="w", padx=16, pady=(0, 8))

        self.kcl_branches = []
        branch_frame = ttk.Frame(parent, style="Card.TFrame")
        branch_frame.grid(row=row0 + 3, column=0, sticky="ew", padx=16)

        self.kcl_solve_idx = tk.IntVar(value=N_BRANCHES - 1)
        defaults = [("2", "in"), ("3", "in"), ("1.5", "out"), ("0", "out")]
        for i in range(N_BRANCHES):
            val_default, dir_default = defaults[i]
            val_var = tk.StringVar(value=val_default)
            dir_var = tk.StringVar(value=t("kirch.direction_in") if dir_default == "in"
                                    else t("kirch.direction_out"))
            self.kcl_branches.append({"value": val_var, "dir": dir_var, "raw_dir": dir_default})

            ttk.Radiobutton(branch_frame, text=t("kirch.solve_for"), variable=self.kcl_solve_idx,
                             value=i, command=self._kcl_solve).grid(row=i, column=0, sticky="w", pady=3)
            ttk.Label(branch_frame, text=t("kirch.branch_label").format(n=i + 1), font=FONT_BODY,
                      style="CardBody.TLabel", width=10).grid(row=i, column=1, sticky="w")
            entry = ttk.Entry(branch_frame, textvariable=val_var, width=8)
            entry.grid(row=i, column=2, sticky="w", padx=(4, 8))
            entry.bind("<KeyRelease>", lambda e: self._kcl_solve())
            dir_cb = ttk.Combobox(branch_frame, textvariable=dir_var,
                                   values=[t("kirch.direction_in"), t("kirch.direction_out")],
                                   state="readonly", width=8)
            dir_cb.grid(row=i, column=3, sticky="w")
            dir_cb.bind("<<ComboboxSelected>>", lambda e: self._kcl_solve())

        sep2 = ttk.Separator(parent, orient="horizontal")
        sep2.grid(row=row0 + 4, column=0, sticky="ew", padx=16, pady=10)

        ttk.Label(parent, text=t("kirch.sum_check_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=row0 + 5, column=0, sticky="w", padx=16)
        self.kcl_result_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.kcl_result_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", wraplength=420, justify="left")\
            .grid(row=row0 + 6, column=0, sticky="w", padx=16, pady=(2, 8))
        from uikit import FitCanvas
        self.kcl_cv = FitCanvas(parent, 460, 300, kmax=1.4, height=320)
        self.kcl_cv.grid(row=row0 + 7, column=0, sticky="nsew", padx=16, pady=(0, 16))

        self._kcl_solve()

    def _kcl_solve(self):
        solve_i = self.kcl_solve_idx.get()
        try:
            values = []
            dirs = []
            for i, b in enumerate(self.kcl_branches):
                is_in = b["dir"].get() == t("kirch.direction_in")
                dirs.append(is_in)
                if i == solve_i:
                    values.append(None)
                else:
                    values.append(float(b["value"].get()))
        except ValueError:
            self.kcl_result_var.set(t("kirch.invalid"))
            return

        known_in = sum(v for v, d in zip(values, dirs) if v is not None and d)
        known_out = sum(v for v, d in zip(values, dirs) if v is not None and not d)

        if dirs[solve_i]:
            solved = known_out - known_in  # this branch must supply the missing "in"
        else:
            solved = known_in - known_out
        solved = max(solved, 0.0) if solved >= 0 else solved
        self.kcl_branches[solve_i]["value"].set(f"{solved:.4g}")

        total_in = known_in + (solved if dirs[solve_i] else 0)
        total_out = known_out + (solved if not dirs[solve_i] else 0)
        lines = [f"ΣI_in = {total_in:.4g} A     ΣI_out = {total_out:.4g} A"]
        lines.append(t("kirch.balanced"))
        self.kcl_result_var.set("\n".join(lines))
        vals = [solved if v is None else v for v in values]
        if hasattr(self, "kcl_cv"):
            self.kcl_cv.show(lambda: self._paint_kcl(vals, dirs, solve_i))

    def _paint_kcl(self, vals, dirs, solve_i):
        import math
        c = self.kcl_cv
        cx, cy, R = 230, 155, 95
        n = len(vals)
        c.create_oval(cx - 9, cy - 9, cx + 9, cy + 9, fill="#1f2a44", outline="")
        mx = max([abs(v) for v in vals] + [1e-12])
        for k, (v, d) in enumerate(zip(vals, dirs)):
            ang = math.pi / 2 + 2 * math.pi * k / n
            ex, ey = cx + R * math.cos(ang), cy - R * math.sin(ang)
            w = 2 + 6 * abs(v) / mx
            col = "#2e7d32" if d else "#c62828"
            if d:
                c.create_line(ex, ey, cx + 14 * math.cos(ang), cy - 14 * math.sin(ang), fill=col, width=w,
                              arrow="last", arrowshape=(12 + w, 14 + w, 5 + w / 2))
            else:
                c.create_line(cx + 12 * math.cos(ang), cy - 12 * math.sin(ang), ex, ey, fill=col, width=w,
                              arrow="last", arrowshape=(12 + w, 14 + w, 5 + w / 2))
            ca, sa = math.cos(ang), math.sin(ang)
            anchor = "w" if ca > 0.3 else "e" if ca < -0.3 else ("s" if sa > 0 else "n")
            lx, ly = cx + (R + 8) * ca, cy - (R + 8) * sa
            txt = f"I{k + 1} = {v:.3g} A" + ("  (?)" if k == solve_i else "")
            c.create_text(lx, ly, text=txt, anchor=anchor, font=("Segoe UI", 10, "bold"), fill=col)
        c.create_text(8, 8, text="ΣI_in = ΣI_out", anchor="nw", font=("Segoe UI", 10, "bold"), fill="#1f2a44")
        c.create_text(8, 28, text="→ in", anchor="nw", font=("Segoe UI", 9, "bold"), fill="#2e7d32")
        c.create_text(8, 44, text="← out", anchor="nw", font=("Segoe UI", 9, "bold"), fill="#c62828")
