"""
rf package - Multiport RF & Microwave simulation engine and GUI.

Layout:
    model.py    - circuit data model (grid points, wires, components, ports)
                  and netlist / graph construction (union-find node merging).
    solver.py   - general N-port nodal-analysis solver -> S-parameter matrix.
    tline.py    - ideal lossless transmission-line ABCD/Y model.
    simstate.py - shared simulation cache (the ONE circuit -> ONE sweep ->
                  ONE S-parameter dataset used by every view).
    smithchart.py - programmatic Smith chart grid + trace rendering.
    canvas_builder.py - the Circuit Builder schematic-capture canvas widget.
    vna_view.py - Virtual VNA (two independent display channels).
    results_view.py - S-Parameter Results table view.

This package is intentionally kept separate from tabs/ and GUI event
handlers: the math (model/solver/tline) never imports tkinter and can be
unit-tested standalone.
"""
