""" pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: plotly 6.5.2 | Python 3.14.3
Quality: 91/100 | Updated: 2026-02-23
"""

import numpy as np
import plotly.graph_objects as go


# Data — department budgets with functional groupings
departments = [
    ("Engineering", 4500000, "Technology"),
    ("R&D", 3800000, "Technology"),
    ("IT", 2100000, "Technology"),
    ("Data Science", 1650000, "Technology"),
    ("QA", 880000, "Technology"),
    ("Sales", 3200000, "Revenue"),
    ("Marketing", 2800000, "Revenue"),
    ("Operations", 1800000, "Operations"),
    ("Finance", 1200000, "Operations"),
    ("Support", 1100000, "Operations"),
    ("Admin", 450000, "Operations"),
    ("HR", 950000, "Corporate"),
    ("Legal", 650000, "Corporate"),
    ("Product", 1500000, "Corporate"),
    ("Design", 720000, "Corporate"),
]

labels = [d[0] for d in departments]
values = np.array([d[1] for d in departments])
groups = [d[2] for d in departments]
n = len(labels)

# Group colors — colorblind-safe palette starting with Python Blue
group_colors = {"Technology": "#306998", "Revenue": "#E69F00", "Operations": "#009E73", "Corporate": "#CC79A7"}

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

# Weight-based centering for better visual balance (larger bubbles pull center)
area_weights = radii**2
x_pos -= np.average(x_pos, weights=area_weights)
y_pos -= np.average(y_pos, weights=area_weights)

# Format values for display
formatted = [f"${v / 1e6:.1f}M" if v >= 1e6 else f"${v / 1e3:.0f}K" for v in values]
shares = [f"{v / values.sum() * 100:.1f}" for v in values]
total = f"${values.sum() / 1e6:.1f}M"

# Tight axis ranges for better canvas utilization
pad = 15
x_lo = (x_pos - radii).min() - pad
x_hi = (x_pos + radii).max() + pad
y_lo = (y_pos - radii).min() - pad
y_hi = (y_pos + radii).max() + pad

# Convert data-coordinate radii to pixel marker diameters
fig_w, fig_h = 1600, 900
m_l, m_r, m_t, m_b = 35, 35, 85, 85
plot_w, plot_h = fig_w - m_l - m_r, fig_h - m_t - m_b
px_per_unit = min(plot_w / (x_hi - x_lo), plot_h / (y_hi - y_lo))
marker_diameters = 2 * radii * px_per_unit

# Text colors for contrast against group backgrounds
text_colors = []
for g in groups:
    c = group_colors[g]
    lum = 0.299 * int(c[1:3], 16) + 0.587 * int(c[3:5], 16) + 0.114 * int(c[5:7], 16)
    text_colors.append("white" if lum < 160 else "#333")

# Build figure — one trace per group for idiomatic Plotly legend
fig = go.Figure()

for group_name, group_color in group_colors.items():
    idx = [i for i in range(n) if groups[i] == group_name]
    fig.add_trace(
        go.Scatter(
            x=x_pos[idx],
            y=y_pos[idx],
            mode="markers",
            name=group_name,
            marker={
                "size": marker_diameters[idx],
                "sizemode": "diameter",
                "color": group_color,
                "opacity": 0.9,
                "line": {"color": "white", "width": 2.5},
            },
            text=[labels[i] for i in idx],
            customdata=np.column_stack(
                [[formatted[i] for i in idx], [shares[i] for i in idx], [groups[i] for i in idx]]
            ),
            hovertemplate="<b>%{text}</b> (%{customdata[2]})<br>Budget: %{customdata[0]}<br>Share: %{customdata[1]}%<extra></extra>",
        )
    )

# Text labels inside bubbles — minimum 14pt for readability
for i in range(n):
    font_size = max(14, min(20, int(radii[i] * 0.22)))
    label_text = f"<b>{labels[i]}</b><br>{formatted[i]}" if radii[i] > 35 else f"<b>{labels[i]}</b>"
    fig.add_annotation(
        x=x_pos[i],
        y=y_pos[i],
        text=label_text,
        showarrow=False,
        font={"size": font_size, "color": text_colors[i], "family": "Arial"},
    )

# Layout
fig.update_layout(
    title={
        "text": "Department Budget Allocation · bubble-packed · plotly · pyplots.ai",
        "font": {"size": 32, "color": "#333"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "title": "", "range": [x_lo, x_hi]},
    yaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "title": "",
        "scaleanchor": "x",
        "scaleratio": 1,
        "range": [y_lo, y_hi],
    },
    template="plotly_white",
    legend={
        "font": {"size": 16, "family": "Arial"},
        "orientation": "h",
        "yanchor": "top",
        "y": -0.04,
        "xanchor": "center",
        "x": 0.5,
        "itemsizing": "constant",
    },
    margin={"l": m_l, "r": m_r, "t": m_t, "b": m_b},
    paper_bgcolor="white",
    plot_bgcolor="white",
)

# Total budget annotation below the cluster
fig.add_annotation(
    text=f"Total: {total}",
    xref="paper",
    yref="paper",
    x=0.5,
    y=-0.01,
    showarrow=False,
    font={"size": 18, "color": "#666", "family": "Arial"},
)

# Save
fig.write_image("plot.png", width=fig_w, height=fig_h, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
