"""
tabs/coupling_viz.py - Inductors > Coupling (k): animated magnetic coupling.

Two coils drawn in cross-section. An AC current in coil 1 (shown with the
usual ⊙ / ⊗ winding marks) builds a magnetic field whose lines pulse and
reverse with the current. A fraction k of the flux also threads coil 2 -
drag the coils closer/further (or set k) and watch how many field lines
link both coils. The changing linked flux induces v2 = M·di1/dt in coil 2;
with a load connected, coil 2's own current creates an opposing field
(Lenz's law, drawn dashed). A live scope underneath shows that v2 peaks
when i1 crosses zero - the induced voltage follows the RATE OF CHANGE.

The animation runs in slow motion (one AC period ≈ 3 s) so the eye can
follow it; all numbers shown are for the real frequency.
"""
import math
import time
import tkinter as tk
from widgets import is_shown
from tkinter import ttk

from widgets import parse_value, format_value, FONT_BODY, FONT_H2, ScrollableFrame
from i18n import t

BG = "#fdfaf3"
C1 = "#c9622a"     # primary field / current colour
C2 = "#2A9D8F"     # secondary (induced) colour
CORE = "#9aa3b2"
TICK_MS = 40
PERIOD_S = 3.0     # slow-motion: one AC period on screen


class CouplingPanel(ttk.Frame):
    def __init__(self, parent, accent):
        super().__init__(parent, style="Card.TFrame")
        self.accent = accent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body
        body.columnconfigure(1, weight=1)
        self._phase = 0.0
        self._after = None
        self._drag = None
        self._hist = []

        intro = ttk.Label(body, text=t("cpl.intro"), font=FONT_BODY, style="CardBody.TLabel", justify="left",
                          wraplength=900)
        intro.grid(row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(12, 6))
        body.bind("<Configure>", lambda e: intro.configure(wraplength=max(300, e.width - 40)), add="+")

        ctl = ttk.Frame(body, style="Card.TFrame")
        ctl.grid(row=1, column=0, sticky="nw", padx=(16, 8))
        self.vars = {}
        rows = [("l1", "L1", "10m", "H"), ("l2", "L2", "40m", "H"), ("i1", t("cpl.i1"), "1", "A"),
                ("f", t("cpl.freq"), "50", "Hz"), ("rl", t("cpl.rl"), "10", "Ω")]
        for r, (k, lbl, d, u) in enumerate(rows):
            ttk.Label(ctl, text=lbl, font=FONT_BODY, style="CardBody.TLabel").grid(row=r, column=0, sticky="w", pady=2)
            v = tk.StringVar(value=d)
            e = ttk.Entry(ctl, textvariable=v, width=9)
            e.grid(row=r, column=1, sticky="w", padx=6)
            e.bind("<KeyRelease>", lambda ev: self._recalc())
            ttk.Label(ctl, text=u, font=FONT_BODY, style="CardBody.TLabel").grid(row=r, column=2, sticky="w")
            self.vars[k] = v
        self.load_on = tk.BooleanVar(value=True)
        ttk.Checkbutton(ctl, text=t("cpl.load_on"), variable=self.load_on, command=self._recalc)\
            .grid(row=len(rows), column=0, columnspan=3, sticky="w", pady=(4, 2))
        self.core_on = tk.BooleanVar(value=False)
        ttk.Checkbutton(ctl, text=t("cpl.core"), variable=self.core_on, command=self._recalc)\
            .grid(row=len(rows) + 1, column=0, columnspan=3, sticky="w", pady=2)
        ttk.Label(ctl, text=t("cpl.k_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=len(rows) + 2, column=0, sticky="w", pady=(8, 0))
        self.k_var = tk.DoubleVar(value=0.5)
        ttk.Scale(ctl, from_=0.0, to=0.99, variable=self.k_var, orient="horizontal", length=170,
                  command=lambda v: self._recalc()).grid(row=len(rows) + 2, column=1, columnspan=2, sticky="w",
                                                         pady=(8, 0))
        self.k_txt = tk.StringVar()
        ttk.Label(ctl, textvariable=self.k_txt, font=("Consolas", 10, "bold"), foreground=accent,
                  style="CardFormula.TLabel").grid(row=len(rows) + 3, column=1, columnspan=2, sticky="w")
        self.res_var = tk.StringVar()
        ttk.Label(ctl, textvariable=self.res_var, font=("Consolas", 10, "bold"), foreground=accent,
                  style="CardFormula.TLabel", justify="left").grid(row=len(rows) + 4, column=0, columnspan=3,
                                                                  sticky="w", pady=(8, 4))
        self.tip_var = tk.StringVar()
        ttk.Label(ctl, textvariable=self.tip_var, font=("Segoe UI", 9), style="CardBody.TLabel",
                  wraplength=300, justify="left").grid(row=len(rows) + 5, column=0, columnspan=3, sticky="w",
                                                        pady=(0, 12))

        right = ttk.Frame(body, style="Card.TFrame")
        right.grid(row=1, column=1, sticky="new", padx=(8, 16))
        right.columnconfigure(0, weight=1)
        self.cv = tk.Canvas(right, height=330, width=560, bg=BG, highlightthickness=0)
        self.cv.grid(row=0, column=0, sticky="ew")
        self.cv.bind("<Button-1>", self._on_press)
        self.cv.bind("<B1-Motion>", self._on_drag)
        self.cv.bind("<ButtonRelease-1>", lambda e: setattr(self, "_drag", None))
        ttk.Label(right, text=t("cpl.drag_hint"), font=("Segoe UI", 8), foreground="#777",
                  style="CardBody.TLabel").grid(row=1, column=0, sticky="w")
        self.scope = tk.Canvas(right, height=170, width=560, bg=BG, highlightthickness=0)
        self.scope.grid(row=2, column=0, sticky="ew", pady=(6, 12))

        self.bind("<Destroy>", self._on_destroy, add="+")
        self._recalc()
        self._tick()

    # ------------------------------------------------------------------
    def _recalc(self):
        k = self.k_var.get()
        if self.core_on.get():
            k = max(k, 0.95)
            self.k_var.set(k)
        self.k = k
        self.k_txt.set(f"k = {k:.2f}")
        try:
            l1 = parse_value(self.vars["l1"].get())
            l2 = parse_value(self.vars["l2"].get())
            i1 = parse_value(self.vars["i1"].get())
            f = parse_value(self.vars["f"].get())
            rl = parse_value(self.vars["rl"].get())
            if min(l1, l2, f) <= 0:
                raise ValueError
        except Exception:
            self.res_var.set(t("common.enter_valid_values"))
            return
        w = 2 * math.pi * f
        m = k * math.sqrt(l1 * l2)
        v2_open = w * m * i1
        n = math.sqrt(l2 / l1)
        if self.load_on.get() and rl > 0:
            z2 = complex(rl, w * l2)
            i2c = complex(0, -w * m * i1) / z2          # I2 = -jωM·I1 / (RL + jωL2)
            i2, ph2 = abs(i2c), math.atan2(i2c.imag, i2c.real)
            v2 = i2 * rl
        else:
            i2, ph2, v2 = 0.0, 0.0, v2_open
        self.i2_rel = min(1.0, i2 * math.sqrt(l2) / max(i1 * math.sqrt(l1), 1e-12))  # field strength ratio
        self.ph2 = ph2
        self.v2_open = v2_open
        self.params = dict(l1=l1, l2=l2, i1=i1, f=f, w=w, m=m, i2=i2, v2=v2)
        fv = lambda x, u: format_value(float(f"{x:.4g}"), u)  # noqa: E731
        lines = [f"M = k·√(L1·L2) = {fv(m, 'H')}",
                 f"v2 (open) = ω·M·I1 = {fv(v2_open, 'V')} peak",
                 f"≈ √(L2/L1) = {n:.2f}  (ideal turns ratio)"]
        if i2 > 0:
            lines.append(f"I2 = {fv(i2, 'A')} peak   V(RL) = {fv(v2, 'V')}")
            lines.append(f"P(RL) = {fv(i2 * i2 * rl / 2, 'W')}")
        self.res_var.set("\n".join(lines))
        if k < 0.2:
            tip = t("cpl.tip_loose")
        elif k > 0.9:
            tip = t("cpl.tip_tight")
        else:
            tip = t("cpl.tip_mid")
        self.tip_var.set(tip)
        self._hist = []

    # ------------------------------------------------------------------
    def _coil_x(self, W):
        """x centres of the two coils; the gap shrinks as k rises."""
        c1 = W * 0.30
        gap = 70 + (1 - self.k) * (W * 0.45)
        return c1, min(W - 70, c1 + gap)

    def _on_press(self, e):
        W = max(420, self.cv.winfo_width())
        _, c2 = self._coil_x(W)
        if abs(e.x - c2) < 50:
            self._drag = True

    def _on_drag(self, e):
        if not self._drag or self.core_on.get():
            return
        W = max(420, self.cv.winfo_width())
        c1 = W * 0.30
        gap = max(70, min(W * 0.45 + 70, e.x - c1))
        k = 1 - (gap - 70) / (W * 0.45)
        self.k_var.set(max(0.0, min(0.99, k)))
        self._recalc()

    # ------------------------------------------------------------------
    def _tick(self):
        try:
            if not self.winfo_exists():
                return
        except tk.TclError:
            return
        if not is_shown(self):
            self._after = self.after(300, self._tick)
            return
        t_start = time.perf_counter()
        self._phase = (self._phase + (TICK_MS / 1000) / PERIOD_S * 2 * math.pi) % (2 * math.pi)
        self._draw()
        spent = int((time.perf_counter() - t_start) * 1000)
        self._after = self.after(max(TICK_MS, 2 * spent), self._tick)

    def _on_destroy(self, e):
        if e.widget is self and self._after is not None:
            try:
                self.after_cancel(self._after)
            except Exception:
                pass

    def _loop(self, c, cx, cy, rx, ry, col, width, direction, dash=None, tag="f"):
        """A closed field line (ellipse) with arrowheads showing the field
        direction (direction = +1 clockwise on screen, -1 anticlockwise)."""
        pts = []
        n = 48
        for i in range(n + 1):
            a = 2 * math.pi * i / n
            pts += [cx + rx * math.cos(a), cy + ry * math.sin(a)]
        kw = {"dash": dash} if dash else {}
        c.create_line(*pts, fill=col, width=width, smooth=True, tags=tag, **kw)
        for a0 in (math.pi / 2, 3 * math.pi / 2):
            a1 = a0 + 0.15 * direction
            c.create_line(cx + rx * math.cos(a0), cy + ry * math.sin(a0), cx + rx * math.cos(a1),
                          cy + ry * math.sin(a1), fill=col, width=width, arrow="last",
                          arrowshape=(9, 11, 4), tags=tag)

    def _coil(self, c, cx, cy, current, col, label):
        """Coil cross-section: winding rows top & bottom with ⊙ (out of page)
        and ⊗ (into page) marks whose meaning flips with the current sign."""
        h, w = 70, 56
        c.create_rectangle(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2, outline="#555", width=1, dash=(3, 2))
        if self.core_on.get():
            c.create_rectangle(cx - w / 2 + 6, cy - 6, cx + w / 2 - 6, cy + 6, fill=CORE, outline="")
        mag = abs(current)
        for i in range(4):
            x = cx - w / 2 + 7 + i * (w - 14) / 3
            for y, top in ((cy - h / 2, True), (cy + h / 2, False)):
                r = 6
                fill = col if mag > 0.05 else "white"
                c.create_oval(x - r, y - r, x + r, y + r, outline="#333", width=1.5, fill="white")
                if mag > 0.05:
                    out = (current > 0) == top
                    if out:
                        c.create_oval(x - 2, y - 2, x + 2, y + 2, fill=col, outline=col)
                    else:
                        c.create_line(x - 4, y - 4, x + 4, y + 4, fill=col, width=2)
                        c.create_line(x - 4, y + 4, x + 4, y - 4, fill=col, width=2)
        c.create_text(cx, cy + h / 2 + 22, text=label, font=("Segoe UI", 9, "bold"), fill="#333")

    def _draw(self):
        c = self.cv
        c.delete("all")
        W = max(420, c.winfo_width() if c.winfo_width() > 50 else 560)
        H = 330
        cy = H / 2 - 10
        x1, x2 = self._coil_x(W)
        ph = self._phase
        i1n = math.sin(ph)                                   # normalised primary current
        di1 = math.cos(ph)                                   # its rate of change
        i2n = self.i2_rel * math.sin(ph + self.ph2) if self.load_on.get() else 0.0
        # primary field lines: 5 loops, the outer ones (fraction k) link coil 2
        n_lines = 6
        n_linked = int(round(self.k * n_lines))
        strength = abs(i1n)
        direction = 1 if i1n > 0 else -1
        for j in range(n_lines):
            linked = j >= n_lines - n_linked
            if linked:
                span = (x2 - x1) / 2 + 60 + 12 * (j - (n_lines - n_linked))
                cx_l = (x1 + x2) / 2
                ry = 55 + 16 * j
            else:
                span = 45 + 18 * j
                cx_l = x1
                ry = 50 + 15 * j
            width = 0.5 + 3.0 * strength
            col = C1 if strength > 0.08 else "#d8c9bd"
            self._loop(c, cx_l, cy, span, ry, col, width, direction)
        # secondary (Lenz) field
        if abs(i2n) > 0.03:
            d2 = 1 if i2n > 0 else -1
            for j in range(3):
                self._loop(c, x2, cy, 38 + 14 * j, 44 + 12 * j, C2, 0.5 + 2.5 * abs(i2n), d2, dash=(5, 3))
        self._coil(c, x1, cy, i1n, C1, t("cpl.coil1"))
        self._coil(c, x2, cy, i2n, C2, t("cpl.coil2"))
        # induced-voltage bar on coil 2
        v2n = -di1  # v2 ∝ -dΦ/dt (sign convention: opposes the change)
        bx = x2 + 50
        c.create_rectangle(bx, cy - 50, bx + 12, cy + 50, outline="#999")
        c.create_rectangle(bx, cy, bx + 12, cy - 50 * v2n, fill=C2, outline="")
        c.create_text(bx + 6, cy - 62, text="v2", font=("Segoe UI", 8, "bold"), fill=C2)
        c.create_text(12, 14, anchor="nw", font=("Segoe UI", 9, "bold"), fill="#555",
                      text=t("cpl.caption").format(k=self.k, n=int(round(self.k * 6))))
        self._draw_scope(i1n, v2n, i2n)

    def _draw_scope(self, i1n, v2n, i2n):
        s = self.scope
        s.delete("all")
        W = max(420, s.winfo_width() if s.winfo_width() > 50 else 560)
        H = 170
        L, R, T, B = 40, W - 10, 18, H - 22
        mid = (T + B) / 2
        amp = (B - T) / 2 - 6
        s.create_rectangle(L, T, R, B, outline="#bbb")
        s.create_line(L, mid, R, mid, fill="#ccc")
        # full two-period curves with a moving cursor (the "now" line)
        n = 200
        for fn, col, dash, lbl in ((lambda a: math.sin(a), C1, None, "i1"),
                                   (lambda a: -math.cos(a) * min(1.0, self.k * 1.4 + 0.1), C2, None, "v2"),
                                   (lambda a: (self.i2_rel * math.sin(a + self.ph2)) if self.load_on.get() else 0,
                                    "#6A4C93", (4, 3), "i2")):
            pts = []
            for i in range(n + 1):
                a = 4 * math.pi * i / n
                pts += [L + (R - L) * i / n, mid - amp * fn(a)]
            kw = {"dash": dash} if dash else {}
            s.create_line(*pts, fill=col, width=2, smooth=True, **kw)
        xnow = L + (R - L) * (self._phase / (4 * math.pi))
        for k in range(2):
            x = xnow + k * (R - L) / 2
            s.create_line(x, T, x, B, fill="#d97706", width=1.5)
        s.create_text(L + 4, T - 9, anchor="w", font=("Segoe UI", 8, "bold"), fill=C1, text="i1 (" + t("cpl.primary") + ")")
        s.create_text(L + 120, T - 9, anchor="w", font=("Segoe UI", 8, "bold"), fill=C2,
                      text="v2 = M·di1/dt")
        if self.load_on.get():
            s.create_text(L + 240, T - 9, anchor="w", font=("Segoe UI", 8, "bold"), fill="#6A4C93", text="i2 (Lenz)")
        s.create_text((L + R) / 2, H - 8, text=t("cpl.scope_hint"), font=("Segoe UI", 8), fill="#666")
