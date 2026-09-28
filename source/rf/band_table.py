"""
rf/band_table.py - RF Band Explorer.

  * Frequency lookup: ITU band, IEEE / NATO letter band, wavelength,
    antenna lengths and every allocation in the database that contains it.
  * Spectrum ruler (3 kHz - 300 GHz, log scale) with the ITU bands, the IEEE
    radar letters and every allocation; click to look up / select.
  * Filterable list of allocations; each one shows per-region ranges, power
    and access rules, the channel plan with its centre-frequency formula, a
    drawing of the channels and practical notes.
  * Reference tables: ITU bands, IEEE and NATO letter bands.

Engineering quick reference only - always confirm with the regulator.
"""
import math
import tkinter as tk
from tkinter import ttk

from i18n import t, get_language
from widgets import FONT_H1, FONT_H2, FONT_BODY, ScrollableFrame, parse_value, debounce
from rf import band_data as D

ACCENT_C = "#2A9D8F"
C0 = 299792458.0
F_MIN, F_MAX = 3e3, 300e9      # ruler span (Hz)


def tr(d):
    return d.get(get_language(), d["en"]) if isinstance(d, dict) else d


def fmt_hz(f):
    if f >= 1e9:
        return f"{f / 1e9:.6g} GHz"
    if f >= 1e6:
        return f"{f / 1e6:.6g} MHz"
    if f >= 1e3:
        return f"{f / 1e3:.6g} kHz"
    return f"{f:.4g} Hz"


def fmt_len(m):
    if m >= 1000:
        return f"{m / 1000:.4g} km"
    if m >= 1:
        return f"{m:.4g} m"
    if m >= 0.01:
        return f"{m * 100:.4g} cm"
    return f"{m * 1000:.4g} mm"


def parse_freq(text):
    s = text.strip().replace(",", ".")
    for suf in ("Hz", "hz", "HZ"):
        if s.endswith(suf):
            s = s[: -len(suf)]
    s = s.strip()
    # "2.4 G" -> "2.4G";  lower-case g/k accepted
    s = s.replace(" ", "")
    if s and s[-1] in "gGkK":
        s = s[:-1] + {"g": "G", "G": "G", "k": "k", "K": "k"}[s[-1]]
    return parse_value(s)


class RFBandsView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        scroll = ScrollableFrame(self, style="Tab.TFrame")
        scroll.grid(row=0, column=0, sticky="nsew")
        body = scroll.body
        body.columnconfigure(0, weight=1)
        self.body = body
        self._sel_id = None
        self._freq = 2.45e9

        tk.Frame(body, bg=ACCENT_C, height=6).grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 0))
        ttk.Label(body, text=t("rfx.title"), font=FONT_H1, style="TabTitle.TLabel")\
            .grid(row=1, column=0, sticky="w", padx=16, pady=(10, 2))
        intro = ttk.Label(body, text=t("rfx.intro"), style="TabTitle.TLabel", font=FONT_BODY, justify="left", wraplength=1100)
        intro.grid(row=2, column=0, sticky="w", padx=16, pady=(0, 8))
        body.bind("<Configure>", lambda e: intro.configure(wraplength=max(400, e.width - 40)), add="+")

        self._build_lookup(body, 3)
        self._build_ruler(body, 4)
        self._build_browser(body, 5)
        self._build_reference(body, 6)

        disc = ttk.Label(body, text=t("rf.bands.disclaimer"), style="TabTitle.TLabel",
                         font=("Segoe UI", 9, "italic"), foreground="#b3691d", wraplength=1100, justify="left")
        disc.grid(row=7, column=0, sticky="w", padx=16, pady=(4, 20))
        body.bind("<Configure>", lambda e: disc.configure(wraplength=max(400, e.width - 40)), add="+")

        self._lookup()
        self._select(D.BANDS[4]["id"])

    # ------------------------------------------------------------------
    # Frequency lookup
    # ------------------------------------------------------------------
    def _card(self, parent, row, title):
        card = ttk.Frame(parent, style="Card.TFrame", padding=(14, 10))
        card.grid(row=row, column=0, sticky="ew", padx=16, pady=6)
        card.columnconfigure(0, weight=1)
        ttk.Label(card, text=title, font=FONT_H2, foreground=ACCENT_C, style="CardTitle.TLabel")\
            .grid(row=0, column=0, sticky="w", pady=(0, 6))
        return card

    def _build_lookup(self, parent, row):
        card = self._card(parent, row, t("rfx.lookup_title"))
        top = ttk.Frame(card, style="Card.TFrame")
        top.grid(row=1, column=0, sticky="w")
        ttk.Label(top, text=t("rfx.freq_label"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self.f_var = tk.StringVar(value="2.45 GHz")
        e = ttk.Entry(top, textvariable=self.f_var, width=16, font=("Consolas", 11))
        e.pack(side="left", padx=6)
        e.bind("<Return>", lambda ev: self._lookup())
        e.bind("<KeyRelease>", lambda ev: self._lookup(quiet=True))
        ttk.Button(top, text=t("rfx.lookup_btn"), command=self._lookup).pack(side="left", padx=4)
        ttk.Label(top, text=t("rfx.lookup_hint"), font=("Segoe UI", 8), foreground="#777",
                  style="CardBody.TLabel").pack(side="left", padx=8)
        ex = ttk.Frame(card, style="Card.TFrame")
        ex.grid(row=2, column=0, sticky="w", pady=(4, 2))
        for txt in ("125 kHz", "13.56 MHz", "100 MHz", "433.92 MHz", "868 MHz", "1575.42 MHz", "2.45 GHz",
                    "5.8 GHz", "24.125 GHz", "77 GHz"):
            ttk.Button(ex, text=txt, style="Small.TButton",
                       command=lambda v=txt: (self.f_var.set(v), self._lookup())).pack(side="left", padx=2)
        self.lookup_var = tk.StringVar()
        ttk.Label(card, textvariable=self.lookup_var, font=("Consolas", 10, "bold"), foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left").grid(row=3, column=0, sticky="w", pady=(6, 2))
        self.hits_frame = ttk.Frame(card, style="Card.TFrame")
        self.hits_frame.grid(row=4, column=0, sticky="w")

    def _lookup(self, quiet=False):
        try:
            f = parse_freq(self.f_var.get())
            if f <= 0:
                raise ValueError
        except Exception:
            if not quiet:
                self.lookup_var.set(t("rfx.bad_freq"))
            return
        self._freq = f
        lam = C0 / f
        itu = next((b for b in D.ITU_BANDS if b[2] <= f < b[3]), None)
        ieee = next((b[0] for b in D.IEEE_BANDS if b[1] <= f < b[2]), "-")
        nato = next((b[0] for b in D.NATO_BANDS if b[1] <= f < b[2]), "-")
        itu_txt = f"{t('rfx.itu_band')} {itu[0]}: {itu[1]}  ({tr(itu[4])})" if itu else f"{t('rfx.itu_band')}: -"
        fspl1 = 20 * math.log10(4 * math.pi * 1.0 / lam)
        fspl1k = fspl1 + 60
        lines = [
            f"f = {fmt_hz(f)}    T = 1/f = {self._fmt_t(1 / f)}    ω = 2πf = {2 * math.pi * f:.4g} rad/s",
            itu_txt,
            f"IEEE: {ieee}    NATO: {nato}",
            f"λ = c/f = {fmt_len(lam)}    λ/2 {t('rfx.dipole')} ≈ {fmt_len(0.475 * lam)}    "
            f"λ/4 {t('rfx.monopole')} ≈ {fmt_len(0.25 * lam * 0.95)}",
            f"{t('rfx.fspl')}: 1 m = {fspl1:.1f} dB,  1 km = {fspl1k:.1f} dB",
        ]
        self.lookup_var.set("\n".join(lines))
        for w in self.hits_frame.winfo_children():
            w.destroy()
        fm = f / 1e6
        hits = [b for b in D.BANDS if b["lo"] <= fm <= b["hi"]]
        ttk.Label(self.hits_frame, text=t("rfx.inside") + (":" if hits else ": " + t("rfx.none")),
                  font=("Segoe UI", 9, "bold"), style="CardBody.TLabel").grid(row=0, column=0, sticky="w")
        for i, b in enumerate(hits):
            ttk.Button(self.hits_frame, text=tr(b["name"]), style="Small.TButton",
                       command=lambda bid=b["id"]: self._select(bid, scroll=True))\
                .grid(row=1 + i // 4, column=i % 4, sticky="w", padx=2, pady=2)
        self._draw_ruler()

    @staticmethod
    def _fmt_t(s):
        for unit, k in (("s", 1), ("ms", 1e-3), ("µs", 1e-6), ("ns", 1e-9), ("ps", 1e-12)):
            if s >= k:
                return f"{s / k:.4g} {unit}"
        return f"{s * 1e15:.4g} fs"

    # ------------------------------------------------------------------
    # Spectrum ruler
    # ------------------------------------------------------------------
    def _build_ruler(self, parent, row):
        card = self._card(parent, row, t("rfx.ruler_title"))
        ttk.Label(card, text=t("rfx.ruler_hint"), font=("Segoe UI", 8), foreground="#777",
                  style="CardBody.TLabel").grid(row=1, column=0, sticky="w")
        self.rc = tk.Canvas(card, height=250, bg="white", highlightthickness=0)
        self.rc.grid(row=2, column=0, sticky="ew", pady=(4, 0))
        self.rc.bind("<Configure>", debounce(self.rc, lambda *a: self._draw_ruler(), 100))
        self.rc.bind("<Button-1>", self._ruler_click)
        self.rc.bind("<Motion>", self._ruler_motion)
        self.ruler_info = tk.StringVar()
        ttk.Label(card, textvariable=self.ruler_info, font=("Segoe UI", 9), style="CardBody.TLabel")\
            .grid(row=3, column=0, sticky="w", pady=(2, 0))
        leg = ttk.Frame(card, style="Card.TFrame")
        leg.grid(row=4, column=0, sticky="w", pady=(4, 0))
        for i, (cid, col, name) in enumerate(D.CATEGORIES):
            f = ttk.Frame(leg, style="Card.TFrame")
            f.grid(row=i // 6, column=i % 6, sticky="w", padx=(0, 12))
            tk.Label(f, bg=col, width=2).pack(side="left")
            ttk.Label(f, text=tr(name), font=("Segoe UI", 8), style="CardBody.TLabel").pack(side="left", padx=3)

    def _fx(self, f):
        W = max(self.rc.winfo_width(), 400)
        return 40 + (W - 60) * (math.log10(f) - math.log10(F_MIN)) / (math.log10(F_MAX) - math.log10(F_MIN))

    def _xf(self, x):
        W = max(self.rc.winfo_width(), 400)
        a = (x - 40) / (W - 60)
        return 10 ** (math.log10(F_MIN) + a * (math.log10(F_MAX) - math.log10(F_MIN)))

    def _draw_ruler(self):
        c = getattr(self, "rc", None)
        if c is None:
            return
        c.delete("all")
        W = max(c.winfo_width(), 400)
        itu_cols = ["#fde68a", "#fcd34d", "#bbf7d0", "#86efac", "#bfdbfe", "#93c5fd", "#ddd6fe", "#c4b5fd",
                    "#fecaca", "#fca5a5"]
        # ITU bands
        for i, b in enumerate(D.ITU_BANDS):
            lo, hi = max(b[2], F_MIN), min(b[3], F_MAX)
            if hi <= lo:
                continue
            x0, x1 = self._fx(lo), self._fx(hi)
            c.create_rectangle(x0, 6, x1, 30, fill=itu_cols[i % len(itu_cols)], outline="white")
            c.create_text((x0 + x1) / 2, 18, text=b[1], font=("Segoe UI", 9, "bold"), fill="#333")
        c.create_text(4, 18, text="ITU", anchor="w", font=("Segoe UI", 7, "bold"), fill="#555")
        # IEEE letters
        for i, (name, lo, hi) in enumerate(D.IEEE_BANDS):
            x0, x1 = self._fx(lo), self._fx(hi)
            c.create_rectangle(x0, 33, x1, 49, fill="#f1f5f9" if i % 2 else "#e2e8f0", outline="white")
            if x1 - x0 > 12:
                c.create_text((x0 + x1) / 2, 41, text=name.split()[0], font=("Segoe UI", 7, "bold"), fill="#333")
        c.create_text(4, 41, text="IEEE", anchor="w", font=("Segoe UI", 7, "bold"), fill="#555")
        # allocation lanes
        lanes = []
        self._ruler_items = {}
        top = 56
        for b in sorted(D.BANDS, key=lambda b: b["lo"]):
            x0, x1 = self._fx(b["lo"] * 1e6), self._fx(b["hi"] * 1e6)
            if x1 - x0 < 4:
                m = (x0 + x1) / 2
                x0, x1 = m - 2, m + 2
            for li, end in enumerate(lanes):
                if x0 > end + 2:
                    lanes[li] = x1
                    break
            else:
                lanes.append(x1)
                li = len(lanes) - 1
            y = top + li * 13
            sel = b["id"] == self._sel_id
            it = c.create_rectangle(x0, y, x1, y + 10, fill=D.CAT_COLOR[b["cat"]],
                                    outline="#111" if sel else "", width=2 if sel else 1)
            self._ruler_items[it] = b["id"]
        ybot = top + len(lanes) * 13 + 6
        if int(c.cget("height")) != ybot + 22:
            c.configure(height=ybot + 22)
        # decade axis
        for e in range(4, 12):
            f = 10 ** e
            x = self._fx(f)
            c.create_line(x, 52, x, ybot, fill="#e5e7eb")
            c.create_text(x, ybot + 10, text=fmt_hz(f).replace(".0 ", " "), font=("Segoe UI", 7), fill="#555")
        for it in self._ruler_items:
            c.tag_raise(it)
        # cursor
        if F_MIN <= self._freq <= F_MAX:
            x = self._fx(self._freq)
            c.create_line(x, 2, x, ybot, fill="#dc2626", width=2)
            c.create_text(x + 3, ybot, text=fmt_hz(self._freq), anchor="sw", font=("Segoe UI", 8, "bold"),
                          fill="#dc2626")

    def _ruler_hit(self, e):
        for it in self.rc.find_overlapping(e.x - 2, e.y - 2, e.x + 2, e.y + 2):
            if it in getattr(self, "_ruler_items", {}):
                return self._ruler_items[it]
        return None

    def _ruler_click(self, e):
        bid = self._ruler_hit(e)
        if bid:
            self._select(bid, scroll=False)
            return
        f = self._xf(e.x)
        if F_MIN <= f <= F_MAX:
            self.f_var.set(fmt_hz(float(f"{f:.3g}")))
            self._lookup()

    def _ruler_motion(self, e):
        bid = self._ruler_hit(e)
        if bid:
            b = D.BAND_BY_ID[bid]
            self.ruler_info.set(f"{tr(b['name'])}:  {fmt_hz(b['lo'] * 1e6)} – {fmt_hz(b['hi'] * 1e6)}")
        else:
            self.ruler_info.set(f"≈ {fmt_hz(float(f'{self._xf(e.x):.3g}'))}")

    # ------------------------------------------------------------------
    # Allocation browser
    # ------------------------------------------------------------------
    def _build_browser(self, parent, row):
        card = self._card(parent, row, t("rfx.browser_title"))
        self.browser_card = card
        flt = ttk.Frame(card, style="Card.TFrame")
        flt.grid(row=1, column=0, sticky="w", pady=(0, 4))
        ttk.Label(flt, text=t("rfx.category"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self._cat_labels = [t("rfx.all")] + [tr(c[2]) for c in D.CATEGORIES]
        self.cat_var = tk.StringVar(value=self._cat_labels[0])
        cb = ttk.Combobox(flt, textvariable=self.cat_var, values=self._cat_labels, state="readonly", width=30)
        cb.pack(side="left", padx=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self._fill_list())
        ttk.Label(flt, text=t("rfx.search"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left", padx=(12, 0))
        self.q_var = tk.StringVar()
        q = ttk.Entry(flt, textvariable=self.q_var, width=22)
        q.pack(side="left", padx=6)
        q.bind("<KeyRelease>", lambda e: self._fill_list())

        pane = ttk.Frame(card, style="Card.TFrame")
        pane.grid(row=2, column=0, sticky="ew")
        pane.columnconfigure(1, weight=1)
        lst = ttk.Frame(pane, style="Card.TFrame")
        lst.grid(row=0, column=0, sticky="nsw")
        self.tree = ttk.Treeview(lst, columns=("name", "range"), show="headings", height=16, selectmode="browse")
        self.tree.heading("name", text=t("rf.bands.col_band"))
        self.tree.heading("range", text=t("rfx.envelope"))
        self.tree.column("name", width=250, stretch=False)
        self.tree.column("range", width=150, stretch=False)
        self.tree.grid(row=0, column=0, sticky="ns")
        vsb = ttk.Scrollbar(lst, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree)
        for cid, col, _ in D.CATEGORIES:
            self.tree.tag_configure(cid, foreground=col)

        self.detail = ttk.Frame(pane, style="Card.TFrame")
        self.detail.grid(row=0, column=1, sticky="nsew", padx=(14, 0))
        self.detail.columnconfigure(0, weight=1)
        self.detail.bind("<Configure>", debounce(self.detail, self._on_detail_resize, 100), add="+")
        self._wrap_labels = []
        self._fill_list()

    def _fill_list(self):
        cat_idx = self._cat_labels.index(self.cat_var.get())
        cat = D.CATEGORIES[cat_idx - 1][0] if cat_idx > 0 else None
        q = self.q_var.get().strip().lower()
        self.tree.delete(*self.tree.get_children())
        for b in D.BANDS:
            if cat and b["cat"] != cat:
                continue
            text = (tr(b["name"]) + " " + b.get("tech", "") + " " + " ".join(b["ranges"].values())).lower()
            if q and q not in text:
                continue
            rng = f"{fmt_hz(b['lo'] * 1e6)} – {fmt_hz(b['hi'] * 1e6)}"
            self.tree.insert("", "end", iid=b["id"], values=(tr(b["name"]), rng), tags=(b["cat"],))
        if self._sel_id and self.tree.exists(self._sel_id):
            self.tree.selection_set(self._sel_id)

    def _on_tree(self, _e):
        sel = self.tree.selection()
        if sel and sel[0] != self._sel_id:
            self._select(sel[0])

    def _select(self, bid, scroll=False):
        self._sel_id = bid
        if self.tree.exists(bid):
            if self.tree.selection() != (bid,):
                self.tree.selection_set(bid)
            self.tree.see(bid)
        self._show_detail(D.BAND_BY_ID[bid])
        self._draw_ruler()

    def _on_detail_resize(self, e):
        for lbl, off in self._wrap_labels:
            try:
                lbl.configure(wraplength=max(200, e.width - off))
            except tk.TclError:
                pass
        if getattr(self, "_chan_band", None) is not None:
            self._draw_channels()

    def _show_detail(self, b):
        d = self.detail
        for w in d.winfo_children():
            w.destroy()
        self._wrap_labels = []
        width = max(d.winfo_width(), 520)
        col = D.CAT_COLOR[b["cat"]]
        tk.Frame(d, bg=col, height=4).grid(row=0, column=0, sticky="ew")
        ttk.Label(d, text=tr(b["name"]), font=FONT_H2, foreground=col, style="CardTitle.TLabel")\
            .grid(row=1, column=0, sticky="w", pady=(4, 0))
        cat_name = tr(next(c[2] for c in D.CATEGORIES if c[0] == b["cat"]))
        tech = ttk.Label(d, text=f"{cat_name}  ·  {b.get('tech', '')}", font=("Segoe UI", 9, "italic"),
                         style="CardBody.TLabel", wraplength=width - 20, justify="left")
        tech.grid(row=2, column=0, sticky="w", pady=(0, 6))
        self._wrap_labels.append((tech, 20))

        grid = ttk.Frame(d, style="Card.TFrame")
        grid.grid(row=3, column=0, sticky="ew")
        heads = (t("rfx.region"), t("rfx.range"), t("rfx.power"), t("rfx.access"))
        weights = (0, 3, 2, 2)
        for j, h in enumerate(heads):
            grid.columnconfigure(j, weight=weights[j])
            tk.Label(grid, text=h, font=("Segoe UI", 9, "bold"), bg="#1f2a44", fg="white", anchor="w", padx=6)\
                .grid(row=0, column=j, sticky="ew")
        colw = [(width - 140) * w / 7 for w in weights]
        for i, (rk, rname) in enumerate(D.REGIONS, start=1):
            bg = "#f8fafc" if i % 2 else "#eef2f7"
            vals = (tr(rname), b["ranges"].get(rk, "-"), b["power"].get(rk, "-"), b["access"].get(rk, "-"))
            for j, v in enumerate(vals):
                lbl = tk.Label(grid, text=v, font=("Segoe UI", 9, "bold" if j == 0 else "normal"), bg=bg,
                               anchor="nw", justify="left", padx=6, pady=3,
                               wraplength=130 if j == 0 else max(120, colw[j]))
                lbl.grid(row=i, column=j, sticky="nsew")

        ch = b["chan"]
        cp = ttk.Frame(d, style="Card.TFrame")
        cp.grid(row=4, column=0, sticky="ew", pady=(8, 0))
        ttk.Label(cp, text=t("rfx.chan_plan"), font=("Segoe UI", 10, "bold"), style="CardBody.TLabel")\
            .grid(row=0, column=0, columnspan=2, sticky="w")
        for i, (key, lab) in enumerate((("count", "rfx.ch_count"), ("spacing", "rfx.ch_spacing"),
                                        ("width", "rfx.ch_width"), ("formula", "rfx.ch_formula")), start=1):
            ttk.Label(cp, text=t(lab) + ":", font=("Segoe UI", 9, "bold"), style="CardBody.TLabel")\
                .grid(row=i, column=0, sticky="nw", padx=(0, 8))
            v = ttk.Label(cp, text=ch.get(key, "-"), font=("Consolas", 9) if key == "formula" else ("Segoe UI", 9),
                          foreground="#1f2a44", style="CardBody.TLabel", wraplength=width - 160, justify="left")
            v.grid(row=i, column=1, sticky="w")
            self._wrap_labels.append((v, 160))

        self._chan_band = None
        if b.get("plot"):
            self._chan_band = b
            self.chc = tk.Canvas(d, height=162, bg="white", highlightthickness=0)
            self.chc.grid(row=5, column=0, sticky="ew", pady=(8, 0))
            self.chc.bind("<Configure>", debounce(self.chc, lambda *a: self._draw_channels(), 100))
            self._draw_channels()

        notes = ttk.Label(d, text=t("rfx.note") + " " + tr(b["notes"]), font=FONT_BODY, style="CardBody.TLabel",
                          wraplength=width - 20, justify="left")
        notes.grid(row=6, column=0, sticky="w", pady=(8, 4))
        self._wrap_labels.append((notes, 20))

    def _draw_channels(self):
        b = self._chan_band
        c = getattr(self, "chc", None)
        if b is None or c is None:
            return
        try:
            c.delete("all")
        except tk.TclError:
            return
        gen, lo, hi = b["plot"]
        chans = gen()
        W = max(c.winfo_width(), 300)
        L, R = 10, W - 10
        X = lambda f: L + (R - L) * (f - lo) / (hi - lo)  # noqa: E731
        # band envelope
        bx0, bx1 = X(max(lo, b["lo"])), X(min(hi, b["hi"]))
        c.create_rectangle(bx0, 4, bx1, 118, fill="#f0fdfa", outline="")
        # lanes for overlapping channels
        lanes = []
        placed = []
        for fc, bw, lab in sorted(chans, key=lambda x: x[0] - x[1] / 2):
            a, z = fc - bw / 2, fc + bw / 2
            for li, end in enumerate(lanes):
                if a >= end - 1e-9:
                    lanes[li] = z
                    break
            else:
                lanes.append(z)
                li = len(lanes) - 1
            placed.append((fc, bw, lab, li))
        nl = max(1, len(lanes))
        lh = min(18, 100 / nl)
        col = D.CAT_COLOR[b["cat"]]
        for fc, bw, lab, li in placed:
            x0, x1 = X(fc - bw / 2), X(fc + bw / 2)
            if x1 - x0 < 1.5:
                x0, x1 = X(fc) - 0.75, X(fc) + 0.75
            y0 = 8 + li * lh
            c.create_rectangle(x0, y0, x1, y0 + lh - 2, fill=col, outline="white", stipple="" if nl < 3 else "")
            if lab and x1 - x0 > 7 * len(lab) and lh >= 10:
                c.create_text((x0 + x1) / 2, y0 + lh / 2 - 1, text=lab, fill="white",
                              font=("Segoe UI", 7, "bold"))
        # axis
        c.create_line(L, 120, R, 120, fill="#555")
        span = hi - lo
        step = 10 ** math.floor(math.log10(span / 5))
        for m in (1, 2, 5, 10):
            if span / (step * m) <= 8:
                step *= m
                break
        f = math.ceil(lo / step) * step
        while f <= hi:
            x = X(f)
            c.create_line(x, 120, x, 125, fill="#555")
            c.create_text(x, 134, text=fmt_hz(f * 1e6), font=("Segoe UI", 7), fill="#444")
            f += step
        c.create_text(R, 154, text=t("rfx.chan_drawing").format(n=len(chans)), anchor="e",
                      font=("Segoe UI", 7), fill="#777")

    # ------------------------------------------------------------------
    # Reference tables
    # ------------------------------------------------------------------
    def _build_reference(self, parent, row):
        card = self._card(parent, row, t("rfx.ref_title"))
        ttk.Label(card, text=t("rfx.itu_rule"), font=("Segoe UI", 9), style="CardBody.TLabel",
                  wraplength=1000, justify="left").grid(row=1, column=0, sticky="w", pady=(0, 4))
        tv = ttk.Treeview(card, columns=("n", "sym", "range", "lam", "use"), show="headings",
                          height=len(D.ITU_BANDS))
        for col, key, w in (("n", "rfx.col_n", 40), ("sym", "rfx.col_sym", 60), ("range", "rfx.range", 150),
                            ("lam", "rfx.col_lambda", 200), ("use", "rfx.col_use", 520)):
            tv.heading(col, text=t(key))
            tv.column(col, width=w, stretch=(col == "use"))
        for n, sym, lo, hi, lam, use in D.ITU_BANDS:
            tv.insert("", "end", values=(n, sym, f"{fmt_hz(lo)} – {fmt_hz(hi)}", tr(lam), tr(use)))
        tv.grid(row=2, column=0, sticky="ew")

        row2 = ttk.Frame(card, style="Card.TFrame")
        row2.grid(row=3, column=0, sticky="w", pady=(10, 0))
        for j, (title, data) in enumerate(((t("rfx.ieee_title"), D.IEEE_BANDS), (t("rfx.nato_title"), D.NATO_BANDS))):
            f = ttk.Frame(row2, style="Card.TFrame")
            f.grid(row=0, column=j, sticky="nw", padx=(0, 20))
            ttk.Label(f, text=title, font=("Segoe UI", 10, "bold"), style="CardBody.TLabel").pack(anchor="w")
            tv2 = ttk.Treeview(f, columns=("b", "r"), show="headings", height=len(data))
            tv2.heading("b", text=t("rfx.col_letter"))
            tv2.heading("r", text=t("rfx.range"))
            tv2.column("b", width=70)
            tv2.column("r", width=190)
            for name, lo, hi in data:
                tv2.insert("", "end", values=(name, f"{fmt_hz(lo) if lo else '0'} – {fmt_hz(hi)}"))
            tv2.pack(anchor="w")
        ttk.Label(card, text=tr(D.ITU_REGIONS), font=("Segoe UI", 9, "italic"), style="CardBody.TLabel",
                  wraplength=1000, justify="left").grid(row=4, column=0, sticky="w", pady=(8, 0))
