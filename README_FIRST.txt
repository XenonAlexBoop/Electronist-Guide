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

WHAT'S NEW IN THIS BUILD
-------------------------
Boolean Logic -> "Logic Circuit Builder":
  - New: a Junction Node part for clean signal branching (wire one
    output into it, then wire its output to as many inputs as you like).
  - New: scroll to zoom in/out (anchored on your cursor, like a map),
    right-drag to pan, +/- buttons and a "Reset View" button in the
    palette - built for navigating larger circuits.
  - New: a live grid-snap preview (a small crosshair) follows your
    cursor while placing parts, so you can see exactly where a click
    will land before you commit to it.
  - Everything still updates in real time: toggle an input switch and
    watch every gate, mux/demux, node and wire update instantly.

RF & Microwave -> "Multiport RF Simulator": circuit builder with real
component symbols, a Virtual VNA (two independent channels with
click-to-place markers), a Smith Chart whose reference impedance
auto-syncs to the simulated port, and full S-parameter results.

Both tools are available in English and Romanian, matching the rest
of the app.

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
