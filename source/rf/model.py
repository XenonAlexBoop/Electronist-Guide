"""
rf/model.py - The RF circuit data model.

The schematic is stored as a simple graph/netlist, not a fixed
Port-1 -> components -> Port-2 chain:

  - Every component lives on an integer grid. Its terminal(s) are grid
    points (x, y).
  - A `Wire` directly joins two grid points into the SAME electrical node
    (zero impedance).
  - Two-terminal components (R, L, C, transmission line) are edges in the
    impedance graph between the electrical nodes their endpoints resolve to.
  - One-terminal components (loads, grounds) tie a node to the reference
    (ground) node.
  - Ports mark a node as an external port with its own reference impedance.

Electrical nodes are derived with union-find over the *wires* only, so
branches, junctions (three or more wires/components meeting at one grid
point) and arbitrary connected topologies all fall out naturally instead
of being special-cased.
"""
import math


GROUND = "GND"

# Component "families"
TWO_TERMINAL = {"R", "L", "C", "TL"}
ONE_TERMINAL = {"LOAD_MATCHED", "LOAD_R", "LOAD_Z", "OPEN", "SHORT"}
PORT = "PORT"


class Component:
    """A single placed schematic element.

    p1, p2: grid coordinates, (x, y) tuples. p2 is None for one-terminal
    elements (loads) and for ports (a port's "return" is the implicit
    reference/ground plane, consistent with the ground-referenced nodal
    solver).
    """

    _next_id = 1

    def __init__(self, kind, p1, p2=None, params=None, orientation=0):
        self.id = Component._next_id
        Component._next_id += 1
        self.kind = kind
        self.p1 = p1
        self.p2 = p2
        self.params = dict(params or {})
        self.orientation = orientation  # 0 or 90 (degrees), display only

    def label(self):
        if self.kind == "R":
            return f"R{self.id}"
        if self.kind == "L":
            return f"L{self.id}"
        if self.kind == "C":
            return f"C{self.id}"
        if self.kind == "TL":
            return f"TL{self.id}"
        if self.kind == PORT:
            return f"P{self.params.get('number', '?')}"
        if self.kind == "LOAD_MATCHED":
            return "Z0"
        if self.kind == "LOAD_R":
            return f"RL{self.id}"
        if self.kind == "LOAD_Z":
            return f"ZL{self.id}"
        if self.kind == "OPEN":
            return "OPEN"
        if self.kind == "SHORT":
            return "SHORT"
        return self.kind


class CircuitModel:
    """The whole schematic: wires, components, grounds."""

    def __init__(self):
        self.wires = []        # list of (p1, p2)
        self.components = []   # list of Component (grounds are "GND" components)
        self.default_z0 = 50.0

    # -- editing -----------------------------------------------------
    def add_wire(self, p1, p2):
        if p1 == p2:
            return
        self.wires.append((tuple(p1), tuple(p2)))

    def add_component(self, comp):
        self.components.append(comp)
        return comp

    def add_ground(self, p):
        """Grounds are ordinary one-terminal components (kind 'GND'), so
        they can be selected, moved and deleted exactly like any other
        component - see canvas_builder.py."""
        comp = Component("GND", tuple(p))
        return self.add_component(comp)

    def remove(self, obj):
        if obj in self.components:
            self.components.remove(obj)
        elif obj in self.wires:
            self.wires.remove(obj)

    def clear(self):
        self.wires.clear()
        self.components.clear()

    def ports(self):
        return [c for c in self.components if c.kind == PORT]

    # -- node resolution (union-find over wires) ----------------------
    def _resolve_nodes(self):
        """Returns (node_of(point) -> node_id string, all points touched)."""
        parent = {}

        def find(x):
            parent.setdefault(x, x)
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra != rb:
                parent[ra] = rb

        points = set()
        for a, b in self.wires:
            points.add(a)
            points.add(b)
            union(a, b)
        for c in self.components:
            if c.p1 is not None:
                points.add(c.p1)
                find(c.p1)
            if c.p2 is not None:
                points.add(c.p2)
                find(c.p2)
        gnd_points = [c.p1 for c in self.components if c.kind == "GND"]
        for g in gnd_points:
            points.add(g)
            find(g)

        # merge every grounded point into one group
        gnd_list = gnd_points
        for g in gnd_list[1:]:
            union(g, gnd_list[0])

        node_of = {}
        next_id = [1]
        group_to_node = {}
        for p in points:
            root = find(p)
            if gnd_list and find(gnd_list[0]) == root:
                node_of[p] = GROUND
                continue
            if root not in group_to_node:
                group_to_node[root] = f"N{next_id[0]}"
                next_id[0] += 1
            node_of[p] = group_to_node[root]
        return node_of

    def build_netlist(self):
        """Resolve the schematic into a Netlist ready for the solver.

        Raises ValueError with a human-readable message on invalid/
        incomplete circuits.
        """
        if not self.components:
            raise ValueError("The circuit is empty. Place at least one port and one component.")

        node_of = self._resolve_nodes()

        ports_by_number = {}
        edges = []          # (node_a, node_b, admittance_fn(freq_hz) -> complex siemens)
        shunt_edges = []    # (node, admittance_fn(freq_hz))
        port_nodes = {}     # port number -> (node, z0)

        for c in self.components:
            if c.kind == "GND":
                continue  # already folded into the ground node by _resolve_nodes()

            if c.kind == PORT:
                if not c.params.get("enabled", True):
                    continue
                number = int(c.params.get("number", 0))
                if number < 1 or number > 4:
                    raise ValueError(f"Port number must be 1-4 (got {number}).")
                if number in ports_by_number:
                    raise ValueError(f"Port {number} is placed more than once.")
                node = node_of.get(c.p1)
                if node is None:
                    raise ValueError(f"Port {number} is not connected to the circuit.")
                if node == GROUND:
                    raise ValueError(f"Port {number} is shorted directly to ground.")
                z0 = c.params.get("z0", self.default_z0)
                if z0 is None or z0 <= 0:
                    raise ValueError(f"Port {number} has an invalid reference impedance.")
                ports_by_number[number] = c
                port_nodes[number] = (node, complex(z0))
                continue

            n1 = node_of.get(c.p1)
            if n1 is None:
                raise ValueError(f"{c.label()} is not connected to the circuit.")

            if c.kind in ONE_TERMINAL:
                shunt_edges.append((n1, _one_terminal_admittance(c)))
                continue

            if c.kind in TWO_TERMINAL:
                n2 = node_of.get(c.p2)
                if n2 is None:
                    raise ValueError(f"{c.label()} has an unconnected terminal.")
                if n1 == n2:
                    raise ValueError(f"{c.label()} has both terminals on the same node (short).")
                if c.kind == "TL":
                    edges.append(("TL", n1, n2, _tline_stamp(c)))
                else:
                    edges.append(("Y", n1, n2, _lumped_admittance(c)))
                continue

            raise ValueError(f"Unknown component type '{c.kind}'.")

        if not port_nodes:
            raise ValueError("No enabled ports found. Place at least one RF port on the circuit.")

        # topology sanity: every port node must be reachable from at least
        # one component/wire connection into the rest of the network
        # (otherwise the "network" the port sees is trivially open/floating,
        # which is allowed - the solver will simply report |S|=1 - but we
        # still want a real, non-empty network to exist).
        return Netlist(node_of, edges, shunt_edges, port_nodes)

    def validate_values(self):
        """Raise ValueError for physically invalid component values."""
        for c in self.components:
            if c.kind == "R" and c.params.get("value", 0) < 0:
                raise ValueError(f"{c.label()}: resistance cannot be negative.")
            if c.kind == "L" and c.params.get("value", 0) < 0:
                raise ValueError(f"{c.label()}: inductance cannot be negative.")
            if c.kind == "C" and c.params.get("value", 0) <= 0:
                raise ValueError(f"{c.label()}: capacitance must be greater than zero.")
            if c.kind == "TL":
                if c.params.get("z0", 50) <= 0:
                    raise ValueError(f"{c.label()}: characteristic impedance must be > 0.")
                if c.params.get("length", 0) <= 0:
                    raise ValueError(f"{c.label()}: physical length must be > 0.")
                vf = c.params.get("vf", 1.0)
                if not (0 < vf <= 1.0):
                    raise ValueError(f"{c.label()}: velocity factor must be in (0, 1].")
            if c.kind == "LOAD_R" and c.params.get("value", 0) < 0:
                raise ValueError(f"{c.label()}: load resistance cannot be negative.")


class Netlist:
    """Resolved, solver-ready representation of a CircuitModel."""

    def __init__(self, node_of, edges, shunt_edges, port_nodes):
        self.node_of = node_of
        self.edges = edges              # 2-terminal edges (R/L/C or TL)
        self.shunt_edges = shunt_edges  # node -> ground admittance (loads)
        self.port_nodes = port_nodes    # port number -> (node, z0)

    def port_count(self):
        return len(self.port_nodes)

    def sorted_port_numbers(self):
        return sorted(self.port_nodes.keys())


# ---------------------------------------------------------------------
# Per-component frequency-dependent admittance / stamp builders
# ---------------------------------------------------------------------
def _lumped_admittance(c):
    kind = c.kind
    value = c.params.get("value", 0.0)

    def fn(f_hz):
        w = 2 * math.pi * f_hz
        if kind == "R":
            z = complex(value, 0.0)
        elif kind == "L":
            z = complex(0.0, w * value) if w > 0 else complex(1e-15, 0.0)
            if value == 0:
                z = complex(1e-12, 0.0)  # ideal wire; avoid /0
        elif kind == "C":
            if value <= 0 or w == 0:
                return complex(0.0, 0.0)  # open at DC / invalid
            z = complex(0.0, -1.0 / (w * value))
        else:
            raise ValueError(f"unsupported lumped kind {kind}")
        if z == 0:
            z = complex(1e-12, 0.0)
        return 1.0 / z

    return fn


def _one_terminal_admittance(c):
    kind = c.kind

    def fn(f_hz):
        if kind == "LOAD_MATCHED":
            z0 = c.params.get("z0", c.params.get("_default_z0", 50.0))
            return 1.0 / complex(z0, 0.0)
        if kind == "LOAD_R":
            r = c.params.get("value", 50.0)
            if r <= 0:
                r = 1e-9
            return 1.0 / complex(r, 0.0)
        if kind == "LOAD_Z":
            r = c.params.get("r", 50.0)
            x = c.params.get("x", 0.0)
            z = complex(r, x)
            if z == 0:
                z = complex(1e-12, 0.0)
            return 1.0 / z
        if kind == "OPEN":
            return complex(1e-12, 0.0)  # ~0 S
        if kind == "SHORT":
            return complex(1e9, 0.0)    # ~ideal short
        raise ValueError(f"unsupported one-terminal kind {kind}")

    return fn


def _tline_stamp(c):
    """Returns fn(f_hz) -> (Y11, Y12, Y21, Y22) for an ideal lossless line."""
    from rf.tline import ideal_line_y_params
    z0 = c.params.get("z0", 50.0)
    length = c.params.get("length", 0.0)
    vf = c.params.get("vf", 1.0)

    def fn(f_hz):
        return ideal_line_y_params(f_hz, z0, length, vf)

    return fn
