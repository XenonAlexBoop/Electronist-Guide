"""EN/RO strings for the reworked Junction Visualizer and the transistor
Basic Circuits sub-tab (v5.1). Merged into i18n.STRINGS."""

EXTRA_TR = {
    # ---------------- Junction visualizer ----------------
    "jv.intro.bjt": {
        "en": "Each slider biases one junction. Pick a preset or drag the dot on the bias map to visit every "
              "way charge can flow: forward active, saturation, cut-off, reverse active, and both breakdowns. "
              "Blue dots = electrons, red rings = holes; more dots = more current.",
        "ro": "Fiecare cursor polarizează o joncțiune. Alege o presetare sau trage punctul pe harta de "
              "polarizare ca să vezi toate modurile în care pot circula sarcinile: activ normal, saturație, "
              "blocare, activ invers și ambele străpungeri. Puncte albastre = electroni, cercuri roșii = goluri; "
              "mai multe puncte = curent mai mare."},
    "jv.intro.mosfet": {
        "en": "The gate voltage pulls carriers to the surface and forms a channel; the drain voltage makes them "
              "flow and pinches the channel near the drain. Go negative on VDS to see the channel run backwards "
              "and the body diode turn on, or push VDS past breakdown.",
        "ro": "Tensiunea de grilă atrage purtătorii la suprafață și formează canalul; tensiunea de drenă îi pune "
              "în mișcare și ștrangulează canalul lângă drenă. Mergi la VDS negativ ca să vezi canalul "
              "conducând invers și dioda internă deschizându-se, sau depășește tensiunea de străpungere."},
    "jv.intro.jfet": {
        "en": "The reverse-biased gate junctions grow depletion regions that squeeze the channel. VGS narrows "
              "it everywhere; VDS narrows it more near the drain (pinch-off). Forward-bias the gate or exceed "
              "the gate-drain breakdown to see the other current paths.",
        "ro": "Joncțiunile grilei polarizate invers creează regiuni golite care strâng canalul. VGS îl îngustează "
              "peste tot; VDS îl îngustează mai mult lângă drenă (ștrangulare). Polarizează direct grila sau "
              "depășește străpungerea grilă-drenă ca să vezi celelalte căi de curent."},
    "jv.presets": {"en": "Try:", "ro": "Încearcă:"},
    "jv.legend": {
        "en": "●  electron (moving)     ○  hole (moving)     small dots = free majority carriers at rest     "
              "+ / − in the beige zones = fixed ionised dopants (depletion region)     ⚡ = breakdown",
        "ro": "●  electron (în mișcare)     ○  gol (în mișcare)     puncte mici = purtători majoritari liberi în "
              "repaus     + / − în zonele bej = ioni ficși (regiunea golită)     ⚡ = străpungere"},
    "jv.vbe": {"en": "Base-emitter voltage VBE", "ro": "Tensiunea bază-emitor VBE"},
    "jv.vce": {"en": "Collector-emitter voltage VCE", "ro": "Tensiunea colector-emitor VCE"},
    "jv.vbc": {"en": "Base-collector voltage VBC", "ro": "Tensiunea bază-colector VBC"},
    "jv.vgs": {"en": "Gate-source voltage VGS", "ro": "Tensiunea grilă-sursă VGS"},
    "jv.vds": {"en": "Drain-source voltage VDS", "ro": "Tensiunea drenă-sursă VDS"},
    "jv.second_control": {"en": "Second slider sets:", "ro": "Al doilea cursor setează:"},
    "jv.mode_vce": {"en": "VCE (circuit view)", "ro": "VCE (vedere de circuit)"},
    "jv.mode_vbc": {"en": "VBC (junction view)", "ro": "VBC (vedere pe joncțiuni)"},
    "jv.mos_type": {"en": "Type:", "ro": "Tip:"},
    "jv.enhancement": {"en": "Enhancement", "ro": "Cu îmbogățire"},
    "jv.depletion": {"en": "Depletion", "ro": "Cu sărăcire"},
    "jv.clip_note": {
        "en": "Note: with this VBE and VCE the collector junction would be forward biased by more than 0.9 V. "
              "A real circuit limits that with its resistors, so the view is held at VBC = 0.9 V.",
        "ro": "Notă: cu aceste VBE și VCE joncțiunea colectorului ar fi polarizată direct cu peste 0,9 V. "
              "Într-un circuit real rezistoarele limitează acest lucru, așa că vizualizarea rămâne la VBC = 0,9 V."},
    "jv.oxide_note": {
        "en": "⚠ |VGS| is above the typical 20 V oxide rating: the thin gate oxide can be punctured and the "
              "MOSFET permanently destroyed. (The model still shows the channel.)",
        "ro": "⚠ |VGS| depășește valoarea tipică de 20 V a oxidului: oxidul subțire al grilei poate fi străpuns "
              "și MOSFET-ul distrus definitiv. (Modelul încă arată canalul.)"},
    "jv.ptype_note": {
        "en": "(P-type device: every voltage and current is reversed and holes do the job of electrons.)",
        "ro": "(Dispozitiv de tip P: toate tensiunile și curenții sunt inversate, iar golurile fac rolul electronilor.)"},
    "jv.forward": {"en": "forward", "ro": "direct"},
    "jv.reverse": {"en": "reverse", "ro": "invers"},
    "jv.zero_bias": {"en": "0 V", "ro": "0 V"},
    "jv.bjt.emitter": {"en": "Emitter", "ro": "Emitor"},
    "jv.bjt.base": {"en": "Base", "ro": "Bază"},
    "jv.bjt.collector": {"en": "Collector", "ro": "Colector"},
    "jv.mos.source": {"en": "source", "ro": "sursă"},
    "jv.mos.drain": {"en": "drain", "ro": "drenă"},
    "jv.mos.body": {"en": "body (substrate)", "ro": "substrat"},
    "jv.mos.channel": {"en": "inversion channel", "ro": "canal de inversie"},
    "jv.mos.pinched": {"en": "channel pinched off at one end", "ro": "canal ștrangulat la un capăt"},
    "jv.mos.oxide": {"en": "gate oxide", "ro": "oxidul grilei"},
    "jv.mos.body_tied": {"en": "body tied to source", "ro": "substratul legat la sursă"},
    "jv.jfet.gate": {"en": "gate", "ro": "grilă"},
    "jv.jfet.channel": {"en": "channel", "ro": "canal"},
    "jv.jfet.pinched": {"en": "depletion regions meet: pinch-off (current still flows through the neck)",
                        "ro": "regiunile golite se ating: ștrangulare (curentul trece totuși prin gât)"},
    "jv.symbol_title": {"en": "Symbol & terminal currents", "ro": "Simbol și curenții terminalelor"},
    "jv.conv_current": {"en": "orange arrows = conventional current (+ → −)",
                        "ro": "săgeți portocalii = sensul convențional al curentului (+ → −)"},
    "jv.map_hint": {"en": "click / drag to set the bias", "ro": "clic / trage pentru a polariza"},
    "jv.curve_hint": {"en": "ID(VDS) at VGS = {v} V", "ro": "ID(VDS) la VGS = {v} V"},

    # region names
    "jv.region.bjt.active": {"en": "Forward active", "ro": "Activ normal"},
    "jv.region.bjt.saturation": {"en": "Saturation", "ro": "Saturație"},
    "jv.region.bjt.cutoff": {"en": "Cut-off", "ro": "Blocare"},
    "jv.region.bjt.reverse": {"en": "Reverse active", "ro": "Activ invers"},
    "jv.region.bjt.weak": {"en": "Weak conduction", "ro": "Conducție slabă"},
    "jv.region.bjt.eb_breakdown": {"en": "E-B breakdown", "ro": "Străpungere E-B"},
    "jv.region.bjt.avalanche": {"en": "C-B avalanche", "ro": "Avalanșă C-B"},
    "jv.region.mosfet.saturation": {"en": "Saturation", "ro": "Saturație"},
    "jv.region.mosfet.triode": {"en": "Triode (ohmic)", "ro": "Triodă (ohmic)"},
    "jv.region.mosfet.cutoff": {"en": "Cut-off", "ro": "Blocare"},
    "jv.region.mosfet.subthreshold": {"en": "Sub-threshold", "ro": "Sub prag"},
    "jv.region.mosfet.reverse_channel": {"en": "Reverse channel", "ro": "Canal invers"},
    "jv.region.mosfet.body_diode": {"en": "Body diode", "ro": "Dioda internă"},
    "jv.region.mosfet.avalanche": {"en": "Avalanche", "ro": "Avalanșă"},
    "jv.region.mosfet.oxide": {"en": "Oxide over-stress", "ro": "Suprasolicitare oxid"},
    "jv.region.jfet.ohmic": {"en": "Ohmic", "ro": "Ohmic"},
    "jv.region.jfet.saturation": {"en": "Saturation (pinch-off)", "ro": "Saturație (ștrangulare)"},
    "jv.region.jfet.cutoff": {"en": "Cut-off", "ro": "Blocare"},
    "jv.region.jfet.gate_forward": {"en": "Gate forward", "ro": "Grilă în direct"},
    "jv.region.jfet.reversed": {"en": "Reversed VDS", "ro": "VDS inversat"},
    "jv.region.jfet.breakdown": {"en": "Gate-drain breakdown", "ro": "Străpungere grilă-drenă"},

    # explanations
    "jv.explain.bjt.active": {
        "en": "E-B forward, C-B reverse. The emitter injects electrons into the thin base; almost all of them "
              "diffuse across it and are swept into the collector by the C-B field. The few holes the base "
              "supplies (IB) control the large IC ≈ β·IB — this is the amplifying region.",
        "ro": "E-B direct, C-B invers. Emitorul injectează electroni în baza subțire; aproape toți o traversează "
              "și sunt aspirați în colector de câmpul joncțiunii C-B. Puținele goluri furnizate de bază (IB) "
              "controlează curentul mare IC ≈ β·IB — aceasta este regiunea de amplificare."},
    "jv.explain.bjt.saturation": {
        "en": "Both junctions forward. The collector also injects carriers back into the base, so IC can no "
              "longer grow with IB (IC/IB < β) and VCE falls to about 0.1–0.2 V: a closed switch.",
        "ro": "Ambele joncțiuni în direct. Și colectorul injectează purtători înapoi în bază, astfel IC nu mai "
              "crește cu IB (IC/IB < β), iar VCE scade la circa 0,1–0,2 V: un comutator închis."},
    "jv.explain.bjt.cutoff": {
        "en": "Both junctions reverse (or unbiased). Depletion regions are wide, nothing is injected; only a tiny "
              "leakage flows: an open switch.",
        "ro": "Ambele joncțiuni în invers (sau nepolarizate). Regiunile golite sunt late, nu se injectează nimic; "
              "circulă doar un curent de scurgere infim: un comutator deschis."},
    "jv.explain.bjt.reverse": {
        "en": "E-B reverse, C-B forward: the roles of emitter and collector swap. The collector now injects and "
              "the emitter collects, but because the collector is lightly doped and large the gain βR is tiny "
              "(≈1–5). Current flows from emitter to collector.",
        "ro": "E-B invers, C-B direct: rolurile emitorului și colectorului se inversează. Colectorul injectează, "
              "iar emitorul colectează, dar colectorul fiind slab dopat și mare, câștigul βR este mic (≈1–5). "
              "Curentul circulă de la emitor spre colector."},
    "jv.explain.bjt.weak": {
        "en": "The E-B junction is below its ~0.6 V knee: the current is growing exponentially but is still "
              "small (µA or less). Every +60 mV multiplies it by 10.",
        "ro": "Joncțiunea E-B este sub cotul de ~0,6 V: curentul crește exponențial dar este încă mic (µA sau "
              "mai puțin). Fiecare +60 mV îl înmulțește cu 10."},
    "jv.explain.bjt.eb_breakdown": {
        "en": "The E-B junction is reverse biased beyond its ~7 V rating and breaks down (Zener effect): current "
              "flows backwards from emitter to base. Repeated E-B breakdown slowly degrades the transistor's gain.",
        "ro": "Joncțiunea E-B este polarizată invers peste ~7 V și se străpunge (efect Zener): curentul circulă "
              "invers, de la emitor spre bază. Străpungerea E-B repetată degradează treptat câștigul."},
    "jv.explain.bjt.avalanche": {
        "en": "The collector-base field is so strong that carriers crossing it knock new electron-hole pairs "
              "loose (avalanche multiplication). Extra electrons go to the collector, extra holes leave through "
              "the base — IB can even reverse. Beyond BVCEO the current runs away.",
        "ro": "Câmpul colector-bază este atât de puternic încât purtătorii care îl traversează eliberează noi "
              "perechi electron-gol (multiplicare în avalanșă). Electronii în plus merg la colector, golurile ies "
              "prin bază — IB se poate chiar inversa. Peste BVCEO curentul scapă de sub control."},
    "jv.explain.mosfet.saturation": {
        "en": "VGS > Vth forms the channel, but VDS > VGS − Vth pinches it off near the drain. Carriers are "
              "fired across the pinched zone by the field, so ID ≈ K(VGS − Vth)² hardly depends on VDS: a "
              "voltage-controlled current source (amplifier region).",
        "ro": "VGS > Vth formează canalul, dar VDS > VGS − Vth îl ștrangulează lângă drenă. Purtătorii sunt "
              "aruncați prin zona ștrangulată de câmp, deci ID ≈ K(VGS − Vth)² aproape nu depinde de VDS: o "
              "sursă de curent comandată în tensiune (regiune de amplificare)."},
    "jv.explain.mosfet.triode": {
        "en": "The channel is continuous from source to drain and acts like a resistor controlled by VGS: "
              "RDS(on) ≈ 1/(2K(VGS − Vth)). This is how a MOSFET is used as a closed switch.",
        "ro": "Canalul este continuu de la sursă la drenă și se comportă ca un rezistor comandat de VGS: "
              "RDS(on) ≈ 1/(2K(VGS − Vth)). Așa este folosit MOSFET-ul ca și comutator închis."},
    "jv.explain.mosfet.cutoff": {
        "en": "VGS is well below the threshold: no channel, the drain junction is reverse biased, practically no "
              "current. The gate never conducts DC — the oxide is an insulator.",
        "ro": "VGS este mult sub prag: nu există canal, joncțiunea drenei este polarizată invers, practic nu "
              "circulă curent. Grila nu conduce niciodată în DC — oxidul este izolator."},
    "jv.explain.mosfet.subthreshold": {
        "en": "Just below threshold a weak channel already exists and ID grows exponentially with VGS "
              "(≈ ×10 every 90 mV). Important for low-power circuits and for why 'off' is never exactly zero.",
        "ro": "Chiar sub prag există deja un canal slab, iar ID crește exponențial cu VGS (≈ ×10 la fiecare "
              "90 mV). Important în circuitele de mică putere și explică de ce 'blocat' nu înseamnă exact zero."},
    "jv.explain.mosfet.reverse_channel": {
        "en": "VDS is negative but the gate is on: the channel is symmetric, so the drain simply acts as the "
              "source and current flows from source to drain (third quadrant). Used in synchronous rectifiers.",
        "ro": "VDS este negativ, dar grila este deschisă: canalul este simetric, deci drena devine sursă și "
              "curentul circulă de la sursă la drenă (cadranul trei). Folosit în redresoarele sincrone."},
    "jv.explain.mosfet.body_diode": {
        "en": "The body is tied to the source, so the body-drain PN junction is a built-in diode. With VDS "
              "negative by more than ~0.6 V it conducts no matter what the gate does: electrons flow from the "
              "drain into the body and holes the other way.",
        "ro": "Substratul este legat la sursă, deci joncțiunea PN substrat-drenă este o diodă internă. Cu VDS "
              "negativ mai mult de ~0,6 V conduce indiferent de grilă: electronii trec din drenă în substrat, "
              "iar golurile invers."},
    "jv.explain.mosfet.avalanche": {
        "en": "VDS exceeds the drain breakdown voltage (40 V here): the drain-body junction avalanches and "
              "current flows even with the gate off. Power MOSFETs rated 'avalanche rugged' survive short pulses.",
        "ro": "VDS depășește tensiunea de străpungere a drenei (aici 40 V): joncțiunea drenă-substrat intră în "
              "avalanșă și curentul circulă chiar cu grila blocată. MOSFET-urile 'avalanche rugged' suportă "
              "impulsuri scurte."},
    "jv.explain.jfet.ohmic": {
        "en": "Small VDS: the channel is open along its whole length and behaves like a resistor whose value is "
              "set by VGS (wider depletion = higher resistance).",
        "ro": "VDS mic: canalul este deschis pe toată lungimea și se comportă ca un rezistor a cărui valoare e "
              "stabilită de VGS (regiune golită mai lată = rezistență mai mare)."},
    "jv.explain.jfet.saturation": {
        "en": "The gate-to-channel reverse voltage is largest at the drain end, so the depletion regions meet "
              "there (pinch-off). The current saturates at ID = IDSS·(1 − VGS/VP)²: a current source.",
        "ro": "Tensiunea inversă grilă-canal este maximă la capătul drenei, deci regiunile golite se ating acolo "
              "(ștrangulare). Curentul se saturează la ID = IDSS·(1 − VGS/VP)²: o sursă de curent."},
    "jv.explain.jfet.cutoff": {
        "en": "VGS is beyond the pinch-off voltage VP: the depletion regions close the channel along its whole "
              "length and the current stops.",
        "ro": "VGS depășește tensiunea de ștrangulare VP: regiunile golite închid canalul pe toată lungimea și "
              "curentul se oprește."},
    "jv.explain.jfet.gate_forward": {
        "en": "A gate junction is forward biased by more than ~0.5 V: it conducts like a diode, holes are "
              "injected from the gate into the channel and a real gate current flows. Normally avoided.",
        "ro": "O joncțiune a grilei este polarizată direct cu peste ~0,5 V: conduce ca o diodă, golurile sunt "
              "injectate din grilă în canal și circulă un curent de grilă real. În mod normal se evită."},
    "jv.explain.jfet.reversed": {
        "en": "VDS is negative: the JFET channel is symmetric, so source and drain swap roles and current flows "
              "the other way, now controlled by VGD.",
        "ro": "VDS este negativ: canalul JFET este simetric, deci sursa și drena își schimbă rolurile și curentul "
              "circulă invers, controlat acum de VGD."},
    "jv.explain.jfet.breakdown": {
        "en": "The gate-drain junction is reverse biased beyond its breakdown voltage (35 V here): avalanche "
              "current flows from drain to gate.",
        "ro": "Joncțiunea grilă-drenă este polarizată invers peste tensiunea de străpungere (aici 35 V): curentul "
              "de avalanșă circulă de la drenă spre grilă."},

    # ---------------- Basic circuits ----------------
    "tc.tab": {"en": "Basic Circuits", "ro": "Circuite de bază"},
    "tc.choose": {"en": "Circuit:", "ro": "Circuit:"},
    "tc.values": {"en": "Values", "ro": "Valori"},
    "tc.hint": {"en": "Everything updates as you type. Prefixes allowed (4.7k, 10m, 1M).",
                "ro": "Totul se actualizează pe măsură ce scrii. Prefixe permise (4.7k, 10m, 1M)."},
    "tc.state": {"en": "Operating state", "ro": "Starea de funcționare"},
    "tc.rb_hint": {"en": "For a hard, reliable switch (forced β = 10) use RB ≤ {rb}.",
                   "ro": "Pentru o comutare fermă și sigură (β forțat = 10) folosește RB ≤ {rb}."},
    "tc.compliance": {"en": "Current stays constant for any load up to RL ≈ {r} (compliance limit).",
                      "ro": "Curentul rămâne constant pentru orice sarcină până la RL ≈ {r} (limita de complianță)."},
    "tc.ptype_note": {
        "en": "P-type version: the circuit is drawn mirrored — emitter/source on the positive rail, load to "
              "ground — and the drive pulls the base/gate BELOW the supply. Voltages shown are real values.",
        "ro": "Versiunea de tip P: circuitul este desenat în oglindă — emitorul/sursa la plusul alimentării, "
              "sarcina la masă — iar comanda coboară baza/grila SUB alimentare. Tensiunile afișate sunt reale."},
    "tc.desc.bjt.switch": {
        "en": "A small base current turns on a large collector current. Choose RB so the transistor saturates "
              "(VCE ≈ 0.2 V) — then it wastes almost no power. Typical use: driving LEDs, relays, motors from "
              "a microcontroller pin.",
        "ro": "Un curent mic de bază comandă un curent mare de colector. Alege RB astfel încât tranzistorul să se "
              "satureze (VCE ≈ 0,2 V) — atunci disipă foarte puțină putere. Utilizare tipică: comanda LED-urilor, "
              "releelor, motoarelor de la un pin de microcontroler."},
    "tc.desc.bjt.ce": {
        "en": "The classic voltage amplifier. R1/R2 set the base voltage, RE stabilises the operating point "
              "against β changes, RC converts the collector current back into a voltage. Output is inverted.",
        "ro": "Amplificatorul de tensiune clasic. R1/R2 fixează tensiunea bazei, RE stabilizează punctul de "
              "funcționare față de variațiile lui β, RC transformă curentul de colector în tensiune. Ieșirea este "
              "inversată."},
    "tc.desc.bjt.ef": {
        "en": "Voltage gain ≈ 1 but high input and low output impedance: a buffer that lets a weak source drive "
              "a heavy load. The output follows the input, ~0.7 V lower.",
        "ro": "Câștig în tensiune ≈ 1, dar impedanță de intrare mare și de ieșire mică: un buffer care permite unei "
              "surse slabe să comande o sarcină mare. Ieșirea urmărește intrarea, cu ~0,7 V mai jos."},
    "tc.desc.bjt.ccs": {
        "en": "The Zener fixes the base voltage, so the emitter voltage (VZ − 0.7 V) and therefore the current "
              "through RE are fixed. The collector delivers that same current into any load within the limit.",
        "ro": "Dioda Zener fixează tensiunea bazei, deci tensiunea emitorului (VZ − 0,7 V) și curentul prin RE "
              "sunt fixe. Colectorul livrează același curent în orice sarcină, în limita de complianță."},
    "tc.desc.mosfet.switch": {
        "en": "The gate draws no DC current; once VGS is well above Vth the channel resistance RDS(on) is tiny "
              "and the load gets almost the full supply. Logic-level MOSFETs switch fully at 4.5 V.",
        "ro": "Grila nu consumă curent DC; când VGS este mult peste Vth, rezistența canalului RDS(on) este foarte "
              "mică și sarcina primește aproape toată alimentarea. MOSFET-urile 'logic-level' comută complet la 4,5 V."},
    "tc.desc.mosfet.cs": {
        "en": "MOSFET version of the common-emitter amplifier. The gate divider sets VG, RS stabilises ID, and "
              "the gain is −gm·RD (bypassed). Very high input impedance (set by R1 ∥ R2).",
        "ro": "Varianta MOSFET a amplificatorului cu emitor comun. Divizorul de grilă stabilește VG, RS "
              "stabilizează ID, iar câștigul este −gm·RD (cu decuplare). Impedanță de intrare foarte mare (R1 ∥ R2)."},
    "tc.desc.mosfet.sf": {
        "en": "Buffer: the source follows the gate minus VGS. Gain slightly below 1, output impedance ≈ 1/gm.",
        "ro": "Buffer: sursa urmărește grila minus VGS. Câștig puțin sub 1, impedanța de ieșire ≈ 1/gm."},
    "tc.desc.jfet.amp": {
        "en": "Self-bias: the current through RS lifts the source above the grounded gate, making VGS negative "
              "automatically — no divider needed. Gain −gm·RD with RS bypassed.",
        "ro": "Autopolarizare: curentul prin RS ridică sursa deasupra grilei legate la masă, făcând VGS negativ "
              "automat — nu e nevoie de divizor. Câștig −gm·RD cu RS decuplat."},
    "tc.desc.jfet.ccs": {
        "en": "Gate tied to the bottom of RS: the JFET sets its own current (IDSS with RS = 0). This two-terminal "
              "circuit is a 'current-regulator diode'.",
        "ro": "Grila legată la capătul de jos al lui RS: JFET-ul își stabilește singur curentul (IDSS cu RS = 0). "
              "Acest circuit cu două terminale este o 'diodă regulatoare de curent'."},
    "tc.desc.jfet.vcr": {
        "en": "At VGS = 0 the JFET is fully on (normally-on); making VGS negative raises its resistance until it "
              "switches off at VP. For small VDS it is a voltage-controlled resistor (used in AGC, analog switches).",
        "ro": "La VGS = 0 JFET-ul este complet deschis (normal deschis); făcând VGS negativ îi crește rezistența "
              "până se blochează la VP. Pentru VDS mic este un rezistor controlat în tensiune (AGC, comutatoare analogice)."},
    "tc.desc.jfet.sf": {
        "en": "JFET buffer: extremely high input impedance (RG), gain just under 1. Popular as a guitar/sensor "
              "input stage.",
        "ro": "Buffer cu JFET: impedanță de intrare extrem de mare (RG), câștig puțin sub 1. Popular ca etaj de "
              "intrare pentru chitară/senzori."},
    "tc.formula.bjt.switch": {"en": "IB = (Vin − VBE)/RB     IC = min(β·IB, (VCC − VCE(sat))/RC)",
                              "ro": "IB = (Vin − VBE)/RB     IC = min(β·IB, (VCC − VCE(sat))/RC)"},
    "tc.formula.bjt.ce": {"en": "VTh = VCC·R2/(R1+R2)   IB = (VTh − VBE)/(RTh + (β+1)RE)   Av = −(RC∥RL)/(re [+ RE])",
                          "ro": "VTh = VCC·R2/(R1+R2)   IB = (VTh − VBE)/(RTh + (β+1)RE)   Av = −(RC∥RL)/(re [+ RE])"},
    "tc.formula.bjt.ef": {"en": "VE = VB − VBE     Av = (RE∥RL)/(re + RE∥RL) ≈ 1     Zout ≈ re + RTh/β",
                          "ro": "VE = VB − VBE     Av = (RE∥RL)/(re + RE∥RL) ≈ 1     Zout ≈ re + RTh/β"},
    "tc.formula.bjt.ccs": {"en": "I = (VZ − VBE)/RE     RL(max) = (VCC − VCE(sat) − VE)/I",
                           "ro": "I = (VZ − VBE)/RE     RL(max) = (VCC − VCE(sat) − VE)/I"},
    "tc.formula.mosfet.switch": {"en": "ID = K(VGS−Vth)² (sat.)  or  K[2(VGS−Vth)VDS − VDS²] (triode),  VDS = VDD − ID·RL",
                                 "ro": "ID = K(VGS−Vth)² (sat.)  sau  K[2(VGS−Vth)VDS − VDS²] (triodă),  VDS = VDD − ID·RL"},
    "tc.formula.mosfet.cs": {"en": "VG = VDD·R2/(R1+R2)   VG = VGS + K(VGS−Vth)²·RS   gm = 2K(VGS−Vth)   Av = −gm(RD∥RL)",
                             "ro": "VG = VDD·R2/(R1+R2)   VG = VGS + K(VGS−Vth)²·RS   gm = 2K(VGS−Vth)   Av = −gm(RD∥RL)"},
    "tc.formula.mosfet.sf": {"en": "Av = gm·RS'/(1 + gm·RS')     Zout = RS ∥ 1/gm",
                             "ro": "Av = gm·RS'/(1 + gm·RS')     Zout = RS ∥ 1/gm"},
    "tc.formula.jfet.amp": {"en": "ID = IDSS(1 − VGS/VP)²,  VGS = −ID·RS   gm = 2·IDSS/|VP|·(1 − VGS/VP)   Av = −gm(RD∥RL)",
                            "ro": "ID = IDSS(1 − VGS/VP)²,  VGS = −ID·RS   gm = 2·IDSS/|VP|·(1 − VGS/VP)   Av = −gm(RD∥RL)"},
    "tc.formula.jfet.ccs": {"en": "ID = IDSS(1 − VGS/VP)² with VGS = −ID·RS     RL(max) = (VDD − |VP|)/ID",
                            "ro": "ID = IDSS(1 − VGS/VP)² cu VGS = −ID·RS     RL(max) = (VDD − |VP|)/ID"},
    "tc.formula.jfet.vcr": {"en": "RDS ≈ VP² / (2·IDSS·(VGS − VP))  for small VDS",
                            "ro": "RDS ≈ VP² / (2·IDSS·(VGS − VP))  pentru VDS mic"},
    "tc.formula.jfet.sf": {"en": "VS = ID·RS = −VGS     Av = gm·RS'/(1 + gm·RS')",
                           "ro": "VS = ID·RS = −VGS     Av = gm·RS'/(1 + gm·RS')"},
}
