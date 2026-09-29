"""
tabs/smd_panel.py - "SMD & Codes" sub-tab used by the Resistor, Capacitor
and Inductor pages.

  * Code -> value: type what is printed on the part; every plausible
    reading is listed with the scheme name and the working, and the chip is
    drawn to scale in the chosen package with the marking on it.
  * Value -> code: all the markings that describe a value (and whether
    they are exact).
  * Package sizes and reference tables (EIA-96, EIA-198, voltage and
    tolerance letters...).
  * Capacitors additionally get the colour-band code used on older
    film/ceramic parts.
"""
import tkinter as tk
from tkinter import ttk

import smd_codes as sc
from data import COLOR_CODE, DIGIT_COLORS
from drawing import draw_resistor
from widgets import ScrollableFrame, parse_value, FONT_H2, FONT_BODY, FONT_MONO
from i18n import t, register, tr

register({
    "smd.subtab": ("SMD & Codes", "SMD și coduri"),
    "smd.decode_title": ("Marking → value", "Marcaj → valoare"),
    "smd.encode_title": ("Value → marking", "Valoare → marcaj"),
    "smd.code": ("Printed code:", "Codul tipărit:"),
    "smd.examples": ("Try:", "Încearcă:"),
    "smd.package": ("Package:", "Capsulă:"),
    "smd.value": ("Value:", "Valoare:"),
    "smd.col.scheme": ("Marking system", "Sistem de marcare"),
    "smd.col.code": ("Code", "Cod"),
    "smd.col.exact": ("Exact?", "Exact?"),
    "smd.yes": ("yes", "da"),
    "smd.no": ("rounded", "rotunjit"),
    "smd.unknown": ("Not a code I recognise. Examples of valid markings are listed above.",
                    "Nu recunosc acest cod. Exemple de marcaje valide sunt mai sus."),
    "smd.ambiguous": ("This marking can be read more than one way — the most likely reading is first.",
                      "Acest marcaj poate fi citit în mai multe feluri — cea mai probabilă variantă este prima."),
    "smd.reading": ("Reading", "Varianta"),
    "smd.tol": ("tolerance", "toleranță"),
    "smd.volt": ("rated voltage", "tensiune nominală"),
    "smd.nearest": ("Nearest standard values:", "Cele mai apropiate valori standard:"),
    "smd.pkg_info": ("{imp} (metric {met}): {l} × {w} mm", "{imp} (metric {met}): {l} × {w} mm"),
    "smd.pkg_power": ("typical resistor rating ≈ {p}", "putere tipică rezistor ≈ {p}"),
    "smd.tables": ("Reference tables", "Tabele de referință"),
    "smd.table": ("Table:", "Tabel:"),
    "smd.tb.e96": ("EIA-96 codes (01–96)", "Coduri EIA-96 (01–96)"),
    "smd.tb.e96m": ("EIA-96 multiplier letters", "Litere multiplicator EIA-96"),
    "smd.tb.e198": ("EIA-198 capacitor letters", "Litere condensator EIA-198"),
    "smd.tb.volt": ("Voltage codes (ceramic/film)", "Coduri de tensiune (ceramic/film)"),
    "smd.tb.tvolt": ("Voltage letters (tantalum)", "Litere de tensiune (tantal)"),
    "smd.tb.tol": ("Tolerance letters", "Litere de toleranță"),
    "smd.tb.pkg": ("Package sizes", "Dimensiuni capsule"),
    "smd.tb.tcase": ("Tantalum case sizes", "Capsule tantal"),
    "smd.melf_note": ("MELF (cylindrical) SMD resistors use the same colour bands as through-hole parts — "
                      "use the Color Code tab for them.",
                      "Rezistoarele SMD MELF (cilindrice) folosesc aceleași benzi colorate ca cele cu terminale — "
                      "folosește tab-ul Cod Culori pentru ele."),
    "smd.mlcc_note": ("Most ceramic chip capacitors (MLCC) carry NO marking at all — the value is only on the reel "
                      "label. Codes appear on tantalum/polymer/electrolytic parts and on some larger ceramics.",
                      "Majoritatea condensatoarelor ceramice SMD (MLCC) NU au niciun marcaj — valoarea e doar pe "
                      "eticheta rolei. Codurile apar pe condensatoare cu tantal/polimer/electrolitice și pe unele "
                      "ceramice mai mari."),
    "smd.ind_note": ("Chip inductors are often unmarked or colour-dotted; the 3-digit code is in µH, "
                     "R marks the decimal point in µH and N the decimal point in nH.",
                     "Bobinele SMD sunt adesea nemarcate sau cu puncte colorate; codul din 3 cifre e în µH, "
                     "R marchează virgula în µH, iar N virgula în nH."),
    "smd.cband_title": ("Colour bands (older film / ceramic capacitors, value in pF)",
                        "Benzi colorate (condensatoare vechi film/ceramice, valoare în pF)"),
    "smd.cband.volt": ("Voltage band", "Banda de tensiune"),
    # scheme names
    "smd.s.jumper": ("Zero-ohm jumper", "Șunt de zero ohmi"),
    "smd.s.rnot": ("R-notation (R = decimal point, Ω)", "Notația R (R = virgulă, Ω)"),
    "smd.s.mnot": ("m-notation (milliohm current sense)", "Notația m (miliohmi, șunt de curent)"),
    "smd.s.eia96": ("EIA-96 (1%)", "EIA-96 (1%)"),
    "smd.s.three": ("3-digit code", "Cod din 3 cifre"),
    "smd.s.four": ("4-digit code", "Cod din 4 cifre"),
    "smd.s.plain": ("Plain value", "Valoare directă"),
    "smd.s.tant": ("Polarised (tantalum) code: voltage letter + pF code",
                   "Cod polarizat (tantal): literă tensiune + cod pF"),
    "smd.s.cap3": ("3-digit pF code", "Cod pF din 3 cifre"),
    "smd.s.cap2": ("Value in pF", "Valoare în pF"),
    "smd.s.cap4": ("4-digit pF code", "Cod pF din 4 cifre"),
    "smd.s.eia198": ("EIA-198 letter + digit", "EIA-198 literă + cifră"),
    "smd.s.letterpoint": ("Unit letter as decimal point (4n7)", "Litera unității pe post de virgulă (4n7)"),
    "smd.s.rnot_pf": ("R-notation in pF", "Notația R în pF"),
    "smd.s.ind_r": ("R-notation (µH)", "Notația R (µH)"),
    "smd.s.ind_n": ("N-notation (nH)", "Notația N (nH)"),
    "smd.s.ind3": ("3-digit µH code", "Cod µH din 3 cifre"),
    "smd.s.ind3_nh": ("3-digit code in nH (some RF chip inductors)", "Cod din 3 cifre în nH (unele bobine RF)"),
    "smd.s.ind2": ("Value in µH", "Valoare în µH"),
    # notes
    "smd.n.jumper": ("A 0 Ω part is used as a bridge / optional link on the PCB.",
                     "O piesă de 0 Ω e folosită ca punte / legătură opțională pe cablaj."),
    "smd.n.rnot": ("Used below 10 Ω where a 3-digit code cannot express the value.",
                   "Folosită sub 10 Ω, unde codul din 3 cifre nu poate exprima valoarea."),
    "smd.n.three_bar": ("A bar under the code (e.g. 1̲0̲2̲) marks a 1% part using the 3-digit system.",
                        "O bară sub cod (ex. 1̲0̲2̲) indică o piesă de 1% care folosește sistemul din 3 cifre."),
    "smd.n.tant": ("The stripe / bevel marks the + (anode) side on tantalum capacitors.",
                   "Dunga / teșitura marchează partea + (anod) la condensatoarele cu tantal."),
    "smd.n.eia198": ("EIA-198 is case sensitive: 'a', 'b', 'd', 'e', 'f', 'm', 'n', 't', 'y' are different values from the capitals.",
                     "EIA-198 face diferența între litere mari și mici: 'a', 'b', 'd', 'e', 'f', 'm', 'n', 't', 'y' au alte valori decât majusculele."),
    "smd.n.not_e96": ("not an E96 value, EIA-96 can't mark it", "nu e valoare E96, EIA-96 nu o poate marca"),
    "smd.n.not_eia198": ("no EIA-198 letter for these digits", "nu există literă EIA-198 pentru aceste cifre"),
    "smd.n.ind3": ("Same rule as resistors: two digits then the number of zeros, in µH.",
                   "Aceeași regulă ca la rezistoare: două cifre apoi numărul de zerouri, în µH."),
    "smd.n.ind3_nh": ("Check the datasheet — a few RF chip-inductor series use nH.",
                      "Verifică foaia de catalog — câteva serii de bobine RF folosesc nH."),
})

CANVAS_BG = "#fdfaf3"
UNITS = {"resistor": "Ω", "capacitor": "F", "inductor": "H"}
EXAMPLES = {
    "resistor": ["103", "472", "4R7", "R047", "1002", "01C", "68X", "000", "5m0"],
    "capacitor": ["104", "472J", "2A104K", "A106", "107C", "S3", "4n7", "479"],
    "inductor": ["101", "4R7", "R10", "47N", "220", "2R2"],
}
DEFAULT = {"resistor": "103", "capacitor": "104", "inductor": "4R7"}
DEFAULT_VALUE = {"resistor": "4.7k", "capacitor": "100n", "inductor": "10u"}

# capacitor colour-band tolerance (C > 10 pF) and voltage bands
CAP_BAND_TOL = {"Black": 20, "Brown": 1, "Red": 2, "Green": 5, "White": 10}
CAP_BAND_VOLT = {"None": None, "Red": 250, "Yellow": 400, "Black": 100, "Brown": 100, "Blue": 630}


class SmdCodePanel(ttk.Frame):
    def __init__(self, parent, kind, accent):
        super().__init__(parent, style="Card.TFrame")
        self.kind = kind
        self.accent = accent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body
        body.columnconfigure(0, weight=1)
        self._build_decode(body)
        self._build_encode(body)
        if kind == "capacitor":
            self._build_cap_bands(body)
        self._build_tables(body)

    # ------------------------------------------------------------------
    def _h2(self, parent, key):
        ttk.Label(parent, text=t(key), font=FONT_H2, foreground=self.accent,
                  style="CardSub.TLabel").pack(anchor="w", padx=16, pady=(12, 4))

    def _build_decode(self, body):
        self._h2(body, "smd.decode_title")
        note = {"resistor": "smd.melf_note", "capacitor": "smd.mlcc_note", "inductor": "smd.ind_note"}[self.kind]
        ttk.Label(body, text=t(note), font=("Segoe UI", 9), style="CardBody.TLabel", wraplength=440,
                  justify="left").pack(anchor="w", padx=16, pady=(0, 6))

        row = ttk.Frame(body, style="Card.TFrame")
        row.pack(fill="x", padx=16, pady=4)
        ttk.Label(row, text=t("smd.code"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self.code = tk.StringVar(value=DEFAULT[self.kind])
        e = ttk.Entry(row, textvariable=self.code, width=12, font=("Consolas", 14, "bold"))
        e.pack(side="left", padx=8)
        e.bind("<KeyRelease>", lambda _e: self._decode())
        ttk.Label(row, text=t("smd.package"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left", padx=(12, 4))
        self.pkg = tk.StringVar(value="0805" if self.kind != "capacitor" else "1206")
        cb = ttk.Combobox(row, textvariable=self.pkg, values=[p[0] for p in sc.PACKAGES],
                          state="readonly", width=7)
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda _e: self._decode())

        ex = ttk.Frame(body, style="Card.TFrame")
        ex.pack(fill="x", padx=16, pady=(2, 4))
        ttk.Label(ex, text=t("smd.examples"), font=("Segoe UI", 9), style="CardBody.TLabel").pack(side="left")
        for c in EXAMPLES[self.kind]:
            b = tk.Label(ex, text=c, font=("Consolas", 9, "bold"), bg="#eef1f6", fg="#1f2a44",
                         padx=6, pady=1, cursor="hand2", relief="flat", bd=0)
            b.pack(side="left", padx=2)
            b.bind("<Button-1>", lambda _e, c=c: (self.code.set(c), self._decode()))

        self.canvas = tk.Canvas(body, width=460, height=170, bg=CANVAS_BG, highlightthickness=0)
        self.canvas.pack(padx=16, pady=6, anchor="w")
        self.main_result = tk.StringVar()
        ttk.Label(body, textvariable=self.main_result, font=("Consolas", 15, "bold"), foreground=self.accent,
                  style="CardFormula.TLabel").pack(anchor="w", padx=16)
        self.detail = tk.Text(body, height=8, width=60, wrap="word", font=("Segoe UI", 9), bd=0,
                              bg="#ffffff", highlightthickness=0)
        self.detail.pack(fill="x", padx=16, pady=(4, 8))
        self.detail.tag_configure("h", font=("Segoe UI", 9, "bold"), foreground=self.accent)
        self.detail.tag_configure("m", font=("Consolas", 9))
        self.detail.tag_configure("n", foreground="#666666", font=("Segoe UI", 9, "italic"))
        self.pkg_info = tk.StringVar()
        ttk.Label(body, textvariable=self.pkg_info, font=("Segoe UI", 9), style="CardBody.TLabel")\
            .pack(anchor="w", padx=16, pady=(0, 6))
        ttk.Separator(body).pack(fill="x", padx=16, pady=6)
        self._decode()

    def _decode(self):
        interps = sc.decode(self.kind, self.code.get())
        txt = self.detail
        txt.configure(state="normal")
        txt.delete("1.0", "end")
        unit = UNITS[self.kind]
        if not interps:
            self.main_result.set("= ?")
            txt.insert("end", t("smd.unknown"), "n")
        else:
            best = interps[0]
            extra = []
            if best.tol:
                extra.append(best.tol)
            if best.voltage:
                extra.append(f"{best.voltage:g} V")
            self.main_result.set(f"= {sc.fmt(best.value, unit)}" + (f"   {'  '.join(extra)}" if extra else ""))
            if len(interps) > 1:
                txt.insert("end", t("smd.ambiguous") + "\n", "n")
            for i, it in enumerate(interps):
                head = f"{t('smd.reading')} {i + 1}: " if len(interps) > 1 else ""
                txt.insert("end", f"{head}{t(it.scheme)}  →  {sc.fmt(it.value, unit)}\n", "h")
                for s in it.steps:
                    txt.insert("end", f"   {s}\n", "m")
                if it.tol:
                    txt.insert("end", f"   {t('smd.tol')}: {it.tol}\n", "m")
                if it.voltage:
                    txt.insert("end", f"   {t('smd.volt')}: {it.voltage:g} V\n", "m")
                if it.note:
                    txt.insert("end", f"   {t(it.note)}\n", "n")
        lines = int(txt.index("end-1c").split(".")[0])
        txt.configure(height=max(3, min(16, lines)), state="disabled")
        self._draw_chip(interps)

    def _draw_chip(self, interps):
        c = self.canvas
        c.delete("all")
        W, H = 460, 170
        code = self.code.get().strip() or "?"
        tant = bool(interps) and interps[0].scheme == "smd.s.tant"
        pk = next(p for p in sc.PACKAGES if p[0] == self.pkg.get())
        imp, met, L, Wd, pw = pk
        if tant:
            case = next((tc for tc in sc.TANT_CASES if tc[2] >= L), sc.TANT_CASES[-1])
            L, Wd = case[2], case[3]
        # scale so the largest package still fits; small parts get a zoom badge
        scale = min(300 / L, 100 / Wd)
        scale = min(scale, 90)
        bw, bh = L * scale, Wd * scale
        cx, cy = W / 2, H / 2 + 2
        x0, y0, x1, y1 = cx - bw / 2, cy - bh / 2, cx + bw / 2, cy + bh / 2
        # PCB pads
        pad = bw * 0.28
        c.create_rectangle(x0 - pad * 0.35, y0 - 6, x0 + pad * 0.6, y1 + 6, fill="#d9a441", outline="#b07d1f")
        c.create_rectangle(x1 - pad * 0.6, y0 - 6, x1 + pad * 0.35, y1 + 6, fill="#d9a441", outline="#b07d1f")
        if self.kind == "resistor":
            cap_w = bw * 0.14
            c.create_rectangle(x0, y0, x1, y1, fill="#1b1b1b", outline="#000")
            c.create_rectangle(x0, y0, x0 + cap_w, y1, fill="#c9ccd1", outline="#8a8f96")
            c.create_rectangle(x1 - cap_w, y0, x1, y1, fill="#c9ccd1", outline="#8a8f96")
            fg = "#f2f2f2"
        elif self.kind == "capacitor" and tant:
            c.create_rectangle(x0, y0, x1, y1, fill="#e8a317", outline="#8a5a00", width=2)
            c.create_rectangle(x0 + bw * 0.08, y0 + 3, x0 + bw * 0.2, y1 - 3, fill="#6b3d00", outline="")
            c.create_text(x0 + bw * 0.14, y0 - 12, text="+", font=("Segoe UI", 14, "bold"), fill="#6b3d00")
            fg = "#3b2200"
        elif self.kind == "capacitor":
            cap_w = bw * 0.16
            c.create_rectangle(x0, y0, x1, y1, fill="#b88a57", outline="#6e4f2c")
            c.create_rectangle(x0, y0, x0 + cap_w, y1, fill="#c9ccd1", outline="#8a8f96")
            c.create_rectangle(x1 - cap_w, y0, x1, y1, fill="#c9ccd1", outline="#8a8f96")
            fg = "#3b2a12"
        else:
            cap_w = bw * 0.14
            c.create_rectangle(x0, y0, x1, y1, fill="#3a3f47", outline="#15181c")
            c.create_rectangle(x0, y0, x0 + cap_w, y1, fill="#c9ccd1", outline="#8a8f96")
            c.create_rectangle(x1 - cap_w, y0, x1, y1, fill="#c9ccd1", outline="#8a8f96")
            fg = "#f2f2f2"
        fs = int(max(9, min(34, bh * 0.5, bw * 0.55 / max(1, len(code)) * 1.6)))
        c.create_text(cx, cy, text=code, font=("Consolas", fs, "bold"), fill=fg)
        # dimension lines
        c.create_line(x0, y1 + 16, x1, y1 + 16, arrow="both", fill="#555")
        c.create_text(cx, y1 + 26, text=f"{L:g} mm", font=("Segoe UI", 8), fill="#555")
        c.create_line(x1 + 22, y0, x1 + 22, y1, arrow="both", fill="#555")
        c.create_text(x1 + 26, cy, text=f"{Wd:g} mm", font=("Segoe UI", 8), fill="#555", anchor="w")
        label = f"{case[0]} ({case[1]})" if tant else f"{imp} / {met}M"
        c.create_text(8, 8, text=label, anchor="nw", font=("Segoe UI", 9, "bold"), fill="#1f2a44")
        c.create_text(W - 8, 8, text=f"×{scale / 3.78:.0f}", anchor="ne", font=("Segoe UI", 8), fill="#888")
        pinfo = t("smd.pkg_info").format(imp=imp, met=met, l=pk[2], w=pk[3])
        if self.kind == "resistor":
            p = pw
            ptxt = f"1/{round(1 / p)} W" if p < 1 else f"{p:g} W"
            pinfo += "  ·  " + t("smd.pkg_power").format(p=ptxt)
        self.pkg_info.set(pinfo)

    # ------------------------------------------------------------------
    def _build_encode(self, body):
        self._h2(body, "smd.encode_title")
        row = ttk.Frame(body, style="Card.TFrame")
        row.pack(fill="x", padx=16, pady=4)
        ttk.Label(row, text=t("smd.value"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self.enc_val = tk.StringVar(value=DEFAULT_VALUE[self.kind])
        e = ttk.Entry(row, textvariable=self.enc_val, width=12)
        e.pack(side="left", padx=8)
        ttk.Label(row, text=UNITS[self.kind], font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        e.bind("<KeyRelease>", lambda _e: self._encode())
        cols = ("scheme", "code", "exact")
        self.enc_tree = ttk.Treeview(body, columns=cols, show="headings", height=5)
        for col, key, w in zip(cols, ("smd.col.scheme", "smd.col.code", "smd.col.exact"), (260, 90, 80)):
            self.enc_tree.heading(col, text=t(key))
            self.enc_tree.column(col, width=w, anchor="w" if col == "scheme" else "center")
        self.enc_tree.pack(fill="x", padx=16, pady=4)
        self.enc_tree.bind("<Double-1>", self._use_code)
        self.nearest = tk.StringVar()
        ttk.Label(body, textvariable=self.nearest, font=("Segoe UI", 9), style="CardBody.TLabel",
                  wraplength=440, justify="left").pack(anchor="w", padx=16, pady=(0, 6))
        ttk.Separator(body).pack(fill="x", padx=16, pady=6)
        self._encode()

    def _use_code(self, _e=None):
        sel = self.enc_tree.selection()
        if sel:
            code = self.enc_tree.item(sel[0], "values")[1].split()[0]
            if code != "—":
                self.code.set(code)
                self._decode()

    def _encode(self):
        tree = self.enc_tree
        tree.delete(*tree.get_children())
        try:
            v = parse_value(self.enc_val.get())
        except Exception:
            self.nearest.set("")
            return
        rows = sc.encode(self.kind, v)
        for scheme, code, exact, note in rows:
            ex = t("smd.yes") if exact else (t(note) if note else t("smd.no"))
            tree.insert("", "end", values=(t(scheme), code, ex))
        tree.configure(height=max(2, len(rows)))
        unit = UNITS[self.kind]
        if v > 0:
            parts = []
            for name, series in (("E6", sc.E6), ("E12", sc.E12), ("E24", sc.E24), ("E96", sc.E96)):
                if self.kind != "resistor" and name == "E96":
                    continue
                parts.append(f"{name}: {sc.fmt(sc.nearest_series(v, series), unit)}")
            self.nearest.set(t("smd.nearest") + "  " + "   ".join(parts))
        else:
            self.nearest.set("")

    # ------------------------------------------------------------------
    def _build_cap_bands(self, body):
        self._h2(body, "smd.cband_title")
        row = ttk.Frame(body, style="Card.TFrame")
        row.pack(fill="x", padx=16, pady=4)
        labels = [t("resistor.band.digit1"), t("resistor.band.digit2"), t("resistor.band.multiplier"),
                  t("resistor.band.tolerance"), t("smd.cband.volt")]
        mults = [c for c in COLOR_CODE if COLOR_CODE[c]["multiplier"] is not None and
                 COLOR_CODE[c]["multiplier"] <= 1e6]
        opts = [DIGIT_COLORS, DIGIT_COLORS, mults, list(CAP_BAND_TOL), list(CAP_BAND_VOLT)]
        defaults = ["Yellow", "Violet", "Yellow", "White", "Red"]
        self.cb_vars = []
        for i, (lab, op, d) in enumerate(zip(labels, opts, defaults)):
            f = ttk.Frame(row, style="Card.TFrame")
            f.grid(row=0, column=i, padx=3)
            ttk.Label(f, text=lab, font=("Segoe UI", 8), style="CardBody.TLabel").pack()
            v = tk.StringVar(value=d)
            cb = ttk.Combobox(f, textvariable=v, values=op, state="readonly", width=7)
            cb.pack()
            cb.bind("<<ComboboxSelected>>", lambda _e: self._cap_bands())
            self.cb_vars.append(v)
        self.cb_canvas = tk.Canvas(body, width=460, height=130, bg=CANVAS_BG, highlightthickness=0)
        self.cb_canvas.pack(padx=16, pady=4, anchor="w")
        self.cb_result = tk.StringVar()
        ttk.Label(body, textvariable=self.cb_result, font=FONT_MONO, foreground=self.accent,
                  style="CardFormula.TLabel").pack(anchor="w", padx=16, pady=(0, 6))
        ttk.Separator(body).pack(fill="x", padx=16, pady=6)
        self._cap_bands()

    def _cap_bands(self):
        cols = [v.get() for v in self.cb_vars]
        bands = cols[:4] + ([cols[4]] if CAP_BAND_VOLT.get(cols[4]) else [])
        draw_resistor(self.cb_canvas, bands, h=130, body="#4f7cc4", edge="#2a4c80")
        try:
            pf = (COLOR_CODE[cols[0]]["digit"] * 10 + COLOR_CODE[cols[1]]["digit"]) * COLOR_CODE[cols[2]]["multiplier"]
            tol = CAP_BAND_TOL[cols[3]]
            volt = CAP_BAND_VOLT.get(cols[4])
            txt = f"= {pf:g} pF = {sc.fmt(pf * 1e-12, 'F')}  ±{tol}%"
            if volt:
                txt += f"  {volt} V"
            self.cb_result.set(txt)
        except Exception:
            self.cb_result.set("-")

    # ------------------------------------------------------------------
    def _build_tables(self, body):
        self._h2(body, "smd.tables")
        tables = {
            "resistor": ["smd.tb.e96", "smd.tb.e96m", "smd.tb.pkg"],
            "capacitor": ["smd.tb.e198", "smd.tb.volt", "smd.tb.tvolt", "smd.tb.tol", "smd.tb.pkg", "smd.tb.tcase"],
            "inductor": ["smd.tb.pkg"],
        }[self.kind]
        self._table_keys = tables
        row = ttk.Frame(body, style="Card.TFrame")
        row.pack(fill="x", padx=16, pady=4)
        ttk.Label(row, text=t("smd.table"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self.tbl = tk.StringVar(value=t(tables[0]))
        cb = ttk.Combobox(row, textvariable=self.tbl, values=[t(k) for k in tables], state="readonly", width=34)
        cb.pack(side="left", padx=8)
        cb.bind("<<ComboboxSelected>>", lambda _e: self._fill_table())
        wrap = ttk.Frame(body, style="Card.TFrame")
        wrap.pack(fill="x", padx=16, pady=(4, 16))
        self.ref_tree = ttk.Treeview(wrap, show="headings", height=10)
        vsb = ttk.Scrollbar(wrap, orient="vertical", command=self.ref_tree.yview)
        self.ref_tree.configure(yscrollcommand=vsb.set)
        self.ref_tree.pack(side="left", fill="x", expand=True)
        vsb.pack(side="right", fill="y")
        self._fill_table()

    def _fill_table(self):
        key = next(k for k in self._table_keys if t(k) == self.tbl.get())
        tree = self.ref_tree
        tree.delete(*tree.get_children())
        if key == "smd.tb.e96":
            cols = ("c1", "v1", "c2", "v2", "c3", "v3", "c4", "v4")
            heads = (tr("Code", "Cod"), tr("Value", "Valoare")) * 4
            rows = []
            for i in range(24):
                r = []
                for j in range(4):
                    k = i + 24 * j
                    r += [f"{k + 1:02d}", sc.E96[k]]
                rows.append(r)
        elif key == "smd.tb.e96m":
            cols, heads = ("l", "m"), (tr("Letter", "Literă"), tr("Multiplier", "Multiplicator"))
            rows = [(L, f"× {m:g}") for L, m in sc.EIA96_MULT.items()]
        elif key == "smd.tb.e198":
            cols = ("l1", "v1", "l2", "v2", "l3", "v3")
            heads = (tr("Letter", "Literă"), tr("Value", "Valoare")) * 3
            items = list(sc.EIA198_LETTER.items())
            rows = []
            n = (len(items) + 2) // 3
            for i in range(n):
                r = []
                for j in range(3):
                    k = i + n * j
                    r += list(items[k]) if k < len(items) else ["", ""]
                rows.append(r)
            rows.append(["digit 0–7", "× 10ⁿ pF", "digit 9", "× 0.1 pF", "", ""])
        elif key == "smd.tb.volt":
            cols, heads = ("c", "v"), (tr("Code", "Cod"), tr("Volts", "Volți"))
            rows = [(k, f"{v:g} V") for k, v in sc.CAP_VOLT_EIA.items()]
        elif key == "smd.tb.tvolt":
            cols, heads = ("c", "v"), (tr("Letter", "Literă"), tr("Volts", "Volți"))
            rows = [(k, f"{v:g} V") for k, v in sc.TANT_VOLT.items()]
        elif key == "smd.tb.tol":
            cols, heads = ("c", "v"), (tr("Letter", "Literă"), tr("Tolerance", "Toleranță"))
            rows = list(sc.CAP_TOL.items())
        elif key == "smd.tb.tcase":
            cols, heads = ("c", "e", "d"), (tr("Case", "Capsulă"), "EIA", "L × W × H (mm)")
            rows = [(c, e, f"{l} × {w} × {h}") for c, e, l, w, h in sc.TANT_CASES]
        else:
            cols = ("i", "m", "d", "p")
            heads = (tr("Imperial", "Imperial"), tr("Metric", "Metric"), "L × W (mm)", tr("Resistor P", "P rezistor"))
            rows = [(i, m, f"{l} × {w}", (f"1/{round(1 / p)} W" if p < 1 else f"{p:g} W"))
                    for i, m, l, w, p in sc.PACKAGES]
        tree.configure(columns=cols)
        for c, h in zip(cols, heads):
            tree.heading(c, text=h)
            tree.column(c, width=max(50, 440 // len(cols)), anchor="center")
        for r in rows:
            tree.insert("", "end", values=r)
        tree.configure(height=min(12, len(rows)))
