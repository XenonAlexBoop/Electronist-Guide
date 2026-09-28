import tkinter as tk
from tkinter import ttk

from data import get_theory
from drawing import draw_gate_symbol, draw_timing_diagram
from widgets import TheoryPanel, ScrollableFrame, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ACCENT, debounce
from logic.boolexpr import parse, ParseError
from logic.truthtable import build_truth_table
from logic.minimize import minimize
from logic.circuit_canvas import LogicBuilderView
from i18n import t

ACCENT_C = ACCENT["digital"]

GATES = ["NOT", "AND", "OR", "NAND", "NOR", "XOR", "XNOR"]

_GATE_FUNCS = {
    "NOT":  lambda a, b: 1 - a,
    "AND":  lambda a, b: 1 if (a and b) else 0,
    "OR":   lambda a, b: 1 if (a or b) else 0,
    "NAND": lambda a, b: 0 if (a and b) else 1,
    "NOR":  lambda a, b: 0 if (a or b) else 1,
    "XOR":  lambda a, b: a ^ b,
    "XNOR": lambda a, b: 1 - (a ^ b),
}

_GATE_EXPR = {
    "NOT": "Y = A'", "AND": "Y = A · B", "OR": "Y = A + B",
    "NAND": "Y = (A · B)'", "NOR": "Y = (A + B)'",
    "XOR": "Y = A ⊕ B", "XNOR": "Y = (A ⊕ B)'",
}

HIGH_COLOR = "#1f6a5f"
LOW_COLOR = "#999999"
TIMING_STEPS = 8


class DigitalLogicTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1, minsize=380)
        self.columnconfigure(1, weight=1, minsize=360)
        self.rowconfigure(1, weight=1)

        title = ttk.Label(self, text=t("digital.tab_title"), font=FONT_H1, style="TabTitle.TLabel")
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 6))

        left = ttk.Frame(self, style="Tab.TFrame")
        left.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=10)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        right = ttk.Frame(self, style="Card.TFrame")
        right.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=10)

        nb = ttk.Notebook(left)
        nb.grid(row=0, column=0, sticky="nsew")

        gates_page = ttk.Frame(nb, style="Card.TFrame")
        solver_page = ttk.Frame(nb, style="Card.TFrame")
        builder_page = ttk.Frame(nb, style="Card.TFrame")
        nb.add(gates_page, text=t("digital.subtab.gates"))
        nb.add(solver_page, text=t("digital.subtab.solver"))
        nb.add(builder_page, text=t("digital.subtab.builder"))

        # Each sub-tab's real content lives inside a ScrollableFrame: the
        # layout below is arranged to fit without scrolling at a normal
        # window size, but a short/narrow window (or a future gate with
        # more content) no longer clips anything - a scrollbar appears
        # only if it's actually needed.
        gates_scroll = ScrollableFrame(gates_page, style="Card.TFrame")
        gates_scroll.pack(fill="both", expand=True)
        solver_scroll = ScrollableFrame(solver_page, style="Card.TFrame")
        solver_scroll.pack(fill="both", expand=True)

        self._build_gates_tab(gates_scroll.body)
        self._build_solver_tab(solver_scroll.body)

        builder_page.columnconfigure(0, weight=1)
        builder_page.rowconfigure(0, weight=1)
        LogicBuilderView(builder_page).grid(row=0, column=0, sticky="nsew")

        right_scroll = ScrollableFrame(right, style="Card.TFrame")
        right_scroll.pack(fill="both", expand=True)
        TheoryPanel(right_scroll.body, get_theory("digital"), accent=ACCENT_C).pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Logic Gates explorer
    # ------------------------------------------------------------------
    def _build_gates_tab(self, parent):
        parent.columnconfigure(0, weight=0)
        parent.columnconfigure(1, weight=0)

        selector = ttk.Frame(parent, style="Card.TFrame")
        selector.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 6))
        ttk.Label(selector, text=t("digital.gate_select"), font=FONT_BODY, style="CardBody.TLabel")\
            .pack(side="left", padx=(0, 8))
        self.gate_var = tk.StringVar(value="AND")
        gate_cb = ttk.Combobox(selector, textvariable=self.gate_var, values=GATES,
                                state="readonly", width=10, font=FONT_BODY)
        gate_cb.pack(side="left")
        gate_cb.bind("<<ComboboxSelected>>", lambda e: self._on_gate_change())

        # left column: symbol + I/O toggles + expression + explanation
        left_col = ttk.Frame(parent, style="Card.TFrame")
        left_col.grid(row=1, column=0, sticky="nw", padx=16, pady=6)

        self.gate_canvas = tk.Canvas(left_col, width=220, height=130, bg="white",
                                      highlightthickness=1, highlightbackground="#ddd")
        self.gate_canvas.pack(anchor="w")

        io_frame = ttk.Frame(left_col, style="Card.TFrame")
        io_frame.pack(anchor="w", pady=6)
        self.input_a_var = tk.IntVar(value=0)
        self.input_b_var = tk.IntVar(value=1)
        self.btn_a = ttk.Button(io_frame, text="A = 0", width=6, command=lambda: self._toggle_input("A"))
        self.btn_a.pack(side="left", padx=(0, 8))
        self.btn_b = ttk.Button(io_frame, text="B = 1", width=6, command=lambda: self._toggle_input("B"))
        self.btn_b.pack(side="left", padx=(0, 12))
        self.output_var = tk.StringVar(value="Y = 0")
        self.output_lbl = ttk.Label(io_frame, textvariable=self.output_var, font=(FONT_MONO[0], 14, "bold"),
                                     style="CardFormula.TLabel")
        self.output_lbl.pack(side="left")

        self.expr_var = tk.StringVar()
        ttk.Label(left_col, textvariable=self.expr_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel").pack(anchor="w", pady=(6, 0))
        self.explain_var = tk.StringVar()
        ttk.Label(left_col, textvariable=self.explain_var, font=FONT_BODY, style="CardBody.TLabel",
                  wraplength=220, justify="left").pack(anchor="w", pady=(2, 0))
        self.use_var = tk.StringVar()
        ttk.Label(left_col, textvariable=self.use_var, font=FONT_BODY, style="CardBody.TLabel",
                  wraplength=220, justify="left").pack(anchor="w", pady=(4, 0))

        # right column: truth table (beside the symbol, not stacked below it)
        right_col = ttk.Frame(parent, style="Card.TFrame")
        right_col.grid(row=1, column=1, sticky="nw", padx=(8, 16), pady=6)

        ttk.Label(right_col, text=t("digital.truth_table"), font=FONT_H2, style="CardSub.TLabel")\
            .pack(anchor="w", pady=(0, 2))
        self.gate_table = ttk.Treeview(right_col, columns=("a", "b", "y"), show="headings", height=4)
        for c, label in (("a", "A"), ("b", "B"), ("y", "Y")):
            self.gate_table.heading(c, text=label)
            self.gate_table.column(c, width=44, anchor="center")
        self.gate_table.tag_configure("current", background="#dff0ea")
        self.gate_table.pack(anchor="w")

        # timing diagram spans the full width, below both columns
        timing_section = ttk.Frame(parent, style="Card.TFrame")
        timing_section.grid(row=2, column=0, columnspan=2, sticky="w", padx=16, pady=(10, 16))
        ttk.Label(timing_section, text=t("digital.timing_diagram"), font=FONT_H2, style="CardSub.TLabel")\
            .pack(anchor="w", pady=(4, 2))
        ttk.Label(timing_section, text=t("digital.timing_hint"), font=(FONT_BODY[0], 8), foreground="#777",
                  style="CardBody.TLabel").pack(anchor="w")
        self.timing_canvas = tk.Canvas(timing_section, width=34 + TIMING_STEPS * 38, height=170, bg="white",
                                        highlightthickness=1, highlightbackground="#ddd")
        self.timing_canvas.pack(anchor="w", pady=(4, 0))
        self.timing_canvas.bind("<Button-1>", self._on_timing_click)

        # Default sequence is deliberately not flat/boring on first view.
        self._timing_a = [0, 0, 1, 1, 0, 1, 1, 0][:TIMING_STEPS]
        self._timing_b = [0, 1, 0, 1, 1, 1, 0, 0][:TIMING_STEPS]
        self._timing_geom = None
        self._timing_rows = []

        self._on_gate_change()

    def _on_gate_change(self):
        kind = self.gate_var.get()
        n_in = 1 if kind == "NOT" else 2
        self.btn_b.pack_forget()
        if n_in == 2:
            self.btn_b.pack(side="left", padx=(0, 12), after=self.btn_a)
        self._redraw_gate()
        self._redraw_table()
        self._redraw_timing()

    def _toggle_input(self, which):
        var = self.input_a_var if which == "A" else self.input_b_var
        var.set(1 - var.get())
        self._redraw_gate()
        self._redraw_table()

    def _current_output(self):
        kind = self.gate_var.get()
        return _GATE_FUNCS[kind](self.input_a_var.get(), self.input_b_var.get())

    def _redraw_gate(self):
        kind = self.gate_var.get()
        n_in = 1 if kind == "NOT" else 2
        a, b = self.input_a_var.get(), self.input_b_var.get()
        y = self._current_output()

        self.btn_a.configure(text=f"A = {a}")
        if n_in == 2:
            self.btn_b.configure(text=f"B = {b}")
        self.output_var.set(f"Y = {y}")
        self.output_lbl.configure(foreground=HIGH_COLOR if y else LOW_COLOR)
        self.expr_var.set(_GATE_EXPR[kind])
        self.explain_var.set(t(f"digital.explain.{kind}"))
        self.use_var.set(t(f"digital.use.{kind}"))

        canvas = self.gate_canvas
        canvas.delete("all")
        pins = draw_gate_symbol(canvas, kind, 20, 25, w=130, h=70,
                                 in_labels=(["A"] if n_in == 1 else ["A", "B"]))
        in_vals = [a] if n_in == 1 else [a, b]
        for (px, py), v in zip(pins["inputs"], in_vals):
            canvas.create_line(0, py, px, py, fill=HIGH_COLOR if v else LOW_COLOR, width=3)
        ox, oy = pins["output"]
        canvas.create_line(ox, oy, 220, oy, fill=HIGH_COLOR if y else LOW_COLOR, width=3)

    def _redraw_table(self):
        kind = self.gate_var.get()
        n_in = 1 if kind == "NOT" else 2
        table = self.gate_table
        table.delete(*table.get_children())
        table["displaycolumns"] = ("a", "y") if n_in == 1 else ("a", "b", "y")
        a_cur, b_cur = self.input_a_var.get(), self.input_b_var.get()
        combos = [(0,), (1,)] if n_in == 1 else [(0, 0), (0, 1), (1, 0), (1, 1)]
        for combo in combos:
            av = combo[0]
            bv = combo[1] if n_in == 2 else 0
            y = _GATE_FUNCS[kind](av, bv)
            is_current = (av == a_cur) and (n_in == 1 or bv == b_cur)
            values = (av, y) if n_in == 1 else (av, bv, y)
            table.insert("", "end", values=values, tags=("current",) if is_current else ())

    def _redraw_timing(self):
        kind = self.gate_var.get()
        n_in = 1 if kind == "NOT" else 2
        a_seq = self._timing_a
        b_seq = self._timing_b if n_in == 2 else [0] * TIMING_STEPS
        y_seq = [_GATE_FUNCS[kind](a_seq[i], b_seq[i]) for i in range(TIMING_STEPS)]
        rows = [("A", a_seq)]
        if n_in == 2:
            rows.append(("B", b_seq))
        rows.append(("Y", y_seq))
        # Resize the canvas to fit however many rows this gate needs (2 for
        # a single-input NOT, 3 for a 2-input gate) plus room for the
        # step-number row underneath, so nothing gets cut off at the bottom.
        needed_h = 14 + len(rows) * 42 + 26
        self.timing_canvas.configure(height=needed_h)
        self._timing_geom = draw_timing_diagram(self.timing_canvas, rows)
        self._timing_rows = rows

    def _on_timing_click(self, event):
        if self._timing_geom is None:
            return
        step_w, row_h, left_margin = self._timing_geom
        if event.x < left_margin:
            return
        step = int((event.x - left_margin) // step_w)
        row = int((event.y - 14) // row_h)
        if not (0 <= step < TIMING_STEPS):
            return
        if row == 0:
            self._timing_a[step] = 1 - self._timing_a[step]
        elif row == 1 and len(self._timing_rows) == 3:
            self._timing_b[step] = 1 - self._timing_b[step]
        else:
            return  # clicked the (non-editable) Y row
        self._redraw_timing()

    # ------------------------------------------------------------------
    # Boolean solver
    # ------------------------------------------------------------------
    def _build_solver_tab(self, parent):
        parent.columnconfigure(0, weight=1)

        ttk.Label(parent, text=t("digital.solver.title"), font=FONT_H2, style="CardSub.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=16, pady=(14, 4))

        self.solver_entry_var = tk.StringVar()
        entry = ttk.Entry(parent, textvariable=self.solver_entry_var, font=FONT_MONO, width=48)
        self.solver_entry = entry
        entry.grid(row=1, column=0, sticky="w", padx=16)
        entry.bind("<KeyRelease>", lambda e: self._on_solver_change())

        ttk.Label(parent, text=t("digital.solver.placeholder_hint"), font=(FONT_BODY[0], 8),
                  foreground="#777", style="CardBody.TLabel").grid(row=3, column=0, sticky="w", padx=16, pady=(2, 0))
        ttk.Label(parent, text=t("digital.solver.syntax_hint"), font=(FONT_BODY[0], 8),
                  foreground="#777", style="CardBody.TLabel", wraplength=900, justify="left")\
            .grid(row=4, column=0, sticky="w", padx=16, pady=(2, 10))

        self.solver_status_var = tk.StringVar(value=t("digital.solver.empty"))
        ttk.Label(parent, textvariable=self.solver_status_var, font=FONT_BODY, style="CardBody.TLabel",
                  wraplength=900, justify="left").grid(row=5, column=0, sticky="w", padx=16, pady=(0, 4))

        self.solver_symbolic_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.solver_symbolic_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", wraplength=900, justify="left")\
            .grid(row=6, column=0, sticky="w", padx=16)
        self.solver_words_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.solver_words_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", wraplength=900, justify="left")\
            .grid(row=7, column=0, sticky="w", padx=16, pady=(0, 10))

        ttk.Label(parent, text=t("digital.truth_table"), font=FONT_H2, style="CardSub.TLabel")\
            .grid(row=8, column=0, sticky="w", padx=16, pady=(4, 2))
        self.solver_table_frame = ttk.Frame(parent, style="Card.TFrame")
        self.solver_table_frame.grid(row=9, column=0, sticky="w", padx=16, pady=(0, 10))
        self.solver_table = None

        # Boolean simplification: canonical -> minimal SOP/POS, with an
        # optional derivation trace generated from the actual Quine-
        # McCluskey run (not separately-written text).
        ttk.Label(parent, text=t("digital.solver.simplification_title"),
                  font=FONT_H2, style="CardSub.TLabel").grid(row=10, column=0, sticky="w", padx=16, pady=(4, 4))

        simp = ttk.Frame(parent, style="Card.TFrame")
        simp.grid(row=11, column=0, sticky="w", padx=16, pady=(0, 4))

        self.canon_sop_var = tk.StringVar()
        self.min_sop_var = tk.StringVar()
        self.canon_pos_var = tk.StringVar()
        self.min_pos_var = tk.StringVar()

        ttk.Label(simp, text=t("digital.solver.canonical_sop"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=0, column=0, sticky="nw", pady=2)
        ttk.Label(simp, textvariable=self.canon_sop_var, font=FONT_MONO, style="CardBody.TLabel",
                  wraplength=760, justify="left").grid(row=0, column=1, sticky="w", padx=(8, 0), pady=2)

        ttk.Label(simp, text=t("digital.solver.minimal_sop"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=1, column=0, sticky="nw", pady=2)
        ttk.Label(simp, textvariable=self.min_sop_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", wraplength=760, justify="left")\
            .grid(row=1, column=1, sticky="w", padx=(8, 0), pady=2)

        ttk.Label(simp, text=t("digital.solver.canonical_pos"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=2, column=0, sticky="nw", pady=2)
        ttk.Label(simp, textvariable=self.canon_pos_var, font=FONT_MONO, style="CardBody.TLabel",
                  wraplength=760, justify="left").grid(row=2, column=1, sticky="w", padx=(8, 0), pady=2)

        ttk.Label(simp, text=t("digital.solver.minimal_pos"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=3, column=0, sticky="nw", pady=2)
        ttk.Label(simp, textvariable=self.min_pos_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", wraplength=760, justify="left")\
            .grid(row=3, column=1, sticky="w", padx=(8, 0), pady=2)

        self.steps_visible = False
        self.steps_btn = ttk.Button(parent, text=t("digital.solver.show_steps"), command=self._toggle_steps)
        self.steps_btn.grid(row=13, column=0, sticky="w", padx=16, pady=(6, 4))

        self.steps_frame = ttk.Frame(parent, style="Card.TFrame")
        # not gridded until toggled on
        ttk.Label(self.steps_frame, text=t("digital.solver.steps_title"), font=(FONT_BODY[0], 9, "bold"),
                  style="CardBody.TLabel", wraplength=520, justify="left").pack(anchor="w")
        # Plain wrapped text, not a bordered/scrolling Text box - it lives
        # inside the tab's own ScrollableFrame, so the page just grows and
        # the outer scrollbar handles it. Much easier to read/navigate than
        # a small fixed-height box with its own separate (and easy-to-miss)
        # scrolling behavior.
        self.steps_var = tk.StringVar()
        self.steps_label = ttk.Label(self.steps_frame, textvariable=self.steps_var, font=FONT_BODY,
                                      style="CardBody.TLabel", wraplength=520, justify="left")
        self.steps_label.pack(anchor="w", pady=(4, 12), fill="x")

        self._minimization = None

        self._build_keypad(parent, 2)
        self._build_diagrams(parent, 12)

        self.solver_entry_var.set("A·B + ¬A·C")
        self._on_solver_change()

    # ---- keypad: build the expression with the mouse --------------------
    def _build_keypad(self, parent, row):
        kp = ttk.Frame(parent, style="Card.TFrame")
        kp.grid(row=row, column=0, sticky="w", padx=16, pady=(6, 2))
        rows = [
            [(v, v) for v in "ABCDEFGH"],
            [("·  AND", "·"), ("+  OR", " + "), ("′  NOT", "'"), ("¬(", "¬("), ("⊕  XOR", " ⊕ "),
             ("(", "("), (")", ")")],
            [("NAND", " NAND "), ("NOR", " NOR "), ("XNOR", " XNOR "), ("←", "<LEFT>"), ("→", "<RIGHT>"),
             ("⌫", "<BS>"), (t("digital.kp.clear"), "<CLR>")],
        ]
        for r, items in enumerate(rows):
            fr = ttk.Frame(kp, style="Card.TFrame")
            fr.grid(row=r, column=0, sticky="w", pady=1)
            for label, ins in items:
                w = 4 if len(label) <= 2 else 8
                ttk.Button(fr, text=label, width=w, style="Small.TButton",
                           command=lambda s_=ins: self._kp_press(s_)).pack(side="left", padx=1)
        ex = ttk.Frame(kp, style="Card.TFrame")
        ex.grid(row=3, column=0, sticky="w", pady=(4, 0))
        ttk.Label(ex, text=t("digital.kp.examples"), font=("Segoe UI", 8, "bold"), style="CardBody.TLabel")\
            .pack(side="left")
        for e in ("AB + A'C + BC", "A ⊕ B ⊕ C", "(A + B)(A + C)", "A'B'C + A'BC + AB'C + ABC", "ABC + AB'C + A'BC'D"):
            ttk.Button(ex, text=e, style="Small.TButton",
                       command=lambda e=e: (self.solver_entry_var.set(e), self._on_solver_change()))\
                .pack(side="left", padx=2)

    def _kp_press(self, ins):
        e = self.solver_entry
        pos = e.index("insert")
        txt = self.solver_entry_var.get()
        if ins == "<CLR>":
            self.solver_entry_var.set("")
        elif ins == "<BS>":
            if pos > 0:
                e.delete(pos - 1)
        elif ins == "<LEFT>":
            e.icursor(max(0, pos - 1))
        elif ins == "<RIGHT>":
            e.icursor(min(len(txt), pos + 1))
        else:
            e.insert(pos, ins)
        e.focus_set()
        self._on_solver_change()

    # ---- gate diagrams of the entered and the minimized expression -------
    def _build_diagrams(self, parent, row):
        box = ttk.Frame(parent, style="Card.TFrame")
        box.grid(row=row, column=0, sticky="ew", padx=16, pady=(8, 4))
        box.columnconfigure(0, weight=1)
        ttk.Label(box, text=t("digital.diag.title"), font=FONT_H2, style="CardSub.TLabel")\
            .grid(row=0, column=0, sticky="w")
        self.diag_mode = tk.StringVar(value="sop")
        mr = ttk.Frame(box, style="Card.TFrame")
        mr.grid(row=1, column=0, sticky="w", pady=(2, 4))
        ttk.Label(mr, text=t("digital.diag.min_form"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        for val, key in (("sop", "digital.solver.minimal_sop"), ("pos", "digital.solver.minimal_pos")):
            ttk.Radiobutton(mr, text=t(key), value=val, variable=self.diag_mode,
                            command=self._draw_diagrams).pack(side="left", padx=6)
        self.diag_cap1 = tk.StringVar()
        self.diag_cap2 = tk.StringVar()
        ttk.Label(box, textvariable=self.diag_cap1, font=("Segoe UI", 10, "bold"), style="CardBody.TLabel")\
            .grid(row=2, column=0, sticky="w")
        self.diag_in = tk.Canvas(box, height=120, bg="white", highlightthickness=1, highlightbackground="#ddd")
        self.diag_in.grid(row=3, column=0, sticky="ew", pady=(2, 8))
        ttk.Label(box, textvariable=self.diag_cap2, font=("Segoe UI", 10, "bold"), foreground=ACCENT_C,
                  style="CardBody.TLabel").grid(row=4, column=0, sticky="w")
        self.diag_min = tk.Canvas(box, height=120, bg="white", highlightthickness=1, highlightbackground="#ddd")
        self.diag_min.grid(row=5, column=0, sticky="ew", pady=(2, 4))
        self.diag_note = tk.StringVar()
        ttk.Label(box, textvariable=self.diag_note, font=("Segoe UI", 9), style="CardBody.TLabel",
                  wraplength=900, justify="left").grid(row=6, column=0, sticky="w")
        self._diag_nodes = (None, None)
        for c in (self.diag_in, self.diag_min):
            c.bind("<Configure>", debounce(c, lambda *a: self._draw_diagrams(), 120))

    def _draw_one(self, canvas, node):
        canvas.delete("all")
        if node is None:
            canvas.configure(height=40)
            return None
        from logic import expr_diagram as xd
        w, h = xd.layout_size(node)
        avail = max(canvas.winfo_width(), 400)
        col_w = xd.COL_W
        depth_cols = max(1, (w - xd.LEFT - 80) / xd.COL_W)
        if w > avail:
            col_w = max(56, (avail - xd.LEFT - 90) / depth_cols)
        ww, hh, gates, ins = xd.draw(canvas, node, 6, 4, col_w=col_w)
        canvas.configure(height=max(60, hh + 8))
        return gates, ins

    def _draw_diagrams(self):
        if not hasattr(self, "diag_in"):
            return
        entered, mres = self._diag_nodes
        c1 = self._draw_one(self.diag_in, entered)
        mnode = None
        if mres is not None:
            mnode = mres.minimal_sop if self.diag_mode.get() == "sop" else mres.minimal_pos
        c2 = self._draw_one(self.diag_min, mnode)
        fmt = t("digital.diag.cost")
        self.diag_cap1.set(t("digital.diag.entered") + ("   (" + fmt.format(g=c1[0], i=c1[1]) + ")" if c1 else ""))
        self.diag_cap2.set(t("digital.diag.minimized") + ("   (" + fmt.format(g=c2[0], i=c2[1]) + ")" if c2 else ""))
        if c1 and c2:
            if (c2[0], c2[1]) < (c1[0], c1[1]):
                self.diag_note.set(t("digital.diag.saved").format(g=c1[0] - c2[0], i=c1[1] - c2[1]))
            else:
                self.diag_note.set(t("digital.diag.already_min"))
        else:
            self.diag_note.set("")

    def _toggle_steps(self):
        self.steps_visible = not self.steps_visible
        if self.steps_visible:
            self.steps_frame.grid(row=14, column=0, sticky="w", padx=16)
            self.steps_btn.configure(text=t("digital.solver.hide_steps"))
        else:
            self.steps_frame.grid_forget()
            self.steps_btn.configure(text=t("digital.solver.show_steps"))

    def _update_steps_text(self):
        if self._minimization is not None:
            self.steps_var.set("\n".join(self._minimization.steps))
        else:
            self.steps_var.set("")

    def _on_solver_change(self):
        text = self.solver_entry_var.get()
        if not text.strip():
            self.solver_status_var.set(t("digital.solver.empty"))
            self.solver_symbolic_var.set("")
            self.solver_words_var.set("")
            self._clear_solver_table()
            self._clear_simplification()
            return
        try:
            node = parse(text)
        except ParseError as e:
            self.solver_status_var.set(f"⚠ {e.message}")
            self.solver_symbolic_var.set("")
            self.solver_words_var.set("")
            self._clear_solver_table()
            self._clear_simplification()
            return

        variables = sorted(node.variables())
        self.solver_status_var.set(t("digital.solver.variables") + " " + ", ".join(variables))
        self.solver_symbolic_var.set(t("digital.solver.parsed_symbolic") + "  Y = " + node.to_symbolic())
        self.solver_words_var.set(t("digital.solver.parsed_words") + "  Y = " + node.to_words())

        if len(variables) > 8:
            # The parser accepted the expression (so the symbolic/word forms
            # above still render correctly), but building an 8-variable-max
            # truth table from a truncated variable list would silently drop
            # variables the expression actually depends on - the evaluator
            # would then hit a missing key for every row that needs them.
            # Stop cleanly instead of building an incomplete/incorrect table.
            self.solver_status_var.set(t("digital.solver.too_many_vars").format(n=len(variables)))
            self._clear_solver_table()
            self._clear_simplification()
            return

        tt = build_truth_table(node, variables)
        self._show_solver_table(tt)

        self._minimization = minimize(tt)
        self.canon_sop_var.set("Y = " + self._minimization.canonical_sop.to_symbolic())
        self.min_sop_var.set("Y = " + self._minimization.minimal_sop.to_symbolic())
        self.canon_pos_var.set("Y = " + self._minimization.canonical_pos.to_symbolic())
        self.min_pos_var.set("Y = " + self._minimization.minimal_pos.to_symbolic())
        self._update_steps_text()
        self._diag_nodes = (node, self._minimization)
        self._draw_diagrams()

    def _clear_simplification(self):
        self.canon_sop_var.set("")
        self.min_sop_var.set("")
        self.canon_pos_var.set("")
        self.min_pos_var.set("")
        self._minimization = None
        self._update_steps_text()
        self._diag_nodes = (None, None)
        self._draw_diagrams()

    def _clear_solver_table(self):
        if self.solver_table is not None:
            self.solver_table.destroy()
            self.solver_table = None

    def _show_solver_table(self, tt):
        self._clear_solver_table()
        cols = list(tt.variables) + ["Y"]
        table = ttk.Treeview(self.solver_table_frame, columns=cols, show="headings",
                              height=min(16, len(tt.rows)))
        for c in cols:
            table.heading(c, text=c)
            table.column(c, width=48, anchor="center")
        for bits, y in tt.rows:
            table.insert("", "end", values=list(bits) + [y])
        table.pack(side="left")
        self.solver_table = table
