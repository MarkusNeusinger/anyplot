"""pyplots.ai
bar-pareto: Pareto Chart with Cumulative Line
Library: plotly 6.6.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-20
"""

import numpy as np
import plotly.graph_objects as go


# Data
categories = [
    "Scratches",
    "Dents",
    "Misalignment",
    "Cracks",
    "Discoloration",
    "Burrs",
    "Warping",
    "Contamination",
    "Chipping",
    "Porosity",
]
counts = np.array([142, 118, 87, 64, 53, 38, 29, 21, 15, 9])

sort_idx = np.argsort(-counts)
categories = [categories[i] for i in sort_idx]
counts = counts[sort_idx]

cumulative_pct = np.cumsum(counts) / counts.sum() * 100

# Color: vital few (≤80%) vs trivial many
threshold_idx = int(np.searchsorted(cumulative_pct, 80, side="right")) + 1
bar_colors = ["#306998" if i < threshold_idx else "#A8C4D9" for i in range(len(counts))]

# Plot
fig = go.Figure()

# Bars with color-coded vital few / trivial many
fig.add_trace(
    go.Bar(
        x=categories[:threshold_idx],
        y=counts[:threshold_idx],
        marker={"color": "#306998", "line": {"width": 0}},
        name="Vital Few",
        yaxis="y",
        showlegend=True,
    )
)

fig.add_trace(
    go.Bar(
        x=categories[threshold_idx:],
        y=counts[threshold_idx:],
        marker={"color": "#A8C4D9", "line": {"width": 0}},
        name="Trivial Many",
        yaxis="y",
        showlegend=True,
    )
)

# Cumulative line with gradient-like markers
marker_colors = ["#C0392B" if i < threshold_idx else "#E8A598" for i in range(len(cumulative_pct))]

fig.add_trace(
    go.Scatter(
        x=categories,
        y=cumulative_pct,
        mode="lines+markers+text",
        marker={"size": 14, "color": marker_colors, "line": {"width": 2.5, "color": "white"}},
        line={"width": 3.5, "color": "#C0392B", "shape": "spline"},
        text=[f"{v:.0f}%" if i == threshold_idx - 1 else "" for i, v in enumerate(cumulative_pct)],
        textposition="top center",
        textfont={"size": 15, "color": "#C0392B"},
        name="Cumulative %",
        yaxis="y2",
    )
)

# 80% reference line with shaded region annotation
fig.add_hline(y=80, line={"color": "#888888", "width": 2, "dash": "dot"}, yref="y2")
fig.add_annotation(
    x=0.99,
    y=80,
    xref="paper",
    yref="y2",
    text="<b>80% threshold</b>",
    showarrow=False,
    font={"size": 14, "color": "#666666"},
    xanchor="right",
    yanchor="bottom",
    yshift=6,
)

# Annotation: vital few bracket
fig.add_vrect(x0=-0.5, x1=threshold_idx - 0.5, fillcolor="rgba(48, 105, 152, 0.04)", line_width=0, layer="below")

# Value labels on top bars (first 3 only to avoid clutter)
for i in range(min(3, len(counts))):
    fig.add_annotation(
        x=categories[i],
        y=counts[i],
        text=f"<b>{counts[i]}</b>",
        showarrow=False,
        font={"size": 15, "color": "#306998"},
        yshift=12,
    )

# Style
fig.update_layout(
    title={
        "text": "bar-pareto · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#2C3E50"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Defect Type", "font": {"size": 22, "color": "#444444"}, "standoff": 15},
        "tickfont": {"size": 17, "color": "#555555"},
        "showline": True,
        "linecolor": "#CCCCCC",
        "linewidth": 1,
    },
    yaxis={
        "title": {"text": "Frequency", "font": {"size": 22, "color": "#444444"}, "standoff": 10},
        "tickfont": {"size": 18, "color": "#555555"},
        "showgrid": True,
        "gridcolor": "rgba(0,0,0,0.06)",
        "gridwidth": 1,
        "zeroline": False,
    },
    yaxis2={
        "title": {"text": "Cumulative Percentage (%)", "font": {"size": 22, "color": "#444444"}, "standoff": 10},
        "tickfont": {"size": 18, "color": "#555555"},
        "overlaying": "y",
        "side": "right",
        "range": [0, 108],
        "showgrid": False,
        "ticksuffix": "%",
        "zeroline": False,
    },
    template="plotly_white",
    legend={
        "font": {"size": 15},
        "x": 0.68,
        "y": 0.35,
        "bgcolor": "rgba(255,255,255,0.9)",
        "bordercolor": "rgba(0,0,0,0.1)",
        "borderwidth": 1,
    },
    bargap=0.12,
    plot_bgcolor="white",
    paper_bgcolor="white",
    margin={"t": 90, "b": 70, "l": 70, "r": 90},
    barmode="relative",
)

# Save
fig.write_html("plot.html", include_plotlyjs="cdn")
fig.write_image("plot.png", width=1600, height=900, scale=3)
