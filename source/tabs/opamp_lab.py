"""
tabs/opamp_lab.py - Op-amp circuit lab (v6).

Pick a configuration (amplifiers, integrator / differentiator, comparators
and Schmitt triggers, peak detector / precision rectifier, oscillators and
signal generators), set the parts and the op-amp model, and see the
schematic, the waveforms, the transfer (X-Y) curve and the key numbers.
"""
import math
import numpy as np
import tkinter as tk
from tkinter import ttk
from matplotlib.gridspec import GridSpec

import symbols as sym
import opamp_sim as osim
from charts import MplChartFrame, PLOT_BG
from widgets import ScrollableFrame, FONT_BODY
from uikit import Segmented, ParamForm, TileRow, section, note, eng
from i18n import t, register, tr

C_IN = "#c9622a"
C_IN2 = "#8a6d00"
C_OUT = "#1f6a5f"
C_AUX = "#6A4C93"

register({
    "oa.lab": ("Circuit Lab", "Laborator circuite"),
    "oa.group": ("Family", "Familie"),
    "oa.g.amp": ("Amplifiers", "Amplificatoare"),
    "oa.g.math": ("Integrate / differentiate", "Integrare / derivare"),
    "oa.g.cmp": ("Comparators", "Comparatoare"),
    "oa.g.proc": ("Signal processing", "Prelucrare semnal"),
    "oa.g.osc": ("Oscillators / generators", "Oscilatoare / generatoare"),
    "oa.c.inv": ("Inverting", "Inversor"),
    "oa.c.noninv": ("Non-inverting", "Neinversor"),
    "oa.c.buffer": ("Buffer (follower)", "Repetor"),
    "oa.c.sum": ("Summing", "Sumator"),
    "oa.c.diff": ("Differential", "Diferențial"),
    "oa.c.int": ("Integrator", "Integrator"),
    "oa.c.der": ("Differentiator", "Derivator"),
    "oa.c.cmp": ("Comparator", "Comparator"),
    "oa.c.st_inv": ("Schmitt trigger (inverting)", "Trigger Schmitt (inversor)"),
    "oa.c.st_non": ("Schmitt trigger (non-inverting)", "Trigger Schmitt (neinversor)"),
    "oa.c.peak": ("Peak detector", "Detector de vârf"),
    "oa.c.rect": ("Precision rectifier", "Redresor de precizie"),
    "oa.c.relax": ("Relaxation oscillator", "Oscilator de relaxare"),
    "oa.c.sqtri": ("Square + triangle generator", "Generator dreptunghi + triunghi"),
    "oa.c.wien": ("Wien-bridge (sine) oscillator", "Oscilator cu punte Wien (sinus)"),
    "oa.input": ("Input signal", "Semnal de intrare"),
    "oa.input2": ("Second input V2", "A doua intrare V2"),
    "oa.w.sine": ("Sine", "Sinus"), "oa.w.square": ("Square", "Dreptunghi"),
    "oa.w.tri": ("Triangle", "Triunghi"), "oa.w.dc": ("DC", "DC"),
    "oa.amp": ("Amplitude (peak)", "Amplitudine (vârf)"),
    "oa.freq": ("Frequency", "Frecvență"),
    "oa.offset": ("DC offset", "Offset DC"),
    "oa.parts": ("Components", "Componente"),
    "oa.model": ("Op-amp", "Amplificator operațional"),
    "oa.m.ideal": ("Ideal", "Ideal"),
    "oa.m.lm741": ("LM741 (1 MHz, 0.5 V/µs)", "LM741 (1 MHz, 0,5 V/µs)"),
    "oa.m.tl081": ("TL081 (3 MHz, 13 V/µs)", "TL081 (3 MHz, 13 V/µs)"),
    "oa.m.lm358": ("LM358 (1 MHz, 0.3 V/µs)", "LM358 (1 MHz, 0,3 V/µs)"),
    "oa.m.rrio": ("Rail-to-rail (10 MHz, 10 V/µs)", "Rail-to-rail (10 MHz, 10 V/µs)"),
    "oa.vcc": ("Supply ±Vcc", "Alimentare ±Vcc"),
    "oa.stab": ("Diode amplitude stabilisation", "Stabilizare amplitudine cu diode"),
    "oa.ax.t": ("Time (ms)", "Timp (ms)"),
    "oa.ax.v": ("Voltage (V)", "Tensiune (V)"),
    "oa.xy": ("Transfer (Vout vs Vin)", "Transfer (Vout față de Vin)"),
    "oa.xy.osc": ("X-Y view", "Vedere X-Y"),
    "oa.op_out": ("op-amp output", "ieșire AO"),
    "oa.ideal_out": ("ideal", "ideal"),
    "oa.t.gain": ("Gain (formula)", "Câștig (formulă)"),
    "oa.t.vpk": ("Vout peak (simulated)", "Vout vârf (simulat)"),
    "oa.t.bw": ("Closed-loop bandwidth", "Bandă în buclă închisă"),
    "oa.t.status": ("Status", "Stare"),
    "oa.t.ok": ("OK — linear", "OK — liniar"),
    "oa.t.clip": ("CLIPPING (rails)", "LIMITARE (la alimentare)"),
    "oa.t.slew": ("SLEW-RATE LIMITED", "LIMITAT DE SLEW-RATE"),
    "oa.t.bwlim": ("above bandwidth", "peste bandă"),
    "oa.t.f0": ("Unity-gain frequency", "Frecvența de câștig unitar"),
    "oa.t.slope": ("Output slope", "Panta ieșirii"),
    "oa.t.dcg": ("DC gain (−Rf/R)", "Câștig DC (−Rf/R)"),
    "oa.t.gf": ("|Gain| at input f", "|Câștig| la f intrare"),
    "oa.t.fc": ("Rin·C corner", "Colțul Rin·C"),
    "oa.t.ut": ("Upper threshold", "Prag superior"),
    "oa.t.lt": ("Lower threshold", "Prag inferior"),
    "oa.t.hyst": ("Hysteresis", "Histerezis"),
    "oa.t.swing": ("Output swing", "Excursia ieșirii"),
    "oa.t.held": ("Peak held", "Vârf memorat"),
    "oa.t.droop": ("Droop per period", "Scădere pe perioadă"),
    "oa.t.tau": ("τ = RC", "τ = RC"),
    "oa.t.err": ("Error at peak", "Eroare la vârf"),
    "oa.t.fth": ("f (formula)", "f (formulă)"),
    "oa.t.fsim": ("f (simulated)", "f (simulat)"),
    "oa.t.amp": ("Output amplitude", "Amplitudine ieșire"),
    "oa.t.tri": ("Triangle amplitude", "Amplitudine triunghi"),
    "oa.t.loop": ("Loop gain (Rf/Rg + 1)", "Câștig buclă (Rf/Rg + 1)"),
    # component labels
    "oa.p.rin": ("Rin", "Rin"), "oa.p.rf": ("Rf (feedback)", "Rf (reacție)"), "oa.p.rg": ("Rg (to ground)", "Rg (la masă)"),
    "oa.p.r1": ("R1", "R1"), "oa.p.r2": ("R2", "R2"), "oa.p.mis": ("Resistor mismatch", "Nepotrivire rezistoare"),
    "oa.p.r": ("R", "R"), "oa.p.c": ("C", "C"), "oa.p.rleak": ("Rf (DC leak, 0 = none)", "Rf (scurgere DC, 0 = fără)"),
    "oa.p.vref": ("Reference Vref", "Referință Vref"), "oa.p.rbleed": ("R (discharge)", "R (descărcare)"),
    # explanations
    "oa.x.inv": ("The (+) input is grounded, so feedback holds the (−) input at 0 V too (virtual ground). "
                 "All the input current Vin/Rin must flow through Rf: Vout = −(Rf/Rin)·Vin. Input impedance = Rin.",
                 "Intrarea (+) e la masă, deci reacția ține și intrarea (−) la 0 V (masă virtuală). Tot curentul "
                 "Vin/Rin trece prin Rf: Vout = −(Rf/Rin)·Vin. Impedanța de intrare = Rin."),
    "oa.x.noninv": ("Vin drives the (+) input; the op-amp sets Vout so the divider Rf–Rg returns exactly Vin to "
                    "(−): Vout = (1 + Rf/Rg)·Vin, in phase, with a very high input impedance.",
                    "Vin intră pe (+); AO fixează Vout astfel încât divizorul Rf–Rg să aducă exact Vin pe (−): "
                    "Vout = (1 + Rf/Rg)·Vin, în fază, cu impedanță de intrare foarte mare."),
    "oa.x.buffer": ("100 % feedback: Vout = Vin. No voltage gain, but huge input impedance and low output "
                    "impedance — used to stop a load from pulling down a weak source (e.g. a divider).",
                    "Reacție 100 %: Vout = Vin. Fără câștig în tensiune, dar impedanță de intrare uriașă și de ieșire "
                    "mică — folosit ca o sarcină să nu 'tragă' o sursă slabă (ex. un divizor)."),
    "oa.x.sum": ("Each input pushes its own current Vn/Rn into the virtual-ground node; Rf turns the total "
                 "into a voltage: Vout = −Rf·(V1/R1 + V2/R2). With equal resistors it is an (inverting) mixer.",
                 "Fiecare intrare împinge propriul curent Vn/Rn în nodul de masă virtuală; Rf transformă suma "
                 "în tensiune: Vout = −Rf·(V1/R1 + V2/R2). Cu rezistoare egale e un mixer (inversor)."),
    "oa.x.diff": ("Amplifies the DIFFERENCE: Vout = (R2/R1)·(V2 − V1) and rejects what both inputs have in "
                  "common — if the resistors match. Set a mismatch to see common-mode signal leak through (CMRR).",
                  "Amplifică DIFERENȚA: Vout = (R2/R1)·(V2 − V1) și rejectează ce au comun cele două intrări — "
                  "dacă rezistoarele sunt egale. Introdu o nepotrivire ca să vezi cum trece semnalul comun (CMRR)."),
    "oa.x.int": ("The input current Vin/R charges C: Vout = −(1/RC)·∫Vin dt. A square wave becomes a triangle, "
                 "a sine becomes a (−)cosine. Any DC offset integrates to the rail, so a large Rf across C is "
                 "used to limit the DC gain.",
                 "Curentul de intrare Vin/R încarcă C: Vout = −(1/RC)·∫Vin dt. Un dreptunghi devine triunghi, un "
                 "sinus devine −cosinus. Orice offset DC se integrează până la alimentare, de aceea se pune un Rf "
                 "mare în paralel cu C, care limitează câștigul în DC."),
    "oa.x.der": ("The current through C is C·dVin/dt, so Vout = −Rf·C·dVin/dt: a triangle becomes a square, "
                 "a square becomes spikes. A small Rin in series with C limits the gain at high frequency "
                 "(otherwise noise is amplified and the circuit rings).",
                 "Curentul prin C este C·dVin/dt, deci Vout = −Rf·C·dVin/dt: un triunghi devine dreptunghi, un "
                 "dreptunghi devine impulsuri. Un Rin mic în serie cu C limitează câștigul la frecvențe mari "
                 "(altfel zgomotul e amplificat și circuitul oscilează)."),
    "oa.x.cmp": ("No feedback: the huge open-loop gain slams the output to a rail depending on whether Vin is "
                 "above or below Vref. A noisy or slow input can make it chatter around the threshold — the "
                 "Schmitt trigger fixes that.",
                 "Fără reacție: câștigul uriaș în buclă deschisă duce ieșirea la o alimentare după cum Vin e peste "
                 "sau sub Vref. O intrare zgomotoasă sau lentă poate face ieșirea să 'tremure' la prag — triggerul "
                 "Schmitt rezolvă asta."),
    "oa.x.st_inv": ("Positive feedback through R2 moves the threshold with the output: while Vout is high the "
                    "input must rise above UT to switch it low, then fall below LT to switch back. The gap "
                    "(hysteresis) ignores noise. UT/LT = (Vref·R2 ± Vsat·R1)/(R1 + R2).",
                    "Reacția pozitivă prin R2 mută pragul odată cu ieșirea: cât Vout e sus, intrarea trebuie să urce "
                    "peste UT ca să o comute jos, apoi să coboare sub LT ca să revină. Intervalul (histerezisul) "
                    "ignoră zgomotul. UT/LT = (Vref·R2 ± Vsat·R1)/(R1 + R2)."),
    "oa.x.st_non": ("Same idea, but the input enters the (+) side through R1, so the output is in phase with the "
                    "input. Thresholds: Vin = Vref·(1 + R1/R2) ∓ Vsat·R1/R2.",
                    "Aceeași idee, dar intrarea intră pe (+) prin R1, deci ieșirea e în fază cu intrarea. Praguri: "
                    "Vin = Vref·(1 + R1/R2) ∓ Vsat·R1/R2."),
    "oa.x.peak": ("The op-amp charges C through the diode until Vout = Vin (the diode drop is inside the loop, so "
                  "it cancels), then the diode blocks and C holds the highest value seen. R slowly discharges it. "
                  "Watch the op-amp output: it slams to the negative rail between peaks and must slew back — "
                  "slow op-amps miss fast peaks.",
                  "AO încarcă C prin diodă până Vout = Vin (căderea pe diodă e în buclă, deci se anulează), apoi "
                  "dioda blochează și C păstrează cea mai mare valoare. R îl descarcă încet. Urmărește ieșirea "
                  "AO: între vârfuri merge la alimentarea negativă și trebuie să revină cu slew-rate-ul — AO lente "
                  "ratează vârfurile rapide."),
    "oa.x.rect": ("A 'super-diode': with the diode inside the feedback loop the 0.6 V drop is divided by the "
                  "open-loop gain, so even millivolt signals are rectified. On negative half-cycles the loop "
                  "opens and the output saturates; at high frequency the time to slew back shows up as a glitch.",
                  "O 'super-diodă': cu dioda în bucla de reacție, căderea de 0,6 V e împărțită la câștigul în buclă "
                  "deschisă, deci chiar și semnale de milivolți sunt redresate. Pe semiperioadele negative bucla "
                  "se deschide și ieșirea se saturează; la frecvență mare timpul de revenire apare ca o distorsiune."),
    "oa.x.relax": ("A Schmitt trigger whose output charges C through R. When Vc reaches the upper threshold "
                   "the output flips and C discharges toward the other rail: a square wave at "
                   "f = 1 / (2RC·ln((1+β)/(1−β))), β = R1/(R1+R2).",
                   "Un trigger Schmitt a cărui ieșire încarcă C prin R. Când Vc atinge pragul superior, ieșirea "
                   "comută și C se descarcă spre cealaltă alimentare: undă dreptunghiulară cu "
                   "f = 1 / (2RC·ln((1+β)/(1−β))), β = R1/(R1+R2)."),
    "oa.x.sqtri": ("Two op-amps in a loop: the integrator turns the square into a linear ramp, the Schmitt "
                   "trigger flips when the ramp reaches ±Vsat·R1/R2. Result: a square AND a triangle, "
                   "f = R2 / (4·R1·R·C) — the basis of classic function generators.",
                   "Două AO în buclă: integratorul transformă dreptunghiul într-o rampă liniară, triggerul Schmitt "
                   "comută când rampa ajunge la ±Vsat·R1/R2. Rezultat: un dreptunghi ȘI un triunghi, "
                   "f = R2 / (4·R1·R·C) — baza generatoarelor de funcții clasice."),
    "oa.x.wien": ("The RC network (series R-C then parallel R‖C) passes 1/3 of the signal with zero phase shift "
                  "at f0 = 1/(2πRC). With a non-inverting gain of exactly 3 the loop sustains a sine. Gain < 3: "
                  "it dies away; gain > 3: it grows until something limits it — rails (distorted) or diodes "
                  "across Rf (clean).",
                  "Rețeaua RC (R-C serie apoi R‖C paralel) lasă să treacă 1/3 din semnal cu defazaj zero la "
                  "f0 = 1/(2πRC). Cu un câștig neinversor de exact 3 bucla întreține un sinus. Câștig < 3: se "
                  "stinge; câștig > 3: crește până e limitat — de alimentare (distorsionat) sau de diodele pe "
                  "Rf (curat)."),
})

GROUPS = [
    ("amp", ["inv", "noninv", "buffer", "sum", "diff"]),
    ("math", ["int", "der"]),
    ("cmp", ["cmp", "st_inv", "st_non"]),
    ("proc", ["peak", "rect"]),
    ("osc", ["relax", "sqtri", "wien"]),
]
OSC = ("relax", "sqtri", "wien")

PARAMS = {
    "inv": [("rin", "oa.p.rin", "1k", "Ω", (100, 100e3, True)), ("rf", "oa.p.rf", "10k", "Ω", (100, 1e6, True))],
    "noninv": [("rg", "oa.p.rg", "1k", "Ω", (100, 100e3, True)), ("rf", "oa.p.rf", "4.7k", "Ω", (0, 1e6))],
    "buffer": [],
    "sum": [("r1", "oa.p.r1", "10k", "Ω", (1e3, 100e3, True)), ("r2", "oa.p.r2", "10k", "Ω", (1e3, 100e3, True)),
            ("rf", "oa.p.rf", "10k", "Ω", (1e3, 1e6, True))],
    "diff": [("r1", "oa.p.r1", "10k", "Ω", (1e3, 100e3, True)), ("r2", "oa.p.r2", "10k", "Ω", (1e3, 1e6, True)),
             ("mis", "oa.p.mis", "0", "%", (0, 10))],
    "int": [("r", "oa.p.r", "10k", "Ω", (1e3, 1e6, True)), ("c", "oa.p.c", "100n", "F", None),
            ("rf", "oa.p.rleak", "1M", "Ω", None)],
    "der": [("rin", "oa.p.rin", "100", "Ω", (1, 10e3, True)), ("c", "oa.p.c", "100n", "F", None),
            ("rf", "oa.p.rf", "10k", "Ω", (1e3, 1e6, True))],
    "cmp": [("vref", "oa.p.vref", "0", "V", (-10, 10))],
    "st_inv": [("r1", "oa.p.r1", "10k", "Ω", (1e3, 100e3, True)), ("r2", "oa.p.r2", "47k", "Ω", (1e3, 1e6, True)),
               ("vref", "oa.p.vref", "0", "V", (-10, 10))],
    "st_non": [("r1", "oa.p.r1", "10k", "Ω", (1e3, 100e3, True)), ("r2", "oa.p.r2", "47k", "Ω", (1e3, 1e6, True)),
               ("vref", "oa.p.vref", "0", "V", (-10, 10))],
    "peak": [("c", "oa.p.c", "1u", "F", None), ("r", "oa.p.rbleed", "100k", "Ω", (1e3, 10e6, True))],
    "rect": [],
    "relax": [("r", "oa.p.r", "10k", "Ω", (1e3, 1e6, True)), ("c", "oa.p.c", "100n", "F", None),
              ("r1", "oa.p.r1", "10k", "Ω", (1e3, 100e3, True)), ("r2", "oa.p.r2", "10k", "Ω", (1e3, 100e3, True))],
    "sqtri": [("r", "oa.p.r", "10k", "Ω", (1e3, 1e6, True)), ("c", "oa.p.c", "100n", "F", None),
              ("r1", "oa.p.r1", "10k", "Ω", (1e3, 100e3, True)), ("r2", "oa.p.r2", "20k", "Ω", (1e3, 100e3, True))],
    "wien": [("r", "oa.p.r", "10k", "Ω", (1e3, 100e3, True)), ("c", "oa.p.c", "10n", "F", None),
             ("rf", "oa.p.rf", "22k", "Ω", (10e3, 30e3)), ("rg", "oa.p.rg", "10k", "Ω", None)],
}
# default input per circuit: (wave, amp, freq, offset)
INPUT_DEFAULT = {
    "inv": ("sine", "1", "1k", "0"), "noninv": ("sine", "1", "1k", "0"), "buffer": ("sine", "5", "1k", "0"),
    "sum": ("sine", "1", "1k", "0"), "diff": ("sine", "0.5", "1k", "2"),
    "int": ("square", "1", "1k", "0"), "der": ("tri", "1", "1k", "0"),
    "cmp": ("sine", "5", "100", "0"), "st_inv": ("sine", "5", "100", "0"), "st_non": ("sine", "5", "100", "0"),
    "peak": ("sine", "5", "100", "0"), "rect": ("sine", "1", "1k", "0"),
}
MODEL_KEYS = ["ideal", "lm741", "tl081", "lm358", "rrio"]


class OpAmpLabPanel(ttk.Frame):
    def __init__(self, parent, accent):
        super().__init__(parent, style="Card.TFrame")
        self.accent = accent
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        sf = ScrollableFrame(self, style="Card.TFrame")
        sf.grid(row=0, column=0, sticky="nsew")
        body = sf.body

        pick = ttk.Frame(body, style="Card.TFrame")
        pick.pack(fill="x", padx=16, pady=(12, 0))
        self.group = tk.StringVar(value="amp")
        Segmented(pick, [(g, t("oa.g." + g)) for g, _ in GROUPS], self.group, self._on_group,
                  accent=accent, font_size=10).pack(anchor="w")
        self.circ_row = ttk.Frame(pick, style="Card.TFrame")
        self.circ_row.pack(anchor="w", pady=(6, 0))
        self.circuit = tk.StringVar(value="inv")

        top = ttk.Frame(body, style="Card.TFrame")
        top.pack(fill="both", expand=True, padx=16, pady=(8, 12))
        top.columnconfigure(1, weight=1)
        left = ttk.Frame(top, style="Card.TFrame")
        left.grid(row=0, column=0, sticky="nw")
        right = ttk.Frame(top, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(16, 0))
        self.left = left

        # input 1
        self.in_box = ttk.Frame(left, style="Card.TFrame")
        self.in_box.pack(fill="x")
        ttk.Label(self.in_box, text=t("oa.input"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel")\
            .pack(anchor="w")
        self.wave = tk.StringVar(value="sine")
        self.wave_seg = Segmented(self.in_box, [(k, t("oa.w." + k)) for k in ("sine", "square", "tri", "dc")],
                                  self.wave, lambda k: self.simulate(), accent=accent)
        self.wave_seg.pack(anchor="w", pady=(2, 4))
        self.in_form = ParamForm(self.in_box, [
            dict(key="amp", label=t("oa.amp"), default="1", unit="V", slider=(0, 10)),
            dict(key="f", label=t("oa.freq"), default="1k", unit="Hz", slider=(10, 100e3, True)),
            dict(key="off", label=t("oa.offset"), default="0", unit="V", slider=(-5, 5)),
        ], self.simulate, label_width=18)
        self.in_form.pack(anchor="w")
        # input 2
        self.in2_box = ttk.Frame(left, style="Card.TFrame")
        ttk.Label(self.in2_box, text=t("oa.input2"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel")\
            .pack(anchor="w", pady=(6, 0))
        self.wave2 = tk.StringVar(value="dc")
        Segmented(self.in2_box, [(k, t("oa.w." + k)) for k in ("sine", "square", "tri", "dc")], self.wave2,
                  lambda k: self.simulate(), accent=accent).pack(anchor="w", pady=(2, 4))
        self.in2_form = ParamForm(self.in2_box, [
            dict(key="amp", label=t("oa.amp"), default="0", unit="V", slider=(0, 10)),
            dict(key="f", label=t("oa.freq"), default="250", unit="Hz", slider=(10, 100e3, True)),
            dict(key="off", label=t("oa.offset"), default="2", unit="V", slider=(-5, 5)),
        ], self.simulate, label_width=18)
        self.in2_form.pack(anchor="w")

        self.parts_label = ttk.Label(left, text=t("oa.parts"), font=("Segoe UI", 10, "bold"),
                                     style="CardSub.TLabel")
        self.parts_label.pack(anchor="w", pady=(8, 0))
        self.form_holder = ttk.Frame(left, style="Card.TFrame")
        self.form_holder.pack(anchor="w", fill="x")
        self.stab = tk.BooleanVar(value=True)
        self.stab_cb = ttk.Checkbutton(left, text=t("oa.stab"), variable=self.stab, command=self.simulate)

        ttk.Label(left, text=t("oa.model"), font=("Segoe UI", 10, "bold"), style="CardSub.TLabel")\
            .pack(anchor="w", pady=(8, 0))
        mrow = ttk.Frame(left, style="Card.TFrame")
        mrow.pack(anchor="w")
        self.model_names = {k: t("oa.m." + k) for k in MODEL_KEYS}
        self.model = tk.StringVar(value=self.model_names["ideal"])
        cb = ttk.Combobox(mrow, textvariable=self.model, values=list(self.model_names.values()),
                          state="readonly", width=30)
        cb.pack(side="left")
        cb.bind("<<ComboboxSelected>>", lambda e: self.simulate())
        self.sup_form = ParamForm(left, [dict(key="vcc", label=t("oa.vcc"), default="15", unit="V",
                                              slider=(3, 18))], self.simulate, label_width=18)
        self.sup_form.pack(anchor="w", pady=(4, 0))

        self.tiles = TileRow(left, [("a", "a"), ("b", "b"), ("c", "c"), ("d", "d")], accent, per_row=2)
        self.tiles.pack(fill="x", pady=(10, 0))
        self.explain = note(left, "", wrap=440, padx=0, pady=(8, 4))

        self.canvas = tk.Canvas(right, width=540, height=280, bg=sym.CANVAS_BG, highlightthickness=0)
        self.canvas.pack(anchor="n")
        self.chart = MplChartFrame(right, figsize=(7.2, 3.6), with_toolbar=True)
        self.chart.pack(fill="both", expand=True, pady=(6, 0))
        self._on_group("amp")

    # ------------------------------------------------------------------
    def _on_group(self, g):
        for w in self.circ_row.winfo_children():
            w.destroy()
        items = dict(GROUPS)[g]
        if self.circuit.get() not in items:
            self.circuit.set(items[0])
        Segmented(self.circ_row, [(k, t("oa.c." + k)) for k in items], self.circuit, self._on_circuit,
                  accent=self.accent).pack(anchor="w")
        self._on_circuit(self.circuit.get())

    def _on_circuit(self, key):
        for w in self.form_holder.winfo_children():
            w.destroy()
        fields = [dict(key=k, label=t(lab), default=d, unit=u, slider=sl) for k, lab, d, u, sl in PARAMS[key]]
        self.form = ParamForm(self.form_holder, fields, self.simulate, label_width=18) if fields else None
        if self.form:
            self.form.pack(anchor="w")
        # inputs
        if key in OSC:
            self.in_box.pack_forget()
        else:
            if not self.in_box.winfo_ismapped():
                self.in_box.pack(fill="x", before=self.parts_label)
            w, a, f, o = INPUT_DEFAULT[key]
            self.wave_seg.select(w, fire=False)
            self.in_form.set("amp", a)
            self.in_form.set("f", f)
            self.in_form.set("off", o)
        if key in ("sum", "diff"):
            if not self.in2_box.winfo_ismapped():
                self.in2_box.pack(fill="x", before=self.parts_label)
        else:
            self.in2_box.pack_forget()
        if key == "wien":
            self.stab_cb.pack(anchor="w", after=self.form_holder)
        else:
            self.stab_cb.pack_forget()
        self.explain.configure(text=t("oa.x." + key))
        self.simulate()

    def _model_key(self):
        for k, v in self.model_names.items():
            if v == self.model.get():
                return k
        return "ideal"

    # ------------------------------------------------------------------
    def simulate(self, *_):
        key = self.circuit.get()
        try:
            P = self.form.values() if self.form else {}
            vcc = self.sup_form.get("vcc")
            I = self.in_form.values()
            I2 = self.in2_form.values()
        except Exception:
            return
        op = osim.OpAmp(self._model_key(), vcc)
        f = max(I["f"], 1e-3)
        v1 = osim.source(self.wave.get(), I["amp"], f, I["off"])
        v2 = osim.source(self.wave2.get(), I2["amp"], max(I2["f"], 1e-3), I2["off"])
        try:
            if key in ("inv", "noninv", "buffer", "sum", "diff"):
                r = osim.amplifier(key, P, op, v1, v2 if key in ("sum", "diff") else None, f, periods=3)
            elif key == "int":
                r = osim.integrator(P, op, v1, f)
            elif key == "der":
                r = osim.differentiator(P, op, v1, f)
            elif key == "cmp":
                r = osim.comparator(P, op, v1, f)
            elif key == "st_inv":
                r = osim.schmitt(P, op, v1, f, inverting=True)
            elif key == "st_non":
                r = osim.schmitt(P, op, v1, f, inverting=False)
            elif key == "peak":
                r = osim.peak_detector(P, op, v1, f)
            elif key == "rect":
                r = osim.precision_rectifier(P, op, v1, f)
            elif key == "relax":
                r = osim.relaxation(P, op)
            elif key == "sqtri":
                r = osim.square_triangle(P, op)
            elif key == "wien":
                r = osim.wien(P, op, stabilise=self.stab.get())
        except (ZeroDivisionError, ValueError, OverflowError):
            return
        self._metrics(key, r, P, op, I, f)
        self._plot(key, r, op)
        self._draw(key, P)

    # ------------------------------------------------------------------
    def _set_tiles(self, items):
        for (k, _), (cap, val, warn) in zip([("a", 0), ("b", 0), ("c", 0), ("d", 0)], items):
            self.tiles.tiles[k].cap.configure(text=cap)
            self.tiles.set(k, val, warn)

    def _metrics(self, key, r, P, op, I, f):
        vo = r["vout"]
        n = len(vo)
        last = vo[n // 3:]
        pk = float(np.max(np.abs(last)))
        rails = pk >= min(op.vmax, -op.vmin) * 0.999
        if key in ("inv", "noninv", "buffer", "sum", "diff"):
            if key == "inv":
                g = f"−{P['rf'] / P['rin']:.3g}"
            elif key == "noninv":
                g = f"{1 + P['rf'] / P['rg']:.3g}"
            elif key == "buffer":
                g = "1"
            elif key == "sum":
                g = f"−{P['rf'] / P['r1']:.3g}·V1 −{P['rf'] / P['r2']:.3g}·V2"
            else:
                g = f"{P['r2'] / P['r1']:.3g}·(V2 − V1)"
            ideal = r["ideal"]
            err = float(np.max(np.abs(ideal[n // 3:] - last)))
            bw = (op.gbw / r["noise_gain"]) if op.gbw else None
            slew_need = float(np.max(np.abs(np.diff(ideal)))) / (r["t"][1] - r["t"][0])
            if rails:
                st, w = t("oa.t.clip"), True
            elif op.sr and slew_need > op.sr * 1.05 and err > 0.05 * max(pk, 1e-3):
                st, w = t("oa.t.slew"), True
            elif bw and f > bw * 0.5 and err > 0.05 * max(pk, 1e-3):
                st, w = t("oa.t.bwlim"), True
            else:
                st, w = t("oa.t.ok"), False
            self._set_tiles([(t("oa.t.gain"), g, False), (t("oa.t.vpk"), eng(pk, "V"), rails),
                             (t("oa.t.bw"), eng(bw, "Hz") if bw else "∞", False), (t("oa.t.status"), st, w)])
        elif key == "int":
            f0 = 1 / (2 * math.pi * P["r"] * P["c"])
            slope = I["amp"] / (P["r"] * P["c"])
            dcg = f"−{P['rf'] / P['r']:.3g}" if P.get("rf") else "∞"
            self._set_tiles([(t("oa.t.f0"), eng(f0, "Hz"), False), (t("oa.t.slope"), eng(slope / 1e3, "V/ms"), False),
                             (t("oa.t.vpk"), eng(pk, "V"), rails), (t("oa.t.dcg"), dcg, False)])
        elif key == "der":
            gf = 2 * math.pi * f * P["rf"] * P["c"]
            fc = 1 / (2 * math.pi * max(P["rin"], 1) * P["c"])
            self._set_tiles([(t("oa.t.gf"), f"{gf:.3g}", False), (t("oa.t.fc"), eng(fc, "Hz"), False),
                             (t("oa.t.vpk"), eng(pk, "V"), rails),
                             (t("oa.t.status"), t("oa.t.clip") if rails else t("oa.t.ok"), rails)])
        elif key in ("cmp", "st_inv", "st_non"):
            ut, lt = r["ut"], r["lt"]
            self._set_tiles([(t("oa.t.ut"), eng(ut, "V"), False), (t("oa.t.lt"), eng(lt, "V"), False),
                             (t("oa.t.hyst"), eng(ut - lt, "V"), False),
                             (t("oa.t.swing"), f"{op.vmin:+.2f} … {op.vmax:+.2f} V", False)])
        elif key == "peak":
            tau = P["r"] * P["c"]
            held = float(np.max(last))
            droop = held * (1 - math.exp(-1 / (f * tau))) if tau > 0 else 0
            self._set_tiles([(t("oa.t.held"), eng(held, "V"), False), (t("oa.t.droop"), eng(droop, "V"), False),
                             (t("oa.t.tau"), eng(tau, "s"), False),
                             (t("oa.t.err"), eng(float(np.max(r["vin"])) - held, "V"), False)])
        elif key == "rect":
            vin_pk = float(np.max(r["vin"]))
            self._set_tiles([(t("oa.t.vpk"), eng(pk, "V"), False), (tr("Vin peak", "Vin vârf"), eng(vin_pk, "V"), False),
                             (t("oa.t.err"), eng(vin_pk - pk, "V"), vin_pk - pk > 0.05 * max(vin_pk, 1e-3)),
                             (t("oa.t.swing"), eng(float(np.min(r["vop"])), "V"), False)])
        else:
            fth, fm = r["f_th"], r.get("f_meas")
            amp = float(np.max(np.abs(vo[n // 2:])))
            third = (t("oa.t.tri"), eng(r["tri_amp"], "V"), False) if key == "sqtri" else \
                (t("oa.t.loop"), f"{r['gain']:.3g}", abs(r["gain"] - 3) > 0.5) if key == "wien" else \
                (t("oa.t.ut"), f"±{eng(r['ut'], 'V')}", False)
            self._set_tiles([(t("oa.t.fth"), eng(fth, "Hz"), False),
                             (t("oa.t.fsim"), eng(fm, "Hz") if fm else "–", False),
                             (t("oa.t.amp"), eng(amp, "V"), False), third])

    # ------------------------------------------------------------------
    def _plot(self, key, r, op):
        fig = self.chart.fig
        fig.clear()
        gs = GridSpec(1, 2, figure=fig, width_ratios=[2.4, 1], wspace=0.28)
        ax = fig.add_subplot(gs[0])
        xy = fig.add_subplot(gs[1])
        tm = r["t"] * 1e3
        if key in OSC:
            if key == "relax":
                ax.plot(tm, r["vc"], color=C_AUX, lw=1.6, label="Vc")
                ax.axhline(r["ut"], color="#999", ls=":", lw=1)
                ax.axhline(r["lt"], color="#999", ls=":", lw=1)
                xy.plot(r["vc"], r["vout"], color=C_OUT, lw=1.2)
                xy.set_xlabel("Vc", fontsize=8)
            elif key == "sqtri":
                ax.plot(tm, r["vtri"], color=C_AUX, lw=1.8, label=tr("triangle", "triunghi"))
                xy.plot(r["vtri"], r["vout"], color=C_OUT, lw=1.2)
                xy.set_xlabel(tr("V triangle", "V triunghi"), fontsize=8)
            else:
                ax.plot(tm, r["vplus"], color=C_AUX, lw=1.2, label="V(+)")
                n = len(tm)
                xy.plot(r["vplus"][n // 2:], r["vout"][n // 2:], color=C_OUT, lw=1.2)
                xy.set_xlabel("V(+)", fontsize=8)
            ax.plot(tm, r["vout"], color=C_OUT, lw=1.8, label="Vout")
            xy.set_title(t("oa.xy.osc"), fontsize=9)
        else:
            ax.plot(tm, r["vin"], color=C_IN, lw=1.4, label="Vin" if key not in ("sum", "diff") else "V1")
            if r.get("vin2") is not None:
                ax.plot(tm, r["vin2"], color=C_IN2, lw=1.2, label="V2")
            if key in ("st_inv", "st_non", "cmp"):
                ax.axhline(r["ut"], color="#999", ls=":", lw=1)
                ax.axhline(r["lt"], color="#999", ls=":", lw=1)
                ax.text(tm[-1], r["ut"], " UT", fontsize=7, color="#666", va="bottom", ha="right")
                if key != "cmp":
                    ax.text(tm[-1], r["lt"], " LT", fontsize=7, color="#666", va="top", ha="right")
            if key in ("peak", "rect"):
                ax.plot(tm, r["vop"], color="#999", lw=1, ls="--", label=t("oa.op_out"))
            if "ideal" in r and key != "buffer":
                clip = np.any(np.abs(r["ideal"] - r["vout"]) > 1e-3)
                if clip:
                    ax.plot(tm, r["ideal"], color=C_OUT, lw=0.9, ls=":", alpha=0.7, label=t("oa.ideal_out"))
            ax.plot(tm, r["vout"], color=C_OUT, lw=1.8, label="Vout")
            n = len(tm)
            xin = r["vin"] if key != "diff" else (r["vin2"] - r["vin"])
            xy.plot(xin[n // 4:], r["vout"][n // 4:], color=C_OUT, lw=1.3)
            xy.set_xlabel("Vin" if key != "diff" else "V2 − V1", fontsize=8)
            xy.set_title(t("oa.xy"), fontsize=9)
        span = max(float(np.max(np.abs(r["vout"]))), float(np.max(np.abs(r.get("vin", r["vout"])))), 1e-3)
        near_rail = span > 0.6 * min(op.vmax, -op.vmin)
        for a in (ax, xy):
            a.set_facecolor(PLOT_BG)
            a.grid(True, alpha=0.25)
            a.tick_params(labelsize=7)
            if near_rail:
                a.axhline(op.vmax, color="#c62828", lw=0.7, ls="--", alpha=0.5)
                a.axhline(op.vmin, color="#c62828", lw=0.7, ls="--", alpha=0.5)
        xy.set_ylabel("Vout", fontsize=8)
        ax.set_xlabel(t("oa.ax.t"), fontsize=8)
        ax.set_ylabel(t("oa.ax.v"), fontsize=8)
        ax.legend(fontsize=7, loc="upper right", ncol=4)
        fig.subplots_adjust(left=0.08, right=0.98, top=0.9, bottom=0.14)
        self.chart.redraw()

    # ------------------------------------------------------------------
    def _draw(self, key, P):
        cv = self.canvas
        cv.delete("all")
        cx, cy = 280, 140
        inv_y, non_y = cy - 14, cy + 14
        in_x = cx - 48          # end of the input stubs
        out_x = cx + 48
        W = 540

        def val(k, unit):
            try:
                return eng(P[k], unit)
            except Exception:
                return None

        def opamp(x=cx, y=cy, s=1.0):
            sym.opamp(cv, x, y, s=s, supplies=True)

        def out_line(xn=360, xt=500, y=cy, label="Vout"):
            sym.wire(cv, out_x, y, xt, y)
            sym.node(cv, xn, y)
            sym.terminal(cv, xt, y, label=label)

        def fb_top(x0, comp="r", key_="rf", label="Rf", y=70):
            sym.wire(cv, x0, inv_y, x0, y)
            if comp == "r":
                sym.resistor(cv, x0, y, 360, y, label=label, value=val(key_, "Ω"))
            else:
                sym.capacitor(cv, x0, y, 360, y, label=label, value=val(key_, "F"))
            sym.wire(cv, 360, y, 360, cy)
            sym.node(cv, x0, inv_y)

        def gnd_plus(x=215):
            sym.wire(cv, in_x, non_y, x, non_y, x, 210)
            sym.ground(cv, x, 210)

        if key in ("inv", "int", "der", "sum"):
            opamp()
            out_line()
            sym.wire(cv, 190, inv_y, in_x, inv_y)
            if key == "sum":
                sym.terminal(cv, 30, 90, label="V1")
                sym.resistor(cv, 30, 90, 150, 90, label="R1", value=val("r1", "Ω"))
                sym.wire(cv, 150, 90, 190, 90, 190, inv_y)
                sym.terminal(cv, 30, 175, label="V2", anchor="n", dy=8)
                sym.resistor(cv, 30, 175, 150, 175, label="R2", value=val("r2", "Ω"), label_side=1)
                sym.wire(cv, 150, 175, 175, 175, 175, inv_y + 0.01)
                sym.wire(cv, 175, inv_y, 190, inv_y)
                sym.node(cv, 175, inv_y)
                gnd_plus(215)
            else:
                sym.terminal(cv, 30, inv_y, label="Vin")
                if key == "der":
                    sym.resistor(cv, 30, inv_y, 105, inv_y, label="Rin", value=val("rin", "Ω"))
                    sym.capacitor(cv, 105, inv_y, 190, inv_y, label="C", value=val("c", "F"))
                elif key == "int":
                    sym.resistor(cv, 30, inv_y, 190, inv_y, label="R", value=val("r", "Ω"))
                else:
                    sym.resistor(cv, 30, inv_y, 190, inv_y, label="Rin", value=val("rin", "Ω"))
                gnd_plus(215)
            if key == "int":
                fb_top(190, "c", "c", "C", y=80)
                if P.get("rf"):
                    sym.wire(cv, 190, 80, 190, 24)
                    sym.resistor(cv, 190, 24, 360, 24)
                    cv.create_text(366, 24, text=f"Rf {val('rf', 'Ω')}", anchor="w", font=("Segoe UI", 8),
                                   fill=sym.VALUE_COLOR)
                    sym.wire(cv, 360, 24, 360, 80)
                    sym.node(cv, 190, 80)
                    sym.node(cv, 360, 80)
            else:
                fb_top(190, "r", "rf", "Rf")
        elif key == "noninv":
            opamp()
            out_line()
            sym.terminal(cv, 30, non_y, label="Vin", anchor="n", dy=8)
            sym.wire(cv, 30, non_y, in_x, non_y)
            sym.wire(cv, 200, inv_y, in_x, inv_y)
            sym.resistor(cv, 200, inv_y, 200, 240, label="Rg", value=val("rg", "Ω"), label_side=-1)
            sym.ground(cv, 200, 240)
            fb_top(200, "r", "rf", "Rf")
        elif key == "buffer":
            opamp()
            out_line()
            sym.terminal(cv, 30, non_y, label="Vin", anchor="n", dy=8)
            sym.wire(cv, 30, non_y, in_x, non_y)
            sym.wire(cv, in_x, inv_y, 200, inv_y, 200, 70, 360, 70, 360, cy)
        elif key == "diff":
            opamp()
            out_line()
            sym.terminal(cv, 30, inv_y, label="V1")
            sym.resistor(cv, 30, inv_y, 170, inv_y, label="R1", value=val("r1", "Ω"))
            sym.wire(cv, 170, inv_y, in_x, inv_y)
            fb_top(190, "r", "r2", "R2")
            sym.terminal(cv, 30, 195, label="V2", anchor="n", dy=8)
            sym.resistor(cv, 30, 195, 170, 195, label="R3 = R1", label_side=1)
            sym.wire(cv, 170, 195, 210, 195, 210, non_y, in_x, non_y)
            sym.node(cv, 210, 195)
            sym.resistor(cv, 210, 195, 210, 262, label="R4 = R2", label_side=1)
            sym.ground(cv, 210, 262)
        elif key in ("cmp", "st_inv", "st_non"):
            opamp()
            out_line()
            if key == "cmp":
                sym.terminal(cv, 30, non_y, label="Vin", anchor="n", dy=8)
                sym.wire(cv, 30, non_y, in_x, non_y)
                sym.wire(cv, in_x, inv_y, 170, inv_y)
                sym.terminal(cv, 170, inv_y, label=f"Vref = {val('vref', 'V')}")
            elif key == "st_inv":
                sym.terminal(cv, 30, inv_y, label="Vin")
                sym.wire(cv, 30, inv_y, in_x, inv_y)
                sym.wire(cv, in_x, non_y, 215, non_y, 215, 190)
                sym.node(cv, 215, 190)
                sym.resistor(cv, 215, 190, 360, 190, label="R2", value=val("r2", "Ω"), label_side=1)
                sym.wire(cv, 360, 190, 360, cy)
                sym.resistor(cv, 215, 190, 110, 190, label="R1", value=val("r1", "Ω"), label_side=1)
                sym.terminal(cv, 110, 190, label=f"Vref {val('vref', 'V')}", anchor="n", dy=8)
            else:
                sym.terminal(cv, 30, non_y, label="Vin", anchor="n", dy=8)
                sym.resistor(cv, 30, non_y, 180, non_y, label="R1", value=val("r1", "Ω"), label_side=1)
                sym.wire(cv, 180, non_y, in_x, non_y)
                sym.node(cv, 205, non_y)
                sym.wire(cv, 205, non_y, 205, 215)
                sym.resistor(cv, 205, 215, 360, 215, label="R2", value=val("r2", "Ω"), label_side=1)
                sym.wire(cv, 360, 215, 360, cy)
                sym.wire(cv, in_x, inv_y, 170, inv_y)
                sym.terminal(cv, 170, inv_y, label=f"Vref = {val('vref', 'V')}")
        elif key in ("peak", "rect"):
            opamp()
            sym.terminal(cv, 30, non_y, label="Vin", anchor="n", dy=8)
            sym.wire(cv, 30, non_y, in_x, non_y)
            sym.diode(cv, out_x, cy, 400, cy, label="D")
            sym.wire(cv, 400, cy, 510, cy)
            sym.node(cv, 420, cy)
            sym.terminal(cv, 510, cy, label="Vout")
            sym.wire(cv, in_x, inv_y, 200, inv_y, 200, 60, 420, 60, 420, cy)
            if key == "peak":
                sym.capacitor(cv, 420, cy, 420, 240, label="C", value=val("c", "F"), label_side=-1)
                sym.resistor(cv, 470, cy, 470, 240, label="R", value=val("r", "Ω"), label_side=1)
                sym.node(cv, 470, cy)
                sym.wire(cv, 420, 240, 470, 240)
                sym.ground(cv, 445, 240)
            else:
                sym.resistor(cv, 460, cy, 460, 240, label="RL", label_side=1)
                sym.node(cv, 460, cy)
                sym.ground(cv, 460, 240)
        elif key == "relax":
            opamp()
            out_line()
            sym.wire(cv, 120, inv_y, in_x, inv_y)
            sym.node(cv, 120, inv_y)
            sym.capacitor(cv, 120, inv_y, 120, 250, label="C", value=val("c", "F"), label_side=-1)
            sym.ground(cv, 120, 250)
            sym.wire(cv, 120, inv_y, 120, 70)
            sym.resistor(cv, 120, 70, 360, 70, label="R", value=val("r", "Ω"))
            sym.wire(cv, 360, 70, 360, cy)
            sym.wire(cv, in_x, non_y, 215, non_y, 215, 185)
            sym.node(cv, 215, 185)
            sym.resistor(cv, 215, 185, 360, 185, label="R2", value=val("r2", "Ω"), label_side=1)
            sym.wire(cv, 360, 185, 360, cy)
            sym.resistor(cv, 215, 185, 215, 255, label="R1", value=val("r1", "Ω"), label_side=-1)
            sym.ground(cv, 215, 255)
        elif key == "sqtri":
            s = 0.8
            a1x, a2x, y = 150, 380, 150
            sym.opamp(cv, a1x, y, s=s)
            sym.opamp(cv, a2x, y, s=s)
            i1 = (a1x - 38.4, y - 11.2)
            p1 = (a1x - 38.4, y + 11.2)
            o1 = (a1x + 38.4, y)
            i2 = (a2x - 38.4, y - 11.2)
            p2 = (a2x - 38.4, y + 11.2)
            o2 = (a2x + 38.4, y)
            # A1 (-) to 0 V
            sym.wire(cv, i1[0], i1[1], 95, i1[1])
            sym.terminal(cv, 95, i1[1], label="0 V")
            # square node
            sym.wire(cv, o1[0], o1[1], 215, y)
            sym.node(cv, 215, y)
            cv.create_text(215, y + 14, text=tr("square", "dreptunghi"), font=("Segoe UI", 8, "bold"), fill=C_OUT)
            sym.resistor(cv, 215, y, 300, y, label="R", value=val("r", "Ω"))
            sym.wire(cv, 300, y, 300, i2[1], i2[0], i2[1])
            sym.node(cv, 300, i2[1])
            sym.wire(cv, 300, i2[1], 300, 80)
            sym.capacitor(cv, 300, 80, 450, 80, label="C", value=val("c", "F"))
            sym.wire(cv, 450, 80, 450, y)
            sym.wire(cv, p2[0], p2[1], 325, p2[1], 325, 200)
            sym.ground(cv, 325, 200)
            sym.wire(cv, o2[0], o2[1], 505, y)
            sym.node(cv, 450, y)
            sym.terminal(cv, 505, y, label=tr("triangle", "triunghi"))
            # R2: square -> A1(+) over the top
            sym.wire(cv, 215, y, 215, 45)
            sym.resistor(cv, 215, 45, 80, 45, label="R2", value=val("r2", "Ω"))
            sym.wire(cv, 80, 45, 80, p1[1], p1[0], p1[1])
            sym.node(cv, 80, p1[1])
            # R1: triangle -> A1(+) along the bottom
            sym.wire(cv, 450, y, 450, 245, 300, 245)
            sym.resistor(cv, 300, 245, 170, 245, label="R1", value=val("r1", "Ω"), label_side=-1)
            sym.wire(cv, 170, 245, 80, 245, 80, p1[1])
            cv.create_text(a1x, y - 40, text="A1 Schmitt", font=("Segoe UI", 8), fill="#666")
            cv.create_text(a2x, y + 40, text="A2 integrator", font=("Segoe UI", 8), fill="#666")
        elif key == "wien":
            ox = 320
            sym.opamp(cv, ox, cy, s=1.0, supplies=True)
            pin, nin, oo = (ox - 48, non_y), (ox - 48, inv_y), (ox + 48, cy)
            sym.wire(cv, oo[0], oo[1], 500, cy)
            sym.node(cv, 440, cy)
            sym.terminal(cv, 500, cy, label="Vout")
            # (-) node, Rf to output (top), Rg to ground (left)
            sym.wire(cv, nin[0], nin[1], 250, inv_y)
            sym.node(cv, 250, inv_y)
            sym.wire(cv, 250, inv_y, 250, 75)
            sym.resistor(cv, 250, 75, 440, 75, label="Rf", value=val("rf", "Ω"))
            sym.wire(cv, 440, 75, 440, cy)
            if self.stab.get():
                sym.wire(cv, 285, 75, 285, 18)
                sym.wire(cv, 405, 75, 405, 18)
                sym.diode(cv, 285, 18, 345, 18, s=0.7)
                sym.diode(cv, 405, 18, 345, 18, s=0.7)
            sym.resistor(cv, 250, inv_y, 150, inv_y, label="Rg", value=val("rg", "Ω"))
            sym.wire(cv, 150, inv_y, 40, inv_y, 40, 255)
            sym.ground(cv, 40, 255)
            # (+) node with parallel R||C to ground and series RC from the output
            sym.wire(cv, pin[0], pin[1], 110, non_y)
            sym.node(cv, 200, non_y)
            sym.node(cv, 150, non_y)
            sym.resistor(cv, 150, non_y, 150, 230, label="R", label_side=1)
            sym.capacitor(cv, 110, non_y, 110, 230, label="C", label_side=-1)
            sym.wire(cv, 110, 230, 150, 230)
            sym.ground(cv, 130, 230)
            sym.wire(cv, 440, cy, 440, 250, 370, 250)
            sym.resistor(cv, 370, 250, 290, 250, label="R", value=val("r", "Ω"), label_side=-1)
            sym.capacitor(cv, 290, 250, 215, 250, label="C", value=val("c", "F"), label_side=-1)
            sym.wire(cv, 215, 250, 200, 250, 200, non_y)
