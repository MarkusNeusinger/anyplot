"""pyplots.ai
heatmap-cohort-retention: Cohort Retention Heatmap
Library: plotly | Python 3.13
Quality: pending | Created: 2026-03-16
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

# Build annotation text and hovertext
annotations_text = []
hover_text = []
for i in range(num_cohorts):
    row_text = []
    row_hover = []
    for j in range(num_periods):
        if np.isnan(retention[i, j]):
            row_text.append("")
            row_hover.append("")
        else:
            val = retention[i, j]
            row_text.append(f"{val:.0f}%")
            row_hover.append(
                f"Cohort: {cohort_labels[i]}<br>Size: {cohort_sizes[i]:,}<br>Month {j}<br>Retention: {val:.1f}%"
            )
    annotations_text.append(row_text)
    hover_text.append(row_hover)

# Y-axis labels with cohort size
y_labels = [f"{label} (n={size:,})" for label, size in zip(cohort_labels, cohort_sizes, strict=False)]
x_labels = [f"Month {i}" for i in range(num_periods)]

# Plot
fig = go.Figure(
    data=go.Heatmap(
        z=retention,
        x=x_labels,
        y=y_labels,
        text=annotations_text,
        texttemplate="%{text}",
        textfont={"size": 15, "color": "white"},
        hovertext=hover_text,
        hoverinfo="text",
        colorscale=[[0.0, "#e0f2e9"], [0.25, "#7bc8a4"], [0.5, "#3a9d6e"], [0.75, "#1a7a4e"], [1.0, "#0d5233"]],
        zmin=0,
        zmax=100,
        colorbar={
            "title": {"text": "Retention %", "font": {"size": 18}},
            "tickfont": {"size": 16},
            "ticksuffix": "%",
            "len": 0.8,
            "thickness": 20,
        },
        xgap=2,
        ygap=2,
    )
)

# Style
fig.update_layout(
    title={
        "text": "heatmap-cohort-retention · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={"title": {"text": "Months Since Signup", "font": {"size": 22}}, "tickfont": {"size": 16}, "side": "bottom"},
    yaxis={"title": {"text": "Signup Cohort", "font": {"size": 22}}, "tickfont": {"size": 16}, "autorange": "reversed"},
    template="plotly_white",
    width=1600,
    height=900,
    margin={"l": 180, "r": 80, "t": 80, "b": 80},
    plot_bgcolor="white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
