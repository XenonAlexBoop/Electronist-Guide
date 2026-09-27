import math
import tkinter as tk
from tkinter import ttk

from drawing import draw_divider_diagram
from widgets import parse_value, format_value, ScrollableFrame, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO
from charts import (MplChartFrame, divider_ac_signals, divider_dc_signals,
                     divider_ac_signals2, divider_dc_signals2, divider_ac_am_signals,
                     V_COLOR, I_COLOR, PLOT_BG, include_zero)
from i18n import t

ACCENT_C = "#8854d0"

KIND_KEYS = [("resistor", "comp.resistor"), ("capacitor", "comp.capacitor"), ("inductor", "comp.inductor")]
DEFAULT_BY_KIND = {"resistor": "1k", "capacitor": "100n", "inductor": "10m"}


class _DividerFilterBase(ttk.Frame):
    """Shared 2-element (series + shunt) network engine used by both the
    Voltage Divider tool (Resistors tab) and the Filter tool (Signals tab).
    A pure resistor/resistor pair behaves as a classic voltage divider;
    mixing in a capacitor or inductor turns the same network into a filter."""

    def __init__(self, parent, *, show_title=True, title_key="divider.tab_title",
                 intro_key="divider.intro", default_series_idx=0, default_shunt_idx=1,
                 resistor_only=False):
        super().__init__(parent, style="Tab.TFrame" if show_title else "Card.TFrame")
        self._ready = False
        self._intro_key = intro_key
        self._default_series_idx = default_series_idx
        self._default_shunt_idx = default_shunt_idx
        self._resistor_only = resistor_only
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)

        row = 0
        if show_title:
            ttk.Label(self, text=t(title_key), font=FONT_H1, style="TabTitle.TLabel")\
                .grid(row=0, column=0, columnspan=2, sticky="w", padx=20, pady=(16, 6))
            row = 1
        self.rowconfigure(row, weight=1)
        pad_x_left = (20, 10) if show_title else (10, 10)
        pad_x_right = (10, 20) if show_title else (10, 10)

        left_wrap = ttk.Frame(self, style="Card.TFrame")
        left_wrap.grid(row=row, column=0, sticky="nsew", padx=pad_x_left, pady=10)
        left_wrap.columnconfigure(0, weight=1)
        left_wrap.rowconfigure(0, weight=1)
        right = ttk.Frame(self, style="Card.TFrame")
        right.grid(row=row, column=1, sticky="nsew", padx=pad_x_right, pady=10)
        right.columnconfigure(0, weight=1)
        right.rowconfigure(1, weight=1)

        # Scrollable so the (optional) component calculator added below the
        # core network controls never ends up hidden off the bottom edge.
        left_scroll = ScrollableFrame(left_wrap, style="Card.TFrame")
        left_scroll.grid(row=0, column=0, sticky="nsew")
        left = left_scroll.body

        self._build_chart(right)
        self._build_controls(left)
        self._ready = True
        self._simulate()

    # ------------------------------------------------------------------
    def _build_stage_card(self, container, column, title_key, series_kind_attr, series_val_attr,
                           shunt_kind_attr, shunt_val_attr, default_series_idx=0, default_shunt_idx=1):
        card = ttk.Frame(container, style="Card.TFrame")
        card.grid(row=0, column=column, sticky="new", padx=6)
        type_labels = [t(key) for _, key in KIND_KEYS]
        resistor_only = self._resistor_only

        ttk.Label(card, text=t(title_key), font=FONT_H2, foreground=ACCENT_C, style="CardSub.TLabel")\
            .grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 6))

        row = 1
        # ---- Series element (R1) ----
        pos = 1 if column == 0 else 3
        series_header = t("divider.r1_label") if resistor_only else f"#{pos}  {t('divider.series_element')}"
        ttk.Label(card, text=series_header, font=("Segoe UI", 9, "bold"),
                  style="CardBody.TLabel").grid(row=row, column=0, columnspan=2, sticky="w", pady=(4, 2))
        row += 1
        if resistor_only:
            s_kind = tk.StringVar(value=type_labels[0])  # fixed: resistor
        else:
            ttk.Label(card, text=t("divider.type_label"), font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=row, column=0, sticky="w")
            s_kind = tk.StringVar(value=type_labels[default_series_idx])
            cb1 = ttk.Combobox(card, textvariable=s_kind, values=type_labels, state="readonly", width=11)
            cb1.grid(row=row, column=1, sticky="w", pady=3)
            cb1.bind("<<ComboboxSelected>>", lambda e: self._on_type_change())
            row += 1
        setattr(self, series_kind_attr, s_kind)
        value_label = t("divider.r_value_label") if resistor_only else t("divider.value_label")
        ttk.Label(card, text=value_label, font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=row, column=0, sticky="w")
        s_val = tk.StringVar(value=DEFAULT_BY_KIND[KIND_KEYS[default_series_idx][0]])
        e1 = ttk.Entry(card, textvariable=s_val, width=11)
        e1.grid(row=row, column=1, sticky="w", pady=3)
        e1.bind("<KeyRelease>", lambda e: self._simulate())
        setattr(self, series_val_attr, s_val)
        row += 1

        # ---- Shunt element (R2) ----
        shunt_header = t("divider.r2_label") if resistor_only else f"#{pos + 1}  {t('divider.shunt_element')}"
        ttk.Label(card, text=shunt_header, font=("Segoe UI", 9, "bold"),
                  style="CardBody.TLabel").grid(row=row, column=0, columnspan=2, sticky="w", pady=(8, 2))
        row += 1
        if resistor_only:
            p_kind = tk.StringVar(value=type_labels[0])  # fixed: resistor
        else:
            ttk.Label(card, text=t("divider.type_label"), font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=row, column=0, sticky="w")
            p_kind = tk.StringVar(value=type_labels[default_shunt_idx])
            cb2 = ttk.Combobox(card, textvariable=p_kind, values=type_labels, state="readonly", width=11)
            cb2.grid(row=row, column=1, sticky="w", pady=3)
            cb2.bind("<<ComboboxSelected>>", lambda e: self._on_type_change())
            row += 1
        setattr(self, shunt_kind_attr, p_kind)
        ttk.Label(card, text=value_label, font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=row, column=0, sticky="w")
        p_val = tk.StringVar(value=DEFAULT_BY_KIND[KIND_KEYS[default_shunt_idx][0]])
        e2 = ttk.Entry(card, textvariable=p_val, width=11)
        e2.grid(row=row, column=1, sticky="w", pady=3)
        e2.bind("<KeyRelease>", lambda e: self._simulate())
        setattr(self, shunt_val_attr, p_val)
        return card

    def _build_controls(self, parent):
        pad = {"padx": 16, "pady": 6}
        parent.columnconfigure(0, weight=1)

        ttk.Label(parent, text=t(self._intro_key), font=FONT_BODY, wraplength=380,
                  justify="left", style="CardBody.TLabel").grid(row=0, column=0, sticky="w", **pad)

        self.canvas = tk.Canvas(parent, width=420, height=220, bg="#fdfaf3", highlightthickness=0)
        self.canvas.grid(row=1, column=0, padx=16, pady=6, sticky="w")
        self._diagram_avail_w = 420
        # The ScrollableFrame forces `parent` to exactly the visible viewport
        # width (see widgets.ScrollableFrame) so it can report real, current
        # room for the diagram; add="+" so we don't clobber its own binding.
        parent.bind("<Configure>", self._on_left_resize, add="+")

        self._type_labels = [t(key) for _, key in KIND_KEYS]
        self._type_kinds = [k for k, _ in KIND_KEYS]

        self.stages_row = ttk.Frame(parent, style="Card.TFrame")
        self.stages_row.grid(row=2, column=0, sticky="ew", padx=10)
        self.stages_row.columnconfigure(0, weight=1)
        self.stages_row.columnconfigure(1, weight=1)

        self._build_stage_card(self.stages_row, 0, "divider.stage1",
                                "series_type", "series_value", "shunt_type", "shunt_value",
                                default_series_idx=self._default_series_idx,
                                default_shunt_idx=self._default_shunt_idx)

        self.stage2_on = tk.BooleanVar(value=False)
        stage2_text = t("divider.add_stage2_resistive") if self._resistor_only else t("divider.add_stage2")
        chk = ttk.Checkbutton(parent, text=stage2_text, variable=self.stage2_on,
                               command=self._toggle_stage2)
        chk.grid(row=3, column=0, sticky="w", padx=16, pady=(10, 4))

        ttk.Label(parent, text=t("divider.stage2_intro"), font=("Segoe UI", 9), wraplength=380,
                  justify="left", style="CardBody.TLabel").grid(row=4, column=0, sticky="w", padx=16)

        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=5, column=0, sticky="ew", padx=16, pady=10)

        ttk.Label(parent, text=t("divider.formula_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=6, column=0, sticky="w", padx=16)
        if self._resistor_only:
            ttk.Label(parent, text=t("divider.formula_resistive"), font=("Consolas", 10, "bold"), foreground=ACCENT_C,
                      style="CardFormula.TLabel", wraplength=380, justify="left")\
                .grid(row=7, column=0, sticky="w", padx=16, pady=(4, 10))
        else:
            ttk.Label(parent, text=t("divider.formula_ac"), font=("Consolas", 10, "bold"), foreground=ACCENT_C,
                      style="CardFormula.TLabel", wraplength=380, justify="left")\
                .grid(row=7, column=0, sticky="w", padx=16, pady=(4, 0))
            ttk.Label(parent, text=t("divider.formula_impedances"), font=("Consolas", 10, "bold"), foreground=ACCENT_C,
                      style="CardFormula.TLabel", wraplength=380, justify="left")\
                .grid(row=8, column=0, sticky="w", padx=16, pady=(2, 10))

        self._on_type_change()

        if not self._resistor_only:
            self._build_component_calculator(parent, start_row=9)

    # ------------------------------------------------------------------
    # Component Calculator: pick a filter topology + target cutoff freq,
    # fix one component, solve for the other(s).
    # ------------------------------------------------------------------
    CALC_TYPES = [
        ("rc_lp", "filter.calc.type.rc_lp"), ("rc_hp", "filter.calc.type.rc_hp"),
        ("rl_lp", "filter.calc.type.rl_lp"), ("rl_hp", "filter.calc.type.rl_hp"),
        ("rlc_bp", "filter.calc.type.rlc_bp"), ("rlc_bs", "filter.calc.type.rlc_bs"),
    ]

    def _build_component_calculator(self, parent, start_row):
        pad = {"padx": 16, "pady": 4}
        row = start_row

        sep = ttk.Separator(parent, orient="horizontal")
        sep.grid(row=row, column=0, sticky="ew", padx=16, pady=10)
        row += 1

        ttk.Label(parent, text=t("filter.calc_title"), font=FONT_H2, foreground=ACCENT_C,
                  style="CardSub.TLabel").grid(row=row, column=0, sticky="w", **pad)
        row += 1
        ttk.Label(parent, text=t("filter.calc_intro"), font=("Segoe UI", 9), wraplength=380,
                  justify="left", style="CardBody.TLabel").grid(row=row, column=0, sticky="w", padx=16)
        row += 1

        self._calc_type_labels = [t(key) for _, key in self.CALC_TYPES]
        self._calc_type_kinds = [k for k, _ in self.CALC_TYPES]
        ttk.Label(parent, text=t("filter.calc_type_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=row, column=0, sticky="w", padx=16, pady=(6, 0))
        row += 1
        self.calc_type_var = tk.StringVar(value=self._calc_type_labels[0])
        calc_cb = ttk.Combobox(parent, textvariable=self.calc_type_var, values=self._calc_type_labels,
                                state="readonly", width=22)
        calc_cb.grid(row=row, column=0, sticky="w", padx=16)
        calc_cb.bind("<<ComboboxSelected>>", lambda e: self._on_calc_type_change())
        row += 1

        ttk.Label(parent, text=t("filter.calc_cutoff_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=row, column=0, sticky="w", padx=16, pady=(6, 0))
        row += 1
        self.calc_fc_var = tk.StringVar(value="1000")
        ttk.Entry(parent, textvariable=self.calc_fc_var, width=14).grid(row=row, column=0, sticky="w", padx=16)
        row += 1

        self._calc_known_labels = [t("filter.calc_r_label"), t("filter.calc_l_label"), t("filter.calc_c_label")]
        ttk.Label(parent, text=t("filter.calc_known_label"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=row, column=0, sticky="w", padx=16, pady=(6, 0))
        row += 1
        self.calc_known_var = tk.StringVar(value=self._calc_known_labels[0])
        self.calc_known_cb = ttk.Combobox(parent, textvariable=self.calc_known_var,
                                           values=self._calc_known_labels, state="readonly", width=14)
        self.calc_known_cb.grid(row=row, column=0, sticky="w", padx=16)
        self.calc_known_cb.bind("<<ComboboxSelected>>", lambda e: self._on_calc_known_change())
        row += 1

        self.calc_known_val_label = tk.StringVar(value=self._calc_known_labels[0])
        ttk.Label(parent, textvariable=self.calc_known_val_label, font=("Segoe UI", 9), style="CardBody.TLabel")\
            .grid(row=row, column=0, sticky="w", padx=16, pady=(6, 0))
        row += 1
        self.calc_known_val_var = tk.StringVar(value="1k")
        ttk.Entry(parent, textvariable=self.calc_known_val_var, width=14)\
            .grid(row=row, column=0, sticky="w", padx=16)
        row += 1

        self.calc_q_label_widget = ttk.Label(parent, text=t("filter.calc_q_label"), font=FONT_BODY,
                                              style="CardBody.TLabel")
        self.calc_q_label_widget.grid(row=row, column=0, sticky="w", padx=16, pady=(6, 0))
        row += 1
        self.calc_q_var = tk.StringVar(value="2.0")
        self.calc_q_entry = ttk.Entry(parent, textvariable=self.calc_q_var, width=14)
        self.calc_q_entry.grid(row=row, column=0, sticky="w", padx=16)
        row += 1

        btn_row = ttk.Frame(parent, style="Card.TFrame")
        btn_row.grid(row=row, column=0, sticky="w", padx=16, pady=(8, 4))
        ttk.Button(btn_row, text=t("filter.calc_button"), command=self._calc_solve).pack(side="left", padx=(0, 8))
        self.calc_apply_btn = ttk.Button(btn_row, text=t("filter.calc_apply_button"), command=self._calc_apply,
                                          state="disabled")
        self.calc_apply_btn.pack(side="left")
        row += 1

        self.calc_result_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.calc_result_var, font=FONT_MONO, foreground=ACCENT_C,
                  style="CardFormula.TLabel", justify="left", wraplength=380)\
            .grid(row=row, column=0, sticky="w", padx=16, pady=(4, 16))

        self._calc_result = None
        self._on_calc_type_change()

    def _on_calc_type_change(self):
        kind = self._calc_type_kinds[self._calc_type_labels.index(self.calc_type_var.get())]
        if kind.startswith("rlc"):
            values = [t("filter.calc_r_label")]
        else:
            values = [t("filter.calc_r_label"), (t("filter.calc_c_label") if "rc" in kind else t("filter.calc_l_label"))]
        self.calc_known_cb.configure(values=values)
        if self.calc_known_var.get() not in values:
            self.calc_known_var.set(values[0])
        if kind.startswith("rlc"):
            self.calc_q_label_widget.grid()
            self.calc_q_entry.grid()
        else:
            self.calc_q_label_widget.grid_remove()
            self.calc_q_entry.grid_remove()
        self.calc_apply_btn.configure(state="disabled")
        self.calc_result_var.set("")
        self._on_calc_known_change()

    def _on_calc_known_change(self):
        self.calc_known_val_label.set(self.calc_known_var.get())

    def _calc_solve(self):
        kind = self._calc_type_kinds[self._calc_type_labels.index(self.calc_type_var.get())]
        known_label = self.calc_known_var.get()
        try:
            fc = parse_value(self.calc_fc_var.get())
            known_val = parse_value(self.calc_known_val_var.get())
        except Exception:
            self.calc_result_var.set(t("filter.calc_invalid"))
            self.calc_apply_btn.configure(state="disabled")
            return
        if fc <= 0 or known_val <= 0:
            self.calc_result_var.set(t("filter.calc_invalid"))
            self.calc_apply_btn.configure(state="disabled")
            return

        w = 2 * math.pi * fc
        try:
            if kind in ("rc_lp", "rc_hp"):
                if known_label == t("filter.calc_r_label"):
                    r = known_val
                    c = 1 / (w * r)
                else:
                    c = known_val
                    r = 1 / (w * c)
                result_kind = "rc"
                l = None
            elif kind in ("rl_lp", "rl_hp"):
                if known_label == t("filter.calc_r_label"):
                    r = known_val
                    l = r / w
                else:
                    l = known_val
                    r = l * w
                result_kind = "rl"
                c = None
            elif kind == "rlc_bp":
                # Series RLC band-pass, output taken across R.
                # f0 = 1/(2*pi*sqrt(L*C));  Q = w0*L/R  =>  L = Q*R/w0
                try:
                    q = parse_value(self.calc_q_var.get())
                except Exception:
                    q = 2.0
                if q <= 0:
                    q = 2.0
                r = known_val
                l = (q * r) / w
                c = 1 / (w * w * l)
                result_kind = "rlc_bp"
            else:  # rlc_bs - parallel L||C notch/trap in series with the load R.
                # f0 = 1/(2*pi*sqrt(L*C));  Q = R/(w0*L) = w0*R*C  =>  L = R/(Q*w0)
                try:
                    q = parse_value(self.calc_q_var.get())
                except Exception:
                    q = 2.0
                if q <= 0:
                    q = 2.0
                r = known_val
                l = r / (q * w)
                c = 1 / (w * w * l)
                result_kind = "rlc_bs"
        except ZeroDivisionError:
            self.calc_result_var.set(t("filter.calc_invalid"))
            self.calc_apply_btn.configure(state="disabled")
            return

        if result_kind == "rc":
            self.calc_result_var.set(f"R = {format_value(r, 'Ω')}      C = {format_value(c, 'F')}")
            self._calc_result = ("resistor", r, "capacitor", c) if kind == "rc_lp" else ("capacitor", c, "resistor", r)
            self.calc_apply_btn.configure(state="normal")
        elif result_kind == "rl":
            self.calc_result_var.set(f"R = {format_value(r, 'Ω')}      L = {format_value(l, 'H')}")
            self._calc_result = ("inductor", l, "resistor", r) if kind == "rl_lp" else ("resistor", r, "inductor", l)
            self.calc_apply_btn.configure(state="normal")
        elif result_kind == "rlc_bp":
            self.calc_result_var.set(
                f"R = {format_value(r, 'Ω')}      L = {format_value(l, 'H')}      "
                f"C = {format_value(c, 'F')}\n{t('filter.calc_rlc_bp_note')}")
            self._calc_result = None
            self.calc_apply_btn.configure(state="disabled")
        else:  # rlc_bs
            self.calc_result_var.set(
                f"R = {format_value(r, 'Ω')}      L = {format_value(l, 'H')}      "
                f"C = {format_value(c, 'F')}\n{t('filter.calc_rlc_bs_note')}")
            self._calc_result = None
            self.calc_apply_btn.configure(state="disabled")

    def _calc_apply(self):
        if not self._calc_result:
            return
        s_kind, s_val, p_kind, p_val = self._calc_result
        labels = dict(zip(self._type_kinds, self._type_labels))
        self.series_type.set(labels[s_kind])
        self.series_value.set(format_value(s_val, "").replace(" ", ""))
        self.shunt_type.set(labels[p_kind])
        self.shunt_value.set(format_value(p_val, "").replace(" ", ""))
        self._simulate()
        self.calc_result_var.set(self.calc_result_var.get() + f"\n{t('filter.calc_applied_note')}")

    def _on_left_resize(self, event):
        avail = max(240, event.width - 32)
        if abs(avail - self._diagram_avail_w) > 10:
            self._diagram_avail_w = avail
            if self._ready:
                self._simulate()

    def _toggle_stage2(self):
        if self.stage2_on.get():
            d_s = 0 if self._resistor_only else 0
            d_p = 0 if self._resistor_only else 1
            self._build_stage_card(self.stages_row, 1, "divider.stage2",
                                    "series2_type", "series2_value", "shunt2_type", "shunt2_value",
                                    default_series_idx=d_s, default_shunt_idx=d_p)
        else:
            for child in list(self.stages_row.winfo_children()):
                if int(child.grid_info().get("column", 0)) == 1:
                    child.destroy()
        self._on_type_change()

    def _kind_from_label(self, label):
        idx = self._type_labels.index(label)
        return self._type_kinds[idx]

    def _on_type_change(self):
        self.series_value.set(DEFAULT_BY_KIND[self._kind_from_label(self.series_type.get())])
        self.shunt_value.set(DEFAULT_BY_KIND[self._kind_from_label(self.shunt_type.get())])
        if hasattr(self, "series2_type"):
            self.series2_value.set(DEFAULT_BY_KIND[self._kind_from_label(self.series2_type.get())])
            self.shunt2_value.set(DEFAULT_BY_KIND[self._kind_from_label(self.shunt2_type.get())])
        self._simulate()

    # ------------------------------------------------------------------
    def _build_chart(self, parent):
        top = ttk.Frame(parent, style="Card.TFrame")
        top.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 0))

        ttk.Label(top, text=t("common.mode"), font=FONT_BODY, style="CardBody.TLabel")\
            .grid(row=0, column=0, sticky="w")
        self.mode = tk.StringVar(value="AC")
        mode_cb = ttk.Combobox(top, textvariable=self.mode, values=["AC", "DC"], state="readonly", width=6)
        mode_cb.grid(row=0, column=1, sticky="w", padx=(6, 20))
        mode_cb.bind("<<ComboboxSelected>>", lambda e: self._rebuild_fields())

        self.modulated_on = tk.BooleanVar(value=False)
        if not self._resistor_only:
            mod_chk = ttk.Checkbutton(top, text=t("filter.modulated_toggle"), variable=self.modulated_on,
                                       command=self._rebuild_fields)
            mod_chk.grid(row=0, column=2, sticky="w", padx=(0, 16))

        self.field_frame = ttk.Frame(top, style="Card.TFrame")
        self.field_frame.grid(row=1, column=0, columnspan=3, sticky="w", pady=(6, 0))
        self.field_vars = {}

        ttk.Button(top, text=t("common.simulate"), command=self._simulate)\
            .grid(row=0, column=3, sticky="w", padx=(20, 0))

        self.chart = MplChartFrame(parent)
        self.chart.grid(row=1, column=0, sticky="nsew", padx=16, pady=(6, 6))

        self.note_var = tk.StringVar()
        ttk.Label(parent, textvariable=self.note_var, font=("Segoe UI", 9), foreground=ACCENT_C,
                  style="CardBody.TLabel", wraplength=380, justify="left")\
            .grid(row=2, column=0, sticky="w", padx=16, pady=(0, 16))

        self._rebuild_fields()

    def _rebuild_fields(self):
        for child in self.field_frame.winfo_children():
            child.destroy()
        self.field_vars = {}
        modulated = (not self._resistor_only) and self.mode.get() == "AC" and self.modulated_on.get()
        if self.mode.get() == "DC":
            fields = [("voltage", t("capacitor.chart.dc_field_v"), "5")]
        elif modulated:
            fields = [("amplitude", t("resistor.chart.ac_field_amp"), "5"),
                      ("carrier_frequency", t("filter.carrier_freq"), "10000"),
                      ("mod_frequency", t("filter.mod_freq"), "500"),
                      ("mod_index", t("filter.mod_index"), "0.5")]
        else:
            fields = [("amplitude", t("resistor.chart.ac_field_amp"), "5"),
                      ("frequency", t("common.frequency"), "1000")]
        for i, (key, label, default) in enumerate(fields):
            ttk.Label(self.field_frame, text=label, font=FONT_BODY, style="CardBody.TLabel")\
                .grid(row=0, column=i * 2, sticky="w", padx=(0, 4))
            var = tk.StringVar(value=default)
            ttk.Entry(self.field_frame, textvariable=var, width=8).grid(row=0, column=i * 2 + 1, padx=(0, 12))
            self.field_vars[key] = var
        self._simulate()

    def _simulate(self):
        if not self._ready:
            return
        series_kind = self._kind_from_label(self.series_type.get())
        shunt_kind = self._kind_from_label(self.shunt_type.get())
        stage2 = self.stage2_on.get()
        try:
            series_val = parse_value(self.series_value.get())
            shunt_val = parse_value(self.shunt_value.get())
            if stage2:
                series2_kind = self._kind_from_label(self.series2_type.get())
                shunt2_kind = self._kind_from_label(self.shunt2_type.get())
                series2_val = parse_value(self.series2_value.get())
                shunt2_val = parse_value(self.shunt2_value.get())
        except Exception:
            self.note_var.set(t("combos.invalid_value"))
            return

        preferred_w = 620 if stage2 else 420
        diagram_w = max(250, min(preferred_w, self._diagram_avail_w))
        if int(self.canvas["width"]) != diagram_w:
            self.canvas.configure(width=diagram_w)
        if stage2:
            draw_divider_diagram(self.canvas, series_kind, series_val, shunt_kind, shunt_val,
                                  series2_kind=series2_kind, series2_val=series2_val,
                                  shunt2_kind=shunt2_kind, shunt2_val=shunt2_val, w=diagram_w)
        else:
            draw_divider_diagram(self.canvas, series_kind, series_val, shunt_kind, shunt_val, w=diagram_w)

        try:
            kwargs = {key: parse_value(var.get()) for key, var in self.field_vars.items()}
        except Exception:
            self.note_var.set(t("common.enter_valid_values"))
            return

        self.chart.clear()
        ax1 = self.chart.fig.add_subplot(111)
        ax1.set_facecolor(PLOT_BG)

        modulated = (not self._resistor_only) and self.mode.get() == "AC" and self.modulated_on.get() and not stage2

        if modulated:
            t_arr, vin, vout, mag, phase = divider_ac_am_signals(
                series_kind, series_val, shunt_kind, shunt_val, **kwargs)
            ax1.plot(t_arr, vin, color=V_COLOR, linewidth=1, label="Vin (AM)")
            ax1.plot(t_arr, vout, color="#2A9D8F", linewidth=1.5, label="Vout")
            ax1.set_xlabel(t("common.time_s"))
            ax1.set_ylabel(t("common.voltage"))
            ax1.legend(loc="upper right", fontsize=8)
            ax1.set_title(t("chart.ac_title"), fontsize=11)
            ax1.grid(True, alpha=0.25)
            include_zero(ax1)
            note = (f"{t('divider.ratio_prefix')} {mag:.3f} @ fc   |   "
                    f"{t('divider.phase_prefix')} {math.degrees(phase):.1f}°\n{t('filter.modulated_note')}")
        elif self.mode.get() == "AC":
            if stage2:
                t_arr, vin, vout, mag, phase = divider_ac_signals2(
                    series_kind, series_val, shunt_kind, shunt_val,
                    series2_kind, series2_val, shunt2_kind, shunt2_val, **kwargs)
            else:
                t_arr, vin, vout, mag, phase = divider_ac_signals(series_kind, series_val, shunt_kind, shunt_val,
                                                                    **kwargs)
            ax1.plot(t_arr, vin, color=V_COLOR, linewidth=1.5, label="Vin")
            ax1.plot(t_arr, vout, color="#2A9D8F", linewidth=2, label="Vout")
            ax1.set_xlabel(t("common.time_s"))
            ax1.set_ylabel(t("common.voltage"))
            ax1.legend(loc="upper right", fontsize=8)
            ax1.set_title(t("chart.ac_title"), fontsize=11)
            ax1.grid(True, alpha=0.25)
            include_zero(ax1)
            note = (f"{t('divider.ratio_prefix')} {mag:.3f}   |   "
                    f"{t('divider.phase_prefix')} {math.degrees(phase):.1f}°")
            if not stage2 and series_kind == "resistor" and shunt_kind == "resistor":
                note += f"\n{t('divider.note_flat_rr')}"
        else:
            if stage2:
                t_arr, vin, vout, tau = divider_dc_signals2(
                    series_kind, series_val, shunt_kind, shunt_val,
                    series2_kind, series2_val, shunt2_kind, shunt2_val, **kwargs)
            else:
                t_arr, vin, vout, tau = divider_dc_signals(series_kind, series_val, shunt_kind, shunt_val, **kwargs)
            ax1.plot(t_arr, vin, color=V_COLOR, linewidth=1.5, label="Vin")
            ax1.plot(t_arr, vout, color="#2A9D8F", linewidth=2, label="Vout")
            ax1.set_xlabel(t("common.time_s"))
            ax1.set_ylabel(t("common.voltage"))
            ax1.legend(loc="upper right", fontsize=8)
            ax1.set_title(t("chart.dc_title"), fontsize=11)
            ax1.grid(True, alpha=0.25)
            include_zero(ax1)
            if tau is not None:
                note = f"{t('common.time_constant')} τ = {tau:.4g} s\n{t('divider.note_transient')}"
            elif not stage2 and series_kind == "resistor" and shunt_kind == "resistor":
                note = t("divider.note_flat_rr")
            else:
                note = t("divider.note_fallback")

        self.chart.fig.tight_layout()
        self.chart.redraw()
        self.note_var.set(note)


class VoltageDividerPanel(_DividerFilterBase):
    """Embedded 'Voltage Divider' subtab inside the Resistors tab.
    Defaults to two resistors (the classic Vout = Vin * R2/(R1+R2) case);
    the type dropdowns still allow swapping in a capacitor/inductor to show
    how the ratio becomes frequency-dependent."""

    def __init__(self, parent):
        super().__init__(parent, show_title=False, intro_key="divider.voltage.intro",
                          default_series_idx=0, default_shunt_idx=0, resistor_only=True)


class FilterTab(_DividerFilterBase):
    """Standalone 'Filters' tab (Signals group). Defaults to a resistor in
    series with a capacitor — a basic RC low-pass filter — and lets the user
    build higher-order responses via the optional second stage."""

    def __init__(self, parent):
        super().__init__(parent, show_title=True, title_key="filter.tab_title",
                          intro_key="filter.intro", default_series_idx=0, default_shunt_idx=1)
