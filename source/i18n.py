"""
i18n.py - Minimal internationalization system.

Usage:
    from i18n import t, set_language, get_language, on_change
    label = t("common.calculate")   # returns string in the current language

The app uses a "rebuild everything" strategy for language switching: when
set_language() is called, registered listeners (usually "rebuild the whole
notebook") are invoked, so every widget is freshly constructed with t()
calls resolving to the new language. This keeps each tab's code simple —
no need to hunt down and update every live widget's text individually.
"""

_CURRENT_LANG = "en"
_listeners = []


def get_language():
    return _CURRENT_LANG


def set_language(lang):
    global _CURRENT_LANG
    if lang not in ("en", "ro"):
        return
    _CURRENT_LANG = lang
    for cb in list(_listeners):
        cb()


def on_change(callback):
    _listeners.append(callback)


def t(key):
    entry = STRINGS.get(key)
    if entry is None:
        return key
    return entry.get(_CURRENT_LANG, entry.get("en", key))


# ---------------------------------------------------------------------------
# Translation table
# ---------------------------------------------------------------------------
STRINGS = {
    # ---- App shell ---------------------------------------------------
    "app.title": {"en": "⚡  The Electronist's Guide", "ro": "⚡  Ghidul Electronistului"},
    "app.subtitle": {"en": "Interactive calculators & visual theory for electronic components",
                      "ro": "Calculatoare interactive și teorie vizuală pentru componente electronice"},

    "nav.resistors": {"en": "Resistors", "ro": "Rezistoare"},
    "nav.capacitors": {"en": "Capacitors", "ro": "Condensatoare"},
    "nav.inductors": {"en": "Inductors", "ro": "Bobine"},
    "nav.diodes": {"en": "Diodes / LEDs", "ro": "Diode / LED-uri"},
    "nav.transistors": {"en": "Transistors", "ro": "Tranzistoare"},
    "nav.opamps": {"en": "Op-Amps", "ro": "Amplif. Operaționale"},
    "nav.batteries": {"en": "Batteries", "ro": "Baterii"},
    "nav.basics": {"en": "AC/DC Basics", "ro": "Bazele AC/DC"},
    "nav.filters": {"en": "Filters", "ro": "Filtre"},

    # ---- Top-level navigation groups ------------------------------------
    "nav.group.basic_components": {"en": "Basic Components", "ro": "Componente de Bază"},
    "nav.group.signals": {"en": "Signals", "ro": "Semnale"},

    # ---- Common / shared -----------------------------------------------
    "common.learn": {"en": "Learn", "ro": "Teorie"},
    "common.what": {"en": "What it does:", "ro": "Ce face:"},
    "common.how": {"en": "How it works:", "ro": "Cum funcționează:"},
    "common.dc_formulas": {"en": "⎓ DC formulas:", "ro": "⎓ Formule DC:"},
    "common.ac_formulas": {"en": "∿ AC formulas:", "ro": "∿ Formule AC:"},
    "common.key_formulas": {"en": "Key formulas:", "ro": "Formule cheie:"},
    "common.calculate": {"en": "Calculate", "ro": "Calculează"},
    "common.convert": {"en": "Convert", "ro": "Convertește"},
    "common.simulate": {"en": "▶ Simulate", "ro": "▶ Simulează"},
    "common.mode": {"en": "Mode:", "ro": "Mod:"},
    "common.series": {"en": "Series", "ro": "Serie"},
    "common.parallel": {"en": "Parallel", "ro": "Paralel"},
    "common.show_series": {"en": "Show as Series", "ro": "Arată ca Serie"},
    "common.show_parallel": {"en": "Show as Parallel", "ro": "Arată ca Paralel"},
    "common.series_total": {"en": "Series total", "ro": "Total serie"},
    "common.parallel_total": {"en": "Parallel total", "ro": "Total paralel"},
    "common.could_not_compute": {"en": "Could not compute", "ro": "Nu s-a putut calcula"},
    "common.enter_valid_numbers": {"en": "Enter valid numbers", "ro": "Introduceți numere valide"},
    "common.enter_valid_values": {"en": "Please enter valid numeric values.",
                                   "ro": "Vă rugăm introduceți valori numerice valide."},
    "common.could_not_simulate": {"en": "Could not simulate", "ro": "Nu s-a putut simula"},
    "common.time_constant": {"en": "Time constant", "ro": "Constanta de timp"},
    "common.resistance": {"en": "Resistance", "ro": "Rezistență"},
    "common.frequency": {"en": "Frequency (Hz)", "ro": "Frecvență (Hz)"},
    "common.voltage": {"en": "Voltage (V)", "ro": "Tensiune (V)"},
    "common.time_s": {"en": "Time (s)", "ro": "Timp (s)"},

    # ---- Language button ------------------------------------------------
    "lang.tooltip": {"en": "Language", "ro": "Limbă"},

    # ---- Theory: Resistor -------------------------------------------------
    "theory.resistor.title": {"en": "Resistors", "ro": "Rezistoare"},
    "theory.resistor.what": {
        "en": ("A resistor opposes the flow of electric current, converting electrical "
               "energy into heat. It's used to limit current, divide voltage, and set "
               "bias points in circuits."),
        "ro": ("Un rezistor se opune trecerii curentului electric, transformând energia "
               "electrică în căldură. Este folosit pentru a limita curentul, a diviza "
               "tensiunea și a stabili puncte de polarizare în circuite."),
    },
    "theory.resistor.how": {
        "en": ("Inside, a resistive material (carbon film, metal film, or wirewound) "
               "restricts electron flow. The more resistive the material and the longer/"
               "thinner it is, the higher the resistance (R = ρL/A). Two resistors in "
               "series form a voltage divider: connecting a load across the output "
               "changes the effective resistance there and therefore changes the output "
               "voltage."),
        "ro": ("În interior, un material rezistiv (peliculă de carbon, peliculă metalică "
               "sau bobinaj) limitează fluxul de electroni. Cu cât materialul este mai "
               "rezistiv și mai lung/subțire, cu atât rezistența este mai mare (R = ρL/A). "
               "Două rezistențe în serie formează un divizor de tensiune: conectarea unei "
               "sarcini la ieșire modifică rezistența efectivă din acel punct și, "
               "implicit, tensiunea de ieșire."),
    },
    "theory.capacitor.title": {"en": "Capacitors", "ro": "Condensatoare"},
    "theory.capacitor.what": {
        "en": ("A capacitor stores electrical energy in an electric field between two "
               "conductive plates separated by an insulator (dielectric). An ideal "
               "capacitor blocks steady-state DC current after it has charged, while "
               "allowing AC signals to pass with an impedance that decreases as "
               "frequency increases. During transients, a capacitor can carry current "
               "while its voltage is changing."),
        "ro": ("Un condensator stochează energie electrică într-un câmp electric între "
               "două plăci conductoare separate de un izolator (dielectric). Un "
               "condensator ideal blochează curentul DC în regim staționar după "
               "încărcare, în timp ce permite trecerea semnalelor AC printr-o impedanță "
               "care scade odată cu creșterea frecvenței. În regim tranzitoriu, "
               "condensatorul poate conduce curent cât timp tensiunea sa se modifică."),
    },
    "theory.capacitor.how": {
        "en": ("When voltage is applied, charge accumulates on the plates. Ceramic caps "
               "use a ceramic dielectric and are non-polarized; electrolytic caps use a "
               "chemical electrolyte, giving higher capacitance in a smaller size but "
               "requiring correct polarity. The capacitor current is proportional to the "
               "rate of change of voltage (iC = C·dv/dt); for a first-order RC circuit "
               "the time constant τ = RC sets how fast it charges, and after one time "
               "constant a charging capacitor reaches about 63.2% of its final voltage."),
        "ro": ("Când se aplică tensiune, sarcina se acumulează pe plăci. Condensatoarele "
               "ceramice folosesc un dielectric ceramic și nu sunt polarizate; cele "
               "electrolitice folosesc un electrolit chimic, oferind o capacitate mai "
               "mare într-o dimensiune mai mică, dar necesită polaritate corectă. "
               "Curentul prin condensator este proporțional cu viteza de variație a "
               "tensiunii (iC = C·dv/dt); pentru un circuit RC de ordinul întâi, "
               "constanta de timp τ = RC determină cât de repede se încarcă, iar după o "
               "constantă de timp condensatorul ajunge la aproximativ 63,2% din tensiunea "
               "finală."),
    },
    "theory.inductor.title": {"en": "Inductors", "ro": "Bobine"},
    "theory.inductor.what": {
        "en": ("An inductor stores energy in a magnetic field when current flows through "
               "a coil of wire. An ideal inductor opposes changes in current (not the "
               "current itself), making it useful for filtering, energy storage, and "
               "transformers."),
        "ro": ("O bobină stochează energie într-un câmp magnetic atunci când curentul "
               "trece printr-o înfășurare de sârmă. O bobină ideală se opune variațiilor "
               "curentului (nu curentului în sine), fiind utilă pentru filtrare, "
               "stocarea energiei și transformatoare."),
    },
    "theory.inductor.how": {
        "en": ("Current through the coil creates a magnetic field. Any change in current "
               "induces a voltage (back-EMF) that opposes the change — this property is "
               "called self-inductance, measured in Henrys (H). In a first-order RL "
               "circuit the time constant τ = L/R sets how quickly current rises or "
               "falls. Real transformers have losses, so Pin is only approximately "
               "equal to Pout."),
        "ro": ("Curentul prin bobină creează un câmp magnetic. Orice variație a curentului "
               "induce o tensiune (tensiune electromotoare indusă) care se opune "
               "variației — această proprietate se numește autoinductanță, măsurată în "
               "Henry (H). Într-un circuit RL de ordinul întâi, constanta de timp τ = L/R "
               "determină cât de repede crește sau scade curentul. Transformatoarele "
               "reale au pierderi, așa că Pin este doar aproximativ egal cu Pout."),
    },
    "theory.diode.title": {"en": "Diodes & LEDs", "ro": "Diode & LED-uri"},
    "theory.diode.what": {
        "en": ("A diode allows current to flow in one direction only. LEDs (Light "
               "Emitting Diodes) additionally emit light when forward biased. A "
               "silicon PN diode commonly has a forward voltage around 0.6–0.7 V at "
               "moderate current, but Vf depends strongly on diode type, current and "
               "temperature — it is not a universal constant."),
        "ro": ("O diodă permite curentului să circule într-o singură direcție. LED-urile "
               "(diode electroluminiscente) emit în plus lumină atunci când sunt "
               "polarizate direct. O diodă PN din siliciu are în mod obișnuit o "
               "tensiune directă de aproximativ 0,6–0,7 V la curenți moderați, dar Vf "
               "depinde puternic de tipul diodei, curent și temperatură — nu este o "
               "constantă universală."),
    },
    "theory.diode.how": {
        "en": ("A diode is a P-N junction, modeled by the Shockley diode equation "
               "ID = IS·(exp(VD/(n·VT)) − 1), where IS is the saturation current, n is "
               "the ideality factor, and VT is the thermal voltage (VT ≈ 25.85 mV at "
               "25°C). Forward bias above threshold makes it conduct; reverse bias "
               "blocks current (until breakdown, exploited by Zener diodes for voltage "
               "regulation). The simulator in this app uses a simplified educational "
               "version of this model."),
        "ro": ("O diodă este o joncțiune P-N, modelată prin ecuația lui Shockley "
               "ID = IS·(exp(VD/(n·VT)) − 1), unde IS este curentul de saturație, n "
               "este factorul de idealitate, iar VT este tensiunea termică "
               "(VT ≈ 25,85 mV la 25°C). Polarizarea directă peste prag o face să "
               "conducă; polarizarea inversă blochează curentul (până la străpungere, "
               "fenomen exploatat de diodele Zener pentru reglarea tensiunii). "
               "Simulatorul din această aplicație folosește o versiune educațională "
               "simplificată a acestui model."),
    },
    "theory.transistor.title": {"en": "Transistors", "ro": "Tranzistoare"},
    "theory.transistor.what": {
        "en": ("A transistor is a semiconductor device used to amplify or switch "
               "electronic signals. BJTs are current-controlled; MOSFETs are "
               "voltage-controlled. A BJT has four operating regions: cutoff (both "
               "junctions reverse biased, no conduction), forward active (base-emitter "
               "forward biased, base-collector reverse biased — the amplifying region), "
               "saturation (both junctions forward biased, transistor acts like a "
               "closed switch), and reverse active (roles of emitter/collector "
               "swapped, rarely used, much lower gain)."),
        "ro": ("Un tranzistor este un dispozitiv semiconductor folosit pentru a amplifica "
               "sau comuta semnale electronice. Tranzistoarele bipolare (BJT) sunt "
               "controlate prin curent; MOSFET-urile sunt controlate prin tensiune. Un "
               "BJT are patru regiuni de funcționare: blocare (ambele joncțiuni "
               "polarizate invers, fără conducție), activă directă (joncțiunea "
               "bază-emitor polarizată direct, baza-colector polarizată invers — "
               "regiunea de amplificare), saturație (ambele joncțiuni polarizate "
               "direct, tranzistorul se comportă ca un întrerupător închis) și activă "
               "inversă (rolurile emitorului și colectorului sunt schimbate, rar "
               "folosită, amplificare mult mai mică)."),
    },
    "theory.transistor.how": {
        "en": ("In a BJT, a small base current controls a much larger collector current "
               "(current gain, β / hFE): IC ≈ β·IB is a simplified forward-active model "
               "and is not universally valid — it does not hold in saturation, where "
               "IC is instead limited by the external circuit (VCE drops to VCE(sat)). "
               "The common-emitter current gain α relates to β by α = β/(β+1), giving "
               "IC ≈ α·IE. In a MOSFET, a voltage on the gate creates a conductive "
               "channel between drain and source."),
        "ro": ("Într-un BJT, un curent mic de bază controlează un curent de colector mult "
               "mai mare (amplificare de curent, β / hFE): IC ≈ β·IB este un model "
               "simplificat valabil în regiunea activă directă și nu este universal "
               "valabil — nu se aplică în saturație, unde IC este limitat de circuitul "
               "extern (VCE scade la VCE(sat)). Amplificarea de curent în bază comună α "
               "se leagă de β prin α = β/(β+1), rezultând IC ≈ α·IE. Într-un MOSFET, o "
               "tensiune pe poartă creează un canal conductor între drenă și sursă."),
    },
    "theory.mosfet.title": {"en": "MOSFETs", "ro": "MOSFET-uri"},
    "theory.mosfet.what": {
        "en": ("A MOSFET (Metal-Oxide-Semiconductor FET) controls current between source "
               "and drain using an electric field from the gate. The gate is "
               "electrically insulated, so its steady-state DC gate current is ideally "
               "zero. During switching, however, current flows temporarily to charge "
               "and discharge the gate capacitances. It's the dominant transistor in "
               "digital logic and power electronics."),
        "ro": ("Un MOSFET (tranzistor cu efect de câmp Metal-Oxid-Semiconductor) controlează "
               "curentul dintre sursă și drenă folosind un câmp electric produs de poartă. "
               "Poarta este izolată electric, astfel încât în regim DC curentul de "
               "poartă este ideal zero. În timpul comutării apare însă curent pentru "
               "încărcarea și descărcarea capacităților porții. Este tranzistorul "
               "dominant în logica digitală și electronica de putere."),
    },
    "theory.mosfet.how": {
        "en": ("A voltage on the gate, insulated from the channel by a thin oxide layer, "
               "attracts charge carriers to form a conductive channel between source and "
               "drain. In enhancement-mode devices (the common type), this channel only "
               "exists once the gate voltage exceeds a threshold, Vth. Overdrive voltage "
               "VOV = VGS − VTH. The device is in cutoff for VGS ≤ VTH; in the "
               "linear/triode region for VDS < VOV (behaves like a voltage-controlled "
               "resistor); and in saturation for VDS ≥ VOV (this app uses ID = "
               "k·(VGS−VTH)², where k = ½·μn·Cox·(W/L) — do not mix this with the "
               "alternative convention ID = ½·K·(VGS−VTH)² where K = μn·Cox·(W/L); the "
               "two 'k'/'K' definitions differ by a factor of 2). Textbooks vary in "
               "calling the resistive region 'linear' or 'triode' — both terms are used "
               "here interchangeably. Real MOSFETs also have non-idealities not modeled "
               "by this simplified equation: on-resistance RDS(on), a body (parasitic) "
               "diode from source to drain, gate capacitance and gate charge that limit "
               "switching speed, transconductance gm describing small-signal gain, "
               "power dissipation (conduction + switching losses), and temperature-"
               "dependent threshold/RDS(on)."),
        "ro": ("O tensiune pe poartă, izolată de canal printr-un strat subțire de oxid, "
               "atrage purtători de sarcină formând un canal conductor între sursă și "
               "drenă. La dispozitivele cu îmbogățire (tipul comun), acest canal există "
               "doar după ce tensiunea de poartă depășește un prag, Vth. Tensiunea de "
               "supraexcitare VOV = VGS − VTH. Dispozitivul este blocat pentru VGS ≤ "
               "VTH; în regiunea liniară/triodă pentru VDS < VOV (se comportă ca un "
               "rezistor controlat în tensiune); și în saturație pentru VDS ≥ VOV "
               "(această aplicație folosește ID = k·(VGS−VTH)², unde k = ½·μn·Cox·(W/L) "
               "— nu amesteca această convenție cu cealaltă, ID = ½·K·(VGS−VTH)² unde K "
               "= μn·Cox·(W/L); cele două definiții 'k'/'K' diferă printr-un factor 2). "
               "Manualele variază în a numi regiunea rezistivă 'liniară' sau 'triodă' — "
               "ambii termeni sunt folosiți aici interschimbabil. MOSFET-urile reale au "
               "și neidealități nemodelate de această ecuație simplificată: rezistență "
               "de conducție RDS(on), o diodă parazită (de corp) de la sursă la drenă, "
               "capacitate de poartă și sarcină de poartă care limitează viteza de "
               "comutație, transconductanța gm ce descrie amplificarea de semnal mic, "
               "putere disipată (pierderi de conducție + comutație) și dependența de "
               "temperatură a pragului/RDS(on)."),
    },
    "theory.jfet.title": {"en": "JFETs", "ro": "JFET-uri"},
    "theory.jfet.what": {
        "en": ("A JFET (Junction FET) controls current through a channel by narrowing it "
               "with a reverse-biased gate-channel junction — no oxide layer, and the "
               "channel is normally ON when Vgs = 0 (unlike enhancement MOSFETs)."),
        "ro": ("Un JFET (tranzistor cu efect de câmp cu joncțiune) controlează curentul "
               "printr-un canal îngustându-l cu o joncțiune poartă-canal polarizată invers "
               "— fără strat de oxid, iar canalul este în mod normal deschis la Vgs = 0 "
               "(spre deosebire de MOSFET-urile cu îmbogățire)."),
    },
    "theory.jfet.how": {
        "en": ("A reverse-biased gate-channel junction widens the depletion region and "
               "narrows the channel. As VGS approaches the cutoff voltage VP, the "
               "channel is eventually closed and the drain current approaches zero "
               "(ID ≈ 0 at VGS = VP). Separately, increasing VDS can cause pinch-off "
               "near the drain and move the JFET into its saturation region, where "
               "drain current remains approximately constant — this VDS-driven "
               "pinch-off is distinct from VGS-driven cutoff and does NOT mean the "
               "current is zero; a conducting JFET in saturation still carries its "
               "full ID. The channel current follows Shockley's equation "
               "ID = IDSS·(1 − VGS/VP)². In the common self-biased configuration, a "
               "source resistor RS sets VGS = −ID·RS, and VDS = VDD − ID·(RD + RS). "
               "For this simplified model, the operating point is in saturation only "
               "when VDS ≥ VGS − VP; the exact boundary/model depends on the adopted "
               "device model."),
        "ro": ("O joncțiune poartă-canal polarizată invers lărgește regiunea de golire și "
               "îngustează canalul. Pe măsură ce VGS se apropie de tensiunea de blocare "
               "VP, canalul se închide, iar curentul de drenă se apropie de zero "
               "(ID ≈ 0 la VGS = VP). Separat, creșterea lui VDS poate produce pinch-off "
               "în apropierea drenei și poate introduce JFET-ul în regiunea de "
               "saturație, unde curentul de drenă rămâne aproximativ constant — acest "
               "pinch-off produs de VDS este distinct de blocarea produsă de VGS și NU "
               "înseamnă că, curentul este zero; un JFET aflat în conducție, în "
               "saturație, conduce în continuare curentul ID complet. Curentul prin "
               "canal urmează ecuația lui Shockley ID = IDSS·(1 − VGS/VP)². În "
               "configurația uzuală cu autopolarizare, un rezistor de sursă RS "
               "stabilește VGS = −ID·RS, iar VDS = VDD − ID·(RD + RS). Pentru acest "
               "model simplificat, punctul de funcționare este în saturație doar când "
               "VDS ≥ VGS − VP; granița/modelul exact depinde de modelul de dispozitiv "
               "adoptat."),
    },
    "theory.opamp.title": {"en": "Operational Amplifiers", "ro": "Amplificatoare Operaționale"},
    "theory.opamp.what": {
        "en": ("An op-amp is a high-gain differential amplifier used to perform "
               "amplification, filtering, summing, and many other analog signal "
               "processing tasks. Its output can only swing between the positive and "
               "negative supply rails — an ideal calculated output beyond those rails "
               "is not physically achievable; the real output saturates (clips) at "
               "the rail."),
        "ro": ("Un amplificator operațional este un amplificator diferențial cu "
               "amplificare mare, folosit pentru amplificare, filtrare, însumare și "
               "multe alte operații de procesare a semnalelor analogice. Ieșirea sa "
               "poate varia doar între alimentarea pozitivă și cea negativă — o "
               "ieșire ideală calculată dincolo de aceste limite nu este realizabilă "
               "fizic; ieșirea reală saturează (se limitează) la nivelul alimentării."),
    },
    "theory.opamp.how": {
        "en": ("Ideal op-amps draw essentially no input current (I+ ≈ I- ≈ 0) and, "
               "through negative feedback, keep both inputs at nearly the same "
               "voltage (V+ ≈ V-, the 'virtual short' rule). This virtual-short "
               "condition applies only when negative feedback is active and the "
               "op-amp is operating in its linear region — it breaks down in "
               "open-loop or saturated operation. Real op-amps also have limits: "
               "output saturation near the supply rails, a common-mode input range, "
               "a finite slew rate (maximum dV/dt at the output), a gain-bandwidth "
               "product that trades gain for bandwidth, a small input offset voltage, "
               "and a small input bias current."),
        "ro": ("Amplificatoarele operaționale ideale nu consumă practic curent de "
               "intrare (I+ ≈ I- ≈ 0) și, prin reacție negativă, mențin ambele intrări "
               "la aproximativ aceeași tensiune (V+ ≈ V-, regula 'scurtcircuitului "
               "virtual'). Această condiție de scurtcircuit virtual se aplică doar "
               "atunci când reacția negativă este activă și AO funcționează în "
               "regiunea liniară — nu se mai aplică în funcționare în buclă deschisă "
               "sau saturată. AO-urile reale au și limite: saturația ieșirii aproape "
               "de alimentare, un domeniu de tensiune de mod comun, o viteză de "
               "creștere (slew rate) finită (dV/dt maxim la ieșire), un produs "
               "câștig-bandă ce schimbă amplificarea pentru bandă, o mică tensiune de "
               "offset la intrare și un mic curent de polarizare la intrare."),
    },
    "theory.battery.title": {"en": "Batteries & Power Sources", "ro": "Baterii & Surse de Alimentare"},
    "theory.battery.what": {
        "en": ("A battery stores chemical energy and converts it to electrical energy, "
               "supplying a roughly constant DC voltage until depleted."),
        "ro": ("O baterie stochează energie chimică și o transformă în energie electrică, "
               "furnizând o tensiune DC aproximativ constantă până la epuizare."),
    },
    "theory.battery.how": {
        "en": ("Cells combined in series add their voltages (same capacity); cells "
               "combined in parallel add their capacity (same voltage). Stored energy "
               "in watt-hours is EWh = V × Ah, and the ideal runtime is only an "
               "estimate: t ≈ Ah / I. Real battery runtime depends on discharge rate, "
               "internal resistance, temperature, cutoff voltage, battery chemistry "
               "and battery-management limits."),
        "ro": ("Celulele conectate în serie își însumează tensiunile (capacitate "
               "identică); celulele conectate în paralel își însumează capacitatea "
               "(tensiune identică). Energia stocată în wați-oră este EWh = V × Ah, "
               "iar autonomia ideală este doar o estimare: t ≈ Ah / I. Autonomia "
               "reală depinde de rata de descărcare, rezistența internă, temperatură, "
               "tensiunea de cutoff, chimia bateriei și limitele sistemului de "
               "management al bateriei."),
    },
    "theory.basics.title": {"en": "AC / DC Basics", "ro": "Bazele AC / DC"},
    "theory.basics.what": {
        "en": ("DC describes current or voltage with a fixed polarity. It may be "
               "constant or vary with time. AC periodically changes polarity and "
               "commonly has a sinusoidal waveform, described by frequency, "
               "amplitude, and phase."),
        "ro": ("DC descrie un curent sau o tensiune cu polaritate fixă. Valoarea poate "
               "fi constantă sau poate varia în timp. AC își schimbă periodic "
               "polaritatea și are frecvent o formă de undă sinusoidală, descrisă prin "
               "frecvență, amplitudine și fază."),
    },
    "theory.basics.how": {
        "en": ("In AC circuits, resistors, capacitors and inductors combine into "
               "impedance (Z), a complex quantity with magnitude and phase, because "
               "capacitors and inductors react differently to changing signals than to "
               "steady DC."),
        "ro": ("În circuitele AC, rezistoarele, condensatoarele și bobinele se combină "
               "într-o impedanță (Z), o mărime complexă cu modul și fază, deoarece "
               "condensatoarele și bobinele reacționează diferit la semnale variabile "
               "față de curentul continuu constant."),
    },

    # ---- Formula names (short labels) ----------------------------------
    "f.ohms_law": {"en": "Ohm's Law", "ro": "Legea lui Ohm"},
    "f.power": {"en": "Power", "ro": "Putere"},
    "f.series": {"en": "Series", "ro": "Serie"},
    "f.parallel": {"en": "Parallel", "ro": "Paralel"},
    "f.impedance": {"en": "Impedance", "ro": "Impedanță"},
    "f.voltage_current_phase": {"en": "Voltage/current", "ro": "Tensiune/curent"},
    "f.rms_form": {"en": "RMS form", "ro": "Formă RMS"},
    "f.avg_power": {"en": "Average power", "ro": "Putere medie"},
    "f.charge": {"en": "Charge", "ro": "Sarcină electrică"},
    "f.energy_stored": {"en": "Energy stored", "ro": "Energie stocată"},
    "f.cap_current": {"en": "Capacitor current", "ro": "Curent prin condensator"},
    "f.rc_time_constant": {"en": "RC time constant", "ro": "Constanta de timp RC"},
    "f.steady_state": {"en": "Steady state", "ro": "Regim staționar"},
    "f.capacitive_reactance": {"en": "Capacitive reactance", "ro": "Reactanță capacitivă"},
    "f.resonance_lc": {"en": "Resonance (with L)", "ro": "Rezonanță (cu L)"},
    "f.induced_voltage": {"en": "Induced voltage", "ro": "Tensiune indusă"},
    "f.inductive_reactance": {"en": "Inductive reactance", "ro": "Reactanță inductivă"},
    "f.mutual_coupling": {"en": "Mutual coupling", "ro": "Cuplaj mutual"},
    "f.transformer_ratio": {"en": "Transformer ratio", "ro": "Raport de transformare"},
    "f.transformer_current_ratio": {"en": "Transformer current ratio", "ro": "Raport de curent transformator"},
    "f.transformer_power": {"en": "Ideal transformer power", "ro": "Putere transformator ideal"},
    "f.rl_time_constant": {"en": "RL time constant", "ro": "Constanta de timp RL"},
    "f.fwd_voltage_si": {"en": "Forward voltage drop (silicon, typical)", "ro": "Cădere de tensiune directă (siliciu, tipică)"},
    "f.fwd_voltage_schottky": {"en": "Forward voltage drop (Schottky, typical)", "ro": "Cădere de tensiune directă (Schottky, tipică)"},
    "f.led_resistor": {"en": "LED current-limiting resistor", "ro": "Rezistor de limitare curent LED"},
    "f.power_dissipated_r": {"en": "Power dissipated in R", "ro": "Putere disipată pe R"},
    "f.diode_shockley": {"en": "Shockley diode equation", "ro": "Ecuația diodei (Shockley)"},
    "f.diode_thermal_voltage": {"en": "Thermal voltage (25°C)", "ro": "Tensiune termică (25°C)"},
    "f.diode_power": {"en": "Diode power dissipation", "ro": "Putere disipată de diodă"},
    "f.bjt_gain": {"en": "BJT current gain (forward-active, simplified)", "ro": "Amplificare de curent BJT (activă directă, simplificată)"},
    "f.bjt_emitter": {"en": "BJT emitter current (KCL, always true)", "ro": "Curent de emitor BJT (KCL, mereu valabilă)"},
    "f.bjt_alpha": {"en": "Common-base current gain α", "ro": "Amplificare de curent bază comună α"},
    "f.bjt_ic_alpha": {"en": "IC from α", "ro": "IC din α"},
    "f.base_resistor_switch": {"en": "Base resistor (switch)", "ro": "Rezistor de bază (comutare)"},
    "f.mosfet_sat": {"en": "MOSFET (saturation, this app's k convention)", "ro": "MOSFET (saturație, convenția k a aplicației)"},
    "f.mosfet_triode": {"en": "MOSFET (triode/linear region)", "ro": "MOSFET (regiune triodă/liniară)"},
    "f.mosfet_vov": {"en": "Overdrive voltage", "ro": "Tensiune de supraexcitare"},
    "f.mosfet_region": {"en": "Operating region", "ro": "Regiune de funcționare"},
    "f.mosfet_cutoff": {"en": "Cutoff condition", "ro": "Condiție de blocare"},
    "f.jfet_shockley": {"en": "Shockley's equation", "ro": "Ecuația lui Shockley"},
    "f.jfet_pinchoff": {"en": "Cutoff condition (VGS-driven)", "ro": "Condiție de blocare (produsă de VGS)"},
    "f.jfet_selfbias": {"en": "Self-bias relation", "ro": "Relație de auto-polarizare"},
    "f.jfet_vds": {"en": "Drain-source voltage (self-bias)", "ro": "Tensiune drenă-sursă (auto-polarizare)"},
    "f.jfet_saturation": {"en": "Saturation-region condition", "ro": "Condiție regiune de saturație"},
    "f.bjt_vce": {"en": "Collector-emitter voltage", "ro": "Tensiune colector-emitor"},
    "f.bjt_regions": {"en": "Operating regions", "ro": "Regiuni de funcționare"},
    "f.bjt_design_heuristics": {"en": "Design heuristics (textbook guideline, not a law)",
                                 "ro": "Euristici de proiectare (recomandare didactică, nu o lege)"},
    "f.inv_gain": {"en": "Inverting gain", "ro": "Amplificare inversoare"},
    "f.noninv_gain": {"en": "Non-inverting gain", "ro": "Amplificare neinversoare"},
    "f.voltage_follower": {"en": "Voltage follower", "ro": "Repetor de tensiune"},
    "f.ideal_input_current": {"en": "Ideal input current", "ro": "Curent de intrare ideal"},
    "f.virtual_short": {"en": "Virtual short (feedback + linear region)", "ro": "Scurtcircuit virtual (reacție + regiune liniară)"},
    "f.opamp_summing": {"en": "Summing amplifier", "ro": "Amplificator sumator"},
    "f.opamp_integrator": {"en": "Integrator", "ro": "Integrator"},
    "f.opamp_differentiator": {"en": "Differentiator", "ro": "Derivator"},
    "f.series_voltage": {"en": "Series voltage", "ro": "Tensiune serie"},
    "f.parallel_capacity": {"en": "Parallel capacity", "ro": "Capacitate paralel"},
    "f.runtime_estimate": {"en": "Runtime estimate (not guaranteed)", "ro": "Estimare autonomie (fără garanție)"},
    "f.energy_wh": {"en": "Energy stored", "ro": "Energie stocată"},
    "f.crate": {"en": "C-rate", "ro": "Rată C"},
    "f.freq_period": {"en": "Frequency / Period", "ro": "Frecvență / Perioadă"},
    "f.rms_from_peak": {"en": "RMS from peak (sine)", "ro": "RMS din amplitudine (sinus)"},
    "f.resonant_freq_lc": {"en": "Resonant frequency (LC)", "ro": "Frecvență de rezonanță (LC)"},
    "f.resistivity": {"en": "Resistance from geometry", "ro": "Rezistență din geometrie"},
    "f.voltage_divider": {"en": "Voltage divider", "ro": "Divizor de tensiune"},
    "f.divider_ratio": {"en": "Divider ratio", "ro": "Raport divizor"},

    # ---- Formula values that contain English words (need translation) --
    "fv.resistor.ac.impedance": {
        "en": "Z_R = R  (0° phase — purely resistive)",
        "ro": "Z_R = R  (fază 0° — pur rezistiv)"},
    "fv.resistor.ac.phase": {
        "en": "V(t) and I(t) stay in phase",
        "ro": "V(t) și I(t) rămân în fază"},
    "fv.capacitor.dc.steady_state": {
        "en": "Fully charged capacitor = open circuit (I = 0)",
        "ro": "Condensator complet încărcat = circuit deschis (I = 0)"},
    "fv.capacitor.ac.impedance": {
        "en": "Z_C = -jXc  (current leads voltage by 90°)",
        "ro": "Z_C = -jXc  (curentul este defazat înaintea tensiunii cu 90°)"},
    "fv.inductor.dc.steady_state": {
        "en": "Fully energized inductor = short circuit (V = 0)",
        "ro": "Bobină complet energizată = scurtcircuit (V = 0)"},
    "fv.inductor.ac.impedance": {
        "en": "Z_L = +jXL  (voltage leads current by 90°)",
        "ro": "Z_L = +jXL  (tensiunea este defazată înaintea curentului cu 90°)"},
    "fv.battery.runtime": {
        "en": "Hours ≈ Capacity (mAh) / Load current (mA)",
        "ro": "Ore ≈ Capacitate (mAh) / Curent de sarcină (mA)"},
    "fv.battery.crate": {
        "en": "Current = C-rate × Capacity",
        "ro": "Curent = Rată C × Capacitate"},

    # ---- Resistor tab ----------------------------------------------------
    "resistor.tab_title": {"en": "🎯 Resistor Color Code Calculator", "ro": "🎯 Calculator Cod Culori Rezistor"},
    "resistor.subtab.color": {"en": "Color Code", "ro": "Cod Culori"},
    "resistor.subtab.combo": {"en": "Series / Parallel", "ro": "Serie / Paralel"},
    "resistor.subtab.divider": {"en": "Voltage Divider", "ro": "Divizor de Tensiune"},
    "resistor.subtab.chart": {"en": "Chart / Simulate", "ro": "Grafic / Simulare"},
    "resistor.color_to_value": {"en": "Color → Value", "ro": "Culoare → Valoare"},
    "resistor.num_bands": {"en": "Number of bands:", "ro": "Număr de benzi:"},
    "resistor.band.digit1": {"en": "Digit 1", "ro": "Cifra 1"},
    "resistor.band.digit2": {"en": "Digit 2", "ro": "Cifra 2"},
    "resistor.band.digit3": {"en": "Digit 3", "ro": "Cifra 3"},
    "resistor.band.multiplier": {"en": "Multiplier", "ro": "Multiplicator"},
    "resistor.band.tolerance": {"en": "Tolerance", "ro": "Toleranță"},
    "resistor.band.tempco": {"en": "Temp.Co", "ro": "Coef.Temp"},
    "resistor.resistance_prefix": {"en": "Resistance:", "ro": "Rezistență:"},
    "resistor.range_prefix": {"en": "Range:", "ro": "Interval:"},
    "resistor.tempco_prefix": {"en": "Temp. coefficient:", "ro": "Coeficient de temperatură:"},
    "resistor.value_to_color": {"en": "Value → Color", "ro": "Valoare → Culoare"},
    "resistor.enter_resistance": {"en": "Enter resistance (e.g. 4.7k, 220, 1M):",
                                   "ro": "Introduceți rezistența (ex: 4.7k, 220, 1M):"},
    "resistor.invalid_value": {"en": "Please enter a valid value, e.g. 4.7k",
                                "ro": "Introduceți o valoare validă, ex: 4.7k"},
    "resistor.combo_title": {"en": "Series & Parallel Resistor Combinations",
                              "ro": "Combinații Serie și Paralel de Rezistoare"},
    "resistor.combo_instructions": {
        "en": "Enter resistor values separated by commas or spaces\n(e.g. 220, 4.7k, 10k):",
        "ro": "Introduceți valorile rezistoarelor separate prin virgulă sau spațiu\n(ex: 220, 4.7k, 10k):"},
    "resistor.combo_invalid": {"en": "Enter one or more valid resistor values.",
                                "ro": "Introduceți una sau mai multe valori valide de rezistoare."},
    "resistor.chart.title": {"en": "Simulate: Voltage & Current", "ro": "Simulare: Tensiune & Curent"},
    "resistor.chart.dc_field_r": {"en": "Resistance (e.g. 220)", "ro": "Rezistență (ex: 220)"},
    "resistor.chart.dc_field_v": {"en": "DC Voltage (V)", "ro": "Tensiune DC (V)"},
    "resistor.chart.ac_field_amp": {"en": "AC Amplitude (V peak)", "ro": "Amplitudine AC (V vârf)"},
    "resistor.chart.dc_note": {
        "en": "A resistor has no time dynamics on DC — voltage and current jump "
              "instantly to their final values.",
        "ro": "Un rezistor nu are dinamică temporală pe DC — tensiunea și curentul sar "
              "instantaneu la valorile finale."},
    "resistor.chart.ac_note": {
        "en": "V(t) and I(t) stay perfectly in phase — a resistor doesn't shift "
              "phase at any frequency.",
        "ro": "V(t) și I(t) rămân perfect în fază — un rezistor nu defazează semnalul "
              "la nicio frecvență."},

    # ---- Capacitor tab -----------------------------------------------
    "capacitor.tab_title": {"en": "🔋 Capacitor Calculators", "ro": "🔋 Calculatoare Condensator"},
    "capacitor.subtab.ceramic": {"en": "Ceramic (code)", "ro": "Ceramic (cod)"},
    "capacitor.subtab.electro": {"en": "Electrolytic", "ro": "Electrolitic"},
    "capacitor.subtab.reactance": {"en": "Reactance (Xc)", "ro": "Reactanță (Xc)"},
    "capacitor.subtab.combo": {"en": "Series / Parallel", "ro": "Serie / Paralel"},
    "capacitor.subtab.chart": {"en": "Chart / Simulate", "ro": "Grafic / Simulare"},
    "capacitor.enter_code": {"en": "3-digit code (e.g. 104, 223):", "ro": "Cod din 3 cifre (ex: 104, 223):"},
    "capacitor.tolerance_letter": {"en": "Tolerance letter (optional):", "ro": "Literă toleranță (opțional):"},
    "capacitor.enter_valid_code": {"en": "Enter a numeric code, e.g. 104", "ro": "Introduceți un cod numeric, ex: 104"},
    "capacitor.tolerance_word": {"en": "tolerance", "ro": "toleranță"},
    "capacitor.value_uf": {"en": "Capacitance (e.g. 470u, 10u):", "ro": "Capacitate (ex: 470u, 10u):"},
    "capacitor.voltage_rating": {"en": "Voltage rating (V):", "ro": "Tensiune nominală (V):"},
    "capacitor.energy_stored": {"en": "Max energy stored at rated voltage: E = ½CV²",
                                 "ro": "Energie maximă stocată la tensiunea nominală: E = ½CV²"},
    "capacitor.polarity_warning": {
        "en": "⚠ Reversing polarity on an electrolytic capacitor can damage or "
              "even rupture it. Always match + to + and - to -.",
        "ro": "⚠ Inversarea polarității unui condensator electrolitic îl poate deteriora "
              "sau chiar rupe. Respectați întotdeauna + la + și - la -."},
    "capacitor.ac_reactance": {"en": "AC Reactance", "ro": "Reactanță AC"},
    "capacitor.capacitance_100n": {"en": "Capacitance (e.g. 100n):", "ro": "Capacitate (ex: 100n):"},
    "capacitor.calc_xc": {"en": "Calculate Xc", "ro": "Calculează Xc"},
    "capacitor.enter_valid_cf": {"en": "Enter valid capacitance and frequency",
                                 "ro": "Introduceți capacitate și frecvență valide"},
    "capacitor.combo_title": {"en": "Series & Parallel Capacitor Combinations",
                               "ro": "Combinații Serie și Paralel de Condensatoare"},
    "capacitor.combo_instructions": {
        "en": "Enter capacitor values separated by commas or spaces\n(e.g. 100n, 220n, 1u):",
        "ro": "Introduceți valorile condensatoarelor separate prin virgulă sau spațiu\n(ex: 100n, 220n, 1u):"},
    "capacitor.combo_invalid": {"en": "Enter one or more valid capacitance values.",
                                 "ro": "Introduceți una sau mai multe valori valide de capacitate."},
    "capacitor.chart.title": {"en": "Simulate: Charge / Discharge", "ro": "Simulare: Încărcare / Descărcare"},
    "capacitor.chart.dc_field_c": {"en": "Capacitance (e.g. 100u)", "ro": "Capacitate (ex: 100u)"},
    "capacitor.chart.dc_field_r": {"en": "Series Resistance (Ω)", "ro": "Rezistență Serie (Ω)"},
    "capacitor.chart.dc_field_v": {"en": "Source Voltage (V)", "ro": "Tensiune Sursă (V)"},
    "capacitor.chart.ac_field_c": {"en": "Capacitance (e.g. 100n)", "ro": "Capacitate (ex: 100n)"},
    "capacitor.chart.dc_note": {
        "en": "Charging through a resistor: voltage rises and current decays "
              "exponentially, reaching ~63% of final value after one time constant τ. "
              "After 5τ the source is removed and the capacitor discharges back "
              "through the same resistor, with current reversing direction.",
        "ro": "Încărcare printr-un rezistor: tensiunea crește și curentul scade "
              "exponențial, ajungând la ~63% din valoarea finală după o constantă de "
              "timp τ. După 5τ sursa este îndepărtată și condensatorul se descarcă "
              "înapoi prin același rezistor, curentul inversându-și sensul."},
    "capacitor.chart.ac_note": {
        "en": "Current leads voltage by 90° — the capacitor's defining AC behavior.",
        "ro": "Curentul este defazat înaintea tensiunii cu 90° — comportamentul AC "
              "definitoriu al condensatorului."},

    # ---- Inductor tab -----------------------------------------------
    "inductor.tab_title": {"en": "🌀 Inductor & Transformer Calculators",
                            "ro": "🌀 Calculatoare Bobină & Transformator"},
    "inductor.subtab.color": {"en": "Color Code", "ro": "Cod Culori"},
    "inductor.subtab.reactance": {"en": "Reactance", "ro": "Reactanță"},
    "inductor.subtab.coupling": {"en": "Coupling (k)", "ro": "Cuplaj (k)"},
    "inductor.subtab.transformer": {"en": "Transformer", "ro": "Transformator"},
    "inductor.subtab.combo": {"en": "Series / Parallel", "ro": "Serie / Paralel"},
    "inductor.subtab.chart": {"en": "Chart / Simulate", "ro": "Grafic / Simulare"},
    "inductor.color_intro": {
        "en": "Note: not all inductors use color bands — many print the value directly, "
              "or use SMD codes like capacitors. This band system (value in µH) appears "
              "mainly on small molded/axial inductors and RF chokes.",
        "ro": "Notă: nu toate bobinele folosesc benzi colorate — multe au valoarea "
              "imprimată direct, sau folosesc coduri SMD ca la condensatoare. Acest sistem "
              "de benzi (valoare în µH) apare mai ales pe bobine axiale mici turnate și "
              "șocuri RF."},
    "inductor.inductance_prefix": {"en": "Inductance:", "ro": "Inductanță:"},
    "inductor.reactance_ind": {"en": "Inductance (e.g. 10m, 100u):", "ro": "Inductanță (ex: 10m, 100u):"},
    "inductor.calc_xl": {"en": "Calculate XL", "ro": "Calculează XL"},
    "inductor.enter_valid_lf": {"en": "Enter valid inductance and frequency",
                                "ro": "Introduceți inductanță și frecvență valide"},
    "inductor.coupling_intro": {
        "en": "Two coils placed near each other share magnetic flux. The coupling "
              "coefficient k (0 to 1) describes how tightly linked they are (k=1 is "
              "perfect coupling, as in an ideal transformer).",
        "ro": "Două bobine plasate una lângă alta partajează flux magnetic. Coeficientul "
              "de cuplaj k (0 până la 1) descrie cât de strâns sunt legate (k=1 este "
              "cuplaj perfect, ca într-un transformator ideal)."},
    "inductor.l1": {"en": "L1 (e.g. 10m)", "ro": "L1 (ex: 10m)"},
    "inductor.l2": {"en": "L2 (e.g. 10m)", "ro": "L2 (ex: 10m)"},
    "inductor.mutual_m": {"en": "Mutual inductance M (e.g. 5m)", "ro": "Inductanță mutuală M (ex: 5m)"},
    "inductor.calc_k": {"en": "Calculate k", "ro": "Calculează k"},
    "inductor.enter_valid_l1l2m": {"en": "Enter valid L1, L2 and M", "ro": "Introduceți L1, L2 și M valide"},
    "inductor.not_possible": {"en": "(not physically possible — M can't exceed √(L1·L2))",
                               "ro": "(imposibil fizic — M nu poate depăși √(L1·L2))"},
    "inductor.negative_k_note": {
        "en": "(negative k: the winding/dot-convention polarity opposes; |k| still gives the coupling tightness)",
        "ro": "(k negativ: polaritatea înfășurărilor/convenția punctelor se opune; |k| indică în continuare gradul de cuplaj)"},
    "inductor.primary_turns": {"en": "Primary turns Np", "ro": "Spire primar Np"},
    "inductor.secondary_turns": {"en": "Secondary turns Ns", "ro": "Spire secundar Ns"},
    "inductor.primary_voltage": {"en": "Primary voltage Vp (V)", "ro": "Tensiune primar Vp (V)"},
    "inductor.turns_ratio": {"en": "Turns ratio Np:Ns", "ro": "Raport de spire Np:Ns"},
    "inductor.secondary_voltage": {"en": "Secondary voltage Vs", "ro": "Tensiune secundar Vs"},
    "inductor.step_down": {"en": "Step-down transformer", "ro": "Transformator coborâtor"},
    "inductor.step_up": {"en": "Step-up transformer", "ro": "Transformator ridicător"},
    "inductor.step_neutral": {"en": "Neutral transformer", "ro": "Transformator neutru"},
    "inductor.enter_valid_turns": {"en": "Enter valid turns and voltage", "ro": "Introduceți spire și tensiune valide"},
    "inductor.combo_title": {"en": "Series & Parallel Inductor Combinations",
                              "ro": "Combinații Serie și Paralel de Bobine"},
    "inductor.combo_instructions": {
        "en": "Enter inductance values separated by commas or spaces\n"
              "(e.g. 10m, 4.7m, 100u) — assumes no mutual coupling:",
        "ro": "Introduceți valorile inductanțelor separate prin virgulă sau spațiu\n"
              "(ex: 10m, 4.7m, 100u) — se presupune fără cuplaj mutual:"},
    "inductor.combo_invalid": {"en": "Enter one or more valid inductance values.",
                                "ro": "Introduceți una sau mai multe valori valide de inductanță."},
    "inductor.chart.title": {"en": "Simulate: Current Rise", "ro": "Simulare: Creștere Curent"},
    "inductor.chart.dc_field_l": {"en": "Inductance (e.g. 10m)", "ro": "Inductanță (ex: 10m)"},
    "inductor.chart.dc_field_r": {"en": "Series Resistance (Ω)", "ro": "Rezistență Serie (Ω)"},
    "inductor.chart.dc_field_v": {"en": "Source Voltage (V)", "ro": "Tensiune Sursă (V)"},
    "inductor.chart.dc_note": {
        "en": "Current rises exponentially toward V/R while inductor voltage decays, "
              "reaching ~63% after one time constant τ = L/R. After 5τ the source is "
              "removed and the inductor's stored energy drives current through the "
              "same resistor as it decays to zero, with the inductor voltage flipping "
              "sign to sustain the current.",
        "ro": "Curentul crește exponențial spre V/R în timp ce tensiunea bobinei scade, "
              "ajungând la ~63% după o constantă de timp τ = L/R. După 5τ sursa este "
              "îndepărtată, iar energia stocată în bobină menține curentul prin același "
              "rezistor pe măsură ce scade spre zero, tensiunea bobinei schimbându-și "
              "semnul pentru a susține curentul."},
    "inductor.chart.ac_note": {
        "en": "Current lags voltage by 90° — the inductor's defining AC behavior.",
        "ro": "Curentul este defazat în urma tensiunii cu 90° — comportamentul AC "
              "definitoriu al bobinei."},

    # ---- Diode tab -----------------------------------------------
    "diode.tab_title": {"en": "💡 Diode & LED Calculator", "ro": "💡 Calculator Diodă & LED"},
    "diode.subtab.calc": {"en": "LED Resistor Calc", "ro": "Calcul Rezistor LED"},
    "diode.subtab.chart": {"en": "Chart / Simulate", "ro": "Grafic / Simulare"},
    "diode.led_calc_title": {"en": "LED Series-Resistor Calculator", "ro": "Calculator Rezistor Serie LED"},
    "diode.supply_voltage": {"en": "Supply voltage (V)", "ro": "Tensiune alimentare (V)"},
    "diode.forward_voltage": {"en": "LED forward voltage Vf (V)", "ro": "Tensiune directă LED Vf (V)"},
    "diode.desired_current": {"en": "Desired current If (mA)", "ro": "Curent dorit If (mA)"},
    "diode.led_color": {"en": "LED color: ", "ro": "Culoare LED: "},
    "diode.supply_must_exceed": {"en": "Supply voltage must be greater than LED forward voltage.",
                                  "ro": "Tensiunea de alimentare trebuie să fie mai mare decât tensiunea directă a LED-ului."},
    "diode.resistor_result": {"en": "R = (Vs - Vf) / If", "ro": "R = (Vs - Vf) / If"},
    "diode.power_result": {"en": "Power dissipated in resistor", "ro": "Putere disipată în rezistor"},
    "diode.table_title": {"en": "📊 Common diode / LED forward voltages",
                           "ro": "📊 Tensiuni directe uzuale diodă / LED"},
    "diode.table.type": {"en": "Type", "ro": "Tip"},
    "diode.table.vf": {"en": "Typical Vf", "ro": "Vf tipic"},
    "diode.table.use": {"en": "Typical use", "ro": "Utilizare tipică"},
    "diode.type.silicon": {"en": "Silicon", "ro": "Siliciu"},
    "diode.type.germanium": {"en": "Germanium", "ro": "Germaniu"},
    "diode.type.schottky": {"en": "Schottky", "ro": "Schottky"},
    "diode.type.zener": {"en": "Zener", "ro": "Zener"},
    "diode.type.red_led": {"en": "Red LED", "ro": "LED Roșu"},
    "diode.type.green_led": {"en": "Green LED", "ro": "LED Verde"},
    "diode.type.blue_led": {"en": "Blue/White", "ro": "Albastru/Alb"},
    "diode.use.rectification": {"en": "General rectification",
                                 "ro": "Redresare generală"},
    "diode.use.radios": {"en": "Signal detection",
                          "ro": "Detecție semnal"},
    "diode.use.fast_switch": {"en": "Fast switching",
                               "ro": "Comutare rapidă"},
    "diode.use.regulation": {"en": "Voltage regulation", "ro": "Reglare tensiune"},
    "diode.use.indicators": {"en": "Indicators", "ro": "Indicatoare"},
    "diode.use.lighting": {"en": "Indicators, lighting", "ro": "Indicatoare, iluminat"},
    "diode.chart.title": {"en": "Simulate: Diode Behavior", "ro": "Simulare: Comportament Diodă"},
    "diode.chart.dc_field_is": {"en": "Saturation current Is (A)", "ro": "Curent de saturație Is (A)"},
    "diode.chart.dc_field_n": {"en": "Ideality factor n", "ro": "Factor de idealitate n"},
    "diode.chart.ac_field_vf": {"en": "Forward voltage Vf (V)", "ro": "Tensiune directă Vf (V)"},
    "diode.chart.ac_field_amp": {"en": "AC Amplitude (V peak)", "ro": "Amplitudine AC (V vârf)"},
    "diode.chart.ac_field_rload": {"en": "Load Resistance (Ω)", "ro": "Rezistență de Sarcină (Ω)"},
    "diode.chart.dc_title": {"en": "DC Characteristic Curve (I vs V)", "ro": "Curba Caracteristică DC (I vs V)"},
    "diode.chart.dc_xlabel": {"en": "Diode Voltage (V)", "ro": "Tensiune Diodă (V)"},
    "diode.chart.dc_ylabel": {"en": "Diode Current (mA)", "ro": "Curent Diodă (mA)"},
    "diode.chart.dc_note": {
        "en": "This static I-V curve shows how sharply current rises once forward "
              "voltage passes the diode's turn-on threshold, using the Shockley diode "
              "equation ID = IS·(exp(VD/(n·VT)) − 1). This is a simplified educational "
              "model: fixed IS/n, no self-heating, series resistance, or breakdown effects.",
        "ro": "Această curbă statică I-V arată cât de abrupt crește curentul odată ce "
              "tensiunea directă depășește pragul de conducție al diodei, folosind "
              "ecuația lui Shockley ID = IS·(exp(VD/(n·VT)) − 1). Este un model "
              "educațional simplificat: IS/n fixe, fără autoîncălzire, rezistență "
              "serie sau efecte de străpungere."},
    "diode.chart.ac_title": {"en": "Half-Wave Rectification", "ro": "Redresare Monoalternanță"},
    "diode.chart.legend_vin": {"en": "Vin (AC source)", "ro": "Vin (sursă AC)"},
    "diode.chart.legend_vout": {"en": "Vout (rectified)", "ro": "Vout (redresat)"},
    "diode.chart.ac_note": {
        "en": "The diode only conducts while Vin exceeds Vf, clipping the negative "
              "half-cycle and producing a pulsing DC output. Simplified educational "
              "model: fixed Vf, ideal source, and no reverse-recovery, leakage, "
              "junction-capacitance, or dynamic-resistance effects.",
        "ro": "Dioda conduce doar când Vin depășește Vf, tăind semi-alternanța negativă "
              "și producând o ieșire DC pulsatorie. Model educațional simplificat: Vf "
              "constant, sursă ideală și fără efecte de recuperare inversă, curent de "
              "scurgere, capacitate de joncțiune sau rezistență dinamică."},

    # ---- Diode bridge rectifiers ------------------------------------------
    "diode.subtab.bridge2": {"en": "2-Diode Rectifier", "ro": "Redresor cu 2 Diode"},
    "diode.subtab.bridge4": {"en": "4-Diode Bridge", "ro": "Punte cu 4 Diode"},
    "diode.bridge2.title": {"en": "2-Diode Full-Wave Rectifier (center-tap)",
                             "ro": "Redresor Bidirecțional cu 2 Diode (priză mediană)"},
    "diode.bridge2.intro": {
        "en": "Two AC sources of opposite polarity (representing the two halves of a "
              "center-tapped winding) each feed one diode, joining at a shared "
              "output/ground. D1 and D2 conduct on alternating half-cycles, so only "
              "one diode drop (Vf) appears in the output.",
        "ro": "Două surse AC de polaritate opusă (reprezentând cele două jumătăți ale "
              "unei înfășurări cu priză mediană) alimentează fiecare câte o diodă, "
              "unindu-se la o ieșire/masă comună. D1 și D2 conduc alternativ, deci "
              "apare o singură cădere de tensiune (Vf) la ieșire."},
    "diode.bridge4.title": {"en": "4-Diode Full Bridge Rectifier", "ro": "Punte Redresoare cu 4 Diode"},
    "diode.bridge4.intro": {
        "en": "Uses 4 diodes in a bridge arrangement — no center tap needed, works with "
              "any simple AC source. Two diodes conduct at a time, so the output loses "
              "2×Vf instead of just Vf.",
        "ro": "Folosește 4 diode într-o configurație de punte — nu necesită priză "
              "mediană, funcționează cu orice sursă AC simplă. Două diode conduc "
              "simultan, deci ieșirea pierde 2×Vf în loc de doar Vf."},
    "diode.bridge.amplitude": {"en": "AC Amplitude (V peak)", "ro": "Amplitudine AC (V vârf)"},
    "diode.bridge.frequency": {"en": "Frequency (Hz)", "ro": "Frecvență (Hz)"},
    "diode.bridge.vf": {"en": "Diode drop Vf (V)", "ro": "Cădere diodă Vf (V)"},
    "diode.bridge.rload": {"en": "Load Resistance (Ω)", "ro": "Rezistență de Sarcină (Ω)"},
    "diode.bridge.add_cap": {"en": "➕ Add Smoothing Capacitor", "ro": "➕ Adaugă Condensator de Netezire"},
    "diode.bridge.remove_cap": {"en": "➖ Remove Capacitor", "ro": "➖ Elimină Condensatorul"},
    "diode.bridge.cap_value": {"en": "Capacitance (e.g. 100u)", "ro": "Capacitate (ex: 100u)"},
    "diode.bridge.legend_vin": {"en": "Vin (AC source)", "ro": "Vin (sursă AC)"},
    "diode.bridge.legend_vout": {"en": "Vout (rectified)", "ro": "Vout (redresat)"},
    "diode.bridge.legend_vout_smoothed": {"en": "Vout (smoothed)", "ro": "Vout (netezit)"},
    "diode.bridge.legend_vout_before": {"en": "Vout (before capacitor)", "ro": "Vout (înainte de condensator)"},
    "diode.bridge.chart_title": {"en": "Full-Wave Rectification", "ro": "Redresare Bidirecțională"},
    "diode.bridge2.note": {
        "en": "Full-wave output with a single diode drop (Vf) — both humps come from "
              "alternating halves of the center-tapped winding. Simplified educational "
              "model: fixed Vf, ideal source, and no reverse-recovery, leakage, "
              "junction-capacitance, or dynamic-resistance effects.",
        "ro": "Ieșire bidirecțională cu o singură cădere de tensiune (Vf) — ambele "
              "gibozități provin din jumătățile alternante ale înfășurării cu priză "
              "mediană. Model educațional simplificat: Vf constant, sursă ideală și "
              "fără efecte de recuperare inversă, curent de scurgere, capacitate de "
              "joncțiune sau rezistență dinamică."},
    "diode.bridge4.note": {
        "en": "Full-wave output with two diode drops (2×Vf), since two diodes conduct "
              "in series at any moment. Simplified educational model: fixed Vf, ideal "
              "source, and no reverse-recovery, leakage, junction-capacitance, or "
              "dynamic-resistance effects.",
        "ro": "Ieșire bidirecțională cu două căderi de tensiune (2×Vf), deoarece două "
              "diode conduc în serie în orice moment. Model educațional simplificat: "
              "Vf constant, sursă ideală și fără efecte de recuperare inversă, curent "
              "de scurgere, capacitate de joncțiune sau rezistență dinamică."},
    "diode.bridge4.note_smoothed": {
        "en": "With the capacitor added, the output only dips slightly between peaks "
              "(ripple) instead of returning to zero — this is how DC power supplies "
              "smooth rectified AC.",
        "ro": "Cu condensatorul adăugat, ieșirea scade doar puțin între vârfuri "
              "(ondulație) în loc să revină la zero — așa netezesc sursele de "
              "alimentare DC curentul alternativ redresat."},

    # ---- Transistor tab -----------------------------------------------
    "transistor.tab_title": {"en": "🔺 Transistor Calculator", "ro": "🔺 Calculator Tranzistor"},
    "transistor.subtab.calc": {"en": "Bias Calculator", "ro": "Calculator Polarizare"},
    "transistor.subtab.chart": {"en": "Chart / Simulate", "ro": "Grafic / Simulare"},
    "transistor.bjt_type": {"en": "BJT Type:", "ro": "Tip BJT:"},
    "transistor.switch_calc_title": {"en": "Switching / Amplifier Calculator",
                                      "ro": "Calculator Comutare / Amplificator"},
    "transistor.vin": {"en": "Supply voltage Vin (V)", "ro": "Tensiune alimentare Vin (V)"},
    "transistor.vbe": {"en": "Base-emitter drop Vbe (V)", "ro": "Cădere bază-emitor Vbe (V)"},
    "transistor.ib": {"en": "Desired base current Ib (mA)", "ro": "Curent de bază dorit Ib (mA)"},
    "transistor.beta": {"en": "Current gain (β / hFE)", "ro": "Amplificare curent (β / hFE)"},
    "transistor.vin_must_exceed": {"en": "Vin must exceed Vbe for the transistor to turn on.",
                                    "ro": "Vin trebuie să depășească Vbe pentru ca tranzistorul să se deschidă."},
    "transistor.rb_result": {"en": "Base resistor Rb = (Vin - Vbe)/Ib", "ro": "Rezistor de bază Rb = (Vin - Vbe)/Ib"},
    "transistor.ic_result": {"en": "Resulting collector current Ic = β × Ib",
                              "ro": "Curent de colector rezultat Ic = β × Ib"},
    "transistor.chart.title": {"en": "Simulate: Switch vs Amplifier", "ro": "Simulare: Comutator vs Amplificator"},
    "transistor.chart.mode_hint": {"en": "(DC = switch, AC = small-signal amplifier)",
                                    "ro": "(DC = comutator, AC = amplificator semnal mic)"},
    "transistor.chart.dc_vin_high": {"en": "Input high level (V)", "ro": "Nivel logic 1 intrare (V)"},
    "transistor.chart.dc_vbe": {"en": "Vbe threshold (V)", "ro": "Prag Vbe (V)"},
    "transistor.chart.dc_beta": {"en": "Current gain β", "ro": "Amplificare curent β"},
    "transistor.chart.dc_rb": {"en": "Base resistor Rb (Ω)", "ro": "Rezistor de bază Rb (Ω)"},
    "transistor.chart.dc_rc": {"en": "Collector resistor Rc (Ω)", "ro": "Rezistor de colector Rc (Ω)"},
    "transistor.chart.dc_vcc": {"en": "Supply Vcc (V)", "ro": "Alimentare Vcc (V)"},
    "transistor.chart.dc_freq": {"en": "Switching rate (Hz)", "ro": "Rată de comutare (Hz)"},
    "transistor.chart.ac_vin_amp": {"en": "Input signal amplitude (V)", "ro": "Amplitudine semnal intrare (V)"},
    "transistor.chart.ac_gain": {"en": "Voltage gain (Rc/Re, unitless)", "ro": "Amplificare tensiune (Rc/Re, adimensional)"},
    "transistor.chart.ac_vcc": {"en": "Supply Vcc (V, clip limit)", "ro": "Alimentare Vcc (V, limită de tăiere)"},
    "transistor.chart.dc_title": {"en": "DC Switching Behavior", "ro": "Comportament de Comutare DC"},
    "transistor.chart.ac_title": {"en": "AC Common-Emitter Amplifier", "ro": "Amplificator AC Emitor Comun"},
    "transistor.chart.legend_vin_base": {"en": "Vin (base drive)", "ro": "Vin (comandă bază)"},
    "transistor.chart.legend_vout_collector": {"en": "Vout (collector)", "ro": "Vout (colector)"},
    "transistor.chart.legend_vin": {"en": "Vin", "ro": "Vin"},
    "transistor.chart.legend_vout": {"en": "Vout", "ro": "Vout"},
    "transistor.chart.dc_note": {
        "en": "As an ideal switch: when Vin rises above Vbe the transistor saturates, "
              "pulling Vout low. Collector current is capped at Vcc/Rc once saturated.",
        "ro": "Ca un comutator ideal: când Vin depășește Vbe, tranzistorul saturează, "
              "trăgând Vout la valoare mică. Curentul de colector este limitat la Vcc/Rc "
              "odată saturat."},
    "transistor.chart.ac_note": {
        "en": "A common-emitter amplifier inverts and amplifies its input (180° phase "
              "shift). Output clips if it would exceed the supply rails.",
        "ro": "Un amplificator cu emitor comun inversează și amplifică intrarea "
              "(defazaj de 180°). Ieșirea se limitează dacă ar depăși tensiunile de "
              "alimentare."},

    # ---- Transistor Chart/Simulate — MOSFET fields & text -----------------
    "transistor.chart.dc_vgs_high": {"en": "Input high level Vgs (V)", "ro": "Nivel logic 1 Vgs (V)"},
    "transistor.chart.dc_vth": {"en": "Threshold Vth (V)", "ro": "Prag Vth (V)"},
    "transistor.chart.dc_k": {"en": "Transconductance k (A/V²)", "ro": "Transconductanță k (A/V²)"},
    "transistor.chart.dc_rd": {"en": "Drain resistor Rd (Ω)", "ro": "Rezistor de drenă Rd (Ω)"},
    "transistor.chart.dc_vdd": {"en": "Supply Vdd (V)", "ro": "Alimentare Vdd (V)"},
    "transistor.chart.ac_gm": {"en": "Voltage gain (gm×Rd, unitless)", "ro": "Amplificare tensiune (gm×Rd, adimensional)"},
    "transistor.chart.ac_vdd": {"en": "Supply Vdd (V, clip limit)", "ro": "Alimentare Vdd (V, limită de tăiere)"},
    "transistor.chart.mosfet_dc_title": {"en": "DC Switching Behavior", "ro": "Comportament de Comutare DC"},
    "transistor.chart.mosfet_ac_title": {"en": "AC Common-Source Amplifier", "ro": "Amplificator AC Sursă Comună"},
    "transistor.chart.legend_vin_gate": {"en": "Vin (gate drive)", "ro": "Vin (comandă poartă)"},
    "transistor.chart.legend_vout_drain": {"en": "Vout (drain)", "ro": "Vout (drenă)"},
    "transistor.chart.mosfet_dc_note": {
        "en": "As an ideal switch: when Vgs rises above Vth the MOSFET turns on, pulling "
              "Vout low. Drain current is capped at Vdd/Rd once fully on.",
        "ro": "Ca un comutator ideal: când Vgs depășește Vth, MOSFET-ul se deschide, "
              "trăgând Vout la valoare mică. Curentul de drenă este limitat la Vdd/Rd "
              "odată complet deschis."},
    "transistor.chart.mosfet_ac_note": {
        "en": "A common-source amplifier inverts and amplifies its input (180° phase "
              "shift). Output clips if it would exceed the supply rails.",
        "ro": "Un amplificator cu sursă comună inversează și amplifică intrarea "
              "(defazaj de 180°). Ieșirea se limitează dacă ar depăși tensiunile de "
              "alimentare."},

    # ---- Transistor Chart/Simulate — JFET fields & text --------------------
    "transistor.chart.dc_vgs_pinch": {"en": "Pinch-off drive Vgs (V)", "ro": "Comandă blocare Vgs (V)"},
    "transistor.chart.dc_idss": {"en": "Idss (A)", "ro": "Idss (A)"},
    "transistor.chart.dc_vp": {"en": "Pinch-off Vp (V)", "ro": "Tensiune de blocare Vp (V)"},
    "transistor.chart.jfet_dc_title": {"en": "DC Switching Behavior", "ro": "Comportament de Comutare DC"},
    "transistor.chart.jfet_ac_title": {"en": "AC Common-Source Amplifier", "ro": "Amplificator AC Sursă Comună"},
    "transistor.chart.jfet_dc_note": {
        "en": "JFETs are normally ON: Id is largest near Vgs = 0 and pinches off as Vgs "
              "swings toward Vp. Here Vin toggles the gate between 0 V (on) and the "
              "pinch-off drive level (off).",
        "ro": "JFET-urile sunt normal deschise: Id este maxim în jurul Vgs = 0 și se "
              "blochează pe măsură ce Vgs se apropie de Vp. Aici Vin comută poarta între "
              "0 V (deschis) și nivelul de blocare (închis)."},
    "transistor.chart.jfet_ac_note": {
        "en": "A common-source JFET amplifier inverts and amplifies its input (180° "
              "phase shift). Output clips if it would exceed the supply rails.",
        "ro": "Un amplificator JFET cu sursă comună inversează și amplifică intrarea "
              "(defazaj de 180°). Ieșirea se limitează dacă ar depăși tensiunile de "
              "alimentare."},

    # ---- Op-amp tab -----------------------------------------------
    "opamp.tab_title": {"en": "📈 Op-Amp Gain Calculator", "ro": "📈 Calculator Amplificare AO"},
    "opamp.configuration": {"en": "Configuration:", "ro": "Configurație:"},
    "opamp.inverting": {"en": "Inverting", "ro": "Inversoare"},
    "opamp.noninverting": {"en": "Non-inverting", "ro": "Neinversoare"},
    "opamp.rin": {"en": "Rin (e.g. 1k)", "ro": "Rin (ex: 1k)"},
    "opamp.rf": {"en": "Rf (e.g. 10k)", "ro": "Rf (ex: 10k)"},
    "opamp.vin": {"en": "Vin (V)", "ro": "Vin (V)"},
    "opamp.vplus": {"en": "V+ supply (V)", "ro": "Alimentare V+ (V)"},
    "opamp.vminus": {"en": "V- supply (V)", "ro": "Alimentare V- (V)"},
    "opamp.vout_ideal": {"en": "Vout (ideal)", "ro": "Vout (ideal)"},
    "opamp.vout_actual": {"en": "Vout (clipped to supply rails)", "ro": "Vout (limitat la alimentare)"},
    "opamp.clip_warning": {"en": "Ideal output exceeds the selected supply rails.",
                            "ro": "Valoarea ideală a ieșirii depășește limitele de alimentare selectate."},
    "opamp.gain": {"en": "Gain", "ro": "Amplificare"},
    "opamp.assumption": {"en": "(assuming ideal, unclipped op-amp)", "ro": "(presupunând AO ideal, nesaturat)"},
    "opamp.enter_valid": {"en": "Enter valid Rin, Rf and Vin", "ro": "Introduceți Rin, Rf și Vin valide"},

    # ---- Battery tab -----------------------------------------------
    "battery.tab_title": {"en": "🔌 Battery & Power Source Calculator",
                           "ro": "🔌 Calculator Baterie & Sursă de Alimentare"},
    "battery.arrangement": {"en": "Arrangement:", "ro": "Aranjament:"},
    "battery.num_cells": {"en": "Number of cells", "ro": "Număr de celule"},
    "battery.voltage_per_cell": {"en": "Voltage per cell (V)", "ro": "Tensiune per celulă (V)"},
    "battery.capacity_per_cell": {"en": "Capacity per cell (mAh)", "ro": "Capacitate per celulă (mAh)"},
    "battery.load_current": {"en": "Load current (mA)", "ro": "Curent de sarcină (mA)"},
    "battery.total_voltage": {"en": "Total voltage", "ro": "Tensiune totală"},
    "battery.total_capacity": {"en": "Total capacity", "ro": "Capacitate totală"},
    "battery.runtime_estimate": {"en": "Estimated runtime at", "ro": "Autonomie estimată la"},
    "battery.energy_estimate": {"en": "Estimated energy", "ro": "Energie estimată"},
    "battery.runtime_disclaimer": {
        "en": "Real battery runtime depends on discharge rate, internal resistance, "
              "temperature, cutoff voltage, battery chemistry and battery-management limits.",
        "ro": "Autonomia reală depinde de rata de descărcare, rezistența internă, "
              "temperatură, tensiunea de cutoff, chimia bateriei și limitele "
              "sistemului de management al bateriei."},
    "battery.load": {"en": "load", "ro": "sarcină"},
    "battery.hours": {"en": "hours", "ro": "ore"},
    "battery.enter_valid": {"en": "Enter valid numbers", "ro": "Introduceți numere valide"},
    "battery.series_adds": {"en": "Series (voltages add)", "ro": "Serie (tensiunile se adună)"},
    "battery.parallel_adds": {"en": "Parallel (capacity adds)", "ro": "Paralel (capacitatea se adună)"},

    # ---- Basics tab -----------------------------------------------
    "basics.tab_title": {"en": "⚡ AC / DC Basics & Ohm's Law", "ro": "⚡ Bazele AC/DC & Legea lui Ohm"},
    "basics.ohms_triangle_title": {"en": "Ohm's Law Triangle Solver", "ro": "Rezolvator Triunghi Legea lui Ohm"},
    "basics.fill_two": {"en": "Fill in any two values, leave one blank:",
                         "ro": "Completați oricare două valori, lăsați una goală:"},
    "basics.voltage_v": {"en": "Voltage V (volts):", "ro": "Tensiune V (volți):"},
    "basics.current_i": {"en": "Current I (amps):", "ro": "Curent I (amperi):"},
    "basics.resistance_r": {"en": "Resistance R (ohms):", "ro": "Rezistență R (ohmi):"},
    "basics.solve": {"en": "Solve", "ro": "Rezolvă"},
    "basics.fill_exactly_two": {"en": "Please fill exactly two of the three fields.",
                                 "ro": "Vă rugăm completați exact două din cele trei câmpuri."},
    "basics.not_valid_number": {"en": "is not a valid number for", "ro": "nu este un număr valid pentru"},
    "basics.r_cannot_be_zero": {"en": "R cannot be 0 when solving for I", "ro": "R nu poate fi 0 când se calculează I"},
    "basics.i_cannot_be_zero": {"en": "I cannot be 0 when solving for R", "ro": "I nu poate fi 0 când se calculează R"},
    "basics.rms_peak_title": {"en": "RMS ⇄ Peak (sine wave)", "ro": "RMS ⇄ Vârf (undă sinusoidală)"},
    "basics.peak_voltage": {"en": "Peak voltage (V):", "ro": "Tensiune de vârf (V):"},

    # ---- Interactive Ohm's Law live slider simulator ----------------------
    "basics.live.title": {"en": "🎚 Live Ohm's Law Simulator", "ro": "🎚 Simulator Interactiv Legea lui Ohm"},
    "basics.live.intro": {
        "en": "Pick one quantity to lock (it stays fixed), then drag either of the "
              "other two sliders — the third one reacts automatically to keep "
              "V = I × R true. Only one quantity can be locked at a time.",
        "ro": "Alege o mărime de blocat (rămâne fixă), apoi trage oricare dintre "
              "celelalte două cursoare — a treia reacționează automat pentru a "
              "menține adevărată relația V = I × R. Doar o mărime poate fi blocată "
              "simultan."},
    "basics.live.voltage": {"en": "Voltage (V)", "ro": "Tensiune (V)"},
    "basics.live.current": {"en": "Current (I)", "ro": "Curent (I)"},
    "basics.live.resistance": {"en": "Resistance (R)", "ro": "Rezistență (R)"},
    "basics.live.lock": {"en": "🔒 Lock", "ro": "🔒 Blochează"},
    "basics.live.locked_note": {"en": "{param} is locked — drag either of the other two sliders.",
                                 "ro": "{param} este blocat — trage oricare dintre celelalte două cursoare."},

    # ---- Canvas drawing captions -----------------------------------
    "draw.ceramic_caption": {"en": "Ceramic Capacitor (non-polarized)", "ro": "Condensator Ceramic (nepolarizat)"},
    "draw.electro_caption": {"en": "Electrolytic Capacitor (polarized)", "ro": "Condensator Electrolitic (polarizat)"},
    "draw.primary": {"en": "Primary (Np)", "ro": "Primar (Np)"},
    "draw.secondary": {"en": "Secondary (Ns)", "ro": "Secundar (Ns)"},
    "draw.led_caption": {"en": "LED (emits light when forward biased)",
                          "ro": "LED (emite lumină la polarizare directă)"},
    "draw.diode_caption": {"en": "Diode  (Anode → | → Cathode)", "ro": "Diodă  (Anod → | → Catod)"},
    "draw.bjt_suffix": {"en": "Bipolar Junction Transistor", "ro": "Tranzistor Bipolar cu Joncțiune"},
    "draw.battery_series": {"en": "Series (voltages add)", "ro": "Serie (tensiunile se adună)"},
    "draw.battery_parallel": {"en": "Parallel (capacity adds)", "ro": "Paralel (capacitatea se adună)"},

    # ---- Generic chart (TimeChartTab) -----------------------------------
    "chart.dc": {"en": "DC", "ro": "DC"},
    "chart.ac": {"en": "AC", "ro": "AC"},
    "chart.dc_title": {"en": "DC transient response", "ro": "Răspuns tranzitoriu DC"},
    "chart.ac_title": {"en": "AC steady-state waveform", "ro": "Formă de undă AC în regim permanent"},
    "chart.voltage_axis": {"en": "Voltage", "ro": "Tensiune"},
    "chart.current_axis": {"en": "Current", "ro": "Curent"},
    "chart.power_note": {"en": "Power P(t) = V(t) × I(t)  —  peak ≈ {ppeak}, average ≈ {pavg}",
                          "ro": "Putere P(t) = V(t) × I(t)  —  vârf ≈ {ppeak}, medie ≈ {pavg}"},
    "chart.model_assumptions": {
        "en": "Model assumptions: this simulation uses simplified/ideal component "
              "models unless otherwise stated. ESR, ESL, parasitic capacitance, "
              "winding resistance, core losses, temperature effects, device "
              "tolerances and other frequency-dependent non-idealities may not be "
              "modeled.",
        "ro": "Ipoteze de model: această simulare folosește modele "
              "simplificate/ideale pentru componente, dacă nu se specifică altfel. "
              "ESR, ESL, capacitățile parazite, rezistența înfășurărilor, "
              "pierderile în miez, efectele temperaturii, toleranțele "
              "componentelor și alte neidealități dependente de frecvență pot să "
              "nu fie modelate."},

    # ---- Junction visualizer -------------------------------------------
    "junction.state_active": {"en": "active region", "ro": "regiune activă"},
    "junction.state_saturation": {"en": "Saturation — both junctions forward biased", "ro": "Saturație — ambele joncțiuni polarizate direct"},
    "junction.state_cutoff": {"en": "Cutoff — no conduction", "ro": "Blocare — fără conducție"},
    "junction.depletion_eb": {"en": "E-B depletion", "ro": "Sărăcire E-B"},
    "junction.depletion_cb": {"en": "C-B depletion", "ro": "Sărăcire C-B"},
    "junction.depletion_eb_short": {"en": "E-B", "ro": "E-B"},
    "junction.depletion_cb_short": {"en": "C-B", "ro": "C-B"},
    "junction.flow_label": {"en": "flow", "ro": "flux"},
    "junction.state_saturation_fet": {"en": "Saturation — channel pinched near drain", "ro": "Saturație — canal strangulat lângă drenă"},
    "junction.state_triode": {"en": "Triode/linear region", "ro": "Regiune triodă/liniară"},
    "junction.state_pinchoff": {"en": "Pinch-off — channel fully closed", "ro": "Strangulare — canal complet închis"},
    "junction.state_conducting": {"en": "Conducting", "ro": "Conduce"},
    "junction.state_body_diode": {"en": "Body diode conducting (reverse Vds)",
                                   "ro": "Diodă de corp conduce (Vds invers)"},
    "junction.state_gate_forward": {"en": "Gate junction forward biased (reverse/leakage current)",
                                     "ro": "Joncțiune de poartă polarizată direct (curent invers/scurgere)"},
    "junction.body_diode_legend": {"en": "body-diode current", "ro": "curent diodă de corp"},
    "junction.gate_current_legend": {"en": "gate leakage current", "ro": "curent de scurgere poartă"},

    # ---- MOSFET/JFET operating-region panel (tabs/transistor.py) --------
    "junction.mosfet_region_cutoff": {"en": "CUTOFF", "ro": "BLOCARE"},
    "junction.mosfet_region_triode": {"en": "TRIODE / LINEAR", "ro": "TRIODĂ / LINIAR"},
    "junction.mosfet_region_saturation": {"en": "SATURATION", "ro": "SATURAȚIE"},
    "junction.mosfet_region_body_diode": {"en": "BODY DIODE (reverse)", "ro": "DIODĂ DE CORP (invers)"},
    "junction.jfet_region_cutoff": {"en": "PINCH-OFF", "ro": "STRANGULARE"},
    "junction.jfet_region_conducting": {"en": "CONDUCTING", "ro": "CONDUCE"},
    "junction.jfet_region_gate_forward": {"en": "GATE FORWARD (reverse current)", "ro": "POARTĂ DIRECTĂ (curent invers)"},
    "junction.id_readout": {"en": "ID (relative units, illustrative)", "ro": "ID (unități relative, ilustrativ)"},
    "junction.mosfet_saturation_note": {"en": "Saturation: ID stays roughly constant as Vds rises further (current-source-like).",
                                         "ro": "Saturație: ID rămâne aproximativ constant pe măsură ce Vds crește (asemănător unei surse de curent)."},
    "junction.mosfet_triode_note": {"en": "Triode/linear region: the channel behaves like a voltage-controlled resistor.",
                                     "ro": "Regiune triodă/liniară: canalul se comportă ca un rezistor controlat în tensiune."},
    "junction.jfet_conducting_note": {"en": "The gate-channel junction stays reverse biased - normal JFET operation.",
                                       "ro": "Joncțiunea poartă-canal rămâne polarizată invers - funcționare normală JFET."},
    "junction.tab_title": {"en": "Junction Visualizer", "ro": "Vizualizator Joncțiuni"},
    "junction.qualitative_note": {
        "en": "This is a qualitative visualization, not a SPICE/device-physics simulation.",
        "ro": "Aceasta este o vizualizare calitativă, nu o simulare SPICE sau o simulare "
              "exactă a fizicii dispozitivului."},
    "junction.intro_bjt": {
        "en": "Drag the sliders to bias the junctions and watch the depletion regions "
              "shrink and grow in a way that qualitatively follows the real device's "
              "behavior. This is a qualitative visualization, not a SPICE/device-physics "
              "simulation.",
        "ro": "Trage sliderele pentru a polariza joncțiunile și urmărește regiunile de "
              "sărăcire micșorându-se și crescând într-un mod care urmează calitativ "
              "comportamentul dispozitivului real. Aceasta este o vizualizare "
              "calitativă, nu o simulare SPICE sau o simulare exactă a fizicii "
              "dispozitivului."},
    "junction.intro_mosfet": {
        "en": "Raise Vgs above the threshold to form the conducting channel, then raise "
              "Vds to see it pinch off near the drain in saturation. This is a "
              "qualitative visualization, not a SPICE/device-physics simulation.",
        "ro": "Ridică Vgs peste prag pentru a forma canalul conductor, apoi ridică Vds "
              "pentru a-l vedea strangulându-se lângă drenă în saturație. Aceasta este "
              "o vizualizare calitativă, nu o simulare SPICE sau o simulare exactă a "
              "fizicii dispozitivului."},
    "junction.intro_jfet": {
        "en": "Make Vgs more negative (N-channel) to widen the gate depletion regions "
              "and pinch the channel — at Vgs = Vp it closes completely. This is a "
              "qualitative visualization, not a SPICE/device-physics simulation.",
        "ro": "Fă Vgs mai negativ (canal N) pentru a lărgi regiunile de sărăcire ale "
              "porții și a strangula canalul — la Vgs = Vp se închide complet. Aceasta "
              "este o vizualizare calitativă, nu o simulare SPICE sau o simulare exactă "
              "a fizicii dispozitivului."},
    "junction.vbe": {"en": "Base-Emitter Voltage Vbe (V)", "ro": "Tensiune Bază-Emitor Vbe (V)"},
    "junction.vce": {"en": "Collector-Emitter Voltage Vce (V)", "ro": "Tensiune Colector-Emitor Vce (V)"},
    "junction.vgs": {"en": "Gate-Source Voltage Vgs (V)", "ro": "Tensiune Poartă-Sursă Vgs (V)"},
    "junction.vds": {"en": "Drain-Source Voltage Vds (V)", "ro": "Tensiune Drenă-Sursă Vds (V)"},
    "junction.vth": {"en": "Threshold Voltage Vth (V)", "ro": "Tensiune de Prag Vth (V)"},
    "junction.vp": {"en": "Pinch-off Voltage Vp (V)", "ro": "Tensiune de Strangulare Vp (V)"},

    # ---- Operating-region / current-gain panel keys (BJT only) --------
    "junction.operating_region": {"en": "Operating Region", "ro": "Regiune de Funcționare"},
    "junction.region_cutoff": {"en": "CUTOFF", "ro": "BLOCARE"},
    "junction.region_active": {"en": "FORWARD ACTIVE", "ro": "ACTIV DIRECT"},
    "junction.region_saturation": {"en": "SATURATION", "ro": "SATURAȚIE"},
    "junction.region_reverse_active": {"en": "REVERSE ACTIVE", "ro": "ACTIV INVERS"},
    "junction.region_transition": {"en": "TRANSITION", "ro": "TRANZIȚIE"},
    "junction.eb_forward": {"en": "E-B forward biased", "ro": "E-B polarizată direct"},
    "junction.eb_reverse": {"en": "E-B reverse biased", "ro": "E-B polarizată invers"},
    "junction.cb_forward": {"en": "C-B forward biased", "ro": "C-B polarizată direct"},
    "junction.cb_reverse": {"en": "C-B reverse biased", "ro": "C-B polarizată invers"},
    "junction.beta_note": {"en": "relative units, illustrative — not a calibrated physical current",
                            "ro": "unități relative, ilustrative — nu este un curent fizic calibrat"},
    "junction.switch_note": {"en": "Switch behavior: the transistor is fully OFF or fully ON.",
                              "ro": "Comportament de comutator: tranzistorul este complet OPRIT sau complet PORNIT."},
    "junction.amplifier_note": {"en": "Amplifier behavior: a small change in IB controls a much larger IC (current gain).",
                                 "ro": "Comportament de amplificator: o mică variație a IB controlează o variație mult mai mare a IC (câștig de curent)."},
    "junction.emitter": {"en": "Emitter", "ro": "Emitor"},
    "junction.base": {"en": "Base", "ro": "Bază"},
    "junction.collector": {"en": "Collector", "ro": "Colector"},
    "junction.state_active_full": {"en": "Forward-active — emitter injecting, collector sweeping",
                                    "ro": "Activ direct — emitorul injectează, colectorul colectează"},
    "junction.state_reverse_active": {"en": "Reverse-active — roles of emitter and collector swapped",
                                       "ro": "Activ invers — rolurile emitorului și colectorului sunt inversate"},
    "junction.state_transition": {"en": "Transition region", "ro": "Regiune de tranziție"},
    "junction.electron_flow": {"en": "carrier motion", "ro": "mișcarea purtătorilor"},
    "junction.conventional_current": {"en": "conventional current", "ro": "curent convențional"},

    # ---- Transistor family / polarity selector --------------------------
    "transistor.family": {"en": "Family:", "ro": "Familie:"},
    "transistor.family.bjt": {"en": "BJT (Bipolar)", "ro": "BJT (Bipolar)"},
    "transistor.family.mosfet": {"en": "MOSFET", "ro": "MOSFET"},
    "transistor.family.jfet": {"en": "JFET", "ro": "JFET"},
    "transistor.polarity": {"en": "Type:", "ro": "Tip:"},
    "transistor.polarity.npn": {"en": "NPN", "ro": "NPN"},
    "transistor.polarity.pnp": {"en": "PNP", "ro": "PNP"},
    "transistor.polarity.nchannel": {"en": "N-channel", "ro": "Canal N"},
    "transistor.polarity.pchannel": {"en": "P-channel", "ro": "Canal P"},
    "transistor.subtab.visualizer": {"en": "Junction Visualizer", "ro": "Vizualizator Joncțiuni"},
    "transistor.subtab.bias": {"en": "Q-Point / Bias Calculator (PSF)", "ro": "Calculator Punct Static (PSF)"},

    # ---- Bias / PSF calculator -------------------------------------------
    "bias.mode_analyze": {"en": "Analyze given components", "ro": "Analizează componente date"},
    "bias.mode_design": {"en": "Design for target Q-point", "ro": "Proiectează pentru punct țintă"},
    "bias.vcc": {"en": "Supply Voltage Vcc (V)", "ro": "Tensiune Alimentare Vcc (V)"},
    "bias.vdd": {"en": "Supply Voltage Vdd (V)", "ro": "Tensiune Alimentare Vdd (V)"},
    "bias.r1": {"en": "R1 (Ω)", "ro": "R1 (Ω)"},
    "bias.r2": {"en": "R2 (Ω)", "ro": "R2 (Ω)"},
    "bias.rc": {"en": "Rc (Ω)", "ro": "Rc (Ω)"},
    "bias.re": {"en": "Re (Ω)", "ro": "Re (Ω)"},
    "bias.rd": {"en": "Rd (Ω)", "ro": "Rd (Ω)"},
    "bias.rs": {"en": "Rs (Ω)", "ro": "Rs (Ω)"},
    "bias.beta": {"en": "Current gain β", "ro": "Amplificare curent β"},
    "bias.vbe": {"en": "Vbe (V)", "ro": "Vbe (V)"},
    "bias.vth": {"en": "Threshold Vth (V)", "ro": "Prag Vth (V)"},
    "bias.k": {"en": "Transconductance k (A/V²)", "ro": "Transconductanță k (A/V²)"},
    "bias.idss": {"en": "Idss (A)", "ro": "Idss (A)"},
    "bias.vp": {"en": "Pinch-off Vp (V)", "ro": "Strangulare Vp (V)"},
    "bias.ic_target": {"en": "Target Ic (A)", "ro": "Ic țintă (A)"},
    "bias.vce_target": {"en": "Target Vce (V)", "ro": "Vce țintă (V)"},
    "bias.id_target": {"en": "Target Id (A)", "ro": "Id țintă (A)"},
    "bias.vds_target": {"en": "Target Vds (V)", "ro": "Vds țintă (V)"},
    "bias.result_title": {"en": "Q-Point (PSF)", "ro": "Punct Static (PSF)"},
    "bias.suggested_components": {"en": "Suggested components:", "ro": "Componente sugerate:"},
    "bias.design_heuristics_note": {
        "en": "Uses common textbook heuristics: VE ≈ 0.1×VCC and divider current ≈ "
              "10×IB. These are design guidelines, not universal requirements.",
        "ro": "Folosește euristici uzuale din proiectarea didactică: VE ≈ 0,1×VCC și "
              "curentul divizorului ≈ 10×IB. Acestea sunt recomandări de proiectare, "
              "nu condiții universale."},
    "bias.region_prefix": {"en": "Operating region:", "ro": "Regiune de funcționare:"},
    "bias.region.active": {"en": "Active", "ro": "Activă"},
    "bias.region.saturation": {"en": "Saturation", "ro": "Saturație"},
    "bias.region.cutoff": {"en": "Cutoff", "ro": "Blocare"},
    "bias.region.triode": {"en": "Triode/Linear", "ro": "Triodă/Liniară"},
    "bias.load_line_title": {"en": "DC Load Line", "ro": "Dreapta de Sarcină DC"},
    "bias.qpoint_label": {"en": "Q-point", "ro": "Punct Q"},
    "bias.enter_valid": {"en": "Enter valid component values.", "ro": "Introduceți valori valide pentru componente."},
    "chart.source_removed": {"en": "source removed →", "ro": "sursă îndepărtată →"},

    # ---- Component type names (singular, for dropdowns) -----------------
    "comp.resistor": {"en": "Resistor", "ro": "Rezistor"},
    "comp.capacitor": {"en": "Capacitor", "ro": "Condensator"},
    "comp.inductor": {"en": "Inductor", "ro": "Bobină"},

    # ---- Voltage Divider (Resistors tab) / Filter (Signals tab) ----------
    # Both share the same underlying 2-element network engine (divider.py);
    # they're presented as two focused tools in two different places.
    "nav.divider": {"en": "Voltage Divider / Filter", "ro": "Divizor de Tensiune / Filtru"},
    "divider.tab_title": {"en": "🔀 Voltage Divider / Filter Simulator",
                           "ro": "🔀 Simulator Divizor de Tensiune / Filtru"},
    "divider.intro": {
        "en": "Build a simple 2-element network: one component in series with the "
              "signal, one in parallel (shunt) to ground. Choosing two resistors gives "
              "a classic voltage divider; mixing in a capacitor or inductor gives a "
              "basic filter (low-pass, high-pass, etc).",
        "ro": "Construiește o rețea simplă cu 2 elemente: un component în serie cu "
              "semnalul, unul în paralel (shunt) la masă. Alegând două rezistoare obții "
              "un divizor de tensiune clasic; combinând cu un condensator sau o bobină "
              "obții un filtru de bază (trece-jos, trece-sus etc)."},
    "divider.voltage.intro": {
        "en": "Classic 2-resistor voltage divider: Vout = Vin × R2/(R1+R2). Only "
              "resistors are used here — a resistive divider's output is flat with "
              "frequency. To see how a capacitor or inductor changes that ratio with "
              "frequency, check out the dedicated Filter tool in the Signals tab.",
        "ro": "Divizor de tensiune clasic cu 2 rezistoare: Vout = Vin × R2/(R1+R2). "
              "Aici se folosesc doar rezistoare — ieșirea unui divizor rezistiv este "
              "constantă cu frecvența. Pentru a vedea cum un condensator sau o bobină "
              "schimbă acest raport cu frecvența, încearcă unealta dedicată de Filtrare "
              "din tab-ul Semnale."},
    "filter.tab_title": {"en": "∿ Filter Simulator", "ro": "∿ Simulator de Filtru"},
    "filter.intro": {
        "en": "Build a simple RC/RL/LC filter: one component in series with the signal, "
              "one in parallel (shunt) to ground. Mixing a resistor with a capacitor or "
              "inductor gives a basic low-pass, high-pass, or (with 2 stages) band-pass "
              "filter — watch the ratio and phase shift change with frequency.",
        "ro": "Construiește un filtru RC/RL/LC simplu: un component în serie cu "
              "semnalul, unul în paralel (shunt) la masă. Combinând un rezistor cu un "
              "condensator sau o bobină obții un filtru de bază trece-jos, trece-sus sau "
              "(cu 2 etape) trece-bandă — urmărește cum se schimbă raportul și defazajul "
              "cu frecvența."},
    "divider.series_element": {"en": "Series element (in line with signal)",
                                "ro": "Element serie (pe linia de semnal)"},
    "divider.shunt_element": {"en": "Shunt element (to ground)", "ro": "Element paralel (la masă)"},
    "divider.type_label": {"en": "Type:", "ro": "Tip:"},
    "divider.value_label": {"en": "Value:", "ro": "Valoare:"},
    "divider.r1_label": {"en": "R1 (series)", "ro": "R1 (serie)"},
    "divider.r2_label": {"en": "R2 (shunt to ground)", "ro": "R2 (paralel la masă)"},
    "divider.r_value_label": {"en": "Resistance (Ω):", "ro": "Rezistență (Ω):"},
    "divider.formula_resistive": {"en": "Vout = Vin × R2 / (R1 + R2)",
                                   "ro": "Vout = Vin × R2 / (R1 + R2)"},
    "divider.add_stage2_resistive": {"en": "➕ Add Stage 2 (cascade another divider)",
                                      "ro": "➕ Adaugă Etapa 2 (cascadă un alt divizor)"},
    "divider.formula_title": {"en": "Formula", "ro": "Formulă"},
    "divider.formula_ac": {"en": "Vout = Vin × Zshunt / (Zseries + Zshunt)",
                            "ro": "Vout = Vin × Zshunt / (Zserie + Zshunt)"},
    "divider.formula_impedances": {"en": "Z_R = R,   Z_L = jωL,   Z_C = -j/(ωC)",
                                    "ro": "Z_R = R,   Z_L = jωL,   Z_C = -j/(ωC)"},
    "divider.ratio_prefix": {"en": "Output/Input ratio |H|:", "ro": "Raport Ieșire/Intrare |H|:"},
    "divider.phase_prefix": {"en": "Phase shift:", "ro": "Defazaj:"},
    "divider.note_flat_rr": {
        "en": "Pure resistive divider — the output is constant and follows the input "
              "instantly, at any frequency.",
        "ro": "Divizor pur rezistiv — ieșirea este constantă și urmărește instantaneu "
              "intrarea, la orice frecvență."},
    "divider.note_transient": {
        "en": "Showing the classic single-time-constant transient for this combination.",
        "ro": "Se arată tranzitoriul clasic cu o singură constantă de timp pentru "
              "această combinație."},
    "divider.note_fallback": {
        "en": "This reactive+reactive combination needs 2nd-order analysis for a full "
              "transient — showing the DC steady-state value only.",
        "ro": "Această combinație reactiv+reactiv necesită o analiză de ordinul 2 pentru "
              "un tranzitoriu complet — se arată doar valoarea de regim staționar DC."},
    "divider.add_stage2": {"en": "➕ Add Stage 2 (2nd-order filter: band-pass, etc.)",
                            "ro": "➕ Adaugă Etapa 2 (filtru de ordinul 2: trece-bandă etc.)"},
    "divider.stage1": {"en": "Stage 1", "ro": "Etapa 1"},
    "divider.stage2": {"en": "Stage 2", "ro": "Etapa 2"},
    "divider.stage2_intro": {
        "en": "Cascading a second L-section lets you build real 2nd-order responses: "
              "e.g. high-pass then low-pass gives a band-pass filter.",
        "ro": "Adăugarea unei a doua secțiuni permite construirea unor răspunsuri reale "
              "de ordinul 2: de ex. trece-sus urmat de trece-jos dă un filtru trece-bandă."},

    # ---- Mixed builder (used inside Resistor/Capacitor/Inductor combo tabs) --
    "combos.subtab.quicklist": {"en": "Quick List", "ro": "Listă Rapidă"},
    "combos.subtab.mixed": {"en": "Mixed Builder", "ro": "Constructor Mixt"},
    "combos.intro": {
        "en": "Build a mixed series+parallel network step by step: add a starting "
              "value, then keep adding components, choosing whether each new one "
              "combines in series or in parallel with everything built so far.",
        "ro": "Construiește o rețea mixtă serie+paralel pas cu pas: adaugă o valoare de "
              "pornire, apoi continuă să adaugi componente, alegând dacă fiecare se "
              "combină în serie sau în paralel cu tot ce ai construit până acum."},
    "combos.new_value": {"en": "New value:", "ro": "Valoare nouă:"},
    "combos.combine_as": {"en": "Combine as:", "ro": "Combină ca:"},
    "combos.add": {"en": "＋ Add", "ro": "＋ Adaugă"},
    "combos.undo": {"en": "↶ Undo last", "ro": "↶ Anulează ultimul"},
    "combos.reset": {"en": "⟲ Reset", "ro": "⟲ Resetează"},
    "combos.col_step": {"en": "Step", "ro": "Pas"},
    "combos.col_value": {"en": "Value added", "ro": "Valoare adăugată"},
    "combos.col_op": {"en": "Operation", "ro": "Operație"},
    "combos.col_total": {"en": "Running total", "ro": "Total curent"},
    "combos.first_value": {"en": "Starting value", "ro": "Valoare de pornire"},
    "combos.final_result": {"en": "Final equivalent value:", "ro": "Valoare echivalentă finală:"},
    "combos.empty_state": {"en": "Add a starting value to begin.", "ro": "Adaugă o valoare de pornire pentru a începe."},
    "combos.prev_total_label": {"en": "Total so far", "ro": "Total până acum"},
    "combos.new_label": {"en": "New", "ro": "Nou"},
    "combos.invalid_value": {"en": "Enter a valid numeric value.", "ro": "Introduceți o valoare numerică validă."},

    # =======================================================================
    # DIGITAL LOGIC
    # =======================================================================
    "nav.digital": {"en": "Boolean Logic", "ro": "Logică Booleană"},
    "digital.tab_title": {"en": "Boolean Logic", "ro": "Logică Booleană"},
    "digital.subtab.gates": {"en": "Logic Gates", "ro": "Porți Logice"},
    "digital.subtab.solver": {"en": "Boolean Solver", "ro": "Rezolvator Boolean"},
    "digital.subtab.builder": {"en": "Logic Circuit Builder", "ro": "Constructor de Circuite Logice"},

    "digital.gate_select": {"en": "Gate:", "ro": "Poartă:"},
    "digital.inputs": {"en": "Inputs", "ro": "Intrări"},
    "digital.output": {"en": "Output", "ro": "Ieșire"},
    "digital.truth_table": {"en": "Truth Table", "ro": "Tabel de Adevăr"},
    "digital.expression": {"en": "Boolean Expression", "ro": "Expresie Booleană"},
    "digital.explanation": {"en": "How it works", "ro": "Cum funcționează"},
    "digital.timing_diagram": {"en": "Timing Diagram", "ro": "Diagramă de Temporizare"},
    "digital.timing_hint": {"en": "Click a step on the A/B waveform to toggle it — Y updates automatically.",
                             "ro": "Apasă pe un pas din forma de undă A/B pentru a-l comuta — Y se actualizează automat."},

    "digital.explain.NOT": {"en": "Output is the opposite of the input.", "ro": "Ieșirea este opusul intrării."},
    "digital.explain.AND": {"en": "Output is HIGH only when ALL inputs are HIGH.",
                             "ro": "Ieșirea este HIGH doar când TOATE intrările sunt HIGH."},
    "digital.explain.OR": {"en": "Output is HIGH when AT LEAST ONE input is HIGH.",
                            "ro": "Ieșirea este HIGH când CEL PUȚIN O intrare este HIGH."},
    "digital.explain.NAND": {"en": "Output is LOW only when ALL inputs are HIGH (opposite of AND).",
                              "ro": "Ieșirea este LOW doar când TOATE intrările sunt HIGH (opusul AND)."},
    "digital.explain.NOR": {"en": "Output is HIGH only when ALL inputs are LOW (opposite of OR).",
                             "ro": "Ieșirea este HIGH doar când TOATE intrările sunt LOW (opusul OR)."},
    "digital.explain.XOR": {"en": "Output is HIGH when the inputs are DIFFERENT.",
                             "ro": "Ieșirea este HIGH când intrările sunt DIFERITE."},
    "digital.explain.XNOR": {"en": "Output is HIGH when the inputs are the SAME.",
                              "ro": "Ieșirea este HIGH când intrările sunt IDENTICE."},

    "digital.use.NOT": {"en": "Common use: inverters, signal complementing, active-low logic.",
                         "ro": "Utilizare comună: inversoare, complementarea semnalelor, logică activă pe LOW."},
    "digital.use.AND": {"en": "Common use: enabling a signal only when multiple conditions hold (e.g. masking, gating).",
                         "ro": "Utilizare comună: activarea unui semnal doar când mai multe condiții sunt îndeplinite (mascare, comandă)."},
    "digital.use.OR": {"en": "Common use: combining alarms/flags, any-of conditions, wired-OR logic.",
                        "ro": "Utilizare comună: combinarea alarmelor/flagurilor, condiții de tip 'oricare din', logică cablată OR."},
    "digital.use.NAND": {"en": "Common use: a universal gate — any Boolean function can be built from NAND gates alone.",
                          "ro": "Utilizare comună: poartă universală — orice funcție booleană poate fi construită doar din porți NAND."},
    "digital.use.NOR": {"en": "Common use: also a universal gate; common in SR-latches and CMOS logic.",
                         "ro": "Utilizare comună: de asemenea poartă universală; frecventă în latch-uri SR și logică CMOS."},
    "digital.use.XOR": {"en": "Common use: binary addition (sum bit), parity/error checking, comparators.",
                         "ro": "Utilizare comună: adunare binară (bitul de sumă), verificare paritate/erori, comparatoare."},
    "digital.use.XNOR": {"en": "Common use: equality comparators, parity checking (even parity).",
                          "ro": "Utilizare comună: comparatoare de egalitate, verificarea parității (paritate pară)."},

    "digital.solver.title": {"en": "Enter a Boolean function", "ro": "Introdu o funcție booleană"},
    "digital.solver.placeholder_hint": {
        "en": "e.g. A·B + ¬A·C   or   (A AND B) OR (NOT A AND C)   or   A XOR B",
        "ro": "ex: A·B + ¬A·C   sau   (A AND B) OR (NOT A AND C)   sau   A XOR B"},
    "digital.solver.parsed_symbolic": {"en": "Parsed (symbolic):", "ro": "Interpretat (simbolic):"},
    "digital.solver.parsed_words": {"en": "Parsed (words):", "ro": "Interpretat (cuvinte):"},
    "digital.solver.variables": {"en": "Variables:", "ro": "Variabile:"},
    "digital.solver.syntax_hint": {
        "en": "Type with the keyboard or click the keypad. AND: · * & && . or just write letters together (AB = A·B)   "
              "OR: + | ||   NOT: ' after a variable (A'), ! ~ ¬ or NOT   XOR: ^ ⊕   also NAND, NOR, XNOR and ( ). "
              "Words work too: (A and B) or not C. Names with digits or lower-case letters (x1, Sel) stay one variable.",
        "ro": "Scrie de la tastatură sau apasă tastele de pe ecran. AND: · * & && . sau scrie literele lipite (AB = A·B)   "
              "OR: + | ||   NOT: ' după variabilă (A'), ! ~ ¬ sau NOT   XOR: ^ ⊕   plus NAND, NOR, XNOR și ( ). "
              "Merg și cuvintele: (A and B) or not C. Numele cu cifre sau litere mici (x1, Sel) rămân o singură variabilă."},
    "digital.solver.empty": {"en": "Enter an expression above to see its truth table.",
                              "ro": "Introdu o expresie mai sus pentru a vedea tabelul de adevăr."},
    "digital.solver.too_many_vars": {
        "en": "Maximum 8 variables are supported by the truth-table and minimization engine "
              "(this expression uses {n}). Remove some variables to see the truth table and simplification.",
        "ro": "Sunt suportate maximum 8 variabile de către motorul pentru tabelul de adevăr și "
              "minimizare (această expresie folosește {n}). Elimină câteva variabile pentru a "
              "vedea tabelul de adevăr și simplificarea."},
    "digital.solver.canonical_sop": {"en": "Canonical SOP:", "ro": "SOP Canonică:"},
    "digital.solver.simplification_title": {"en": "Boolean Simplification", "ro": "Simplificare Booleană"},
    "digital.solver.minimal_sop": {"en": "Minimal SOP:", "ro": "SOP Minimizată:"},
    "digital.solver.canonical_pos": {"en": "Canonical POS:", "ro": "POS Canonică:"},
    "digital.solver.minimal_pos": {"en": "Minimal POS:", "ro": "POS Minimizată:"},
    "digital.solver.show_steps": {"en": "Show derivation steps ▾", "ro": "Arată pașii derivării ▾"},
    "digital.solver.hide_steps": {"en": "Hide derivation steps ▴", "ro": "Ascunde pașii derivării ▴"},
    "digital.solver.steps_title": {"en": "How the minimization was derived (Quine–McCluskey):",
                                    "ro": "Cum a fost derivată minimizarea (Quine–McCluskey):"},

    "theory.digital.title": {"en": "Digital Logic", "ro": "Logică Digitală"},
    "theory.digital.what": {
        "en": "Digital logic represents information as two discrete states, HIGH (1) and LOW (0), "
              "and combines them with logic gates to compute Boolean functions.",
        "ro": "Logica digitală reprezintă informația prin două stări discrete, HIGH (1) și LOW (0), "
              "și le combină cu porți logice pentru a calcula funcții booleene."},
    "theory.digital.how": {
        "en": "Every gate implements one basic Boolean operation. Chaining gates together builds up "
              "arbitrarily complex functions — any truth table can be built from AND, OR and NOT alone.",
        "ro": "Fiecare poartă implementează o operație booleană de bază. Înlănțuirea porților construiește "
              "funcții oricât de complexe — orice tabel de adevăr poate fi construit doar din AND, OR și NOT."},
    "theory.digital.f.demorgan1": {"en": "De Morgan's law", "ro": "Legea lui De Morgan"},
    "theory.digital.f.demorgan2": {"en": "De Morgan's law (dual)", "ro": "Legea lui De Morgan (duală)"},
    "theory.digital.f.identity": {"en": "Identity", "ro": "Identitate"},
    "theory.digital.f.complement": {"en": "Complement", "ro": "Complement"},
    "theory.digital.f.idempotent": {"en": "Idempotent", "ro": "Idempotent"},
    "theory.digital.f.distributive": {"en": "Distributive", "ro": "Distributiv"},
    "theory.digital.f.commutative": {"en": "Commutative", "ro": "Comutativ"},
    "theory.digital.f.associative": {"en": "Associative", "ro": "Asociativ"},
    "theory.digital.f.absorption": {"en": "Absorption", "ro": "Absorbție"},
    "theory.digital.f.xor": {"en": "XOR (exclusive OR)", "ro": "XOR (SAU exclusiv)"},
    "theory.digital.f.xnor": {"en": "XNOR (exclusive NOR)", "ro": "XNOR (NU-SAU exclusiv)"},

    # ===================================================================
    # New navigation entries (2.6)
    # ===================================================================
    "nav.unit_converter": {"en": "Unit Converter", "ro": "Convertor de Unități"},
    "nav.ac_circuits": {"en": "AC Circuits & Phasors", "ro": "Circuite AC & Fazori"},
    "nav.signal_gen": {"en": "Signal Generator", "ro": "Generator de Semnal"},

    # ===================================================================
    # Unit Converter tab
    # ===================================================================
    "uc.tab_title": {"en": "🔁 Unit Converter", "ro": "🔁 Convertor de Unități"},
    "uc.intro": {
        "en": "Convert a value between SI magnitude prefixes (pico, nano, micro, milli, "
              "kilo, mega, giga...). Works for any unit — volts, amps, ohms, farads, "
              "henries, hertz, watts — since the prefix is just a power-of-ten multiplier.",
        "ro": "Convertește o valoare între prefixele SI de mărime (pico, nano, micro, "
              "mili, kilo, mega, giga...). Funcționează pentru orice unitate — volți, "
              "amperi, ohmi, farazi, henry, hertz, wați — deoarece prefixul este doar "
              "un multiplicator de putere a lui zece."},
    "uc.value_label": {"en": "Value:", "ro": "Valoare:"},
    "uc.from_label": {"en": "From prefix:", "ro": "Din prefixul:"},
    "uc.to_label": {"en": "To prefix:", "ro": "În prefixul:"},
    "uc.swap": {"en": "⇄ Swap", "ro": "⇄ Inversează"},
    "uc.result_label": {"en": "Result:", "ro": "Rezultat:"},
    "uc.best_fit_label": {"en": "Auto (best-fit) notation:", "ro": "Notație automată (cea mai potrivită):"},
    "uc.invalid_value": {"en": "Please enter a valid number.", "ro": "Vă rugăm introduceți un număr valid."},
    "uc.quick_ref_title": {"en": "SI Prefix Reference", "ro": "Referință Prefixe SI"},
    "uc.table.prefix": {"en": "Prefix", "ro": "Prefix"},
    "uc.table.symbol": {"en": "Symbol", "ro": "Simbol"},
    "uc.table.factor": {"en": "Factor", "ro": "Factor"},
    "uc.table.example": {"en": "1 unit =", "ro": "1 unitate ="},
    "uc.prefix.pico": {"en": "pico", "ro": "pico"},
    "uc.prefix.nano": {"en": "nano", "ro": "nano"},
    "uc.prefix.micro": {"en": "micro", "ro": "micro"},
    "uc.prefix.milli": {"en": "milli", "ro": "mili"},
    "uc.prefix.base": {"en": "(base unit)", "ro": "(unitate de bază)"},
    "uc.prefix.kilo": {"en": "kilo", "ro": "kilo"},
    "uc.prefix.mega": {"en": "mega", "ro": "mega"},
    "uc.prefix.giga": {"en": "giga", "ro": "giga"},
    "uc.prefix.tera": {"en": "tera", "ro": "tera"},
    "uc.prefix.quecto": {"en": "quecto", "ro": "quecto"},
    "uc.prefix.ronto": {"en": "ronto", "ro": "ronto"},
    "uc.prefix.yocto": {"en": "yocto", "ro": "yocto"},
    "uc.prefix.zepto": {"en": "zepto", "ro": "zepto"},
    "uc.prefix.atto": {"en": "atto", "ro": "atto"},
    "uc.prefix.femto": {"en": "femto", "ro": "femto"},
    "uc.prefix.peta": {"en": "peta", "ro": "peta"},
    "uc.prefix.exa": {"en": "exa", "ro": "exa"},
    "uc.prefix.zetta": {"en": "zetta", "ro": "zetta"},
    "uc.prefix.yotta": {"en": "yotta", "ro": "yotta"},
    "uc.prefix.ronna": {"en": "ronna", "ro": "ronna"},
    "uc.prefix.quetta": {"en": "quetta", "ro": "quetta"},
    "uc.full_si_toggle": {"en": "Full SI prefixes (quecto ... quetta)", "ro": "Prefixe SI complete (quecto ... quetta)"},

    # ===================================================================
    # Filter Simulator enhancements
    # ===================================================================
    "filter.modulated_toggle": {"en": "Modulated (AM) input signal", "ro": "Semnal de intrare modulat (AM)"},
    "filter.carrier_freq": {"en": "Carrier freq. (Hz)", "ro": "Frecv. purtătoare (Hz)"},
    "filter.mod_freq": {"en": "Modulation freq. (Hz)", "ro": "Frecv. de modulație (Hz)"},
    "filter.mod_index": {"en": "Modulation index", "ro": "Indice de modulație"},
    "filter.modulated_note": {
        "en": "Showing the AM-modulated carrier at the input vs. the filtered output — "
              "a low-pass filter set well below the carrier will strip the carrier and "
              "recover roughly the modulating envelope.",
        "ro": "Se arată purtătoarea modulată AM la intrare față de ieșirea filtrată — un "
              "filtru trece-jos setat mult sub purtătoare va elimina purtătoarea și va "
              "recupera aproximativ anvelopa de modulație."},
    "filter.calc_title": {"en": "🧮 Component Calculator", "ro": "🧮 Calculator de Componente"},
    "filter.calc_intro": {
        "en": "Pick a filter topology and a target cutoff frequency, fix one component, "
              "and the calculator solves for the other(s).",
        "ro": "Alege o topologie de filtru și o frecvență de tăiere țintă, fixează o "
              "componentă, iar calculatorul o rezolvă pe cealaltă/celelalte."},
    "filter.calc_type_label": {"en": "Filter type:", "ro": "Tip de filtru:"},
    "filter.calc.type.rc_lp": {"en": "RC Low-pass", "ro": "RC Trece-jos"},
    "filter.calc.type.rc_hp": {"en": "RC High-pass", "ro": "RC Trece-sus"},
    "filter.calc.type.rl_lp": {"en": "RL Low-pass", "ro": "RL Trece-jos"},
    "filter.calc.type.rl_hp": {"en": "RL High-pass", "ro": "RL Trece-sus"},
    "filter.calc.type.rlc_bp": {"en": "RLC Band-pass (series, output across R)",
                                 "ro": "RLC Trece-bandă (serie, ieșire pe R)"},
    "filter.calc.type.rlc_bs": {"en": "RLC Band-stop / Notch (parallel L‖C trap, in series with load)",
                                 "ro": "RLC Opreşte-bandă / Notch (capcană L‖C paralel, în serie cu sarcina)"},
    "filter.calc_cutoff_label": {"en": "Target center freq. f0 (Hz):", "ro": "Frecv. centrală țintă f0 (Hz):"},
    "filter.calc_known_label": {"en": "Fix this component:", "ro": "Fixează această componentă:"},
    "filter.calc_r_label": {"en": "R (Ω)", "ro": "R (Ω)"},
    "filter.calc_l_label": {"en": "L (H)", "ro": "L (H)"},
    "filter.calc_c_label": {"en": "C (F)", "ro": "C (F)"},
    "filter.calc_q_label": {"en": "Quality factor Q:", "ro": "Factor de calitate Q:"},
    "filter.calc_button": {"en": "Calculate", "ro": "Calculează"},
    "filter.calc_apply_button": {"en": "Apply to network above ↑", "ro": "Aplică la rețeaua de mai sus ↑"},
    "filter.calc_applied_note": {"en": "Applied to the network above.", "ro": "Aplicat la rețeaua de mai sus."},
    "filter.calc_invalid": {"en": "Enter valid positive numbers.", "ro": "Introduceți numere pozitive valide."},
    "filter.calc_rlc_bp_note": {
        "en": "Series RLC band-pass: R, L and C in series, output taken across R. "
              "f0 = 1/(2π√(LC)); Q = ω0·L/R (higher Q ⇒ narrower passband). "
              "Values are shown for reference — build them as two cascaded stages "
              "above (R+L, then the result in series with C) to see the response.",
        "ro": "RLC trece-bandă serie: R, L și C în serie, ieșirea se ia pe R. "
              "f0 = 1/(2π√(LC)); Q = ω0·L/R (Q mai mare ⇒ bandă mai îngustă). "
              "Valorile sunt afișate ca referință — construiește-le ca două etape "
              "în cascadă mai sus (R+L, apoi rezultatul în serie cu C) pentru a vedea răspunsul."},
    "filter.calc_rlc_bs_note": {
        "en": "Parallel RLC notch/band-stop: L and C in parallel (a resonant tank) placed "
              "in series with the load R. Near f0 the tank's impedance is very high and "
              "blocks that band; away from f0 it passes. f0 = 1/(2π√(LC)); "
              "Q = R/(ω0·L) = ω0·R·C (higher Q ⇒ narrower notch). A plain series RLC "
              "circuit is NOT automatically a band-stop network — with the output taken "
              "across R it is actually a band-pass network (see the band-pass option above).",
        "ro": "Notch/opreşte-bandă RLC paralel: L și C în paralel (un circuit rezonant) "
              "montat în serie cu sarcina R. Aproape de f0 impedanța circuitului rezonant "
              "este foarte mare și blochează acea bandă; departe de f0, semnalul trece. "
              "f0 = 1/(2π√(LC)); Q = R/(ω0·L) = ω0·R·C (Q mai mare ⇒ notch mai îngust). "
              "Un simplu circuit RLC serie NU este automat un filtru opreşte-bandă — cu "
              "ieșirea luată pe R, acesta este de fapt un filtru trece-bandă (vezi opțiunea "
              "de mai sus)."},

    # ===================================================================
    # AC/DC Basics restructuring
    # ===================================================================
    "basics.subtab.ohms_law": {"en": "Ohm's Law", "ro": "Legea lui Ohm"},
    "basics.subtab.kirchhoff": {"en": "Kirchhoff's Laws", "ro": "Legile lui Kirchhoff"},

    # ===================================================================
    # Kirchhoff's Laws sub-tab
    # ===================================================================
    "kirch.kvl_title": {"en": "Kirchhoff's Voltage Law (KVL)", "ro": "Legea lui Kirchhoff pentru Tensiune (KVL)"},
    "kirch.kvl_intro": {
        "en": "Around any closed loop, the algebraic sum of all voltages is zero: the "
              "source voltage equals the sum of the drops across every resistor in the loop.",
        "ro": "Pe orice buclă închisă, suma algebrică a tuturor tensiunilor este zero: "
              "tensiunea sursei este egală cu suma căderilor de tensiune pe fiecare "
              "rezistor din buclă."},
    "kirch.source_label": {"en": "Source voltage V (V):", "ro": "Tensiune sursă V (V):"},
    "kirch.resistor_label": {"en": "R{n} (Ω):", "ro": "R{n} (Ω):"},
    "kirch.add_resistor": {"en": "+ Add resistor", "ro": "+ Adaugă rezistor"},
    "kirch.remove_resistor": {"en": "− Remove", "ro": "− Elimină"},
    "kirch.current_result": {"en": "Loop current I = V / ΣR", "ro": "Curent de buclă I = V / ΣR"},
    "kirch.loop_eq_label": {"en": "Loop equation (KVL check):", "ro": "Ecuația buclei (verificare KVL):"},
    "kirch.kcl_title": {"en": "Kirchhoff's Current Law (KCL)", "ro": "Legea lui Kirchhoff pentru Curent (KCL)"},
    "kirch.kcl_intro": {
        "en": "At any node, the currents flowing in equal the currents flowing out. Set "
              "the direction and value for each branch — the branch marked \"solve\" is "
              "computed so the node balances.",
        "ro": "În orice nod, curenții care intră sunt egali cu curenții care ies. "
              "Setează direcția și valoarea pentru fiecare ramură — ramura marcată "
              "\"rezolvă\" este calculată astfel încât nodul să fie echilibrat."},
    "kirch.branch_label": {"en": "Branch I{n} (A):", "ro": "Ramura I{n} (A):"},
    "kirch.direction_in": {"en": "In →", "ro": "Intră →"},
    "kirch.direction_out": {"en": "Out →", "ro": "Iese →"},
    "kirch.solve_for": {"en": "Solve for:", "ro": "Rezolvă pentru:"},
    "kirch.sum_check_label": {"en": "Node balance (KCL check):", "ro": "Echilibrul nodului (verificare KCL):"},
    "kirch.invalid": {"en": "Enter valid numeric currents.", "ro": "Introduceți valori de curent numerice valide."},
    "kirch.balanced": {"en": "✓ Balanced — ΣI_in = ΣI_out", "ro": "✓ Echilibrat — ΣI_intrare = ΣI_ieșire"},

    "theory.kirchhoff.title": {"en": "Kirchhoff's Laws", "ro": "Legile lui Kirchhoff"},
    "theory.kirchhoff.what": {
        "en": "Kirchhoff's Voltage Law (KVL) and Current Law (KCL) are the two "
              "bookkeeping rules that let you analyze any circuit, no matter how "
              "complex. A node is a point where two or more branches (circuit "
              "elements) connect; a branch carries a single current; a loop is any "
              "closed path traced through branches back to its starting node.",
        "ro": "Legea Tensiunii (KVL) și Legea Curentului (KCL) ale lui Kirchhoff sunt "
              "cele două reguli de contabilitate care permit analiza oricărui circuit, "
              "indiferent de complexitate. Un nod este un punct unde se conectează "
              "două sau mai multe ramuri (elemente de circuit); o ramură transportă "
              "un singur curent; o buclă este orice traseu închis parcurs prin ramuri "
              "înapoi la nodul de plecare."},
    "theory.kirchhoff.how": {
        "en": "KCL says charge is conserved at a node: ΣIin = ΣIout, i.e. whatever "
              "current flows in must flow back out — current direction (arrows you "
              "assign) is a bookkeeping choice; a negative result just means the "
              "actual current flows opposite to the assumed direction. KVL says "
              "energy is conserved around a loop: ΣV = 0, i.e. the sum of voltage "
              "rises and drops around any closed path is zero — this depends on a "
              "consistent sign convention: pick a traversal direction around the "
              "loop, and treat a voltage as a rise (+) or drop (−) based on which "
              "terminal (+ or −) you enter first for each element; KVL is NOT "
              "independent of that sign convention, it simply must be applied "
              "consistently once chosen. Both laws follow from two conservation "
              "principles: KCL from conservation of charge, KVL from conservation "
              "of energy.",
        "ro": "KCL spune că sarcina se conservă într-un nod: ΣIintrare = ΣIieșire, "
              "adică tot curentul care intră trebuie să iasă — direcția curentului "
              "(săgețile pe care le alegi) este o convenție de notare; un rezultat "
              "negativ înseamnă doar că, curentul real circulă opus direcției "
              "presupuse. KVL spune că energia se conservă pe o buclă: ΣV = 0, "
              "adică suma creșterilor și căderilor de tensiune pe orice traseu "
              "închis este zero — aceasta depinde de o convenție de semn "
              "consecventă: alege o direcție de parcurgere a buclei și tratează o "
              "tensiune ca o creștere (+) sau o cădere (−) în funcție de care bornă "
              "(+ sau −) este întâlnită prima pentru fiecare element; KVL NU este "
              "independentă de această convenție de semn, trebuie doar aplicată "
              "consecvent odată aleasă. Ambele legi decurg din două principii de "
              "conservare: KCL din conservarea sarcinii electrice, KVL din "
              "conservarea energiei."},
    "theory.kirchhoff.f.kvl": {"en": "Voltage Law", "ro": "Legea Tensiunii"},
    "theory.kirchhoff.f.kcl": {"en": "Current Law", "ro": "Legea Curentului"},
    "theory.kirchhoff.f.ohms_law": {"en": "Ohm's Law", "ro": "Legea lui Ohm"},
    "theory.kirchhoff.f.series_current": {"en": "Series current", "ro": "Curent de serie"},

    # ===================================================================
    # AC Circuits & Phasor Visualizer tab
    # ===================================================================
    "ac.tab_title": {"en": "∿ AC Circuits & Phasors", "ro": "∿ Circuite AC & Fazori"},
    "ac.subtab.passive": {"en": "Passive AC Circuits", "ro": "Circuite AC Pasive"},
    "ac.subtab.power": {"en": "AC Power Systems", "ro": "Sisteme de Putere AC"},

    "ac.passive.intro": {
        "en": "Pick a series RC, RL, or RLC network, set the source frequency, and see "
              "the impedance triangle, phasor diagram, and power breakdown update live.",
        "ro": "Alege o rețea serie RC, RL sau RLC, setează frecvența sursei și "
              "urmărește triunghiul de impedanță, diagrama fazorială și distribuția "
              "puterii actualizându-se în timp real."},
    "ac.passive.circuit_label": {"en": "Circuit:", "ro": "Circuit:"},
    "ac.passive.r_label": {"en": "R (Ω)", "ro": "R (Ω)"},
    "ac.passive.l_label": {"en": "L (H)", "ro": "L (H)"},
    "ac.passive.c_label": {"en": "C (F)", "ro": "C (F)"},
    "ac.passive.freq_label": {"en": "Frequency (Hz)", "ro": "Frecvență (Hz)"},
    "ac.passive.vsource_label": {"en": "Source V (peak, V)", "ro": "Sursă V (vârf, V)"},
    "ac.passive.results_title": {"en": "Results", "ro": "Rezultate"},
    "ac.passive.impedance_label": {"en": "Impedance |Z|:", "ro": "Impedanță |Z|:"},
    "ac.passive.phase_label": {"en": "Phase angle θ:", "ro": "Unghi de fază θ:"},
    "ac.passive.current_label": {"en": "Current I (peak):", "ro": "Curent I (vârf):"},
    "ac.passive.pf_label": {"en": "Power factor cos φ:", "ro": "Factor de putere cos φ:"},
    "ac.passive.power_p": {"en": "Active power P:", "ro": "Putere activă P:"},
    "ac.passive.power_q": {"en": "Reactive power Q:", "ro": "Putere reactivă Q:"},
    "ac.passive.power_s": {"en": "Apparent power S:", "ro": "Putere aparentă S:"},
    "ac.passive.diagram_title": {"en": "Phasor Diagram (V & I, independent scales)",
                                  "ro": "Diagramă Fazorială (V & I, scări independente)"},
    "ac.passive.invalid": {"en": "Enter valid positive component values.",
                            "ro": "Introduceți valori pozitive valide pentru componente."},
    "ac.circuit.rc": {"en": "RC (series)", "ro": "RC (serie)"},
    "ac.circuit.rl": {"en": "RL (series)", "ro": "RL (serie)"},
    "ac.circuit.rlc": {"en": "RLC (series)", "ro": "RLC (serie)"},

    "ac.power.intro": {
        "en": "Choose a supply system and enter the phase quantities — the tool derives "
              "line values, draws the phasor star, and totals the real/reactive/apparent power.",
        "ro": "Alege un sistem de alimentare și introdu mărimile de fază — unealta "
              "deduce valorile de linie, desenează steaua fazorială și totalizează "
              "puterea activă/reactivă/aparentă."},
    "ac.power.system_label": {"en": "System:", "ro": "Sistem:"},
    "ac.power.vphase_label": {"en": "Phase voltage Vp (V)", "ro": "Tensiune de fază Vp (V)"},
    "ac.power.iphase_label": {"en": "Phase current Ip (A)", "ro": "Curent de fază Ip (A)"},
    "ac.power.pf_angle_label": {"en": "PF angle φ (°)", "ro": "Unghi FP φ (°)"},
    "ac.power.freq_label": {"en": "Frequency (Hz)", "ro": "Frecvență (Hz)"},
    "ac.power.waveform_title": {"en": "Waveforms (v & i vs. time)", "ro": "Forme de undă (v & i vs. timp)"},
    "ac.power.wave_note": {
        "en": "Solid = voltage, dashed = current (independent scales). The dot marks the "
              "instant shown by the phasor diagram; it sweeps left→right as the phasors rotate.",
        "ro": "Continuu = tensiune, întrerupt = curent (scări independente). Punctul "
              "marchează momentul afișat de diagrama fazorială; se deplasează de la stânga "
              "la dreapta pe măsură ce fazorii se rotesc."},
    "ac.power.animate_toggle": {"en": "▶ Animate phasor rotation", "ro": "▶ Animă rotația fazorilor"},
    "ac.power.results_title": {"en": "Results", "ro": "Rezultate"},
    "ac.power.vline_label": {"en": "Line voltage V_L:", "ro": "Tensiune de linie V_L:"},
    "ac.power.iline_label": {"en": "Line current I_L:", "ro": "Curent de linie I_L:"},
    "ac.power.ptotal_label": {"en": "Total P:", "ro": "P total:"},
    "ac.power.qtotal_label": {"en": "Total Q:", "ro": "Q total:"},
    "ac.power.stotal_label": {"en": "Total S:", "ro": "S total:"},
    "ac.power.diagram_title": {"en": "Rotating Phasor Diagram", "ro": "Diagramă Fazorială Rotativă"},
    "ac.power.invalid": {"en": "Enter valid numeric values.", "ro": "Introduceți valori numerice valide."},
    "ac.system.single": {"en": "Single-phase", "ro": "Monofazat"},
    "ac.system.two_phase": {"en": "Two-phase (90°)", "ro": "Bifazat (90°)"},
    "ac.system.three_star": {"en": "Three-phase — Star (Y)", "ro": "Trifazat — Stea (Y)"},
    "ac.system.three_delta": {"en": "Three-phase — Delta (Δ)", "ro": "Trifazat — Triunghi (Δ)"},

    "theory.ac_circuits.title": {"en": "AC Circuits & Power", "ro": "Circuite AC & Putere"},
    "theory.ac_circuits.what": {
        "en": "In AC circuits, resistors, capacitors, and inductors combine into a "
              "complex impedance Z that sets both how much current flows and how far out "
              "of phase it is with the voltage.",
        "ro": "În circuitele AC, rezistoarele, condensatoarele și bobinele se combină "
              "într-o impedanță complexă Z care stabilește atât cât curent circulă, "
              "cât și cât de defazat este acesta față de tensiune."},
    "theory.ac_circuits.how": {
        "en": "A phasor freezes a sinusoid's amplitude and phase as a rotating vector. "
              "Each element has its own impedance: ZR = R (real, no phase shift), "
              "ZL = jωL (positive/inductive reactance, current lags voltage by 90°), "
              "and ZC = 1/(jωC) = -j/(ωC) (negative/capacitive reactance, current "
              "leads voltage by 90°); combined, Z = R + jX with positive X meaning "
              "net inductive, negative X meaning net capacitive, and X = 0 meaning "
              "purely resistive. Voltage and current phasors separated by angle θ "
              "give a power factor cos θ that splits the apparent power S (using RMS "
              "voltage and current) into real power P (does work) and reactive power "
              "Q (sloshes between source and field).",
        "ro": "Un fazor \"îngheață\" amplitudinea și faza unei sinusoide ca vector "
              "rotativ. Fiecare element are propria impedanță: ZR = R (reală, fără "
              "defazaj), ZL = jωL (reactanță pozitivă/inductivă, curentul este defazat "
              "în urma tensiunii cu 90°) și ZC = 1/(jωC) = -j/(ωC) (reactanță negativă/"
              "capacitivă, curentul este defazat înaintea tensiunii cu 90°); combinate, "
              "Z = R + jX, unde X pozitiv înseamnă caracter inductiv net, X negativ "
              "înseamnă caracter capacitiv net, iar X = 0 înseamnă caracter pur "
              "rezistiv. Fazorii de tensiune și curent separați printr-un unghi θ dau "
              "un factor de putere cos θ care împarte puterea aparentă S (folosind "
              "valori RMS de tensiune și curent) în putere activă P (efectuează lucru "
              "mecanic) și putere reactivă Q (oscilează între sursă și câmp)."},
    "theory.ac_circuits.f.mag_phase": {"en": "Magnitude & phase", "ro": "Modul & fază"},
    "theory.ac_circuits.f.power_factor": {"en": "Power factor", "ro": "Factor de putere"},
    "theory.ac_circuits.f.powers": {"en": "Power triangle", "ro": "Triunghiul puterilor"},
    "theory.ac_circuits.f.three_phase_y": {"en": "Three-phase star", "ro": "Trifazat stea"},
    "theory.ac_circuits.f.three_phase_d": {"en": "Three-phase delta", "ro": "Trifazat triunghi"},
    "theory.ac_circuits.f.zr": {"en": "Resistor impedance", "ro": "Impedanța rezistorului"},
    "theory.ac_circuits.f.zl": {"en": "Inductor impedance", "ro": "Impedanța bobinei"},
    "theory.ac_circuits.f.zc": {"en": "Capacitor impedance", "ro": "Impedanța condensatorului"},
    "theory.ac_circuits.f.ohms_law_ac": {"en": "Ohm's law (AC, phasor form)", "ro": "Legea lui Ohm (AC, formă fazorială)"},
    "theory.ac_circuits.f.reactance_sign": {"en": "Reactance sign convention", "ro": "Convenția de semn a reactanței"},
    "theory.ac_circuits.f.three_phase_power": {"en": "Three-phase power (balanced)", "ro": "Putere trifazată (echilibrată)"},

    # ===================================================================
    # Signal Generator sub-tab
    # ===================================================================
    "sig.tab_title": {"en": "🌊 Signal Generator", "ro": "🌊 Generator de Semnal"},
    "sig.intro": {
        "en": "Generate a standard waveform and tune its parameters live — the controls "
              "shown adapt to the waveform you pick (e.g. duty cycle only matters for "
              "square/triangle waves).",
        "ro": "Generează o formă de undă standard și ajustează-i parametrii în timp "
              "real — comenzile afișate se adaptează la forma de undă aleasă (de ex. "
              "factorul de umplere contează doar pentru undele dreptunghiulare/triunghiulare)."},
    "sig.wave_label": {"en": "Waveform:", "ro": "Formă de undă:"},
    "sig.wave.sine": {"en": "Sine", "ro": "Sinusoidală"},
    "sig.wave.square": {"en": "Square", "ro": "Dreptunghiulară"},
    "sig.wave.sawtooth": {"en": "Sawtooth", "ro": "Dinte de fierăstrău"},
    "sig.wave.triangle": {"en": "Triangle", "ro": "Triunghiulară"},
    "sig.freq_label": {"en": "Frequency (Hz)", "ro": "Frecvență (Hz)"},
    "sig.period_label": {"en": "Period (s)", "ro": "Perioadă (s)"},
    "sig.amplitude_label": {"en": "Peak Amplitude (V)", "ro": "Amplitudine de vârf (V)"},
    "sig.offset_label": {"en": "DC offset (V)", "ro": "Offset DC (V)"},
    "sig.duty_label": {"en": "Duty cycle (%)", "ro": "Factor de umplere (%)"},
    "sig.rms_label": {"en": "RMS:", "ro": "RMS:"},
    "sig.pp_label": {"en": "Peak-to-peak:", "ro": "Vârf-la-vârf:"},
    "sig.invalid": {"en": "Enter valid numeric values.", "ro": "Introduceți valori numerice valide."},

    "theory.signal_gen.title": {"en": "Signals & Waveforms", "ro": "Semnale & Forme de Undă"},
    "theory.signal_gen.what": {
        "en": "A periodic signal repeats itself every period T = 1/f. Its shape (sine, "
              "square, sawtooth, triangle) determines its harmonic content and how it "
              "behaves when passed through filters or reactive components. Non-"
              "sinusoidal signals contain harmonics — sine-wave components at integer "
              "multiples of the fundamental frequency.",
        "ro": "Un semnal periodic se repetă la fiecare perioadă T = 1/f. Forma sa "
              "(sinusoidală, dreptunghiulară, dinte de fierăstrău, triunghiulară) "
              "determină conținutul armonic și comportamentul la trecerea prin filtre "
              "sau componente reactive. Semnalele nesinusoidale conțin armonici — "
              "componente sinusoidale la multipli întregi ai frecvenței fundamentale."},
    "theory.signal_gen.how": {
        "en": "Peak amplitude sets the peak swing from the offset (v(t) = Voffset + "
              "A·sin(2πft+φ) for a sine wave); Vpp = 2·Vpeak for an unclipped sine with "
              "no additional waveform asymmetry, but must be measured directly (max−min) "
              "for asymmetric or clipped waveforms. Offset shifts the whole waveform up "
              "or down, and (for square/triangle waves) duty cycle sets how the period "
              "is split between the rising and falling portions (for square waves it "
              "sets the fraction of the period spent high; for sawtooth, it sets the "
              "ramp direction/shape). RMS is defined generally as XRMS = √((1/T)∫x²(t)dt) "
              "— or for discrete samples, XRMS = √((1/N)Σxₙ²) — and only reduces to the "
              "sine-only shortcut Vrms = Vpeak/√2 for a pure, zero-offset sine wave; it "
              "does NOT apply directly to square/triangle/sawtooth waves or to signals "
              "with a DC offset. This app computes RMS directly from the sampled "
              "waveform, so it is correct for any shape. When a periodic signal has a "
              "DC component plus a zero-mean AC part, the total RMS follows "
              "Vrms_total² = VDC² + Vrms_AC² — the displayed RMS is the *total* RMS "
              "(including any offset), not just the AC component.",
        "ro": "Amplitudinea de vârf stabilește excursia de vârf față de offset (v(t) = "
              "Voffset + A·sin(2πft+φ) pentru o sinusoidă); Vpp = 2·Vvârf pentru o "
              "sinusoidă netăiată fără altă asimetrie a formei de undă, dar trebuie "
              "măsurat direct (max−min) pentru forme de undă asimetrice sau tăiate. "
              "Offset-ul deplasează întreaga formă de undă în sus sau în jos, iar "
              "(pentru undele dreptunghiulare/triunghiulare) factorul de umplere "
              "stabilește cum este împărțită perioada între porțiunile de creștere și "
              "scădere (pentru unde dreptunghiulare stabilește fracțiunea din perioadă "
              "petrecută la nivel înalt; pentru dinte de fierăstrău, direcția/forma "
              "rampei). RMS este definit general ca XRMS = √((1/T)∫x²(t)dt) — sau, "
              "pentru eșantioane discrete, XRMS = √((1/N)Σxₙ²) — și se reduce la "
              "scurtătura valabilă doar pentru sinusoidă Vrms = Vvârf/√2 numai pentru o "
              "sinusoidă pură, fără offset; NU se aplică direct undelor dreptunghiulare/"
              "triunghiulare/dinte de fierăstrău sau semnalelor cu offset DC. Această "
              "aplicație calculează RMS direct din forma de undă eșantionată, deci este "
              "corect pentru orice formă. Când un semnal periodic are o componentă DC "
              "plus o parte AC cu medie zero, RMS-ul total urmează "
              "Vrms_total² = VDC² + Vrms_AC² — RMS-ul afișat este RMS-ul *total* "
              "(inclusiv orice offset), nu doar componenta AC."},
    "theory.signal_gen.f.angular": {"en": "Angular frequency", "ro": "Frecvență unghiulară"},
    "theory.signal_gen.f.duty": {"en": "Duty cycle", "ro": "Factor de umplere"},
    "theory.signal_gen.f.sine": {"en": "Sine wave", "ro": "Undă sinusoidală"},
    "theory.signal_gen.f.vpp": {"en": "Peak-to-peak (unclipped sine)", "ro": "Vârf-la-vârf (sinusoidă netăiată)"},
    "theory.signal_gen.f.rms_general": {"en": "RMS (general, continuous)", "ro": "RMS (general, continuu)"},
    "theory.signal_gen.f.rms_discrete": {"en": "RMS (general, discrete samples)", "ro": "RMS (general, eșantioane discrete)"},
    "theory.signal_gen.f.rms_sine_shortcut": {"en": "RMS shortcut (sine only!)", "ro": "Scurtătură RMS (doar sinusoidă!)"},
    "theory.signal_gen.f.rms_with_offset": {"en": "Total RMS with DC offset", "ro": "RMS total cu offset DC"},

    # ===================================================================
    # New navigation entry (Modulation sub-tab under Signals)
    # ===================================================================
    "nav.modulation": {"en": "Modulation", "ro": "Modulație"},

    # ===================================================================
    # Unit Converter: inner sub-tab labels
    # ===================================================================
    "uc.subtab.prefix": {"en": "Prefix Converter", "ro": "Convertor de Prefixe"},
    "uc.subtab.db": {"en": "dB / Ratios", "ro": "dB / Rapoarte"},
    "uc.subtab.base": {"en": "Number Base / ADC-DAC", "ro": "Bază Numerică / ADC-DAC"},

    # ===================================================================
    # dB Calculator (Unit Converter > dB / Ratios)
    # ===================================================================
    "db.r2db_title": {"en": "Ratio → dB", "ro": "Raport → dB"},
    "db.r2db_intro": {
        "en": "Enter two values and see the ratio expressed in dB both ways at "
              "once — the same numbers give a different dB figure depending on "
              "whether they're powers or voltages/currents.",
        "ro": "Introdu două valori și vezi raportul exprimat în dB în ambele "
              "moduri simultan — aceleași numere dau o valoare dB diferită după "
              "cum sunt puteri sau tensiuni/curenți."},
    "db.impedance_note": {
        "en": "The 20×log10 voltage/current formula corresponds to the same dB "
              "figure as the power-ratio formula only when the relevant "
              "impedances are equal (or unchanged) between the two "
              "measurements — e.g. same load resistance, same reference "
              "impedance. If the impedance differs, the two numbers above are "
              "not interchangeable.",
        "ro": "Formula 20×log10 pentru tensiune/curent corespunde aceleiași "
              "valori dB ca formula raportului de putere doar atunci când "
              "impedanțele relevante sunt egale (sau neschimbate) între cele "
              "două măsurători — de ex. aceeași rezistență de sarcină, aceeași "
              "impedanță de referință. Dacă impedanța diferă, cele două valori "
              "de mai sus nu sunt interschimbabile."},
    "db.value1_label": {"en": "Value 1 (reference):", "ro": "Valoarea 1 (referință):"},
    "db.value2_label": {"en": "Value 2:", "ro": "Valoarea 2:"},
    "db.as_power_label": {"en": "As a power ratio (10×log₁₀):", "ro": "Ca raport de putere (10×log₁₀):"},
    "db.as_voltage_label": {"en": "As a voltage/current ratio (20×log₁₀):",
                             "ro": "Ca raport de tensiune/curent (20×log₁₀):"},
    "db.db2r_title": {"en": "dB → Ratio", "ro": "dB → Raport"},
    "db.db2r_intro": {
        "en": "The reverse direction: enter a dB figure and a reference value, "
              "get the other value under both interpretations.",
        "ro": "Direcția inversă: introdu o valoare în dB și o valoare de "
              "referință, obții cealaltă valoare în ambele interpretări."},
    "db.db_value_label": {"en": "dB value:", "ro": "Valoare dB:"},
    "db.ref_value_label": {"en": "Reference value (Value 1):", "ro": "Valoare de referință (Valoarea 1):"},
    "db.abs_title": {"en": "Absolute Levels (dBm / dBW)", "ro": "Niveluri Absolute (dBm / dBW)"},
    "db.abs_intro": {
        "en": "dBm and dBW are power levels relative to a fixed reference (1 mW "
              "or 1 W) rather than a ratio between two of your own values.",
        "ro": "dBm și dBW sunt niveluri de putere relative la o referință fixă "
              "(1 mW sau 1 W), nu un raport între două valori proprii."},
    "db.power_value_label": {"en": "Power value:", "ro": "Valoare putere:"},
    "db.db_abs_value_label": {"en": "dB value:", "ro": "Valoare dB:"},
    "db.invalid": {"en": "Enter valid positive numbers.", "ro": "Introduceți numere pozitive valide."},
    "db.quick_ref_title": {"en": "dB Quick Reference", "ro": "Referință Rapidă dB"},
    "db.quick_ref_note": {
        "en": "The \"muscle memory\" values worth just knowing by heart.",
        "ro": "Valorile de \"memorat pe de rost\" care merită știute din cap."},
    "db.table.db": {"en": "dB", "ro": "dB"},
    "db.table.power_ratio": {"en": "Power ratio", "ro": "Raport putere"},
    "db.table.voltage_ratio": {"en": "Voltage/current ratio", "ro": "Raport tensiune/curent"},

    # ===================================================================
    # AC/DC Basics: Troubleshooting sub-tab
    # ===================================================================
    "basics.subtab.troubleshoot": {"en": "Troubleshooting", "ro": "Depanare"},

    "tol.title": {"en": "🧮 Component Tolerance Calculator", "ro": "🧮 Calculator Toleranță Componente"},
    "tol.intro": {
        "en": "Pick a mode and see the true worst-case range — not just added "
              "percentages. A voltage-divider ratio, for instance, doesn't hit "
              "its extremes when both resistors are at their max at once.",
        "ro": "Alege un mod și vezi intervalul real de caz cel mai defavorabil — "
              "nu doar procente adunate. De exemplu, raportul unui divizor de "
              "tensiune nu atinge extremele când ambele rezistențe sunt la maxim simultan."},
    "tol.mode_label": {"en": "Mode:", "ro": "Mod:"},
    "tol.mode.single": {"en": "Single component", "ro": "O singură componentă"},
    "tol.mode.stack": {"en": "Series/Parallel stack-up", "ro": "Combinație Serie/Paralel"},
    "tol.mode.divider": {"en": "Voltage-divider ratio", "ro": "Raport divizor de tensiune"},
    "tol.nominal_label": {"en": "Nominal value:", "ro": "Valoare nominală:"},
    "tol.tolerance_pct_label": {"en": "Tolerance (%):", "ro": "Toleranță (%):"},
    "tol.range_label": {"en": "Range:", "ro": "Interval:"},
    "tol.invalid": {"en": "Enter valid numbers.", "ro": "Introduceți numere valide."},
    "tol.combo_type_label": {"en": "Combination:", "ro": "Combinație:"},
    "tol.component_label": {"en": "Component {n}:", "ro": "Componenta {n}:"},
    "tol.add_component": {"en": "+ Add component", "ro": "+ Adaugă componentă"},
    "tol.remove_component": {"en": "− Remove", "ro": "− Elimină"},
    "tol.nominal_result_label": {"en": "Nominal:", "ro": "Nominal:"},
    "tol.worst_case_label": {"en": "Worst-case:", "ro": "Caz defavorabil:"},
    "tol.rss_label": {"en": "RSS estimate:", "ro": "Estimare RSS:"},
    "tol.rss_caveat": {
        "en": "RSS assumes each component's error is independent and random — "
              "it's a realistic statistical estimate, not a guarantee. For a "
              "safety-critical design, use the worst-case range instead.",
        "ro": "RSS presupune că eroarea fiecărei componente este independentă și "
              "aleatorie — este o estimare statistică realistă, nu o garanție. "
              "Pentru un proiect critic pentru siguranță, folosiți intervalul de caz defavorabil."},
    "tol.divider_intro": {
        "en": "R2/(R1+R2): increasing R1 pushes the ratio down while increasing "
              "R2 pushes it up, so the true min/max isn't \"everything at max.\"",
        "ro": "R2/(R1+R2): creșterea lui R1 scade raportul, în timp ce creșterea "
              "lui R2 îl crește, deci min/max real nu înseamnă \"totul la maxim\"."},
    "tol.r1_label": {"en": "R1:", "ro": "R1:"},
    "tol.r2_label": {"en": "R2:", "ro": "R2:"},
    "tol.ratio_nominal_label": {"en": "Nominal ratio:", "ro": "Raport nominal:"},

    "ict.title": {"en": "🔍 ICT Debug Helper", "ro": "🔍 Asistent de Depanare"},
    "ict.disclaimer": {
        "en": "This is a heuristic reasoning aid based on simple thresholds, "
              "not a real fault-detection algorithm — it's meant to teach the "
              "thought process, not replace it.",
        "ro": "Acesta este un instrument euristic de raționament bazat pe praguri "
              "simple, nu un algoritm real de detectare a defectelor — este "
              "menit să învețe procesul de gândire, nu să îl înlocuiască."},
    "ict.res_title": {"en": "Resistance Mode", "ro": "Mod Rezistență"},
    "ict.res_intro": {
        "en": "Enter the expected value and (optionally) what else loads it "
              "in-circuit, then compare against what you measured.",
        "ro": "Introdu valoarea așteptată și (opțional) ce altceva o încarcă în "
              "circuit, apoi compară cu ce ai măsurat."},
    "ict.expected_r_label": {"en": "Expected R:", "ro": "R așteptat:"},
    "ict.loaded_toggle": {"en": "Loaded by another resistance in-circuit", "ro": "Încărcat de o altă rezistență în circuit"},
    "ict.load_r_label": {"en": "Loading R:", "ro": "R de încărcare:"},
    "ict.measured_label": {"en": "Measured value:", "ro": "Valoare măsurată:"},
    "ict.expected_range_label": {"en": "Expected in-circuit range:", "ro": "Interval așteptat în circuit:"},
    "ict.nominal_word": {"en": "nominal", "ro": "nominal"},
    "ict.volt_title": {"en": "Voltage Mode", "ro": "Mod Tensiune"},
    "ict.volt_intro": {
        "en": "For a node between R1 (to the supply) and R2 (to ground), "
              "compare the expected node voltage to what you measured.",
        "ro": "Pentru un nod între R1 (spre sursă) și R2 (spre masă), compară "
              "tensiunea așteptată a nodului cu ce ai măsurat."},
    "ict.vsupply_label": {"en": "Supply voltage:", "ro": "Tensiune de alimentare:"},
    "ict.measured_v_label": {"en": "Measured node voltage:", "ro": "Tensiune măsurată la nod:"},
    "ict.cheatsheet_title": {"en": "Symptom → Likely Cause", "ro": "Simptom → Cauză Probabilă"},
    "ict.cheat.1": {"en": "Measures ~0 Ω exactly → dead short.",
                     "ro": "Măsoară ~0 Ω exact → scurtcircuit."},
    "ict.cheat.2": {"en": "Meter reads OL (overload/infinite) → open circuit.",
                     "ro": "Multimetrul indică OL (suprasarcină/infinit) → circuit deschis."},
    "ict.cheat.3": {"en": "Measures ~2x the expected parallel value → one of two parallel legs is open.",
                     "ro": "Măsoară ~de 2x valoarea paralelă așteptată → una din cele două ramuri paralele e deschisă."},
    "ict.cheat.4": {"en": "Node voltage pulled all the way to supply → open path to ground, or a short to supply.",
                     "ro": "Tensiunea nodului trasă complet spre sursă → cale deschisă spre masă, sau scurtcircuit la sursă."},
    "ict.cheat.5": {"en": "Node voltage pulled all the way to ground → open path to supply, or a short to ground.",
                     "ro": "Tensiunea nodului trasă complet spre masă → cale deschisă spre sursă, sau scurtcircuit la masă."},
    "ict.cheat.6": {"en": "Value drifts with temperature/touch → a marginal solder joint, not the component itself.",
                     "ro": "Valoarea variază cu temperatura/atingerea → o lipitură defectuoasă, nu componenta în sine."},
    "ict.cheat.7": {"en": "Always power the circuit OFF before taking resistance measurements — measuring resistance on a live circuit gives meaningless readings and can damage the meter.",
                     "ro": "Deconectează întotdeauna alimentarea circuitului înainte de a măsura rezistența — măsurarea rezistenței pe un circuit alimentat dă valori fără sens și poate deteriora multimetrul."},
    "ict.cheat.8": {"en": "Discharge capacitors before probing them — a charged capacitor can give a false resistance reading, damage the meter, or shock you.",
                     "ro": "Descarcă condensatoarele înainte de a le testa — un condensator încărcat poate da o citire falsă de rezistență, poate deteriora multimetrul sau te poate electrocuta."},
    "ict.cheat.9": {"en": "Diode-test mode reads the forward voltage drop (not resistance) and only works with the circuit unpowered; a healthy silicon junction typically reads ~0.5-0.8 V one way and OL the other.",
                     "ro": "Modul de testare a diodelor citește căderea de tensiune directă (nu rezistența) și funcționează doar cu circuitul deconectat; o joncțiune de siliciu sănătoasă indică de obicei ~0,5-0,8 V într-un sens și OL în celălalt."},
    "ict.cheat.10": {"en": "Continuity mode is a threshold check (usually a beep below a few Ω) — it can miss a high-resistance partial fault that isn't a dead short or a clean open.",
                      "ro": "Modul de continuitate este o verificare de prag (de obicei sonerie sub câțiva Ω) — poate rata un defect parțial de rezistență mare, care nu e nici scurtcircuit franc, nici circuit deschis curat."},
    "ict.cheat.11": {"en": "A lifted pad/pin (not making contact) can read like an open even though the component itself is fine — check for physical/visual clues too, not just the meter.",
                      "ro": "Un pad/pin ridicat (fără contact) poate indica un circuit deschis chiar dacă, componenta în sine este bună — verifică și indicii fizice/vizuale, nu doar multimetrul."},
    "ict.cheat.12": {"en": "Every measurement has uncertainty (meter accuracy, probe contact, component tolerance) — a reading just outside the expected range is a clue to investigate further, not automatic proof of a fault.",
                      "ro": "Orice măsurătoare are o incertitudine (precizia multimetrului, contactul sondelor, toleranța componentei) — o valoare puțin în afara intervalului așteptat este un indiciu de investigat, nu o dovadă automată de defect."},

    "tsh.class.ok": {"en": "✓ Within expected range.", "ro": "✓ În intervalul așteptat."},
    "tsh.class.short": {"en": "⚠ Likely short — reads far below the expected range, near 0.",
                         "ro": "⚠ Probabil scurtcircuit — citește mult sub intervalul așteptat, aproape de 0."},
    "tsh.class.open": {"en": "⚠ Likely open — reads far above the expected range (or OL).",
                        "ro": "⚠ Probabil circuit deschis — citește mult peste intervalul așteptat (sau OL)."},
    "tsh.class.pulled_high": {"en": "⚠ Pulled toward supply — check for an open path to ground, or a short to supply.",
                               "ro": "⚠ Trasă spre sursă — verifică o cale deschisă spre masă, sau scurtcircuit la sursă."},
    "tsh.class.pulled_low": {"en": "⚠ Pulled toward ground — check for an open path to supply, or a short to ground.",
                              "ro": "⚠ Trasă spre masă — verifică o cale deschisă spre sursă, sau scurtcircuit la masă."},
    "tsh.class.check": {"en": "? Outside tolerance but not clearly open/short — check neighboring components.",
                         "ro": "? În afara toleranței dar nu clar deschis/scurt — verifică componentele vecine."},

    "theory.troubleshooting.title": {"en": "Tolerance & Fault Reasoning", "ro": "Toleranță & Raționament de Defecte"},
    "theory.troubleshooting.what": {
        "en": "Real components never hit their nominal value exactly. Tolerance "
              "stack-up tells you the realistic range a measurement should fall "
              "in — the starting point for deciding whether something you "
              "measured is normal or a sign of a fault.",
        "ro": "Componentele reale nu ating niciodată exact valoarea nominală. "
              "Calculul toleranței cumulate arată intervalul realist în care ar "
              "trebui să se încadreze o măsurătoare — punctul de plecare pentru "
              "a decide dacă ceva măsurat este normal sau semn de defect."},
    "theory.troubleshooting.how": {
        "en": "For a simple sum (series resistors), the worst case is everything "
              "at its max or everything at its min. For anything with mixed "
              "effects (like a divider ratio), each part's own extreme has to "
              "be chosen based on which direction it actually pushes the result.",
        "ro": "Pentru o sumă simplă (rezistențe în serie), cazul cel mai "
              "defavorabil este totul la maxim sau totul la minim. Pentru orice "
              "are efecte mixte (precum raportul unui divizor), extrema fiecărei "
              "părți trebuie aleasă în funcție de direcția în care împinge efectiv rezultatul."},
    "theory.troubleshooting.f.range": {"en": "Single-component range", "ro": "Interval componentă unică"},
    "theory.troubleshooting.f.divider": {"en": "Divider ratio", "ro": "Raport divizor"},
    "theory.troubleshooting.f.rss": {"en": "RSS stack-up", "ro": "Cumul RSS"},
    "theory.troubleshooting.f.short": {"en": "Short symptom", "ro": "Simptom scurtcircuit"},
    "theory.troubleshooting.f.open": {"en": "Open symptom", "ro": "Simptom circuit deschis"},

    # ===================================================================
    # Signals: Modulation sub-tab
    # ===================================================================
    "mod.tab_title": {"en": "📡 Modulation", "ro": "📡 Modulație"},
    "mod.subtab.calculator": {"en": "Modulator", "ro": "Modulator"},
    "mod.intro": {
        "en": "Modulate a message signal (any shape) onto a carrier and watch "
              "the result — plus its frequency spectrum — update live.",
        "ro": "Modulează un semnal mesaj (orice formă) pe o purtătoare și "
              "urmărește rezultatul — plus spectrul de frecvență — actualizându-se live."},
    "mod.type_label": {"en": "Modulation type:", "ro": "Tip de modulație:"},
    "mod.type.am": {"en": "AM (Amplitude)", "ro": "AM (Amplitudine)"},
    "mod.type.fm": {"en": "FM (Frequency)", "ro": "FM (Frecvență)"},
    "mod.type.pm": {"en": "PM (Phase)", "ro": "PM (Fază)"},
    "mod.message_title": {"en": "Message Signal", "ro": "Semnal Mesaj"},
    "mod.msg_freq_label": {"en": "Message frequency (Hz)", "ro": "Frecvență mesaj (Hz)"},
    "mod.msg_amp_label": {"en": "Message amplitude", "ro": "Amplitudine mesaj"},
    "mod.msg_duty_label": {"en": "Duty cycle (%)", "ro": "Factor de umplere (%)"},
    "mod.carrier_title": {"en": "Carrier", "ro": "Purtătoare"},
    "mod.carrier_freq_label": {"en": "Carrier frequency (Hz)", "ro": "Frecvență purtătoare (Hz)"},
    "mod.carrier_amp_label": {"en": "Carrier amplitude", "ro": "Amplitudine purtătoare"},
    "mod.param_title": {"en": "Modulation Parameter", "ro": "Parametru de Modulație"},
    "mod.am_index_label": {"en": "Modulation index (m)", "ro": "Indice de modulație (m)"},
    "mod.fm_dev_label": {"en": "Frequency deviation Δf (Hz)", "ro": "Deviație de frecvență Δf (Hz)"},
    "mod.pm_dev_label": {"en": "Phase deviation Δφ (°)", "ro": "Deviație de fază Δφ (°)"},
    "mod.demod_toggle": {"en": "Show AM Envelope Visualization", "ro": "Arată Vizualizarea Anvelopei AM"},
    "mod.demod_note": {
        "en": "This is an educational envelope visualization, not a complete AM "
              "receiver/demodulator model.",
        "ro": "Aceasta este o vizualizare educațională a anvelopei, nu un model "
              "complet de receptor/demodulator AM."},
    "mod.results_title": {"en": "Estimated Bandwidth", "ro": "Lățime de Bandă Estimată"},
    "mod.bw_estimate": {"en": "Bandwidth", "ro": "Lățime de bandă"},
    "mod.bw_am_note": {"en": "2x the message frequency, for a single-tone message",
                        "ro": "2x frecvența mesajului, pentru un mesaj cu un singur ton"},
    "mod.bw_pm_note": {"en": "approximated via an effective FM-style deviation",
                        "ro": "aproximată printr-o deviație echivalentă de tip FM"},
    "mod.mod_index_label": {"en": "Modulation index", "ro": "Indice de modulație"},
    "mod.invalid": {"en": "Enter valid numeric values.", "ro": "Introduceți valori numerice valide."},
    "mod.chart_title": {"en": "Message → Carrier → Modulated → Spectrum",
                         "ro": "Mesaj → Purtătoare → Modulat → Spectru"},
    "mod.chart_message": {"en": "Message", "ro": "Mesaj"},
    "mod.chart_carrier": {"en": "Carrier", "ro": "Purtătoare"},
    "mod.chart_modulated": {"en": "Modulated signal", "ro": "Semnal modulat"},
    "mod.chart_spectrum": {"en": "Spectrum (FFT magnitude)", "ro": "Spectru (magnitudine FFT)"},
    "mod.freq_axis": {"en": "Frequency (Hz)", "ro": "Frecvență (Hz)"},

    "theory.modulation.title": {"en": "Modulation", "ro": "Modulație"},
    "theory.modulation.what": {
        "en": "Modulation encodes a low-frequency message onto a high-frequency "
              "carrier so it can be transmitted efficiently — by varying the "
              "carrier's amplitude (AM), frequency (FM), or phase (PM) in step "
              "with the message.",
        "ro": "Modulația codifică un mesaj de joasă frecvență pe o purtătoare de "
              "înaltă frecvență pentru a putea fi transmis eficient — variind "
              "amplitudinea (AM), frecvența (FM) sau faza (PM) purtătoarei în "
              "pas cu mesajul."},
    "theory.modulation.how": {
        "en": "For single-tone AM, the modulation index m = Am/Ac (message amplitude "
              "over carrier amplitude) sets how deep the modulation is: m < 1 is "
              "under-modulation, m = 1 is 100% modulation, and m > 1 is "
              "over-modulation, which distorts the envelope and makes simple "
              "envelope detection unreliable — this app allows m > 1 so you can see "
              "that distortion. AM produces two sidebands mirrored around the "
              "carrier at fUSB = fc + fm and fLSB = fc - fm; for single-tone "
              "conventional AM the total transmitted power is PT = PC·(1 + m²/2), "
              "with efficiency η = m²/(2 + m²) (assuming a single sinusoidal message "
              "and conventional double-sideband AM). FM and PM spread energy across "
              "a wider band that grows with both the deviation and the message "
              "frequency (Carson's rule estimates how wide): BW ≈ 2(Δf + fm) for a "
              "single-tone message; more generally, for a message of bandwidth Bm, "
              "AM bandwidth is BW ≈ 2·Bm and FM bandwidth is BW ≈ 2(Δf + Bm).",
        "ro": "Pentru AM cu un singur ton, indicele de modulație m = Am/Ac (amplitudinea "
              "mesajului raportată la amplitudinea purtătoarei) stabilește cât de "
              "profundă este modulația: m < 1 este sub-modulație, m = 1 este "
              "modulație 100%, iar m > 1 este supra-modulație, care distorsionează "
              "anvelopa și face detecția simplă a anvelopei nesigură — această "
              "aplicație permite m > 1 pentru a putea observa această distorsiune. AM "
              "produce două benzi laterale oglindite în jurul purtătoarei, la "
              "fUSB = fc + fm și fLSB = fc - fm; pentru AM convențională cu un "
              "singur ton, puterea totală transmisă este PT = PC·(1 + m²/2), cu "
              "randamentul η = m²/(2 + m²) (presupunând un mesaj sinusoidal unic și "
              "AM convențională cu bandă laterală dublă). FM și PM răspândesc energia "
              "pe o bandă mai largă, care crește atât cu deviația cât și cu frecvența "
              "mesajului (regula lui Carson estimează cât de largă): BW ≈ 2(Δf + fm) "
              "pentru un mesaj cu un singur ton; mai general, pentru un mesaj cu "
              "lățimea de bandă Bm, lățimea de bandă AM este BW ≈ 2·Bm, iar cea FM "
              "este BW ≈ 2(Δf + Bm)."},
    "theory.modulation.f.am": {"en": "Amplitude modulation", "ro": "Modulație de amplitudine"},
    "theory.modulation.f.fm": {"en": "Frequency modulation", "ro": "Modulație de frecvență"},
    "theory.modulation.f.pm": {"en": "Phase modulation", "ro": "Modulație de fază"},
    "theory.modulation.f.carson": {"en": "Carson's rule (single-tone FM)", "ro": "Regula lui Carson (FM, un singur ton)"},
    "theory.modulation.f.carson_general": {"en": "Carson's rule (general message)", "ro": "Regula lui Carson (mesaj general)"},
    "theory.modulation.f.am_bw": {"en": "AM bandwidth (single-tone)", "ro": "Lățime de bandă AM (un singur ton)"},
    "theory.modulation.f.am_bw_general": {"en": "AM bandwidth (general message)", "ro": "Lățime de bandă AM (mesaj general)"},
    "theory.modulation.f.am_index": {"en": "AM modulation index", "ro": "Indice de modulație AM"},
    "theory.modulation.f.sidebands": {"en": "AM sidebands", "ro": "Benzi laterale AM"},
    "theory.modulation.f.am_power": {"en": "Total transmitted power (single-tone)", "ro": "Putere totală transmisă (un singur ton)"},
    "theory.modulation.f.am_efficiency": {"en": "Power efficiency", "ro": "Randament de putere"},

    # ===================================================================
    # Modulation chart axis labels (readability pass)
    # ===================================================================
    "mod.amplitude_axis": {"en": "Amplitude", "ro": "Amplitudine"},
    "mod.magnitude_axis": {"en": "Magnitude", "ro": "Magnitudine"},

    # ===================================================================
    # dB calculator: ratio-vs-dB visualization
    # ===================================================================
    "db.chart_title": {"en": "📈 Why the scale isn't linear", "ro": "📈 De ce scala nu este liniară"},
    "db.chart_note": {
        "en": "dB is a log scale, so equal steps in dB are equal MULTIPLES of "
              "the ratio, not equal amounts — that's why the curves below "
              "bend upward instead of forming a straight line. Dots mark your "
              "last Ratio → dB result above.",
        "ro": "dB este o scală logaritmică, deci pași egali în dB înseamnă "
              "multiplii egali ai raportului, nu cantități egale — de aceea "
              "curbele de mai jos se curbează în sus în loc să formeze o "
              "linie dreaptă. Punctele marchează ultimul rezultat Raport → dB de mai sus."},
    "db.chart_xlabel": {"en": "dB", "ro": "dB"},
    "db.chart_ylabel": {"en": "Ratio (linear)", "ro": "Raport (liniar)"},
    "db.chart_power_legend": {"en": "Power ratio (10^(dB/10))", "ro": "Raport putere (10^(dB/10))"},
    "db.chart_voltage_legend": {"en": "Voltage/current ratio (10^(dB/20))", "ro": "Raport tensiune/curent (10^(dB/20))"},

    # ===================================================================
    # RF & Microwave - Multiport RF Simulator
    # ===================================================================
    "nav.group.rf_microwave": {"en": "RF & Microwave", "ro": "RF și Microunde"},
    "rf.tab_title": {"en": "Multiport RF Simulator", "ro": "Simulator RF Multiport"},
    "rf.tab_subtitle": {
        "en": "Build a circuit below, press SIMULATE, then check the Virtual VNA, Smith Chart "
              "and S-Parameter Results tabs to see how it behaves across frequency.",
        "ro": "Construiește un circuit mai jos, apasă SIMULEAZĂ, apoi verifică filele VNA Virtual, "
              "Diagrama Smith și Rezultate Parametri S pentru a vedea comportamentul în frecvență."},

    "rf.subtab.circuit_builder": {"en": "Circuit Builder", "ro": "Constructor de Circuite"},
    "rf.subtab.vna": {"en": "Virtual VNA", "ro": "VNA Virtual"},
    "rf.subtab.smith": {"en": "Smith Chart", "ro": "Diagrama Smith"},
    "rf.subtab.results": {"en": "S-Parameter Results", "ro": "Rezultate Parametri S"},

    "rf.sweep.simulate": {"en": "▶  SIMULATE", "ro": "▶  SIMULEAZĂ"},
    "rf.sweep.start": {"en": "Start Frequency", "ro": "Frecvență de Start"},
    "rf.sweep.stop": {"en": "Stop Frequency", "ro": "Frecvență de Stop"},
    "rf.sweep.points": {"en": "Number of Points", "ro": "Număr de Puncte"},
    "rf.sweep.not_simulated": {"en": "Not simulated yet.", "ro": "Nesimulat încă."},
    "rf.sweep.changed": {"en": "Circuit changed — press SIMULATE to update results.",
                          "ro": "Circuitul s-a schimbat — apasă SIMULEAZĂ pentru rezultate noi."},
    "rf.sweep.error": {"en": "Simulation failed — see error message.", "ro": "Simularea a eșuat — vezi mesajul de eroare."},
    "rf.sweep.ok": {"en": "Simulated {n}-port network, {pts} points.",
                    "ro": "Rețea cu {n} porturi simulată, {pts} puncte."},

    "rf.axis.ghz": {"en": "GHz", "ro": "GHz"},
    "rf.axis.db": {"en": "dB", "ro": "dB"},
    "rf.axis.linear": {"en": "Linear", "ro": "Liniar"},
    "rf.axis.deg": {"en": "degrees", "ro": "grade"},
    "rf.axis.vswr": {"en": "VSWR", "ro": "VSWR"},
    "rf.axis.ns": {"en": "Group delay (s)", "ro": "Întârziere de grup (s)"},

    "rf.error.title": {"en": "RF Simulator", "ro": "Simulator RF"},
    "rf.error.invalid_sweep": {"en": "Please enter valid numeric Start/Stop frequencies (GHz) and Number of Points.",
                               "ro": "Introduceți frecvențe de Start/Stop (GHz) și un Număr de Puncte valide."},
    "rf.error.invalid_value": {"en": "Please enter a valid numeric value for this field.",
                                "ro": "Introduceți o valoare numerică validă pentru acest câmp."},

    "rf.palette.title": {"en": "Components", "ro": "Componente"},
    "rf.palette.port_number": {"en": "Next port #", "ro": "Port urm. #"},
    "rf.palette.hint": {"en": "Click a tool, then click the canvas. Two-terminal parts "
                               "(R/L/C/TL/Wire) need two clicks. Right-drag to pan, scroll to zoom, "
                               "Delete key removes the selected item, Escape cancels a pending click.",
                         "ro": "Alege o unealtă, apoi dă clic pe canava. Componentele cu două "
                               "terminale (R/L/C/TL/Fir) au nevoie de două clicuri. Trage cu "
                               "butonul drept pentru a deplasa vederea, derulează pentru zoom, "
                               "tasta Delete șterge elementul selectat, Escape anulează un clic în așteptare."},
    "rf.palette.clear_circuit": {"en": "Clear Circuit", "ro": "Golește Circuitul"},
    "rf.palette.clear_confirm": {"en": "Remove every component and wire from this circuit?",
                                  "ro": "Ștergi toate componentele și firele din acest circuit?"},

    "rf.hint.select": {"en": "Select / Move: click a part to select it, drag to move it, Delete to remove it.",
                        "ro": "Selectează / Mută: dă clic pe o piesă pentru a o selecta, trage pentru a o muta, Delete pentru a o șterge."},
    "rf.hint.wire": {"en": "Wire: click the first point, then click the second point to connect them.",
                      "ro": "Fir: dă clic pe primul punct, apoi pe al doilea pentru a le conecta."},
    "rf.hint.gnd": {"en": "Ground: click a grid point to tie it to the reference/ground node.",
                     "ro": "Împământare: dă clic pe un punct din grilă pentru a-l lega la nodul de referință (masă)."},
    "rf.hint.port": {"en": "Port: click a grid point to place the next RF port there.",
                      "ro": "Port: dă clic pe un punct din grilă pentru a plasa acolo următorul port RF."},
    "rf.hint.twoclick": {"en": "Click the first terminal, then click the second terminal to place this part.",
                          "ro": "Dă clic pe primul terminal, apoi pe al doilea pentru a plasa piesa."},
    "rf.hint.oneclick": {"en": "Click a grid point to place this part there.",
                          "ro": "Dă clic pe un punct din grilă pentru a plasa piesa acolo."},
    "rf.hint.delete": {"en": "Delete: click any part or wire to remove it.",
                        "ro": "Șterge: dă clic pe orice piesă sau fir pentru a-l elimina."},
    "rf.hint.second_click": {"en": "Now click the second terminal.", "ro": "Acum dă clic pe al doilea terminal."},
    "rf.hint.pending_marker": {"en": "1st point", "ro": "Punct 1"},

    "rf.props.gnd_desc": {"en": "This is the circuit's reference/ground node. Anything wired here "
                                 "is tied directly to 0 V.",
                           "ro": "Acesta este nodul de referință (masă) al circuitului. Orice este "
                                 "conectat aici este legat direct la 0 V."},

    "rf.tool.select": {"en": "Select / Move", "ro": "Selectează / Mută"},
    "rf.tool.wire": {"en": "Wire", "ro": "Fir"},
    "rf.tool.gnd": {"en": "Ground", "ro": "Împământare"},
    "rf.tool.port": {"en": "Port", "ro": "Port"},
    "rf.tool.r": {"en": "Resistor (R)", "ro": "Rezistor (R)"},
    "rf.tool.l": {"en": "Inductor (L)", "ro": "Bobină (L)"},
    "rf.tool.c": {"en": "Capacitor (C)", "ro": "Condensator (C)"},
    "rf.tool.tl": {"en": "Transmission Line", "ro": "Linie de Transmisie"},
    "rf.tool.load_matched": {"en": "Matched Load", "ro": "Sarcină Adaptată"},
    "rf.tool.load_r": {"en": "Resistive Load", "ro": "Sarcină Rezistivă"},
    "rf.tool.load_z": {"en": "Complex Impedance", "ro": "Impedanță Complexă"},
    "rf.tool.open": {"en": "Open Circuit", "ro": "Circuit Deschis"},
    "rf.tool.short": {"en": "Short Circuit", "ro": "Scurtcircuit"},
    "rf.tool.delete": {"en": "Delete", "ro": "Șterge"},

    "rf.props.none_selected": {"en": "Nothing selected. Click a component in Select mode.",
                                "ro": "Nimic selectat. Dă clic pe o componentă în modul Selectează."},
    "rf.props.no_params": {"en": "This component has no editable properties.",
                            "ro": "Această componentă nu are proprietăți editabile."},
    "rf.props.port_number": {"en": "Port Number", "ro": "Număr Port"},
    "rf.props.enabled": {"en": "Enabled", "ro": "Activat"},
    "rf.props.ref_impedance": {"en": "Reference Impedance (Ω)", "ro": "Impedanță de Referință (Ω)"},
    "rf.props.value": {"en": "Value", "ro": "Valoare"},
    "rf.props.z0_line": {"en": "Characteristic Impedance (Ω)", "ro": "Impedanță Caracteristică (Ω)"},
    "rf.props.length_m": {"en": "Physical Length (m)", "ro": "Lungime Fizică (m)"},
    "rf.props.velocity_factor": {"en": "Velocity Factor", "ro": "Factor de Viteză"},
    "rf.props.resistance_r": {"en": "Resistance R (Ω)", "ro": "Rezistență R (Ω)"},
    "rf.props.reactance_x": {"en": "Reactance X (Ω)", "ro": "Reactanță X (Ω)"},
    "rf.props.delete_selected": {"en": "Delete Selected", "ro": "Șterge Selecția"},

    "common.component_properties": {"en": "Component Properties", "ro": "Proprietățile Componentei"},
    "common.apply": {"en": "Apply", "ro": "Aplică"},
    "common.markers": {"en": "Markers", "ro": "Markeri"},

    "rf.vna.channel": {"en": "Channel", "ro": "Canal"},
    "rf.vna.trace_visible": {"en": "Trace visible", "ro": "Traseu vizibil"},
    "rf.vna.measurement": {"en": "Measurement", "ro": "Măsurătoare"},
    "rf.vna.format": {"en": "Format", "ro": "Format"},
    "rf.vna.ghz": {"en": "GHz", "ro": "GHz"},
    "rf.vna.no_data": {"en": "No simulation yet — press SIMULATE.", "ro": "Nicio simulare încă — apasă SIMULEAZĂ."},
    "rf.vna.hidden": {"en": "Trace hidden.", "ro": "Traseu ascuns."},
    "rf.vna.search_max": {"en": "Max", "ro": "Maxim"},
    "rf.vna.search_min": {"en": "Min", "ro": "Minim"},
    "rf.vna.search_peak": {"en": "Peak", "ro": "Vârf"},
    "rf.vna.search_dip": {"en": "Dip", "ro": "Adâncitură"},
    "rf.vna.intro": {
        "en": "A VNA (vector network analyzer) measures how a circuit reflects and transmits signal "
              "across frequency. Channel A and Channel B are two independent display windows onto the "
              "same simulated circuit — each picks its own S-parameter and display format, so you can "
              "compare two views (e.g. input match on a Smith Chart alongside transmission loss in dB) "
              "side by side.",
        "ro": "Un VNA (analizor de rețea vectorial) măsoară cum reflectă și transmite semnal un circuit "
              "în funcție de frecvență. Canalul A și Canalul B sunt două ferestre de afișare independente "
              "asupra aceluiași circuit simulat — fiecare își alege propriul parametru S și format de "
              "afișare, astfel încât poți compara două vederi (de exemplu adaptarea la intrare pe "
              "Diagrama Smith alături de pierderea de transmisie în dB) una lângă alta."},
    "rf.vna.search_label": {"en": "Move active marker to:", "ro": "Mută markerul activ la:"},
    "rf.vna.click_hint": {"en": "Click the graph to move Marker {m}. Click the ● next to another "
                                 "marker to make it the active one.",
                           "ro": "Dă clic pe grafic pentru a muta Markerul {m}. Dă clic pe ● lângă "
                                 "alt marker pentru a-l face activ."},

    "rf.format.log_mag": {"en": "Log Magnitude", "ro": "Magnitudine Logaritmică"},
    "rf.format.lin_mag": {"en": "Linear Magnitude", "ro": "Magnitudine Liniară"},
    "rf.format.phase": {"en": "Phase", "ro": "Fază"},
    "rf.format.smith": {"en": "Smith Chart", "ro": "Diagrama Smith"},
    "rf.format.polar": {"en": "Polar", "ro": "Polar"},
    "rf.format.vswr": {"en": "VSWR", "ro": "VSWR"},
    "rf.format.return_loss": {"en": "Return Loss", "ro": "Pierdere de Retur"},
    "rf.format.group_delay": {"en": "Group Delay", "ro": "Întârziere de Grup"},

    "rf.smith.mode": {"en": "Mode", "ro": "Mod"},
    "rf.smith.impedance": {"en": "Normalized Impedance", "ro": "Impedanță Normalizată"},
    "rf.smith.admittance": {"en": "Normalized Admittance", "ro": "Admitanță Normalizată"},
    "rf.smith.intro": {
        "en": "The Smith Chart plots the complex reflection coefficient (Γ) of the selected "
              "S-parameter as frequency sweeps — the closer the trace hugs the center, the better "
              "matched that port is. It shares the exact same simulated data as the Virtual VNA.",
        "ro": "Diagrama Smith reprezintă coeficientul de reflexie complex (Γ) al parametrului S "
              "selectat pe măsură ce frecvența variază — cu cât traseul e mai aproape de centru, cu "
              "atât portul respectiv este mai bine adaptat. Folosește exact aceleași date simulate ca VNA Virtual."},
    "rf.smith.z0_label": {"en": "Chart Z0 (Ω)", "ro": "Z0 Diagramă (Ω)"},
    "rf.smith.z0_auto": {"en": "(auto: this port's own reference impedance)",
                          "ro": "(automat: impedanța de referință proprie a portului)"},
    "rf.smith.z0_manual": {"en": "(manually overridden)", "ro": "(suprascris manual)"},
    "rf.smith.click_hint": {"en": "Click the chart to move Marker {m}. Click the ● next to another "
                                   "marker to make it the active one.",
                             "ro": "Dă clic pe diagramă pentru a muta Markerul {m}. Dă clic pe ● "
                                   "lângă alt marker pentru a-l face activ."},

    "rf.results.frequency": {"en": "Frequency Point", "ro": "Punct de Frecvență"},
    "rf.results.intro": {
        "en": "The full S-parameter matrix at one specific frequency, read straight from the "
              "simulated sweep — drag the slider to step through frequency points.",
        "ro": "Matricea completă de parametri S la o anumită frecvență, citită direct din "
              "baleierea simulată — trage cursorul pentru a parcurge punctele de frecvență."},
    "rf.results.no_data": {"en": "No simulation yet — press SIMULATE.", "ro": "Nicio simulare încă — apasă SIMULEAZĂ."},
    "rf.results.n_ports_note": {"en": "{n}-port network — full S-parameter matrix below.",
                                 "ro": "Rețea cu {n} porturi — matricea completă de parametri S mai jos."},
    "rf.results.col_param": {"en": "Parameter", "ro": "Parametru"},
    "rf.results.col_mag": {"en": "Magnitude", "ro": "Magnitudine"},
    "rf.results.col_db": {"en": "dB", "ro": "dB"},
    "rf.results.col_phase": {"en": "Phase (°)", "ro": "Fază (°)"},

    # -------------------------------------------------------------
    # RF & Microwave Learn section (theory.rf.*)
    # -------------------------------------------------------------
    "theory.rf.title": {"en": "RF & Microwave / Multiport S-Parameters",
                         "ro": "RF și Microunde / Parametri S Multiport"},
    "theory.rf.what": {
        "en": "RF and microwave circuits operate at frequencies high enough that a "
              "component's physical size becomes comparable to the signal's "
              "wavelength. At that point, wires and traces behave like "
              "transmission lines rather than ideal zero-impedance connections, "
              "voltage and current vary with position, and energy can reflect "
              "back toward the source instead of being fully absorbed by the "
              "load. S-parameters (scattering parameters) describe such a "
              "circuit — with any number of ports — purely in terms of how much "
              "of an incident wave at one port is reflected, and how much is "
              "transmitted to every other port.",
        "ro": "Circuitele RF și de microunde funcționează la frecvențe suficient "
              "de mari încât dimensiunea fizică a unei componente devine "
              "comparabilă cu lungimea de undă a semnalului. La acel punct, "
              "firele și traseele de cablaj se comportă ca linii de transmisie, "
              "nu ca simple conexiuni ideale cu impedanță zero; tensiunea și "
              "curentul variază cu poziția, iar energia se poate reflecta către "
              "sursă în loc să fie absorbită complet de sarcină. Parametrii S "
              "(parametri de dispersie) descriu un astfel de circuit — cu orice "
              "număr de porturi — exclusiv în funcție de cât din unda incidentă "
              "la un port este reflectată și cât este transmisă la fiecare "
              "celălalt port."},
    "theory.rf.how": {
        "en": "Every port k is driven, one at a time, with a normalized incident "
              "wave a_k = 1 while every other port is terminated in its own "
              "reference impedance Z0 (not open or shorted — exactly like a real "
              "VNA measurement). The reflected/transmitted wave that appears at "
              "port q is, by definition, S_qk. Doing this for every port in turn "
              "builds up the complete S-parameter matrix. Internally, this "
              "simulator represents the schematic as a node/wire graph (a "
              "netlist), solves it with nodal analysis at each swept frequency, "
              "and converts the resulting node voltages into S-parameters — the "
              "same underlying voltages and currents also fix every other "
              "quantity below (impedance, reflection coefficient, VSWR, return "
              "loss), so nothing here is calculated independently or "
              "inconsistently between views.",
        "ro": "Fiecare port k este excitat, pe rând, cu o undă incidentă "
              "normalizată a_k = 1, în timp ce toate celelalte porturi sunt "
              "terminate pe propria impedanță de referință Z0 (nu în gol și nu "
              "în scurtcircuit — exact ca la o măsurătoare reală cu un VNA). "
              "Unda reflectată/transmisă care apare la portul q este, prin "
              "definiție, S_qk. Repetând acest lucru pentru fiecare port se "
              "obține matricea completă de parametri S. Intern, acest simulator "
              "reprezintă schema ca un graf de noduri/fire (o listă de conexiuni "
              "— netlist), îl rezolvă prin analiză nodală la fiecare frecvență "
              "din baleiere și transformă tensiunile de nod rezultate în "
              "parametri S — aceleași tensiuni și curenți determină și toate "
              "celelalte mărimi de mai jos (impedanță, coeficient de reflexie, "
              "VSWR, pierdere de retur), deci nimic nu este calculat independent "
              "sau inconsecvent între diferitele afișaje."},
    "f.rf.impedance_freq": {"en": "Frequency-dependent complex impedance", "ro": "Impedanță complexă dependentă de frecvență"},
    "f.rf.reactance": {"en": "Reactance", "ro": "Reactanță"},
    "f.rf.char_impedance": {"en": "Characteristic impedance", "ro": "Impedanță caracteristică"},
    "f.rf.elec_length": {"en": "Electrical length & wavelength", "ro": "Lungime electrică și lungime de undă"},
    "f.rf.reflection_coeff": {"en": "Reflection coefficient", "ro": "Coeficient de reflexie"},
    "f.rf.vswr": {"en": "VSWR", "ro": "VSWR"},
    "f.rf.return_loss": {"en": "Return loss", "ro": "Pierdere de retur"},
    "f.rf.s_matrix": {"en": "Multiport S-parameter matrix", "ro": "Matricea de parametri S multiport"},
    "f.rf.s11_meaning": {"en": "Meaning of S11", "ro": "Semnificația S11"},
    "f.rf.s21_meaning": {"en": "Meaning of S21", "ro": "Semnificația S21"},
    "f.rf.s22_meaning": {"en": "Meaning of S22", "ro": "Semnificația S22"},
    "f.rf.norm_impedance": {"en": "Normalized impedance (Smith Chart)", "ro": "Impedanță normalizată (Diagrama Smith)"},
    "f.rf.norm_admittance": {"en": "Normalized admittance (Smith Chart)", "ro": "Admitanță normalizată (Diagrama Smith)"},
    "f.rf.quarter_wave": {"en": "Quarter-wave impedance transformation", "ro": "Transformare de impedanță cu linie sfert de undă"},

    # ===================================================================
    # Logic Circuit Builder
    # ===================================================================
    "logic.builder.intro": {
        "en": "Place input switches, gates, a mux/demux, and output probes on the grid, "
              "then wire an output pin to an input pin. Click any input switch to toggle it "
              "0/1 — every gate and wire updates instantly, all the way to the outputs.",
        "ro": "Plasează întrerupătoare de intrare, porți, un mux/demux și sonde de ieșire pe "
              "grilă, apoi conectează un pin de ieșire la un pin de intrare. Dă clic pe orice "
              "întrerupător de intrare pentru a-l comuta 0/1 — fiecare poartă și fir se "
              "actualizează instant, până la ieșiri."},

    "logic.palette.title": {"en": "Components", "ro": "Componente"},
    "logic.palette.clear_circuit": {"en": "Clear Circuit", "ro": "Golește Circuitul"},
    "logic.palette.clear_confirm": {"en": "Remove every component and wire from this circuit?",
                                     "ro": "Ștergi toate componentele și firele din acest circuit?"},
    "logic.palette.hint": {"en": "Click a tool, then click the canvas to place it (one click "
                                  "each — nothing needs a second click except wires). Scroll to "
                                  "zoom (in/out around your cursor), right-drag to pan. Delete "
                                  "key removes the selected item, Escape cancels a wire in "
                                  "progress.",
                            "ro": "Alege o unealtă, apoi dă clic pe canava pentru a o plasa (un "
                                  "singur clic — nimic nu are nevoie de al doilea clic, în afară "
                                  "de fire). Derulează pentru zoom (în jurul cursorului), trage cu "
                                  "butonul drept pentru a deplasa vederea. Tasta Delete șterge "
                                  "elementul selectat, Escape anulează un fir în curs."},
    "logic.palette.reset_view": {"en": "Reset View", "ro": "Resetează Vederea"},

    "logic.tool.select": {"en": "Select / Move", "ro": "Selectează / Mută"},
    "logic.tool.wire": {"en": "Wire", "ro": "Fir"},
    "logic.tool.input": {"en": "Input Switch", "ro": "Întrerupător de Intrare"},
    "logic.tool.node": {"en": "Junction Node", "ro": "Nod de Joncțiune"},
    "logic.tool.output": {"en": "Output Probe", "ro": "Sondă de Ieșire"},
    "logic.tool.not_": {"en": "NOT Gate", "ro": "Poartă NOT"},
    "logic.tool.and_": {"en": "AND Gate", "ro": "Poartă AND"},
    "logic.tool.or_": {"en": "OR Gate", "ro": "Poartă OR"},
    "logic.tool.nand": {"en": "NAND Gate", "ro": "Poartă NAND"},
    "logic.tool.nor": {"en": "NOR Gate", "ro": "Poartă NOR"},
    "logic.tool.xor": {"en": "XOR Gate", "ro": "Poartă XOR"},
    "logic.tool.xnor": {"en": "XNOR Gate", "ro": "Poartă XNOR"},
    "logic.tool.mux2": {"en": "Mux (2→1)", "ro": "Multiplexor (2→1)"},
    "logic.tool.mux4": {"en": "Mux (4→1)", "ro": "Multiplexor (4→1)"},
    "logic.tool.demux2": {"en": "Demux (1→2)", "ro": "Demultiplexor (1→2)"},
    "logic.tool.demux4": {"en": "Demux (1→4)", "ro": "Demultiplexor (1→4)"},
    "logic.tool.delete": {"en": "Delete", "ro": "Șterge"},

    "logic.hint.select": {"en": "Select / Move: click an input switch to toggle it, click any "
                                 "other part to select it, drag to move, Delete to remove.",
                           "ro": "Selectează / Mută: dă clic pe un întrerupător de intrare "
                                 "pentru a-l comuta, dă clic pe orice altă piesă pentru a o "
                                 "selecta, trage pentru a muta, Delete pentru a șterge."},
    "logic.hint.wire": {"en": "Wire: click an output pin, then click an input pin to connect them.",
                         "ro": "Fir: dă clic pe un pin de ieșire, apoi pe un pin de intrare "
                               "pentru a le conecta."},
    "logic.hint.wire_second": {"en": "Now click the input pin to connect to.",
                                "ro": "Acum dă clic pe pinul de intrare la care te conectezi."},
    "logic.hint.delete": {"en": "Delete: click any part or wire to remove it.",
                           "ro": "Șterge: dă clic pe orice piesă sau fir pentru a-l elimina."},
    "logic.hint.place": {"en": "Click the canvas to place this part.",
                          "ro": "Dă clic pe canava pentru a plasa această piesă."},

    "logic.error.title": {"en": "Logic Circuit Builder", "ro": "Constructor de Circuite Logice"},
    "logic.error.cycle": {"en": "⚠ Combinational loop detected — the affected gates read as unknown.",
                           "ro": "⚠ Buclă combinațională detectată — porțile afectate sunt necunoscute."},

    "logic.props.title": {"en": "Component Properties", "ro": "Proprietățile Componentei"},
    "logic.props.none_selected": {"en": "Nothing selected. Click a part in Select mode.",
                                   "ro": "Nimic selectat. Dă clic pe o piesă în modul Selectează."},
    "logic.props.label": {"en": "Label", "ro": "Etichetă"},
    "logic.props.input_desc": {"en": "An input switch. Click it directly (in Select mode) to "
                                      "toggle between 0 and 1.",
                                "ro": "Un întrerupător de intrare. Dă clic direct pe el (în modul "
                                      "Selectează) pentru a comuta între 0 și 1."},
    "logic.props.output_desc": {"en": "An output probe — lights up green for 1, gray for 0, "
                                       "and stays hollow/white while unconnected.",
                                 "ro": "O sondă de ieșire — se aprinde verde pentru 1, gri pentru "
                                       "0, și rămâne goală/albă cât timp e neconectată."},
    "logic.props.gate_desc": {"en": "Wire both inputs to see the output update live.",
                               "ro": "Conectează ambele intrări pentru a vedea ieșirea "
                                     "actualizându-se în timp real."},
    "logic.props.node_desc": {"en": "A junction node: wire one output into it, then wire its "
                                     "output to as many inputs as you like — a clean way to "
                                     "branch a signal without wires crossing awkwardly.",
                               "ro": "Un nod de joncțiune: conectează o ieșire la el, apoi "
                                     "conectează ieșirea lui la câte intrări dorești — un mod "
                                     "curat de a ramifica un semnal fără fire încrucișate stângaci."},
    "logic.props.desc.MUX2": {"en": "2-to-1 multiplexer: Y = I1 when S=1, otherwise Y = I0. "
                                     "S picks which data input reaches the output.",
                               "ro": "Multiplexor 2 la 1: Y = I1 când S=1, altfel Y = I0. S "
                                     "alege ce intrare de date ajunge la ieșire."},
    "logic.props.desc.MUX4": {"en": "4-to-1 multiplexer: the 2-bit select (S1 S0) picks which "
                                     "of I0..I3 reaches the output Y.",
                               "ro": "Multiplexor 4 la 1: selecția pe 2 biți (S1 S0) alege care "
                                     "dintre I0..I3 ajunge la ieșirea Y."},
    "logic.props.desc.DEMUX2": {"en": "1-to-2 demultiplexer: routes input D to O0 when S=0, or "
                                       "to O1 when S=1; the unselected output is held at 0.",
                                 "ro": "Demultiplexor 1 la 2: direcționează intrarea D către O0 "
                                       "când S=0, sau către O1 când S=1; ieșirea neselectată "
                                       "rămâne la 0."},
    "logic.props.desc.DEMUX4": {"en": "1-to-4 demultiplexer: the 2-bit select (S1 S0) routes "
                                       "input D to exactly one of O0..O3; the rest stay at 0.",
                                 "ro": "Demultiplexor 1 la 4: selecția pe 2 biți (S1 S0) "
                                       "direcționează intrarea D către exact una din O0..O3; "
                                       "restul rămân la 0."},

    # ===================================================================
    # Number Base Converter + ADC/DAC (Unit Converter subtab)
    # ===================================================================
    "base.title": {"en": "Number Base Converter", "ro": "Convertor de Bază Numerică"},
    "base.intro": {
        "en": "Type a value, pick the base it's written in, and see it instantly in binary, "
              "octal, decimal, hexadecimal, and any custom base 2-36.",
        "ro": "Introdu o valoare, alege baza în care e scrisă și o vezi instant în binar, octal, "
              "zecimal, hexazecimal și în orice bază personalizată 2-36."},
    "base.mode_plain": {"en": "Plain integer (any size, signed)", "ro": "Întreg simplu (orice mărime, cu semn)"},
    "base.mode_twos": {"en": "Fixed-width two's complement", "ro": "Complement față de doi, lățime fixă"},
    "base.bit_width": {"en": "Bit width", "ro": "Lățime (biți)"},
    "base.value_label": {"en": "Value", "ro": "Valoare"},
    "base.from_base_label": {"en": "Is written in base", "ro": "Este scrisă în baza"},
    "base.custom_base_label": {"en": "Custom base:", "ro": "Bază personalizată:"},
    "base.bin": {"en": "Binary", "ro": "Binar"},
    "base.oct": {"en": "Octal", "ro": "Octal"},
    "base.dec": {"en": "Decimal", "ro": "Zecimal"},
    "base.hex": {"en": "Hex", "ro": "Hex"},
    "base.error_invalid": {"en": "Not a valid number in that base: {msg}",
                            "ro": "Nu este un număr valid în acea bază: {msg}"},
    "base.overflow_note": {"en": "⚠ That value doesn't fit in {bits}-bit two's complement "
                                  "(range {lo}..{hi}) — showing the wrapped-around bit pattern.",
                            "ro": "⚠ Acea valoare nu încape în complement față de doi pe {bits} "
                                  "biți (interval {lo}..{hi}) — se arată modelul de biți rezultat "
                                  "din suprascriere."},
    "base.twos_note": {"en": "{bits}-bit pattern {pattern} = {signed} in signed decimal.",
                        "ro": "Modelul pe {bits} biți {pattern} = {signed} în zecimal cu semn."},

    "base.adc_title": {"en": "ADC / DAC Code Converter", "ro": "Convertor de Cod ADC / DAC"},
    "base.adc_intro": {
        "en": "The quantization math behind any ADC or DAC: set the resolution and reference "
              "voltage, then convert either direction between an analog voltage and its digital "
              "code.",
        "ro": "Matematica de cuantizare din spatele oricărui ADC sau DAC: setează rezoluția și "
              "tensiunea de referință, apoi convertește în orice direcție între o tensiune "
              "analogică și codul ei digital."},
    "base.resolution_label": {"en": "Resolution (bits)", "ro": "Rezoluție (biți)"},
    "base.vref_label": {"en": "Reference voltage (Vref)", "ro": "Tensiune de referință (Vref)"},
    "base.lsb_note": {"en": "1 LSB = {lsb}", "ro": "1 LSB = {lsb}"},
    "base.voltage_label": {"en": "Analog voltage (Vin)", "ro": "Tensiune analogică (Vin)"},
    "base.code_label": {"en": "Digital code (decimal)", "ro": "Cod digital (zecimal)"},
    "base.code_decimal": {"en": "Code (decimal)", "ro": "Cod (zecimal)"},
    "base.code_binary": {"en": "Code (binary)", "ro": "Cod (binar)"},
    "base.code_hex": {"en": "Code (hex)", "ro": "Cod (hex)"},
    "base.reconstructed_voltage": {"en": "Reconstructed voltage", "ro": "Tensiune reconstruită"},
    "base.clamped_note": {"en": "Clamped to the valid code range [{lo}, {hi}].",
                           "ro": "Limitat la intervalul valid de cod [{lo}, {hi}]."},
    "base.error_invalid_number": {"en": "Enter valid numbers for voltage, Vref and resolution.",
                                   "ro": "Introdu valori numerice valide pentru tensiune, Vref și rezoluție."},

    # ===================================================================
    # RF Band Allocations (RF & Microwave subtab)
    # ===================================================================
    "rf.bands.tab_title": {"en": "RF Band Explorer", "ro": "Explorator benzi RF"},
    "rf.bands.title": {"en": "RF Band Allocations by Region", "ro": "Alocări de Benzi RF pe Regiuni"},
    "rf.bands.intro": {
        "en": "A quick-lookup reference for how common RF bands are allocated across four major "
              "regulatory regions. Built for a fast sanity check during design or production "
              "(\"is 915 MHz actually usable here?\") — not a substitute for checking the current "
              "regulator's own publication before a compliance decision.",
        "ro": "O referință rapidă pentru modul în care benzile RF comune sunt alocate în patru "
              "regiuni de reglementare majore. Gândită pentru o verificare rapidă în timpul "
              "proiectării sau producției (\"e utilizabil 915 MHz aici?\") — nu înlocuiește "
              "verificarea publicației curente a autorității de reglementare înainte de o decizie "
              "de conformitate."},
    "rf.bands.col_band": {"en": "Band / Application", "ro": "Bandă / Aplicație"},
    "rf.bands.col_eu": {"en": "EU", "ro": "UE"},
    "rf.bands.col_china": {"en": "China", "ro": "China"},
    "rf.bands.col_na": {"en": "North America", "ro": "America de Nord"},
    "rf.bands.col_japan": {"en": "Japan", "ro": "Japonia"},
    "rf.bands.regulators_label": {"en": "Regulators:", "ro": "Autorități de reglementare:"},
    "rf.bands.notes_title": {"en": "Notes", "ro": "Note"},
    "rf.bands.disclaimer": {
        "en": "⚠ Reference only. Allocations, power limits and duty-cycle rules change over time "
              "and have sub-bands/exceptions not shown here. Always confirm against the current "
              "regulator's own publication (ETSI, SRRC/MIIT, FCC/ISED, ARIB/MIC) before a design, "
              "production or compliance decision.",
        "ro": "⚠ Doar cu titlu de referință. Alocările, limitele de putere și regulile de ciclu de "
              "lucru se schimbă în timp și au sub-benzi/excepții neafișate aici. Verifică "
              "întotdeauna publicația curentă a autorității de reglementare (ETSI, SRRC/MIIT, "
              "FCC/ISED, ARIB/MIC) înainte de o decizie de proiectare, producție sau conformitate."},

    "rf.band.subghz_ism": {"en": "Sub-GHz ISM", "ro": "ISM Sub-GHz"},
    "rf.band.note.subghz_ism": {
        "en": "License-free for short-range devices, but the exact sub-band, power limit and "
              "duty cycle differ by region — e.g. EU 868 MHz has duty-cycle limits (1%/10%) "
              "instead of a US-style frequency-hopping requirement.",
        "ro": "Fără licență pentru dispozitive de rază scurtă, dar sub-banda exactă, limita de "
              "putere și ciclul de lucru diferă pe regiuni — de ex. 868 MHz UE are limite de "
              "ciclu de lucru (1%/10%) în loc de o cerință de salt de frecvență de tip SUA."},
    "rf.band.24ghz_ism": {"en": "2.4 GHz ISM (WiFi / BT / Zigbee)", "ro": "ISM 2,4 GHz (WiFi / BT / Zigbee)"},
    "rf.band.note.24ghz_ism": {
        "en": "The most globally consistent unlicensed band, which is exactly why it's so "
              "congested — WiFi, Bluetooth, Zigbee, and microwave ovens all share it.",
        "ro": "Cea mai consecventă bandă fără licență la nivel global, exact de aceea este atât "
              "de aglomerată — WiFi, Bluetooth, Zigbee și cuptoarele cu microunde o împart."},
    "rf.band.5ghz_lower": {"en": "5 GHz WiFi (lower/UNII-1,2A)", "ro": "WiFi 5 GHz (inferior/UNII-1,2A)"},
    "rf.band.note.5ghz_lower": {
        "en": "Often requires DFS (Dynamic Frequency Selection) to avoid interfering with "
              "weather/military radar sharing the same spectrum — a device here isn't free to "
              "transmit at will.",
        "ro": "Necesită adesea DFS (Selecție Dinamică a Frecvenței) pentru a evita interferența cu "
              "radarul meteo/militar care împarte același spectru — un dispozitiv aici nu poate "
              "transmite liber oricând."},
    "rf.band.5ghz_upper": {"en": "5 GHz WiFi (upper/UNII-3)", "ro": "WiFi 5 GHz (superior/UNII-3)"},
    "rf.band.note.5ghz_upper": {
        "en": "Region boundaries here are not aligned — a channel legal in North America may sit "
              "outside the allocated range in the EU or vice versa, so a WiFi module's regulatory "
              "domain setting genuinely matters.",
        "ro": "Limitele regiunilor nu sunt aliniate aici — un canal legal în America de Nord poate "
              "fi în afara intervalului alocat în UE sau invers, deci setarea domeniului de "
              "reglementare a unui modul WiFi chiar contează."},
    "rf.band.lorawan": {"en": "LoRaWAN regional plan", "ro": "Plan regional LoRaWAN"},
    "rf.band.note.lorawan": {
        "en": "LoRaWAN doesn't use one global band — the regional plan (EU868/US915/CN470/AS923) "
              "must match where the device actually ships, or it won't be legal to transmit, and "
              "may not even reach a gateway using a different plan.",
        "ro": "LoRaWAN nu folosește o singură bandă globală — planul regional (EU868/US915/CN470/"
              "AS923) trebuie să corespundă locului unde dispozitivul este livrat efectiv, altfel "
              "transmisia nu este legală și s-ar putea nici să nu ajungă la un gateway cu alt plan."},
    "rf.band.nfc_hf": {"en": "NFC / RFID (HF, 13.56 MHz)", "ro": "NFC / RFID (HF, 13,56 MHz)"},
    "rf.band.note.nfc_hf": {
        "en": "One of the very few bands that's essentially identical worldwide, which is why "
              "NFC hardware needs no regional variant.",
        "ro": "Una dintre puținele benzi practic identice la nivel mondial, motiv pentru care "
              "hardware-ul NFC nu are nevoie de o variantă regională."},
    "rf.band.uhf_rfid": {"en": "UHF RFID", "ro": "RFID UHF"},
    "rf.band.note.uhf_rfid": {
        "en": "Unlike HF NFC, UHF RFID reader frequency is region-specific — a reader tuned for "
              "one region's sub-band will have degraded range (or won't work at all) in another.",
        "ro": "Spre deosebire de NFC HF, frecvența cititorului RFID UHF este specifică regiunii — "
              "un cititor calibrat pentru sub-banda unei regiuni va avea rază redusă (sau nu va "
              "funcționa deloc) în alta."},
    "rf.band.gnss_l1": {"en": "GNSS L1 (GPS)", "ro": "GNSS L1 (GPS)"},
    "rf.band.note.gnss_l1": {
        "en": "A receive-only band for consumer GPS, so there's no regional licensing question — "
              "the satellite signal itself is global.",
        "ro": "O bandă doar de recepție pentru GPS de consum, deci nu există o problemă de "
              "licențiere regională — semnalul de satelit în sine este global."},
    "rf.band.cellular_2g": {"en": "Cellular 2G (legacy)", "ro": "Celular 2G (vechi)"},
    "rf.band.note.cellular_2g": {
        "en": "Shown mainly as a caution: 2G has been or is being shut down by many carriers "
              "worldwide (Japan already retired it), so designing new hardware around it is "
              "increasingly risky regardless of region.",
        "ro": "Prezentat mai ales ca avertisment: 2G a fost sau este în curs de oprire de multe "
              "rețele la nivel mondial (Japonia l-a retras deja), deci proiectarea de hardware nou "
              "în jurul lui este din ce în ce mai riscantă, indiferent de regiune."},
    "rf.band.cellular_low": {"en": "Cellular low-band example (LTE)", "ro": "Exemplu bandă joasă celulară (LTE)"},
    "rf.band.note.cellular_low": {
        "en": "Just one illustrative example — real cellular allocation is dozens of 3GPP bands "
              "per region with carrier-specific licensing; a real cellular-module design needs "
              "the module vendor's regional band table, not this row alone.",
        "ro": "Doar un exemplu ilustrativ — alocarea celulară reală înseamnă zeci de benzi 3GPP pe "
              "regiune, cu licențiere specifică fiecărui operator; un proiect real cu modul celular "
              "are nevoie de tabelul de benzi regional al furnizorului modulului, nu doar de acest rând."},
}

# Additional strings (v5.0 features) live in i18n_extra.py
from i18n_extra import EXTRA as _EXTRA
STRINGS.update(_EXTRA)
from i18n_transistor import EXTRA_TR as _EXTRA_TR
STRINGS.update(_EXTRA_TR)
from i18n_v52 import EXTRA_52 as _EXTRA_52
STRINGS.update(_EXTRA_52)


def register(table):
    """Add strings from a feature module: {key: (english, romanian)}.
    Lets new modules keep their texts next to the code that uses them."""
    for k, v in table.items():
        if isinstance(v, dict):
            STRINGS[k] = v
        else:
            STRINGS[k] = {"en": v[0], "ro": v[1]}


def tr(en, ro):
    """Inline two-language text for short labels (v6 modules)."""
    return ro if _CURRENT_LANG == "ro" else en
