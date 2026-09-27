"""
rf/tline.py - Ideal lossless transmission-line model.

For an ideal lossless line of characteristic impedance Z0, physical
length `length` (metres) and velocity factor `vf` (0 < vf <= 1):

    v_p = c0 * vf                      (phase velocity)
    beta = 2*pi*f / v_p                (phase constant, rad/m)
    theta = beta * length              (electrical length, rad)

    ABCD = [[cos(theta),          j*Z0*sin(theta)],
            [j*sin(theta)/Z0,     cos(theta)      ]]

This is frequency-dependent through `theta` alone (lossless => magnitude
of transmission is always 1; only phase rotates with frequency), which is
exactly the physically-correct behaviour to verify in testing.

The line is stamped into the nodal-admittance solver as a Y-parameter
2-port (no internal extra node needed), converted from ABCD via the
standard reciprocal-network relations:

    Y11 =  D / B
    Y12 = -1 / B   (= Y21 for a reciprocal ABCD, since AD - BC = 1)
    Y21 = -1 / B
    Y22 =  A / B

Architecture is deliberately kept function-based (not a class) so that
future, more advanced line models (lossy, dispersive, coupled lines) can
be dropped in as additional functions returning the same (Y11,Y12,Y21,Y22)
tuple without touching the solver.
"""
import cmath
import math

C0 = 299_792_458.0  # speed of light, m/s


def electrical_length(f_hz, length, vf):
    if vf <= 0:
        raise ValueError("velocity factor must be > 0")
    v_p = C0 * vf
    beta = 2 * math.pi * f_hz / v_p
    return beta * length


def ideal_line_abcd(f_hz, z0, length, vf):
    theta = electrical_length(f_hz, length, vf)
    cos_t = cmath.cos(theta)
    sin_t = cmath.sin(theta)
    A = cos_t
    B = 1j * z0 * sin_t
    C = 1j * sin_t / z0
    D = cos_t
    return A, B, C, D


def ideal_line_y_params(f_hz, z0, length, vf):
    A, B, C, D = ideal_line_abcd(f_hz, z0, length, vf)
    if abs(B) < 1e-18:
        # theta -> 0 (DC / zero length): line behaves as an ideal wire.
        # Represent as a very high (but finite) shunt-free direct connection
        # by returning a very large admittance between the two nodes.
        big = 1e9
        return complex(big, 0), complex(-big, 0), complex(-big, 0), complex(big, 0)
    Y11 = D / B
    Y12 = -1.0 / B
    Y21 = -1.0 / B
    Y22 = A / B
    return Y11, Y12, Y21, Y22


def quarter_wave_length(f_hz, vf):
    """Physical length (m) that makes a line a quarter-wavelength at f_hz."""
    v_p = C0 * vf
    wavelength = v_p / f_hz
    return wavelength / 4.0


def quarter_wave_transform(z0_line, z_load):
    """Zin = Z0^2 / ZL for an ideal lossless quarter-wave line."""
    return (z0_line ** 2) / z_load
