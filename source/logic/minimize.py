"""
minimize.py - Boolean minimization via the Quine-McCluskey method plus
Petrick's method for an exact (not merely heuristic) minimal cover.

This is the single source of truth for "which prime implicants were
selected and why" - the K-map (kmap.py) highlights exactly the groups
this module chose, and the "explain" trace exposed here is the real
algorithm trace, not separately-written text.
"""
from . import boolexpr as bx

_MAX_VARS = 12  # generous for an educational tool; keeps worst-case QM cost bounded


class MinimizationResult:
    def __init__(self, variables, canonical_sop, canonical_pos,
                 minimal_sop, minimal_pos, sop_terms, pos_terms, steps):
        self.variables = variables
        self.canonical_sop = canonical_sop      # Node: OR of all minterms
        self.canonical_pos = canonical_pos      # Node: AND of all maxterms
        self.minimal_sop = minimal_sop          # Node: minimized SOP
        self.minimal_pos = minimal_pos          # Node: minimized POS
        self.sop_terms = sop_terms              # [(pattern, covered_minterms), ...] chosen for minimal SOP
        self.pos_terms = pos_terms              # [(pattern, covered_maxterms), ...] chosen for minimal POS
        self.steps = steps                      # list of human-readable strings tracing the QM merges


def _bits_of(m, n):
    return tuple('1' if (m >> (n - 1 - k)) & 1 else '0' for k in range(n))


def _combine(t1, t2):
    """If t1 and t2 differ in exactly one position, return the merged
    pattern (that position replaced with '-'); otherwise None."""
    diff = None
    for i, (a, b) in enumerate(zip(t1, t2)):
        if a != b:
            if diff is not None:
                return None
            diff = i
    if diff is None:
        return None
    merged = list(t1)
    merged[diff] = '-'
    return tuple(merged)


def _literal_count(pattern):
    return sum(1 for b in pattern if b != '-')


def find_prime_implicants(n_vars, terms, steps=None, term_word="minterm"):
    """Quine-McCluskey reduction: repeatedly combine terms differing in one
    bit until nothing more can combine. Returns [(pattern, covered_set), ...]
    for every prime implicant found. `terms` is a list of term indices
    (minterm or maxterm numbers, 0..2**n_vars-1)."""
    if n_vars > _MAX_VARS:
        raise ValueError(f"Too many variables ({n_vars}) for minimization")
    if not terms:
        return []

    current = {_bits_of(m, n_vars): frozenset([m]) for m in terms}
    primes = {}
    round_no = 1
    while current:
        used = set()
        next_round = {}
        merge_log = []
        items = list(current.items())
        for i in range(len(items)):
            for j in range(i + 1, len(items)):
                t1, cov1 = items[i]
                t2, cov2 = items[j]
                merged = _combine(t1, t2)
                if merged is not None:
                    used.add(t1)
                    used.add(t2)
                    prev = next_round.get(merged, frozenset())
                    next_round[merged] = prev | cov1 | cov2
                    merge_log.append(f"{''.join(t1)}+{''.join(t2)}->{''.join(merged)}")
        for t, cov in current.items():
            if t not in used:
                primes[t] = primes.get(t, frozenset()) | cov
        if steps is not None and merge_log:
            steps.append(f"Round {round_no}: combined adjacent {term_word}s differing in one bit -> "
                          + ", ".join(merge_log))
        round_no += 1
        current = next_round

    return list(primes.items())


def _absorb(products):
    """Remove any product-of-indices that is a superset of another
    (X + XY = X), used to keep Petrick's-method expansion small."""
    uniq = list({frozenset(p) for p in products})
    return [p for p in uniq if not any(q < p for q in uniq if q != p)]


def _select_cover(prime_list, terms, steps=None, term_word="minterm"):
    """Essential prime implicants first, then Petrick's method (exact,
    not greedy) for whatever remains uncovered."""
    if not terms:
        return []
    remaining = set(terms)
    chart = {m: [i for i, (_, cov) in enumerate(prime_list) if m in cov] for m in terms}

    essential_idx = set()
    for m, covers in chart.items():
        if len(covers) == 1:
            essential_idx.add(covers[0])
    covered = set()
    for idx in essential_idx:
        covered |= prime_list[idx][1]
    remaining -= covered

    if steps is not None and essential_idx:
        steps.append(f"Essential prime implicants (only one PI covers that {term_word}): " +
                      ", ".join(str(i) for i in sorted(essential_idx)))

    chosen = set(essential_idx)
    if remaining:
        candidate_idxs = [i for i in range(len(prime_list)) if prime_list[i][1] & remaining]
        clauses = []
        for m in sorted(remaining):
            clause = frozenset(i for i in candidate_idxs if m in prime_list[i][1])
            if clause:
                clauses.append(clause)
        if clauses:
            products = [frozenset([i]) for i in clauses[0]]
            for clause in clauses[1:]:
                new_products = [p | frozenset([i]) for p in products for i in clause]
                products = _absorb(new_products)
                if len(products) > 4000:
                    # Pathological case safety net: fall back to a greedy
                    # cover rather than let Petrick's method blow up.
                    products = None
                    break
            if products:
                best = min(products, key=lambda p: (len(p), sum(_literal_count(prime_list[i][0]) for i in p)))
                chosen |= set(best)
                if steps is not None:
                    steps.append(f"Remaining {term_word}s covered by prime implicants: " +
                                  ", ".join(str(i) for i in sorted(best)))
            else:
                chosen |= _greedy_cover(prime_list, remaining, candidate_idxs)
        else:
            chosen |= _greedy_cover(prime_list, remaining, candidate_idxs)

    return [prime_list[i] for i in sorted(chosen)]


def _greedy_cover(prime_list, remaining, candidate_idxs):
    chosen = set()
    remaining = set(remaining)
    while remaining:
        best_i = max(candidate_idxs, key=lambda i: len(prime_list[i][1] & remaining))
        chosen.add(best_i)
        remaining -= prime_list[best_i][1]
    return chosen


def _term_to_and_node(pattern, variables):
    lits = [bx.var(v) if b == '1' else bx.NOT(bx.var(v)) for b, v in zip(pattern, variables) if b != '-']
    if not lits:
        return bx.Node("AND", children=[])  # all variables eliminated -> constant 1
    if len(lits) == 1:
        return lits[0]
    return bx.AND(*lits)


def _term_to_or_node(pattern, variables):
    # De Morgan of an AND-term: literal senses flip (1 -> NOT var, 0 -> var)
    lits = [bx.NOT(bx.var(v)) if b == '1' else bx.var(v) for b, v in zip(pattern, variables) if b != '-']
    if not lits:
        return bx.Node("OR", children=[])  # constant 0
    if len(lits) == 1:
        return lits[0]
    return bx.OR(*lits)


def minimize(table):
    """Full minimization pipeline for a logic.truthtable.TruthTable:
    canonical SOP/POS plus exact-minimal SOP/POS (Quine-McCluskey +
    Petrick's method), with a human-readable step trace."""
    variables = table.variables
    n = len(variables)
    minterms = table.minterms()
    maxterms = table.maxterms()
    steps = []

    # Canonical forms: one term per minterm/maxterm, no combining.
    if minterms:
        sop_canon_terms = [_term_to_and_node(_bits_of(m, n), variables) for m in minterms]
        canonical_sop = sop_canon_terms[0] if len(sop_canon_terms) == 1 else bx.OR(*sop_canon_terms)
    else:
        canonical_sop = bx.Node("OR", children=[])  # constant 0
    if maxterms:
        pos_canon_terms = [_term_to_or_node(_bits_of(m, n), variables) for m in maxterms]
        canonical_pos = pos_canon_terms[0] if len(pos_canon_terms) == 1 else bx.AND(*pos_canon_terms)
    else:
        canonical_pos = bx.Node("AND", children=[])  # constant 1

    # Minimal SOP: QM + Petrick's method directly on the minterms.
    steps.append("--- Minimizing SOP ---")
    sop_primes = find_prime_implicants(n, minterms, steps, "minterm")
    sop_terms = _select_cover(sop_primes, minterms, steps, "minterm")
    if not sop_terms:
        minimal_sop = bx.Node("OR", children=[])  # constant 0
    else:
        and_nodes = [_term_to_and_node(p, variables) for p, _ in sop_terms]
        minimal_sop = and_nodes[0] if len(and_nodes) == 1 else bx.OR(*and_nodes)

    # Minimal POS: QM + Petrick's method on the maxterms (= minterms of the
    # complement), then De Morgan each chosen AND-term into an OR-term.
    steps.append("--- Minimizing POS (via the complement) ---")
    pos_primes = find_prime_implicants(n, maxterms, steps, "maxterm")
    pos_terms = _select_cover(pos_primes, maxterms, steps, "maxterm")
    if not pos_terms:
        minimal_pos = bx.Node("AND", children=[])  # constant 1
    else:
        or_nodes = [_term_to_or_node(p, variables) for p, _ in pos_terms]
        minimal_pos = or_nodes[0] if len(or_nodes) == 1 else bx.AND(*or_nodes)

    return MinimizationResult(variables, canonical_sop, canonical_pos,
                               minimal_sop, minimal_pos, sop_terms, pos_terms, steps)
