"""
The Electronist's Guide
------------------------
An interactive, visual desktop reference & calculator app for common
electronic components: resistors, capacitors, inductors/transformers,
diodes/LEDs, transistors, op-amps, and batteries — plus core AC/DC theory.

Run with:  python main.py
Requires tkinter (bundled with Python) plus matplotlib and numpy
(see requirements.txt) for the Chart / Simulate tabs.
"""
import os
import sys
import tkinter as tk
from tkinter import ttk

import i18n
import symbols
from i18n import t
from tabs.resistor import ResistorTab
from tabs.capacitor import CapacitorTab
from tabs.inductor import InductorTab
from tabs.diode import DiodeTab
from tabs.transistor import TransistorTab
from tabs.opamp import OpAmpTab
from tabs.battery import BatteryTab
from tabs.basics import BasicsTab
from tabs.filter_lab import FilterTab
from tabs.digital_logic import DigitalLogicTab
from tabs.group import GroupTab
from tabs.unit_converter import UnitConverterTab
from tabs.ac_circuits import ACCircuitsTab
from tabs.modulation import ModulationTab
from tabs.rf_simulator import RFSimulatorTab
from rf.band_table import RFBandsView
from widgets import lazy_tab, build_lazy

BG = "#F1EFE9"
CARD_BG = "#FFFFFF"
HEADER_BG = "#1f2a44"
HEADER_FG = "#F5F5F5"
HEADER_SUB = "#B7C0D8"


def setup_style(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except tk.TclError:
        pass

    root.configure(bg=BG)
    # base ttk colours
    style.configure(".", background="#dcdad5", foreground="#000000", fieldbackground="#ffffff",
                    troughcolor="#bab5ab", bordercolor="#9e9a91", lightcolor="#eeebe7", darkcolor="#cfcdc8",
                    selectbackground="#4a6984", selectforeground="#ffffff", insertcolor="#000000")
    style.map(".", background=[("disabled", "#dcdad5"), ("active", "#eeebe7")],
              foreground=[("disabled", "#999999")])
    style.configure("TEntry", fieldbackground="#ffffff", foreground="#000000", insertcolor="#000000")
    style.configure("TCombobox", fieldbackground="#ffffff", foreground="#000000", arrowcolor="#000000")
    style.map("TCombobox", fieldbackground=[("readonly", "#ffffff")], foreground=[("readonly", "#000000")],
              selectbackground=[("readonly", "#ffffff")], selectforeground=[("readonly", "#000000")])
    style.configure("Treeview", background="#ffffff", fieldbackground="#ffffff", foreground="#000000")
    style.map("Treeview", background=[("selected", "#4a6984")], foreground=[("selected", "#ffffff")])
    style.configure("Treeview.Heading", background="#dcdad5", foreground="#000000")
    style.configure("TCheckbutton", background=CARD_BG, foreground="#000000", indicatorbackground="#ffffff")
    style.configure("TRadiobutton", background=CARD_BG, foreground="#000000", indicatorbackground="#ffffff")
    style.configure("TScale", background="#dcdad5", troughcolor="#bab5ab")
    style.configure("TScrollbar", background="#dcdad5", troughcolor="#bab5ab", arrowcolor="#000000")
    for pat, val in (("*TCombobox*Listbox.background", "#ffffff"), ("*TCombobox*Listbox.foreground", "#000000"),
                     ("*Listbox.background", "#ffffff"), ("*Listbox.foreground", "#000000"),
                     ("*Text.background", "#ffffff"), ("*Text.foreground", "#000000"),
                     ("*Canvas.background", "#ffffff")):
        root.option_add(pat, val)

    style.configure("TFrame", background=BG)
    style.configure("Tab.TFrame", background=BG)
    style.configure("Card.TFrame", background=CARD_BG)

    style.configure("TabTitle.TLabel", background=BG, foreground="#1f2a44")
    style.configure("CardTitle.TLabel", background=CARD_BG, foreground="#1f2a44")
    style.configure("CardSub.TLabel", background=CARD_BG, foreground="#1f2a44")
    style.configure("CardBody.TLabel", background=CARD_BG, foreground="#3d3d3d")
    style.configure("CardFormula.TLabel", background=CARD_BG)
    style.configure("TLabel", background=CARD_BG)

    style.configure("TNotebook", background=BG, borderwidth=0)
    style.configure("TNotebook.Tab", padding=(16, 10), font=("Segoe UI", 10, "bold"))
    style.map("TNotebook.Tab",
              background=[("selected", CARD_BG), ("!selected", "#DAD6CB")],
              foreground=[("selected", "#1f2a44"), ("!selected", "#555")])

    style.configure("TButton", padding=(10, 6), font=("Segoe UI", 10, "bold"),
                     background="#1f2a44",
                     foreground="white")
    style.map("TButton", background=[("active", "#334166")])

    style.configure("Small.TButton", padding=(6, 2), font=("Segoe UI", 8, "bold"))
    style.configure("TCombobox", padding=4)
    style.configure("Treeview", rowheight=26, font=("Segoe UI", 9))
    style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"))

    # Language toggle pill buttons
    style.configure("LangActive.TButton", padding=(10, 4), font=("Segoe UI", 9, "bold"),
                     background="#F5C542", foreground="#1f2a44")
    style.map("LangActive.TButton", background=[("active", "#F5C542")])
    style.configure("LangInactive.TButton", padding=(10, 4), font=("Segoe UI", 9, "bold"),
                     background="#334166", foreground="#D8DDEA")
    style.map("LangInactive.TButton", background=[("active", "#3d4a7a")])

    return style


# ---------------------------------------------------------------------------
# Top-level navigation structure:
#   Basic Components  > Resistors, Capacitors, Inductors, Diodes/LEDs,
#                        Transistors, Op-Amps, Batteries
#   Signals           > Filters, AC Circuits & Phasors (Passive AC Circuits /
#                        AC Power Systems), Signal Generator
#   Boolean Logic       (its own tab; internally split into
#                        Logic Gates / Boolean Solver)
#   AC/DC Basics        (its own tab; internally split into
#                        Ohm's Law / Kirchhoff's Laws)
#   Unit Converter      (its own standalone tab)
# (The former "PCB & Production" tab was removed in v5.0.)
# ---------------------------------------------------------------------------
BASIC_COMPONENT_CHILDREN = [
    ("nav.resistors", ResistorTab),
    ("nav.capacitors", CapacitorTab),
    ("nav.inductors", InductorTab),
    ("nav.diodes", DiodeTab),
    ("nav.transistors", TransistorTab),
    ("nav.opamps", OpAmpTab),
    ("nav.batteries", BatteryTab),
]

SIGNALS_CHILDREN = [
    ("nav.filters", FilterTab),
    ("nav.ac_circuits", ACCircuitsTab),
    ("nav.modulation", ModulationTab),
]

RF_MICROWAVE_CHILDREN = [
    ("rf.tab_title", RFSimulatorTab),
    ("rf.bands.tab_title", RFBandsView),
]


def _make_basic_components_tab(parent):
    return GroupTab(parent, BASIC_COMPONENT_CHILDREN)


def _make_signals_tab(parent):
    return GroupTab(parent, SIGNALS_CHILDREN)


def _make_rf_microwave_tab(parent):
    return GroupTab(parent, RF_MICROWAVE_CHILDREN)


TAB_SPECS = [
    ("nav.group.basic_components", _make_basic_components_tab),
    ("nav.group.signals", _make_signals_tab),
    ("nav.group.rf_microwave", _make_rf_microwave_tab),
    ("nav.digital", DigitalLogicTab),
    ("nav.basics", BasicsTab),
    ("nav.unit_converter", UnitConverterTab),
]


def resource_path(relative_path):
    """Resolve a bundled asset's path, working both when run from source and
    when frozen into a standalone executable by PyInstaller."""
    base_path = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


class ElectronistGuideApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("The Electronist's Guide")
        try:
            icon_img = tk.PhotoImage(file=resource_path(os.path.join("assets", "icon.png")))
            self.iconphoto(True, icon_img)
            self._icon_img = icon_img  # keep a reference so it isn't garbage-collected
        except Exception:
            pass
        self._maximize()
        self.minsize(1000, 700)
        setup_style(self)
        self._install_popdown_guard()

        self.header = tk.Frame(self, bg=HEADER_BG, height=64)
        self.header.pack(fill="x", side="top")
        self.header.pack_propagate(False)

        self.title_label = tk.Label(self.header, bg=HEADER_BG, fg=HEADER_FG,
                                     font=("Segoe UI", 18, "bold"))
        self.title_label.pack(side="left", padx=(20, 12))
        self.subtitle_label = tk.Label(self.header, bg=HEADER_BG, fg=HEADER_SUB,
                                        font=("Segoe UI", 10))
        self.subtitle_label.pack(side="left")

        lang_frame = tk.Frame(self.header, bg=HEADER_BG)
        lang_frame.pack(side="right", padx=20)
        self.en_btn = ttk.Button(lang_frame, text="EN", width=4,
                                  command=lambda: self._set_lang("en"))
        self.en_btn.pack(side="left", padx=(0, 4))
        self.ro_btn = ttk.Button(lang_frame, text="RO", width=4,
                                  command=lambda: self._set_lang("ro"))
        self.ro_btn.pack(side="left")

        sym_frame = tk.Frame(self.header, bg=HEADER_BG)
        sym_frame.pack(side="right", padx=(20, 0))
        self.sym_label = tk.Label(sym_frame, bg=HEADER_BG, fg=HEADER_SUB, font=("Segoe UI", 9))
        self.sym_label.pack(side="left", padx=(0, 6))
        self.iec_btn = ttk.Button(sym_frame, text="IEC", width=5,
                                   command=lambda: symbols.set_style("IEC"))
        self.iec_btn.pack(side="left", padx=(0, 4))
        self.ansi_btn = ttk.Button(sym_frame, text="ANSI", width=5,
                                    command=lambda: symbols.set_style("ANSI"))
        self.ansi_btn.pack(side="left")

        self.notebook_container = ttk.Frame(self, style="Tab.TFrame")
        self.notebook_container.pack(fill="both", expand=True)

        self._build_ui()

    def _maximize(self):
        """Best-effort full-screen/maximized startup across platforms."""
        try:
            self.state("zoomed")  # Windows, some Linux WMs
            return
        except tk.TclError:
            pass
        try:
            self.attributes("-zoomed", True)  # X11/Linux
            return
        except tk.TclError:
            pass
        # Fallback: size to the screen manually (e.g. macOS)
        try:
            w = self.winfo_screenwidth()
            h = self.winfo_screenheight()
            self.geometry(f"{w}x{h}+0+0")
        except tk.TclError:
            self.geometry("1280x860")

    def _set_lang(self, lang):
        if i18n.get_language() == lang:
            return
        i18n.set_language(lang)

    def _build_ui(self):
        self.title_label.configure(text=t("app.title"))
        self.subtitle_label.configure(text=t("app.subtitle"))

        active = i18n.get_language()
        self.en_btn.configure(style="LangActive.TButton" if active == "en" else "LangInactive.TButton")
        self.ro_btn.configure(style="LangActive.TButton" if active == "ro" else "LangInactive.TButton")
        style = symbols.get_style()
        self.sym_label.configure(text=t("sym.header_label"))
        self.iec_btn.configure(style="LangActive.TButton" if style == "IEC" else "LangInactive.TButton")
        self.ansi_btn.configure(style="LangActive.TButton" if style == "ANSI" else "LangInactive.TButton")

        path = self._selected_path() if getattr(self, "notebook", None) is not None else []
        for child in self.notebook_container.winfo_children():
            child.destroy()

        notebook = ttk.Notebook(self.notebook_container)
        notebook.pack(fill="both", expand=True)
        self.notebook = notebook

        # Pages are created the first time they are opened (much faster
        # start-up and language switching).
        holders = [lazy_tab(notebook, t(key), cls) for key, cls in TAB_SPECS]
        build_lazy(holders[0])
        if path:
            self._restore_path(path)

    # ------------------------------------------------------------------
    # A ttk.Combobox drop-down is a separate always-on-top window on Windows:
    # if the user Alt+Tabs away while it is open, it stayed floating over the
    # other apps. Close any open drop-down as soon as the app loses focus.
    def _install_popdown_guard(self):
        self._open_combos = set()

        def remember(e):
            self._open_combos.add(str(e.widget))
            if not getattr(self, "_popdown_poll", False):
                self._popdown_poll = True
                self.after(300, self._poll_popdowns)
        self.bind_class("TCombobox", "<ButtonPress-1>", remember, add="+")
        self.bind_class("TCombobox", "<KeyPress-Down>", remember, add="+")
        self.bind_all("<FocusOut>", lambda _e: self.after(150, self._close_popdowns_if_inactive), add="+")
        for seq in ("<Deactivate>", "<Unmap>"):
            try:
                self.bind(seq, lambda _e: self.after(50, self._close_popdowns_if_inactive), add="+")
            except tk.TclError:
                pass

    def _poll_popdowns(self):
        """While a drop-down is open, check a few times a second that the
        app still has focus (belt and braces for the FocusOut binding)."""
        any_open = False
        for path in list(self._open_combos):
            try:
                pd = self.tk.call("ttk::combobox::PopdownWindow", path)
                any_open |= bool(int(self.tk.call("winfo", "ismapped", pd)))
            except tk.TclError:
                self._open_combos.discard(path)
        if any_open:
            self._close_popdowns_if_inactive()
            self.after(300, self._poll_popdowns)
        else:
            self._popdown_poll = False

    def _app_has_focus(self):
        try:
            return bool(self.tk.call("focus"))
        except tk.TclError:
            return False

    def _close_popdowns_if_inactive(self):
        if self._app_has_focus() and self.state() != "iconic":
            return
        self.close_popdowns()

    def close_popdowns(self):
        for path in list(self._open_combos):
            try:
                if not int(self.tk.call("winfo", "exists", path)):
                    self._open_combos.discard(path)
                    continue
                pd = self.tk.call("ttk::combobox::PopdownWindow", path)
                if int(self.tk.call("winfo", "ismapped", pd)):
                    self.tk.call("ttk::combobox::Unpost", path)
            except tk.TclError:
                self._open_combos.discard(path)

    # remember which page (and sub-pages) are open across a rebuild
    @staticmethod
    def _inner_notebook(w):
        stack = [w]
        while stack:
            c = stack.pop(0)
            if isinstance(c, ttk.Notebook):
                return c
            try:
                stack.extend(c.winfo_children())
            except tk.TclError:
                pass
        return None

    def _selected_path(self):
        path, nb = [], self.notebook
        while nb is not None:
            try:
                cur = nb.select()
                if not cur:
                    break
                path.append(nb.index(cur))
                nb = self._inner_notebook(nb.nametowidget(cur))
            except tk.TclError:
                break
        return path

    def _restore_path(self, path):
        nb = self.notebook
        for idx in path:
            if nb is None:
                break
            try:
                nb.select(idx)
                page = nb.nametowidget(nb.select())
            except tk.TclError:
                break
            build_lazy(page)
            nb = self._inner_notebook(page)

    def rebuild(self):
        self._build_ui()


def main():
    app = ElectronistGuideApp()
    i18n.on_change(app.rebuild)
    symbols.on_style_change(app.rebuild)
    app.mainloop()


if __name__ == "__main__":
    main()
