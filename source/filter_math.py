"""
filter_math.py - Transfer functions of the classic analogue filters and
the numerical tools to simulate them (no UI).

Every filter is described by H(s) = num(s) / den(s) (numpy polynomial
coefficient lists, highest power first). From that one description we get
the Bode plot, poles/zeros, and - after a bilinear transform - the time
response to any input (sine, square, triangle, sweep, step).
"""
import math
import numpy as np

TWO_PI = 2 * math.pi


# ---------------------------------------------------------------------------
# Numerical helpers
# ---------------------------------------------------------------------------
def freq_response(num, den, f):
    s = 1j * TWO_PI * np.asarray(f)
    return np.polyval(num, s) / np.polyval(den, s)


def bilinear(num, den, fs):
    """Analogue (s) -> digital (z) coefficients via the bilinear transform."""
    n = max(len(num), len(den)) - 1
    num = np.concatenate([np.zeros(n + 1 - len(num)), num])
    den = np.concatenate([np.zeros(n + 1 - len(den)), den])
    K = 2 * fs
    b = np.zeros(n + 1)
    a = np.zeros(n + 1)
    for k in range(n + 1):
        # coefficient of s^(n-k)
        p = n - k
        term = np.array([1.0])
        for _ in range(p):
            term = np.polymul(term, [1.0, -1.0])      # (1 - z^-1)
        for _ in range(n - p):
            term = np.polymul(term, [1.0, 1.0])       # (1 + z^-1)
        b += num[k] * K ** p * term
        a += den[k] * K ** p * term
    return b / a[0], a / a[0]


def lfilter(b, a, x):
    """Direct-form II transposed IIR filter (small orders, plain Python)."""
    n = len(a) - 1
    z = [0.0] * (n + 1)
    y = np.empty_like(x)
    b = [float(v) for v in b]
    a = [float(v) for v in a]
    for i, xi in enumerate(x):
        yi = b[0] * xi + z[0]
        for k in range(n - 1):
            z[k] = b[k + 1] * xi + z[k + 1] - a[k + 1] * yi
        if n:
            z[n - 1] = b[n] * xi - a[n] * yi
        y[i] = yi
    return y


def simulate(num, den, t, x):
    fs = 1.0 / (t[1] - t[0])
    b, a = bilinear(np.asarray(num, float), np.asarray(den, float), fs)
    return lfilter(b, a, np.asarray(x, float))


def waveform(kind, amp, f, t, f_lo=None, f_hi=None):
    w = TWO_PI * f
    if kind == "square":
        return amp * np.where(np.sin(w * t) >= 0, 1.0, -1.0)
    if kind == "tri":
        return amp * 2 / math.pi * np.arcsin(np.sin(w * t))
    if kind == "sweep":
        T = t[-1] if t[-1] > 0 else 1.0
        k = math.log(f_hi / f_lo) / T
        phase = TWO_PI * f_lo * (np.exp(k * t) - 1) / k
        return amp * np.sin(phase)
    if kind == "step":
        return amp * np.ones_like(t)
    return amp * np.sin(w * t)


def harmonics(kind, amp, n=15):
    """(k, amplitude) of the Fourier series of the standard waveforms."""
    out = []
    for k in range(1, n + 1):
        if kind == "square":
            a = 4 * amp / (math.pi * k) if k % 2 else 0.0
        elif kind == "tri":
            a = 8 * amp / (math.pi ** 2 * k * k) if k % 2 else 0.0
        else:
            a = amp if k == 1 else 0.0
        out.append((k, a))
    return out


def minus3db(num, den, f_lo, f_hi, ref=None):
    """Frequencies where |H| crosses ref/sqrt(2) (log sweep)."""
    f = np.logspace(math.log10(f_lo), math.log10(f_hi), 3000)
    mag = np.abs(freq_response(num, den, f))
    if ref is None:
        ref = mag.max()
    lvl = ref / math.sqrt(2)
    above = mag >= lvl
    idx = np.where(above[:-1] != above[1:])[0]
    out = []
    for i in idx:
        # log-interpolate
        m0, m1 = mag[i], mag[i + 1]
        fr = (lvl - m0) / (m1 - m0) if m1 != m0 else 0
        out.append(10 ** (math.log10(f[i]) + fr * (math.log10(f[i + 1]) - math.log10(f[i]))))
    return out


# ---------------------------------------------------------------------------
# Filter catalogue
#   params: list of (key, symbol, default, unit)
#   tf(P) -> (num, den)
#   info(P) -> dict(f0=..., q=..., gain=..., order=..., kind='lp'|'hp'|'bp'|'bs')
#   design(P, f0, q, g) -> dict of new values  (keeps the "base" part)
# ---------------------------------------------------------------------------
def _rc_lp():
    return dict(
        params=[("r", "R", 1e3, "Ω"), ("c", "C", 100e-9, "F")],
        tf=lambda P: ([1.0], [P["r"] * P["c"], 1.0]),
        info=lambda P: dict(f0=1 / (TWO_PI * P["r"] * P["c"]), q=None, gain=1.0, order=1, kind="lp"),
        design=lambda P, f0, q, g: dict(r=1 / (TWO_PI * f0 * P["c"])),
        design_keeps="c",
    )


def _rc_hp():
    return dict(
        params=[("c", "C", 100e-9, "F"), ("r", "R", 1e3, "Ω")],
        tf=lambda P: ([P["r"] * P["c"], 0.0], [P["r"] * P["c"], 1.0]),
        info=lambda P: dict(f0=1 / (TWO_PI * P["r"] * P["c"]), q=None, gain=1.0, order=1, kind="hp"),
        design=lambda P, f0, q, g: dict(r=1 / (TWO_PI * f0 * P["c"])),
        design_keeps="c",
    )


def _rl_lp():
    return dict(
        params=[("l", "L", 10e-3, "H"), ("r", "R", 100.0, "Ω")],
        tf=lambda P: ([1.0], [P["l"] / P["r"], 1.0]),
        info=lambda P: dict(f0=P["r"] / (TWO_PI * P["l"]), q=None, gain=1.0, order=1, kind="lp"),
        design=lambda P, f0, q, g: dict(r=TWO_PI * f0 * P["l"]),
        design_keeps="l",
    )


def _rl_hp():
    return dict(
        params=[("r", "R", 100.0, "Ω"), ("l", "L", 10e-3, "H")],
        tf=lambda P: ([P["l"] / P["r"], 0.0], [P["l"] / P["r"], 1.0]),
        info=lambda P: dict(f0=P["r"] / (TWO_PI * P["l"]), q=None, gain=1.0, order=1, kind="hp"),
        design=lambda P, f0, q, g: dict(r=TWO_PI * f0 * P["l"]),
        design_keeps="l",
    )


def _rcrc_lp():
    def tf(P):
        r1, c1, r2, c2 = P["r1"], P["c1"], P["r2"], P["c2"]
        return [1.0], [r1 * c1 * r2 * c2, r1 * c1 + r2 * c2 + r1 * c2, 1.0]

    def info(P):
        num, den = tf(P)
        w0 = 1 / math.sqrt(den[0])
        return dict(f0=w0 / TWO_PI, q=math.sqrt(den[0]) / den[1], gain=1.0, order=2, kind="lp")
    return dict(
        params=[("r1", "R1", 1e3, "Ω"), ("c1", "C1", 100e-9, "F"), ("r2", "R2", 10e3, "Ω"), ("c2", "C2", 10e-9, "F")],
        tf=tf, info=info,
        design=lambda P, f0, q, g: dict(r1=1 / (TWO_PI * f0 * P["c1"]), r2=10 / (TWO_PI * f0 * P["c1"]),
                                        c2=P["c1"] / 10),
        design_keeps="c1",
    )


def _twin_t():
    def tf(P):
        w0 = 1 / (P["r"] * P["c"])
        return [1.0, 0.0, w0 * w0], [1.0, 4 * w0, w0 * w0]
    return dict(
        params=[("r", "R", 10e3, "Ω"), ("c", "C", 10e-9, "F")],
        tf=tf,
        info=lambda P: dict(f0=1 / (TWO_PI * P["r"] * P["c"]), q=0.25, gain=1.0, order=2, kind="bs"),
        design=lambda P, f0, q, g: dict(r=1 / (TWO_PI * f0 * P["c"])),
        design_keeps="c",
    )


def _rlc_bp():
    def tf(P):
        r, l, c = P["r"], P["l"], P["c"]
        return [r * c, 0.0], [l * c, r * c, 1.0]

    def design(P, f0, q, g):
        c = P["c"]
        w0 = TWO_PI * f0
        l = 1 / (w0 * w0 * c)
        return dict(l=l, r=math.sqrt(l / c) / q)
    return dict(
        params=[("l", "L", 10e-3, "H"), ("c", "C", 100e-9, "F"), ("r", "R", 100.0, "Ω")],
        tf=tf,
        info=lambda P: dict(f0=1 / (TWO_PI * math.sqrt(P["l"] * P["c"])),
                            q=math.sqrt(P["l"] / P["c"]) / P["r"], gain=1.0, order=2, kind="bp"),
        design=design, design_keeps="c", uses_q=True,
    )


def _rlc_bs():
    def tf(P):
        r, l, c = P["r"], P["l"], P["c"]
        return [l * c, 0.0, 1.0], [l * c, r * c, 1.0]
    d = _rlc_bp()
    return dict(
        params=[("r", "R", 100.0, "Ω"), ("l", "L", 10e-3, "H"), ("c", "C", 100e-9, "F")],
        tf=tf,
        info=lambda P: dict(f0=1 / (TWO_PI * math.sqrt(P["l"] * P["c"])),
                            q=math.sqrt(P["l"] / P["c"]) / P["r"], gain=1.0, order=2, kind="bs"),
        design=d["design"], design_keeps="c", uses_q=True,
    )


def _lc_lp():
    def tf(P):
        l, c, r = P["l"], P["c"], P["r"]
        return [1.0], [l * c, l / r, 1.0]

    def design(P, f0, q, g):
        r = P["r"]
        w0 = TWO_PI * f0
        return dict(c=q / (w0 * r), l=r / (q * w0))
    return dict(
        params=[("l", "L", 10e-3, "H"), ("c", "C", 1e-6, "F"), ("r", "R load", 70.0, "Ω")],
        tf=tf,
        info=lambda P: dict(f0=1 / (TWO_PI * math.sqrt(P["l"] * P["c"])), q=P["r"] * math.sqrt(P["c"] / P["l"]),
                            gain=1.0, order=2, kind="lp"),
        design=design, design_keeps="r", uses_q=True,
    )


def _lc_hp():
    def tf(P):
        l, c, r = P["l"], P["c"], P["r"]
        return [l * c, 0.0, 0.0], [l * c, l / r, 1.0]
    d = _lc_lp()
    return dict(
        params=[("c", "C", 1e-6, "F"), ("l", "L", 10e-3, "H"), ("r", "R load", 70.0, "Ω")],
        tf=tf,
        info=lambda P: dict(f0=1 / (TWO_PI * math.sqrt(P["l"] * P["c"])), q=P["r"] * math.sqrt(P["c"] / P["l"]),
                            gain=1.0, order=2, kind="hp"),
        design=d["design"], design_keeps="r", uses_q=True,
    )


def _act_lp1():
    return dict(
        params=[("rin", "Rin", 1e3, "Ω"), ("rf", "Rf", 10e3, "Ω"), ("c", "C", 10e-9, "F")],
        tf=lambda P: ([-P["rf"] / P["rin"]], [P["rf"] * P["c"], 1.0]),
        info=lambda P: dict(f0=1 / (TWO_PI * P["rf"] * P["c"]), q=None, gain=P["rf"] / P["rin"], order=1, kind="lp"),
        design=lambda P, f0, q, g: dict(c=1 / (TWO_PI * f0 * P["rf"]), rin=P["rf"] / max(g, 1e-6)),
        design_keeps="rf", uses_g=True,
    )


def _sk_lp():
    def tf(P):
        r1, r2, c1, c2 = P["r1"], P["r2"], P["c1"], P["c2"]
        return [1.0], [r1 * r2 * c1 * c2, c2 * (r1 + r2), 1.0]

    def info(P):
        r1, r2, c1, c2 = P["r1"], P["r2"], P["c1"], P["c2"]
        x = math.sqrt(r1 * r2 * c1 * c2)
        return dict(f0=1 / (TWO_PI * x), q=x / (c2 * (r1 + r2)), gain=1.0, order=2, kind="lp")

    def design(P, f0, q, g):
        c2 = P["c2"]
        c1 = 4 * q * q * c2
        r = 1 / (TWO_PI * f0 * math.sqrt(c1 * c2))
        return dict(c1=c1, r1=r, r2=r)
    return dict(
        params=[("r1", "R1", 10e3, "Ω"), ("r2", "R2", 10e3, "Ω"), ("c1", "C1 (feedback)", 20e-9, "F"),
                ("c2", "C2 (to ground)", 10e-9, "F")],
        tf=tf, info=info, design=design, design_keeps="c2", uses_q=True,
    )


def _sk_hp():
    def tf(P):
        ra, rb, c1, c2 = P["ra"], P["rb"], P["c1"], P["c2"]
        k = ra * rb * c1 * c2
        return [k, 0.0, 0.0], [k, ra * (c1 + c2), 1.0]

    def info(P):
        ra, rb, c1, c2 = P["ra"], P["rb"], P["c1"], P["c2"]
        x = math.sqrt(ra * rb * c1 * c2)
        return dict(f0=1 / (TWO_PI * x), q=x / (ra * (c1 + c2)), gain=1.0, order=2, kind="hp")

    def design(P, f0, q, g):
        c = P["c1"]
        w0 = TWO_PI * f0
        return dict(c2=c, ra=1 / (2 * q * w0 * c), rb=2 * q / (w0 * c))
    return dict(
        params=[("c1", "C1", 10e-9, "F"), ("c2", "C2", 10e-9, "F"), ("ra", "Ra (feedback)", 11.3e3, "Ω"),
                ("rb", "Rb (to ground)", 22.5e3, "Ω")],
        tf=tf, info=info, design=design, design_keeps="c1", uses_q=True,
    )


def _mfb_bp():
    def tf(P):
        r1, r2, r3, c = P["r1"], P["r2"], P["r3"], P["c"]
        return [-1 / (r1 * c), 0.0], [1.0, 2 / (r3 * c), (r1 + r2) / (r1 * r2 * r3 * c * c)]

    def info(P):
        r1, r2, r3, c = P["r1"], P["r2"], P["r3"], P["c"]
        w0 = math.sqrt((r1 + r2) / (r1 * r2 * r3)) / c
        q = w0 * r3 * c / 2
        return dict(f0=w0 / TWO_PI, q=q, gain=r3 / (2 * r1), order=2, kind="bp")

    def design(P, f0, q, g):
        c = P["c"]
        r3 = q / (math.pi * f0 * c)
        r1 = r3 / (2 * max(g, 1e-3))
        den = 4 * q * q - 2 * g
        r2 = r3 / den if den > 0 else 1e9
        return dict(r1=r1, r2=r2, r3=r3)
    return dict(
        params=[("r1", "R1", 15.9e3, "Ω"), ("r2", "R2", 1.77e3, "Ω"), ("r3", "R3", 159e3, "Ω"), ("c", "C1 = C2", 10e-9, "F")],
        tf=tf, info=info, design=design, design_keeps="c", uses_q=True, uses_g=True,
    )


FILTERS = {
    "rc_lp": _rc_lp(), "rc_hp": _rc_hp(), "rl_lp": _rl_lp(), "rl_hp": _rl_hp(),
    "rcrc_lp": _rcrc_lp(), "twin_t": _twin_t(),
    "rlc_bp": _rlc_bp(), "rlc_bs": _rlc_bs(), "lc_lp": _lc_lp(), "lc_hp": _lc_hp(),
    "act_lp1": _act_lp1(), "sk_lp": _sk_lp(), "sk_hp": _sk_hp(), "mfb_bp": _mfb_bp(),
}

GROUPS = [
    ("passive", ["rc_lp", "rc_hp", "rl_lp", "rl_hp", "rcrc_lp", "twin_t"]),
    ("resonant", ["rlc_bp", "rlc_bs", "lc_lp", "lc_hp"]),
    ("active", ["act_lp1", "sk_lp", "sk_hp", "mfb_bp"]),
]
