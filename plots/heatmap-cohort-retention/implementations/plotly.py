""" pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: plotly 6.6.0 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-16
"""

import numpy as np
import plotly.graph_objects as go


# Data
np.random.seed(42)

cohort_labels = [
    "Jan 2024",
    "Feb 2024",
    "Mar 2024",
    "Apr 2024",
    "May 2024",
    "Jun 2024",
    "Jul 2024",
    "Aug 2024",
    "Sep 2024",
    "Oct 2024",
]
num_cohorts = len(cohort_labels)
num_periods = num_cohorts
cohort_sizes = [1200, 1350, 980, 1100, 1450, 1280, 1050, 1380, 1150, 900]

retention = np.full((num_cohorts, num_periods), np.nan)
for i in range(num_cohorts):
    max_period = num_periods - i
    retention[i, 0] = 100.0
    for j in range(1, max_period):
        base_drop = np.exp(-0.25 * j) * 100
        noise = np.random.normal(0, 3)
        trend_bonus = i * 0.8
        retention[i, j] = np.clip(base_drop + noise + trend_bonus, 5, 100)

# Build hovertext and cell annotations with conditional coloring
hover_text = []
cell_annotations = []
for i in range(num_cohorts):
    row_hover = []
    for j in range(num_periods):
        if np.isnan(retention[i, j]):
            row_hover.append("")
        else:
            val = retention[i, j]
            row_hover.append(
                f"<b>{cohort_labels[i]}</b> · Month {j}<br>"
                f"Cohort size: {cohort_sizes[i]:,} users<br>"
                f"Retained: <b>{val:.1f}%</b>"
            )
            cell_annotations.append(
                {
                    "x": f"Month {j}",
                    "y": f"{cohort_labels[i]}  (n={cohort_sizes[i]:,})",
                    "text": f"<b>{val:.0f}%</b>",
                    "showarrow": False,
                    "font": {"size": 15, "color": "#1a2e1a" if val < 45 else "white"},
                }
            )
    hover_text.append(row_hover)

# Y-axis labels with cohort size
y_labels = [f"{label}  (n={size:,})" for label, size in zip(cohort_labels, cohort_sizes, strict=False)]
x_labels = [f"Month {i}" for i in range(num_periods)]

# Custom colorscale — teal-green sequential with good perceptual uniformity
colorscale = [
    [0.0, "#f0f9f4"],
    [0.15, "#c6e7d4"],
    [0.30, "#7cc5a3"],
    [0.50, "#3a9d6e"],
    [0.70, "#1e7a4e"],
    [0.85, "#135c39"],
    [1.0, "#0a3d26"],
]

# Plot
fig = go.Figure(
    data=go.Heatmap(
        z=retention,
        x=x_labels,
        y=y_labels,
        showscale=True,
        hovertext=hover_text,
        hoverinfo="text",
        colorscale=colorscale,
        zmin=0,
        zmax=100,
        colorbar={
            "title": {"text": "Retention Rate", "font": {"size": 18, "color": "#2d2d2d"}},
            "tickfont": {"size": 16, "color": "#2d2d2d"},
            "ticksuffix": "%",
            "tickvals": [0, 20, 40, 60, 80, 100],
            "len": 0.75,
            "thickness": 18,
            "outlinewidth": 0,
            "x": 1.02,
        },
        xgap=3,
        ygap=3,
    )
)

# Add cell annotations with conditional text coloring (dark on light, white on dark)
for ann in cell_annotations:
    fig.add_annotation(**ann)

# Add a subtle annotation highlighting the improving trend
fig.add_annotation(
    text="↑ Later cohorts retain better",
    xref="paper",
    yref="paper",
    x=0.0,
    y=-0.10,
    showarrow=False,
    font={"size": 15, "color": "#3a9d6e", "family": "Arial"},
    xanchor="left",
)

# Style
fig.update_layout(
    title={
        "text": "heatmap-cohort-retention · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#1a1a1a", "family": "Arial Black, Arial"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Months Since Signup", "font": {"size": 22, "color": "#2d2d2d"}, "standoff": 15},
        "tickfont": {"size": 17, "color": "#3d3d3d"},
        "side": "bottom",
        "dtick": 1,
    },
    yaxis={
        "title": {"text": "Signup Cohort", "font": {"size": 22, "color": "#2d2d2d"}, "standoff": 20},
        "tickfont": {"size": 16, "color": "#3d3d3d"},
        "autorange": "reversed",
    },
    template="plotly_white",
    width=1600,
    height=900,
    margin={"l": 195, "r": 90, "t": 75, "b": 95},
    paper_bgcolor="#fafafa",
    plot_bgcolor="#fafafa",
    font={"family": "Arial, Helvetica, sans-serif"},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
