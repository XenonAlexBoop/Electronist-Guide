"""
rf/builder.py - RF Circuit Builder (v6, rebuilt for ease of use).

Same circuit model and solver as before (rf.model / rf.solver); only the
editor changed:

  * Parts go down with ONE click (or drag them from the list). Two-terminal
    parts are placed at a fixed length, horizontal; press R (or the Rotate
    button / right-click) to turn them. The tool returns to Select after
    each placement (hold Shift to keep placing).
  * Every connection point is drawn: a RED ring means "nothing is connected
    here", a green dot means connected, a big dot marks a junction.
  * To wire: press on any connection point and drag to another point
    (the wire is drawn as a neat L). Dropping a wire end or a part on the
    middle of an existing wire joins it there automatically.
  * Moving a part drags its wires along.
  * Values are edited with sliders or typed values and apply immediately;
    with Auto-simulate on, the S-parameters are recomputed on every change
    and shown in the live mini-plot.
  * "Circuit check" explains in plain words what is wrong, and clicking an
    item selects the offending part.
  * Undo / Redo, duplicate, examples (filters, matching networks, stubs,
    attenuator, splitter...), fit-to-view, drag-empty-space to pan.
"""
import json
import math
import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np

from i18n import t, register, tr
from widgets import parse_value, format_value, ScrollableFrame, FONT_BODY, FONT_H2, FONT_MONO, debounce
from rf.model import Component
from rf.canvas_builder import (draw_resistor, draw_inductor, draw_capacitor, draw_transmission_line,
                               draw_ground_symbol, draw_load_symbol, _draw_palette_icon, _value_summary,
                               DEFAULTS, BG, GRID_COLOR, GRID_COLOR_MAJOR, WIRE_COLOR, SELECT_COLOR,
                               PORT_COLOR, GND_COLOR, COMP_COLOR, TEXT_COLOR)
from charts import MplChartFrame

register({
    "rb.undo": ("↶ Undo", "↶ Anulează"), "rb.redo": ("↷ Redo", "↷ Refă"),
    "rb.rotate": ("⟳ Rotate (R)", "⟳ Rotește (R)"), "rb.delete": ("✕ Delete", "✕ Șterge"),
    "rb.dup": ("⧉ Duplicate", "⧉ Duplică"), "rb.clear": ("Clear all", "Golește tot"),
    "rb.fit": ("Fit", "Încadrează"), "rb.examples": ("Examples…", "Exemple…"),
    "rb.nodes": ("Show node names", "Arată numele nodurilor"),
    "rb.parts": ("Parts", "Piese"),
    "rb.parts_hint": ("Drag onto the grid, or click then click the grid.",
                      "Trage pe grilă sau apasă, apoi apasă pe grilă."),
    "rb.g.conn": ("Connections", "Conexiuni"), "rb.g.lumped": ("Components", "Componente"),
    "rb.g.term": ("Terminations", "Terminații"),
    "rb.h.idle": ("Drag from a connection point (dot / red ring) to another point to add a wire · drag a part to "
                  "move it · R = rotate · drag empty space to pan · wheel = zoom · right-click = menu",
                  "Trage de la un punct de conexiune (punct / cerc roșu) la alt punct ca să adaugi un fir · trage o "
                  "piesă ca s-o muți · R = rotește · trage spațiul gol pentru deplasare · rotița = zoom · "
                  "click dreapta = meniu"),
    "rb.h.place": ("Click on the grid to place: {p}. R = rotate, Shift+click = place several, Esc = cancel.",
                   "Apasă pe grilă ca să plasezi: {p}. R = rotește, Shift+click = mai multe, Esc = renunță."),
    "rb.h.wire": ("Wire: click point after point (each click adds an L-shaped segment). Clicking a connection "
                  "point, double-click or Esc finishes.",
                  "Fir: apasă punct după punct (fiecare clic adaugă un segment în L). Clic pe un punct de conexiune, "
                  "dublu-clic sau Esc termină."),
    "rb.h.wiring": ("Release on the point where the wire should end.", "Eliberează în punctul unde se termină firul."),
    "rb.t.wire": ("Wire", "Fir"),
    "rb.props": ("Selected part", "Piesa selectată"),
    "rb.none": ("Nothing selected — click a part.", "Nimic selectat — apasă pe o piesă."),
    "rb.wire_sel": ("A wire (zero-ohm connection). Delete it with the Delete key.",
                    "Un fir (conexiune de zero ohmi). Șterge-l cu tasta Delete."),
    "rb.check": ("Circuit check", "Verificarea circuitului"),
    "rb.ok": ("✓ Ready — every connection point is joined.", "✓ Gata — toate punctele sunt conectate."),
    "rb.p.dangling": ("{c}: {end} is not connected to anything", "{c}: {end} nu e conectat la nimic"),
    "rb.p.end1": ("left/top end", "capătul stâng/sus"), "rb.p.end2": ("right/bottom end", "capătul drept/jos"),
    "rb.p.end": ("its terminal", "terminalul"),
    "rb.p.wire": ("A wire end is left open", "Un capăt de fir e lăsat liber"),
    "rb.p.noport": ("Add at least one Port — that is where the virtual VNA connects.",
                    "Adaugă cel puțin un Port — acolo se conectează VNA-ul virtual."),
    "rb.p.noground": ("Tip: nothing goes to ground. Shunt parts need a Ground symbol at their other end.",
                      "Sfat: nimic nu merge la masă. Piesele în paralel au nevoie de simbolul Masă la celălalt capăt."),
    "rb.live": ("Live result", "Rezultat live"),
    "rb.live_none": ("The plot appears as soon as the circuit can be simulated.",
                     "Graficul apare imediat ce circuitul poate fi simulat."),
    "rb.m.rotate": ("Rotate", "Rotește"), "rb.m.delete": ("Delete", "Șterge"), "rb.m.dup": ("Duplicate", "Duplică"),
    "rb.clear_confirm": ("Remove every part and wire?", "Ștergi toate piesele și firele?"),
    "rb.d.R": ("Resistor: the same impedance at every frequency.", "Rezistor: aceeași impedanță la orice frecvență."),
    "rb.d.L": ("Inductor: impedance jωL rises with frequency — passes low, blocks high.",
               "Bobină: impedanța jωL crește cu frecvența — lasă joasele, blochează înaltele."),
    "rb.d.C": ("Capacitor: impedance 1/(jωC) falls with frequency — blocks low, passes high.",
               "Condensator: impedanța 1/(jωC) scade cu frecvența — blochează joasele, lasă înaltele."),
    "rb.d.TL": ("Ideal transmission line. Electrical length = length / (velocity factor × wavelength). "
                "A quarter-wave line transforms impedances: Zin = Z0² / ZL.",
                "Linie de transmisie ideală. Lungimea electrică = lungime / (factor de viteză × lungime de undă). "
                "O linie de sfert de undă transformă impedanțe: Zin = Z0² / ZL."),
    "rb.d.PORT": ("A VNA port: it injects a wave and measures what comes back (S11) and what arrives at the other "
                  "ports (S21…). Its other side is ground.",
                  "Un port de VNA: injectează o undă și măsoară ce se întoarce (S11) și ce ajunge la celelalte porturi "
                  "(S21…). Cealaltă parte a lui este masa."),
    "rb.d.GND": ("Ground (reference). Every ground symbol is the same node.",
                 "Masă (referință). Toate simbolurile de masă sunt același nod."),
    "rb.d.LOAD_MATCHED": ("A load equal to the reference impedance: absorbs everything, no reflection.",
                          "O sarcină egală cu impedanța de referință: absoarbe tot, fără reflexie."),
    "rb.d.LOAD_R": ("A resistor from this point to ground.", "Un rezistor de la acest punct la masă."),
    "rb.d.LOAD_Z": ("Any complex impedance R + jX from this point to ground.",
                    "Orice impedanță complexă R + jX de la acest punct la masă."),
    "rb.d.OPEN": ("Open circuit: nothing connected (total reflection, in phase).",
                  "Circuit deschis: nimic conectat (reflexie totală, în fază)."),
    "rb.d.SHORT": ("Short to ground (total reflection, inverted).", "Scurtcircuit la masă (reflexie totală, inversată)."),
    "rb.f.value": ("Value", "Valoare"), "rb.f.z0": ("Characteristic impedance Z0", "Impedanța caracteristică Z0"),
    "rb.f.len": ("Length", "Lungime"), "rb.f.vf": ("Velocity factor", "Factor de viteză"),
    "rb.f.ref": ("Reference impedance", "Impedanța de referință"), "rb.f.num": ("Port number", "Numărul portului"),
    "rb.f.r": ("Resistance R", "Rezistența R"), "rb.f.x": ("Reactance X", "Reactanța X"),
    "rb.f.en": ("Enabled", "Activ"),
    "rb.elen": ("≈ {deg:.0f}° electrical length at {f}", "≈ {deg:.0f}° lungime electrică la {f}"),
    "rb.ex.thru": ("50 Ω line (through)", "Linie de 50 Ω (directă)"),
    "rb.ex.pi": ("π attenuator, 6 dB", "Atenuator π, 6 dB"),
    "rb.ex.lpf": ("LC low-pass filter, 2 GHz (3rd order)", "Filtru trece-jos LC, 2 GHz (ord. 3)"),
    "rb.ex.rlc": ("Series RLC band-pass, 2 GHz", "Trece-bandă RLC serie, 2 GHz"),
    "rb.ex.lmatch": ("L-match 50 Ω → 200 Ω at 2 GHz", "Adaptare L 50 Ω → 200 Ω la 2 GHz"),
    "rb.ex.qwt": ("Quarter-wave transformer 50 → 100 Ω", "Transformator λ/4 50 → 100 Ω"),
    "rb.ex.stub": ("Open-stub notch at 2 GHz", "Notch cu stub deschis la 2 GHz"),
    "rb.ex.split": ("3-port resistive splitter", "Divizor rezistiv cu 3 porturi"),
})

TWO = {"R", "L", "C", "TL"}
POINT = {"gnd", "port", "LOAD_MATCHED", "LOAD_R", "LOAD_Z", "OPEN", "SHORT"}
PALETTE = [("conn", ["wire", "gnd", "port"]), ("lumped", ["R", "L", "C", "TL"]),
           ("term", ["LOAD_MATCHED", "LOAD_R", "LOAD_Z", "OPEN", "SHORT"])]
TOOL_KEYS = {"wire": "rf.tool.wire", "gnd": "rf.tool.gnd", "port": "rf.tool.port", "R": "rf.tool.r",
             "L": "rf.tool.l", "C": "rf.tool.c", "TL": "rf.tool.tl", "LOAD_MATCHED": "rf.tool.load_matched",
             "LOAD_R": "rf.tool.load_r", "LOAD_Z": "rf.tool.load_z", "OPEN": "rf.tool.open",
             "SHORT": "rf.tool.short"}
PART_LEN = 4
BAD = "#fc5c5c"
GOOD = "#48d597"

# slider ranges (lo, hi, log)
FIELD_SPECS = {
    "R": [("value", "rb.f.value", "Ω", (0.1, 10e3, True))],
    "L": [("value", "rb.f.value", "H", (0.1e-9, 1e-6, True))],
    "C": [("value", "rb.f.value", "F", (0.01e-12, 100e-12, True))],
    "TL": [("z0", "rb.f.z0", "Ω", (10, 200, True)), ("length", "rb.f.len", "m", (1e-3, 0.3, True)),
           ("vf", "rb.f.vf", "", (0.3, 1.0, False))],
    "LOAD_MATCHED": [("z0", "rb.f.ref", "Ω", (10, 200, True))],
    "LOAD_R": [("value", "rb.f.value", "Ω", (0.1, 10e3, True))],
    "LOAD_Z": [("r", "rb.f.r", "Ω", (0.1, 1e3, True)), ("x", "rb.f.x", "Ω", (-500, 500, False))],
    "PORT": [("z0", "rb.f.ref", "Ω", (10, 200, True))],
}


def _serialize(model):
    return {"wires": [[list(a), list(b)] for a, b in model.wires],
            "comps": [{"id": c.id, "kind": c.kind, "p1": list(c.p1), "p2": list(c.p2) if c.p2 else None,
                       "params": c.params} for c in model.components]}


def _deserialize(model, data):
    model.wires = [(tuple(a), tuple(b)) for a, b in data["wires"]]
    model.components = []
    mx = 0
    for d in data["comps"]:
        c = Component(d["kind"], tuple(d["p1"]), tuple(d["p2"]) if d["p2"] else None, dict(d["params"]))
        c.id = d["id"]
        mx = max(mx, c.id)
        model.components.append(c)
    Component._next_id = max(Component._next_id, mx + 1)


def _on_segment(p, a, b):
    if p == a or p == b:
        return False
    (px, py), (ax, ay), (bx, by) = p, a, b
    if (bx - ax) * (py - ay) - (by - ay) * (px - ax) != 0:
        return False
    return min(ax, bx) <= px <= max(ax, bx) and min(ay, by) <= py <= max(ay, by)


class RFBuilderView(ttk.Frame):
    def __init__(self, parent, sim_state, on_change=None, on_sweep=None):
        super().__init__(parent, style="Tab.TFrame")
        self.sim_state = sim_state
        self.model = sim_state.circuit
        self.on_change = on_change or (lambda: None)
        self.on_sweep = on_sweep
        self.grid_px = 28
        self.ox, self.oy = 80, 80
        self.tool = None
        self.orient = 0              # rotation for the part being placed (0 / 90)
        self.selected = None
        self.drag = None
        self.ghost = None
        self.wire_start = None       # wire tool: current start point
        self.hover_pt = None
        self.undo_stack, self.redo_stack = [], []
        self._palette_drag = None
        self._show_nodes = tk.BooleanVar(value=False)

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self._build_toolbar()
        body = ttk.Frame(self, style="Tab.TFrame")
        body.grid(row=1, column=0, sticky="nsew", padx=10)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        pal = ttk.Frame(body, style="Card.TFrame", width=228)
        pal.grid(row=0, column=0, sticky="nsw")
        pal.grid_propagate(False)
        holder = ttk.Frame(body, style="Tab.TFrame")
        holder.grid(row=0, column=1, sticky="nsew", padx=6)
        side = ttk.Frame(body, style="Card.TFrame", width=320)
        side.grid(row=0, column=2, sticky="nse")
        side.grid_propagate(False)
        self._build_palette(pal)
        self._build_canvas(holder)
        self._build_side(side)
        self.status = ttk.Label(self, text=t("rb.h.idle"), style="CardBody.TLabel", font=("Segoe UI", 9, "italic"),
                                wraplength=1300)
        self.status.grid(row=2, column=0, sticky="w", padx=12, pady=(2, 6))
        sim_state.on_result(lambda r: self._draw_live())
        self._changed(notify=False)

    # ================================================================ UI
    def _build_toolbar(self):
        bar = ttk.Frame(self, style="Tab.TFrame")
        bar.grid(row=0, column=0, sticky="ew", padx=10, pady=6)

        def btn(key, cmd):
            b = ttk.Button(bar, text=t(key), style="Small.TButton", command=cmd)
            b.pack(side="left", padx=(0, 4))
        btn("rb.undo", self.undo)
        btn("rb.redo", self.redo)
        btn("rb.rotate", self.rotate)
        btn("rb.delete", self.delete_selected)
        btn("rb.dup", self.duplicate)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        self._ex_names = {t("rb.ex." + k): k for k in EXAMPLES}
        self.ex_var = tk.StringVar(value=t("rb.examples"))
        cb = ttk.Combobox(bar, textvariable=self.ex_var, values=list(self._ex_names), state="readonly", width=34)
        cb.pack(side="left", padx=(0, 4))
        cb.bind("<<ComboboxSelected>>", lambda e: self.load_example(self._ex_names.get(self.ex_var.get())))
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(bar, text="−", width=3, style="Small.TButton", command=lambda: self._zoom(1 / 1.2)).pack(side="left")
        self.zoom_lbl = ttk.Label(bar, text="100%", width=6, anchor="center", style="CardBody.TLabel")
        self.zoom_lbl.pack(side="left")
        ttk.Button(bar, text="+", width=3, style="Small.TButton", command=lambda: self._zoom(1.2)).pack(side="left")
        btn("rb.fit", self.fit)
        btn("rb.clear", self.clear)
        ttk.Checkbutton(bar, text=t("rb.nodes"), variable=self._show_nodes, command=self.redraw)\
            .pack(side="left", padx=8)

    def _build_palette(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        ttk.Label(parent, text=t("rb.parts"), font=FONT_H2, style="CardTitle.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=8, pady=(8, 0))
        sf = ScrollableFrame(parent, style="Card.TFrame")
        sf.grid(row=1, column=0, sticky="nsew")
        body = sf.body
        ttk.Label(body, text=t("rb.parts_hint"), font=("Segoe UI", 8), style="CardBody.TLabel", wraplength=180,
                  justify="left").pack(anchor="w", padx=8)
        self.pal_items = {}
        for grp, kinds in PALETTE:
            ttk.Label(body, text=t("rb.g." + grp), font=("Segoe UI", 9, "bold"), style="CardSub.TLabel")\
                .pack(anchor="w", padx=8, pady=(6, 2))
            for kind in kinds:
                row = tk.Frame(body, bg="#1c2130", cursor="hand2")
                row.pack(fill="x", padx=6, pady=1)
                ic = tk.Canvas(row, width=26, height=20, bg="#1c2130", highlightthickness=0, cursor="hand2")
                ic.pack(side="left", padx=(3, 4), pady=3)
                _draw_palette_icon(ic, kind)
                lab = tk.Label(row, text=t(TOOL_KEYS[kind]), bg="#1c2130", fg=TEXT_COLOR, anchor="w",
                               font=FONT_BODY, cursor="hand2")
                lab.pack(side="left", fill="x", expand=True)
                for w in (row, ic, lab):
                    w.bind("<ButtonPress-1>", lambda e, k=kind: self._pal_press(e, k))
                    w.bind("<B1-Motion>", self._pal_motion)
                    w.bind("<ButtonRelease-1>", self._pal_release)
                self.pal_items[kind] = (row, ic, lab)

    def _paint_palette(self):
        for kind, ws in self.pal_items.items():
            col = "#3b4a78" if kind == self.tool else "#1c2130"
            for w in ws:
                w.configure(bg=col)

    def _build_canvas(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        c = tk.Canvas(parent, bg=BG, highlightthickness=0)
        c.grid(row=0, column=0, sticky="nsew")
        self.canvas = c
        c.bind("<Configure>", lambda e: self.redraw())
        c.bind("<ButtonPress-1>", self._press)
        c.bind("<B1-Motion>", self._motion)
        c.bind("<ButtonRelease-1>", self._release)
        c.bind("<Double-Button-1>", lambda e: self._end_wire())
        c.bind("<Motion>", self._hover)
        c.bind("<Leave>", lambda e: self._set_ghost(None))
        c.bind("<ButtonPress-3>", self._context)
        c.bind("<ButtonPress-2>", lambda e: setattr(self, "drag", {"mode": "pan", "x0": e.x, "y0": e.y,
                                                                    "o0": (self.ox, self.oy)}))
        c.bind("<B2-Motion>", self._motion)
        c.bind("<MouseWheel>", lambda e: self._zoom(1.1 if e.delta > 0 else 1 / 1.1, e))
        c.bind("<Button-4>", lambda e: self._zoom(1.1, e))
        c.bind("<Button-5>", lambda e: self._zoom(1 / 1.1, e))
        c.bind("<Enter>", lambda e: c.focus_set())
        for seq, fn in (("<Delete>", self.delete_selected), ("<BackSpace>", self.delete_selected),
                        ("<Escape>", self._escape), ("<Control-z>", self.undo), ("<Control-y>", self.redo),
                        ("<Control-Z>", self.redo), ("<Control-d>", self.duplicate), ("<r>", self.rotate),
                        ("<R>", self.rotate)):
            c.bind(seq, lambda e, f=fn: f())

    def _build_side(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        sf = ScrollableFrame(parent, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body
        self.props_box = ttk.Frame(body, style="Card.TFrame")
        self.props_box.pack(fill="x")
        self.check_box = ttk.Frame(body, style="Card.TFrame")
        self.check_box.pack(fill="x", pady=(8, 0))
        ttk.Label(body, text=t("rb.live"), font=FONT_H2, style="CardTitle.TLabel").pack(anchor="w", padx=10,
                                                                                        pady=(10, 0))
        self.live_note = ttk.Label(body, text=t("rb.live_none"), font=("Segoe UI", 8), style="CardBody.TLabel",
                                   wraplength=290, justify="left")
        self.live_note.pack(anchor="w", padx=10)
        self.live = MplChartFrame(body, figsize=(3.1, 2.4), with_toolbar=False)
        self.live.pack(fill="x", padx=6, pady=(2, 10))
        self._apply_later = debounce(self, self._params_changed, 250)

    # ================================================================ geometry
    @property
    def s(self):
        return self.grid_px / 28

    def g2p(self, g):
        return self.ox + g[0] * self.grid_px, self.oy + g[1] * self.grid_px

    def p2g(self, x, y):
        return round((x - self.ox) / self.grid_px), round((y - self.oy) / self.grid_px)

    def incidence(self):
        """grid point -> list of (owner, which) touching it."""
        inc = {}
        for w in self.model.wires:
            inc.setdefault(w[0], []).append((w, 0))
            inc.setdefault(w[1], []).append((w, 1))
        for c in self.model.components:
            inc.setdefault(c.p1, []).append((c, 1))
            if c.p2 is not None:
                inc.setdefault(c.p2, []).append((c, 2))
        return inc

    def port_side(self, c):
        """-1: symbol drawn to the left of the terminal, +1: to the right
        (chosen so it never sits on top of what the port connects to)."""
        p = c.p1
        left = right = 0
        for a, b in self.model.wires:
            for u, v in ((a, b), (b, a)):
                if u == p:
                    left += v[0] < p[0]
                    right += v[0] > p[0]
        for o in self.model.components:
            if o.p2 is not None:
                for u, v in ((o.p1, o.p2), (o.p2, o.p1)):
                    if u == p:
                        left += v[0] < p[0]
                        right += v[0] > p[0]
        return 1 if left > right else -1

    def _body_hit(self, c, x, y):
        s = self.s
        px, py = self.g2p(c.p1)
        if c.p2 is not None:
            qx, qy = self.g2p(c.p2)
            # exclude the last few px at each end (those are connection points)
            L = math.hypot(qx - px, qy - py) or 1
            ux, uy = (qx - px) / L, (qy - py) / L
            ax, ay = px + ux * 12 * s, py + uy * 12 * s
            bx, by = qx - ux * 12 * s, qy - uy * 12 * s
            return _seg_dist(x, y, ax, ay, bx, by) < 11 * s
        if c.kind == "PORT":
            cx = px + self.port_side(c) * 30 * s
            return math.hypot(x - cx, y - py) < 14 * s
        if c.kind == "GND":
            return px - 12 * s <= x <= px + 12 * s and py + 5 * s <= y <= py + 30 * s
        return px - 12 * s <= x <= px + 12 * s and py + 6 * s <= y <= py + 46 * s

    def hit_comp(self, x, y):
        for c in reversed(self.model.components):
            if self._body_hit(c, x, y):
                return c
        return None

    def hit_point(self, x, y, inc=None):
        inc = inc if inc is not None else self.incidence()
        g = self.p2g(x, y)
        gx, gy = self.g2p(g)
        if g in inc and math.hypot(x - gx, y - gy) < max(8, 9 * self.s):
            return g
        return None

    def hit_wire(self, x, y):
        for w in reversed(self.model.wires):
            ax, ay = self.g2p(w[0])
            bx, by = self.g2p(w[1])
            if _seg_dist(x, y, ax, ay, bx, by) < 6:
                return w
        return None

    # ================================================================ history
    def _checkpoint(self):
        self.undo_stack.append(json.dumps(_serialize(self.model)))
        self.undo_stack = self.undo_stack[-100:]
        self.redo_stack.clear()

    def undo(self):
        if self.undo_stack:
            self.redo_stack.append(json.dumps(_serialize(self.model)))
            _deserialize(self.model, json.loads(self.undo_stack.pop()))
            self.selected = None
            self._changed()

    def redo(self):
        if self.redo_stack:
            self.undo_stack.append(json.dumps(_serialize(self.model)))
            _deserialize(self.model, json.loads(self.redo_stack.pop()))
            self.selected = None
            self._changed()

    # ================================================================ editing
    def _normalize(self):
        """Split wires where another wire end / terminal lands on them, drop
        zero-length and duplicate wires."""
        changed = True
        guard = 0
        while changed and guard < 200:
            changed = False
            guard += 1
            pts = set()
            for a, b in self.model.wires:
                pts.add(a)
                pts.add(b)
            for c in self.model.components:
                pts.add(c.p1)
                if c.p2 is not None:
                    pts.add(c.p2)
            for w in list(self.model.wires):
                for p in pts:
                    if _on_segment(p, w[0], w[1]):
                        self.model.wires.remove(w)
                        self.model.wires += [(w[0], p), (p, w[1])]
                        changed = True
                        break
                if changed:
                    break
        seen = set()
        out = []
        for a, b in self.model.wires:
            if a == b:
                continue
            key = (min(a, b), max(a, b))
            if key in seen:
                continue
            seen.add(key)
            out.append((a, b))
        self.model.wires[:] = out

    def _cost(self, pts):
        """How badly a candidate wire path runs over parts (grid points
        strictly inside the path that sit on a part's body or terminal)."""
        cost = 0
        for (ax, ay), (bx, by) in zip(pts, pts[1:]):
            n = max(abs(bx - ax), abs(by - ay))
            for i in range(1, n):
                q = (ax + (bx - ax) * i // n, ay + (by - ay) * i // n)
                for c in self.model.components:
                    if c.p2 is not None:
                        if q in (c.p1, c.p2) or _on_segment(q, c.p1, c.p2):
                            cost += 3
                    elif q == c.p1:
                        cost += 3
        return cost

    def add_wire_L(self, a, b):
        if a == b:
            return
        if a[0] == b[0] or a[1] == b[1]:
            self.model.add_wire(a, b)
            return
        k1, k2 = (b[0], a[1]), (a[0], b[1])
        k = k1 if self._cost([a, k1, b]) <= self._cost([a, k2, b]) else k2
        self.model.add_wire(a, k)
        self.model.add_wire(k, b)

    def _next_port(self):
        used = {int(c.params.get("number", 0)) for c in self.model.components if c.kind == "PORT"}
        for n in range(1, 5):
            if n not in used:
                return n
        return None

    def place(self, kind, x, y):
        g = self.p2g(x, y)
        if kind == "port" and self._next_port() is None:
            messagebox.showinfo(t("rf.error.title"), tr("Maximum 4 ports.", "Maxim 4 porturi."))
            return None
        self._checkpoint()
        if kind in TWO:
            half = PART_LEN // 2
            if self.orient == 0:
                p1, p2 = (g[0] - half, g[1]), (g[0] + half, g[1])
            else:
                p1, p2 = (g[0], g[1] - half), (g[0], g[1] + half)
            comp = Component(kind, p1, p2, params=dict(DEFAULTS.get(kind, {})))
        elif kind == "gnd":
            comp = Component("GND", g)
        elif kind == "port":
            comp = Component("PORT", g, params={"number": self._next_port(), "z0": self.model.default_z0,
                                                "enabled": True})
        else:
            comp = Component(kind, g, params=dict(DEFAULTS.get(kind, {})))
        self.model.add_component(comp)
        self._normalize()
        self.selected = comp
        self._changed()
        return comp

    def rotate(self):
        if self.tool in TWO:
            self.orient = 90 - self.orient
            self.redraw()
            return
        c = self.selected
        if not isinstance(c, Component) or c.p2 is None:
            return
        self._checkpoint()
        old = (c.p1, c.p2)
        mx, my = (c.p1[0] + c.p2[0]) / 2, (c.p1[1] + c.p2[1]) / 2

        def rot(p):
            dx, dy = p[0] - mx, p[1] - my
            return (round(mx - dy), round(my + dx))
        c.p1, c.p2 = rot(c.p1), rot(c.p2)
        self._drag_wires(old, (c.p1, c.p2))
        self._normalize()
        self._changed()

    def _drag_wires(self, old_pts, new_pts):
        """Move wire ends that were attached to a part's old terminals, and
        re-route any wire that became diagonal as an L."""
        mapping = {o: n for o, n in zip(old_pts, new_pts) if o is not None}
        new_wires = []
        for a, b in self.model.wires:
            a2, b2 = mapping.get(a, a), mapping.get(b, b)
            new_wires.append((a2, b2))
        self.model.wires[:] = []
        for a, b in new_wires:
            self.add_wire_L(a, b)

    def delete_selected(self):
        sel = self.selected
        if sel is None:
            return
        self._checkpoint()
        self.model.remove(sel)
        self.selected = None
        self._changed()

    def duplicate(self):
        c = self.selected
        if not isinstance(c, Component) or c.kind == "PORT":
            return
        self._checkpoint()
        off = (1, 3)
        n = Component(c.kind, (c.p1[0] + off[0], c.p1[1] + off[1]),
                      (c.p2[0] + off[0], c.p2[1] + off[1]) if c.p2 else None, dict(c.params))
        self.model.add_component(n)
        self.selected = n
        self._normalize()
        self._changed()

    def clear(self):
        if not self.model.components and not self.model.wires:
            return
        if not messagebox.askyesno(t("rf.error.title"), t("rb.clear_confirm")):
            return
        self._checkpoint()
        self.model.clear()
        self.selected = None
        self._changed()

    def load_example(self, key):
        if not key:
            return
        self._checkpoint()
        self.model.clear()
        build, sweep = EXAMPLES[key]
        build(self.model)
        self._normalize()
        self.selected = None
        self.ex_var.set(t("rb.examples"))
        if self.on_sweep and sweep:
            self.on_sweep(*sweep)
        self._changed()
        self.after(40, self.fit)

    # ================================================================ palette
    def _pal_press(self, e, kind):
        self._palette_drag = [kind, e.x_root, e.y_root, False]

    def _pal_motion(self, e):
        d = self._palette_drag
        if not d:
            return
        if abs(e.x_root - d[1]) + abs(e.y_root - d[2]) > 6:
            d[3] = True
            if self.tool != d[0]:
                self._set_tool(d[0])
            cx, cy = e.x_root - self.canvas.winfo_rootx(), e.y_root - self.canvas.winfo_rooty()
            inside = 0 <= cx <= self.canvas.winfo_width() and 0 <= cy <= self.canvas.winfo_height()
            self._set_ghost((cx, cy) if inside else None)

    def _pal_release(self, e):
        d = self._palette_drag
        self._palette_drag = None
        if not d:
            return
        kind, _, _, moved = d
        cx, cy = e.x_root - self.canvas.winfo_rootx(), e.y_root - self.canvas.winfo_rooty()
        if moved:
            if kind != "wire" and 0 <= cx <= self.canvas.winfo_width() and 0 <= cy <= self.canvas.winfo_height():
                self.place(kind, cx, cy)
            self._set_tool("wire" if kind == "wire" else None)
        else:
            self._set_tool(kind)

    def _set_tool(self, kind):
        self.tool = kind
        self.wire_start = None
        self.ghost = None
        self._paint_palette()
        self.canvas.configure(cursor="crosshair" if kind else "")
        self._status()
        self.redraw()

    def _escape(self):
        if self.wire_start is not None:
            self.wire_start = None
            self.redraw()
            return
        self.drag = None
        self._set_tool(None)

    def _end_wire(self):
        if self.tool == "wire":
            self.wire_start = None
            self.redraw()

    def _set_ghost(self, pt):
        self.ghost = pt
        self.redraw()

    # ================================================================ mouse
    def _press(self, e):
        self.canvas.focus_set()
        x, y = e.x, e.y
        if self.tool == "wire":
            g = self.p2g(x, y)
            inc = self.incidence()
            if self.wire_start is None:
                self.wire_start = g
            else:
                self._checkpoint()
                self.add_wire_L(self.wire_start, g)
                self._normalize()
                ends_on_point = g in inc
                self.wire_start = None if ends_on_point else g
                self._changed()
            self.redraw()
            return
        if self.tool:
            self.place(self.tool, x, y)
            if not (e.state & 0x0001):
                self._set_tool(None)
            return
        inc = self.incidence()
        pt = self.hit_point(x, y, inc)
        comp = self.hit_comp(x, y)
        if pt is not None:
            self.drag = {"mode": "wire", "from": pt, "x": x, "y": y}
            self._status(t("rb.h.wiring"))
            return
        if comp is not None:
            self.selected = comp
            self.drag = {"mode": "move", "comp": comp, "x0": x, "y0": y, "p0": (comp.p1, comp.p2),
                         "moved": False, "snap": json.dumps(_serialize(self.model)),
                         "wires0": list(self.model.wires)}
            self._render_props()
            self.redraw()
            return
        w = self.hit_wire(x, y)
        if w is not None:
            self.selected = w
            self.drag = None
            self._render_props()
            self.redraw()
            return
        self.selected = None
        self.drag = {"mode": "pan", "x0": x, "y0": y, "o0": (self.ox, self.oy)}
        self.canvas.configure(cursor="fleur")
        self._render_props()
        self.redraw()

    def _motion(self, e):
        d = self.drag
        if not d:
            return
        if d["mode"] == "pan":
            self.ox = d["o0"][0] + e.x - d["x0"]
            self.oy = d["o0"][1] + e.y - d["y0"]
            self.redraw()
        elif d["mode"] == "move":
            c = d["comp"]
            dgx = round((e.x - d["x0"]) / self.grid_px)
            dgy = round((e.y - d["y0"]) / self.grid_px)
            p1, p2 = d["p0"]
            c.p1 = (p1[0] + dgx, p1[1] + dgy)
            c.p2 = (p2[0] + dgx, p2[1] + dgy) if p2 else None
            d["moved"] = bool(dgx or dgy)
            # rubber-band: attached wire ends follow (straight preview)
            mapping = {p1: c.p1}
            if p2:
                mapping[p2] = c.p2
            self.model.wires[:] = [(mapping.get(a, a), mapping.get(b, b)) for a, b in d["wires0"]]
            self.redraw()
        elif d["mode"] == "wire":
            d["x"], d["y"] = e.x, e.y
            self.redraw()

    def _release(self, e):
        d = self.drag
        self.drag = None
        self.canvas.configure(cursor="crosshair" if self.tool else "")
        if not d:
            return
        if d["mode"] == "wire":
            g = self.p2g(e.x, e.y)
            if g != d["from"]:
                self._checkpoint()
                self.add_wire_L(d["from"], g)
                self._normalize()
                self._changed()
            else:
                # a plain click on a point: select what is there
                comp = next((o for o, _ in self.incidence().get(g, []) if isinstance(o, Component)), None)
                self.selected = comp
                self._render_props()
            self._status()
            self.redraw()
        elif d["mode"] == "move":
            if d["moved"]:
                c = d["comp"]
                cur = (c.p1, c.p2)
                self.model.wires[:] = list(d["wires0"])
                self._drag_wires(d["p0"], cur)
                self.undo_stack.append(d["snap"])
                self.redo_stack.clear()
                self._normalize()
                self._changed()
            else:
                self.model.wires[:] = list(d["wires0"])

    def _hover(self, e):
        if self.tool:
            self._set_ghost((e.x, e.y))
            return
        if self.drag:
            return
        pt = self.hit_point(e.x, e.y)
        comp = self.hit_comp(e.x, e.y)
        if pt != self.hover_pt:
            self.hover_pt = pt
            self.redraw()
        self.canvas.configure(cursor="fleur" if comp else ("hand2" if pt else ""))

    def _context(self, e):
        if self.tool:
            self._escape()
            return
        comp = self.hit_comp(e.x, e.y)
        wire = None if comp else self.hit_wire(e.x, e.y)
        if comp is None and wire is None:
            return
        self.selected = comp or wire
        self._render_props()
        self.redraw()
        m = tk.Menu(self, tearoff=0)
        if comp is not None and comp.p2 is not None:
            m.add_command(label=t("rb.m.rotate"), command=self.rotate)
        if comp is not None and comp.kind != "PORT":
            m.add_command(label=t("rb.m.dup"), command=self.duplicate)
        m.add_command(label=t("rb.m.delete"), command=self.delete_selected)
        m.tk_popup(e.x_root, e.y_root)

    def _zoom(self, f, e=None):
        new = max(12, min(70, self.grid_px * f))
        cx = e.x if e is not None else self.canvas.winfo_width() / 2
        cy = e.y if e is not None else self.canvas.winfo_height() / 2
        wx, wy = (cx - self.ox) / self.grid_px, (cy - self.oy) / self.grid_px
        self.grid_px = new
        self.ox, self.oy = cx - wx * new, cy - wy * new
        self.zoom_lbl.configure(text=f"{round(self.s * 100)}%")
        self.redraw()

    def fit(self):
        pts = [p for w in self.model.wires for p in w] + \
              [p for c in self.model.components for p in (c.p1, c.p2) if p is not None]
        if not pts:
            return
        x0 = min(p[0] for p in pts) - 2
        x1 = max(p[0] for p in pts) + 2
        y0 = min(p[1] for p in pts) - 2
        y1 = max(p[1] for p in pts) + 3
        W = max(200, self.canvas.winfo_width())
        H = max(200, self.canvas.winfo_height())
        self.grid_px = max(12, min(48, min(W / (x1 - x0), H / (y1 - y0))))
        self.ox = (W - (x1 - x0) * self.grid_px) / 2 - x0 * self.grid_px
        self.oy = (H - (y1 - y0) * self.grid_px) / 2 - y0 * self.grid_px
        self.zoom_lbl.configure(text=f"{round(self.s * 100)}%")
        self.redraw()

    # ================================================================ state
    def _status(self, text=None):
        if text is None:
            if self.tool == "wire":
                text = t("rb.h.wire")
            elif self.tool:
                text = t("rb.h.place").format(p=t(TOOL_KEYS[self.tool]))
            else:
                text = t("rb.h.idle")
        self.status.configure(text=text)

    def _changed(self, notify=True):
        self._render_props()
        self._render_check()
        self.redraw()
        if notify:
            self.on_change()
        self._draw_live()

    def _params_changed(self):
        self._render_check()
        self.redraw()
        self.on_change()
        self._draw_live()

    # ================================================================ side panel
    def _render_props(self):
        box = self.props_box
        for w in box.winfo_children():
            w.destroy()
        ttk.Label(box, text=t("rb.props"), font=FONT_H2, style="CardTitle.TLabel").pack(anchor="w", padx=10,
                                                                                        pady=(10, 4))
        sel = self.selected
        if sel is None:
            ttk.Label(box, text=t("rb.none"), style="CardBody.TLabel", wraplength=290).pack(anchor="w", padx=10)
            return
        if isinstance(sel, tuple):
            ttk.Label(box, text=t("rb.wire_sel"), style="CardBody.TLabel", wraplength=290).pack(anchor="w", padx=10)
            return
        name = t(TOOL_KEYS.get({"GND": "gnd", "PORT": "port"}.get(sel.kind, sel.kind), "rf.tool.gnd"))
        ttk.Label(box, text=f"{name}  ·  {sel.label()}", font=FONT_MONO, style="CardBody.TLabel")\
            .pack(anchor="w", padx=10)
        ttk.Label(box, text=t("rb.d." + sel.kind), style="CardBody.TLabel", wraplength=290, justify="left",
                  font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(2, 6))
        if sel.kind == "PORT":
            row = ttk.Frame(box, style="Card.TFrame")
            row.pack(fill="x", padx=10, pady=2)
            ttk.Label(row, text=t("rb.f.num"), style="CardBody.TLabel", width=18).pack(side="left")
            nv = tk.StringVar(value=str(sel.params.get("number", 1)))
            cb = ttk.Combobox(row, textvariable=nv, values=["1", "2", "3", "4"], state="readonly", width=4)
            cb.pack(side="left")

            def set_num(_e=None):
                n = int(nv.get())
                other = next((c for c in self.model.components if c.kind == "PORT" and c is not sel
                              and int(c.params.get("number", 0)) == n), None)
                self._checkpoint()
                if other is not None:
                    other.params["number"] = sel.params.get("number", 1)
                sel.params["number"] = n
                self._params_changed()
            cb.bind("<<ComboboxSelected>>", set_num)
            ev = tk.BooleanVar(value=sel.params.get("enabled", True))

            def set_en():
                sel.params["enabled"] = bool(ev.get())
                self._params_changed()
            ttk.Checkbutton(box, text=t("rb.f.en"), variable=ev, command=set_en).pack(anchor="w", padx=10)
        for key, lab, unit, sl in FIELD_SPECS.get(sel.kind, []):
            self._field(box, sel, key, t(lab), unit, sl)
        if sel.kind == "TL":
            self.elen_lbl = ttk.Label(box, text="", style="CardBody.TLabel", font=("Segoe UI", 9, "italic"))
            self.elen_lbl.pack(anchor="w", padx=10)
            self._update_elen(sel)
        row = ttk.Frame(box, style="Card.TFrame")
        row.pack(anchor="w", padx=10, pady=(8, 0))
        if sel.p2 is not None:
            ttk.Button(row, text=t("rb.rotate"), style="Small.TButton", command=self.rotate).pack(side="left",
                                                                                                padx=(0, 4))
        ttk.Button(row, text=t("rb.delete"), style="Small.TButton", command=self.delete_selected).pack(side="left")

    def _update_elen(self, c):
        try:
            f = 0.5 * (self.sim_state.sweep["f_start"] + self.sim_state.sweep["f_stop"])
            lam = 3e8 * c.params.get("vf", 1.0) / f
            deg = 360 * c.params.get("length", 0) / lam
            self.elen_lbl.configure(text=t("rb.elen").format(deg=deg, f=format_value(f, "Hz")))
        except Exception:
            pass

    def _field(self, box, comp, key, label, unit, spec):
        lo, hi, lg = spec
        row = ttk.Frame(box, style="Card.TFrame")
        row.pack(fill="x", padx=10, pady=(4, 0))
        ttk.Label(row, text=label, style="CardBody.TLabel").pack(anchor="w")
        r2 = ttk.Frame(box, style="Card.TFrame")
        r2.pack(fill="x", padx=10)
        val = comp.params.get(key, 0.0)
        var = tk.StringVar(value=_fmt(val, unit))
        ent = ttk.Entry(r2, textvariable=var, width=11)
        ent.pack(side="left")
        ttk.Label(r2, text=unit, style="CardBody.TLabel").pack(side="left", padx=(2, 6))
        sc = ttk.Scale(r2, from_=0, to=1000, orient="horizontal", length=150)
        sc.pack(side="left", fill="x", expand=True)
        state = {"lock": False, "snap": False}

        def to_pos(v):
            if lg:
                v = max(v, lo)
                return 1000 * (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo))
            return 1000 * (v - lo) / (hi - lo)

        def from_pos(p):
            p = float(p) / 1000
            if lg:
                return 10 ** (math.log10(lo) + p * (math.log10(hi) - math.log10(lo)))
            return lo + p * (hi - lo)

        def commit(v):
            if not state["snap"]:
                self._checkpoint()
                state["snap"] = True
            comp.params[key] = v
            if comp.kind == "TL" and hasattr(self, "elen_lbl"):
                self._update_elen(comp)
            self._apply_later()

        def on_scale(p):
            if state["lock"]:
                return
            v = from_pos(p)
            v = float(f"{v:.3g}")
            var.set(_fmt(v, unit))
            commit(v)

        def on_type(_e=None):
            try:
                v = parse_value(var.get()) if unit else float(var.get())
            except Exception:
                ent.configure(foreground="#c62828")
                return
            ent.configure(foreground="")
            state["lock"] = True
            sc.set(max(0, min(1000, to_pos(v))))
            state["lock"] = False
            commit(v)
        state["lock"] = True
        try:
            sc.set(max(0, min(1000, to_pos(float(val)))))
        except Exception:
            pass
        state["lock"] = False
        sc.configure(command=on_scale)
        ent.bind("<Return>", on_type)
        ent.bind("<KeyRelease>", lambda e: self.after(400, on_type) if e.keysym not in ("Return",) else None)

    def _render_check(self):
        box = self.check_box
        for w in box.winfo_children():
            w.destroy()
        ttk.Label(box, text=t("rb.check"), font=FONT_H2, style="CardTitle.TLabel").pack(anchor="w", padx=10)
        if not self.model.components:
            ttk.Label(box, text=t("rb.p.noport"), style="CardBody.TLabel", wraplength=290).pack(anchor="w", padx=10)
            return
        problems = []
        inc = self.incidence()
        for p, items in inc.items():
            if len(items) != 1:
                continue
            owner, which = items[0]
            if isinstance(owner, Component):
                if owner.kind in ("GND",):
                    continue
                end = t("rb.p.end") if owner.p2 is None else (t("rb.p.end1") if which == 1 else t("rb.p.end2"))
                problems.append((owner, t("rb.p.dangling").format(c=owner.label(), end=end)))
            else:
                problems.append((owner, t("rb.p.wire")))
        if not any(c.kind == "PORT" for c in self.model.components):
            problems.insert(0, (None, t("rb.p.noport")))
        try:
            self.model.validate_values()
            self.model.build_netlist()
        except ValueError as exc:
            msg = str(exc)
            if not problems or all(m != msg for _, m in problems):
                problems.append((None, msg))
        if not problems:
            ttk.Label(box, text=t("rb.ok"), foreground="#1f9d55", style="CardBody.TLabel", wraplength=290)\
                .pack(anchor="w", padx=10)
            return
        for owner, msg in problems[:8]:
            lab = tk.Label(box, text="• " + msg, fg="#c62828", bg="#FFFFFF", anchor="w", justify="left",
                           wraplength=285, font=("Segoe UI", 9), cursor="hand2" if owner is not None else "")
            lab.pack(anchor="w", padx=10)
            if owner is not None:
                lab.bind("<Button-1>", lambda e, o=owner: self._select(o))

    def _select(self, obj):
        self.selected = obj
        self._render_props()
        self.redraw()

    def _draw_live(self):
        fig = self.live.fig
        fig.clear()
        r = self.sim_state.result
        ok = r is not None and not self._stale()
        if not ok:
            self.live_note.configure(text=t("rb.live_none"))
            self.live.redraw()
            return
        self.live_note.configure(text="")
        ax = fig.add_subplot(111)
        ax.set_facecolor("#fdfaf3")
        f = r.freqs_hz / 1e9
        cols = ["#c9622a", "#2A9D8F", "#6A4C93", "#277DA1"]
        p1 = r.port_numbers[0]
        k = 0
        for q in r.port_numbers[:3]:
            s = r.s_trace(q, p1)
            ax.plot(f, 20 * np.log10(np.maximum(np.abs(s), 1e-9)), color=cols[k % 4], lw=1.6, label=f"S{q}{p1}")
            k += 1
        ax.set_xlabel("GHz", fontsize=7)
        ax.set_ylabel("dB", fontsize=7)
        ax.tick_params(labelsize=7)
        ax.grid(True, alpha=0.3)
        lo = max(-60, ax.get_ylim()[0])
        ax.set_ylim(lo, 3)
        ax.legend(fontsize=7, loc="lower left")
        fig.subplots_adjust(left=0.18, right=0.97, top=0.95, bottom=0.18)
        self.live.redraw()

    def _stale(self):
        return getattr(self, "_is_stale", False)

    def set_stale(self, stale):
        self._is_stale = stale
        self._draw_live()

    # ================================================================ drawing
    def redraw(self):
        c = self.canvas
        c.delete("all")
        W, H = c.winfo_width(), c.winfo_height()
        if W < 10:
            return
        g = self.grid_px
        x = self.ox % g
        while x < W:
            c.create_line(x, 0, x, H, fill=GRID_COLOR_MAJOR if round((x - self.ox) / g) % 5 == 0 else GRID_COLOR)
            x += g
        y = self.oy % g
        while y < H:
            c.create_line(0, y, W, y, fill=GRID_COLOR_MAJOR if round((y - self.oy) / g) % 5 == 0 else GRID_COLOR)
            y += g
        if not self.model.components and not self.model.wires and not self.tool:
            c.create_text(W / 2, H / 2, fill="#6f7a9c", font=("Segoe UI", 12), width=min(560, W - 40),
                          justify="center", text=tr("Drag a Port, some components and a Ground onto the grid — or "
                                                    "pick one of the Examples above.",
                                                    "Trage un Port, câteva componente și o Masă pe grilă — sau alege "
                                                    "unul dintre Exemplele de sus."))
        for w in self.model.wires:
            a, b = self.g2p(w[0]), self.g2p(w[1])
            c.create_line(*a, *b, fill=SELECT_COLOR if self.selected is w else WIRE_COLOR,
                          width=4 if self.selected is w else 2, capstyle="round")
        for comp in self.model.components:
            self._draw_comp(comp)
        self._draw_points()
        d = self.drag
        if d and d["mode"] == "wire":
            a = d["from"]
            b = self.p2g(d["x"], d["y"])
            if a[0] != b[0] and a[1] != b[1]:
                k1, k2 = (b[0], a[1]), (a[0], b[1])
                pts = [a, k1 if self._cost([a, k1, b]) <= self._cost([a, k2, b]) else k2, b]
            else:
                pts = [a, b]
            flat = [v for p in pts for v in self.g2p(p)]
            c.create_line(*flat, fill=SELECT_COLOR, width=2, dash=(6, 3))
            bx, by = self.g2p(b)
            c.create_oval(bx - 5, by - 5, bx + 5, by + 5, outline=SELECT_COLOR, width=2)
        if self.tool == "wire" and self.wire_start is not None and self.ghost:
            a = self.wire_start
            b = self.p2g(*self.ghost)
            pts = [a, (b[0], a[1]), b]
            flat = [v for p in pts for v in self.g2p(p)]
            c.create_line(*flat, fill=SELECT_COLOR, width=2, dash=(6, 3))
        if self.tool and self.tool != "wire" and self.ghost:
            self._draw_ghost()
        if self._show_nodes.get():
            self._draw_node_names()

    def _draw_points(self):
        c = self.canvas
        inc = self.incidence()
        r = max(3, 4 * self.s)
        for p, items in inc.items():
            x, y = self.g2p(p)
            n = len(items)
            if n == 1 and not (isinstance(items[0][0], Component) and items[0][0].kind == "GND"):
                c.create_oval(x - r - 1.5, y - r - 1.5, x + r + 1.5, y + r + 1.5, outline=BAD, width=2)
            elif n >= 3:
                c.create_oval(x - r, y - r, x + r, y + r, fill=WIRE_COLOR, outline="")
            else:
                c.create_oval(x - 2.5, y - 2.5, x + 2.5, y + 2.5, fill=GOOD, outline="")
            if self.hover_pt == p:
                c.create_oval(x - 2 * r, y - 2 * r, x + 2 * r, y + 2 * r, outline=SELECT_COLOR, width=2)

    def _draw_node_names(self):
        try:
            node_of = self.model._resolve_nodes()
        except Exception:
            return
        done = set()
        for p, n in node_of.items():
            if n in done:
                continue
            done.add(n)
            x, y = self.g2p(p)
            self.canvas.create_text(x + 6, y - 10, text=n, fill="#ffd166", font=("Consolas", 8, "bold"), anchor="w")

    def _draw_comp(self, comp):
        c = self.canvas
        sel = self.selected is comp
        color = SELECT_COLOR if sel else COMP_COLOR
        s = self.s
        p1 = self.g2p(comp.p1)
        if comp.kind == "PORT":
            col = SELECT_COLOR if sel else PORT_COLOR
            side = self.port_side(comp)
            cx = p1[0] + side * 30 * s
            r = 10 * s
            c.create_line(cx - side * r, p1[1], p1[0], p1[1], fill=col, width=2)
            c.create_oval(cx - r, p1[1] - r, cx + r, p1[1] + r, outline=col, width=2, fill="#1b2a33")
            c.create_text(cx, p1[1], text=str(comp.params.get("number", "?")), fill=col,
                          font=("Consolas", max(7, int(9 * s)), "bold"))
            en = "" if comp.params.get("enabled", True) else " (off)"
            c.create_text(cx, p1[1] - r - 9, text=f"Port {comp.params.get('number', '?')}{en}", fill=col,
                          font=("Consolas", max(7, int(8 * s)), "bold"))
            c.create_text(cx, p1[1] + r + 9, text=f"{comp.params.get('z0', 50):g} Ω", fill=TEXT_COLOR,
                          font=("Consolas", max(7, int(8 * s))))
            return
        if comp.kind == "GND":
            draw_ground_symbol(c, p1, SELECT_COLOR if sel else GND_COLOR)
            return
        if comp.p2 is None:
            draw_load_symbol(c, comp.kind, p1, color, comp.label(), _value_summary(comp))
            return
        p2 = self.g2p(comp.p2)
        {"R": draw_resistor, "L": draw_inductor, "C": draw_capacitor,
         "TL": draw_transmission_line}[comp.kind](c, p1, p2, color)
        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        horiz = abs(p2[0] - p1[0]) >= abs(p2[1] - p1[1])
        if horiz:
            c.create_text(mx, my - 20, text=comp.label(), fill=TEXT_COLOR, font=("Consolas", 8, "bold"))
            c.create_text(mx, my + 20, text=_value_summary(comp), fill=TEXT_COLOR, font=("Consolas", 8))
        else:
            c.create_text(mx + 16, my - 7, text=comp.label(), fill=TEXT_COLOR, font=("Consolas", 8, "bold"),
                          anchor="w")
            c.create_text(mx + 16, my + 7, text=_value_summary(comp), fill=TEXT_COLOR, font=("Consolas", 8),
                          anchor="w")
        if sel:
            x0, x1 = min(p1[0], p2[0]) - 8, max(p1[0], p2[0]) + 8
            y0, y1 = min(p1[1], p2[1]) - 14, max(p1[1], p2[1]) + 14
            c.create_rectangle(x0, y0, x1, y1, outline=SELECT_COLOR, dash=(4, 3))

    def _draw_ghost(self):
        c = self.canvas
        g = self.p2g(*self.ghost)
        col = "#6ea8ff"
        if self.tool in TWO:
            half = PART_LEN // 2
            a, b = ((g[0] - half, g[1]), (g[0] + half, g[1])) if self.orient == 0 else \
                ((g[0], g[1] - half), (g[0], g[1] + half))
            pa, pb = self.g2p(a), self.g2p(b)
            {"R": draw_resistor, "L": draw_inductor, "C": draw_capacitor,
             "TL": draw_transmission_line}[self.tool](c, pa, pb, col)
            for p in (pa, pb):
                c.create_oval(p[0] - 4, p[1] - 4, p[0] + 4, p[1] + 4, outline=col, width=2)
        else:
            x, y = self.g2p(g)
            if self.tool == "gnd":
                draw_ground_symbol(c, (x, y), col)
            elif self.tool == "port":
                c.create_oval(x - 40 * self.s, y - 10 * self.s, x - 20 * self.s, y + 10 * self.s, outline=col, width=2)
                c.create_line(x - 20 * self.s, y, x, y, fill=col, width=2)
            else:
                draw_load_symbol(c, self.tool, (x, y), col, "", "")
            c.create_oval(x - 4, y - 4, x + 4, y + 4, outline=col, width=2)


def _fmt(v, unit):
    try:
        v = float(v)
    except Exception:
        return str(v)
    if unit in ("", "°") or unit == "Ω" and abs(v) < 1e4 and v == round(v, 3):
        return f"{v:.4g}"
    if unit == "m":
        return f"{v * 1000:.4g}m"
    txt = format_value(v, "").strip()
    return txt.replace(" ", "")


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    if L == 0:
        return math.hypot(px - ax, py - ay)
    u = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return math.hypot(px - ax - u * dx, py - ay - u * dy)


# ---------------------------------------------------------------------------
# Examples. Each builds straight into the model; (f_start, f_stop) in GHz.
# ---------------------------------------------------------------------------
def _port(m, p, n, z0=50.0):
    m.add_component(Component("PORT", p, params={"number": n, "z0": z0, "enabled": True}))


def _two(m, kind, a, b, **params):
    base = dict(DEFAULTS.get(kind, {}))
    base.update(params)
    m.add_component(Component(kind, a, b, base))


def _gnd(m, p):
    m.add_component(Component("GND", p))


def _ex_thru(m):
    _port(m, (0, 0), 1)
    _two(m, "TL", (0, 0), (8, 0), z0=50.0, length=0.0375, vf=1.0)
    _port(m, (12, 0), 2)
    m.add_wire((8, 0), (12, 0))


def _ex_pi(m):
    _port(m, (0, 0), 1)
    m.add_wire((0, 0), (2, 0))
    _two(m, "R", (2, 0), (2, 4), value=150.5)
    _gnd(m, (2, 4))
    _two(m, "R", (2, 0), (6, 0), value=37.35)
    _two(m, "R", (6, 0), (6, 4), value=150.5)
    _gnd(m, (6, 4))
    m.add_wire((6, 0), (10, 0))
    _port(m, (10, 0), 2)


def _ex_lpf(m):
    _port(m, (0, 0), 1)
    m.add_wire((0, 0), (2, 0))
    _two(m, "C", (2, 0), (2, 4), value=1.59e-12)
    _gnd(m, (2, 4))
    _two(m, "L", (2, 0), (6, 0), value=7.96e-9)
    _two(m, "C", (6, 0), (6, 4), value=1.59e-12)
    _gnd(m, (6, 4))
    m.add_wire((6, 0), (10, 0))
    _port(m, (10, 0), 2)


def _ex_rlc(m):
    _port(m, (0, 0), 1)
    _two(m, "R", (0, 0), (4, 0), value=5.0)
    _two(m, "L", (4, 0), (8, 0), value=10e-9)
    _two(m, "C", (8, 0), (12, 0), value=0.633e-12)
    _port(m, (16, 0), 2)
    m.add_wire((12, 0), (16, 0))


def _ex_lmatch(m):
    _port(m, (0, 0), 1)
    _two(m, "L", (0, 0), (4, 0), value=6.89e-9)
    _two(m, "C", (6, 0), (6, 4), value=0.689e-12)
    _gnd(m, (6, 4))
    m.add_wire((4, 0), (10, 0))
    m.add_component(Component("LOAD_R", (10, 0), params={"value": 200.0}))


def _ex_qwt(m):
    _port(m, (0, 0), 1)
    _two(m, "TL", (0, 0), (8, 0), z0=70.7, length=0.0375, vf=1.0)
    m.add_component(Component("LOAD_R", (8, 0), params={"value": 100.0}))


def _ex_stub(m):
    _port(m, (0, 0), 1)
    m.add_wire((0, 0), (12, 0))
    _port(m, (12, 0), 2)
    _two(m, "TL", (6, 0), (6, 6), z0=50.0, length=0.0375, vf=1.0)
    m.add_component(Component("OPEN", (6, 6)))


def _ex_split(m):
    _port(m, (0, 0), 1)
    _two(m, "R", (0, 0), (4, 0), value=16.67)
    m.add_wire((4, 0), (4, -3))
    m.add_wire((4, 0), (4, 3))
    _two(m, "R", (4, -3), (8, -3), value=16.67)
    _two(m, "R", (4, 3), (8, 3), value=16.67)
    m.add_wire((8, -3), (12, -3))
    m.add_wire((8, 3), (12, 3))
    _port(m, (12, -3), 2)
    _port(m, (12, 3), 3)


EXAMPLES = {
    "thru": (_ex_thru, (0.5, 4.0)), "pi": (_ex_pi, (0.1, 3.0)), "lpf": (_ex_lpf, (0.1, 6.0)),
    "rlc": (_ex_rlc, (1.0, 3.0)), "lmatch": (_ex_lmatch, (1.0, 3.0)), "qwt": (_ex_qwt, (0.5, 4.0)),
    "stub": (_ex_stub, (0.5, 4.0)), "split": (_ex_split, (0.1, 3.0)),
}
