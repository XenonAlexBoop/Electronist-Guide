# How I build a Windows .exe for The Electronist's Guide

Keep this file. When you want a new .exe in a **future chat**, upload this
guide together with the current project source zip and say something like
"follow this guide to build me the .exe." I have no memory between chats,
so this file is what lets me reproduce the exact same process instead of
re-deriving it (and re-hitting the same bugs) from scratch.

## Why this is even tricky

PyInstaller does not cross-compile. A Windows `.exe` can only be built by
a real Windows Python. I only have a Linux sandbox — no Windows, no
internet access beyond a fixed allow-list of domains (GitHub is on it;
python.org is not). So the approach is: install Wine (a Windows
compatibility layer) in the Linux sandbox, get a **real Windows build of
Python** running inside Wine, and run PyInstaller with *that* interpreter.
The output is a genuine Windows `.exe`, not a Linux binary in disguise —
I always verify this with the `file` command and by actually launching it.

Everything below happens inside my sandbox and does **not** persist
between separate conversations. In a new chat I have to redo all of
Steps 1-4 (roughly 10-15 minutes of tool calls) before I can even start
building. Don't expect a rebuild request to be instant — the first one
in any new chat is bootstrapping a whole toolchain, not just running a
script.

---

## Step 1 — Install Wine

```bash
apt-get update
apt-get install -y --no-install-recommends wine64
```

**Known gotcha:** this sometimes fails with unmet dependencies on
`libgphoto2-6t64` / `libgphoto2-port12t64` even though they show a valid
candidate version — this is a transient package-mirror sync issue, not a
real problem. Fix: install those two packages directly first, then retry:
```bash
apt-get install -y --no-install-recommends libgphoto2-6t64 libgphoto2-port12t64
apt-get install -y --no-install-recommends wine64
```

## Step 2 — Get a portable Windows build of Python

python.org isn't reachable, but GitHub is, and the
`astral-sh/python-build-standalone` project publishes ready-to-run
Windows Python builds as GitHub release assets (this is the same project
tools like `uv` use).

```bash
# Find the current release tag
curl -s https://raw.githubusercontent.com/astral-sh/python-build-standalone/latest-release/latest-release.json
# -> gives a "tag", e.g. "20260623"

# List the Windows x86_64 builds for that tag (this endpoint is what
# GitHub's own UI calls to lazy-load the asset list, and it's reachable
# directly even though python.org isn't)
curl -s "https://github.com/astral-sh/python-build-standalone/releases/expanded_assets/<TAG>" -o assets.html
grep -o 'cpython-3\.[0-9]*\.[0-9]*+<TAG>-x86_64-pc-windows-msvc-install_only_stripped\.tar\.gz' assets.html | sort -u

# Pick a mature, stable minor version (I used 3.12.x last time - avoid
# the newest/beta one in the list, and avoid anything with "rc"/"b" in
# the version). Download it:
curl -sL -o python-win.tar.gz \
  "https://github.com/astral-sh/python-build-standalone/releases/download/<TAG>/<chosen-filename>.tar.gz"
```

## Step 3 — Set up the Wine prefix and extract Python into it

```bash
export WINEARCH=win64
export WINEPREFIX=/home/claude/.wine
wineboot --init

mkdir -p "$WINEPREFIX/drive_c/Python312"
tar -xzf python-win.tar.gz -C "$WINEPREFIX/drive_c/Python312" --strip-components=1

# Sanity check - this alone confirms Wine + the Windows Python both work
export DISPLAY=:99   # see Step 4 for why
wine "$WINEPREFIX/drive_c/Python312/python.exe" --version
```

## Step 4 — Xvfb (a virtual display)

The sandbox has no real screen. Wine (and the app itself) still need a
`DISPLAY` to draw to, even for a build step that doesn't obviously need
graphics. Start this once per session and restart it if it ever dies
(background processes, including Xvfb, do **not** survive across
separate user turns/messages in the same conversation — restart it
whenever a wine/python command fails with "couldn't connect to display"):

```bash
rm -f /tmp/.X11-unix/X99
setsid Xvfb :99 -screen 0 1300x900x24 < /dev/null > /home/claude/xvfb.log 2>&1 &
sleep 2
export DISPLAY=:99
```

## Step 5 — Install the project's Python dependencies into Wine's Python

```bash
wine "$WINEPREFIX/drive_c/Python312/python.exe" -m pip install --upgrade pip
wine "$WINEPREFIX/drive_c/Python312/python.exe" -m pip install -r requirements.txt pyinstaller
```

**Known gotcha — numpy version:** numpy >= 2's bundled OpenBLAS calls a
`ucrtbase.dll` math function (`crealf`) that Wine's C runtime doesn't
implement, causing every import of numpy to hard-crash under Wine only
(this is invisible on real Windows). Fix, already applied in this
project's `requirements.txt` — **check it's still there** in whatever zip
you're handed:
```
numpy>=1.24,<2
```
If a future dependency bump ever removes that pin, re-add it before
building, or the build will produce an exe that crashes on launch.

## Step 6 — Build with PyInstaller

**Two hard-won gotchas that make this NOT a simple one-liner:**

1. **Must run through a real pty, not a plain background redirect.**
   Running `wine python.exe ... &` with plain `> log 2>&1` redirection
   causes Wine's console layer to hand CPython invalid stdio handles,
   crashing with `OSError: [WinError 6] Invalid handle` during
   interpreter init. Fix: wrap the whole command in the `script` utility,
   which allocates a pty:
   ```bash
   script -qec '<command>' /path/to/logfile
   ```

2. **Must fully detach so it doesn't hang the tool call.** `script` tees
   output to both the pty and the log file, and if its own stdout isn't
   redirected away, a backgrounded call still blocks whatever is waiting
   on that pipe. Combine `setsid` (full detach) with `> /dev/null 2>&1`
   on the outer command:
   ```bash
   setsid env WINEPREFIX=/home/claude/.wine WINEDEBUG=-all DISPLAY=:99 \
     script -qec 'wine "/home/claude/.wine/drive_c/Python312/python.exe" -m PyInstaller --noconfirm electronist_guide.spec' \
     /home/claude/build.log > /dev/null 2>&1 &
   ```
   Then poll it from separate tool calls (`sleep 30; tail build.log`,
   repeat) rather than waiting on it directly — a full build takes
   roughly 45-90 seconds, which can exceed a single tool call's own
   time budget.

3. **The project's `.spec` file must list `PIL._tkinter_finder` as a
   hidden import.** Without it, PyInstaller's static analysis misses a
   module matplotlib's Tk backend needs at runtime, and the built exe
   crashes the instant you open any tab with a chart (works fine when
   run from source, only breaks once frozen — a very confusing failure
   mode if you don't already know to look for it). Already in this
   project's `electronist_guide.spec`:
   ```python
   hiddenimports=['PIL._tkinter_finder'],
   ```
   Check this is still present in whatever `.spec` you're given, since
   this only shows up as a bug in the *packaged* app, not in testing
   from source.

Confirm success:
```bash
ls -la dist/ElectronistGuide/ElectronistGuide.exe
file dist/ElectronistGuide/ElectronistGuide.exe
# should say: PE32+ executable (GUI) x86-64, for MS Windows
```

## Step 7 — Actually verify it, don't just trust a clean build log

A successful PyInstaller run is not proof the app works — I've caught
real crashes (the numpy issue, the missing hidden import) only by
launching the built exe and looking at it. Every time:

```bash
cd dist/ElectronistGuide
setsid env WINEPREFIX=/home/claude/.wine WINEDEBUG=-all DISPLAY=:99 \
  script -qec 'wine ElectronistGuide.exe' /home/claude/run.log > /dev/null 2>&1 &
```
Wait — under Wine, with a large app, the first window can take up to
~60 seconds to appear (this is a Wine/emulation cost; not necessarily
representative of real Windows). Then:
```bash
sleep 60
DISPLAY=:99 xdotool search --name "" | wc -l   # should be >1 once a window exists
DISPLAY=:99 import -window root /home/claude/check.png
```
Look at the screenshot. Click into at least one chart-heavy tab (that's
where the hidden-import bug hides) using `xdotool mousemove --window
<id> <x> <y>` + `xdotool click 1` (coordinates are **window-relative**,
so subtract the window's `getwindowgeometry` offset from any screenshot
pixel coordinate — this trips me up if I forget it), screenshot again,
and actually look at the result before calling it done.

## Step 8 — Package for delivery

```bash
cd dist/ElectronistGuide
# add Create_Desktop_Shortcut.bat and README_FIRST.txt (see the project's
# existing copies from the last build for the exact content used before)
cd ..
zip -rq ElectronistGuide_Windows.zip ElectronistGuide

# separately, for the source deliverable:
cd ../..
rm -rf build dist __pycache__ tabs/__pycache__ logic/__pycache__
zip -rq electronist_guide_source.zip electronist_guide_X.Y -x "*.pyc" -x "*__pycache__*"
```

Before handing either zip over, unzip the source one fresh into a new
folder and run a quick `python3 -m py_compile` + import-every-tab smoke
test against *that* copy — confirms nothing was left out of the zip,
rather than trusting the working directory I'd been editing in.

---

## Quick checklist for "just rebuild it" in a new chat

1. Confirm the zip you gave me has `electronist_guide.spec` (with the
   PIL hidden import), `requirements.txt` (with `numpy<2`), and
   `assets/icon.{ico,icns,png}`. If any are missing, recreate them
   first (I can regenerate the icon and spec file from scratch if
   needed — they don't depend on anything project-version-specific).
2. Wine + Xvfb + Windows Python: bootstrap from Step 1 if this is a
   fresh sandbox (it will be, in a new chat).
3. Install deps (Step 5), build (Step 6), verify by actually looking at
   it (Step 7), package (Step 8).
4. Tell you the truth about what I verified and what I didn't — e.g. if
   I only click through 2-3 tabs, say so rather than imply full
   coverage.

---

## Addendum (v5.0 build, Sept 2026) — the "patch the existing exe" route

In the v5.0 session **GitHub release assets, python.org and nuget.org were
all blocked** by the sandbox egress policy, so Steps 2–6 (get a Windows
Python, pip-install, run PyInstaller under Wine) were impossible. What
worked instead — and is much faster when only the app's own `.py` files
changed (no new third-party packages):

1. Stage the user's *existing* `ElectronistGuide\ElectronistGuide.exe`
   (a PyInstaller 6.x one-dir build for CPython 3.12).
2. With a **Linux CPython 3.12** (same bytecode magic as the bundled
   `python312.dll`; `apt install python3.12` + `python3.12-tk`, and
   `pip install pyinstaller` in a venv just for its archive readers),
   run `tools/patch_exe.py SRC_DIR OLD_EXE NEW_EXE`:
   - splits the exe into Windows bootloader + CArchive (find the
     `MEI\014\013\012\013\016` cookie at the end),
   - opens the embedded `PYZ.pyz`, removes the app's old modules,
     compiles every project `.py` with `compile()` and adds them
     (zlib level 6, TOC = marshalled list of
     `(name, (typecode 0=module/1=package, offset, length))`),
   - recompiles the `main` script entry, keeps every other CArchive
     entry byte-for-byte, re-serialises the TOC (16-byte aligned) and
     writes a new cookie.
3. The `_internal` folder is reused unchanged, so only the new exe is
   delivered. Keep the old exe as a backup next to it.
4. Verify: (a) load every app module from the new exe's PYZ into Linux
   Python 3.12 and walk every tab; (b) run the real exe under Wine
   (binaries are in `/usr/lib/wine/`, i.e. `wine64`; the prefix must be in
   a directory owned by the current user, e.g. `/root/wineprefix`). For
   Wine you need a copy of `_internal` — staging only ~150 of its ~1200
   files is enough if you skip `_tcl_data/tzdata`, `_tcl_data/msgs` and
   most of `mpl-data`, but you DO need `numpy/core/_multiarray_tests*.pyd`
   and `mpl-data/fonts/ttf/LastResortHE-Regular.ttf` (matplotlib 3.11
   hard-requires it).

Limit: if a change needs a new third-party package or a new compiled
extension, this route can't add it — fall back to the full Wine +
PyInstaller build above.
