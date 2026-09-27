"""
truthtable.py - Evaluate a Boolean expression tree over every input
combination to build a truth table.
"""


class TruthTable:
    """rows: list of (input_bits_tuple, output_bit), in standard ascending
    binary-counting order over `variables` (first variable = MSB)."""

    def __init__(self, variables, rows):
        self.variables = variables  # sorted list of variable names
        self.rows = rows            # [(bits_tuple, output), ...]

    def minterms(self):
        """Row indices (0-based, matching the bits-as-binary-number
        convention) where the output is 1."""
        return [i for i, (_, y) in enumerate(self.rows) if y == 1]

    def maxterms(self):
        return [i for i, (_, y) in enumerate(self.rows) if y == 0]


def build_truth_table(node, variables=None):
    """Build a TruthTable for `node` (a logic.boolexpr.Node). If
    `variables` is not given, it's inferred from the expression and sorted
    alphabetically."""
    if variables is None:
        variables = sorted(node.variables())
    n = len(variables)
    rows = []
    for i in range(2 ** n):
        bits = tuple((i >> (n - 1 - k)) & 1 for k in range(n))
        env = dict(zip(variables, bits))
        y = node.evaluate(env)
        rows.append((bits, y))
    return TruthTable(variables, rows)
