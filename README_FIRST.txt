The Electronist's Guide v5.3 — Windows Build
==============================================

HOW TO RUN
----------
Double-click "ElectronistGuide.exe" in this folder. No installer, no
Python required — everything is bundled in the "_internal" folder next
to the .exe (keep the .exe in this folder).

Optional: run "Create_Desktop_Shortcut.bat" once to add a Desktop
shortcut.

WHAT'S NEW IN v5.3 (speed)
--------------------------
- Opens much faster: each page is built the first time you open it.
- Switching language or IEC/ANSI keeps you on the same page.
- Hidden animations and charts no longer use the CPU; charts redraw
  once, after scrolling/resizing has settled.
- Mouse wheel always scrolls the page under the pointer.
- Dark mode removed.

WHAT'S NEW IN v5.2
------------------
- Resistors: stray circle on the last band fixed; chart tab removed.
- Capacitors / Inductors AC chart: waveforms with phase shift, power
  p(t) (energy in / returned), phasor diagram, reactance vs frequency,
  optional series R.
- Inductor coupling: animated magnetic field between two coils (drag
  coil 2, iron core, load + Lenz's law, live scope).
- 4-diode bridge: new page; load resistor appears only with the
  smoothing capacitor.
- Transistors > Chart / Simulate: graphical load-line analysis (transfer
  curve, load line + Q point, output waveform with clipping) for BJT,
  MOSFET and JFET; FET Junction Visualizer gets a draggable region map;
  JFET/MOSFET carriers now obey current continuity at the pinch-off.
- Op-amp non-inverting: Rin no longer crosses the + input.
- RF Band Explorer: frequency lookup, spectrum map, 35+ allocations with
  per-region ranges, power, access rules and channel plans.
- Boolean solver: logic diagrams of your expression and of the minimized
  circuit, on-screen keypad, easier typing (AB = A·B, &&, ||, !).
- Unit converter reworked: all-units converter (18 categories), linked
  dB/level fields, number systems with clickable bits, ADC/DAC.

WHAT'S NEW IN v5.1 (Transistors)
--------------------------------
- Junction Visualizer rebuilt for BJT, MOSFET and JFET (N and P): wide-
  range sliders + one-click presets for every way current can flow
  (active, saturation, cut-off, reverse, sub-threshold, reverse channel,
  body diode, gate conduction, breakdown/avalanche). Electrons and holes
  move along each real current path, depletion regions show their ions,
  channels taper and pinch off. Bias map (BJT) / live ID-VDS curve (FETs)
  and the symbol with every terminal current.
- Correct transistor symbols everywhere.
- New "Basic Circuits" tab: switches, amplifiers, followers, current
  sources, JFET voltage-controlled resistor - edit any value, see the
  schematic, Q-point, transfer curve and waveforms update live.

WHAT'S NEW IN v5.0
------------------
- The "PCB & Production" tab has been removed.
- Correct schematic symbols: every component tab has a "Schematic
  symbols" card, and every circuit drawing uses real symbols (resistor,
  capacitor, inductor, diode, BJT/MOSFET/JFET, op-amp, cell/battery,
  sources, ground). Switch resistor style IEC / ANSI in the top bar.
- Mixed Builder now draws the COMPLETE network schematic, shows the
  expression (e.g. Req = ((R1 + R2) || R3) + R4), and gives voltage,
  current/charge and power/energy for every component.
- Voltage Divider rebuilt: R1, R2, R3, R4 and RL clearly named on the
  schematic, node voltages and currents drawn on it, any value can be
  the unknown, per-resistor table, E-series pair finder.
- Signals > AC Circuits > "AC Quantities & Ripple": amplitude, peak-to-
  peak, RMS, average, instantaneous value, period <-> frequency, ripple,
  form/crest factor and more; plus rectifier + capacitor ripple.
- Resistors / Capacitors / Inductors: new "Calculator (solve any)" tab
  with ~40 formulas — tick the quantity you want and it is solved for.
- DC charts: voltage and current share the same zero line.

The full Python source is in the "source" folder of this repository.

TROUBLESHOOTING
----------------
- Windows SmartScreen may warn about an "unrecognized app" (the exe is
  not code-signed). Click "More info" -> "Run anyway".
- Some antivirus tools flag PyInstaller apps as a false positive. The
  full source is in the "source" folder.
