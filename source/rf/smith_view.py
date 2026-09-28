"""
rf/smith_view.py - Standalone, full-size Smith Chart subtab.

Reads the same shared SimulationState as the VNA. Selecting a
measurement, switching impedance/admittance mode, or moving a marker
never re-runs the solver - only the already-cached S-parameter dataset
is re-plotted.

Reference impedance: the trace being plotted (S_qk) was already computed
relative to that port's own reference impedance during simulation, so
the chart's Z0 field defaults to that real value every time the
measurement or the simulation result changes - typing a different Z0 is
still allowed (for "what if I renormalize to a different system
impedance" questions), but it's clearly marked as a manual override so a
plotted trace never silently looks like it belongs to the wrong network.
"""
import numpy as np
import tkinter as tk
from widgets import debounce_figure, smart_draw
from tkinter import ttk

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from i18n import t
from widgets import FONT_H2, FONT_BODY, FONT_MONO
from rf import smithchart

MARKER_COLORS = ["#f6ad55", "#fc8181", "#63b3ed", "#c792ea"]
TRACE_COLOR = "#4fd1c5"


class SmithChartView(ttk.Frame):
    def __init__(self, parent, sim_state):
        super().__init__(parent, style="Tab.TFrame")
        self.sim_state = sim_state
        self.out_port = 1
        self.in_port = 1
        self.mode = tk.StringVar(value="impedance")
        self.z0_var = tk.StringVar(value="50")
        self.z0_is_manual = False
        self.markers = [{"enabled": i == 0, "freq": None} for i in range(4)]
        self.active_marker = 0

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        intro = ttk.Label(self, text=t("rf.smith.intro"), style="CardBody.TLabel",
                           wraplength=1100, justify="left")
        intro.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 4))

        controls = ttk.Frame(self, style="Tab.TFrame")
        controls.grid(row=1, column=0, sticky="ew", padx=16, pady=(0, 4))

        ttk.Label(controls, text=t("rf.vna.measurement"), style="TabTitle.TLabel").pack(side="left")
        self.meas_var = tk.StringVar(value="S11")
        self.meas_combo = ttk.Combobox(controls, textvariable=self.meas_var, state="readonly", width=8)
        self.meas_combo.pack(side="left", padx=(6, 20))
        self.meas_combo.bind("<<ComboboxSelected>>", self._on_measurement_change)

        ttk.Label(controls, text=t("rf.smith.mode"), style="TabTitle.TLabel").pack(side="left")
        mode_combo = ttk.Combobox(controls, textvariable=self.mode, state="readonly", width=18,
                                   values=[t("rf.smith.impedance"), t("rf.smith.admittance")])
        mode_combo.set(t("rf.smith.impedance"))
        mode_combo.pack(side="left", padx=(6, 20))
        mode_combo.bind("<<ComboboxSelected>>", lambda e: self.redraw())
        self._mode_combo = mode_combo

        ttk.Label(controls, text=t("rf.smith.z0_label"), style="TabTitle.TLabel").pack(side="left")
        z0_entry = ttk.Entry(controls, textvariable=self.z0_var, width=8)
        z0_entry.pack(side="left", padx=6)
        z0_entry.bind("<Return>", self._on_manual_z0)
        z0_entry.bind("<FocusOut>", self._on_manual_z0)
        self.z0_note = ttk.Label(controls, text="", style="CardBody.TLabel", font=("Segoe UI", 8, "italic"))
        self.z0_note.pack(side="left", padx=(6, 0))

        body = ttk.Frame(self, style="Tab.TFrame")
        body.grid(row=2, column=0, sticky="nsew", padx=16, pady=(4, 12))
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        self.fig = Figure(figsize=(6, 6), dpi=100, facecolor="#10141f")
        self.canvas = FigureCanvasTkAgg(self.fig, master=body)
        debounce_figure(self.canvas)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")
        self.canvas.mpl_connect("button_press_event", self._on_plot_click)

        marker_panel = ttk.Frame(body, style="Card.TFrame")
        marker_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0))
        ttk.Label(marker_panel, text=t("common.markers"), font=FONT_H2,
                  style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(10, 2))
        self.click_hint = ttk.Label(marker_panel, text="", style="CardBody.TLabel",
                                     font=("Segoe UI", 8, "italic"), wraplength=200, justify="left")
        self.click_hint.pack(anchor="w", padx=10, pady=(0, 8))

        self.marker_widgets = []
        for i in range(4):
            row = ttk.Frame(marker_panel, style="Card.TFrame")
            row.pack(fill="x", padx=10, pady=3)
            select_btn = tk.Button(row, text="●", width=2, relief="flat",
                                    fg=MARKER_COLORS[i % len(MARKER_COLORS)],
                                    command=lambda i=i: self._set_active_marker(i))
            select_btn.pack(side="left")
            en = tk.BooleanVar(value=self.markers[i]["enabled"])
            ttk.Checkbutton(row, text="M" + str(i + 1), variable=en,
                             command=lambda i=i, en=en: self._toggle(i, en)).pack(side="left", padx=(2, 4))
            fv = tk.StringVar(value="")
            ent = ttk.Entry(row, textvariable=fv, width=8)
            ent.pack(side="left", padx=4)
            ent.bind("<Return>", lambda e, i=i, v=fv: self._set_freq(i, v))
            ttk.Label(row, text=t("rf.vna.ghz"), style="CardBody.TLabel").pack(side="left")
            val = ttk.Label(marker_panel, text="", style="CardBody.TLabel", font=FONT_MONO,
                             wraplength=200, justify="left")
            val.pack(anchor="w", padx=10, pady=(0, 6))
            self.marker_widgets.append({"select_btn": select_btn, "enabled_var": en,
                                         "freq_var": fv, "val_lbl": val})

        self._update_click_hint()
        self._update_active_marker_highlight()
        sim_state.on_result(lambda _r: self.refresh_and_redraw())
        self.refresh_and_redraw()

    def _set_active_marker(self, i):
        self.active_marker = i
        if not self.markers[i]["enabled"]:
            self.markers[i]["enabled"] = True
            self.marker_widgets[i]["enabled_var"].set(True)
        self._update_click_hint()
        self._update_active_marker_highlight()
        self.redraw()

    def _update_click_hint(self):
        self.click_hint.configure(text=t("rf.smith.click_hint").format(m=self.active_marker + 1))

    def _update_active_marker_highlight(self):
        for i, mw in enumerate(self.marker_widgets):
            mw["select_btn"].configure(relief="sunken" if i == self.active_marker else "flat",
                                        bg="#334166" if i == self.active_marker else "#e8e8e8")

    def refresh_and_redraw(self):
        result = self.sim_state.result
        ports = result.port_numbers if result else [1, 2]
        options = ["S" + str(o) + str(i) for o in ports for i in ports]
        cur = self.meas_var.get()
        self.meas_combo["values"] = options
        if cur not in options and options:
            self.meas_var.set(options[0])
        self.out_port, self.in_port = self._current_ports()
        self._sync_z0_default()
        self.redraw()

    def _current_ports(self):
        s = self.meas_var.get()
        digits = s[1:]
        return int(digits[0]), int(digits[1])

    def _on_measurement_change(self, _evt=None):
        self.out_port, self.in_port = self._current_ports()
        self.z0_is_manual = False
        self._sync_z0_default()
        self.redraw()

    def _sync_z0_default(self):
        if self.z0_is_manual:
            self.z0_note.configure(text=t("rf.smith.z0_manual"))
            return
        result = self.sim_state.result
        if result is None:
            self.z0_note.configure(text="")
            return
        z0 = result.z0_by_port.get(self.out_port)
        if z0 is not None:
            if z0.imag == 0:
                self.z0_var.set("{:g}".format(z0.real))
            else:
                self.z0_var.set("{:g}{:+g}j".format(z0.real, z0.imag))
        self.z0_note.configure(text=t("rf.smith.z0_auto"))

    def _on_manual_z0(self, _evt=None):
        self.z0_is_manual = True
        self.z0_note.configure(text=t("rf.smith.z0_manual"))
        self.redraw()

    def _toggle(self, i, var):
        self.markers[i]["enabled"] = bool(var.get())
        if var.get():
            self.active_marker = i
            self._update_click_hint()
            self._update_active_marker_highlight()
        self.redraw()

    def _set_freq(self, i, var):
        try:
            self.markers[i]["freq"] = float(var.get()) * 1e9
        except ValueError:
            return
        self.active_marker = i
        self._update_click_hint()
        self._update_active_marker_highlight()
        self.redraw()

    def _on_plot_click(self, event):
        result = self.sim_state.result
        if result is None or event.inaxes is None or event.xdata is None or event.ydata is None:
            return
        clicked = complex(event.xdata, event.ydata)
        trace = result.s_trace(self.out_port, self.in_port)
        idx = int(np.argmin(np.abs(trace - clicked)))
        i = self.active_marker
        self.markers[i]["enabled"] = True
        self.markers[i]["freq"] = result.freqs_hz[idx]
        self.marker_widgets[i]["enabled_var"].set(True)
        self.marker_widgets[i]["freq_var"].set("{:.4f}".format(result.freqs_hz[idx] / 1e9))
        self.redraw()

    def redraw(self):
        self.fig.clear()
        ax = self.fig.add_subplot(111)
        result = self.sim_state.result
        mode_key = "impedance" if self._mode_combo.get() == t("rf.smith.impedance") else "admittance"
        smithchart.draw_grid(ax, mode_key)

        if result is None:
            ax.text(0, 0, t("rf.vna.no_data"), color="#c7cbd8", ha="center", va="center")
            smart_draw(self.canvas)
            for mw in self.marker_widgets:
                mw["val_lbl"].configure(text="")
            return

        z0 = _parse_z0(self.z0_var.get())

        trace = result.s_trace(self.out_port, self.in_port)
        smithchart.plot_trace(ax, trace, TRACE_COLOR)
        z0_disp = "{:g}{:+g}jΩ".format(z0.real, z0.imag) if z0.imag else "{:g}Ω".format(z0.real)
        ax.set_title("S" + str(self.out_port) + str(self.in_port) + "  (Z0 = " + z0_disp + ")",
                      color="#c7cbd8", fontsize=10)

        for i, mk in enumerate(self.markers):
            lbl = self.marker_widgets[i]["val_lbl"]
            if not mk["enabled"] or mk["freq"] is None:
                lbl.configure(text="")
                continue
            idx = result.nearest_index(mk["freq"])
            gamma = trace[idx]
            smithchart.plot_marker(ax, gamma, MARKER_COLORS[i % len(MARKER_COLORS)], "M" + str(i + 1))
            z = smithchart.gamma_to_z(gamma, z0)
            f_hz = result.freqs_hz[idx]
            lbl.configure(text="{:.4f} GHz\n|Γ|={:.3f} ∠{:.1f}°\nZ={:.2f}{:+.2f}j Ω".format(
                f_hz / 1e9, abs(gamma), np.angle(gamma, deg=True), z.real, z.imag))

        self.fig.tight_layout()
        smart_draw(self.canvas)


def _parse_z0(text):
    text = text.strip().replace(" ", "")
    try:
        return complex(float(text), 0.0)
    except ValueError:
        pass
    try:
        return complex(text.replace("j", "j") if "j" in text else text + "j")
    except ValueError:
        return complex(50.0, 0.0)
