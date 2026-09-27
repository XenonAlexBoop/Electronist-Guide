"""
bjt_sim.py - Animated, physically-motivated BJT junction visualizer.

This replaces the old "static diagram redrawn on slider move" approach for
the BJT Junction Visualizer with a small continuously-running particle
simulation. The guiding rule: every visual element (depletion width, field
intensity, carrier spawn rate, crossing probability) is derived from the
*same* electrical-state numbers computed in `compute_junction_state()` -
nothing is set independently just to "look right". Moving a slider changes
Vbe/Vce, which changes that state, which changes what the carriers do.

Geometry note: the semiconductor regions (E/B/C) and the two metallurgical
junction lines are FIXED - they never move as bias changes. Only the
depletion-region overlay drawn around each fixed junction line grows or
shrinks. This matters pedagogically: the material doesn't physically
expand/contract, only the depletion zone (and the barrier/field it
represents) does. See `_geometry()` (fixed) vs `_depletion_overlay()`
(bias-dependent) below.

Usage (see tabs/transistor.py):
    sim = BjtJunctionSim(canvas, kind="NPN", on_stats=update_panel)
    sim.start()
    ...
    sim.set_bias(vbe=0.7, vce=5.0)   # called from slider callbacks
    ...
    sim.stop()                        # called before the canvas is destroyed
"""
import math
import random

from drawing import draw_wire, _N_COLOR, _P_COLOR
from i18n import t

TICK_MS = 40          # ~25 fps
MAX_ACTIVE_CARRIERS = 55
MAX_SPAWN_RATE = 0.55  # spawn probability per tick at inj_* == 1.0
N_IDLE_CARRIERS = 7     # ambient "material has free carriers at rest" dots

SPEED_BULK = 3.2
SPEED_CROSS_MIN = 0.9
SPEED_CROSS_MAX = 3.2

DEPLETION_PX_MIN = 6
DEPLETION_PX_MAX = 64

E_FRAC = 0.32   # fraction of body width given to the emitter block
B_FRAC = 0.20   # fraction given to the base block (collector gets the rest)

TURN_ON = 0.55
SLOPE = 0.035

STAT_SCALE = 11.0  # display scaling only - these stay "relative units", not physical mA


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def _sigmoid(x):
    if x > 30:
        return 1.0
    if x < -30:
        return 0.0
    return 1.0 / (1.0 + math.exp(-x))


def compute_junction_state(vbe, vce, npn=True):
    """Pure function mapping bias voltages to a simplified, internally
    consistent picture of a BJT's two junctions.

    Note on NPN/PNP: the app's Vbe/Vce sliders use the same range and the
    same sign convention for both polarities (there's no separate "PNP
    range" the way there is for the MOSFET/JFET tabs) - a positive slider
    value always means "this junction is being driven toward forward bias"
    for whichever polarity is currently selected. So `npn` does NOT flip
    the sign of the electrical formulas here; it only changes carrier
    symbol/color and the C-B current-arrow direction at draw time."""
    ve = vbe
    vc = vce
    vbc = ve - vc  # voltage across the C-B junction, base referenced

    inj_eb = _sigmoid((ve - TURN_ON) / SLOPE)     # E->B carrier injection strength
    inj_cb = _sigmoid((vbc - TURN_ON) / SLOPE)    # C->B carrier injection strength
                                                    # (only significant when C-B is forward biased)
    barrier_eb = 1.0 - inj_eb
    barrier_cb = 1.0 - inj_cb

    # Depletion width (0..1, exaggerated for visibility): forward bias
    # narrows it, reverse bias widens it. Directly a function of the same
    # junction voltages used above, not an independent slider effect.
    depletion_eb = _clamp(0.42 - 0.55 * ve, 0.08, 1.0)
    depletion_cb = _clamp(0.42 + 0.10 * (vc - ve), 0.10, 1.0)

    # Sweep strength: how strongly each junction's field helps carriers that
    # reach it cross over. Positive = reverse biased, field assists carriers
    # across (normal active-mode C-B behavior). Negative/small = forward
    # biased, field no longer cleanly sweeps carriers (base flooding in
    # saturation, or the mirror case at the E-B junction in reverse-active).
    sweep_cb = _clamp((vc - ve) / 4.0, -0.35, 1.0)
    sweep_eb = _clamp(-ve / 4.0, -0.35, 1.0)

    # Base recombination: low baseline (most injected carriers should
    # successfully cross to the collector in active mode - that's what
    # "current gain" looks like), elevated sharply when the base is
    # flooded because the C-B field isn't efficiently sweeping carriers out.
    recomb_base = 0.0007 + 0.10 * max(0.0, -sweep_cb)

    if inj_eb < 0.15 and inj_cb < 0.15:
        state = "cutoff"
    elif inj_eb >= 0.5 and inj_cb < 0.3 and sweep_cb > 0.15:
        state = "active"
    elif inj_eb >= 0.3 and inj_cb >= 0.3:
        state = "saturation"
    elif inj_cb >= 0.5 and inj_eb < 0.3:
        state = "reverse_active"
    else:
        state = "transition"

    return {
        "npn": npn, "vbe": vbe, "vce": vce, "vbc": vbc,
        "inj_eb": inj_eb, "inj_cb": inj_cb,
        "barrier_eb": barrier_eb, "barrier_cb": barrier_cb,
        "depletion_eb": depletion_eb, "depletion_cb": depletion_cb,
        "sweep_cb": sweep_cb, "sweep_eb": sweep_eb,
        "recomb_base": recomb_base, "state": state,
        "eb_forward": ve >= TURN_ON * 0.35,   # loose "which way is this junction biased" flags,
        "cb_forward": vbc >= TURN_ON * 0.35,  # used only for the operating-region panel text
    }


class _Carrier:
    """One animated carrier. `origin` is which terminal it was injected
    from ('E' or 'C'); that plus `stage` drives its position through the
    E -> (EB junction) -> B -> (CB junction) -> C pipeline (or the mirror
    image for origin='C', relevant in reverse-active operation). `target`
    is the x position a crossing carrier is currently moving toward -
    captured once when the crossing begins so a mid-flight bias change
    can't yank it around."""
    __slots__ = ("x", "y", "origin", "stage", "speed", "target")

    def __init__(self, x, y, origin, stage, speed=SPEED_BULK, target=0.0):
        self.x = x
        self.y = y
        self.origin = origin
        self.stage = stage
        self.speed = speed
        self.target = target


class BjtJunctionSim:
    def __init__(self, canvas, kind="NPN", w=440, h=300, vbe=0.7, vce=5.0, on_stats=None):
        self.canvas = canvas
        self.kind = kind
        self.w = w
        self.h = h
        self.vbe = vbe
        self.vce = vce
        self.on_stats = on_stats  # optional callback(state, ib, ic) fired once per tick

        self._rng = random.Random()
        self._carriers = []
        self._idle_carriers = []
        self._running = False
        self._after_id = None
        self._collected_c = 0.0
        self._collected_e = 0.0
        self._recombined = 0.0

        self._geo = self._geometry()
        self._init_idle_carriers()

    # ------------------------------------------------------------------
    # Public control
    # ------------------------------------------------------------------
    def set_bias(self, vbe, vce):
        self.vbe = vbe
        self.vce = vce

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
    # Geometry
    # ------------------------------------------------------------------
    def _geometry(self):
        """Fixed layout: the semiconductor blocks and the two metallurgical
        junction lines (xj1 = E-B, xj2 = C-B) never depend on bias. This is
        computed once (in __init__) and reused every frame - nothing here
        reads `state`."""
        body_top, body_bot = 66, self.h - 86
        body_left, body_right = 40, self.w - 40
        total_w = body_right - body_left

        e_w = total_w * E_FRAC
        b_w = total_w * B_FRAC
        c_w = total_w - e_w - b_w

        x0 = body_left
        xj1 = x0 + e_w
        xj2 = xj1 + b_w
        x5 = xj2 + c_w

        return {
            "body_top": body_top, "body_bot": body_bot,
            "x0": x0, "xj1": xj1, "xj2": xj2, "x5": x5,
        }

    def _depletion_overlay(self, state):
        """Bias-dependent depletion-region extent, as a band straddling
        each *fixed* junction line. Clamped so the two overlays can never
        touch/cross each other or spill outside the E/C outer edges,
        regardless of how extreme the bias is."""
        geo = self._geo
        mid = (geo["xj1"] + geo["xj2"]) / 2

        eb_half = (DEPLETION_PX_MIN + (DEPLETION_PX_MAX - DEPLETION_PX_MIN) * state["depletion_eb"]) / 2
        cb_half = (DEPLETION_PX_MIN + (DEPLETION_PX_MAX - DEPLETION_PX_MIN) * state["depletion_cb"]) / 2

        eb_left = max(geo["x0"] + 2, geo["xj1"] - eb_half)
        eb_right = min(mid - 2, geo["xj1"] + eb_half)
        eb_left = min(eb_left, eb_right)  # guard against pathological clamping

        cb_left = max(mid + 2, geo["xj2"] - cb_half)
        cb_right = min(geo["x5"] - 2, geo["xj2"] + cb_half)
        cb_right = max(cb_right, cb_left)

        return {"eb_left": eb_left, "eb_right": eb_right, "cb_left": cb_left, "cb_right": cb_right}

    def _init_idle_carriers(self):
        self._idle_carriers = []
        for _ in range(N_IDLE_CARRIERS):
            self._idle_carriers.append({
                "frac": self._rng.uniform(0.05, 0.95),
                "region": self._rng.choice(["E", "B", "C"]),
                "y_off": self._rng.uniform(-0.28, 0.28),
                "phase": self._rng.uniform(0, math.tau),
            })

    def _current_estimate(self, state):
        """Expected-value IB/IC, computed analytically from the *same*
        per-tick probabilities `_advance_one` actually uses for each
        carrier (injection rate, base recombination chance, C-B crossing
        chance). This is deliberately not sampled from the live particle
        counts: those are individually-rare stochastic events (a handful
        of recombinations per second), so an event-rate estimate stays
        noisy no matter how much it's smoothed. Taking the expected value
        of the same probabilities instead gives an immediately-responsive,
        stable reading that still reflects the identical electrical model
        the animation is built on - nothing here is an independently
        chosen number.
        """
        geo = self._geo
        ie = state["inj_eb"] * MAX_SPAWN_RATE  # emitter injection rate (carriers/tick)
        if ie <= 0.0:
            return 0.0, 0.0

        # Every carrier that enters the base eventually either recombines
        # in transit or reaches the C-B junction (EB_block never removes a
        # carrier, it only delays it) - so start from the base-transit leg.
        n_transit = max((geo["xj2"] - geo["xj1"]) / SPEED_BULK, 1.0)
        p_survive_transit = (1.0 - state["recomb_base"]) ** n_transit

        p_cross = _clamp(0.05 + 0.55 * max(0.0, state["sweep_cb"]), 0.0, 1.0)
        p_recomb_wait = _clamp(state["recomb_base"] * 2.0, 0.0, 1.0)
        p_exit = p_cross + p_recomb_wait
        p_cross_at_block = (p_cross / p_exit) if p_exit > 0 else 0.0

        p_reach_collector = p_survive_transit * p_cross_at_block
        ic = ie * p_reach_collector * STAT_SCALE
        ib = ie * (1.0 - p_reach_collector) * STAT_SCALE
        return ib, ic

    # ------------------------------------------------------------------
    # Simulation step
    # ------------------------------------------------------------------
    def _tick(self):
        if not self._running:
            return
        if not self.canvas.winfo_exists():
            self._running = False
            return
        state = compute_junction_state(self.vbe, self.vce, npn=self.kind.upper() == "NPN")
        overlay = self._depletion_overlay(state)
        self._advance(state, overlay)
        self._draw(state, overlay)
        if self.on_stats is not None:
            ib, ic = self._current_estimate(state)
            self.on_stats(state, ib, ic)
        self._after_id = self.canvas.after(TICK_MS, self._tick)

    def _advance(self, state, overlay):
        geo = self._geo
        mid_y = (geo["body_top"] + geo["body_bot"]) / 2
        span = (geo["body_bot"] - geo["body_top"]) * 0.28

        # --- spawn new carriers, gated purely by the injection strengths ---
        # Spawned at a randomized depth within the bulk region (not pinned
        # to the outer edge) so a slider change is reflected at the junction
        # within roughly a second rather than after a long uniform drift -
        # the doped material already has free carriers throughout its
        # volume, it isn't only the ones freshly entering at the contact.
        if len(self._carriers) < MAX_ACTIVE_CARRIERS:
            if self._rng.random() < state["inj_eb"] * MAX_SPAWN_RATE:
                y = mid_y + self._rng.uniform(-span, span)
                x = geo["x0"] + self._rng.uniform(0.0, 0.85) * (geo["xj1"] - geo["x0"])
                self._carriers.append(_Carrier(x, y, origin="E", stage="E"))
            if self._rng.random() < state["inj_cb"] * MAX_SPAWN_RATE:
                y = mid_y + self._rng.uniform(-span, span)
                x = geo["x5"] - self._rng.uniform(0.0, 0.85) * (geo["x5"] - geo["xj2"])
                self._carriers.append(_Carrier(x, y, origin="C", stage="C"))

        survivors = []
        for c in self._carriers:
            c.y += self._rng.uniform(-0.4, 0.4)
            c.y = _clamp(c.y, mid_y - span, mid_y + span)
            keep = self._advance_one(c, state, geo, overlay)
            if keep:
                survivors.append(c)
        self._carriers = survivors

        # ambient idle carriers just jitter in place, no crossing - present
        # even at cutoff to suggest "the material still has carriers, they
        # just aren't flowing", without implying current.
        for idle in self._idle_carriers:
            idle["phase"] += 0.12

    def _advance_one(self, c, state, geo, overlay):
        """Advance one carrier by one tick. Returns False if it should be
        removed (collected at a terminal, or recombined in the base)."""
        forward = c.origin == "E"  # forward = moving left-to-right (E->C)
        direction = 1 if forward else -1

        if c.stage in ("E", "C"):
            # drifting through a neutral bulk region toward the (fixed)
            # junction line
            c.x += direction * SPEED_BULK
            boundary = geo["xj1"] if (c.stage == "E") else geo["xj2"]
            reached = (c.x >= boundary) if forward else (c.x <= boundary)
            if reached:
                c.stage = "EB_block" if c.stage == "E" else "CB_block"
            return True

        if c.stage == "EB_block":
            # sitting right at the fixed E-B junction line, jittering,
            # re-rolling each tick whether it has enough probability to
            # cross - this position never moves, regardless of bias.
            prob = state["inj_eb"] if forward else max(0.0, state["sweep_eb"])
            c.x += self._rng.uniform(-0.5, 0.5)
            c.x = _clamp(c.x, geo["xj1"] - 2, geo["xj1"] + 2)
            if self._rng.random() < 0.06 + 0.5 * prob:
                c.stage = "EB_cross"
                c.target = overlay["eb_right"] if forward else overlay["eb_left"]
                span = max(abs(c.target - c.x), 1.0)
                c.speed = _clamp(SPEED_CROSS_MIN + prob * (SPEED_CROSS_MAX - SPEED_CROSS_MIN),
                                  SPEED_CROSS_MIN, SPEED_CROSS_MAX) * (span / 30.0 + 0.6)
            return True

        if c.stage == "CB_block":
            prob = max(0.0, state["sweep_cb"]) if forward else state["inj_cb"]
            c.x += self._rng.uniform(-0.5, 0.5)
            c.x = _clamp(c.x, geo["xj2"] - 2, geo["xj2"] + 2)
            if self._rng.random() < state["recomb_base"] * 2:
                return False  # recombined while waiting at the barrier
            if self._rng.random() < 0.05 + 0.55 * prob:
                c.stage = "CB_cross"
                c.target = overlay["cb_right"] if forward else overlay["cb_left"]
                span = max(abs(c.target - c.x), 1.0)
                c.speed = _clamp(SPEED_CROSS_MIN + prob * (SPEED_CROSS_MAX - SPEED_CROSS_MIN),
                                  SPEED_CROSS_MIN, SPEED_CROSS_MAX) * (span / 30.0 + 0.6)
            return True

        if c.stage in ("EB_cross", "CB_cross"):
            c.x += direction * c.speed
            arrived = (c.x >= c.target) if forward else (c.x <= c.target)
            if arrived:
                c.x = c.target
                if c.stage == "EB_cross":
                    c.stage = "B" if forward else "E_exit"
                else:
                    c.stage = "C_exit" if forward else "B"
            return True

        if c.stage == "B":
            # free bulk drift across the whole base width (xj1..xj2) -
            # crossing difficulty is already modeled at the *_block stages
            # above, so movement inside the base itself is unobstructed
            # aside from the chance of recombining.
            c.x += direction * SPEED_BULK
            if self._rng.random() < state["recomb_base"]:
                self._recombined += 1
                return False
            boundary = geo["xj2"] if forward else geo["xj1"]
            reached = (c.x >= boundary) if forward else (c.x <= boundary)
            if reached:
                c.stage = "CB_block" if forward else "EB_block"
            return True

        if c.stage == "C_exit":
            c.x += SPEED_BULK
            if c.x >= geo["x5"]:
                self._collected_c += 1
                return False
            return True

        if c.stage == "E_exit":
            c.x -= SPEED_BULK
            if c.x <= geo["x0"]:
                self._collected_e += 1
                return False
            return True

        return False

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------
    def _draw(self, state, overlay):
        canvas = self.canvas
        canvas.delete("all")
        npn = state["npn"]
        outer_color = _N_COLOR if npn else _P_COLOR
        inner_color = _P_COLOR if npn else _N_COLOR
        carrier_label = "e⁻" if npn else "h⁺"
        carrier_dot_color = "#2255aa" if npn else "#aa2255"

        geo = self._geo
        x0, xj1, xj2, x5 = geo["x0"], geo["xj1"], geo["xj2"], geo["x5"]
        body_top, body_bot = geo["body_top"], geo["body_bot"]
        mid_y = (body_top + body_bot) / 2

        # --- fixed semiconductor blocks: these never move ---
        canvas.create_rectangle(x0, body_top, xj1, body_bot, fill=outer_color, outline="#333", width=2)
        canvas.create_rectangle(xj1, body_top, xj2, body_bot, fill=inner_color, outline="#333", width=2)
        canvas.create_rectangle(xj2, body_top, x5, body_bot, fill=outer_color, outline="#333", width=2)

        # --- depletion-region overlays: translucent (stippled) bands that
        # grow/shrink around the fixed junction lines, drawn on top of the
        # solid blocks above rather than displacing them ---
        canvas.create_rectangle(overlay["eb_left"], body_top, overlay["eb_right"], body_bot,
                                 fill="#ffffff", stipple="gray50", outline="")
        canvas.create_rectangle(overlay["cb_left"], body_top, overlay["cb_right"], body_bot,
                                 fill="#ffffff", stipple="gray50", outline="")

        # --- the actual metallurgical junctions: fixed solid lines, always
        # in the same place regardless of bias ---
        canvas.create_line(xj1, body_top, xj1, body_bot, fill="#222", width=2)
        canvas.create_line(xj2, body_top, xj2, body_bot, fill="#222", width=2)

        self._draw_field_ticks(overlay["eb_left"], overlay["eb_right"], body_top, body_bot,
                                state["barrier_eb"], rightward=False)
        cb_rightward = state["sweep_cb"] >= 0
        cb_intensity = state["sweep_cb"] if cb_rightward else min(1.0, -state["sweep_cb"] / 0.35)
        self._draw_field_ticks(overlay["cb_left"], overlay["cb_right"], body_top, body_bot,
                                cb_intensity, rightward=cb_rightward)

        label_e = "N" if npn else "P"
        label_b = "P" if npn else "N"
        canvas.create_text((x0 + xj1) / 2, mid_y - (body_bot - body_top) / 2 + 12,
                            text=f"{label_e}\n({t('junction.emitter')})", font=("Segoe UI", 9, "bold"))
        canvas.create_text((xj1 + xj2) / 2, mid_y - (body_bot - body_top) / 2 + 12,
                            text=f"{label_b}\n({t('junction.base')})", font=("Segoe UI", 9, "bold"))
        canvas.create_text((xj2 + x5) / 2, mid_y - (body_bot - body_top) / 2 + 12,
                            text=f"{label_e}\n({t('junction.collector')})", font=("Segoe UI", 9, "bold"))

        # terminal leads - straight vertical leads only, all terminating at
        # the same height, with their letter labels lined up above them
        # (no sideways jog between terminals, and clear of the kind tag).
        lead_top = 30
        label_y = 15
        e_x, b_x, c_x = (x0 + xj1) / 2, (xj1 + xj2) / 2, (xj2 + x5) / 2
        draw_wire(canvas, e_x, body_top, e_x, lead_top)
        draw_wire(canvas, b_x, body_top, b_x, lead_top)
        draw_wire(canvas, c_x, body_top, c_x, lead_top)
        canvas.create_text(e_x, label_y, text="E", font=("Segoe UI", 11, "bold"))
        canvas.create_text(b_x, label_y, text="B", font=("Segoe UI", 11, "bold"))
        canvas.create_text(c_x, label_y, text="C", font=("Segoe UI", 11, "bold"))

        # device-type tag, tucked in the corner so it never competes with
        # the E/B/C cluster above the leads.
        canvas.create_text(x0, label_y, text=self.kind.upper(), anchor="w",
                            font=("Segoe UI", 9, "bold"), fill="#666")

        # conventional current: opposite to electron motion (NPN), same
        # direction as hole motion (PNP) - drawn as a thin dashed arrow
        # above the leads, clearly labeled so it isn't confused with the
        # carrier dots below.
        cur_dir = -1 if npn else 1
        self._draw_current_arrow(canvas, (x0 + xj1) / 2, body_top - 15, cur_dir)
        self._draw_current_arrow(canvas, (xj2 + x5) / 2, body_top - 15, -cur_dir)

        # carriers
        for idle in self._idle_carriers:
            regions = {"E": (x0, xj1), "B": (xj1, xj2), "C": (xj2, x5)}
            rx0, rx1 = regions[idle["region"]]
            ix = rx0 + idle["frac"] * (rx1 - rx0) + 2.5 * math.sin(idle["phase"])
            iy = mid_y + idle["y_off"] * (body_bot - body_top) + 2.0 * math.cos(idle["phase"] * 0.7)
            canvas.create_oval(ix - 2, iy - 2, ix + 2, iy + 2, fill="#c9c9c9", outline="")

        for c in self._carriers:
            canvas.create_oval(c.x - 3.5, c.y - 3.5, c.x + 3.5, c.y + 3.5,
                                fill=carrier_dot_color, outline="")

        # banner / status
        state_key = {
            "cutoff": "junction.state_cutoff",
            "active": "junction.state_active_full",
            "saturation": "junction.state_saturation",
            "reverse_active": "junction.state_reverse_active",
            "transition": "junction.state_transition",
        }[state["state"]]
        banner_color = {
            "cutoff": "#999", "active": "#1f6a5f", "saturation": "#b3691d",
            "reverse_active": "#7a3fa0", "transition": "#555",
        }[state["state"]]
        canvas.create_text(self.w / 2, body_bot + 18, text=t(state_key),
                            font=("Segoe UI", 9, "bold"), fill=banner_color)
        canvas.create_text((overlay["eb_left"] + overlay["eb_right"]) / 2, body_bot + 40,
                            text=t("junction.depletion_eb_short"), font=("Segoe UI", 7), fill="#777")
        canvas.create_text((overlay["cb_left"] + overlay["cb_right"]) / 2, body_bot + 40,
                            text=t("junction.depletion_cb_short"), font=("Segoe UI", 7), fill="#777")

        legend_y = body_bot + 58
        canvas.create_oval(x0 - 2, legend_y - 3, x0 + 4, legend_y + 3, fill=carrier_dot_color, outline="")
        canvas.create_text(x0 + 34, legend_y, text=f"{carrier_label} {t('junction.electron_flow')}",
                            font=("Segoe UI", 7), fill="#555", anchor="w")
        canvas.create_line(x0 + 150, legend_y, x0 + 170, legend_y, fill="#555", dash=(3, 2), arrow="last")
        canvas.create_text(x0 + 178, legend_y, text=t("junction.conventional_current"),
                            font=("Segoe UI", 7), fill="#555", anchor="w")

    def _draw_field_ticks(self, xa, xb, top, bot, intensity, rightward=True):
        intensity = _clamp(intensity, 0.0, 1.0)
        if intensity < 0.04 or xb - xa < 4:
            return
        n = 2 + round(6 * intensity)
        color = _lerp_color("#dddddd", "#c0392b", intensity)
        span = bot - top
        for i in range(n):
            y = top + span * (i + 1) / (n + 1)
            cx = (xa + xb) / 2
            half = max(3.0, (xb - xa) / 2 - 2)
            if rightward:
                x_start, x_end = cx - half, cx + half
            else:
                x_start, x_end = cx + half, cx - half
            self.canvas.create_line(x_start, y, x_end, y, fill=color,
                                     width=1 + round(1.5 * intensity), arrow="last")

    def _draw_current_arrow(self, canvas, x, y, direction):
        length = 16
        x_start = x - direction * length / 2
        x_end = x + direction * length / 2
        canvas.create_line(x_start, y, x_end, y, fill="#8a5a00", dash=(3, 2), width=1, arrow="last")


def _lerp_color(c1, c2, t_):
    t_ = _clamp(t_, 0.0, 1.0)
    r1, g1, b1 = int(c1[1:3], 16), int(c1[3:5], 16), int(c1[5:7], 16)
    r2, g2, b2 = int(c2[1:3], 16), int(c2[3:5], 16), int(c2[5:7], 16)
    r = round(r1 + (r2 - r1) * t_)
    g = round(g1 + (g2 - g1) * t_)
    b = round(b1 + (b2 - b1) * t_)
    return f"#{r:02x}{g:02x}{b:02x}"
