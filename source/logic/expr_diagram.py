"""
logic/expr_diagram.py - draw a Boolean expression tree as a gate-level
logic diagram on a Tk canvas.

  * Gates with any number of inputs (AND / OR / XOR, and their inverted
    NAND / NOR / XNOR forms when a NOT sits directly on top of them).
  * Every leaf is an input label on the left; complemented inputs get a
    small NOT gate. Wires are routed orthogonally.
  * Returns simple cost figures (gate count, gate inputs) so an entered
    circuit can be compared with its minimized version.
"""
import math

GATE_FILL = "#f5f0e2"
GATE_LINE = "#333"
WIRE = "#1f2a44"
IN_COL = "#1D4ED8"

PITCH = 26        # vertical space per input
GATE_W = 46
COL_W = 92        # horizontal space per tree level
LEFT = 34
BUB = 4


class _G:
    __slots__ = ("kind", "inv", "children", "name", "x", "y", "h", "depth", "pins", "out")

    def __init__(self, kind, inv=False, children=None, name=None):
        self.kind = kind          # 'IN', 'AND', 'OR', 'XOR', 'NOT', 'CONST'
        self.inv = inv
        self.children = children or []
        self.name = name


def _convert(node):
    k = node.kind
    if k == "VAR":
        return _G("IN", name=node.name)
    if k == "NOT":
        c = node.children[0]
        if c.kind in ("AND", "OR", "XOR") and len(c.children) >= 2:
            g = _convert(c)
            g.inv = True
            return g
        return _G("NOT", children=[_convert(c)])
    if k in ("AND", "OR") and not node.children:
        return _G("CONST", name="1" if k == "AND" else "0")
    kids = [_convert(c) for c in node.children]
    if len(kids) == 1:
        return kids[0]
    return _G(k, children=kids)


def _depth(g):
    if g.kind in ("IN", "CONST"):
        g.depth = 0
    else:
        g.depth = 1 + max(_depth(c) for c in g.children)
    return g.depth


def _cost(g):
    if g.kind in ("IN", "CONST"):
        return 0, 0
    n, i = 1, len(g.children)
    for c in g.children:
        a, b = _cost(c)
        n += a
        i += b
    return n, i


def layout_size(node):
    g = _convert(node)
    d = _depth(g)
    leaves = _count_leaves(g)
    return LEFT + 40 + (d + 1) * COL_W + 40, max(70, leaves * PITCH + 30)


def _count_leaves(g):
    if g.kind in ("IN", "CONST"):
        return 1
    return sum(_count_leaves(c) for c in g.children)


def draw(canvas, node, x0=0, y0=0, out_label="Y", col_w=None):
    """Draw `node` with its top-left corner at (x0, y0). Returns
    (width, height, gates, gate_inputs)."""
    g = _convert(node)
    depth = _depth(g)
    cw = col_w or COL_W
    right = x0 + LEFT + 30 + depth * cw
    cursor = [y0 + 18]

    def place(n):
        # x from depth (output on the right), y from the leaves below it
        n.x = right - (depth - n.depth) * cw if n.kind not in ("IN", "CONST") else x0 + LEFT
        if n.kind in ("IN", "CONST"):
            n.y = cursor[0] + PITCH / 2
            cursor[0] += PITCH
            return
        for c in n.children:
            place(c)
        ys = [c.y for c in n.children]
        n.y = (min(ys) + max(ys)) / 2
    place(g)

    def draw_node(n):
        c = canvas
        if n.kind in ("IN", "CONST"):
            n.out = (n.x + 10, n.y)
            c.create_text(n.x - 4, n.y, text=n.name, anchor="e", font=("Consolas", 11, "bold"),
                          fill=IN_COL if n.kind == "IN" else "#b45309")
            c.create_oval(n.x + 7, n.y - 3, n.x + 13, n.y + 3, fill=WIRE, outline="")
            return
        for ch in n.children:
            draw_node(ch)
        k = len(n.children)
        if n.kind == "NOT":
            h = 22
        else:
            h = max(34, min(k * 16 + 6, (k - 1) * PITCH * 0.7 + 30))
        bx0 = n.x - GATE_W
        bx1 = n.x - (2 * BUB if n.inv or n.kind == "NOT" else 0)
        by0, by1 = n.y - h / 2, n.y + h / 2
        # input pins spread evenly over the body
        pins = []
        for i in range(k):
            py = n.y if k == 1 else by0 + h * (i + 0.5) / k
            pins.append(py)
        back = bx0
        if n.kind in ("OR", "XOR"):
            back = bx0 + 6
        # wires from children (orthogonal, staggered elbows to avoid overlaps)
        order = sorted(range(k), key=lambda i: abs(pins[i] - n.y))
        for rank, i in enumerate(order):
            ch = n.children[i]
            sx, sy = ch.out
            ex = back - (8 if n.kind == "XOR" else 0)
            elbow = bx0 - 12 - rank * 5
            elbow = max(elbow, sx + 6)
            canvas.create_line(sx, sy, elbow, sy, elbow, pins[i], ex + (6 if n.kind in ("OR", "XOR") else 0),
                               pins[i], fill=WIRE, width=1.6)
            if abs(sy - pins[i]) > 1 and elbow > sx + 8 and ch.kind == "IN":
                pass
        _gate_body(canvas, n.kind, bx0, by0, bx1, by1)
        out_x = bx1
        if n.inv or n.kind == "NOT":
            canvas.create_oval(bx1, n.y - BUB, bx1 + 2 * BUB, n.y + BUB, fill="white", outline=GATE_LINE, width=1.6)
            out_x = bx1 + 2 * BUB
        n.out = (out_x, n.y)
        name = {"AND": "AND", "OR": "OR", "XOR": "XOR", "NOT": ""}[n.kind]
        if n.inv:
            name = {"AND": "NAND", "OR": "NOR", "XOR": "XNOR"}[n.kind]
        if name and h >= 30:
            canvas.create_text((bx0 + bx1) / 2 + 2, n.y, text=name, font=("Segoe UI", 6, "bold"), fill="#777")
    draw_node(g)
    ox, oy = g.out
    canvas.create_line(ox, oy, ox + 24, oy, fill=WIRE, width=1.8)
    canvas.create_oval(ox + 21, oy - 3, ox + 27, oy + 3, fill=WIRE, outline="")
    canvas.create_text(ox + 31, oy, text=out_label, anchor="w", font=("Consolas", 12, "bold"), fill="#b91c1c")
    gates, ins = _cost(g)
    return ox + 50 - x0, cursor[0] + 12 - y0, gates, ins


def _gate_body(c, kind, x0, y0, x1, y1):
    h = y1 - y0
    w = x1 - x0
    ym = (y0 + y1) / 2
    if kind == "NOT":
        c.create_polygon(x0, y0, x0, y1, x1, ym, fill=GATE_FILL, outline=GATE_LINE, width=1.8)
        return
    if kind == "AND":
        r = min(w * 0.55, h / 2)
        sx = x1 - r
        pts = [(x0, y0), (sx, y0)]
        for i in range(21):
            a = -math.pi / 2 + math.pi * i / 20
            pts.append((sx + r * math.cos(a), ym + (h / 2) * math.sin(a)))
        pts.append((x0, y1))
        c.create_polygon(*[v for p in pts for v in p], fill=GATE_FILL, outline=GATE_LINE, width=1.8)
        return
    # OR / XOR shield
    pts = []
    for i in range(15):          # back curve (concave)
        t = i / 14
        pts.append((x0 + 7 * math.sin(math.pi * t), y1 - h * t))
    for i in range(1, 15):       # top edge to the tip
        t = i / 14
        pts.append((x0 + w * t, y0 + (h / 2) * t * t))
    for i in range(1, 15):       # tip back to bottom
        t = i / 14
        pts.append((x1 - w * t, ym + (h / 2) * (2 * t - t * t)))
    c.create_polygon(*[v for p in pts for v in p], fill=GATE_FILL, outline=GATE_LINE, width=1.8, smooth=True)
    if kind == "XOR":
        c.create_line(*[v for i in range(15) for v in (x0 - 6 + 7 * math.sin(math.pi * i / 14), y1 - h * i / 14)],
                      fill=GATE_LINE, width=1.8, smooth=True)
