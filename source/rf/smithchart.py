"""
rf/smithchart.py - A real, programmatically generated Smith chart.

Draws the constant-resistance / constant-reactance (impedance) or
constant-conductance / constant-susceptance (admittance) grid circles on
a matplotlib Axes, plus complex reflection-coefficient traces and
frequency markers. No static image is ever used.

Gamma = (Z - Z0) / (Z + Z0)           reflection coefficient
z     = Z / Z0                         normalized impedance
y     = 1 / z                          normalized admittance
"""
import numpy as np

RESISTANCE_RINGS = [0, 0.2, 0.5, 1, 2, 5]
REACTANCE_ARCS = [0.2, 0.5, 1, 2, 5]

GRID_COLOR = "#3a4256"
AXIS_COLOR = "#5a6482"
BG_COLOR = "#10141f"
TRACE_COLORS = ["#4fd1c5", "#f6ad55", "#fc8181", "#63b3ed"]


def _r_circle(r, n=200):
    """Constant-resistance (or conductance) circle in the Gamma plane."""
    cx = r / (r + 1)
    rad = 1 / (r + 1)
    th = np.linspace(0, 2 * np.pi, n)
    return cx + rad * np.cos(th), rad * np.sin(th)


def _x_arc(x, n=200):
    """Constant-reactance (or susceptance) arc in the Gamma plane."""
    if x == 0:
        th = np.linspace(0, 0, 1)
        return np.array([1.0]), np.array([0.0])
    cy = 1 / x
    rad = 1 / abs(x)
    # Standard formula: circle centered at (1, 1/x) with radius 1/x, but
    # only the portion inside the unit circle is physically valid.
    cx = 1.0
    gx = cx + rad * np.cos(np.linspace(0, 2 * np.pi, n))
    gy = cy + rad * np.sin(np.linspace(0, 2 * np.pi, n))
    mask = gx ** 2 + gy ** 2 <= 1.0 + 1e-9
    return gx[mask], gy[mask]


def draw_grid(ax, mode="impedance"):
    """mode: 'impedance' or 'admittance'. Admittance mode simply mirrors
    the same grid (z and y grids are geometrically identical circles;
    only the interpretation of which physical quantity each ring
    represents changes) about the origin, matching standard Z/Y Smith
    chart practice."""
    ax.clear()
    ax.set_facecolor(BG_COLOR)
    ax.set_aspect("equal")
    ax.set_xlim(-1.12, 1.12)
    ax.set_ylim(-1.12, 1.12)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)

    sign = 1.0 if mode == "impedance" else -1.0

    outer_th = np.linspace(0, 2 * np.pi, 400)
    ax.plot(np.cos(outer_th), np.sin(outer_th), color=AXIS_COLOR, linewidth=1.4, zorder=2)
    ax.plot([-1, 1], [0, 0], color=AXIS_COLOR, linewidth=1.0, zorder=2)

    for r in RESISTANCE_RINGS:
        gx, gy = _r_circle(r)
        ax.plot(sign * gx, gy, color=GRID_COLOR, linewidth=0.8, zorder=1)

    for x in REACTANCE_ARCS:
        for sgn in (1, -1):
            gx, gy = _x_arc(sgn * x)
            if len(gx) < 2:
                continue
            ax.plot(sign * gx, gy, color=GRID_COLOR, linewidth=0.8, zorder=1)


def plot_trace(ax, gamma, color, label=None, linewidth=1.6):
    ax.plot(gamma.real, gamma.imag, color=color, linewidth=linewidth, label=label, zorder=3)


def plot_marker(ax, gamma_point, color, text=None):
    ax.plot([gamma_point.real], [gamma_point.imag], marker="o", markersize=6,
             markerfacecolor=color, markeredgecolor="white", markeredgewidth=1.0, zorder=5)
    if text:
        ax.annotate(text, (gamma_point.real, gamma_point.imag),
                    xytext=(8, 8), textcoords="offset points",
                    color=color, fontsize=8, fontweight="bold", zorder=6)


def z_to_gamma(z, z0):
    return (z - z0) / (z + z0)


def gamma_to_z(gamma, z0):
    if abs(1 - gamma) < 1e-15:
        return complex(1e12, 0.0)
    return z0 * (1 + gamma) / (1 - gamma)
