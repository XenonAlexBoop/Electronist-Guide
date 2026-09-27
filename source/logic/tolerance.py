"""
logic/tolerance.py - Pure-math helpers for component tolerance analysis.
No UI code here - tabs/troubleshooting.py is the presentation layer.

The core idea is `stackup_worst_case()`: instead of hand-deriving a
min/max formula for every possible combination (series sum, parallel
combo, a voltage-divider ratio, ...), it numerically probes how the
result changes as each component is nudged, and uses that to know
*which* extreme (min or max) of each component pushes the result up vs.
down. This matters because it's not always the same direction: e.g. for
a divider ratio R2/(R1+R2), increasing R1 pushes the ratio DOWN while
increasing R2 pushes it UP, so "plug in everything at its max" does not
give you the maximum ratio. Naive percentage-adding gets this wrong;
this doesn't.
"""
import math

# Common standard tolerance grades (%) found on real components.
STANDARD_TOLERANCES = [0.1, 0.25, 0.5, 1, 2, 5, 10, 20]


def component_range(nominal, tolerance_pct):
    """(lo, hi) for a single component given a +/- tolerance in percent."""
    delta = abs(nominal) * (tolerance_pct / 100.0)
    return nominal - delta, nominal + delta


def stackup_worst_case(f, components):
    """
    f: a function taking a list of values (same order as `components`)
       and returning a single float result.
    components: list of (nominal, tolerance_pct) tuples.

    Returns a dict:
      nominal   - f() evaluated at all nominal values
      lo, hi    - true worst-case bounds (every component can independently
                  be anywhere within its own tolerance)
      rss_lo, rss_hi - a root-sum-square statistical estimate, i.e. the
                  band you'd expect if each component's error is an
                  independent random variable rather than everything
                  drifting to its worst case simultaneously. This is
                  usually a tighter, more realistic band, but it is NOT a
                  guarantee the way worst-case is.
    """
    nominals = [c[0] for c in components]
    tols = [c[1] for c in components]
    deltas = [abs(n) * (tp / 100.0) for n, tp in zip(nominals, tols)]

    nominal_result = f(nominals)

    lo_vals, hi_vals = list(nominals), list(nominals)
    sensitivities = []
    for i in range(len(components)):
        step = deltas[i] if deltas[i] != 0 else max(abs(nominals[i]), 1.0) * 1e-6
        probe = list(nominals)
        probe[i] = nominals[i] + step
        slope = (f(probe) - nominal_result) / step
        sensitivities.append(slope)
        if slope >= 0:
            lo_vals[i] = nominals[i] - deltas[i]
            hi_vals[i] = nominals[i] + deltas[i]
        else:
            lo_vals[i] = nominals[i] + deltas[i]
            hi_vals[i] = nominals[i] - deltas[i]

    lo = f(lo_vals)
    hi = f(hi_vals)
    if lo > hi:
        lo, hi = hi, lo

    rss_delta = math.sqrt(sum((s * d) ** 2 for s, d in zip(sensitivities, deltas)))

    return {
        "nominal": nominal_result,
        "lo": lo, "hi": hi,
        "rss_lo": nominal_result - rss_delta, "rss_hi": nominal_result + rss_delta,
    }


# ---------------------------------------------------------------------------
# Convenience combination functions + wrappers for the common cases the
# Troubleshooting tab offers.
# ---------------------------------------------------------------------------
def series_sum(values):
    return sum(values)


def parallel_combo(values):
    if any(v == 0 for v in values):
        raise ValueError("a value of 0 is not valid in a parallel combination")
    return 1.0 / sum(1.0 / v for v in values)


def divider_ratio(values):
    r1, r2 = values
    if r1 + r2 == 0:
        raise ValueError("R1 + R2 cannot be 0")
    return r2 / (r1 + r2)


def series_stackup(components):
    return stackup_worst_case(series_sum, components)


def parallel_stackup(components):
    return stackup_worst_case(parallel_combo, components)


def divider_stackup(r1, r1_tol, r2, r2_tol):
    return stackup_worst_case(divider_ratio, [(r1, r1_tol), (r2, r2_tol)])


def divider_voltage_stackup(r1, r1_tol, r2, r2_tol, vsupply, vsupply_tol=0.0):
    """Same idea, extended to the actual node voltage: ratio x Vsupply,
    with Vsupply optionally carrying its own tolerance/ripple too."""
    def f(vals):
        _r1, _r2, _v = vals
        return (_r2 / (_r1 + _r2)) * _v
    return stackup_worst_case(f, [(r1, r1_tol), (r2, r2_tol), (vsupply, vsupply_tol)])


# ---------------------------------------------------------------------------
# ICT Debug Helper - simple threshold-based classification. This is a
# heuristic teaching aid ("does this measurement look plausible, and if
# not, which family of fault does it look like"), not a real diagnostic
# algorithm - see the UI copy in tabs/troubleshooting.py for the caveat
# shown to the user.
# ---------------------------------------------------------------------------
def classify_resistance(expected_lo, expected_hi, expected_nominal, measured):
    short_threshold = max(expected_nominal * 0.02, 1.0)
    open_threshold = max(expected_hi * 5, expected_nominal * 5)
    if measured <= short_threshold:
        return "short"
    if measured >= open_threshold:
        return "open"
    if expected_lo <= measured <= expected_hi:
        return "ok"
    return "check"


def classify_voltage(expected_lo, expected_hi, vsupply, measured):
    if expected_lo <= measured <= expected_hi:
        return "ok"
    if vsupply > 0 and measured >= vsupply * 0.9:
        return "pulled_high"
    if vsupply > 0 and measured <= vsupply * 0.1:
        return "pulled_low"
    return "check"
