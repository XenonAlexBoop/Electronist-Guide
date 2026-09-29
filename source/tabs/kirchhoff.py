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
            .grid(row=11, column=0, sticky="w", padx=16, pady=(2, 16))

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
            .grid(row=row0 + 6, column=0, sticky="w", padx=16, pady=(2, 20))

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
