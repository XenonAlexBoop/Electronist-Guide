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
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from i18n import t
from widgets import FONT_H2, FONT_BODY, FONT_MONO
from rf import formats, smithchart

PLOT_BG = "#10141f"
PLOT_FG = "#c7cbd8"
TRACE_COLOR = "#4fd1c5"
MARKER_COLORS = ["#f6ad55", "#fc8181", "#63b3ed", "#c792ea"]

SEARCHABLE_FORMATS = {"log_mag", "lin_mag", "vswr", "return_loss", "group_delay"}


class RFVNAView(ttk.Frame):
    def __init__(self, parent, sim_state):
        super().__init__(parent, style="Tab.TFrame")
        self.sim_state = sim_state
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(1, weight=1)

        intro = ttk.Label(self, text=t("rf.vna.intro"), style="CardBody.TLabel",
                           wraplength=1100, justify="left")
        intro.grid(row=0, column=0, columnspan=2, sticky="ew", padx=10, pady=(10, 4))

        self.chan_a = ChannelPanel(self, sim_state, "A", TRACE_COLOR)
        self.chan_a.grid(row=1, column=0, sticky="nsew", padx=(10, 5), pady=(0, 10))
        self.chan_b = ChannelPanel(self, sim_state, "B", "#63b3ed")
        self.chan_b.grid(row=1, column=1, sticky="nsew", padx=(5, 10), pady=(0, 10))

        sim_state.on_result(lambda _r: self.refresh_all())

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

        self.columnconfigure(0, weight=1)

        header = ttk.Frame(self, style="Card.TFrame")
        header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 6))
        ttk.Label(header, text=t("rf.vna.channel") + f" {name}", font=FONT_H2,
                  style="CardTitle.TLabel").pack(side="left")
        ttk.Checkbutton(header, text=t("rf.vna.trace_visible"), variable=self.visible,
                         command=self.redraw).pack(side="right")

        # Measurement + format each get their own labeled row (instead of
        # being crammed side-by-side) so nothing truncates on a narrow
        # half-width panel.
        meas_row = ttk.Frame(self, style="Card.TFrame")
        meas_row.grid(row=1, column=0, sticky="ew", padx=12)
        ttk.Label(meas_row, text=t("rf.vna.measurement"), style="CardBody.TLabel").grid(
            row=0, column=0, sticky="w")
        self.meas_var = tk.StringVar(value="S11")
        self.meas_combo = ttk.Combobox(meas_row, textvariable=self.meas_var, state="readonly", width=8)
        self.meas_combo.grid(row=0, column=1, padx=(6, 24), sticky="w")
        self.meas_combo.bind("<<ComboboxSelected>>", self._on_measurement_change)

        ttk.Label(meas_row, text=t("rf.vna.format"), style="CardBody.TLabel").grid(
            row=0, column=2, sticky="w")
        self.fmt_var = tk.StringVar(value="Log Magnitude")
        self.fmt_combo = ttk.Combobox(meas_row, textvariable=self.fmt_var, state="readonly", width=18)
        self.fmt_combo.grid(row=0, column=3, padx=(6, 0), sticky="w")
        self.fmt_combo.bind("<<ComboboxSelected>>", self._on_format_change)

        search_row = ttk.Frame(self, style="Card.TFrame")
        search_row.grid(row=2, column=0, sticky="ew", padx=12, pady=(8, 0))
        ttk.Label(search_row, text=t("rf.vna.search_label"), style="CardBody.TLabel").pack(side="left")
        self.search_buttons = []
        for label_key, mode in (("rf.vna.search_max", "max"), ("rf.vna.search_min", "min"),
                                 ("rf.vna.search_peak", "peak"), ("rf.vna.search_dip", "dip")):
            b = ttk.Button(search_row, text=t(label_key), command=lambda m=mode: self._search(m))
            b.pack(side="left", padx=(6, 0))
            self.search_buttons.append(b)

        self.click_hint = ttk.Label(self, text="", style="CardBody.TLabel",
                                     font=("Segoe UI", 8, "italic"))
        self.click_hint.grid(row=3, column=0, sticky="w", padx=12, pady=(6, 0))

        self.fig = Figure(figsize=(5.0, 3.8), dpi=100, facecolor=PLOT_BG)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self)
        self.canvas.get_tk_widget().grid(row=4, column=0, sticky="nsew", padx=12, pady=8)
        self.rowconfigure(4, weight=1)
        self.canvas.mpl_connect("button_press_event", self._on_plot_click)

        marker_frame = ttk.Frame(self, style="Card.TFrame")
        marker_frame.grid(row=5, column=0, sticky="ew", padx=12, pady=(0, 12))
        self.marker_widgets = []
        for i in range(4):
            row = ttk.Frame(marker_frame, style="Card.TFrame")
            row.pack(fill="x", pady=2)
            # A small colored dot button is the "this marker moves when I
            # click the plot" selector (like choosing the active marker on
            # a real VNA before dragging it).
            select_btn = tk.Button(row, text="●", width=2, relief="flat",
                                    fg=MARKER_COLORS[i % len(MARKER_COLORS)],
                                    command=lambda i=i: self._set_active_marker(i))
            select_btn.pack(side="left")
            en = tk.BooleanVar(value=self.markers[i]["enabled"])
            cb = ttk.Checkbutton(row, text=f"M{i+1}", variable=en,
                                  command=lambda i=i, en=en: self._toggle_marker(i, en))
            cb.pack(side="left", padx=(2, 4))
            freq_var = tk.StringVar(value="")
            ent = ttk.Entry(row, textvariable=freq_var, width=9)
            ent.pack(side="left", padx=4)
            ent.bind("<Return>", lambda e, i=i, v=freq_var: self._set_marker_freq(i, v))
            unit_lbl = ttk.Label(row, text=t("rf.vna.ghz"), style="CardBody.TLabel")
            unit_lbl.pack(side="left")
            val_lbl = ttk.Label(row, text="", style="CardBody.TLabel", font=FONT_MONO)
            val_lbl.pack(side="left", padx=(10, 0))
            self.marker_widgets.append({"select_btn": select_btn, "enabled_var": en,
                                         "freq_var": freq_var, "val_lbl": val_lbl})

        self._update_click_hint()
        self._update_active_marker_highlight()
        self.refresh_measurement_options()
        self.redraw()

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

    def _on_plot_click(self, event):
        result = self.sim_state.result
        if result is None or event.inaxes is None or event.xdata is None:
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
    def redraw(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        result = self.sim_state.result

        if not self.visible.get() or result is None:
            ax.set_facecolor(PLOT_BG)
            ax.set_xticks([])
            ax.set_yticks([])
            for s in ax.spines.values():
                s.set_visible(False)
            msg = t("rf.vna.no_data") if result is None else t("rf.vna.hidden")
            ax.text(0.5, 0.5, msg, color=PLOT_FG, ha="center", va="center", transform=ax.transAxes)
            self.canvas.draw()
            self._clear_marker_labels()
            return

        trace = result.s_trace(self.out_port, self.in_port)

        if self.fmt in ("smith", "polar"):
            self._draw_polar_like(ax, result, trace)
        else:
            self._draw_rect(ax, result, trace)

        self.fig.tight_layout()
        self.canvas.draw()

    def _draw_rect(self, ax, result, trace):
        ax.set_facecolor(PLOT_BG)
        vals = np.real(formats.compute(self.fmt, trace, result.freqs_hz))
        freqs_ghz = result.freqs_hz / 1e9
        ax.plot(freqs_ghz, vals, color=self.color, linewidth=1.6, picker=True)
        ax.set_xlabel(t("rf.axis.ghz"), color=PLOT_FG, fontsize=8)
        ax.set_ylabel(t(formats.y_axis_label_key(self.fmt)), color=PLOT_FG, fontsize=8)
        ax.tick_params(colors=PLOT_FG, labelsize=7)
        for s in ax.spines.values():
            s.set_color("#3a4256")
        ax.grid(color="#232838")
        title = f"S{self.out_port}{self.in_port} - {t(formats.FORMAT_LABEL_KEYS[self.fmt])}"
        ax.set_title(title, color=PLOT_FG, fontsize=9)

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
                        fontsize=7, fontweight="bold")
            marker_vals.append((f_snapped, v))
        self._update_marker_labels(marker_vals, complex_mode=False)

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
        self._update_marker_labels(marker_vals, complex_mode=True)

    def _update_marker_labels(self, marker_vals, complex_mode):
        for i, mv in enumerate(marker_vals):
            lbl = self.marker_widgets[i]["val_lbl"]
            if mv is None:
                lbl.configure(text="")
                continue
            f_hz, v = mv
            if complex_mode:
                mag = abs(v)
                ang = np.angle(v, deg=True)
                z0 = 50.0
                z = smithchart.gamma_to_z(v, z0)
                lbl.configure(text=f"{f_hz/1e9:.4f} GHz  |Γ|={mag:.3f}∠{ang:.1f}°  Z={z.real:.1f}{z.imag:+.1f}jΩ")
            else:
                lbl.configure(text=f"{f_hz/1e9:.4f} GHz  {v:.3f}")

    def _clear_marker_labels(self):
        for mw in self.marker_widgets:
            mw["val_lbl"].configure(text="")


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
