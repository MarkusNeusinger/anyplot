""" anyplot.ai
venn-basic: Venn Diagram
Library: plotly 6.7.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data: Programming language preference survey
set_labels = ["Python", "JavaScript", "SQL"]
set_sizes = [100, 80, 60]

ab_overlap = 30  # Python & JavaScript
ac_overlap = 20  # Python & SQL
bc_overlap = 25  # JavaScript & SQL
abc_overlap = 10  # All three

only_a = set_sizes[0] - ab_overlap - ac_overlap + abc_overlap
only_b = set_sizes[1] - ab_overlap - bc_overlap + abc_overlap
only_c = set_sizes[2] - ac_overlap - bc_overlap + abc_overlap
only_ab = ab_overlap - abc_overlap
only_ac = ac_overlap - abc_overlap
only_bc = bc_overlap - abc_overlap

# Radii proportional to set size (area ∝ count)
r_base = 1.0
radii = [r_base * np.sqrt(s / set_sizes[0]) for s in set_sizes]

# Equilateral triangle arrangement
angle_offset = np.pi / 2
angles = [angle_offset, angle_offset + 2 * np.pi / 3, angle_offset + 4 * np.pi / 3]
distance = 0.6
cx = [distance * np.cos(a) for a in angles]
cy = [distance * np.sin(a) for a in angles]

# Okabe-Ito palette with transparency
IMPRINT = ["#009E73", "#C475FD", "#4467A3"]
fill_colors = ["rgba(0,158,115,0.45)", "rgba(213,94,0,0.45)", "rgba(0,114,178,0.45)"]

hover_texts = [
    f"<b>Python</b><br>Total: {set_sizes[0]}<br>Only Python: {only_a}<br>Python ∩ JS: {only_ab}<br>Python ∩ SQL: {only_ac}",
    f"<b>JavaScript</b><br>Total: {set_sizes[1]}<br>Only JavaScript: {only_b}<br>JS ∩ Python: {only_ab}<br>JS ∩ SQL: {only_bc}",
    f"<b>SQL</b><br>Total: {set_sizes[2]}<br>Only SQL: {only_c}<br>SQL ∩ Python: {only_ac}<br>SQL ∩ JS: {only_bc}",
]

theta = np.linspace(0, 2 * np.pi, 200)
fig = go.Figure()

for i in range(3):
    r = radii[i]
    x_circle = cx[i] + r * np.cos(theta)
    y_circle = cy[i] + r * np.sin(theta)
    fig.add_trace(
        go.Scatter(
            x=x_circle,
            y=y_circle,
            fill="toself",
            fillcolor=fill_colors[i],
            line={"color": IMPRINT[i], "width": 3},
            mode="lines",
            name=set_labels[i],
            showlegend=False,
            hoverinfo="text",
            hovertext=hover_texts[i],
        )
    )

# Set labels outside each circle
label_positions = [
    (cx[0], cy[0] + radii[0] + 0.32, set_labels[0], set_sizes[0]),
    (cx[1] - radii[1] - 0.32, cy[1], set_labels[1], set_sizes[1]),
    (cx[2] + radii[2] + 0.32, cy[2], set_labels[2], set_sizes[2]),
]

for x, y, label, size in label_positions:
    fig.add_annotation(
        x=x,
        y=y,
        text=f"<b>{label}</b><br>({size})",
        showarrow=False,
        font={"size": 28, "color": INK},
        xanchor="center",
        yanchor="middle",
    )

# Region annotation positions
pos_a = (cx[0], cy[0] + 0.32)
pos_b = (cx[1] - 0.32, cy[1] - 0.18)
pos_c = (cx[2] + 0.32, cy[2] - 0.18)
pos_ab = ((cx[0] + cx[1]) / 2 - 0.12, (cy[0] + cy[1]) / 2 + 0.12)
pos_ac = ((cx[0] + cx[2]) / 2 + 0.12, (cy[0] + cy[2]) / 2 + 0.12)
pos_bc = ((cx[1] + cx[2]) / 2, (cy[1] + cy[2]) / 2 - 0.22)
pos_abc = (0, 0)

region_annotations = [
    (*pos_a, only_a, "Only<br>Python"),
    (*pos_b, only_b, "Only<br>JavaScript"),
    (*pos_c, only_c, "Only<br>SQL"),
    (*pos_ab, only_ab, ""),
    (*pos_ac, only_ac, ""),
    (*pos_bc, only_bc, ""),
    (*pos_abc, abc_overlap, "All"),
]

for x, y, value, desc in region_annotations:
    if desc:
        text = f"<b>{value}</b><br><span style='font-size:18px'>{desc}</span>"
    else:
        text = f"<b>{value}</b>"
    fig.add_annotation(
        x=x, y=y, text=text, showarrow=False, font={"size": 24, "color": INK}, xanchor="center", yanchor="middle"
    )

fig.update_layout(
    title={
        "text": "venn-basic · plotly · anyplot.ai",
        "font": {"size": 36, "color": INK},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.95,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    xaxis={"visible": False, "range": [-2.5, 2.5], "scaleanchor": "y", "scaleratio": 1},
    yaxis={"visible": False, "range": [-2.2, 2.5]},
    margin={"l": 40, "r": 40, "t": 100, "b": 40},
)

fig.write_image(f"plot-{THEME}.png", width=1200, height=1200, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
