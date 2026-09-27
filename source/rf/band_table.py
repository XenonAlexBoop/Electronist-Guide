"""
rf/band_table.py - RF Band Allocations reference table.

A quick-lookup table of commonly-used RF bands (ISM, WiFi, LoRaWAN,
cellular, GNSS, NFC) and how their allocation differs across four major
regulatory regions: EU (ETSI), China (SRRC/MIIT), North America
(FCC/ISED) and Japan (ARIB/MIC).

This is a practical engineering quick-reference, not a legal source -
allocations, power limits and duty-cycle rules change over time and
have exceptions/sub-bands not captured in a single row. Always confirm
against the current regulator's own publication before a production or
compliance decision.
"""
import tkinter as tk
from tkinter import ttk

from i18n import t
from widgets import FONT_H1, FONT_H2, FONT_BODY, ScrollableFrame

ACCENT_C = "#2A9D8F"

BANDS = [
    ("rf.band.subghz_ism", "rf.band.note.subghz_ism",
     "863-870 MHz", "470-510 / 779-787 MHz", "902-928 MHz", "920-928 MHz"),
    ("rf.band.24ghz_ism", "rf.band.note.24ghz_ism",
     "2400-2483.5 MHz", "2400-2483.5 MHz", "2400-2483.5 MHz", "2400-2483.5 MHz"),
    ("rf.band.5ghz_lower", "rf.band.note.5ghz_lower",
     "5150-5350 MHz", "5150-5350 MHz", "5150-5350 MHz", "5150-5350 MHz"),
    ("rf.band.5ghz_upper", "rf.band.note.5ghz_upper",
     "5470-5725 MHz", "5725-5850 MHz", "5725-5850 MHz", "5470-5730 MHz"),
    ("rf.band.lorawan", "rf.band.note.lorawan",
     "EU868: 863-870 MHz", "CN470: 470-510 MHz", "US915: 902-928 MHz", "AS923: 920-928 MHz"),
    ("rf.band.nfc_hf", "rf.band.note.nfc_hf",
     "13.553-13.567 MHz", "13.553-13.567 MHz", "13.553-13.567 MHz", "13.553-13.567 MHz"),
    ("rf.band.uhf_rfid", "rf.band.note.uhf_rfid",
     "865.6-867.6 MHz", "920.5-924.5 MHz", "902-928 MHz", "916.7-920.9 MHz"),
    ("rf.band.gnss_l1", "rf.band.note.gnss_l1",
     "1575.42 MHz", "1575.42 MHz", "1575.42 MHz", "1575.42 MHz"),
    ("rf.band.cellular_2g", "rf.band.note.cellular_2g",
     "GSM900 / GSM1800", "GSM900 / GSM1800", "GSM850 / PCS1900", "N/A (2G retired)"),
    ("rf.band.cellular_low", "rf.band.note.cellular_low",
     "B20: 791-862 MHz", "B41 (TDD): 2496-2690 MHz", "B12/B13/B17: 698-806 MHz", "B28: 703-803 MHz"),
]

REGULATORS = {
    "eu": "ETSI", "china": "SRRC / MIIT", "na": "FCC / ISED", "japan": "ARIB / MIC",
}


class RFBandsView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        scroll = ScrollableFrame(self, style="Tab.TFrame")
        scroll.grid(row=0, column=0, sticky="nsew")
        body = scroll.body
        body.columnconfigure(0, weight=1)

        header = tk.Frame(body, bg=ACCENT_C, height=6)
        header.grid(row=0, column=0, sticky="ew", padx=16, pady=(16, 0))

        ttk.Label(body, text=t("rf.bands.title"), font=FONT_H1, style="TabTitle.TLabel") \
            .grid(row=1, column=0, sticky="w", padx=16, pady=(10, 4))
        ttk.Label(body, text=t("rf.bands.intro"), style="CardBody.TLabel", wraplength=1100,
                  justify="left").grid(row=2, column=0, sticky="w", padx=16, pady=(0, 12))

        table_wrap = ttk.Frame(body, style="Card.TFrame")
        table_wrap.grid(row=3, column=0, sticky="ew", padx=16, pady=(0, 8))
        table_wrap.columnconfigure(0, weight=1)

        columns = ("band", "eu", "china", "na", "japan")
        tree = ttk.Treeview(table_wrap, columns=columns, show="headings", height=len(BANDS))
        headings = [
            ("band", "rf.bands.col_band", 220),
            ("eu", "rf.bands.col_eu", 190),
            ("china", "rf.bands.col_china", 190),
            ("na", "rf.bands.col_na", 190),
            ("japan", "rf.bands.col_japan", 170),
        ]
        for col, key, width in headings:
            tree.heading(col, text=t(key))
            tree.column(col, width=width, minwidth=110, anchor="w", stretch=True)

        for name_key, note_key, eu, china, na, japan in BANDS:
            tree.insert("", "end", values=(t(name_key), eu, china, na, japan))

        tree.grid(row=0, column=0, sticky="ew")
        vsb = ttk.Scrollbar(table_wrap, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=vsb.set)
        vsb.grid(row=0, column=1, sticky="ns")
        self.tree = tree

        reg_row = ttk.Frame(body, style="Card.TFrame")
        reg_row.grid(row=4, column=0, sticky="w", padx=16, pady=(0, 8))
        reg_text = "   |   ".join(k.upper() + ": " + v for k, v in
                                   (("eu", REGULATORS["eu"]), ("china", REGULATORS["china"]),
                                    ("na", REGULATORS["na"]), ("japan", REGULATORS["japan"])))
        ttk.Label(reg_row, text=t("rf.bands.regulators_label") + "  " + reg_text,
                  style="CardBody.TLabel", font=("Segoe UI", 9, "italic")).pack(anchor="w")

        notes_frame = ttk.Frame(body, style="Card.TFrame")
        notes_frame.grid(row=5, column=0, sticky="ew", padx=16, pady=(4, 16))
        notes_frame.columnconfigure(0, weight=1)
        ttk.Label(notes_frame, text=t("rf.bands.notes_title"), font=FONT_H2,
                  style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", pady=(8, 4), padx=10)
        for i, row_data in enumerate(BANDS, start=1):
            name_key, note_key = row_data[0], row_data[1]
            row = ttk.Frame(notes_frame, style="Card.TFrame")
            row.grid(row=i, column=0, sticky="ew", padx=10, pady=2)
            ttk.Label(row, text=t(name_key) + ":", font=("Segoe UI", 9, "bold"),
                      style="CardBody.TLabel").pack(side="left", anchor="n")
            ttk.Label(row, text=" " + t(note_key), style="CardBody.TLabel", wraplength=950,
                      justify="left").pack(side="left", anchor="n")

        disclaimer = ttk.Label(body, text=t("rf.bands.disclaimer"), style="CardBody.TLabel",
                                font=("Segoe UI", 9, "italic"), foreground="#b3691d",
                                wraplength=1100, justify="left")
        disclaimer.grid(row=6, column=0, sticky="w", padx=16, pady=(0, 20))
