The Electronist's Guide — Windows Build
========================================

HOW TO RUN
----------
Double-click "ElectronistGuide.exe" in this folder. That's it — no
installer, no Python required, everything needed is already bundled
in the "_internal" folder next to the .exe (don't move the .exe away
from that folder, or it won't find its files).

Optional: run "Create_Desktop_Shortcut.bat" once to add a shortcut to
your Desktop so you don't have to open this folder every time.

WHAT CHANGED IN THIS BUILD
----------------------------
Removed (per request, judged low-value):
  - Resistor's "Chart / Simulate" subtab
  - Capacitor's "Electrolytic" subtab
  - Diode's "2-Diode Rectifier" subtab
  - The entire standalone "Signal Generator" tab
  - AC/DC Basics' "Troubleshooting" subtab

Fixed: charts that plot roughly-constant values (e.g. a DC voltage
divider's flat Vin/Vout lines) used to auto-zoom tight to just the data,
hiding where 0 actually is. Every remaining chart across the app now
always keeps 0 in view as a reference, without ever cropping real data.

Added: the BJT, MOSFET and JFET Q-Point / Bias calculators now draw the
actual family of characteristic curves (Ic-vs-Vce or Id-vs-Vds at a few
different Ib/Vgs values) behind the load line, with the one curve that
actually passes through the calculated Q-point drawn bolder than the
others — not just the load line and a dot as before.

Everything from the last build (RF & Microwave, Logic Circuit Builder,
Number Base / ADC-DAC converter) is unchanged and still included, in
both English and Romanian.

TROUBLESHOOTING
----------------
- If Windows SmartScreen warns about an "unrecognized app", this is
  expected for an app that isn't code-signed by a commercial
  certificate. Click "More info" -> "Run anyway".
- If your antivirus flags it, this is a common false positive for
  PyInstaller-built executables; it is not caused by any actual
  malicious code. You can inspect the full Python source in the
  companion source zip if you'd like to verify this yourself.
- Nothing is written outside this folder except normal Windows temp
  files during startup (PyInstaller unpacks itself to a temp
  directory each run); no installation, no registry changes.
