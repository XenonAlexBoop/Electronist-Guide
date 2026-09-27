"""
rf/formats.py - Converts raw complex S-parameter data into the display
quantities a VNA channel can show. Kept separate from any GUI code so the
same conversions back the VNA, the Smith Chart, and the S-Parameter
Results table from one shared source of truth.

Only mathematically meaningful formats are offered per measurement type:
reflection (Sii) vs. transmission (Sij, i != j) - see FORMATS_FOR().
"""
import numpy as np

REFLECTION_FORMATS = [
    "log_mag", "lin_mag", "phase", "smith", "polar", "vswr", "return_loss",
]
TRANSMISSION_FORMATS = [
    "log_mag", "lin_mag", "phase", "group_delay",
]

FORMAT_LABEL_KEYS = {
    "log_mag": "rf.format.log_mag",
    "lin_mag": "rf.format.lin_mag",
    "phase": "rf.format.phase",
    "smith": "rf.format.smith",
    "polar": "rf.format.polar",
    "vswr": "rf.format.vswr",
    "return_loss": "rf.format.return_loss",
    "group_delay": "rf.format.group_delay",
}


def formats_for(out_port, in_port):
    return REFLECTION_FORMATS if out_port == in_port else TRANSMISSION_FORMATS


def is_reflection(out_port, in_port):
    return out_port == in_port


def log_mag_db(s):
    mag = np.maximum(np.abs(s), 1e-15)
    return 20 * np.log10(mag)


def lin_mag(s):
    return np.abs(s)


def phase_deg(s):
    return np.angle(s, deg=True)


def vswr(s):
    mag = np.clip(np.abs(s), 0, 0.999999)
    return (1 + mag) / (1 - mag)


def return_loss_db(s):
    mag = np.maximum(np.abs(s), 1e-15)
    return -20 * np.log10(mag)


def group_delay_s(s, freqs_hz):
    """Group delay = -d(phase)/d(omega), via unwrapped phase & central
    differences over the (already-computed) sweep - does not re-run the
    solver, only differentiates already-cached data."""
    phase = np.unwrap(np.angle(s))
    omega = 2 * np.pi * freqs_hz
    if len(freqs_hz) < 2:
        return np.zeros_like(phase)
    return -np.gradient(phase, omega)


def compute(fmt, s, freqs_hz=None):
    """s: complex array (a trace) or a single complex value."""
    if fmt == "log_mag":
        return log_mag_db(s)
    if fmt == "lin_mag":
        return lin_mag(s)
    if fmt == "phase":
        return phase_deg(s)
    if fmt in ("smith", "polar"):
        return s  # complex, plotted directly
    if fmt == "vswr":
        return vswr(s)
    if fmt == "return_loss":
        return return_loss_db(s)
    if fmt == "group_delay":
        return group_delay_s(s, freqs_hz)
    raise ValueError(f"unknown format {fmt}")


def y_axis_label_key(fmt):
    return {
        "log_mag": "rf.axis.db",
        "lin_mag": "rf.axis.linear",
        "phase": "rf.axis.deg",
        "vswr": "rf.axis.vswr",
        "return_loss": "rf.axis.db",
        "group_delay": "rf.axis.ns",
    }.get(fmt, "")
