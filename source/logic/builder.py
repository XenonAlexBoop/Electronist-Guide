"""
logic/builder.py - Logic Circuit Builder (v6, rebuilt for ease of use).

What changed compared with the first builder:
  * No separate Wire tool needed: press on ANY pin (the round dots) and drag
    to another pin. Compatible pins light up green while you drag; drop
    anywhere near one and it snaps. Works from outputs or from inputs.
  * Parts can be dragged straight from the palette onto the grid, or
    clicked once and placed with one click (the tool then goes back to
    Select by itself - hold Shift to keep placing the same part).
  * Click a switch to toggle it; drag a part to move it; drag empty space
    to pan; mouse wheel to zoom; right-click for a menu.
  * Undo / Redo (Ctrl+Z / Ctrl+Y), duplicate (Ctrl+D), Delete key.
  * Floating (unconnected) inputs are drawn as red rings and listed.
  * Live truth table of the whole circuit - click a row to set the
    switches - plus the minimized Boolean expression of every output.
  * Ready-made examples (adders, decoder, mux, NAND-only XOR ...),
    save / open circuits as .json files.
"""
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from i18n import t, register, tr
from widgets import ScrollableFrame, FONT_BODY, FONT_H2, FONT_MONO
from drawing import draw_gate_symbol
from logic.circuit_model import LogicCircuitModel, LogicComponent, GATE_KINDS, MUX_DEMUX_KINDS
from logic.truthtable import TruthTable
from logic import minimize as qm

register({
    "lb.intro": ("Drag parts from the list onto the grid. Press on a pin (a round dot) and drag to another pin to "
                 "connect them. Click a switch to flip it — every wire and output updates instantly.",
                 "Trage piesele din listă pe grilă. Apasă pe un pin (punct rotund) și trage până la alt pin ca să-i "
                 "conectezi. Apasă pe un întrerupător ca să-l comuți — toate firele și ieșirile se actualizează "
                 "instant."),
    "lb.undo": ("↶ Undo", "↶ Anulează"), "lb.redo": ("↷ Redo", "↷ Refă"),
    "lb.delete": ("✕ Delete", "✕ Șterge"), "lb.dup": ("⧉ Duplicate", "⧉ Duplică"),
    "lb.clear": ("Clear all", "Golește tot"), "lb.fit": ("Fit", "Încadrează"),
    "lb.examples": ("Examples…", "Exemple…"), "lb.save": ("Save…", "Salvează…"), "lb.open": ("Open…", "Deschide…"),
    "lb.ex.half": ("Half adder", "Semisumator"), "lb.ex.full": ("Full adder", "Sumator complet"),
    "lb.ex.nandxor": ("XOR from 4 NAND gates", "XOR din 4 porți NAND"),
    "lb.ex.mux": ("2-to-1 multiplexer from gates", "Multiplexor 2→1 din porți"),
    "lb.ex.major": ("Majority vote (2 of 3)", "Vot majoritar (2 din 3)"),
    "lb.ex.dec": ("2-to-4 decoder", "Decodor 2→4"),
    "lb.ex.cmp": ("1-bit comparator", "Comparator pe 1 bit"),
    "lb.ex.demorgan": ("De Morgan check", "Verificare De Morgan"),
    "lb.parts": ("Parts", "Piese"),
    "lb.parts_hint": ("Drag onto the grid, or click then click the grid.",
                      "Trage pe grilă sau apasă, apoi apasă pe grilă."),
    "lb.g.io": ("Inputs & outputs", "Intrări și ieșiri"), "lb.g.gates": ("Gates", "Porți"),
    "lb.g.mux": ("Mux / Demux", "Mux / Demux"),
    "lb.h.idle": ("Drag from a pin to another pin to wire · click a switch to toggle · drag empty space to pan · "
                  "wheel = zoom · right-click = menu",
                  "Trage de la un pin la altul pentru fir · apasă un întrerupător ca să-l comuți · trage spațiul gol "
                  "pentru deplasare · rotița = zoom · click dreapta = meniu"),
    "lb.h.place": ("Click on the grid to place the {p}. Esc = cancel, Shift+click = place several.",
                   "Apasă pe grilă ca să plasezi {p}. Esc = renunță, Shift+click = plasează mai multe."),
    "lb.h.wiring": ("Release on a green pin to connect.", "Eliberează pe un pin verde ca să conectezi."),
    "lb.h.pin": ("{c} · {io} {p} = {v}", "{c} · {io} {p} = {v}"),
    "lb.in": ("input", "intrare"), "lb.out": ("output", "ieșire"),
    "lb.float": ("floating", "flotant"),
    "lb.msg.replaced": ("That input already had a wire — it was replaced (an input can have only one driver).",
                        "Intrarea avea deja un fir — a fost înlocuit (o intrare poate avea un singur semnal)."),
    "lb.msg.same": ("Connect an OUTPUT to an INPUT of another part.", "Conectează o IEȘIRE la o INTRARE a altei piese."),
    "lb.msg.loop": ("⚠ Feedback loop: a gate's output reaches its own input — shown as unknown (?).",
                    "⚠ Buclă de reacție: ieșirea unei porți ajunge la propria intrare — afișată ca necunoscută (?)."),
    "lb.props": ("Selected part", "Piesa selectată"),
    "lb.none": ("Nothing selected — click a part.", "Nimic selectat — apasă pe o piesă."),
    "lb.label": ("Label", "Etichetă"),
    "lb.check": ("Circuit check", "Verificarea circuitului"),
    "lb.ok": ("✓ Every input pin is connected.", "✓ Toți pinii de intrare sunt conectați."),
    "lb.floating_n": ("{n} input pin(s) not connected (red rings):", "{n} pin(i) de intrare neconectați (cercuri roșii):"),
    "lb.tt": ("Truth table", "Tabel de adevăr"),
    "lb.tt_hint": ("Click a row to set the switches.", "Apasă un rând ca să setezi întrerupătoarele."),
    "lb.tt_need": ("Add input switches and output probes to see the truth table.",
                   "Adaugă întrerupătoare de intrare și sonde de ieșire ca să vezi tabelul de adevăr."),
    "lb.tt_many": ("Too many inputs for a table (max 6).", "Prea multe intrări pentru tabel (max 6)."),
    "lb.expr": ("Simplest expression", "Expresia cea mai simplă"),
    "lb.m.delete": ("Delete", "Șterge"), "lb.m.dup": ("Duplicate", "Duplică"), "lb.m.toggle": ("Toggle 0/1", "Comută 0/1"),
    "lb.m.rename": ("Rename…", "Redenumește…"), "lb.m.disconnect": ("Disconnect all wires", "Deconectează toate firele"),
    "lb.clear_confirm": ("Remove every part and wire?", "Ștergi toate piesele și firele?"),
    "lb.file_err": ("Could not open that file.", "Fișierul nu a putut fi deschis."),
})

BG = "#ffffff"
GRID = "#eef0f3"
GRID_MAJOR = "#dfe3ea"
BODY = "#f5f0e2"
OUTLINE = "#333333"
SEL = "#e08a2b"
TEXT = "#555555"
HIGH = "#1f9d55"
LOW = "#9aa0a8"
FLOAT = "#c3c7cf"
PIN_OK = "#2f6fdd"
PIN_BAD = "#d64545"
GOOD = "#22b35e"

BASE = 24          # grid px at 100 %
STUB = 18          # length of pin leads (px at 100 %)
GATE_W, GATE_H = 96, 64

PALETTE = [
    ("io", ["INPUT", "OUTPUT", "NODE"]),
    ("gates", ["NOT", "AND", "OR", "NAND", "NOR", "XOR", "XNOR"]),
    ("mux", ["MUX2", "MUX4", "DEMUX2", "DEMUX4"]),
]
TOOL_KEYS = {"INPUT": "logic.tool.input", "OUTPUT": "logic.tool.output", "NODE": "logic.tool.node",
             "NOT": "logic.tool.not_", "AND": "logic.tool.and_", "OR": "logic.tool.or_",
             "NAND": "logic.tool.nand", "NOR": "logic.tool.nor", "XOR": "logic.tool.xor",
             "XNOR": "logic.tool.xnor", "MUX2": "logic.tool.mux2", "MUX4": "logic.tool.mux4",
             "DEMUX2": "logic.tool.demux2", "DEMUX4": "logic.tool.demux4"}

# local geometry (px at 100 %): body box (x0, y0, x1, y1) and pins name -> (x, y)
_MUX = {
    "MUX2": (70, 90, {"I0": 15, "I1": 75}, {"S": 35}, {"Y": 45}),
    "MUX4": (70, 150, {"I0": 15, "I1": 55, "I2": 95, "I3": 135}, {"S0": 23, "S1": 47}, {"Y": 75}),
    "DEMUX2": (70, 90, {"D": 45}, {"S": 35}, {"O0": 15, "O1": 75}),
    "DEMUX4": (70, 150, {"D": 75}, {"S0": 23, "S1": 47}, {"O0": 15, "O1": 55, "O2": 95, "O3": 135}),
}


def geometry(kind):
    """Returns (bbox, in_pins, out_pins, size) in unscaled local px.
    Pins are the OUTER ends of the pin leads - that is where wires attach."""
    if kind in GATE_KINDS:
        n = 1 if kind == "NOT" else 2
        ys = [GATE_H / 2] if n == 1 else [GATE_H * 0.28, GATE_H * 0.72]
        ins = {("A", "B")[i]: (0, y) for i, y in enumerate(ys)}
        return (0, 0, GATE_W, GATE_H), ins, {"Y": (GATE_W, GATE_H / 2)}, (GATE_W, GATE_H)
    if kind == "INPUT":
        return (0, 0, 56, 30), {}, {"Y": (56 + STUB, 15)}, (56 + STUB, 30)
    if kind == "OUTPUT":
        return (STUB, 0, STUB + 30, 30), {"A": (0, 15)}, {}, (STUB + 30, 30)
    if kind == "NODE":
        return (0, 0, 24, 24), {"A": (0, 12)}, {"Y": (24, 12)}, (24, 24)
    w, h, left, bottom, right = _MUX[kind]
    ins = {n: (0, y) for n, y in left.items()}
    ins.update({n: (STUB + x, h + STUB) for n, x in bottom.items()})
    outs = {n: (STUB + w + STUB, y) for n, y in right.items()}
    return (STUB, 0, STUB + w, h), ins, outs, (STUB + w + STUB, h + STUB)


def serialize(model):
    return {"components": [{"id": c.id, "kind": c.kind, "pos": list(c.pos), "params": dict(c.params)}
                           for c in model.components],
            "wires": [{"src": list(w["src"]), "dst": list(w["dst"])} for w in model.wires]}


def deserialize(model, data):
    model.clear()
    mx = 0
    for d in data.get("components", []):
        c = LogicComponent(d["kind"], tuple(d["pos"]), d.get("params"))
        c.id = int(d["id"])
        mx = max(mx, c.id)
        model.add_component(c)
    LogicComponent._next_id = max(LogicComponent._next_id, mx + 1)
    for w in data.get("wires", []):
        model.wires.append({"src": tuple(w["src"]), "dst": tuple(w["dst"])})


# ---------------------------------------------------------------------------
# Examples: parts as (key, kind, (gx, gy), label), wires as (key.pin, key.pin)
# ---------------------------------------------------------------------------
EXAMPLES = {
    "half": ([("A", "INPUT", (0, 0), "A"), ("B", "INPUT", (0, 5), "B"),
              ("x", "XOR", (6, -1), ""), ("a", "AND", (6, 4), ""),
              ("S", "OUTPUT", (12, 0), "S"), ("C", "OUTPUT", (12, 5), "C")],
             [("A.Y", "x.A"), ("B.Y", "x.B"), ("A.Y", "a.A"), ("B.Y", "a.B"), ("x.Y", "S.A"), ("a.Y", "C.A")]),
    "full": ([("A", "INPUT", (0, 0), "A"), ("B", "INPUT", (0, 3), "B"), ("Ci", "INPUT", (0, 8), "Cin"),
              ("x1", "XOR", (5, 0), ""), ("x2", "XOR", (11, 2), ""), ("a1", "AND", (11, 6), ""),
              ("a2", "AND", (5, 9), ""), ("o", "OR", (17, 7), ""),
              ("S", "OUTPUT", (17, 3), "S"), ("Co", "OUTPUT", (23, 8), "Cout")],
             [("A.Y", "x1.A"), ("B.Y", "x1.B"), ("x1.Y", "x2.A"), ("Ci.Y", "x2.B"), ("x1.Y", "a1.A"),
              ("Ci.Y", "a1.B"), ("A.Y", "a2.A"), ("B.Y", "a2.B"), ("a1.Y", "o.A"), ("a2.Y", "o.B"),
              ("x2.Y", "S.A"), ("o.Y", "Co.A")]),
    "nandxor": ([("A", "INPUT", (0, 0), "A"), ("B", "INPUT", (0, 7), "B"),
                 ("n1", "NAND", (5, 3), ""), ("n2", "NAND", (11, 0), ""), ("n3", "NAND", (11, 6), ""),
                 ("n4", "NAND", (17, 3), ""), ("Y", "OUTPUT", (23, 4), "Y")],
                [("A.Y", "n1.A"), ("B.Y", "n1.B"), ("A.Y", "n2.A"), ("n1.Y", "n2.B"), ("n1.Y", "n3.A"),
                 ("B.Y", "n3.B"), ("n2.Y", "n4.A"), ("n3.Y", "n4.B"), ("n4.Y", "Y.A")]),
    "mux": ([("A", "INPUT", (0, 0), "A"), ("B", "INPUT", (0, 5), "B"), ("S", "INPUT", (0, 10), "S"),
             ("n", "NOT", (5, 9), ""), ("a1", "AND", (11, 0), ""), ("a2", "AND", (11, 6), ""),
             ("o", "OR", (17, 3), ""), ("Y", "OUTPUT", (23, 4), "Y")],
            [("A.Y", "a1.A"), ("S.Y", "n.A"), ("n.Y", "a1.B"), ("B.Y", "a2.A"), ("S.Y", "a2.B"),
             ("a1.Y", "o.A"), ("a2.Y", "o.B"), ("o.Y", "Y.A")]),
    "major": ([("A", "INPUT", (0, 0), "A"), ("B", "INPUT", (0, 5), "B"), ("C", "INPUT", (0, 10), "C"),
               ("a1", "AND", (6, -1), ""), ("a2", "AND", (6, 4), ""), ("a3", "AND", (6, 9), ""),
               ("o1", "OR", (12, 1), ""), ("o2", "OR", (17, 5), ""), ("Y", "OUTPUT", (23, 6), "Y")],
              [("A.Y", "a1.A"), ("B.Y", "a1.B"), ("A.Y", "a2.A"), ("C.Y", "a2.B"), ("B.Y", "a3.A"),
               ("C.Y", "a3.B"), ("a1.Y", "o1.A"), ("a2.Y", "o1.B"), ("o1.Y", "o2.A"), ("a3.Y", "o2.B"),
               ("o2.Y", "Y.A")]),
    "dec": ([("A", "INPUT", (0, 0), "A1"), ("B", "INPUT", (0, 8), "A0"),
             ("nA", "NOT", (5, 2), ""), ("nB", "NOT", (5, 10), ""),
             ("y0", "AND", (12, -1), ""), ("y1", "AND", (12, 4), ""), ("y2", "AND", (12, 9), ""),
             ("y3", "AND", (12, 14), ""),
             ("Y0", "OUTPUT", (18, 0), "Y0"), ("Y1", "OUTPUT", (18, 5), "Y1"), ("Y2", "OUTPUT", (18, 10), "Y2"),
             ("Y3", "OUTPUT", (18, 15), "Y3")],
            [("A.Y", "nA.A"), ("B.Y", "nB.A"), ("nA.Y", "y0.A"), ("nB.Y", "y0.B"), ("nA.Y", "y1.A"),
             ("B.Y", "y1.B"), ("A.Y", "y2.A"), ("nB.Y", "y2.B"), ("A.Y", "y3.A"), ("B.Y", "y3.B"),
             ("y0.Y", "Y0.A"), ("y1.Y", "Y1.A"), ("y2.Y", "Y2.A"), ("y3.Y", "Y3.A")]),
    "cmp": ([("A", "INPUT", (0, 0), "A"), ("B", "INPUT", (0, 9), "B"),
             ("nA", "NOT", (5, 7), ""), ("nB", "NOT", (5, 2), ""),
             ("gt", "AND", (11, -1), ""), ("eq", "XNOR", (11, 4), ""), ("lt", "AND", (11, 9), ""),
             ("G", "OUTPUT", (17, 0), "A>B"), ("E", "OUTPUT", (17, 5), "A=B"), ("L", "OUTPUT", (17, 10), "A<B")],
            [("A.Y", "nA.A"), ("B.Y", "nB.A"), ("A.Y", "gt.A"), ("nB.Y", "gt.B"), ("A.Y", "eq.A"),
             ("B.Y", "eq.B"), ("nA.Y", "lt.A"), ("B.Y", "lt.B"), ("gt.Y", "G.A"), ("eq.Y", "E.A"),
             ("lt.Y", "L.A")]),
    "demorgan": ([("A", "INPUT", (0, 0), "A"), ("B", "INPUT", (0, 7), "B"),
                  ("n", "NAND", (6, 0), ""), ("na", "NOT", (6, 5), ""), ("nb", "NOT", (6, 9), ""),
                  ("o", "OR", (12, 6), ""),
                  ("Y1", "OUTPUT", (12, 1), "(AB)'"), ("Y2", "OUTPUT", (18, 7), "A'+B'")],
                 [("A.Y", "n.A"), ("B.Y", "n.B"), ("A.Y", "na.A"), ("B.Y", "nb.A"), ("na.Y", "o.A"),
                  ("nb.Y", "o.B"), ("n.Y", "Y1.A"), ("o.Y", "Y2.A")]),
}


class LogicBuilderView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.model = LogicCircuitModel()
        self.grid_px = BASE
        self.ox, self.oy = 60, 50
        self.tool = None                 # None = select; otherwise a part kind being placed
        self.selected = None
        self.drag = None
        self.hover_pin = None
        self.ghost = None                # (px, py) while placing
        self.pin_values = {}
        self.eval_error = None
        self.undo_stack, self.redo_stack = [], []
        self._palette_drag = None
        self._flash_job = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)
        ttk.Label(self, text=t("lb.intro"), style="CardBody.TLabel", wraplength=1200, justify="left")\
            .grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 0))
        self._build_toolbar()
        body = ttk.Frame(self, style="Tab.TFrame")
        body.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 8))
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        pal = ttk.Frame(body, style="Card.TFrame", width=228)
        pal.grid(row=0, column=0, sticky="nsw")
        pal.grid_propagate(False)
        cv_holder = ttk.Frame(body, style="Tab.TFrame")
        cv_holder.grid(row=0, column=1, sticky="nsew", padx=6)
        side = ttk.Frame(body, style="Card.TFrame", width=300)
        side.grid(row=0, column=2, sticky="nse")
        side.grid_propagate(False)
        self._build_palette(pal)
        self._build_canvas(cv_holder)
        self._build_side(side)
        self.status = ttk.Label(self, text=t("lb.h.idle"), style="CardBody.TLabel", font=("Segoe UI", 9, "italic"))
        self.status.grid(row=3, column=0, sticky="w", padx=12, pady=(0, 6))
        self._recompute()

    # ------------------------------------------------------------------ UI
    def _build_toolbar(self):
        bar = ttk.Frame(self, style="Tab.TFrame")
        bar.grid(row=1, column=0, sticky="ew", padx=10, pady=6)

        def btn(key, cmd):
            b = ttk.Button(bar, text=t(key), style="Small.TButton", command=cmd)
            b.pack(side="left", padx=(0, 4))
            return b
        btn("lb.undo", self.undo)
        btn("lb.redo", self.redo)
        btn("lb.delete", self._delete_selected)
        btn("lb.dup", self._duplicate)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        self.ex_var = tk.StringVar(value=t("lb.examples"))
        names = {t("lb.ex." + k): k for k in EXAMPLES}
        self._ex_names = names
        cb = ttk.Combobox(bar, textvariable=self.ex_var, values=list(names), state="readonly", width=28)
        cb.pack(side="left", padx=(0, 4))
        cb.bind("<<ComboboxSelected>>", lambda e: self._load_example(names.get(self.ex_var.get())))
        btn("lb.open", self._open)
        btn("lb.save", self._save)
        ttk.Separator(bar, orient="vertical").pack(side="left", fill="y", padx=6)
        ttk.Button(bar, text="−", width=3, style="Small.TButton", command=lambda: self._zoom(1 / 1.2)).pack(side="left")
        self.zoom_lbl = ttk.Label(bar, text="100%", width=6, anchor="center", style="CardBody.TLabel")
        self.zoom_lbl.pack(side="left")
        ttk.Button(bar, text="+", width=3, style="Small.TButton", command=lambda: self._zoom(1.2)).pack(side="left")
        btn("lb.fit", self._fit).pack_configure(padx=(6, 4))
        btn("lb.clear", self._clear)
        self.msg = ttk.Label(bar, text="", style="CardBody.TLabel", foreground="#b3413a",
                             font=("Segoe UI", 9, "bold"))
        self.msg.pack(side="left", padx=10)

    def _build_palette(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)
        ttk.Label(parent, text=t("lb.parts"), font=FONT_H2, style="CardTitle.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=8, pady=(8, 0))
        sf = ScrollableFrame(parent, style="Card.TFrame")
        sf.grid(row=1, column=0, sticky="nsew")
        body = sf.body
        ttk.Label(body, text=t("lb.parts_hint"), font=("Segoe UI", 8), style="CardBody.TLabel",
                  wraplength=205, justify="left").pack(anchor="w", padx=8, pady=(0, 4))
        self.pal_items = {}
        for grp, kinds in PALETTE:
            ttk.Label(body, text=t("lb.g." + grp), font=("Segoe UI", 9, "bold"), style="CardSub.TLabel")\
                .pack(anchor="w", padx=8, pady=(6, 2))
            for kind in kinds:
                row = tk.Frame(body, bg="#f4f4f4", cursor="hand2")
                row.pack(fill="x", padx=6, pady=1)
                ic = tk.Canvas(row, width=34, height=24, bg="#f4f4f4", highlightthickness=0, cursor="hand2")
                ic.pack(side="left", padx=(3, 4), pady=2)
                _palette_icon(ic, kind)
                lab = tk.Label(row, text=t(TOOL_KEYS[kind]), bg="#f4f4f4", fg="#222", anchor="w",
                               font=FONT_BODY, cursor="hand2")
                lab.pack(side="left", fill="x", expand=True)
                for w in (row, ic, lab):
                    w.bind("<ButtonPress-1>", lambda e, k=kind: self._pal_press(e, k))
                    w.bind("<B1-Motion>", self._pal_motion)
                    w.bind("<ButtonRelease-1>", self._pal_release)
                self.pal_items[kind] = (row, ic, lab)

    def _paint_palette(self):
        for kind, ws in self.pal_items.items():
            col = "#dbe6ff" if kind == self.tool else "#f4f4f4"
            for w in ws:
                w.configure(bg=col)

    def _build_canvas(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        c = tk.Canvas(parent, bg=BG, highlightthickness=1, highlightbackground="#ccd")
        c.grid(row=0, column=0, sticky="nsew")
        self.canvas = c
        c.bind("<Configure>", lambda e: self.redraw())
        c.bind("<ButtonPress-1>", self._press)
        c.bind("<B1-Motion>", self._motion)
        c.bind("<ButtonRelease-1>", self._release)
        c.bind("<Motion>", self._hover)
        c.bind("<Leave>", lambda e: self._set_ghost(None))
        c.bind("<ButtonPress-2>", self._pan_start)
        c.bind("<B2-Motion>", self._pan_move)
        c.bind("<ButtonPress-3>", self._context)
        c.bind("<MouseWheel>", lambda e: self._zoom(1.1 if e.delta > 0 else 1 / 1.1, e))
        c.bind("<Button-4>", lambda e: self._zoom(1.1, e))
        c.bind("<Button-5>", lambda e: self._zoom(1 / 1.1, e))
        c.bind("<Enter>", lambda e: c.focus_set())
        for seq, fn in (("<Delete>", self._delete_selected), ("<BackSpace>", self._delete_selected),
                        ("<Escape>", self._cancel), ("<Control-z>", self.undo), ("<Control-y>", self.redo),
                        ("<Control-Z>", self.redo), ("<Control-d>", self._duplicate)):
            c.bind(seq, lambda e, f=fn: f())

    def _build_side(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)
        sf = ScrollableFrame(parent, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        self.side = sf.body
        self.props_box = ttk.Frame(self.side, style="Card.TFrame")
        self.props_box.pack(fill="x")
        self.check_box = ttk.Frame(self.side, style="Card.TFrame")
        self.check_box.pack(fill="x", pady=(8, 0))
        ttk.Label(self.side, text=t("lb.tt"), font=FONT_H2, style="CardTitle.TLabel")\
            .pack(anchor="w", padx=10, pady=(10, 0))
        self.tt_note = ttk.Label(self.side, text="", font=("Segoe UI", 8), style="CardBody.TLabel",
                                 wraplength=270, justify="left")
        self.tt_note.pack(anchor="w", padx=10)
        self.tt = ttk.Treeview(self.side, show="headings", height=8, selectmode="browse")
        self.tt.pack(fill="x", padx=8, pady=4)
        self.tt.tag_configure("cur", background="#d9f2e3")
        self.tt.bind("<<TreeviewSelect>>", self._tt_pick)
        ttk.Label(self.side, text=t("lb.expr"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel")\
            .pack(anchor="w", padx=10, pady=(6, 0))
        self.expr_lbl = ttk.Label(self.side, text="", font=("Consolas", 10), style="CardBody.TLabel",
                                  wraplength=270, justify="left")
        self.expr_lbl.pack(anchor="w", padx=10, pady=(0, 12))
        self._tt_inputs = []
        self._tt_lock = False

    # ------------------------------------------------------------ geometry
    @property
    def s(self):
        return self.grid_px / BASE

    def g2p(self, g):
        return self.ox + g[0] * self.grid_px, self.oy + g[1] * self.grid_px

    def p2g(self, x, y):
        return round((x - self.ox) / self.grid_px), round((y - self.oy) / self.grid_px)

    def pins(self, comp):
        ax, ay = self.g2p(comp.pos)
        s = self.s
        _, ins, outs, _ = geometry(comp.kind)
        return ({n: (ax + x * s, ay + y * s) for n, (x, y) in ins.items()},
                {n: (ax + x * s, ay + y * s) for n, (x, y) in outs.items()})

    def bbox(self, comp):
        ax, ay = self.g2p(comp.pos)
        w, h = geometry(comp.kind)[3]
        return ax, ay, ax + w * self.s, ay + h * self.s

    def hit_pin(self, x, y, tol=None):
        tol = tol or max(10, 11 * self.s)
        best, bd = None, tol
        for comp in reversed(self.model.components):
            ins, outs = self.pins(comp)
            for name, (px, py) in ins.items():
                d = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
                if d < bd:
                    best, bd = (comp, name, False), d
            for name, (px, py) in outs.items():
                d = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
                if d < bd:
                    best, bd = (comp, name, True), d
        return best

    def hit_comp(self, x, y):
        for comp in reversed(self.model.components):
            x0, y0, x1, y1 = self.bbox(comp)
            if x0 - 3 <= x <= x1 + 3 and y0 - 3 <= y <= y1 + 3:
                return comp
        return None

    def route(self, sx, sy, dx, dy, lane=0):
        g = self.grid_px
        if dx >= sx + g:
            # the vertical run sits just before the destination pin; each input
            # pin of a part gets its own lane so parallel wires don't overlap
            mid = dx - g * (0.75 + 0.5 * lane)
            if mid <= sx + g * 0.4:
                mid = (sx + dx) / 2
            return [sx, sy, mid, sy, mid, dy, dx, dy]
        # backwards: go round
        ymid = (sy + dy) / 2 if abs(sy - dy) > 2 * g else max(sy, dy) + 2 * g
        return [sx, sy, sx + g / 2, sy, sx + g / 2, ymid, dx - g / 2, ymid, dx - g / 2, dy, dx, dy]

    def wire_pts(self, w):
        a = self.model.get_component(w["src"][0])
        b = self.model.get_component(w["dst"][0])
        if a is None or b is None:
            return None
        s = self.pins(a)[1].get(w["src"][1])
        d = self.pins(b)[0].get(w["dst"][1])
        if s is None or d is None:
            return None
        names = b.input_pins()
        lane = names.index(w["dst"][1]) if w["dst"][1] in names else 0
        if b.kind in MUX_DEMUX_KINDS or b.kind == "OUTPUT":
            lane = 0
        return self.route(s[0], s[1], d[0], d[1], lane)

    def hit_wire(self, x, y, tol=6):
        for w in reversed(self.model.wires):
            pts = self.wire_pts(w)
            if not pts:
                continue
            for i in range(0, len(pts) - 2, 2):
                if _seg_dist(x, y, pts[i], pts[i + 1], pts[i + 2], pts[i + 3]) < tol:
                    return w
        return None

    # ------------------------------------------------------------ history
    def _checkpoint(self):
        self.undo_stack.append(json.dumps(serialize(self.model)))
        self.undo_stack = self.undo_stack[-100:]
        self.redo_stack.clear()

    def undo(self):
        if not self.undo_stack:
            return
        self.redo_stack.append(json.dumps(serialize(self.model)))
        deserialize(self.model, json.loads(self.undo_stack.pop()))
        self.selected = None
        self._changed()

    def redo(self):
        if not self.redo_stack:
            return
        self.undo_stack.append(json.dumps(serialize(self.model)))
        deserialize(self.model, json.loads(self.redo_stack.pop()))
        self.selected = None
        self._changed()

    # ------------------------------------------------------------ editing
    def _next_label(self, kind):
        used = {c.params.get("label") for c in self.model.components}
        if kind == "INPUT":
            for ch in "ABCDEFGHJKLMNPQRSTUVW":
                if ch not in used:
                    return ch
        if kind == "OUTPUT":
            for lab in ["Y"] + [f"Y{i}" for i in range(1, 30)]:
                if lab not in used:
                    return lab
        return ""

    def place(self, kind, x, y):
        w, h = geometry(kind)[3]
        gx, gy = self.p2g(x - w * self.s / 2, y - h * self.s / 2)
        self._checkpoint()
        comp = LogicComponent(kind, (gx, gy))
        comp.params["label"] = self._next_label(kind)
        self.model.add_component(comp)
        self.selected = comp
        self._changed()
        return comp

    def connect(self, a, b):
        """a, b = (comp, pin, is_out). Returns True when a wire was made."""
        if a[2] == b[2] or a[0] is b[0]:
            self._flash(t("lb.msg.same"))
            return False
        src, dst = (a, b) if a[2] else (b, a)
        self._checkpoint()
        replaced = self.model.wire_to(dst[0].id, dst[1]) is not None
        self.model.add_wire((src[0].id, src[1]), (dst[0].id, dst[1]))
        if replaced:
            self._flash(t("lb.msg.replaced"))
        self._changed()
        return True

    def _delete_selected(self):
        sel = self.selected
        if sel is None:
            return
        self._checkpoint()
        if isinstance(sel, LogicComponent):
            self.model.remove_component(sel)
        else:
            self.model.remove_wire(sel)
        self.selected = None
        self._changed()

    def _duplicate(self):
        sel = self.selected
        if not isinstance(sel, LogicComponent):
            return
        self._checkpoint()
        c = LogicComponent(sel.kind, (sel.pos[0] + 2, sel.pos[1] + 2), dict(sel.params))
        if sel.kind in ("INPUT", "OUTPUT"):
            c.params["label"] = self._next_label(sel.kind)
        self.model.add_component(c)
        self.selected = c
        self._changed()

    def _clear(self):
        if not self.model.components:
            return
        if not messagebox.askyesno(t("logic.error.title"), t("lb.clear_confirm")):
            return
        self._checkpoint()
        self.model.clear()
        self.selected = None
        self._changed()

    def _load_example(self, key):
        if not key:
            return
        parts, wires = EXAMPLES[key]
        self._checkpoint()
        self.model.clear()
        ids = {}
        for k, kind, pos, label in parts:
            c = LogicComponent(kind, pos)
            c.params["label"] = label
            self.model.add_component(c)
            ids[k] = c
        for a, b in wires:
            ka, pa = a.split(".")
            kb, pb = b.split(".")
            self.model.add_wire((ids[ka].id, pa), (ids[kb].id, pb))
        self.selected = None
        self._changed()
        self.after(30, self._fit)
        self.ex_var.set(t("lb.examples"))

    def _save(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("Logic circuit", "*.json")])
        if not path:
            return
        with open(path, "w", encoding="utf-8") as f:
            json.dump(serialize(self.model), f, indent=1)

    def _open(self):
        path = filedialog.askopenfilename(filetypes=[("Logic circuit", "*.json"), ("All", "*.*")])
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self._checkpoint()
            deserialize(self.model, data)
        except Exception:
            messagebox.showerror(t("logic.error.title"), t("lb.file_err"))
            return
        self.selected = None
        self._changed()
        self.after(30, self._fit)

    # ------------------------------------------------------------ palette drag & drop
    def _pal_press(self, e, kind):
        self._palette_drag = (kind, e.x_root, e.y_root, False)

    def _pal_motion(self, e):
        if not self._palette_drag:
            return
        kind, x0, y0, moved = self._palette_drag
        if abs(e.x_root - x0) + abs(e.y_root - y0) > 6:
            self._palette_drag = (kind, x0, y0, True)
            self.tool = kind
            self._paint_palette()
            cx = e.x_root - self.canvas.winfo_rootx()
            cy = e.y_root - self.canvas.winfo_rooty()
            inside = 0 <= cx <= self.canvas.winfo_width() and 0 <= cy <= self.canvas.winfo_height()
            self._set_ghost((cx, cy) if inside else None)

    def _pal_release(self, e):
        if not self._palette_drag:
            return
        kind, x0, y0, moved = self._palette_drag
        self._palette_drag = None
        cx = e.x_root - self.canvas.winfo_rootx()
        cy = e.y_root - self.canvas.winfo_rooty()
        if moved:
            if 0 <= cx <= self.canvas.winfo_width() and 0 <= cy <= self.canvas.winfo_height():
                self.place(kind, cx, cy)
            self._set_tool(None)
        else:
            self._set_tool(kind)          # click: arm the tool, then click the grid

    def _set_tool(self, kind):
        self.tool = kind
        self.ghost = None
        self._paint_palette()
        self.canvas.configure(cursor="crosshair" if kind else "")
        self._status()
        self.redraw()

    def _cancel(self):
        self.drag = None
        self._set_tool(None)

    def _set_ghost(self, pt):
        self.ghost = pt
        self.redraw()

    # ------------------------------------------------------------ mouse
    def _press(self, e):
        self.canvas.focus_set()
        x, y = e.x, e.y
        if self.tool:
            self.place(self.tool, x, y)
            if not (e.state & 0x0001):          # Shift keeps the tool armed
                self._set_tool(None)
            return
        pin = self.hit_pin(x, y)
        if pin:
            self.drag = {"mode": "wire", "from": pin, "x": x, "y": y, "target": None}
            self._status(t("lb.h.wiring"))
            return
        comp = self.hit_comp(x, y)
        if comp is not None:
            self.selected = comp
            self.drag = {"mode": "move", "comp": comp, "x0": x, "y0": y, "pos0": comp.pos,
                         "moved": False, "snap": json.dumps(serialize(self.model))}
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
            dgx = round((e.x - d["x0"]) / self.grid_px)
            dgy = round((e.y - d["y0"]) / self.grid_px)
            if dgx or dgy:
                d["moved"] = True
            d["comp"].pos = (d["pos0"][0] + dgx, d["pos0"][1] + dgy)
            self.redraw()
        elif d["mode"] == "wire":
            d["x"], d["y"] = e.x, e.y
            tgt = self.hit_pin(e.x, e.y, tol=max(18, 18 * self.s))
            fr = d["from"]
            d["target"] = tgt if (tgt and tgt[2] != fr[2] and tgt[0] is not fr[0]) else None
            self.redraw()

    def _release(self, e):
        d = self.drag
        self.drag = None
        self.canvas.configure(cursor="crosshair" if self.tool else "")
        if not d:
            return
        if d["mode"] == "wire":
            if d["target"]:
                self.connect(d["from"], d["target"])
            else:
                tgt = self.hit_pin(e.x, e.y, tol=max(18, 18 * self.s))
                if tgt and (tgt[2] == d["from"][2] or tgt[0] is d["from"][0]):
                    self._flash(t("lb.msg.same"))
            self._status()
            self.redraw()
        elif d["mode"] == "move":
            if d["moved"]:
                self.undo_stack.append(d["snap"])
                self.redo_stack.clear()
                self._changed()
            elif d["comp"].kind == "INPUT":
                self._toggle(d["comp"])

    def _toggle(self, comp):
        comp.params["value"] = 1 - int(comp.params.get("value", 0))
        self._recompute()

    def _hover(self, e):
        if self.tool:
            self._set_ghost((e.x, e.y))
            return
        if self.drag:
            return
        pin = self.hit_pin(e.x, e.y)
        key = (pin[0].id, pin[1], pin[2]) if pin else None
        if key != self.hover_pin:
            self.hover_pin = key
            if pin:
                comp, name, is_out = pin
                v = self.pin_values.get((comp.id, name))
                self._status(t("lb.h.pin").format(
                    c=comp.params.get("label") or comp.kind, io=t("lb.out") if is_out else t("lb.in"), p=name,
                    v=t("lb.float") if v is None else v))
            else:
                self._status()
            self.redraw()
        comp = self.hit_comp(e.x, e.y) if not pin else None
        self.canvas.configure(cursor="hand2" if pin else ("fleur" if comp else ""))

    def _pan_start(self, e):
        self.drag = {"mode": "pan", "x0": e.x, "y0": e.y, "o0": (self.ox, self.oy)}

    def _pan_move(self, e):
        self._motion(e)

    def _context(self, e):
        comp = self.hit_comp(e.x, e.y)
        wire = None if comp else self.hit_wire(e.x, e.y)
        if comp is None and wire is None:
            return
        self.selected = comp or wire
        self._render_props()
        self.redraw()
        m = tk.Menu(self, tearoff=0)
        if comp is not None:
            if comp.kind == "INPUT":
                m.add_command(label=t("lb.m.toggle"), command=lambda: self._toggle(comp))
            m.add_command(label=t("lb.m.rename"), command=lambda: self._rename(comp))
            m.add_command(label=t("lb.m.dup"), command=self._duplicate)
            m.add_command(label=t("lb.m.disconnect"), command=lambda: self._disconnect(comp))
        m.add_separator()
        m.add_command(label=t("lb.m.delete"), command=self._delete_selected)
        m.tk_popup(e.x_root, e.y_root)

    def _rename(self, comp):
        from tkinter import simpledialog
        v = simpledialog.askstring(t("lb.label"), t("lb.label"), initialvalue=comp.params.get("label", ""),
                                   parent=self)
        if v is not None:
            self._checkpoint()
            comp.params["label"] = v.strip()
            self._changed()

    def _disconnect(self, comp):
        self._checkpoint()
        self.model.wires = [w for w in self.model.wires if w["src"][0] != comp.id and w["dst"][0] != comp.id]
        self._changed()

    def _zoom(self, f, e=None):
        new = max(10, min(60, self.grid_px * f))
        cx = e.x if e is not None else self.canvas.winfo_width() / 2
        cy = e.y if e is not None else self.canvas.winfo_height() / 2
        wx, wy = (cx - self.ox) / self.grid_px, (cy - self.oy) / self.grid_px
        self.grid_px = new
        self.ox, self.oy = cx - wx * new, cy - wy * new
        self.zoom_lbl.configure(text=f"{round(self.s * 100)}%")
        self.redraw()

    def _fit(self):
        if not self.model.components:
            return
        self.grid_px = BASE
        boxes = [self.bbox(c) for c in self.model.components]
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes)
        y1 = max(b[3] for b in boxes)
        W = max(200, self.canvas.winfo_width())
        H = max(200, self.canvas.winfo_height())
        f = min((W - 80) / max(1, x1 - x0), (H - 80) / max(1, y1 - y0), 1.6)
        self.grid_px = max(10, min(60, BASE * f))
        boxes = [self.bbox(c) for c in self.model.components]
        x0 = min(b[0] for b in boxes)
        y0 = min(b[1] for b in boxes)
        x1 = max(b[2] for b in boxes)
        y1 = max(b[3] for b in boxes)
        self.ox += (W - (x1 - x0)) / 2 - x0
        self.oy += (H - (y1 - y0)) / 2 - y0
        self.zoom_lbl.configure(text=f"{round(self.s * 100)}%")
        self.redraw()

    # ------------------------------------------------------------ state
    def _status(self, text=None):
        if text is None:
            text = t("lb.h.place").format(p=t(TOOL_KEYS[self.tool])) if self.tool else t("lb.h.idle")
        self.status.configure(text=text)

    def _flash(self, text):
        self.msg.configure(text=text)
        if self._flash_job:
            self.after_cancel(self._flash_job)
        self._flash_job = self.after(4500, lambda: self.msg.configure(text=""))

    def _changed(self):
        self._render_props()
        self._recompute()

    def _recompute(self):
        self.pin_values, self.eval_error = self.model.evaluate()
        if self.eval_error == "cycle":
            self._flash(t("lb.msg.loop"))
        self.redraw()
        self._render_check()
        self._render_tt()

    # ------------------------------------------------------------ side panel
    def _render_props(self):
        for w in self.props_box.winfo_children():
            w.destroy()
        ttk.Label(self.props_box, text=t("lb.props"), font=FONT_H2, style="CardTitle.TLabel")\
            .pack(anchor="w", padx=10, pady=(10, 4))
        sel = self.selected
        if not isinstance(sel, LogicComponent):
            ttk.Label(self.props_box, text=t("lb.none"), style="CardBody.TLabel", wraplength=270)\
                .pack(anchor="w", padx=10)
            return
        ttk.Label(self.props_box, text=t(TOOL_KEYS[sel.kind]), font=FONT_MONO, style="CardBody.TLabel")\
            .pack(anchor="w", padx=10)
        row = ttk.Frame(self.props_box, style="Card.TFrame")
        row.pack(fill="x", padx=10, pady=4)
        ttk.Label(row, text=t("lb.label"), style="CardBody.TLabel").pack(side="left")
        var = tk.StringVar(value=sel.params.get("label", ""))
        ent = ttk.Entry(row, textvariable=var, width=14)
        ent.pack(side="left", padx=6)

        def apply(_e=None):
            if sel.params.get("label", "") != var.get().strip():
                self._checkpoint()
                sel.params["label"] = var.get().strip()
                self._recompute()
        ent.bind("<Return>", apply)
        ent.bind("<FocusOut>", apply)
        if sel.kind == "INPUT":
            ttk.Button(self.props_box, text=t("lb.m.toggle"), style="Small.TButton",
                       command=lambda: self._toggle(sel)).pack(anchor="w", padx=10)
        key = {"INPUT": "logic.props.input_desc", "OUTPUT": "logic.props.output_desc",
               "NODE": "logic.props.node_desc"}.get(sel.kind)
        if sel.kind in MUX_DEMUX_KINDS:
            key = "logic.props.desc." + sel.kind
        if key:
            ttk.Label(self.props_box, text=t(key), style="CardBody.TLabel", wraplength=270, justify="left",
                      font=("Segoe UI", 9)).pack(anchor="w", padx=10, pady=(4, 0))

    def _render_check(self):
        for w in self.check_box.winfo_children():
            w.destroy()
        ttk.Label(self.check_box, text=t("lb.check"), font=FONT_H2, style="CardTitle.TLabel")\
            .pack(anchor="w", padx=10)
        floating = []
        for c in self.model.components:
            if c.kind == "INPUT":
                continue
            for p in c.input_pins():
                if self.model.wire_to(c.id, p) is None:
                    floating.append((c, p))
        if not self.model.components:
            return
        if not floating:
            ttk.Label(self.check_box, text=t("lb.ok"), foreground=GOOD, style="CardBody.TLabel")\
                .pack(anchor="w", padx=10)
            return
        ttk.Label(self.check_box, text=t("lb.floating_n").format(n=len(floating)), foreground=PIN_BAD,
                  style="CardBody.TLabel", wraplength=270).pack(anchor="w", padx=10)
        for c, p in floating[:8]:
            lab = tk.Label(self.check_box, text=f"  • {c.params.get('label') or c.kind} . {p}", fg=PIN_BAD,
                           bg="#FFFFFF", cursor="hand2", font=("Segoe UI", 9))
            lab.pack(anchor="w", padx=10)
            lab.bind("<Button-1>", lambda e, c=c: self._select(c))

    def _select(self, comp):
        self.selected = comp
        self._render_props()
        self.redraw()

    def _io(self):
        ins = [c for c in self.model.components if c.kind == "INPUT"]
        outs = [c for c in self.model.components if c.kind == "OUTPUT"]
        return ins, outs

    def _render_tt(self):
        tree = self.tt
        tree.delete(*tree.get_children())
        ins, outs = self._io()
        self._tt_inputs = ins
        if not ins or not outs:
            tree.configure(columns=())
            self.tt_note.configure(text=t("lb.tt_need"))
            self.expr_lbl.configure(text="")
            return
        if len(ins) > 6:
            tree.configure(columns=())
            self.tt_note.configure(text=t("lb.tt_many"))
            self.expr_lbl.configure(text="")
            return
        self.tt_note.configure(text=t("lb.tt_hint"))
        names_in = [c.params.get("label") or f"I{c.id}" for c in ins]
        names_out = [c.params.get("label") or f"O{c.id}" for c in outs]
        cols = [f"i{k}" for k in range(len(ins))] + [f"o{k}" for k in range(len(outs))]
        tree.configure(columns=cols, height=min(16, 2 ** len(ins)))
        for k, n in enumerate(names_in):
            tree.heading(f"i{k}", text=n)
            tree.column(f"i{k}", width=34, anchor="center")
        for k, n in enumerate(names_out):
            tree.heading(f"o{k}", text=n)
            tree.column(f"o{k}", width=max(40, 8 * len(n)), anchor="center")
        saved = [c.params.get("value", 0) for c in ins]
        n = len(ins)
        results = {k: [] for k in range(len(outs))}
        cur_row = None
        for i in range(2 ** n):
            bits = [(i >> (n - 1 - k)) & 1 for k in range(n)]
            for c, b in zip(ins, bits):
                c.params["value"] = b
            vals, _ = self.model.evaluate()
            ys = [vals.get((o.id, "A")) for o in outs]
            for k, y in enumerate(ys):
                results[k].append(y)
            tag = ("cur",) if bits == [int(v) for v in saved] else ()
            iid = tree.insert("", "end", values=bits + ["?" if y is None else y for y in ys], tags=tag)
            if tag:
                cur_row = iid
        for c, v in zip(ins, saved):
            c.params["value"] = v
        if cur_row:
            tree.see(cur_row)
        # minimized expressions
        lines = []
        var_names = [_safe_var(nm, k) for k, nm in enumerate(names_in)]
        for k, nm in enumerate(names_out):
            col = results[k]
            if any(y is None for y in col):
                lines.append(f"{nm} = ?  ({t('lb.float')})")
                continue
            table = TruthTable(var_names, [(tuple((i >> (n - 1 - b)) & 1 for b in range(n)), y)
                                           for i, y in enumerate(col)])
            try:
                res = qm.minimize(table)
                lines.append(f"{nm} = {res.minimal_sop.to_symbolic()}")
            except Exception:
                pass
        self.expr_lbl.configure(text="\n".join(lines))

    def _tt_pick(self, _e=None):
        sel = self.tt.selection()
        if not sel or self._tt_lock:
            return
        vals = self.tt.item(sel[0], "values")
        ins = self._tt_inputs
        for c, v in zip(ins, vals[:len(ins)]):
            c.params["value"] = int(v)
        self._tt_lock = True
        try:
            self._recompute()
        finally:
            self._tt_lock = False

    # ------------------------------------------------------------ drawing
    def _col(self, v):
        return HIGH if v == 1 else (LOW if v == 0 else FLOAT)

    def redraw(self):
        c = self.canvas
        c.delete("all")
        W, H = c.winfo_width(), c.winfo_height()
        if W < 10:
            return
        g = self.grid_px
        x = self.ox % g
        while x < W:
            major = round((x - self.ox) / g) % 5 == 0
            c.create_line(x, 0, x, H, fill=GRID_MAJOR if major else GRID)
            x += g
        y = self.oy % g
        while y < H:
            major = round((y - self.oy) / g) % 5 == 0
            c.create_line(0, y, W, y, fill=GRID_MAJOR if major else GRID)
            y += g
        if not self.model.components and not self.tool:
            c.create_text(W / 2, H / 2, text=t("lb.intro"), fill="#9aa3b2", font=("Segoe UI", 12),
                          width=min(520, W - 40), justify="center")
        for w in self.model.wires:
            pts = self.wire_pts(w)
            if not pts:
                continue
            v = self.pin_values.get(tuple(w["src"]))
            sel = self.selected is w
            c.create_line(*pts, fill=SEL if sel else self._col(v), width=4 if sel else (3 if v == 1 else 2),
                          dash=None if v is not None else (5, 3), joinstyle="round")
        for comp in self.model.components:
            self._draw_comp(comp)
        self._draw_pins()
        d = self.drag
        if d and d["mode"] == "wire":
            fr = d["from"]
            ins, outs = self.pins(fr[0])
            px, py = (outs if fr[2] else ins)[fr[1]]
            if d["target"]:
                ti, to = self.pins(d["target"][0])
                tx, ty = (to if d["target"][2] else ti)[d["target"][1]]
                pts = self.route(px, py, tx, ty) if fr[2] else self.route(tx, ty, px, py)
                c.create_line(*pts, fill=GOOD, width=3)
            else:
                c.create_line(px, py, d["x"], d["y"], fill=SEL, width=2, dash=(6, 3))
        if self.tool and self.ghost:
            self._draw_ghost(self.tool, *self.ghost)

    def _draw_pins(self):
        c = self.canvas
        r = max(3.5, 4.5 * self.s)
        wiring = self.drag if (self.drag and self.drag["mode"] == "wire") else None
        for comp in self.model.components:
            ins, outs = self.pins(comp)
            for name, (px, py) in ins.items():
                connected = self.model.wire_to(comp.id, name) is not None
                self._pin_dot(px, py, r, comp, name, False, connected, wiring)
            for name, (px, py) in outs.items():
                connected = any(tuple(w["src"]) == (comp.id, name) for w in self.model.wires)
                self._pin_dot(px, py, r, comp, name, True, connected, wiring)

    def _pin_dot(self, px, py, r, comp, name, is_out, connected, wiring):
        c = self.canvas
        v = self.pin_values.get((comp.id, name))
        if wiring:
            fr = wiring["from"]
            ok = is_out != fr[2] and comp is not fr[0]
            if ok:
                tgt = wiring["target"]
                big = tgt and tgt[0] is comp and tgt[1] == name
                rr = r * (2.2 if big else 1.6)
                c.create_oval(px - rr, py - rr, px + rr, py + rr, outline=GOOD, width=2,
                              fill="#d9f7e5" if big else "")
            return self._dot(px, py, r, v, connected, is_out)
        self._dot(px, py, r, v, connected, is_out)
        if self.hover_pin == (comp.id, name, is_out):
            rr = r * 2
            c.create_oval(px - rr, py - rr, px + rr, py + rr, outline=PIN_OK, width=2)

    def _dot(self, px, py, r, v, connected, is_out):
        c = self.canvas
        if not connected and not is_out:
            c.create_oval(px - r, py - r, px + r, py + r, outline=PIN_BAD, width=2, fill="white")
        else:
            c.create_oval(px - r, py - r, px + r, py + r, outline="#333", width=1, fill=self._col(v)
                          if v is not None else "white")

    def _draw_comp(self, comp):
        c = self.canvas
        s = self.s
        sel = self.selected is comp
        ax, ay = self.g2p(comp.pos)
        outline = SEL if sel else OUTLINE
        ins, outs = self.pins(comp)
        if sel:
            x0, y0, x1, y1 = self.bbox(comp)
            c.create_rectangle(x0 - 4, y0 - 4, x1 + 4, y1 + 4, outline=SEL, width=2, dash=(4, 3))
        label = comp.params.get("label", "")
        if comp.kind in GATE_KINDS:
            draw_gate_symbol(c, comp.kind, ax, ay, w=GATE_W * s, h=GATE_H * s, show_pin_labels=False,
                             stub=STUB * s, fill="#fbe7cf" if sel else BODY)
            for name, (px, py) in ins.items():
                v = self.pin_values.get((comp.id, name))
                c.create_line(px, py, px + STUB * s - 1, py, fill=self._col(v), width=3)
            for name, (px, py) in outs.items():
                v = self.pin_values.get((comp.id, name))
                c.create_line(px - STUB * s + 1, py, px, py, fill=self._col(v), width=3)
            c.create_text(ax + GATE_W * s / 2, ay - 8 * s, text=label or comp.kind, fill=TEXT,
                          font=("Segoe UI", max(7, int(8 * s)), "bold"))
            return
        if comp.kind == "INPUT":
            v = int(comp.params.get("value", 0))
            w, h = 56 * s, 30 * s
            c.create_rectangle(ax, ay, ax + w, ay + h, outline=outline, width=2, fill=HIGH if v else "#e4e4e4")
            # a little slide switch
            kx = ax + (w - 20 * s) if v else ax + 4 * s
            c.create_rectangle(kx, ay + 5 * s, kx + 16 * s, ay + h - 5 * s, fill="white", outline="#666")
            c.create_text(ax + (w * 0.3 if v else w * 0.7), ay + h / 2, text=str(v),
                          fill="white" if v else "#444", font=("Segoe UI", max(8, int(12 * s)), "bold"))
            c.create_line(ax + w, ay + h / 2, ax + w + STUB * s, ay + h / 2, fill=self._col(v), width=3)
            c.create_text(ax + w / 2, ay - 9 * s, text=label, fill=TEXT, font=("Consolas", max(7, int(9 * s)), "bold"))
            return
        if comp.kind == "OUTPUT":
            v = self.pin_values.get((comp.id, "A"))
            r = 14 * s
            cx, cy = ax + STUB * s + r, ay + 15 * s
            c.create_line(ax, cy, cx - r, cy, fill=self._col(v), width=3)
            fill = "#ffd54a" if v == 1 else ("#e4e4e4" if v == 0 else "white")
            if v == 1:
                c.create_oval(cx - r * 1.5, cy - r * 1.5, cx + r * 1.5, cy + r * 1.5, fill="#fff3c4", outline="")
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=outline, width=2, fill=fill,
                          dash=None if v is not None else (3, 2))
            c.create_text(cx, cy, text="?" if v is None else str(v), fill="#333",
                          font=("Segoe UI", max(8, int(10 * s)), "bold"))
            c.create_text(cx, ay - 9 * s, text=label or "Y", fill=TEXT, font=("Consolas", max(7, int(9 * s)), "bold"))
            return
        if comp.kind == "NODE":
            v = self.pin_values.get((comp.id, "A"))
            cy = ay + 12 * s
            c.create_line(ax, cy, ax + 24 * s, cy, fill=self._col(v), width=3)
            rr = 6 * s
            c.create_oval(ax + 12 * s - rr, cy - rr, ax + 12 * s + rr, cy + rr, fill=self._col(v), outline=outline)
            return
        w, h = _MUX[comp.kind][0] * s, _MUX[comp.kind][1] * s
        bx = ax + STUB * s
        if comp.kind.startswith("MUX"):
            pts = [bx, ay, bx, ay + h, bx + w, ay + h * 0.8, bx + w, ay + h * 0.2]
        else:
            pts = [bx, ay + h * 0.2, bx, ay + h * 0.8, bx + w, ay + h, bx + w, ay]
        c.create_polygon(pts, fill="#fbe7cf" if sel else BODY, outline=outline, width=2)
        c.create_text(bx + w / 2, ay + h / 2, text=comp.kind[:-1], fill="#333",
                      font=("Segoe UI", max(7, int(9 * s)), "bold"))
        f = ("Segoe UI", max(6, int(8 * s)))
        for name, (px, py) in ins.items():
            v = self.pin_values.get((comp.id, name))
            if name.startswith("S"):
                c.create_line(px, py, px, py - STUB * s, fill=self._col(v), width=3)
                c.create_text(px + 8 * s, py - 6 * s, text=name, fill=TEXT, font=f, anchor="w")
            else:
                c.create_line(px, py, px + STUB * s, py, fill=self._col(v), width=3)
                c.create_text(px + STUB * s + 3, py, text=name, fill=TEXT, font=f, anchor="w")
        for name, (px, py) in outs.items():
            v = self.pin_values.get((comp.id, name))
            c.create_line(px - STUB * s, py, px, py, fill=self._col(v), width=3)
            c.create_text(px - STUB * s - 3, py, text=name, fill=TEXT, font=f, anchor="e")
        if label:
            c.create_text(bx + w / 2, ay - 9 * s, text=label, fill=TEXT, font=("Consolas", max(7, int(9 * s)), "bold"))

    def _draw_ghost(self, kind, x, y):
        w, h = geometry(kind)[3]
        s = self.s
        gx, gy = self.p2g(x - w * s / 2, y - h * s / 2)
        ax, ay = self.g2p((gx, gy))
        self.canvas.create_rectangle(ax, ay, ax + w * s, ay + h * s, outline="#3b6fd1", width=2, dash=(4, 3),
                                     fill="#eef3ff")
        self.canvas.create_text(ax + w * s / 2, ay + h * s / 2, text=t(TOOL_KEYS[kind]), fill="#3b6fd1",
                                font=("Segoe UI", max(7, int(9 * s)), "bold"))


def _safe_var(name, k):
    out = "".join(ch for ch in name if ch.isalnum())
    if not out or not out[0].isalpha():
        out = "X" + str(k)
    return out


def _seg_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    L = dx * dx + dy * dy
    if L == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    u = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L))
    return ((px - ax - u * dx) ** 2 + (py - ay - u * dy) ** 2) ** 0.5


def _palette_icon(cv, kind):
    if kind == "INPUT":
        cv.create_rectangle(4, 5, 26, 19, outline="#333", width=2, fill=HIGH)
        cv.create_text(15, 12, text="1", fill="white", font=("Segoe UI", 8, "bold"))
    elif kind == "OUTPUT":
        cv.create_oval(9, 3, 27, 21, outline="#333", width=2, fill="#ffd54a")
    elif kind == "NODE":
        cv.create_line(3, 12, 31, 12, fill="#333", width=2)
        cv.create_oval(12, 7, 22, 17, outline="#333", fill="#666")
    elif kind in GATE_KINDS:
        draw_gate_symbol(cv, kind, 1, 2, w=32, h=20, show_pin_labels=False, stub=4)
    else:
        if kind.startswith("MUX"):
            pts = [7, 2, 7, 22, 27, 17, 27, 7]
        else:
            pts = [7, 7, 7, 17, 27, 22, 27, 2]
        cv.create_polygon(pts, fill=BODY, outline="#333")
