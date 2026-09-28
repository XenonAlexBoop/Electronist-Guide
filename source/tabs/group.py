"""
tabs/group.py - A top-level navigation tab that itself contains a notebook
of sub-tabs. Used to nest a family of related tools (e.g. all "basic
component" calculators, or all "signal" tools) under one top-level nav
entry, matching the app's grouped navigation structure:

    Basic Components > Resistors, Capacitors, Inductors, Diodes/LEDs,
                        Transistors, Op-Amps, Batteries
    Signals          > Filters
    Boolean Logic     (its own tab, already internally split into
                        Logic Gates / Boolean Solver)
    AC/DC Basics      (its own standalone tab)
"""
from tkinter import ttk
from i18n import t
from widgets import lazy_tab, build_lazy


class GroupTab(ttk.Frame):
    def __init__(self, parent, children):
        """children: list of (i18n_key, TabClass) tuples. Each TabClass is
        instantiated with the inner notebook as its parent, exactly like a
        normal top-level tab."""
        super().__init__(parent, style="Tab.TFrame")
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        nb = ttk.Notebook(self)
        nb.grid(row=0, column=0, sticky="nsew")

        # pages are built the first time they are opened
        first = None
        for key, cls in children:
            h = lazy_tab(nb, t(key), cls)
            first = first or h
        self.nb = nb
        build_lazy(first)
