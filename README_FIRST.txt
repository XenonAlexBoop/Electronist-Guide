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

WHAT'S IN THE "RF & MICROWAVE" TAB
------------------------------------
A "Multiport RF Simulator" with:
  - Circuit Builder: a grid-based schematic editor with real component
    symbols (zigzag resistor, coil inductor, plate capacitor, etc.),
    ports, transmission lines, loads, wires, and grounds. Grounds (and
    everything else) can be selected, dragged, and deleted, including
    when placed on top of another part's terminal.
  - Virtual VNA: two independent measurement/display channels, with an
    on-screen explanation of what each channel does, click-to-place
    markers, and automatic peak/dip/max/min search.
  - Smith Chart: a real, live-plotted Smith chart whose reference
    impedance auto-matches the actual simulated port (clearly marked
    as auto vs. manually overridden), with click-to-place markers.
  - S-Parameter Results: the full S-parameter matrix at any swept
    frequency point.
  - A Learn tab covering S-parameters, reflection coefficient, VSWR,
    return loss, transmission lines, and Smith Chart theory.
Supports up to 4 ports, arbitrary branched circuit topologies, and is
available in both English and Romanian.

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
