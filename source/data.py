"""
data.py - Reference data for the Electronist's Guide
Contains resistor/inductor color codes, capacitor codes, and component
reference text used across the app.
"""

# ---------------------------------------------------------------------------
# RESISTOR / INDUCTOR COLOR CODE TABLE
# ---------------------------------------------------------------------------
# digit      -> value used as a significant digit (0-9)
# multiplier -> value the digits are multiplied by
# tolerance  -> % tolerance represented by this color (None if not used)
# tempco     -> ppm/K temperature coefficient (6-band resistors only)
# hex        -> color used to draw the band

COLOR_CODE = {
    "Black":  {"digit": 0, "multiplier": 1,          "tolerance": None, "tempco": 250, "hex": "#1a1a1a"},
    "Brown":  {"digit": 1, "multiplier": 10,         "tolerance": 1,    "tempco": 100, "hex": "#7B3F00"},
    "Red":    {"digit": 2, "multiplier": 100,        "tolerance": 2,    "tempco": 50,  "hex": "#D62828"},
    "Orange": {"digit": 3, "multiplier": 1_000,      "tolerance": None, "tempco": 15,  "hex": "#F77F00"},
    "Yellow": {"digit": 4, "multiplier": 10_000,     "tolerance": None, "tempco": 25,  "hex": "#FCBF49"},
    "Green":  {"digit": 5, "multiplier": 100_000,    "tolerance": 0.5,  "tempco": 20,  "hex": "#2A9D8F"},
    "Blue":   {"digit": 6, "multiplier": 1_000_000,  "tolerance": 0.25, "tempco": 10,  "hex": "#277DA1"},
    "Violet": {"digit": 7, "multiplier": 10_000_000, "tolerance": 0.1,  "tempco": 5,   "hex": "#6A4C93"},
    "Grey":   {"digit": 8, "multiplier": 100_000_000,"tolerance": 0.05, "tempco": 1,   "hex": "#9CA3AF"},
    "White":  {"digit": 9, "multiplier": 1_000_000_000, "tolerance": None, "tempco": None, "hex": "#F4F4F4"},
    "Gold":   {"digit": None, "multiplier": 0.1,  "tolerance": 5,  "tempco": None, "hex": "#D4AF37"},
    "Silver": {"digit": None, "multiplier": 0.01, "tolerance": 10, "tempco": None, "hex": "#C0C0C0"},
    "None":   {"digit": None, "multiplier": None, "tolerance": 20, "tempco": None, "hex": "#EDE6DA"},
}

DIGIT_COLORS = [c for c, v in COLOR_CODE.items() if v["digit"] is not None]
MULTIPLIER_COLORS = [c for c, v in COLOR_CODE.items() if v["multiplier"] is not None]
TOLERANCE_COLORS = [c for c, v in COLOR_CODE.items() if v["tolerance"] is not None]
TEMPCO_COLORS = [c for c, v in COLOR_CODE.items() if v["tempco"] is not None]

BODY_COLOR = "#EDE0C8"   # resistor/inductor body color
WIRE_COLOR = "#B0B0B0"

# ---------------------------------------------------------------------------
# CAPACITOR CERAMIC TOLERANCE LETTER CODES
# ---------------------------------------------------------------------------
CERAMIC_TOLERANCE = {
    "B": "±0.1 pF", "C": "±0.25 pF", "D": "±0.5 pF", "F": "±1%",
    "G": "±2%", "J": "±5%", "K": "±10%", "M": "±20%", "Z": "+80%/-20%",
}

# Standard capacitor / resistor / inductor engineering unit prefixes
SI_PREFIXES = {
    "f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3,
    "": 1, "k": 1e3, "M": 1e6, "G": 1e9, "T": 1e12,
}

# Ordered list of (symbol, name-i18n-suffix, factor) used by the Unit
# Converter tab - kept separate from SI_PREFIXES (which drives free-text
# value parsing) so the converter can offer a clean, ordered dropdown.
UNIT_PREFIXES = [
    ("p", "pico", 1e-12),
    ("n", "nano", 1e-9),
    ("µ", "micro", 1e-6),
    ("m", "milli", 1e-3),
    ("", "base", 1.0),
    ("k", "kilo", 1e3),
    ("M", "mega", 1e6),
    ("G", "giga", 1e9),
    ("T", "tera", 1e12),
]

# Complete official set of SI prefixes (2022 extension through
# quecto/quetta), for the "Full SI prefixes" mode of the Unit Converter.
# The shorter UNIT_PREFIXES list above stays the default since it covers
# what's actually used in everyday electronics.
FULL_SI_PREFIXES = [
    ("q", "quecto", 1e-30),
    ("r", "ronto", 1e-27),
    ("y", "yocto", 1e-24),
    ("z", "zepto", 1e-21),
    ("a", "atto", 1e-18),
    ("f", "femto", 1e-15),
    ("p", "pico", 1e-12),
    ("n", "nano", 1e-9),
    ("µ", "micro", 1e-6),
    ("m", "milli", 1e-3),
    ("", "base", 1.0),
    ("k", "kilo", 1e3),
    ("M", "mega", 1e6),
    ("G", "giga", 1e9),
    ("T", "tera", 1e12),
    ("P", "peta", 1e15),
    ("E", "exa", 1e18),
    ("Z", "zetta", 1e21),
    ("Y", "yotta", 1e24),
    ("R", "ronna", 1e27),
    ("Q", "quetta", 1e30),
]


# ---------------------------------------------------------------------------
# COMPONENT REFERENCE TEXT (theory tab content), sourced from i18n so it
# reflects the currently selected language.
# ---------------------------------------------------------------------------
from i18n import t


def _f(name_key, value):
    return (t(name_key), value)


def get_theory(component):
    if component == "resistor":
        return {
            "title": t("theory.resistor.title"),
            "what": t("theory.resistor.what"),
            "how": t("theory.resistor.how"),
            "dc_formulas": [
                _f("f.ohms_law", "V = I × R"),
                _f("f.power", "P = V × I  =  I² × R  =  V² / R"),
                _f("f.series", "R_total = R1 + R2 + ... + Rn"),
                _f("f.parallel", "1/R_total = 1/R1 + 1/R2 + ... + 1/Rn"),
                _f("f.resistivity", "R = ρ × L / A  (ρ=resistivity, L=length, A=cross-section area)"),
                _f("f.voltage_divider", "Vout = Vin × R2 / (R1 + R2)"),
                _f("f.divider_ratio", "Vout / Vin = R2 / (R1 + R2)"),
            ],
            "ac_formulas": [
                _f("f.impedance", t("fv.resistor.ac.impedance")),
                _f("f.voltage_current_phase", t("fv.resistor.ac.phase")),
                _f("f.rms_form", "V_rms = I_rms × R"),
                _f("f.avg_power", "P_avg = I_rms² × R = V_rms² / R"),
            ],
        }
    if component == "capacitor":
        return {
            "title": t("theory.capacitor.title"),
            "what": t("theory.capacitor.what"),
            "how": t("theory.capacitor.how"),
            "dc_formulas": [
                _f("f.charge", "Q = C × V"),
                _f("f.energy_stored", "E = ½ × C × V²"),
                _f("f.cap_current", "iC = C × dv/dt"),
                _f("f.rc_time_constant", "τ = R × C"),
                _f("f.steady_state", t("fv.capacitor.dc.steady_state")),
                _f("f.series", "1/C_total = 1/C1 + 1/C2 + ..."),
                _f("f.parallel", "C_total = C1 + C2 + ..."),
            ],
            "ac_formulas": [
                _f("f.capacitive_reactance", "Xc = 1 / (2 × π × f × C)"),
                _f("f.impedance", t("fv.capacitor.ac.impedance")),
                _f("f.rms_form", "I_rms = V_rms / Xc"),
                _f("f.resonance_lc", "f0 = 1 / (2π√(LC))"),
            ],
        }
    if component == "inductor":
        return {
            "title": t("theory.inductor.title"),
            "what": t("theory.inductor.what"),
            "how": t("theory.inductor.how"),
            "dc_formulas": [
                _f("f.induced_voltage", "V = L × (dI/dt)"),
                _f("f.energy_stored", "E = ½ × L × I²"),
                _f("f.rl_time_constant", "τ = L / R"),
                _f("f.steady_state", t("fv.inductor.dc.steady_state")),
                _f("f.series", "L_total = L1 + L2 + ..."),
                _f("f.parallel", "1/L_total = 1/L1 + 1/L2 + ..."),
            ],
            "ac_formulas": [
                _f("f.inductive_reactance", "XL = 2 × π × f × L"),
                _f("f.impedance", t("fv.inductor.ac.impedance")),
                _f("f.rms_form", "V_rms = I_rms × XL"),
                _f("f.mutual_coupling", "k = M / √(L1 × L2)"),
                _f("f.transformer_ratio", "Vp/Vs = Np/Ns"),
                _f("f.transformer_current_ratio", "Ip/Is = Ns/Np  (ideal transformer)"),
                _f("f.transformer_power", "Pin ≈ Pout  (ideal; real transformers have losses)"),
            ],
        }
    if component == "diode":
        return {
            "title": t("theory.diode.title"),
            "what": t("theory.diode.what"),
            "how": t("theory.diode.how"),
            "formulas": [
                _f("f.diode_shockley", "ID = IS × (exp(VD / (n×VT)) − 1)"),
                _f("f.diode_thermal_voltage", "VT ≈ 25.85 mV"),
                _f("f.diode_power", "PD ≈ VD × ID"),
                _f("f.fwd_voltage_si", "Vf ≈ 0.6 - 0.7 V (typical, silicon, moderate current)"),
                _f("f.fwd_voltage_schottky", "Vf ≈ 0.2 - 0.4 V (typical, Schottky, moderate current)"),
                _f("f.led_resistor", "R = (Vsupply - Vf) / If"),
                _f("f.power_dissipated_r", "P = I² × R"),
            ],
        }
    if component in ("transistor", "transistor_bjt"):
        return {
            "title": t("theory.transistor.title"),
            "what": t("theory.transistor.what"),
            "how": t("theory.transistor.how"),
            "formulas": [
                _f("f.bjt_gain", "Ic = β × Ib   (forward active only)"),
                _f("f.bjt_emitter", "Ie = Ic + Ib"),
                _f("f.bjt_alpha", "α = β / (β + 1)"),
                _f("f.bjt_ic_alpha", "Ic ≈ α × Ie"),
                _f("f.bjt_regions", "Cutoff | Forward active | Saturation | Reverse active"),
                _f("f.base_resistor_switch", "Rb = (Vin - Vbe) / Ib"),
                _f("f.bjt_vce", "Vce = Vcc - Ic·Rc - Ie·Re"),
                _f("f.bjt_design_heuristics", "VE ≈ 0.1×VCC ;  Idivider ≈ 10×IB"),
            ],
        }
    if component == "transistor_mosfet":
        return {
            "title": t("theory.mosfet.title"),
            "what": t("theory.mosfet.what"),
            "how": t("theory.mosfet.how"),
            "formulas": [
                _f("f.mosfet_cutoff", "Cutoff:  Id = 0  for VGS ≤ VTH"),
                _f("f.mosfet_vov", "VOV = VGS - VTH"),
                _f("f.mosfet_triode", "Id = k[2·VOV·Vds - Vds²]   (linear/triode, Vds < VOV)"),
                _f("f.mosfet_sat", "Id = k·VOV²   (saturation, Vds ≥ VOV; k = ½·μn·Cox·(W/L))"),
                _f("f.mosfet_region", "Saturation if Vds ≥ Vov, else Linear/Triode"),
            ],
        }
    if component == "transistor_jfet":
        return {
            "title": t("theory.jfet.title"),
            "what": t("theory.jfet.what"),
            "how": t("theory.jfet.how"),
            "formulas": [
                _f("f.jfet_shockley", "Id = Idss × (1 - Vgs/Vp)²"),
                _f("f.jfet_pinchoff", "Vgs = Vp  ⇒  Id ≈ 0  (cutoff)"),
                _f("f.jfet_selfbias", "Vgs = -Id × Rs   (self-bias)"),
                _f("f.jfet_vds", "Vds = Vdd - Id × (Rd + Rs)"),
                _f("f.jfet_saturation", "Saturation if Vds ≥ Vgs - Vp  (model-dependent boundary)"),
            ],
        }
    if component == "opamp":
        return {
            "title": t("theory.opamp.title"),
            "what": t("theory.opamp.what"),
            "how": t("theory.opamp.how"),
            "formulas": [
                _f("f.virtual_short", "I+ ≈ I- ≈ 0 ;  V+ ≈ V-  (feedback + linear region only)"),
                _f("f.inv_gain", "Vout = -(Rf / Rin) × Vin"),
                _f("f.noninv_gain", "Vout = (1 + Rf / Rin) × Vin"),
                _f("f.voltage_follower", "Vout = Vin"),
                _f("f.opamp_summing", "Vout = -Rf × (V1/R1 + V2/R2 + ...)"),
                _f("f.opamp_integrator", "Vout = -(1/RC) × ∫Vin dt"),
                _f("f.opamp_differentiator", "Vout = -RC × dVin/dt"),
            ],
        }
    if component == "battery":
        return {
            "title": t("theory.battery.title"),
            "what": t("theory.battery.what"),
            "how": t("theory.battery.how"),
            "formulas": [
                _f("f.series_voltage", "V_total = V1 + V2 + ... + Vn"),
                _f("f.parallel_capacity", "Cap_total = Cap1 + Cap2 + ... + Capn"),
                _f("f.energy_wh", "E_Wh = V × Ah"),
                _f("f.runtime_estimate", t("fv.battery.runtime")),
                _f("f.crate", t("fv.battery.crate")),
            ],
        }
    if component == "basics":
        return {
            "title": t("theory.basics.title"),
            "what": t("theory.basics.what"),
            "how": t("theory.basics.how"),
            "formulas": [
                _f("f.ohms_law", "V = I × R"),
                _f("f.freq_period", "f = 1 / T"),
                _f("f.impedance", "Z = R + jX   (X = XL - Xc)"),
                _f("f.rms_from_peak", "Vrms = Vpeak / √2 ≈ 0.707 × Vpeak"),
                _f("f.resonant_freq_lc", "f0 = 1 / (2 × π × √(L × C))"),
            ],
        }
    if component == "digital":
        return {
            "title": t("theory.digital.title"),
            "what": t("theory.digital.what"),
            "how": t("theory.digital.how"),
            "formulas": [
                _f("theory.digital.f.commutative", "A+B = B+A     A·B = B·A"),
                _f("theory.digital.f.associative", "A+(B+C) = (A+B)+C     A·(B·C) = (A·B)·C"),
                _f("theory.digital.f.demorgan1", "(A · B)' = A' + B'"),
                _f("theory.digital.f.demorgan2", "(A + B)' = A' · B'"),
                _f("theory.digital.f.identity", "A + 0 = A     A · 1 = A"),
                _f("theory.digital.f.complement", "A + A' = 1     A · A' = 0"),
                _f("theory.digital.f.idempotent", "A + A = A     A · A = A"),
                _f("theory.digital.f.distributive", "A·(B+C) = A·B + A·C"),
                _f("theory.digital.f.absorption", "A + A·B = A     A·(A+B) = A"),
                _f("theory.digital.f.xor", "A XOR B = A'B + AB'"),
                _f("theory.digital.f.xnor", "A XNOR B = AB + A'B'"),
            ],
        }
    if component == "kirchhoff":
        return {
            "title": t("theory.kirchhoff.title"),
            "what": t("theory.kirchhoff.what"),
            "how": t("theory.kirchhoff.how"),
            "formulas": [
                _f("theory.kirchhoff.f.kvl", "ΣV = 0 (around any closed loop)"),
                _f("theory.kirchhoff.f.kcl", "ΣI_in = ΣI_out (at any node)"),
                _f("theory.kirchhoff.f.ohms_law", "V = I × R"),
                _f("theory.kirchhoff.f.series_current", "I is the same through every element in a loop"),
            ],
        }
    if component == "ac_circuits":
        return {
            "title": t("theory.ac_circuits.title"),
            "what": t("theory.ac_circuits.what"),
            "how": t("theory.ac_circuits.how"),
            "formulas": [
                _f("theory.ac_circuits.f.zr", "ZR = R"),
                _f("theory.ac_circuits.f.zl", "ZL = jωL"),
                _f("theory.ac_circuits.f.zc", "ZC = 1/(jωC) = -j/(ωC)"),
                _f("theory.ac_circuits.f.ohms_law_ac", "I = V / Z"),
                _f("f.impedance", "Z = R + jX"),
                _f("theory.ac_circuits.f.mag_phase", "|Z| = √(R² + X²)     θ = atan2(X, R)"),
                _f("theory.ac_circuits.f.reactance_sign", "X > 0: inductive   X < 0: capacitive   X = 0: purely resistive"),
                _f("theory.ac_circuits.f.power_factor", "cos φ = P / S = R / |Z|"),
                _f("theory.ac_circuits.f.powers", "S = Vrms·Irms     P = S·cos φ     Q = S·sin φ  (RMS values)"),
                _f("theory.ac_circuits.f.three_phase_y", "Star (Y): V_line = √3 × V_phase, I_line = I_phase"),
                _f("theory.ac_circuits.f.three_phase_d", "Delta (Δ): V_line = V_phase, I_line = √3 × I_phase"),
                _f("theory.ac_circuits.f.three_phase_power", "Balanced 3-phase: P = √3·VL·IL·cosφ,  Q = √3·VL·IL·sinφ,  S = √3·VL·IL"),
            ],
        }
    if component == "signal_gen":
        return {
            "title": t("theory.signal_gen.title"),
            "what": t("theory.signal_gen.what"),
            "how": t("theory.signal_gen.how"),
            "formulas": [
                _f("f.freq_period", "f = 1 / T"),
                _f("theory.signal_gen.f.angular", "ω = 2 × π × f"),
                _f("theory.signal_gen.f.sine", "v(t) = Voffset + A·sin(2πft + φ)"),
                _f("theory.signal_gen.f.vpp", "Vpp = 2 × Vpeak  (unclipped sine, no asymmetry)"),
                _f("theory.signal_gen.f.duty", "Duty cycle = t_high / T"),
                _f("theory.signal_gen.f.rms_general", "XRMS = √((1/T) ∫ x²(t) dt)"),
                _f("theory.signal_gen.f.rms_discrete", "XRMS = √((1/N) Σ xₙ²)"),
                _f("f.rms_from_peak", "Vrms = Vpeak / √2   (sine only!)"),
                _f("theory.signal_gen.f.rms_with_offset", "Vrms_total² = VDC² + Vrms_AC²"),
            ],
        }
    if component == "troubleshooting":
        return {
            "title": t("theory.troubleshooting.title"),
            "what": t("theory.troubleshooting.what"),
            "how": t("theory.troubleshooting.how"),
            "formulas": [
                _f("theory.troubleshooting.f.range", "Range = Nominal × (1 ± Tolerance%)"),
                _f("theory.troubleshooting.f.divider", "Ratio = R2 / (R1 + R2)"),
                _f("theory.troubleshooting.f.rss", "RSS Δ = √(Σ (sensitivity × Δxi)²)"),
                _f("theory.troubleshooting.f.short", "Measured ≈ 0 Ω → short"),
                _f("theory.troubleshooting.f.open", "Measured ≫ expected (OL) → open"),
            ],
        }
    if component == "modulation":
        return {
            "title": t("theory.modulation.title"),
            "what": t("theory.modulation.what"),
            "how": t("theory.modulation.how"),
            "formulas": [
                _f("theory.modulation.f.am", "AM: s(t) = Ac·(1 + m·mn(t))·cos(2πfc·t)"),
                _f("theory.modulation.f.am_index", "m = Am / Ac   (m<1 under-mod, m=1 100%, m>1 over-mod/distortion)"),
                _f("theory.modulation.f.sidebands", "fUSB = fc + fm     fLSB = fc - fm"),
                _f("theory.modulation.f.am_power", "PT = PC × (1 + m²/2)   (single-tone)"),
                _f("theory.modulation.f.am_efficiency", "η = m² / (2 + m²)"),
                _f("theory.modulation.f.am_bw", "AM bandwidth (single-tone): BW = 2 × fm"),
                _f("theory.modulation.f.am_bw_general", "AM bandwidth (general message, Bm): BW ≈ 2 × Bm"),
                _f("theory.modulation.f.fm", "FM: s(t) = Ac·cos(2πfc·t + 2πΔf·∫mn(t)dt)"),
                _f("theory.modulation.f.pm", "PM: s(t) = Ac·cos(2πfc·t + Δφ·mn(t))"),
                _f("theory.modulation.f.carson", "Carson's rule (single-tone): BW ≈ 2×(Δf + fm)"),
                _f("theory.modulation.f.carson_general", "Carson's rule (general message, Bm): BW ≈ 2×(Δf + Bm)"),
            ],
        }
    if component == "rf":
        return {
            "title": t("theory.rf.title"),
            "what": t("theory.rf.what"),
            "how": t("theory.rf.how"),
            "formulas": [
                _f("f.rf.impedance_freq", "Z = R + jX,   X_L = ωL,   X_C = -1/(ωC),   ω = 2πf"),
                _f("f.rf.reactance", "Inductive reactance X_L = ωL     Capacitive reactance X_C = 1/(ωC)"),
                _f("f.rf.char_impedance", "Z0 = √(L'/C')   (L', C' = per-unit-length inductance/capacitance)"),
                _f("f.rf.elec_length", "θ = β·l = (2πf / v_p)·l,   v_p = c0 × velocity factor,   λ = v_p / f"),
                _f("f.rf.reflection_coeff", "Γ = (Z_L - Z0) / (Z_L + Z0)"),
                _f("f.rf.vswr", "VSWR = (1 + |Γ|) / (1 - |Γ|)   (VSWR ≥ 1; VSWR = 1 is a perfect match)"),
                _f("f.rf.return_loss", "Return Loss (dB) = -20·log10(|Γ|) = -20·log10(|S11|)"),
                _f("f.rf.s_matrix", "[b] = [S]·[a]   —   for N ports, b_q = Σ_k S_qk·a_k   (S is N×N)"),
                _f("f.rf.s11_meaning", "S11 = b1/a1 with a2=a3=a4=0: reflection coefficient looking into port 1"),
                _f("f.rf.s21_meaning", "S21 = b2/a1 with a2=a3=a4=0: forward transmission, port 1 → port 2"),
                _f("f.rf.s22_meaning", "S22 = b2/a2 with a1=a3=a4=0: reflection coefficient looking into port 2"),
                _f("f.rf.norm_impedance", "z = Z / Z0   (Smith Chart resistance/reactance grid)"),
                _f("f.rf.norm_admittance", "y = 1 / z   (Smith Chart conductance/susceptance grid)"),
                _f("f.rf.quarter_wave", "Quarter-wave transformer: Zin = Z0² / Z_L   (physical length = λ/4)"),
            ],
        }
    raise KeyError(component)
