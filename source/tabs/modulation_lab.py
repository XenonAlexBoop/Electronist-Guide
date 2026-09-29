"""
tabs/modulation_lab.py - v6 Modulation Lab.

One screen, no scrolling needed: pick a scheme from the button bar (analog
AM / DSB-SC / SSB / FM / PM, digital ASK / FSK / BPSK / QPSK), drag the
sliders, and switch between four views:

    Overview    message -> modulated signal (with envelope) -> spectrum
    Spectrum    larger spectrum (linear or dB) with the bandwidth marked
    Demodulate  what an ideal receiver recovers vs. the original message
    I/Q (phasor) the complex envelope: where the carrier's phasor goes

Every signal is built from its complex envelope e(t):
    s(t) = Re{ e(t) · exp(j·2π·fc·t) }
which makes the demodulated outputs and the I/Q view exact.
"""
import math
import numpy as np
import tkinter as tk
from tkinter import ttk

from charts import MplChartFrame, PLOT_BG
from widgets import ScrollableFrame, FONT_BODY
from uikit import Segmented, ParamForm, TileRow, note, eng
from i18n import t, register, tr

ACCENT_C = "#7c3aed"
MSG = "#2A9D8F"
MOD = "#7c3aed"
CAR = "#c9622a"

register({
    "ml.analog": ("Analog", "Analogic"),
    "ml.digital": ("Digital", "Digital"),
    "ml.m.am": ("AM", "MA"), "ml.m.dsb": ("DSB-SC", "DSB-SC"), "ml.m.ssb": ("SSB (USB)", "BLU (sup.)"),
    "ml.m.fm": ("FM", "MF"), "ml.m.pm": ("PM", "MP"),
    "ml.m.ask": ("ASK / OOK", "ASK / OOK"), "ml.m.fsk": ("FSK", "FSK"), "ml.m.bpsk": ("BPSK", "BPSK"),
    "ml.m.qpsk": ("QPSK", "QPSK"),
    "ml.message": ("Message", "Mesaj"),
    "ml.w.sine": ("Sine", "Sinus"), "ml.w.square": ("Square", "Dreptunghi"),
    "ml.w.tri": ("Triangle", "Triunghi"), "ml.w.saw": ("Sawtooth", "Dinte de fierăstrău"),
    "ml.w.two": ("Two tones", "Două tonuri"),
    "ml.fm_": ("Message frequency fm", "Frecvența mesajului fm"),
    "ml.bits": ("Bits", "Biți"),
    "ml.rate": ("Bit rate", "Rata de bit"),
    "ml.carrier": ("Carrier", "Purtătoare"),
    "ml.fc": ("Carrier frequency fc", "Frecvența purtătoarei fc"),
    "ml.ac": ("Carrier amplitude Ac", "Amplitudinea purtătoarei Ac"),
    "ml.p.m": ("Modulation index m", "Indice de modulație m"),
    "ml.p.dev": ("Frequency deviation Δf", "Deviația de frecvență Δf"),
    "ml.p.pdev": ("Phase deviation Δφ (°)", "Deviația de fază Δφ (°)"),
    "ml.p.fsk": ("FSK shift ±Δf", "Deplasare FSK ±Δf"),
    "ml.view": ("View", "Vizualizare"),
    "ml.v.over": ("Overview", "Ansamblu"), "ml.v.spec": ("Spectrum", "Spectru"),
    "ml.v.demod": ("Demodulate", "Demodulare"), "ml.v.iq": ("I/Q (phasor)", "I/Q (fazor)"),
    "ml.db": ("dB scale", "Scară dB"),
    "ml.t.bw": ("Bandwidth", "Lățime de bandă"),
    "ml.t.index": ("Modulation index", "Indice de modulație"),
    "ml.t.eff": ("Power in sidebands", "Putere în benzile laterale"),
    "ml.t.pk": ("Peak amplitude", "Amplitudine de vârf"),
    "ml.t.rule": ("Rule used", "Regula folosită"),
    "ml.t.baud": ("Symbol rate", "Rata de simboluri"),
    "ml.t.bps": ("Bits per symbol", "Biți pe simbol"),
    "ml.ax.t": ("Time (ms)", "Timp (ms)"),
    "ml.ax.f": ("Frequency (Hz)", "Frecvență (Hz)"),
    "ml.ax.a": ("Amplitude", "Amplitudine"),
    "ml.ax.mag": ("Magnitude", "Magnitudine"),
    "ml.p.msg": ("Message", "Mesaj"),
    "ml.p.mod": ("Modulated signal", "Semnal modulat"),
    "ml.p.spec": ("Spectrum", "Spectru"),
    "ml.p.demod": ("Recovered (ideal receiver)", "Recuperat (receptor ideal)"),
    "ml.p.orig": ("original message", "mesajul original"),
    "ml.p.iq": ("Complex envelope (I/Q plane)", "Anvelopa complexă (planul I/Q)"),
    "ml.env": ("envelope", "anvelopă"),
    "ml.overmod": ("OVER-MODULATED (m > 1): the envelope folds, an envelope detector distorts",
                   "SUPRAMODULAT (m > 1): anvelopa se pliază, detectorul de anvelopă distorsionează"),
    "ml.x.am": ("The message changes the carrier's AMPLITUDE: s = Ac·(1 + m·x(t))·cos(2πfc·t). The spectrum is the "
                "carrier plus two mirror-image sidebands at fc ± fm, so B = 2·fm. At m = 1 only 1/3 of the power "
                "carries information; m > 1 over-modulates.",
                "Mesajul modifică AMPLITUDINEA purtătoarei: s = Ac·(1 + m·x(t))·cos(2πfc·t). Spectrul are "
                "purtătoarea plus două benzi laterale simetrice la fc ± fm, deci B = 2·fm. La m = 1 doar 1/3 din "
                "putere poartă informație; m > 1 supramodulează."),
    "ml.x.dsb": ("Double-sideband suppressed carrier: s = Ac·x(t)·cos(2πfc·t). No wasted carrier power, same "
                 "2·fm bandwidth, but the envelope is |x(t)| — the receiver must regenerate the carrier "
                 "(coherent detection). Note the 180° phase flips where x(t) crosses zero.",
                 "Bandă laterală dublă cu purtătoare suprimată: s = Ac·x(t)·cos(2πfc·t). Fără putere irosită în "
                 "purtătoare, aceeași bandă 2·fm, dar anvelopa este |x(t)| — receptorul trebuie să refacă "
                 "purtătoarea (detecție coerentă). Observă salturile de fază de 180° la trecerile prin zero."),
    "ml.x.ssb": ("Single sideband: the lower sideband is removed (Hilbert transform), so B = fm — half of AM. "
                 "Used for HF voice radio. With a single tone the output is just one sine at fc + fm.",
                 "Bandă laterală unică: banda inferioară e eliminată (transformata Hilbert), deci B = fm — jumătate "
                 "din MA. Folosită în radio de voce pe unde scurte. Cu un singur ton, ieșirea e un singur sinus "
                 "la fc + fm."),
    "ml.x.fm": ("The message changes the carrier's FREQUENCY: f(t) = fc + Δf·x(t). The amplitude never changes "
                "(robust to noise and amplitude distortion). β = Δf/fm; the spectrum has many sidebands spaced fm "
                "apart; Carson's rule: B ≈ 2·(Δf + fm).",
                "Mesajul modifică FRECVENȚA purtătoarei: f(t) = fc + Δf·x(t). Amplitudinea nu se schimbă niciodată "
                "(rezistent la zgomot și distorsiuni de amplitudine). β = Δf/fm; spectrul are multe benzi "
                "laterale la distanțe fm; regula lui Carson: B ≈ 2·(Δf + fm)."),
    "ml.x.pm": ("The message changes the carrier's PHASE: φ(t) = Δφ·x(t). PM and FM are relatives — PM of a "
                "signal equals FM of its derivative, so a square message gives phase jumps (and wide spectrum).",
                "Mesajul modifică FAZA purtătoarei: φ(t) = Δφ·x(t). MP și MF sunt înrudite — MP a unui semnal este "
                "MF a derivatei lui, deci un mesaj dreptunghiular dă salturi de fază (și spectru larg)."),
    "ml.x.ask": ("Amplitude-shift keying / on-off keying: carrier on for 1, off for 0. The simplest digital "
                 "scheme (IR remotes, 433 MHz key fobs) but sensitive to noise and fading.",
                 "Modulație prin salt de amplitudine / on-off: purtătoare prezentă pentru 1, absentă pentru 0. Cea mai "
                 "simplă schemă digitală (telecomenzi IR, chei de 433 MHz), dar sensibilă la zgomot."),
    "ml.x.fsk": ("Frequency-shift keying: 1 → fc + Δf, 0 → fc − Δf, with continuous phase. Constant amplitude, "
                 "easy to receive; used by old modems, pagers, LoRa's cousins and many ISM-band radios.",
                 "Modulație prin salt de frecvență: 1 → fc + Δf, 0 → fc − Δf, cu fază continuă. Amplitudine "
                 "constantă, ușor de recepționat; folosită de modemurile vechi, pagere și multe radiouri ISM."),
    "ml.x.bpsk": ("Binary phase-shift keying: 1 → 0°, 0 → 180°. In the I/Q plane the carrier jumps between two "
                  "opposite points — the most noise-robust of the simple schemes (GPS, deep-space links).",
                  "Modulație binară prin salt de fază: 1 → 0°, 0 → 180°. În planul I/Q purtătoarea sare între două "
                  "puncte opuse — cea mai robustă la zgomot dintre schemele simple (GPS, legături spațiale)."),
    "ml.x.qpsk": ("Quadrature PSK: bits are taken in pairs and each pair picks one of four phases (45°, 135°, "
                  "225°, 315°): twice the data of BPSK in the same bandwidth. Basis of Wi-Fi, LTE, DVB-S.",
                  "PSK în cuadratură: biții sunt luați câte doi și fiecare pereche alege una din patru faze (45°, "
                  "135°, 225°, 315°): de două ori mai multe date decât BPSK în aceeași bandă. Baza Wi-Fi, LTE, DVB-S."),
})

ANALOG = ["am", "dsb", "ssb", "fm", "pm"]
DIGITAL = ["ask", "fsk", "bpsk", "qpsk"]


def _msg(kind, f, t):
    ph = np.mod(f * t, 1.0)
    if kind == "square":
        return np.where(ph < 0.5, 1.0, -1.0)
    if kind == "tri":
        return 2 / math.pi * np.arcsin(np.sin(2 * math.pi * f * t))
    if kind == "saw":
        return 2 * ph - 1
    if kind == "two":
        return 0.6 * np.sin(2 * math.pi * f * t) + 0.4 * np.sin(2 * math.pi * 2.5 * f * t)
    return np.sin(2 * math.pi * f * t)


def _cis(theta):
    """exp(j·theta) built from cos/sin: numpy's complex exp goes through the C
    runtime's cexp(), which Wine's ucrtbase lacks (crashes only under Wine)."""
    theta = np.asarray(theta, float)
    return np.cos(theta) + 1j * np.sin(theta)


def _hilbert(x):
    n = len(x)
    X = np.fft.fft(x)
    h = np.zeros(n)
    if n % 2 == 0:
        h[0] = h[n // 2] = 1
        h[1:n // 2] = 2
    else:
        h[0] = 1
        h[1:(n + 1) // 2] = 2
    return np.fft.ifft(X * h).imag


class ModulationLabPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        accent = ACCENT_C
        self.accent = accent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body

        bar = ttk.Frame(body, style="Card.TFrame")
        bar.pack(fill="x", padx=16, pady=(12, 0))
        self.mode = tk.StringVar(value="am")
        ttk.Label(bar, text=t("ml.analog"), font=("Segoe UI", 9, "bold"), style="CardBody.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.seg_a = Segmented(bar, [(k, t("ml.m." + k)) for k in ANALOG], self.mode, self._on_mode,
                               accent=accent, font_size=10)
        self.seg_a.grid(row=0, column=1, sticky="w")
        ttk.Label(bar, text=t("ml.digital"), font=("Segoe UI", 9, "bold"), style="CardBody.TLabel")\
            .grid(row=0, column=2, sticky="w", padx=(18, 6))
        self.seg_d = Segmented(bar, [(k, t("ml.m." + k)) for k in DIGITAL], self.mode, self._on_mode,
                               accent=accent, font_size=10)
        self.seg_d.grid(row=0, column=3, sticky="w")

        top = ttk.Frame(body, style="Card.TFrame")
        top.pack(fill="both", expand=True, padx=16, pady=(10, 12))
        top.columnconfigure(1, weight=1)
        left = ttk.Frame(top, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nw")
        right = ttk.Frame(top, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        self.left = left

        ttk.Label(left, text=t("ml.message"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel")\
            .pack(anchor="w")
        self.msg_box = ttk.Frame(left, style="Card.TFrame")
        self.msg_box.pack(anchor="w", fill="x")
        self.wave = tk.StringVar(value="sine")
        Segmented(self.msg_box, [(k, t("ml.w." + k)) for k in ("sine", "square", "tri", "saw", "two")],
                  self.wave, lambda k: self.update_all(), accent=accent).pack(anchor="w", pady=(2, 4))
        self.msg_form = ParamForm(self.msg_box, [
            dict(key="fm", label=t("ml.fm_"), default="200", unit="Hz", slider=(10, 5e3, True)),
        ], self.update_all, label_width=22)
        self.msg_form.pack(anchor="w")
        self.bit_box = ttk.Frame(left, style="Card.TFrame")
        r = ttk.Frame(self.bit_box, style="Card.TFrame")
        r.pack(anchor="w", pady=(2, 2))
        ttk.Label(r, text=t("ml.bits"), font=FONT_BODY, style="CardBody.TLabel", width=22, anchor="w")\
            .pack(side="left")
        self.bits = tk.StringVar(value="10110010")
        e = ttk.Entry(r, textvariable=self.bits, width=14, font=("Consolas", 11))
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda _e: self.update_all())
        self.bit_form = ParamForm(self.bit_box, [
            dict(key="rate", label=t("ml.rate"), default="500", unit="bit/s", slider=(50, 5e3, True)),
        ], self.update_all, label_width=22)
        self.bit_form.pack(anchor="w")

        ttk.Label(left, text=t("ml.carrier"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel")\
            .pack(anchor="w", pady=(8, 0))
        self.car_form = ParamForm(left, [
            dict(key="fc", label=t("ml.fc"), default="5k", unit="Hz", slider=(500, 50e3, True)),
            dict(key="ac", label=t("ml.ac"), default="1", unit="V", slider=(0.1, 5)),
        ], self.update_all, label_width=22)
        self.car_form.pack(anchor="w")
        self.param_holder = ttk.Frame(left, style="Card.TFrame")
        self.param_holder.pack(anchor="w", fill="x", pady=(6, 0))
        self.tiles = TileRow(left, [("a", "a"), ("b", "b"), ("c", "c"), ("d", "d")], accent, per_row=2)
        self.tiles.pack(fill="x", pady=(10, 0))
        self.warn = note(left, "", wrap=400, padx=0, color="#c62828")
        self.explain = note(left, "", wrap=400, padx=0, pady=(6, 4))

        vrow = ttk.Frame(right, style="Card.TFrame")
        vrow.pack(anchor="w", fill="x")
        self.view = tk.StringVar(value="over")
        Segmented(vrow, [(k, t("ml.v." + k)) for k in ("over", "spec", "demod", "iq")], self.view,
                  lambda k: self.update_all(), accent=accent, font_size=10).pack(side="left")
        self.db = tk.BooleanVar(value=False)
        ttk.Checkbutton(vrow, text=t("ml.db"), variable=self.db, command=self.update_all).pack(side="left", padx=12)
        self.chart = MplChartFrame(right, figsize=(7.6, 5.6), with_toolbar=True)
        self.chart.pack(fill="both", expand=True, pady=(6, 0))
        self._params = {}
        self._on_mode("am")

    # ------------------------------------------------------------------
    def _on_mode(self, key):
        self.seg_a._paint()
        self.seg_d._paint()
        for w in self.param_holder.winfo_children():
            w.destroy()
        fields = {
            "am": [dict(key="m", label=t("ml.p.m"), default="0.6", unit="", slider=(0, 1.5))],
            "fm": [dict(key="dev", label=t("ml.p.dev"), default="1k", unit="Hz", slider=(10, 20e3, True))],
            "pm": [dict(key="pdev", label=t("ml.p.pdev"), default="90", unit="°", slider=(1, 360))],
            "fsk": [dict(key="shift", label=t("ml.p.fsk"), default="1k", unit="Hz", slider=(50, 10e3, True))],
        }.get(key, [])
        self.pform = ParamForm(self.param_holder, fields, self.update_all, label_width=22) if fields else None
        if self.pform:
            self.pform.pack(anchor="w")
        digital = key in DIGITAL
        if digital:
            self.msg_box.pack_forget()
            if not self.bit_box.winfo_ismapped():
                self.bit_box.pack(anchor="w", fill="x", after=self.left.winfo_children()[0])
        else:
            self.bit_box.pack_forget()
            if not self.msg_box.winfo_ismapped():
                self.msg_box.pack(anchor="w", fill="x", after=self.left.winfo_children()[0])
        self.explain.configure(text=t("ml.x." + key))
        self.update_all()

    # ------------------------------------------------------------------
    def _signals(self, reps=1):
        key = self.mode.get()
        C = self.car_form.values()
        fc, ac = max(C["fc"], 1), C["ac"]
        P = self.pform.values() if self.pform else {}
        if key in DIGITAL:
            bits = [int(c) for c in self.bits.get() if c in "01"] or [1, 0]
            rate = max(self.bit_form.get("rate"), 1)
            if key == "qpsk" and len(bits) % 2:
                bits = bits + [0]
            bits = bits * reps
            T = len(bits) / rate
            n = int(np.clip(40 * fc * T, 3000, 60000 * reps))
            tt = np.linspace(0, T, n, endpoint=False)
            idx = np.minimum((tt * rate).astype(int), len(bits) - 1)
            b = np.array(bits, float)[idx]
            x = 2 * b - 1
            if key == "ask":
                env = ac * b
            elif key == "fsk":
                dt = tt[1] - tt[0]
                env = ac * _cis(2 * math.pi * P["shift"] * np.cumsum(x) * dt)
            elif key == "bpsk":
                env = ac * x.astype(complex)
            else:
                sym = np.minimum((tt * rate / 2).astype(int), len(bits) // 2 - 1)
                pairs = np.array(bits).reshape(-1, 2)
                # Gray mapping: 00->45, 01->135, 11->225, 10->315
                gray = {(0, 0): 45, (0, 1): 135, (1, 1): 225, (1, 0): 315}
                ph = np.radians([gray[tuple(p)] for p in pairs])[sym]
                env = ac * _cis(ph)
            msg = x
            fm = rate / 2
        else:
            fm = max(self.msg_form.get("fm"), 0.1)
            T = 3 * reps / fm
            n = int(np.clip(40 * fc * T, 3000, 60000 * reps))
            tt = np.linspace(0, T, n, endpoint=False)
            msg = _msg(self.wave.get(), fm, tt)
            if key == "am":
                env = ac * (1 + P["m"] * msg) + 0j
            elif key == "dsb":
                env = ac * msg + 0j
            elif key == "ssb":
                env = ac * (msg + 1j * _hilbert(msg)) / 2
            elif key == "fm":
                dt = tt[1] - tt[0]
                env = ac * _cis(2 * math.pi * P["dev"] * np.cumsum(msg) * dt)
            else:
                env = ac * _cis(math.radians(P["pdev"]) * msg)
        s = np.real(env * _cis(2 * math.pi * fc * tt))
        return key, tt, msg, env, s, fc, fm, ac, P

    def update_all(self, *_):
        try:
            key, tt, msg, env, s, fc, fm, ac, P = self._signals()
        except Exception:
            return
        self._metrics(key, fc, fm, ac, P, env)
        v = self.view.get()
        fig = self.chart.fig
        fig.clear()
        if v == "over":
            self._overview(fig, key, tt, msg, env, s, fc, fm, P)
        elif v == "spec":
            ax = fig.add_subplot(111)
            self._spectrum(ax, key, tt, s, fc, fm, P, big=True)
            fig.subplots_adjust(left=0.1, right=0.97, top=0.93, bottom=0.1)
        elif v == "demod":
            self._demod(fig, key, tt, msg, env, fc, P, ac)
        else:
            self._iq(fig, key, env)
        self.chart.redraw()

    def _bw(self, key, fm, P):
        if key in ("am", "dsb"):
            return 2 * fm, "B = 2·fm"
        if key == "ssb":
            return fm, "B = fm"
        if key == "fm":
            return 2 * (P["dev"] + fm), "Carson: 2(Δf + fm)"
        if key == "pm":
            return 2 * (math.radians(P["pdev"]) * fm + fm), "Carson: 2(Δφ·fm + fm)"
        rate = self.bit_form.get("rate")
        if key == "fsk":
            return 2 * P["shift"] + 2 * rate, "2Δf + 2·Rb"
        if key == "qpsk":
            return rate, "≈ Rb (null-to-null)"
        return 2 * rate, "≈ 2·Rb (null-to-null)"

    def _set(self, items):
        for k, (cap, val, warn) in zip("abcd", items):
            self.tiles.tiles[k].cap.configure(text=cap)
            self.tiles.set(k, val, warn)

    def _metrics(self, key, fc, fm, ac, P, env):
        bw, rule = self._bw(key, fm, P)
        self.warn.configure(text="")
        if key == "am":
            m = P["m"]
            eff = m * m / (2 + m * m) * 100
            self._set([(t("ml.t.bw"), eng(bw, "Hz"), False), (t("ml.t.index"), f"m = {m:.2f}", m > 1),
                       (t("ml.t.eff"), f"{eff:.0f} %", False), (t("ml.t.pk"), eng(ac * (1 + m), "V"), False)])
            if m > 1:
                self.warn.configure(text=t("ml.overmod"))
        elif key == "fm":
            beta = P["dev"] / fm
            self._set([(t("ml.t.bw"), eng(bw, "Hz"), False), (t("ml.t.index"), f"β = Δf/fm = {beta:.3g}", False),
                       (t("ml.t.rule"), rule, False), (t("ml.t.pk"), eng(ac, "V"), False)])
        elif key == "pm":
            self._set([(t("ml.t.bw"), eng(bw, "Hz"), False),
                       (t("ml.t.index"), f"Δφ = {math.radians(P['pdev']):.3g} rad", False),
                       (t("ml.t.rule"), rule, False), (t("ml.t.pk"), eng(ac, "V"), False)])
        elif key in ("dsb", "ssb"):
            self._set([(t("ml.t.bw"), eng(bw, "Hz"), False), (t("ml.t.rule"), rule, False),
                       (t("ml.t.eff"), "100 %", False), (t("ml.t.pk"), eng(float(np.max(np.abs(env))), "V"), False)])
        else:
            rate = self.bit_form.get("rate")
            bps = 2 if key == "qpsk" else 1
            self._set([(t("ml.t.bw"), eng(bw, "Hz"), False), (t("ml.t.rule"), rule, False),
                       (t("ml.t.baud"), eng(rate / bps, "Bd"), False), (t("ml.t.bps"), str(bps), False)])

    # ------------------------------------------------------------------
    def _style(self, ax, title=None):
        ax.set_facecolor(PLOT_BG)
        ax.grid(True, alpha=0.25)
        ax.tick_params(labelsize=8)
        if title:
            ax.set_title(title, fontsize=9, loc="left", fontweight="bold", color="#333")

    def _overview(self, fig, key, tt, msg, env, s, fc, fm, P):
        a1 = fig.add_subplot(311)
        a2 = fig.add_subplot(312, sharex=a1)
        a3 = fig.add_subplot(313)
        tm = tt * 1e3
        if key in DIGITAL:
            a1.step(tm, (msg + 1) / 2, color=MSG, lw=1.8, where="post")
            bits = [c for c in self.bits.get() if c in "01"]
            rate = self.bit_form.get("rate")
            for i, bch in enumerate(bits):
                a1.text((i + 0.5) / rate * 1e3, 1.12, bch, ha="center", fontsize=9, color=MSG, fontweight="bold")
            a1.set_ylim(-0.2, 1.35)
        else:
            a1.plot(tm, msg, color=MSG, lw=1.8)
        self._style(a1, t("ml.p.msg"))
        a1.tick_params(labelbottom=False)
        a2.plot(tm, s, color=MOD, lw=0.8)
        if key in ("am", "dsb", "ask"):
            a2.plot(tm, np.abs(env), color=MSG, lw=1.4, ls="--", label=t("ml.env"))
            a2.plot(tm, -np.abs(env), color=MSG, lw=1.4, ls="--")
            if key == "am":
                a2.plot(tm, np.real(env), color=CAR, lw=1, ls=":", alpha=0.8)
        self._style(a2, t("ml.p.mod"))
        a2.set_xlabel(t("ml.ax.t"), fontsize=8)
        self._spectrum(a3, key, tt, s, fc, fm, P)
        fig.subplots_adjust(left=0.08, right=0.98, top=0.95, bottom=0.08, hspace=0.55)

    def _spectrum(self, ax, key, tt, s, fc, fm, P, big=False):
        # a longer record than the one on screen -> sharp spectral lines
        try:
            _k, tt, _m, _e, s, *_r = self._signals(reps=6)
        except Exception:
            pass
        n = len(s)
        dt = tt[1] - tt[0]
        w = np.hanning(n)
        X = np.abs(np.fft.rfft(s * w)) / (w.sum() / 2)
        f = np.fft.rfftfreq(n, dt)
        bw, _ = self._bw(key, fm, P)
        span = max(bw * 1.2, 6 * fm, 200)
        lo, hi = max(0, fc - span), fc + span
        sel = (f >= lo) & (f <= hi)
        if self.db.get():
            y = 20 * np.log10(np.maximum(X, 1e-6))
            ax.plot(f[sel], y[sel], color=MOD, lw=1.2)
            ax.set_ylim(max(y[sel].max() - 70, -120), y[sel].max() + 5)
            ax.set_ylabel("dBV", fontsize=8)
        else:
            ax.plot(f[sel], X[sel], color=MOD, lw=1.2)
            ax.fill_between(f[sel], X[sel], color=MOD, alpha=0.15)
            ax.set_ylabel(t("ml.ax.mag"), fontsize=8)
        lo_b = fc - bw / 2 if key != "ssb" else fc
        ax.axvspan(lo_b, lo_b + bw, color="#2e9d44", alpha=0.08)
        ax.axvline(fc, color=CAR, lw=1, ls=":")
        ax.text(fc, ax.get_ylim()[1], " fc", color=CAR, fontsize=8, va="top")
        ax.set_xlim(lo, hi)
        ax.set_xlabel(t("ml.ax.f"), fontsize=8)
        self._style(ax, t("ml.p.spec") + f"  ·  B ≈ {eng(bw, 'Hz')}")

    def _demod(self, fig, key, tt, msg, env, fc, P, ac):
        ax = fig.add_subplot(111)
        tm = tt * 1e3
        dt = tt[1] - tt[0]
        if key == "am":
            rec = (np.abs(env) / ac - 1) / max(P["m"], 1e-6)
            label = tr("|e(t)|  (envelope detector)", "|e(t)|  (detector de anvelopă)")
        elif key in ("dsb", "ssb"):
            rec = np.real(env) / ac * (2 if key == "ssb" else 1)
            label = tr("Re{e(t)}  (coherent detector)", "Re{e(t)}  (detector coerent)")
        elif key == "fm":
            ph = np.unwrap(np.angle(env))
            rec = np.gradient(ph, dt) / (2 * math.pi) / P["dev"]
            label = tr("dφ/dt / 2πΔf  (discriminator)", "dφ/dt / 2πΔf  (discriminator)")
        elif key == "pm":
            rec = np.unwrap(np.angle(env)) / math.radians(P["pdev"])
            label = tr("φ(t) / Δφ  (phase detector)", "φ(t) / Δφ  (detector de fază)")
        elif key == "ask":
            rec = (np.abs(env) / ac > 0.5).astype(float) * 2 - 1
            label = tr("|e(t)| > threshold", "|e(t)| > prag")
        elif key == "fsk":
            ph = np.unwrap(np.angle(env))
            rec = np.sign(np.gradient(ph, dt))
            label = tr("sign of frequency offset", "semnul abaterii de frecvență")
        elif key == "bpsk":
            rec = np.sign(np.real(env))
            label = tr("sign of I", "semnul lui I")
        else:
            rec = np.sign(np.real(env))
            ax.plot(tm, np.sign(np.imag(env)) * 0.5 - 2.6, color=CAR, lw=1.6, label=tr("Q bit (sign of Q)", "bit Q (semnul lui Q)"))
            label = tr("I bit (sign of I)", "bit I (semnul lui I)")
        ax.plot(tm, msg, color="#999", lw=3, alpha=0.6, label=t("ml.p.orig"))
        ax.plot(tm, rec, color=MSG, lw=1.6, label=label)
        ax.set_xlabel(t("ml.ax.t"), fontsize=8)
        ax.legend(fontsize=8, loc="upper right")
        self._style(ax, t("ml.p.demod"))
        fig.subplots_adjust(left=0.08, right=0.98, top=0.93, bottom=0.1)

    def _iq(self, fig, key, env):
        ax = fig.add_subplot(111)
        step = max(1, len(env) // 3000)
        e = env[::step]
        ax.plot(e.real, e.imag, color=MOD, lw=1.2, alpha=0.8)
        if key in ("bpsk", "qpsk", "ask"):
            pts = np.unique(np.round(env, 6))
            ax.plot(pts.real, pts.imag, "o", color="#c62828", ms=10)
            if key == "qpsk":
                for lab, ang in (("00", 45), ("01", 135), ("11", 225), ("10", 315)):
                    r = np.max(np.abs(env)) * 1.18
                    ax.text(r * math.cos(math.radians(ang)), r * math.sin(math.radians(ang)), lab,
                            ha="center", va="center", fontsize=10, fontweight="bold", color="#c62828")
        lim = float(np.max(np.abs(env))) * 1.35 + 1e-9
        ax.set_xlim(-lim, lim)
        ax.set_ylim(-lim, lim)
        ax.set_aspect("equal", adjustable="box")
        ax.axhline(0, color="#999", lw=0.8)
        ax.axvline(0, color="#999", lw=0.8)
        ax.set_xlabel(tr("I (in-phase)", "I (în fază)"), fontsize=8)
        ax.set_ylabel(tr("Q (quadrature)", "Q (cuadratură)"), fontsize=8)
        self._style(ax, t("ml.p.iq"))
        fig.subplots_adjust(left=0.08, right=0.98, top=0.93, bottom=0.1)
