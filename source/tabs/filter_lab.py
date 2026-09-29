"""
tabs/filter_lab.py - Filter Lab (v6): pick any classic filter, change the
parts with sliders (or ask for a target cut-off / Q and let it design the
parts), and look at it every way:

    Bode (gain + phase)  ·  time response to sine / square / triangle / sweep
    step response  ·  poles & zeros  ·  harmonic spectrum in → out

The previous 'build your own L-section' tool is kept as a second sub-tab.
"""
import math
import numpy as np
import tkinter as tk
from tkinter import ttk
from matplotlib.gridspec import GridSpec

import symbols as sym
import filter_math as fm
from charts import MplChartFrame, PLOT_BG
from widgets import ScrollableFrame, FONT_H1, FONT_BODY, lazy_tab, parse_value
from uikit import Segmented, ParamForm, TileRow, section, note, eng, nice
from i18n import t, register, tr

ACCENT_C = "#8854d0"
C_IN = "#c9622a"
C_OUT = "#8854d0"
C_PH = "#2A9D8F"

register({
    "fl.title": ("∿ Filter Lab", "∿ Laborator de filtre"),
    "fl.lab": ("Filter Lab", "Laborator filtre"),
    "fl.custom": ("Build your own (L-sections)", "Construiește-ți propriul (secțiuni L)"),
    "fl.g.passive": ("RC / RL", "RC / RL"),
    "fl.g.resonant": ("RLC (resonant)", "RLC (rezonante)"),
    "fl.g.active": ("Active (op-amp)", "Active (AO)"),
    "fl.f.rc_lp": ("RC low-pass", "Trece-jos RC"),
    "fl.f.rc_hp": ("RC high-pass", "Trece-sus RC"),
    "fl.f.rl_lp": ("RL low-pass", "Trece-jos RL"),
    "fl.f.rl_hp": ("RL high-pass", "Trece-sus RL"),
    "fl.f.rcrc_lp": ("2× RC low-pass", "2× RC trece-jos"),
    "fl.f.twin_t": ("Twin-T notch", "Notch dublu T"),
    "fl.f.rlc_bp": ("RLC band-pass", "Trece-bandă RLC"),
    "fl.f.rlc_bs": ("RLC band-stop", "Oprește-bandă RLC"),
    "fl.f.lc_lp": ("LC low-pass (2nd)", "Trece-jos LC (ord. 2)"),
    "fl.f.lc_hp": ("LC high-pass (2nd)", "Trece-sus LC (ord. 2)"),
    "fl.f.act_lp1": ("Active low-pass (1st)", "Trece-jos activ (ord. 1)"),
    "fl.f.sk_lp": ("Sallen-Key low-pass", "Sallen-Key trece-jos"),
    "fl.f.sk_hp": ("Sallen-Key high-pass", "Sallen-Key trece-sus"),
    "fl.f.mfb_bp": ("MFB band-pass", "Trece-bandă MFB"),
    "fl.parts": ("Components (drag the sliders)", "Componente (trage de glisoare)"),
    "fl.design": ("Design for", "Proiectează pentru"),
    "fl.design_btn": ("Calculate parts", "Calculează piesele"),
    "fl.keeps": ("keeps {p} as chosen", "păstrează {p} cum l-ai ales"),
    "fl.view": ("View", "Vizualizare"),
    "fl.v.bode": ("Bode plot", "Diagrama Bode"),
    "fl.v.time": ("Signal in → out", "Semnal intrare → ieșire"),
    "fl.v.step": ("Step response", "Răspuns la treaptă"),
    "fl.v.pz": ("Poles & zeros", "Poli și zerouri"),
    "fl.v.spec": ("Harmonics", "Armonici"),
    "fl.input": ("Test signal", "Semnal de test"),
    "fl.w.sine": ("Sine", "Sinus"), "fl.w.square": ("Square", "Dreptunghi"),
    "fl.w.tri": ("Triangle", "Triunghi"), "fl.w.sweep": ("Sweep (chirp)", "Baleiaj (chirp)"),
    "fl.fin": ("Frequency", "Frecvență"),
    "fl.amp": ("Amplitude", "Amplitudine"),
    "fl.at_f0": ("set to f0", "setează la f0"),
    "fl.t.f0": ("Cut-off / centre f0", "Frecvență de tăiere / centrală f0"),
    "fl.t.q": ("Quality factor Q", "Factor de calitate Q"),
    "fl.t.gain": ("Pass-band gain", "Câștig în bandă"),
    "fl.t.bw": ("−3 dB points", "Punctele −3 dB"),
    "fl.t.slope": ("Roll-off", "Pantă"),
    "fl.t.atf": ("Gain at test freq.", "Câștig la frecv. de test"),
    "fl.t.phase": ("Phase at test freq.", "Faza la frecv. de test"),
    "fl.t.type": ("Response", "Răspuns"),
    "fl.k.lp": ("low-pass", "trece-jos"), "fl.k.hp": ("high-pass", "trece-sus"),
    "fl.k.bp": ("band-pass", "trece-bandă"), "fl.k.bs": ("band-stop / notch", "oprește-bandă / notch"),
    "fl.ax.f": ("Frequency (Hz)", "Frecvență (Hz)"),
    "fl.ax.mag": ("Gain (dB)", "Câștig (dB)"),
    "fl.ax.ph": ("Phase (°)", "Fază (°)"),
    "fl.ax.t": ("Time (ms)", "Timp (ms)"),
    "fl.ax.v": ("Voltage (V)", "Tensiune (V)"),
    "fl.ax.re": ("Real part σ (×ω0)", "Parte reală σ (×ω0)"),
    "fl.ax.im": ("Imag. part jω (×ω0)", "Parte imag. jω (×ω0)"),
    "fl.ax.h": ("Harmonic (× f)", "Armonica (× f)"),
    "fl.ax.a": ("Amplitude (V)", "Amplitudine (V)"),
    "fl.leg.in": ("input", "intrare"), "fl.leg.out": ("output", "ieșire"),
    "fl.pz.note": ("× poles (must be in the left half for a stable filter), ○ zeros. Poles further from the "
                   "axis → more damping; close to the jω axis → high Q, a sharp peak and ringing.",
                   "× poli (trebuie să fie în semiplanul stâng pentru un filtru stabil), ○ zerouri. Poli departe "
                   "de axă → amortizare mare; aproape de axa jω → Q mare, vârf ascuțit și oscilații."),
    "fl.spec.note": ("Bars: amplitude of each harmonic of the test signal, before (light) and after (dark) the "
                     "filter. The line is the filter's gain at that frequency.",
                     "Bare: amplitudinea fiecărei armonici a semnalului de test, înainte (deschis) și după "
                     "(închis) filtru. Linia este câștigul filtrului la acea frecvență."),
    "fl.x.rc_lp": ("C has a low impedance at high frequency, so it shorts the high frequencies to ground: "
                   "fc = 1/(2πRC), −20 dB/decade above it, output lags up to −90°.",
                   "C are impedanță mică la frecvență mare, deci scurtcircuitează frecvențele înalte la masă: "
                   "fc = 1/(2πRC), −20 dB/decadă peste ea, ieșirea rămâne în urmă până la −90°."),
    "fl.x.rc_hp": ("C blocks DC and low frequencies; above fc = 1/(2πRC) the signal passes. Used as a "
                   "coupling / DC-blocking stage. Output leads by up to +90°.",
                   "C blochează DC și frecvențele joase; peste fc = 1/(2πRC) semnalul trece. Folosit pentru "
                   "cuplaj / blocarea componentei continue. Ieșirea e defazată înainte până la +90°."),
    "fl.x.rl_lp": ("The inductor's impedance ωL grows with frequency, so high frequencies are blocked: "
                   "fc = R/(2πL). Common in power supplies (with a C it becomes an LC filter).",
                   "Impedanța bobinei ωL crește cu frecvența, deci frecvențele înalte sunt blocate: fc = R/(2πL). "
                   "Frecvent în surse de alimentare (cu un C devine filtru LC)."),
    "fl.x.rl_hp": ("The inductor shorts low frequencies to ground; above fc = R/(2πL) its impedance is high "
                   "and the signal passes.",
                   "Bobina scurtcircuitează frecvențele joase la masă; peste fc = R/(2πL) impedanța ei e mare și "
                   "semnalul trece."),
    "fl.x.rcrc_lp": ("Two RC stages in cascade: −40 dB/decade far away, but the second stage loads the first, "
                     "so the knee is soft (Q < 0.5) — this is why active filters exist. Making R2 ≫ R1 reduces "
                     "the loading.",
                     "Două etaje RC în cascadă: −40 dB/decadă departe, dar al doilea etaj îl încarcă pe primul, deci "
                     "cotul e moale (Q < 0,5) — de aceea există filtrele active. R2 ≫ R1 reduce încărcarea."),
    "fl.x.twin_t": ("Two T-networks in parallel (R-R with 2C, and C-C with R/2) cancel each other exactly at "
                    "f0 = 1/(2πRC): a deep notch, e.g. to remove 50 Hz hum. The notch is wide (Q = 0.25) unless "
                    "it is put inside an op-amp feedback loop.",
                    "Două rețele T în paralel (R-R cu 2C și C-C cu R/2) se anulează exact la f0 = 1/(2πRC): o "
                    "rejecție adâncă, de ex. pentru brumul de 50 Hz. Rejecția e largă (Q = 0,25) dacă nu e pusă "
                    "în bucla de reacție a unui AO."),
    "fl.x.rlc_bp": ("At resonance f0 = 1/(2π√LC) the reactances of L and C cancel and all of Vin appears "
                    "across R. Away from f0 one of them blocks. Q = (1/R)·√(L/C): bandwidth = f0/Q.",
                    "La rezonanță f0 = 1/(2π√LC) reactanțele lui L și C se anulează și toată Vin apare pe R. "
                    "Departe de f0 una dintre ele blochează. Q = (1/R)·√(L/C): banda = f0/Q."),
    "fl.x.rlc_bs": ("The series LC branch is a short circuit at resonance, pulling the output to zero at f0 "
                    "while passing everything else. Higher Q → narrower notch.",
                    "Ramura LC serie este un scurtcircuit la rezonanță și trage ieșirea la zero la f0, lăsând restul "
                    "să treacă. Q mai mare → rejecție mai îngustă."),
    "fl.x.lc_lp": ("Series L, shunt C, driving a load R: a 2nd-order low-pass (−40 dB/decade). The load sets "
                   "the damping: Q = R·√(C/L). Q = 0.707 is maximally flat (Butterworth); larger Q peaks.",
                   "L serie, C paralel, pe o sarcină R: trece-jos de ordinul 2 (−40 dB/decadă). Sarcina stabilește "
                   "amortizarea: Q = R·√(C/L). Q = 0,707 este maxim plat (Butterworth); Q mai mare face vârf."),
    "fl.x.lc_hp": ("Series C, shunt L into a load R: 2nd-order high-pass, +40 dB/decade below f0. Same "
                   "damping rule Q = R·√(C/L).",
                   "C serie, L paralel pe o sarcină R: trece-sus de ordinul 2, +40 dB/decadă sub f0. Aceeași "
                   "regulă de amortizare Q = R·√(C/L)."),
    "fl.x.act_lp1": ("An inverting amplifier whose feedback resistor has a capacitor across it: gain −Rf/Rin "
                     "at low frequency, falling above fc = 1/(2πRfC). Gain and cut-off can be set independently "
                     "and the output can drive a load.",
                     "Un amplificator inversor cu un condensator în paralel pe rezistorul de reacție: câștig "
                     "−Rf/Rin la frecvență joasă, care scade peste fc = 1/(2πRfC). Câștigul și frecvența de tăiere "
                     "se aleg independent, iar ieșirea poate comanda o sarcină."),
    "fl.x.sk_lp": ("Sallen-Key: two RC sections around a unity-gain buffer. C1 feeds the output back to the "
                   "middle node, which lets the pair behave like an LC filter without an inductor. "
                   "Q = √(C1/C2)/2 for equal resistors — set Q = 0.707 for Butterworth.",
                   "Sallen-Key: două secțiuni RC în jurul unui repetor. C1 aduce ieșirea înapoi în nodul din mijloc, "
                   "ceea ce face perechea să se comporte ca un filtru LC fără bobină. Q = √(C1/C2)/2 pentru "
                   "rezistoare egale — alege Q = 0,707 pentru Butterworth."),
    "fl.x.sk_hp": ("The high-pass Sallen-Key swaps R and C. With equal capacitors Q = ½·√(Rb/Ra).",
                   "Sallen-Key trece-sus schimbă R cu C. Cu condensatoare egale Q = ½·√(Rb/Ra)."),
    "fl.x.mfb_bp": ("Multiple-feedback band-pass (inverting): R3 and C2 both feed the output back. Can give high "
                    "Q and gain with one op-amp: f0 = √((R1+R2)/(R1·R2·R3))/(2πC), Q = πf0·R3·C, "
                    "gain = −R3/(2R1).",
                    "Trece-bandă cu reacție multiplă (inversor): R3 și C2 aduc ambele ieșirea înapoi. Oferă Q și "
                    "câștig mari cu un singur AO: f0 = √((R1+R2)/(R1·R2·R3))/(2πC), Q = πf0·R3·C, "
                    "câștig = −R3/(2R1)."),
})

UNIT_OF = {"Ω": "Ω", "F": "F", "H": "H"}
SLIDER = {"Ω": (1, 1e6, True), "F": (100e-12, 100e-6, True), "H": (10e-6, 10.0, True)}


class FilterLabPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        accent = ACCENT_C
        self.accent = accent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body

        pick = ttk.Frame(body, style="Card.TFrame")
        pick.pack(fill="x", padx=16, pady=(12, 0))
        self.group = tk.StringVar(value="passive")
        Segmented(pick, [(g, t("fl.g." + g)) for g, _ in fm.GROUPS], self.group, self._on_group,
                  accent=accent, font_size=10).pack(anchor="w")
        self.frow = ttk.Frame(pick, style="Card.TFrame")
        self.frow.pack(anchor="w", pady=(6, 0))
        self.fkey = tk.StringVar(value="rc_lp")

        top = ttk.Frame(body, style="Card.TFrame")
        top.pack(fill="both", expand=True, padx=16, pady=(8, 12))
        top.columnconfigure(1, weight=1)
        left = ttk.Frame(top, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nw")
        right = ttk.Frame(top, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(16, 0))

        self.canvas = tk.Canvas(left, width=470, height=280, bg=sym.CANVAS_BG, highlightthickness=0)
        self.canvas.pack(anchor="w")
        ttk.Label(left, text=t("fl.parts"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel")\
            .pack(anchor="w", pady=(6, 0))
        self.form_holder = ttk.Frame(left, style="Card.TFrame")
        self.form_holder.pack(anchor="w", fill="x")
        # design row
        drow = ttk.Frame(left, style="Card.TFrame")
        drow.pack(anchor="w", pady=(6, 0), fill="x")
        ttk.Label(drow, text=t("fl.design"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        ttk.Label(drow, text=" f0", font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self.d_f0 = tk.StringVar(value="1k")
        ttk.Entry(drow, textvariable=self.d_f0, width=7).pack(side="left", padx=(2, 6))
        self.d_q_lab = ttk.Label(drow, text="Q", font=FONT_BODY, style="CardBody.TLabel")
        self.d_q = tk.StringVar(value="0.707")
        self.d_q_ent = ttk.Entry(drow, textvariable=self.d_q, width=6)
        self.d_g_lab = ttk.Label(drow, text="gain", font=FONT_BODY, style="CardBody.TLabel")
        self.d_g = tk.StringVar(value="1")
        self.d_g_ent = ttk.Entry(drow, textvariable=self.d_g, width=5)
        self.d_btn = ttk.Button(drow, text=t("fl.design_btn"), style="Small.TButton", command=self._design)
        self.d_row = drow
        self.keeps = note(left, "", wrap=440, padx=0, pady=(2, 4), italic=True)
        self.tiles = TileRow(left, [("f0", t("fl.t.f0")), ("q", t("fl.t.q")), ("gain", t("fl.t.gain")),
                                    ("bw", t("fl.t.bw")), ("slope", t("fl.t.slope")), ("type", t("fl.t.type")),
                                    ("atf", t("fl.t.atf")), ("ph", t("fl.t.phase"))], accent, per_row=2)
        self.tiles.pack(fill="x", pady=(6, 0))
        self.explain = note(left, "", wrap=440, padx=0, pady=(8, 4))

        # right: view selector + input + chart
        vrow = ttk.Frame(right, style="Card.TFrame")
        vrow.pack(anchor="w", fill="x")
        self.view = tk.StringVar(value="bode")
        Segmented(vrow, [(k, t("fl.v." + k)) for k in ("bode", "time", "step", "pz", "spec")], self.view,
                  lambda k: self.update_all(), accent=accent, font_size=10).pack(side="left")
        irow = ttk.Frame(right, style="Card.TFrame")
        irow.pack(anchor="w", fill="x", pady=(6, 0))
        ttk.Label(irow, text=t("fl.input"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel")\
            .pack(side="left", padx=(0, 6))
        self.wave = tk.StringVar(value="square")
        Segmented(irow, [(k, t("fl.w." + k)) for k in ("sine", "square", "tri", "sweep")], self.wave,
                  lambda k: self.update_all(), accent=accent).pack(side="left")
        self.in_form = ParamForm(right, [
            dict(key="f", label=t("fl.fin"), default="1k", unit="Hz", slider=(1, 1e6, True)),
            dict(key="amp", label=t("fl.amp"), default="1", unit="V", slider=(0.1, 10)),
        ], self.update_all, label_width=12)
        self.in_form.pack(anchor="w", pady=(4, 0))
        b = ttk.Button(right, text=t("fl.at_f0"), style="Small.TButton", command=self._set_f0)
        b.pack(anchor="w", pady=(2, 0))
        self.chart = MplChartFrame(right, figsize=(7.0, 4.6), with_toolbar=True)
        self.chart.pack(fill="both", expand=True, pady=(6, 0))
        self.view_note = note(right, "", wrap=680, padx=0, pady=(4, 0), italic=True)
        self._on_group("passive")

    # ------------------------------------------------------------------
    def _on_group(self, g):
        for w in self.frow.winfo_children():
            w.destroy()
        items = dict(fm.GROUPS)[g]
        if self.fkey.get() not in items:
            self.fkey.set(items[0])
        Segmented(self.frow, [(k, t("fl.f." + k)) for k in items], self.fkey, self._on_filter,
                  accent=self.accent).pack(anchor="w")
        self._on_filter(self.fkey.get())

    def _on_filter(self, key):
        F = fm.FILTERS[key]
        self.F = F
        for w in self.form_holder.winfo_children():
            w.destroy()
        fields = []
        for k, symb, d, unit in F["params"]:
            fields.append(dict(key=k, label=symb, default=nice(d), unit=unit, slider=SLIDER[unit]))
        self.form = ParamForm(self.form_holder, fields, self.update_all, label_width=14)
        self.form.pack(anchor="w")
        # design row widgets
        for w in (self.d_q_lab, self.d_q_ent, self.d_g_lab, self.d_g_ent, self.d_btn):
            w.pack_forget()
        if F.get("uses_q"):
            self.d_q_lab.pack(side="left")
            self.d_q_ent.pack(side="left", padx=(2, 6))
        if F.get("uses_g"):
            self.d_g_lab.pack(side="left")
            self.d_g_ent.pack(side="left", padx=(2, 6))
        self.d_btn.pack(side="left", padx=(4, 0))
        keep = next(p[1] for p in F["params"] if p[0] == F["design_keeps"])
        self.keeps.configure(text=t("fl.keeps").format(p=keep))
        self.explain.configure(text=t("fl.x." + key))
        try:
            P = self.form.values()
            self.d_f0.set(nice(F["info"](P)["f0"]))
            q = F["info"](P).get("q")
            if q:
                self.d_q.set(f"{q:.3g}")
        except Exception:
            pass
        self.update_all()

    def _design(self):
        try:
            P = self.form.values()
            f0 = parse_value(self.d_f0.get())
            q = float(self.d_q.get()) if self.F.get("uses_q") else 0.707
            g = float(self.d_g.get()) if self.F.get("uses_g") else 1.0
            new = self.F["design"](P, f0, q, g)
        except Exception:
            return
        for k, v in new.items():
            self.form.set(k, v)
        self.update_all()

    def _set_f0(self):
        try:
            self.in_form.set("f", self.F["info"](self.form.values())["f0"])
        except Exception:
            return
        self.update_all()

    # ------------------------------------------------------------------
    def update_all(self, *_):
        try:
            P = self.form.values()
            I = self.in_form.values()
            num, den = self.F["tf"](P)
            info = self.F["info"](P)
        except Exception:
            return
        key = self.fkey.get()
        f0 = info["f0"]
        fin = max(I["f"], 1e-3)
        H = fm.freq_response(num, den, [fin])[0]
        tl = self.tiles
        tl.set("f0", eng(f0, "Hz"))
        tl.set("q", f"{info['q']:.3g}" if info.get("q") else "—")
        tl.set("gain", f"{info['gain']:.3g} ({20 * math.log10(max(info['gain'], 1e-12)):+.1f} dB)")
        kind = info["kind"]
        ref = None
        if kind == "bs":
            ref = abs(fm.freq_response(num, den, [f0 / 1000])[0])
        pts = fm.minus3db(num, den, f0 / 1000, f0 * 1000, ref)
        tl.set("bw", " … ".join(eng(p, "Hz") for p in pts[:2]) if pts else "—")
        if kind in ("bp",):
            tl.set("slope", f"±{20 * info['order'] // 2} dB/dec")
        elif kind == "bs":
            tl.set("slope", "notch")
        else:
            tl.set("slope", f"{'−' if kind == 'lp' else '+'}{20 * info['order']} dB/dec")
        tl.set("type", t("fl.k." + kind))
        g_db = 20 * math.log10(max(abs(H), 1e-12))
        tl.set("atf", f"{abs(H):.3g} ({g_db:+.1f} dB)")
        tl.set("ph", f"{math.degrees(math.atan2(H.imag, H.real)):+.1f}°")
        self._draw(key, P)
        v = self.view.get()
        fig = self.chart.fig
        fig.clear()
        self.view_note.configure(text="")
        if v == "bode":
            self._bode(fig, num, den, f0, fin, info)
        elif v == "time":
            self._time(fig, num, den, f0, fin, I["amp"])
        elif v == "step":
            self._step(fig, num, den, f0, info)
        elif v == "pz":
            self._pz(fig, num, den, f0)
            self.view_note.configure(text=t("fl.pz.note"))
        else:
            self._spec(fig, num, den, fin, I["amp"])
            self.view_note.configure(text=t("fl.spec.note"))
        self.chart.redraw()

    def _style(self, ax):
        ax.set_facecolor(PLOT_BG)
        ax.grid(True, alpha=0.25, which="both")
        ax.tick_params(labelsize=8)

    def _bode(self, fig, num, den, f0, fin, info):
        f = np.logspace(math.log10(f0) - 3, math.log10(f0) + 3, 800)
        H = fm.freq_response(num, den, f)
        mag = 20 * np.log10(np.maximum(np.abs(H), 1e-9))
        ph = np.degrees(np.unwrap(np.angle(H)))
        a1 = fig.add_subplot(211)
        a2 = fig.add_subplot(212, sharex=a1)
        a1.semilogx(f, mag, color=C_OUT, lw=2)
        top = max(mag.max(), 0)
        a1.set_ylim(max(mag.min(), top - 80) - 3, top + 6)
        ref = 20 * math.log10(max(info["gain"], 1e-12))
        a1.axhline(ref - 3, color="#999", ls=":", lw=1)
        a1.text(f[0], ref - 3, " −3 dB", fontsize=7, color="#666", va="bottom")
        a2.semilogx(f, ph, color=C_PH, lw=2)
        for a in (a1, a2):
            a.axvline(f0, color="#888", ls="--", lw=1)
            a.axvline(fin, color=C_IN, ls="-", lw=1.2, alpha=0.8)
            self._style(a)
        Hin = fm.freq_response(num, den, [fin])[0]
        a1.plot([fin], [20 * math.log10(max(abs(Hin), 1e-9))], "o", color=C_IN)
        a1.annotate(f"f0 = {eng(f0, 'Hz')}", (f0, a1.get_ylim()[0]), xytext=(4, 4), textcoords="offset points",
                    fontsize=8, color="#555")
        a1.set_ylabel(t("fl.ax.mag"), fontsize=9)
        a2.set_ylabel(t("fl.ax.ph"), fontsize=9)
        a2.set_xlabel(t("fl.ax.f"), fontsize=9)
        a1.tick_params(labelbottom=False)
        fig.subplots_adjust(left=0.1, right=0.98, top=0.97, bottom=0.1, hspace=0.08)

    def _time(self, fig, num, den, f0, fin, amp):
        ax = fig.add_subplot(111)
        wv = self.wave.get()
        if wv == "sweep":
            flo, fhi = f0 / 10, f0 * 10
            T = 15 / flo
            n = int(min(60000, max(4000, T * fhi * 20)))
            tt = np.linspace(0, T, n)
            x = fm.waveform("sweep", amp, fin, tt, flo, fhi)
            y = fm.simulate(num, den, tt, x)
            ax.plot(tt * 1e3, x, color=C_IN, lw=0.6, alpha=0.6, label=t("fl.leg.in"))
            ax.plot(tt * 1e3, y, color=C_OUT, lw=0.8, label=t("fl.leg.out"))
            # secondary x labels: frequency at a few times
            k = math.log(fhi / flo) / T
            for fr in (flo, f0, fhi):
                tx = math.log(fr / flo) / k * 1e3
                ax.axvline(tx, color="#888", ls=":", lw=1)
                ax.text(tx, ax.get_ylim()[1] if False else amp * 1.05, eng(fr, "Hz"), fontsize=7, ha="center",
                        color="#555")
        else:
            periods = 6
            T = periods / fin
            n = int(min(40000, max(3000, T * max(fin * 200, f0 * 40))))
            tt = np.linspace(0, T, n)
            x = fm.waveform(wv, amp, fin, tt)
            y = fm.simulate(num, den, tt, x)
            ax.plot(tt * 1e3, x, color=C_IN, lw=1.3, label=t("fl.leg.in"))
            ax.plot(tt * 1e3, y, color=C_OUT, lw=2, label=t("fl.leg.out"))
        ax.set_xlabel(t("fl.ax.t"), fontsize=9)
        ax.set_ylabel(t("fl.ax.v"), fontsize=9)
        ax.legend(fontsize=8, loc="upper right")
        self._style(ax)
        fig.subplots_adjust(left=0.1, right=0.98, top=0.95, bottom=0.11)

    def _step(self, fig, num, den, f0, info):
        ax = fig.add_subplot(111)
        T = 8 / f0 if info.get("q", 0) is None or (info.get("q") or 0) < 2 else (info["q"] * 3) / f0
        T = max(T, 5 / f0)
        n = 6000
        tt = np.linspace(0, T, n)
        x = np.ones_like(tt)
        y = fm.simulate(num, den, tt, x)
        ax.plot(tt * 1e3, x, color=C_IN, lw=1.2, label=t("fl.leg.in"))
        ax.plot(tt * 1e3, y, color=C_OUT, lw=2, label=t("fl.leg.out"))
        tau = 1 / (2 * math.pi * f0)
        ax.axvline(tau * 1e3, color="#888", ls=":", lw=1)
        ax.text(tau * 1e3, ax.get_ylim()[1], " τ = 1/(2πf0)", fontsize=7, color="#555", va="top")
        ax.set_xlabel(t("fl.ax.t"), fontsize=9)
        ax.set_ylabel(t("fl.ax.v"), fontsize=9)
        ax.legend(fontsize=8, loc="best")
        self._style(ax)
        fig.subplots_adjust(left=0.1, right=0.98, top=0.95, bottom=0.11)

    def _pz(self, fig, num, den, f0):
        ax = fig.add_subplot(111)
        w0 = 2 * math.pi * f0
        z = np.roots(num) / w0 if len(num) > 1 else np.array([])
        p = np.roots(den) / w0
        ax.axhline(0, color="#999", lw=0.8)
        ax.axvline(0, color="#999", lw=0.8)
        th = np.linspace(0, 2 * math.pi, 200)
        ax.plot(np.cos(th), np.sin(th), color="#bbb", ls=":", lw=1)
        ax.plot(p.real, p.imag, "x", color="#c62828", ms=12, mew=2.5, label=tr("poles", "poli"))
        if len(z):
            ax.plot(z.real, z.imag, "o", mfc="none", color=C_OUT, ms=11, mew=2, label=tr("zeros", "zerouri"))
        lim = max(1.5, float(np.max(np.abs(np.concatenate([p, z])))) * 1.2 if len(z) else
                  float(np.max(np.abs(p))) * 1.2)
        lim = min(lim, 10)
        ax.set_xlim(-lim, lim * 0.6)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal", adjustable="box")
        ax.axvspan(0, lim, color="#c62828", alpha=0.05)
        ax.set_xlabel(t("fl.ax.re"), fontsize=9)
        ax.set_ylabel(t("fl.ax.im"), fontsize=9)
        ax.legend(fontsize=8, loc="upper left")
        self._style(ax)
        fig.subplots_adjust(left=0.1, right=0.98, top=0.95, bottom=0.11)

    def _spec(self, fig, num, den, fin, amp):
        ax = fig.add_subplot(111)
        wv = self.wave.get()
        if wv == "sweep":
            wv = "square"
        hs = fm.harmonics(wv, amp, 15)
        k = np.array([h[0] for h in hs])
        a_in = np.array([h[1] for h in hs])
        Hk = np.abs(fm.freq_response(num, den, k * fin))
        a_out = a_in * Hk
        ax.bar(k - 0.18, a_in, width=0.36, color=C_IN, alpha=0.45, label=t("fl.leg.in"))
        ax.bar(k + 0.18, a_out, width=0.36, color=C_OUT, label=t("fl.leg.out"))
        kk = np.linspace(0.5, 15.5, 300)
        ax2 = ax.twinx()
        ax2.plot(kk, np.abs(fm.freq_response(num, den, kk * fin)), color="#555", lw=1, ls="--")
        ax2.set_ylabel("|H|", fontsize=9)
        ax2.set_ylim(0, max(1.05, float(np.max(np.abs(fm.freq_response(num, den, kk * fin)))) * 1.05))
        ax2.tick_params(labelsize=8)
        ax.set_xticks(range(1, 16))
        ax.set_xlabel(t("fl.ax.h"), fontsize=9)
        ax.set_ylabel(t("fl.ax.a"), fontsize=9)
        ax.legend(fontsize=8, loc="upper right")
        self._style(ax)
        fig.subplots_adjust(left=0.1, right=0.9, top=0.95, bottom=0.11)

    # ------------------------------------------------------------------
    def _draw(self, key, P):
        cv = self.canvas
        cv.delete("all")
        top, bot = 100, 225

        def v(k):
            unit = next(p[3] for p in self.F["params"] if p[0] == k)
            return eng(P[k], unit)

        def vin(x=25, y=top):
            sym.terminal(cv, x, y, label="Vin")

        def vout(x=430, y=top):
            sym.terminal(cv, x, y, label="Vout")

        def rail(x1=25, x2=430):
            sym.wire(cv, x1, bot, x2, bot)
            sym.ground(cv, (x1 + x2) / 2, bot + 3)
            sym.terminal(cv, x1, bot)
            sym.terminal(cv, x2, bot)

        def ser(kind, x1, x2, label, value, y=top):
            sym.component(cv, kind, x1, y, x2, y, label=label, value=value)

        def shunt(kind, x, label, value, y1=top, y2=bot, side=1):
            sym.node(cv, x, y1)
            sym.component(cv, kind, x, y1, x, y2, label=label, value=value, label_side=side)
            sym.node(cv, x, y2)

        simple = {
            "rc_lp": [("s", "resistor", "R", "r"), ("p", "capacitor", "C", "c")],
            "rc_hp": [("s", "capacitor", "C", "c"), ("p", "resistor", "R", "r")],
            "rl_lp": [("s", "inductor", "L", "l"), ("p", "resistor", "R", "r")],
            "rl_hp": [("s", "resistor", "R", "r"), ("p", "inductor", "L", "l")],
            "rcrc_lp": [("s", "resistor", "R1", "r1"), ("p", "capacitor", "C1", "c1"),
                        ("s", "resistor", "R2", "r2"), ("p", "capacitor", "C2", "c2")],
            "rlc_bp": [("s", "inductor", "L", "l"), ("s", "capacitor", "C", "c"), ("p", "resistor", "R", "r")],
            "lc_lp": [("s", "inductor", "L", "l"), ("p", "capacitor", "C", "c"), ("p", "resistor", "R", "r")],
            "lc_hp": [("s", "capacitor", "C", "c"), ("p", "inductor", "L", "l"), ("p", "resistor", "R", "r")],
        }
        if key in simple:
            items = simple[key]
            vin()
            x = 25
            n_s = sum(1 for it in items if it[0] == "s")
            seg = 330 / (n_s + sum(1 for it in items if it[0] == "p") * 0.6)
            for kind_, comp, lab, k in items:
                if kind_ == "s":
                    sym.wire(cv, x, top, x + 15, top)
                    ser(comp, x + 15, x + 15 + seg * 0.85, lab, v(k))
                    x = x + 15 + seg * 0.85
                else:
                    sym.wire(cv, x, top, x + 30, top)
                    x += 45
                    sym.wire(cv, x - 15, top, x, top)
                    shunt(comp, x, lab, v(k))
            sym.wire(cv, x, top, 430, top)
            vout()
            rail()
        elif key == "rlc_bs":
            vin()
            sym.wire(cv, 25, top, 50, top)
            ser("resistor", 50, 170, "R", v("r"))
            sym.wire(cv, 170, top, 430, top)
            x = 280
            sym.node(cv, x, top)
            mid = (top + bot) / 2
            sym.inductor(cv, x, top, x, mid, label="L", value=v("l"), label_side=1)
            sym.capacitor(cv, x, mid, x, bot, label="C", value=v("c"), label_side=1)
            sym.node(cv, x, bot)
            vout()
            rail()
        elif key == "twin_t":
            yt, yb = 65, 175
            ym = (yt + yb) / 2
            sym.terminal(cv, 20, ym, label="Vin")
            sym.wire(cv, 20, ym, 55, ym, 55, yt, 70, yt)
            sym.wire(cv, 55, ym, 55, yb, 70, yb)
            sym.node(cv, 55, ym)
            ser("resistor", 70, 185, "R", v("r"), y=yt)
            ser("resistor", 235, 350, "R", None, y=yt)
            sym.wire(cv, 185, yt, 235, yt)
            sym.node(cv, 210, yt)
            sym.capacitor(cv, 210, yt, 210, yt + 55, label="2C", label_side=1)
            sym.ground(cv, 210, yt + 55)
            ser("capacitor", 70, 185, "C", v("c"), y=yb)
            ser("capacitor", 235, 350, "C", None, y=yb)
            sym.wire(cv, 185, yb, 235, yb)
            sym.node(cv, 210, yb)
            sym.resistor(cv, 210, yb, 210, yb + 60, label="R/2", label_side=1)
            sym.ground(cv, 210, yb + 60)
            sym.wire(cv, 350, yt, 380, yt, 380, yb, 350, yb)
            sym.wire(cv, 380, ym, 430, ym)
            sym.node(cv, 380, ym)
            sym.terminal(cv, 430, ym, label="Vout")
        else:
            self._draw_active(key, P, v)
            cv.move("all", 0, 28)

    def _draw_active(self, key, P, v):
        cv = self.canvas
        cx, cy = 320, 140
        inv_y, non_y = cy - 14, cy + 14
        in_x, out_x = cx - 48, cx + 48
        sym.opamp(cv, cx, cy, supplies=True)
        sym.wire(cv, out_x, cy, 440, cy)
        sym.node(cv, 400, cy)
        sym.terminal(cv, 440, cy, label="Vout")
        if key == "act_lp1":
            sym.terminal(cv, 20, inv_y, label="Vin")
            sym.resistor(cv, 20, inv_y, 170, inv_y, label="Rin", value=v("rin"))
            sym.wire(cv, 170, inv_y, in_x, inv_y)
            sym.node(cv, 220, inv_y)
            sym.wire(cv, 220, inv_y, 220, 40)
            sym.resistor(cv, 220, 88, 400, 88, label="Rf", value=v("rf"), label_side=-1)
            sym.capacitor(cv, 220, 40, 400, 40, label="C", value=v("c"))
            sym.wire(cv, 400, 40, 400, cy)
            sym.node(cv, 220, 88)
            sym.node(cv, 400, 88)
            sym.wire(cv, in_x, non_y, 240, non_y, 240, 215)
            sym.ground(cv, 240, 215)
        elif key in ("sk_lp", "sk_hp"):
            lp = key == "sk_lp"
            sym.terminal(cv, 15, non_y, label="Vin")
            k1, k2 = ("resistor", "resistor") if lp else ("capacitor", "capacitor")
            l1, l2 = ("R1", "R2") if lp else ("C1", "C2")
            v1, v2 = (v("r1"), v("r2")) if lp else (v("c1"), v("c2"))
            sym.component(cv, k1, 15, non_y, 120, non_y, label=l1, value=v1, label_side=1)
            sym.wire(cv, 120, non_y, 140, non_y)
            sym.node(cv, 140, non_y)
            sym.component(cv, k2, 140, non_y, 225, non_y, label=l2, value=v2, label_side=1)
            sym.wire(cv, 225, non_y, in_x, non_y)
            sym.node(cv, 240, non_y)
            if lp:
                sym.capacitor(cv, 240, non_y, 240, 240, label="C2", label_side=1)
            else:
                sym.resistor(cv, 240, non_y, 240, 240, label="Rb", value=v("rb"), label_side=1)
            sym.ground(cv, 240, 240)
            # feedback element from the middle node to the output (over the top)
            sym.wire(cv, 140, non_y, 140, 45)
            if lp:
                sym.capacitor(cv, 140, 45, 400, 45, label="C1", value=v("c1"))
            else:
                sym.resistor(cv, 140, 45, 400, 45, label="Ra", value=v("ra"))
            sym.wire(cv, 400, 45, 400, cy)
            # unity-gain: (-) to output
            sym.wire(cv, in_x, inv_y, 255, inv_y, 255, 95, 400, 95)
            sym.node(cv, 400, 95)
        elif key == "mfb_bp":
            sym.terminal(cv, 15, inv_y, label="Vin")
            sym.resistor(cv, 15, inv_y, 110, inv_y, label="R1", value=v("r1"))
            sym.wire(cv, 110, inv_y, 140, inv_y)
            sym.node(cv, 140, inv_y)
            sym.capacitor(cv, 140, inv_y, 230, inv_y, label="C1")
            sym.wire(cv, 230, inv_y, in_x, inv_y)
            sym.node(cv, 245, inv_y)
            sym.resistor(cv, 140, inv_y, 140, 240, label="R2", value=v("r2"), label_side=-1)
            sym.ground(cv, 140, 240)
            sym.wire(cv, 140, inv_y, 140, 40)
            sym.capacitor(cv, 140, 40, 400, 40, label="C2", value=v("c"))
            sym.wire(cv, 400, 40, 400, cy)
            sym.wire(cv, 245, inv_y, 245, 90)
            sym.resistor(cv, 245, 90, 400, 90, label="R3", value=v("r3"), label_side=-1)
            sym.node(cv, 400, 90)
            sym.wire(cv, in_x, non_y, 255, non_y, 255, 215)
            sym.ground(cv, 255, 215)


class FilterTab(ttk.Frame):
    """Signals > Filters: the v6 Filter Lab plus the older L-section builder."""

    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        ttk.Label(self, text=t("fl.title"), font=FONT_H1, style="TabTitle.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))
        holder = ttk.Frame(self, style="Tab.TFrame")
        holder.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        holder.columnconfigure(0, weight=1)
        holder.rowconfigure(0, weight=1)
        nb = ttk.Notebook(holder)
        nb.grid(row=0, column=0, sticky="nsew")
        nb.add(FilterLabPanel(nb), text=t("fl.lab"))

        def custom(parent):
            from .divider import _DividerFilterBase
            return _DividerFilterBase(parent, show_title=False, intro_key="filter.intro",
                                      default_series_idx=0, default_shunt_idx=1)
        lazy_tab(nb, t("fl.custom"), custom)
