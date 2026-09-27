"""
rf/simstate.py - The single shared simulation result.

Exactly one CircuitModel, one frequency sweep and one resulting
S-parameter dataset are kept here. The Circuit Builder, Virtual VNA,
Smith Chart and S-Parameter Results views all read from this same
object - there is no per-view re-simulation.

Cache invalidation rule (deliberately explicit, not "recompute on every
read"): the cached `SimResult` stays valid across display-only changes
(selected measurement, display format, marker position, which trace is
visible). It is only thrown away and recomputed when `simulate()` is
called again, which the GUI only does in response to a real topology /
value / sweep-setting change followed by pressing SIMULATE.
"""
import hashlib
import numpy as np

from rf.model import CircuitModel
from rf.solver import solve_sweep


class SimResult:
    def __init__(self, port_numbers, z0_by_port, freqs_hz, S):
        self.port_numbers = port_numbers      # e.g. [1, 2, 3]
        self.z0_by_port = z0_by_port          # {port_number: complex Z0}
        self.freqs_hz = freqs_hz              # np.array
        self.S = S                            # complex np.array (nF, nP, nP)

    def n_ports(self):
        return len(self.port_numbers)

    def nearest_index(self, f_hz):
        return int(np.argmin(np.abs(self.freqs_hz - f_hz)))

    def s_trace(self, out_port, in_port):
        """Complex S_out,in trace across the whole sweep."""
        i = self.port_numbers.index(out_port)
        j = self.port_numbers.index(in_port)
        return self.S[:, i, j]

    def s_at(self, out_port, in_port, index):
        i = self.port_numbers.index(out_port)
        j = self.port_numbers.index(in_port)
        return self.S[index, i, j]


class SimulationState:
    """Owns the circuit model, sweep settings, cached result, and notifies
    listeners only when a *new* simulation result is produced."""

    def __init__(self):
        self.circuit = CircuitModel()
        self.sweep = {"f_start": 1e9, "f_stop": 3e9, "n_points": 201}
        self.result = None          # last SimResult, or None
        self._listeners = []
        self._last_error = None

    def on_result(self, callback):
        self._listeners.append(callback)

    def _notify(self):
        for cb in list(self._listeners):
            cb(self.result)

    def last_error(self):
        return self._last_error

    def validate_sweep(self):
        f_start = self.sweep["f_start"]
        f_stop = self.sweep["f_stop"]
        n_points = self.sweep["n_points"]
        if f_start <= 0:
            raise ValueError("Start Frequency must be greater than 0.")
        if f_stop <= f_start:
            raise ValueError("Stop Frequency must be greater than Start Frequency.")
        if n_points < 2:
            raise ValueError("Number of Points must be at least 2.")
        if n_points > 20000:
            raise ValueError("Number of Points is too large (max 20000).")

    def simulate(self):
        """Validate + solve. Raises ValueError with a user-facing message
        on any problem; otherwise stores a fresh SimResult and notifies
        listeners."""
        self._last_error = None
        self.circuit.validate_values()
        self.validate_sweep()
        netlist = self.circuit.build_netlist()

        freqs = np.linspace(self.sweep["f_start"], self.sweep["f_stop"],
                             int(self.sweep["n_points"]))
        port_numbers, S = solve_sweep(netlist, freqs)
        z0_by_port = {p: netlist.port_nodes[p][1] for p in port_numbers}
        self.result = SimResult(port_numbers, z0_by_port, freqs, S)
        self._notify()
        return self.result

    def circuit_fingerprint(self):
        """A cheap hash of everything that should invalidate the cache,
        used only for an on-screen 'circuit changed since last simulate'
        indicator - the cache itself is only ever replaced by an explicit
        simulate() call, never silently on a read."""
        parts = []
        for w in self.circuit.wires:
            parts.append(("W", w))
        for c in self.circuit.components:
            parts.append((c.kind, c.p1, c.p2, tuple(sorted(c.params.items()))))
        parts.append(tuple(sorted(self.circuit.grounds)))
        parts.append(tuple(sorted(self.sweep.items())))
        digest = hashlib.sha1(repr(parts).encode("utf-8")).hexdigest()
        return digest
