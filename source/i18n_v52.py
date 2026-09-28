"""EN/RO strings added in v5.2 (reactive AC charts, coupling animation,
bridge rectifier rework, transistor graphical analysis, RF explorer,
Boolean solver diagrams/keypad, unit converter rework, dark mode).
Merged into i18n.STRINGS."""

EXTRA_52 = {
    # ---------------- reactive AC chart ----------------
    "chart.i_leads": {"en": "current leads", "ro": "curentul este defazat înainte"},
    "chart.i_lags": {"en": "current lags", "ro": "curentul este defazat în urmă"},
    "chart.p_in": {"en": "energy flows INTO the component", "ro": "energia intră ÎN componentă"},
    "chart.p_back": {"en": "energy returned to the source", "ro": "energia returnată sursei"},
    "chart.p_avg": {"en": "average power P", "ro": "puterea medie P"},
    "chart.power_title": {"en": "Instantaneous power p(t) = v·i", "ro": "Puterea instantanee p(t) = v·i"},
    "chart.phasor_title": {"en": "Phasor diagram (I = reference)", "ro": "Diagrama fazorială (I = referință)"},
    "chart.reactance_title": {"en": "Reactance vs frequency", "ro": "Reactanța în funcție de frecvență"},
    "chart.e_peak": {"en": "Peak stored energy", "ro": "Energia maximă stocată"},
    "chart.series_r": {"en": "Series resistance R (Ω, 0 = ideal)", "ro": "Rezistență serie R (Ω, 0 = ideal)"},

    # ---------------- magnetic coupling ----------------
    "cpl.intro": {
        "en": "An alternating current in coil 1 builds a magnetic field that grows, collapses and reverses every "
              "cycle. The part of that field passing through coil 2 (the linked flux, set by the coupling "
              "coefficient k) induces a voltage v2 = M·di1/dt. Connect a load and the current in coil 2 creates "
              "its own field that opposes the change (Lenz's law, dashed lines). Drag coil 2 closer or add an "
              "iron core to raise k.",
        "ro": "Un curent alternativ prin bobina 1 creează un câmp magnetic care crește, scade și își schimbă sensul "
              "în fiecare perioadă. Partea din câmp care trece prin bobina 2 (fluxul înlănțuit, dat de "
              "coeficientul de cuplaj k) induce tensiunea v2 = M·di1/dt. Conectează o sarcină și curentul din "
              "bobina 2 creează propriul câmp, care se opune variației (legea lui Lenz, linii punctate). Trage "
              "bobina 2 mai aproape sau adaugă un miez de fier ca să crești k."},
    "cpl.i1": {"en": "I1 peak", "ro": "I1 de vârf"},
    "cpl.freq": {"en": "Frequency", "ro": "Frecvență"},
    "cpl.rl": {"en": "Load RL", "ro": "Sarcină RL"},
    "cpl.load_on": {"en": "Connect load to coil 2", "ro": "Conectează sarcina la bobina 2"},
    "cpl.core": {"en": "Shared iron core", "ro": "Miez de fier comun"},
    "cpl.k_label": {"en": "Coupling k", "ro": "Cuplaj k"},
    "cpl.drag_hint": {"en": "Tip: drag coil 2 left/right to change the coupling.",
                      "ro": "Sfat: trage bobina 2 stânga/dreapta ca să schimbi cuplajul."},
    "cpl.tip_loose": {
        "en": "Loose coupling: most field lines close back on coil 1 (leakage flux). Little voltage reaches "
              "coil 2 — this is how antennas, RFID tags and wireless chargers at a distance behave.",
        "ro": "Cuplaj slab: majoritatea liniilor de câmp se închid înapoi în bobina 1 (flux de scăpări). La "
              "bobina 2 ajunge puțină tensiune — așa se comportă antenele, etichetele RFID și încărcătoarele "
              "wireless aflate la distanță."},
    "cpl.tip_mid": {
        "en": "Medium coupling: part of the flux links both coils. Typical of air-core RF transformers and "
              "wireless-charging pads.",
        "ro": "Cuplaj mediu: o parte din flux înlănțuie ambele bobine. Tipic pentru transformatoarele RF cu aer "
              "și pentru plăcile de încărcare wireless."},
    "cpl.tip_tight": {
        "en": "Tight coupling: almost all the flux goes through both coils, like in a mains transformer with an "
              "iron core. The voltage ratio approaches the turns ratio √(L2/L1).",
        "ro": "Cuplaj strâns: aproape tot fluxul trece prin ambele bobine, ca într-un transformator de rețea cu "
              "miez de fier. Raportul tensiunilor se apropie de raportul de spire √(L2/L1)."},
    "cpl.coil1": {"en": "Coil 1 (primary)", "ro": "Bobina 1 (primar)"},
    "cpl.coil2": {"en": "Coil 2 (secondary)", "ro": "Bobina 2 (secundar)"},
    "cpl.caption": {"en": "k = {k:.2f}: {n} of 6 field lines pass through coil 2",
                    "ro": "k = {k:.2f}: {n} din 6 linii de câmp trec prin bobina 2"},
    "cpl.primary": {"en": "primary", "ro": "primar"},
    "cpl.scope_hint": {"en": "v2 is largest where i1 changes fastest (zero crossings), not where i1 peaks",
                       "ro": "v2 este maximă unde i1 variază cel mai repede (la trecerile prin zero), nu la vârful lui i1"},

    # ---------------- 4-diode bridge ----------------
    "diode.bridge.add_cap_chk": {"en": "Add smoothing capacitor (then the load matters)",
                                 "ro": "Adaugă condensator de filtrare (atunci contează sarcina)"},
    "diode.bridge.rl_hint": {
        "en": "Without a capacitor the output is just |vin| − 2·Vf whatever the load, so RL only appears "
              "once C is added: RL discharges C between peaks and sets the ripple.",
        "ro": "Fără condensator ieșirea este |vin| − 2·Vf indiferent de sarcină, deci RL apare doar după ce "
              "adaugi C: RL descarcă C între vârfuri și stabilește riplul."},
    "diode.bridge.load_generic": {"en": "Load", "ro": "Sarcină"},
    "diode.bridge.phase_pos": {"en": "Positive half-cycle: D1 and D4 conduct",
                               "ro": "Semialternanța pozitivă: conduc D1 și D4"},
    "diode.bridge.phase_neg": {"en": "Negative half-cycle: D2 and D3 conduct",
                               "ro": "Semialternanța negativă: conduc D2 și D3"},

    # ---------------- transistor graphical analysis ----------------
    "tg.intro.bjt": {
        "en": "Graphical analysis of a common-emitter stage (RC to VCC). Chart 1: how the base current controls IC. "
              "Chart 2: the output curves with the load line — the transistor can only sit on this line, and "
              "the orange dot is the Q point. Chart 3: the output waveform. Move the bias to slide Q along the line, "
              "increase the signal to see it clip, or pick 'Switch' to drive it between cut-off and saturation.",
        "ro": "Analiza grafică a unui etaj emitor comun (RC la VCC). Graficul 1: cum controlează curentul de bază pe "
              "IC. Graficul 2: caracteristicile de ieșire cu dreapta de sarcină — tranzistorul poate lucra doar pe "
              "această dreaptă, iar punctul portocaliu este punctul static Q. Graficul 3: forma de undă la ieșire. Mută "
              "polarizarea ca să deplasezi Q pe dreaptă, mărește semnalul ca să vezi limitarea, sau alege "
              "'Comutator' ca să-l comanzi între blocare și saturație."},
    "tg.intro.mosfet": {
        "en": "Graphical analysis of a common-source stage (RD to VDD). Chart 1: transfer curve ID(VGS) — nothing "
              "flows below Vth. Chart 2: output curves with the load line and Q point. Chart 3: output waveform. "
              "Move the gate bias to slide Q, increase the signal to see clipping, or pick 'Switch' to see the "
              "MOSFET used as a switch (the way it is used most often).",
        "ro": "Analiza grafică a unui etaj sursă comună (RD la VDD). Graficul 1: caracteristica de transfer ID(VGS) — "
              "sub Vth nu circulă curent. Graficul 2: caracteristicile de ieșire cu dreapta de sarcină și punctul Q. "
              "Graficul 3: forma de undă la ieșire. Mută polarizarea grilei ca să deplasezi Q, mărește semnalul ca "
              "să vezi limitarea, sau alege 'Comutator' ca să vezi MOSFET-ul folosit ca întrerupător (cel mai "
              "des întâlnit mod de utilizare)."},
    "tg.intro.jfet": {
        "en": "Graphical analysis of a common-source JFET stage (RD to VDD). The JFET is ON at VGS = 0 (ID = IDSS) "
              "and is turned OFF by making the gate negative down to VP. Chart 1: transfer curve. Chart 2: output "
              "curves with the load line and Q point. Chart 3: output waveform.",
        "ro": "Analiza grafică a unui etaj JFET sursă comună (RD la VDD). JFET-ul conduce la VGS = 0 (ID = IDSS) "
              "și se blochează făcând grila negativă până la VP. Graficul 1: caracteristica de transfer. Graficul 2: "
              "caracteristicile de ieșire cu dreapta de sarcină și punctul Q. Graficul 3: forma de undă la ieșire."},
    "tg.preset.amp": {"en": "Linear amplifier", "ro": "Amplificator liniar"},
    "tg.preset.clip": {"en": "Overdriven (clipping)", "ro": "Supracomandat (limitare)"},
    "tg.preset.switch": {"en": "Switch", "ro": "Comutator"},
    "tg.preset.center": {"en": "Centre Q point", "ro": "Centrează punctul Q"},
    "tg.bias_ib": {"en": "Base bias IB", "ro": "Polarizare bază IB"},
    "tg.sig_ib": {"en": "Signal ± ΔIB", "ro": "Semnal ± ΔIB"},
    "tg.bias_vgs": {"en": "Gate bias VGS", "ro": "Polarizare grilă VGS"},
    "tg.bias_vgs_j": {"en": "Gate bias VGS (negative)", "ro": "Polarizare grilă VGS (negativă)"},
    "tg.sig_vgs": {"en": "Signal ± ΔVGS", "ro": "Semnal ± ΔVGS"},
    "tg.wave": {"en": "Input wave", "ro": "Semnal intrare"},
    "tg.wave_sine": {"en": "Sine", "ro": "Sinus"},
    "tg.wave_square": {"en": "Square", "ro": "Dreptunghi"},
    "tg.t_transfer": {"en": "1. Input controls the current", "ro": "1. Intrarea controlează curentul"},
    "tg.t_output": {"en": "2. Load line and Q point", "ro": "2. Dreapta de sarcină și punctul Q"},
    "tg.t_wave": {"en": "3. Output voltage vs time", "ro": "3. Tensiunea de ieșire în timp"},
    "tg.loadline": {"en": "load line", "ro": "dreapta de sarcină"},
    "tg.swing": {"en": "signal swing", "ro": "excursia semnalului"},
    "tg.vout": {"en": "output", "ro": "ieșire"},
    "tg.clipped": {"en": "clipped", "ro": "limitat"},
    "tg.periods": {"en": "time (periods)", "ro": "timp (perioade)"},
    "tg.input": {"en": "input", "ro": "intrare"},
    "tg.out_swing": {"en": "Output swing", "ro": "Excursia ieșirii"},
    "tg.current_gain": {"en": "current gain", "ro": "câștig în curent"},
    "tg.explain.linear": {
        "en": "Linear amplification: the input swing moves Q up and down the load line and stays between "
              "cut-off and saturation, so the output is a larger, inverted copy of the input.",
        "ro": "Amplificare liniară: semnalul de intrare mută punctul Q în sus și în jos pe dreapta de sarcină "
              "fără să atingă blocarea sau saturația, deci ieșirea este o copie mai mare și inversată a intrării."},
    "tg.explain.dc": {
        "en": "No signal: the transistor rests at the Q point. Increase the signal to see amplification.",
        "ro": "Fără semnal: tranzistorul stă în punctul Q. Mărește semnalul ca să vezi amplificarea."},
    "tg.explain.clip_sat": {
        "en": "The bottom of the output is flattened: on those peaks the transistor hits saturation (the left "
              "end of the load line) and the output cannot go below ≈ 0 V. Lower the bias or the signal.",
        "ro": "Partea de jos a ieșirii este aplatizată: pe acele vârfuri tranzistorul intră în saturație "
              "(capătul stâng al dreptei de sarcină) și ieșirea nu poate coborî sub ≈ 0 V. Micșorează "
              "polarizarea sau semnalul."},
    "tg.explain.clip_cut": {
        "en": "The top of the output is flattened: on those peaks the transistor turns off (cut-off, the right "
              "end of the load line) and the output cannot rise above the supply. Raise the bias or lower the signal.",
        "ro": "Partea de sus a ieșirii este aplatizată: pe acele vârfuri tranzistorul se blochează (capătul drept "
              "al dreptei de sarcină) și ieșirea nu poate urca peste tensiunea de alimentare. Mărește "
              "polarizarea sau micșorează semnalul."},
    "tg.explain.clip_both": {
        "en": "Both peaks are clipped: the signal is too large for the load line and drives the transistor into "
              "both saturation and cut-off. The output starts to look like a square wave.",
        "ro": "Ambele vârfuri sunt limitate: semnalul este prea mare pentru dreapta de sarcină și duce "
              "tranzistorul atât în saturație, cât și în blocare. Ieșirea începe să arate ca o undă dreptunghiulară."},
    "tg.explain.switch": {
        "en": "Switching: the input jumps between OFF (output = supply, no current) and fully ON (output ≈ 0 V, "
              "current limited only by the resistor). The transistor spends almost no time in between, so it "
              "dissipates very little power — this is how logic and power switches work.",
        "ro": "Comutare: intrarea sare între BLOCAT (ieșire = alimentare, fără curent) și complet DESCHIS (ieșire "
              "≈ 0 V, curent limitat doar de rezistor). Tranzistorul stă foarte puțin între cele două stări, deci "
              "disipă foarte puțină putere — așa funcționează comutatoarele logice și de putere."},
    "tg.explain.off": {
        "en": "The transistor is off: no current flows and the output sits at the supply voltage.",
        "ro": "Tranzistorul este blocat: nu circulă curent și ieșirea stă la tensiunea de alimentare."},
    "tg.explain.sat": {
        "en": "The transistor is fully on (saturated / ohmic): the output is close to 0 V and the current is set "
              "by the resistor, not by the transistor.",
        "ro": "Tranzistorul este complet deschis (saturat / regiune ohmică): ieșirea este aproape de 0 V, iar "
              "curentul este stabilit de rezistor, nu de tranzistor."},
    # ---------------- RF band explorer ----------------
    "rfx.title": {"en": "RF Band Explorer", "ro": "Explorator de benzi RF"},
    "rfx.intro": {
        "en": "Type any frequency to see which ITU band and radar letter band it belongs to, its wavelength, "
              "antenna lengths and which services use it. Browse the allocations by category to compare the "
              "frequency ranges, power limits, access rules and channel plans of Europe, North America, China "
              "and Japan.",
        "ro": "Introdu orice frecvență ca să vezi în ce bandă ITU și în ce bandă radar (literă) se află, lungimea "
              "de undă, lungimile de antenă și ce servicii o folosesc. Răsfoiește alocările pe categorii ca să "
              "compari intervalele de frecvență, limitele de putere, regulile de acces și planurile de canale din "
              "Europa, America de Nord, China și Japonia."},
    "rfx.lookup_title": {"en": "Frequency lookup", "ro": "Căutare frecvență"},
    "rfx.freq_label": {"en": "Frequency:", "ro": "Frecvență:"},
    "rfx.lookup_btn": {"en": "Look up", "ro": "Caută"},
    "rfx.lookup_hint": {"en": "e.g. 2.45 GHz, 868M, 13.56 MHz, 125k", "ro": "ex. 2.45 GHz, 868M, 13.56 MHz, 125k"},
    "rfx.bad_freq": {"en": "Enter a frequency, e.g. 433.92 MHz", "ro": "Introdu o frecvență, ex. 433.92 MHz"},
    "rfx.itu_band": {"en": "ITU band", "ro": "Banda ITU"},
    "rfx.dipole": {"en": "dipole", "ro": "dipol"},
    "rfx.monopole": {"en": "monopole (whip)", "ro": "monopol (bici)"},
    "rfx.fspl": {"en": "Free-space path loss", "ro": "Pierderi în spațiu liber"},
    "rfx.inside": {"en": "Allocations containing this frequency", "ro": "Alocări care conțin această frecvență"},
    "rfx.none": {"en": "none in this database", "ro": "niciuna în această bază de date"},
    "rfx.ruler_title": {"en": "Spectrum map 3 kHz – 300 GHz (log scale)", "ro": "Harta spectrului 3 kHz – 300 GHz (scară logaritmică)"},
    "rfx.ruler_hint": {"en": "Click a coloured bar to open that allocation, or click anywhere else to look up that frequency.",
                       "ro": "Clic pe o bară colorată ca să deschizi alocarea, sau oriunde altundeva ca să cauți acea frecvență."},
    "rfx.browser_title": {"en": "Allocations and channel plans", "ro": "Alocări și planuri de canale"},
    "rfx.category": {"en": "Category:", "ro": "Categorie:"},
    "rfx.all": {"en": "All categories", "ro": "Toate categoriile"},
    "rfx.search": {"en": "Search:", "ro": "Caută:"},
    "rfx.envelope": {"en": "Overall range", "ro": "Interval total"},
    "rfx.region": {"en": "Region", "ro": "Regiune"},
    "rfx.range": {"en": "Frequency range", "ro": "Interval de frecvență"},
    "rfx.power": {"en": "Max power", "ro": "Putere maximă"},
    "rfx.access": {"en": "Access rules", "ro": "Reguli de acces"},
    "rfx.chan_plan": {"en": "Channel plan", "ro": "Planul de canale"},
    "rfx.ch_count": {"en": "Channels", "ro": "Canale"},
    "rfx.ch_spacing": {"en": "Spacing", "ro": "Ecart"},
    "rfx.ch_width": {"en": "Bandwidth", "ro": "Lățime de bandă"},
    "rfx.ch_formula": {"en": "Centre frequency", "ro": "Frecvența centrală"},
    "rfx.chan_drawing": {"en": "{n} channels drawn to scale; overlapping channels are stacked in rows",
                         "ro": "{n} canale desenate la scară; canalele care se suprapun sunt așezate pe rânduri"},
    "rfx.note": {"en": "Note:", "ro": "Notă:"},
    "rfx.ref_title": {"en": "Reference: band designations", "ro": "Referință: denumirile benzilor"},
    "rfx.itu_rule": {
        "en": "ITU band N covers 0.3·10^N to 3·10^N Hz. Wavelength λ = c / f = 300 / f(MHz) metres.",
        "ro": "Banda ITU N acoperă 0,3·10^N până la 3·10^N Hz. Lungimea de undă λ = c / f = 300 / f(MHz) metri."},
    "rfx.col_n": {"en": "N", "ro": "N"},
    "rfx.col_sym": {"en": "Symbol", "ro": "Simbol"},
    "rfx.col_lambda": {"en": "Wavelength", "ro": "Lungime de undă"},
    "rfx.col_use": {"en": "Typical uses", "ro": "Utilizări tipice"},
    "rfx.col_letter": {"en": "Band", "ro": "Bandă"},
    "rfx.ieee_title": {"en": "IEEE 521 radar letter bands", "ro": "Benzi radar IEEE 521 (litere)"},
    "rfx.nato_title": {"en": "NATO / EU letter bands", "ro": "Benzi NATO / UE (litere)"},
    # ---------------- Boolean solver keypad + diagrams ----------------
    "digital.kp.clear": {"en": "Clear", "ro": "Șterge"},
    "digital.kp.examples": {"en": "Examples:", "ro": "Exemple:"},
    "digital.diag.title": {"en": "Logic diagrams", "ro": "Scheme logice"},
    "digital.diag.min_form": {"en": "Minimized form to draw:", "ro": "Forma minimizată desenată:"},
    "digital.diag.entered": {"en": "Circuit of the expression you entered", "ro": "Circuitul expresiei introduse"},
    "digital.diag.minimized": {"en": "Minimized circuit (same truth table)", "ro": "Circuitul minimizat (același tabel de adevăr)"},
    "digital.diag.cost": {"en": "{g} gates, {i} gate inputs", "ro": "{g} porți, {i} intrări de poartă"},
    "digital.diag.saved": {
        "en": "Minimization saves {g} gate(s) and {i} gate input(s) — fewer chips, less delay, lower power.",
        "ro": "Minimizarea economisește {g} poartă(i) și {i} intrare(i) de poartă — mai puține cipuri, întârziere și consum mai mici."},
    "digital.diag.already_min": {
        "en": "Your expression is already as small as the minimal two-level form (or smaller, if it uses XOR or multi-level logic).",
        "ro": "Expresia ta este deja la fel de mică precum forma minimă pe două niveluri (sau mai mică, dacă folosește XOR sau logică pe mai multe niveluri)."},
    # ---------------- Unit converter (reworked) ----------------
    "uc2.tab.convert": {"en": "Converter", "ro": "Convertor"},
    "uc2.tab.levels": {"en": "dB & signal levels", "ro": "dB și niveluri de semnal"},
    "uc2.tab.numbers": {"en": "Number systems", "ro": "Sisteme de numerație"},
    "uc2.tab.adc": {"en": "ADC / DAC", "ro": "ADC / DAC"},
    "uc2.convert_intro": {
        "en": "Pick a category, type a value and choose its unit — the table shows it in every other unit at once. "
            "Click any row to continue from that unit.",
        "ro": "Alege o categorie, scrie o valoare și alege-i unitatea — tabelul o arată imediat în toate celelalte "
            "unități. Clic pe un rând ca să continui de la acea unitate."},
    "uc2.category": {"en": "Category", "ro": "Categorie"},
    "uc2.value": {"en": "Value:", "ro": "Valoare:"},
    "uc2.col_unit": {"en": "Unit", "ro": "Unitate"},
    "uc2.col_value": {"en": "Value", "ro": "Valoare"},
    "uc2.col_desc": {"en": "Meaning", "ro": "Semnificație"},
    "uc2.row_hint": {"en": "Blue row = the unit you typed in; green = the best engineering prefix.",
                     "ro": "Rândul albastru = unitatea introdusă; verde = cel mai potrivit prefix ingineresc."},
    "uc2.hint": {"en": "Use a dot or comma for decimals; 1e-3 style is accepted.",
                 "ro": "Folosește punct sau virgulă pentru zecimale; se acceptă și forma 1e-3."},
    "uc2.elec_hint": {"en": "You can type prefixes directly: 4.7k, 100n, 2.2u, 10M.",
                      "ro": "Poți scrie direct prefixele: 4.7k, 100n, 2.2u, 10M."},
    "uc2.hint_freq": {"en": "Frequency, period and wavelength are linked: T = 1/f, λ = c/f, ω = 2πf.",
                      "ro": "Frecvența, perioada și lungimea de undă sunt legate: T = 1/f, λ = c/f, ω = 2πf."},
    "uc2.hint_temp": {"en": "Temperature scales have different zero points, so they are not simple factors.",
                      "ro": "Scalele de temperatură au zerouri diferite, deci nu sunt simpli factori."},
    "uc2.hint_awg": {"en": "Each AWG step changes the diameter by ≈ 12 %; 6 steps ≈ half the diameter, 3 steps ≈ half the area.",
                     "ro": "Fiecare treaptă AWG schimbă diametrul cu ≈ 12 %; 6 trepte ≈ jumătate din diametru, 3 trepte ≈ jumătate din secțiune."},
    "uc2.hint_energy": {"en": "Battery energy: Wh = mAh × V / 1000.", "ro": "Energia bateriei: Wh = mAh × V / 1000."},
    "uc2.hint_data": {"en": "kB/MB/GB are powers of 1000; KiB/MiB/GiB are powers of 1024.",
                      "ro": "kB/MB/GB sunt puteri ale lui 1000; KiB/MiB/GiB sunt puteri ale lui 1024."},
    "uc2.lv.intro": {
        "en": "Type into ANY field — the others update instantly. Power and voltage are linked through the "
              "impedance R (P = V²/R), so pick 50 Ω for RF, 75 Ω for video/TV, 600 Ω for old audio lines.",
        "ro": "Scrie în ORICE câmp — celelalte se actualizează imediat. Puterea și tensiunea sunt legate prin "
              "impedanța R (P = V²/R), deci alege 50 Ω pentru RF, 75 Ω pentru video/TV, 600 Ω pentru liniile audio vechi."},
    "uc2.lv.abs_title": {"en": "Absolute levels", "ro": "Niveluri absolute"},
    "uc2.lv.impedance": {"en": "Impedance R", "ro": "Impedanța R"},
    "uc2.lv.w": {"en": "power (prefixes ok: 10m = 10 mW)", "ro": "putere (se acceptă prefixe: 10m = 10 mW)"},
    "uc2.lv.dbm": {"en": "dB relative to 1 mW", "ro": "dB față de 1 mW"},
    "uc2.lv.dbw": {"en": "dB relative to 1 W", "ro": "dB față de 1 W"},
    "uc2.lv.vrms": {"en": "RMS voltage (sine)", "ro": "tensiune efectivă (sinus)"},
    "uc2.lv.vpk": {"en": "peak = √2 · Vrms", "ro": "vârf = √2 · Vef"},
    "uc2.lv.vpp": {"en": "peak-to-peak = 2√2 · Vrms", "ro": "vârf-vârf = 2√2 · Vef"},
    "uc2.lv.dbv": {"en": "dB relative to 1 Vrms", "ro": "dB față de 1 Vef"},
    "uc2.lv.dbu": {"en": "dB relative to 0.775 Vrms (audio)", "ro": "dB față de 0,775 Vef (audio)"},
    "uc2.lv.dbuv": {"en": "dB relative to 1 µV (receivers, EMC)", "ro": "dB față de 1 µV (receptoare, EMC)"},
    "uc2.lv.note": {"en": "Voltages assume a sine wave across R = {r}Ω. dBm → dBµV at 50 Ω: add 107.",
                    "ro": "Tensiunile presupun o sinusoidă pe R = {r}Ω. dBm → dBµV la 50 Ω: adună 107."},
    "uc2.lv.ratio_title": {"en": "Ratios and gains", "ro": "Rapoarte și amplificări"},
    "uc2.lv.pratio": {"en": "Power ratio", "ro": "Raport de putere"},
    "uc2.lv.vratio": {"en": "Voltage ratio", "ro": "Raport de tensiune"},
    "uc2.lv.vpct": {"en": "Voltage %", "ro": "Tensiune %"},
    "uc2.lv.ratio_note": {
        "en": "Power: dB = 10·log10(P2/P1). Voltage/current: dB = 20·log10(V2/V1) (same impedance). "
              "Gains in dB simply add along a chain. Click a row of the table to use it.",
        "ro": "Putere: dB = 10·log10(P2/P1). Tensiune/curent: dB = 20·log10(V2/V1) (aceeași impedanță). "
              "Amplificările în dB se adună de-a lungul unui lanț. Clic pe un rând din tabel ca să-l folosești."},
    "uc2.nb.intro": {
        "en": "Type in any field (decimal, hex, octal, binary or text) or click the bits below to toggle them. "
              "Prefixes 0x / 0b / 0o and spaces or underscores are accepted.",
        "ro": "Scrie în orice câmp (zecimal, hexazecimal, octal, binar sau text) sau apasă pe biții de mai jos ca să-i "
              "comuți. Se acceptă prefixele 0x / 0b / 0o și spații sau liniuțe jos."},
    "uc2.nb.width": {"en": "Word size:", "ro": "Dimensiune cuvânt:"},
    "uc2.nb.signed": {"en": "Signed (two's complement)", "ro": "Cu semn (complement față de 2)"},
    "uc2.nb.dec": {"en": "Decimal (10)", "ro": "Zecimal (10)"},
    "uc2.nb.hex": {"en": "Hexadecimal (16)", "ro": "Hexazecimal (16)"},
    "uc2.nb.oct": {"en": "Octal (8)", "ro": "Octal (8)"},
    "uc2.nb.bin": {"en": "Binary (2)", "ro": "Binar (2)"},
    "uc2.nb.ascii": {"en": "ASCII text", "ro": "Text ASCII"},
    "uc2.nb.bits_title": {"en": "Bits — click to toggle", "ro": "Biți — clic pentru a comuta"},
    "uc2.nb.clear": {"en": "All 0", "ro": "Toți 0"},
    "uc2.nb.all1": {"en": "All 1", "ro": "Toți 1"},
    "uc2.nb.invert": {"en": "Invert (NOT)", "ro": "Inversează (NOT)"},
    "uc2.nb.overflow": {"en": "Value does not fit in {n} bits", "ro": "Valoarea nu încape în {n} biți"},
    "uc2.nb.invalid": {"en": "Invalid digit for this base", "ro": "Cifră invalidă pentru această bază"},
    "uc2.nb.unsigned": {"en": "Unsigned", "ro": "Fără semn"},
    "uc2.nb.signed_val": {"en": "Signed", "ro": "Cu semn"},
    "uc2.nb.range": {"en": "Range", "ro": "Domeniu"},
    "uc2.nb.ones": {"en": "Bits set", "ro": "Biți de 1"},
    "uc2.nb.bytes": {"en": "Bytes (big-endian)", "ro": "Octeți (big-endian)"},
}
