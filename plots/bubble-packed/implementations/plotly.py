""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: plotly 6.5.2 | Python 3.14.3
Quality: 88/100 | Updated: 2026-02-23
"""

import numpy as np
import plotly.graph_objects as go


# Data - department budget allocation
budgets = {
    "Marketing": 2800000,
    "Engineering": 4500000,
    "Sales": 3200000,
    "Operations": 1800000,
    "HR": 950000,
    "Finance": 1200000,
    "R&D": 3800000,
    "Support": 1100000,
    "Legal": 650000,
    "IT": 2100000,
    "Product": 1500000,
    "QA": 880000,
    "Data Science": 1650000,
    "Design": 720000,
    "Admin": 450000,
}

labels = list(budgets.keys())
values = np.array(list(budgets.values()))
n = len(labels)

# Scale radii by area (sqrt) for accurate visual perception
radii = np.sqrt(values / values.max()) * 110

# Circle packing via force simulation
np.random.seed(42)
angles = np.linspace(0, 2 * np.pi, n, endpoint=False)
x_pos = np.cos(angles) * 150 + np.random.randn(n) * 30
y_pos = np.sin(angles) * 150 + np.random.randn(n) * 30

for _ in range(600):
    for i in range(n):
        fx, fy = -x_pos[i] * 0.01, -y_pos[i] * 0.01
        for j in range(n):
            if i != j:
                dx = x_pos[i] - x_pos[j]
                dy = y_pos[i] - y_pos[j]
                dist = np.sqrt(dx**2 + dy**2) + 0.1
                min_dist = radii[i] + radii[j] + 4
                if dist < min_dist:
                    force = (min_dist - dist) * 0.3
                    fx += (dx / dist) * force
                    fy += (dy / dist) * force
        x_pos[i] += fx
        y_pos[i] += fy

# Color palette - Python colors first, then colorblind-safe
colors = [
    "#306998",
    "#FFD43B",
    "#4E79A7",
    "#F28E2B",
    "#E15759",
    "#76B7B2",
    "#59A14F",
    "#EDC948",
    "#B07AA1",
    "#FF9DA7",
    "#9C755F",
    "#BAB0AC",
    "#5778A4",
    "#E49444",
    "#85B6B2",
]

# Format values for display
formatted = [f"${v / 1e6:.1f}M" if v >= 1e6 else f"${v / 1e3:.0f}K" for v in values]
total = f"${values.sum() / 1e6:.1f}M"

# Build figure with shapes for precise circles
fig = go.Figure()

# Draw circles as layout shapes for crisp rendering
shapes = []
for i in range(n):
    shapes.append(
        {
            "type": "circle",
            "x0": x_pos[i] - radii[i],
            "y0": y_pos[i] - radii[i],
            "x1": x_pos[i] + radii[i],
            "y1": y_pos[i] + radii[i],
            "fillcolor": colors[i],
            "opacity": 0.88,
            "line": {"color": "white", "width": 2.5},
        }
    )

# Invisible scatter for hover interactivity
fig.add_trace(
    go.Scatter(
        x=x_pos,
        y=y_pos,
        mode="markers",
        marker={"size": radii * 2, "color": "rgba(0,0,0,0)"},
        hovertemplate=[f"<b>{lbl}</b><br>{fval}<extra></extra>" for lbl, fval in zip(labels, formatted, strict=True)],
        showlegend=False,
    )
)

# Add text labels — only inside bubbles that are large enough
for i in range(n):
    font_size = max(9, min(18, int(radii[i] * 0.18)))
    if radii[i] > 35:
        text = f"<b>{labels[i]}</b><br>{formatted[i]}"
    else:
        text = f"<b>{labels[i]}</b>"
    fig.add_annotation(
        x=x_pos[i],
        y=y_pos[i],
        text=text,
        showarrow=False,
        font={"size": font_size, "color": "white", "family": "Arial"},
    )

# Layout
pad = 140
fig.update_layout(
    title={
        "text": "Department Budget Allocation · bubble-packed · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "title": "",
        "range": [x_pos.min() - pad, x_pos.max() + pad],
    },
    yaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "title": "",
        "scaleanchor": "x",
        "scaleratio": 1,
        "range": [y_pos.min() - pad, y_pos.max() + pad],
    },
    shapes=shapes,
    template="plotly_white",
    showlegend=False,
    margin={"l": 50, "r": 50, "t": 100, "b": 60},
    paper_bgcolor="white",
    plot_bgcolor="white",
)

# Add total budget annotation at bottom
fig.add_annotation(
    text=f"Total: {total}",
    xref="paper",
    yref="paper",
    x=0.5,
    y=-0.02,
    showarrow=False,
    font={"size": 18, "color": "#666", "family": "Arial"},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
