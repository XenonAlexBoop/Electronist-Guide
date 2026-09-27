"""
logic/circuit_model.py - The data model behind the Logic Circuit Builder.

Unlike the RF circuit model (continuous, frequency-swept), this is a
discrete combinational-logic model: components have named input/output
pins, wires connect one output pin to one input pin, and the whole
circuit is evaluated by a topological pass (Kahn's algorithm) each time
something changes - cheap enough to redo on every click, which is what
gives the "real time" propagation the builder shows.

An unconnected input pin is *floating* (value None), not silently 0 -
gates propagate None through as None so an incomplete circuit reads as
"unknown", never as a misleadingly confident 0 or 1.
"""

# Every placeable kind's fixed pin layout: (input pin names, output pin names).
PIN_SPECS = {
    "INPUT": ([], ["Y"]),
    "OUTPUT": (["A"], []),
    "NODE": (["A"], ["Y"]),
    "NOT": (["A"], ["Y"]),
    "AND": (["A", "B"], ["Y"]),
    "OR": (["A", "B"], ["Y"]),
    "NAND": (["A", "B"], ["Y"]),
    "NOR": (["A", "B"], ["Y"]),
    "XOR": (["A", "B"], ["Y"]),
    "XNOR": (["A", "B"], ["Y"]),
    "MUX2": (["I0", "I1", "S"], ["Y"]),
    "MUX4": (["I0", "I1", "I2", "I3", "S0", "S1"], ["Y"]),
    "DEMUX2": (["D", "S"], ["O0", "O1"]),
    "DEMUX4": (["D", "S0", "S1"], ["O0", "O1", "O2", "O3"]),
}

GATE_KINDS = ("NOT", "AND", "OR", "NAND", "NOR", "XOR", "XNOR")
MUX_DEMUX_KINDS = ("MUX2", "MUX4", "DEMUX2", "DEMUX4")


def _b(v):
    """AND/OR-style combine helper: None is 'unknown', propagates through."""
    return v


def evaluate_component(kind, ins):
    """ins: dict pin_name -> 0/1/None. Returns dict pin_name -> 0/1/None
    for every OUTPUT pin of this kind."""
    def g(name):
        return ins.get(name)

    if kind == "NODE":
        return {"Y": g("A")}

    if kind == "NOT":
        a = g("A")
        return {"Y": None if a is None else 1 - a}

    if kind in ("AND", "NAND"):
        a, b = g("A"), g("B")
        if a == 0 or b == 0:
            y = 0
        elif a is None or b is None:
            y = None
        else:
            y = 1 if (a and b) else 0
        if kind == "NAND" and y is not None:
            y = 1 - y
        return {"Y": y}

    if kind in ("OR", "NOR"):
        a, b = g("A"), g("B")
        if a == 1 or b == 1:
            y = 1
        elif a is None or b is None:
            y = None
        else:
            y = 1 if (a or b) else 0
        if kind == "NOR" and y is not None:
            y = 1 - y
        return {"Y": y}

    if kind in ("XOR", "XNOR"):
        a, b = g("A"), g("B")
        if a is None or b is None:
            y = None
        else:
            y = a ^ b
            if kind == "XNOR":
                y = 1 - y
        return {"Y": y}

    if kind == "MUX2":
        s = g("S")
        if s is None:
            return {"Y": None}
        return {"Y": g("I1") if s else g("I0")}

    if kind == "MUX4":
        s0, s1 = g("S0"), g("S1")
        if s0 is None or s1 is None:
            return {"Y": None}
        idx = (s1 << 1) | s0
        return {"Y": g(f"I{idx}")}

    if kind == "DEMUX2":
        s = g("S")
        d = g("D")
        if s is None:
            return {"O0": None, "O1": None}
        return {"O0": (d if s == 0 else 0), "O1": (d if s == 1 else 0)}

    if kind == "DEMUX4":
        s0, s1 = g("S0"), g("S1")
        d = g("D")
        if s0 is None or s1 is None:
            return {"O0": None, "O1": None, "O2": None, "O3": None}
        idx = (s1 << 1) | s0
        return {f"O{i}": (d if i == idx else 0) for i in range(4)}

    raise ValueError(f"unknown component kind {kind}")


class LogicComponent:
    _next_id = 1

    def __init__(self, kind, pos, params=None):
        self.id = LogicComponent._next_id
        LogicComponent._next_id += 1
        self.kind = kind
        self.pos = tuple(pos)  # grid anchor point (top-left-ish)
        self.params = dict(params or {})
        if kind == "INPUT" and "value" not in self.params:
            self.params["value"] = 0
        if "label" not in self.params:
            self.params["label"] = ""

    def input_pins(self):
        return PIN_SPECS[self.kind][0]

    def output_pins(self):
        return PIN_SPECS[self.kind][1]

    def display_label(self):
        return self.params.get("label") or self.kind


class LogicCircuitModel:
    def __init__(self):
        self.components = []
        # wires: list of dicts {"src": (comp_id, pin), "dst": (comp_id, pin)}
        self.wires = []

    def add_component(self, comp):
        self.components.append(comp)
        return comp

    def remove_component(self, comp):
        if comp in self.components:
            self.components.remove(comp)
        self.wires = [w for w in self.wires
                      if w["src"][0] != comp.id and w["dst"][0] != comp.id]

    def get_component(self, comp_id):
        for c in self.components:
            if c.id == comp_id:
                return c
        return None

    def wire_to(self, comp_id, pin):
        """The wire (if any) driving this input pin."""
        for w in self.wires:
            if w["dst"] == (comp_id, pin):
                return w
        return None

    def add_wire(self, src, dst):
        """src=(comp_id,pin) must be an output pin, dst=(comp_id,pin) an
        input pin. Replaces any existing wire already driving dst (an
        input can only have one driver)."""
        self.wires = [w for w in self.wires if w["dst"] != dst]
        self.wires.append({"src": src, "dst": dst})

    def remove_wire(self, wire):
        if wire in self.wires:
            self.wires.remove(wire)

    def clear(self):
        self.components.clear()
        self.wires.clear()

    # ------------------------------------------------------------------
    def evaluate(self):
        """Returns (pin_values, error) where pin_values maps
        (comp_id, pin_name) -> 0/1/None for every input and output pin
        of every component, and error is None or a short message (e.g.
        a combinational-loop warning). Never raises."""
        comp_by_id = {c.id: c for c in self.components}

        # component-level dependency graph: dst depends on src
        deps = {c.id: set() for c in self.components}
        dependents = {c.id: set() for c in self.components}
        for w in self.wires:
            src_id, _ = w["src"]
            dst_id, _ = w["dst"]
            if src_id in deps and dst_id in deps:
                deps[dst_id].add(src_id)
                dependents[src_id].add(dst_id)

        # Kahn's algorithm
        in_degree = {cid: len(deps[cid]) for cid in deps}
        ready = [cid for cid, d in in_degree.items() if d == 0]
        order = []
        ready_set = set(ready)
        while ready:
            cid = ready.pop()
            ready_set.discard(cid)
            order.append(cid)
            for nxt in dependents[cid]:
                in_degree[nxt] -= 1
                if in_degree[nxt] == 0:
                    ready.append(nxt)
                    ready_set.add(nxt)

        error = None
        if len(order) != len(self.components):
            error = "cycle"

        pin_values = {}

        def input_value(comp_id, pin):
            w = self.wire_to(comp_id, pin)
            if w is None:
                return None
            src_id, src_pin = w["src"]
            return pin_values.get((src_id, src_pin))

        # Evaluate everything we *can* (topological order); components
        # caught in a cycle just report all-None/floating rather than
        # crashing or looping forever.
        evaluated = set()
        for cid in order:
            comp = comp_by_id[cid]
            if comp.kind == "INPUT":
                val = 1 if comp.params.get("value") else 0
                pin_values[(cid, "Y")] = val
                evaluated.add(cid)
                continue
            ins = {pin: input_value(cid, pin) for pin in comp.input_pins()}
            for pin in comp.input_pins():
                pin_values.setdefault((cid, pin), ins[pin])
            if comp.kind == "OUTPUT":
                pin_values[(cid, "A")] = ins.get("A")
                evaluated.add(cid)
                continue
            outs = evaluate_component(comp.kind, ins)
            for pin, val in outs.items():
                pin_values[(cid, pin)] = val
            evaluated.add(cid)

        for comp in self.components:
            if comp.id in evaluated:
                continue
            for pin in comp.input_pins():
                pin_values.setdefault((comp.id, pin), None)
            for pin in comp.output_pins():
                pin_values.setdefault((comp.id, pin), None)

        return pin_values, error
