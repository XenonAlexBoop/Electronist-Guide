"""
rf/vna_view.py - The Virtual VNA: two independent display channels
(Channel A, Channel B) reading from the one shared SimulationState.

A real bench VNA has one set of RF ports on the circuit under test, but
several independent *display* channels, each free to show a different
S-parameter in a different format at the same time (e.g. Channel A =
S11 on a Smith Chart, Channel B = S21 in dB) - that's exactly what
Channel A / Channel B model here. Changing Channel A's measurement,
format, trace visibility or markers never touches Channel B's state,
and vice-versa - and neither one ever re-runs the RF solver: they only
redraw already-cached data.

Markers are placed by clicking directly on the trace (like dragging a
marker on a real VNA) - typing an exact frequency is still available as
a fallback in the field next to each marker's checkbox.
"""
import numpy as np
import tkinter as tk
from widgets import debounce_figure, smart_draw
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk

from i18n import t, register
from widgets import FONT_H2, FONT_BODY, FONT_MONO
from rf import formats, smithchart

PLOT_BG = "#10141f"
PLOT_FG = "#c7cbd8"
TRACE_COLOR = "#4fd1c5"
MARKER_COLORS = ["#f6ad55", "#fc8181", "#63b3ed", "#c792ea"]

SEARCHABLE_FORMATS = {"log_mag", "lin_mag", "vswr", "return_loss", "group_delay"}


register({
    "rf.vna.layout": ("Layout:", "Aranjare:"),
    "rf.vna.lay_stack": ("A over B", "A peste B"),
    "rf.vna.lay_side": ("A | B side by side", "A | B alăturate"),
    "rf.vna.lay_a": ("Only A (big)", "Doar A (mare)"),
    "rf.vna.lay_b": ("Only B (big)", "Doar B (mare)"),
    "rf.vna.nav_hint": ("Mouse wheel = zoom frequency · Zoom box / Pan buttons for more · Full view resets.",
                        "Rotița = zoom pe frecvență · butoanele Zoom zonă / Deplasare · Vedere completă resetează."),
    "rf.vna.markers": ("Markers", "Markere"),
    "rf.vna.no_markers": ("Markers: none placed yet - click the trace, or use Max / Min / Peak / Dip.",
                          "Markere: niciunul încă - clic pe traseu sau folosește Maxim / Minim / Vârf / Adâncitură."),
    "rf.vna.nav_home": ("⌂ Full view", "⌂ Vedere completă"),
    "rf.vna.nav_zoom": ("Zoom box", "Zoom zonă"),
    "rf.vna.nav_pan": ("Pan", "Deplasare"),
    "rf.vna.nav_save": ("Save image", "Salvează imaginea"),
})


class RFVNAView(ttk.Frame):
    """v6.2: the channels no longer squeeze their plot under a tall stack of
    controls - each channel keeps its controls in a compact side column and
    gives the plot the rest.  A layout switch shows A | B side by side
    (default), A over B, or a single channel using the whole page."""

    LAYOUTS = ("side", "stack", "a", "b")

    def __init__(self, parent, sim_state):
        super().__init__(parent, style="Tab.TFrame")
        self.sim_state = sim_state
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        top = ttk.Frame(self, style="Tab.TFrame")
        top.grid(row=0, column=0, sticky="ew", padx=10, pady=(8, 4))
        top.columnconfigure(0, weight=1)
        intro = ttk.Label(top, text=t("rf.vna.intro"), style="CardBody.TLabel",
                          wraplength=900, justify="left", font=("Segoe UI", 9))
        intro.grid(row=0, column=0, sticky="ew")
        top.bind("<Configure>", lambda e: intro.configure(wraplength=max(300, e.width - 560)), add="+")
        lay = ttk.Frame(top, style="Tab.TFrame")
        lay.grid(row=0, column=1, sticky="e", padx=(12, 0))
        ttk.Label(lay, text=t("rf.vna.layout"), style="CardBody.TLabel").pack(side="left", padx=(0, 6))
        from uikit import Segmented
        self.layout_var = tk.StringVar(value="side")
        Segmented(lay, [(k, t("rf.vna.lay_" + k)) for k in self.LAYOUTS], self.layout_var,
                  command=self._apply_layout, accent="#2b6cb0").pack(side="left")

        self.body = ttk.Frame(self, style="Tab.TFrame")
        self.body.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        self.chan_a = ChannelPanel(self.body, sim_state, "A", TRACE_COLOR)
        self.chan_b = ChannelPanel(self.body, sim_state, "B", "#63b3ed")
        self.chan_b.set_default_measurement("S21")
        self._apply_layout("side")

        sim_state.on_result(lambda _r: self.refresh_all())

    def _apply_layout(self, key):
        b = self.body
        for c in (self.chan_a, self.chan_b):
            c.grid_forget()
        for i in range(2):
            b.rowconfigure(i, weight=0, uniform="")
            b.columnconfigure(i, weight=0, uniform="")
        if key == "stack":
            b.columnconfigure(0, weight=1)
            b.rowconfigure(0, weight=1, uniform="ch")
            b.rowconfigure(1, weight=1, uniform="ch")
            self.chan_a.grid(row=0, column=0, sticky="nsew", pady=(0, 5))
            self.chan_b.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
            orient = "row"
        elif key == "side":
            b.rowconfigure(0, weight=1)
            b.columnconfigure(0, weight=1, uniform="ch")
            b.columnconfigure(1, weight=1, uniform="ch")
            self.chan_a.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
            self.chan_b.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
            orient = "col"
        else:
            b.rowconfigure(0, weight=1)
            b.columnconfigure(0, weight=1)
            (self.chan_a if key == "a" else self.chan_b).grid(row=0, column=0, sticky="nsew")
            orient = "row"
        for c in (self.chan_a, self.chan_b):
            c.set_orientation(orient)

    def refresh_all(self):
        self.chan_a.refresh_measurement_options()
        self.chan_a.redraw()
        self.chan_b.refresh_measurement_options()
        self.chan_b.redraw()


class ChannelPanel(ttk.Frame):
    def __init__(self, parent, sim_state, name, color):
        super().__init__(parent, style="Card.TFrame")
        self.sim_state = sim_state
        self.name = name
        self.color = color
        self.out_port = 1
        self.in_port = 1
        self.fmt = "log_mag"
        self.visible = tk.BooleanVar(value=True)
        self.markers = [{"enabled": i == 0, "freq": None} for i in range(4)]
        self.active_marker = 0  # which marker moves when you click the plot
        self._view_key = None
        self._auto_lims = None
        self._orient = None

        # ---- controls: two blocks (settings, markers) that sit in a side
        # column ("row" orientation) or side by side above the plot ("col")
        self.ctl = ttk.Frame(self, style="Card.TFrame")
        self.ctl_main = ttk.Frame(self.ctl, style="Card.TFrame")
        self.ctl_mk = ttk.Frame(self.ctl, style="Card.TFrame")

        header = ttk.Frame(self.ctl_main, style="Card.TFrame")
        header.pack(fill="x", pady=(0, 6))
        tk.Frame(header, bg=color, width=6, height=22).pack(side="left", padx=(0, 8))
        ttk.Label(header, text=t("rf.vna.channel") + f" {name}", font=FONT_H2,
                  style="CardTitle.TLabel").pack(side="left")
        ttk.Checkbutton(header, text=t("rf.vna.trace_visible"), variable=self.visible,
                        command=self.redraw).pack(side="right")

        meas_row = ttk.Frame(self.ctl_main, style="Card.TFrame")
        meas_row.pack(fill="x")
        meas_row.columnconfigure(1, weight=1)
        ttk.Label(meas_row, text=t("rf.vna.measurement"), style="CardBody.TLabel").grid(
            row=0, column=0, sticky="w", pady=2)
        self.meas_var = tk.StringVar(value="S11")
        self.meas_combo = ttk.Combobox(meas_row, textvariable=self.meas_var, state="readonly", width=8)
        self.meas_combo.grid(row=0, column=1, padx=(6, 0), sticky="ew", pady=2)
        self.meas_combo.bind("<<ComboboxSelected>>", self._on_measurement_change)
        ttk.Label(meas_row, text=t("rf.vna.format"), style="CardBody.TLabel").grid(
            row=1, column=0, sticky="w", pady=2)
        self.fmt_var = tk.StringVar(value="Log Magnitude")
        self.fmt_combo = ttk.Combobox(meas_row, textvariable=self.fmt_var, state="readonly", width=18)
        self.fmt_combo.grid(row=1, column=1, padx=(6, 0), sticky="ew", pady=2)
        self.fmt_combo.bind("<<ComboboxSelected>>", self._on_format_change)

        ttk.Label(self.ctl_main, text=t("rf.vna.search_label"), style="CardBody.TLabel")\
            .pack(anchor="w", pady=(8, 2))
        search_row = ttk.Frame(self.ctl_main, style="Card.TFrame")
        search_row.pack(fill="x")
        self.search_buttons = []
        for k, (label_key, mode) in enumerate((("rf.vna.search_max", "max"), ("rf.vna.search_min", "min"),
                                               ("rf.vna.search_peak", "peak"), ("rf.vna.search_dip", "dip"))):
            b = ttk.Button(search_row, text=t(label_key), width=8, command=lambda m=mode: self._search(m))
            b.grid(row=0, column=k, padx=(0, 3), sticky="ew")
            search_row.columnconfigure(k, weight=1)
            self.search_buttons.append(b)

        ttk.Label(self.ctl_mk, text=t("rf.vna.markers"), font=("Segoe UI", 9, "bold"),
                  style="CardBody.TLabel").pack(anchor="w", pady=(0, 2))
        self.marker_widgets = []
        self._mk_rows = []
        mk_grid = ttk.Frame(self.ctl_mk, style="Card.TFrame")
        mk_grid.pack(anchor="w")
        for i in range(4):
            row = ttk.Frame(mk_grid, style="Card.TFrame")
            row.grid(row=i // 2, column=i % 2, sticky="w", padx=(0, 10), pady=1)
            self._mk_rows.append(row)
            # A small colored dot button is the "this marker moves when I
            # click the plot" selector (like choosing the active marker on
            # a real VNA before dragging it).
            select_btn = tk.Button(row, text="●", width=2, relief="flat", bd=1, pady=0, padx=0,
                                   font=("Segoe UI", 9), fg=MARKER_COLORS[i % len(MARKER_COLORS)],
                                   command=lambda i=i: self._set_active_marker(i))
            select_btn.pack(side="left")
            en = tk.BooleanVar(value=self.markers[i]["enabled"])
            cb = ttk.Checkbutton(row, text=f"M{i+1}", variable=en,
                                 command=lambda i=i, en=en: self._toggle_marker(i, en))
            cb.pack(side="left", padx=(2, 4))
            freq_var = tk.StringVar(value="")
            ent = ttk.Entry(row, textvariable=freq_var, width=8)
            ent.pack(side="left", padx=4)
            ent.bind("<Return>", lambda e, i=i, v=freq_var: self._set_marker_freq(i, v))
            ttk.Label(row, text=t("rf.vna.ghz"), style="CardBody.TLabel").pack(side="left")
            val_lbl = None   # v6.2: marker read-outs are drawn inside the plot
            self.marker_widgets.append({"select_btn": select_btn, "enabled_var": en,
                                        "freq_var": freq_var, "val_lbl": val_lbl})


        # ---- plot: gets all the remaining room, with a zoom/pan toolbar
        self.plot_box = tk.Frame(self, bg=PLOT_BG)
        self.plot_box.rowconfigure(1, weight=1)
        self.plot_box.columnconfigure(0, weight=1)
        # marker read-outs live in a strip above the plot (never cover the trace)
        self.readout = tk.Frame(self.plot_box, bg=PLOT_BG)
        self.readout.grid(row=0, column=0, sticky="ew", padx=6, pady=(4, 0))
        self.readout_lbls = [tk.Label(self.readout, text="", bg=PLOT_BG, font=("Consolas", 9, "bold"),
                                      fg=MARKER_COLORS[i % len(MARKER_COLORS)], anchor="w")
                             for i in range(4)]
        self.readout_empty = tk.Label(self.readout, text=t("rf.vna.no_markers"), bg=PLOT_BG,
                                      font=("Consolas", 9), fg="#6b7390", anchor="w")
        self.readout_empty.grid(row=0, column=0, sticky="w")
        self.fig = Figure(figsize=(4.0, 2.6), dpi=100, facecolor=PLOT_BG)
        try:   # re-fit the margins on every draw, so a resized plot never clips its labels
            self.fig.set_layout_engine("tight", pad=0.6)
        except Exception:
            pass
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.plot_box)
        debounce_figure(self.canvas)
        cw = self.canvas.get_tk_widget()
        cw.configure(width=300, height=180)   # small natural size - the grid stretches it
        cw.grid(row=1, column=0, sticky="nsew")
        tb_frame = tk.Frame(self.plot_box, bg=PLOT_BG)
        tb_frame.grid(row=2, column=0, sticky="ew")
        # matplotlib's own toolbar is kept (hidden) for its zoom/pan logic;
        # a slim row of labelled buttons drives it and leaves more room for the plot
        self.toolbar = NavigationToolbar2Tk(self.canvas, tb_frame)
        self.toolbar.update()
        self.toolbar.pack_forget()
        self.nav_buttons = {}
        for key, cmd in (("home", self._nav_home), ("zoom", lambda: self._nav_mode("zoom")),
                         ("pan", lambda: self._nav_mode("pan")), ("save", self.toolbar.save_figure)):
            b = tk.Label(tb_frame, text=t("rf.vna.nav_" + key), font=("Segoe UI", 8, "bold"),
                         bg="#232a3b", fg=PLOT_FG, padx=8, pady=2, cursor="hand2")
            b.pack(side="left", padx=(4 if key == "home" else 0, 3), pady=3)
            b.bind("<Button-1>", lambda _e, c=cmd: c())
            self.nav_buttons[key] = b
        hints = tk.Frame(tb_frame, bg=PLOT_BG)
        hints.pack(side="right", padx=6, fill="x", expand=True)
        self.click_hint = tk.Label(hints, text="", font=("Segoe UI", 8, "italic"), anchor="e",
                                   fg="#e2e8f0", bg=PLOT_BG)
        self.click_hint.pack(anchor="e")
        self.nav_hint = tk.Label(hints, text=t("rf.vna.nav_hint"), font=("Segoe UI", 8), anchor="e",
                                 fg="#8a93a8", bg=PLOT_BG, justify="right")
        self.nav_hint.pack(anchor="e")
        tb_frame.bind("<Configure>", self._fit_hints, add="+")
        self.canvas.mpl_connect("button_press_event", self._on_plot_click)
        self.canvas.mpl_connect("scroll_event", self._on_scroll)

        self.set_orientation("row")
        self._update_click_hint()
        self._update_active_marker_highlight()
        self.refresh_measurement_options()
        self.redraw()

    def _fit_hints(self, e):
        # on a narrow panel keep just the (more important) click hint
        room = e.width - 340
        self.click_hint.configure(wraplength=max(150, room))
        if room < 560:
            self.nav_hint.pack_forget()
        elif not self.nav_hint.winfo_ismapped():
            self.nav_hint.pack(anchor="e")

    def _nav_home(self):
        if getattr(self.toolbar, "mode", ""):
            self._nav_mode(None)
        self.redraw(reset_view=True)

    def _nav_mode(self, mode):
        cur = str(getattr(self.toolbar, "mode", "") or "")
        if mode == "zoom" or (mode is None and "zoom" in cur):
            self.toolbar.zoom()
        elif mode == "pan" or (mode is None and "pan" in cur):
            self.toolbar.pan()
        now = str(getattr(self.toolbar, "mode", "") or "")
        for k in ("zoom", "pan"):
            on = k in now
            self.nav_buttons[k].configure(bg="#4fd1c5" if on else "#232a3b",
                                          fg="#10141f" if on else PLOT_FG)

    def set_default_measurement(self, meas):
        self.meas_var.set(meas)
        self.out_port, self.in_port = self._current_ports()
        self._sync_format_options()
        self.redraw()

    def set_orientation(self, orient):
        """"row": controls in a left column, plot on the right (wide panels);
        "col": controls in two blocks above the plot (narrow panels)."""
        if orient == self._orient:
            return
        self._orient = orient
        for w in (self.ctl, self.plot_box, self.ctl_main, self.ctl_mk):
            w.grid_forget()
        for i in range(2):
            self.rowconfigure(i, weight=0)
            self.columnconfigure(i, weight=0)
            self.ctl.columnconfigure(i, weight=0)
        if orient == "row":
            self.columnconfigure(1, weight=1)
            self.rowconfigure(0, weight=1)
            self.ctl.grid(row=0, column=0, sticky="nsw", padx=(12, 8), pady=10)
            self.ctl_main.grid(row=0, column=0, sticky="new")
            self.ctl_mk.grid(row=1, column=0, sticky="new", pady=(10, 0))
            self.plot_box.grid(row=0, column=1, sticky="nsew", padx=(0, 10), pady=10)
            for i, r in enumerate(self._mk_rows):
                r.grid_configure(row=i // 2, column=i % 2)
        else:
            self.columnconfigure(0, weight=1)
            self.rowconfigure(1, weight=1)
            self.ctl.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 4))
            self.ctl.columnconfigure(0, weight=1)
            self.ctl.columnconfigure(1, weight=1)
            self.ctl_main.grid(row=0, column=0, sticky="new", padx=(0, 10))
            self.ctl_mk.grid(row=0, column=1, sticky="new")
            self.plot_box.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))
            for i, r in enumerate(self._mk_rows):
                r.grid_configure(row=i, column=0)

    # ------------------------------------------------------------------
    def _set_active_marker(self, i):
        self.active_marker = i
        if not self.markers[i]["enabled"]:
            self.markers[i]["enabled"] = True
            self.marker_widgets[i]["enabled_var"].set(True)
        self._update_click_hint()
        self._update_active_marker_highlight()
        self.redraw()

    def _update_active_marker_highlight(self):
        for i, mw in enumerate(self.marker_widgets):
            mw["select_btn"].configure(
                relief="sunken" if i == self.active_marker else "flat",
                bg="#334166" if i == self.active_marker else "#e8e8e8")

    def _update_click_hint(self):
        self.click_hint.configure(text=t("rf.vna.click_hint").format(m=self.active_marker + 1))

    def refresh_measurement_options(self):
        result = self.sim_state.result
        if result is None:
            ports = [1, 2]
        else:
            ports = result.port_numbers
        options = [f"S{o}{i}" for o in ports for i in ports]
        cur = self.meas_var.get()
        self.meas_combo["values"] = options
        if cur not in options and options:
            self.meas_var.set(options[0])
            self.out_port, self.in_port = ports[0], ports[0]
        self._sync_format_options()

    def _current_ports(self):
        s = self.meas_var.get()
        digits = s[1:]
        return int(digits[0]), int(digits[1])

    def _sync_format_options(self):
        out_p, in_p = self._current_ports()
        avail = formats.formats_for(out_p, in_p)
        labels = [t(formats.FORMAT_LABEL_KEYS[f]) for f in avail]
        self.fmt_combo["values"] = labels
        if self.fmt not in avail:
            self.fmt = avail[0]
        self.fmt_var.set(t(formats.FORMAT_LABEL_KEYS[self.fmt]))
        searchable = self.fmt in SEARCHABLE_FORMATS
        for b in self.search_buttons:
            b.configure(state=("normal" if searchable else "disabled"))

    def _on_measurement_change(self, _evt=None):
        self.out_port, self.in_port = self._current_ports()
        self._sync_format_options()
        self.redraw()

    def _on_format_change(self, _evt=None):
        label = self.fmt_var.get()
        for key, key_i18n in formats.FORMAT_LABEL_KEYS.items():
            if t(key_i18n) == label:
                self.fmt = key
                break
        searchable = self.fmt in SEARCHABLE_FORMATS
        for b in self.search_buttons:
            b.configure(state=("normal" if searchable else "disabled"))
        self.redraw()

    def _toggle_marker(self, i, var):
        self.markers[i]["enabled"] = bool(var.get())
        if var.get():
            self.active_marker = i
            self._update_click_hint()
            self._update_active_marker_highlight()
        self.redraw()

    def _set_marker_freq(self, i, var):
        try:
            f_ghz = float(var.get())
        except ValueError:
            return
        self.markers[i]["freq"] = f_ghz * 1e9
        self.active_marker = i
        self._update_click_hint()
        self._update_active_marker_highlight()
        self.redraw()

    def _on_scroll(self, event):
        """Mouse wheel = zoom the frequency axis around the cursor."""
        if event.inaxes is None or event.xdata is None or self.fmt in ("smith", "polar"):
            return
        ax = event.inaxes
        try:
            if self.toolbar._nav_stack() is None:
                self.toolbar.push_current()
        except Exception:
            pass
        f = 0.8 if event.button == "up" else 1.25
        x0, x1 = ax.get_xlim()
        x = event.xdata
        ax.set_xlim(x - (x - x0) * f, x + (x1 - x) * f)
        if self._auto_lims:   # never zoom out past the full sweep
            a0, a1 = self._auto_lims[0]
            n0, n1 = ax.get_xlim()
            if n1 - n0 >= a1 - a0:
                ax.set_xlim(a0, a1)
        self._autoscale_y_visible(ax)
        self.toolbar.push_current()
        smart_draw(self.canvas)

    def _autoscale_y_visible(self, ax):
        result = self.sim_state.result
        if result is None:
            return
        x0, x1 = ax.get_xlim()
        fg = result.freqs_hz / 1e9
        vals = np.real(formats.compute(self.fmt, result.s_trace(self.out_port, self.in_port), result.freqs_hz))
        if self.fmt == "group_delay":
            vals = vals * 1e9
        m = (fg >= x0) & (fg <= x1) & np.isfinite(vals)
        if m.sum() < 2:
            return
        lo, hi = float(vals[m].min()), float(vals[m].max())
        pad = (hi - lo) * 0.08 or max(abs(hi) * 0.05, 0.05)
        ax.set_ylim(lo - pad, hi + pad)

    def _on_plot_click(self, event):
        result = self.sim_state.result
        if result is None or event.inaxes is None or event.xdata is None:
            return
        if getattr(self.toolbar, "mode", ""):
            return   # the toolbar's pan/zoom tool is active - leave the click to it
        if event.button != 1:
            return
        i = self.active_marker
        if self.fmt in ("smith", "polar"):
            if event.ydata is None:
                return
            clicked = complex(event.xdata, event.ydata)
            trace = result.s_trace(self.out_port, self.in_port)
            idx = int(np.argmin(np.abs(trace - clicked)))
        else:
            f_hz = event.xdata * 1e9
            idx = result.nearest_index(f_hz)
        self.markers[i]["enabled"] = True
        self.markers[i]["freq"] = result.freqs_hz[idx]
        self.marker_widgets[i]["enabled_var"].set(True)
        self.marker_widgets[i]["freq_var"].set(f"{result.freqs_hz[idx] / 1e9:.4f}")
        self.redraw()

    def _search(self, mode):
        result = self.sim_state.result
        if result is None:
            return
        trace = result.s_trace(self.out_port, self.in_port)
        vals = formats.compute(self.fmt, trace, result.freqs_hz)
        vals = np.real(vals)
        if mode == "max":
            idx = int(np.argmax(vals))
        elif mode == "min":
            idx = int(np.argmin(vals))
        elif mode == "peak":
            idx = _local_extremum(vals, want_max=True)
        else:
            idx = _local_extremum(vals, want_max=False)
        target = self.active_marker
        self.markers[target]["enabled"] = True
        self.markers[target]["freq"] = result.freqs_hz[idx]
        self.marker_widgets[target]["enabled_var"].set(True)
        self.marker_widgets[target]["freq_var"].set(f"{result.freqs_hz[idx] / 1e9:.4f}")
        self.redraw()

    # ------------------------------------------------------------------
    def redraw(self, reset_view=False):
        # keep a zoom the user made (toolbar / mouse wheel) across redraws of
        # the same measurement - e.g. while placing markers
        result = self.sim_state.result
        key = (self.meas_var.get(), self.fmt, None if result is None else
               (float(result.freqs_hz[0]), float(result.freqs_hz[-1]), len(result.freqs_hz)))
        keep = None
        if (not reset_view and self.fig.axes and key == self._view_key
                and self._auto_lims is not None):
            old = self.fig.axes[0]
            cur = (tuple(old.get_xlim()), tuple(old.get_ylim()))
            if cur != self._auto_lims:
                keep = cur
        self.fig.clear()
        ax = self.fig.add_subplot(111)

        if not self.visible.get() or result is None:
            ax.set_facecolor(PLOT_BG)
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)
            msg = t("rf.vna.no_data") if result is None else t("rf.vna.hidden")
            ax.text(0.5, 0.5, msg, color=PLOT_FG, ha="center", va="center", transform=ax.transAxes,
                    fontsize=11)
            self._view_key, self._auto_lims = None, None
            self.toolbar.update()
            smart_draw(self.canvas)
            self._clear_marker_labels()
            return

        trace = result.s_trace(self.out_port, self.in_port)

        if self.fmt in ("smith", "polar"):
            self._draw_polar_like(ax, result, trace)
        else:
            self._draw_rect(ax, result, trace)

        self._view_key = key
        self._auto_lims = (tuple(ax.get_xlim()), tuple(ax.get_ylim()))
        self.toolbar.update()          # new axes -> fresh zoom history
        if keep is not None:
            self.toolbar.push_current()    # "home" = the full view
            ax.set_xlim(*keep[0])
            ax.set_ylim(*keep[1])
            self.toolbar.push_current()
        smart_draw(self.canvas)

    def _draw_rect(self, ax, result, trace):
        ax.set_facecolor(PLOT_BG)
        vals = np.real(formats.compute(self.fmt, trace, result.freqs_hz))
        if self.fmt == "group_delay":
            vals = vals * 1e9          # seconds -> ns (the axis is labelled ns)
        freqs_ghz = result.freqs_hz / 1e9
        ax.plot(freqs_ghz, vals, color=self.color, linewidth=1.8, picker=True)
        ax.set_xlim(freqs_ghz[0], freqs_ghz[-1])
        ax.set_xlabel(t("rf.axis.ghz"), color=PLOT_FG, fontsize=9)
        ax.set_ylabel(t(formats.y_axis_label_key(self.fmt)), color=PLOT_FG, fontsize=9)
        ax.tick_params(colors=PLOT_FG, labelsize=8)
        for s in ax.spines.values():
            s.set_color("#3a4256")
        ax.grid(color="#232838")
        title = f"S{self.out_port}{self.in_port} - {t(formats.FORMAT_LABEL_KEYS[self.fmt])}"
        ax.set_title(title, color=PLOT_FG, fontsize=10)

        marker_vals = []
        for i, mk in enumerate(self.markers):
            if not mk["enabled"] or mk["freq"] is None:
                marker_vals.append(None)
                continue
            idx = result.nearest_index(mk["freq"])
            f_snapped = result.freqs_hz[idx]
            v = vals[idx]
            is_active = (i == self.active_marker)
            ax.plot([f_snapped / 1e9], [v], marker="o", markersize=8 if is_active else 6,
                    color=MARKER_COLORS[i % len(MARKER_COLORS)],
                    markeredgecolor="white" if is_active else None,
                    markeredgewidth=1.5 if is_active else 0)
            ax.annotate(f"M{i+1}", (f_snapped / 1e9, v), xytext=(6, 6),
                        textcoords="offset points", color=MARKER_COLORS[i % len(MARKER_COLORS)],
                        fontsize=8, fontweight="bold")
            marker_vals.append((f_snapped, v))
        self._update_marker_labels(marker_vals, complex_mode=False, ax=ax)

    def _draw_polar_like(self, ax, result, trace):
        if self.fmt == "smith":
            smithchart.draw_grid(ax, "impedance")
        else:
            ax.set_facecolor(PLOT_BG)
            ax.set_aspect("equal")
            ax.set_xlim(-1.1, 1.1)
            ax.set_ylim(-1.1, 1.1)
            th = np.linspace(0, 2 * np.pi, 200)
            ax.plot(np.cos(th), np.sin(th), color="#3a4256", linewidth=1)
            ax.axhline(0, color="#3a4256", linewidth=0.8)
            ax.axvline(0, color="#3a4256", linewidth=0.8)
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)

        smithchart.plot_trace(ax, trace, self.color)
        ax.set_title(f"S{self.out_port}{self.in_port} - {t(formats.FORMAT_LABEL_KEYS[self.fmt])}",
                      color=PLOT_FG, fontsize=9)

        marker_vals = []
        for i, mk in enumerate(self.markers):
            if not mk["enabled"] or mk["freq"] is None:
                marker_vals.append(None)
                continue
            idx = result.nearest_index(mk["freq"])
            gamma = trace[idx]
            smithchart.plot_marker(ax, gamma, MARKER_COLORS[i % len(MARKER_COLORS)], f"M{i+1}")
            marker_vals.append((result.freqs_hz[idx], gamma))
        self._update_marker_labels(marker_vals, complex_mode=True, ax=ax)

    def _update_marker_labels(self, marker_vals, complex_mode, ax=None):
        """Marker read-outs (frequency + value) in the strip above the plot."""
        lines, colors = [], []
        unit = "" if complex_mode else {"log_mag": " dB", "return_loss": " dB", "phase": "°",
                                         "group_delay": " ns"}.get(self.fmt, "")
        for i, mv in enumerate(marker_vals):
            if mv is None:
                continue
            f_hz, v = mv
            if complex_mode:
                z = smithchart.gamma_to_z(v, 50.0)
                txt = (f"M{i+1}  {f_hz/1e9:.4f} GHz  |Γ| {abs(v):.3f}∠{np.angle(v, deg=True):.1f}°"
                       f"  Z {z.real:.1f}{z.imag:+.1f}j Ω")
            else:
                txt = f"M{i+1}  {f_hz/1e9:.4f} GHz   {v:.3f}{unit}"
            lines.append(txt)
            colors.append(MARKER_COLORS[i % len(MARKER_COLORS)])
        for lb in self.readout_lbls:
            lb.grid_forget()
        if lines:
            self.readout_empty.grid_forget()
        else:
            self.readout_empty.grid(row=0, column=0, sticky="w")
        w = self.plot_box.winfo_width()
        per_row = max(1, min(4, w // (440 if complex_mode else 250))) if w > 50 else 2
        k = 0
        for i, mv in enumerate(marker_vals):
            if mv is None:
                continue
            lb = self.readout_lbls[i]
            lb.configure(text=lines[k])
            lb.grid(row=k // per_row, column=k % per_row, sticky="w", padx=(0, 18))
            k += 1

    def _clear_marker_labels(self):
        for lb in self.readout_lbls:
            lb.grid_forget()
        self.readout_empty.grid(row=0, column=0, sticky="w")


def _local_extremum(vals, want_max):
    n = len(vals)
    candidates = []
    for i in range(1, n - 1):
        if want_max and vals[i] > vals[i - 1] and vals[i] > vals[i + 1]:
            candidates.append(i)
        if not want_max and vals[i] < vals[i - 1] and vals[i] < vals[i + 1]:
            candidates.append(i)
    if not candidates:
        return int(np.argmax(vals)) if want_max else int(np.argmin(vals))
    if want_max:
        return max(candidates, key=lambda i: vals[i])
    return min(candidates, key=lambda i: vals[i])
