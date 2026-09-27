"""
combos.py - Step-by-step "Mixed Builder" tool: the person adds components one
at a time, choosing at each step whether the new component joins in series or
in parallel with everything built so far.

Shows:
  * a running step log,
  * the COMPLETE schematic of the whole network built so far (every
    component drawn with its real symbol, name and value - not just the last
    merge),
  * the equivalent-value expression, e.g.  Req = (R1 + R2) ∥ R3 = 1.2 kΩ,
  * optionally, what happens when a voltage (R, C) or current (L) is applied
    between terminals A and B: voltage, current/charge and power/energy of
    EVERY component.
"""
import tkinter as tk
from tkinter import ttk

from widgets import combine_pair, format_value, parse_value, ScrollableFrame, FONT_H2, FONT_BODY, FONT_MONO
import symbols as sym
from i18n import t

UNIT_BY_KIND = {"resistor": "Ω", "capacitor": "F", "inductor": "H"}
PREFIX = {"resistor": "R", "capacitor": "C", "inductor": "L"}

LEAF_W, LEAF_H = 118, 70
PAR_PAD, PAR_GAP = 26, 6


# ---------------------------------------------------------------------------
# Network tree helpers.  node = {"op": "leaf"|"series"|"parallel", ...}
# ---------------------------------------------------------------------------
def _eq(node, kind):
    if node["op"] == "leaf":
        return node["value"]
    a, b = _eq(node["a"], kind), _eq(node["b"], kind)
    return combine_pair(a, b, node["op"], kind)


def _expr(node, parent_op=None):
    if node["op"] == "leaf":
        return node["name"]
    sep = " + " if node["op"] == "series" else " ∥ "
    txt = _expr(node["a"], node["op"]) + sep + _expr(node["b"], node["op"])
    if parent_op is not None and parent_op != node["op"]:
        txt = f"({txt})"
    return txt


def _layout(node):
    """Return (w, h) at scale 1 and cache it on the node."""
    if node["op"] == "leaf":
        node["_wh"] = (LEAF_W, LEAF_H)
    elif node["op"] == "series":
        wa, ha = _layout(node["a"])
        wb, hb = _layout(node["b"])
        node["_wh"] = (wa + wb, max(ha, hb))
    else:
        wa, ha = _layout(node["a"])
        wb, hb = _layout(node["b"])
        node["_wh"] = (max(wa, wb) + 2 * PAR_PAD, ha + hb + PAR_GAP)
    return node["_wh"]


class MixedBuilderPanel(ttk.Frame):
    def __init__(self, parent, kind, accent):
        super().__init__(parent, style="Card.TFrame")
        self.kind = kind
        self.accent = accent
        self.unit = UNIT_BY_KIND[kind]
        self.steps = []  # list of dicts: {value, mode, total}
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        _sf = ScrollableFrame(self, style="Card.TFrame")
        _sf.grid(row=0, column=0, sticky="nsew")
        root = _sf.body
        root.columnconfigure(0, weight=1)

        pad = {"padx": 16, "pady": 6}
        ttk.Label(root, text=t("combos.intro"), font=FONT_BODY, wraplength=760,
                  justify="left", style="CardBody.TLabel").grid(row=0, column=0, sticky="w", **pad)

        row1 = ttk.Frame(root, style="Card.TFrame")
        row1.grid(row=1, column=0, sticky="w", padx=16)
        ttk.Label(row1, text=t("combos.new_value"), font=FONT_BODY, style="CardBody.TLabel")\
            .pack(side="left")
        self.value_var = tk.StringVar()
        entry = ttk.Entry(row1, textvariable=self.value_var, width=12)
        entry.pack(side="left", padx=(6, 12))
        entry.bind("<Return>", lambda e: self._add_step())
        ttk.Label(row1, text=t("combos.combine_as"), font=FONT_BODY, style="CardBody.TLabel")\
            .pack(side="left")
        self._mode_labels = {t("common.series"): "series", t("common.parallel"): "parallel"}
        self.mode_var = tk.StringVar(value=t("common.series"))
        ttk.Combobox(row1, textvariable=self.mode_var, values=list(self._mode_labels),
                     state="readonly", width=10).pack(side="left", padx=(6, 0))

        btn_row = ttk.Frame(root, style="Card.TFrame")
        btn_row.grid(row=2, column=0, sticky="w", padx=16, pady=(6, 8))
        ttk.Button(btn_row, text=t("combos.add"), command=self._add_step).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text=t("combos.undo"), command=self._undo).pack(side="left", padx=(0, 8))
        ttk.Button(btn_row, text=t("combos.reset"), command=self._reset).pack(side="left")

        # ---- complete schematic (scrollable) ----
        ttk.Label(root, text=t("combos.schematic_title"), font=FONT_H2, foreground=accent,
                  style="CardSub.TLabel").grid(row=3, column=0, sticky="w", padx=16, pady=(4, 2))
        sch = ttk.Frame(root, style="Card.TFrame")
        sch.grid(row=4, column=0, sticky="ew", padx=16)
        sch.columnconfigure(0, weight=1)
        self.canvas = tk.Canvas(sch, height=180, bg=sym.CANVAS_BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="ew")
        self._hsb = ttk.Scrollbar(sch, orient="horizontal", command=self.canvas.xview)
        self._hsb.grid(row=1, column=0, sticky="ew")
        self.canvas.configure(xscrollcommand=self._hsb.set)
        self._last_w = 0
        self.canvas.bind("<Configure>", self._on_canvas_resize)

        self.result_var = tk.StringVar(value=t("combos.empty_state"))
        ttk.Label(root, textvariable=self.result_var, font=FONT_MONO, foreground=accent,
                  style="CardFormula.TLabel", justify="left", wraplength=700)\
            .grid(row=5, column=0, sticky="w", padx=16, pady=(8, 4))

        # ---- step log ----
        self.table = ttk.Treeview(root, columns=("step", "name", "value", "op", "total"),
                                   show="headings", height=5)
        for col, key, wdt in (("step", "combos.col_step", 50), ("name", "combos.col_name", 60),
                              ("value", "combos.col_value", 110), ("op", "combos.col_op", 110),
                              ("total", "combos.col_total", 140)):
            self.table.heading(col, text=t(key))
            self.table.column(col, width=wdt, anchor="center")
        self.table.grid(row=6, column=0, sticky="ew", padx=16, pady=(4, 8))

        # ---- apply a source between A and B ----
        ttk.Separator(root, orient="horizontal").grid(row=7, column=0, sticky="ew", padx=16, pady=6)
        src = ttk.Frame(root, style="Card.TFrame")
        src.grid(row=8, column=0, sticky="w", padx=16)
        src_key = "combos.apply_current" if kind == "inductor" else "combos.apply_voltage"
        ttk.Label(src, text=t(src_key), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self.source_var = tk.StringVar(value="1" if kind == "inductor" else "10")
        e2 = ttk.Entry(src, textvariable=self.source_var, width=10)
        e2.pack(side="left", padx=6)
        e2.bind("<KeyRelease>", lambda e: self._redraw())
        ttk.Label(src, text="A" if kind == "inductor" else "V", font=FONT_BODY,
                  style="CardBody.TLabel").pack(side="left")

        cols = ("name", "value", "v", "x", "p")
        self.detail = ttk.Treeview(root, columns=cols, show="headings", height=6)
        hdr = {
            "resistor": ("combos.col_name", "combos.col_value", "combos.col_voltage",
                         "combos.col_current", "combos.col_power"),
            "capacitor": ("combos.col_name", "combos.col_value", "combos.col_voltage",
                          "combos.col_charge", "combos.col_energy"),
            "inductor": ("combos.col_name", "combos.col_value", "combos.col_current",
                         "combos.col_flux", "combos.col_energy"),
        }[kind]
        for col, key in zip(cols, hdr):
            self.detail.heading(col, text=t(key))
            self.detail.column(col, width=110, anchor="center")
        self.detail.grid(row=9, column=0, sticky="ew", padx=16, pady=(6, 4))
        self.detail_note = tk.StringVar()
        ttk.Label(root, textvariable=self.detail_note, font=("Segoe UI", 9), style="CardBody.TLabel",
                  wraplength=700, justify="left").grid(row=10, column=0, sticky="w", padx=16, pady=(0, 16))

        self._redraw()

    # ------------------------------------------------------------------
    def _add_step(self):
        try:
            val = parse_value(self.value_var.get())
            if val <= 0:
                raise ValueError
        except Exception:
            self.result_var.set(t("combos.invalid_value"))
            return
        if not self.steps:
            self.steps.append({"value": val, "mode": None, "total": val})
        else:
            mode = self._mode_labels.get(self.mode_var.get(), "series")
            new_total = combine_pair(self.steps[-1]["total"], val, mode, self.kind)
            self.steps.append({"value": val, "mode": mode, "total": new_total})
        self.value_var.set("")
        self._redraw()

    def _undo(self):
        if self.steps:
            self.steps.pop()
            self._redraw()

    def _reset(self):
        self.steps = []
        self._redraw()

    def _tree(self):
        node = None
        for i, st in enumerate(self.steps):
            leaf = {"op": "leaf", "value": st["value"], "name": f"{PREFIX[self.kind]}{i + 1}", "idx": i}
            node = leaf if node is None else {"op": st["mode"], "a": node, "b": leaf}
        return node

    def _on_canvas_resize(self, event):
        if abs(event.width - self._last_w) > 8:
            self._last_w = event.width
            self._draw_schematic()

    # ------------------------------------------------------------------
    def _draw_schematic(self):
        c = self.canvas
        c.delete("all")
        tree = self._tree()
        if tree is None:
            c.configure(scrollregion=(0, 0, 10, 10), height=120)
            c.create_text(20, 60, anchor="w", text=t("combos.empty_state"), fill="#888",
                          font=("Segoe UI", 10))
            return
        w, h = _layout(tree)
        avail = max(200, (c.winfo_width() or 600) - 70)
        s = max(0.5, min(1.0, avail / w))
        x0, y0 = 35, 18
        total_w = w * s + 70
        total_h = h * s + 36
        c.configure(height=max(120, min(520, total_h)), scrollregion=(0, 0, total_w, total_h))
        self._draw_node(tree, x0, y0, s, len(self.steps) - 1)
        mid = y0 + h * s / 2
        sym.wire(c, 12, mid, x0, mid)
        sym.wire(c, x0 + w * s, mid, x0 + w * s + 23, mid)
        sym.terminal(c, 12, mid, label="A")
        sym.terminal(c, x0 + w * s + 23, mid, label="B")

    def _draw_node(self, node, x, y, s, newest):
        c = self.canvas
        w, h = node["_wh"]
        w, h = w * s, h * s
        mid = y + h / 2
        if node["op"] == "leaf":
            lead = 10 * s
            color = self.accent if node["idx"] == newest and len(self.steps) > 1 else sym.SYM_COLOR
            sym.wire(c, x, mid, x + lead, mid)
            sym.wire(c, x + w - lead, mid, x + w, mid)
            sym.component(c, self.kind, x + lead, mid, x + w - lead, mid, label=node["name"],
                          value=format_value(node["value"], self.unit), s=0.9 * s, color=color)
            return
        a, b = node["a"], node["b"]
        wa, ha = (v * s for v in a["_wh"])
        wb, hb = (v * s for v in b["_wh"])
        if node["op"] == "series":
            self._draw_node(a, x, mid - ha / 2, s, newest)
            self._draw_node(b, x + wa, mid - hb / 2, s, newest)
        else:
            pad = PAR_PAD * s
            inner = w - 2 * pad
            yt = y + ha / 2
            yb = y + ha + PAR_GAP * s + hb / 2
            lx, rx = x + pad, x + w - pad
            sym.wire(c, x, mid, lx, mid)
            sym.wire(c, rx, mid, x + w, mid)
            sym.wire(c, lx, yt, lx, yb)
            sym.wire(c, rx, yt, rx, yb)
            sym.node(c, lx, mid, s)
            sym.node(c, rx, mid, s)
            for sub, sw, sy, yc in ((a, wa, y, yt), (b, wb, y + ha + PAR_GAP * s, yb)):
                sx = lx + (inner - sw) / 2
                if sx > lx:
                    sym.wire(c, lx, yc, sx, yc)
                    sym.wire(c, sx + sw, yc, rx, yc)
                self._draw_node(sub, sx, sy, s, newest)
                sym.node(c, lx, yc, s)
                sym.node(c, rx, yc, s)

    # ------------------------------------------------------------------
    def _redraw(self):
        for row in self.table.get_children():
            self.table.delete(row)
        for row in self.detail.get_children():
            self.detail.delete(row)
        self._draw_schematic()

        if not self.steps:
            self.result_var.set(t("combos.empty_state"))
            self.detail_note.set("")
            return

        for i, step in enumerate(self.steps):
            op = t("combos.first_value") if step["mode"] is None else (
                t("common.series") if step["mode"] == "series" else t("common.parallel"))
            self.table.insert("", "end", values=(
                i + 1, f"{PREFIX[self.kind]}{i + 1}", format_value(step["value"], self.unit), op,
                format_value(step["total"], self.unit)))

        tree = self._tree()
        final = self.steps[-1]["total"]
        sym_eq = f"{PREFIX[self.kind]}eq"
        self.result_var.set(f"{sym_eq} = {_expr(tree)}\n{sym_eq} = {format_value(final, self.unit)}"
                            f"      ({t('combos.op_legend')})")
        self._solve_details(tree)

    def _solve_details(self, tree):
        try:
            src = parse_value(self.source_var.get())
        except Exception:
            self.detail_note.set(t("common.enter_valid_values"))
            return
        rows = []
        kind = self.kind

        def walk(node, v=None, i=None):
            """Resistor/capacitor: v = voltage across node. Inductor: i = current through node."""
            if node["op"] == "leaf":
                val = node["value"]
                if kind == "resistor":
                    cur = v / val
                    rows.append((node["name"], format_value(val, "Ω"), format_value(v, "V"),
                                 format_value(cur, "A"), format_value(v * cur, "W")))
                elif kind == "capacitor":
                    q = val * v
                    rows.append((node["name"], format_value(val, "F"), format_value(v, "V"),
                                 format_value(q, "C"), format_value(0.5 * val * v * v, "J")))
                else:
                    rows.append((node["name"], format_value(val, "H"), format_value(i, "A"),
                                 format_value(val * i, "Wb"), format_value(0.5 * val * i * i, "J")))
                return
            a, b = node["a"], node["b"]
            ea, eb = _eq(a, kind), _eq(b, kind)
            if kind == "resistor":
                if node["op"] == "series":
                    cur = v / (ea + eb)
                    walk(a, v=cur * ea)
                    walk(b, v=cur * eb)
                else:
                    walk(a, v=v)
                    walk(b, v=v)
            elif kind == "capacitor":
                if node["op"] == "series":
                    q = v * (ea * eb / (ea + eb))
                    walk(a, v=q / ea)
                    walk(b, v=q / eb)
                else:
                    walk(a, v=v)
                    walk(b, v=v)
            else:
                if node["op"] == "series":
                    walk(a, i=i)
                    walk(b, i=i)
                else:
                    walk(a, i=i * eb / (ea + eb))
                    walk(b, i=i * ea / (ea + eb))

        try:
            if kind == "inductor":
                walk(tree, i=src)
            else:
                walk(tree, v=src)
        except ZeroDivisionError:
            return
        rows.sort(key=lambda r: int(r[0][1:]))
        for r in rows:
            self.detail.insert("", "end", values=r)
        eq = self.steps[-1]["total"]
        if kind == "resistor":
            it = src / eq
            note = t("combos.detail_note_r").format(i=format_value(it, "A"), p=format_value(src * it, "W"))
        elif kind == "capacitor":
            note = t("combos.detail_note_c").format(q=format_value(eq * src, "C"),
                                                    e=format_value(0.5 * eq * src * src, "J"))
        else:
            note = t("combos.detail_note_l").format(e=format_value(0.5 * eq * src * src, "J"))
        self.detail_note.set(note)
