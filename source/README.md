# ⚡ The Electronist's Guide (v6.4)

An interactive, visual desktop app for learning about and calculating values
for common electronic components — built with Python's `tkinter` for the UI
and `matplotlib` for live charts/simulations. Available in **English and
Romanian**.

## Features

Each component has its own tab with a live-updating visual (drawn on a
canvas) plus a "Learn" panel explaining what it is, how it works, and its
key DC and AC formulas.

- **Resistors** — 4/5/6-band color code ↔ value calculator, Series/Parallel/Mixed
  combination calculators, Chart/Simulate (V & I vs time), DC/AC formulas.
- **Capacitors** — Ceramic code calculator, electrolytic calculator (with
  polarity warning), AC reactance, Series/Parallel/Mixed, Chart/Simulate
  (charge/discharge transient or 90°-phase-lead AC waveform), DC/AC formulas.
- **Inductors** — Color-code calculator (with an honest caveat that not all
  inductors use color bands), reactance, magnetic coupling (k), transformer
  turns-ratio, Series/Parallel/Mixed, Chart/Simulate (current-rise transient
  or 90°-phase-lag AC waveform), DC/AC formulas.
- **Diodes / LEDs** — LED series-resistor calculator, forward-voltage
  reference table, Chart/Simulate (DC I-V curve or AC half-wave rectifier).
- **Transistors** — three families with full family/type selectors:
  - **BJT** (NPN/PNP) — junction visualizer, Q-point (PSF) bias calculator,
    Chart/Simulate (switch/amplifier)
  - **MOSFET** (N-channel/P-channel) — junction visualizer, Q-point (PSF)
    bias calculator
  - **JFET** (N-channel/P-channel) — junction visualizer, Q-point (PSF)
    bias calculator

### Junction Visualizer (new)

For every transistor family and polarity, an interactive cross-section shows
what's happening *inside* the device as you drag bias-voltage sliders:
- **BJT**: the depletion regions at both junctions visibly shrink and grow
  as Vbe/Vce change, with carrier-flow arrows appearing in the active
  region and clear cutoff/saturation/active state labels.
- **MOSFET**: raising Vgs above Vth forms the conducting channel; raising
  Vds shows it visibly pinch off near the drain once saturation is reached.
- **JFET**: making Vgs more reverse-biased widens the gate depletion
  regions until they meet in the middle at Vgs = Vp, fully pinching off
  the channel.

These are deliberately illustrative (not device-physics-accurate), designed
to build intuition about *why* a transistor behaves the way it does.

### Q-Point / PSF Bias Calculator (new)

"Punctul static de funcționare" — for each family, pick **Analyze** (enter
actual resistor values, get the resulting Q-point) or **Design** (enter a
target operating point, get the suggested resistor values), with a DC load
line chart showing the Q-point plotted against the load line:
- **BJT**: voltage-divider bias (R1, R2, Rc, Re) — the standard
  temperature-stable configuration.
- **MOSFET**: voltage-divider gate bias (R1, R2, Rd, Rs) for enhancement-mode
  devices.
- **JFET**: self-bias (Rd, Rs only, using Shockley's equation).

Design mode uses standard textbook design rules (e.g. Ve ≈ 0.1·Vcc, a
"stiff" divider current ≈ 10·Ib) and was verified to round-trip exactly:
feeding its own suggested components back into Analyze mode reproduces the
requested target Q-point.
- **Op-Amps** — Inverting/non-inverting gain calculators with circuit sketch.
- **Batteries** — Series/parallel cell calculator (voltage, capacity, runtime).
- **Voltage Divider / Filter** — pick any two components (R, L, or C), one in
  series with the signal and one shunting to ground, and simulate Vin/Vout in
  DC or AC. Two resistors gives a classic voltage divider; mixing in a
  capacitor or inductor gives a basic RC/RL low-pass or high-pass filter.
- **AC/DC Basics** — Interactive Ohm's Law triangle solver, RMS ↔ peak, core
  AC/DC theory.

### Series / Parallel / Mixed combination tools (Resistors, Capacitors, Inductors)

Each of these three components' "Series / Parallel" section now has two modes:
- **Quick List** — type any list of values (e.g. `220, 4.7k, 10k`) and get
  both the pure-series and pure-parallel totals at once.
- **Mixed Builder** — add components one at a time, choosing at each step
  whether the new one combines in series or in parallel with everything
  built so far. Shows a running step log and a diagram of the current merge,
  so you can build arbitrary mixed series+parallel networks.

### Voltage Divider / Filter simulator

A dedicated tab lets you build a simple 2-element network — one series
element, one shunt element, either can be a resistor, capacitor, or
inductor — and simulate it in DC or AC:
- **AC mode** uses proper complex impedance (Z_R = R, Z_L = jωL, Z_C = -j/ωC)
  so it correctly handles any combination, showing the output/input ratio
  and phase shift.
- **DC mode** shows the classic single-time-constant transient for the four
  standard RC/RL cases, or the steady-state value for other combinations
  (an honest simplification — a full transient for reactive-on-both-sides
  networks would need 2nd-order analysis).

## What's new in v6.4

- **Learn comes first** - on every page the Learn sub-tab is now the first tab and
  the one you see when you open that page, so you know what the tools that follow
  are about.
- **Calculator (solve any)** - the "how it changes" chart has its own full-height
  column on the right (it was a flat strip under the result).
- **Series / Parallel** - every part you type is drawn (the parallel diagram grows
  with the number of parts and scales to fit); the page scrolls instead of
  squashing on short windows.
- **Resistor colour code** - with 5 or 6 bands the selectors wrap onto a second
  row instead of running off the page.
- **Capacitor colour bands** moved from "SMD & Codes" to the through-hole page,
  now called "THT codes (ceramic / film)".
- **Inductor colour code** shows the coil drawing with colour dots again.
- **Logic gates** - the switch-and-lamp picture follows the inputs: switches
  open/close, the lamp lights, and you can click a switch to flip that input.

## What's new in v6.3 (better use of the screen)

Every page was reviewed at full-HD and at 1366×768. Instead of padding the
empty areas, the layouts were rearranged so the controls sit in a compact
left column and drawings/charts scale into the space on the right (never
blown up past a sensible size, never shrunk below readable; a scrollbar
appears on small windows).

- **Resistor / Inductor colour code** - large part drawing + a full colour-code
  chart that highlights the bands in use.
- **Ceramic capacitor code** - big part, clickable common codes (100 … 476) and
  tolerance letters, step-by-step reading and a "how to read it" guide.
- **SMD & Codes** - decode (large chip drawing) on the left, value → marking and
  the reference tables on the right.
- **Calculator (solve any)** - all formulas listed on the left (one click to
  switch), large equation and result, plus a chart of how the answer changes
  with any one input (÷10 … ×10 around your value).
- **Series / Parallel** - series and parallel shown side by side, each with its
  diagram, total and how the voltage / current / charge is shared.
- **Transformer** - rebuilt: load, secondary / primary current, power, reflected
  impedance, a drawing whose coils follow the turns ratio, and waveforms.
- **LED resistor** - next E12 value up and the real current it gives, power and
  rating, efficiency, colour presets and a current-vs-resistor chart.
- **Battery pack** - SxP packs with chemistry presets (Li-ion, LiFePO4, NiMH,
  alkaline, lead-acid), runtime, C-rate, sag, heat and a discharge curve.
- **Logic gates** - gate buttons, large symbol (click the inputs), a big
  clickable truth table, IEC symbol and switch-and-lamp analogy, full-width
  timing diagram.
- **Ohm's law** - live circuit + I-V line that follow the sliders, RMS/peak
  sine drawing. **Kirchhoff** - drawn KVL loop with the drops and a KCL node
  with arrows sized by current.
- **Unit converter** - list and table stretch to the page; **dB levels** get a
  clickable "where is this level" dBm scale; **number systems** get large bits,
  hex digit per nibble, place-value sum and a hex-digit strip; **ADC/DAC** gets
  the quantisation staircase and error plot.
- **LED array** drawing scales with the page.
- **Learn pages** of components get quick-reference tables under the symbols
  (E-series and power ratings, capacitor types, core materials, BJT/MOSFET/JFET,
  common op-amps, battery chemistries).

## What's new in v6.2.1 (polish)

- **Schematics no longer stretch** on wide windows: the voltage divider, the
  transistor junction visualizer and the transistor basic-circuit schematics keep
  their proportions and are centred instead of being pulled across the screen.
- **Drop-down lists close when you switch apps** (Alt+Tab, minimise): an open
  combobox list no longer stays floating on top of other windows.
- **Picture galleries on the Learn pages** that had no symbols: Boolean Logic
  (every gate with symbol, expression and truth table), AC Circuits (R/L/C phase
  relations with waveforms and phasors, impedance and power triangles,
  resonance), Modulation (what AM, DSB, FM, PM, ASK, FSK, BPSK and QPSK look
  like, AM spectrum) and RF (two-port S-parameters, reflection, standing waves,
  Smith-chart landmarks, λ/4 transformer, stubs).

## What's new in v6.2 (more room on screen)

- **Learn is now its own sub-tab everywhere.** The theory/formula panel and the
  schematic-symbol gallery no longer sit in a permanent right-hand column: every
  page (Resistors, Capacitors, Inductors, Transistors, Op-Amps, Batteries,
  AC/DC Basics, Kirchhoff, Boolean Logic, AC Circuits, Modulation, RF) has a
  **Learn** tab, exactly like Diodes / LEDs. Calculators, charts and simulators
  now use the full window width. Learn pages show the theory at a comfortable
  reading width with the symbols beside it; AC/DC Basics shows Ohm's law and
  Kirchhoff's laws side by side. Ohm's law + live simulator, and KVL + KCL, are
  now laid out side by side too.
- **Virtual VNA rebuilt for readability.** Each channel keeps its controls in a
  compact block and hands the rest of the space to the plot. A **Layout** switch
  offers *A | B side by side* (default), *A over B*, *Only A* or *Only B* (one
  channel over the whole page). Marker read-outs are shown in a strip above the
  plot (never on top of the trace), markers sit in a compact 2×2 grid, the mouse
  wheel zooms the frequency axis around the cursor, and slim **Full view / Zoom
  box / Pan / Save image** buttons replace the bulky toolbar. A zoom is kept while
  you place markers; plot margins re-fit on every resize so labels never clip.
  Group delay is now plotted in ns (matching its axis label).

## What's new in v6.1 (circuit builders)

- **Logic Circuit Builder** rebuilt: drag parts from the list onto the grid (or click, then click the
  grid - the tool returns to Select by itself, Shift keeps it); wire by pressing on any pin dot and
  dragging to another pin (compatible pins light up, drops snap, works in either direction); click a
  switch to flip it; drag empty space to pan; right-click menu (toggle, rename, duplicate, disconnect,
  delete); Undo/Redo, Duplicate, Fit; unconnected inputs shown as red rings and listed; live truth
  table (click a row to set the switches) and the minimized expression of every output; 8 ready-made
  examples; save/open circuits as .json. The builder now uses the full page width.
- **Multiport RF Simulator builder** rebuilt: one-click placement of parts (R rotates), drag-and-drop
  from the list, every connection point drawn (red ring = not connected, dot = connected, big dot =
  junction), wiring by dragging from any point with neat L-shaped wires that avoid parts, automatic
  T-junctions when a wire or part lands on a wire, wires follow a part when it is moved, sliders for
  every value, auto-simulate on every change with a live S-parameter plot next to the schematic,
  plain-language circuit check (click an item to select the part), Undo/Redo, Duplicate, Fit, node
  names, 8 examples (π attenuator, LC low-pass, RLC band-pass, L-match, λ/4 transformer, open-stub
  notch, 3-port splitter, through line) that also set a suitable sweep.

## What's new in v6.0

- **Resistor colour bands** are drawn with one consistent pitch: value bands evenly spaced, a clear
  gap, then tolerance (and temp.co) — identical spacing for 4, 5 and 6-band parts.
- **SMD & Codes** sub-tab on Resistors, Capacitors and Inductors: decode any marking (3/4-digit,
  EIA-96, R/m notation, 0 Ω jumpers; capacitor pF codes with tolerance & voltage codes, EIA-198
  letter codes, tantalum voltage letters, 4n7-style; inductor µH/R/N codes), with every possible
  reading and its working, the chip drawn to scale in the chosen package, value → all markings,
  nearest E-series values, package/power tables and the capacitor colour-band code.
- **Diodes**: Circuit Lab (rectifier ± reservoir C, clippers, zener clipper, clampers, voltage
  doubler, AM envelope detector, freewheeling diode) simulated by a small built-in SPICE-like engine
  (`minispice.py`) with a time cursor that lights up the conducting diode, PIV and peak current;
  I-V Explorer (Si/Ge/Schottky/LEDs/zener, temperature, log scale, load line & Q point);
  Zener Regulator designer (worst-case R range, powers, line/load regulation plots);
  LED Array planner (series/parallel strings, resistor, efficiency, Vf-spread sensitivity).
- **Op-Amps**: Circuit Lab with 15 configurations — inverting, non-inverting, buffer, summing,
  differential (with resistor mismatch/CMRR), integrator, differentiator, comparator, inverting and
  non-inverting Schmitt triggers, peak detector, precision rectifier, relaxation oscillator,
  square + triangle generator and Wien-bridge sine oscillator; ideal or real op-amp models
  (GBW, slew rate, output headroom), waveforms + X-Y transfer plot and key numbers.
- **Filters** rebuilt as a Filter Lab: 14 filters (RC/RL, 2× RC, twin-T, RLC band-pass/stop, LC
  2nd-order, active 1st-order, Sallen-Key LP/HP, MFB band-pass) with sliders, "design for f0/Q/gain",
  Bode plot, response to sine/square/triangle/sweep, step response, poles & zeros and a harmonics
  view. The old L-section builder is kept as a second sub-tab.
- **AC Circuits & Phasors**: Phasor Lab (8 series/parallel/mixed circuits) with rotating phasors
  linked to the waveforms, tip-to-tail sums, impedance & power triangles and a frequency sweep with
  resonance/Q/bandwidth; new Power & PF-correction page.
- **Modulation** redesigned: one-screen Modulation Lab with AM, DSB-SC, SSB, FM, PM, ASK, FSK, BPSK
  and QPSK; sliders; Overview / Spectrum (lin or dB) / Demodulate / I-Q views.

## What's new in v5.3 (speed)

- Pages are built the first time you open them (start-up ~20× faster, far fewer widgets alive).
- Changing language or IEC/ANSI keeps you on the same page and only rebuilds that page.
- Animations (Junction Visualizer, coupling, bridge, phasors) stop working while their page is
  hidden and never request frames faster than the PC can draw them.
- Charts render once per change: redraws wait until resizing/scrolling has settled and are
  skipped while a chart is hidden.
- One mouse-wheel handler scrolls the page under the pointer (nested pages no longer fight).
- Dark mode removed.

## What's new in v5.2

- **Resistors**: the stray circle over the last colour band is gone; the useless DC/AC
  chart sub-tab was removed.
- **Capacitors / Inductors — AC chart**: four linked plots — v(t) and i(t) with the phase
  shift marked, instantaneous power p(t) (energy in / energy returned), phasor diagram and
  reactance vs frequency — plus optional series resistance, |Z|, φ, P, Q and peak energy.
- **Inductor coupling**: animated cross-section of two coils — field lines from coil 1,
  the part that links coil 2 (set by k), Lenz's-law opposing field when loaded, drag coil 2
  or add an iron core; live scope of i1, v2 = M·di1/dt and i2.
- **4-diode bridge**: redesigned page with the conducting pair highlighted; the load
  resistor only appears once the smoothing capacitor is added (without it RL has no effect).
- **Transistors — Chart / Simulate** is now a graphical load-line analysis for BJT, MOSFET
  and JFET: input → current transfer curve, output curves with load line and Q point, and
  the output waveform with clipping shown in red. Presets: linear amplifier, overdriven,
  switch, centre Q.
- **Junction Visualizer (FETs)**: new draggable VGS–VDS region map (like the BJT map) next
  to the ID–VDS curve.
- **JFET physics**: carriers speed up through the pinched neck (current continuity) and
  fan out gradually into the drain instead of jumping to full width; same continuity rule
  in the MOSFET channel.
- **Op-amp non-inverting**: Rin no longer overlaps the + input wire.
- **RF Band Explorer** (replaces the band table): frequency lookup (ITU band, IEEE/NATO
  letter, λ, antenna lengths, path loss, matching allocations), clickable log-scale
  spectrum map, 35+ allocations with per-region ranges, power limits, access rules,
  channel plans with centre-frequency formulas and scaled channel drawings, plus ITU /
  IEEE / NATO reference tables.
- **Boolean solver**: gate diagrams of the entered expression and of the minimized SOP or
  POS (with gate/input counts), an on-screen keypad and easier keyboard syntax
  (`AB` = A·B, `&&`, `||`, `!`, `.`, words).
- **Unit converter** reworked: one-value → all-units converter in 18 categories (incl.
  SI-prefix electrical values, temperature, frequency/period/wavelength, AWG), linked
  dB / level fields (W, dBm, dBW, Vrms, Vpk, Vpp, dBV, dBu, dBµV at any impedance),
  number systems with a clickable bit grid, and the ADC/DAC calculator.

## What's new in v5.1 (Transistors)

- **Junction Visualizer rebuilt** (BJT, MOSFET, JFET, N and P types): a
  physics-based model (Ebers-Moll BJT with E-B Zener and C-B avalanche
  breakdown; MOSFET with sub-threshold, triode/saturation, reverse channel,
  body diode, avalanche and oxide-stress warning; JFET with gate conduction,
  reversed channel and gate-drain breakdown) drives a cross-section where
  every current path has its own stream of electrons/holes, depletion
  regions show their fixed ions, the MOSFET channel tapers and pinches off,
  and the JFET depletion regions squeeze the channel toward the drain.
  Wide-range sliders (with typed values), one-click presets for every
  operating region, a draggable VBE/VBC bias map (BJT) or live ID-VDS curve
  (FETs), and the real symbol with every terminal current.
- **Symbols fixed**: new MOSFET/JFET/BJT symbols (correct arrows, broken vs
  solid channel, mirrored versions for P-type circuits) used everywhere.
- **Basic Circuits** sub-tab: switch, common-emitter / common-source /
  self-biased amplifiers, followers, constant-current sources and the JFET
  voltage-controlled resistor, with live schematic values, Q-point/load line,
  transfer curves and input/output waveforms (with clipping detection).
  P-type versions are drawn mirrored with real node voltages.

## What's new in v5.0

- **PCB & Production tab removed** completely (tab, code and strings).
- **Correct schematic symbols everywhere**: every component tab (resistors,
  capacitors, inductors, diodes, transistors, op-amps, batteries) has a
  "Schematic symbols" card, and all circuit drawings (series/parallel,
  Mixed Builder, voltage divider, filters, op-amp, BJT/MOSFET/JFET bias
  circuits, batteries, rectifier load) now use real symbols instead of
  labelled boxes. Resistors can be drawn IEC (rectangle, default) or ANSI
  (zig-zag) with the switch in the top bar.
- **Mixed Builder shows the complete schematic** of the whole network (every
  component with its name and value, the newest one highlighted), the
  equivalent expression (e.g. `Req = ((R1 + R2) ∥ R3) + R4`), and — for an
  applied voltage (R, C) or current (L) — the voltage, current/charge and
  power/energy of every component.
- **Voltage Divider rebuilt**: schematic with R1, R2, R3, R4 and RL clearly
  named, node voltages and branch currents drawn on it, a solve-for-anything
  table (Vin, any resistor, or Vout can be the unknown), optional 2nd stage and
  load, per-resistor V/I/P table and an E6/E12/E24/E96 pair finder.
- **AC Quantities & Ripple** (Signals > AC Circuits): from any one of
  amplitude / peak-to-peak / RMS / average and any one of f / T / ω, get all
  the others, plus instantaneous value v(t), the moments a value is reached,
  DC component, form & crest factor, ripple factor, wavelength — for sine,
  square, triangle, sawtooth, half- and full-wave rectified signals — and a
  rectifier + filter-capacitor ripple calculator (or ripple from measured
  Vmax/Vmin).
- **Calculator (solve any)** sub-tab in Resistors, Capacitors and Inductors:
  ~40 formulas (Ohm's law, power, resistivity, temperature coefficient, RC/RL
  time constants, charge/discharge at time t, reactance, energy, plate
  capacitor, solenoid inductance, resonance, transformer, …); tick the
  quantity you want and it is solved for, whichever it is.
- **DC charts**: the voltage and current axes now share the same zero line,
  with readable units (ms, mA, …), a legend, τ gridlines and shaded
  charge/discharge phases. The Resistors tab has its chart back as well.

## Language

Click the **EN** / **RO** buttons in the top-right corner of the header to
switch the entire interface between English and Romanian at any time.
Switching language rebuilds the tabs, so any values you've typed in will
reset to their defaults.

## Full-screen friendly

The app opens maximized to fill your screen on startup. The theory panels
reflow their text to use the available width, and the whole layout scales
with the window (there's also a sensible minimum size of 1000×700 if you
resize down).

## Running the app

Requires Python 3.8+ with `tkinter` (bundled with most Python installs; on
Debian/Ubuntu: `sudo apt-get install python3-tk`), plus `matplotlib` and
`numpy` for the Chart / Simulate tabs:

```bash
pip install -r requirements.txt
python main.py
```

## Project structure

```
electronist_guide/
├── main.py            # App entry point, window/theme setup, language toggle, tab notebook
├── i18n.py             # Translation engine + full EN/RO string table
├── data.py             # Color code tables, capacitor codes, i18n-driven theory content
├── drawing.py           # Canvas drawing helpers (components + series/parallel + divider diagrams)
├── widgets.py           # Shared UI helpers (Theory panel, value parsing, series/parallel math)
├── charts.py            # Matplotlib chart embedding + DC/AC signal simulation functions
├── combos.py            # Step-by-step Mixed Builder tool (draws the complete network schematic)
├── symbols.py           # Standard schematic symbols (IEC / ANSI) + per-component symbol gallery
├── solver.py            # "Solve for anything" formula calculator + R / C / L formula libraries
├── i18n_extra.py        # EN/RO strings for the v5.0 features
├── bias.py              # BJT/MOSFET/JFET Q-point (PSF) analyze & design formulas
├── i18n_transistor.py   # EN/RO strings for v5.1 (transistors)
├── i18n_v52.py          # EN/RO strings for v5.2
├── transistor_models.py # BJT / MOSFET / JFET device models
├── transistor_viz.py    # Junction Visualizer (animated carriers, region maps)
├── transistor_circuits.py # Transistors > Basic Circuits
├── transistor_graph.py  # Transistors > Chart / Simulate (graphical load-line analysis)
├── logic/expr_diagram.py  # gate diagrams for the Boolean solver
├── rf/band_data.py      # RF Band Explorer data; rf/band_table.py = the explorer UI
├── requirements.txt
└── tabs/
    ├── resistor.py     # Color Code | Calculator | Series/Parallel | Voltage Divider
    ├── capacitor.py    # Ceramic | Calculator | Series/Parallel | Chart
    ├── inductor.py     # Color Code | Calculator | Coupling | Transformer | Series/Parallel | Chart
    ├── coupling_viz.py # Inductors > Coupling (animated magnetic coupling)
    ├── unit_converter.py # Converter | dB & levels | Number systems | ADC/DAC
    ├── resistive_divider.py  # Resistors > Voltage Divider (R1..R4, RL, solve-for-anything, E-series)
    ├── ac_waveform.py  # AC Circuits > AC Quantities & Ripple
    ├── diode.py        # LED Resistor Calc | Chart | 4-Diode Bridge
    ├── transistor.py   # Junction Visualizer | Basic Circuits | Q-Point | Chart (load line)
    ├── opamp.py
    ├── battery.py
    ├── divider.py      # Voltage Divider / Filter simulator (new top-level tab)
    └── basics.py
```

## How the language system works

`i18n.py` holds a simple `t(key)` lookup function and a `set_language()`
call. Switching language triggers a full rebuild of the tab notebook (rather
than trying to update hundreds of live widgets in place), so every label is
guaranteed to be freshly resolved in the new language. Component/color names
used internally as dictionary keys (e.g. resistor band colors like "Black",
"Brown") stay in English since they're also used as lookup keys throughout
the calculation logic — this is standard practice, and reference tables in
many countries (including Romania) use the English color names for resistor
codes too.

## Notes

- Value fields accept engineering shorthand like `4.7k`, `220n`, `10u`, `1M`.
- Series/Parallel fields accept a comma or space separated list of any length,
  e.g. `220, 4.7k, 10k`.
- Chart tabs let you switch between DC and AC modes; parameter fields update
  to match. Every plot has a zoom/pan toolbar (from matplotlib).
- All formulas and simulations use idealized textbook models for educational
  clarity; real components have secondary effects (parasitic resistance/
  capacitance, temperature drift, saturation, etc.) not modeled here.

## Fixes in this update

- Fixed several disconnected/misaligned wires in the component drawings: the
  ceramic capacitor had a stray diagonal line that didn't connect to
  anything, the electrolytic capacitor's leads were offset instead of
  running straight through, the transformer's coil leads stopped short of
  the coil by ~28px, and the op-amp's feedback line started from a floating
  point inside the triangle instead of the actual inverting-input node.
- Softened the inductor color-code wording to be upfront that this system
  is common on small molded/axial inductors and RF chokes, not universal —
  many inductors print their value directly or use SMD codes instead.
- Fixed an infinite `<Configure>` event feedback loop in the theory panel's
  responsive text reflow, which could freeze the app after switching
  languages a couple of times.

## Fixes & additions in this round

- **Battery bank diagram**: rebuilt with uniform cells and proper bus bars
  for parallel mode — the external wires now actually reach the + and -
  rails instead of entering at a height that didn't touch them.
- **Op-amp schematic**: added the missing Rin box on the input line, and
  rerouted the feedback loop so it no longer overlaps the triangle's edge.
- **Capacitor & Inductor DC charts**: now show a full charge → discharge
  cycle. After 5τ, a dotted marker shows where the source is removed, and
  the component discharges back through the same resistor (with current/
  voltage correctly reversing sign).
- **Diode/LED tab**: added two new rectifier sub-tabs —
  - *2-Diode Rectifier* (center-tap full-wave, single diode drop)
  - *4-Diode Bridge* (full bridge, two diode drops) — with an "Add
    Smoothing Capacitor" button that adds a filter cap and shows the
    resulting ripple waveform using an idealized peak-detector model.
- **Voltage Divider / Filter tab**: added an optional **Stage 2** (checkbox)
  that cascades a second series+shunt L-section after the first, using the
  proper loaded 4-element ladder transfer function. This unlocks real
  2nd-order responses — e.g. high-pass into low-pass gives a band-pass
  filter — verified against expected behavior (attenuates at both low and
  high frequencies, passes more in between).
- Fixed the divider/filter formula text overflowing its box — labels now
  wrap properly instead of being clipped off-screen.

## Fixes & additions in this round

- **BJT junction visualizer**: fixed overlapping status-text labels, and
  fixed the operating-region logic so it's actually tied to both junctions
  (Vbe *and* Vcb) instead of a Vce-only threshold — cutoff, active, and
  saturation are all now reachable and visually distinct as you drag the
  sliders.
- **MOSFET junction visualizer**: completely redrawn. The channel used to
  render as a 6px sliver that just got shorter (looking like a "tentacle"),
  with no real pinch-off shape. It's now a full-height, blocky channel with
  a proper wedge-shaped depletion region that visibly grows in from the
  drain side as Vds increases into saturation.
- **JFET junction visualizer**: fixed a sign-logic bug that made the pinch
  fraction always evaluate to zero for N-channel devices — moving the Vgs
  slider now visibly narrows (and at Vgs=Vp, fully closes) the channel.
- **Schematic symbols added** for every family/polarity (not just BJT):
  MOSFET and JFET now have standard circuit symbols shown alongside the
  cross-section in the Junction Visualizer.
- **Bias circuit schematics**: the Q-Point/PSF Bias Calculator for all three
  families now shows a small labeled circuit diagram (updating live with
  whatever values you type or whatever the Design mode suggests) above the
  load-line chart, so it's clear exactly where R1/R2/Rc/Re (or Rd/Rs, or
  the gate divider) sit in the actual bias network.

## Fixes in this round (critical)

- **Found and fixed a real hang**: switching the transistor Family selector
  from MOSFET straight to JFET would freeze the app. Root cause was the
  same class of bug as an earlier `<Configure>`-event feedback loop in the
  theory panel's responsive text-wrapping, resurfacing in a new scenario.
  Removed that dynamic-wraplength mechanism entirely (in favor of a fixed
  wraplength) rather than patching it again — it's a recurring source of
  fragile feedback loops and isn't worth the risk for a cosmetic feature.
  Verified with 12 rapid consecutive family switches in both directions.
- **Bias circuit diagram was badly distorted**: the circuit canvas had been
  sized to 440×210, but the diagram's internal layout used fixed pixel
  offsets designed for 460×340 — at the smaller size this produced
  inverted (negative-height) resistor boxes and cramped, overlapping
  elements. Fixed by matching the canvas to the diagram's natural
  proportions instead of squeezing it.
- **Junction visualizer clipping**: the cross-section canvas was being
  drawn assuming its default 460×280 design size while the actual widget
  was 440×300, clipping content on the right edge. Now passes explicit
  matching dimensions.
- **Symbol captions overflowing their canvas** (e.g. "NPN Bipolar Junction
  Transisto[r]" getting cut off) — captions now auto-wrap within the
  available width instead of overflowing.
- **Schematic symbols drawn partially off-canvas**: the BJT/MOSFET/JFET
  symbols were sized for a 460px-wide canvas but shown in a 160px-wide
  inset, pushing the base/gate leads and labels to negative (invisible)
  coordinates. All three symbols are now scale-aware and fit correctly
  regardless of canvas size.
- **Base lead color inconsistency**: the BJT symbol's collector and emitter
  leads were drawn in black, but the base lead used the generic (lighter
  gray) wire color — fixed so all three leads are consistently black,
  matching standard schematic symbol convention. Same fix applied to the
  MOSFET and JFET symbols' gate leads.

## Fixes in this round

- **Diode bridge wires were invisible**: the `_diode_on_line` helper drew the
  diode symbol itself but never the wire leads on either side of it — fixed
  to draw the full connection.
- **4-diode bridge schematic was mostly off-canvas**: its coordinates were
  hardcoded for a 460×260 canvas but the diode tab renders it at 280×210,
  clipping most of the circuit (including the capacitor) out of view. Both
  bridge schematics now scale proportionally to whatever canvas size is
  requested.
- **Smoothing capacitor comparison**: the 4-diode bridge chart now also
  plots the pre-capacitor (unsmoothed) signal as a dotted gray line, so the
  ripple-smoothing effect is easy to see against the "before" waveform.
- **Divider/Filter Stage 2 layout**: rebuilt as two side-by-side cards
  (Stage 1 | Stage 2) instead of Stage 2 appearing below the fold with no
  way to scroll down to it.
- **Resistor 5/6-band spacing**: the last two bands were only ~15px apart
  (nearly overlapping) due to a positioning bug; all bands are now evenly
  spaced regardless of band count.
- **Series combination diagram**: fixed a bug where the final wire after
  the last component started one full gap-width too far right, leaving it
  visibly disconnected from the last box.


