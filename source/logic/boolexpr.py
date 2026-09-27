"""
boolexpr.py - Boolean expression parsing and evaluation.

Accepts both symbolic notation (A·B + ¬A·C, A'B + C) and word notation
((A AND B) OR (NOT A AND C)) in the same grammar, and folds NAND/NOR/XNOR
into the four fundamental node kinds (VAR, NOT, AND, OR, XOR) at parse
time, so every downstream consumer (truth tables, minimization, circuit
generation) only ever has to handle five node kinds.

Precedence (highest to lowest): NOT  >  AND  >  XOR  >  OR
Parentheses override precedence as usual. Adjacent terms with no explicit
operator between them are treated as an implicit AND (e.g. "AB" or "A(B+C)").
"""
import re

# ---------------------------------------------------------------------------
# Expression tree
# ---------------------------------------------------------------------------

class Node:
    """A Boolean expression tree node. `kind` is one of:
    'VAR', 'NOT', 'AND', 'OR', 'XOR'. VAR nodes carry a `name`; the others
    carry a list of child Nodes (NOT always has exactly one child)."""

    __slots__ = ("kind", "name", "children")

    def __init__(self, kind, name=None, children=None):
        self.kind = kind
        self.name = name
        self.children = children or []

    def evaluate(self, env):
        if self.kind == "VAR":
            return env[self.name]
        if self.kind == "NOT":
            return 1 - self.children[0].evaluate(env)
        if self.kind == "AND":
            return 1 if all(c.evaluate(env) for c in self.children) else 0
        if self.kind == "OR":
            return 1 if any(c.evaluate(env) for c in self.children) else 0
        if self.kind == "XOR":
            total = 0
            for c in self.children:
                total ^= c.evaluate(env)
            return total
        raise ValueError(f"Unknown node kind: {self.kind}")

    def variables(self):
        """Return the set of variable names used in this expression."""
        out = set()
        self._collect_vars(out)
        return out

    def _collect_vars(self, out):
        if self.kind == "VAR":
            out.add(self.name)
        else:
            for c in self.children:
                c._collect_vars(out)

    def to_symbolic(self):
        """Render using ·, +, ¬ notation (with minimal parentheses)."""
        return _render(self, "symbolic", 0)

    def to_words(self):
        """Render using AND/OR/NOT word notation."""
        return _render(self, "words", 0)

    def __repr__(self):
        if self.kind == "VAR":
            return f"VAR({self.name})"
        return f"{self.kind}({', '.join(repr(c) for c in self.children)})"


def var(name):
    return Node("VAR", name=name)


def NOT(child):
    return Node("NOT", children=[child])


def AND(*children):
    return Node("AND", children=list(children))


def OR(*children):
    return Node("OR", children=list(children))


def XOR(*children):
    return Node("XOR", children=list(children))


# Operator precedence, used only for deciding when to parenthesize on render.
_PRECEDENCE = {"OR": 0, "XOR": 1, "AND": 2, "NOT": 3, "VAR": 4}


def _render(node, style, parent_prec):
    if node.kind == "VAR":
        return node.name

    if node.kind in ("AND", "OR") and not node.children:
        # Degenerate case: every literal was eliminated during
        # minimization (e.g. A+A' or A·A'). Empty AND is the identity
        # for AND (vacuously true); empty OR is the identity for OR
        # (vacuously false) - i.e. these represent the constants 1 and 0.
        return "1" if node.kind == "AND" else "0"

    if node.kind == "NOT":
        inner = node.children[0]
        if style == "symbolic":
            if inner.kind == "VAR":
                return f"{inner.name}'"
            return "¬(" + _render(inner, style, 0) + ")"
        else:
            if inner.kind == "VAR":
                return f"NOT {inner.name}"
            return "NOT (" + _render(inner, style, 0) + ")"

    prec = _PRECEDENCE[node.kind]
    if style == "symbolic":
        sep = {"AND": "·", "OR": " + ", "XOR": " ⊕ "}[node.kind]
    else:
        sep = {"AND": " AND ", "OR": " OR ", "XOR": " XOR "}[node.kind]

    if style == "words" and node.kind == "OR":
        # Word notation reads much more clearly with explicit grouping,
        # even where symbolic notation's operator precedence alone would
        # be unambiguous - beginners can't be assumed to know AND binds
        # tighter than OR just from the words "AND"/"OR".
        parts = []
        for c in node.children:
            rendered = _render(c, style, 0)
            if c.kind in ("AND", "XOR"):
                rendered = "(" + rendered + ")"
            parts.append(rendered)
    else:
        parts = [_render(c, style, prec) for c in node.children]

    text = sep.join(parts)
    if prec < parent_prec:
        text = "(" + text + ")"
    return text


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class ParseError(Exception):
    """Raised on malformed input. `position` is a character offset into the
    original text, for pointing the user at the problem."""

    def __init__(self, message, position=None):
        super().__init__(message)
        self.message = message
        self.position = position


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"""
    \s*(?:
        (?P<LPAREN>\()
      | (?P<RPAREN>\))
      | (?P<NOT>NOT\b|¬|!|~)
      | (?P<XNOR>XNOR\b|⊙|<=>)
      | (?P<NAND>NAND\b)
      | (?P<NOR>NOR\b)
      | (?P<XOR>XOR\b|⊕|\^)
      | (?P<AND>AND\b|·|\*|&)
      | (?P<OR>OR\b|\+|\|)
      | (?P<PRIME>')
      | (?P<VAR>[A-Za-z][A-Za-z0-9_]*)
    )
""", re.VERBOSE | re.IGNORECASE)

_WORD_OPS = {"AND", "OR", "NOT", "XOR", "NAND", "NOR", "XNOR"}


def tokenize(text):
    tokens = []
    pos = 0
    n = len(text)
    while pos < n:
        if text[pos].isspace():
            pos += 1
            continue
        m = _TOKEN_RE.match(text, pos)
        if not m or m.end() == pos:
            raise ParseError(f"Unrecognized character {text[pos]!r}", pos)
        kind = m.lastgroup
        value = m.group(kind)
        if kind == "VAR" and value.upper() in _WORD_OPS:
            # A word-operator matched the VAR pattern's earlier fallback
            # position only if the dedicated group failed to match case
            # (shouldn't normally happen since re.IGNORECASE covers it,
            # this is just a safety net).
            kind = value.upper()
        tokens.append((kind, value, pos))
        pos = m.end()
    tokens.append(("EOF", "", n))
    return tokens


# ---------------------------------------------------------------------------
# Recursive-descent parser
# ---------------------------------------------------------------------------

class _Parser:
    def __init__(self, tokens, text):
        self.tokens = tokens
        self.text = text
        self.i = 0

    def peek(self):
        return self.tokens[self.i]

    def advance(self):
        tok = self.tokens[self.i]
        self.i += 1
        return tok

    def expect(self, kind):
        tok = self.peek()
        if tok[0] != kind:
            raise ParseError(f"Expected {kind} but found {tok[1] or 'end of input'}", tok[2])
        return self.advance()

    def parse(self):
        node = self.parse_or()
        tok = self.peek()
        if tok[0] != "EOF":
            raise ParseError(f"Unexpected {tok[1]!r} after expression", tok[2])
        return node

    def parse_or(self):
        left = self.parse_xor()
        terms = [left]
        while self.peek()[0] in ("OR", "NOR"):
            op = self.advance()
            right = self.parse_xor()
            if op[0] == "OR":
                terms.append(right)
            else:  # NOR: fold as NOT(OR(accumulated_so_far, right)) - only
                    # sensible for simple binary use ("A NOR B"), which is
                    # the expected common case.
                acc = terms[0] if len(terms) == 1 else Node("OR", children=terms)
                terms = [NOT(Node("OR", children=[acc, right]))]
        if len(terms) == 1:
            return terms[0]
        return Node("OR", children=terms)

    def parse_xor(self):
        left = self.parse_and()
        terms = [left]
        while self.peek()[0] in ("XOR", "XNOR"):
            op = self.advance()
            right = self.parse_and()
            if op[0] == "XOR":
                terms.append(right)
            else:  # XNOR
                acc = terms[0] if len(terms) == 1 else Node("XOR", children=terms)
                terms = [NOT(Node("XOR", children=[acc, right]))]
        if len(terms) == 1:
            return terms[0]
        return Node("XOR", children=terms)

    def parse_and(self):
        left = self.parse_not()
        terms = [left]
        while True:
            kind = self.peek()[0]
            if kind in ("AND", "NAND"):
                op = self.advance()
                right = self.parse_not()
                if op[0] == "AND":
                    terms.append(right)
                else:  # NAND
                    acc = terms[0] if len(terms) == 1 else Node("AND", children=terms)
                    terms = [NOT(Node("AND", children=[acc, right]))]
            elif kind in ("VAR", "NOT", "LPAREN"):
                # implicit AND: two primaries back-to-back with no operator,
                # e.g. "AB" or "A(B+C)"
                right = self.parse_not()
                terms.append(right)
            else:
                break
        if len(terms) == 1:
            return terms[0]
        return Node("AND", children=terms)

    def parse_not(self):
        if self.peek()[0] == "NOT":
            self.advance()
            return NOT(self.parse_not())
        return self.parse_postfix()

    def parse_postfix(self):
        node = self.parse_primary()
        while self.peek()[0] == "PRIME":
            self.advance()
            node = NOT(node)
        return node

    def parse_primary(self):
        tok = self.peek()
        if tok[0] == "VAR":
            self.advance()
            return var(tok[1])
        if tok[0] == "LPAREN":
            self.advance()
            node = self.parse_or()
            self.expect("RPAREN")
            return node
        raise ParseError(f"Expected a variable or '(' but found {tok[1] or 'end of input'}", tok[2])


def parse(text):
    """Parse a Boolean expression string into an expression tree.
    Raises ParseError on malformed input."""
    if not text or not text.strip():
        raise ParseError("Expression is empty", 0)
    tokens = tokenize(text)
    return _Parser(tokens, text).parse()
