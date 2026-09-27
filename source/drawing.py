"""
drawing.py - Canvas drawing helpers that render visual, animated-feeling
representations of components on a tk.Canvas.
"""
import math
from data import COLOR_CODE, WIRE_COLOR, BODY_COLOR
from i18n import t
import symbols as sym


def clear(canvas):
    canvas.delete("all")


def draw_wire(canvas, x1, y1, x2, y2, width=3, color=WIRE_COLOR):
    canvas.create_line(x1, y1, x2, y2, width=width, fill=color, capstyle="round")


def draw_resistor(canvas, band_colors, w=460, h=160):
    """band_colors: ordered list of color names (4, 5 or 6 bands)."""
    clear(canvas)
    cx, cy = w / 2, h / 2
    body_w, body_h = 260, 70
    bx0, by0 = cx - body_w / 2, cy - body_h / 2
    bx1, by1 = cx + body_w / 2, cy + body_h / 2

    # leads
    draw_wire(canvas, 20, cy, bx0, cy)
    draw_wire(canvas, bx1, cy, w - 20, cy)

    # body (rounded rectangle via oval-capped rect)
    canvas.create_oval(bx0 - 18, by0, bx0 + 18, by1, fill=BODY_COLOR, outline="#8a7752", width=2)
    canvas.create_rectangle(bx0, by0, bx1, by1, fill=BODY_COLOR, outline="")
    canvas.create_oval(bx1 - 18, by0, bx1 + 18, by1, fill=BODY_COLOR, outline="#8a7752", width=2)
    canvas.create_line(bx0, by0, bx1, by0, fill="#8a7752", width=2)
    canvas.create_line(bx0, by1, bx1, by1, fill="#8a7752", width=2)

    n = len(band_colors)
    band_w = 16
    if n <= 4:
        usable_w = body_w - 50
        gap = usable_w / (n - 1) if n > 1 else 0
        start_x = bx0 + 25
        positions = [start_x + i * gap for i in range(n)]
    else:
        # 5-6 bands: evenly space all bands with consistent gaps (no cramped overlap)
        usable_w = body_w - 40
        gap = usable_w / (n - 1)
        start_x = bx0 + 20
        positions = [start_x + i * gap for i in range(n)]

    for pos, color in zip(positions, band_colors):
        hexcol = COLOR_CODE[color]["hex"]
        outline = "#000000" if hexcol.lower() in ("#f4f4f4", "#ede6da") else hexcol
        canvas.create_rectangle(pos - band_w / 2, by0 + 2, pos + band_w / 2, by1 - 2,
                                 fill=hexcol, outline=outline, width=1)


def draw_inductor(canvas, band_colors=None, w=460, h=160, loops=6):
    clear(canvas)
    cx, cy = w / 2, h / 2
    coil_w = 260
    x0, x1 = cx - coil_w / 2, cx + coil_w / 2
    draw_wire(canvas, 20, cy, x0, cy)
    draw_wire(canvas, x1, cy, w - 20, cy)

    step = coil_w / loops
    for i in range(loops):
        lx = x0 + i * step
        canvas.create_arc(lx, cy - 35, lx + step, cy + 35, start=0, extent=180,
                           style="arc", outline="#B8860B", width=5)
    if band_colors:
        # draw small color dots under the coil to show the code
        n = len(band_colors)
        gap = coil_w / (n + 1)
        for i, color in enumerate(band_colors):
            dx = x0 + gap * (i + 1)
            canvas.create_oval(dx - 7, cy + 45, dx + 7, cy + 59,
                                fill=COLOR_CODE[color]["hex"], outline="#333")


def draw_capacitor_ceramic(canvas, code_text="", w=460, h=160):
    clear(canvas)
    cx, cy = w / 2, h / 2
    draw_wire(canvas, 20, cy, cx - 65, cy)
    draw_wire(canvas, cx + 65, cy, w - 20, cy)
    # disc body
    canvas.create_oval(cx - 65, cy - 55, cx + 65, cy + 55, fill="#F4A93A", outline="#7a5210", width=3)
    canvas.create_oval(cx - 65, cy - 55, cx + 65, cy + 55, outline="#d98c1a", width=1)
    canvas.create_text(cx, cy, text=code_text, font=("Segoe UI", 16, "bold"), fill="#3a2400")
    canvas.create_text(cx, cy + 75, text=t("draw.ceramic_caption"),
                        font=("Segoe UI", 9), fill="#666")


def draw_capacitor_electrolytic(canvas, label="", w=460, h=160):
    clear(canvas)
    cx, cy = w / 2, h / 2
    body_w, body_h = 90, 130
    bx0, bx1 = cx - body_w / 2, cx + body_w / 2
    by0, by1 = cy - body_h / 2, cy + body_h / 2
    draw_wire(canvas, 20, cy, bx0, cy)
    draw_wire(canvas, bx1, cy, w - 20, cy)

    canvas.create_rectangle(bx0, by0, bx1, by1, fill="#2E5EAA", outline="#12305c", width=2)
    # top cap
    canvas.create_rectangle(bx0, by0 - 6, bx1, by0, fill="#c9c9c9", outline="#12305c")
    # minus stripe
    canvas.create_rectangle(bx1 - 14, by0, bx1, by1, fill="#e6e6e6", outline="")
    for i in range(4):
        yy = by0 + 15 + i * 25
        canvas.create_text(bx1 - 7, yy, text="-", font=("Segoe UI", 12, "bold"), fill="#222")
    canvas.create_text(bx0 + 10, by0 + 15, text="+", font=("Segoe UI", 12, "bold"), fill="#fff")
    canvas.create_text(cx - 7, cy, text=label, font=("Segoe UI", 11, "bold"), fill="#fff", angle=90)
    canvas.create_text(cx, by1 + 20, text=t("draw.electro_caption"),
                        font=("Segoe UI", 9), fill="#666")


def draw_transformer(canvas, w=460, h=200):
    clear(canvas)
    cx, cy = w / 2, h / 2
    core_x0, core_x1 = cx - 20, cx + 20
    canvas.create_rectangle(core_x0, cy - 70, core_x1, cy + 70, fill="#8a8a8a", outline="#4d4d4d", width=2)
    # primary coil (left) - each bump's bounding box is (core_x0-45, yy, core_x0+10, yy+24),
    # so its vertical spine (where leads must attach) sits at the box's x mid-point.
    primary_spine_x = core_x0 - 45 + (core_x0 + 10 - (core_x0 - 45)) / 2
    for i in range(6):
        yy = cy - 60 + i * 20
        canvas.create_arc(core_x0 - 45, yy, core_x0 + 10, yy + 24, start=90, extent=180,
                           style="arc", outline="#B8860B", width=4)
    draw_wire(canvas, 20, cy - 60, primary_spine_x, cy - 60)
    draw_wire(canvas, 20, cy + 64, primary_spine_x, cy + 64)
    # secondary coil (right)
    secondary_spine_x = core_x1 - 10 + (core_x1 + 45 - (core_x1 - 10)) / 2
    for i in range(6):
        yy = cy - 60 + i * 20
        canvas.create_arc(core_x1 - 10, yy, core_x1 + 45, yy + 24, start=270, extent=180,
                           style="arc", outline="#2A9D8F", width=4)
    draw_wire(canvas, secondary_spine_x, cy - 60, w - 20, cy - 60)
    draw_wire(canvas, secondary_spine_x, cy + 64, w - 20, cy + 64)
    canvas.create_text(cx - 90, cy + 90, text=t("draw.primary"), font=("Segoe UI", 9), fill="#7a5210")
    canvas.create_text(cx + 90, cy + 90, text=t("draw.secondary"), font=("Segoe UI", 9), fill="#1f6a5f")


def draw_diode(canvas, is_led=False, led_color="#ff4444", w=460, h=160):
    clear(canvas)
    cx, cy = w / 2, h / 2
    draw_wire(canvas, 20, cy, cx - 40, cy)
    draw_wire(canvas, cx + 40, cy, w - 20, cy)
    # triangle
    canvas.create_polygon(cx - 40, cy - 35, cx - 40, cy + 35, cx + 20, cy,
                           fill=(led_color if is_led else "#444444"), outline="#111", width=2)
    canvas.create_line(cx + 20, cy - 35, cx + 20, cy + 35, fill="#111", width=4)
    if is_led:
        # little light rays
        for dx, dy in [(20, -55), (35, -45)]:
            canvas.create_line(cx + dx, cy - 40, cx + dx + 15, cy - 55, fill=led_color, width=2, arrow="last")
        canvas.create_text(cx, cy + 60, text=t("draw.led_caption"),
                            font=("Segoe UI", 9), fill="#666")
    else:
        canvas.create_text(cx, cy + 60, text=t("draw.diode_caption"),
                            font=("Segoe UI", 9), fill="#666")


def _ground_symbol(canvas, gx, gy):
    for i, dx in enumerate([10, 6, 3]):
        canvas.create_line(gx - dx, gy + 5 + i * 5, gx + dx, gy + 5 + i * 5, fill="#333", width=2)


def _place_device(canvas, family, kind, dev_x, cy, left_x, r, s=0.8):
    """Draw the real schematic symbol of a transistor whose collector/drain
    sits on the vertical wire at x=dev_x (wires end at cy-r above and cy+r
    below), and wire its base/gate terminal left to x=left_x."""
    p_type = kind.upper().startswith("P")
    off = 10 * s if family == "jfet" else 12 * s
    cx = dev_x - off
    if family == "bjt":
        sym.bjt(canvas, cx, cy, s=s, npn=not p_type)
    elif family == "mosfet":
        sym.mosfet(canvas, cx, cy, s=s, nch=not p_type)
    else:
        sym.jfet(canvas, cx, cy, s=s, nch=not p_type)
    term = sym.device_terminals(family, cx, cy, s)
    names = list(term)
    (gx, gy), (_, top), (_, bot) = term[names[0]], term[names[1]], term[names[2]]
    if top > cy - r:
        draw_wire(canvas, dev_x, cy - r, dev_x, top)
    if bot < cy + r:
        draw_wire(canvas, dev_x, bot, dev_x, cy + r)
    draw_wire(canvas, gx, gy, left_x, gy)
    sym.node(canvas, left_x, gy)


def draw_bjt_bias_circuit(canvas, kind="NPN", r1_text="R1", r2_text="R2", rc_text="Rc", re_text="Re",
                           w=460, h=340):
    clear(canvas)
    rail_y, gnd_y = 30, h - 30
    left_x, right_x = 90, w - 60
    draw_wire(canvas, left_x, rail_y, right_x, rail_y)
    canvas.create_text(w / 2, rail_y - 15, text="Vcc", font=("Segoe UI", 10, "bold"))

    base_x, coll_x = left_x, right_x - 40
    tr_cy, r = 150, 28

    r1_y0, r1_y1 = rail_y + 15, tr_cy - 40
    draw_wire(canvas, base_x, rail_y, base_x, r1_y0)
    sym.resistor(canvas, base_x, r1_y0, base_x, r1_y1, s=0.8)
    canvas.create_text(base_x - 20, (r1_y0 + r1_y1) / 2, text=r1_text, font=("Segoe UI", 8, "bold"),
                        anchor="e", justify="right")
    draw_wire(canvas, base_x, r1_y1, base_x, tr_cy)

    r2_y0, r2_y1 = tr_cy + 40, gnd_y - 15
    draw_wire(canvas, base_x, tr_cy, base_x, r2_y0)
    sym.resistor(canvas, base_x, r2_y0, base_x, r2_y1, s=0.8)
    canvas.create_text(base_x - 20, (r2_y0 + r2_y1) / 2, text=r2_text, font=("Segoe UI", 8, "bold"),
                        anchor="e", justify="right")
    draw_wire(canvas, base_x, r2_y1, base_x, gnd_y)

    rc_y0, rc_y1 = rail_y + 15, tr_cy - r - 20
    draw_wire(canvas, coll_x, rail_y, coll_x, rc_y0)
    sym.resistor(canvas, coll_x, rc_y0, coll_x, rc_y1, s=0.8)
    canvas.create_text(coll_x + 20, (rc_y0 + rc_y1) / 2, text=rc_text, font=("Segoe UI", 8, "bold"),
                        anchor="w", justify="left")
    draw_wire(canvas, coll_x, rc_y1, coll_x, tr_cy - r)

    re_y0, re_y1 = tr_cy + r + 20, gnd_y - 15
    draw_wire(canvas, coll_x, tr_cy + r, coll_x, re_y0)
    sym.resistor(canvas, coll_x, re_y0, coll_x, re_y1, s=0.8)
    canvas.create_text(coll_x + 20, (re_y0 + re_y1) / 2, text=re_text, font=("Segoe UI", 8, "bold"),
                        anchor="w", justify="left")
    draw_wire(canvas, coll_x, re_y1, coll_x, gnd_y)

    _place_device(canvas, "bjt", kind, coll_x, tr_cy, base_x, r)

    draw_wire(canvas, base_x, gnd_y, coll_x, gnd_y)
    _ground_symbol(canvas, base_x, gnd_y)
    _ground_symbol(canvas, coll_x, gnd_y)


def draw_mosfet_bias_circuit(canvas, kind="N-channel", r1_text="R1", r2_text="R2", rd_text="Rd", rs_text="Rs",
                              w=460, h=340):
    clear(canvas)
    rail_y, gnd_y = 30, h - 30
    left_x, right_x = 90, w - 60
    draw_wire(canvas, left_x, rail_y, right_x, rail_y)
    canvas.create_text(w / 2, rail_y - 15, text="Vdd", font=("Segoe UI", 10, "bold"))

    gate_x, drain_x = left_x, right_x - 40
    tr_cy, r = 150, 28

    r1_y0, r1_y1 = rail_y + 15, tr_cy - 40
    draw_wire(canvas, gate_x, rail_y, gate_x, r1_y0)
    sym.resistor(canvas, gate_x, r1_y0, gate_x, r1_y1, s=0.8)
    canvas.create_text(gate_x - 20, (r1_y0 + r1_y1) / 2, text=r1_text, font=("Segoe UI", 8, "bold"),
                        anchor="e", justify="right")
    draw_wire(canvas, gate_x, r1_y1, gate_x, tr_cy)

    r2_y0, r2_y1 = tr_cy + 40, gnd_y - 15
    draw_wire(canvas, gate_x, tr_cy, gate_x, r2_y0)
    sym.resistor(canvas, gate_x, r2_y0, gate_x, r2_y1, s=0.8)
    canvas.create_text(gate_x - 20, (r2_y0 + r2_y1) / 2, text=r2_text, font=("Segoe UI", 8, "bold"),
                        anchor="e", justify="right")
    draw_wire(canvas, gate_x, r2_y1, gate_x, gnd_y)

    rd_y0, rd_y1 = rail_y + 15, tr_cy - r - 20
    draw_wire(canvas, drain_x, rail_y, drain_x, rd_y0)
    sym.resistor(canvas, drain_x, rd_y0, drain_x, rd_y1, s=0.8)
    canvas.create_text(drain_x + 20, (rd_y0 + rd_y1) / 2, text=rd_text, font=("Segoe UI", 8, "bold"),
                        anchor="w", justify="left")
    draw_wire(canvas, drain_x, rd_y1, drain_x, tr_cy - r)

    rs_y0, rs_y1 = tr_cy + r + 20, gnd_y - 15
    draw_wire(canvas, drain_x, tr_cy + r, drain_x, rs_y0)
    sym.resistor(canvas, drain_x, rs_y0, drain_x, rs_y1, s=0.8)
    canvas.create_text(drain_x + 20, (rs_y0 + rs_y1) / 2, text=rs_text, font=("Segoe UI", 8, "bold"),
                        anchor="w", justify="left")
    draw_wire(canvas, drain_x, rs_y1, drain_x, gnd_y)

    _place_device(canvas, "mosfet", kind, drain_x, tr_cy, gate_x, r)

    draw_wire(canvas, gate_x, gnd_y, drain_x, gnd_y)
    _ground_symbol(canvas, gate_x, gnd_y)
    _ground_symbol(canvas, drain_x, gnd_y)


def draw_jfet_bias_circuit(canvas, kind="N-channel", rd_text="Rd", rs_text="Rs", rg_text="Rg", w=460, h=340):
    clear(canvas)
    rail_y, gnd_y = 30, h - 30
    left_x, right_x = 90, w - 60
    draw_wire(canvas, left_x, rail_y, right_x, rail_y)
    canvas.create_text(w / 2, rail_y - 15, text="Vdd", font=("Segoe UI", 10, "bold"))

    gate_x, drain_x = left_x, right_x - 40
    tr_cy, r = 150, 28

    # Gate self-bias resistor Rg (ties the gate to ground; carries ~0 A since
    # the gate junction is reverse-biased, but it still needs its own symbol
    # like every other resistor in the circuit, not just a bare labeled wire).
    rg_y0, rg_y1 = tr_cy + 25, gnd_y - 15
    draw_wire(canvas, gate_x, tr_cy, gate_x, rg_y0)
    sym.resistor(canvas, gate_x, rg_y0, gate_x, rg_y1, s=0.8)
    canvas.create_text(gate_x - 20, (rg_y0 + rg_y1) / 2, text=rg_text, font=("Segoe UI", 8, "bold"),
                        anchor="e", justify="right")
    draw_wire(canvas, gate_x, rg_y1, gate_x, gnd_y)

    rd_y0, rd_y1 = rail_y + 15, tr_cy - r - 20
    draw_wire(canvas, drain_x, rail_y, drain_x, rd_y0)
    sym.resistor(canvas, drain_x, rd_y0, drain_x, rd_y1, s=0.8)
    canvas.create_text(drain_x + 20, (rd_y0 + rd_y1) / 2, text=rd_text, font=("Segoe UI", 8, "bold"),
                        anchor="w", justify="left")
    draw_wire(canvas, drain_x, rd_y1, drain_x, tr_cy - r)

    rs_y0, rs_y1 = tr_cy + r + 20, gnd_y - 15
    draw_wire(canvas, drain_x, tr_cy + r, drain_x, rs_y0)
    sym.resistor(canvas, drain_x, rs_y0, drain_x, rs_y1, s=0.8)
    canvas.create_text(drain_x + 20, (rs_y0 + rs_y1) / 2, text=rs_text, font=("Segoe UI", 8, "bold"),
                        anchor="w", justify="left")
    draw_wire(canvas, drain_x, rs_y1, drain_x, gnd_y)

    _place_device(canvas, "jfet", kind, drain_x, tr_cy, gate_x, r)

    draw_wire(canvas, gate_x, gnd_y, drain_x, gnd_y)
    _ground_symbol(canvas, gate_x, gnd_y)
    _ground_symbol(canvas, drain_x, gnd_y)


def draw_transistor(canvas, kind="NPN", w=460, h=200):
    clear(canvas)
    cx, cy = w / 2, h / 2
    r = min(60, w * 0.22, h * 0.35)
    s = r / 60.0
    lw = max(2, round(3 * s))
    canvas.create_oval(cx - r, cy - r, cx + r, cy + r, outline="#333", width=2)
    # base line
    canvas.create_line(cx - 10 * s, cy - 30 * s, cx - 10 * s, cy + 30 * s, fill="#111", width=lw + 1)
    canvas.create_line(cx - r - 30 * s, cy, cx - 10 * s, cy, fill="#111", width=lw)
    # collector (top right) & emitter (bottom right)
    canvas.create_line(cx - 10 * s, cy - 15 * s, cx + 35 * s, cy - 45 * s, fill="#111", width=lw)
    canvas.create_line(cx + 35 * s, cy - 45 * s, cx + 35 * s, cy - r - 20 * s, fill="#111", width=lw)
    canvas.create_line(cx - 10 * s, cy + 15 * s, cx + 35 * s, cy + 45 * s, fill="#111", width=lw)
    canvas.create_line(cx + 35 * s, cy + 45 * s, cx + 35 * s, cy + r + 20 * s, fill="#111", width=lw)
    arrow_out = kind.upper() == "NPN"
    if arrow_out:
        canvas.create_line(cx - 10 * s, cy + 15 * s, cx + 20 * s, cy + 32 * s, fill="#111", width=lw, arrow="last")
    else:
        canvas.create_line(cx + 20 * s, cy + 32 * s, cx - 10 * s, cy + 15 * s, fill="#111", width=lw, arrow="last")
    fsz = max(8, round(11 * s))
    canvas.create_text(cx - r - 30 * s - 15, cy, text="B", font=("Segoe UI", fsz, "bold"))
    canvas.create_text(cx + 35 * s, cy - r - 30 * s, text="C", font=("Segoe UI", fsz, "bold"))
    canvas.create_text(cx + 35 * s, cy + r + 32 * s, text="E", font=("Segoe UI", fsz, "bold"))
    canvas.create_text(cx, cy + r + 20 * s + 35, text=f"{kind.upper()} {t('draw.bjt_suffix')}",
                        font=("Segoe UI", 9), fill="#666", width=min(w - 10, 260), justify="center")


def draw_mosfet_symbol(canvas, kind="N-channel", w=460, h=200):
    clear(canvas)
    is_n = kind.lower().startswith("n")
    cx, cy = w / 2, h / 2
    s = min(1.0, w / 300, h / 200)
    bar_top, bar_bot = cy - 45 * s, cy + 45 * s
    seg_gap = 7 * s
    seg_h = (bar_bot - bar_top - 2 * seg_gap) / 3
    lw = max(2, round(4 * s))
    for i in range(3):
        y0 = bar_top + i * (seg_h + seg_gap)
        canvas.create_line(cx, y0, cx, y0 + seg_h, width=lw, fill="#111")

    gate_x = cx - 26 * s
    canvas.create_line(gate_x, bar_top, gate_x, bar_bot, width=lw, fill="#111")
    canvas.create_line(gate_x - 40 * s, cy, gate_x, cy, fill="#111", width=max(2, round(3 * s)))
    fsz = max(8, round(11 * s))
    canvas.create_text(gate_x - 50 * s, cy, text="G", font=("Segoe UI", fsz, "bold"), anchor="e")

    canvas.create_line(cx, bar_top, cx, bar_top - 35 * s, fill="#111", width=max(2, round(3 * s)))
    canvas.create_text(cx, bar_top - 45 * s, text="D", font=("Segoe UI", fsz, "bold"))
    canvas.create_line(cx, bar_bot, cx, bar_bot + 35 * s, fill="#111", width=max(2, round(3 * s)))
    canvas.create_text(cx, bar_bot + 45 * s, text="S", font=("Segoe UI", fsz, "bold"))

    if is_n:
        canvas.create_line(gate_x + 16 * s, cy + 16 * s, cx - 2, cy, fill="#111",
                            width=max(2, round(3 * s)), arrow="last")
    else:
        canvas.create_line(cx - 2, cy, gate_x + 16 * s, cy + 16 * s, fill="#111",
                            width=max(2, round(3 * s)), arrow="last")

    canvas.create_text(cx, bar_bot + 65 * s, text=f"{kind} MOSFET", font=("Segoe UI", 9), fill="#666",
                        width=min(w - 10, 260), justify="center")


def draw_jfet_symbol(canvas, kind="N-channel", w=460, h=200):
    clear(canvas)
    is_n = kind.lower().startswith("n")
    cx, cy = w / 2, h / 2
    s = min(1.0, w / 300, h / 200)
    bar_top, bar_bot = cy - 45 * s, cy + 45 * s
    lw = max(2, round(4 * s))
    canvas.create_line(cx, bar_top, cx, bar_bot, width=lw, fill="#111")

    fsz = max(8, round(11 * s))
    canvas.create_line(cx, bar_top, cx, bar_top - 35 * s, fill="#111", width=max(2, round(3 * s)))
    canvas.create_text(cx, bar_top - 45 * s, text="D", font=("Segoe UI", fsz, "bold"))
    canvas.create_line(cx, bar_bot, cx, bar_bot + 35 * s, fill="#111", width=max(2, round(3 * s)))
    canvas.create_text(cx, bar_bot + 45 * s, text="S", font=("Segoe UI", fsz, "bold"))

    gate_x = cx - 55 * s
    canvas.create_line(gate_x - 35 * s, cy, gate_x, cy, fill="#111", width=max(2, round(3 * s)))
    canvas.create_text(gate_x - 45 * s, cy, text="G", font=("Segoe UI", fsz, "bold"), anchor="e")
    if is_n:
        canvas.create_line(gate_x, cy, cx - 2, cy, fill="#111", width=max(2, round(3 * s)), arrow="last")
    else:
        canvas.create_line(cx - 2, cy, gate_x, cy, fill="#111", width=max(2, round(3 * s)), arrow="last")

    canvas.create_text(cx, bar_bot + 65 * s, text=f"{kind} JFET", font=("Segoe UI", 9), fill="#666",
                        width=min(w - 10, 260), justify="center")


_N_COLOR = "#a8d4f0"
_P_COLOR = "#f5b8c4"
_DEPLETION_COLOR = "#f4f4f4"
_CHANNEL_COLOR = "#7ec8f2"
_CHANNEL_COLOR_P = "#f0a0b8"


def draw_bjt_junction(canvas, kind="NPN", vbe=0.7, vce=5.0, w=460, h=280):
    """Illustrative cross-section of a BJT showing depletion regions at both
    junctions, widening/narrowing with bias, plus majority-carrier flow arrows
    when in forward-active operation."""
    clear(canvas)
    npn = kind.upper() == "NPN"
    outer_color = _N_COLOR if npn else _P_COLOR
    inner_color = _P_COLOR if npn else _N_COLOR
    carrier = "e⁻" if npn else "h⁺"
    vcb = vce - vbe

    # --- region determination, tied to both junctions (not just Vce) ---
    if vbe < 0.5:
        state = "cutoff"
    elif vcb > 0.2:
        state = "active"
    else:
        state = "saturation"

    body_top, body_bot = 66, h - 86
    body_left, body_right = 40, w - 40
    total_w = body_right - body_left

    # depletion widths (illustrative, clamped) - both shrink when forward biased
    dw_eb = max(4, min(42, 34 * (1 - max(-1.0, min(vbe, 0.7)) / 0.7)))
    if state == "saturation":
        dw_cb = max(4, min(70, 10 + 3.0 * max(0.0, vcb)))
    else:
        dw_cb = max(10, min(70, 16 + 3.2 * max(0.0, vcb)))

    e_w = total_w * 0.24
    b_w = total_w * 0.20
    c_w = total_w - e_w - b_w - dw_eb - dw_cb

    x0 = body_left
    x1 = x0 + e_w
    x2 = x1 + dw_eb
    x3 = x2 + b_w
    x4 = x3 + dw_cb
    x5 = body_right

    canvas.create_rectangle(x0, body_top, x1, body_bot, fill=outer_color, outline="#333", width=2)
    canvas.create_rectangle(x1, body_top, x2, body_bot, fill=_DEPLETION_COLOR, outline="", width=0)
    canvas.create_rectangle(x2, body_top, x3, body_bot, fill=inner_color, outline="#333", width=2)
    canvas.create_rectangle(x3, body_top, x4, body_bot, fill=_DEPLETION_COLOR, outline="", width=0)
    canvas.create_rectangle(x4, body_top, x5, body_bot, fill=outer_color, outline="#333", width=2)
    canvas.create_line(x1, body_top, x1, body_bot, fill="#888", dash=(3, 2))
    canvas.create_line(x2, body_top, x2, body_bot, fill="#888", dash=(3, 2))
    canvas.create_line(x3, body_top, x3, body_bot, fill="#888", dash=(3, 2))
    canvas.create_line(x4, body_top, x4, body_bot, fill="#888", dash=(3, 2))

    label_e = "N" if npn else "P"
    label_b = "P" if npn else "N"
    mid_y = (body_top + body_bot) / 2
    canvas.create_text((x0 + x1) / 2, mid_y - 12, text=f"{label_e}\n(Emitter)", font=("Segoe UI", 9, "bold"))
    canvas.create_text((x2 + x3) / 2, mid_y - 12, text=f"{label_b}\n(Base)", font=("Segoe UI", 9, "bold"))
    canvas.create_text((x4 + x5) / 2, mid_y - 12, text=f"{label_e}\n(Collector)", font=("Segoe UI", 9, "bold"))

    # terminal leads
    draw_wire(canvas, (x0 + x1) / 2, body_top, (x0 + x1) / 2, body_top - 30)
    draw_wire(canvas, (x2 + x3) / 2, body_top - 30, (x2 + x3) / 2, 20)
    draw_wire(canvas, (x2 + x3) / 2, 20, (x0 + x1) / 2 - 5, 20)
    canvas.create_text((x0 + x1) / 2, body_top - 40, text="E", font=("Segoe UI", 11, "bold"))
    canvas.create_text((x2 + x3) / 2 - 20, 20, text="B", font=("Segoe UI", 11, "bold"))
    draw_wire(canvas, (x4 + x5) / 2, body_top, (x4 + x5) / 2, body_top - 30)
    canvas.create_text((x4 + x5) / 2, body_top - 40, text="C", font=("Segoe UI", 11, "bold"))

    if state == "active":
        n_arrows = 4
        for i in range(n_arrows):
            ax = x0 + (i + 1) * (x5 - x0) / (n_arrows + 1)
            canvas.create_line(ax, mid_y + 22, ax + 22, mid_y + 22, fill="#1f6a5f", width=2, arrow="last")
        banner = f"{carrier}  {t('junction.flow_label')}: E → B → C   ({t('junction.state_active')})"
        banner_color = "#1f6a5f"
    elif state == "saturation":
        banner = t("junction.state_saturation")
        banner_color = "#b3691d"
    else:
        banner = t("junction.state_cutoff")
        banner_color = "#999"

    canvas.create_text(w / 2, body_top - 55, text=f"{kind.upper()}", font=("Segoe UI", 10, "bold"), fill="#555")
    canvas.create_text(w / 2, body_bot + 18, text=banner, font=("Segoe UI", 9, "bold"), fill=banner_color)
    canvas.create_text((x1 + x2) / 2, body_bot + 40, text=t("junction.depletion_eb_short"),
                        font=("Segoe UI", 7), fill="#777")
    canvas.create_text((x3 + x4) / 2, body_bot + 40, text=t("junction.depletion_cb_short"),
                        font=("Segoe UI", 7), fill="#777")


def draw_mosfet_junction(canvas, kind="N-channel", vgs=0.0, vds=0.0, vth=2.0, w=460, h=280):
    """Illustrative cross-section of an enhancement MOSFET: substrate, source/
    drain wells, gate oxide, and a full-height inversion channel that forms
    (and shows a growing depletion wedge pinching it off near the drain in
    saturation) as bias changes."""
    clear(canvas)
    is_n = kind.lower().startswith("n")
    sign = 1 if is_n else -1
    substrate_color = _P_COLOR if is_n else _N_COLOR
    well_color = _N_COLOR if is_n else _P_COLOR
    channel_color = _CHANNEL_COLOR if is_n else _CHANNEL_COLOR_P

    body_left, body_right = 55, w - 55
    body_top, body_bot = 100, h - 55
    well_w = (body_right - body_left) * 0.20
    well_top = body_top + 6
    well_bot = body_bot - 14

    canvas.create_rectangle(body_left, body_top, body_right, body_bot,
                             fill=substrate_color, outline="#333", width=2)

    sx0, sx1 = body_left + 12, body_left + 12 + well_w
    dx0, dx1 = body_right - 12 - well_w, body_right - 12
    canvas.create_rectangle(sx0, well_top, sx1, well_bot, fill=well_color, outline="#333", width=2)
    canvas.create_rectangle(dx0, well_top, dx1, well_bot, fill=well_color, outline="#333", width=2)
    canvas.create_text((sx0 + sx1) / 2, (well_top + well_bot) / 2, text="S", font=("Segoe UI", 10, "bold"))
    canvas.create_text((dx0 + dx1) / 2, (well_top + well_bot) / 2, text="D", font=("Segoe UI", 10, "bold"))

    # gate oxide + metal gate
    ox_top, ox_bot = body_top - 10, body_top
    gate_left, gate_right = sx1 - 6, dx0 + 6
    gate_cx = (gate_left + gate_right) / 2
    canvas.create_rectangle(gate_left, ox_top, gate_right, ox_bot, fill="#fff2b8", outline="#8a7752", width=1)
    canvas.create_rectangle(gate_left, ox_top - 16, gate_right, ox_top, fill="#999", outline="#333", width=2)
    gate_attach_y = ox_top - 16
    draw_wire(canvas, gate_cx, gate_attach_y, gate_cx, gate_attach_y - 30)
    canvas.create_text(gate_cx, gate_attach_y - 40, text="G", font=("Segoe UI", 11, "bold"))

    overdrive = sign * (vgs - vth)
    on = overdrive > 0

    ch_left, ch_right = sx1, dx0
    ch_top, ch_bot = well_top, well_bot  # full well height -> a solid, blocky channel (not a thin sliver)

    if on:
        canvas.create_rectangle(ch_left, ch_top, ch_right, ch_bot, fill=channel_color, outline="")
        # a depletion wedge grows in from the drain side once Vds exceeds the
        # overdrive voltage, visually "pinching" the channel closed
        excess = sign * vds - overdrive
        pinch_frac = 0.0
        if excess > 0:
            pinch_frac = min(0.90, 0.20 + 0.6 * excess / (abs(overdrive) + excess + 1e-6))
        if pinch_frac > 0:
            wedge_w = (ch_right - ch_left) * pinch_frac
            apex_x = ch_right - wedge_w
            canvas.create_polygon(ch_right, ch_top, apex_x, (ch_top + ch_bot) / 2, ch_right, ch_bot,
                                   fill=substrate_color, outline="#333", width=1)
            state_text = t("junction.state_saturation_fet")
            state_color = "#b3691d"
            arrow_limit = apex_x
        else:
            state_text = t("junction.state_triode")
            state_color = "#1f6a5f"
            arrow_limit = ch_right
        usable = arrow_limit - ch_left
        if usable > 30:
            n_arrows = 3
            for i in range(n_arrows):
                ax = ch_left + 10 + i * (usable - 24) / max(1, n_arrows - 1)
                canvas.create_line(ax, (ch_top + ch_bot) / 2, ax + 14, (ch_top + ch_bot) / 2,
                                    fill="#1f6a5f", width=2, arrow="last")
        canvas.create_text((ch_left + ch_right) / 2, ch_bot + 18, text=state_text,
                            font=("Segoe UI", 8, "bold"), fill=state_color)
    else:
        for wx0, wx1 in [(sx0, sx1), (dx0, dx1)]:
            canvas.create_oval(wx0 - 6, well_top - 4, wx1 + 6, well_bot + 10,
                                outline="#bbb", width=1, dash=(2, 2))
        canvas.create_text((ch_left + ch_right) / 2, ch_bot + 18, text=t("junction.state_cutoff"),
                            font=("Segoe UI", 8, "bold"), fill="#999")

    draw_wire(canvas, (sx0 + sx1) / 2, well_top, (sx0 + sx1) / 2, well_top - 30)
    canvas.create_text((sx0 + sx1) / 2, well_top - 40, text="S", font=("Segoe UI", 10, "bold"))
    draw_wire(canvas, (dx0 + dx1) / 2, well_top, (dx0 + dx1) / 2, well_top - 30)
    canvas.create_text((dx0 + dx1) / 2, well_top - 40, text="D", font=("Segoe UI", 10, "bold"))
    draw_wire(canvas, (body_left + body_right) / 2, body_bot, (body_left + body_right) / 2, body_bot + 22)
    canvas.create_text((body_left + body_right) / 2, body_bot + 32, text="B", font=("Segoe UI", 9), fill="#666")

    canvas.create_text(w / 2, body_top - 58, text=f"{kind} MOSFET", font=("Segoe UI", 10, "bold"), fill="#555")


def draw_jfet_junction(canvas, kind="N-channel", vgs=0.0, vp=-4.0, w=460, h=280):
    """Illustrative cross-section of a JFET: a conductive channel with gate
    p-n junctions above and below that narrow (and eventually pinch off) the
    channel as the reverse gate bias increases."""
    clear(canvas)
    is_n = kind.lower().startswith("n")
    channel_color = _CHANNEL_COLOR if is_n else _CHANNEL_COLOR_P
    gate_color = _P_COLOR if is_n else _N_COLOR

    body_left, body_right = 50, w - 50
    ch_top, ch_bot = 100, h - 100
    ch_height = ch_bot - ch_top

    frac = 0.0
    if vp != 0:
        frac = vgs / vp  # same sign for both vgs and vp within normal operating range -> ratio in [0,1]
    frac = max(0.0, min(1.0, frac))
    pinch = min(0.49, 0.49 * frac)

    canvas.create_rectangle(body_left, ch_top, body_right, ch_bot, fill=channel_color, outline="#333", width=2)
    if pinch > 0:
        canvas.create_rectangle(body_left, ch_top, body_right, ch_top + ch_height * pinch,
                                 fill=_DEPLETION_COLOR, outline="")
        canvas.create_rectangle(body_left, ch_bot - ch_height * pinch, body_right, ch_bot,
                                 fill=_DEPLETION_COLOR, outline="")
        canvas.create_line(body_left, ch_top + ch_height * pinch, body_right, ch_top + ch_height * pinch,
                            fill="#888", dash=(3, 2))
        canvas.create_line(body_left, ch_bot - ch_height * pinch, body_right, ch_bot - ch_height * pinch,
                            fill="#888", dash=(3, 2))

    gate_h = 22
    canvas.create_rectangle(body_left + 30, ch_top - gate_h, body_right - 30, ch_top,
                             fill=gate_color, outline="#333", width=2)
    canvas.create_rectangle(body_left + 30, ch_bot, body_right - 30, ch_bot + gate_h,
                             fill=gate_color, outline="#333", width=2)
    canvas.create_text(w / 2, ch_top - gate_h / 2, text="G", font=("Segoe UI", 9, "bold"))
    canvas.create_text(w / 2, ch_bot + gate_h / 2, text="G", font=("Segoe UI", 9, "bold"))
    draw_wire(canvas, w / 2, ch_top - gate_h, w / 2, ch_top - gate_h - 25)
    canvas.create_text(w / 2, ch_top - gate_h - 35, text="G", font=("Segoe UI", 11, "bold"))

    draw_wire(canvas, body_left, (ch_top + ch_bot) / 2, body_left - 30, (ch_top + ch_bot) / 2)
    canvas.create_text(body_left - 40, (ch_top + ch_bot) / 2, text="S", font=("Segoe UI", 11, "bold"))
    draw_wire(canvas, body_right, (ch_top + ch_bot) / 2, body_right + 30, (ch_top + ch_bot) / 2)
    canvas.create_text(body_right + 40, (ch_top + ch_bot) / 2, text="D", font=("Segoe UI", 11, "bold"))

    if pinch >= 0.485:
        canvas.create_text(w / 2, ch_bot + gate_h + 20, text=t("junction.state_pinchoff"),
                            font=("Segoe UI", 9, "bold"), fill="#b3691d")
    else:
        mid_y = (ch_top + ch_bot) / 2
        for i in range(3):
            ax = body_left + (i + 1) * (body_right - body_left) / 4
            canvas.create_line(ax, mid_y, ax + 16, mid_y, fill="#1f6a5f", width=2, arrow="last")
        canvas.create_text(w / 2, ch_bot + gate_h + 20, text=t("junction.state_conducting"),
                            font=("Segoe UI", 9, "bold"), fill="#1f6a5f")

    canvas.create_text(w / 2, ch_top - gate_h - 45, text=f"{kind} JFET", font=("Segoe UI", 10, "bold"), fill="#555")


def draw_opamp(canvas, w=460, h=220, mode="inverting", rin_text="Rin", rf_text="Rf"):
    """Op-amp amplifier schematic with the standard triangle symbol.
    mode: 'inverting'     -> Vin -[Rin]- (-) , (+) to ground, Rf feedback
          'noninverting'  -> Vin -> (+),  (-) -[Rin]- ground, Rf feedback"""
    clear(canvas)
    s = 1.0
    cx, cy = w / 2 + 20, h / 2 + 15
    left = cx - 30
    inv_y, non_y = cy - 14, cy + 14
    out_x = cx + 48
    sym.opamp(canvas, cx, cy, s=s)
    in_node_x = left - 30
    fb_y = cy - 75
    # output
    sym.wire(canvas, out_x, cy, w - 30, cy)
    sym.terminal(canvas, w - 30, cy, label="Vout")
    # feedback resistor from (-) node to output
    sym.wire(canvas, left - 18, inv_y, in_node_x, inv_y)
    sym.wire(canvas, in_node_x, inv_y, in_node_x, fb_y)
    sym.resistor(canvas, in_node_x, fb_y, out_x + 10, fb_y, label=rf_text)
    sym.wire(canvas, out_x + 10, fb_y, out_x + 10, cy)
    sym.node(canvas, out_x + 10, cy)
    sym.node(canvas, in_node_x, inv_y)
    if mode == "inverting":
        sym.resistor(canvas, 40, inv_y, in_node_x, inv_y, label=rin_text)
        sym.terminal(canvas, 40, inv_y, label="Vin")
        sym.wire(canvas, left - 18, non_y, in_node_x + 10, non_y)
        sym.wire(canvas, in_node_x + 10, non_y, in_node_x + 10, h - 30)
        sym.ground(canvas, in_node_x + 10, h - 30)
    else:
        sym.wire(canvas, 40, non_y, left - 18, non_y)
        sym.terminal(canvas, 40, non_y, label="Vin", anchor="n", dy=8)
        sym.wire(canvas, in_node_x, inv_y, in_node_x - 40, inv_y)
        sym.resistor(canvas, in_node_x - 40, inv_y, in_node_x - 40, h - 25, label=rin_text,
                     label_side=-1)
        sym.ground(canvas, in_node_x - 40, h - 25)


_COMBO_STYLE = {
    "resistor":  {"label": "R", "fill": "#EDE0C8", "outline": "#8a7752"},
    "capacitor": {"label": "C", "fill": "#F4A93A", "outline": "#7a5210"},
    "inductor":  {"label": "L", "fill": "#e9c46a", "outline": "#7a5210"},
}


def draw_combo_diagram(canvas, values, mode, kind, w=460, h=200, labels=None, unit=None):
    """Schematic of N same-type components in series or parallel, drawn
    with the real schematic symbol (resistor / capacitor / inductor).
    `labels`, if given, overrides the auto-generated R1/C1/L1... names."""
    clear(canvas)
    n = len(values)
    if n == 0:
        return
    try:
        w = max(w, int(canvas.winfo_width())) if int(canvas.winfo_width()) > 50 else w
    except Exception:
        pass
    prefix = sym.PREFIX_BY_KIND.get(kind, "R")
    unit = unit if unit is not None else {"resistor": "Ω", "capacitor": "F", "inductor": "H"}.get(kind, "")
    names = labels if labels is not None else [f"{prefix}{i + 1}" for i in range(n)]
    cy = h / 2
    term_l, term_r = 22, w - 22
    if mode == "series":
        span = (term_r - term_l - 20) / n
        s = max(0.55, min(1.0, span / 95))
        canvas.configure(height=h)
        sym.wire(canvas, term_l, cy, term_l + 10, cy)
        x = term_l + 10
        for i, val in enumerate(values):
            sym.component(canvas, kind, x, cy, x + span, cy, label=names[i],
                          value=_short(val) + unit, s=s)
            x += span
        sym.wire(canvas, x, cy, term_r, cy)
    else:
        spacing = 52
        need_h = max(h, int(n * spacing + 50))
        canvas.configure(height=need_h)
        top = need_h / 2 - (n - 1) * spacing / 2
        bot = top + (n - 1) * spacing
        cy = need_h / 2
        left_x, right_x = term_l + 40, term_r - 40
        sym.wire(canvas, term_l, cy, left_x, cy)
        sym.wire(canvas, right_x, cy, term_r, cy)
        sym.wire(canvas, left_x, top, left_x, bot)
        sym.wire(canvas, right_x, top, right_x, bot)
        sym.node(canvas, left_x, cy)
        sym.node(canvas, right_x, cy)
        mid = (left_x + right_x) / 2
        for i, val in enumerate(values):
            yy = top + i * spacing
            sym.component(canvas, kind, left_x, yy, right_x, yy, s=0.85)
            canvas.create_text(left_x + 8, yy - 5, text=f"{names[i]} = {_short(val)}{unit}",
                               anchor="sw", font=("Segoe UI", 8, "bold"), fill=sym.LABEL_COLOR)
        cy_term = cy
    sym.terminal(canvas, term_l, cy, label="A")
    sym.terminal(canvas, term_r, cy, label="B")


def _short(val):
    prefixes = [("G", 1e9), ("M", 1e6), ("k", 1e3), ("", 1), ("m", 1e-3),
                ("µ", 1e-6), ("n", 1e-9), ("p", 1e-12)]
    av = abs(val)
    if av == 0:
        return "0"
    for sym, factor in prefixes:
        if av >= factor:
            return f"{val/factor:g}{sym}"
    return f"{val:g}"


def draw_divider_diagram(canvas, series_kind, series_val, shunt_kind, shunt_val, w=460, h=220,
                          series2_kind=None, series2_val=None, shunt2_kind=None, shunt2_val=None):
    """Series + shunt divider/filter drawn with real schematic symbols:
    Vin -> [Z1 series] -> node A -> Vout, with [Z2] from A to ground.
    With a second stage: A -> [Z3 series] -> node B (Vout), [Z4] B to ground.
    Each part is named by its type and position (e.g. R1, C2, R3, C4) so the
    names match the stage cards on the left."""
    clear(canvas)
    has_stage2 = series2_kind is not None
    s = max(0.6, min(1.1, w / 460))
    left_x = 34 * s
    right_x = w - 28 * s
    node_y = 62 * s
    ground_y = h - 30
    units = {"resistor": "Ω", "capacitor": "F", "inductor": "H"}

    def name(kind, idx):
        return f"{sym.PREFIX_BY_KIND.get(kind, 'Z')}{idx}"

    def series_part(x1, x2, kind, val, idx):
        sym.component(canvas, kind, x1, node_y, x2, node_y, label=name(kind, idx),
                      value=_short(val) + units.get(kind, ""), s=s)

    def shunt_part(x, kind, val, idx):
        top = node_y + 18 * s
        sym.wire(canvas, x, node_y, x, top)
        side = -1 if x > w * 0.55 else 1
        sym.component(canvas, kind, x, top, x, ground_y, label=name(kind, idx),
                      value=_short(val) + units.get(kind, ""), s=s, label_side=side)
        sym.ground(canvas, x, ground_y, s=s)
        sym.node(canvas, x, node_y, s=s)

    if not has_stage2:
        node_a_x = w * 0.64
        series_part(left_x, node_a_x, series_kind, series_val, 1)
        sym.wire(canvas, node_a_x, node_y, right_x, node_y)
        shunt_part(node_a_x, shunt_kind, shunt_val, 2)
    else:
        node_a_x = w * 0.40
        node_b_x = w * 0.80
        series_part(left_x, node_a_x, series_kind, series_val, 1)
        shunt_part(node_a_x, shunt_kind, shunt_val, 2)
        series_part(node_a_x, node_b_x, series2_kind, series2_val, 3)
        sym.wire(canvas, node_b_x, node_y, right_x, node_y)
        shunt_part(node_b_x, shunt2_kind, shunt2_val, 4)
        canvas.create_text(node_a_x + 6 * s, node_y + 12 * s, text="A", anchor="nw",
                           font=("Segoe UI", max(7, round(9 * s)), "bold"), fill="#8854d0")
    sym.terminal(canvas, left_x, node_y, s=s, label="Vin", anchor="s", dy=-9)
    sym.terminal(canvas, right_x, node_y, s=s, label="Vout", anchor="s", dy=-9)


def _draw_cell(canvas, x, cy, cell_w, cell_h, label):
    canvas.create_rectangle(x, cy - cell_h * 0.5, x + cell_w * 0.15, cy + cell_h * 0.5,
                             fill="#333", outline="")
    canvas.create_rectangle(x + cell_w * 0.15, cy - cell_h * 0.35, x + cell_w,
                             cy + cell_h * 0.35, fill="#e2b93b", outline="#7a5210", width=2)
    canvas.create_text(x + cell_w / 2, cy, text=label, font=("Segoe UI", 8, "bold"))


def _diode_on_line(canvas, x1, y1, x2, y2, label=None, color="#444444"):
    """Draws a wire from (x1,y1) to (x2,y2) with a diode symbol centered on it,
    oriented automatically along that segment. (x1,y1) is the anode side."""
    dx, dy = x2 - x1, y2 - y1
    length = math.hypot(dx, dy) or 1
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    mx, my = (x1 + x2) / 2, (y1 + y2) / 2
    size = 11
    base_x, base_y = mx - ux * size, my - uy * size
    apex_x, apex_y = mx + ux * size, my + uy * size

    draw_wire(canvas, x1, y1, base_x, base_y)
    draw_wire(canvas, apex_x, apex_y, x2, y2)

    p1 = (base_x + px * size * 0.85, base_y + py * size * 0.85)
    p2 = (base_x - px * size * 0.85, base_y - py * size * 0.85)
    canvas.create_polygon(p1[0], p1[1], p2[0], p2[1], apex_x, apex_y,
                           fill=color, outline="#111", width=1)
    bx1, by1 = apex_x + px * size * 0.95, apex_y + py * size * 0.95
    bx2, by2 = apex_x - px * size * 0.95, apex_y - py * size * 0.95
    canvas.create_line(bx1, by1, bx2, by2, fill="#111", width=3)
    if label:
        lx, ly = mx + px * 20, my + py * 20
        canvas.create_text(lx, ly, text=label, font=("Segoe UI", 8, "bold"))


def _draw_source_symbol(canvas, x, y, r=18):
    canvas.create_oval(x - r, y - r, x + r, y + r, outline="#333", width=2, fill="#fdfaf3")
    xs = [x - r * 0.6 + i * (r * 1.2 / 20) for i in range(21)]
    ys = [y + (r * 0.35) * math.sin((xv - x) / r * math.pi) for xv in xs]
    for i in range(len(xs) - 1):
        canvas.create_line(xs[i], ys[i], xs[i + 1], ys[i + 1], fill="#333", width=2)


def _draw_load_and_cap(canvas, dc_plus, dc_minus, x, show_cap=False, cap_label=""):
    """Draws Rload (and optionally a capacitor in parallel) between two y-levels at column x."""
    top_y, bot_y = dc_plus, dc_minus
    load_x = x if not show_cap else x + 45
    if load_x != x:
        draw_wire(canvas, x, top_y, load_x, top_y)
    draw_wire(canvas, load_x, top_y, load_x, top_y + (bot_y - top_y) * 0.4)
    sym.resistor(canvas, load_x, top_y + (bot_y - top_y) * 0.4, load_x, top_y + (bot_y - top_y) * 0.6,
                 label="Rload", s=0.8, label_side=1)
    draw_wire(canvas, load_x, top_y + (bot_y - top_y) * 0.6, load_x, bot_y)
    if load_x != x:
        draw_wire(canvas, load_x, bot_y, x, bot_y)

    if show_cap:
        cap_x = x
        cap_top_plate = top_y + (bot_y - top_y) * 0.42
        cap_bot_plate = top_y + (bot_y - top_y) * 0.5
        draw_wire(canvas, cap_x, top_y, cap_x, cap_top_plate)
        draw_wire(canvas, cap_x, cap_bot_plate, cap_x, bot_y)
        sym.capacitor(canvas, cap_x, cap_top_plate - 4, cap_x, cap_bot_plate + 4, s=0.9,
                      variant="polarized")
        canvas.create_text(cap_x - 20, (cap_top_plate + cap_bot_plate) / 2, text=cap_label,
                            font=("Segoe UI", 8, "bold"), anchor="e", fill="#2E5EAA")


def draw_bridge_2diode(canvas, w=460, h=260):
    """Simplified 2-diode full-wave rectifier: two AC source symbols (one
    inverted relative to the other, i.e. opposite polarity/phase) feed D1
    and D2, which are mirrored around the shared center/ground line. This
    keeps the diode orientation obvious without drawing a wound-coil
    center-tapped transformer, which tends to confuse beginners."""
    clear(canvas)
    design_w, design_h = 460, 260
    src_x = 95
    top_y, bot_y = 65, 195
    ct_y = (top_y + bot_y) / 2
    node_x = 250
    out_y = ct_y - 45

    _draw_source_symbol(canvas, src_x, top_y, r=22)
    _draw_source_symbol(canvas, src_x, bot_y, r=22)
    canvas.create_text(src_x, top_y - 34, text="+", font=("Segoe UI", 11, "bold"), fill="#1f2a44")
    canvas.create_text(src_x, bot_y + 34, text="-", font=("Segoe UI", 11, "bold"), fill="#1f2a44")
    canvas.create_text(src_x - 55, ct_y, text="opposite\npolarity", font=("Segoe UI", 8), fill="#7a5210",
                        justify="center")

    draw_wire(canvas, src_x + 22, top_y, node_x - 60, top_y)
    draw_wire(canvas, src_x + 22, bot_y, node_x - 60, bot_y)

    draw_wire(canvas, src_x, top_y + 22, src_x, ct_y)
    draw_wire(canvas, src_x, ct_y, src_x, bot_y - 22)
    draw_wire(canvas, src_x, ct_y, node_x - 60, ct_y)
    canvas.create_text(src_x + 16, ct_y - 10, text="CT / GND", font=("Segoe UI", 8, "bold"), fill="#7a5210")

    _diode_on_line(canvas, node_x - 60, top_y, node_x, out_y, label="D1")
    _diode_on_line(canvas, node_x - 60, bot_y, node_x, out_y, label="D2")

    dc_plus_x = 340
    draw_wire(canvas, node_x, out_y, dc_plus_x - 60, out_y)
    draw_wire(canvas, dc_plus_x - 60, out_y, dc_plus_x - 60, top_y - 25)
    draw_wire(canvas, dc_plus_x - 60, top_y - 25, dc_plus_x, top_y - 25)
    draw_wire(canvas, node_x - 60, ct_y, dc_plus_x, ct_y)

    _draw_load_and_cap(canvas, top_y - 25, ct_y, dc_plus_x, show_cap=False)
    canvas.create_text(dc_plus_x + 45, top_y - 25, text="+", font=("Segoe UI", 11, "bold"), fill="#1f2a44")
    canvas.create_text(dc_plus_x + 45, ct_y, text="-", font=("Segoe UI", 11, "bold"), fill="#1f2a44")

    if w != design_w or h != design_h:
        canvas.scale("all", 0, 0, w / design_w, h / design_h)


def draw_bridge_4diode(canvas, w=460, h=260, show_cap=False, cap_label=""):
    clear(canvas)
    design_w, design_h = 460, 260
    cx, cy = 190, design_h / 2
    dw, dh = 70, 65
    left = (cx - dw, cy)
    right = (cx + dw, cy)
    top = (cx, cy - dh)
    bottom = (cx, cy + dh)

    _draw_source_symbol(canvas, left[0] - 45, cy)
    draw_wire(canvas, left[0] - 27, cy, *left)
    _draw_source_symbol(canvas, right[0] + 45, cy)
    draw_wire(canvas, right[0] + 27, cy, *right)

    _diode_on_line(canvas, left[0], left[1], top[0], top[1], label="D1")
    _diode_on_line(canvas, right[0], right[1], top[0], top[1], label="D2")
    _diode_on_line(canvas, bottom[0], bottom[1], left[0], left[1], label="D3")
    _diode_on_line(canvas, bottom[0], bottom[1], right[0], right[1], label="D4")

    dc_x = 360
    draw_wire(canvas, top[0], top[1], top[0], top[1] - 30)
    draw_wire(canvas, top[0], top[1] - 30, dc_x, top[1] - 30)
    draw_wire(canvas, bottom[0], bottom[1], bottom[0], bottom[1] + 30)
    draw_wire(canvas, bottom[0], bottom[1] + 30, dc_x, bottom[1] + 30)

    _draw_load_and_cap(canvas, top[1] - 30, bottom[1] + 30, dc_x, show_cap=show_cap, cap_label=cap_label)
    canvas.create_text(dc_x + 45 if not show_cap else dc_x + 90, top[1] - 30,
                        text="+", font=("Segoe UI", 11, "bold"), fill="#1f2a44")
    canvas.create_text(dc_x + 45 if not show_cap else dc_x + 90, bottom[1] + 30,
                        text="-", font=("Segoe UI", 11, "bold"), fill="#1f2a44")

    if w != design_w or h != design_h:
        canvas.scale("all", 0, 0, w / design_w, h / design_h)


def draw_battery(canvas, count=1, series=True, w=460, h=160):
    """Battery pack schematic using the standard cell symbol (long plate = +)."""
    clear(canvas)
    cy = h / 2 - 8
    count = max(1, count)
    if series:
        x0, x1 = 40, w - 40
        span = (x1 - x0) / count
        s = max(0.6, min(1.0, span / 70))
        for i in range(count):
            sym.cell(canvas, x0 + i * span, cy, x0 + (i + 1) * span, cy, label=f"B{i + 1}", s=s)
        sym.terminal(canvas, x0, cy)
        canvas.create_text(x0 - 8, cy, text="+", anchor="e", font=("Segoe UI", 11, "bold"), fill="#c62828")
        sym.terminal(canvas, x1, cy)
        canvas.create_text(x1 + 8, cy, text="−", anchor="w", font=("Segoe UI", 11, "bold"), fill="#1f2a44")
    else:
        top_y, bot_y = 22, h - 34
        left_x, right_x = 60, w - 60
        n = count
        span = (right_x - left_x) / n
        sym.wire(canvas, left_x - 30, top_y, right_x - span / 2, top_y)
        sym.wire(canvas, left_x + span / 2, bot_y, right_x + 30, bot_y)
        for i in range(n):
            x = left_x + span / 2 + i * span
            sym.cell(canvas, x, top_y, x, bot_y, label=f"B{i + 1}", s=0.8, label_side=1)
            sym.node(canvas, x, top_y)
            sym.node(canvas, x, bot_y)
        sym.terminal(canvas, left_x - 30, top_y)
        canvas.create_text(left_x - 38, top_y, text="+", anchor="e", font=("Segoe UI", 11, "bold"), fill="#c62828")
        sym.terminal(canvas, right_x + 30, bot_y)
        canvas.create_text(right_x + 38, bot_y, text="−", anchor="w", font=("Segoe UI", 11, "bold"), fill="#1f2a44")

    mode = t("draw.battery_series") if series else t("draw.battery_parallel")
    canvas.create_text(w / 2, h - 12, text=mode, font=("Segoe UI", 9), fill="#666")


# ---------------------------------------------------------------------------
# Digital logic gate symbols
# ---------------------------------------------------------------------------

_GATE_BODY_FILL = "#f5f0e2"
_GATE_OUTLINE = "#333"
_BUBBLE_R = 5


def _sine_bulge_curve(x0, y0, x1, y1, bulge, steps=16):
    """Points along a line from (x0,y0) to (x1,y1), displaced perpendicular
    to that line by up to `bulge` (sinusoidal profile, zero at both ends).
    Used as a cheap, good-enough stand-in for circular/bezier arcs when
    drawing gate-body outlines."""
    dx, dy = x1 - x0, y1 - y0
    length = math.hypot(dx, dy) or 1.0
    nx, ny = dy / length, -dx / length  # unit normal (rotate direction vector +90°)
    pts = []
    for i in range(steps + 1):
        t = i / steps
        bx = x0 + dx * t
        by = y0 + dy * t
        off = bulge * math.sin(math.pi * t)
        pts.append((bx + nx * off, by + ny * off))
    return pts


def _gate_outline_points(kind, bx0, by0, bx1, by1):
    """Body outline (closed polygon point list, NOT including the
    inversion bubble) for one gate kind. bx0/by0/bx1/by1 is the bounding
    box for the body only (stubs and bubble are drawn separately by the
    caller, outside this box)."""
    h = by1 - by0
    mid_y = (by0 + by1) / 2
    base_kind = {"NAND": "AND", "NOR": "OR", "XNOR": "XOR"}.get(kind, kind)

    if base_kind == "NOT":
        return [(bx0, by0), (bx0, by1), (bx1, mid_y)]

    if base_kind == "AND":
        r = h / 2
        straight_x = max(bx0, bx1 - r)
        pts = [(bx0, by0), (straight_x, by0)]
        pts += _sine_bulge_curve(straight_x, by0, straight_x, by1, r, steps=20)
        pts += [(bx0, by1)]
        return pts

    # OR and XOR share the same "shield" body; XOR adds an extra detached
    # curve behind it (handled separately by the caller).
    back_bulge = h * 0.16
    top_bulge = h * 0.14
    pts = []
    pts += _sine_bulge_curve(bx0, by0, bx0, by1, back_bulge, steps=14)
    pts += _sine_bulge_curve(bx0, by1, bx1, mid_y, -top_bulge, steps=14)[1:]
    pts += _sine_bulge_curve(bx1, mid_y, bx0, by0, -top_bulge, steps=14)[1:]
    return pts


def draw_gate_symbol(canvas, kind, x, y, w=90, h=60,
                      in_labels=None, out_label="Y", show_pin_labels=True,
                      stub=16, fill=None):
    """Draw a standard-ish schematic symbol for one logic gate kind
    ('NOT','AND','OR','NAND','NOR','XOR','XNOR') with its bounding box
    at (x, y, x+w, y+h). Input/output stub wires extend `stub` px beyond
    the body on each side. Returns a dict of pin coordinates:
    {'inputs': [(x,y), ...], 'output': (x,y)} in canvas coordinates, for
    callers that need to attach wires.
    """
    is_not = kind == "NOT"
    n_in = 1 if is_not else 2
    inverted = kind in ("NOT", "NAND", "NOR", "XNOR")
    is_xor_family = kind in ("XOR", "XNOR")

    bx0, by0 = x + stub, y
    bx1, by1 = x + w - stub - (2 * _BUBBLE_R if inverted else 0), y + h
    mid_y = (by0 + by1) / 2

    body_fill = fill or _GATE_BODY_FILL
    pts = _gate_outline_points(kind, bx0, by0, bx1, by1)
    canvas.create_polygon(pts, fill=body_fill, outline=_GATE_OUTLINE, width=2,
                           joinstyle="round", smooth=(kind in ("OR", "NOR", "XOR", "XNOR")))

    if is_xor_family:
        extra = _sine_bulge_curve(bx0 - 7, by0, bx0 - 7, by1, h * 0.16, steps=14)
        canvas.create_line(extra, fill=_GATE_OUTLINE, width=2, smooth=True)

    out_x = bx1
    if inverted:
        bubble_cx = bx1 + _BUBBLE_R
        canvas.create_oval(bx1, mid_y - _BUBBLE_R, bx1 + 2 * _BUBBLE_R, mid_y + _BUBBLE_R,
                            fill=body_fill, outline=_GATE_OUTLINE, width=2)
        out_x = bubble_cx + _BUBBLE_R

    # input stubs
    in_pins = []
    left_x = bx0 - 7 if is_xor_family else bx0
    if n_in == 1:
        in_ys = [mid_y]
    else:
        in_ys = [by0 + h * 0.28, by0 + h * 0.72]
    for iy in in_ys:
        draw_wire(canvas, x, iy, left_x, iy, width=2, color=WIRE_COLOR)
        in_pins.append((x, iy))

    # output stub
    draw_wire(canvas, out_x, mid_y, x + w, mid_y, width=2, color=WIRE_COLOR)
    out_pin = (x + w, mid_y)

    if show_pin_labels:
        labels = in_labels or (["A"] if n_in == 1 else ["A", "B"])
        for (px, py), lbl in zip(in_pins, labels):
            canvas.create_text(px + 8, py - 9, text=lbl, font=("Segoe UI", 8), fill="#555", anchor="w")
        canvas.create_text(out_pin[0] - 8, out_pin[1] - 9, text=out_label,
                            font=("Segoe UI", 8), fill="#555", anchor="e")

    return {"inputs": in_pins, "output": out_pin}


def draw_timing_diagram(canvas, rows, left_margin=34, step_w=38, row_h=42,
                         high_color="#1f6a5f", low_color="#999", grid_color="#ddd"):
    """Draw a simple digital step-waveform timing diagram.

    rows: list of (label, bits) where bits is a list of 0/1 of equal length
    across all rows. Returns (step_w, row_h, left_margin) so callers can
    map a click position back to (row_index, step_index).
    """
    canvas.delete("all")
    if not rows:
        return step_w, row_h, left_margin
    n_steps = len(rows[0][1])
    top = 14

    for ri, (label, bits) in enumerate(rows):
        y_top = top + ri * row_h
        y_mid = y_top + row_h / 2
        y_hi = y_top + row_h * 0.22
        y_lo = y_top + row_h * 0.78
        canvas.create_text(left_margin - 10, y_mid, text=label, font=("Segoe UI", 10, "bold"), anchor="e")

        for i in range(n_steps + 1):
            x = left_margin + i * step_w
            canvas.create_line(x, y_top, x, y_top + row_h, fill=grid_color)

        prev_y = None
        for i, b in enumerate(bits):
            x0 = left_margin + i * step_w
            x1 = x0 + step_w
            y = y_hi if b else y_lo
            if prev_y is not None and y != prev_y:
                canvas.create_line(x0, prev_y, x0, y, fill=high_color, width=2)
            canvas.create_line(x0, y, x1, y, fill=high_color, width=2)
            prev_y = y

    bottom = top + len(rows) * row_h
    for i in range(n_steps):
        x = left_margin + i * step_w + step_w / 2
        canvas.create_text(x, bottom + 10, text=str(i), font=("Segoe UI", 7), fill="#999")

    return step_w, row_h, left_margin
