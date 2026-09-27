"""
bias.py - DC operating point (Q-point / "punctul static de functionare")
calculations for BJT, MOSFET, and JFET bias networks, plus load-line data
for charting. Formulas are the standard simplified textbook models used for
hand-analysis and design (not SPICE-level accuracy).
"""
import math


# ---------------------------------------------------------------------------
# BJT - voltage-divider bias (the standard, temperature-stable configuration)
#
# Simplified forced-VCE(sat) saturation model: IB is set by the external base
# network exactly as in forward-active analysis (a common textbook
# simplification - the true base current changes somewhat once beta is
# "forced" into saturation, but this is not modeled here). Given that IB,
# VCE is clamped to VCE(sat) and IC is solved so that KCL, IE = IC + IB,
# holds exactly - the previous version instead set IE_sat = IC_sat, which
# silently broke that identity.
# ---------------------------------------------------------------------------
def bjt_analyze(vcc, r1, r2, rc, re, beta, vbe=0.7):
    """Given the actual resistor network, compute the Q-point."""
    vth = vcc * r2 / (r1 + r2)
    rth = (r1 * r2) / (r1 + r2)
    ib = (vth - vbe) / (rth + (beta + 1) * re)
    if ib < 0:
        ib = 0.0

    if ib <= 1e-12:
        return {"ib": 0.0, "ic": 0.0, "ie": 0.0, "vb": vth, "ve": max(0.0, vth - vbe),
                "vc": vcc, "vce": vcc, "region": "cutoff"}

    ic = beta * ib
    ie = ic + ib
    vce = vcc - ic * rc - ie * re
    vce_sat = 0.2
    if vce < vce_sat:
        # Solve IC so that VCC - IC*RC - (IC+IB)*RE = VCE_sat, i.e. keep
        # IE = IC + IB exactly rather than approximating IE ≈ IC.
        ic_sat = (vcc - vce_sat - ib * re) / (rc + re)
        ic_sat = max(0.0, ic_sat)
        ie_sat = ic_sat + ib
        vb = vth
        ve = ie_sat * re
        vc = vcc - ic_sat * rc
        return {"ib": ib, "ic": ic_sat, "ie": ie_sat, "vb": vb, "ve": ve, "vc": vc,
                "vce": vce_sat, "region": "saturation"}

    vb, ve, vc = vth, ie * re, vcc - ic * rc
    return {"ib": ib, "ic": ic, "ie": ie, "vb": vb, "ve": ve, "vc": vc, "vce": vce, "region": "active"}


def bjt_design(vcc, ic_target, vce_target, beta, vbe=0.7):
    """Standard design recipe: Ve ~ 0.1*Vcc, stiff divider (I2 ~ 10*Ib).
    These are common textbook heuristics, not universal requirements - see
    the Learn section for the caveat shown to the user."""
    ie = ic_target * (beta + 1) / beta
    ve = 0.1 * vcc
    re = ve / ie
    rc = (vcc - vce_target - ve) / ic_target
    vth = ve + vbe
    ib = ic_target / beta
    i2 = 10 * ib
    i1 = i2 + ib
    r2 = vth / i2
    r1 = (vcc - vth) / i1
    return {"r1": r1, "r2": r2, "rc": max(rc, 0.0), "re": re, "vth": vth, "ib": ib}


def bjt_load_line(vcc, rc, re):
    i_max = vcc / (rc + re)
    return [0.0, vcc], [i_max, 0.0]


def bjt_characteristic_curves(beta, ib_q, vce_max, vce_sat=0.2, npts=200):
    """A small family of Ic-vs-Vce curves at different base currents around
    the actual operating Ib (so the Q-point sits exactly on one of them),
    using the same forced-VCE(sat) knee already used for the Q-point math
    above, rather than a separate, inconsistent curve model."""
    if ib_q <= 0 or vce_max <= 0:
        return []
    fracs = (0.25, 0.5, 1.0, 1.5, 2.0)
    vce = [vce_max * i / (npts - 1) for i in range(npts)]
    curves = []
    for f in fracs:
        ib = ib_q * f
        ic = [beta * ib * (1 - math.exp(-v / vce_sat)) for v in vce]
        curves.append({"param": ib, "is_q_curve": f == 1.0, "x": vce, "y": ic})
    return curves


# ---------------------------------------------------------------------------
# MOSFET - voltage-divider gate bias (enhancement mode)
# Internally solved using magnitudes; sign is re-applied for P-channel display.
# ---------------------------------------------------------------------------
def _solve_mosfet_id(vg_m, vth_m, rs, k):
    x = vg_m - vth_m
    if x <= 0:
        return 0.0
    a = k * rs ** 2
    b = -(2 * k * rs * x + 1)
    c = k * x ** 2
    if a == 0:
        return -c / b if b != 0 else 0.0
    disc = b ** 2 - 4 * a * c
    if disc < 0:
        return 0.0
    roots = [(-b + math.sqrt(disc)) / (2 * a), (-b - math.sqrt(disc)) / (2 * a)]
    candidates = [r for r in roots if r >= 0]
    return min(candidates) if candidates else 0.0


def mosfet_analyze(vdd, r1, r2, rd, rs, vth, k, nchannel=True):
    vdd_m, vth_m = abs(vdd), abs(vth)
    vg_m = vdd_m * r2 / (r1 + r2)
    id_m = _solve_mosfet_id(vg_m, vth_m, rs, k)
    vgs_m = vg_m - id_m * rs

    sign = 1 if nchannel else -1
    if vgs_m <= vth_m or id_m <= 1e-12:
        return {"id": 0.0, "vgs": sign * vg_m, "vds": sign * vdd_m, "vg": sign * vg_m, "region": "cutoff"}

    vds_m = vdd_m - id_m * (rd + rs)
    vov_m = vgs_m - vth_m
    region = "saturation" if vds_m >= vov_m else "triode"
    return {"id": id_m, "vgs": sign * vgs_m, "vds": sign * vds_m, "vg": sign * vg_m, "region": region}


def mosfet_design(vdd, id_target, vds_target, vth, k, nchannel=True):
    vdd_m, vth_m = abs(vdd), abs(vth)
    vov = math.sqrt(id_target / k) if k > 0 else 0.0
    vgs_m = vth_m + vov
    vs_m = 0.2 * vdd_m
    rs = vs_m / id_target if id_target > 0 else 0.0
    vg_m = vs_m + vgs_m
    rd = max(0.0, (vdd_m - vds_target - id_target * rs) / id_target) if id_target > 0 else 0.0
    r2 = 1e6
    r1 = r2 * (vdd_m - vg_m) / vg_m if vg_m > 0 else r2
    sign = 1 if nchannel else -1
    return {"r1": r1, "r2": r2, "rd": rd, "rs": rs, "vg": sign * vg_m, "vgs": sign * vgs_m}


def mosfet_load_line(vdd, rd, rs):
    r_total = rd + rs
    i_max = abs(vdd) / r_total if r_total > 0 else 0.0
    return [0.0, abs(vdd)], [i_max, 0.0]


def mosfet_characteristic_curves(k, vov_q, vds_max, npts=200):
    """Id-vs-Vds family at a few overdrive voltages (Vgs-Vth) around the
    actual operating point, using the same square-law triode/saturation
    split as compute_mosfet_state() in mosfet_sim.py: triode
    Id = k*(2*Vov*Vds - Vds^2), saturation Id = k*Vov^2."""
    if vov_q <= 0 or vds_max <= 0:
        return []
    fracs = (0.5, 0.75, 1.0, 1.25, 1.5)
    vds = [vds_max * i / (npts - 1) for i in range(npts)]
    curves = []
    for f in fracs:
        vov = vov_q * f
        id_arr = [k * (2 * vov * v - v * v) if v < vov else k * vov * vov for v in vds]
        curves.append({"param": vov, "is_q_curve": f == 1.0, "x": vds, "y": id_arr})
    return curves


# ---------------------------------------------------------------------------
# JFET - self-bias (gate at ~0V through Rg, source resistor sets Vgs)
#
# Shockley equation:  ID = IDSS * (1 - VGS/VP)^2
# Self-bias:           VGS = -ID*RS   (N-channel; magnitudes used internally)
#
# Substituting gives a quadratic in ID. Writing x = |VGS|/|VP| = ID*RS/VP_m,
# the quadratic's two roots x1, x2 always satisfy x1*x2 = 1 (this follows
# from the ratio of the constant and leading coefficients below). Only the
# root with x <= 1 lies inside the domain where the Shockley equation
# actually models the device (0 <= VGS/VP <= 1); the other root is a
# spurious mathematical continuation of the parabola for x > 1 and does
# NOT correspond to a real operating point (a real JFET is simply cut off
# there). Blindly taking max(candidates) can select that spurious root, so
# every root is validated against the physical constraints (0 <= ID <=
# IDSS and |VGS| <= |VP|) before being accepted.
# ---------------------------------------------------------------------------
def jfet_analyze(vdd, rd, rs, idss, vp, nchannel=True):
    vdd_m, vp_m = abs(vdd), abs(vp)
    a = idss * (rs / vp_m) ** 2 if vp_m > 0 else 0.0
    b = -(2 * idss * rs / vp_m + 1) if vp_m > 0 else -1.0
    c = idss
    if a == 0:
        roots = [-c / b] if b != 0 else []
    else:
        disc = b ** 2 - 4 * a * c
        if disc < 0:
            roots = []
        else:
            roots = [(-b + math.sqrt(disc)) / (2 * a), (-b - math.sqrt(disc)) / (2 * a)]

    # Reject non-physical roots: ID must lie in [0, IDSS], and the implied
    # |VGS| = ID*RS must not exceed |VP| (the model is only valid up to
    # cutoff). Among the survivors (generically at most one), take the
    # smallest ID - the branch actually reachable by the self-bias line
    # starting from the origin.
    valid = []
    for r in roots:
        if r < -1e-9 or r > idss + 1e-9:
            continue
        r = max(0.0, min(r, idss))
        vgs_candidate = r * rs
        if rs > 0 and vgs_candidate > vp_m + 1e-9:
            continue
        valid.append(r)
    id_m = min(valid) if valid else 0.0

    vgs_m = id_m * rs
    vds_m = vdd_m - id_m * (rd + rs)
    sign = 1 if nchannel else -1

    if id_m <= 1e-12 or vgs_m >= vp_m:
        # Cutoff: the gate-source reverse bias has pinched the channel off
        # entirely (|VGS| has reached |VP|), so ID ~ 0. This is distinct
        # from VDS-induced pinch-off at the drain end of the channel, which
        # is what puts a *conducting* JFET into saturation (see Learn).
        return {"id": 0.0, "vgs": -sign * vp_m, "vds": sign * vdd_m, "region": "cutoff"}

    vov_m = vp_m - vgs_m
    # Saturation-region validity check per the simplified Shockley model:
    # VDS >= VGS - VP  (equivalently, in magnitudes, VDS >= VP - |VGS|).
    region = "saturation" if vds_m >= vov_m else "triode"
    return {"id": id_m, "vgs": -sign * vgs_m, "vds": sign * vds_m, "region": region}


def jfet_design(vdd, id_target, vds_target, idss, vp):
    vdd_m, vp_m = abs(vdd), abs(vp)
    ratio = math.sqrt(max(0.0, min(1.0, id_target / idss))) if idss > 0 else 0.0
    vgs_m = vp_m * (1 - ratio)
    rs = vgs_m / id_target if id_target > 0 else 0.0
    rd = max(0.0, (vdd_m - vds_target - id_target * rs) / id_target) if id_target > 0 else 0.0
    return {"rs": rs, "rd": rd, "vgs": vgs_m}


def jfet_load_line(vdd, rd, rs):
    r_total = rd + rs
    i_max = abs(vdd) / r_total if r_total > 0 else 0.0
    return [0.0, abs(vdd)], [i_max, 0.0]


def jfet_characteristic_curves(idss, vp_m, ratio_q, vds_max, npts=200):
    """Id-vs-Vds family at a few gate-conduction ratios (ratio = 1 -
    Vgs/Vp, the same quantity that gets squared in the Shockley equation)
    around the actual operating point: saturation Id = Idss*ratio^2,
    triode Id = Idss*(2*ratio*(Vds/|Vp|) - (Vds/|Vp|)^2), the JFET analog
    of the MOSFET square-law split above."""
    if ratio_q <= 0 or vds_max <= 0 or vp_m <= 0:
        return []
    fracs = (0.5, 0.75, 1.0, 1.25, 1.5)
    vds = [vds_max * i / (npts - 1) for i in range(npts)]
    curves = []
    for f in fracs:
        ratio = min(1.0, ratio_q * f)
        vgs_m = vp_m * (1 - ratio)
        knee = ratio * vp_m
        id_arr = []
        for v in vds:
            u = v / vp_m
            if v < knee:
                id_arr.append(idss * (2 * ratio * u - u * u))
            else:
                id_arr.append(idss * ratio * ratio)
        curves.append({"param": vgs_m, "is_q_curve": f == 1.0, "x": vds, "y": id_arr})
    return curves
