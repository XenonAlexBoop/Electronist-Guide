"""
i18n_extra.py - Translation strings for the v5.0 features (schematic
symbols, "solve for anything" calculators, new voltage divider, full
Mixed-Builder schematic, AC quantities & ripple). Merged into
i18n.STRINGS at import time.
"""

EXTRA = {
    # ---- generic chart ----
    "chart.time_axis": {"en": "Time", "ro": "Timp"},

    # ---- schematic symbols ----
    "sym.header_label": {"en": "Symbols:", "ro": "Simboluri:"},
    "sym.gallery_title": {"en": "🔣  Schematic symbols", "ro": "🔣  Simboluri în schemă"},
    "sym.gallery_hint": {
        "en": "How this component is drawn in circuit diagrams. Diagrams in the app use the {style} "
              "standard (switch IEC / ANSI in the top bar).",
        "ro": "Cum se desenează această componentă în schemele electrice. Schemele din aplicație "
              "folosesc standardul {style} (comută IEC / ANSI din bara de sus)."},
    "sym.res_iec": {"en": "Resistor (IEC)", "ro": "Rezistor (IEC)"},
    "sym.res_ansi": {"en": "Resistor (ANSI)", "ro": "Rezistor (ANSI)"},
    "sym.res_variable": {"en": "Variable resistor", "ro": "Rezistor variabil"},
    "sym.res_pot": {"en": "Potentiometer", "ro": "Potențiometru"},
    "sym.res_ntc": {"en": "Thermistor (NTC)", "ro": "Termistor (NTC)"},
    "sym.res_ldr": {"en": "Photoresistor (LDR)", "ro": "Fotorezistor (LDR)"},
    "sym.cap_fixed": {"en": "Capacitor", "ro": "Condensator"},
    "sym.cap_polarized": {"en": "Polarized (electrolytic)", "ro": "Polarizat (electrolitic)"},
    "sym.cap_variable": {"en": "Variable capacitor", "ro": "Condensator variabil"},
    "sym.ind_air": {"en": "Inductor (air core)", "ro": "Bobină (miez de aer)"},
    "sym.ind_iron": {"en": "Iron core", "ro": "Miez de fier"},
    "sym.ind_ferrite": {"en": "Ferrite core", "ro": "Miez de ferită"},
    "sym.ind_variable": {"en": "Variable inductor", "ro": "Bobină variabilă"},
    "sym.transformer": {"en": "Transformer", "ro": "Transformator"},
    "sym.diode": {"en": "Diode", "ro": "Diodă"},
    "sym.zener": {"en": "Zener diode", "ro": "Diodă Zener"},
    "sym.schottky": {"en": "Schottky diode", "ro": "Diodă Schottky"},
    "sym.led": {"en": "LED", "ro": "LED"},
    "sym.photodiode": {"en": "Photodiode", "ro": "Fotodiodă"},
    "sym.varicap": {"en": "Varicap", "ro": "Varicap"},
    "sym.npn": {"en": "NPN transistor", "ro": "Tranzistor NPN"},
    "sym.pnp": {"en": "PNP transistor", "ro": "Tranzistor PNP"},
    "sym.nmos_enh": {"en": "N-MOSFET (enhancement)", "ro": "MOSFET-N (cu îmbogățire)"},
    "sym.pmos_enh": {"en": "P-MOSFET (enhancement)", "ro": "MOSFET-P (cu îmbogățire)"},
    "sym.nmos_dep": {"en": "N-MOSFET (depletion)", "ro": "MOSFET-N (cu sărăcire)"},
    "sym.pmos_dep": {"en": "P-MOSFET (depletion)", "ro": "MOSFET-P (cu sărăcire)"},
    "sym.njfet": {"en": "N-channel JFET", "ro": "JFET canal N"},
    "sym.pjfet": {"en": "P-channel JFET", "ro": "JFET canal P"},
    "sym.opamp": {"en": "Op-amp", "ro": "Amplificator operațional"},
    "sym.opamp_supply": {"en": "Op-amp with supply pins", "ro": "AO cu pini de alimentare"},
    "sym.cell": {"en": "Cell", "ro": "Element (celulă)"},
    "sym.battery": {"en": "Battery (3 cells)", "ro": "Baterie (3 elemente)"},
    "sym.dc_source": {"en": "DC voltage source", "ro": "Sursă de tensiune DC"},
    "sym.ac_source": {"en": "AC source", "ro": "Sursă AC"},
    "sym.ground": {"en": "Ground", "ro": "Masă"},

    # ---- formula solver ----
    "solver.tab": {"en": "🧮 Calculator (solve any)", "ro": "🧮 Calculator (orice mărime)"},
    "solver.intro": {
        "en": "Pick a formula, then tick the ○ of the quantity you want to find. Type the others — "
              "the result updates as you type. Any variable can be the unknown.",
        "ro": "Alege o formulă, apoi bifează ○ la mărimea pe care vrei să o afli. Completează-le pe "
              "celelalte — rezultatul se actualizează pe măsură ce scrii. Orice variabilă poate fi necunoscuta."},
    "solver.choose": {"en": "Formula:", "ro": "Formula:"},
    "solver.col_solve": {"en": "Find", "ro": "Află"},
    "solver.col_symbol": {"en": "Symbol", "ro": "Simbol"},
    "solver.col_quantity": {"en": "Quantity", "ro": "Mărime"},
    "solver.col_value": {"en": "Value", "ro": "Valoare"},
    "solver.presets": {"en": "presets…", "ro": "valori tipice…"},
    "solver.no_solution": {"en": "No real solution for {sym} with these values — check the inputs.",
                           "ro": "Nu există soluție reală pentru {sym} cu aceste valori — verifică datele."},
    "solver.or": {"en": "or", "ro": "sau"},
    "solver.multiple": {"en": "(more than one value satisfies the formula)",
                        "ro": "(mai multe valori satisfac formula)"},
    "solver.hint": {
        "en": "Prefixes: p n u(µ) m k M G — e.g. 4.7k, 100n, 22u, 1.5M. Note: \"m\" means milli (10m = 0.01), "
              "so type lengths in metres as plain numbers. Scientific notation works too (1.68e-8).",
        "ro": "Prefixe: p n u(µ) m k M G — ex. 4.7k, 100n, 22u, 1.5M. Atenție: \"m\" înseamnă mili (10m = 0,01), "
              "deci scrie lungimile în metri ca numere simple. Merge și notația științifică (1.68e-8)."},

    # ---- mixed builder ----
    "combos.schematic_title": {"en": "Complete schematic (A → B)", "ro": "Schema completă (A → B)"},
    "combos.col_name": {"en": "Name", "ro": "Nume"},
    "combos.col_voltage": {"en": "Voltage", "ro": "Tensiune"},
    "combos.col_current": {"en": "Current", "ro": "Curent"},
    "combos.col_power": {"en": "Power", "ro": "Putere"},
    "combos.col_charge": {"en": "Charge Q", "ro": "Sarcină Q"},
    "combos.col_energy": {"en": "Energy", "ro": "Energie"},
    "combos.col_flux": {"en": "Flux linkage L·I", "ro": "Flux înlănțuit L·I"},
    "combos.op_legend": {"en": "+ = series,  ∥ = parallel", "ro": "+ = serie,  ∥ = paralel"},
    "combos.apply_voltage": {"en": "Apply a voltage between A and B:", "ro": "Aplică o tensiune între A și B:"},
    "combos.apply_current": {"en": "Current flowing from A to B:", "ro": "Curentul care intră în A și iese prin B:"},
    "combos.detail_note_r": {"en": "Total current from the source: {i}   —   total power: {p}",
                             "ro": "Curentul total din sursă: {i}   —   putere totală: {p}"},
    "combos.detail_note_c": {"en": "Total charge taken from the source: {q}   —   total stored energy: {e}",
                             "ro": "Sarcina totală preluată din sursă: {q}   —   energie totală înmagazinată: {e}"},
    "combos.detail_note_l": {"en": "Total stored magnetic energy: {e}  (ideal coils, no mutual coupling)",
                             "ro": "Energia magnetică totală înmagazinată: {e}  (bobine ideale, fără cuplaj mutual)"},

    # ---- voltage divider ----
    "vd.intro": {
        "en": "Vin feeds R1 (top). Node A connects to R2 (bottom, to ground). With a 2nd stage, R3 continues "
              "from A to the output node and R4 goes to ground. RL is an optional load on the output. "
              "Choose which quantity to find with the ○ in the table.",
        "ro": "Vin alimentează R1 (sus). Nodul A se leagă la R2 (jos, la masă). Cu a 2-a etapă, R3 continuă "
              "de la A spre nodul de ieșire, iar R4 merge la masă. RL este o sarcină opțională pe ieșire. "
              "Alege mărimea de aflat cu ○ din tabel."},
    "vd.opt_stage2": {"en": "Second stage (R3, R4)", "ro": "A doua etapă (R3, R4)"},
    "vd.opt_load": {"en": "Load resistor RL", "ro": "Rezistor de sarcină RL"},
    "vd.inputs_title": {"en": "Values", "ro": "Valori"},
    "vd.inputs_hint": {"en": "Tick ○ next to the unknown; fill in the rest (prefixes allowed: 4.7k, 1M…).",
                       "ro": "Bifează ○ lângă necunoscută; completează restul (prefixe permise: 4.7k, 1M…)."},
    "vd.field.Vin": {"en": "Input (source) voltage", "ro": "Tensiunea de intrare (sursă)"},
    "vd.field.R1": {"en": "Top resistor (Vin → A)", "ro": "Rezistorul de sus (Vin → A)"},
    "vd.field.R2": {"en": "Bottom resistor (A → GND)", "ro": "Rezistorul de jos (A → masă)"},
    "vd.field.R3": {"en": "Stage 2 series (A → Vout)", "ro": "Etapa 2, serie (A → Vout)"},
    "vd.field.R4": {"en": "Stage 2 to ground (Vout → GND)", "ro": "Etapa 2, la masă (Vout → masă)"},
    "vd.field.RL": {"en": "Load on the output", "ro": "Sarcina de la ieșire"},
    "vd.field.Vout": {"en": "Output voltage", "ro": "Tensiunea de ieșire"},
    "vd.solved": {"en": "Result:", "ro": "Rezultat:"},
    "vd.no_solution": {"en": "No valid value of {x} gives that output — the target may be out of range.",
                       "ro": "Nicio valoare validă pentru {x} nu dă această ieșire — ținta poate fi în afara domeniului."},
    "vd.rin": {"en": "Resistance seen by the source", "ro": "Rezistența văzută de sursă"},
    "vd.pin": {"en": "Power drawn", "ro": "Puterea consumată"},
    "vd.load_effect": {"en": "Without load: {unl}  →  with RL: {ld}   (drop {pct} %)",
                       "ro": "Fără sarcină: {unl}  →  cu RL: {ld}   (scădere {pct} %)"},
    "vd.col_element": {"en": "Element", "ro": "Element"},
    "vd.col_resistance": {"en": "Resistance", "ro": "Rezistență"},
    "vd.col_voltage": {"en": "Voltage across", "ro": "Tensiune pe el"},
    "vd.col_current": {"en": "Current", "ro": "Curent"},
    "vd.col_power": {"en": "Power", "ro": "Putere"},
    "vd.source": {"en": "Source", "ro": "Sursa"},
    "vd.formulas": {
        "en": "Vout = Vin · R2/(R1+R2)        I = Vin/(R1+R2)\n"
              "With load:  R2 → R2∥RL = R2·RL/(R2+RL)\n"
              "2 stages:   V_A = Vin · Z_A/(R1+Z_A),  Z_A = R2 ∥ (R3 + R4∥RL),   Vout = V_A · R4/(R3+R4)",
        "ro": "Vout = Vin · R2/(R1+R2)        I = Vin/(R1+R2)\n"
              "Cu sarcină: R2 → R2∥RL = R2·RL/(R2+RL)\n"
              "2 etape:    V_A = Vin · Z_A/(R1+Z_A),  Z_A = R2 ∥ (R3 + R4∥RL),   Vout = V_A · R4/(R3+R4)"},
    "vd.design_title": {"en": "Design with standard values (E-series)", "ro": "Proiectare cu valori standard (seria E)"},
    "vd.design_intro": {
        "en": "Enter the voltages you need and roughly how much current the divider may draw; the best "
              "standard R1/R2 pairs are listed. Select a row and press Apply.",
        "ro": "Introdu tensiunile dorite și aproximativ ce curent poate consuma divizorul; sunt listate cele mai "
              "bune perechi standard R1/R2. Selectează un rând și apasă Aplică."},
    "vd.design_target": {"en": "Target Vout", "ro": "Vout dorit"},
    "vd.design_current": {"en": "Divider current ≈", "ro": "Curent divizor ≈"},
    "vd.design_series": {"en": "Series", "ro": "Seria"},
    "vd.design_find": {"en": "Find pairs", "ro": "Caută perechi"},
    "vd.design_apply": {"en": "Apply selected pair ↑", "ro": "Aplică perechea selectată ↑"},
    "vd.design_bad": {"en": "Need 0 < Vout < Vin", "ro": "Trebuie 0 < Vout < Vin"},
    "vd.d_r1": {"en": "R1", "ro": "R1"},
    "vd.d_r2": {"en": "R2", "ro": "R2"},
    "vd.d_vout": {"en": "Vout", "ro": "Vout"},
    "vd.d_err": {"en": "Error", "ro": "Eroare"},
    "vd.d_i": {"en": "Current", "ro": "Curent"},

    # ---- AC quantities ----
    "acw.tab": {"en": "AC Quantities & Ripple", "ro": "Mărimi alternative & Riplu"},
    "acw.intro": {
        "en": "Enter ONE amplitude quantity and ONE time quantity (whatever you know) — every other value "
              "of the signal is calculated: maximum, peak-to-peak, effective (RMS), average, period, "
              "frequency, instantaneous value and more.",
        "ro": "Introdu O mărime de amplitudine și O mărime de timp (ce cunoști) — toate celelalte valori ale "
              "semnalului sunt calculate: maximă, vârf-vârf, efectivă (RMS), medie, perioadă, frecvență, "
              "valoare instantanee și altele."},
    "acw.waveform": {"en": "Waveform", "ro": "Forma de undă"},
    "acw.wave.sine": {"en": "Sine", "ro": "Sinusoidală"},
    "acw.wave.square": {"en": "Square (symmetric)", "ro": "Dreptunghiulară (simetrică)"},
    "acw.wave.triangle": {"en": "Triangle", "ro": "Triunghiulară"},
    "acw.wave.sawtooth": {"en": "Sawtooth", "ro": "Dinte de fierăstrău"},
    "acw.wave.half_rect": {"en": "Half-wave rectified sine", "ro": "Sinus redresat monoalternanță"},
    "acw.wave.full_rect": {"en": "Full-wave rectified sine", "ro": "Sinus redresat dublă alternanță"},
    "acw.quantity": {"en": "Quantity", "ro": "Mărimea"},
    "acw.qty.voltage": {"en": "Voltage (V)", "ro": "Tensiune (V)"},
    "acw.qty.current": {"en": "Current (A)", "ro": "Curent (A)"},
    "acw.known_amp": {"en": "1. What amplitude value do you know?", "ro": "1. Ce valoare de amplitudine cunoști?"},
    "acw.amp.max": {"en": "Amplitude / maximum (peak) value", "ro": "Amplitudine / valoare maximă (de vârf)"},
    "acw.amp.pp": {"en": "Peak-to-peak value", "ro": "Valoare vârf-vârf"},
    "acw.amp.rms": {"en": "Effective (RMS) value", "ro": "Valoare efectivă (RMS)"},
    "acw.amp.avg": {"en": "Average (rectified) value", "ro": "Valoare medie (redresată)"},
    "acw.known_time": {"en": "2. What time value do you know?", "ro": "2. Ce mărime de timp cunoști?"},
    "acw.time.f": {"en": "Frequency f (Hz)", "ro": "Frecvența f (Hz)"},
    "acw.time.T": {"en": "Period T (s)", "ro": "Perioada T (s)"},
    "acw.time.w": {"en": "Angular frequency ω (rad/s)", "ro": "Pulsația ω (rad/s)"},
    "acw.value": {"en": "Value", "ro": "Valoare"},
    "acw.extras": {"en": "3. Optional", "ro": "3. Opțional"},
    "acw.phase": {"en": "Initial phase φ", "ro": "Faza inițială φ"},
    "acw.offset": {"en": "DC offset", "ro": "Componentă continuă (offset)"},
    "acw.instant_t": {"en": "Instantaneous value at t =", "ro": "Valoarea instantanee la t ="},
    "acw.find_value": {"en": "When does it reach the value", "ro": "Când atinge valoarea"},
    "acw.results": {"en": "Results", "ro": "Rezultate"},
    "acw.col_quantity": {"en": "Quantity", "ro": "Mărime"},
    "acw.col_symbol": {"en": "Symbol", "ro": "Simbol"},
    "acw.col_value": {"en": "Value", "ro": "Valoare"},
    "acw.r.amplitude": {"en": "Amplitude (of the AC part)", "ro": "Amplitudine (a părții alternative)"},
    "acw.r.max": {"en": "Maximum value", "ro": "Valoare maximă"},
    "acw.r.min": {"en": "Minimum value", "ro": "Valoare minimă"},
    "acw.r.pp": {"en": "Peak-to-peak value", "ro": "Valoare vârf-vârf"},
    "acw.r.rms": {"en": "Effective (RMS) value", "ro": "Valoare efectivă (RMS)"},
    "acw.r.avg_rect": {"en": "Average (rectified) value", "ro": "Valoare medie (redresată)"},
    "acw.r.mean": {"en": "True average / DC component", "ro": "Media reală / componenta continuă"},
    "acw.r.ac_rms": {"en": "RMS of the AC part (ripple)", "ro": "RMS al părții alternative (riplu)"},
    "acw.r.ripple_factor": {"en": "Ripple factor", "ro": "Factor de ondulație (riplu)"},
    "acw.r.form": {"en": "Form factor (RMS / avg)", "ro": "Factor de formă (RMS / medie)"},
    "acw.r.crest": {"en": "Crest (peak) factor (max / RMS)", "ro": "Factor de vârf (max / RMS)"},
    "acw.r.freq": {"en": "Frequency", "ro": "Frecvență"},
    "acw.r.period": {"en": "Period", "ro": "Perioadă"},
    "acw.r.omega": {"en": "Angular frequency", "ro": "Pulsație"},
    "acw.r.out_freq": {"en": "Pulse (ripple) frequency", "ro": "Frecvența pulsurilor (riplului)"},
    "acw.r.lambda": {"en": "Wavelength (in free space)", "ro": "Lungime de undă (în vid)"},
    "acw.r.instant": {"en": "Instantaneous value at t = {t}", "ro": "Valoarea instantanee la t = {t}"},
    "acw.r.angle": {"en": "Phase angle at t", "ro": "Unghiul de fază la t"},
    "acw.r.when": {"en": "Reaches {v} at t =", "ro": "Atinge {v} la t ="},
    "acw.never": {"en": "never (outside min…max)", "ro": "niciodată (în afara min…max)"},
    "acw.chart_y": {"en": "Instantaneous value", "ro": "Valoare instantanee"},
    "acw.note_amp": {
        "en": "The amplitude you enter describes the AC waveform itself; a DC offset is then added on top. "
              "Times are measured within the first period.",
        "ro": "Amplitudinea introdusă descrie forma de undă alternativă; componenta continuă se adaugă peste. "
              "Momentele de timp sunt căutate în prima perioadă."},
    "acw.note_rect": {
        "en": "For rectified waves, f and T are those of the source sine; a full-wave output pulses at 2·f.",
        "ro": "Pentru undele redresate, f și T sunt ale sinusului sursei; ieșirea dublă alternanță pulsează la 2·f."},
    "acw.rip_title": {"en": "Rectifier + filter capacitor ripple", "ro": "Riplul redresor + condensator de filtraj"},
    "acw.rip_intro": {
        "en": "Transformer secondary (RMS) → diodes → reservoir capacitor → load. Standard approximation "
              "Vr = I / (f_ripple · C).",
        "ro": "Secundar transformator (RMS) → diode → condensator de filtraj → sarcină. Aproximarea uzuală "
              "Vr = I / (f_riplu · C)."},
    "acw.rip_rect": {"en": "Rectifier", "ro": "Redresor"},
    "acw.rip_half": {"en": "Half-wave (1 diode)", "ro": "Monoalternanță (1 diodă)"},
    "acw.rip_full": {"en": "Full-wave bridge (4 diodes)", "ro": "Punte dublă alternanță (4 diode)"},
    "acw.rip_vrms": {"en": "AC input (RMS)", "ro": "Intrare AC (RMS)"},
    "acw.rip_f": {"en": "Mains frequency", "ro": "Frecvența rețelei"},
    "acw.rip_vd": {"en": "Diode drop", "ro": "Căderea pe diodă"},
    "acw.rip_il": {"en": "Load current", "ro": "Curentul de sarcină"},
    "acw.rip_c": {"en": "Filter capacitor", "ro": "Condensator de filtraj"},
    "acw.rip_solve_c": {"en": "Find C for ripple Vr(pp) =", "ro": "Află C pentru riplul Vr(vv) ="},
    "acw.rip_warn": {"en": "⚠ Ripple larger than the peak — use a bigger capacitor.",
                     "ro": "⚠ Riplul depășește vârful — folosește un condensator mai mare."},
    "acw.meas_title": {"en": "Ripple from measured Vmax / Vmin", "ro": "Riplu din Vmax / Vmin măsurate"},
    "acw.meas_max": {"en": "Vmax (V)", "ro": "Vmax (V)"},
    "acw.meas_min": {"en": "Vmin (V)", "ro": "Vmin (V)"},
    "acw.meas_pct": {"en": "Ripple", "ro": "Riplu"},
    "acw.meas_tri": {"en": "sawtooth-shaped ripple", "ro": "riplu în formă de dinte de fierăstrău"},
}
