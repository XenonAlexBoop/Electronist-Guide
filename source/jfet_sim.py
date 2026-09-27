"""
jfet_sim.py - Animated, physically-motivated JFET channel visualizer.

Same fixed-geometry architecture as bjt_sim.py / mosfet_sim.py: the channel
block and the two gate strips never move. The gate-junction depletion
region grows in from the top and bottom (symmetrically) as reverse gate
bias increases, pinching off the open conduction band in the middle -
carriers are confined to whatever's left of that open band, not to a
resized channel block.

Two carrier populations:
  - channel carriers: drift source -> drain (or drain -> source if Vds is
    reversed - a JFET channel is symmetric, so reversing Vds genuinely
    reverses the current direction, unlike a MOSFET's body diode).
  - gate carriers: normally the gate-channel junction is kept reverse
    biased (that's the whole operating principle). If Vgs is pushed past
    the gate-channel turn-on voltage in the forward direction, that
    junction starts conducting a real (undesirable) gate current - this is
    the JFET's own "reverse current" case, shown as carriers flowing from
    the gate strips into the channel. The Vgs slider now reaches slightly
    past 0V specifically so this is reachable.
"""
import math
import random

from drawing import draw_wire, _P_COLOR, _N_COLOR, _CHANNEL_COLOR, _CHANNEL_COLOR_P
from i18n import t

TICK_MS = 40
MAX_ACTIVE_CARRIERS = 45
MAX_SPAWN_RATE = 0.55
SPEED_BULK = 3.4

TURN_ON = 0.55
SLOPE = 0.035

STAT_SCALE = 11.0
K_FACTOR = 0.9


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _sigmoid(x):
    if x > 30:
        return 1.0
    if x < -30:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def compute_jfet_state(vgs, vp, vds, is_n=True):
    """Pure function: bias -> simplified JFET electrical state."""
    sign = 1.0 if is_n else -1.0

    frac = 0.0
    if vp != 0:
        frac = vgs / vp  # normal operation: same sign for vgs and vp -> ratio in [0,1]
    frac = _clamp(frac, 0.0, 1.0)
    pinch_frac = min(0.49, 0.49 * frac)
    channel_open = 1.0 - pinch_frac / 0.49  # 1 = fully open, 0 = fully pinched
    is_cutoff = pinch_frac >= 0.485

    # Gate-channel junction: normally kept reverse biased (that's the whole
    # operating principle). If pushed past turn-on in the forward
    # direction, it conducts a real gate current into the channel.
    vgs_forward = sign * vgs
    gate_inj = _sigmoid((vgs_forward - TURN_ON) / SLOPE)
    gate_conducting = gate_inj > 0.15

    flow_dir = 1 if vds >= 0 else -1  # +1: S->D (normal); -1: D->S (Vds reversed)

    id_rel = K_FACTOR * channel_open * channel_open
    if gate_conducting:
        region = "gate_forward"
        id_rel = max(id_rel, gate_inj * 3.0)
    elif is_cutoff:
        region = "cutoff"
        id_rel = 0.0
    else:
        region = "conducting"

    return {
        "is_n": is_n, "vgs": vgs, "vp": vp, "vds": vds,
        "pinch_frac": pinch_frac, "channel_open": channel_open, "is_cutoff": is_cutoff,
        "gate_inj": gate_inj, "gate_conducting": gate_conducting,
        "flow_dir": flow_dir, "region": region, "id_rel": max(0.0, id_rel) * STAT_SCALE,
    }


class _Carrier:
    __slots__ = ("x", "y", "kind", "target_y")

    def __init__(self, x, y, kind, target_y=0.0):
        self.x = x
        self.y = y
        self.kind = kind  # "channel" or "gate"
        self.target_y = target_y


class JfetJunctionSim:
    def __init__(self, canvas, kind="N-channel", w=440, h=300, vgs=0.0, vp=-4.0, vds=5.0, on_stats=None):
        self.canvas = canvas
        self.kind = kind
        self.w = w
        self.h = h
        self.vgs = vgs
        self.vp = vp
        self.vds = vds
        self.on_stats = on_stats

        self._rng = random.Random()
        self._carriers = []
        self._running = False
        self._after_id = None
        self._geo = self._geometry()

    def set_bias(self, vgs, vp=None, vds=None):
        self.vgs = vgs
        if vp is not None:
            self.vp = vp
        if vds is not None:
            self.vds = vds

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
        body_left, body_right = 50, self.w - 50
        ch_top, ch_bot = 100, self.h - 100
        gate_h = 22
        return {
            "body_left": body_left, "body_right": body_right,
            "ch_top": ch_top, "ch_bot": ch_bot, "ch_height": ch_bot - ch_top,
            "gate_h": gate_h,
        }

    # ------------------------------------------------------------------
    def _tick(self):
        if not self._running:
            return
        if not self.canvas.winfo_exists():
            self._running = False
            return
        state = compute_jfet_state(self.vgs, self.vp, self.vds, is_n=self.kind.lower().startswith("n"))
        self._advance(state)
        self._draw(state)
        if self.on_stats is not None:
            self.on_stats(state)
        self._after_id = self.canvas.after(TICK_MS, self._tick)

    def _advance(self, state):
        geo = self._geo
        ch_top, ch_bot = geo["ch_top"], geo["ch_bot"]
        mid_y = (ch_top + ch_bot) / 2
        open_half = (ch_bot - ch_top) / 2 * (1.0 - state["pinch_frac"] / 0.49) if state["pinch_frac"] < 0.485 else 2.0
        open_half = max(2.0, open_half)

        if len(self._carriers) < MAX_ACTIVE_CARRIERS:
            if state["region"] == "conducting" and self._rng.random() < state["channel_open"] * MAX_SPAWN_RATE:
                start_x = geo["body_left"] if state["flow_dir"] > 0 else geo["body_right"]
                y = mid_y + self._rng.uniform(-open_half * 0.8, open_half * 0.8)
                self._carriers.append(_Carrier(start_x, y, "channel"))
            if state["gate_conducting"] and self._rng.random() < state["gate_inj"] * MAX_SPAWN_RATE * 0.6:
                from_top = self._rng.random() < 0.5
                x = self._rng.uniform(geo["body_left"] + 40, geo["body_right"] - 40)
                y = ch_top if from_top else ch_bot
                self._carriers.append(_Carrier(x, y, "gate", target_y=mid_y))

        survivors = []
        for c in self._carriers:
            if c.kind == "channel":
                c.x += SPEED_BULK * state["flow_dir"]
                c.y += self._rng.uniform(-0.3, 0.3)
                c.y = _clamp(c.y, mid_y - open_half, mid_y + open_half)
                if geo["body_left"] < c.x < geo["body_right"]:
                    survivors.append(c)
            else:
                dy = c.target_y - c.y
                if abs(dy) > 2.0:
                    c.y += SPEED_BULK * (1 if dy > 0 else -1) * 0.7
                    survivors.append(c)
        self._carriers = survivors

    # ------------------------------------------------------------------
    def _draw(self, state):
        canvas = self.canvas
        canvas.delete("all")
        geo = self._geo
        is_n = state["is_n"]
        channel_color = _CHANNEL_COLOR if is_n else _CHANNEL_COLOR_P
        gate_color = _P_COLOR if is_n else _N_COLOR
        carrier_color = "#2255aa" if is_n else "#aa2255"
        gate_carrier_color = "#c0392b"

        body_left, body_right = geo["body_left"], geo["body_right"]
        ch_top, ch_bot = geo["ch_top"], geo["ch_bot"]
        ch_height = geo["ch_height"]
        gate_h = geo["gate_h"]

        canvas.create_rectangle(body_left, ch_top, body_right, ch_bot,
                                 fill=channel_color, outline="#333", width=2)

        pinch = state["pinch_frac"]
        if pinch > 0:
            canvas.create_rectangle(body_left, ch_top, body_right, ch_top + ch_height * pinch,
                                     fill="#ffffff", stipple="gray50", outline="")
            canvas.create_rectangle(body_left, ch_bot - ch_height * pinch, body_right, ch_bot,
                                     fill="#ffffff", stipple="gray50", outline="")
            canvas.create_line(body_left, ch_top + ch_height * pinch, body_right, ch_top + ch_height * pinch,
                                fill="#888", dash=(3, 2))
            canvas.create_line(body_left, ch_bot - ch_height * pinch, body_right, ch_bot - ch_height * pinch,
                                fill="#888", dash=(3, 2))

        canvas.create_rectangle(body_left + 30, ch_top - gate_h, body_right - 30, ch_top,
                                 fill=gate_color, outline="#333", width=2)
        canvas.create_rectangle(body_left + 30, ch_bot, body_right - 30, ch_bot + gate_h,
                                 fill=gate_color, outline="#333", width=2)
        canvas.create_text(self.w / 2, ch_top - gate_h / 2, text="G", font=("Segoe UI", 9, "bold"))
        canvas.create_text(self.w / 2, ch_bot + gate_h / 2, text="G", font=("Segoe UI", 9, "bold"))
        draw_wire(canvas, self.w / 2, ch_top - gate_h, self.w / 2, ch_top - gate_h - 25)
        canvas.create_text(self.w / 2, ch_top - gate_h - 38, text="G", font=("Segoe UI", 11, "bold"))

        draw_wire(canvas, body_left, (ch_top + ch_bot) / 2, body_left - 30, (ch_top + ch_bot) / 2)
        canvas.create_text(body_left - 42, (ch_top + ch_bot) / 2, text="S", font=("Segoe UI", 11, "bold"))
        draw_wire(canvas, body_right, (ch_top + ch_bot) / 2, body_right + 30, (ch_top + ch_bot) / 2)
        canvas.create_text(body_right + 42, (ch_top + ch_bot) / 2, text="D", font=("Segoe UI", 11, "bold"))

        for c in self._carriers:
            color = carrier_color if c.kind == "channel" else gate_carrier_color
            canvas.create_oval(c.x - 3.5, c.y - 3.5, c.x + 3.5, c.y + 3.5, fill=color, outline="")

        canvas.create_text(body_left, ch_top - gate_h - 38, text=self.kind.upper(), anchor="w",
                            font=("Segoe UI", 9, "bold"), fill="#666")

        region_key = {
            "cutoff": "junction.state_pinchoff",
            "conducting": "junction.state_conducting",
            "gate_forward": "junction.state_gate_forward",
        }[state["region"]]
        region_color = {
            "cutoff": "#b3691d", "conducting": "#1f6a5f", "gate_forward": "#c0392b",
        }[state["region"]]
        canvas.create_text(self.w / 2, ch_bot + gate_h + 20, text=t(region_key),
                            font=("Segoe UI", 9, "bold"), fill=region_color)

        legend_y = ch_bot + gate_h + 40
        canvas.create_oval(body_left - 2, legend_y - 3, body_left + 4, legend_y + 3,
                            fill=carrier_color, outline="")
        carrier_label = "e⁻" if is_n else "h⁺"
        canvas.create_text(body_left + 32, legend_y, text=f"{carrier_label} {t('junction.electron_flow')}",
                            font=("Segoe UI", 7), fill="#555", anchor="w")
        canvas.create_oval(body_left + 148, legend_y - 3, body_left + 154, legend_y + 3,
                            fill=gate_carrier_color, outline="")
        canvas.create_text(body_left + 180, legend_y, text=t("junction.gate_current_legend"),
                            font=("Segoe UI", 7), fill="#555", anchor="w")
