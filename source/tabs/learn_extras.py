"""
learn_extras.py - visual reference cards shown next to the theory on Learn
pages that have no component symbols (v6.2.1):

    Boolean Logic   - every gate: symbol, expression and truth table
    AC Circuits     - R / L / C phase relations, impedance & power triangles,
                      resonance
    Modulation      - what each modulation looks like (AM, DSB, FM, PM, ASK,
                      FSK, BPSK, QPSK) + the AM spectrum
    RF              - two-port S-parameters, reflection, standing waves,
                      Smith-chart landmarks, lines and stubs

Each gallery is a responsive grid on one canvas (like SymbolGallery): the
number of columns follows the available width, the cards keep their size.
"""
import math
import tkinter as tk
from tkinter import ttk

from i18n import t, register
from widgets import debounce

BG = "#fdfaf3"
CARD = "#ffffff"
EDGE = "#e3dccb"
INK = "#1f2a44"
MUTED = "#5b6475"
V_COL = "#c0392b"      # voltage / carrier
I_COL = "#1f6fb2"      # current / message
G_COL = "#2e7d32"
GRID = "#e8e2d4"

register({
    "lx.title.digital": ("Gates at a glance", "Porțile pe scurt"),
    "lx.hint.digital": ("Symbol, Boolean expression and truth table of every basic gate. "
                        "A small circle (bubble) on the output means the result is inverted.",
                        "Simbolul, expresia booleană și tabelul de adevăr pentru fiecare poartă. "
                        "Cercul mic (bula) de la ieșire înseamnă că rezultatul este negat."),
    "lx.title.ac": ("Phase relationships", "Relații de fază"),
    "lx.hint.ac": ("Red = voltage, blue = current. The waveforms and phasors show who leads whom "
                   "in each element, and how R and X combine.",
                   "Roșu = tensiune, albastru = curent. Formele de undă și fazorii arată cine este "
                   "defazat înainte în fiecare element și cum se combină R și X."),
    "lx.ac.r": ("Resistor: V and I in phase (φ = 0°)", "Rezistor: V și I în fază (φ = 0°)"),
    "lx.ac.l": ("Inductor: I lags V by 90°", "Bobină: I rămâne în urma lui V cu 90°"),
    "lx.ac.c": ("Capacitor: I leads V by 90°", "Condensator: I este înaintea lui V cu 90°"),
    "lx.ac.z": ("Impedance triangle  Z = R + jX", "Triunghiul impedanței  Z = R + jX"),
    "lx.ac.p": ("Power triangle  S = P + jQ", "Triunghiul puterilor  S = P + jQ"),
    "lx.ac.res": ("Series RLC: |Z| is minimum at f0", "RLC serie: |Z| minim la f0"),
    "lx.title.mod": ("What each modulation looks like", "Cum arată fiecare modulație"),
    "lx.hint.mod": ("Blue = message (data), red = transmitted signal. Analog modulations follow a "
                    "smooth message; digital ones switch between a few states.",
                    "Albastru = mesajul (datele), roșu = semnalul transmis. Modulațiile analogice "
                    "urmăresc un mesaj continuu; cele digitale comută între câteva stări."),
    "lx.mod.am": ("AM: amplitude follows the message", "MA: amplitudinea urmărește mesajul"),
    "lx.mod.dsb": ("DSB-SC: carrier suppressed, phase flips", "DSB-SC: purtătoare suprimată, faza se inversează"),
    "lx.mod.fm": ("FM: frequency follows the message", "MF: frecvența urmărește mesajul"),
    "lx.mod.pm": ("PM: phase follows the message", "MP: faza urmărește mesajul"),
    "lx.mod.ask": ("ASK / OOK: carrier on for 1, off for 0", "ASK / OOK: purtătoare pornită la 1, oprită la 0"),
    "lx.mod.fsk": ("FSK: two frequencies for 0 and 1", "FSK: două frecvențe pentru 0 și 1"),
    "lx.mod.bpsk": ("BPSK: phase 0° / 180° for 0 / 1", "BPSK: faza 0° / 180° pentru 0 / 1"),
    "lx.mod.qpsk": ("QPSK: 4 phases, 2 bits per symbol", "QPSK: 4 faze, 2 biți pe simbol"),
    "lx.mod.spec": ("AM spectrum: carrier + 2 sidebands", "Spectru MA: purtătoare + 2 benzi laterale"),
    "lx.title.rf": ("RF picture book", "RF în imagini"),
    "lx.hint.rf": ("The ideas behind the simulator: incident and reflected waves, standing waves, "
                   "and how lines and stubs transform impedances.",
                   "Ideile din spatele simulatorului: unde incidente și reflectate, unde staționare "
                   "și cum liniile și stuburile transformă impedanțele."),
    "lx.rf.2port": ("Two-port: b = S · a", "Diport: b = S · a"),
    "lx.rf.refl": ("Reflection at a mismatched load  Γ", "Reflexie pe o sarcină neadaptată  Γ"),
    "lx.rf.sw": ("Standing wave: VSWR = Vmax / Vmin", "Undă staționară: VSWR = Vmax / Vmin"),
    "lx.rf.smith": ("Smith chart landmarks", "Repere pe diagrama Smith"),
    "lx.rf.qw": ("λ/4 transformer: Zin = Z0² / ZL", "Transformator λ/4: Zin = Z0² / ZL"),
    "lx.rf.stub": ("Stubs: short → L or C, open → C or L", "Stuburi: scurt → L sau C, gol → C sau L"),
    "lx.rf.short": ("short", "scurt"),
    "lx.rf.open": ("open", "gol"),
    "lx.rf.match": ("match", "adaptat"),
    "lx.ind": ("inductive", "inductiv"),
    "lx.cap": ("capacitive", "capacitiv"),
})


# ---------------------------------------------------------------------------
class CardGallery(ttk.Frame):
    """Responsive grid of fixed-size drawing cards: items = [(draw(c, x, y, w, h), caption)]."""

    def __init__(self, parent, title, hint, items, accent, cell_w=230, cell_h=170):
        super().__init__(parent, style="Card.TFrame")
        self.items, self.cw, self.ch = items, cell_w, cell_h
        self.columnconfigure(0, weight=1)
        tk.Frame(self, bg=accent, height=6).grid(row=0, column=0, sticky="ew")
        ttk.Label(self, text=title, font=("Segoe UI", 12, "bold"), style="CardSub.TLabel",
                  foreground=accent).grid(row=1, column=0, sticky="w", padx=16, pady=(10, 0))
        hint_l = ttk.Label(self, text=hint, font=("Segoe UI", 8), style="CardBody.TLabel",
                           wraplength=300, justify="left")
        hint_l.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 6))
        self.bind("<Configure>", lambda e: hint_l.configure(wraplength=max(160, e.width - 40)), add="+")
        self.canvas = tk.Canvas(self, height=cell_h, width=300, bg=BG, highlightthickness=0)
        self.canvas.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 14))
        self._width = 0
        self.canvas.bind("<Configure>", debounce(self.canvas, self._on_resize, 100))

    def _on_resize(self, e):
        if abs(e.width - self._width) < 3 and self.canvas.find_all():
            return
        self._width = e.width
        self.redraw()

    def redraw(self):
        c = self.canvas
        c.delete("all")
        width = max(self._width, self.cw)
        cols = max(1, min(len(self.items), int(width // self.cw)))
        rows = math.ceil(len(self.items) / cols)
        cell_w = width / cols
        c.configure(height=rows * self.ch)
        for i, (fn, cap) in enumerate(self.items):
            r, k = divmod(i, cols)
            x0, y0 = k * cell_w + 4, r * self.ch + 4
            w, h = cell_w - 8, self.ch - 8
            c.create_rectangle(x0, y0, x0 + w, y0 + h, fill=CARD, outline=EDGE)
            try:
                fn(c, x0 + 8, y0 + 6, w - 16, h - 30)
            except Exception:
                pass
            c.create_text(x0 + w / 2, y0 + h - 12, text=cap, font=("Segoe UI", 8), fill=INK,
                          width=w - 10)


# ---------------------------------------------------------------------------
# small drawing helpers
def _curve(c, x0, y0, w, h, f, color, width=2, n=180, t0=0.0, t1=1.0):
    pts = []
    for i in range(n + 1):
        tt = t0 + (t1 - t0) * i / n
        pts += [x0 + w * i / n, y0 + h / 2 - f(tt) * h / 2]
    c.create_line(*pts, fill=color, width=width, smooth=False)


def _axis(c, x0, y0, w, h):
    c.create_line(x0, y0 + h / 2, x0 + w, y0 + h / 2, fill=GRID)


def _arrow(c, x1, y1, x2, y2, color, width=2, text=None, anchor="w", dx=4, dy=0):
    c.create_line(x1, y1, x2, y2, fill=color, width=width, arrow="last", arrowshape=(9, 11, 4))
    if text:
        c.create_text(x2 + dx, y2 + dy, text=text, anchor=anchor, fill=color, font=("Segoe UI", 9, "bold"))


# ---------------------------------------------------------------------------
# Boolean logic
_GATES = {
    "AND": (lambda a, b: a & b, "Y = A · B"),
    "OR": (lambda a, b: a | b, "Y = A + B"),
    "NOT": (lambda a, b: 1 - a, "Y = A'"),
    "NAND": (lambda a, b: 1 - (a & b), "Y = (A · B)'"),
    "NOR": (lambda a, b: 1 - (a | b), "Y = (A + B)'"),
    "XOR": (lambda a, b: a ^ b, "Y = A ⊕ B"),
    "XNOR": (lambda a, b: 1 - (a ^ b), "Y = (A ⊕ B)'"),
}


def _gate_card(kind):
    fn, expr = _GATES[kind]

    def draw(c, x, y, w, h):
        from drawing import draw_gate_symbol
        gw, gh = min(110, w * 0.52), 54
        x += 10
        draw_gate_symbol(c, kind, x, y + 10, w=gw, h=gh,
                         in_labels=(["A"] if kind == "NOT" else ["A", "B"]))
        c.create_text(x + gw / 2, y + gh + 26, text=expr, font=("Consolas", 10, "bold"), fill=G_COL)
        # truth table
        rows = [(0,), (1,)] if kind == "NOT" else [(0, 0), (0, 1), (1, 0), (1, 1)]
        heads = ["A", "Y"] if kind == "NOT" else ["A", "B", "Y"]
        tx = x + gw + 14
        cw_ = min(22, (x + w - tx) / len(heads))
        rh = 17
        ty = y + 6
        for j, hd in enumerate(heads):
            c.create_rectangle(tx + j * cw_, ty, tx + (j + 1) * cw_, ty + rh, fill="#eef1f6", outline=EDGE)
            c.create_text(tx + (j + 0.5) * cw_, ty + rh / 2, text=hd, font=("Segoe UI", 8, "bold"), fill=INK)
        for i, r in enumerate(rows):
            yv = fn(r[0], r[1] if len(r) > 1 else 0)
            vals = list(r) + [yv]
            for j, v in enumerate(vals):
                last = j == len(vals) - 1
                c.create_rectangle(tx + j * cw_, ty + (i + 1) * rh, tx + (j + 1) * cw_, ty + (i + 2) * rh,
                                   fill=("#e3f4e5" if (last and v) else "#ffffff"), outline=EDGE)
                c.create_text(tx + (j + 0.5) * cw_, ty + (i + 1.5) * rh, text=str(v),
                              font=("Consolas", 9, "bold" if last else "normal"),
                              fill=G_COL if (last and v) else INK)
    return draw


def digital_gallery(parent, accent):
    items = [(_gate_card(k), k) for k in ("AND", "OR", "NOT", "NAND", "NOR", "XOR", "XNOR")]
    return CardGallery(parent, t("lx.title.digital"), t("lx.hint.digital"), items, accent,
                       cell_w=240, cell_h=150)


# ---------------------------------------------------------------------------
# AC circuits
def _phase_card(shift_deg):
    def draw(c, x, y, w, h):
        pw = w * 0.62
        _axis(c, x, y, pw, h)
        _curve(c, x, y + 4, pw, h - 8, lambda s: math.sin(2 * math.pi * 1.5 * s), V_COL)
        ph = math.radians(shift_deg)
        _curve(c, x, y + 4 + h * 0.15, pw, h * 0.7 - 8,
               lambda s: math.sin(2 * math.pi * 1.5 * s + ph), I_COL)
        c.create_text(x + 2, y + 4, text="v", anchor="nw", fill=V_COL, font=("Segoe UI", 9, "bold"))
        c.create_text(x + 14, y + 4, text="i", anchor="nw", fill=I_COL, font=("Segoe UI", 9, "bold"))
        # phasors
        cx, cy = x + pw + (w - pw) / 2, y + h / 2
        r = min((w - pw) / 2 - 6, h / 2 - 6)
        c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=GRID)
        _arrow(c, cx, cy, cx + r, cy, V_COL)
        c.create_text(cx + r - 2, cy - 8, text="V", fill=V_COL, font=("Segoe UI", 9, "bold"))
        ri = r * 0.7
        ex, ey = cx + ri * math.cos(ph), cy - ri * math.sin(ph)
        _arrow(c, cx, cy, ex, ey, I_COL)
        c.create_text(ex + (8 if math.cos(ph) >= 0 else -8), ey + (-8 if math.sin(ph) > 0 else 8),
                      text="I", fill=I_COL, font=("Segoe UI", 9, "bold"))
    return draw


def _triangle(labels, colors, second_color):
    def draw(c, x, y, w, h):
        bx, by = x + 14, y + h - 18
        ex = x + w * 0.72
        ty = y + 8
        c.create_line(bx, by, ex, by, fill=colors[0], width=3)                  # R / P
        c.create_line(ex, by, ex, ty, fill=colors[1], width=3)                  # X / Q
        c.create_line(bx, by, ex, ty, fill=second_color, width=3, arrow="last")  # Z / S
        c.create_text((bx + ex) / 2, by + 1, text=labels[0], anchor="n", fill=colors[0],
                      font=("Segoe UI", 9, "bold"))
        c.create_text(ex + 5, (by + ty) / 2, text=labels[1], anchor="w", fill=colors[1],
                      font=("Segoe UI", 9, "bold"))
        c.create_text((bx + ex) / 2 - 10, (by + ty) / 2 - 6, text=labels[2], anchor="e", fill=second_color,
                      font=("Segoe UI", 9, "bold"))
        c.create_arc(bx - 26, by - 26, bx + 26, by + 26, start=0,
                     extent=math.degrees(math.atan2(by - ty, ex - bx)), style="arc", outline=MUTED)
        c.create_text(bx + 30, by - 10, text="φ", fill=MUTED, font=("Segoe UI", 9, "bold"))
    return draw


def _resonance(c, x, y, w, h):
    c.create_line(x, y + h, x + w, y + h, fill=GRID)
    c.create_line(x, y, x, y + h, fill=GRID)

    def z(s):   # s in [0,1] -> log frequency around f0 at 0.5
        r = 10 ** ((s - 0.5) * 2)
        return math.sqrt(0.08 ** 2 + (r - 1 / r) ** 2)
    zs = [z(i / 160) for i in range(161)]
    zmax = max(zs)
    pts = []
    for i, zz in enumerate(zs):
        pts += [x + w * i / 160, y + h - (h - 6) * min(1.0, zz / zmax * 1.6)]
    c.create_line(*pts, fill=V_COL, width=2)
    c.create_line(x + w / 2, y, x + w / 2, y + h, fill=MUTED, dash=(3, 3))
    c.create_text(x + w / 2 + 3, y + 2, text="f0", anchor="nw", fill=MUTED, font=("Segoe UI", 9, "bold"))
    c.create_text(x + 3, y + 2, text="|Z|", anchor="nw", fill=V_COL, font=("Segoe UI", 9, "bold"))
    c.create_text(x + 6, y + h - 4, text=t("lx.cap"), anchor="sw", fill=MUTED, font=("Segoe UI", 8))
    c.create_text(x + w - 4, y + h - 4, text=t("lx.ind"), anchor="se", fill=MUTED, font=("Segoe UI", 8))


def ac_gallery(parent, accent):
    items = [
        (_phase_card(0), t("lx.ac.r")),
        (_phase_card(-90), t("lx.ac.l")),
        (_phase_card(90), t("lx.ac.c")),
        (_triangle(("R", "X", "|Z|"), ("#555", "#8e44ad"), V_COL), t("lx.ac.z")),
        (_triangle(("P [W]", "Q [var]", "S [VA]"), (G_COL, "#8e44ad"), V_COL), t("lx.ac.p")),
        (_resonance, t("lx.ac.res")),
    ]
    return CardGallery(parent, t("lx.title.ac"), t("lx.hint.ac"), items, accent, cell_w=250, cell_h=150)


# ---------------------------------------------------------------------------
# Modulation
_BITS = [1, 0, 1, 1, 0]


def _bit(s):
    return _BITS[min(len(_BITS) - 1, int(s * len(_BITS)))]


def _mod_card(kind):
    fc = 14.0

    def msg(s):
        return math.sin(2 * math.pi * 1.2 * s)

    def sig(s):
        if kind == "am":
            return (1 + 0.6 * msg(s)) / 1.6 * math.cos(2 * math.pi * fc * s)
        if kind == "dsb":
            return msg(s) * math.cos(2 * math.pi * fc * s)
        if kind == "fm":   # phase = integral of message
            return math.cos(2 * math.pi * fc * s - 5.0 * math.cos(2 * math.pi * 1.2 * s))
        if kind == "pm":
            return math.cos(2 * math.pi * fc * s + 1.6 * msg(s))
        if kind == "ask":
            return _bit(s) * math.cos(2 * math.pi * fc * s)
        if kind == "fsk":
            return math.cos(2 * math.pi * (fc * 1.35 if _bit(s) else fc * 0.6) * s)
        if kind == "bpsk":
            return math.cos(2 * math.pi * 10 * s + (0 if _bit(s) else math.pi))
        if kind == "qpsk":
            k = min(3, int(s * 4))
            return math.cos(2 * math.pi * 10 * s + [0.25, 0.75, 1.25, 1.75][[0, 3, 1, 2][k]] * math.pi)
        return 0.0

    def draw(c, x, y, w, h):
        mh = h * 0.28
        if kind in ("ask", "fsk", "bpsk"):
            _curve(c, x, y, w, mh, lambda s: 0.8 if _bit(s) else -0.8, I_COL, width=2, n=400)
            for i, b in enumerate(_BITS):
                c.create_text(x + w * (i + 0.5) / len(_BITS), y + mh / 2, text=str(b),
                              fill=I_COL, font=("Segoe UI", 8, "bold"))
        elif kind == "qpsk":
            for i, pair in enumerate(("00", "11", "01", "10")):
                c.create_text(x + w * (i + 0.5) / 4, y + mh / 2, text=pair, fill=I_COL,
                              font=("Consolas", 9, "bold"))
                if i:
                    c.create_line(x + w * i / 4, y, x + w * i / 4, y + h, fill=GRID, dash=(2, 3))
        else:
            _curve(c, x, y, w, mh, msg, I_COL)
        sy = y + mh + 4
        sh = h - mh - 4
        _axis(c, x, sy, w, sh)
        _curve(c, x, sy, w, sh, sig, V_COL, width=1, n=500)
        if kind == "am":
            _curve(c, x, sy, w, sh, lambda s: (1 + 0.6 * msg(s)) / 1.6, I_COL, width=1)
            _curve(c, x, sy, w, sh, lambda s: -(1 + 0.6 * msg(s)) / 1.6, I_COL, width=1)
    return draw


def _am_spectrum(c, x, y, w, h):
    base = y + h - 12
    c.create_line(x, base, x + w, base, fill=MUTED)
    for fx, amp, lbl, col in ((0.5, 1.0, "fc", V_COL), (0.28, 0.45, "fc−fm", I_COL), (0.72, 0.45, "fc+fm", I_COL)):
        px = x + w * fx
        c.create_line(px, base, px, base - (h - 26) * amp, fill=col, width=3)
        c.create_text(px, base + 2, text=lbl, anchor="n", fill=col, font=("Segoe UI", 8, "bold"))
    c.create_line(x + w * 0.28, y + 8, x + w * 0.72, y + 8, arrow="both", fill=MUTED)
    c.create_text(x + w * 0.5, y + 6, text="B = 2·fm", anchor="s", fill=MUTED, font=("Segoe UI", 8))


def modulation_gallery(parent, accent):
    items = [(_mod_card(k), t("lx.mod." + k)) for k in ("am", "dsb", "fm", "pm", "ask", "fsk", "bpsk", "qpsk")]
    items.append((_am_spectrum, t("lx.mod.spec")))
    return CardGallery(parent, t("lx.title.mod"), t("lx.hint.mod"), items, accent, cell_w=250, cell_h=140)


# ---------------------------------------------------------------------------
# RF
def _two_port(c, x, y, w, h):
    bx0, bx1 = x + w * 0.33, x + w * 0.67
    c.create_rectangle(bx0, y + 12, bx1, y + h - 8, fill="#eef1f6", outline=INK, width=2)
    c.create_text((bx0 + bx1) / 2, y + h / 2 + 2, text="[S]", font=("Segoe UI", 12, "bold"), fill=INK)
    for side, xa, xb in ((1, x + 4, bx0), (2, bx1, x + w - 4)):
        ya, yb = y + h * 0.36, y + h * 0.7
        inward = side == 1
        _arrow(c, xa if inward else xb, ya, xb if inward else xa, ya, G_COL)
        _arrow(c, xb if inward else xa, yb, xa if inward else xb, yb, V_COL)
        lx = xa + 4 if inward else xb - 4
        anc = "w" if inward else "e"
        c.create_text(lx, ya - 9, text=f"a{side}", anchor=anc, fill=G_COL, font=("Segoe UI", 9, "bold"))
        c.create_text(lx, yb + 9, text=f"b{side}", anchor=anc, fill=V_COL, font=("Segoe UI", 9, "bold"))
    c.create_text(x + w / 2, y + 4, text="S11 = b1/a1   S21 = b2/a1", fill=MUTED, font=("Consolas", 8))


def _reflection(c, x, y, w, h):
    lx1 = x + w * 0.8
    y_top, y_bot = y + h * 0.28, y + h * 0.86
    c.create_line(x, y_top, lx1, y_top, fill=INK, width=2)
    c.create_line(x, y_bot, lx1, y_bot, fill=INK, width=2)
    c.create_rectangle(lx1, y_top - 2, lx1 + 14, y_bot + 2, fill="#ddd", outline=INK)
    c.create_text(lx1 + 7, (y_top + y_bot) / 2, text="ZL", font=("Segoe UI", 8, "bold"), fill=INK, angle=90)
    ya, yb = y + h * 0.44, y + h * 0.62
    _arrow(c, x + 10, ya, lx1 - 10, ya, G_COL)
    _arrow(c, lx1 - 10, yb, x + 10, yb, V_COL)
    c.create_text(x + 12, ya - 9, text="V⁺", anchor="w", fill=G_COL, font=("Segoe UI", 9, "bold"))
    c.create_text(x + 12, yb + 10, text="V⁻ = Γ·V⁺", anchor="w", fill=V_COL, font=("Segoe UI", 9, "bold"))
    c.create_text(x + w / 2, y + 2, text="Γ = (ZL − Z0) / (ZL + Z0)", anchor="n", fill=MUTED,
                  font=("Consolas", 8))


def _standing(c, x, y, w, h):
    g = 0.5
    base = y + h - 4
    c.create_line(x, base, x + w, base, fill=GRID)

    def env(s):
        return abs(1 + g * complex(math.cos(4 * math.pi * 2 * s), math.sin(4 * math.pi * 2 * s))) / (1 + g)
    pts = []
    for i in range(201):
        s = i / 200
        pts += [x + w * s, base - (h - 16) * env(s)]
    c.create_line(*pts, fill=V_COL, width=2)
    top = base - (h - 16)
    bot = base - (h - 16) * (1 - g) / (1 + g)
    c.create_line(x, top, x + w, top, fill=MUTED, dash=(3, 3))
    c.create_line(x, bot, x + w, bot, fill=MUTED, dash=(3, 3))
    c.create_text(x + w - 2, top - 1, text="Vmax", anchor="se", fill=MUTED, font=("Segoe UI", 8))
    c.create_text(x + w - 2, bot + 1, text="Vmin", anchor="ne", fill=MUTED, font=("Segoe UI", 8))
    c.create_text(x + 2, top - 1, text="|V(z)|", anchor="sw", fill=V_COL, font=("Segoe UI", 8, "bold"))


def _smith(c, x, y, w, h):
    r = min(w, h) / 2 - 4
    cx, cy = x + w / 2, y + h / 2
    c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=INK, width=2)
    c.create_line(cx - r, cy, cx + r, cy, fill=MUTED)
    for rr in (1 / 3, 1.0, 3.0):     # constant-resistance circles
        rad = r / (1 + rr)
        c.create_oval(cx + r - 2 * rad, cy - rad, cx + r, cy + rad, outline=GRID)
    for xx in (1.0,):                # x = ±1 arcs (upper / lower)
        rad = r / xx
        c.create_arc(cx + r - rad, cy - 2 * rad, cx + r + rad, cy, start=180, extent=90, style="arc",
                     outline=GRID)
        c.create_arc(cx + r - rad, cy, cx + r + rad, cy + 2 * rad, start=90, extent=90, style="arc",
                     outline=GRID)
    for px, lbl, col, anc in ((cx - r, t("lx.rf.short"), V_COL, "e"), (cx + r, t("lx.rf.open"), I_COL, "w"),
                              (cx, t("lx.rf.match"), G_COL, "n")):
        c.create_oval(px - 4, cy - 4, px + 4, cy + 4, fill=col, outline="")
        c.create_text(px + (6 if anc == "w" else -6 if anc == "e" else 0), cy + (8 if anc == "n" else 0),
                      text=lbl, anchor=anc, fill=col, font=("Segoe UI", 8, "bold"))
    c.create_text(cx, cy - r * 0.62, text="+jX  L", fill=MUTED, font=("Segoe UI", 8))
    c.create_text(cx, cy + r * 0.62, text="−jX  C", fill=MUTED, font=("Segoe UI", 8))


def _qw(c, x, y, w, h):
    my = y + h / 2
    c.create_text(x, my, text="Zin", anchor="w", fill=G_COL, font=("Segoe UI", 9, "bold"))
    x0, x1 = x + 34, x + w - 40
    c.create_line(x0, my, x1, my, fill=INK, width=2)
    c.create_rectangle(x0 + 20, my - 9, x1 - 20, my + 9, fill="#f3e9d2", outline=INK, width=2)
    c.create_text((x0 + x1) / 2, my, text="Z1 = √(Z0·ZL)", fill=INK, font=("Segoe UI", 8, "bold"))
    c.create_line(x0 + 20, my + 18, x1 - 20, my + 18, arrow="both", fill=MUTED)
    c.create_text((x0 + x1) / 2, my + 20, text="λ/4", anchor="n", fill=MUTED, font=("Segoe UI", 9, "bold"))
    c.create_rectangle(x1, my - 14, x1 + 14, my + 14, fill="#ddd", outline=INK)
    c.create_text(x1 + 18, my, text="ZL", anchor="w", fill=INK, font=("Segoe UI", 9, "bold"))


def _stub(c, x, y, w, h):
    ty = y + 14
    c.create_line(x, ty, x + w, ty, fill=INK, width=2)
    for fx, short in ((0.3, True), (0.72, False)):
        sx = x + w * fx
        yb = y + h - 26
        c.create_rectangle(sx - 7, ty, sx + 7, yb, fill="#f3e9d2", outline=INK, width=2)
        if short:
            c.create_line(sx - 12, yb, sx + 12, yb, fill=INK, width=3)
            for k in range(4):
                c.create_line(sx - 10 + k * 6, yb, sx - 13 + k * 6, yb + 5, fill=INK)
        c.create_text(sx + 16, yb, text=t("lx.rf.short") if short else t("lx.rf.open"),
                      anchor="w", fill=V_COL if short else I_COL, font=("Segoe UI", 8, "bold"))
        c.create_text(sx + 10, (ty + yb) / 2, text="ℓ", anchor="w", fill=MUTED, font=("Segoe UI", 10))


def rf_gallery(parent, accent):
    items = [(_two_port, t("lx.rf.2port")), (_reflection, t("lx.rf.refl")), (_standing, t("lx.rf.sw")),
             (_smith, t("lx.rf.smith")), (_qw, t("lx.rf.qw")), (_stub, t("lx.rf.stub"))]
    return CardGallery(parent, t("lx.title.rf"), t("lx.hint.rf"), items, accent, cell_w=250, cell_h=150)
