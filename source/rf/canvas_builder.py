"""
rf/canvas_builder.py - The RF Circuit Builder schematic canvas.

A dark, grid-based schematic-capture editor: pick a tool from the
palette, click the canvas to place it, wire points together, select /
move / delete / edit values. The circuit the user draws here IS the
model the RF solver runs on (rf.model.CircuitModel) - nothing here is
decorative.

Grounds are ordinary one-terminal components (kind "GND") in the data
model, so they are selectable, movable and deletable through the exact
same code path as every other component - no special-casing needed here.
"""
import math
import tkinter as tk
from tkinter import ttk, messagebox

from i18n import t
from widgets import parse_value, format_value, ScrollableFrame, FONT_BODY, FONT_H2, FONT_MONO
from rf.model import CircuitModel, Component

BG = "#12151f"
GRID_COLOR = "#232838"
GRID_COLOR_MAJOR = "#2d3348"
WIRE_COLOR = "#c7cbd8"
SELECT_COLOR = "#f6ad55"
PORT_COLOR = "#4fd1c5"
GND_COLOR = "#8fa0c7"
COMP_COLOR = "#e7e9f0"
TEXT_COLOR = "#aeb6cf"
HINT_COLOR = "#7c86a8"

FONT_MONO_SMALL = ("Consolas", 8, "bold")
FONT_MONO_TINY = ("Consolas", 8)

TOOLS = [
    ("select", "rf.tool.select"),
    ("wire", "rf.tool.wire"),
    ("gnd", "rf.tool.gnd"),
    ("port", "rf.tool.port"),
    ("R", "rf.tool.r"),
    ("L", "rf.tool.l"),
    ("C", "rf.tool.c"),
    ("TL", "rf.tool.tl"),
    ("LOAD_MATCHED", "rf.tool.load_matched"),
    ("LOAD_R", "rf.tool.load_r"),
    ("LOAD_Z", "rf.tool.load_z"),
    ("OPEN", "rf.tool.open"),
    ("SHORT", "rf.tool.short"),
    ("delete", "rf.tool.delete"),
]

TWO_CLICK_KINDS = {"R", "L", "C", "TL"}
ONE_CLICK_KINDS = {"gnd", "port", "LOAD_MATCHED", "LOAD_R", "LOAD_Z", "OPEN", "SHORT"}

DEFAULTS = {
    "R": {"value": 50.0},
    "L": {"value": 10e-9},
    "C": {"value": 1e-12},
    "TL": {"z0": 50.0, "length": 0.03, "vf": 0.66},
    "LOAD_MATCHED": {"z0": 50.0},
    "LOAD_R": {"value": 50.0},
    "LOAD_Z": {"r": 50.0, "x": 0.0},
}

TOOL_HINT_KEYS = {
    "select": "rf.hint.select",
    "wire": "rf.hint.wire",
    "gnd": "rf.hint.gnd",
    "port": "rf.hint.port",
    "R": "rf.hint.twoclick",
    "L": "rf.hint.twoclick",
    "C": "rf.hint.twoclick",
    "TL": "rf.hint.twoclick",
    "LOAD_MATCHED": "rf.hint.oneclick",
    "LOAD_R": "rf.hint.oneclick",
    "LOAD_Z": "rf.hint.oneclick",
    "OPEN": "rf.hint.oneclick",
    "SHORT": "rf.hint.oneclick",
    "delete": "rf.hint.delete",
}


class CircuitBuilderView(ttk.Frame):
    def __init__(self, parent, sim_state, on_change=None):
        super().__init__(parent, style="Tab.TFrame")
        self.sim_state = sim_state
        self.model = sim_state.circuit
        self.on_change = on_change or (lambda: None)

        self.grid_px = 28
        self.origin_x = 60
        self.origin_y = 60
        self.tool = "select"
        self.next_port_number = tk.IntVar(value=1)
        self.pending_point = None
        self.selected = None
        self._drag_start_pixel = None
        self._drag_orig_points = None
        self._pan_start = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)

        self._build_status_strip()

        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.grid(row=1, column=0, sticky="nsew", padx=10, pady=(0, 10))

        palette_holder = ttk.Frame(paned, style="Card.TFrame", width=230)
        canvas_holder = ttk.Frame(paned, style="Tab.TFrame")
        props_holder = ttk.Frame(paned, style="Card.TFrame", width=230)
        # Pin the side panes to a fixed width regardless of their content's
        # natural size request, so the properties panel never gets
        # squeezed down to a sliver - only the canvas (weight=1) grows or
        # shrinks with the window.
        palette_holder.grid_propagate(False)
        props_holder.grid_propagate(False)
        paned.add(palette_holder, weight=0)
        paned.add(canvas_holder, weight=1)
        paned.add(props_holder, weight=0)

        self._build_palette(palette_holder)
        self._build_canvas(canvas_holder)
        self._build_props_panel(props_holder)

        self._paned = paned
        self.redraw()

    # ------------------------------------------------------------------
    def _build_status_strip(self):
        strip = ttk.Frame(self, style="Tab.TFrame")
        strip.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 4))
        self.status_lbl = ttk.Label(strip, text="", style="CardBody.TLabel",
                                     font=("Segoe UI", 9, "italic"))
        self.status_lbl.pack(side="left")
        self._update_status()

    def _update_status(self):
        hint_key = TOOL_HINT_KEYS.get(self.tool, "rf.hint.select")
        text = t(hint_key)
        if self.tool in TWO_CLICK_KINDS or self.tool == "wire":
            if self.pending_point is not None:
                text = t("rf.hint.second_click")
        self.status_lbl.configure(text=text)

    # ------------------------------------------------------------------
    def _build_palette(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        ttk.Label(parent, text=t("rf.palette.title"), font=FONT_H2,
                  style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))

        scroller = ScrollableFrame(parent, style="Card.TFrame")
        scroller.grid(row=1, column=0, sticky="nsew", padx=4)
        pal = scroller.body

        self.tool_buttons = {}
        for kind, key in TOOLS:
            row = ttk.Frame(pal, style="Card.TFrame")
            row.pack(fill="x", padx=4, pady=1)
            icon = tk.Canvas(row, width=26, height=20, bg="#1c2130", highlightthickness=0)
            icon.pack(side="left", padx=(2, 4))
            _draw_palette_icon(icon, kind)
            b = tk.Button(row, text=t(key), anchor="w", relief="flat",
                          bg="#1c2130", fg=TEXT_COLOR, activebackground="#334166",
                          activeforeground="white", font=FONT_BODY,
                          command=lambda k=kind: self._set_tool(k))
            b.pack(side="left", fill="x", expand=True)
            self.tool_buttons[kind] = (b, icon)

        port_row = ttk.Frame(pal, style="Card.TFrame")
        port_row.pack(fill="x", padx=8, pady=(10, 4))
        ttk.Label(port_row, text=t("rf.palette.port_number"), style="CardBody.TLabel").pack(side="left")
        spn = ttk.Spinbox(port_row, from_=1, to=4, width=3, textvariable=self.next_port_number)
        spn.pack(side="left", padx=4)

        clear_btn = ttk.Button(pal, text=t("rf.palette.clear_circuit"), command=self._clear_circuit)
        clear_btn.pack(fill="x", padx=8, pady=(10, 4))

        hint = ttk.Label(pal, text=t("rf.palette.hint"), font=("Segoe UI", 8),
                          style="CardBody.TLabel", wraplength=190, justify="left")
        hint.pack(anchor="w", padx=8, pady=(8, 10))

        self._highlight_tool()

    def _clear_circuit(self):
        if not self.model.components and not self.model.wires:
            return
        if not messagebox.askyesno(t("rf.error.title"), t("rf.palette.clear_confirm")):
            return
        self.model.clear()
        self.selected = None
        self.pending_point = None
        self._render_props()
        self.redraw()
        self.on_change()

    def _set_tool(self, kind):
        self.tool = kind
        self.pending_point = None
        self._highlight_tool()
        self._update_status()
        self.redraw()

    def _highlight_tool(self):
        for kind, (btn, icon) in self.tool_buttons.items():
            btn.configure(bg="#334166" if kind == self.tool else "#1c2130")

    # ------------------------------------------------------------------
    def _build_canvas(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(parent, bg=BG, highlightthickness=0)
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._start_pan)
        self.canvas.bind("<B3-Motion>", self._do_pan)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", lambda e: self._zoom(1.1, e))
        self.canvas.bind("<Button-5>", lambda e: self._zoom(1 / 1.1, e))
        self.canvas.bind("<Delete>", lambda e: self._delete_selected())
        self.canvas.bind("<BackSpace>", lambda e: self._delete_selected())
        self.canvas.bind("<Escape>", lambda e: self._cancel_pending())
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())

    def _cancel_pending(self):
        self.pending_point = None
        self._update_status()
        self.redraw()

    def _build_props_panel(self, parent):
        self.props = parent
        self.props.columnconfigure(0, weight=1)
        self._render_props()

    # ------------------------------------------------------------------
    def _grid_to_px(self, p):
        gx, gy = p
        return self.origin_x + gx * self.grid_px, self.origin_y + gy * self.grid_px

    def _px_to_nearest_grid(self, x, y):
        gx = round((x - self.origin_x) / self.grid_px)
        gy = round((y - self.origin_y) / self.grid_px)
        return (gx, gy)

    # ------------------------------------------------------------------
    def _on_wheel(self, event):
        factor = 1.1 if event.delta > 0 else 1 / 1.1
        self._zoom(factor, event)

    def _zoom(self, factor, event):
        self.grid_px = max(12, min(80, self.grid_px * factor))
        self.redraw()

    def _start_pan(self, event):
        self._pan_start = (event.x, event.y, self.origin_x, self.origin_y)

    def _do_pan(self, event):
        if not self._pan_start:
            return
        sx, sy, ox, oy = self._pan_start
        self.origin_x = ox + (event.x - sx)
        self.origin_y = oy + (event.y - sy)
        self.redraw()

    # ------------------------------------------------------------------
    def _hit_test(self, x, y, tol=11):
        # Point-like parts (ports, grounds, loads) get first priority: they
        # are very often placed exactly on top of another component's
        # terminal (e.g. "resistor to ground" - the ground point coincides
        # with the resistor's end), and the small symbol drawn there is
        # what the person is visually aiming for, not the line passing
        # through it. Without this, whichever was added first would always
        # win the tie and the other would become permanently unclickable.
        best = None
        best_d = tol
        for c in self.model.components:
            if c.p2 is not None:
                continue
            px1, py1 = self._grid_to_px(c.p1)
            d = ((x - px1) ** 2 + (y - py1) ** 2) ** 0.5
            if d < best_d:
                best_d = d
                best = c
        if best is not None:
            return best

        # Then two-terminal component bodies and wires (line-segment hit
        # test), also preferring the closest match.
        for c in self.model.components:
            if c.p2 is None:
                continue
            px1, py1 = self._grid_to_px(c.p1)
            px2, py2 = self._grid_to_px(c.p2)
            d = _point_segment_dist(x, y, px1, py1, px2, py2)
            if d < best_d:
                best_d = d
                best = c
        for w in self.model.wires:
            px1, py1 = self._grid_to_px(w[0])
            px2, py2 = self._grid_to_px(w[1])
            d = _point_segment_dist(x, y, px1, py1, px2, py2)
            if d < best_d:
                best_d = d
                best = w
        return best

    def _on_click(self, event):
        self.canvas.focus_set()
        gpt = self._px_to_nearest_grid(event.x, event.y)

        if self.tool == "select":
            hit = self._hit_test(event.x, event.y)
            self.selected = hit
            if hit is not None and isinstance(hit, Component):
                self._drag_start_pixel = (event.x, event.y)
                self._drag_orig_points = (hit.p1, hit.p2)
            self._render_props()
            self.redraw()
            return

        if self.tool == "delete":
            hit = self._hit_test(event.x, event.y)
            if hit is not None:
                if isinstance(hit, Component):
                    self.model.components.remove(hit)
                else:
                    self.model.wires.remove(hit)
                if self.selected is hit:
                    self.selected = None
                self._render_props()
                self.redraw()
                self.on_change()
            return

        if self.tool == "gnd":
            comp = self.model.add_ground(gpt)
            self.selected = comp
            self._render_props()
            self.redraw()
            self.on_change()
            return

        if self.tool == "port":
            n = int(self.next_port_number.get())
            comp = Component("PORT", gpt, params={"number": n, "z0": self.model.default_z0, "enabled": True})
            self.model.add_component(comp)
            self.selected = comp
            self._render_props()
            self.redraw()
            self.on_change()
            return

        if self.tool in ("LOAD_MATCHED", "LOAD_R", "LOAD_Z", "OPEN", "SHORT"):
            params = dict(DEFAULTS.get(self.tool, {}))
            comp = Component(self.tool, gpt, params=params)
            self.model.add_component(comp)
            self.selected = comp
            self._render_props()
            self.redraw()
            self.on_change()
            return

        if self.tool == "wire":
            if self.pending_point is None:
                self.pending_point = gpt
            else:
                self.model.add_wire(self.pending_point, gpt)
                self.pending_point = None
                self.on_change()
            self._update_status()
            self.redraw()
            return

        if self.tool in TWO_CLICK_KINDS:
            if self.pending_point is None:
                self.pending_point = gpt
            else:
                params = dict(DEFAULTS.get(self.tool, {}))
                comp = Component(self.tool, self.pending_point, gpt, params=params)
                self.model.add_component(comp)
                self.pending_point = None
                self.selected = comp
                self._render_props()
                self.on_change()
            self._update_status()
            self.redraw()
            return

    def _on_drag(self, event):
        if self.tool != "select" or not isinstance(self.selected, Component) or not self._drag_start_pixel:
            return
        sx, sy = self._drag_start_pixel
        dgx = round((event.x - sx) / self.grid_px)
        dgy = round((event.y - sy) / self.grid_px)
        p1, p2 = self._drag_orig_points
        self.selected.p1 = (p1[0] + dgx, p1[1] + dgy)
        if p2 is not None:
            self.selected.p2 = (p2[0] + dgx, p2[1] + dgy)
        self.redraw()

    def _on_release(self, event):
        if isinstance(self.selected, Component) and self._drag_start_pixel:
            self.on_change()
        self._drag_start_pixel = None
        self._drag_orig_points = None

    # ------------------------------------------------------------------
    def redraw(self):
        c = self.canvas
        c.delete("all")
        w = c.winfo_width() or 800
        h = c.winfo_height() or 600
        if w < 10 or h < 10:
            self.after(50, self.redraw)
            return

        step = self.grid_px
        gx = self.origin_x % step
        while gx < w:
            major = (round((gx - self.origin_x) / step) % 5 == 0)
            c.create_line(gx, 0, gx, h, fill=GRID_COLOR_MAJOR if major else GRID_COLOR, width=1)
            gx += step
        gy = self.origin_y % step
        while gy < h:
            major = (round((gy - self.origin_y) / step) % 5 == 0)
            c.create_line(0, gy, w, gy, fill=GRID_COLOR_MAJOR if major else GRID_COLOR, width=1)
            gy += step

        for wr in self.model.wires:
            p1, p2 = self._grid_to_px(wr[0]), self._grid_to_px(wr[1])
            color = SELECT_COLOR if self.selected is wr else WIRE_COLOR
            c.create_line(*p1, *p2, fill=color, width=2)

        for comp in self.model.components:
            self._draw_component(comp)

        if self.pending_point is not None:
            px, py = self._grid_to_px(self.pending_point)
            c.create_oval(px - 6, py - 6, px + 6, py + 6, outline=SELECT_COLOR, width=2)
            c.create_text(px, py - 16, text=t("rf.hint.pending_marker"), fill=SELECT_COLOR,
                          font=FONT_MONO_TINY)

    def _draw_component(self, comp):
        c = self.canvas
        selected = (self.selected is comp)
        color = SELECT_COLOR if selected else COMP_COLOR

        if comp.kind == "PORT":
            draw_port_symbol(c, self._grid_to_px(comp.p1), comp.params.get("number", "?"),
                              color if selected else PORT_COLOR, selected)
            return

        if comp.kind == "GND":
            draw_ground_symbol(c, self._grid_to_px(comp.p1), color if selected else GND_COLOR)
            return

        if comp.p2 is None:
            p1 = self._grid_to_px(comp.p1)
            draw_load_symbol(c, comp.kind, p1, color, comp.label(), _value_summary(comp))
            return

        p1 = self._grid_to_px(comp.p1)
        p2 = self._grid_to_px(comp.p2)
        if comp.kind == "R":
            draw_resistor(c, p1, p2, color)
        elif comp.kind == "L":
            draw_inductor(c, p1, p2, color)
        elif comp.kind == "C":
            draw_capacitor(c, p1, p2, color)
        elif comp.kind == "TL":
            draw_transmission_line(c, p1, p2, color)
        else:
            c.create_line(*p1, *p2, fill=color, width=2)

        mx, my = (p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2
        dx, dy = p2[0] - p1[0], p2[1] - p1[1]
        length = max(1e-6, math.hypot(dx, dy))
        offx, offy = -dy / length, dx / length
        label_pt = (mx + offx * 18, my + offy * 18 - 6)
        value_pt = (mx + offx * 18, my + offy * 18 + 12)
        c.create_text(*label_pt, text=comp.label(), fill=TEXT_COLOR, font=FONT_MONO_SMALL)
        val = _value_summary(comp)
        if val:
            c.create_text(*value_pt, text=val, fill=TEXT_COLOR, font=FONT_MONO_TINY)

    # ------------------------------------------------------------------
    def _render_props(self):
        for w in self.props.winfo_children():
            w.destroy()

        ttk.Label(self.props, text=t("common.component_properties"), font=FONT_H2,
                  style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(10, 6))

        sel = self.selected
        if sel is None or isinstance(sel, tuple):
            ttk.Label(self.props, text=t("rf.props.none_selected"), style="CardBody.TLabel",
                      wraplength=190, justify="left").pack(anchor="w", padx=10)
            return

        entries = {}

        def add_field(label_key, key, initial, unit=""):
            row = ttk.Frame(self.props, style="Card.TFrame")
            row.pack(fill="x", padx=10, pady=3)
            ttk.Label(row, text=t(label_key), style="CardBody.TLabel").pack(anchor="w")
            var = tk.StringVar(value=str(initial))
            ent = ttk.Entry(row, textvariable=var, width=16)
            ent.pack(anchor="w", pady=(2, 0))
            entries[key] = (var, unit)

        if sel.kind == "GND":
            ttk.Label(self.props, text=t("rf.props.gnd_desc"), style="CardBody.TLabel",
                      wraplength=190, justify="left").pack(anchor="w", padx=10, pady=(0, 6))

        elif sel.kind == "PORT":
            row = ttk.Frame(self.props, style="Card.TFrame")
            row.pack(fill="x", padx=10, pady=3)
            ttk.Label(row, text=t("rf.props.port_number"), style="CardBody.TLabel").pack(anchor="w")
            num_var = tk.IntVar(value=sel.params.get("number", 1))
            ttk.Spinbox(row, from_=1, to=4, width=6, textvariable=num_var).pack(anchor="w")
            entries["number"] = (num_var, None)

            en_var = tk.BooleanVar(value=sel.params.get("enabled", True))
            ttk.Checkbutton(self.props, text=t("rf.props.enabled"), variable=en_var).pack(
                anchor="w", padx=10, pady=(6, 0))
            entries["enabled"] = (en_var, None)

            add_field("rf.props.ref_impedance", "z0", sel.params.get("z0", 50.0))

        elif sel.kind in ("R", "L", "C"):
            unit = {"R": "Ω", "L": "H", "C": "F"}[sel.kind]
            add_field("rf.props.value", "value", format_value(sel.params.get("value", 0.0), unit), unit)

        elif sel.kind == "TL":
            add_field("rf.props.z0_line", "z0", sel.params.get("z0", 50.0))
            add_field("rf.props.length_m", "length", sel.params.get("length", 0.03))
            add_field("rf.props.velocity_factor", "vf", sel.params.get("vf", 0.66))

        elif sel.kind == "LOAD_MATCHED":
            add_field("rf.props.ref_impedance", "z0", sel.params.get("z0", 50.0))

        elif sel.kind == "LOAD_R":
            add_field("rf.props.value", "value", format_value(sel.params.get("value", 50.0), "Ω"), "Ω")

        elif sel.kind == "LOAD_Z":
            add_field("rf.props.resistance_r", "r", sel.params.get("r", 50.0))
            add_field("rf.props.reactance_x", "x", sel.params.get("x", 0.0))

        else:
            ttk.Label(self.props, text=t("rf.props.no_params"), style="CardBody.TLabel").pack(
                anchor="w", padx=10)

        if entries:
            def apply():
                self._apply_props(sel, entries)

            ttk.Button(self.props, text=t("common.apply"), command=apply).pack(
                anchor="w", padx=10, pady=(10, 4))

        ttk.Button(self.props, text=t("rf.props.delete_selected"),
                   command=lambda: self._delete_selected()).pack(anchor="w", padx=10, pady=(4, 10))

    def _delete_selected(self):
        if self.selected is None:
            return
        if isinstance(self.selected, Component):
            if self.selected in self.model.components:
                self.model.components.remove(self.selected)
        elif isinstance(self.selected, tuple) and self.selected in self.model.wires:
            self.model.wires.remove(self.selected)
        self.selected = None
        self._render_props()
        self.redraw()
        self.on_change()

    def _apply_props(self, sel, entries):
        try:
            if sel.kind == "PORT":
                sel.params["number"] = int(entries["number"][0].get())
                sel.params["enabled"] = bool(entries["enabled"][0].get())
                sel.params["z0"] = parse_value(str(entries["z0"][0].get()))
            elif sel.kind in ("R", "L", "C"):
                unit = {"R": "Ω", "L": "H", "C": "F"}[sel.kind]
                sel.params["value"] = parse_value(str(entries["value"][0].get()), unit)
            elif sel.kind == "TL":
                sel.params["z0"] = float(entries["z0"][0].get())
                sel.params["length"] = float(entries["length"][0].get())
                sel.params["vf"] = float(entries["vf"][0].get())
            elif sel.kind == "LOAD_MATCHED":
                sel.params["z0"] = float(entries["z0"][0].get())
            elif sel.kind == "LOAD_R":
                sel.params["value"] = parse_value(str(entries["value"][0].get()), "Ω")
            elif sel.kind == "LOAD_Z":
                sel.params["r"] = float(entries["r"][0].get())
                sel.params["x"] = float(entries["x"][0].get())
        except (ValueError, KeyError):
            messagebox.showerror(t("rf.error.title"), t("rf.error.invalid_value"))
            return
        self.redraw()
        self.on_change()


def _unit_and_perp(p1, p2):
    dx, dy = p2[0] - p1[0], p2[1] - p1[1]
    length = max(1e-6, math.hypot(dx, dy))
    ux, uy = dx / length, dy / length
    return ux, uy, -uy, ux, length


def draw_resistor(canvas, p1, p2, color, body_frac=0.5, n_zig=6, amp=6):
    ux, uy, px, py, length = _unit_and_perp(p1, p2)
    body_len = length * body_frac
    lead_len = (length - body_len) / 2
    start = (p1[0] + ux * lead_len, p1[1] + uy * lead_len)
    end = (p2[0] - ux * lead_len, p2[1] - uy * lead_len)
    canvas.create_line(*p1, *start, fill=color, width=2)
    canvas.create_line(*end, *p2, fill=color, width=2)

    pts = [start]
    seg = body_len / n_zig
    for i in range(1, n_zig):
        along = start[0] + ux * seg * i, start[1] + uy * seg * i
        side = amp if i % 2 else -amp
        pts.append((along[0] + px * side, along[1] + py * side))
    pts.append(end)
    flat = [coord for pt in pts for coord in pt]
    canvas.create_line(*flat, fill=color, width=2, joinstyle="round")


def draw_inductor(canvas, p1, p2, color, body_frac=0.6, n_bumps=4, amp=8):
    ux, uy, px, py, length = _unit_and_perp(p1, p2)
    body_len = length * body_frac
    lead_len = (length - body_len) / 2
    start = (p1[0] + ux * lead_len, p1[1] + uy * lead_len)
    end = (p2[0] - ux * lead_len, p2[1] - uy * lead_len)
    canvas.create_line(*p1, *start, fill=color, width=2)
    canvas.create_line(*end, *p2, fill=color, width=2)

    n_pts = 60
    pts = []
    for i in range(n_pts + 1):
        frac = i / n_pts
        along = (start[0] + (end[0] - start[0]) * frac, start[1] + (end[1] - start[1]) * frac)
        bump = math.sin(frac * n_bumps * math.pi) if frac not in (0, 1) else 0
        bump = abs(bump)
        offset = amp * bump
        pts.append((along[0] + px * offset, along[1] + py * offset))
    flat = [coord for pt in pts for coord in pt]
    canvas.create_line(*flat, fill=color, width=2, smooth=True)


def draw_capacitor(canvas, p1, p2, color, gap=7, plate_half=10):
    ux, uy, px, py, length = _unit_and_perp(p1, p2)
    mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
    plate1_c = (mid[0] - ux * gap / 2, mid[1] - uy * gap / 2)
    plate2_c = (mid[0] + ux * gap / 2, mid[1] + uy * gap / 2)
    canvas.create_line(*p1, *plate1_c, fill=color, width=2)
    canvas.create_line(*plate2_c, *p2, fill=color, width=2)
    canvas.create_line(plate1_c[0] - px * plate_half, plate1_c[1] - py * plate_half,
                        plate1_c[0] + px * plate_half, plate1_c[1] + py * plate_half,
                        fill=color, width=3)
    canvas.create_line(plate2_c[0] - px * plate_half, plate2_c[1] - py * plate_half,
                        plate2_c[0] + px * plate_half, plate2_c[1] + py * plate_half,
                        fill=color, width=3)


def draw_transmission_line(canvas, p1, p2, color, half_w=7):
    ux, uy, px, py, length = _unit_and_perp(p1, p2)
    corners = [
        (p1[0] + px * half_w, p1[1] + py * half_w),
        (p2[0] + px * half_w, p2[1] + py * half_w),
        (p2[0] - px * half_w, p2[1] - py * half_w),
        (p1[0] - px * half_w, p1[1] - py * half_w),
    ]
    flat = [coord for pt in corners for coord in pt]
    canvas.create_polygon(*flat, outline=color, fill=BG, width=2)
    for frac in (0.35, 0.65):
        cx = p1[0] + (p2[0] - p1[0]) * frac
        cy = p1[1] + (p2[1] - p1[1]) * frac
        canvas.create_line(cx + px * half_w * 0.6, cy + py * half_w * 0.6,
                            cx - px * half_w * 0.6, cy - py * half_w * 0.6,
                            fill=color, width=1)


def draw_port_symbol(canvas, p, number, color, selected):
    px, py = p
    r = 9
    canvas.create_line(px, py, px - 14, py, fill=color, width=2)
    canvas.create_oval(px - r, py - r, px + r, py + r, outline=color, width=2,
                        fill=(SELECT_COLOR if selected else ""))
    canvas.create_text(px, py - 20, text=f"P{number}", fill=color, font=FONT_MONO_SMALL)


def draw_ground_symbol(canvas, p, color):
    px, py = p
    canvas.create_line(px, py, px, py + 12, fill=color, width=2)
    for i, half in enumerate((9, 6, 3)):
        yy = py + 12 + i * 5
        canvas.create_line(px - half, yy, px + half, yy, fill=color, width=2)


def draw_load_symbol(canvas, kind, p1, color, label, value_text):
    px, py = p1
    lead_end = (px, py + 16)
    canvas.create_line(px, py, *lead_end, fill=color, width=2)

    if kind == "LOAD_MATCHED":
        tip = (px, py + 30)
        canvas.create_polygon(px - 8, py + 16, px + 8, py + 16, tip[0], tip[1],
                              outline=color, fill=BG, width=2)
        canvas.create_line(px - 9, py + 30, px + 9, py + 30, fill=color, width=2)
    elif kind == "LOAD_R":
        draw_resistor(canvas, lead_end, (px, py + 44), color, body_frac=0.8, amp=5)
        canvas.create_line(px - 9, py + 44, px + 9, py + 44, fill=color, width=2)
    elif kind == "LOAD_Z":
        canvas.create_rectangle(px - 9, py + 16, px + 9, py + 34, outline=color, width=2, fill=BG)
        canvas.create_text(px, py + 25, text="Z", fill=color, font=FONT_MONO_SMALL)
        canvas.create_line(px - 9, py + 34, px + 9, py + 34, fill=color, width=2)
    elif kind == "OPEN":
        canvas.create_oval(lead_end[0] - 4, lead_end[1] - 4, lead_end[0] + 4, lead_end[1] + 4,
                            outline=color, width=2)
    elif kind == "SHORT":
        canvas.create_line(px - 11, py + 16, px + 11, py + 16, fill=color, width=4)

    canvas.create_text(px + 24, py + 8, text=label, fill=TEXT_COLOR, font=FONT_MONO_SMALL, anchor="w")
    if value_text:
        canvas.create_text(px + 24, py + 20, text=value_text, fill=TEXT_COLOR,
                            font=FONT_MONO_TINY, anchor="w")


def _draw_palette_icon(canvas, kind):
    color = COMP_COLOR
    cx, cy = 13, 10
    if kind == "select":
        canvas.create_polygon(4, 3, 4, 17, 8, 13, 11, 18, 13, 17, 10, 12, 15, 12,
                              fill=color, outline=color)
    elif kind == "wire":
        canvas.create_line(3, 10, 23, 10, fill=color, width=2)
    elif kind == "gnd":
        draw_ground_symbol(canvas, (cx, 2), color)
    elif kind == "port":
        canvas.create_oval(cx - 5, cy - 5, cx + 5, cy + 5, outline=PORT_COLOR, width=2)
    elif kind == "R":
        draw_resistor(canvas, (3, cy), (23, cy), color, amp=4)
    elif kind == "L":
        draw_inductor(canvas, (3, cy), (23, cy), color, amp=5, body_frac=0.8)
    elif kind == "C":
        draw_capacitor(canvas, (3, cy), (23, cy), color, plate_half=6)
    elif kind == "TL":
        draw_transmission_line(canvas, (4, cy), (22, cy), color, half_w=5)
    elif kind == "LOAD_MATCHED":
        canvas.create_polygon(cx - 6, 2, cx + 6, 2, cx, 16, outline=color, fill="", width=2)
    elif kind == "LOAD_R":
        draw_resistor(canvas, (cx, 1), (cx, 17), color, amp=4)
    elif kind == "LOAD_Z":
        canvas.create_rectangle(cx - 6, 3, cx + 6, 17, outline=color, width=2)
        canvas.create_text(cx, 10, text="Z", fill=color, font=("Consolas", 7, "bold"))
    elif kind == "OPEN":
        canvas.create_line(cx, 2, cx, 12, fill=color, width=2)
        canvas.create_oval(cx - 3, 12, cx + 3, 18, outline=color, width=2)
    elif kind == "SHORT":
        canvas.create_line(cx, 2, cx, 10, fill=color, width=2)
        canvas.create_line(cx - 7, 10, cx + 7, 10, fill=color, width=3)
    elif kind == "delete":
        canvas.create_line(5, 5, 21, 15, fill="#fc8181", width=2)
        canvas.create_line(5, 15, 21, 5, fill="#fc8181", width=2)


def _value_summary(comp):
    if comp.kind == "R":
        return format_value(comp.params.get("value", 0), "Ω")
    if comp.kind == "L":
        return format_value(comp.params.get("value", 0), "H")
    if comp.kind == "C":
        return format_value(comp.params.get("value", 0), "F")
    if comp.kind == "TL":
        return f"{comp.params.get('z0', 50):g}Ω {comp.params.get('length', 0) * 1000:g}mm"
    if comp.kind == "LOAD_R":
        return format_value(comp.params.get("value", 0), "Ω")
    if comp.kind == "LOAD_Z":
        return f"{comp.params.get('r', 0):g}{'+' if comp.params.get('x', 0) >= 0 else ''}{comp.params.get('x', 0):g}jΩ"
    if comp.kind == "LOAD_MATCHED":
        return f"{comp.params.get('z0', 50):g}Ω"
    return ""


def _point_segment_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t_ = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    projx, projy = ax + t_ * dx, ay + t_ * dy
    return ((px - projx) ** 2 + (py - projy) ** 2) ** 0.5
