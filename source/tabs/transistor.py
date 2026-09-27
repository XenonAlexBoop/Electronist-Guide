import tkinter as tk
from tkinter import ttk

from data import get_theory
from drawing import (draw_transistor,
                      draw_mosfet_symbol, draw_jfet_symbol,
                      draw_bjt_bias_circuit, draw_mosfet_bias_circuit, draw_jfet_bias_circuit)
from bjt_sim import BjtJunctionSim
from mosfet_sim import MosfetJunctionSim
from jfet_sim import JfetJunctionSim
from widgets import TheoryPanel, ScrollableFrame, parse_value, format_value, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO, ACCENT
from charts import (MplChartFrame, transistor_switch, transistor_amplifier,
                     mosfet_switch, mosfet_amplifier, jfet_switch, jfet_amplifier,
                     V_COLOR, I_COLOR, PLOT_BG, include_zero)
import bias
from i18n import t
from symbols import SymbolGallery
from transistor_viz import JunctionVisualizer
from transistor_circuits import TransistorCircuitsPanel

ACCENT_C = ACCENT["transistor"]

FAMILIES = ["bjt", "mosfet", "jfet"]
POLARITY_BY_FAMILY = {
    "bjt": [("NPN", "transistor.polarity.npn"), ("PNP", "transistor.polarity.pnp")],
    "mosfet": [("N-channel", "transistor.polarity.nchannel"), ("P-channel", "transistor.polarity.pchannel")],
    "jfet": [("N-channel", "transistor.polarity.nchannel"), ("P-channel", "transistor.polarity.pchannel")],
}
FAMILY_LABEL_KEY = {"bjt": "transistor.family.bjt", "mosfet": "transistor.family.mosfet",
                     "jfet": "transistor.family.jfet"}
THEORY_KEY = {"bjt": "transistor_bjt", "mosfet": "transistor_mosfet", "jfet": "transistor_jfet"}


class TransistorTab(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self._active_sim = None

        ttk.Label(self, text=t("transistor.tab_title"), font=FONT_H1, style="TabTitle.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=20, pady=(16, 6))

        selector = ttk.Frame(self, style="Tab.TFrame")
        selector.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 6))

        ttk.Label(selector, text=t("transistor.family"), font=FONT_BODY, style="TabTitle.TLabel")\
            .grid(row=0, column=0, sticky="w", padx=(0, 6))
        self._family_labels = [t(FAMILY_LABEL_KEY[f]) for f in FAMILIES]
        self.family_var = tk.StringVar(value=self._family_labels[0])
        family_cb = ttk.Combobox(selector, textvariable=self.family_var, values=self._family_labels,
                                  state="readonly", width=14)
        family_cb.grid(row=0, column=1, sticky="w", padx=(0, 20))
        family_cb.bind("<<ComboboxSelected>>", lambda e: self._on_family_change())

        ttk.Label(selector, text=t("transistor.polarity"), font=FONT_BODY, style="TabTitle.TLabel")\
            .grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.polarity_var = tk.StringVar()
        self.polarity_cb = ttk.Combobox(selector, textvariable=self.polarity_var, state="readonly", width=12)
        self.polarity_cb.grid(row=0, column=3, sticky="w")
        self.polarity_cb.bind("<<ComboboxSelected>>", lambda e: self._rebuild_content())

        self.content = ttk.Frame(self, style="Tab.TFrame")
        self.content.grid(row=2, column=0, sticky="nsew", padx=0, pady=0)
        self.content.columnconfigure(0, weight=1, minsize=380)
        self.content.columnconfigure(1, weight=1, minsize=360)
        self.content.rowconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        self._update_polarity_options()
        self._rebuild_content()

    def _current_family(self):
        idx = self._family_labels.index(self.family_var.get())
        return FAMILIES[idx]

    def _current_polarity_key(self):
        family = self._current_family()
        labels = [lbl for lbl, _ in POLARITY_BY_FAMILY[family]]
        idx = self._polarity_labels.index(self.polarity_var.get())
        return labels[idx]

    def _update_polarity_options(self):
        family = self._current_family()
        opts = POLARITY_BY_FAMILY[family]
        self._polarity_labels = [t(key) for _, key in opts]
        self.polarity_cb.configure(values=self._polarity_labels)
        self.polarity_var.set(self._polarity_labels[0])

    def _on_family_change(self):
        self._update_polarity_options()
        self._rebuild_content()

    def _rebuild_content(self):
        if self._active_sim is not None:
            self._active_sim.stop()
            self._active_sim = None
        for child in self.content.winfo_children():
            child.destroy()

        family = self._current_family()
        polarity = self._current_polarity_key()

        left = ttk.Frame(self.content, style="Tab.TFrame")
        left.grid(row=0, column=0, sticky="nsew", padx=(20, 10), pady=10)
        left.columnconfigure(0, weight=1)
        left.rowconfigure(0, weight=1)
        right = ttk.Frame(self.content, style="Card.TFrame")
        right.grid(row=0, column=1, sticky="nsew", padx=(10, 20), pady=10)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(0, weight=1)

        nb = ttk.Notebook(left)
        nb.grid(row=0, column=0, sticky="nsew")

        vis_tab = ttk.Frame(nb, style="Card.TFrame")
        bias_tab = ttk.Frame(nb, style="Card.TFrame")
        circ_tab = ttk.Frame(nb, style="Card.TFrame")
        nb.add(vis_tab, text=t("transistor.subtab.visualizer"))
        nb.add(circ_tab, text=t("tc.tab"))
        nb.add(bias_tab, text=t("transistor.subtab.bias"))
        TransistorCircuitsPanel(circ_tab, family, polarity, ACCENT_C).pack(fill="both", expand=True)

        # Wrap each sub-tab's real content in a ScrollableFrame so that
        # sliders/parameters are never clipped when the window is
        # maximized/fullscreen or otherwise shorter than the content
        # (e.g. the bias calculator's circuit diagram + fields + result).
        vis_scroll = ScrollableFrame(vis_tab, style="Card.TFrame")
        vis_scroll.pack(fill="both", expand=True)
        bias_scroll = ScrollableFrame(bias_tab, style="Card.TFrame")
        bias_scroll.pack(fill="both", expand=True)

        self._build_visualizer(vis_scroll.body, family, polarity)
        self._build_bias_calculator(bias_scroll.body, family, polarity)

        chart_tab = ttk.Frame(nb, style="Card.TFrame")
        nb.add(chart_tab, text=t("transistor.subtab.chart"))
        chart_scroll = ScrollableFrame(chart_tab, style="Card.TFrame")
        chart_scroll.pack(fill="both", expand=True)
        self._build_chart(chart_scroll.body, family, polarity)

        right_scroll = ScrollableFrame(right, style="Card.TFrame")
        right_scroll.grid(row=0, column=0, sticky="nsew")
        SymbolGallery(right_scroll.body, family, accent=ACCENT_C).pack(fill="x", pady=(0, 8))
        theory = TheoryPanel(right_scroll.body, get_theory(THEORY_KEY[family]), accent=ACCENT_C)
        theory.pack(fill="both", expand=True)

    # ------------------------------------------------------------------
    # Junction visualizer
    # ------------------------------------------------------------------
    def _build_visualizer(self, parent, family, polarity):
        parent.columnconfigure(0, weight=1)
        viz = JunctionVisualizer(parent, family, polarity, ACCENT_C)
        viz.grid(row=0, column=0, sticky="nsew")
        self._active_sim = viz

    # ------------------------------------------------------------------
    # Bias / PSF calculator
    # ------------------------------------------------------------------
    def _build_bias_calculator(self, parent, family, polarity):
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        controls = ttk.Frame(parent, style="Card.TFrame")
        controls.grid(row=0, column=0, sticky="ns", padx=(16, 8), pady=16)

        ttk.Label(controls, text=t("bias.result_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        mode_var = tk.StringVar(value=t("bias.mode_analyze"))
        mode_cb = ttk.Combobox(controls, textvariable=mode_var,
                                values=[t("bias.mode_analyze"), t("bias.mode_design")],
                                state="readonly", width=26)
        mode_cb.grid(row=1, column=0, columnspan=2, sticky="w", pady=(0, 8))

        field_frame = ttk.Frame(controls, style="Card.TFrame")
        field_frame.grid(row=2, column=0, columnspan=2, sticky="w")
        field_vars = {}

        result_var = tk.StringVar()
        result_lbl = ttk.Label(controls, textvariable=result_var, font=FONT_MONO, foreground=ACCENT_C,
                                style="CardFormula.TLabel", justify="left", wraplength=280)
        result_lbl.grid(row=4, column=0, columnspan=2, sticky="w", pady=(10, 0))

        right_col = ttk.Frame(parent, style="Card.TFrame")
        right_col.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        right_col.columnconfigure(0, weight=1)
        right_col.rowconfigure(1, weight=1)

        circuit_canvas = tk.Canvas(right_col, width=460, height=340, bg="#fdfaf3", highlightthickness=0)
        circuit_canvas.grid(row=0, column=0, pady=(0, 8))

        # Redraw the diagram whenever the canvas is actually resized (e.g.
        # the window/pane changed size), so it always renders at its real
        # on-screen size instead of the original 460x340 design size.
        self._circuit_canvas_size = (460, 340)

        def _on_circuit_resize(event):
            new_size = (event.width, event.height)
            if new_size == self._circuit_canvas_size or event.width < 80 or event.height < 80:
                return
            self._circuit_canvas_size = new_size
            compute()

        circuit_canvas.bind("<Configure>", _on_circuit_resize)

        chart_wrap = ttk.Frame(right_col, style="Card.TFrame")
        chart_wrap.grid(row=1, column=0, sticky="nsew")
        chart = MplChartFrame(chart_wrap)
        chart.pack(fill="both", expand=True)

        is_n = polarity.lower() in ("npn", "n-channel")

        def field_specs():
            analyze = mode_var.get() == t("bias.mode_analyze")
            if family == "bjt":
                if analyze:
                    return [("vcc", "bias.vcc", "12"), ("r1", "bias.r1", "47k"), ("r2", "bias.r2", "10k"),
                            ("rc", "bias.rc", "2.2k"), ("re", "bias.re", "560"),
                            ("beta", "bias.beta", "100"), ("vbe", "bias.vbe", "0.7")]
                return [("vcc", "bias.vcc", "12"), ("ic_target", "bias.ic_target", "0.002"),
                        ("vce_target", "bias.vce_target", "6"), ("beta", "bias.beta", "100"),
                        ("vbe", "bias.vbe", "0.7")]
            if family == "mosfet":
                if analyze:
                    return [("vdd", "bias.vdd", "12"), ("r1", "bias.r1", "470k"), ("r2", "bias.r2", "220k"),
                            ("rd", "bias.rd", "1.8k"), ("rs", "bias.rs", "1.2k"),
                            ("vth", "bias.vth", "2" if is_n else "-2"), ("k", "bias.k", "0.0005")]
                return [("vdd", "bias.vdd", "12"), ("id_target", "bias.id_target", "0.002"),
                        ("vds_target", "bias.vds_target", "6"),
                        ("vth", "bias.vth", "2" if is_n else "-2"), ("k", "bias.k", "0.0005")]
            # jfet
            if analyze:
                return [("vdd", "bias.vdd", "12"), ("rd", "bias.rd", "1.5k"), ("rs", "bias.rs", "390"),
                        ("idss", "bias.idss", "0.01"), ("vp", "bias.vp", "-4" if is_n else "4")]
            return [("vdd", "bias.vdd", "12"), ("id_target", "bias.id_target", "0.004"),
                    ("vds_target", "bias.vds_target", "6"), ("idss", "bias.idss", "0.01"),
                    ("vp", "bias.vp", "-4" if is_n else "4")]

        def rebuild_fields():
            for c in field_frame.winfo_children():
                c.destroy()
            field_vars.clear()
            for i, (key, label_key, default) in enumerate(field_specs()):
                ttk.Label(field_frame, text=t(label_key), font=FONT_BODY, style="CardBody.TLabel")\
                    .grid(row=i, column=0, sticky="w", pady=3)
                var = tk.StringVar(value=default)
                entry = ttk.Entry(field_frame, textvariable=var, width=10)
                entry.grid(row=i, column=1, pady=3, padx=(6, 0))
                entry.bind("<KeyRelease>", lambda e: compute())
                field_vars[key] = var
            compute()

        def region_label(region):
            return {
                "active": t("bias.region.active"), "saturation": t("bias.region.saturation"),
                "cutoff": t("bias.region.cutoff"), "triode": t("bias.region.triode"),
            }.get(region, region)

        def draw_curve_family(ax, curves):
            """The family of characteristic curves (Ic-Vce or Id-Vds at a
            few different Ib/Vgs values) behind the load line - the actual
            operating curve (the one that passes exactly through the
            Q-point) is drawn bolder than its neighbors."""
            for c in curves:
                is_q = c["is_q_curve"]
                ax.plot(c["x"], [y * 1000 for y in c["y"]],
                        color="#2e7d32" if is_q else "#8fbf8a",
                        linewidth=2.0 if is_q else 1.1, zorder=2)

        def compute():
            try:
                kw = {k: parse_value(v.get()) for k, v in field_vars.items()}
            except Exception:
                result_var.set(t("bias.enter_valid"))
                return
            analyze = mode_var.get() == t("bias.mode_analyze")
            # Draw the circuit at whatever size Tk actually gave the canvas
            # (it shrinks under horizontal space pressure), not a hardcoded
            # 460x340 - draw_*_bias_circuit already scales its layout to
            # any w/h, so this keeps the whole diagram visible instead of
            # letting the excess get silently clipped off the right edge.
            cw, ch = circuit_canvas.winfo_width(), circuit_canvas.winfo_height()
            if cw < 80 or ch < 80:
                cw, ch = 460, 340
            chart.clear()
            ax = chart.fig.add_subplot(111)
            ax.set_facecolor(PLOT_BG)

            try:
                if family == "bjt":
                    if analyze:
                        q = bias.bjt_analyze(kw["vcc"], kw["r1"], kw["r2"], kw["rc"], kw["re"],
                                              kw["beta"], kw["vbe"])
                        vx, iy = bias.bjt_load_line(kw["vcc"], kw["rc"], kw["re"])
                        text = (f"Ib = {q['ib']*1e6:.2f} µA\nIc = {q['ic']*1000:.3f} mA\n"
                                f"Ie = {q['ie']*1000:.3f} mA\nVb = {q['vb']:.2f} V  Ve = {q['ve']:.2f} V  "
                                f"Vc = {q['vc']:.2f} V\nVce = {q['vce']:.2f} V\n"
                                f"{t('bias.region_prefix')} {region_label(q['region'])}")
                        qx, qy = q["vce"], q["ic"] * 1000
                        draw_bjt_bias_circuit(circuit_canvas, kind=polarity,
                                               r1_text=f"R1\n{format_value(kw['r1'], 'Ω')}",
                                               r2_text=f"R2\n{format_value(kw['r2'], 'Ω')}",
                                               rc_text=f"Rc\n{format_value(kw['rc'], 'Ω')}",
                                               re_text=f"Re\n{format_value(kw['re'], 'Ω')}",
                                               w=cw, h=ch)
                    else:
                        d = bias.bjt_design(kw["vcc"], kw["ic_target"], kw["vce_target"], kw["beta"], kw["vbe"])
                        vx, iy = bias.bjt_load_line(kw["vcc"], d["rc"], d["re"])
                        text = (f"{t('bias.suggested_components')}\nR1 = {d['r1']:.0f} Ω   "
                                f"R2 = {d['r2']:.0f} Ω\nRc = {d['rc']:.0f} Ω   Re = {d['re']:.0f} Ω\n"
                                f"{t('bias.design_heuristics_note')}")
                        qx, qy = kw["vce_target"], kw["ic_target"] * 1000
                        draw_bjt_bias_circuit(circuit_canvas, kind=polarity,
                                               r1_text=f"R1\n{format_value(d['r1'], 'Ω')}",
                                               r2_text=f"R2\n{format_value(d['r2'], 'Ω')}",
                                               rc_text=f"Rc\n{format_value(d['rc'], 'Ω')}",
                                               re_text=f"Re\n{format_value(d['re'], 'Ω')}",
                                               w=cw, h=ch)
                    ax.set_xlabel("Vce (V)")
                    ax.set_ylabel("Ic (mA)")
                    ib_q = q["ib"] if analyze else d["ib"]
                    draw_curve_family(ax, bias.bjt_characteristic_curves(kw["beta"], ib_q, vx[1]))
                    ax.plot(vx, [v * 1000 for v in iy], color=V_COLOR, linewidth=2, zorder=3)
                elif family == "mosfet":
                    if analyze:
                        q = bias.mosfet_analyze(kw["vdd"], kw["r1"], kw["r2"], kw["rd"], kw["rs"],
                                                 kw["vth"], kw["k"], nchannel=is_n)
                        vx, iy = bias.mosfet_load_line(kw["vdd"], kw["rd"], kw["rs"])
                        text = (f"Id = {q['id']*1000:.3f} mA\nVgs = {q['vgs']:.2f} V   "
                                f"Vds = {q['vds']:.2f} V\nVg = {q['vg']:.2f} V\n"
                                f"{t('bias.region_prefix')} {region_label(q['region'])}")
                        qx, qy = abs(q["vds"]), q["id"] * 1000
                        draw_mosfet_bias_circuit(circuit_canvas, kind=polarity,
                                                  r1_text=f"R1\n{format_value(kw['r1'], 'Ω')}",
                                                  r2_text=f"R2\n{format_value(kw['r2'], 'Ω')}",
                                                  rd_text=f"Rd\n{format_value(kw['rd'], 'Ω')}",
                                                  rs_text=f"Rs\n{format_value(kw['rs'], 'Ω')}",
                                                  w=cw, h=ch)
                    else:
                        d = bias.mosfet_design(kw["vdd"], kw["id_target"], kw["vds_target"], kw["vth"],
                                                kw["k"], nchannel=is_n)
                        vx, iy = bias.mosfet_load_line(kw["vdd"], d["rd"], d["rs"])
                        text = (f"{t('bias.suggested_components')}\nR1 = {d['r1']:.0f} Ω   "
                                f"R2 = {d['r2']:.0f} Ω\nRd = {d['rd']:.0f} Ω   Rs = {d['rs']:.0f} Ω\n"
                                f"Vgs = {d['vgs']:.2f} V")
                        qx, qy = kw["vds_target"], kw["id_target"] * 1000
                        draw_mosfet_bias_circuit(circuit_canvas, kind=polarity,
                                                  r1_text=f"R1\n{format_value(d['r1'], 'Ω')}",
                                                  r2_text=f"R2\n{format_value(d['r2'], 'Ω')}",
                                                  rd_text=f"Rd\n{format_value(d['rd'], 'Ω')}",
                                                  rs_text=f"Rs\n{format_value(d['rs'], 'Ω')}",
                                                  w=cw, h=ch)
                    ax.set_xlabel("Vds (V)")
                    ax.set_ylabel("Id (mA)")
                    vgs_q = q["vgs"] if analyze else d["vgs"]
                    vov_q = abs(vgs_q) - abs(kw["vth"])
                    draw_curve_family(ax, bias.mosfet_characteristic_curves(kw["k"], vov_q, vx[1]))
                    ax.plot(vx, [v * 1000 for v in iy], color=V_COLOR, linewidth=2, zorder=3)
                else:
                    if analyze:
                        q = bias.jfet_analyze(kw["vdd"], kw["rd"], kw["rs"], kw["idss"], kw["vp"], nchannel=is_n)
                        vx, iy = bias.jfet_load_line(kw["vdd"], kw["rd"], kw["rs"])
                        text = (f"Id = {q['id']*1000:.3f} mA\nVgs = {q['vgs']:.2f} V   "
                                f"Vds = {q['vds']:.2f} V\n{t('bias.region_prefix')} {region_label(q['region'])}")
                        qx, qy = abs(q["vds"]), q["id"] * 1000
                        draw_jfet_bias_circuit(circuit_canvas, kind=polarity,
                                                rd_text=f"Rd\n{format_value(kw['rd'], 'Ω')}",
                                                rs_text=f"Rs\n{format_value(kw['rs'], 'Ω')}",
                                                w=cw, h=ch)
                    else:
                        d = bias.jfet_design(kw["vdd"], kw["id_target"], kw["vds_target"], kw["idss"], kw["vp"])
                        vx, iy = bias.jfet_load_line(kw["vdd"], d["rd"], d["rs"])
                        text = (f"{t('bias.suggested_components')}\nRd = {d['rd']:.0f} Ω   "
                                f"Rs = {d['rs']:.0f} Ω\nVgs = {d['vgs']:.2f} V")
                        qx, qy = kw["vds_target"], kw["id_target"] * 1000
                        draw_jfet_bias_circuit(circuit_canvas, kind=polarity,
                                                rd_text=f"Rd\n{format_value(d['rd'], 'Ω')}",
                                                rs_text=f"Rs\n{format_value(d['rs'], 'Ω')}",
                                                w=cw, h=ch)
                    ax.set_xlabel("Vds (V)")
                    ax.set_ylabel("Id (mA)")
                    vgs_q = q["vgs"] if analyze else d["vgs"]
                    vp_m = abs(kw["vp"])
                    ratio_q = max(0.0, min(1.0, 1 - abs(vgs_q) / vp_m)) if vp_m > 0 else 0.0
                    draw_curve_family(ax, bias.jfet_characteristic_curves(kw["idss"], vp_m, ratio_q, vx[1]))
                    ax.plot(vx, [v * 1000 for v in iy], color=V_COLOR, linewidth=2, zorder=3)

                ax.plot([qx], [qy], "o", color="#c0392b", markersize=9, zorder=5)
                ax.annotate(t("bias.qpoint_label"), (qx, qy), textcoords="offset points",
                            xytext=(8, 8), fontsize=9, color="#c0392b", fontweight="bold")
                ax.set_title(t("bias.load_line_title"), fontsize=11)
                ax.grid(True, alpha=0.25)
                include_zero(ax, axis="x")
                include_zero(ax, axis="y")
                chart.fig.tight_layout()
                chart.redraw()
                result_var.set(text)
            except Exception as exc:
                result_var.set(f"{t('common.could_not_compute')}: {exc}")

        mode_cb.bind("<<ComboboxSelected>>", lambda e: rebuild_fields())
        rebuild_fields()

    # ------------------------------------------------------------------
    # BJT switch / amplifier chart (unchanged behavior from before)
    # ------------------------------------------------------------------
    def _build_chart(self, parent, family, polarity):
        self._chart_family = family
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        controls = ttk.Frame(parent, style="Card.TFrame")
        controls.grid(row=0, column=0, sticky="ns", padx=(16, 8), pady=16)

        ttk.Label(controls, text=t("transistor.chart.title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 8))

        ttk.Label(controls, text=t("common.mode"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=1, column=0, sticky="w", pady=4)
        self.mode = tk.StringVar(value="AC")
        mode_cb = ttk.Combobox(controls, textvariable=self.mode, values=["AC", "DC"],
                                state="readonly", width=8)
        mode_cb.grid(row=1, column=1, sticky="w", pady=4)
        mode_cb.bind("<<ComboboxSelected>>", lambda e: self._rebuild_fields())
        ttk.Label(controls, text=t("transistor.chart.mode_hint"),
                  font=("Segoe UI", 8), style="CardBody.TLabel")\
            .grid(row=2, column=0, columnspan=2, sticky="w")

        self.field_frame = ttk.Frame(controls, style="Card.TFrame")
        self.field_frame.grid(row=3, column=0, columnspan=2, sticky="w", pady=6)
        self.field_vars = {}

        ttk.Button(controls, text=t("common.simulate"), command=self._simulate)\
            .grid(row=4, column=0, columnspan=2, pady=(10, 6), sticky="ew")

        self.note_var = tk.StringVar()
        ttk.Label(controls, textvariable=self.note_var, font=("Segoe UI", 9), foreground=ACCENT_C,
                  style="CardBody.TLabel", wraplength=220, justify="left")\
            .grid(row=5, column=0, columnspan=2, sticky="w", pady=(4, 0))

        chart_wrap = ttk.Frame(parent, style="Card.TFrame")
        chart_wrap.grid(row=0, column=1, sticky="nsew", padx=(8, 16), pady=16)
        self.chart = MplChartFrame(chart_wrap)
        self.chart.pack(fill="both", expand=True)

        self._rebuild_fields()

    def _rebuild_fields(self):
        for child in self.field_frame.winfo_children():
            child.destroy()
        self.field_vars = {}
        family = self._chart_family
        is_dc = self.mode.get() == "DC"

        if family == "bjt":
            if is_dc:
                fields = [("vin_high", t("transistor.chart.dc_vin_high"), "5"),
                          ("vbe", t("transistor.chart.dc_vbe"), "0.7"),
                          ("beta", t("transistor.chart.dc_beta"), "100"),
                          ("rb", t("transistor.chart.dc_rb"), "1000"),
                          ("rc", t("transistor.chart.dc_rc"), "220"),
                          ("vcc", t("transistor.chart.dc_vcc"), "5"),
                          ("frequency", t("transistor.chart.dc_freq"), "200")]
            else:
                fields = [("vin_amp", t("transistor.chart.ac_vin_amp"), "0.05"),
                          ("frequency", t("common.frequency"), "1000"),
                          ("gain", t("transistor.chart.ac_gain"), "50"),
                          ("vcc", t("transistor.chart.ac_vcc"), "5")]
        elif family == "mosfet":
            if is_dc:
                fields = [("vgs_high", t("transistor.chart.dc_vgs_high"), "5"),
                          ("vth", t("transistor.chart.dc_vth"), "2"),
                          ("k", t("transistor.chart.dc_k"), "0.0005"),
                          ("rd", t("transistor.chart.dc_rd"), "220"),
                          ("vdd", t("transistor.chart.dc_vdd"), "5"),
                          ("frequency", t("transistor.chart.dc_freq"), "200")]
            else:
                fields = [("vin_amp", t("transistor.chart.ac_vin_amp"), "0.05"),
                          ("frequency", t("common.frequency"), "1000"),
                          ("gain", t("transistor.chart.ac_gm"), "10"),
                          ("vdd", t("transistor.chart.ac_vdd"), "5")]
        else:  # jfet
            if is_dc:
                fields = [("vgs_pinch", t("transistor.chart.dc_vgs_pinch"), "-4"),
                          ("idss", t("transistor.chart.dc_idss"), "0.01"),
                          ("vp", t("transistor.chart.dc_vp"), "-4"),
                          ("rd", t("transistor.chart.dc_rd"), "220"),
                          ("vdd", t("transistor.chart.dc_vdd"), "5"),
                          ("frequency", t("transistor.chart.dc_freq"), "200")]
            else:
                fields = [("vin_amp", t("transistor.chart.ac_vin_amp"), "0.05"),
                          ("frequency", t("common.frequency"), "1000"),
                          ("gain", t("transistor.chart.ac_gm"), "5"),
                          ("vdd", t("transistor.chart.ac_vdd"), "5")]

        for i, (key, label, default) in enumerate(fields):
            ttk.Label(self.field_frame, text=label, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=i, column=0, sticky="w", pady=3)
            var = tk.StringVar(value=default)
            ttk.Entry(self.field_frame, textvariable=var, width=10).grid(row=i, column=1, pady=3, padx=(6, 0))
            self.field_vars[key] = var
        self._simulate()

    def _simulate(self):
        try:
            kwargs = {key: parse_value(var.get()) for key, var in self.field_vars.items()}
        except Exception:
            self.note_var.set(t("common.enter_valid_values"))
            return

        family = self._chart_family
        is_dc = self.mode.get() == "DC"
        self.chart.clear()
        ax1 = self.chart.fig.add_subplot(111)
        ax1.set_facecolor(PLOT_BG)

        if family == "bjt":
            if is_dc:
                t_arr, vin, vout, _ = transistor_switch(**kwargs)
                legend_in, legend_out = t("transistor.chart.legend_vin_base"), t("transistor.chart.legend_vout_collector")
                title, note = t("transistor.chart.dc_title"), t("transistor.chart.dc_note")
            else:
                t_arr, vin, vout = transistor_amplifier(**kwargs)
                legend_in, legend_out = t("transistor.chart.legend_vin"), t("transistor.chart.legend_vout")
                title, note = t("transistor.chart.ac_title"), t("transistor.chart.ac_note")
        elif family == "mosfet":
            if is_dc:
                t_arr, vin, vout, _ = mosfet_switch(**kwargs)
                legend_in, legend_out = t("transistor.chart.legend_vin_gate"), t("transistor.chart.legend_vout_drain")
                title, note = t("transistor.chart.mosfet_dc_title"), t("transistor.chart.mosfet_dc_note")
            else:
                t_arr, vin, vout = mosfet_amplifier(**kwargs)
                legend_in, legend_out = t("transistor.chart.legend_vin"), t("transistor.chart.legend_vout")
                title, note = t("transistor.chart.mosfet_ac_title"), t("transistor.chart.mosfet_ac_note")
        else:  # jfet
            if is_dc:
                t_arr, vin, vout, _ = jfet_switch(**kwargs)
                legend_in, legend_out = t("transistor.chart.legend_vin_gate"), t("transistor.chart.legend_vout_drain")
                title, note = t("transistor.chart.jfet_dc_title"), t("transistor.chart.jfet_dc_note")
            else:
                t_arr, vin, vout = jfet_amplifier(**kwargs)
                legend_in, legend_out = t("transistor.chart.legend_vin"), t("transistor.chart.legend_vout")
                title, note = t("transistor.chart.jfet_ac_title"), t("transistor.chart.jfet_ac_note")

        ax1.plot(t_arr, vin, color=V_COLOR, linewidth=1.5, label=legend_in)
        ax1.plot(t_arr, vout, color="#2A9D8F", linewidth=2, label=legend_out)
        ax1.set_xlabel(t("common.time_s"))
        ax1.set_ylabel(t("common.voltage"))
        ax1.legend(loc="upper right", fontsize=8)
        ax1.set_title(title, fontsize=11)
        ax1.grid(True, alpha=0.25)
        include_zero(ax1)

        self.chart.fig.tight_layout()
        self.chart.redraw()
        self.note_var.set(note)


class _FloatProxy:
    """Lightweight stand-in so entry-based device parameters (Vth, Vp) can be
    read with the same .get() interface as the tk.DoubleVar sliders."""
    def __init__(self, value):
        self._value = value

    def get(self):
        return self._value
