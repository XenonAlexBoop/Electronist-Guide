"""
transistor_circuits.py - "Basic circuits" sub-tab of the Transistors tab.

Essential circuits for each transistor family, every value editable and
the result updated live:

  BJT     switch · common-emitter amplifier (divider bias) · emitter
          follower · constant-current source
  MOSFET  low-side / high-side switch · common-source amplifier · source
          follower
  JFET    self-biased amplifier · constant-current source · voltage-
          controlled resistor / switch · source follower

The maths is written once for the N-type device, using magnitudes. The
P-type (PNP / P-channel) version is the mirror image: the schematic is
flipped vertically so the emitter/source sits on the positive rail, the
rails are relabelled, the current arrows reverse, and every node voltage
is shown as its real value (Vcc minus the N-model value).
"""
import math
import numpy as np
import tkinter as tk
from tkinter import ttk

import symbols as sym
from charts import MplChartFrame, PLOT_BG
from widgets import parse_value, format_value, ScrollableFrame, FONT_BODY, FONT_H2, FONT_MONO, debounce, cap_width
from i18n import t, get_language

VT = 0.025852


def L(en, ro):
    return ro if get_language() == "ro" else en


def fv(x, u):
    if x is None or (isinstance(x, float) and not math.isfinite(x)):
        return "—"
    if abs(x) < 1e-15:
        return f"0 {u}"
    return format_value(float(f"{x:.3g}"), u)


def par(a, b):
    if a <= 0:
        return b
    if b <= 0:
        return a
    return a * b / (a + b)


class P:
    """Editable parameter. kind: 'num' or 'bool'."""

    def __init__(self, key, sym_, en, ro, unit, default, kind="num"):
        self.key, self.sym, self.name, self.unit, self.default, self.kind = key, sym_, (en, ro), unit, default, kind


# ===========================================================================
# Solvers (N-type convention, all values positive magnitudes)
# ===========================================================================
def bjt_switch(p):
    ib = max(0.0, (p["vin"] - p["vbe"]) / p["rb"])
    ic_lin = p["beta"] * ib
    ic_sat = max(0.0, (p["vcc"] - p["vsat"]) / p["rc"])
    ic = min(ic_lin, ic_sat)
    vce = p["vcc"] - ic * p["rc"]
    state = "off" if ib <= 0 else ("sat" if ic_lin >= ic_sat else "active")
    rb_max = (p["vin"] - p["vbe"]) / (ic_sat / 10) if ic_sat > 0 and p["vin"] > p["vbe"] else float("nan")
    return {"ib": ib, "ic": ic, "ie": ic + ib, "vce": vce, "vc": vce, "vb": p["vbe"] if ib > 0 else p["vin"],
            "ve": 0.0, "state": state, "ic_sat": ic_sat, "rb_max": rb_max,
            "p_dev": ic * vce + ib * p["vbe"], "p_load": ic * ic * p["rc"]}


def _divider_bias(p, rc, re):
    vth = p["vcc"] * p["r2"] / (p["r1"] + p["r2"])
    rth = par(p["r1"], p["r2"])
    beta = p["beta"]
    ib = max(0.0, (vth - p["vbe"]) / (rth + (beta + 1) * re))
    ic = beta * ib
    ie = ic + ib
    vce = p["vcc"] - ic * rc - ie * re
    sat = False
    if vce < p["vsat"] and ib > 0:
        sat = True
        vce = p["vsat"]
        ic = (p["vcc"] - p["vsat"]) / (rc + re) if rc + re > 0 else ic
        ie = ic
    ve = ie * re
    return {"vth": vth, "rth": rth, "ib": ib, "ic": ic, "ie": ie, "vce": vce, "ve": ve,
            "vb": ve + p["vbe"] if ib > 0 else vth, "vc": ve + vce, "sat": sat}


def bjt_ce(p):
    r = _divider_bias(p, p["rc"], p["re"])
    re_small = VT / r["ie"] if r["ie"] > 0 else float("inf")
    rload = par(p["rc"], p["rl"])
    r_emit = 0.0 if p["bypass"] else p["re"]
    av = -rload / (re_small + r_emit) if math.isfinite(re_small) else 0.0
    zin = par(r["rth"], (p["beta"] + 1) * (re_small + r_emit)) if math.isfinite(re_small) else r["rth"]
    r.update(av=av, re_small=re_small, zin=zin, zout=p["rc"], gm=r["ic"] / VT,
             swing_up=p["vcc"] - r["vc"], swing_down=r["vc"] - r["ve"] - p["vsat"],
             state="sat" if r["sat"] else ("off" if r["ib"] <= 0 else "active"))
    return r


def bjt_ef(p):
    r = _divider_bias(p, 0.0, p["re"])
    re_small = VT / r["ie"] if r["ie"] > 0 else float("inf")
    rl = par(p["re"], p["rl"])
    av = rl / (re_small + rl) if math.isfinite(re_small) else 0.0
    zin = par(r["rth"], (p["beta"] + 1) * (re_small + rl)) if math.isfinite(re_small) else r["rth"]
    zout = par(p["re"], re_small + r["rth"] / (p["beta"] + 1)) if math.isfinite(re_small) else p["re"]
    r.update(av=av, zin=zin, zout=zout, re_small=re_small, vc=p["vcc"],
             state="sat" if r["sat"] else ("off" if r["ib"] <= 0 else "active"))
    return r


def bjt_ccs(p, rl=None):
    rl = p["rl"] if rl is None else rl
    vb = min(p["vz"], p["vcc"])
    ve = max(0.0, vb - p["vbe"])
    ie = ve / p["re"]
    ic_nom = ie * p["beta"] / (p["beta"] + 1)
    vc = p["vcc"] - ic_nom * rl
    sat = vc - ve < p["vsat"]
    ic = ic_nom
    if sat:
        ic = max(0.0, (p["vcc"] - p["vsat"] - ve) / (rl + 1e-12))
        ic = min(ic, ic_nom)
        vc = p["vcc"] - ic * rl
    iz = (p["vcc"] - vb) / p["rb"] - ic / p["beta"]
    rl_max = (p["vcc"] - p["vsat"] - ve) / ic_nom if ic_nom > 0 else float("inf")
    return {"vb": vb, "ve": ve, "vc": vc, "ic": ic, "ic_nom": ic_nom, "ie": ic * (p["beta"] + 1) / p["beta"],
            "ib": ic / p["beta"], "vce": vc - ve, "sat": sat, "rl_max": rl_max, "iz": iz,
            "state": "sat" if sat else "active", "p_dev": ic * (vc - ve)}


def _mos_id(vgs, vds, vth, k, lam=0.0):
    vov = vgs - vth
    if vov <= 0 or vds <= 0:
        return 0.0
    if vds < vov:
        return k * (2 * vov * vds - vds * vds) * (1 + lam * vds)
    return k * vov * vov * (1 + lam * vds)


def _solve_load(fn_id, vdd, rl, i_max):
    """Solve I = fn_id(vds) with vds = vdd - I*rl by bisection."""
    lo, hi = 0.0, i_max
    for _ in range(100):
        mid = (lo + hi) / 2
        if fn_id(vdd - mid * rl) > mid:
            lo = mid
        else:
            hi = mid
    return (lo + hi) / 2


def mos_switch(p, vgs=None):
    vgs = p["vgs"] if vgs is None else vgs
    i_d = _solve_load(lambda vds: _mos_id(vgs, vds, p["vth"], p["k"]), p["vdd"], p["rl"], p["vdd"] / p["rl"])
    vds = p["vdd"] - i_d * p["rl"]
    vov = vgs - p["vth"]
    ron = 1 / (2 * p["k"] * vov) if vov > 0 else float("inf")
    state = "off" if vov <= 0 else ("triode" if vds < vov else "sat")
    return {"id": i_d, "vds": vds, "vd": vds, "vg": vgs, "vs": 0.0, "ron": ron, "state": state,
            "p_dev": i_d * vds, "p_load": i_d * i_d * p["rl"]}


def _mos_bias(p, rd, rs):
    vg = p["vdd"] * p["r2"] / (p["r1"] + p["r2"])
    k, vth = p["k"], p["vth"]
    if vg <= vth:
        x = 0.0
    elif rs > 0:
        x = (-1 + math.sqrt(1 + 4 * k * rs * (vg - vth))) / (2 * k * rs)
    else:
        x = vg - vth
    i_d = k * x * x
    vs = i_d * rs
    vd = p["vdd"] - i_d * rd
    triode = (vd - vs) < x
    if triode and i_d > 0:  # re-solve in triode with bisection on id
        def f(i):
            vgs = vg - i * rs
            return _mos_id(vgs, p["vdd"] - i * (rd + rs), vth, k)
        i_d = _solve_load(lambda v: f((p["vdd"] - v) / (rd + rs) if rd + rs else 0), p["vdd"], rd + rs,
                          p["vdd"] / (rd + rs))
        vs = i_d * rs
        vd = p["vdd"] - i_d * rd
        x = max(0.0, vg - vs - vth)
    return {"vg": vg, "vgs": vg - vs, "vov": x, "id": i_d, "vs": vs, "vd": vd, "vds": vd - vs,
            "gm": 2 * k * x, "triode": triode}


def mos_cs(p):
    r = _mos_bias(p, p["rd"], p["rs"])
    rload = par(p["rd"], p["rl"])
    rsu = 0.0 if p["bypass"] else p["rs"]
    av = -r["gm"] * rload / (1 + r["gm"] * rsu)
    r.update(av=av, zin=par(p["r1"], p["r2"]), zout=p["rd"],
             state="off" if r["id"] <= 0 else ("triode" if r["triode"] else "sat"))
    return r


def mos_sf(p):
    r = _mos_bias(p, 0.0, p["rs"])
    rl = par(p["rs"], p["rl"])
    av = r["gm"] * rl / (1 + r["gm"] * rl)
    zout = par(p["rs"], 1 / r["gm"]) if r["gm"] > 0 else p["rs"]
    r.update(av=av, zin=par(p["r1"], p["r2"]), zout=zout, vd=p["vdd"],
             state="off" if r["id"] <= 0 else "sat")
    return r


def _jfet_ch(vgs, vds, idss, a):
    vp = -a
    if vgs <= vp or vds <= 0:
        return 0.0
    vsat = vgs - vp
    if vds < vsat:
        return idss * (2 * (1 - vgs / vp) * (vds / a) - (vds / vp) ** 2)
    return idss * (1 - vgs / vp) ** 2


def _jfet_self_bias(idss, a, rs):
    if rs <= 0:
        return idss
    k = idss * rs / a
    y = ((2 * k + 1) - math.sqrt((2 * k + 1) ** 2 - 4 * k * k)) / (2 * k)
    return a * y / rs


def jfet_amp(p):
    a = abs(p["vp"])
    i_d = _jfet_self_bias(p["idss"], a, p["rs"])
    vgs = -i_d * p["rs"]
    vd = p["vdd"] - i_d * p["rd"]
    vs = i_d * p["rs"]
    vds = vd - vs
    ohmic = vds < a - abs(vgs)
    if ohmic:
        i_d = _solve_load(lambda v: _jfet_ch(-min(a, (p["vdd"] - v) / (p["rd"] + p["rs"]) * p["rs"]), v, p["idss"], a),
                          p["vdd"], p["rd"] + p["rs"], p["vdd"] / (p["rd"] + p["rs"]))
        vgs = -i_d * p["rs"]
        vd = p["vdd"] - i_d * p["rd"]
        vs = i_d * p["rs"]
        vds = vd - vs
    gm = 2 * p["idss"] / a * (1 - abs(vgs) / a)
    rload = par(p["rd"], p["rl"])
    rsu = 0.0 if p["bypass"] else p["rs"]
    av = -gm * rload / (1 + gm * rsu)
    return {"id": i_d, "vgs": vgs, "vd": vd, "vs": vs, "vds": vds, "vg": 0.0, "gm": gm, "av": av,
            "zin": p["rg"], "zout": p["rd"], "state": "triode" if ohmic else "sat"}


def jfet_ccs(p, rl=None):
    rl = p["rl"] if rl is None else rl
    a = abs(p["vp"])
    rs = p["rs"]

    def fn(vds_guess_i):
        return vds_guess_i
    # solve I = ch(vgs=-I*rs, vds=vdd - I*(rl+rs))
    lo, hi = 0.0, p["idss"] * 1.01
    for _ in range(100):
        mid = (lo + hi) / 2
        ch = _jfet_ch(-mid * rs, p["vdd"] - mid * (rl + rs), p["idss"], a)
        if ch > mid:
            lo = mid
        else:
            hi = mid
    i_d = (lo + hi) / 2
    i_nom = _jfet_self_bias(p["idss"], a, rs)
    vgs = -i_d * rs
    vs = i_d * rs
    vd = p["vdd"] - i_d * rl
    vds = vd - vs
    rl_max = (p["vdd"] - i_nom * rs - (a - i_nom * rs)) / i_nom if i_nom > 0 else float("inf")
    return {"id": i_d, "i_nom": i_nom, "vgs": vgs, "vs": vs, "vd": vd, "vds": vds, "vg": 0.0,
            "rl_max": rl_max, "state": "sat" if abs(i_d - i_nom) < 0.01 * i_nom else "triode"}


def jfet_vcr(p, vgs=None):
    a = abs(p["vp"])
    vgs = -abs(p["vgs_ctl"]) if vgs is None else vgs
    i_d = _solve_load(lambda v: _jfet_ch(vgs, v, p["idss"], a), p["vdd"], p["rl"], p["vdd"] / p["rl"])
    vds = p["vdd"] - i_d * p["rl"]
    rds = vds / i_d if i_d > 1e-12 else float("inf")
    rds_small = a * a / (2 * p["idss"] * (vgs + a)) if vgs > -a else float("inf")
    return {"id": i_d, "vds": vds, "vd": vds, "vg": vgs, "vs": 0.0, "rds": rds, "rds0": rds_small,
            "state": "off" if vgs <= -a else ("triode" if vds < vgs + a else "sat")}


def jfet_sf(p):
    a = abs(p["vp"])
    i_d = _jfet_self_bias(p["idss"], a, p["rs"])
    vgs = -i_d * p["rs"]
    vs = i_d * p["rs"]
    gm = 2 * p["idss"] / a * (1 - abs(vgs) / a)
    rl = par(p["rs"], p["rl"])
    av = gm * rl / (1 + gm * rl)
    return {"id": i_d, "vgs": vgs, "vs": vs, "vd": p["vdd"], "vds": p["vdd"] - vs, "vg": 0.0, "gm": gm, "av": av,
            "zin": p["rg"], "zout": par(p["rs"], 1 / gm) if gm > 0 else p["rs"], "state": "sat"}


# ===========================================================================
# Circuit catalogue
# ===========================================================================
_BJT_COMMON = [P("beta", "β", "Current gain", "Câștig în curent", "", "150"),
               P("vbe", "VBE", "Base-emitter drop", "Căderea bază-emitor", "V", "0.7"),
               P("vsat", "VCE(sat)", "Saturation voltage", "Tensiunea de saturație", "V", "0.2")]

CIRCUITS = {
    "bjt": [
        {"key": "switch", "title": ("Transistor switch (load on the collector)", "Tranzistorul ca și comutator (sarcina în colector)"),
         "solve": bjt_switch, "draw": "switch", "plot": "switch",
         "params": [P("vcc", "VCC", "Supply", "Alimentare", "V", "12"),
                    P("vin", "Vin", "Drive voltage (logic high)", "Tensiune de comandă (nivel 1)", "V", "5"),
                    P("rb", "RB", "Base resistor", "Rezistor de bază", "Ω", "4.7k"),
                    P("rc", "RC", "Load (collector resistor)", "Sarcina (rezistor de colector)", "Ω", "470")] + _BJT_COMMON},
        {"key": "ce", "title": ("Common-emitter amplifier (voltage-divider bias)", "Amplificator cu emitor comun (polarizare cu divizor)"),
         "solve": bjt_ce, "draw": "amp", "plot": "amp",
         "params": [P("vcc", "VCC", "Supply", "Alimentare", "V", "12"),
                    P("r1", "R1", "Divider, top", "Divizor, sus", "Ω", "47k"),
                    P("r2", "R2", "Divider, bottom", "Divizor, jos", "Ω", "10k"),
                    P("rc", "RC", "Collector resistor", "Rezistor de colector", "Ω", "2.2k"),
                    P("re", "RE", "Emitter resistor", "Rezistor de emitor", "Ω", "560"),
                    P("rl", "RL", "Load (0 = none)", "Sarcină (0 = fără)", "Ω", "10k"),
                    P("bypass", "CE", "Emitter bypass capacitor", "Condensator de decuplare pe emitor", "", True, "bool"),
                    P("vin_ac", "vin", "Input amplitude (peak)", "Amplitudine intrare (vârf)", "V", "10m"),
                    P("f", "f", "Signal frequency", "Frecvența semnalului", "Hz", "1k")] + _BJT_COMMON},
        {"key": "ef", "title": ("Emitter follower (common collector / buffer)", "Repetor pe emitor (colector comun / buffer)"),
         "solve": bjt_ef, "draw": "follower", "plot": "amp",
         "params": [P("vcc", "VCC", "Supply", "Alimentare", "V", "12"),
                    P("r1", "R1", "Divider, top", "Divizor, sus", "Ω", "10k"),
                    P("r2", "R2", "Divider, bottom", "Divizor, jos", "Ω", "10k"),
                    P("re", "RE", "Emitter resistor", "Rezistor de emitor", "Ω", "1k"),
                    P("rl", "RL", "Load (0 = none)", "Sarcină (0 = fără)", "Ω", "1k"),
                    P("vin_ac", "vin", "Input amplitude (peak)", "Amplitudine intrare (vârf)", "V", "1"),
                    P("f", "f", "Signal frequency", "Frecvența semnalului", "Hz", "1k")] + _BJT_COMMON},
        {"key": "ccs", "title": ("Constant-current source (Zener reference)", "Sursă de curent constant (referință Zener)"),
         "solve": bjt_ccs, "draw": "ccs", "plot": "ccs",
         "params": [P("vcc", "VCC", "Supply", "Alimentare", "V", "12"),
                    P("rb", "RB", "Zener bias resistor", "Rezistor de polarizare Zener", "Ω", "1k"),
                    P("vz", "VZ", "Zener voltage", "Tensiunea Zener", "V", "3.3"),
                    P("re", "RE", "Emitter (current-set) resistor", "Rezistor de emitor (setează curentul)", "Ω", "130"),
                    P("rl", "RL", "Load", "Sarcina", "Ω", "470")] + _BJT_COMMON},
    ],
    "mosfet": [
        {"key": "switch", "title": ("MOSFET switch (load on the drain)", "MOSFET ca și comutator (sarcina în drenă)"),
         "solve": mos_switch, "draw": "switch", "plot": "switch",
         "params": [P("vdd", "VDD", "Supply", "Alimentare", "V", "12"),
                    P("vgs", "VGS", "Gate drive", "Comanda pe grilă", "V", "10"),
                    P("rl", "RL", "Load", "Sarcina", "Ω", "10"),
                    P("vth", "|Vth|", "Threshold voltage", "Tensiunea de prag", "V", "2"),
                    P("k", "K", "Transconductance parameter", "Parametrul de transconductanță", "A/V²", "0.5")]},
        {"key": "cs", "title": ("Common-source amplifier (divider bias)", "Amplificator cu sursă comună (polarizare cu divizor)"),
         "solve": mos_cs, "draw": "amp", "plot": "amp",
         "params": [P("vdd", "VDD", "Supply", "Alimentare", "V", "15"),
                    P("r1", "R1", "Divider, top", "Divizor, sus", "Ω", "1M"),
                    P("r2", "R2", "Divider, bottom", "Divizor, jos", "Ω", "470k"),
                    P("rd", "RD", "Drain resistor", "Rezistor de drenă", "Ω", "2.2k"),
                    P("rs", "RS", "Source resistor", "Rezistor de sursă", "Ω", "1k"),
                    P("rl", "RL", "Load (0 = none)", "Sarcină (0 = fără)", "Ω", "10k"),
                    P("bypass", "CS", "Source bypass capacitor", "Condensator de decuplare pe sursă", "", True, "bool"),
                    P("vth", "|Vth|", "Threshold voltage", "Tensiunea de prag", "V", "2.1"),
                    P("k", "K", "Transconductance parameter", "Parametrul de transconductanță", "A/V²", "20m"),
                    P("vin_ac", "vin", "Input amplitude (peak)", "Amplitudine intrare (vârf)", "V", "50m"),
                    P("f", "f", "Signal frequency", "Frecvența semnalului", "Hz", "1k")]},
        {"key": "sf", "title": ("Source follower (common drain / buffer)", "Repetor pe sursă (drenă comună / buffer)"),
         "solve": mos_sf, "draw": "follower", "plot": "amp",
         "params": [P("vdd", "VDD", "Supply", "Alimentare", "V", "12"),
                    P("r1", "R1", "Divider, top", "Divizor, sus", "Ω", "1M"),
                    P("r2", "R2", "Divider, bottom", "Divizor, jos", "Ω", "1M"),
                    P("rs", "RS", "Source resistor", "Rezistor de sursă", "Ω", "1k"),
                    P("rl", "RL", "Load (0 = none)", "Sarcină (0 = fără)", "Ω", "10k"),
                    P("vth", "|Vth|", "Threshold voltage", "Tensiunea de prag", "V", "2.1"),
                    P("k", "K", "Transconductance parameter", "Parametrul de transconductanță", "A/V²", "20m"),
                    P("vin_ac", "vin", "Input amplitude (peak)", "Amplitudine intrare (vârf)", "V", "1"),
                    P("f", "f", "Signal frequency", "Frecvența semnalului", "Hz", "1k")]},
    ],
    "jfet": [
        {"key": "amp", "title": ("Self-biased common-source amplifier", "Amplificator cu sursă comună, autopolarizat"),
         "solve": jfet_amp, "draw": "jamp", "plot": "amp",
         "params": [P("vdd", "VDD", "Supply", "Alimentare", "V", "15"),
                    P("rd", "RD", "Drain resistor", "Rezistor de drenă", "Ω", "2.2k"),
                    P("rs", "RS", "Source (self-bias) resistor", "Rezistor de sursă (autopolarizare)", "Ω", "470"),
                    P("rg", "RG", "Gate resistor", "Rezistor de grilă", "Ω", "1M"),
                    P("rl", "RL", "Load (0 = none)", "Sarcină (0 = fără)", "Ω", "10k"),
                    P("bypass", "CS", "Source bypass capacitor", "Condensator de decuplare pe sursă", "", True, "bool"),
                    P("idss", "IDSS", "Saturation current at VGS = 0", "Curentul de saturație la VGS = 0", "A", "10m"),
                    P("vp", "|VP|", "Pinch-off voltage", "Tensiunea de ștrangulare", "V", "4"),
                    P("vin_ac", "vin", "Input amplitude (peak)", "Amplitudine intrare (vârf)", "V", "50m"),
                    P("f", "f", "Signal frequency", "Frecvența semnalului", "Hz", "1k")]},
        {"key": "ccs", "title": ("Constant-current source (current regulator)", "Sursă de curent constant (regulator de curent)"),
         "solve": jfet_ccs, "draw": "jccs", "plot": "ccs",
         "params": [P("vdd", "VDD", "Supply", "Alimentare", "V", "15"),
                    P("rs", "RS", "Current-set resistor (0 = IDSS)", "Rezistor de setare (0 = IDSS)", "Ω", "220"),
                    P("rl", "RL", "Load", "Sarcina", "Ω", "1k"),
                    P("idss", "IDSS", "Saturation current at VGS = 0", "Curentul de saturație la VGS = 0", "A", "10m"),
                    P("vp", "|VP|", "Pinch-off voltage", "Tensiunea de ștrangulare", "V", "4")]},
        {"key": "vcr", "title": ("Switch / voltage-controlled resistor", "Comutator / rezistor controlat în tensiune"),
         "solve": jfet_vcr, "draw": "switch", "plot": "switch",
         "params": [P("vdd", "VDD", "Supply", "Alimentare", "V", "5"),
                    P("vgs_ctl", "|VGS|", "Gate control (reverse)", "Comanda pe grilă (inversă)", "V", "1.5"),
                    P("rl", "RL", "Load", "Sarcina", "Ω", "1k"),
                    P("idss", "IDSS", "Saturation current at VGS = 0", "Curentul de saturație la VGS = 0", "A", "10m"),
                    P("vp", "|VP|", "Pinch-off voltage", "Tensiunea de ștrangulare", "V", "4")]},
        {"key": "sf", "title": ("Source follower (buffer)", "Repetor pe sursă (buffer)"),
         "solve": jfet_sf, "draw": "jfollower", "plot": "amp",
         "params": [P("vdd", "VDD", "Supply", "Alimentare", "V", "15"),
                    P("rs", "RS", "Source resistor", "Rezistor de sursă", "Ω", "1k"),
                    P("rg", "RG", "Gate resistor", "Rezistor de grilă", "Ω", "1M"),
                    P("rl", "RL", "Load (0 = none)", "Sarcină (0 = fără)", "Ω", "10k"),
                    P("idss", "IDSS", "Saturation current at VGS = 0", "Curentul de saturație la VGS = 0", "A", "10m"),
                    P("vp", "|VP|", "Pinch-off voltage", "Tensiunea de ștrangulare", "V", "4"),
                    P("vin_ac", "vin", "Input amplitude (peak)", "Amplitudine intrare (vârf)", "V", "0.5"),
                    P("f", "f", "Signal frequency", "Frecvența semnalului", "Hz", "1k")]},
    ],
}

STATE_TXT = {
    "off": ("OFF (cut-off)", "BLOCAT (tăiere)"),
    "active": ("ACTIVE (linear) region", "Regiune ACTIVĂ (liniară)"),
    "sat": ("SATURATED / fully on", "SATURAT / complet deschis"),
    "triode": ("Ohmic (triode) region", "Regiune ohmică (triodă)"),
}
FET_SAT_TXT = ("Saturation (current-source) region", "Regiune de saturație (sursă de curent)")


# ===========================================================================
class TransistorCircuitsPanel(ttk.Frame):
    def __init__(self, parent, family, polarity, accent):
        super().__init__(parent, style="Card.TFrame")
        self.family = family
        self.ntype = polarity.upper().startswith("N")
        self.accent = accent
        self.circuits = CIRCUITS[family]
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body
        body.columnconfigure(0, weight=1)

        top = ttk.Frame(body, style="Card.TFrame")
        top.grid(row=0, column=0, sticky="w", padx=16, pady=(12, 4))
        ttk.Label(top, text=t("tc.choose"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self._titles = [L(*c["title"]) for c in self.circuits]
        self.sel = tk.StringVar(value=self._titles[0])
        cb = ttk.Combobox(top, textvariable=self.sel, values=self._titles, state="readonly", width=52)
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda e: self._build_form())
        self.desc_var = tk.StringVar()
        self.desc_lbl = ttk.Label(body, textvariable=self.desc_var, font=FONT_BODY, style="CardBody.TLabel",
                                  wraplength=900, justify="left")
        self.desc_lbl.grid(row=1, column=0, sticky="w", padx=16, pady=(0, 6))
        body.bind("<Configure>", lambda e: self.desc_lbl.configure(wraplength=max(300, e.width - 40)), add="+")

        mid = ttk.Frame(body, style="Card.TFrame")
        mid.grid(row=2, column=0, sticky="ew", padx=16)
        mid.columnconfigure(1, weight=1)
        self.form = ttk.Frame(mid, style="Card.TFrame")
        self.form.grid(row=0, column=0, sticky="nw", padx=(0, 12))
        self.canvas = tk.Canvas(mid, width=420, height=380, bg=sym.CANVAS_BG, highlightthickness=0)
        self.canvas.grid(row=0, column=1, sticky="new")
        self.canvas.bind("<Configure>", debounce(self.canvas, lambda *a: self._compute(), 150))

        self.result_var = tk.StringVar()
        ttk.Label(body, textvariable=self.result_var, font=("Consolas", 10, "bold"), foreground=accent,
                  style="CardFormula.TLabel", justify="left").grid(row=3, column=0, sticky="w", padx=16, pady=(8, 4))
        self.chart = MplChartFrame(body, figsize=(9.0, 3.0), with_toolbar=False)
        self.chart.grid(row=4, column=0, sticky="ew", padx=16, pady=(4, 16))
        self._build_form()

    # ------------------------------------------------------------------
    def _circuit(self):
        return self.circuits[self._titles.index(self.sel.get())]

    def _build_form(self):
        for ch in self.form.winfo_children():
            ch.destroy()
        c = self._circuit()
        self.desc_var.set(t(f"tc.desc.{self.family}.{c['key']}") + ("" if self.ntype else "\n" + t("tc.ptype_note")))
        self.vars = {}
        ttk.Label(self.form, text=t("tc.values"), font=FONT_H2, foreground=self.accent, style="CardSub.TLabel")\
            .grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 4))
        for r, prm in enumerate(c["params"], start=1):
            ttk.Label(self.form, text=prm.sym, font=("Consolas", 10, "bold"), foreground=self.accent,
                      style="CardFormula.TLabel").grid(row=r, column=0, sticky="w")
            ttk.Label(self.form, text=L(*prm.name), font=("Segoe UI", 9), style="CardBody.TLabel")\
                .grid(row=r, column=1, sticky="w", padx=(6, 6))
            if prm.kind == "bool":
                var = tk.BooleanVar(value=prm.default)
                ttk.Checkbutton(self.form, variable=var, command=self._compute).grid(row=r, column=2, sticky="w")
            else:
                var = tk.StringVar(value=prm.default)
                e = ttk.Entry(self.form, textvariable=var, width=9)
                e.grid(row=r, column=2, sticky="w", pady=1)
                e.bind("<KeyRelease>", lambda ev: self._compute())
                ttk.Label(self.form, text=prm.unit, font=("Segoe UI", 9), style="CardBody.TLabel")\
                    .grid(row=r, column=3, sticky="w", padx=(3, 0))
            self.vars[prm.key] = (prm, var)
        ttk.Label(self.form, text=t("tc.hint"), font=("Segoe UI", 8), foreground="#777", style="CardBody.TLabel",
                  wraplength=330, justify="left").grid(row=len(c["params"]) + 1, column=0, columnspan=4, sticky="w",
                                                        pady=(8, 0))
        self._compute()

    def _values(self):
        out = {}
        for key, (prm, var) in self.vars.items():
            if prm.kind == "bool":
                out[key] = bool(var.get())
            else:
                v = parse_value(var.get())
                if v < 0:
                    v = abs(v)
                out[key] = v
        for k in ("rb", "rc", "re", "rd", "rl", "r1", "r2", "rg"):
            if k in out and k not in ("rl", "re", "rs") and out[k] <= 0:
                out[k] = 1e-3
        return out

    # ------------------------------------------------------------------
    def _compute(self):
        if not hasattr(self, "vars"):
            return
        try:
            p = self._values()
            c = self._circuit()
            r = c["solve"](p)
        except Exception:
            self.result_var.set(t("common.enter_valid_values"))
            return
        self.p, self.r = p, r
        self.supply = p.get("vcc", p.get("vdd", 0.0))
        self._results(c, p, r)
        self._draw(c, p, r)
        self._plot(c, p, r)

    def real(self, v_n):
        """Real node voltage (to ground) from an N-model voltage."""
        return v_n if self.ntype else self.supply - v_n

    def _results(self, c, p, r):
        fam, key = self.family, c["key"]
        st = r.get("state", "")
        if fam != "bjt" and st == "sat":
            state_txt = L(*FET_SAT_TXT)
        else:
            state_txt = L(*STATE_TXT.get(st, ("", "")))
        lines = [f"{t('tc.state')}: {state_txt}"]
        R = self.real
        if fam == "bjt":
            lines.append(f"IB = {fv(r['ib'], 'A')}    IC = {fv(r['ic'], 'A')}    IE = {fv(r.get('ie', r['ic']), 'A')}")
            lines.append(f"VB = {fv(R(r['vb']), 'V')}   VE = {fv(R(r['ve']), 'V')}   VC = {fv(R(r['vc']), 'V')}   "
                         f"|VCE| = {fv(r['vce'], 'V')}")
            if key == "switch":
                lines.append(f"IC(sat) = {fv(r['ic_sat'], 'A')}   β·IB = {fv(p['beta'] * r['ib'], 'A')}   "
                             f"P(transistor) = {fv(r['p_dev'], 'W')}   P(load) = {fv(r['p_load'], 'W')}")
                lines.append(t("tc.rb_hint").format(rb=fv(r["rb_max"], "Ω")))
            elif key in ("ce", "ef"):
                lines.append(f"re = 25 mV / IE = {fv(r['re_small'], 'Ω')}   Av = {r['av']:+.2f}  "
                             f"({20 * math.log10(max(abs(r['av']), 1e-9)):.1f} dB)")
                lines.append(f"Zin ≈ {fv(r['zin'], 'Ω')}   Zout ≈ {fv(r['zout'], 'Ω')}   vout(peak) ≈ "
                             f"{fv(abs(r['av']) * p['vin_ac'], 'V')}")
            elif key == "ccs":
                lines.append(f"I(load) = (VZ − VBE)/RE = {fv(r['ic_nom'], 'A')}   actual = {fv(r['ic'], 'A')}   "
                             f"IZ = {fv(r['iz'], 'A')}")
                lines.append(t("tc.compliance").format(r=fv(r["rl_max"], "Ω")))
        else:
            vgs_key = "vgs" if "vgs" in r else "vg"
            lines.append(f"ID = {fv(r['id'], 'A')}    |VGS| = {fv(abs(r.get('vgs', r.get('vg', 0))), 'V')}    "
                         f"|VDS| = {fv(r['vds'], 'V')}")
            lines.append(f"VG = {fv(R(r['vg']), 'V')}   VS = {fv(R(r['vs']), 'V')}   VD = {fv(R(r['vd']), 'V')}")
            if key == "switch":
                lines.append(f"RDS(on) ≈ 1/(2K·Vov) = {fv(r['ron'], 'Ω')}   P(transistor) = {fv(r['p_dev'], 'W')}   "
                             f"P(load) = {fv(r['p_load'], 'W')}")
            elif key == "vcr":
                lines.append(f"RDS = VDS/ID = {fv(r['rds'], 'Ω')}   RDS(small VDS) = VP²/(2·IDSS·(VGS+|VP|)) = "
                             f"{fv(r['rds0'], 'Ω')}")
            elif key == "ccs":
                lines.append(f"I(nominal) = {fv(r['i_nom'], 'A')}   actual = {fv(r['id'], 'A')}")
                lines.append(t("tc.compliance").format(r=fv(r["rl_max"], "Ω")))
            else:
                lines.append(f"gm = {fv(r['gm'], 'S')}   Av = {r['av']:+.2f}  "
                             f"({20 * math.log10(max(abs(r['av']), 1e-9)):.1f} dB)")
                lines.append(f"Zin ≈ {fv(r['zin'], 'Ω')}   Zout ≈ {fv(r['zout'], 'Ω')}   vout(peak) ≈ "
                             f"{fv(abs(r['av']) * p['vin_ac'], 'V')}")
        lines.append(t(f"tc.formula.{fam}.{key}"))
        self.result_var.set("\n".join(lines))

    # ------------------------------------------------------------------
    # Schematic
    # ------------------------------------------------------------------
    def _Y(self, y):
        return y if self.ntype else self.H - y

    def _res(self, x1, y1, x2, y2, label, value, side=-1):
        sym.resistor(self.canvas, x1, self._Y(y1), x2, self._Y(y2), label=label, value=value, s=0.85,
                     label_side=side, label_offset=14 if x1 == x2 else None)

    def _wire(self, *pts):
        coords = []
        for i in range(0, len(pts), 2):
            coords += [pts[i], self._Y(pts[i + 1])]
        sym.wire(self.canvas, *coords)

    def _node(self, x, y):
        sym.node(self.canvas, x, self._Y(y))

    def _cap(self, x1, y1, x2, y2, label):
        sym.capacitor(self.canvas, x1, self._Y(y1), x2, self._Y(y2), label=label, s=0.8,
                      label_side=-1 if y1 == y2 else 1)

    def _vlabel(self, x, y, text, anchor="w"):
        self.canvas.create_text(x, self._Y(y), text=text, anchor=anchor, font=("Segoe UI", 8, "bold"), fill="#6a4c93")

    def _iarrow(self, x, y1, y2, text, side=1):
        """Conventional current arrow along a vertical wire (N drawing: y1 -> y2)."""
        a, b = self._Y(y1), self._Y(y2)
        if not self.ntype:
            a, b = b, a
        sym.current_arrow(self.canvas, x, a, x, b, text=text, color="#c62828", text_side=side)

    def _harrow(self, x1, x2, y, text):
        a, b = x1, x2
        if not self.ntype:
            a, b = b, a
        sym.current_arrow(self.canvas, a, self._Y(y), b, self._Y(y), text=text, color="#c62828", text_side=1)

    def _rails(self, W):
        top, bot = 40, self.H - 30
        self._wire(40, top, W - 30, top)
        self._wire(40, bot, W - 30, bot)
        sup = f"+{self.supply:g} V"
        if self.ntype:
            t_lbl, b_lbl = sup, "0 V"
        else:
            t_lbl, b_lbl = "0 V", sup
        c = self.canvas
        c.create_text(W - 28, self._Y(top) + (-10 if self.ntype else 10), text=t_lbl, anchor="e",
                      font=("Segoe UI", 9, "bold"), fill="#b91c1c" if self.ntype else "#1f2a44")
        c.create_text(W - 28, self._Y(bot) + (10 if self.ntype else -10), text=b_lbl, anchor="e",
                      font=("Segoe UI", 9, "bold"), fill="#1f2a44" if self.ntype else "#b91c1c")
        gy = self._Y(bot) if self.ntype else self._Y(top)
        sym.ground(c, 40, gy + 2)
        return top, bot

    def _device(self, x, cy):
        s = 1.05
        fy = 1 if self.ntype else -1
        ycy = self._Y(cy)
        if self.family == "bjt":
            sym.bjt(self.canvas, x, ycy, s=s, npn=self.ntype, fy=fy)
        elif self.family == "mosfet":
            sym.mosfet(self.canvas, x, ycy, s=s, nch=self.ntype, fy=fy)
        else:
            sym.jfet(self.canvas, x, ycy, s=s, nch=self.ntype, fy=fy)
        term = sym.device_terminals(self.family, x, ycy, s, fy=fy)
        names = list(term)
        # return terminal coordinates in the *N drawing* space
        conv = lambda pt: (pt[0], self._Y(pt[1]))  # noqa: E731
        return conv(term[names[0]]), conv(term[names[1]]), conv(term[names[2]])

    def _draw(self, c, p, r):
        cv = self.canvas
        cv.delete("all")
        W = cap_width(cv, max(420, cv.winfo_width() if cv.winfo_width() > 50 else 520), 780)
        self.H = H = 380
        top, bot = self._rails(W)
        kind = c["draw"]
        fam = self.family
        ctrl_name = "B" if fam == "bjt" else "G"
        top_name = "C" if fam == "bjt" else "D"
        bot_name = "E" if fam == "bjt" else "S"
        R = self.real
        dx = W * 0.56
        cy = H / 2
        (gx, gy), (tx, ty), (bx_, by) = self._device(dx, cy)
        i_main = r.get("ic", r.get("id", 0.0))
        pr = lambda k: fv(p[k], "Ω")  # noqa: E731

        # ---- top branch (collector / drain) ----
        if kind in ("switch", "amp", "ccs", "jamp", "jccs"):
            load_key = {"switch": "rc" if fam == "bjt" else "rl", "amp": "rc" if fam == "bjt" else "rd",
                        "ccs": "rl", "jamp": "rd", "jccs": "rl"}[kind]
            load_lbl = {"rc": "RC", "rd": "RD", "rl": "RL"}[load_key]
            self._res(tx, top, tx, 115, load_lbl, pr(load_key), side=1)
            self._wire(tx, 115, tx, ty)
            self._iarrow(tx - 20, 60, 95, fv(i_main, "A"), side=-1)
        else:
            self._wire(tx, top, tx, ty)
        self._node(tx, top)
        self._vlabel(tx - 8, 140, f"V{top_name} = {fv(R(r.get('vc', r.get('vd', 0))), 'V')}", anchor="e")

        # ---- bottom branch (emitter / source) ----
        bot_key = {"bjt": "re"}.get(fam, "rs")
        has_bot_r = kind in ("amp", "follower", "ccs", "jamp", "jccs", "jfollower") and p.get(bot_key, 0) > 0
        if has_bot_r:
            self._wire(tx, by, tx, 262)
            self._res(tx, 262, tx, bot, bot_key.upper(), pr(bot_key), side=1)
            if p.get("bypass"):
                self._wire(tx, 262, tx + 58, 262)
                self._cap(tx + 58, 262, tx + 58, bot, "C" + bot_name)
                self._node(tx, 262)
            self._vlabel(tx + 8, by + 14, f"V{bot_name} = {fv(R(r.get('ve', r.get('vs', 0))), 'V')}")
        else:
            self._wire(tx, by, tx, bot)
        self._node(tx, bot)

        # ---- output for followers ----
        out_node_y = None
        if kind in ("follower", "jfollower"):
            out_node_y = 262
        elif kind in ("amp", "jamp"):
            out_node_y = 130
        if out_node_y is not None and p.get("rl", 0) > 0:
            ox = W - 45
            self._node(tx, out_node_y)
            self._wire(tx, out_node_y, tx + 30, out_node_y)
            self._cap(tx + 30, out_node_y, tx + 64, out_node_y, "Cout")
            self._wire(tx + 64, out_node_y, ox, out_node_y)
            self._res(ox, out_node_y, ox, bot, "RL", pr("rl"), side=1)
            self._node(ox, bot)
            sym.terminal(cv, ox, self._Y(out_node_y), label="vout", anchor="s", dy=-8)
        elif out_node_y is not None:
            self._wire(tx, out_node_y, tx + 70, out_node_y)
            sym.terminal(cv, tx + 70, self._Y(out_node_y), label="vout", anchor="s", dy=-8)

        # ---- control (base / gate) side ----
        nx = gx - 82
        if kind == "switch":
            src_x = 70
            if fam == "bjt":
                self._res(src_x + 30, gy, gx, gy, "RB", pr("rb"))
                self._harrow(gx - 45, gx - 10, gy, f"IB {fv(r['ib'], 'A')}")
            else:
                self._wire(src_x, gy, gx, gy)
            self._wire(src_x, gy, src_x + 30, gy)
            self._wire(src_x, gy, src_x, (gy + bot) / 2 - 16)
            sym.dc_source(cv, src_x, self._Y((gy + bot) / 2))
            self._wire(src_x, (gy + bot) / 2 + 16, src_x, bot)
            val = {"bjt": "vin", "mosfet": "vgs", "jfet": "vgs_ctl"}[fam]
            txt = f"{'Vin' if fam == 'bjt' else 'VGS'} = {'-' if fam == 'jfet' else ''}{fv(p[val], 'V')}"
            cv.create_text(src_x + 22, self._Y((gy + bot) / 2), text=txt, anchor="w", font=("Segoe UI", 8, "bold"),
                           fill=sym.LABEL_COLOR)
            self._node(src_x, bot)
        elif kind in ("amp", "follower"):
            self._wire(nx, gy, gx, gy)
            self._res(nx, top, nx, gy, "R1", pr("r1"), side=-1)
            self._res(nx, gy, nx, bot, "R2", pr("r2"), side=-1)
            self._node(nx, gy)
            self._node(nx, top)
            self._node(nx, bot)
            self._input_ac(nx, gy, bot)
            self._vlabel(nx + 5, gy - 11, f"V{ctrl_name} = {fv(R(r.get('vb', r.get('vg', 0))), 'V')}")
            if fam == "bjt":
                self._harrow(nx + 12, gx - 12, gy, f"IB {fv(r['ib'], 'A')}")
        elif kind in ("jamp", "jfollower"):
            self._wire(nx, gy, gx, gy)
            self._res(nx, gy, nx, bot, "RG", pr("rg"), side=-1)
            self._node(nx, gy)
            self._node(nx, bot)
            self._input_ac(nx, gy, bot)
            self._vlabel(nx + 5, gy - 11, "VG = " + fv(R(0.0), "V"))
        elif kind == "ccs":
            self._wire(nx, gy, gx, gy)
            self._res(nx, top, nx, gy, "RB", pr("rb"), side=-1)
            a_y, k_y = (bot, gy + 20) if self.ntype else (gy + 20, bot)
            sym.diode(cv, nx, self._Y(a_y), nx, self._Y(k_y), variant="zener", s=0.85, label="DZ",
                      value=fv(p["vz"], "V"))
            self._wire(nx, gy, nx, gy + 20)
            self._node(nx, gy)
            self._node(nx, top)
            self._node(nx, bot)
            self._vlabel(nx + 5, gy - 11, f"VB = {fv(R(r['vb']), 'V')}")
        elif kind == "jccs":
            # gate tied to the bottom of RS (i.e. to the rail)
            self._wire(gx, gy, nx, gy, nx, bot)
            self._node(nx, bot)

    def _input_ac(self, nx, gy, bot):
        cv = self.canvas
        sx = 60
        self._wire(nx, gy, nx - 25, gy)
        self._cap(nx - 25, gy, nx - 60, gy, "Cin")
        self._wire(nx - 60, gy, sx, gy, sx, (gy + bot) / 2 - 16)
        sym.ac_source(cv, sx, self._Y((gy + bot) / 2))
        self._wire(sx, (gy + bot) / 2 + 16, sx, bot, nx, bot)
        cv.create_text(sx - 20, self._Y((gy + bot) / 2), text="vin", anchor="e", font=("Segoe UI", 9, "bold"),
                       fill=sym.LABEL_COLOR)

    # ------------------------------------------------------------------
    # Plots
    # ------------------------------------------------------------------
    def _plot(self, c, p, r):
        fig = self.chart.fig
        fig.clear()
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(122)
        for ax in (ax1, ax2):
            ax.set_facecolor(PLOT_BG)
            ax.grid(True, alpha=0.25)
        kind = c["plot"]
        fam = self.family
        R = self.real
        sup = self.supply
        solve = c["solve"]
        if kind == "switch":
            # transfer curve: output (collector/drain) voltage vs drive
            if fam == "bjt":
                xs = np.linspace(0, sup, 160)
                ys = [solve(dict(p, vin=x))["vce"] for x in xs]
                xlabel = L("Vin (V)", "Vin (V)")
                x_now = p["vin"]
            elif fam == "mosfet":
                xs = np.linspace(0, max(sup, p["vgs"]) * 1.0, 160)
                ys = [mos_switch(p, vgs=x)["vds"] for x in xs]
                xlabel = "|VGS| (V)"
                x_now = p["vgs"]
            else:
                a = abs(p["vp"])
                xs = np.linspace(-a * 1.2, 0, 160)
                ys = [jfet_vcr(p, vgs=x)["vds"] for x in xs]
                xlabel = "VGS (V)" if self.ntype else "−VGS (V)"
                x_now = -abs(p["vgs_ctl"])
            yr = [R(y) for y in ys]
            ax1.plot(xs, yr, color=self.accent, lw=2)
            ax1.plot([x_now], [R(r.get("vce", r.get("vds", 0)))], "o", color="#d97706", ms=8)
            ax1.set_xlabel(xlabel if self.ntype or fam == "jfet" else L("drive below +V (V)", "comanda sub +V (V)"))
            ax1.set_ylabel(L("V at collector/drain (V)", "V în colector/drenă (V)"))
            ax1.set_title(L("Transfer characteristic", "Caracteristica de transfer"), fontsize=10)
            # time domain: square-wave drive
            tt = np.linspace(0, 2, 400)
            on = (np.mod(tt, 1) < 0.5)
            if fam == "bjt":
                drv_on, out_on = p["vin"], solve(p)["vce"]
                out_off = solve(dict(p, vin=0))["vce"]
            elif fam == "mosfet":
                drv_on, out_on = p["vgs"], mos_switch(p)["vds"]
                out_off = mos_switch(p, vgs=0)["vds"]
            else:
                drv_on, out_on = 0.0, jfet_vcr(p, vgs=0)["vds"]
                out_off = jfet_vcr(p)["vds"]
            drive = np.where(on, drv_on, 0.0 if fam != "jfet" else -abs(p["vgs_ctl"]))
            out = np.where(on, out_on, out_off)
            ax2.plot(tt, [R(v) if fam != "jfet" else v for v in drive] if fam != "jfet" else drive,
                     color="#6A4C93", lw=1.5, label=L("drive", "comandă"))
            ax2.plot(tt, [R(v) for v in out], color="#c9622a", lw=2, label=L("output", "ieșire"))
            ax2.set_xlabel(L("time (periods)", "timp (perioade)"))
            ax2.set_ylabel("V")
            ax2.legend(fontsize=7, loc="upper right")
            ax2.set_title(L("Switching a square wave", "Comutarea unui semnal dreptunghiular"), fontsize=10)
        elif kind == "amp":
            # DC load line + Q point
            if fam == "bjt":
                rdc = p.get("rc", 0) + p["re"]
                vq, iq = r["vce"], r["ic"]
                xlab, ylab = "|VCE| (V)", "IC (A)"
            else:
                rdc = p.get("rd", 0) + p.get("rs", 0)
                vq, iq = r["vds"], r["id"]
                xlab, ylab = "|VDS| (V)", "ID (A)"
            imax = sup / rdc if rdc > 0 else iq * 2
            ax1.plot([0, sup], [imax, 0], color=self.accent, lw=2, label=L("DC load line", "Dreapta de sarcină DC"))
            ax1.plot([vq], [iq], "o", color="#d97706", ms=9, label="Q")
            ax1.set_xlim(0, sup * 1.05)
            ax1.set_ylim(0, max(imax, iq) * 1.15 if imax > 0 else 1)
            ax1.set_xlabel(xlab)
            ax1.set_ylabel(ylab)
            ax1.legend(fontsize=7)
            ax1.set_title(L("Operating point (Q)", "Punctul static de funcționare (PSF)"), fontsize=10)
            # waveform
            f = max(p["f"], 1e-3)
            tt = np.linspace(0, 2 / f, 500)
            vin = p["vin_ac"] * np.sin(2 * np.pi * f * tt)
            if c["draw"] in ("follower", "jfollower"):
                q = r.get("ve", r.get("vs", 0))
                lo_lim, hi_lim = 0.0, sup - (p.get("vsat", 0.2))
            else:
                q = r.get("vc", r.get("vd", 0))
                lo_lim = r.get("ve", r.get("vs", 0)) + (p.get("vsat", 0.2) if fam == "bjt" else r.get("vov", 0.3))
                hi_lim = sup
            vout = np.clip(q + r["av"] * vin, lo_lim, hi_lim)
            clipped = bool(np.any(np.abs(q + r["av"] * vin - vout) > 1e-9))
            ax2.plot(tt * 1e3, [R(v) for v in vout], color="#c9622a", lw=2, label=L("output node", "nodul de ieșire"))
            ax2b = ax2.twinx()
            ax2b.plot(tt * 1e3, vin, color="#6A4C93", lw=1.2, ls="--", label="vin")
            ax2b.set_ylabel("vin (V)", color="#6A4C93")
            ax2.set_xlabel("t (ms)")
            ax2.set_ylabel(L("output (V)", "ieșire (V)"))
            ttl = L("Input vs output", "Intrare vs ieșire")
            if clipped:
                ttl += L("  — CLIPPING!", "  — LIMITARE!")
            ax2.set_title(ttl, fontsize=10, color="#b91c1c" if clipped else "#222")
        elif kind == "ccs":
            rl_max = r["rl_max"] if math.isfinite(r["rl_max"]) else p["rl"] * 3
            xs = np.linspace(0, max(rl_max * 1.6, p["rl"] * 1.5, 10), 160)
            if fam == "bjt":
                ys = [bjt_ccs(p, rl=x)["ic"] for x in xs]
            else:
                ys = [jfet_ccs(p, rl=x)["id"] for x in xs]
            ax1.plot(xs, ys, color=self.accent, lw=2)
            ax1.plot([p["rl"]], [r.get("ic", r.get("id"))], "o", color="#d97706", ms=8)
            if math.isfinite(r["rl_max"]):
                ax1.axvline(r["rl_max"], color="#b91c1c", ls=":", lw=1.2)
                ax1.text(r["rl_max"], max(ys) * 0.5, " " + L("compliance limit", "limita de complianță"),
                         color="#b91c1c", fontsize=7)
            ax1.set_xlabel("RL (Ω)")
            ax1.set_ylabel(L("load current (A)", "curentul prin sarcină (A)"))
            ax1.set_ylim(0, max(ys) * 1.2 if max(ys) > 0 else 1)
            ax1.set_title(L("Current stays constant up to the limit", "Curentul rămâne constant până la limită"),
                          fontsize=10)
            vs = np.linspace(0, sup * 2, 160)
            if fam == "bjt":
                ys2 = [bjt_ccs(dict(p, vcc=v))["ic"] for v in vs]
            else:
                ys2 = [jfet_ccs(dict(p, vdd=v))["id"] for v in vs]
            ax2.plot(vs, ys2, color="#c9622a", lw=2)
            ax2.plot([sup], [r.get("ic", r.get("id"))], "o", color="#d97706", ms=8)
            ax2.set_xlabel(L("supply voltage (V)", "tensiunea de alimentare (V)"))
            ax2.set_ylabel(L("load current (A)", "curentul prin sarcină (A)"))
            ax2.set_title(L("…and against supply changes", "…și la variații ale alimentării"), fontsize=10)
        fig.tight_layout()
        self.chart.redraw()
