"""
tabs/base_converter.py - Number Base Converter + ADC/DAC Code Converter.

Two independent calculators, side by side:

  - BaseConverterPanel: convert one integer between Binary/Octal/Decimal/
    Hexadecimal and any custom base 2-36 at once, either as a plain
    arbitrary-precision integer or as a fixed-width two's-complement
    bit pattern (the representation real hardware registers actually use).

  - AdcDacPanel: the quantization math behind any ADC/DAC - voltage <->
    digital code for a given resolution (bits) and reference voltage,
    reusing the base converter's digit logic so the code can be read
    off in binary/hex too.
"""
import tkinter as tk
from tkinter import ttk

from widgets import parse_value, format_value, ScrollableFrame, FONT_H1, FONT_H2, FONT_BODY, FONT_MONO
from i18n import t, register

register({"base.adc_plot_code": ("output code", "cod de ieșire"),
          "base.adc_plot_ideal": ("ideal (no quantisation)", "ideal (fără cuantizare)"),
          "base.adc_plot_err": ("error (LSB)", "eroare (LSB)"),
          "base.adc_plot_title": ("{bits}-bit converter - staircase around your input (1 LSB = {lsb})",
                                  "Convertor pe {bits} biți - treptele în jurul intrării tale (1 LSB = {lsb})")})

ACCENT_C = "#0d7d5f"

DIGITS = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
BIT_WIDTHS = [4, 8, 16, 32, 64]


def int_to_base(value, base, group=None, upper=True):
    if value == 0:
        digits = "0"
    else:
        n = abs(value)
        out = []
        while n:
            out.append(DIGITS[n % base])
            n //= base
        digits = "".join(reversed(out))
    if not upper:
        digits = digits.lower()
    if group:
        digits = _group(digits, group)
    text = digits
    if value < 0:
        text = "-" + text
    return text


def _group(digits, size):
    rev = digits[::-1]
    chunks = [rev[i:i + size] for i in range(0, len(rev), size)]
    grouped_rev = " ".join(chunks)
    return grouped_rev[::-1]


def base_to_int(text, base):
    text = text.strip().replace(" ", "").replace("_", "")
    if text == "":
        raise ValueError("empty")
    neg = False
    if text[0] in "+-":
        neg = text[0] == "-"
        text = text[1:]
    if text == "":
        raise ValueError("empty")
    value = 0
    for ch in text.upper():
        d = DIGITS.find(ch)
        if d < 0 or d >= base:
            raise ValueError("'" + ch + "' is not a valid digit in base " + str(base))
        value = value * base + d
    return -value if neg else value


def twos_complement_to_int(pattern_value, bits):
    if pattern_value >= (1 << (bits - 1)):
        return pattern_value - (1 << bits)
    return pattern_value


def int_to_twos_complement(value, bits):
    lo, hi = -(1 << (bits - 1)), (1 << (bits - 1)) - 1
    overflow = value < lo or value > hi
    pattern = value & ((1 << bits) - 1)
    return pattern, overflow


class BaseConverterPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        self.columnconfigure(0, weight=1)

        header = tk.Frame(self, bg=ACCENT_C, height=6)
        header.grid(row=0, column=0, sticky="ew")

        ttk.Label(self, text=t("base.title"), font=FONT_H1, style="CardTitle.TLabel") \
            .grid(row=1, column=0, sticky="w", padx=16, pady=(12, 4))
        ttk.Label(self, text=t("base.intro"), style="CardBody.TLabel", wraplength=420,
                  justify="left").grid(row=2, column=0, sticky="w", padx=16, pady=(0, 10))

        self.mode_var = tk.StringVar(value="plain")
        mode_row = ttk.Frame(self, style="Card.TFrame")
        mode_row.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 6))
        ttk.Radiobutton(mode_row, text=t("base.mode_plain"), variable=self.mode_var,
                         value="plain", command=self._on_mode_change).pack(side="left")
        ttk.Radiobutton(mode_row, text=t("base.mode_twos"), variable=self.mode_var,
                         value="twos", command=self._on_mode_change).pack(side="left", padx=(12, 0))

        self.width_row = ttk.Frame(self, style="Card.TFrame")
        self.width_row.grid(row=4, column=0, sticky="w", padx=16, pady=(0, 8))
        ttk.Label(self.width_row, text=t("base.bit_width"), style="CardBody.TLabel").pack(side="left")
        self.width_var = tk.IntVar(value=8)
        self.width_cb = ttk.Combobox(self.width_row, textvariable=self.width_var, state="readonly",
                                      width=5, values=BIT_WIDTHS)
        self.width_cb.pack(side="left", padx=6)
        self.width_cb.bind("<<ComboboxSelected>>", lambda e: self._convert())
        self.width_row.grid_remove()

        in_row = ttk.Frame(self, style="Card.TFrame")
        in_row.grid(row=5, column=0, sticky="ew", padx=16, pady=(4, 4))
        ttk.Label(in_row, text=t("base.value_label"), style="CardBody.TLabel").grid(row=0, column=0, sticky="w")
        self.value_var = tk.StringVar(value="42")
        entry = ttk.Entry(in_row, textvariable=self.value_var, width=22, font=FONT_MONO)
        entry.grid(row=1, column=0, sticky="w", pady=(2, 0))
        entry.bind("<KeyRelease>", lambda e: self._convert())

        ttk.Label(in_row, text=t("base.from_base_label"), style="CardBody.TLabel").grid(
            row=0, column=1, sticky="w", padx=(16, 0))
        self.from_base_var = tk.IntVar(value=10)
        self.from_base_cb = ttk.Combobox(in_row, textvariable=self.from_base_var, state="readonly",
                                          width=5, values=list(range(2, 37)))
        self.from_base_cb.grid(row=1, column=1, sticky="w", padx=(16, 0), pady=(2, 0))
        self.from_base_cb.bind("<<ComboboxSelected>>", lambda e: self._convert())

        preset_row = ttk.Frame(self, style="Card.TFrame")
        preset_row.grid(row=6, column=0, sticky="w", padx=16, pady=(6, 10))
        for label, base in (("BIN", 2), ("OCT", 8), ("DEC", 10), ("HEX", 16)):
            ttk.Button(preset_row, text=label, width=5,
                       command=lambda b=base: self._set_from_base(b)).pack(side="left", padx=(0, 4))

        sep = ttk.Separator(self, orient="horizontal")
        sep.grid(row=7, column=0, sticky="ew", padx=16, pady=(0, 8))

        self.error_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.error_var, foreground="#b3413a",
                  style="CardBody.TLabel", wraplength=420, justify="left") \
            .grid(row=8, column=0, sticky="w", padx=16)

        results = ttk.Frame(self, style="Card.TFrame")
        results.grid(row=9, column=0, sticky="ew", padx=16, pady=(0, 8))
        results.columnconfigure(1, weight=1)
        self.result_vars = {}
        for i, item in enumerate((("base.bin", 2), ("base.oct", 8), ("base.dec", 10), ("base.hex", 16))):
            key, base = item
            ttk.Label(results, text=t(key), font=FONT_BODY, style="CardBody.TLabel", width=10) \
                .grid(row=i, column=0, sticky="w", pady=2)
            var = tk.StringVar()
            ttk.Label(results, textvariable=var, font=FONT_MONO, foreground=ACCENT_C,
                      style="CardFormula.TLabel", wraplength=280, justify="left") \
                .grid(row=i, column=1, sticky="w", pady=2)
            self.result_vars[base] = var

        custom_row = ttk.Frame(self, style="Card.TFrame")
        custom_row.grid(row=10, column=0, sticky="ew", padx=16, pady=(4, 4))
        ttk.Label(custom_row, text=t("base.custom_base_label"), style="CardBody.TLabel").pack(side="left")
        self.custom_base_var = tk.IntVar(value=36)
        custom_cb = ttk.Combobox(custom_row, textvariable=self.custom_base_var, state="readonly",
                                  width=5, values=list(range(2, 37)))
        custom_cb.pack(side="left", padx=6)
        custom_cb.bind("<<ComboboxSelected>>", lambda e: self._convert())
        self.custom_result_var = tk.StringVar()
        ttk.Label(custom_row, textvariable=self.custom_result_var, font=FONT_MONO,
                  foreground=ACCENT_C, style="CardFormula.TLabel").pack(side="left", padx=(10, 0))

        self.signed_note_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.signed_note_var, style="CardBody.TLabel",
                  wraplength=420, justify="left", font=("Segoe UI", 9, "italic")) \
            .grid(row=11, column=0, sticky="w", padx=16, pady=(4, 14))

        self._convert()

    def _set_from_base(self, base):
        self.from_base_var.set(base)
        self._convert()

    def _on_mode_change(self):
        if self.mode_var.get() == "twos":
            self.width_row.grid()
        else:
            self.width_row.grid_remove()
        self._convert()

    def _convert(self):
        text = self.value_var.get()
        from_base = int(self.from_base_var.get())
        try:
            raw = base_to_int(text, from_base)
        except ValueError as exc:
            self.error_var.set(t("base.error_invalid").format(msg=str(exc)))
            for var in self.result_vars.values():
                var.set("\u2014")
            self.custom_result_var.set("\u2014")
            self.signed_note_var.set("")
            return
        self.error_var.set("")

        if self.mode_var.get() == "twos":
            bits = int(self.width_var.get())
            if raw < 0 or raw >= (1 << bits):
                pattern, overflow = int_to_twos_complement(raw, bits)
            else:
                pattern, overflow = raw, False
            signed_value = twos_complement_to_int(pattern, bits)
            for base, var in self.result_vars.items():
                group = 4 if base in (2, 16) else None
                var.set(int_to_base(pattern, base, group=group))
            self.custom_result_var.set(int_to_base(pattern, int(self.custom_base_var.get())))
            if overflow:
                self.signed_note_var.set(t("base.overflow_note").format(
                    bits=bits, lo=-(1 << (bits - 1)), hi=(1 << (bits - 1)) - 1))
            else:
                self.signed_note_var.set(t("base.twos_note").format(bits=bits, signed=signed_value, pattern=pattern))
        else:
            for base, var in self.result_vars.items():
                group = 4 if base in (2, 16) else None
                var.set(int_to_base(raw, base, group=group))
            self.custom_result_var.set(int_to_base(raw, int(self.custom_base_var.get())))
            self.signed_note_var.set("")


class AdcDacPanel(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Card.TFrame")
        # v6.3: controls on the left, the quantisation staircase on the right
        self.columnconfigure(0, weight=0, minsize=460)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(9, weight=1)
        self._updating = False

        header = tk.Frame(self, bg=ACCENT_C, height=6)
        header.grid(row=0, column=0, columnspan=2, sticky="ew")
        from charts import MplChartFrame
        self.chart = MplChartFrame(self, figsize=(6.5, 5.0), with_toolbar=False)
        self.chart.grid(row=1, column=1, rowspan=9, sticky="nsew", padx=(8, 16), pady=(12, 16))
        self.chart.canvas.get_tk_widget().configure(height=300)

        ttk.Label(self, text=t("base.adc_title"), font=FONT_H1, style="CardTitle.TLabel") \
            .grid(row=1, column=0, sticky="w", padx=16, pady=(12, 4))
        ttk.Label(self, text=t("base.adc_intro"), style="CardBody.TLabel", wraplength=420,
                  justify="left").grid(row=2, column=0, sticky="w", padx=16, pady=(0, 10))

        cfg = ttk.Frame(self, style="Card.TFrame")
        cfg.grid(row=3, column=0, sticky="w", padx=16, pady=(0, 8))
        ttk.Label(cfg, text=t("base.resolution_label"), style="CardBody.TLabel").grid(row=0, column=0, sticky="w")
        self.bits_var = tk.IntVar(value=8)
        bits_cb = ttk.Combobox(cfg, textvariable=self.bits_var, state="readonly", width=5,
                                values=[6, 8, 10, 12, 14, 16, 20, 24])
        bits_cb.grid(row=1, column=0, sticky="w", pady=(2, 0))
        bits_cb.bind("<<ComboboxSelected>>", lambda e: self._on_bits_or_vref_change())

        ttk.Label(cfg, text=t("base.vref_label"), style="CardBody.TLabel").grid(
            row=0, column=1, sticky="w", padx=(16, 0))
        self.vref_var = tk.StringVar(value="5")
        vref_entry = ttk.Entry(cfg, textvariable=self.vref_var, width=10)
        vref_entry.grid(row=1, column=1, sticky="w", padx=(16, 0), pady=(2, 0))
        vref_entry.bind("<KeyRelease>", lambda e: self._on_bits_or_vref_change())

        self.lsb_var = tk.StringVar()
        ttk.Label(cfg, textvariable=self.lsb_var, style="CardBody.TLabel", font=("Segoe UI", 9, "italic")) \
            .grid(row=0, column=2, rowspan=2, sticky="w", padx=(16, 0))

        sep = ttk.Separator(self, orient="horizontal")
        sep.grid(row=4, column=0, sticky="ew", padx=16, pady=(4, 8))

        v_row = ttk.Frame(self, style="Card.TFrame")
        v_row.grid(row=5, column=0, sticky="ew", padx=16, pady=(0, 6))
        ttk.Label(v_row, text=t("base.voltage_label"), style="CardBody.TLabel").pack(anchor="w")
        self.voltage_var = tk.StringVar(value="3.3")
        v_entry = ttk.Entry(v_row, textvariable=self.voltage_var, width=16, font=FONT_MONO)
        v_entry.pack(anchor="w", pady=(2, 0))
        v_entry.bind("<KeyRelease>", lambda e: self._from_voltage())

        c_row = ttk.Frame(self, style="Card.TFrame")
        c_row.grid(row=6, column=0, sticky="ew", padx=16, pady=(6, 6))
        ttk.Label(c_row, text=t("base.code_label"), style="CardBody.TLabel").pack(anchor="w")
        self.code_var = tk.StringVar(value="0")
        c_entry = ttk.Entry(c_row, textvariable=self.code_var, width=16, font=FONT_MONO)
        c_entry.pack(anchor="w", pady=(2, 0))
        c_entry.bind("<KeyRelease>", lambda e: self._from_code())

        results = ttk.Frame(self, style="Card.TFrame")
        results.grid(row=7, column=0, sticky="ew", padx=16, pady=(8, 8))
        results.columnconfigure(1, weight=1)
        self.out_vars = {}
        for i, key in enumerate(("base.code_decimal", "base.code_binary", "base.code_hex",
                                  "base.reconstructed_voltage")):
            ttk.Label(results, text=t(key), style="CardBody.TLabel", width=16) \
                .grid(row=i, column=0, sticky="w", pady=2)
            var = tk.StringVar()
            ttk.Label(results, textvariable=var, font=FONT_MONO, foreground=ACCENT_C,
                      style="CardFormula.TLabel").grid(row=i, column=1, sticky="w", pady=2)
            self.out_vars[key] = var

        self.error_var = tk.StringVar(value="")
        ttk.Label(self, textvariable=self.error_var, foreground="#b3413a", style="CardBody.TLabel",
                  wraplength=420, justify="left").grid(row=8, column=0, sticky="w", padx=16, pady=(0, 14))

        self._on_bits_or_vref_change()
        self._from_voltage()

    def _max_code(self):
        return (1 << int(self.bits_var.get())) - 1

    def _vref(self):
        return parse_value(self.vref_var.get())

    def _on_bits_or_vref_change(self):
        try:
            vref = self._vref()
            lsb = vref / self._max_code()
            self.lsb_var.set(t("base.lsb_note").format(lsb=format_value(lsb, "V")))
        except (ValueError, ZeroDivisionError):
            self.lsb_var.set("")
        self._from_voltage()

    def _from_voltage(self):
        if self._updating:
            return
        self._updating = True
        try:
            vref = self._vref()
            voltage = parse_value(self.voltage_var.get())
            max_code = self._max_code()
            code = round(voltage / vref * max_code) if vref else 0
            clamped = max(0, min(max_code, code))
            self.code_var.set(str(clamped))
            self._render_code(clamped, vref, max_code)
            self.error_var.set("" if code == clamped else t("base.clamped_note").format(lo=0, hi=max_code))
        except (ValueError, ZeroDivisionError):
            self.error_var.set(t("base.error_invalid_number"))
        finally:
            self._updating = False

    def _from_code(self):
        if self._updating:
            return
        self._updating = True
        try:
            vref = self._vref()
            max_code = self._max_code()
            code = int(float(self.code_var.get()))
            clamped = max(0, min(max_code, code))
            if clamped != code:
                self.code_var.set(str(clamped))
            voltage = clamped / max_code * vref if max_code else 0
            self.voltage_var.set(f"{voltage:g}")
            self._render_code(clamped, vref, max_code)
            self.error_var.set("" if code == clamped else t("base.clamped_note").format(lo=0, hi=max_code))
        except (ValueError, ZeroDivisionError):
            self.error_var.set(t("base.error_invalid_number"))
        finally:
            self._updating = False

    def _render_code(self, code, vref, max_code):
        bits = int(self.bits_var.get())
        self.out_vars["base.code_decimal"].set(str(code))
        self.out_vars["base.code_binary"].set(int_to_base(code, 2, group=4).rjust(bits, "0"))
        self.out_vars["base.code_hex"].set("0x" + int_to_base(code, 16, group=4))
        recon = code / max_code * vref if max_code else 0
        self.out_vars["base.reconstructed_voltage"].set(format_value(recon, "V"))
        try:
            v_in = parse_value(self.voltage_var.get())
        except ValueError:
            v_in = recon
        self._plot(v_in, code, vref, max_code, bits)

    def _plot(self, v_in, code, vref, max_code, bits):
        import numpy as np
        fig = self.chart.fig
        fig.clear()
        if not vref or max_code <= 0:
            self.chart.redraw()
            return
        lsb = vref / max_code
        ax = fig.add_subplot(211)
        ax2 = fig.add_subplot(212, sharex=ax)
        if max_code <= 64:
            v0, v1 = 0.0, vref
        else:                                  # zoom on +-10 LSB around the input
            v0 = max(0.0, min(v_in, vref) - 10 * lsb)
            v1 = min(vref, v0 + 20 * lsb)
            v0 = max(0.0, v1 - 20 * lsb)
        vv = np.linspace(v0, v1, 1200)
        cc = np.clip(np.round(vv / lsb), 0, max_code)
        ax.step(vv, cc, where="post", color=ACCENT_C, lw=2, label=t("base.adc_plot_code"))
        ax.plot(vv, vv / lsb, color="#999", lw=1, ls="--", label=t("base.adc_plot_ideal"))
        ax.plot([v_in], [code], "o", color="#c62828", ms=8, zorder=5)
        ax.set_ylabel(t("base.adc_plot_code"), fontsize=9)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=8, loc="upper left")
        ax.set_title(t("base.adc_plot_title").format(bits=bits, lsb=format_value(lsb, "V")), fontsize=10)
        err = (cc * lsb - vv) / lsb
        ax2.plot(vv, err, color="#7c3aed", lw=1.5)
        ax2.axhline(0.5, color="#999", ls=":", lw=1)
        ax2.axhline(-0.5, color="#999", ls=":", lw=1)
        ax2.plot([v_in], [(code * lsb - v_in) / lsb], "o", color="#c62828", ms=7)
        ax2.set_ylabel(t("base.adc_plot_err"), fontsize=9)
        ax2.set_xlabel("Vin (V)", fontsize=9)
        ax2.set_ylim(-0.8, 0.8)
        ax2.grid(alpha=0.3)
        for a in (ax, ax2):
            a.tick_params(labelsize=8)
        try:
            fig.tight_layout(pad=0.6)
        except Exception:
            pass
        self.chart.redraw()


class NumberSystemsTab(ttk.Frame):
    """Combined page hosting both calculators side by side, added as a
    subtab of the Unit Converter."""
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        left_wrap = ttk.Frame(self, style="Card.TFrame")
        left_wrap.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        left_wrap.columnconfigure(0, weight=1)
        left_wrap.rowconfigure(0, weight=1)
        right_wrap = ttk.Frame(self, style="Card.TFrame")
        right_wrap.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        right_wrap.columnconfigure(0, weight=1)
        right_wrap.rowconfigure(0, weight=1)

        left_scroll = ScrollableFrame(left_wrap, style="Card.TFrame")
        left_scroll.grid(row=0, column=0, sticky="nsew")
        left_scroll.body.columnconfigure(0, weight=1)
        BaseConverterPanel(left_scroll.body).grid(row=0, column=0, sticky="nsew")

        right_scroll = ScrollableFrame(right_wrap, style="Card.TFrame")
        right_scroll.grid(row=0, column=0, sticky="nsew")
        right_scroll.body.columnconfigure(0, weight=1)
        AdcDacPanel(right_scroll.body).grid(row=0, column=0, sticky="nsew")
