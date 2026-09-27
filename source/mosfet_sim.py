"""
mosfet_sim.py - Animated, physically-motivated MOSFET channel visualizer.

Same architecture and guiding rules as bjt_sim.py: fixed geometry (the
substrate, source/drain wells, gate stack and channel region never move),
with carrier motion and depletion/pinch-off overlays driven entirely by
`compute_mosfet_state()`.

Two carrier populations are simulated:
  - channel carriers: S -> D through the inversion layer, present only
    when the gate has turned the channel on (Vov > 0).
  - body-diode carriers: D -> B, representing the intrinsic body-drain
    diode every real MOSFET has. It forward-conducts whenever Vds is
    driven far enough negative (for an NMOS) - a real "reverse current"
    path that exists independently of the gate, which is why the Vds
    slider now reaches negative voltages: without that range this
    behavior was simply unreachable.
"""
import math
import random

from drawing import draw_wire, _P_COLOR, _N_COLOR, _CHANNEL_COLOR, _CHANNEL_COLOR_P
from i18n import t

TICK_MS = 40
MAX_ACTIVE_CARRIERS = 45
MAX_SPAWN_RATE = 0.55
SPEED_BULK = 3.2

TURN_ON = 0.55   # body-diode turn-on voltage (same simplified diode law as bjt_sim)
SLOPE = 0.035

STAT_SCALE = 11.0
K_FACTOR = 0.16  # simplified "Id = k(Vov)^2" style scale factor, relative units only


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _sigmoid(x):
    if x > 30:
        return 1.0
    if x < -30:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def compute_mosfet_state(vgs, vds, vth, is_n=True):
    """Pure function: bias -> simplified MOSFET electrical state. `is_n`
    only flips the sign convention (an NMOS turns on with Vgs above a
    positive Vth; a PMOS turns on with Vgs below a negative Vth) - it does
    not change the shape of the formulas, matching how the sliders already
    use mirrored (not shared) ranges for N vs P, unlike the BJT tab."""
    sign = 1.0 if is_n else -1.0
    ov = sign * (vgs - vth)          # overdrive voltage: >0 means a channel has formed
    vds_eff = sign * vds

    on = ov > 0.0
    if on:
        excess = vds_eff - ov
        if excess > 0:
            region = "saturation"
            pinch_frac = _clamp(0.20 + 0.6 * excess / (abs(ov) + excess + 1e-6), 0.0, 0.90)
            id_rel = K_FACTOR * ov * ov
        else:
            region = "triode"
            pinch_frac = 0.0
            id_rel = K_FACTOR * (2 * ov * max(vds_eff, 0.0) - max(vds_eff, 0.0) ** 2)
        channel_strength = _clamp(ov / 3.0, 0.0, 1.0)
    else:
        region = "cutoff"
        pinch_frac = 0.0
        channel_strength = 0.0
        id_rel = 0.0

    # Intrinsic body-drain diode: forward biased (and conducting) when the
    # drain is pulled far enough below the body/source potential, entirely
    # independent of what the gate is doing.
    v_diode = -vds_eff
    diode_inj = _sigmoid((v_diode - TURN_ON) / SLOPE)
    diode_conducting = diode_inj > 0.15
    if diode_conducting:
        region = "body_diode"
        id_rel = max(id_rel, diode_inj * 3.2)

    return {
        "is_n": is_n, "vgs": vgs, "vds": vds, "vth": vth, "ov": ov, "on": on,
        "region": region, "pinch_frac": pinch_frac, "channel_strength": channel_strength,
        "diode_inj": diode_inj, "diode_conducting": diode_conducting,
        "id_rel": max(0.0, id_rel) * STAT_SCALE,
    }


class _Carrier:
    __slots__ = ("x", "y", "kind")

    def __init__(self, x, y, kind):
        self.x = x
        self.y = y
        self.kind = kind  # "channel" or "diode"


class MosfetJunctionSim:
    def __init__(self, canvas, kind="N-channel", w=440, h=300, vgs=0.0, vds=0.0, vth=2.0, on_stats=None):
        self.canvas = canvas
        self.kind = kind
        self.w = w
        self.h = h
        self.vgs = vgs
        self.vds = vds
        self.vth = vth
        self.on_stats = on_stats

        self._rng = random.Random()
        self._carriers = []
        self._running = False
        self._after_id = None
        self._geo = self._geometry()

    def set_bias(self, vgs, vds, vth=None):
        self.vgs = vgs
        self.vds = vds
        if vth is not None:
            self.vth = vth

    def start(self):
        if self._running:
            return
        self._running = True
        self._tick()

    def stop(self):
        self._running = False
        if self._after_id is not None:
            try:
                self.canvas.after_cancel(self._after_id)
            except Exception:
                pass
            self._after_id = None

    # ------------------------------------------------------------------
    def _geometry(self):
        """Fixed layout - identical math to the original static
        draw_mosfet_junction(), just computed once and never touched by
        bias again."""
        body_left, body_right = 55, self.w - 55
        body_top, body_bot = 100, self.h - 55
        well_w = (body_right - body_left) * 0.20
        well_top = body_top + 6
        well_bot = body_bot - 14

        sx0, sx1 = body_left + 12, body_left + 12 + well_w
        dx0, dx1 = body_right - 12 - well_w, body_right - 12

        gate_left, gate_right = sx1 - 6, dx0 + 6
        gate_cx = (gate_left + gate_right) / 2
        ox_top, ox_bot = body_top - 10, body_top

        body_cx = (body_left + body_right) / 2

        return {
            "body_left": body_left, "body_right": body_right, "body_top": body_top, "body_bot": body_bot,
            "well_top": well_top, "well_bot": well_bot,
            "sx0": sx0, "sx1": sx1, "dx0": dx0, "dx1": dx1,
            "gate_left": gate_left, "gate_right": gate_right, "gate_cx": gate_cx,
            "ox_top": ox_top, "ox_bot": ox_bot,
            "body_cx": body_cx,
        }

    # ------------------------------------------------------------------
    def _tick(self):
        if not self._running:
            return
        if not self.canvas.winfo_exists():
            self._running = False
            return
        state = compute_mosfet_state(self.vgs, self.vds, self.vth, is_n=self.kind.lower().startswith("n"))
        self._advance(state)
        self._draw(state)
        if self.on_stats is not None:
            self.on_stats(state)
        self._after_id = self.canvas.after(TICK_MS, self._tick)

    def _advance(self, state):
        geo = self._geo
        mid_y = (geo["well_top"] + geo["well_bot"]) / 2
        span = (geo["well_bot"] - geo["well_top"]) * 0.32

        if len(self._carriers) < MAX_ACTIVE_CARRIERS:
            if state["on"] and self._rng.random() < state["channel_strength"] * MAX_SPAWN_RATE:
                x = geo["sx1"] + self._rng.uniform(0.0, 0.3) * (geo["dx0"] - geo["sx1"])
                y = mid_y + self._rng.uniform(-span, span)
                self._carriers.append(_Carrier(x, y, "channel"))
            if state["diode_conducting"] and self._rng.random() < state["diode_inj"] * MAX_SPAWN_RATE * 0.6:
                x = (geo["dx0"] + geo["dx1"]) / 2 + self._rng.uniform(-4, 4)
                y = geo["well_bot"] + self._rng.uniform(0.0, 6.0)
                self._carriers.append(_Carrier(x, y, "diode"))

        survivors = []
        for c in self._carriers:
            if c.kind == "channel":
                c.x += SPEED_BULK
                c.y += self._rng.uniform(-0.3, 0.3)
                c.y = _clamp(c.y, mid_y - span, mid_y + span)
                if c.x < geo["dx0"]:
                    survivors.append(c)
            else:  # diode carrier: drifts from drain well down to the body lead
                target_y = geo["body_bot"] + 22
                target_x = geo["body_cx"]
                dx = target_x - c.x
                dy = target_y - c.y
                dist = max(1.0, math.hypot(dx, dy))
                c.x += SPEED_BULK * dx / dist
                c.y += SPEED_BULK * dy / dist
                if dist > 2.0:
                    survivors.append(c)
        self._carriers = survivors

    # ------------------------------------------------------------------
    def _draw(self, state):
        canvas = self.canvas
        canvas.delete("all")
        geo = self._geo
        is_n = state["is_n"]
        substrate_color = _P_COLOR if is_n else _N_COLOR
        well_color = _N_COLOR if is_n else _P_COLOR
        channel_color = _CHANNEL_COLOR if is_n else _CHANNEL_COLOR_P
        carrier_color = "#2255aa" if is_n else "#aa2255"
        diode_color = "#c0392b"

        body_left, body_right = geo["body_left"], geo["body_right"]
        body_top, body_bot = geo["body_top"], geo["body_bot"]
        well_top, well_bot = geo["well_top"], geo["well_bot"]
        sx0, sx1, dx0, dx1 = geo["sx0"], geo["sx1"], geo["dx0"], geo["dx1"]

        canvas.create_rectangle(body_left, body_top, body_right, body_bot,
                                 fill=substrate_color, outline="#333", width=2)
        canvas.create_rectangle(sx0, well_top, sx1, well_bot, fill=well_color, outline="#333", width=2)
        canvas.create_rectangle(dx0, well_top, dx1, well_bot, fill=well_color, outline="#333", width=2)
        canvas.create_text((sx0 + sx1) / 2, (well_top + well_bot) / 2, text="S", font=("Segoe UI", 10, "bold"))
        canvas.create_text((dx0 + dx1) / 2, (well_top + well_bot) / 2, text="D", font=("Segoe UI", 10, "bold"))

        gate_left, gate_right, gate_cx = geo["gate_left"], geo["gate_right"], geo["gate_cx"]
        ox_top, ox_bot = geo["ox_top"], geo["ox_bot"]
        canvas.create_rectangle(gate_left, ox_top, gate_right, ox_bot, fill="#fff2b8", outline="#8a7752", width=1)
        canvas.create_rectangle(gate_left, ox_top - 16, gate_right, ox_top, fill="#999", outline="#333", width=2)
        gate_attach_y = ox_top - 16
        draw_wire(canvas, gate_cx, gate_attach_y, gate_cx, gate_attach_y - 30)
        canvas.create_text(gate_cx, gate_attach_y - 40, text="G", font=("Segoe UI", 11, "bold"))

        ch_left, ch_right = sx1, dx0
        ch_top, ch_bot = well_top, well_bot

        if state["on"]:
            canvas.create_rectangle(ch_left, ch_top, ch_right, ch_bot, fill=channel_color, outline="")
            if state["pinch_frac"] > 0:
                wedge_w = (ch_right - ch_left) * state["pinch_frac"]
                apex_x = ch_right - wedge_w
                canvas.create_polygon(ch_right, ch_top, apex_x, (ch_top + ch_bot) / 2, ch_right, ch_bot,
                                       fill=substrate_color, outline="#333", width=1)
        else:
            for wx0, wx1 in [(sx0, sx1), (dx0, dx1)]:
                canvas.create_oval(wx0 - 6, well_top - 4, wx1 + 6, well_bot + 10,
                                    outline="#bbb", width=1, dash=(2, 2))

        for c in self._carriers:
            color = carrier_color if c.kind == "channel" else diode_color
            canvas.create_oval(c.x - 3.5, c.y - 3.5, c.x + 3.5, c.y + 3.5, fill=color, outline="")

        draw_wire(canvas, (sx0 + sx1) / 2, well_top, (sx0 + sx1) / 2, well_top - 30)
        canvas.create_text((sx0 + sx1) / 2, well_top - 40, text="S", font=("Segoe UI", 10, "bold"))
        draw_wire(canvas, (dx0 + dx1) / 2, well_top, (dx0 + dx1) / 2, well_top - 30)
        canvas.create_text((dx0 + dx1) / 2, well_top - 40, text="D", font=("Segoe UI", 10, "bold"))
        draw_wire(canvas, geo["body_cx"], body_bot, geo["body_cx"], body_bot + 22)
        canvas.create_text(geo["body_cx"], body_bot + 32, text="B", font=("Segoe UI", 9), fill="#666")

        canvas.create_text(body_left, 15, text=self.kind.upper(), anchor="w",
                            font=("Segoe UI", 9, "bold"), fill="#666")

        region_key = {
            "cutoff": "junction.state_cutoff",
            "triode": "junction.state_triode",
            "saturation": "junction.state_saturation_fet",
            "body_diode": "junction.state_body_diode",
        }[state["region"]]
        region_color = {
            "cutoff": "#999", "triode": "#1f6a5f", "saturation": "#b3691d", "body_diode": "#c0392b",
        }[state["region"]]
        canvas.create_text(self.w / 2, body_bot + 18, text=t(region_key),
                            font=("Segoe UI", 9, "bold"), fill=region_color)

        legend_y = body_bot + 40
        canvas.create_oval(body_left - 2, legend_y - 3, body_left + 4, legend_y + 3,
                            fill=carrier_color, outline="")
        carrier_label = "e⁻" if is_n else "h⁺"
        canvas.create_text(body_left + 32, legend_y, text=f"{carrier_label} {t('junction.electron_flow')}",
                            font=("Segoe UI", 7), fill="#555", anchor="w")
        canvas.create_oval(body_left + 148, legend_y - 3, body_left + 154, legend_y + 3,
                            fill=diode_color, outline="")
        canvas.create_text(body_left + 180, legend_y, text=t("junction.body_diode_legend"),
                            font=("Segoe UI", 7), fill="#555", anchor="w")
