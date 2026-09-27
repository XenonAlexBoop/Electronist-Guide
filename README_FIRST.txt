The Electronist's Guide v5.0 — Windows Build
==============================================

HOW TO RUN
----------
Double-click "ElectronistGuide.exe" in this folder. No installer, no
Python required — everything is bundled in the "_internal" folder next
to the .exe (keep the .exe in this folder).

Optional: run "Create_Desktop_Shortcut.bat" once to add a Desktop
shortcut.

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

The previous exe is kept next to this one as
ElectronistGuide_v4.5_backup.exe (it uses the same _internal folder);
delete it once you're happy with v5.0.

TROUBLESHOOTING
----------------
- Windows SmartScreen may warn about an "unrecognized app" (the exe is
  not code-signed). Click "More info" -> "Run anyway".
- Some antivirus tools flag PyInstaller apps as a false positive. The
  full source is in the electronist_guide_5.0 folder.
