"""
rf/solver.py - General N-port network solver.

Method (nodal analysis, NOT a fixed cascaded-ABCD chain, so branches,
junctions and arbitrary connected topologies are all supported):

  1. Every electrical node (except ground) gets one row/column of a
     complex nodal-admittance matrix Y, at each sweep frequency.
  2. Two-terminal lumped components (R, L, C) stamp a simple +-y / -y
     admittance between their two nodes. Transmission lines stamp their
     full reciprocal 2-port Y-parameters between their two nodes. Loads
     stamp a shunt admittance from their node to ground.
  3. Each port is represented as its Norton-equivalent excitation: a
     shunt admittance 1/Z0 (the port termination) plus, only for the port
     currently being driven, a current source corresponding to an
     incident power wave a = 1 (all other ports have a = 0, i.e. they are
     simply terminated in their own reference impedance - exactly what a
     real VNA does with its non-driven ports).
  4. Solve Y*V = I for the node voltages, once per port being driven,
     per frequency point.
  5. Extract b_q = V_q / sqrt(Z0_q) - a_q for every port q. Column k of
     the S-matrix (port k driven) is exactly this vector of b_q values.

This is the standard nodal-analysis / MNA technique for extracting
S-parameters from a linear network and is fully general: it makes no
assumption that the network is a simple 2-port cascade.
"""
import numpy as np


def solve_sweep(netlist, freqs_hz):
    """Returns (port_numbers, S) where S has shape (n_freqs, n_ports, n_ports)."""
    port_numbers = netlist.sorted_port_numbers()
    n_ports = len(port_numbers)

    # Assign each non-ground node a matrix row/col index.
    node_ids = set()
    for _kind, n1, n2, _fn in netlist.edges:
        node_ids.add(n1)
        node_ids.add(n2)
    for n, _fn in netlist.shunt_edges:
        node_ids.add(n)
    for pnum in port_numbers:
        n, _z0 = netlist.port_nodes[pnum]
        node_ids.add(n)
    node_ids.discard("GND")
    node_list = sorted(node_ids)
    index = {n: i for i, n in enumerate(node_list)}
    size = len(node_list)
    if size == 0:
        raise ValueError("The circuit has no valid nodes to solve.")

    S = np.zeros((len(freqs_hz), n_ports, n_ports), dtype=complex)

    for fi, f in enumerate(freqs_hz):
        Y = np.zeros((size, size), dtype=complex)

        for kind, n1, n2, fn in netlist.edges:
            i1 = index.get(n1)
            i2 = index.get(n2)
            if kind == "Y":
                y = fn(f)
                if i1 is not None:
                    Y[i1, i1] += y
                if i2 is not None:
                    Y[i2, i2] += y
                if i1 is not None and i2 is not None:
                    Y[i1, i2] -= y
                    Y[i2, i1] -= y
            else:  # "TL" - full reciprocal 2-port Y-parameters
                y11, y12, y21, y22 = fn(f)
                if i1 is not None:
                    Y[i1, i1] += y11
                if i2 is not None:
                    Y[i2, i2] += y22
                if i1 is not None and i2 is not None:
                    Y[i1, i2] += y12
                    Y[i2, i1] += y21

        for n, fn in netlist.shunt_edges:
            i = index.get(n)
            if i is not None:
                Y[i, i] += fn(f)

        port_index = {}
        z0_of = {}
        for pnum in port_numbers:
            n, z0 = netlist.port_nodes[pnum]
            i = index[n]
            port_index[pnum] = i
            z0_of[pnum] = z0
            Y[i, i] += 1.0 / z0  # port termination admittance

        try:
            Y_factored = np.linalg.inv(Y)
        except np.linalg.LinAlgError as exc:
            raise ValueError(
                "The circuit is not solvable at this frequency (singular network - "
                "check for floating nodes or missing return path to ground)."
            ) from exc

        for kcol, pk in enumerate(port_numbers):
            I = np.zeros(size, dtype=complex)
            z0k = z0_of[pk]
            e_k = 2.0 * np.sqrt(z0k)         # source drive for a_k = 1
            I[port_index[pk]] += e_k / z0k
            V = Y_factored @ I

            for qrow, pq in enumerate(port_numbers):
                z0q = z0_of[pq]
                a_q = 1.0 if pq == pk else 0.0
                Vq = V[port_index[pq]]
                b_q = Vq / np.sqrt(z0q) - a_q
                S[fi, qrow, kcol] = b_q

    return port_numbers, S
