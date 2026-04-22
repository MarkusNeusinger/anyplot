""" pyplots.ai
venn-basic: Venn Diagram
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-29
"""

import numpy as np
import plotly.graph_objects as go


# Data: Survey about programming language preferences
# Set A: Python users (100 people)
# Set B: JavaScript users (80 people)
# Set C: SQL users (60 people)
set_labels = ["Python", "JavaScript", "SQL"]
set_sizes = [100, 80, 60]

# Overlaps
ab_overlap = 30  # Python & JavaScript
ac_overlap = 20  # Python & SQL
bc_overlap = 25  # JavaScript & SQL
abc_overlap = 10  # All three

# Calculate exclusive regions
only_a = set_sizes[0] - ab_overlap - ac_overlap + abc_overlap  # Python only
only_b = set_sizes[1] - ab_overlap - bc_overlap + abc_overlap  # JavaScript only
only_c = set_sizes[2] - ac_overlap - bc_overlap + abc_overlap  # SQL only
only_ab = ab_overlap - abc_overlap  # Python & JavaScript only
only_ac = ac_overlap - abc_overlap  # Python & SQL only
only_bc = bc_overlap - abc_overlap  # JavaScript & SQL only

# Circle positions in data coordinates (3-set Venn layout)
# Using equilateral triangle arrangement
r = 1.0  # Circle radius
angle_offset = np.pi / 2  # Start from top
angles = [angle_offset, angle_offset + 2 * np.pi / 3, angle_offset + 4 * np.pi / 3]
distance = 0.6  # Distance from center to circle centers
cx = [distance * np.cos(a) for a in angles]
cy = [distance * np.sin(a) for a in angles]

# Colors with transparency (Python palette)
colors = [
    "rgba(48, 105, 152, 0.5)",  # Python Blue
    "rgba(255, 212, 59, 0.5)",  # Python Yellow
    "rgba(77, 157, 89, 0.5)",  # Green
]
border_colors = ["#306998", "#FFD43B", "#4D9D59"]

# Generate circle points for scatter traces (filled circles)
theta = np.linspace(0, 2 * np.pi, 100)

# Create figure
fig = go.Figure()

# Add circles as filled scatter traces
for i in range(3):
    x_circle = cx[i] + r * np.cos(theta)
    y_circle = cy[i] + r * np.sin(theta)
    fig.add_trace(
        go.Scatter(
            x=x_circle,
            y=y_circle,
            fill="toself",
            fillcolor=colors[i],
            line={"color": border_colors[i], "width": 4},
            mode="lines",
            name=set_labels[i],
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Add set labels outside circles
label_positions = [
    (cx[0], cy[0] + r + 0.35, set_labels[0], set_sizes[0]),  # Python (top)
    (cx[1] - r - 0.35, cy[1], set_labels[1], set_sizes[1]),  # JavaScript (left)
    (cx[2] + r + 0.35, cy[2], set_labels[2], set_sizes[2]),  # SQL (right)
]

for x, y, label, size in label_positions:
    fig.add_annotation(
        x=x,
        y=y,
        text=f"<b>{label}</b><br>({size})",
        showarrow=False,
        font={"size": 28, "color": "#333333"},
        xanchor="center",
        yanchor="middle",
    )

# Calculate annotation positions for each region
# Center of top circle (Python only)
pos_a = (cx[0], cy[0] + 0.35)
# Center of bottom-left circle (JavaScript only)
pos_b = (cx[1] - 0.35, cy[1] - 0.2)
# Center of bottom-right circle (SQL only)
pos_c = (cx[2] + 0.35, cy[2] - 0.2)
# Python & JavaScript overlap
pos_ab = ((cx[0] + cx[1]) / 2 - 0.15, (cy[0] + cy[1]) / 2 + 0.15)
# Python & SQL overlap
pos_ac = ((cx[0] + cx[2]) / 2 + 0.15, (cy[0] + cy[2]) / 2 + 0.15)
# JavaScript & SQL overlap
pos_bc = ((cx[1] + cx[2]) / 2, (cy[1] + cy[2]) / 2 - 0.3)
# Center (all three)
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
        x=x, y=y, text=text, showarrow=False, font={"size": 24, "color": "#333333"}, xanchor="center", yanchor="middle"
    )

# Layout with equal aspect ratio
fig.update_layout(
    title={
        "text": "venn-basic · plotly · pyplots.ai", "font": {"size": 36, "color": "#333333"}, "x": 0.5, "xanchor": "center", "y": 0.95
    },
    template="plotly_white",
    showlegend=False,
    xaxis={"visible": False, "range": [-2.5, 2.5], "scaleanchor": "y", "scaleratio": 1},
    yaxis={"visible": False, "range": [-2.2, 2.5]},
    margin={"l": 40, "r": 40, "t": 100, "b": 40},
    paper_bgcolor="white",
    plot_bgcolor="white",
)

# Save as PNG (square format: 3600x3600) and HTML
fig.write_image("plot.png", width=1200, height=1200, scale=3)
fig.write_html("plot.html")
