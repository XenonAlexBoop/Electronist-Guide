"""
tabs/diode_lab.py - v6 additions to the Diodes page:

  DiodeLabPanel      circuit lab: rectifier, clippers, zener clipper,
                     clampers, voltage doubler, envelope (peak) detector,
                     freewheeling diode - simulated with minispice, time
                     cursor highlights which diode conducts
  IVExplorerPanel    I-V curves of Si / Ge / Schottky / LEDs / zener,
                     temperature, log scale, load line + Q point
  ZenerDesignPanel   shunt zener regulator designer (worst-case R, powers,
                     line & load regulation plots)
  LedArrayPanel      series/parallel LED array planner
"""
import math
import numpy as np
import tkinter as tk
from tkinter import ttk

import symbols as sym
from minispice import Circuit, DiodeModel, VT
from charts import MplChartFrame, PLOT_BG
from widgets import ScrollableFrame, FONT_BODY, is_shown
from uikit import Segmented, ParamForm, TileRow, section, note, eng, nice
from i18n import t, register, tr

ON = "#2e9d44"
OFF = "#9aa3b2"
C_IN = "#c9622a"
C_OUT = "#2A9D8F"
C_AUX = "#6A4C93"
C_I = "#277DA1"

register({
    "dl.lab": ("Circuit Lab", "Laborator circuite"),
    "dl.iv": ("I-V Explorer", "Explorator I-U"),
    "dl.zener": ("Zener Regulator", "Stabilizator Zener"),
    "dl.led": ("LED Array", "Matrice LED"),
    "dl.pick": ("Pick a circuit", "Alege un circuit"),
    "dl.c.half": ("Rectifier", "Redresor"),
    "dl.c.clip": ("Clipper", "Limitator"),
    "dl.c.zclip": ("Zener clipper", "Limitator Zener"),
    "dl.c.clamp": ("Clamper", "Circuit de fixare"),
    "dl.c.doubler": ("Voltage doubler", "Dublor de tensiune"),
    "dl.c.env": ("Envelope detector", "Detector de anvelopă"),
    "dl.c.fw": ("Freewheel diode", "Diodă de descărcare"),
    "dl.source": ("Input signal", "Semnal de intrare"),
    "dl.w.sine": ("Sine", "Sinus"),
    "dl.w.square": ("Square", "Dreptunghi"),
    "dl.w.tri": ("Triangle", "Triunghi"),
    "dl.amp": ("Amplitude (peak)", "Amplitudine (vârf)"),
    "dl.freq": ("Frequency", "Frecvență"),
    "dl.parts": ("Components", "Componente"),
    "dl.dtype": ("Diode type", "Tip diodă"),
    "dl.d.si": ("Silicon (1N4148)", "Siliciu (1N4148)"),
    "dl.d.sch": ("Schottky", "Schottky"),
    "dl.d.ge": ("Germanium", "Germaniu"),
    "dl.rl": ("Load RL", "Sarcina RL"),
    "dl.c": ("Capacitor C (0 = none)", "Condensator C (0 = fără)"),
    "dl.r": ("Series R", "R serie"),
    "dl.vref": ("Bias Vref", "Polarizare Vref"),
    "dl.vz": ("Zener voltage Vz", "Tensiune Zener Vz"),
    "dl.side": ("Clips / clamps", "Limitează / fixează"),
    "dl.side.pos": ("positive", "pozitiv"),
    "dl.side.neg": ("negative", "negativ"),
    "dl.side.both": ("both", "ambele"),
    "dl.cc": ("Capacitors C1 = C2", "Condensatoare C1 = C2"),
    "dl.fc": ("Carrier frequency", "Frecvența purtătoarei"),
    "dl.fm": ("Message frequency", "Frecvența mesajului"),
    "dl.m": ("Modulation index m", "Indice de modulație m"),
    "dl.vdc": ("Supply voltage", "Tensiune alimentare"),
    "dl.l": ("Coil inductance L", "Inductanța bobinei L"),
    "dl.rcoil": ("Coil resistance R", "Rezistența bobinei R"),
    "dl.fsw": ("Switching frequency", "Frecvența de comutare"),
    "dl.with_d": ("Fit the freewheeling diode", "Montează dioda de descărcare"),
    "dl.cursor": ("Time cursor (drag) — the conducting diode turns green",
                  "Cursor de timp (trage) — dioda care conduce devine verde"),
    "dl.play": ("▶ Play", "▶ Redă"),
    "dl.pause": ("❚❚ Pause", "❚❚ Pauză"),
    "dl.t.vmax": ("Vout max", "Vout max"),
    "dl.t.vmin": ("Vout min", "Vout min"),
    "dl.t.vavg": ("Vout average (DC)", "Vout medie (DC)"),
    "dl.t.ripple": ("Ripple (p-p, last cycle)", "Riplu (v-v, ultima perioadă)"),
    "dl.t.ipk": ("Peak diode current", "Curent de vârf diodă"),
    "dl.t.piv": ("Peak inverse voltage", "Tensiune inversă maximă"),
    "dl.t.vsw": ("Peak switch voltage", "Tensiune maximă pe comutator"),
    "dl.t.il": ("Coil current (avg)", "Curent bobină (mediu)"),
    "dl.ax.v": ("Voltage (V)", "Tensiune (V)"),
    "dl.ax.i": ("Diode current (mA)", "Curent diodă (mA)"),
    "dl.ax.t": ("Time (ms)", "Timp (ms)"),
    "dl.vin": ("Vin", "Vin"),
    "dl.vout": ("Vout", "Vout"),
    "dl.vsw": ("V switch", "V comutator"),
    "dl.ilcoil": ("i coil", "i bobină"),
    "dl.x.half": ("The diode only lets current flow while the anode is ~0.7 V above the cathode, so only the "
                  "positive half-cycles reach the load. Add a capacitor and it charges to the peak and feeds the "
                  "load between peaks: ripple ≈ I_load / (f·C). PIV (the reverse voltage the diode must survive) "
                  "reaches ≈ 2·Vpeak with the capacitor fitted.",
                  "Dioda lasă curentul să treacă doar cât anodul e cu ~0,7 V peste catod, deci doar semiperioadele "
                  "pozitive ajung la sarcină. Adaugă un condensator: se încarcă la valoarea de vârf și alimentează "
                  "sarcina între vârfuri: riplu ≈ I_sarcină / (f·C). Tensiunea inversă pe diodă (PIV) ajunge la "
                  "≈ 2·Vvârf cu condensatorul montat."),
    "dl.x.clip": ("A shunt diode to a bias voltage conducts as soon as the output tries to go beyond Vref + Vf, "
                  "so everything above that level is sliced off and dropped across R. Used for input protection "
                  "and wave-shaping. Negative clipping uses a reversed diode; 'both' gives a limiter.",
                  "O diodă în paralel spre o tensiune de polarizare conduce imediat ce ieșirea încearcă să treacă "
                  "de Vref + Vf, deci tot ce e peste acest nivel e tăiat și cade pe R. Folosit pentru protecția "
                  "intrărilor și formarea semnalelor. Limitarea negativă folosește o diodă inversată; 'ambele' "
                  "dă un limitator."),
    "dl.x.zclip": ("Two zeners back to back: in each direction one breaks down (Vz) and the other conducts "
                   "forward (≈0.7 V), so the output is limited to about ±(Vz + 0.7 V). A simple way to make a "
                   "trapezoid/square from a big sine, or to protect an input.",
                   "Două diode Zener în opoziție: în fiecare sens una intră în străpungere (Vz), iar cealaltă "
                   "conduce direct (≈0,7 V), deci ieșirea e limitată la aproximativ ±(Vz + 0,7 V). Un mod simplu "
                   "de a obține un trapez/dreptunghi dintr-un sinus mare sau de a proteja o intrare."),
    "dl.x.clamp": ("The capacitor charges through the diode on one peak and then keeps that charge, so the "
                   "whole waveform is shifted: its shape is unchanged but it now sits above (or below) 0 V. "
                   "Needs RL·C ≫ one period, otherwise the capacitor discharges between peaks.",
                   "Condensatorul se încarcă prin diodă la un vârf și apoi își păstrează sarcina, deci toată forma "
                   "de undă e deplasată: forma nu se schimbă, dar acum stă deasupra (sau dedesubtul) lui 0 V. "
                   "Necesită RL·C ≫ o perioadă, altfel condensatorul se descarcă între vârfuri."),
    "dl.x.doubler": ("A clamper (C1 + D1) followed by a peak detector (D2 + C2): C1 shifts the input up to "
                     "0 … 2·Vpeak and C2 holds the top, so Vout ≈ 2·Vpeak − 2·Vf with no transformer. Cascading "
                     "more stages gives a Cockcroft-Walton multiplier.",
                     "Un circuit de fixare (C1 + D1) urmat de un detector de vârf (D2 + C2): C1 ridică intrarea la "
                     "0 … 2·Vvârf, iar C2 păstrează vârful, deci Vout ≈ 2·Vvârf − 2·Vf fără transformator. "
                     "Mai multe etaje în cascadă dau un multiplicator Cockcroft-Walton."),
    "dl.x.env": ("An AM radio's detector: the diode charges C to each carrier peak and R discharges it slowly, "
                 "so the output follows the envelope (the audio). Choose 1/fc ≪ RC ≪ 1/fm. Too small RC → "
                 "carrier ripple; too large → 'diagonal clipping' (the output can't fall fast enough).",
                 "Detectorul unui radio AM: dioda încarcă C la fiecare vârf al purtătoarei, iar R îl descarcă "
                 "încet, deci ieșirea urmărește anvelopa (semnalul audio). Alege 1/fc ≪ RC ≪ 1/fm. RC prea mic "
                 "→ riplu de purtătoare; prea mare → 'limitare diagonală' (ieșirea nu poate coborî destul de repede)."),
    "dl.x.fw": ("When a switch turns off an inductive load (relay, motor, solenoid), the coil keeps its current "
                "flowing (v = L·di/dt) and the voltage on the switch flies up until something breaks down. The "
                "freewheeling diode gives the current a path round the coil, so the switch only sees Vsupply + "
                "0.7 V. Untick it to see the spike (clamped here by the transistor's ~80 V avalanche).",
                "Când un comutator întrerupe o sarcină inductivă (releu, motor, electromagnet), bobina își "
                "menține curentul (v = L·di/dt) și tensiunea pe comutator crește până se străpunge ceva. Dioda de "
                "descărcare oferă curentului o cale în jurul bobinei, deci comutatorul vede doar Valim + 0,7 V. "
                "Debifeaz-o ca să vezi vârful (limitat aici de străpungerea tranzistorului la ~80 V)."),
    # I-V explorer
    "iv.show": ("Diodes to compare", "Diode de comparat"),
    "iv.temp": ("Temperature (°C)", "Temperatură (°C)"),
    "iv.scale": ("Current axis", "Axa curentului"),
    "iv.lin": ("linear", "liniară"),
    "iv.log": ("logarithmic", "logaritmică"),
    "iv.rev": ("Show reverse region", "Arată regiunea inversă"),
    "iv.ll": ("Load line (Vs — R — diode)", "Dreapta de sarcină (Vs — R — diodă)"),
    "iv.lldiode": ("Diode on the load line", "Dioda pe dreapta de sarcină"),
    "iv.vs": ("Source Vs", "Sursă Vs"),
    "iv.r": ("Resistor R", "Rezistor R"),
    "iv.q_vd": ("Q-point VD", "Punct Q VD"),
    "iv.q_id": ("Q-point ID", "Punct Q ID"),
    "iv.q_p": ("Diode power", "Putere diodă"),
    "iv.q_rd": ("Dynamic resistance rd", "Rezistență dinamică rd"),
    "iv.xlab": ("Diode voltage VD (V)", "Tensiune diodă VD (V)"),
    "iv.ylab": ("Current ID (mA)", "Curent ID (mA)"),
    "iv.explain": ("Each curve is the Shockley equation I = Is·(e^(V/nVT) − 1). Knee voltage depends on the "
                   "material (Ge < Schottky < Si < LEDs by colour). Heating a diode lowers Vf by about 2 mV/°C. "
                   "On the log scale the forward region is a straight line — its slope is set by n. The load line "
                   "I = (Vs − V)/R meets the curve at the operating (Q) point.",
                   "Fiecare curbă e ecuația Shockley I = Is·(e^(V/nVT) − 1). Tensiunea de prag depinde de material "
                   "(Ge < Schottky < Si < LED-uri după culoare). Încălzirea unei diode scade Vf cu aprox. 2 mV/°C. "
                   "Pe scara logaritmică regiunea directă e o dreaptă — panta e dată de n. Dreapta de sarcină "
                   "I = (Vs − V)/R intersectează curba în punctul de funcționare (Q)."),
    # zener designer
    "zd.intro": ("Shunt regulator: R drops the extra voltage and the zener takes whatever current the load does "
                 "not need, keeping Vout ≈ Vz. The resistor must pass enough current at the WORST case (lowest Vin, "
                 "highest load) and must not overload the zener at the other extreme (highest Vin, lightest load).",
                 "Stabilizator paralel: R preia tensiunea în plus, iar dioda Zener preia curentul de care sarcina nu "
                 "are nevoie, menținând Vout ≈ Vz. Rezistorul trebuie să dea destul curent în cazul cel mai "
                 "defavorabil (Vin minim, sarcină maximă) și să nu suprasolicite dioda în celălalt extrem "
                 "(Vin maxim, sarcină minimă)."),
    "zd.vinmin": ("Vin minimum", "Vin minim"),
    "zd.vinmax": ("Vin maximum", "Vin maxim"),
    "zd.vz": ("Zener voltage Vz", "Tensiune Zener Vz"),
    "zd.pz": ("Zener power rating", "Putere nominală Zener"),
    "zd.rz": ("Zener dynamic resistance rz", "Rezistența dinamică rz"),
    "zd.izmin": ("Minimum zener current", "Curent Zener minim"),
    "zd.ilmin": ("Load current minimum", "Curent sarcină minim"),
    "zd.ilmax": ("Load current maximum", "Curent sarcină maxim"),
    "zd.ruse": ("Use R (blank = suggested)", "Folosește R (gol = sugerat)"),
    "zd.t.range": ("Allowed R range", "Domeniu permis pentru R"),
    "zd.t.r": ("Chosen R (E24)", "R ales (E24)"),
    "zd.t.pr": ("R dissipation (max)", "Disipare R (max)"),
    "zd.t.pz": ("Zener dissipation (max)", "Disipare Zener (max)"),
    "zd.t.line": ("Line regulation", "Stabilizare la rețea"),
    "zd.t.load": ("Load regulation", "Stabilizare la sarcină"),
    "zd.t.eff": ("Efficiency (full load)", "Randament (sarcină maximă)"),
    "zd.t.izr": ("Zener current range", "Domeniu curent Zener"),
    "zd.bad": ("Impossible with these numbers: even the largest allowed R cannot keep the zener in "
               "regulation at minimum Vin/maximum load without overloading it at maximum Vin/minimum load. "
               "Use a higher-power zener, narrower Vin range, or a transistor/linear regulator.",
               "Imposibil cu aceste valori: nici cel mai mare R permis nu menține dioda în stabilizare la Vin minim/"
               "sarcină maximă fără să o suprasolicite la Vin maxim/sarcină minimă. Folosește o diodă de putere mai "
               "mare, un domeniu Vin mai îngust sau un tranzistor/regulator liniar."),
    "zd.p1": ("Vout vs Vin", "Vout în funcție de Vin"),
    "zd.p2": ("Vout vs load current", "Vout în funcție de curentul de sarcină"),
    "zd.p3": ("Zener current vs Vin", "Curent Zener în funcție de Vin"),
    "zd.dropout": ("drops out of regulation", "iese din stabilizare"),
    # LED array
    "la.intro": ("Plan an LED array from one supply: LEDs in series share one current (efficient, but their Vf "
                 "adds up), strings in parallel each need their own resistor. More LEDs per string = less power "
                 "wasted in the resistor, but less headroom, so the current becomes sensitive to Vf spread.",
                 "Planifică o matrice de LED-uri dintr-o singură sursă: LED-urile în serie au același curent "
                 "(eficient, dar tensiunile Vf se adună), șirurile în paralel au nevoie fiecare de propriul rezistor. "
                 "Mai multe LED-uri pe șir = mai puțină putere pierdută în rezistor, dar rezervă de tensiune mai "
                 "mică, deci curentul devine sensibil la variația Vf."),
    "la.vs": ("Supply voltage", "Tensiune de alimentare"),
    "la.color": ("LED colour", "Culoarea LED-ului"),
    "la.vf": ("Forward voltage Vf", "Tensiune directă Vf"),
    "la.if": ("LED current", "Curent LED"),
    "la.n": ("Number of LEDs", "Număr de LED-uri"),
    "la.per": ("LEDs per string", "LED-uri pe șir"),
    "la.auto": ("auto (best)", "automat (optim)"),
    "la.t.arr": ("Arrangement", "Aranjament"),
    "la.t.r": ("Resistor per string (E24)", "Rezistor pe șir (E24)"),
    "la.t.i": ("Actual LED current", "Curent LED real"),
    "la.t.itot": ("Total supply current", "Curent total din sursă"),
    "la.t.pr": ("Power per resistor", "Putere pe rezistor"),
    "la.t.eff": ("Efficiency (LED / total)", "Randament (LED / total)"),
    "la.t.spread": ("Current if Vf ±0.1 V", "Curent dacă Vf ±0,1 V"),
    "la.t.ptot": ("Total power", "Putere totală"),
    "la.table": ("All options", "Toate variantele"),
    "la.col.per": ("per string", "pe șir"),
    "la.col.str": ("strings", "șiruri"),
    "la.col.r": ("R", "R"),
    "la.col.eff": ("efficiency", "randament"),
    "la.col.sens": ("ΔI for ΔVf=0.1V", "ΔI pt. ΔVf=0,1V"),
    "la.extra": ("The last string has only {k} LED(s): give it its own resistor ≈ {r}.",
                 "Ultimul șir are doar {k} LED(-uri): pune-i propriul rezistor ≈ {r}."),
    "la.toolow": ("Supply too low for even one LED with a resistor.",
                  "Tensiunea e prea mică chiar și pentru un singur LED cu rezistor."),
    "la.c.red": ("Red", "Roșu"), "la.c.orange": ("Orange", "Portocaliu"), "la.c.yellow": ("Yellow", "Galben"),
    "la.c.green": ("Green", "Verde"), "la.c.blue": ("Blue", "Albastru"), "la.c.white": ("White", "Alb"),
    "la.c.ir": ("Infrared", "Infraroșu"), "la.c.uv": ("UV (400 nm)", "UV (400 nm)"),
})

E24 = [1.0, 1.1, 1.2, 1.3, 1.5, 1.6, 1.8, 2.0, 2.2, 2.4, 2.7, 3.0, 3.3, 3.6, 3.9, 4.3, 4.7, 5.1, 5.6, 6.2,
       6.8, 7.5, 8.2, 9.1]


def e24_list(lo, hi):
    out = []
    d = 10 ** math.floor(math.log10(max(lo, 1e-3)))
    while d <= hi * 10:
        for m in E24:
            v = m * d
            if lo <= v <= hi:
                out.append(v)
        d *= 10
    return out


def e24_up(v):
    """Smallest E24 value >= v."""
    d = 10 ** math.floor(math.log10(v))
    for dd in (d, d * 10):
        for m in E24:
            if m * dd >= v * 0.9999:
                return m * dd
    return v


def _wave(kind, A, f):
    w = 2 * math.pi * f
    if kind == "square":
        return lambda tt: A if math.sin(w * tt) >= 0 else -A
    if kind == "tri":
        return lambda tt: A * 2 / math.pi * math.asin(math.sin(w * tt))
    return lambda tt: A * math.sin(w * tt)


def _dmodel(key):
    return {"si": DiodeModel.silicon(), "sch": DiodeModel.schottky(), "ge": DiodeModel.germanium()}[key]


# ===========================================================================
# Circuit lab
# ===========================================================================
CIRCUITS = ["half", "clip", "zclip", "clamp", "doubler", "env", "fw"]

PARAMS = {
    "half": [("rl", "dl.rl", "1k", "Ω", (10, 100e3, True)), ("c", "dl.c", "0", "F", None)],
    "clip": [("r", "dl.r", "1k", "Ω", (10, 100e3, True)), ("vref", "dl.vref", "2", "V", (0, 10))],
    "zclip": [("r", "dl.r", "1k", "Ω", (10, 100e3, True)), ("vz", "dl.vz", "5.1", "V", (2.4, 15))],
    "clamp": [("c", "dl.c", "10u", "F", None), ("rl", "dl.rl", "100k", "Ω", (100, 1e6, True)),
              ("vref", "dl.vref", "0", "V", (0, 10))],
    "doubler": [("c", "dl.cc", "10u", "F", None), ("rl", "dl.rl", "100k", "Ω", (100, 1e6, True))],
    "env": [("fc", "dl.fc", "10k", "Hz", (1e3, 100e3, True)), ("fm", "dl.fm", "500", "Hz", (50, 5e3, True)),
            ("m", "dl.m", "0.6", "", (0, 1)), ("r", "dl.rl", "10k", "Ω", (100, 1e6, True)),
            ("c", "dl.c", "22n", "F", None)],
    "fw": [("vdc", "dl.vdc", "12", "V", (1, 48)), ("l", "dl.l", "10m", "H", None),
           ("rcoil", "dl.rcoil", "24", "Ω", (1, 1000, True)), ("fsw", "dl.fsw", "200", "Hz", (10, 5e3, True))],
}


class DiodeLabPanel(ttk.Frame):
    def __init__(self, parent, accent):
        super().__init__(parent, style="Card.TFrame")
        self.accent = accent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body
        self.body = body

        section(body, t("dl.pick"), accent)
        self.circuit = tk.StringVar(value="half")
        Segmented(body, [(k, t("dl.c." + k)) for k in CIRCUITS], self.circuit, self._on_circuit,
                  accent=accent, wrap=4).pack(anchor="w", padx=16)

        top = ttk.Frame(body, style="Card.TFrame")
        top.pack(fill="both", expand=True, padx=16, pady=(8, 12))
        top.columnconfigure(1, weight=1)
        left = ttk.Frame(top, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nw")
        right = ttk.Frame(top, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(16, 0))

        self.src_box = ttk.Frame(left, style="Card.TFrame")
        self.src_box.pack(fill="x")
        ttk.Label(self.src_box, text=t("dl.source"), font=("Segoe UI", 10, "bold"),
                  style="CardSub.TLabel").pack(anchor="w")
        self.wave = tk.StringVar(value="sine")
        Segmented(self.src_box, [("sine", t("dl.w.sine")), ("square", t("dl.w.square")), ("tri", t("dl.w.tri"))],
                  self.wave, lambda k: self.simulate(), accent=accent).pack(anchor="w", pady=(2, 4))
        self.src_form = ParamForm(self.src_box, [
            dict(key="amp", label=t("dl.amp"), default="10", unit="V", slider=(0.5, 50)),
            dict(key="f", label=t("dl.freq"), default="50", unit="Hz", slider=(5, 20e3, True)),
        ], self.simulate, label_width=18)
        self.src_form.pack(anchor="w")

        ttk.Label(left, text=t("dl.parts"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel")\
            .pack(anchor="w", pady=(8, 0))
        self.form_holder = ttk.Frame(left, style="Card.TFrame")
        self.form_holder.pack(anchor="w", fill="x")
        self.opt_holder = ttk.Frame(left, style="Card.TFrame")
        self.opt_holder.pack(anchor="w", fill="x", pady=(4, 0))
        drow = ttk.Frame(left, style="Card.TFrame")
        drow.pack(anchor="w", pady=(6, 0))
        ttk.Label(drow, text=t("dl.dtype"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self.dtype_names = {"si": t("dl.d.si"), "sch": t("dl.d.sch"), "ge": t("dl.d.ge")}
        self.dtype = tk.StringVar(value=self.dtype_names["si"])
        cb = ttk.Combobox(drow, textvariable=self.dtype, values=list(self.dtype_names.values()),
                          state="readonly", width=16)
        cb.pack(side="left", padx=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self.simulate())
        self.tiles = TileRow(left, [("vmax", t("dl.t.vmax")), ("vmin", t("dl.t.vmin")), ("vavg", t("dl.t.vavg")),
                                    ("rip", t("dl.t.ripple")), ("ipk", t("dl.t.ipk")), ("piv", t("dl.t.piv"))],
                             accent, per_row=2)
        self.tiles.pack(fill="x", pady=(10, 0))
        self.explain = note(left, "", wrap=440, padx=0, pady=(8, 4))

        self.canvas = tk.Canvas(right, width=470, height=250, bg=sym.CANVAS_BG, highlightthickness=0)
        self.canvas.pack(anchor="n")
        self.chart = MplChartFrame(right, figsize=(6.8, 3.6), with_toolbar=False)
        self.chart.pack(fill="both", expand=True, pady=(6, 0))
        crow = ttk.Frame(right, style="Card.TFrame")
        crow.pack(fill="x", pady=(2, 0))
        self.play_btn = ttk.Button(crow, text=t("dl.play"), style="Small.TButton", command=self._toggle_play)
        self.play_btn.pack(side="left")
        self.cursor = ttk.Scale(crow, from_=0, to=1000, orient="horizontal", command=self._on_cursor)
        self.cursor.pack(side="left", fill="x", expand=True, padx=8)
        ttk.Label(right, text=t("dl.cursor"), font=("Segoe UI", 8), style="CardBody.TLabel").pack(anchor="w")
        self._playing = False
        self.res = None
        self._on_circuit("half")

    # ------------------------------------------------------------------
    def _on_circuit(self, key):
        for w in self.form_holder.winfo_children():
            w.destroy()
        for w in self.opt_holder.winfo_children():
            w.destroy()
        fields = [dict(key=k, label=t(lab), default=d, unit=u, slider=sl) for k, lab, d, u, sl in PARAMS[key]]
        self.form = ParamForm(self.form_holder, fields, self.simulate, label_width=18)
        self.form.pack(anchor="w")
        self.side = tk.StringVar(value="pos")
        self.with_d = tk.BooleanVar(value=True)
        if key in ("clip", "clamp"):
            opts = [("pos", t("dl.side.pos")), ("neg", t("dl.side.neg"))]
            if key == "clip":
                opts.append(("both", t("dl.side.both")))
            r = ttk.Frame(self.opt_holder, style="Card.TFrame")
            r.pack(anchor="w")
            ttk.Label(r, text=t("dl.side"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left", padx=(0, 6))
            Segmented(r, opts, self.side, lambda k: self.simulate(), accent=self.accent).pack(side="left")
        if key == "fw":
            ttk.Checkbutton(self.opt_holder, text=t("dl.with_d"), variable=self.with_d,
                            command=self.simulate).pack(anchor="w")
        # the envelope detector and freewheel circuits bring their own source
        if key in ("env", "fw"):
            self.src_box.pack_forget()
        else:
            if not self.src_box.winfo_ismapped():
                self.src_box.pack(fill="x", before=self.src_box.master.winfo_children()[1])
        if key == "half":
            self.form.set("c", "0")
        self.explain.configure(text=t("dl.x." + key))
        self.simulate()

    def _dkey(self):
        for k, v in self.dtype_names.items():
            if v == self.dtype.get():
                return k
        return "si"

    # ------------------------------------------------------------------
    def simulate(self, *_):
        key = self.circuit.get()
        try:
            P = self.form.values()
            S = self.src_form.values()
        except Exception:
            return
        dm = _dmodel(self._dkey())
        c = Circuit()
        A, f = S["amp"], max(S["f"], 1e-3)
        src = _wave(self.wave.get(), A, f)
        cycles = 3
        steps = 1500
        diodes = []
        plot = [("in", t("dl.vin"), C_IN), ("out", t("dl.vout"), C_OUT)]
        if key == "half":
            c.V("Vs", "in", "0", src)
            c.D("D1", "in", "out", dm)
            c.R("RL", "out", "0", P["rl"])
            if P["c"] > 0:
                c.C("C1", "out", "0", P["c"])
                cycles = 6
            diodes = ["D1"]
        elif key == "clip":
            c.V("Vs", "in", "0", src)
            c.R("R1", "in", "out", P["r"])
            c.R("Rp", "out", "0", 1e7)
            side = self.side.get()
            if side in ("pos", "both"):
                c.V("Vr1", "b1", "0", lambda tt, v=P["vref"]: v)
                c.D("D1", "out", "b1", dm)
                diodes.append("D1")
            if side in ("neg", "both"):
                c.V("Vr2", "b2", "0", lambda tt, v=P["vref"]: -v)
                c.D("D2", "b2", "out", dm)
                diodes.append("D2")
        elif key == "zclip":
            c.V("Vs", "in", "0", src)
            c.R("R1", "in", "out", P["r"])
            c.R("Rp", "out", "0", 1e7)
            zm = DiodeModel.zener(P["vz"])
            c.D("Z1", "m", "out", zm)
            c.D("Z2", "m", "0", zm)
            diodes = ["Z1", "Z2"]
        elif key == "clamp":
            c.V("Vs", "in", "0", src)
            c.C("C1", "in", "out", P["c"])
            c.R("RL", "out", "0", P["rl"])
            if self.side.get() == "pos":
                c.V("Vr", "b", "0", lambda tt, v=P["vref"]: v)
                c.D("D1", "b", "out", dm)
            else:
                c.V("Vr", "b", "0", lambda tt, v=P["vref"]: -v)
                c.D("D1", "out", "b", dm)
            diodes = ["D1"]
            cycles = 5
        elif key == "doubler":
            c.V("Vs", "in", "0", src)
            c.C("C1", "in", "x", P["c"])
            c.D("D1", "0", "x", dm)
            c.D("D2", "x", "out", dm)
            c.C("C2", "out", "0", P["c"])
            c.R("RL", "out", "0", P["rl"])
            diodes = ["D1", "D2"]
            plot.insert(1, ("x", "V(C1/D1)", C_AUX))
            cycles = 8
            steps = 2400
        elif key == "env":
            fc, fm, m = P["fc"], P["fm"], P["m"]
            A = 5.0
            wc, wm = 2 * math.pi * fc, 2 * math.pi * fm
            c.V("Vs", "in", "0", lambda tt: A * (1 + m * math.sin(wm * tt)) * math.sin(wc * tt))
            c.D("D1", "in", "out", dm)
            c.C("C1", "out", "0", P["c"])
            c.R("RL", "out", "0", P["r"])
            diodes = ["D1"]
            f = fm
            cycles = 2
            steps = int(min(6000, max(1500, 30 * fc / fm * cycles)))
        elif key == "fw":
            vdc, fsw = P["vdc"], max(P["fsw"], 1)
            per = 1 / fsw
            c.V("Vs", "vcc", "0", lambda tt, v=vdc: v)
            c.R("Rc", "vcc", "a", max(P["rcoil"], 0.01))
            c.L("L1", "a", "sw", P["l"])
            c.SW("S1", "sw", "0", lambda tt: (tt % per) < per / 2)
            c.D("Qav", "0", "sw", DiodeModel.zener(80))     # transistor avalanche clamp
            if self.with_d.get():
                c.D("D1", "sw", "vcc", dm)
                diodes = ["D1"]
            f = fsw
            cycles = 4
            plot = [("vcc", "Vsupply", C_IN), ("sw", t("dl.vsw"), C_OUT)]
        try:
            res = c.tran(cycles / f, steps)
        except Exception:
            return
        self.res = res
        self.key = key
        self.diodes = diodes
        self.plot_nodes = plot
        self._summaries(res, key, diodes, f, cycles, P)
        self._plot(res, key, diodes, plot)
        self._on_cursor(self.cursor.get())

    def _summaries(self, res, key, diodes, f, cycles, P):
        tl = self.tiles
        vout = res.v("out" if key != "fw" else "sw")
        n = len(res.t)
        last = vout[int(n * (cycles - 1) / cycles):]
        tl.tiles["vmax"].cap.configure(text=t("dl.t.vmax") if key != "fw" else t("dl.t.vsw"))
        tl.tiles["vmin"].cap.configure(text=t("dl.t.vmin") if key != "fw" else t("dl.t.il"))
        tl.set("vmax", eng(vout.max(), "V"), warn=(key == "fw" and vout.max() > P.get("vdc", 0) * 2))
        if key == "fw":
            tl.set("vmin", eng(float(np.mean(res.i("L1")[n // 2:])), "A"))
        else:
            tl.set("vmin", eng(vout.min(), "V"))
        tl.set("vavg", eng(float(np.mean(last)), "V"))
        tl.set("rip", eng(float(last.max() - last.min()), "V"))
        if diodes:
            ipk = max(float(np.max(res.i(d))) for d in diodes)
            piv = 0.0
            for d in diodes:
                a, k = self._diode_nodes(key, d)
                vd = res.v(a) - res.v(k)
                piv = max(piv, float(-vd.min()))
            tl.set("ipk", eng(ipk, "A"))
            tl.set("piv", eng(piv, "V"))
        else:
            tl.set("ipk", "–")
            tl.set("piv", "–")

    def _diode_nodes(self, key, d):
        table = {
            ("half", "D1"): ("in", "out"), ("clip", "D1"): ("out", "b1"), ("clip", "D2"): ("b2", "out"),
            ("zclip", "Z1"): ("m", "out"), ("zclip", "Z2"): ("m", "0"),
            ("doubler", "D1"): ("0", "x"), ("doubler", "D2"): ("x", "out"), ("env", "D1"): ("in", "out"),
            ("fw", "D1"): ("sw", "vcc"),
        }
        if key == "clamp":
            return ("b", "out") if self.side.get() == "pos" else ("out", "b")
        return table[(key, d)]

    def _plot(self, res, key, diodes, plot):
        fig = self.chart.fig
        fig.clear()
        ax1 = fig.add_subplot(211)
        ax2 = fig.add_subplot(212, sharex=ax1)
        tm = res.t * 1e3
        for node, lab, col in plot:
            ax1.plot(tm, res.v(node), color=col, lw=1.8 if node in ("out", "sw") else 1.3, label=lab)
        if key == "env":
            P = self.form.values()
            env = 5.0 * (1 + P["m"] * np.sin(2 * math.pi * P["fm"] * res.t))
            ax1.plot(tm, env, color="#888", lw=1, ls="--", label=tr("envelope", "anvelopă"))
        ax1.set_ylabel(t("dl.ax.v"))
        ax1.tick_params(labelbottom=False)
        ax1.grid(True, alpha=0.25)
        ax1.legend(loc="upper right", fontsize=8, ncol=len(plot) + 1)
        ax1.set_facecolor(PLOT_BG)
        cols = [C_I, "#d62828", C_AUX]
        for i, d in enumerate(diodes):
            ax2.plot(tm, res.i(d) * 1e3, color=cols[i % 3], lw=1.4, label=d)
        if key == "fw":
            ax2.plot(tm, res.i("L1") * 1e3, color="#555", lw=1.2, ls="--", label=t("dl.ilcoil"))
        ax2.set_ylabel(t("dl.ax.i"))
        ax2.set_xlabel(t("dl.ax.t"))
        ax2.grid(True, alpha=0.25)
        if diodes or key == "fw":
            ax2.legend(loc="upper right", fontsize=8)
        ax2.set_facecolor(PLOT_BG)
        self._cur_lines = [ax1.axvline(0, color="#1f2a44", lw=1, alpha=0.6),
                           ax2.axvline(0, color="#1f2a44", lw=1, alpha=0.6)]
        fig.subplots_adjust(left=0.08, right=0.98, top=0.96, bottom=0.12, hspace=0.12)
        self.chart.redraw()

    # ------------------------------------------------------------------
    def _on_cursor(self, pos):
        if self.res is None:
            return
        n = len(self.res.t)
        idx = int(float(pos) / 1000 * (n - 1))
        idx = max(0, min(n - 1, idx))
        self._idx = idx
        tm = self.res.t[idx] * 1e3
        for ln in getattr(self, "_cur_lines", []):
            ln.set_xdata([tm, tm])
        self.chart.redraw()
        state = {}
        for d in self.diodes:
            i = self.res.i(d)
            thr = max(1e-4, 0.02 * float(np.max(np.abs(i))))
            state[d] = abs(float(i[idx])) > thr
        vals = {node: float(self.res.v(node)[idx]) for node in self.res._nodes}
        self._draw(self.key, state, vals)

    def _toggle_play(self):
        self._playing = not self._playing
        self.play_btn.configure(text=t("dl.pause") if self._playing else t("dl.play"))
        if self._playing:
            self._tick()

    def _tick(self):
        if not self._playing:
            return
        try:
            if not is_shown(self):
                self._playing = False
                self.play_btn.configure(text=t("dl.play"))
                return
        except tk.TclError:
            return
        p = (float(self.cursor.get()) + 6) % 1000
        self.cursor.set(p)
        self.after(90, self._tick)

    # ------------------------------------------------------------------
    def _draw(self, key, st, v):
        cv = self.canvas
        cv.delete("all")
        top, bot = 60, 205
        s = 1.0

        def dcol(name):
            return ON if st.get(name) else sym.SYM_COLOR

        def dfill(name):
            return ON if st.get(name) else ""

        def src_left(label="Vin"):
            sym.ac_source(cv, 45, (top + bot) / 2)
            sym.wire(cv, 45, (top + bot) / 2 - 16, 45, top)
            sym.wire(cv, 45, (top + bot) / 2 + 16, 45, bot)
            cv.create_text(52, (top + bot) / 2 - 34, text=f"{label}\n{v.get('in', 0):+.2f} V",
                           font=("Segoe UI", 8), fill=C_IN, anchor="w")

        def out_term(x, node="out"):
            sym.terminal(cv, x, top, label="Vout")
            cv.create_text(x, top + 16, text=f"{v.get(node, 0):+.2f} V", font=("Consolas", 9, "bold"), fill=C_OUT)

        def rail(x1, x2):
            sym.wire(cv, x1, bot, x2, bot)
            sym.ground(cv, (x1 + x2) / 2, bot + 4)

        if key == "half":
            src_left()
            sym.wire(cv, 45, top, 110, top)
            sym.diode(cv, 110, top, 200, top, label="D1", color=dcol("D1"), fill=dfill("D1"))
            sym.wire(cv, 200, top, 400, top)
            sym.resistor(cv, 280, top, 280, bot, label="RL", label_side=1)
            sym.node(cv, 280, top)
            try:
                hasc = self.form.get("c") > 0
            except Exception:
                hasc = False
            if hasc:
                sym.capacitor(cv, 350, top, 350, bot, label="C", label_side=1)
                sym.node(cv, 350, top)
            rail(45, 400)
            out_term(400)
        elif key == "clip":
            src_left()
            sym.wire(cv, 45, top, 90, top)
            sym.resistor(cv, 90, top, 190, top, label="R")
            sym.wire(cv, 190, top, 420, top)
            side = self.side.get()
            if side in ("pos", "both"):
                x = 260
                sym.node(cv, x, top)
                sym.diode(cv, x, top, x, top + 70, label="D1", color=dcol("D1"), fill=dfill("D1"), label_side=1)
                sym.cell(cv, x, top + 80, x, bot, label="Vref", label_side=1)
                sym.wire(cv, x, top + 70, x, top + 80)
            if side in ("neg", "both"):
                x = 340
                sym.node(cv, x, top)
                sym.diode(cv, x, top + 70, x, top, label="D2", color=dcol("D2"), fill=dfill("D2"), label_side=1)
                sym.cell(cv, x, bot, x, top + 80, label="Vref", label_side=1)
                sym.wire(cv, x, top + 70, x, top + 80)
            rail(45, 420)
            out_term(420)
        elif key == "zclip":
            src_left()
            sym.wire(cv, 45, top, 90, top)
            sym.resistor(cv, 90, top, 190, top, label="R")
            sym.wire(cv, 190, top, 400, top)
            x = 290
            mid = (top + bot) / 2
            sym.node(cv, x, top)
            sym.diode(cv, x, mid, x, top, label="Z1", color=dcol("Z1"), fill=dfill("Z1"), variant="zener",
                      label_side=1)
            sym.diode(cv, x, mid, x, bot, label="Z2", color=dcol("Z2"), fill=dfill("Z2"), variant="zener",
                      label_side=1)
            rail(45, 400)
            out_term(400)
        elif key == "clamp":
            src_left()
            sym.wire(cv, 45, top, 90, top)
            sym.capacitor(cv, 90, top, 190, top, label="C")
            sym.wire(cv, 190, top, 420, top)
            x = 260
            sym.node(cv, x, top)
            if self.side.get() == "pos":
                sym.diode(cv, x, top + 75, x, top, label="D1", color=dcol("D1"), fill=dfill("D1"), label_side=1)
                sym.cell(cv, x, top + 85, x, bot, label="Vref", label_side=1)
            else:
                sym.diode(cv, x, top, x, top + 75, label="D1", color=dcol("D1"), fill=dfill("D1"), label_side=1)
                sym.cell(cv, x, bot, x, top + 85, label="Vref", label_side=1)
            sym.wire(cv, x, top + 75, x, top + 85)
            sym.resistor(cv, 350, top, 350, bot, label="RL", label_side=1)
            sym.node(cv, 350, top)
            rail(45, 420)
            out_term(420)
            cv.create_text(145, top - 32, text=f"Vc = {v.get('in', 0) - v.get('out', 0):+.2f} V",
                           font=("Segoe UI", 8), fill=C_AUX)
        elif key == "doubler":
            src_left()
            sym.wire(cv, 45, top, 80, top)
            sym.capacitor(cv, 80, top, 170, top, label="C1")
            sym.wire(cv, 170, top, 210, top)
            sym.node(cv, 210, top)
            sym.diode(cv, 210, bot, 210, top, label="D1", color=dcol("D1"), fill=dfill("D1"), label_side=1)
            sym.diode(cv, 210, top, 310, top, label="D2", color=dcol("D2"), fill=dfill("D2"))
            sym.wire(cv, 310, top, 430, top)
            sym.capacitor(cv, 320, top, 320, bot, label="C2", label_side=1)
            sym.node(cv, 320, top)
            sym.resistor(cv, 385, top, 385, bot, label="RL", label_side=1)
            sym.node(cv, 385, top)
            rail(45, 430)
            out_term(430)
            cv.create_text(212, top + 20, text=f"{v.get('x', 0):+.1f} V", font=("Segoe UI", 8), fill=C_AUX,
                           anchor="w")
        elif key == "env":
            src_left("AM in")
            sym.wire(cv, 45, top, 110, top)
            sym.diode(cv, 110, top, 200, top, label="D1", color=dcol("D1"), fill=dfill("D1"))
            sym.wire(cv, 200, top, 400, top)
            sym.capacitor(cv, 270, top, 270, bot, label="C", label_side=1)
            sym.node(cv, 270, top)
            sym.resistor(cv, 340, top, 340, bot, label="R", label_side=1)
            sym.node(cv, 340, top)
            rail(45, 400)
            out_term(400)
            try:
                P = self.form.values()
                rc = P["r"] * P["c"]
                cv.create_text(230, bot + 30, text=f"RC = {eng(rc, 's')}   1/fc = {eng(1 / P['fc'], 's')}   "
                                                   f"1/fm = {eng(1 / P['fm'], 's')}",
                               font=("Segoe UI", 8), fill="#555")
            except Exception:
                pass
        elif key == "fw":
            tp, bt = 40, 215
            sym.dc_source(cv, 45, 128, label="")
            sym.wire(cv, 45, 112, 45, tp, 300, tp)
            sym.wire(cv, 45, 144, 45, bt, 300, bt)
            sym.ground(cv, 170, bt + 4)
            sym.resistor(cv, 300, tp, 300, 95, label="R", label_side=1)
            sym.inductor(cv, 300, 95, 300, 150, label="L", label_side=1)
            sym.node(cv, 300, 160)
            sym.wire(cv, 300, 150, 300, 172)
            # switch
            on = bool(v) and self._switch_on()
            sym.node(cv, 300, 172)
            if on:
                sym.wire(cv, 300, 172, 300, bt, color=ON)
            else:
                sym.wire(cv, 300, 172, 318, 196)
                sym.wire(cv, 300, 200, 300, bt)
            cv.create_text(322, 190, text="S (" + ("ON" if on else "OFF") + ")", anchor="w",
                           font=("Segoe UI", 8, "bold"), fill=ON if on else "#c62828")
            if self.with_d.get():
                sym.wire(cv, 300, 160, 380, 160)
                sym.wire(cv, 300, tp, 380, tp)
                sym.node(cv, 300, tp)
                sym.diode(cv, 380, 160, 380, tp, label="D1", color=dcol("D1"), fill=dfill("D1"), label_side=1)
            cv.create_text(20, 85, text=f"{v.get('vcc', 0):.1f} V", font=("Segoe UI", 8), fill=C_IN, anchor="w")
            cv.create_text(250, 172, text=f"{v.get('sw', 0):+.1f} V", font=("Consolas", 9, "bold"), fill=C_OUT,
                           anchor="e")

    def _switch_on(self):
        try:
            per = 1 / max(self.form.get("fsw"), 1)
        except Exception:
            return True
        return (self.res.t[getattr(self, "_idx", 0)] % per) < per / 2


# ===========================================================================
# I-V explorer
# ===========================================================================
IV_TYPES = [
    # key, label key/text, Is(25C), n, colour, Eg(eV), bv
    ("si", "dl.d.si", 2.5e-9, 1.9, "#1f2a44", 1.12, None),
    ("ge", "dl.d.ge", 2e-6, 1.3, "#8a6d00", 0.67, None),
    ("sch", "dl.d.sch", 1e-6, 1.05, "#277DA1", 0.69, None),
    ("red", "la.c.red", None, 2.0, "#d62828", 1.9, None),
    ("green", "la.c.green", None, 2.2, "#2e9d44", 2.3, None),
    ("blue", "la.c.blue", None, 2.6, "#1e63d6", 2.8, None),
    ("white", "la.c.white", None, 2.6, "#9a9a9a", 2.8, None),
    ("z51", "Zener 5.1 V", 2.5e-9, 1.9, "#6A4C93", 1.12, 5.1),
]
LED_VF = {"red": 1.9, "green": 2.9, "blue": 3.0, "white": 3.0}


def _iv_params(key, temp_c):
    """Return (Is, n, bv) at temperature."""
    k, labk, Is, n, col, Eg, bv = next(x for x in IV_TYPES if x[0] == key)
    if Is is None:   # LEDs: set Is so that 20 mA flows at the typical Vf
        Is = 0.02 / math.exp(LED_VF[key] / (n * VT))
    T0, T = 298.15, temp_c + 273.15
    vt_t = VT * T / T0
    Is_t = Is * (T / T0) ** (3 / n) * math.exp(Eg / (n * VT) * (1 - T0 / T))
    if bv is not None:
        bv = bv * (1 + 0.0005 * (temp_c - 25))
    return Is_t, n, bv, vt_t


def _iv_curve(key, temp_c, v):
    Is, n, bv, vt = _iv_params(key, temp_c)
    x = np.clip(v / (n * vt), -50, 60)
    i = Is * (np.exp(x) - 1)
    if bv is not None:
        xb = np.clip((-v - bv) / (1.2 * VT), -60, 60)
        i = i - 1e-3 * np.exp(xb)
    return i


class IVExplorerPanel(ttk.Frame):
    def __init__(self, parent, accent):
        super().__init__(parent, style="Card.TFrame")
        self.accent = accent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body
        note(body, t("iv.explain"), wrap=900, pady=(12, 6))
        top = ttk.Frame(body, style="Card.TFrame")
        top.pack(fill="x", padx=16)
        left = ttk.Frame(top, style="Card.TFrame")
        left.pack(side="left", anchor="n")
        ttk.Label(left, text=t("iv.show"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel").pack(anchor="w")
        self.show = {}
        grid = tk.Frame(left, bg="#FFFFFF")
        grid.pack(anchor="w")
        for i, (k, lab, *_r) in enumerate(IV_TYPES):
            var = tk.BooleanVar(value=k in ("si", "sch", "red", "blue"))
            txt = t(lab) if "." in lab else lab
            col = _r[2]
            cbt = tk.Checkbutton(grid, text=txt, variable=var, command=self.redraw, fg=col, bg="#FFFFFF",
                                 activebackground="#FFFFFF", font=("Segoe UI", 9, "bold"), anchor="w",
                                 selectcolor="#FFFFFF")
            cbt.grid(row=i // 2, column=i % 2, sticky="w")
            self.show[k] = var
        self.form = ParamForm(left, [
            dict(key="temp", label=t("iv.temp"), default="25", unit="°C", slider=(-40, 150)),
        ], self.redraw, label_width=16)
        self.form.pack(anchor="w", pady=(6, 0))
        r = ttk.Frame(left, style="Card.TFrame")
        r.pack(anchor="w", pady=4)
        ttk.Label(r, text=t("iv.scale"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left", padx=(0, 6))
        self.scale = tk.StringVar(value="lin")
        Segmented(r, [("lin", t("iv.lin")), ("log", t("iv.log"))], self.scale, lambda k: self.redraw(),
                  accent=accent).pack(side="left")
        self.rev = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text=t("iv.rev"), variable=self.rev, command=self.redraw).pack(anchor="w")

        ttk.Label(left, text=t("iv.ll"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel")\
            .pack(anchor="w", pady=(10, 0))
        r2 = ttk.Frame(left, style="Card.TFrame")
        r2.pack(anchor="w")
        ttk.Label(r2, text=t("iv.lldiode"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left")
        self.names = {k: (t(lab) if "." in lab else lab) for k, lab, *_r in IV_TYPES}
        self.lld = tk.StringVar(value=self.names["red"])
        cb = ttk.Combobox(r2, textvariable=self.lld, values=list(self.names.values()), state="readonly", width=16)
        cb.pack(side="left", padx=6)
        cb.bind("<<ComboboxSelected>>", lambda e: self.redraw())
        self.ll = ParamForm(left, [
            dict(key="vs", label=t("iv.vs"), default="5", unit="V", slider=(0.5, 12)),
            dict(key="r", label=t("iv.r"), default="150", unit="Ω", slider=(10, 10e3, True)),
        ], self.redraw, label_width=16)
        self.ll.pack(anchor="w")
        self.tiles = TileRow(left, [("vd", t("iv.q_vd")), ("id", t("iv.q_id")), ("p", t("iv.q_p")),
                                    ("rd", t("iv.q_rd"))], accent, per_row=2)
        self.tiles.pack(fill="x", pady=(6, 0))

        self.chart = MplChartFrame(top, figsize=(5.8, 5.0), with_toolbar=True)
        self.chart.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.redraw()

    def _key_of(self, name):
        for k, v in self.names.items():
            if v == name:
                return k
        return "si"

    def redraw(self, *_):
        try:
            temp = self.form.get("temp")
            vs = self.ll.get("vs")
            r = max(self.ll.get("r"), 1e-3)
        except Exception:
            return
        fig = self.chart.fig
        fig.clear()
        ax = fig.add_subplot(111)
        ax.set_facecolor(PLOT_BG)
        logy = self.scale.get() == "log"
        vmin = -7 if self.rev.get() else (0 if logy else -0.2)
        vmax = 3.8
        v = np.linspace(vmin, vmax, 1600)
        for k, lab, *rest in IV_TYPES:
            if not self.show[k].get():
                continue
            i = _iv_curve(k, temp, v)
            col = rest[2]
            if logy:
                ax.semilogy(v, np.abs(i) * 1e3 + 1e-12, color=col, lw=1.8, label=self.names[k])
            else:
                ax.plot(v, i * 1e3, color=col, lw=1.8, label=self.names[k])
        # load line & Q point
        dk = self._key_of(self.lld.get())
        Is, n, bv, vt = _iv_params(dk, temp)
        lo, hi = -bv - 1 if bv else -vs, vs
        f = lambda vd: _iv_curve(dk, temp, np.array([vd]))[0] - (vs - vd) / r
        lo, hi = min(0, vs), max(0, vs)
        if vs < 0:
            lo = vs
        for _ in range(80):
            mid = (lo + hi) / 2
            if f(mid) > 0:
                hi = mid
            else:
                lo = mid
        vq = (lo + hi) / 2
        iq = (vs - vq) / r
        ll_v = np.linspace(min(0, vs), max(0, vs), 50)
        ll_i = (vs - ll_v) / r
        if logy:
            ax.semilogy(ll_v, np.abs(ll_i) * 1e3 + 1e-12, color="#555", ls="--", lw=1.2, label=tr("load line", "dreapta de sarcină"))
            ax.semilogy([vq], [abs(iq) * 1e3 + 1e-12], "o", color="#c62828", ms=8)
            ax.set_ylim(1e-6, 1e3)
        else:
            ax.plot(ll_v, ll_i * 1e3, color="#555", ls="--", lw=1.2, label=tr("load line", "dreapta de sarcină"))
            ax.plot([vq], [iq * 1e3], "o", color="#c62828", ms=8)
            top = max(40.0, min(200.0, abs(vs / r) * 1e3 * 1.3))
            ax.set_ylim(-top * (0.6 if self.rev.get() else 0.08), top)
        ax.annotate(f"Q ({vq:.3f} V, {iq * 1e3:.2f} mA)", (vq, abs(iq) * 1e3 if logy else iq * 1e3),
                    textcoords="offset points", xytext=(8, -14), fontsize=8, color="#c62828")
        ax.set_xlim(vmin, vmax)
        ax.axhline(0, color="#999", lw=0.8)
        ax.axvline(0, color="#999", lw=0.8)
        ax.grid(True, alpha=0.25, which="both")
        ax.set_xlabel(t("iv.xlab"))
        ax.set_ylabel(t("iv.ylab"))
        ax.set_title(f"T = {temp:.0f} °C", fontsize=10)
        ax.legend(fontsize=8, loc="upper left")
        fig.tight_layout()
        self.chart.redraw()
        self.tiles.set("vd", f"{vq:.3f} V")
        self.tiles.set("id", eng(iq, "A"))
        self.tiles.set("p", eng(vq * iq, "W"))
        rd = n * vt / iq if iq > 1e-12 else float("inf")
        self.tiles.set("rd", eng(rd, "Ω") if rd < 1e12 else "∞")


# ===========================================================================
# Zener regulator designer
# ===========================================================================
class ZenerDesignPanel(ttk.Frame):
    def __init__(self, parent, accent):
        super().__init__(parent, style="Card.TFrame")
        self.accent = accent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body
        note(body, t("zd.intro"), wrap=900, pady=(12, 6))
        top = ttk.Frame(body, style="Card.TFrame")
        top.pack(fill="x", padx=16)
        left = ttk.Frame(top, style="Card.TFrame")
        left.pack(side="left", anchor="n")
        self.form = ParamForm(left, [
            dict(key="vinmin", label=t("zd.vinmin"), default="10", unit="V", slider=(1, 40)),
            dict(key="vinmax", label=t("zd.vinmax"), default="14", unit="V", slider=(1, 40)),
            dict(key="vz", label=t("zd.vz"), default="5.1", unit="V", slider=(2.4, 30)),
            dict(key="pz", label=t("zd.pz"), default="0.5", unit="W"),
            dict(key="rz", label=t("zd.rz"), default="10", unit="Ω"),
            dict(key="izmin", label=t("zd.izmin"), default="5m", unit="A"),
            dict(key="ilmin", label=t("zd.ilmin"), default="0", unit="A"),
            dict(key="ilmax", label=t("zd.ilmax"), default="30m", unit="A", slider=(0, 0.2)),
        ], self.update_all, label_width=24)
        self.form.pack(anchor="w")
        r = ttk.Frame(left, style="Card.TFrame")
        r.pack(anchor="w", pady=4)
        ttk.Label(r, text=t("zd.ruse"), font=FONT_BODY, style="CardBody.TLabel", width=24, anchor="w")\
            .pack(side="left")
        self.ruse = tk.StringVar(value="")
        e = ttk.Entry(r, textvariable=self.ruse, width=9)
        e.pack(side="left")
        e.bind("<KeyRelease>", lambda _e: self.update_all())
        self.canvas = tk.Canvas(left, width=380, height=170, bg=sym.CANVAS_BG, highlightthickness=0)
        self.canvas.pack(anchor="w", pady=(8, 0))
        right = ttk.Frame(top, style="Card.TFrame")
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.tiles = TileRow(right, [("range", t("zd.t.range")), ("r", t("zd.t.r")), ("pr", t("zd.t.pr")),
                                     ("pz", t("zd.t.pz")), ("izr", t("zd.t.izr")), ("line", t("zd.t.line")),
                                     ("load", t("zd.t.load")), ("eff", t("zd.t.eff"))], accent, per_row=4)
        self.tiles.pack(fill="x")
        self.warn = note(right, "", wrap=560, color="#c62828")
        self.chart = MplChartFrame(right, figsize=(6.4, 4.4), with_toolbar=False)
        self.chart.pack(fill="both", expand=True)
        self.update_all()

    @staticmethod
    def _vout(vin, il, r, vz, rz, izmin_knee=1e-4):
        """Shunt regulator output (zener = Vz + rz·Iz, only while Iz > 0)."""
        # assume zener conducting
        vo = (vin / r + vz / rz - il) / (1 / r + 1 / rz)
        iz = (vo - vz) / rz
        if iz < 0:            # zener off: plain divider/load
            vo = max(0.0, vin - il * r)
            iz = 0.0
        return vo, iz

    def update_all(self, *_):
        try:
            P = self.form.values()
        except Exception:
            return
        vinmin, vinmax, vz, pz, rz = P["vinmin"], max(P["vinmax"], P["vinmin"]), P["vz"], P["pz"], max(P["rz"], 0.01)
        izmin, ilmin, ilmax = P["izmin"], P["ilmin"], max(P["ilmax"], P["ilmin"])
        izmax = pz / vz
        tl = self.tiles
        self.warn.configure(text="")
        rmax = (vinmin - vz) / (ilmax + izmin) if vinmin > vz else 0
        rmin = (vinmax - vz) / (izmax + ilmin) if izmax + ilmin > 0 else float("inf")
        ok = rmax > 0 and rmin <= rmax
        tl.set("range", f"{eng(rmin, 'Ω')} … {eng(rmax, 'Ω')}", warn=not ok)
        r = None
        if self.ruse.get().strip():
            try:
                from widgets import parse_value
                r = parse_value(self.ruse.get())
            except Exception:
                r = None
        if r is None:
            if ok:
                cands = [x for x in e24_list(rmin, rmax)]
                r = cands[len(cands) // 2] if cands else (rmin + rmax) / 2
            else:
                r = max(rmin, 1.0) if rmax <= 0 else rmax
                self.warn.configure(text=t("zd.bad"))
        tl.set("r", eng(r, "Ω"))
        # worst cases with chosen R
        vo_hi, iz_hi = self._vout(vinmax, ilmin, r, vz, rz)
        vo_lo, iz_lo = self._vout(vinmin, ilmax, r, vz, rz)
        pr = (vinmax - vo_hi) ** 2 / r
        pzw = vo_hi * iz_hi
        tl.set("pr", eng(pr, "W") + f" → {self._rating(pr)}")
        tl.set("pz", eng(pzw, "W"), warn=pzw > pz)
        tl.set("izr", f"{eng(iz_lo, 'A')} … {eng(iz_hi, 'A')}", warn=iz_lo < izmin * 0.999)
        vo_a, _ = self._vout(vinmin, ilmax, r, vz, rz)
        vo_b, _ = self._vout(vinmax, ilmax, r, vz, rz)
        line = (vo_b - vo_a) / (vinmax - vinmin) if vinmax > vinmin else 0
        vnl, _ = self._vout(vinmin, ilmin, r, vz, rz)
        vfl, _ = self._vout(vinmin, ilmax, r, vz, rz)
        load = (vnl - vfl) / vfl * 100 if vfl > 0 else float("nan")
        tl.set("line", eng(line, "V/V") if abs(line) < 1 else "–")
        tl.set("load", f"{load:.2f} %")
        eff = vfl * ilmax / (vinmin * (vinmin - vfl) / r) * 100 if r > 0 and vinmin > vfl else 0
        tl.set("eff", f"{eff:.0f} %")
        self._plot(vinmin, vinmax, vz, rz, r, ilmin, ilmax, izmin, izmax)
        self._draw(r, vz)

    @staticmethod
    def _rating(p):
        for rt in (0.125, 0.25, 0.5, 1, 2, 3, 5, 10):
            if p * 2 <= rt:
                return f"{rt:g} W"
        return "> 10 W"

    def _plot(self, vinmin, vinmax, vz, rz, r, ilmin, ilmax, izmin, izmax):
        fig = self.chart.fig
        fig.clear()
        a1 = fig.add_subplot(221)
        a2 = fig.add_subplot(222)
        a3 = fig.add_subplot(212)
        vin = np.linspace(0, vinmax * 1.25, 200)
        for il, ls, lab in ((ilmin, "-", f"IL = {eng(ilmin, 'A')}"), (ilmax, "--", f"IL = {eng(ilmax, 'A')}")):
            vo = [self._vout(x, il, r, vz, rz)[0] for x in vin]
            iz = [self._vout(x, il, r, vz, rz)[1] * 1e3 for x in vin]
            a1.plot(vin, vo, ls=ls, color=C_OUT, lw=1.6, label=lab)
            a3.plot(vin, iz, ls=ls, color=C_AUX, lw=1.6, label=lab)
        for a in (a1, a3):
            a.axvspan(vinmin, vinmax, color="#2e9d44", alpha=0.08)
        a1.set_title(t("zd.p1"), fontsize=9)
        a1.set_xlabel("Vin (V)", fontsize=8)
        a1.set_ylabel("Vout (V)", fontsize=8)
        a1.legend(fontsize=7)
        ilr = np.linspace(0, max(ilmax * 1.5, 1e-3), 200)
        for vi, ls in ((vinmin, "--"), (vinmax, "-")):
            vo = [self._vout(vi, x, r, vz, rz)[0] for x in ilr]
            a2.plot(ilr * 1e3, vo, ls=ls, color=C_OUT, lw=1.6, label=f"Vin = {vi:g} V")
        a2.axvspan(ilmin * 1e3, ilmax * 1e3, color="#2e9d44", alpha=0.08)
        a2.set_title(t("zd.p2"), fontsize=9)
        a2.set_xlabel("IL (mA)", fontsize=8)
        a2.legend(fontsize=7)
        a3.axhline(izmax * 1e3, color="#c62828", lw=1, ls=":")
        a3.text(0, izmax * 1e3, f" Iz max = Pz/Vz = {izmax * 1e3:.1f} mA", color="#c62828", fontsize=7, va="bottom")
        a3.axhline(izmin * 1e3, color="#8a6d00", lw=1, ls=":")
        a3.text(0, izmin * 1e3, f" Iz min {izmin * 1e3:.1f} mA", color="#8a6d00", fontsize=7, va="bottom")
        a3.set_title(t("zd.p3"), fontsize=9)
        a3.set_xlabel("Vin (V)", fontsize=8)
        a3.set_ylabel("Iz (mA)", fontsize=8)
        a3.legend(fontsize=7, loc="upper left")
        for a in (a1, a2, a3):
            a.grid(True, alpha=0.25)
            a.set_facecolor(PLOT_BG)
            a.tick_params(labelsize=7)
        fig.tight_layout()
        self.chart.redraw()

    def _draw(self, r, vz):
        cv = self.canvas
        cv.delete("all")
        top, bot = 35, 145
        sym.dc_source(cv, 40, 90, label="")
        cv.create_text(40, 125, text="Vin", font=("Segoe UI", 8, "bold"), fill=sym.LABEL_COLOR)
        sym.wire(cv, 40, 74, 40, top, 80, top)
        sym.wire(cv, 40, 106, 40, bot, 350, bot)
        sym.ground(cv, 200, bot + 4)
        sym.resistor(cv, 80, top, 180, top, label="R", value=eng(r, "Ω"))
        sym.wire(cv, 180, top, 350, top)
        sym.node(cv, 220, top)
        sym.node(cv, 290, top)
        sym.node(cv, 220, bot)
        sym.node(cv, 290, bot)
        sym.diode(cv, 220, bot, 220, top, label="DZ", value=f"{vz:g} V", variant="zener", label_side=1)
        sym.resistor(cv, 290, top, 290, bot, label="RL", label_side=1)
        sym.terminal(cv, 350, top, label="Vout")


# ===========================================================================
# LED array planner
# ===========================================================================
LED_COLORS = [("red", 2.0, 20e-3, "#e53935", "620–630 nm"), ("orange", 2.1, 20e-3, "#fb8c00", "600–610 nm"),
              ("yellow", 2.1, 20e-3, "#fdd835", "585–590 nm"), ("green", 3.0, 20e-3, "#43a047", "520–530 nm"),
              ("blue", 3.1, 20e-3, "#1e88e5", "465–475 nm"), ("white", 3.1, 20e-3, "#f5f5f5", "~5000–6500 K"),
              ("ir", 1.3, 50e-3, "#7b1f1f", "850–940 nm"), ("uv", 3.4, 20e-3, "#7e57c2", "395–405 nm")]


class LedArrayPanel(ttk.Frame):
    def __init__(self, parent, accent):
        super().__init__(parent, style="Card.TFrame")
        self.accent = accent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body
        note(body, t("la.intro"), wrap=900, pady=(12, 6))
        top = ttk.Frame(body, style="Card.TFrame")
        top.pack(fill="x", padx=16)
        left = ttk.Frame(top, style="Card.TFrame")
        left.pack(side="left", anchor="n")
        r = ttk.Frame(left, style="Card.TFrame")
        r.pack(anchor="w", pady=(0, 4))
        ttk.Label(r, text=t("la.color"), font=FONT_BODY, style="CardBody.TLabel").pack(side="left", padx=(0, 6))
        self.color = tk.StringVar(value="red")
        self.cbtns = {}
        for key, vf, i_, hexc, wl in LED_COLORS:
            b = tk.Label(r, bg=hexc, width=2, relief="solid", bd=1, cursor="hand2")
            b.pack(side="left", padx=1)
            b.bind("<Button-1>", lambda _e, k=key: self._pick(k))
            self.cbtns[key] = b
        self.cname = ttk.Label(left, text="", font=("Segoe UI", 9), style="CardBody.TLabel")
        self.cname.pack(anchor="w")
        self.form = ParamForm(left, [
            dict(key="vs", label=t("la.vs"), default="12", unit="V", slider=(1, 48)),
            dict(key="vf", label=t("la.vf"), default="2", unit="V", slider=(1.2, 3.6)),
            dict(key="if", label=t("la.if"), default="20m", unit="A", slider=(1e-3, 0.35, True)),
            dict(key="n", label=t("la.n"), default="12", unit="", slider=(1, 60)),
        ], self.update_all, label_width=18)
        self.form.pack(anchor="w")
        r2 = ttk.Frame(left, style="Card.TFrame")
        r2.pack(anchor="w", pady=4)
        ttk.Label(r2, text=t("la.per"), font=FONT_BODY, style="CardBody.TLabel", width=18, anchor="w")\
            .pack(side="left")
        self.per = tk.StringVar(value=t("la.auto"))
        self.per_cb = ttk.Combobox(r2, textvariable=self.per, state="readonly", width=12)
        self.per_cb.pack(side="left")
        self.per_cb.bind("<<ComboboxSelected>>", lambda e: self.update_all())
        self.tiles = TileRow(left, [("arr", t("la.t.arr")), ("r", t("la.t.r")), ("i", t("la.t.i")),
                                    ("itot", t("la.t.itot")), ("pr", t("la.t.pr")), ("ptot", t("la.t.ptot")),
                                    ("eff", t("la.t.eff")), ("spread", t("la.t.spread"))], accent, per_row=2)
        self.tiles.pack(fill="x", pady=(6, 0))
        self.warn = note(left, "", wrap=380, color="#c62828")
        right = ttk.Frame(top, style="Card.TFrame")
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))
        self.canvas = tk.Canvas(right, width=520, height=300, bg="#101418", highlightthickness=0)
        self.canvas.pack(anchor="nw")
        ttk.Label(right, text=t("la.table"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel")\
            .pack(anchor="w", pady=(8, 2))
        cols = ("per", "str", "r", "eff", "sens")
        self.tree = ttk.Treeview(right, columns=cols, show="headings", height=6)
        for c, k in zip(cols, ("la.col.per", "la.col.str", "la.col.r", "la.col.eff", "la.col.sens")):
            self.tree.heading(c, text=t(k))
            self.tree.column(c, width=95, anchor="center")
        self.tree.pack(fill="x")
        self._pick("red", update=False)
        self.update_all()

    def _pick(self, key, update=True):
        self.color.set(key)
        for k, b in self.cbtns.items():
            b.configure(relief="sunken" if k == key else "solid", bd=3 if k == key else 1)
        c = next(x for x in LED_COLORS if x[0] == key)
        self.form.set("vf", f"{c[1]:g}")
        self.form.set("if", nice(c[2]))
        self.cname.configure(text=f"{t('la.c.' + key)} · {c[4]} · Vf ≈ {c[1]:g} V")
        if update:
            self.update_all()

    @staticmethod
    def _option(vs, vf, i_led, per, n):
        head = vs - per * vf
        if head <= 0.05:
            return None
        strings = math.ceil(n / per)
        r = e24_up(head / i_led)
        i = head / r
        pr = i * i * r
        p_led = per * vf * i
        eff = p_led / (vs * i)
        di = 0.1 * per / r
        return dict(per=per, strings=strings, r=r, i=i, pr=pr, eff=eff, di=di, head=head, extra=strings * per - n)

    def update_all(self, *_):
        try:
            P = self.form.values()
        except Exception:
            return
        vs, vf, il, n = P["vs"], P["vf"], P["if"], max(1, int(round(P["n"])))
        opts = []
        for per in range(1, n + 1):
            o = self._option(vs, vf, il, per, n)
            if o:
                opts.append(o)
        self.tree.delete(*self.tree.get_children())
        vals = [t("la.auto")] + [str(o["per"]) for o in opts]
        self.per_cb.configure(values=vals)
        if not opts:
            self.warn.configure(text=t("la.toolow"))
            for k in self.tiles.tiles:
                self.tiles.set(k, "–")
            self.canvas.delete("all")
            return
        # best = most efficient with at least 1 V (or 15 %) headroom
        good = [o for o in opts if o["head"] >= max(1.0, 0.15 * vs)] or opts[:1]
        best = max(good, key=lambda o: (o["extra"] == 0, o["eff"], -o["strings"]))
        if self.per.get() != t("la.auto") and self.per.get() in vals:
            best = next(o for o in opts if str(o["per"]) == self.per.get())
        for o in opts:
            self.tree.insert("", "end", values=(o["per"], o["strings"], eng(o["r"], "Ω"), f"{o['eff'] * 100:.0f} %",
                                                 f"±{o['di'] / o['i'] * 100:.0f} %"),
                             tags=("best",) if o is best else ())
        self.tree.tag_configure("best", background="#e3f3e6")
        o = best
        tl = self.tiles
        tl.set("arr", f"{o['strings']} × {o['per']}")
        tl.set("r", eng(o["r"], "Ω"))
        tl.set("i", eng(o["i"], "A"))
        tl.set("itot", eng(o["i"] * o["strings"], "A"))
        tl.set("pr", eng(o["pr"], "W") + f" → {ZenerDesignPanel._rating(o['pr'])}")
        tl.set("ptot", eng(vs * o["i"] * o["strings"], "W"))
        tl.set("eff", f"{o['eff'] * 100:.0f} %")
        tl.set("spread", f"±{o['di'] / o['i'] * 100:.0f} %", warn=o["di"] / o["i"] > 0.25)
        if o["extra"]:
            k = o["per"] - o["extra"]
            r2 = e24_up((vs - k * vf) / il)
            self.warn.configure(text=t("la.extra").format(k=k, r=eng(r2, "Ω")))
        else:
            self.warn.configure(text="")
        self._draw(o, n)

    def _draw(self, o, n):
        cv = self.canvas
        cv.delete("all")
        W, H = 520, 300
        col = next(x for x in LED_COLORS if x[0] == self.color.get())[3]
        strings, per = o["strings"], o["per"]
        # layout: strings as columns, LEDs down each column
        maxcols = min(strings, 12)
        maxrows = min(per, 8)
        x0, x1 = 60, W - 30
        y0, y1 = 40, H - 40
        dx = (x1 - x0) / max(1, maxcols)
        cv.create_line(30, y0 - 18, W - 20, y0 - 18, fill="#e0e0e0", width=2)
        cv.create_line(30, y1 + 18, W - 20, y1 + 18, fill="#e0e0e0", width=2)
        cv.create_text(28, y0 - 18, text="+", fill="#ff8a80", font=("Segoe UI", 12, "bold"), anchor="e")
        cv.create_text(28, y1 + 18, text="−", fill="#90caf9", font=("Segoe UI", 12, "bold"), anchor="e")
        left = n
        for s in range(maxcols):
            x = x0 + dx * (s + 0.5)
            cnt = min(per, left)
            left -= per
            cv.create_line(x, y0 - 18, x, y0, fill="#e0e0e0", width=2)
            # resistor
            cv.create_rectangle(x - 5, y0, x + 5, y0 + 24, outline="#e0c070", width=2)
            ry = y0 + 30
            dy = (y1 - ry) / max(1, maxrows)
            for k in range(maxrows):
                cy = ry + dy * (k + 0.5)
                lit = k < cnt
                glow = col if lit else "#333a44"
                if lit:
                    cv.create_oval(x - 12, cy - 12, x + 12, cy + 12, fill="", outline=col, width=1)
                cv.create_polygon(x - 7, cy - 6, x + 7, cy - 6, x, cy + 6, fill=glow, outline="#dddddd")
                cv.create_line(x - 7, cy + 6, x + 7, cy + 6, fill="#dddddd", width=2)
            cv.create_line(x, y0 + 24, x, y1 + 18, fill="#e0e0e0", width=1)
        more = []
        if strings > maxcols:
            more.append(tr(f"+{strings - maxcols} strings", f"+{strings - maxcols} șiruri"))
        if per > maxrows:
            more.append(tr(f"({per} LEDs per string, {maxrows} drawn)", f"({per} LED-uri pe șir, {maxrows} desenate)"))
        if more:
            cv.create_text(W / 2, H - 10, text="  ".join(more), fill="#bbbbbb", font=("Segoe UI", 8))
        cv.create_text(W - 20, 12, text=tr(f"R = {eng(o['r'], 'Ω')} per string", f"R = {eng(o['r'], 'Ω')} pe șir"), fill="#e0c070",
                       font=("Segoe UI", 9, "bold"), anchor="e")
