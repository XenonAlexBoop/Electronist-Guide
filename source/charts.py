"""
charts.py - Matplotlib-powered "simulate it" chart tabs.
Provides a reusable embedded-figure widget plus per-component signal
generation functions (DC transient / AC steady-state waveforms).
"""
import numpy as np
import tkinter as tk
from widgets import debounce_figure, smart_draw
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from widgets import parse_value, format_value, FONT_BODY, FONT_H2, FONT_MONO
from i18n import t

PLOT_BG = "#fdfaf3"
V_COLOR = "#c9622a"
I_COLOR = "#277DA1"


def include_zero(ax, axis="y", pad_frac=0.05):
    """Extend an already-autoscaled axis so 0 is always visible as a
    reference line, instead of matplotlib's default of zooming tight to
    just the data's own min/max (which can make a flat 2.5 V line look
    like it's swinging wildly, or hide that a value never actually
    reaches ground). Only ever widens the range - never clips data that's
    already shown. `pad_frac` adds a small margin so a value sitting
    exactly at the old edge isn't drawn flush against the frame.
    """
    get_lim, set_lim = (ax.get_ylim, ax.set_ylim) if axis == "y" else (ax.get_xlim, ax.set_xlim)
    lo, hi = get_lim()
    new_lo, new_hi = min(0.0, lo), max(0.0, hi)
    if new_lo == new_hi:
        new_lo, new_hi = -1.0, 1.0
    span = new_hi - new_lo
    pad = span * pad_frac
    # Only pad the side that wasn't already sitting at the natural data
    # edge, so we don't add pointless margin on both sides of a range
    # that was already fine.
    set_lim(new_lo - (pad if new_lo == lo and lo != 0 else 0),
            new_hi + (pad if new_hi == hi and hi != 0 else 0))


def align_zero_axes(ax1, ax2, pad_frac=0.06):
    """Make the 0 of two twin y-axes (e.g. voltage on the left, current on
    the right) sit at the SAME height on the plot, so both traces share one
    visible zero line. Each axis keeps all of its own data visible: we find
    the largest 'share below zero' and 'share above zero' needed by either
    axis and give both axes that same proportion."""
    lims = []
    for ax in (ax1, ax2):
        lo, hi = ax.get_ylim()
        lo, hi = min(lo, 0.0), max(hi, 0.0)
        if hi - lo == 0:
            lo, hi = -1.0, 1.0
        lims.append((lo, hi))
    neg = max(-lo / (hi - lo) for lo, hi in lims)
    pos = max(hi / (hi - lo) for lo, hi in lims)
    for ax, (lo, hi) in zip((ax1, ax2), lims):
        scale = 0.0
        if neg > 0:
            scale = max(scale, -lo / neg)
        if pos > 0:
            scale = max(scale, hi / pos)
        if scale == 0:
            scale = 1.0
        new_lo, new_hi = -neg * scale, pos * scale
        span = new_hi - new_lo
        ax.set_ylim(new_lo - span * pad_frac * (1 if neg > 0 else 0.5),
                    new_hi + span * pad_frac * (1 if pos > 0 else 0.5))
    # after padding, re-equalise the zero fraction exactly
    f0 = [(-a.get_ylim()[0]) / (a.get_ylim()[1] - a.get_ylim()[0]) for a in (ax1, ax2)]
    target = max(f0)
    for ax, f in zip((ax1, ax2), f0):
        lo, hi = ax.get_ylim()
        if f < target and hi > 0:
            ax.set_ylim(-target * hi / (1 - target), hi)


_ENG = [(1e9, "G"), (1e6, "M"), (1e3, "k"), (1.0, ""), (1e-3, "m"), (1e-6, "µ"), (1e-9, "n"), (1e-12, "p")]


def eng_scale(values):
    """Pick an engineering prefix for an array so axis numbers stay readable
    (e.g. 0.0023 A -> 2.3 mA). Returns (factor, prefix)."""
    try:
        m = float(np.nanmax(np.abs(values)))
    except Exception:
        return 1.0, ""
    if not np.isfinite(m) or m == 0:
        return 1.0, ""
    for f, p in _ENG:
        if m >= f * 0.999:
            return f, p
    return 1e-12, "p"


# ---------------------------------------------------------------------------
# Signal generators
# ---------------------------------------------------------------------------
def resistor_signals(r, mode, voltage=5.0, amplitude=5.0, frequency=100.0):
    if mode == "DC":
        # switch closed at 2 ms, opened at 12 ms: shows that a resistor's
        # current follows its voltage instantly (no charging curve).
        t = np.linspace(0, 0.016, 800)
        v = np.where((t >= 0.002) & (t < 0.012), voltage, 0.0)
        i = v / r
        return t, v, i, None, 0.012
    else:
        periods = 2
        t = np.linspace(0, periods / frequency, 800)
        v = amplitude * np.sin(2 * np.pi * frequency * t)
    i = v / r
    return t, v, i, None, None


def capacitor_signals(c, mode, resistance=1000.0, voltage=5.0, amplitude=5.0, frequency=100.0):
    if mode == "DC":
        tau = resistance * c
        t_charge = np.linspace(0, 5 * tau, 300)
        v_charge = voltage * (1 - np.exp(-t_charge / tau))
        i_charge = (voltage / resistance) * np.exp(-t_charge / tau)

        v_at_switch = v_charge[-1]
        t_discharge = np.linspace(5 * tau, 10 * tau, 300)
        v_discharge = v_at_switch * np.exp(-(t_discharge - 5 * tau) / tau)
        i_discharge = -(v_at_switch / resistance) * np.exp(-(t_discharge - 5 * tau) / tau)

        t_arr = np.concatenate([t_charge, t_discharge])
        v_arr = np.concatenate([v_charge, v_discharge])
        i_arr = np.concatenate([i_charge, i_discharge])
        return t_arr, v_arr, i_arr, tau, 5 * tau
    else:
        w = 2 * np.pi * frequency
        t = np.linspace(0, 2 / frequency, 800)
        v = amplitude * np.sin(w * t)
        i = amplitude * w * c * np.sin(w * t + np.pi / 2)
        return t, v, i, None, None


def inductor_signals(l, mode, resistance=100.0, voltage=5.0, amplitude=5.0, frequency=100.0):
    if mode == "DC":
        tau = l / resistance
        t_charge = np.linspace(0, 5 * tau, 300)
        i_charge = (voltage / resistance) * (1 - np.exp(-t_charge / tau))
        v_charge = voltage * np.exp(-t_charge / tau)

        i_at_switch = i_charge[-1]
        t_discharge = np.linspace(5 * tau, 10 * tau, 300)
        i_discharge = i_at_switch * np.exp(-(t_discharge - 5 * tau) / tau)
        v_discharge = -i_at_switch * resistance * np.exp(-(t_discharge - 5 * tau) / tau)

        t_arr = np.concatenate([t_charge, t_discharge])
        v_arr = np.concatenate([v_charge, v_discharge])
        i_arr = np.concatenate([i_charge, i_discharge])
        return t_arr, v_arr, i_arr, tau, 5 * tau
    else:
        w = 2 * np.pi * frequency
        t = np.linspace(0, 2 / frequency, 800)
        v = amplitude * np.sin(w * t)
        i = (amplitude / (w * l)) * np.sin(w * t - np.pi / 2)
        return t, v, i, None, None


def diode_dc_curve(is_amps=1e-12, n=1.8, vt=0.02585, v_max=0.9):
    v = np.linspace(-0.2, v_max, 500)
    i = is_amps * (np.exp(v / (n * vt)) - 1)
    return v, i


def diode_rectifier(vf, amplitude, frequency, r_load):
    t = np.linspace(0, 2 / frequency, 1000)
    vin = amplitude * np.sin(2 * np.pi * frequency * t)
    vout = np.clip(vin - vf, 0, None)
    i = vout / r_load
    return t, vin, vout, i


def transistor_switch(vin_high, vbe, beta, rb, rc, vcc, frequency=200.0):
    t = np.linspace(0, 3 / frequency, 1000)
    vin = np.where(np.mod(t * frequency, 1.0) < 0.5, vin_high, 0.0)
    ib = np.clip((vin - vbe) / rb, 0, None)
    ic_wanted = beta * ib
    ic_max = vcc / rc  # saturation limit
    ic = np.minimum(ic_wanted, ic_max)
    vout = vcc - ic * rc
    return t, vin, vout, ic


def transistor_amplifier(vin_amp, frequency, gain, vcc):
    t = np.linspace(0, 2 / frequency, 800)
    vin = vin_amp * np.sin(2 * np.pi * frequency * t)
    vout = np.clip(-gain * vin, -vcc, vcc)
    return t, vin, vout


def mosfet_switch(vgs_high, vth, k, rd, vdd, frequency=200.0):
    """Ideal MOSFET switch: square-wave gate drive vs. drain output.
    Id follows the square law above threshold, capped at the Vdd/Rd rail."""
    t = np.linspace(0, 3 / frequency, 1000)
    vin = np.where(np.mod(t * frequency, 1.0) < 0.5, vgs_high, 0.0)
    ov = np.clip(vin - vth, 0, None)
    id_wanted = k * ov ** 2
    id_max = vdd / rd  # rail-limited (triode) current
    id_ = np.minimum(id_wanted, id_max)
    vout = vdd - id_ * rd
    return t, vin, vout, id_


def mosfet_amplifier(vin_amp, frequency, gain, vdd):
    """Common-source small-signal amplifier: same inverting-gain model as
    the BJT common-emitter amplifier, parameterized by gm*Rd instead of Rc/Re."""
    t = np.linspace(0, 2 / frequency, 800)
    vin = vin_amp * np.sin(2 * np.pi * frequency * t)
    vout = np.clip(-gain * vin, -vdd, vdd)
    return t, vin, vout


def jfet_switch(vgs_pinch, idss, vp, rd, vdd, frequency=200.0):
    """Ideal JFET switch: depletion-mode device, normally ON at Vgs=0 and
    pinched OFF as Vgs approaches Vp. Gate toggles between 0 V and vgs_pinch."""
    t = np.linspace(0, 3 / frequency, 1000)
    vin = np.where(np.mod(t * frequency, 1.0) < 0.5, 0.0, vgs_pinch)
    ratio = np.clip(1 - vin / vp, 0, None) if vp != 0 else np.zeros_like(vin)
    id_wanted = idss * ratio ** 2
    id_max = vdd / rd
    id_ = np.minimum(id_wanted, id_max)
    vout = vdd - id_ * rd
    return t, vin, vout, id_


def jfet_amplifier(vin_amp, frequency, gain, vdd):
    """Common-source JFET small-signal amplifier, same inverting-gain model."""
    t = np.linspace(0, 2 / frequency, 800)
    vin = vin_amp * np.sin(2 * np.pi * frequency * t)
    vout = np.clip(-gain * vin, -vdd, vdd)
    return t, vin, vout


# ---------------------------------------------------------------------------
# Rectifier bridges (2-diode center-tap, 4-diode full bridge)
# ---------------------------------------------------------------------------
def _rc_peak_detector(vout_raw, t, r_load, cap):
    """Idealized capacitor-input filter: instant charge to the rectified peak,
    exponential RC discharge otherwise. Produces the classic ripple waveform."""
    vcap = np.zeros_like(vout_raw)
    for i in range(1, len(t)):
        dt = t[i] - t[i - 1]
        if vout_raw[i] >= vcap[i - 1]:
            vcap[i] = vout_raw[i]
        else:
            vcap[i] = vcap[i - 1] * np.exp(-dt / (r_load * cap))
    return vcap


def two_diode_rectifier_signals(amplitude=12.0, frequency=60.0, vf=0.7, r_load=1000.0):
    t = np.linspace(0, 3 / frequency, 1000)
    vin = amplitude * np.sin(2 * np.pi * frequency * t)
    vout = np.clip(np.abs(vin) - vf, 0, None)
    i = vout / r_load
    return t, vin, vout, i


def four_diode_bridge_signals(amplitude=12.0, frequency=60.0, vf=0.7, r_load=1000.0, cap=None):
    t = np.linspace(0, 3 / frequency, 1000)
    vin = amplitude * np.sin(2 * np.pi * frequency * t)
    vout_raw = np.clip(np.abs(vin) - 2 * vf, 0, None)
    if cap is not None and cap > 0:
        vout = _rc_peak_detector(vout_raw, t, r_load, cap)
    else:
        vout = vout_raw
    i = vout / r_load
    return t, vin, vout, i, vout_raw


# ---------------------------------------------------------------------------
# Voltage divider / filter (series element + shunt element to ground)
# ---------------------------------------------------------------------------
def _impedance(kind, value, omega):
    if kind == "resistor":
        return complex(value, 0)
    if kind == "inductor":
        return complex(0, omega * value)
    if kind == "capacitor":
        if omega == 0:
            return complex(float("inf"), 0)
        return complex(0, -1 / (omega * value))
    raise ValueError(kind)


def divider_ac_signals(series_kind, series_val, shunt_kind, shunt_val, amplitude=5.0, frequency=1000.0):
    w = 2 * np.pi * frequency
    zs = _impedance(series_kind, series_val, w)
    zp = _impedance(shunt_kind, shunt_val, w)
    h = zp / (zs + zp)
    mag = abs(h)
    phase = np.angle(h)
    t = np.linspace(0, 2 / frequency, 800)
    vin = amplitude * np.sin(w * t)
    vout = mag * amplitude * np.sin(w * t + phase)
    return t, vin, vout, mag, phase


def divider_dc_signals(series_kind, series_val, shunt_kind, shunt_val, voltage=5.0):
    def dc_value(kind, value):
        if kind == "inductor":
            return 0.0
        if kind == "capacitor":
            return float("inf")
        return value

    rs = dc_value(series_kind, series_val)
    rp = dc_value(shunt_kind, shunt_val)

    if rs == float("inf"):
        vout_final = 0.0
    elif rp == float("inf"):
        vout_final = voltage
    elif rs + rp == 0:
        vout_final = 0.0
    else:
        vout_final = voltage * rp / (rs + rp)

    tau = None
    shape = None
    if series_kind == "resistor" and shunt_kind == "capacitor":
        tau, shape = series_val * shunt_val, "charge"
    elif series_kind == "capacitor" and shunt_kind == "resistor":
        tau, shape = series_val * shunt_val, "decay"
    elif series_kind == "resistor" and shunt_kind == "inductor":
        tau, shape = shunt_val / series_val, "decay"
    elif series_kind == "inductor" and shunt_kind == "resistor":
        tau, shape = series_val / shunt_val, "charge"

    if tau is not None and tau > 0:
        t = np.linspace(0, 5 * tau, 600)
        if shape == "charge":
            vout = vout_final * (1 - np.exp(-t / tau))
        else:
            vout = voltage * np.exp(-t / tau)
        vin = np.full_like(t, voltage)
        return t, vin, vout, tau
    else:
        t = np.linspace(0, 0.02, 400)
        vin = np.full_like(t, voltage)
        vout = np.full_like(t, vout_final)
        return t, vin, vout, None


# ---------------------------------------------------------------------------
# Optional 2-stage ladder (Stage 1: Zs1/Zp1, Stage 2: Zs2/Zp2) — lets the
# divider/filter tab build real 2nd-order responses (band-pass, band-stop,
# steeper low/high-pass) by cascading two L-sections.
# ---------------------------------------------------------------------------
def _ladder_transfer(zs1, zp1, zs2, zp2):
    """H = Vout/Vin for Vin--Zs1--A--Zs2--Vout, Zp1: A to gnd, Zp2: Vout to gnd."""
    return (zp1 * zp2) / (zp1 * (zp2 + zs2) + zs1 * (zp2 + zs2 + zp1))


def divider_ac_signals2(s1_kind, s1_val, p1_kind, p1_val, s2_kind, s2_val, p2_kind, p2_val,
                         amplitude=5.0, frequency=1000.0):
    w = 2 * np.pi * frequency
    zs1 = _impedance(s1_kind, s1_val, w)
    zp1 = _impedance(p1_kind, p1_val, w)
    zs2 = _impedance(s2_kind, s2_val, w)
    zp2 = _impedance(p2_kind, p2_val, w)
    h = _ladder_transfer(zs1, zp1, zs2, zp2)
    mag = abs(h)
    phase = np.angle(h)
    t = np.linspace(0, 2 / frequency, 800)
    vin = amplitude * np.sin(w * t)
    vout = mag * amplitude * np.sin(w * t + phase)
    return t, vin, vout, mag, phase


def divider_dc_signals2(s1_kind, s1_val, p1_kind, p1_val, s2_kind, s2_val, p2_kind, p2_val, voltage=5.0):
    def dc_value(kind, value):
        if kind == "inductor":
            return 0.0
        if kind == "capacitor":
            return float("inf")
        return value

    zs1, zp1 = dc_value(s1_kind, s1_val), dc_value(p1_kind, p1_val)
    zs2, zp2 = dc_value(s2_kind, s2_val), dc_value(p2_kind, p2_val)

    # steady state via the same ladder formula, evaluated at DC-equivalent real values
    # (handle infinities by nudging to a very large finite number)
    BIG = 1e15
    zs1r = BIG if zs1 == float("inf") else zs1
    zp1r = BIG if zp1 == float("inf") else zp1
    zs2r = BIG if zs2 == float("inf") else zs2
    zp2r = BIG if zp2 == float("inf") else zp2
    try:
        vout_final = voltage * _ladder_transfer(zs1r, zp1r, zs2r, zp2r)
    except ZeroDivisionError:
        vout_final = 0.0

    reactive_kinds = [k for k in (s1_kind, p1_kind, s2_kind, p2_kind) if k in ("capacitor", "inductor")]
    single_reactive = len(reactive_kinds) == 1

    tau = None
    if single_reactive:
        if p1_kind in ("capacitor", "inductor"):
            comp_kind, comp_val = p1_kind, p1_val
            r_th = _parallel(zs1r, zs2r + zp2r)
        elif s1_kind in ("capacitor", "inductor"):
            comp_kind, comp_val = s1_kind, s1_val
            r_th = _parallel(zp1r, zs2r + zp2r)
        elif p2_kind in ("capacitor", "inductor"):
            comp_kind, comp_val = p2_kind, p2_val
            r_th = zs2r + _parallel(zp1r, zs1r)
        else:
            comp_kind, comp_val = s2_kind, s2_val
            r_th = _parallel(zp1r, zs1r) + zp2r

        if r_th > 0:
            tau = comp_val * r_th if comp_kind == "capacitor" else comp_val / r_th

    if tau is not None and tau > 0:
        t = np.linspace(0, 5 * tau, 600)
        v0 = 0.0
        vout = vout_final + (v0 - vout_final) * np.exp(-t / tau)
        vin = np.full_like(t, voltage)
        return t, vin, vout, tau
    else:
        t = np.linspace(0, 0.02, 400)
        vin = np.full_like(t, voltage)
        vout = np.full_like(t, vout_final)
        return t, vin, vout, None


def _parallel(a, b):
    if a + b == 0:
        return 0.0
    return (a * b) / (a + b)


# ---------------------------------------------------------------------------
# Amplitude-modulated input signal through the divider/filter network.
# vin(t) = A*(1 + m*cos(2*pi*fm*t))*cos(2*pi*fc*t)
#        = A*cos(wc t) + (A*m/2)*cos((wc-wm)t) + (A*m/2)*cos((wc+wm)t)
# Each spectral component is passed through the network's (linear) transfer
# function H(f) independently, then summed - exact for a linear RC/RL/RLC
# network driven by an AM tone.
# ---------------------------------------------------------------------------
def divider_ac_am_signals(series_kind, series_val, shunt_kind, shunt_val,
                           amplitude=5.0, carrier_frequency=10000.0,
                           mod_frequency=500.0, mod_index=0.5):
    if mod_frequency <= 0:
        mod_frequency = 1.0
    if carrier_frequency <= 0:
        carrier_frequency = 1.0

    def h_of(f):
        w = 2 * np.pi * f
        zs = _impedance(series_kind, series_val, w)
        zp = _impedance(shunt_kind, shunt_val, w)
        return zp / (zs + zp)

    components = [
        (carrier_frequency, amplitude),
        (carrier_frequency - mod_frequency, amplitude * mod_index / 2),
        (carrier_frequency + mod_frequency, amplitude * mod_index / 2),
    ]

    periods = 3
    n_samples = int(np.clip(40 * carrier_frequency / mod_frequency, 1200, 20000))
    t = np.linspace(0, periods / mod_frequency, n_samples)

    vin = np.zeros_like(t)
    vout = np.zeros_like(t)
    for f, amp in components:
        if f <= 0:
            continue
        w = 2 * np.pi * f
        vin += amp * np.cos(w * t)
        h = h_of(f)
        vout += amp * abs(h) * np.cos(w * t + np.angle(h))

    h_carrier = h_of(carrier_frequency)
    return t, vin, vout, abs(h_carrier), np.angle(h_carrier)


# ---------------------------------------------------------------------------
# General-purpose waveform generator (Signal Generator sub-tab).
# ---------------------------------------------------------------------------
def _waveform_at(t, wave_type, frequency, amplitude, offset, duty_cycle):
    """Evaluate a standard waveform at an arbitrary, caller-supplied time
    array `t`. Factored out of waveform_signal() so other callers (the
    Modulation tab) can generate a message signal on the *same* time base
    as a carrier, which they need to multiply/combine sample-for-sample."""
    duty_cycle = min(max(duty_cycle, 0.01), 0.99)
    phase = np.mod(frequency * t, 1.0)

    wt = wave_type.lower()
    if wt == "sine":
        v = amplitude * np.sin(2 * np.pi * frequency * t)
    elif wt == "square":
        v = np.where(phase < duty_cycle, amplitude, -amplitude)
    elif wt == "sawtooth":
        v = amplitude * (2 * phase - 1)
    elif wt == "triangle":
        v = np.where(
            phase < duty_cycle,
            -amplitude + 2 * amplitude * (phase / duty_cycle),
            amplitude - 2 * amplitude * ((phase - duty_cycle) / (1 - duty_cycle)),
        )
    else:
        v = amplitude * np.sin(2 * np.pi * frequency * t)
    return v + offset


def waveform_signal(wave_type, frequency=1000.0, amplitude=5.0, offset=0.0,
                     duty_cycle=0.5, periods=3):
    if frequency <= 0:
        frequency = 1.0
    t = np.linspace(0, periods / frequency, 2000)
    v = _waveform_at(t, wave_type, frequency, amplitude, offset, duty_cycle)
    rms = float(np.sqrt(np.mean(v ** 2)))
    peak_to_peak = float(v.max() - v.min())
    return t, v, rms, peak_to_peak


# ---------------------------------------------------------------------------
# Modulation tab: AM / FM / PM of an arbitrary message waveform onto a
# sinusoidal carrier, all sampled on one shared, carrier-resolving time base
# so message/carrier/modulated line up sample-for-sample.
# ---------------------------------------------------------------------------
def modulate_signal(mod_type, wave_type, msg_frequency=100.0, msg_amplitude=1.0,
                     msg_duty=0.5, carrier_frequency=2000.0, carrier_amplitude=1.0,
                     am_index=0.5, fm_deviation=500.0, pm_deviation=1.5708, periods=3):
    if msg_frequency <= 0:
        msg_frequency = 1.0
    if carrier_frequency <= 0:
        carrier_frequency = 1.0

    n_samples = int(np.clip(60 * carrier_frequency / msg_frequency, 1500, 30000))
    t = np.linspace(0, periods / msg_frequency, n_samples)

    message = _waveform_at(t, wave_type, msg_frequency, msg_amplitude, 0.0, msg_duty)
    # Normalized to +/-1 (independent of msg_amplitude) so the AM index /
    # FM deviation / PM deviation parameters mean the same thing regardless
    # of how large the message amplitude is set.
    msg_norm = message / msg_amplitude if msg_amplitude != 0 else np.zeros_like(message)

    carrier = carrier_amplitude * np.cos(2 * np.pi * carrier_frequency * t)

    mt = mod_type.upper()
    if mt == "AM":
        modulated = carrier_amplitude * (1 + am_index * msg_norm) * np.cos(2 * np.pi * carrier_frequency * t)
    elif mt == "FM":
        dt = t[1] - t[0]
        integral = np.cumsum(msg_norm) * dt
        modulated = carrier_amplitude * np.cos(2 * np.pi * carrier_frequency * t + 2 * np.pi * fm_deviation * integral)
    elif mt == "PM":
        modulated = carrier_amplitude * np.cos(2 * np.pi * carrier_frequency * t + pm_deviation * msg_norm)
    else:
        modulated = carrier.copy()

    return t, message, carrier, modulated


def modulation_spectrum(t, signal):
    """Single-sided FFT magnitude spectrum of a time-domain signal."""
    n = len(t)
    if n < 2:
        return np.array([0.0]), np.array([0.0])
    dt = t[1] - t[0]
    freqs = np.fft.rfftfreq(n, d=dt)
    mag = np.abs(np.fft.rfft(signal)) / n * 2
    return freqs, mag


def am_envelope_demod(signal):
    """Crude AM envelope detector: rectify then smooth with a moving-average
    low-pass. Good enough to visually confirm 'does this look like the
    message', not a real receiver design."""
    rectified = np.abs(signal)
    window = max(3, len(signal) // 150)
    kernel = np.ones(window) / window
    return np.convolve(rectified, kernel, mode="same")



# ---------------------------------------------------------------------------
# Embedded chart widget
# ---------------------------------------------------------------------------
class MplChartFrame(ttk.Frame):
    """A matplotlib Figure embedded in a ttk.Frame, with an optional nav toolbar."""

    def __init__(self, parent, figsize=(5.6, 4.0), with_toolbar=True):
        super().__init__(parent, style="Card.TFrame")
        self.fig = Figure(figsize=figsize, dpi=100, facecolor=PLOT_BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        debounce_figure(self.canvas)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        if with_toolbar:
            toolbar_frame = tk.Frame(self, bg=PLOT_BG)
            toolbar_frame.pack(fill="x")
            self.toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
            self.toolbar.update()

    def clear(self):
        self.fig.clear()

    def redraw(self):
        smart_draw(self.canvas)


# ---------------------------------------------------------------------------
# Generic time-domain V/I chart tab (resistor, capacitor, inductor, transistor)
# ---------------------------------------------------------------------------
class ParamField:
    def __init__(self, key, label, default):
        self.key = key
        self.label = label
        self.default = default


class TimeChartTab(ttk.Frame):
    """
    A reusable "Chart / Simulation" sub-tab: mode selector (DC/AC), a set of
    parameter entries that change with mode, a Simulate button, and an
    embedded dual-axis (V left, I right) matplotlib plot.
    """

    def __init__(self, parent, accent, dc_fields, ac_fields, signal_fn,
                 dc_note="", ac_note="", v_unit="V", i_unit="A", title="Simulation", reactive=None):
        super().__init__(parent, style="Card.TFrame")
        self.reactive = reactive   # "capacitor" / "inductor" -> rich AC view
        self.accent = accent
        self.dc_fields = dc_fields
        self.ac_fields = ac_fields
        self.signal_fn = signal_fn
        self.dc_note = dc_note
        self.ac_note = ac_note
        self.v_unit = v_unit
        self.i_unit = i_unit

        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        controls = ttk.Frame(self, style="Card.TFrame")
        controls.grid(row=0, column=0, sticky="ns", padx=(16, 8), pady=16)

        ttk.Label(controls, text=title, font=FONT_H2, foreground=accent,
                  style="CardSub.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(controls, text=t("common.mode"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=1, column=0, sticky="w", pady=4)
        self.mode = tk.StringVar(value="AC")
        mode_cb = ttk.Combobox(controls, textvariable=self.mode, values=["AC", "DC"],
                                state="readonly", width=8)
        mode_cb.grid(row=1, column=1, sticky="w", pady=4)
        mode_cb.bind("<<ComboboxSelected>>", lambda e: self._rebuild_fields())

        self.field_frame = ttk.Frame(controls, style="Card.TFrame")
        self.field_frame.grid(row=2, column=0, columnspan=2, sticky="w", pady=6)
        self.field_vars = {}

        ttk.Button(controls, text=t("common.simulate"), command=self._simulate)\
            .grid(row=3, column=0, columnspan=2, pady=(10, 6), sticky="ew")

        self.note_var = tk.StringVar()
        ttk.Label(controls, textvariable=self.note_var, font=("Segoe UI", 9), foreground=accent,
                  style="CardBody.TLabel", wraplength=220, justify="left")\
            .grid(row=4, column=0, columnspan=2, sticky="w", pady=(4, 0))

        chart_wrap = ttk.Frame(self, style="Card.TFrame")
        chart_wrap.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        self.chart = MplChartFrame(chart_wrap)
        self.chart.pack(fill="both", expand=True)

        self._rebuild_fields()

    def _current_fields(self):
        return self.dc_fields if self.mode.get() == "DC" else self.ac_fields

    def _rebuild_fields(self):
        for child in self.field_frame.winfo_children():
            child.destroy()
        self.field_vars = {}
        for i, field in enumerate(self._current_fields()):
            ttk.Label(self.field_frame, text=field.label, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=i, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=field.default)
            ttk.Entry(self.field_frame, textvariable=var, width=10).grid(row=i, column=1, pady=3, padx=(6, 0))
            self.field_vars[field.key] = var
        self._simulate()

    # ------------------------------------------------------------------
    def _simulate_reactive_ac(self, kw):
        """Rich AC view for a capacitor or inductor (optionally with a series R):
        waveforms with the phase shift marked, instantaneous power (energy
        stored / returned), phasor diagram, and reactance vs frequency."""
        cap = self.reactive == "capacitor"
        val = kw["c"] if cap else kw["l"]
        r = max(0.0, kw.get("resistance", 0.0))
        vp = kw["amplitude"]
        f = kw["frequency"]
        if val <= 0 or f <= 0 or vp <= 0:
            raise ValueError("values must be > 0")
        w = 2 * np.pi * f
        x = -1 / (w * val) if cap else w * val          # signed reactance
        z = complex(r, x)
        zmag = abs(z)
        phi_z = np.angle(z)                               # voltage leads current by phi_z
        ip = vp / zmag
        tt = np.linspace(0, 2 / f, 1000)
        v = vp * np.sin(w * tt)
        i = ip * np.sin(w * tt - phi_z)
        p = v * i
        tf, tp = eng_scale(tt)
        cf, cp = eng_scale(i)
        fig = self.chart.fig
        fig.clear()
        gs = fig.add_gridspec(2, 2, width_ratios=[1.6, 1], hspace=0.55, wspace=0.35)
        ax = fig.add_subplot(gs[0, 0])
        ax.set_facecolor(PLOT_BG)
        ax.plot(tt / tf, v, color=V_COLOR, lw=2, label="v(t)")
        ax.set_ylabel("V", color=V_COLOR)
        ax2 = ax.twinx()
        ax2.plot(tt / tf, i / cf, color=I_COLOR, lw=2, ls="--", label="i(t)")
        ax2.set_ylabel(f"{cp}A", color=I_COLOR)
        align_zero_axes(ax, ax2)
        ax.axhline(0, color="#333", lw=1)
        # mark the time shift between the voltage peak and the current peak
        t_vpk = 0.25 / f
        t_ipk = t_vpk + phi_z / w
        if t_ipk < 0:
            t_ipk += 1 / f
        ax.axvline(t_vpk / tf, color=V_COLOR, lw=0.8, ls=":")
        ax2.axvline(t_ipk / tf, color=I_COLOR, lw=0.8, ls=":")
        y_mark = vp * 1.08
        ax.annotate("", xy=(t_ipk / tf, y_mark), xytext=(t_vpk / tf, y_mark),
                    arrowprops=dict(arrowstyle="<->", color="#6A4C93"))
        lead = t("chart.i_leads") if phi_z < 0 else (t("chart.i_lags") if phi_z > 0 else "")
        ax.text(max(t_vpk, t_ipk) / tf + 0.02 * tt[-1] / tf, y_mark, f"Δφ = {abs(np.degrees(phi_z)):.1f}°  {lead}",
                ha="left", va="center", fontsize=8, color="#6A4C93",
                bbox=dict(boxstyle="round,pad=0.15", fc="white", ec="none", alpha=0.8))
        ax.set_ylim(-vp * 1.3, vp * 1.35)
        ax.set_xlabel(f"t ({tp}s)")
        ax.set_title(t("chart.ac_title"), fontsize=10)
        ax.grid(True, alpha=0.25)
        # power
        axp = fig.add_subplot(gs[1, 0])
        axp.set_facecolor(PLOT_BG)
        pf_, pp = eng_scale(p)
        axp.plot(tt / tf, p / pf_, color="#555", lw=1)
        axp.fill_between(tt / tf, p / pf_, 0, where=p >= 0, color="#2A9D8F", alpha=0.35,
                         label=t("chart.p_in"))
        axp.fill_between(tt / tf, p / pf_, 0, where=p < 0, color="#c0392b", alpha=0.35,
                         label=t("chart.p_back"))
        axp.axhline(np.mean(p) / pf_, color="#1f2a44", lw=1.2, ls="--", label=t("chart.p_avg"))
        axp.axhline(0, color="#333", lw=0.8)
        axp.set_ylabel(f"p(t) ({pp}W)")
        axp.set_xlabel(f"t ({tp}s)")
        axp.legend(fontsize=7, loc="upper center", ncol=2, bbox_to_anchor=(0.5, -0.22), frameon=False)
        axp.set_title(t("chart.power_title"), fontsize=10)
        axp.grid(True, alpha=0.25)
        # phasor diagram
        axph = fig.add_subplot(gs[0, 1])
        axph.set_facecolor(PLOT_BG)
        axph.set_aspect("equal")
        axph.set_xlim(-1.3, 1.3)
        axph.set_ylim(-1.3, 1.3)
        axph.axhline(0, color="#ccc", lw=1)
        axph.axvline(0, color="#ccc", lw=1)
        # reference: current along +x, voltages relative to it
        items = [("I", 0.0, 1.0, I_COLOR)]
        vr, vx = ip * r, ip * abs(x)
        vmax = max(vp, 1e-12)
        items.append(("V", phi_z, 1.0, V_COLOR))
        if r > 0:
            items.append(("VR", 0.0, vr / vmax, "#7a7a7a"))
            items.append(("VC" if cap else "VL", np.sign(x) * np.pi / 2, vx / vmax, "#6A4C93"))
        for lbl, ang, ln, col in items:
            xx, yy = 0.95 * ln * np.cos(ang), 0.95 * ln * np.sin(ang)
            axph.annotate("", xy=(xx, yy), xytext=(0, 0),
                          arrowprops=dict(arrowstyle="-|>", color=col, lw=2, mutation_scale=14))
            axph.text(xx * 1.15 + (0.08 if lbl == "VR" else 0), yy * 1.15 - (0.1 if lbl == "VR" else 0), lbl,
                      color=col, fontsize=9, fontweight="bold", ha="center", va="center")
        axph.set_xticks([])
        axph.set_yticks([])
        axph.set_title(t("chart.phasor_title"), fontsize=10)
        # reactance vs frequency
        axz = fig.add_subplot(gs[1, 1])
        axz.set_facecolor(PLOT_BG)
        fs = np.logspace(np.log10(f) - 2, np.log10(f) + 2, 200)
        xs = 1 / (2 * np.pi * fs * val) if cap else 2 * np.pi * fs * val
        axz.loglog(fs, xs, color=self.accent, lw=2, label=("Xc" if cap else "XL"))
        if r > 0:
            axz.loglog(fs, np.sqrt(r * r + xs * xs), color="#555", lw=1.2, ls="--", label="|Z|")
            axz.axhline(r, color="#999", lw=0.8, ls=":")
        axz.plot([f], [abs(x)], "o", color="#d97706", ms=7)
        axz.set_xlabel("f (Hz)")
        axz.set_ylabel("Ω")
        axz.legend(fontsize=7)
        axz.set_title(t("chart.reactance_title"), fontsize=10)
        axz.grid(True, which="both", alpha=0.2)
        fig.subplots_adjust(left=0.1, right=0.93, top=0.93, bottom=0.16, hspace=0.55)
        self.chart.redraw()
        # numbers
        irms = ip / np.sqrt(2)
        s_va = vp * ip / 2
        p_w = s_va * np.cos(phi_z)
        q = s_va * np.sin(phi_z)
        if abs(p_w) < 1e-9 * s_va:      # ideal reactive part: remove floating-point noise
            p_w = 0.0
        if abs(q) < 1e-9 * s_va:
            q = 0.0
        e_pk = 0.5 * val * (vx ** 2 if cap else 0) if cap else 0.5 * val * ip ** 2
        lines = [
            f"{'Xc = 1/(2πfC)' if cap else 'XL = 2πfL'} = {format_value(float(f'{abs(x):.4g}'), 'Ω')}",
            f"|Z| = √(R² + X²) = {format_value(float(f'{zmag:.4g}'), 'Ω')}",
            f"I peak = {format_value(float(f'{ip:.4g}'), 'A')}   I rms = {format_value(float(f'{irms:.4g}'), 'A')}",
            f"φ = {np.degrees(phi_z):+.1f}°   cos φ = {np.cos(phi_z):.3f}",
            f"P = {format_value(float(f'{p_w:.4g}'), 'W')}   Q = {format_value(float(f'{q:.4g}'), 'VAR')}",
            f"{t('chart.e_peak')} = {format_value(float(f'{e_pk:.4g}'), 'J')}",
        ]
        if r > 0:
            fc = 1 / (2 * np.pi * r * val) if cap else r / (2 * np.pi * val)
            lines.append(f"fc (|X| = R) = {format_value(float(f'{fc:.4g}'), 'Hz')}")
        self.note_var.set("\n".join(lines) + "\n" + (self.ac_note or ""))

    def _simulate(self):
        try:
            kwargs = {key: parse_value(var.get()) for key, var in self.field_vars.items()}
        except Exception:
            self.note_var.set(t("common.enter_valid_values"))
            return
        mode = self.mode.get()
        if mode == "AC" and self.reactive:
            try:
                self._simulate_reactive_ac(kwargs)
            except Exception as exc:
                self.note_var.set(f"{t('common.could_not_simulate')}: {exc}")
            return
        try:
            t_arr, v, i, tau, event_time = self.signal_fn(mode=mode, **kwargs)
        except Exception as exc:
            self.note_var.set(f"{t('common.could_not_simulate')}: {exc}")
            return

        self.chart.clear()
        tf, tp = eng_scale(t_arr)
        vf, vp = eng_scale(v)
        cf, cp = eng_scale(i)
        ts = np.asarray(t_arr) / tf
        ax1 = self.chart.fig.add_subplot(111)
        ax1.set_facecolor(PLOT_BG)
        l1, = ax1.plot(ts, np.asarray(v) / vf, color=V_COLOR, linewidth=2,
                       label=f"{t('chart.voltage_axis')} v(t)")
        ax1.set_xlabel(f"{t('chart.time_axis')} ({tp}s)")
        ax1.set_ylabel(f"{t('chart.voltage_axis')} ({vp}{self.v_unit})", color=V_COLOR)
        ax1.tick_params(axis="y", labelcolor=V_COLOR)

        ax2 = ax1.twinx()
        l2, = ax2.plot(ts, np.asarray(i) / cf, color=I_COLOR, linewidth=2, linestyle="--",
                       label=f"{t('chart.current_axis')} i(t)")
        ax2.set_ylabel(f"{t('chart.current_axis')} ({cp}{self.i_unit})", color=I_COLOR)
        ax2.tick_params(axis="y", labelcolor=I_COLOR)
        # Both zero lines at the same height -> one shared, clearly visible 0 axis
        align_zero_axes(ax1, ax2)
        ax1.axhline(0, color="#333", linewidth=1.1, zorder=1)
        ax1.set_xlim(ts[0], ts[-1])

        if event_time is not None:
            ev = event_time / tf
            ax1.axvspan(ts[0], ev, color="#2A9D8F", alpha=0.06, lw=0)
            ax1.axvspan(ev, ts[-1], color="#888888", alpha=0.07, lw=0)
            ax1.axvline(ev, color="#888", linestyle=":", linewidth=1.5)
            ax1.annotate(t("chart.source_removed"), xy=(ev, ax1.get_ylim()[1]),
                         xytext=(4, -4), textcoords="offset points", fontsize=7,
                         color="#666", ha="left", va="top")
        if mode == "DC" and tau is not None:
            for k in range(1, 6):
                ax1.axvline(k * tau / tf, color="#bbb", linewidth=0.6, linestyle="-", zorder=0)
            ax1.annotate("τ", xy=(tau / tf, ax1.get_ylim()[0]), xytext=(2, 2), textcoords="offset points",
                         fontsize=8, color="#666")

        ax1.grid(True, alpha=0.25)
        ax1.legend(handles=[l1, l2], loc="upper right", fontsize=8, framealpha=0.85)
        chart_title = t("chart.dc_title") if mode == "DC" else t("chart.ac_title")
        ax1.set_title(chart_title, fontsize=11)
        self.chart.fig.tight_layout()
        self.chart.redraw()

        note = self.dc_note if mode == "DC" else self.ac_note
        if mode == "DC" and tau is not None:
            note = f"{t('common.time_constant')} τ = {tau:.4g} s\n{note}"

        # Power P(t) = V(t)*I(t): computed generically from the same v/i
        # traces already produced for any component (resistor, capacitor,
        # inductor, diode, ...), so every simulator gets power information
        # without needing its own separate power formula/plot.
        try:
            p = np.asarray(v) * np.asarray(i)
            p_peak = float(np.max(np.abs(p)))
            p_avg = float(np.mean(p))
            note = (note + "\n" if note else "") + t("chart.power_note").format(
                ppeak=format_value(p_peak, "W"), pavg=format_value(p_avg, "W"))
        except Exception:
            pass

        note = (note + "\n" if note else "") + t("chart.model_assumptions")
        self.note_var.set(note)
