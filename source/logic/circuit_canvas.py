"""
logic/circuit_canvas.py - The Logic Circuit Builder canvas.

Click a tool, click the canvas to place a gate/switch/probe/mux/demux,
then use the Wire tool to connect an output pin to an input pin. Every
change - placing a part, wiring a pin, toggling a switch, moving or
deleting something - immediately re-evaluates the whole circuit and
recolors every wire and pin: green-ish for logic 1, gray for logic 0,
dashed light gray for floating/unconnected. There is no "Simulate"
button - propagation is cheap enough to redo on every click, which is
what gives the real-time feel.
"""
import tkinter as tk
from tkinter import ttk, messagebox

from i18n import t
from widgets import ScrollableFrame, FONT_BODY, FONT_H2, FONT_MONO
from drawing import draw_gate_symbol
from logic.circuit_model import LogicCircuitModel, LogicComponent, PIN_SPECS, GATE_KINDS, MUX_DEMUX_KINDS

BG = "#ffffff"
GRID_COLOR = "#eef0f3"
GRID_COLOR_MAJOR = "#e0e3e8"
BODY_FILL = "#f5f0e2"
OUTLINE = "#333333"
SELECT_COLOR = "#e08a2b"
TEXT_COLOR = "#555555"

HIGH_COLOR = "#1f6a5f"
LOW_COLOR = "#999999"
FLOAT_COLOR = "#c3c7cf"

FONT_PIN = ("Segoe UI", 8)
FONT_LABEL_SMALL = ("Consolas", 8, "bold")

BASE_GRID_PX = 24  # the "100% zoom" reference grid spacing

SIZES = {
    "INPUT": (56, 30),
    "OUTPUT": (56, 30),
    "NODE": (20, 20),
    "MUX2": (70, 90),
    "MUX4": (70, 150),
    "DEMUX2": (70, 90),
    "DEMUX4": (70, 150),
}
PIN_OFFSETS = {
    "INPUT": {"in": {}, "out": {"Y": (56, 15)}},
    "OUTPUT": {"in": {"A": (0, 15)}, "out": {}},
    "NODE": {"in": {"A": (0, 10)}, "out": {"Y": (20, 10)}},
    "MUX2": {"in": {"I0": (0, 15), "I1": (0, 75), "S": (35, 90)}, "out": {"Y": (70, 45)}},
    "MUX4": {"in": {"I0": (0, 15), "I1": (0, 55), "I2": (0, 95), "I3": (0, 135),
                     "S0": (23, 150), "S1": (47, 150)}, "out": {"Y": (70, 75)}},
    "DEMUX2": {"in": {"D": (0, 45), "S": (35, 90)}, "out": {"O0": (70, 15), "O1": (70, 75)}},
    "DEMUX4": {"in": {"D": (0, 75), "S0": (23, 150), "S1": (47, 150)},
               "out": {"O0": (70, 15), "O1": (70, 55), "O2": (70, 95), "O3": (70, 135)}},
}

TOOLS = [
    ("select", "logic.tool.select"),
    ("wire", "logic.tool.wire"),
    ("NODE", "logic.tool.node"),
    ("INPUT", "logic.tool.input"),
    ("OUTPUT", "logic.tool.output"),
    ("NOT", "logic.tool.not_"),
    ("AND", "logic.tool.and_"),
    ("OR", "logic.tool.or_"),
    ("NAND", "logic.tool.nand"),
    ("NOR", "logic.tool.nor"),
    ("XOR", "logic.tool.xor"),
    ("XNOR", "logic.tool.xnor"),
    ("MUX2", "logic.tool.mux2"),
    ("MUX4", "logic.tool.mux4"),
    ("DEMUX2", "logic.tool.demux2"),
    ("DEMUX4", "logic.tool.demux4"),
    ("delete", "logic.tool.delete"),
]


class LogicBuilderView(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Tab.TFrame")
        self.model = LogicCircuitModel()
        self.grid_px = BASE_GRID_PX
        self.origin_x = 50
        self.origin_y = 40
        self.tool = "select"
        self.pending_pin = None
        self.selected = None
        self._drag_start_pixel = None
        self._drag_orig_pos = None
        self._pan_start = None
        self.pin_values = {}
        self.eval_error = None
        self._hover_grid_pt = None

        self.columnconfigure(0, weight=1)
        self.rowconfigure(2, weight=1)

        intro = ttk.Label(self, text=t("logic.builder.intro"), style="CardBody.TLabel",
                           wraplength=1100, justify="left")
        intro.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 0))

        self._build_status_strip()

        paned = ttk.PanedWindow(self, orient="horizontal")
        paned.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))

        palette_holder = ttk.Frame(paned, style="Card.TFrame", width=230)
        canvas_holder = ttk.Frame(paned, style="Tab.TFrame")
        props_holder = ttk.Frame(paned, style="Card.TFrame", width=230)
        palette_holder.grid_propagate(False)
        props_holder.grid_propagate(False)
        paned.add(palette_holder, weight=0)
        paned.add(canvas_holder, weight=1)
        paned.add(props_holder, weight=0)

        self._build_palette(palette_holder)
        self._build_canvas(canvas_holder)
        self._build_props_panel(props_holder)

        self._recompute()

    def _build_status_strip(self):
        strip = ttk.Frame(self, style="Tab.TFrame")
        strip.grid(row=1, column=0, sticky="ew", padx=10, pady=(4, 4))
        self.status_lbl = ttk.Label(strip, text="", style="CardBody.TLabel",
                                     font=("Segoe UI", 9, "italic"))
        self.status_lbl.pack(side="left")
        self.error_lbl = ttk.Label(strip, text="", style="CardBody.TLabel",
                                    foreground="#b3413a", font=("Segoe UI", 9, "bold"))
        self.error_lbl.pack(side="left", padx=(16, 0))
        self._update_status()

    def _update_status(self):
        key = {
            "select": "logic.hint.select",
            "wire": "logic.hint.wire",
            "delete": "logic.hint.delete",
        }.get(self.tool, "logic.hint.place")
        text = t(key)
        if self.tool == "wire" and self.pending_pin is not None:
            text = t("logic.hint.wire_second")
        self.status_lbl.configure(text=text)

    def _build_palette(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=1)

        ttk.Label(parent, text=t("logic.palette.title"), font=FONT_H2,
                  style="CardTitle.TLabel").grid(row=0, column=0, sticky="w", padx=8, pady=(8, 4))

        scroller = ScrollableFrame(parent, style="Card.TFrame")
        scroller.grid(row=1, column=0, sticky="nsew", padx=4)
        pal = scroller.body

        self.tool_buttons = {}
        for kind, key in TOOLS:
            row = ttk.Frame(pal, style="Card.TFrame")
            row.pack(fill="x", padx=4, pady=1)
            icon = tk.Canvas(row, width=30, height=20, bg="#f4f4f4", highlightthickness=0)
            icon.pack(side="left", padx=(2, 4))
            _draw_palette_icon(icon, kind)
            b = tk.Button(row, text=t(key), anchor="w", relief="flat",
                          bg="#f4f4f4", fg="#222", activebackground="#dbe6ff",
                          activeforeground="#222", font=FONT_BODY,
                          command=lambda k=kind: self._set_tool(k))
            b.pack(side="left", fill="x", expand=True)
            self.tool_buttons[kind] = b

        clear_btn = ttk.Button(pal, text=t("logic.palette.clear_circuit"), command=self._clear_circuit)
        clear_btn.pack(fill="x", padx=8, pady=(10, 4))

        zoom_row = ttk.Frame(pal, style="Card.TFrame")
        zoom_row.pack(fill="x", padx=8, pady=(2, 2))
        ttk.Button(zoom_row, text="−", width=3, command=lambda: self._zoom_step(1 / 1.25)).pack(side="left")
        self.zoom_lbl = ttk.Label(zoom_row, text="100%", style="CardBody.TLabel", width=6, anchor="center")
        self.zoom_lbl.pack(side="left", padx=4)
        ttk.Button(zoom_row, text="+", width=3, command=lambda: self._zoom_step(1.25)).pack(side="left")
        reset_btn = ttk.Button(pal, text=t("logic.palette.reset_view"), command=self._reset_view)
        reset_btn.pack(fill="x", padx=8, pady=(4, 4))

        hint = ttk.Label(pal, text=t("logic.palette.hint"), font=("Segoe UI", 8),
                          style="CardBody.TLabel", wraplength=190, justify="left")
        hint.pack(anchor="w", padx=8, pady=(8, 10))

        self._highlight_tool()

    def _clear_circuit(self):
        if not self.model.components:
            return
        if not messagebox.askyesno(t("logic.error.title"), t("logic.palette.clear_confirm")):
            return
        self.model.clear()
        self.selected = None
        self.pending_pin = None
        self._render_props()
        self._recompute()

    def _set_tool(self, kind):
        self.tool = kind
        self.pending_pin = None
        self._hover_grid_pt = None
        self._highlight_tool()
        self._update_status()
        self.redraw()

    def _highlight_tool(self):
        for kind, btn in self.tool_buttons.items():
            btn.configure(bg="#dbe6ff" if kind == self.tool else "#f4f4f4")

    def _build_canvas(self, parent):
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(parent, bg=BG, highlightthickness=1, highlightbackground="#ddd")
        self.canvas.grid(row=0, column=0, sticky="nsew")

        self.canvas.bind("<Configure>", lambda e: self.redraw())
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<B1-Motion>", self._on_drag)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)
        self.canvas.bind("<Button-3>", self._start_pan)
        self.canvas.bind("<B3-Motion>", self._do_pan)
        self.canvas.bind("<MouseWheel>", self._on_wheel)
        self.canvas.bind("<Button-4>", lambda e: self._zoom_step(1.1, e))   # Linux scroll up
        self.canvas.bind("<Button-5>", lambda e: self._zoom_step(1 / 1.1, e))  # Linux scroll down
        self.canvas.bind("<Motion>", self._on_hover)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Delete>", lambda e: self._delete_selected())
        self.canvas.bind("<BackSpace>", lambda e: self._delete_selected())
        self.canvas.bind("<Escape>", lambda e: self._cancel_pending())
        self.canvas.bind("<Enter>", lambda e: self.canvas.focus_set())

    def _cancel_pending(self):
        self.pending_pin = None
        self._update_status()
        self.redraw()

    def _build_props_panel(self, parent):
        self.props = parent
        self.props.columnconfigure(0, weight=1)
        self._render_props()

    def _grid_to_px(self, p):
        gx, gy = p
        return self.origin_x + gx * self.grid_px, self.origin_y + gy * self.grid_px

    def _px_to_nearest_grid(self, x, y):
        gx = round((x - self.origin_x) / self.grid_px)
        gy = round((y - self.origin_y) / self.grid_px)
        return (gx, gy)

    def _start_pan(self, event):
        self._pan_start = (event.x, event.y, self.origin_x, self.origin_y)

    def _do_pan(self, event):
        if not self._pan_start:
            return
        sx, sy, ox, oy = self._pan_start
        self.origin_x = ox + (event.x - sx)
        self.origin_y = oy + (event.y - sy)
        self.redraw()

    @property
    def scale(self):
        return self.grid_px / BASE_GRID_PX

    def _on_wheel(self, event):
        factor = 1.1 if event.delta > 0 else 1 / 1.1
        self._zoom_step(factor, event)

    def _zoom_step(self, factor, event=None):
        old_grid = self.grid_px
        new_grid = max(8, min(72, self.grid_px * factor))
        if new_grid == old_grid:
            return
        # zoom around the mouse pointer (or canvas center if triggered from
        # a button, e.g. the +/- controls) so the thing you're looking at
        # stays under the cursor instead of the view jumping.
        cx = event.x if event is not None else self.canvas.winfo_width() / 2
        cy = event.y if event is not None else self.canvas.winfo_height() / 2
        world_x = (cx - self.origin_x) / old_grid
        world_y = (cy - self.origin_y) / old_grid
        self.grid_px = new_grid
        self.origin_x = cx - world_x * new_grid
        self.origin_y = cy - world_y * new_grid
        self.zoom_lbl.configure(text=f"{round(self.scale * 100)}%")
        self.redraw()

    def _reset_view(self):
        self.grid_px = BASE_GRID_PX
        self.origin_x = 50
        self.origin_y = 40
        self.zoom_lbl.configure(text="100%")
        self.redraw()

    def _on_hover(self, event):
        if self.tool == "select" or self.tool == "delete":
            new_pt = None
        elif self.tool == "wire":
            new_pt = None  # pin snapping (drawn via pending marker) is enough
        else:
            new_pt = self._px_to_nearest_grid(event.x, event.y)
        if new_pt != self._hover_grid_pt:
            self._hover_grid_pt = new_pt
            self.redraw()

    def _on_leave(self, _event=None):
        if self._hover_grid_pt is not None:
            self._hover_grid_pt = None
            self.redraw()

    def _pin_positions(self, comp):
        ax, ay = self._grid_to_px(comp.pos)
        s = self.scale
        if comp.kind in GATE_KINDS:
            n_in = 1 if comp.kind == "NOT" else 2
            labels = ["A"] if n_in == 1 else ["A", "B"]
            pins = draw_gate_symbol(_NullCanvas(), comp.kind, ax, ay, w=90 * s, h=60 * s,
                                     in_labels=labels, show_pin_labels=False, stub=16 * s)
            return {"in": {lbl: p for lbl, p in zip(labels, pins["inputs"])},
                    "out": {"Y": pins["output"]}}
        offs = PIN_OFFSETS[comp.kind]
        return {
            "in": {name: (ax + dx * s, ay + dy * s) for name, (dx, dy) in offs["in"].items()},
            "out": {name: (ax + dx * s, ay + dy * s) for name, (dx, dy) in offs["out"].items()},
        }

    def _all_pins(self):
        for comp in self.model.components:
            pins = self._pin_positions(comp)
            for name, p in pins["in"].items():
                yield comp, name, False, p
            for name, p in pins["out"].items():
                yield comp, name, True, p

    def _snap_x_to_grid(self, x):
        return self.origin_x + round((x - self.origin_x) / self.grid_px) * self.grid_px

    def _hit_pin(self, x, y, want_output=None, tol=None):
        tol = (tol if tol is not None else 10) * self.scale
        best = None
        best_d = tol
        for comp, name, is_out, (px, py) in self._all_pins():
            if want_output is not None and is_out != want_output:
                continue
            d = ((x - px) ** 2 + (y - py) ** 2) ** 0.5
            if d < best_d:
                best_d = d
                best = (comp, name, is_out)
        return best

    def _hit_component(self, x, y, tol=6):
        best = None
        best_d = 1e9
        s = self.scale
        for comp in self.model.components:
            ax, ay = self._grid_to_px(comp.pos)
            if comp.kind in GATE_KINDS:
                w, h = 90 * s, 60 * s
            else:
                bw, bh = SIZES[comp.kind]
                w, h = bw * s, bh * s
            if ax - tol <= x <= ax + w + tol and ay - tol <= y <= ay + h + tol:
                area = w * h
                if area < best_d:
                    best_d = area
                    best = comp
        return best

    def _hit_wire(self, x, y, tol=8):
        for w in self.model.wires:
            src_comp = self.model.get_component(w["src"][0])
            dst_comp = self.model.get_component(w["dst"][0])
            if src_comp is None or dst_comp is None:
                continue
            sx, sy = self._pin_positions(src_comp)["out"].get(w["src"][1], (None, None))
            dx, dy = self._pin_positions(dst_comp)["in"].get(w["dst"][1], (None, None))
            if sx is None or dx is None:
                continue
            mid_x = self._snap_x_to_grid((sx + dx) / 2)
            segs = [(sx, sy, mid_x, sy), (mid_x, sy, mid_x, dy), (mid_x, dy, dx, dy)]
            for ax, ay, bx, by in segs:
                if _point_segment_dist(x, y, ax, ay, bx, by) < tol:
                    return w
        return None

    def _on_click(self, event):
        self.canvas.focus_set()
        x, y = event.x, event.y

        if self.tool == "select":
            hit_pin = self._hit_pin(x, y)
            if hit_pin is not None:
                self.selected = None
                self._render_props()
                self.redraw()
                return
            hit = self._hit_component(x, y)
            if hit is None:
                hit = self._hit_wire(x, y)
            self.selected = hit
            if isinstance(hit, LogicComponent):
                if hit.kind == "INPUT":
                    hit.params["value"] = 1 - hit.params.get("value", 0)
                    self._recompute()
                self._drag_start_pixel = (x, y)
                self._drag_orig_pos = hit.pos
            self._render_props()
            self.redraw()
            return

        if self.tool == "delete":
            hit = self._hit_component(x, y) or self._hit_wire(x, y)
            if hit is not None:
                if isinstance(hit, LogicComponent):
                    self.model.remove_component(hit)
                else:
                    self.model.remove_wire(hit)
                if self.selected is hit:
                    self.selected = None
                self._render_props()
                self._recompute()
            return

        if self.tool == "wire":
            hit_pin = self._hit_pin(x, y)
            if hit_pin is None:
                return
            comp, name, is_out = hit_pin
            if self.pending_pin is None:
                if not is_out:
                    return
                self.pending_pin = (comp.id, name, True)
            else:
                src_id, src_name, _ = self.pending_pin
                if is_out:
                    self.pending_pin = (comp.id, name, True)
                else:
                    self.model.add_wire((src_id, src_name), (comp.id, name))
                    self.pending_pin = None
                    self._update_status()
                    self._recompute()
                    return
            self._update_status()
            self.redraw()
            return

        gpt = self._px_to_nearest_grid(x, y)
        comp = LogicComponent(self.tool, gpt)
        self.model.add_component(comp)
        self.selected = comp
        self._render_props()
        self._recompute()

    def _on_drag(self, event):
        if self.tool != "select" or not isinstance(self.selected, LogicComponent) or not self._drag_start_pixel:
            return
        sx, sy = self._drag_start_pixel
        dgx = round((event.x - sx) / self.grid_px)
        dgy = round((event.y - sy) / self.grid_px)
        ox, oy = self._drag_orig_pos
        self.selected.pos = (ox + dgx, oy + dgy)
        self.redraw()

    def _on_release(self, event):
        self._drag_start_pixel = None
        self._drag_orig_pos = None

    def _delete_selected(self):
        if self.selected is None:
            return
        if isinstance(self.selected, LogicComponent):
            self.model.remove_component(self.selected)
        else:
            self.model.remove_wire(self.selected)
        self.selected = None
        self._render_props()
        self._recompute()

    def _recompute(self):
        self.pin_values, self.eval_error = self.model.evaluate()
        if self.eval_error == "cycle":
            self.error_lbl.configure(text=t("logic.error.cycle"))
        else:
            self.error_lbl.configure(text="")
        self.redraw()

    def _wire_color(self, val):
        if val == 1:
            return HIGH_COLOR
        if val == 0:
            return LOW_COLOR
        return FLOAT_COLOR

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

        for wire in self.model.wires:
            src_comp = self.model.get_component(wire["src"][0])
            dst_comp = self.model.get_component(wire["dst"][0])
            if src_comp is None or dst_comp is None:
                continue
            sx, sy = self._pin_positions(src_comp)["out"].get(wire["src"][1], (None, None))
            dx, dy = self._pin_positions(dst_comp)["in"].get(wire["dst"][1], (None, None))
            if sx is None or dx is None:
                continue
            val = self.pin_values.get(wire["src"])
            color = SELECT_COLOR if self.selected is wire else self._wire_color(val)
            dash = None if val is not None else (4, 2)
            mid_x = self._snap_x_to_grid((sx + dx) / 2)
            c.create_line(sx, sy, mid_x, sy, mid_x, dy, dx, dy, fill=color, width=2, dash=dash)

        for comp in self.model.components:
            self._draw_component(comp)

        if self.tool == "wire" and self.pending_pin is not None:
            comp = self.model.get_component(self.pending_pin[0])
            if comp is not None:
                px, py = self._pin_positions(comp)["out"].get(self.pending_pin[1], (None, None))
                if px is not None:
                    c.create_oval(px - 6, py - 6, px + 6, py + 6, outline=SELECT_COLOR, width=2)

        if self._hover_grid_pt is not None:
            hx, hy = self._grid_to_px(self._hover_grid_pt)
            r = 5
            c.create_line(hx - r * 2, hy, hx + r * 2, hy, fill="#9fb8e8", width=1)
            c.create_line(hx, hy - r * 2, hx, hy + r * 2, fill="#9fb8e8", width=1)
            c.create_oval(hx - r, hy - r, hx + r, hy + r, outline="#3b6fd1", width=2)

    def _draw_component(self, comp):
        c = self.canvas
        selected = (self.selected is comp)
        outline = SELECT_COLOR if selected else OUTLINE
        ax, ay = self._grid_to_px(comp.pos)
        s = self.scale
        stub = 16 * s

        if comp.kind in GATE_KINDS:
            n_in = 1 if comp.kind == "NOT" else 2
            labels = ["A"] if n_in == 1 else ["A", "B"]
            draw_gate_symbol(c, comp.kind, ax, ay, w=90 * s, h=60 * s, in_labels=labels,
                              fill=(BODY_FILL if not selected else "#fbe7cf"), stub=stub)
            if selected:
                c.create_rectangle(ax, ay, ax + 90 * s, ay + 60 * s, outline=SELECT_COLOR,
                                    width=2, dash=(3, 2))
            pins = self._pin_positions(comp)
            for name, (px, py) in pins["in"].items():
                val = self.pin_values.get((comp.id, name))
                c.create_line(px - stub, py, px, py, fill=self._wire_color(val), width=3)
            for name, (px, py) in pins["out"].items():
                val = self.pin_values.get((comp.id, name))
                c.create_line(px, py, px + stub, py, fill=self._wire_color(val), width=3)
            return

        if comp.kind == "NODE":
            w, h = SIZES["NODE"][0] * s, SIZES["NODE"][1] * s
            val = self.pin_values.get((comp.id, "A"))
            cx, cy = ax + w / 2, ay + h / 2
            c.create_line(ax, cy, cx, cy, fill=self._wire_color(val), width=3)
            c.create_line(cx, cy, ax + w, cy, fill=self._wire_color(val), width=3)
            r = min(w, h) * 0.28
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=outline, width=2,
                          fill=self._wire_color(val))
            return

        if comp.kind == "INPUT":
            w, h = SIZES["INPUT"][0] * s, SIZES["INPUT"][1] * s
            val = comp.params.get("value", 0)
            fill = HIGH_COLOR if val else "#e4e4e4"
            c.create_rectangle(ax, ay, ax + w, ay + h, outline=outline, width=2, fill=fill)
            c.create_text(ax + w / 2, ay + h / 2, text=str(val), fill=("white" if val else "#444"),
                          font=("Segoe UI", 11, "bold"))
            if comp.params.get("label"):
                c.create_text(ax + w / 2, ay - 9, text=comp.params["label"], fill=TEXT_COLOR, font=FONT_LABEL_SMALL)
            px, py = ax + w, ay + h / 2
            c.create_line(px, py, px + stub, py, fill=self._wire_color(val), width=3)
            return

        if comp.kind == "OUTPUT":
            w, h = SIZES["OUTPUT"][0] * s, SIZES["OUTPUT"][1] * s
            val = self.pin_values.get((comp.id, "A"))
            r = h / 2 - 2
            cx, cy = ax + w - r - 2, ay + h / 2
            c.create_line(ax, cy, cx - r, cy, fill=self._wire_color(val), width=3)
            led_fill = HIGH_COLOR if val == 1 else ("#e4e4e4" if val == 0 else "#ffffff")
            dash = None if val is not None else (3, 2)
            c.create_oval(cx - r, cy - r, cx + r, cy + r, outline=outline, width=2, fill=led_fill, dash=dash)
            label = comp.params.get("label") or "Y"
            c.create_text(ax + w / 2, ay - 9, text=label, fill=TEXT_COLOR, font=FONT_LABEL_SMALL)
            val_txt = "?" if val is None else str(val)
            c.create_text(cx, cy, text=val_txt, fill=("white" if val == 1 else "#444"),
                          font=("Segoe UI", 9, "bold"))
            return

        bw, bh = SIZES[comp.kind]
        w, h = bw * s, bh * s
        is_mux = comp.kind.startswith("MUX")
        if is_mux:
            pts = [ax, ay + 5 * s, ax, ay + h - 5 * s, ax + w, ay + h * 0.72, ax + w, ay + h * 0.28]
        else:
            pts = [ax, ay + h * 0.28, ax, ay + h * 0.72, ax + w, ay + h - 5 * s, ax + w, ay + 5 * s]
        c.create_polygon(pts, fill=(BODY_FILL if not selected else "#fbe7cf"), outline=outline, width=2)
        c.create_text(ax + w / 2, ay + h / 2, text=comp.kind[:-1] if comp.kind[-1].isdigit() else comp.kind,
                      fill="#333", font=("Segoe UI", 8, "bold"))

        pins = self._pin_positions(comp)
        pin_stub = 14 * s
        for name, (px, py) in pins["in"].items():
            val = self.pin_values.get((comp.id, name))
            is_select = name.startswith("S")
            if is_select:
                c.create_line(px, py - pin_stub, px, py, fill=self._wire_color(val), width=3)
                c.create_text(px, py - pin_stub - 6, text=name, fill=TEXT_COLOR, font=FONT_PIN)
            else:
                c.create_line(px - pin_stub, py, px, py, fill=self._wire_color(val), width=3)
                c.create_text(px - pin_stub - 4, py, text=name, fill=TEXT_COLOR, font=FONT_PIN, anchor="e")
        for name, (px, py) in pins["out"].items():
            val = self.pin_values.get((comp.id, name))
            c.create_line(px, py, px + pin_stub, py, fill=self._wire_color(val), width=3)
            c.create_text(px + pin_stub + 4, py, text=name, fill=TEXT_COLOR, font=FONT_PIN, anchor="w")

    def _render_props(self):
        for w in self.props.winfo_children():
            w.destroy()
        ttk.Label(self.props, text=t("logic.props.title"), font=FONT_H2,
                  style="CardTitle.TLabel").pack(anchor="w", padx=10, pady=(10, 6))

        sel = self.selected
        if not isinstance(sel, LogicComponent):
            ttk.Label(self.props, text=t("logic.props.none_selected"), style="CardBody.TLabel",
                      wraplength=190, justify="left").pack(anchor="w", padx=10)
            return

        ttk.Label(self.props, text=sel.kind, font=FONT_MONO, style="CardBody.TLabel").pack(
            anchor="w", padx=10, pady=(0, 6))

        row = ttk.Frame(self.props, style="Card.TFrame")
        row.pack(fill="x", padx=10, pady=3)
        ttk.Label(row, text=t("logic.props.label"), style="CardBody.TLabel").pack(anchor="w")
        label_var = tk.StringVar(value=sel.params.get("label", ""))
        ent = ttk.Entry(row, textvariable=label_var, width=16)
        ent.pack(anchor="w", pady=(2, 0))

        def apply_label(_evt=None):
            sel.params["label"] = label_var.get()
            self.redraw()

        ent.bind("<Return>", apply_label)
        ent.bind("<FocusOut>", apply_label)

        if sel.kind == "INPUT":
            hint = t("logic.props.input_desc")
        elif sel.kind == "OUTPUT":
            hint = t("logic.props.output_desc")
        elif sel.kind == "NODE":
            hint = t("logic.props.node_desc")
        elif sel.kind in MUX_DEMUX_KINDS:
            hint = t("logic.props.desc." + sel.kind)
        else:
            hint = t("logic.props.gate_desc")
        ttk.Label(self.props, text=hint, style="CardBody.TLabel", wraplength=190,
                  justify="left").pack(anchor="w", padx=10, pady=(6, 6))

        ttk.Button(self.props, text=t("rf.props.delete_selected"),
                   command=self._delete_selected).pack(anchor="w", padx=10, pady=(6, 10))


class _NullCanvas:
    def create_polygon(self, *a, **k):
        pass

    def create_line(self, *a, **k):
        pass

    def create_oval(self, *a, **k):
        pass

    def create_text(self, *a, **k):
        pass


def _draw_palette_icon(canvas, kind):
    if kind == "select":
        canvas.create_polygon(4, 3, 4, 17, 8, 13, 11, 18, 13, 17, 10, 12, 15, 12,
                              fill="#333", outline="#333")
    elif kind == "wire":
        canvas.create_line(3, 10, 27, 10, fill="#333", width=2)
    elif kind == "delete":
        canvas.create_line(5, 4, 25, 16, fill="#b3413a", width=2)
        canvas.create_line(5, 16, 25, 4, fill="#b3413a", width=2)
    elif kind == "INPUT":
        canvas.create_rectangle(4, 3, 22, 17, outline="#333", width=2, fill=HIGH_COLOR)
    elif kind == "NODE":
        canvas.create_line(3, 10, 27, 10, fill="#333", width=2)
        canvas.create_oval(11, 6, 19, 14, outline="#333", width=2, fill="#666")
    elif kind == "OUTPUT":
        canvas.create_oval(8, 3, 22, 17, outline="#333", width=2, fill="#e4e4e4")
    elif kind in GATE_KINDS:
        n_in = 1 if kind == "NOT" else 2
        draw_gate_symbol(canvas, kind, 1, 1, w=26, h=18, show_pin_labels=False,
                          in_labels=(["A"] if n_in == 1 else ["A", "B"]), stub=3)
    elif kind in MUX_DEMUX_KINDS:
        is_mux = kind.startswith("MUX")
        if is_mux:
            pts = [4, 2, 4, 18, 26, 14, 26, 6]
        else:
            pts = [4, 6, 4, 14, 26, 18, 26, 2]
        canvas.create_polygon(pts, fill=BODY_FILL, outline="#333", width=1)


def _point_segment_dist(px, py, ax, ay, bx, by):
    dx, dy = bx - ax, by - ay
    length_sq = dx * dx + dy * dy
    if length_sq == 0:
        return ((px - ax) ** 2 + (py - ay) ** 2) ** 0.5
    t_ = max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / length_sq))
    projx, projy = ax + t_ * dx, ay + t_ * dy
    return ((px - projx) ** 2 + (py - projy) ** 2) ** 0.5
