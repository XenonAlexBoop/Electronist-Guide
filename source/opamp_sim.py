"""
opamp_sim.py - Behavioural time-domain simulation of the classic op-amp
circuits (no UI).

The op-amp model is deliberately simple but shows the effects that matter:
  * output limited to the rails minus a headroom (saturation / clipping)
  * finite gain-bandwidth: a closed-loop stage responds like a first-order
    low-pass with f-3dB = GBW / noise-gain
  * slew-rate limit (V/µs)
Every function returns a dict with the time axis, named traces and metrics.
"""
import math
import numpy as np

MODELS = {
    # name: (GBW Hz, slew V/us, headroom V)   None = ideal
    "ideal": (None, None, 0.0),
    "lm741": (1e6, 0.5, 1.5),
    "tl081": (3e6, 13.0, 1.5),
    "lm358": (1e6, 0.3, 1.5),
    "rrio": (10e6, 10.0, 0.05),
}


class OpAmp:
    def __init__(self, model="ideal", vcc=15.0):
        gbw, sr, head = MODELS[model]
        self.gbw = gbw
        self.sr = sr * 1e6 if sr else None
        self.vmax = vcc - head
        self.vmin = -vcc + head

    def step(self, vo, target, dt, noise_gain=1.0):
        """Advance the output one step towards `target` (what an ideal op-amp
        would output), honouring bandwidth, slew rate and rails."""
        target = min(self.vmax, max(self.vmin, target))
        if self.gbw:
            wc = 2 * math.pi * self.gbw / max(noise_gain, 1.0)
            k = 1 - math.exp(-wc * dt)
            dv = (target - vo) * k
        else:
            dv = target - vo
        if self.sr:
            lim = self.sr * dt
            dv = max(-lim, min(lim, dv))
        return min(self.vmax, max(self.vmin, vo + dv))

    def clamp(self, v):
        return min(self.vmax, max(self.vmin, v))


def source(kind, amp, freq, offset=0.0):
    w = 2 * math.pi * freq
    if kind == "square":
        return lambda t: offset + (amp if math.sin(w * t) >= 0 else -amp)
    if kind == "tri":
        return lambda t: offset + amp * 2 / math.pi * math.asin(math.sin(w * t))
    if kind == "dc":
        return lambda t: offset + amp
    return lambda t: offset + amp * math.sin(w * t)


def _time(periods, freq, n=3000):
    tstop = periods / max(freq, 1e-9)
    t = np.linspace(0, tstop, n + 1)
    return t, tstop / n


def _measure_freq(t, v, level=0.0, skip_frac=0.3):
    """Frequency from rising zero crossings (after the start-up)."""
    i0 = int(len(t) * skip_frac)
    vv = v[i0:] - level
    tt = t[i0:]
    idx = np.where((vv[:-1] < 0) & (vv[1:] >= 0))[0]
    if len(idx) < 2:
        return None
    tc = tt[idx] - vv[idx] * (tt[idx + 1] - tt[idx]) / (vv[idx + 1] - vv[idx])
    return 1.0 / np.mean(np.diff(tc))


# ---------------------------------------------------------------------------
# Linear amplifiers
# ---------------------------------------------------------------------------
def amplifier(kind, P, op, v1, v2=None, freq=1000.0, periods=3):
    t, dt = _time(periods, freq)
    if kind == "inv":
        g1, ng = -P["rf"] / P["rin"], 1 + P["rf"] / P["rin"]
        ideal = lambda a, b: g1 * a
    elif kind == "noninv":
        g1 = 1 + P["rf"] / P["rg"]
        ng = g1
        ideal = lambda a, b: g1 * a
    elif kind == "buffer":
        ng = 1.0
        ideal = lambda a, b: a
    elif kind == "sum":
        rp = 1 / (1 / P["r1"] + 1 / P["r2"])
        ng = 1 + P["rf"] / rp
        ideal = lambda a, b: -(P["rf"] / P["r1"] * a + P["rf"] / P["r2"] * b)
    elif kind == "diff":
        r1, r2 = P["r1"], P["r2"]
        mis = P.get("mis", 0.0) / 100
        r3, r4 = r1, r2 * (1 + mis)
        ng = 1 + r2 / r1
        ideal = lambda a, b: b * r4 / (r3 + r4) * (1 + r2 / r1) - a * r2 / r1
    else:
        raise ValueError(kind)
    vin1 = np.array([v1(x) for x in t])
    vin2 = np.array([v2(x) for x in t]) if v2 else np.zeros_like(t)
    vo = np.zeros_like(t)
    target = np.array([ideal(a, b) for a, b in zip(vin1, vin2)])
    o = op.clamp(target[0])
    for i in range(len(t)):
        o = op.step(o, target[i], dt, ng) if i else o
        vo[i] = o
    return dict(t=t, vin=vin1, vin2=vin2 if v2 else None, vout=vo, ideal=target, noise_gain=ng)


# ---------------------------------------------------------------------------
# Integrator / differentiator
# ---------------------------------------------------------------------------
def integrator(P, op, v1, freq, periods=4):
    t, dt = _time(periods, freq, 4000)
    r, c = P["r"], P["c"]
    rf = P.get("rf", 0) or 0
    vin = np.array([v1(x) for x in t])
    vo = np.zeros_like(t)
    o = 0.0
    for i in range(1, len(t)):
        leak = o / rf if rf > 0 else 0.0
        target = o + (-(vin[i] / r) - leak) / c * dt
        # the integrator itself is the slow part; apply slew and rails
        o = op.step(o, target, dt, 1.0) if op.sr or op.gbw else op.clamp(target)
        vo[i] = o
    return dict(t=t, vin=vin, vout=vo)


def differentiator(P, op, v1, freq, periods=3):
    rin = max(P.get("rin", 0) or 0, 1.0)
    c, rf = P["c"], P["rf"]
    tau = rin * c
    n = int(min(20000, max(3000, periods / freq / (tau / 4))))
    t, dt = _time(periods, freq, n)
    vin = np.array([v1(x) for x in t])
    vo = np.zeros_like(t)
    vc = vin[0]
    o = 0.0
    ng = 1 + rf / rin
    for i in range(1, len(t)):
        # series Rin + C into a virtual ground: i = (vin - vc)/Rin, dvc/dt = i/C
        k = 1 - math.exp(-dt / tau)
        vc = vc + (vin[i] - vc) * k
        cur = (vin[i] - vc) / rin
        o = op.step(o, -rf * cur, dt, ng)
        vo[i] = o
    return dict(t=t, vin=vin, vout=vo)


# ---------------------------------------------------------------------------
# Comparators
# ---------------------------------------------------------------------------
def comparator(P, op, v1, freq, periods=3):
    t, dt = _time(periods, freq)
    vin = np.array([v1(x) for x in t])
    vo = np.zeros_like(t)
    vref = P.get("vref", 0.0)
    o = op.vmax if vin[0] > vref else op.vmin
    for i in range(len(t)):
        target = op.vmax if vin[i] > vref else op.vmin
        o = op.step(o, target, dt, 1.0) if i else o
        vo[i] = o
    return dict(t=t, vin=vin, vout=vo, ut=vref, lt=vref)


def schmitt(P, op, v1, freq, inverting=True, periods=3):
    t, dt = _time(periods, freq)
    vin = np.array([v1(x) for x in t])
    r1, r2, vref = P["r1"], P["r2"], P.get("vref", 0.0)
    vo = np.zeros_like(t)
    vp_tr = np.zeros_like(t)
    if inverting:
        # (+) = divider between Vref (through R1) and Vout (through R2)
        th = lambda o: (vref * r2 + o * r1) / (r1 + r2)
        ut, lt = th(op.vmax), th(op.vmin)
        o = op.vmax if vin[0] < ut else op.vmin
        for i in range(len(t)):
            vp = th(o)
            target = op.vmin if vin[i] > vp else op.vmax
            o = op.step(o, target, dt, 1.0) if i else o
            vo[i] = o
            vp_tr[i] = th(o)
    else:
        # Vin through R1 to (+), R2 from (+) to Vout, (-) at Vref
        ut = (vref * (r1 + r2) - op.vmin * r1) / r2
        lt = (vref * (r1 + r2) - op.vmax * r1) / r2
        o = op.vmin if vin[0] < ut else op.vmax
        for i in range(len(t)):
            vp = (vin[i] * r2 + o * r1) / (r1 + r2)
            target = op.vmax if vp > vref else op.vmin
            o = op.step(o, target, dt, 1.0) if i else o
            vo[i] = o
            vp_tr[i] = vp
    return dict(t=t, vin=vin, vout=vo, ut=ut, lt=lt, vplus=vp_tr)


# ---------------------------------------------------------------------------
# Peak detector / precision rectifier
# ---------------------------------------------------------------------------
def peak_detector(P, op, v1, freq, periods=5, vd=0.6, ilim=0.025):
    t, dt = _time(periods, freq, 4000)
    vin = np.array([v1(x) for x in t])
    c, r = P["c"], P["r"]
    vc, oa = 0.0, 0.0
    vout = np.zeros_like(t)
    vop = np.zeros_like(t)
    for i in range(1, len(t)):
        # while vin > vc the loop is closed through the diode and the output sits
        # one diode drop above vin (charging C); once vc > vin the diode blocks,
        # the loop opens and the output falls to the - rail. C can then only
        # discharge through R.
        target = vin[i] + vd if vin[i] > vc else op.vmin
        oa = op.step(oa, target, dt, 1.0)
        if oa - vd > vc:
            vc = min(oa - vd, vc + ilim / c * dt)      # output current limit
        if r > 0:
            vc -= vc / (r * c) * dt
        vout[i] = vc
        vop[i] = oa
    return dict(t=t, vin=vin, vout=vout, vop=vop)


def precision_rectifier(P, op, v1, freq, periods=3, vd=0.6):
    t, dt = _time(periods, freq, 4000)
    vin = np.array([v1(x) for x in t])
    vout = np.zeros_like(t)
    vop = np.zeros_like(t)
    oa = 0.0
    for i in range(1, len(t)):
        target = vin[i] + vd if vin[i] > 0 else op.vmin     # loop open for vin < 0
        oa = op.step(oa, target, dt, 1.0)
        vout[i] = max(0.0, oa - vd)
        vop[i] = oa
    return dict(t=t, vin=vin, vout=vout, vop=vop)


# ---------------------------------------------------------------------------
# Oscillators
# ---------------------------------------------------------------------------
def relaxation(P, op, periods=5):
    r, c, r1, r2 = P["r"], P["c"], P["r1"], P["r2"]
    beta = r1 / (r1 + r2)
    f_th = 1 / (2 * r * c * math.log((1 + beta) / (1 - beta))) if beta < 1 else 0
    t, dt = _time(periods + 1, f_th, 5000)
    vc = np.zeros_like(t)
    vo = np.zeros_like(t)
    o, x = op.vmax, 0.0
    for i in range(len(t)):
        vp = beta * o
        target = op.vmin if x > vp else op.vmax
        o = op.step(o, target, dt, 1.0) if i else o
        x += (o - x) / (r * c) * dt
        vc[i] = x
        vo[i] = o
    return dict(t=t, vout=vo, vc=vc, f_th=f_th, f_meas=_measure_freq(t, vo), ut=beta * op.vmax,
                lt=beta * op.vmin)


def square_triangle(P, op, periods=4):
    r, c, r1, r2 = P["r"], P["c"], P["r1"], P["r2"]
    f_th = r2 / (4 * r1 * r * c)
    t, dt = _time(periods + 0.5, f_th, 5000)
    sq = np.zeros_like(t)
    tri = np.zeros_like(t)
    s, x = op.vmax, 0.0
    for i in range(len(t)):
        vp = (x * r2 + s * r1) / (r1 + r2)
        target = op.vmax if vp > 0 else op.vmin
        s = op.step(s, target, dt, 1.0) if i else s
        x = op.clamp(x - s / (r * c) * dt)
        sq[i] = s
        tri[i] = x
    return dict(t=t, vout=sq, vtri=tri, f_th=f_th, f_meas=_measure_freq(t, sq),
                tri_amp=op.vmax * r1 / r2)


def wien(P, op, periods=25, stabilise=True):
    r, c, rf, rg = P["r"], P["c"], P["rf"], P["rg"]
    f_th = 1 / (2 * math.pi * r * c)
    a = 1 + rf / rg
    t, dt = _time(periods, f_th, 8000)
    vo = np.zeros_like(t)
    vpl = np.zeros_like(t)
    vc1, vp, o = 0.0, 0.02, 0.0
    vlim = 6.0                    # diodes across part of Rf soften the gain above ~this level
    for i in range(len(t)):
        if stabilise:
            target = vlim * math.tanh(a * vp / vlim)
        else:
            target = a * vp
        o = op.step(o, target, dt, a) if i else o
        cur = (o - vc1 - vp) / r
        vc1 += cur / c * dt
        vp += (cur - vp / r) / c * dt
        vo[i] = o
        vpl[i] = vp
    return dict(t=t, vout=vo, vplus=vpl, f_th=f_th, f_meas=_measure_freq(t, vo, skip_frac=0.6), gain=a)
