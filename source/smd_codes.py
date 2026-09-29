"""
smd_codes.py - Decoding / encoding of the markings printed on SMD (and
small through-hole) resistors, capacitors and inductors.

Pure logic, no UI. Every decoder returns a list of Interpretation objects
(a marking can be ambiguous, e.g. "47" or "101"), each with the value in
base units (ohm / farad / henry), a short name of the scheme that was used
and the step-by-step working so the UI can show *how* it was read.

Schemes covered
  Resistors   3-digit (E24, ~5%), 4-digit (E96, ~1%), EIA-96 (2 digits +
              letter, 1%), R-notation (4R7, R047), m-notation (5m0 milliohm),
              zero-ohm jumpers (0, 00, 000)
  Capacitors  3-digit pF code (104), with tolerance letter and EIA voltage
              code (2A104J), EIA-198 letter+digit code (e.g. S3 = 4.7 nF),
              tantalum/electrolytic polarised code (letter voltage + pF code,
              e.g. A106 = 10 uF 10 V), R/p/n/u notation (4n7, 2u2, 0p5)
  Inductors   3-digit uH code (101 = 100 uH), R-notation in uH (4R7),
              N-notation in nH (4N7, 47N), 2-digit uH
"""
import math
import re

# ---------------------------------------------------------------------------
# Reference tables
# ---------------------------------------------------------------------------
E96 = [100, 102, 105, 107, 110, 113, 115, 118, 121, 124, 127, 130, 133, 137, 140, 143,
       147, 150, 154, 158, 162, 165, 169, 174, 178, 182, 187, 191, 196, 200, 205, 210,
       215, 221, 226, 232, 237, 243, 249, 255, 261, 267, 274, 280, 287, 294, 301, 309,
       316, 324, 332, 340, 348, 357, 365, 374, 383, 392, 402, 412, 422, 432, 442, 453,
       464, 475, 487, 499, 511, 523, 536, 549, 562, 576, 590, 604, 619, 634, 649, 665,
       681, 698, 715, 732, 750, 768, 787, 806, 825, 845, 866, 887, 909, 931, 953, 976]

E24 = [10, 11, 12, 13, 15, 16, 18, 20, 22, 24, 27, 30, 33, 36, 39, 43, 47, 51, 56, 62, 68, 75, 82, 91]
E12 = [10, 12, 15, 18, 22, 27, 33, 39, 47, 56, 68, 82]
E6 = [10, 15, 22, 33, 47, 68]

# EIA-96 multiplier letters (resistors)
EIA96_MULT = {"Z": 0.001, "Y": 0.01, "R": 0.01, "X": 0.1, "S": 0.1, "A": 1, "B": 10,
              "H": 10, "C": 100, "D": 1e3, "E": 1e4, "F": 1e5}
EIA96_MULT_PREFERRED = [("Z", 0.001), ("Y", 0.01), ("X", 0.1), ("A", 1), ("B", 10),
                        ("C", 100), ("D", 1e3), ("E", 1e4), ("F", 1e5)]

# EIA-198 capacitor code: letter = two significant figures (pF), digit = power of ten
EIA198_LETTER = {
    "A": 1.0, "B": 1.1, "C": 1.2, "D": 1.3, "E": 1.5, "F": 1.6, "G": 1.8, "H": 2.0,
    "J": 2.2, "K": 2.4, "a": 2.5, "L": 2.7, "M": 3.0, "N": 3.3, "b": 3.5, "P": 3.6,
    "Q": 3.9, "d": 4.0, "R": 4.3, "e": 4.5, "S": 4.7, "f": 5.0, "T": 5.1, "U": 5.6,
    "m": 6.0, "V": 6.2, "W": 6.8, "n": 7.0, "X": 7.5, "t": 8.0, "Y": 8.2, "y": 9.0,
    "Z": 9.1,
}
EIA198_MULT = {str(d): 10.0 ** d for d in range(0, 8)}
EIA198_MULT["9"] = 0.1

# Capacitor tolerance letters
CAP_TOL = {"B": "±0.1 pF", "C": "±0.25 pF", "D": "±0.5 pF", "F": "±1%", "G": "±2%",
           "J": "±5%", "K": "±10%", "M": "±20%", "Z": "+80/−20%", "P": "+100/−0%"}

# EIA voltage code (ceramic / film, printed as e.g. "2A")
CAP_VOLT_EIA = {"0G": 4, "0L": 5.5, "0J": 6.3, "1A": 10, "1C": 16, "1D": 20, "1E": 25,
                "1V": 35, "1H": 50, "1J": 63, "1K": 80, "2A": 100, "2Q": 110, "2B": 125,
                "2C": 160, "2Z": 180, "2D": 200, "2P": 220, "2E": 250, "2F": 315, "2V": 350,
                "2G": 400, "2W": 450, "2H": 500, "2J": 630, "3A": 1000}

# Single-letter voltage code on tantalum / polymer SMD capacitors (EIA)
TANT_VOLT = {"e": 2.5, "G": 4, "J": 6.3, "A": 10, "C": 16, "D": 20, "E": 25, "V": 35, "H": 50, "T": 50}

# Package sizes: imperial, metric, L x W (mm), typical resistor power (W)
PACKAGES = [
    ("01005", "0402", 0.4, 0.2, 1 / 32),
    ("0201", "0603", 0.6, 0.3, 1 / 20),
    ("0402", "1005", 1.0, 0.5, 1 / 16),
    ("0603", "1608", 1.6, 0.8, 1 / 10),
    ("0805", "2012", 2.0, 1.25, 1 / 8),
    ("1206", "3216", 3.2, 1.6, 1 / 4),
    ("1210", "3225", 3.2, 2.5, 1 / 2),
    ("1812", "4532", 4.5, 3.2, 3 / 4),
    ("2010", "5025", 5.0, 2.5, 3 / 4),
    ("2512", "6332", 6.3, 3.2, 1.0),
]
# Tantalum case codes: case, EIA metric, L x W x H (mm)
TANT_CASES = [("A", "3216-18", 3.2, 1.6, 1.8), ("B", "3528-21", 3.5, 2.8, 2.1),
              ("C", "6032-28", 6.0, 3.2, 2.8), ("D", "7343-31", 7.3, 4.3, 3.1),
              ("E", "7343-43", 7.3, 4.3, 4.3)]


class Interp:
    """One possible reading of a marking."""

    def __init__(self, value, scheme, steps, tol=None, voltage=None, note=None, confidence=1.0):
        self.value = value          # base units (ohm / F / H)
        self.scheme = scheme        # i18n key of the scheme name
        self.steps = steps          # list of human-readable working lines
        self.tol = tol
        self.voltage = voltage
        self.note = note            # i18n key of an extra hint
        self.confidence = confidence

    def __repr__(self):
        return f"Interp({self.value!r}, {self.scheme})"


def _clean(code):
    return code.strip().replace(" ", "").replace("µ", "u").replace("Ω", "")


def _num_with_letter_point(code, letters):
    """'4R7' -> 4.7 ; 'R47' -> 0.47 ; '47R' -> 47. Returns (value, letter) or None."""
    m = re.fullmatch(r"(\d*)([%s])(\d*)" % letters, code)
    if not m or (not m.group(1) and not m.group(3)):
        return None
    a, L, b = m.groups()
    txt = (a or "0") + "." + (b or "0")
    return float(txt), L


# ---------------------------------------------------------------------------
# Resistors
# ---------------------------------------------------------------------------
def decode_resistor(code):
    raw = _clean(code)
    c = raw.upper()
    out = []
    if not c:
        return out
    if re.fullmatch(r"0+", c):
        out.append(Interp(0.0, "smd.s.jumper", ["0 / 00 / 000 → 0 Ω"], note="smd.n.jumper"))
        return out
    # R-notation (decimal point = R), ohms
    r = _num_with_letter_point(c, "R")
    if r:
        v = r[0]
        out.append(Interp(v, "smd.s.rnot", [f"{raw.upper()}:  R = decimal point  →  {v:g} Ω"],
                          tol=None, note="smd.n.rnot"))
        return out
    # m-notation (milliohm), e.g. 5m0 / m50 / 1m
    m = _num_with_letter_point(raw, "m") if "m" in raw else None
    if m:
        v = m[0] * 1e-3
        out.append(Interp(v, "smd.s.mnot", [f"{raw}:  m = decimal point in mΩ  →  {m[0]:g} mΩ"]))
        return out
    # EIA-96: two digits + letter
    mm = re.fullmatch(r"(\d\d)([ZYRXSABHCDEF])", c)
    if mm:
        idx = int(mm.group(1))
        if 1 <= idx <= 96:
            base = E96[idx - 1]
            mult = EIA96_MULT[mm.group(2)]
            v = base * mult
            out.append(Interp(v, "smd.s.eia96",
                              [f"{mm.group(1)} → E96 #{idx} = {base}",
                               f"{mm.group(2)} → × {mult:g}",
                               f"{base} × {mult:g} = {v:g} Ω"], tol="±1%"))
        return out
    if re.fullmatch(r"\d{3}", c):
        sig, exp = int(c[:2]), int(c[2])
        if exp == 9:
            # rarely used as x0.1 on some parts
            v = sig * 0.1
            steps = [f"{c[:2]} = {sig}", f"{c[2]} → × 0.1 (9 = 10⁻¹)", f"= {v:g} Ω"]
        else:
            v = sig * 10 ** exp
            steps = [f"{c[:2]} = {sig}", f"{c[2]} → × 10^{exp} = {10 ** exp:g}", f"{sig} × {10 ** exp:g} = {v:g} Ω"]
        out.append(Interp(v, "smd.s.three", steps, tol="±5% (E24)", note="smd.n.three_bar"))
        return out
    if re.fullmatch(r"\d{4}", c):
        sig, exp = int(c[:3]), int(c[3])
        v = sig * 10 ** exp
        out.append(Interp(v, "smd.s.four", [f"{c[:3]} = {sig}", f"{c[3]} → × 10^{exp} = {10 ** exp:g}",
                                            f"{sig} × {10 ** exp:g} = {v:g} Ω"], tol="±1% (E96)"))
        return out
    if re.fullmatch(r"\d{1,2}", c):
        v = float(int(c))
        out.append(Interp(v, "smd.s.plain", [f"{c} → {v:g} Ω"], confidence=0.6))
    return out


def _sig_exp(value, digits):
    """Split value into `digits` significant figures and a power of ten.
    Returns (sig:int, exp:int, exact:bool)."""
    if value <= 0:
        return None
    exp = math.floor(math.log10(value)) - (digits - 1)
    sig = round(value / 10 ** exp)
    if sig >= 10 ** digits:
        sig //= 10
        exp += 1
    exact = abs(sig * 10 ** exp - value) <= value * 1e-6
    return sig, exp, exact


def _rnot(value, letter="R", max_len=4):
    """4.7 -> 4R7, 0.47 -> R47, 47 -> 47R ... returns None if not neat."""
    txt = f"{value:.6g}"
    if "e" in txt:
        return None
    if "." in txt:
        a, b = txt.split(".")
        a = "" if a == "0" else a
        s = f"{a}{letter}{b}"
    else:
        s = f"{txt}{letter}" + ("0" if value < 10 else "")
    return s if len(s) <= max_len else None


def encode_resistor(ohms):
    """All markings that describe `ohms`. List of (scheme_key, code, exact, note)."""
    res = []
    if ohms == 0:
        return [("smd.s.jumper", "0 / 000", True, None)]
    # 3-digit
    se = _sig_exp(ohms, 2)
    if se and se[1] >= 0 and se[1] <= 8:
        sig, exp, exact = se
        res.append(("smd.s.three", f"{sig:02d}{exp}", exact, None))
    if ohms < 10:
        r = _rnot(ohms, "R", 4)
        if r:
            res.append(("smd.s.rnot", r, True, None))
    if ohms < 100:
        r = _rnot(ohms, "R", 4)
        if r and ("smd.s.rnot", r, True, None) not in res:
            res.append(("smd.s.rnot", r, True, None))
    # 4-digit
    se = _sig_exp(ohms, 3)
    if se and 0 <= se[1] <= 8:
        sig, exp, exact = se
        res.append(("smd.s.four", f"{sig:03d}{exp}", exact, None))
    # EIA-96
    se = _sig_exp(ohms, 3)
    if se:
        sig, exp, exact = se
        if sig in E96:
            mult = 10.0 ** exp
            for L, mv in EIA96_MULT_PREFERRED:
                if abs(mv - mult) <= mult * 1e-9:
                    res.append(("smd.s.eia96", f"{E96.index(sig) + 1:02d}{L}", exact, None))
                    break
        else:
            res.append(("smd.s.eia96", "—", False, "smd.n.not_e96"))
    if ohms < 1:
        m = _rnot(ohms * 1e3, "m", 4)
        if m:
            res.append(("smd.s.mnot", m, True, None))
    return res


def nearest_series(value, series):
    """Nearest value from an E-series (list of 2- or 3-digit mantissas)."""
    if value <= 0:
        return value
    decade = 10 ** math.floor(math.log10(value))
    scale = 10 if series[0] < 100 else 100
    cands = []
    for d in (decade / 10, decade, decade * 10):
        for m in series:
            cands.append(m / scale * d)
    return min(cands, key=lambda c: abs(math.log(c / value)))


# ---------------------------------------------------------------------------
# Capacitors
# ---------------------------------------------------------------------------
def decode_capacitor(code):
    raw = _clean(code)
    out = []
    if not raw:
        return out
    s = raw
    # ---- EIA voltage prefix, e.g. 2A104J / 1H 473K
    volt = None
    mv = re.match(r"^([0-3][A-Z])(?=\d)", s)
    if mv and mv.group(1) in CAP_VOLT_EIA:
        volt = CAP_VOLT_EIA[mv.group(1)]
        s = s[2:]
    # ---- tantalum: voltage letter + 3-digit pF code (e.g. A106, 107C)
    mt = re.fullmatch(r"([eGJACDEVHT])(\d{3})", s) or re.fullmatch(r"(\d{3})([eGJACDEVHT])", s)
    if mt and volt is None:
        g = mt.groups()
        letter, digits = (g[0], g[1]) if not g[0].isdigit() else (g[1], g[0])
        pf = int(digits[:2]) * 10 ** int(digits[2])
        v = pf * 1e-12
        suffix_form = g[0].isdigit()
        if not (1e-8 <= v <= 2.2e-3):
            mt = None
    if mt and volt is None:
        out.append(Interp(v, "smd.s.tant",
                          [f"{letter} → {TANT_VOLT[letter]:g} V (EIA)",
                           f"{digits[:2]} × 10^{digits[2]} pF = {pf:g} pF = {_fmt(v, 'F')}"],
                          voltage=TANT_VOLT[letter], note="smd.n.tant",
                          confidence=(0.5 if suffix_form else 1.0) * (1.0 if v >= 1e-7 else 0.5)))
    # ---- tolerance suffix letter (B/C/D are absolute pF tolerances, only
    #      used on parts below 10 pF)
    tol = None
    if len(s) > 1 and s[-1].upper() in CAP_TOL and s[:-1].isdigit():
        body = s[:-1]
        L = s[-1].upper()
        small = len(body) == 3 and (int(body[2]) >= 8 or int(body[:2]) * 10 ** int(body[2]) < 10)
        if L not in "BCD" or small:
            tol = CAP_TOL[L]
            s = body
    # ---- 3-digit pF code
    if re.fullmatch(r"\d{3}", s):
        sig, e = int(s[:2]), int(s[2])
        mult = {8: 0.01, 9: 0.1}.get(e, 10 ** e)
        pf = sig * mult
        v = pf * 1e-12
        steps = [f"{s[:2]} = {sig}", f"{s[2]} → × {mult:g}" + ("  (8 = ×0.01, 9 = ×0.1)" if e >= 8 else ""),
                 f"{sig} × {mult:g} = {pf:g} pF = {_fmt(v, 'F')}"]
        if volt:
            steps.insert(0, f"{mv.group(1)} → {volt:g} V")
        if tol:
            steps.append(f"{raw[-1].upper()} → {tol}")
        out.append(Interp(v, "smd.s.cap3", steps, tol=tol, voltage=volt))
    elif re.fullmatch(r"\d{1,2}", s):
        pf = int(s)
        out.append(Interp(pf * 1e-12, "smd.s.cap2", [f"{s} → {pf} pF"], tol=tol, voltage=volt,
                          confidence=0.7))
    # ---- 4-digit (film/ceramic, 3 sig. figures)
    elif re.fullmatch(r"\d{4}", s):
        pf = int(s[:3]) * 10 ** int(s[3])
        out.append(Interp(pf * 1e-12, "smd.s.cap4", [f"{s[:3]} × 10^{s[3]} pF = {pf:g} pF"], tol=tol,
                          voltage=volt, confidence=0.6))
    # ---- EIA-198 letter + digit (case sensitive!)
    me = re.fullmatch(r"([A-Za-z])(\d)", raw)
    if me and me.group(1) in EIA198_LETTER:
        mant = EIA198_LETTER[me.group(1)]
        mult = EIA198_MULT[me.group(2)]
        pf = mant * mult
        out.append(Interp(pf * 1e-12, "smd.s.eia198",
                          [f"{me.group(1)} → {mant:g} (EIA-198 table)",
                           f"{me.group(2)} → × {mult:g}", f"{mant:g} × {mult:g} = {pf:g} pF = {_fmt(pf * 1e-12, 'F')}"],
                          note="smd.n.eia198"))
    # ---- p / n / u notation (4n7, 2u2, 0p5, 47n, 100u)
    mn = re.fullmatch(r"(\d*)([pnuPNU])(\d*)", raw)
    if mn and (mn.group(1) or mn.group(3)):
        a, L, b = mn.groups()
        num = float((a or "0") + "." + (b or "0"))
        fac = {"p": 1e-12, "n": 1e-9, "u": 1e-6}[L.lower()]
        v = num * fac
        unit = {"p": "pF", "n": "nF", "u": "µF"}[L.lower()]
        out.append(Interp(v, "smd.s.letterpoint",
                          [f"{raw}: {L} = decimal point and unit → {num:g} {unit}"], tol=tol, voltage=volt))
    # ---- R notation in pF (e.g. 4R7 = 4.7 pF, often on small ceramics)
    r = _num_with_letter_point(raw.upper(), "R")
    if r:
        out.append(Interp(r[0] * 1e-12, "smd.s.rnot_pf", [f"R = decimal point → {r[0]:g} pF"], confidence=0.7))
    out.sort(key=lambda i: -i.confidence)
    return out


def encode_capacitor(farads):
    res = []
    pf = farads * 1e12
    if pf <= 0:
        return res
    # 3-digit
    if pf < 10:
        if abs(pf * 10 - round(pf * 10)) < 1e-6:
            res.append(("smd.s.cap3", f"{round(pf * 10):02d}9", True, None))
        r = _rnot(pf, "R", 4)
        if r:
            res.append(("smd.s.rnot_pf", r, True, None))
    else:
        se = _sig_exp(pf, 2)
        if se and 0 <= se[1] <= 7:
            res.append(("smd.s.cap3", f"{se[0]:02d}{se[1]}", se[2], None))
    # EIA-198
    se = _sig_exp(pf, 2)
    if se:
        mant = se[0] / 10
        found = None
        for L, m in EIA198_LETTER.items():
            if abs(m - mant) < 1e-9:
                found = L
        exp = se[1] + 1
        if found and (0 <= exp <= 7 or exp == -1):
            res.append(("smd.s.eia198", f"{found}{9 if exp == -1 else exp}", se[2], "smd.n.eia198"))
        else:
            res.append(("smd.s.eia198", "—", False, "smd.n.not_eia198"))
    # letter-point
    for unit, fac in (("u", 1e-6), ("n", 1e-9), ("p", 1e-12)):
        x = farads / fac
        if 1 <= x < 1000:
            code = _rnot(x, unit, 5)
            if code:
                res.append(("smd.s.letterpoint", code.replace("u", "µ"), True, None))
            break
    # tantalum style (value part)
    if farads >= 1e-7:
        se = _sig_exp(pf, 2)
        if se and 0 <= se[1] <= 9:
            res.append(("smd.s.tant", f"A{se[0]:02d}{se[1]}  (A = 10 V)", se[2], "smd.n.tant"))
    return res


# ---------------------------------------------------------------------------
# Inductors
# ---------------------------------------------------------------------------
def decode_inductor(code):
    raw = _clean(code)
    c = raw.upper()
    out = []
    if not c:
        return out
    r = _num_with_letter_point(c, "R")
    if r:
        out.append(Interp(r[0] * 1e-6, "smd.s.ind_r", [f"R = decimal point, unit µH → {r[0]:g} µH"]))
        return out
    n = _num_with_letter_point(c, "N")
    if n:
        out.append(Interp(n[0] * 1e-9, "smd.s.ind_n", [f"N = decimal point, unit nH → {n[0]:g} nH"]))
        return out
    if re.fullmatch(r"\d{3}", c):
        sig, e = int(c[:2]), int(c[2])
        uh = sig * 10 ** e
        out.append(Interp(uh * 1e-6, "smd.s.ind3",
                          [f"{c[:2]} = {sig}", f"{c[2]} → × 10^{e}", f"{sig} × {10 ** e:g} = {uh:g} µH"],
                          note="smd.n.ind3"))
        # some RF chip inductors use the same code in nH
        out.append(Interp(uh * 1e-9, "smd.s.ind3_nh", [f"{sig} × {10 ** e:g} = {uh:g} nH"],
                          confidence=0.3, note="smd.n.ind3_nh"))
    elif re.fullmatch(r"\d{1,2}", c):
        out.append(Interp(int(c) * 1e-6, "smd.s.ind2", [f"{c} → {int(c)} µH"], confidence=0.6))
    return out


def encode_inductor(henries):
    res = []
    uh = henries * 1e6
    if uh <= 0:
        return res
    if uh < 1:
        nh = uh * 1000
        code = _rnot(nh, "N", 4)
        if code:
            res.append(("smd.s.ind_n", code, True, None))
        code = _rnot(uh, "R", 4)
        if code:
            res.append(("smd.s.ind_r", code, True, None))
    elif uh < 10:
        code = _rnot(uh, "R", 4)
        if code:
            res.append(("smd.s.ind_r", code, True, None))
    if uh >= 10:
        se = _sig_exp(uh, 2)
        if se and 0 <= se[1] <= 7:
            res.append(("smd.s.ind3", f"{se[0]:02d}{se[1]}", se[2], None))
    return res


def decode(kind, code):
    return {"resistor": decode_resistor, "capacitor": decode_capacitor,
            "inductor": decode_inductor}[kind](code)


def encode(kind, value):
    return {"resistor": encode_resistor, "capacitor": encode_capacitor,
            "inductor": encode_inductor}[kind](value)


def _fmt(value, unit):
    prefixes = [("G", 1e9), ("M", 1e6), ("k", 1e3), ("", 1), ("m", 1e-3), ("µ", 1e-6), ("n", 1e-9), ("p", 1e-12)]
    av = abs(value)
    if av == 0:
        return f"0 {unit}"
    for sym, f in prefixes:
        if av >= f * 0.9999999:
            return f"{value / f:.4g} {sym}{unit}"
    return f"{value / 1e-12:.4g} p{unit}"


fmt = _fmt
