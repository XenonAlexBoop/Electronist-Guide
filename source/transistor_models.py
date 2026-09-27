"""
transistor_models.py - Compact, physically-based DC models used by the
Junction Visualizer and the transistor circuits page.

All three models are written for the N-type device (NPN / N-channel); the
P-type device is obtained by inverting every terminal voltage and every
current (the carriers become holes instead of electrons).

  BJT    - Ebers-Moll transport model + emitter-base Zener breakdown +
           collector-base avalanche multiplication.
  MOSFET - square law (triode / saturation, channel-length modulation),
           exponential sub-threshold conduction, symmetric channel for
           negative Vds, intrinsic body diode (with series resistance),
           drain avalanche, gate-oxide stress flag.
  JFET   - Shockley square law with symmetric channel, gate-source and
           gate-drain diodes (forward gate conduction), gate-drain breakdown,
           plus the depletion-width profile along the channel.

Every function returns plain numbers (SI units) plus a `region` key and the
individual current components, so the animation can draw one particle
stream per physical current path.
"""
import math

VT = 0.025852       # thermal voltage at 300 K
_EXP_CAP = 0.95     # junction voltage above which the exponential is linearised


def _dexp(v):
    """exp(v/VT) - 1, linearised above _EXP_CAP to stay finite."""
    if v <= _EXP_CAP:
        return math.exp(v / VT) - 1.0
    e = math.exp(_EXP_CAP / VT)
    return e * (1.0 + (v - _EXP_CAP) / VT) - 1.0


def diode_with_rs(v, i_s, rs):
    """Current of a diode with series resistance for applied voltage v (>=0 forward)."""
    if v <= 0:
        return i_s * (math.exp(max(v, -40 * VT) / VT) - 1.0)
    lo, hi = 0.0, v / rs if rs > 0 else 1e3
    for _ in range(80):
        mid = (lo + hi) / 2
        vd = v - mid * rs
        f = i_s * _dexp(vd) - mid
        if f > 0:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def depletion_factor(v_junction, vbi=0.75):
    """Relative depletion width (1.0 at zero bias). Shrinks with forward bias,
    grows like sqrt(Vbi - V) with reverse bias."""
    return math.sqrt(max(0.04, (vbi - v_junction) / vbi))


# ---------------------------------------------------------------------------
# BJT
# ---------------------------------------------------------------------------
BJT_DEFAULTS = {"beta_f": 150.0, "beta_r": 2.0, "i_s": 1e-15, "bv_ebo": 7.0, "bv_cbo": 50.0,
                "r_zener": 20.0}


def bjt_state(vbe, vbc, npn=True, **params):
    """Terminal voltages in real polarity (for PNP pass the real, usually
    negative, Vbe/Vbc). Returns currents INTO collector (ic) and base (ib)
    and OUT of the emitter (ie), all in real polarity."""
    p = dict(BJT_DEFAULTS, **params)
    sgn = 1.0 if npn else -1.0
    ve, vc = sgn * vbe, sgn * vbc     # N-equivalent junction voltages
    i_s, bf, br = p["i_s"], p["beta_f"], p["beta_r"]
    i_f = i_s * _dexp(ve)
    i_r = i_s * _dexp(vc)
    transport = i_f - i_r               # carriers crossing the base (E->C if > 0)
    ib_f = i_f / bf                     # base current feeding the E-B junction
    ib_r = i_r / br                     # base current feeding the C-B junction
    ic = transport - ib_r
    ib = ib_f + ib_r
    # emitter-base reverse (Zener) breakdown
    eb_bd = max(0.0, (-ve - p["bv_ebo"]) / p["r_zener"])
    ib -= eb_bd
    # collector-base avalanche multiplication and hard breakdown
    vcb = -vc
    aval = 0.0
    if vcb > 0:
        ratio = min(vcb / p["bv_cbo"], 0.995)
        m = 1.0 / (1.0 - ratio ** 4)
        aval = (m - 1.0) * max(transport, 0.0) + (m - 1.0) * 1e-12
        aval += max(0.0, (vcb - p["bv_cbo"]) / p["r_zener"])
    ic += aval
    ib -= aval
    ie = ic + ib
    # region
    e_on, c_on = ve > 0.5, vc > 0.5
    if eb_bd > 1e-6:
        region = "eb_breakdown"
    elif aval > max(1e-4, 0.1 * abs(transport)):
        region = "avalanche"
    elif e_on and c_on:
        region = "saturation"
    elif e_on:
        region = "active"
    elif c_on:
        region = "reverse"
    elif ve > 0.35 or vc > 0.35:
        region = "weak"
    else:
        region = "cutoff"
    return {
        "ic": sgn * ic, "ib": sgn * ib, "ie": sgn * ie,
        "transport": transport, "ib_f": ib_f, "ib_r": ib_r, "eb_bd": eb_bd, "aval": aval,
        "ve": ve, "vc": vc, "vce": sgn * (ve - vc), "region": region,
        "dep_eb": depletion_factor(ve), "dep_cb": depletion_factor(vc, 0.7),
        "beta_eff": (ic / ib) if abs(ib) > 1e-15 else float("nan"),
    }


# ---------------------------------------------------------------------------
# MOSFET
# ---------------------------------------------------------------------------
MOSFET_DEFAULTS = {"vth": 2.0, "k": 0.1, "lam": 0.02, "n_sub": 1.5, "i_s_body": 1e-12,
                   "rs_body": 0.5, "bv_dss": 40.0, "r_aval": 5.0, "vgs_max": 20.0}


def _channel(vgs, vds, p):
    """Channel current for vds >= 0 (N-equivalent), plus region name."""
    vth, k, lam = p["vth"], p["k"], p["lam"]
    vov = vgs - vth
    nvt = p["n_sub"] * VT
    if vov <= 0:
        i0 = k * (2 * nvt) ** 2
        i = i0 * math.exp(max(vov, -60 * nvt) / nvt) * (1 - math.exp(-vds / VT))
        return i, ("subthreshold" if vov > -0.3 else "cutoff")
    if vds < vov:
        return k * (2 * vov * vds - vds * vds) * (1 + lam * vds), "triode"
    return k * vov * vov * (1 + lam * vds), "saturation"


def mosfet_state(vgs, vds, nch=True, **params):
    p = dict(MOSFET_DEFAULTS, **params)
    sgn = 1.0 if nch else -1.0
    vg, vd = sgn * vgs, sgn * vds
    pn = dict(p, vth=sgn * p["vth"])
    body = 0.0
    if vd >= 0:
        ich, region = _channel(vg, vd, pn)
    else:
        i_rev, region = _channel(vg - vd, -vd, pn)     # drain acts as source
        ich = -i_rev
        if region in ("triode", "saturation"):
            region = "reverse_channel"
        body = diode_with_rs(-vd, p["i_s_body"], p["rs_body"])
        if body > max(1e-4, 0.2 * abs(ich)):
            region = "body_diode"
    aval = max(0.0, (vd - p["bv_dss"]) / p["r_aval"])
    if aval > 1e-6:
        region = "avalanche"
    i_d = ich - body + aval
    vgd = vg - vd
    q_s = max(0.0, vg - pn["vth"])
    q_d = max(0.0, vgd - pn["vth"])
    return {
        "id": sgn * i_d, "ich": ich, "body": body, "aval": aval, "region": region,
        "vg": vg, "vd": vd, "q_s": q_s, "q_d": q_d, "vov": vg - pn["vth"],
        "oxide_stress": abs(vgs) > p["vgs_max"],
        "dep_drain": depletion_factor(-vd, 0.7),
    }


# ---------------------------------------------------------------------------
# JFET
# ---------------------------------------------------------------------------
JFET_DEFAULTS = {"idss": 0.01, "vp": -4.0, "lam": 0.01, "i_s_gate": 1e-12, "rs_gate": 50.0,
                 "bv_gd": 35.0, "r_bd": 50.0, "vbi": 0.7}


def _jfet_channel(vg, v, p):
    vp, idss, lam = p["vp"], p["idss"], p["lam"]
    if vg <= vp:
        return 0.0, "cutoff"
    vsat = vg - vp
    if v < vsat:
        i = idss * (2 * (1 - vg / vp) * (v / -vp) - (v / vp) ** 2)
        return i * (1 + lam * v), "ohmic"
    return idss * (1 - vg / vp) ** 2 * (1 + lam * v), "saturation"


def jfet_state(vgs, vds, nch=True, **params):
    p = dict(JFET_DEFAULTS, **params)
    sgn = 1.0 if nch else -1.0
    vg, vd = sgn * vgs, sgn * vds
    pn = dict(p, vp=-abs(p["vp"]))
    if vd >= 0:
        ich, region = _jfet_channel(vg, vd, pn)
    else:
        i_rev, region = _jfet_channel(vg - vd, -vd, pn)
        ich = -i_rev
        if region != "cutoff":
            region = "reversed"
    ig_s = diode_with_rs(vg, p["i_s_gate"], p["rs_gate"])
    ig_d = diode_with_rs(vg - vd, p["i_s_gate"], p["rs_gate"])
    bd = max(0.0, (vd - vg - p["bv_gd"]) / p["r_bd"])
    i_d = ich - ig_d + bd
    i_g = ig_s + ig_d - bd
    if bd > 1e-6:
        region = "breakdown"
    elif max(ig_s, ig_d) > 1e-5:
        region = "gate_forward"
    return {
        "id": sgn * i_d, "ig": sgn * i_g, "is": sgn * (i_d + i_g), "ich": ich, "ig_s": ig_s,
        "ig_d": ig_d, "bd": bd, "region": region, "vg": vg, "vd": vd,
    }


def jfet_depletion_profile(vg, vd, vp, vbi=0.7, n=40):
    """Fraction (0..1) of the channel half-height taken by each gate's
    depletion region at n points from source (x=0) to drain (x=1).
    1.0 = the two depletion regions meet (pinched)."""
    vp = -abs(vp)
    out = []
    vsat = max(0.0, vg - vp)
    v_eff = max(-vsat, min(vd, vsat)) if vd >= 0 else vd
    for i in range(n + 1):
        x = i / n
        # gradual-channel shape: the channel potential rises slowly near the
        # source and steeply near the drain, so pinch-off happens AT the drain
        # end (it only reaches the drain voltage beyond the pinch point).
        if v_eff >= 0:
            vch = v_eff * (1 - math.sqrt(max(0.0, 1 - x)))
            if vd > vsat and x > 0.97:
                vch = vsat + (vd - vsat) * (x - 0.97) / 0.03
        else:
            # reversed VDS: the drain acts as the source, steep part at the source end
            vch = v_eff + abs(v_eff) * (1 - math.sqrt(max(0.0, x)))
        rev = vbi - vg + vch    # reverse voltage across the gate junction here
        full = vbi - vp
        out.append(min(1.0, math.sqrt(max(0.0, rev) / full)))
    return out
