""" pyplots.ai
chord-basic: Basic Chord Diagram
Library: matplotlib 3.10.8 | Python 3.14
Quality: 87/100 | Created: 2026-04-06
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.path import Path


# Data: Migration flows between continents (in millions)
entities = ["Africa", "Asia", "Europe", "N. America", "S. America", "Oceania"]
n = len(entities)

flow_matrix = np.array(
    [
        [0, 12, 8, 5, 2, 1],  # From Africa
        [8, 0, 15, 10, 3, 4],  # From Asia
        [3, 10, 0, 8, 4, 2],  # From Europe
        [2, 6, 12, 0, 7, 3],  # From N. America
        [1, 2, 5, 8, 0, 1],  # From S. America
        [0, 3, 2, 2, 1, 0],  # From Oceania
    ]
)

# Colorblind-safe palette starting with Python Blue
colors = ["#306998", "#E69F00", "#009E73", "#D55E00", "#56B4E9", "#CC79A7"]

# Calculate entity totals and arc geometry
totals = flow_matrix.sum(axis=1) + flow_matrix.sum(axis=0)
total_flow = totals.sum()
gap_deg = 3
available_deg = 360 - gap_deg * n
arc_spans = (totals / total_flow) * available_deg

# Start angles (clockwise from top)
start_angles = np.zeros(n)
angle = 90
for i in range(n):
    start_angles[i] = angle
    angle -= arc_spans[i] + gap_deg

# Plot — square canvas for circular chart
fig, ax = plt.subplots(figsize=(12, 12), subplot_kw={"aspect": "equal"})
fig.set_facecolor("#FAFAFA")
ax.set_xlim(-1.45, 1.45)
ax.set_ylim(-1.45, 1.45)
ax.set_facecolor("#FAFAFA")
ax.axis("off")

radius = 1.0
arc_width = 0.09
inner_r = radius - arc_width

# Draw outer arcs
for i in range(n):
    theta1 = start_angles[i] - arc_spans[i]
    theta2 = start_angles[i]
    wedge = mpatches.Wedge(
        (0, 0), radius, theta1, theta2, width=arc_width, facecolor=colors[i], edgecolor="white", linewidth=2
    )
    ax.add_patch(wedge)

    # Label placement
    mid = np.radians((theta1 + theta2) / 2)
    lx, ly = (radius + 0.12) * np.cos(mid), (radius + 0.12) * np.sin(mid)
    mid_deg = np.degrees(mid) % 360
    ha = (
        "center"
        if mid_deg < 15 or mid_deg > 345 or 165 < mid_deg < 195
        else ("right" if 90 < mid_deg < 270 else "left")
    )
    ax.text(lx, ly, entities[i], fontsize=20, fontweight="bold", ha=ha, va="center", color=colors[i])

# Track angular position within each arc for chord placement
arc_cursors = start_angles.copy()
unit_angles = arc_spans / totals

# Sort flows by magnitude (draw largest last for visual hierarchy)
flows = [(i, j, flow_matrix[i, j]) for i in range(n) for j in range(n) if i != j and flow_matrix[i, j] > 0]
flows.sort(key=lambda f: f[2])

# Pre-compute chord positions to avoid cursor interference from draw order
min_chord_deg = 1.5  # minimum angular span for visibility
chord_params = []
pos_cursors = start_angles.copy()
for i in range(n):
    for j in range(n):
        if i != j and flow_matrix[i, j] > 0:
            flow = flow_matrix[i, j]
            src_span = max(flow * unit_angles[i], min_chord_deg)
            src_end = pos_cursors[i]
            src_start = src_end - src_span
            pos_cursors[i] = src_start

            tgt_span = max(flow * unit_angles[j], min_chord_deg)
            tgt_end = pos_cursors[j]
            tgt_start = tgt_end - tgt_span
            pos_cursors[j] = tgt_start

            chord_params.append((src_start, src_end, tgt_start, tgt_end, colors[i], flow))

# Sort by flow magnitude so largest chords render on top
chord_params.sort(key=lambda c: c[5])

# Draw chords using cubic Bezier paths
n_arc_pts = 30
ctrl_factor = 0.25

for src_start, src_end, tgt_start, tgt_end, color, flow in chord_params:
    s1, e1 = np.radians(src_start), np.radians(src_end)
    s2, e2 = np.radians(tgt_start), np.radians(tgt_end)

    arc1_t = np.linspace(s1, e1, n_arc_pts)
    arc1 = np.column_stack([inner_r * np.cos(arc1_t), inner_r * np.sin(arc1_t)])

    arc2_t = np.linspace(s2, e2, n_arc_pts)
    arc2 = np.column_stack([inner_r * np.cos(arc2_t), inner_r * np.sin(arc2_t)])

    # Build closed path: arc1 → bezier → arc2 → bezier → close
    verts = [arc1[0]]
    codes = [Path.MOVETO]

    for pt in arc1[1:]:
        verts.append(pt)
        codes.append(Path.LINETO)

    verts.extend([arc1[-1] * ctrl_factor, arc2[0] * ctrl_factor, arc2[0]])
    codes.extend([Path.CURVE4, Path.CURVE4, Path.CURVE4])

    for pt in arc2[1:]:
        verts.append(pt)
        codes.append(Path.LINETO)

    verts.extend([arc2[-1] * ctrl_factor, arc1[0] * ctrl_factor, arc1[0]])
    codes.extend([Path.CURVE4, Path.CURVE4, Path.CURVE4])

    # Scale alpha by flow magnitude for visual depth
    alpha = 0.40 + 0.30 * (flow / flow_matrix.max())
    patch = mpatches.PathPatch(Path(verts, codes), facecolor=color, edgecolor=color, linewidth=0.5, alpha=alpha)
    ax.add_patch(patch)

# Title
ax.set_title(
    "Continental Migration Flows · chord-basic · matplotlib · pyplots.ai",
    fontsize=24,
    fontweight="medium",
    pad=30,
    color="#333333",
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor="#FAFAFA")
