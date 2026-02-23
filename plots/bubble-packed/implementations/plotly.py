"""pyplots.ai
bubble-packed: Basic Packed Bubble Chart
Library: plotly 6.5.2 | Python 3.14.3
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

# Weight-based centering for better visual balance (larger bubbles pull center)
area_weights = radii**2
x_pos -= np.average(x_pos, weights=area_weights)
y_pos -= np.average(y_pos, weights=area_weights)

# Axis ranges — symmetric with generous padding for balanced layout
x_ext = max(abs((x_pos - radii).min()), abs((x_pos + radii).max())) + 50
y_ext = max(abs((y_pos - radii).min()), abs((y_pos + radii).max())) + 50

# Convert data-coordinate radii to pixel marker diameters
# With scaleanchor y=x, the smaller dimension constrains the scale
fig_w, fig_h = 1600, 900
m_l, m_r, m_t, m_b = 50, 50, 100, 60
plot_w, plot_h = fig_w - m_l - m_r, fig_h - m_t - m_b
px_per_unit = min(plot_w / (2 * x_ext), plot_h / (2 * y_ext))
marker_diameters = 2 * radii * px_per_unit

# Sequential blue palette — adaptive text color for readability
norm_vals = (values - values.min()) / (values.max() - values.min())
text_colors = ["white" if nv > 0.3 else "#333" for nv in norm_vals]

# Format values for display
formatted = [f"${v / 1e6:.1f}M" if v >= 1e6 else f"${v / 1e3:.0f}K" for v in values]
shares = [f"{v / values.sum() * 100:.1f}" for v in values]
total = f"${values.sum() / 1e6:.1f}M"

# Build figure — go.Scatter with sized markers as primary visualization
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=x_pos,
        y=y_pos,
        mode="markers",
        marker={
            "size": marker_diameters,
            "sizemode": "diameter",
            "color": values,
            "colorscale": [
                [0, "#C6DBEF"],
                [0.2, "#9ECAE1"],
                [0.4, "#6BAED6"],
                [0.6, "#3182BD"],
                [0.8, "#1565A0"],
                [1, "#08306B"],
            ],
            "showscale": False,
            "opacity": 0.9,
            "line": {"color": "white", "width": 2.5},
        },
        text=labels,
        customdata=np.column_stack([formatted, shares]),
        hovertemplate="<b>%{text}</b><br>Budget: %{customdata[0]}<br>Share: %{customdata[1]}%<extra></extra>",
        showlegend=False,
    )
)

# Text labels inside bubbles
for i in range(n):
    font_size = max(12, min(20, int(radii[i] * 0.20)))
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
    xaxis={"showgrid": False, "zeroline": False, "showticklabels": False, "title": "", "range": [-x_ext, x_ext]},
    yaxis={
        "showgrid": False,
        "zeroline": False,
        "showticklabels": False,
        "title": "",
        "scaleanchor": "x",
        "scaleratio": 1,
        "range": [-y_ext, y_ext],
    },
    template="plotly_white",
    showlegend=False,
    margin={"l": m_l, "r": m_r, "t": m_t, "b": m_b},
    paper_bgcolor="white",
    plot_bgcolor="white",
)

# Total budget annotation below the cluster
fig.add_annotation(
    text=f"Total: {total}",
    x=0,
    y=(y_pos - radii).min() - 25,
    showarrow=False,
    font={"size": 18, "color": "#666", "family": "Arial"},
)

# Save
fig.write_image("plot.png", width=fig_w, height=fig_h, scale=3)
fig.write_html("plot.html", include_plotlyjs=True, full_html=True)
