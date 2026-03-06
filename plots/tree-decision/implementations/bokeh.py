"""pyplots.ai
tree-decision: Decision Tree Visualization with Probabilities
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-06
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import Label
from bokeh.plotting import figure, output_file, save


# Data - Two-stage investment decision tree
# EMV calculations (rollback):
#   Expand chance: 0.7*500 + 0.3*100 = 380
#   Expand decision: max(380, 300) = 380 -> Don't Expand pruned
#   Launch chance: 0.6*380 + 0.4*50 = 248
#   License chance: 0.5*250 + 0.5*120 = 185
#   Root decision: max(248, 185, 0) = 248 -> License & Do Nothing pruned

nodes = {
    "D1": {"type": "decision", "x": 80, "y": 540, "value": 248},
    "C1": {"type": "chance", "x": 300, "y": 790, "value": 248},
    "C2": {"type": "chance", "x": 300, "y": 350, "value": 185},
    "T1": {"type": "terminal", "x": 300, "y": 210, "value": 0},
    "D2": {"type": "decision", "x": 530, "y": 890, "value": 380},
    "T2": {"type": "terminal", "x": 530, "y": 670, "value": 50},
    "T3": {"type": "terminal", "x": 530, "y": 430, "value": 250},
    "T4": {"type": "terminal", "x": 530, "y": 280, "value": 120},
    "C3": {"type": "chance", "x": 760, "y": 950, "value": 380},
    "T5": {"type": "terminal", "x": 760, "y": 820, "value": 300},
    "T6": {"type": "terminal", "x": 990, "y": 1000, "value": 500},
    "T7": {"type": "terminal", "x": 990, "y": 900, "value": 100},
}

edges = [
    ("D1", "C1", "Launch Product", None, False),
    ("D1", "C2", "License Tech", None, True),
    ("D1", "T1", "Do Nothing", None, True),
    ("C1", "D2", "High Demand", 0.6, False),
    ("C1", "T2", "Low Demand", 0.4, False),
    ("C2", "T3", "Strong Partner", 0.5, True),
    ("C2", "T4", "Weak Partner", 0.5, True),
    ("D2", "C3", "Expand", None, False),
    ("D2", "T5", "Don't Expand", None, True),
    ("C3", "T6", "Success", 0.7, False),
    ("C3", "T7", "Failure", 0.3, False),
]

# Plot
p = figure(
    width=4800,
    height=2700,
    title="tree-decision · bokeh · pyplots.ai",
    x_range=(-40, 1120),
    y_range=(100, 1100),
    toolbar_location=None,
)

# Draw edges (right-angle connectors)
for src, dst, label, prob, pruned in edges:
    sx, sy = nodes[src]["x"], nodes[src]["y"]
    dx, dy = nodes[dst]["x"], nodes[dst]["y"]
    mid_x = (sx + dx) / 2

    alpha = 0.25 if pruned else 0.8
    dash = [12, 8] if pruned else "solid"
    lw = 4 if pruned else 6

    p.line(
        [sx, mid_x, mid_x, dx], [sy, sy, dy, dy], line_width=lw, line_alpha=alpha, line_color="#444444", line_dash=dash
    )

    # Branch label positioning
    branch_text = f"{label} (p={prob})" if prob is not None else label
    lbl = Label(
        x=mid_x,
        y=(sy + dy) / 2,
        text=branch_text,
        text_font_size="20pt",
        text_alpha=0.35 if pruned else 0.85,
        text_align="right",
        text_baseline="middle",
        x_offset=-14,
    )
    p.add_layout(lbl)

    # Pruned cross mark on the branch
    if pruned:
        cx = (sx + mid_x) / 2
        cy = sy
        cs = 18
        p.multi_line(
            [[cx - cs, cx + cs], [cx - cs, cx + cs]],
            [[cy - cs, cy + cs], [cy + cs, cy - cs]],
            line_width=5,
            line_color="#C0392B",
            line_alpha=0.75,
        )

# Draw nodes by type
decision_nodes = {k: v for k, v in nodes.items() if v["type"] == "decision"}
chance_nodes = {k: v for k, v in nodes.items() if v["type"] == "chance"}
terminal_nodes = {k: v for k, v in nodes.items() if v["type"] == "terminal"}

# Decision nodes - large squares
p.rect(
    [n["x"] for n in decision_nodes.values()],
    [n["y"] for n in decision_nodes.values()],
    width=65,
    height=65,
    fill_color="#306998",
    fill_alpha=0.92,
    line_color="#1B3D5E",
    line_width=4,
)

# Chance nodes - large circles
p.scatter(
    [n["x"] for n in chance_nodes.values()],
    [n["y"] for n in chance_nodes.values()],
    size=55,
    marker="circle",
    fill_color="#E8983E",
    fill_alpha=0.92,
    line_color="#B5722A",
    line_width=4,
)

# Terminal nodes - right-pointing triangles
p.scatter(
    [n["x"] for n in terminal_nodes.values()],
    [n["y"] for n in terminal_nodes.values()],
    size=48,
    marker="triangle",
    fill_color="#27AE60",
    fill_alpha=0.92,
    line_color="#1D8A4A",
    line_width=4,
    angle=np.pi / 2,
)

# Value labels on each node
for _nid, nd in nodes.items():
    if nd["type"] == "terminal":
        text = f"${nd['value']}K"
        y_off = 38
        fsize = "20pt"
    else:
        text = f"EMV ${nd['value']}K"
        y_off = 44
        fsize = "19pt"

    lbl = Label(
        x=nd["x"],
        y=nd["y"],
        text=text,
        text_font_size=fsize,
        text_font_style="bold",
        text_align="center",
        text_baseline="bottom",
        y_offset=y_off,
        text_color="#1A1A1A",
    )
    p.add_layout(lbl)

# Legend (top-left area)
legend_y_start = 1070
legend_spacing = 45
legend_x = 30

legend_entries = [
    ("decision", "#306998", "Decision Node"),
    ("chance", "#E8983E", "Chance Node"),
    ("terminal", "#27AE60", "Terminal Node"),
]

for i, (ntype, color, text) in enumerate(legend_entries):
    ly = legend_y_start - i * legend_spacing
    if ntype == "decision":
        p.scatter([legend_x], [ly], size=20, marker="square", fill_color=color, line_color="#333", line_width=2)
    elif ntype == "chance":
        p.scatter([legend_x], [ly], size=20, marker="circle", fill_color=color, line_color="#333", line_width=2)
    else:
        p.scatter(
            [legend_x],
            [ly],
            size=18,
            marker="triangle",
            fill_color=color,
            line_color="#333",
            line_width=2,
            angle=np.pi / 2,
        )
    p.add_layout(Label(x=legend_x, y=ly, text=text, text_font_size="20pt", x_offset=18, text_baseline="middle"))

# Pruned branch legend entry
ly = legend_y_start - 3 * legend_spacing
p.line([legend_x - 12, legend_x + 12], [ly, ly], line_width=4, line_dash=[10, 6], line_color="#444", line_alpha=0.4)
cs = 7
p.multi_line(
    [[legend_x - cs, legend_x + cs], [legend_x - cs, legend_x + cs]],
    [[ly - cs, ly + cs], [ly + cs, ly - cs]],
    line_width=4,
    line_color="#C0392B",
    line_alpha=0.7,
)
p.add_layout(
    Label(x=legend_x, y=ly, text="Pruned (suboptimal)", text_font_size="20pt", x_offset=22, text_baseline="middle")
)

# Style
p.title.text_font_size = "36pt"
p.title.text_font_style = "normal"
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.background_fill_color = "#FAFAFA"

# Save
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
