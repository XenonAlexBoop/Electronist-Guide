import tkinter as tk
from tkinter import ttk

from data import get_theory
from drawing import draw_gate_symbol, draw_timing_diagram
from widgets import TheoryPanel, ScrollableFrame, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ACCENT, debounce
from logic.boolexpr import parse, ParseError
from logic.truthtable import build_truth_table
from logic.minimize import minimize
from logic.builder import LogicBuilderView
from i18n import t, register

register({"digital.tt_hint": ("Click a row to set the inputs", "Clic pe un rând pentru a seta intrările")})

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


register({"digital.iec": ("IEC symbol", "Simbol IEC"),
          "digital.switch": ("Switch analogy (lamp = Y)", "Analogie cu întrerupătoare (bec = Y)"),
          "digital.inverted": ("…then inverted", "…apoi negat"),
          "digital.inverted_state": ("lamp = {l}, then inverted → Y = {y}", "bec = {l}, apoi negat → Y = {y}"),
          "digital.lamp_state": ("lamp {y} = Y   (click a switch to flip it)",
                                 "bec {y} = Y   (clic pe un întrerupător pentru a-l comuta)")})

_IEC_TEXT = {"AND": "&", "NAND": "&", "OR": "≥1", "NOR": "≥1", "XOR": "=1", "XNOR": "=1", "NOT": "1"}


def _draw_gate_alternatives(c, kind, a=0, b=0, y=0):
    """IEC rectangular symbol + a switch-and-lamp picture of the gate that
    follows the current inputs (v6.4: switches open/close, lamp lights)."""
    ink, muted = "#1f2a44", "#5b6475"
    on_col, off_col = "#1f6a5f", "#9aa3b2"
    inv = kind in ("NOT", "NAND", "NOR", "XNOR")
    two = kind != "NOT"
    # IEC box
    c.create_text(60, 10, text=t("digital.iec"), font=("Segoe UI", 8, "bold"), fill=muted)
    c.create_rectangle(35, 30, 85, 110, outline=ink, width=2, fill="#f5f0e2")
    c.create_text(60, 45, text=_IEC_TEXT[kind], font=("Segoe UI", 12, "bold"), fill=ink)
    ys = (55, 90) if two else (70,)
    for yy, nm, v in zip(ys, "AB", (a, b)):
        c.create_line(12, yy, 35, yy, fill=on_col if v else off_col, width=3 if v else 2)
        c.create_text(9, yy, text=f"{nm}={v}", anchor="e", font=("Segoe UI", 8, "bold"), fill=on_col if v else muted)
    if inv:
        c.create_polygon(85, 64, 97, 70, 85, 70, fill=ink, outline=ink)   # IEC negation triangle
    c.create_line(85, 70, 110, 70, fill=on_col if y else off_col, width=3 if y else 2)
    c.create_text(113, 70, text=f"Y={y}", anchor="w", font=("Segoe UI", 8, "bold"), fill=on_col if y else muted)
    # switch analogy
    x0 = 150
    c.create_text(265, 10, text=t("digital.switch"), font=("Segoe UI", 8, "bold"), fill=muted)
    base = {"NAND": "AND", "NOR": "OR", "XNOR": "XOR"}.get(kind, kind)

    def switch(x, yy, name, closed, side=False):
        col = on_col if closed else ink
        c.create_oval(x - 3, yy - 3, x + 3, yy + 3, fill=ink, outline=ink)
        c.create_oval(x + 25, yy - 3, x + 31, yy + 3, fill=ink, outline=ink)
        if closed:
            c.create_line(x, yy, x + 28, yy, fill=col, width=3)
        else:
            c.create_line(x, yy, x + 25, yy - 14, fill=col, width=2)
        if side:
            c.create_text(x - 36, yy, text=f"{name}={int(closed)}", anchor="e", font=("Segoe UI", 8, "bold"),
                          fill="#1f6a5f")
        else:
            c.create_text(x + 14, yy - 22, text=f"{name}={int(closed)}", font=("Segoe UI", 8, "bold"),
                          fill="#1f6a5f")

    top, bot = 55, 120
    c.create_line(x0, top, x0, 80, fill=ink, width=2)
    c.create_line(x0 - 10, 80, x0 + 10, 80, fill=ink, width=2)
    c.create_line(x0 - 5, 86, x0 + 5, 86, fill=ink, width=3)
    c.create_line(x0, 86, x0, bot, fill=ink, width=2)
    c.create_line(x0, bot, 360, bot, fill=ink, width=2)
    if base == "AND":
        lit = a and b
        c.create_line(x0, top, 190, top, fill=ink, width=2)
        switch(190, top, "A", a)
        c.create_line(220, top, 250, top, fill=ink, width=2)
        switch(250, top, "B", b)
        c.create_line(280, top, 340, top, fill=ink, width=2)
    elif base == "OR":
        lit = a or b
        c.create_line(x0, top, 200, top, fill=ink, width=2)
        c.create_line(200, top - 22, 200, top + 18, fill=ink, width=2)
        c.create_line(200, top - 22, 230, top - 22, fill=ink, width=2)
        c.create_line(200, top + 18, 230, top + 18, fill=ink, width=2)
        switch(230, top - 22, "A", a, side=True)
        switch(230, top + 18, "B", b, side=True)
        c.create_line(260, top - 22, 290, top - 22, fill=ink, width=2)
        c.create_line(260, top + 18, 290, top + 18, fill=ink, width=2)
        c.create_line(290, top - 22, 290, top + 18, fill=ink, width=2)
        c.create_line(290, top, 340, top, fill=ink, width=2)
    elif base == "XOR":
        # two changeover ("staircase") switches joined by two travelling wires
        lit = a != b
        ta, tb = top - 16, top + 16
        c.create_line(x0, top, 190, top, fill=ink, width=2)
        for yy in (ta, tb):
            c.create_oval(213, yy - 3, 219, yy + 3, fill=ink, outline=ink)
            c.create_oval(267, yy - 3, 273, yy + 3, fill=ink, outline=ink)
            c.create_line(216, yy, 270, yy, fill=ink, width=2)
        c.create_oval(187, top - 3, 193, top + 3, fill=ink, outline=ink)
        c.create_oval(293, top - 3, 299, top + 3, fill=ink, outline=ink)
        c.create_line(190, top, 216, ta if a else tb, fill=on_col if lit else ink, width=3)
        c.create_line(296, top, 270, tb if b else ta, fill=on_col if lit else ink, width=3)
        c.create_text(196, top + 22, text=f"A={a}", font=("Segoe UI", 8, "bold"), fill="#1f6a5f")
        c.create_text(290, top + 22, text=f"B={b}", font=("Segoe UI", 8, "bold"), fill="#1f6a5f")
        c.create_line(296, top, 340, top, fill=ink, width=2)
    else:  # NOT: a closed switch in parallel with the lamp shorts it out
        lit = not a
        c.create_line(x0, top, 340, top, fill=ink, width=2)
        c.create_rectangle(196, top - 6, 214, top + 6, outline=ink, width=2, fill="#ffffff")
        c.create_text(205, top - 14, text="R", font=("Segoe UI", 8), fill=muted)
        c.create_line(300, top, 300, top + 26, fill=ink, width=2)
        # vertical switch
        c.create_oval(297, top + 23, 303, top + 29, fill=ink, outline=ink)
        c.create_oval(297, top + 51, 303, top + 57, fill=ink, outline=ink)
        if a:
            c.create_line(300, top + 26, 300, top + 54, fill=on_col, width=3)
        else:
            c.create_line(300, top + 26, 314, top + 50, fill=ink, width=2)
        c.create_text(288, top + 40, text=f"A={a}", anchor="e", font=("Segoe UI", 8, "bold"), fill="#1f6a5f")
        c.create_line(300, top + 54, 300, bot, fill=ink, width=2)
    # lamp
    c.create_line(340, top, 360, top, 360, 78, fill=ink, width=2)
    if lit:
        for r, col in ((20, "#fff3b0"), (15, "#ffe066")):
            c.create_oval(360 - r, 89 - r, 360 + r, 89 + r, fill=col, outline="")
    c.create_oval(349, 78, 371, 100, outline=ink, width=2, fill="#ffd21f" if lit else "#e9ecef")
    c.create_line(353, 82, 367, 96, fill=ink)
    c.create_line(353, 96, 367, 82, fill=ink)
    c.create_line(360, 100, 360, bot, fill=ink, width=2)
    if inv and kind != "NOT":
        c.create_text(265, 140, text=t("digital.inverted_state").format(l=int(bool(lit)), y=y),
                      font=("Segoe UI", 8, "italic"), fill="#c62828")
    else:
        c.create_text(265, 140, text=t("digital.lamp_state").format(y=y), font=("Segoe UI", 8, "italic"),
                      fill=on_col if y else muted)


class DigitalLogicTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1, minsize=380)
        self.columnconfigure(1, weight=1, minsize=360)
        self.rowconfigure(1, weight=1)

        title = ttk.Label(self, text=t("digital.tab_title"), font=FONT_H1, style="TabTitle.TLabel")
        title.grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 6))

        left = ttk.Frame(self, style="Tab.TFrame")
        left.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=20, pady=10)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)

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

        from widgets import lazy_tab
        from .learn import learn_page
        lazy_tab(nb, t("common.learn"), lambda p: learn_page(p, ACCENT_C, "digital", extra=lambda b: __import__("tabs.learn_extras", fromlist=["x"]).digital_gallery(b, ACCENT_C).pack(fill="x")))

    # ------------------------------------------------------------------
    # Logic Gates explorer
    # ------------------------------------------------------------------
    def _build_gates_tab(self, parent):
        # v6.3: gate picker as buttons; symbol | truth table | explanation side by side,
        # full-width timing diagram underneath - everything scaled to the page
        from uikit import FitCanvas, Segmented
        for c, w in ((0, 4), (1, 3), (2, 4)):
            parent.columnconfigure(c, weight=w, uniform="gates")
        self.gate_var = tk.StringVar(value="AND")
        selector = ttk.Frame(parent, style="Card.TFrame")
        selector.grid(row=0, column=0, columnspan=3, sticky="w", padx=16, pady=(14, 8))
        ttk.Label(selector, text=t("digital.gate_select"), font=FONT_BODY, style="CardBody.TLabel")\
            .pack(side="left", padx=(0, 8))
        Segmented(selector, [(g, g) for g in GATES], self.gate_var, command=lambda _k: self._on_gate_change(),
                  accent=ACCENT_C, font_size=10).pack(side="left")

        # ---- symbol + inputs
        left_col = tk.Frame(parent, bg="#ffffff", highlightthickness=1, highlightbackground="#e3e6ec")
        left_col.grid(row=1, column=0, sticky="nsew", padx=(16, 6), pady=6)
        self.gate_canvas = FitCanvas(left_col, 220, 130, kmax=2.2, height=250, bg="#ffffff")
        self.gate_canvas.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        self.gate_canvas.bind("<Button-1>", self._on_gate_click)
        io_frame = tk.Frame(left_col, bg="#ffffff")
        io_frame.pack(pady=(4, 12))
        self.input_a_var = tk.IntVar(value=0)
        self.input_b_var = tk.IntVar(value=1)
        self.btn_a = ttk.Button(io_frame, text="A = 0", width=7, command=lambda: self._toggle_input("A"))
        self.btn_a.pack(side="left", padx=(0, 8))
        self.btn_b = ttk.Button(io_frame, text="B = 1", width=7, command=lambda: self._toggle_input("B"))
        self.btn_b.pack(side="left", padx=(0, 16))
        self.output_var = tk.StringVar(value="Y = 0")
        self.output_lbl = tk.Label(io_frame, textvariable=self.output_var, font=(FONT_MONO[0], 18, "bold"),
                                   bg="#ffffff")
        self.output_lbl.pack(side="left")

        # ---- truth table
        mid = tk.Frame(parent, bg="#ffffff", highlightthickness=1, highlightbackground="#e3e6ec")
        mid.grid(row=1, column=1, sticky="nsew", padx=6, pady=6)
        tk.Label(mid, text=t("digital.truth_table"), font=FONT_H2, bg="#ffffff", fg="#1f2a44")\
            .pack(anchor="w", padx=14, pady=(10, 6))
        self.tt_frame = tk.Frame(mid, bg="#ffffff")
        self.tt_frame.pack(padx=14, pady=4)
        self.expr_var = tk.StringVar()
        tk.Label(mid, textvariable=self.expr_var, font=(FONT_MONO[0], 16, "bold"), fg=ACCENT_C, bg="#ffffff")\
            .pack(pady=(14, 4))
        tk.Label(mid, text=t("digital.tt_hint"), font=("Segoe UI", 8), fg="#777", bg="#ffffff")\
            .pack(pady=(0, 10))

        # ---- explanation
        right_col = tk.Frame(parent, bg="#ffffff", highlightthickness=1, highlightbackground="#e3e6ec")
        right_col.grid(row=1, column=2, sticky="nsew", padx=(6, 16), pady=6)
        self.gate_title = tk.StringVar()
        tk.Label(right_col, textvariable=self.gate_title, font=FONT_H2, fg=ACCENT_C, bg="#ffffff")\
            .pack(anchor="w", padx=14, pady=(10, 4))
        self.explain_var = tk.StringVar()
        ex = tk.Label(right_col, textvariable=self.explain_var, font=("Segoe UI", 10), bg="#ffffff",
                      justify="left", anchor="w", wraplength=360)
        ex.pack(anchor="w", fill="x", padx=14, pady=(2, 8))
        self.use_var = tk.StringVar()
        us = tk.Label(right_col, textvariable=self.use_var, font=("Segoe UI", 10), bg="#ffffff", fg="#5b6475",
                      justify="left", anchor="w", wraplength=360)
        us.pack(anchor="w", fill="x", padx=14, pady=(2, 6))
        self.alt_canvas = FitCanvas(right_col, 380, 150, kmax=1.4, height=170, bg="#ffffff")
        self.alt_canvas.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.alt_canvas.bind("<Button-1>", self._on_alt_click)
        right_col.bind("<Configure>", lambda e: (ex.configure(wraplength=max(200, e.width - 30)),
                                                 us.configure(wraplength=max(200, e.width - 30))), add="+")

        # ---- timing diagram spans the full width
        timing_section = ttk.Frame(parent, style="Card.TFrame")
        timing_section.grid(row=2, column=0, columnspan=3, sticky="ew", padx=16, pady=(12, 16))
        ttk.Label(timing_section, text=t("digital.timing_diagram"), font=FONT_H2, style="CardSub.TLabel")\
            .pack(anchor="w", pady=(4, 2))
        ttk.Label(timing_section, text=t("digital.timing_hint"), font=(FONT_BODY[0], 8), foreground="#777",
                  style="CardBody.TLabel").pack(anchor="w")
        self.timing_canvas = tk.Canvas(timing_section, height=190, bg="white",
                                       highlightthickness=1, highlightbackground="#ddd")
        self.timing_canvas.pack(fill="x", pady=(4, 0))
        self.timing_canvas.bind("<Button-1>", self._on_timing_click)
        self.timing_canvas.bind("<Configure>", lambda e: self._redraw_timing(), add="+")

        # Default sequence is deliberately not flat/boring on first view.
        self._timing_a = [0, 0, 1, 1, 0, 1, 1, 0][:TIMING_STEPS]
        self._timing_b = [0, 1, 0, 1, 1, 1, 0, 0][:TIMING_STEPS]
        self._timing_geom = None
        self._timing_rows = []

        self._on_gate_change()

    def _on_alt_click(self, e):
        """Click a switch in the switch analogy to flip that input."""
        x, y = self.alt_canvas.to_design(e.x, e.y)
        kind = self.gate_var.get()
        if kind == "NOT":
            if 280 <= x <= 330 and 60 <= y <= 120:
                self._toggle_input("A")
            return
        base = {"NAND": "AND", "NOR": "OR", "XNOR": "XOR"}.get(kind, kind)
        if base == "AND":
            if 180 <= x < 235 and 25 <= y <= 75:
                self._toggle_input("A")
            elif 240 <= x <= 295 and 25 <= y <= 75:
                self._toggle_input("B")
        elif base == "OR":
            if 220 <= x <= 275:
                self._toggle_input("A" if y < 55 else "B")
        else:
            if 180 <= x < 235 and 25 <= y <= 90:
                self._toggle_input("A")
            elif 255 <= x <= 310 and 25 <= y <= 90:
                self._toggle_input("B")

    def _on_gate_click(self, e):
        x, y = self.gate_canvas.to_design(e.x, e.y)
        if x > 60:
            return
        if self.gate_var.get() == "NOT" or y < 60:
            self._toggle_input("A")
        else:
            self._toggle_input("B")

    def _on_gate_change(self):
        kind = self.gate_var.get()
        n_in = 1 if kind == "NOT" else 2
        self.btn_b.pack_forget()
        if n_in == 2:
            self.btn_b.pack(side="left", padx=(0, 16), after=self.btn_a)
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

        self.gate_title.set(kind)
        canvas = self.gate_canvas

        def paint():
            pins = draw_gate_symbol(canvas, kind, 45, 30, w=130, h=70,
                                    in_labels=(["A"] if n_in == 1 else ["A", "B"]))
            in_vals = [a] if n_in == 1 else [a, b]
            for (px, py), v, nm in zip(pins["inputs"], in_vals, ("A", "B")):
                canvas.create_line(12, py, px, py, fill=HIGH_COLOR if v else LOW_COLOR, width=3)
                canvas.create_text(8, py, text=str(v), anchor="e", font=("Consolas", 10, "bold"),
                                   fill=HIGH_COLOR if v else LOW_COLOR)
            ox, oy = pins["output"]
            canvas.create_line(ox, oy, 205, oy, fill=HIGH_COLOR if y else LOW_COLOR, width=3)
            canvas.create_text(210, oy, text=str(y), anchor="w", font=("Consolas", 10, "bold"),
                               fill=HIGH_COLOR if y else LOW_COLOR)
        canvas.show(paint)
        self.alt_canvas.show(lambda: _draw_gate_alternatives(self.alt_canvas, kind, a, b if n_in == 2 else 0, y))

    def _redraw_table(self):
        kind = self.gate_var.get()
        n_in = 1 if kind == "NOT" else 2
        f = self.tt_frame
        for ch in f.winfo_children():
            ch.destroy()
        heads = ["A", "Y"] if n_in == 1 else ["A", "B", "Y"]
        for j, h in enumerate(heads):
            tk.Label(f, text=h, font=("Consolas", 14, "bold"), width=4, bg="#e9edf4", fg="#1f2a44",
                     pady=4).grid(row=0, column=j, padx=1, pady=1)
        a_cur, b_cur = self.input_a_var.get(), self.input_b_var.get()
        combos = [(0,), (1,)] if n_in == 1 else [(0, 0), (0, 1), (1, 0), (1, 1)]
        for r, combo in enumerate(combos, start=1):
            av = combo[0]
            bv = combo[1] if n_in == 2 else 0
            y = _GATE_FUNCS[kind](av, bv)
            cur = (av == a_cur) and (n_in == 1 or bv == b_cur)
            vals = (av, y) if n_in == 1 else (av, bv, y)
            for j, v in enumerate(vals):
                last = j == len(vals) - 1
                bg = "#dff0ea" if cur else "#ffffff"
                lab = tk.Label(f, text=str(v), font=("Consolas", 14, "bold" if last else "normal"), width=4,
                               bg=bg, fg=(HIGH_COLOR if (last and v) else "#1f2a44"), pady=4, cursor="hand2")
                lab.grid(row=r, column=j, padx=1, pady=1)
                lab.bind("<Button-1>", lambda _e, a=av, b=bv: self._set_inputs(a, b))

    def _set_inputs(self, a, b):
        self.input_a_var.set(a)
        self.input_b_var.set(b)
        self._redraw_gate()
        self._redraw_table()

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
        row_h = 62
        needed_h = 14 + len(rows) * row_h + 26
        if int(self.timing_canvas.cget("height")) != needed_h:
            self.timing_canvas.configure(height=needed_h)
        width = max(400, self.timing_canvas.winfo_width())
        step_w = (width - 50 - 16) / TIMING_STEPS
        self._timing_geom = draw_timing_diagram(self.timing_canvas, rows, left_margin=50, step_w=step_w,
                                                row_h=row_h)
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
