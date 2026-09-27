"""
tabs/modulation.py - Signals > Modulation sub-tab.
Amplitude, Frequency, and Phase modulation of an arbitrary message
waveform (any shape from the Signal Generator's set, not just a tone)
onto a sinusoidal carrier. Shows message / carrier / modulated result
stacked, plus the FFT magnitude spectrum of the modulated signal so the
AM sidebands / FM spectral spreading are directly visible, not just
implied by the math.
"""
import math
import tkinter as tk
from tkinter import ttk

from charts import MplChartFrame, modulate_signal, modulation_spectrum, am_envelope_demod, PLOT_BG, include_zero
from widgets import FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ScrollableFrame, TheoryPanel
from data import get_theory
from i18n import t

ACCENT_C = "#7c3aed"
MSG_COLOR = "#2A9D8F"

# Message-waveform choices for the modulator (moved here from the now-removed
# standalone Signal Generator tab, which was this list's only other user).
WAVE_KEYS = [("Sine", "sig.wave.sine"), ("Square", "sig.wave.square"),
             ("Sawtooth", "sig.wave.sawtooth"), ("Triangle", "sig.wave.triangle")]
CARRIER_COLOR = "#c9622a"
MOD_COLOR = "#7c3aed"

MOD_KEYS = [("AM", "mod.type.am"), ("FM", "mod.type.fm"), ("PM", "mod.type.pm")]


class ModulationPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)
        self._ready = False

        left_wrap = ttk.Frame(self, style="Card.TFrame")
        left_wrap.grid(row=0, column=0, sticky="nsew")
        left_wrap.columnconfigure(0, weight=1)
        left_wrap.rowconfigure(0, weight=1)
        left_scroll = ScrollableFrame(left_wrap, style="Card.TFrame")
        left_scroll.grid(row=0, column=0, sticky="nsew")

        right = ttk.Frame(self, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        self._build_controls(left_scroll.body)
        self._build_output(right)
        self._ready = True
        self._simulate()

    # ------------------------------------------------------------------
    def _build_controls(self, parent):
        pad = {"padx": 16, "pady": 6}
        parent.columnconfigure(0, weight=1)

        header = tk.Frame(parent, bg=ACCENT_C, height=6)
        header.grid(row=0, column=0, sticky="ew")

        ttk.Label(parent, text=t("mod.intro"), font=FONT_BODY, wraplength=380,
                  justify="left", style="CardBody.TLabel").grid(row=1, column=0, sticky="w", **pad)

        self._mod_labels = [t(key) for _, key in MOD_KEYS]
        self._mod_kinds = [k for k, _ in MOD_KEYS]
        ttk.Label(parent, text=t("mod.type_label"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=2, column=0, sticky="w", padx=16, pady=(6, 2))
        self.mod_type_var = tk.StringVar(value=self._mod_labels[0])
        mod_cb = ttk.Combobox(parent, textvariable=self.mod_type_var, values=self._mod_labels,
                               state="readonly", width=10)
        mod_cb.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 10))
        mod_cb.bind("<<ComboboxSelected>>", lambda e: self._on_mod_type_change())

        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=4, column=0, sticky="ew", padx=16, pady=4)

        # --- Message signal ---
        ttk.Label(parent, text=t("mod.message_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=5, column=0, sticky="w", padx=16, pady=(6, 2))

        self._wave_labels = [t(key) for _, key in WAVE_KEYS]
        self._wave_kinds = [k for k, _ in WAVE_KEYS]
        self.msg_wave_var = tk.StringVar(value=self._wave_labels[0])
        wave_cb = ttk.Combobox(parent, textvariable=self.msg_wave_var, values=self._wave_labels,
                                state="readonly", width=14)
        wave_cb.grid(row=6, column=0, sticky="w", padx=16, pady=(0, 6))
        wave_cb.bind("<<ComboboxSelected>>", lambda e: self._on_wave_change())

        self.msg_freq_var = tk.StringVar(value="200")
        self.msg_amp_var = tk.StringVar(value="1")
        self.msg_duty_var = tk.StringVar(value="50")

        ttk.Label(parent, text=t("mod.msg_freq_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=7, column=0, sticky="w", padx=16)
        e = ttk.Entry(parent, textvariable=self.msg_freq_var, width=14)
        e.grid(row=8, column=0, sticky="w", padx=16)
        e.bind("<KeyRelease>", lambda e: self._simulate())

        ttk.Label(parent, text=t("mod.msg_amp_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=9, column=0, sticky="w", padx=16, pady=(6, 0))
        e = ttk.Entry(parent, textvariable=self.msg_amp_var, width=14)
        e.grid(row=10, column=0, sticky="w", padx=16)
        e.bind("<KeyRelease>", lambda e: self._simulate())

        self.msg_duty_title = ttk.Label(parent, text=t("mod.msg_duty_label"), font=FONT_BODY,
                                         style="CardBody.TLabel")
        self.msg_duty_title.grid(row=11, column=0, sticky="w", padx=16, pady=(6, 0))
        self.msg_duty_entry = ttk.Entry(parent, textvariable=self.msg_duty_var, width=14)
        self.msg_duty_entry.grid(row=12, column=0, sticky="w", padx=16)
        self.msg_duty_entry.bind("<KeyRelease>", lambda e: self._simulate())
        self._duty_widgets = [self.msg_duty_title, self.msg_duty_entry]

        sep2 = ttk.Separator(parent, orient="horizontal")
        sep2.grid(row=13, column=0, sticky="ew", padx=16, pady=(10, 4))

        # --- Carrier ---
        ttk.Label(parent, text=t("mod.carrier_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=14, column=0, sticky="w", padx=16, pady=(6, 2))
        self.carrier_freq_var = tk.StringVar(value="5000")
        self.carrier_amp_var = tk.StringVar(value="1")

        ttk.Label(parent, text=t("mod.carrier_freq_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=15, column=0, sticky="w", padx=16)
        e = ttk.Entry(parent, textvariable=self.carrier_freq_var, width=14)
        e.grid(row=16, column=0, sticky="w", padx=16)
        e.bind("<KeyRelease>", lambda e: self._simulate())

        ttk.Label(parent, text=t("mod.carrier_amp_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=17, column=0, sticky="w", padx=16, pady=(6, 0))
        e = ttk.Entry(parent, textvariable=self.carrier_amp_var, width=14)
        e.grid(row=18, column=0, sticky="w", padx=16)
        e.bind("<KeyRelease>", lambda e: self._simulate())

        sep3 = ttk.Separator(parent, orient="horizontal")
        sep3.grid(row=19, column=0, sticky="ew", padx=16, pady=(10, 4))

        # --- Modulation-specific parameter (one shown at a time) ---
        ttk.Label(parent, text=t("mod.param_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=20, column=0, sticky="w", padx=16, pady=(6, 2))

        self.am_index_var = tk.StringVar(value="0.5")
        self.fm_dev_var = tk.StringVar(value="800")
        self.pm_dev_var = tk.StringVar(value="90")

        self.am_row_label = ttk.Label(parent, text=t("mod.am_index_label"), font=FONT_BODY,
                                       style="CardBody.TLabel")
        self.am_scale = ttk.Scale(parent, from_=0.0, to=2.0, orient="horizontal",
                                   command=lambda v: self._on_am_slider(v))
        self.am_entry = ttk.Entry(parent, textvariable=self.am_index_var, width=14)

        self.fm_row_label = ttk.Label(parent, text=t("mod.fm_dev_label"), font=FONT_BODY,
                                       style="CardBody.TLabel")
        self.fm_entry = ttk.Entry(parent, textvariable=self.fm_dev_var, width=14)

        self.pm_row_label = ttk.Label(parent, text=t("mod.pm_dev_label"), font=FONT_BODY,
                                       style="CardBody.TLabel")
        self.pm_entry = ttk.Entry(parent, textvariable=self.pm_dev_var, width=14)

        self.fm_entry.bind("<KeyRelease>", lambda e: self._simulate())
        self.pm_entry.bind("<KeyRelease>", lambda e: self._simulate())
        self.am_entry.bind("<KeyRelease>", lambda e: self._simulate())

        self.am_demod_var = tk.BooleanVar(value=False)
        self.am_demod_chk = ttk.Checkbutton(parent, text=t("mod.demod_toggle"), variable=self.am_demod_var,
                                             command=self._simulate)
        self.am_demod_note = ttk.Label(parent, text=t("mod.demod_note"), font=FONT_BODY,
                                        style="CardBody.TLabel", wraplength=380, justify="left")

        self._param_row = 21  # rows 21-25ish reused across mod types

        sepr = ttk.Separator(parent, orient="horizontal")
        self._results_sep = sepr

        ttk.Label(parent, text=t("mod.results_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel")
        self.result_var = tk.StringVar()
        self.result_label_title = ttk.Label(parent, text=t("mod.results_title"), font=FONT_H2,
                                             foreground=ACCENT_C, style="CardSub.TLabel")
        self.result_label = ttk.Label(parent, textvariable=self.result_var, font=FONT_MONO,
                                       foreground=ACCENT_C, style="CardFormula.TLabel",
                                       wraplength=380, justify="left")

        self._on_wave_change(simulate=False)
        self._on_mod_type_change(simulate=False)

    def _on_wave_change(self, simulate=True):
        wave = self._wave_kinds[self._wave_labels.index(self.msg_wave_var.get())]
        show_duty = wave in ("Square", "Triangle")
        for w in self._duty_widgets:
            if show_duty:
                w.grid()
            else:
                w.grid_remove()
        if simulate:
            self._simulate()

    def _on_mod_type_change(self, simulate=True):
        mod = self._mod_kinds[self._mod_labels.index(self.mod_type_var.get())]
        row = self._param_row
        for w in (self.am_row_label, self.am_scale, self.am_entry,
                  self.fm_row_label, self.fm_entry, self.pm_row_label, self.pm_entry,
                  self.am_demod_chk, self.am_demod_note,
                  self._results_sep, self.result_label_title, self.result_label):
            w.grid_forget()

        if mod == "AM":
            self.am_row_label.grid(row=row, column=0, sticky="w", padx=16, pady=(6, 0))
            self.am_scale.grid(row=row + 1, column=0, sticky="ew", padx=16)
            self.am_entry.grid(row=row + 2, column=0, sticky="w", padx=16, pady=(2, 6))
            self.am_demod_chk.grid(row=row + 3, column=0, sticky="w", padx=16, pady=(2, 2))
            self.am_demod_note.grid(row=row + 4, column=0, sticky="w", padx=16, pady=(0, 8))
            next_row = row + 5
        elif mod == "FM":
            self.fm_row_label.grid(row=row, column=0, sticky="w", padx=16, pady=(6, 0))
            self.fm_entry.grid(row=row + 1, column=0, sticky="w", padx=16, pady=(0, 8))
            next_row = row + 2
        else:  # PM
            self.pm_row_label.grid(row=row, column=0, sticky="w", padx=16, pady=(6, 0))
            self.pm_entry.grid(row=row + 1, column=0, sticky="w", padx=16, pady=(0, 8))
            next_row = row + 2

        self._results_sep.grid(row=next_row, column=0, sticky="ew", padx=16, pady=(6, 6))
        self.result_label_title.grid(row=next_row + 1, column=0, sticky="w", padx=16)
        self.result_label.grid(row=next_row + 2, column=0, sticky="w", padx=16, pady=(2, 16))

        if simulate:
            self._simulate()

    def _on_am_slider(self, value_str):
        self.am_index_var.set(f"{float(value_str):.3g}")
        self._simulate()

    # ------------------------------------------------------------------
    def _build_output(self, parent):
        ttk.Label(parent, text=t("mod.chart_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, sticky="w", padx=16, pady=(16, 6))
        self.chart = MplChartFrame(parent, figsize=(6.4, 9.4), with_toolbar=False)
        self.chart.grid(row=1, column=0, sticky="nsew", padx=16, pady=(0, 16))

    def _simulate(self):
        if not self._ready:
            return
        mod = self._mod_kinds[self._mod_labels.index(self.mod_type_var.get())]
        wave = self._wave_kinds[self._wave_labels.index(self.msg_wave_var.get())]
        try:
            msg_freq = float(self.msg_freq_var.get())
            msg_amp = float(self.msg_amp_var.get())
            msg_duty = float(self.msg_duty_var.get()) / 100.0
            carrier_freq = float(self.carrier_freq_var.get())
            carrier_amp = float(self.carrier_amp_var.get())
            am_index = float(self.am_index_var.get())
            fm_dev = float(self.fm_dev_var.get())
            pm_dev_rad = math.radians(float(self.pm_dev_var.get()))
        except ValueError:
            self.result_var.set(t("mod.invalid"))
            return
        if msg_freq <= 0 or carrier_freq <= 0 or msg_amp == 0:
            self.result_var.set(t("mod.invalid"))
            return

        t_arr, message, carrier, modulated = modulate_signal(
            mod, wave, msg_frequency=msg_freq, msg_amplitude=msg_amp, msg_duty=msg_duty,
            carrier_frequency=carrier_freq, carrier_amplitude=carrier_amp,
            am_index=am_index, fm_deviation=fm_dev, pm_deviation=pm_dev_rad)

        freqs, mag = modulation_spectrum(t_arr, modulated)

        fig = self.chart.fig
        fig.clear()
        ax1 = fig.add_subplot(4, 1, 1)
        ax2 = fig.add_subplot(4, 1, 2, sharex=ax1)
        ax3 = fig.add_subplot(4, 1, 3, sharex=ax1)
        ax4 = fig.add_subplot(4, 1, 4)

        for ax in (ax1, ax2, ax3, ax4):
            ax.set_facecolor(PLOT_BG)
            ax.grid(True, alpha=0.3, linewidth=0.6)
            ax.tick_params(labelsize=9)

        ax1.plot(t_arr, message, color=MSG_COLOR, linewidth=1.8)
        ax1.set_title(t("mod.chart_message"), fontsize=11, color="#333", loc="left", fontweight="bold")
        ax1.set_ylabel(t("mod.amplitude_axis"), fontsize=9)
        ax1.tick_params(labelbottom=False)

        ax2.plot(t_arr, carrier, color=CARRIER_COLOR, linewidth=1.1)
        ax2.set_title(t("mod.chart_carrier"), fontsize=11, color="#333", loc="left", fontweight="bold")
        ax2.set_ylabel(t("mod.amplitude_axis"), fontsize=9)
        ax2.tick_params(labelbottom=False)

        ax3.plot(t_arr, modulated, color=MOD_COLOR, linewidth=1.1)
        if mod == "AM" and self.am_demod_var.get():
            envelope = am_envelope_demod(modulated)
            ax3.plot(t_arr, envelope, color=MSG_COLOR, linewidth=2.0, linestyle="--")
            ax3.plot(t_arr, -envelope, color=MSG_COLOR, linewidth=2.0, linestyle="--")
        ax3.set_title(t("mod.chart_modulated"), fontsize=11, color="#333", loc="left", fontweight="bold")
        ax3.set_ylabel(t("mod.amplitude_axis"), fontsize=9)
        ax3.set_xlabel(t("common.time_s"), fontsize=9)

        for ax in (ax1, ax2, ax3):
            include_zero(ax)

        ax4.plot(freqs, mag, color=MOD_COLOR, linewidth=1.3)
        ax4.fill_between(freqs, mag, color=MOD_COLOR, alpha=0.15)
        # The zoom window has to reflect whichever deviation is actually in
        # play for the *selected* mod type - previously this always factored
        # in the FM deviation field even while AM/PM were selected, which
        # could blow the window out to many kHz and squash the real content
        # into a sliver on the left.
        if mod == "FM":
            spread = fm_dev
        elif mod == "PM":
            spread = pm_dev_rad * msg_freq
        else:
            spread = 0.0
        span = max(5 * msg_freq, 2 * spread, 8 * msg_freq if mod == "AM" else 0, 150)
        ax4.set_xlim(max(0, carrier_freq - span * 2), carrier_freq + span * 2)
        ax4.set_title(t("mod.chart_spectrum"), fontsize=11, color="#333", loc="left", fontweight="bold")
        ax4.set_ylabel(t("mod.magnitude_axis"), fontsize=9)
        ax4.set_xlabel(t("mod.freq_axis"), fontsize=9)
        include_zero(ax4)

        fig.subplots_adjust(left=0.13, right=0.97, top=0.96, bottom=0.06, hspace=0.65)
        self.chart.redraw()

        if mod == "AM":
            bw = 2 * msg_freq
            self.result_var.set(f"{t('mod.bw_estimate')} ≈ {bw:.4g} Hz\n({t('mod.bw_am_note')})")
        elif mod == "FM":
            bw = 2 * (fm_dev + msg_freq)
            beta = fm_dev / msg_freq
            self.result_var.set(
                f"{t('mod.bw_estimate')} ≈ {bw:.4g} Hz  (Carson's rule)\n"
                f"{t('mod.mod_index_label')} β = Δf/fm = {beta:.3g}")
        else:
            eff_dev = pm_dev_rad * msg_freq  # peak instantaneous freq deviation ~ dphi/dt max
            bw = 2 * (eff_dev + msg_freq)
            self.result_var.set(
                f"{t('mod.bw_estimate')} ≈ {bw:.4g} Hz  (Carson's rule)\n({t('mod.bw_pm_note')})")


class ModulationTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        ttk.Label(self, text=t("mod.tab_title"), font=FONT_H1, style="TabTitle.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))

        nb = ttk.Notebook(self)
        nb.grid(row=1, column=0, sticky="nsew", padx=20, pady=(0, 10))

        calc_page = ModulationPanel(nb)
        theory_scroll = ScrollableFrame(nb, style="Card.TFrame")
        TheoryPanel(theory_scroll.body, get_theory("modulation"), accent=ACCENT_C)\
            .pack(fill="both", expand=True)
        nb.add(calc_page, text=t("mod.subtab.calculator"))
        nb.add(theory_scroll, text=t("common.learn"))
