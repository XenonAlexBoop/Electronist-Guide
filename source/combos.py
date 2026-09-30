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

from widgets import combine_pair, format_value, parse_value, ScrollableFrame, FONT_H2, FONT_BODY, FONT_MONO, debounce
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
        self.canvas.bind("<Configure>", debounce(self.canvas, self._on_canvas_resize, 100))

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


# ---------------------------------------------------------------------------
# v6.3 "Quick list": series AND parallel side by side, each with its diagram,
# total and how the voltage / current is shared between the parts.
from i18n import register as _register  # noqa: E402

_register({
    "qc.series": ("In series", "În serie"),
    "qc.parallel": ("In parallel", "În paralel"),
    "qc.share_v": ("Share of the voltage", "Cota din tensiune"),
    "qc.share_i": ("Share of the current", "Cota din curent"),
    "qc.share_q": ("Share of the charge", "Cota din sarcină"),
    "qc.note.r_s": ("Always larger than the largest part — the biggest resistor takes most of the voltage.",
                    "Mereu mai mare decât cea mai mare piesă — rezistorul cel mai mare preia cea mai mare tensiune."),
    "qc.note.r_p": ("Always smaller than the smallest part — the smallest resistor carries most of the current.",
                    "Mereu mai mică decât cea mai mică piesă — rezistorul cel mai mic duce cel mai mare curent."),
    "qc.note.c_s": ("Smaller than the smallest capacitor — the SMALLEST capacitor gets the largest voltage (check its rating!).",
                    "Mai mică decât cel mai mic condensator — cel MAI MIC condensator primește cea mai mare tensiune (verifică-i tensiunea nominală!)."),
    "qc.note.c_p": ("Capacitances simply add — every capacitor sees the same voltage.",
                    "Capacitățile se adună — fiecare condensator vede aceeași tensiune."),
    "qc.note.l_s": ("Inductances add (no mutual coupling) — the largest inductor takes most of the voltage.",
                    "Inductanțele se adună (fără cuplaj) — bobina cea mai mare preia cea mai mare tensiune."),
    "qc.note.l_p": ("Smaller than the smallest inductor — the smallest one carries most of the current.",
                    "Mai mică decât cea mai mică bobină — cea mai mică duce cel mai mare curent."),
})


class QuickComboPanel(ttk.Frame):
    FORMULA = {
        "resistor": ("R = R1 + R2 + …", "1/R = 1/R1 + 1/R2 + …", "Ω"),
        "capacitor": ("1/C = 1/C1 + 1/C2 + …", "C = C1 + C2 + …", "F"),
        "inductor": ("L = L1 + L2 + …", "1/L = 1/L1 + 1/L2 + …", "H"),
    }

    def __init__(self, parent, kind, accent, title, instructions, default):
        from uikit import FitCanvas
        super().__init__(parent, style="Card.TFrame")
        self.kind, self.accent = kind, accent
        # v6.4: scrolls instead of squashing the diagrams on short windows
        outer = self
        outer.columnconfigure(0, weight=1)
        outer.rowconfigure(0, weight=1)
        sf = ScrollableFrame(outer, style="Card.TFrame", fill_height=True)
        sf.grid(row=0, column=0, sticky="nsew")
        B = sf.body
        B.columnconfigure(0, weight=1, uniform="qc")
        B.columnconfigure(1, weight=1, uniform="qc")
        B.rowconfigure(3, weight=1)
        ttk.Label(B, text=title, font=FONT_H2, foreground=accent, style="CardSub.TLabel")\
            .grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 2))
        ttk.Label(B, text=instructions, font=FONT_BODY, style="CardBody.TLabel", justify="left")\
            .grid(row=1, column=0, columnspan=2, sticky="w", padx=16)
        row = ttk.Frame(B, style="Card.TFrame")
        row.grid(row=2, column=0, columnspan=2, sticky="w", padx=16, pady=8)
        self.inp = tk.StringVar(value=default)
        e = ttk.Entry(row, textvariable=self.inp, width=46, font=("Consolas", 11))
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda _e: self._deb())
        e.bind("<Return>", lambda _e: self.update_all())
        ttk.Button(row, text=t("common.calculate"), command=self.update_all).pack(side="left", padx=8)
        self.msg = tk.StringVar()
        ttk.Label(row, textvariable=self.msg, foreground="#c62828", style="CardBody.TLabel").pack(side="left")
        self._deb = debounce(self, self.update_all, 300)

        self.cards = {}
        for col, mode in enumerate(("series", "parallel")):
            card = tk.Frame(B, bg="#ffffff", highlightthickness=1, highlightbackground="#e3e6ec")
            card.grid(row=3, column=col, sticky="nsew", padx=(16 if col == 0 else 8, 8 if col == 0 else 16),
                      pady=(4, 16))
            card.columnconfigure(0, weight=1)
            card.rowconfigure(1, weight=1)
            tk.Label(card, text=t("qc." + mode), font=("Segoe UI", 12, "bold"), fg=accent, bg="#ffffff",
                     anchor="w").grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 0))
            cv = FitCanvas(card, 460, 230, kmin=0.3, kmax=1.5, height=260)
            cv.grid(row=1, column=0, sticky="nsew", padx=10, pady=6)
            total = tk.StringVar()
            tk.Label(card, textvariable=total, font=("Consolas", 16, "bold"), fg=accent, bg="#ffffff",
                     anchor="w").grid(row=2, column=0, sticky="ew", padx=12)
            tk.Label(card, text=self.FORMULA[kind][col], font=("Consolas", 10), fg="#5b6475", bg="#ffffff",
                     anchor="w").grid(row=3, column=0, sticky="ew", padx=12)
            note_key = {"resistor": "r", "capacitor": "c", "inductor": "l"}[kind] + ("_s" if col == 0 else "_p")
            tk.Label(card, text=t("qc.note." + note_key), font=("Segoe UI", 9), fg="#5b6475", bg="#ffffff",
                     anchor="w", justify="left", wraplength=520).grid(row=4, column=0, sticky="ew", padx=12,
                                                                      pady=(2, 6))
            share_key = {("resistor", 0): "qc.share_v", ("resistor", 1): "qc.share_i",
                         ("capacitor", 0): "qc.share_v", ("capacitor", 1): "qc.share_q",
                         ("inductor", 0): "qc.share_v", ("inductor", 1): "qc.share_i"}[(kind, col)]
            tk.Label(card, text=t(share_key), font=("Segoe UI", 9, "bold"), fg="#1f2a44", bg="#ffffff",
                     anchor="w").grid(row=5, column=0, sticky="ew", padx=12)
            bars = tk.Canvas(card, height=60, bg="#ffffff", highlightthickness=0)
            bars.grid(row=6, column=0, sticky="ew", padx=12, pady=(2, 12))
            bars.bind("<Configure>", lambda _e: self.update_all(), add="+")
            self.cards[mode] = (cv, total, bars)
        self.after(50, self.update_all)

    def _values(self):
        from widgets import parse_value_list
        return parse_value_list(self.inp.get())

    def update_all(self):
        try:
            vals = [v for v in self._values() if v > 0]
            if not vals:
                raise ValueError
            self.msg.set("")
        except Exception:
            self.msg.set(t("common.enter_valid_values"))
            return
        unit = self.FORMULA[self.kind][2]
        prefix = sym.PREFIX_BY_KIND.get(self.kind, "R")
        ssum = sum(vals)
        rsum = sum(1 / v for v in vals)
        if self.kind == "capacitor":
            tot = {"series": 1 / rsum, "parallel": ssum}
            share = {"series": [(1 / v) / rsum for v in vals], "parallel": [v / ssum for v in vals]}
        else:
            tot = {"series": ssum, "parallel": 1 / rsum}
            share = {"series": [v / ssum for v in vals], "parallel": [(1 / v) / rsum for v in vals]}
        sym_ = {"resistor": "R", "capacitor": "C", "inductor": "L"}[self.kind]
        for mode, (cv, total, bars) in self.cards.items():
            from drawing import draw_combo_diagram
            dh = 230 if mode == "series" else max(230, 52 * len(vals) + 50)
            cv.base_h = dh
            cv.show(lambda cv=cv, mode=mode, dh=dh: draw_combo_diagram(cv, vals, mode, self.kind, w=460, h=dh,
                                                                       fixed=True))
            total.set(f"{sym_}total = {format_value(tot[mode], unit)}")
            self._bars(bars, [f"{prefix}{i + 1}" for i in range(len(vals))], share[mode])

    def _bars(self, c, names, fr):
        c.delete("all")
        W = max(200, c.winfo_width())
        n = len(names)
        rows = min(n, 8)
        rh = 18
        c.configure(height=rows * rh + 4)
        for i in range(rows):
            y = 2 + i * rh
            c.create_text(0, y + rh / 2, text=names[i], anchor="w", font=("Segoe UI", 8, "bold"), fill="#1f2a44")
            x0, x1 = 40, W - 60
            c.create_rectangle(x0, y + 3, x1, y + rh - 3, fill="#eef1f6", outline="")
            c.create_rectangle(x0, y + 3, x0 + (x1 - x0) * fr[i], y + rh - 3, fill=self.accent, outline="")
            c.create_text(W - 4, y + rh / 2, text=f"{100 * fr[i]:.1f} %", anchor="e",
                          font=("Consolas", 9), fill="#1f2a44")
