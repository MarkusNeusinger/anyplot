""" pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: plotly 6.6.0 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-19
"""

import numpy as np
import plotly.graph_objects as go


# Data - WHO-style weight-for-age reference for boys (0-36 months)
np.random.seed(42)
age_months = np.arange(0, 37, 1)

# Synthetic reference percentile data approximating WHO weight-for-age boys 0-36 months (kg)
median = 3.3 + 0.7 * age_months - 0.008 * age_months**2 + 0.00005 * age_months**3
sd = 0.5 + 0.03 * age_months

percentile_3 = median - 1.881 * sd
percentile_10 = median - 1.282 * sd
percentile_25 = median - 0.674 * sd
percentile_50 = median
percentile_75 = median + 0.674 * sd
percentile_90 = median + 1.282 * sd
percentile_97 = median + 1.881 * sd

# Individual patient data - a healthy boy tracked at well-child visits
patient_ages = np.array([0, 1, 2, 4, 6, 9, 12, 15, 18, 24, 30, 36])
patient_weights = np.array([3.5, 4.6, 5.8, 7.2, 8.1, 9.3, 10.2, 11.0, 11.8, 13.0, 14.2, 15.5])

# Colors - blue tones for boys chart, graduated intensity
band_colors = [
    "rgba(30, 80, 140, 0.30)",  # P3-P10 (darker edge)
    "rgba(50, 110, 170, 0.25)",  # P10-P25
    "rgba(80, 140, 200, 0.20)",  # P25-P50
    "rgba(80, 140, 200, 0.20)",  # P50-P75
    "rgba(50, 110, 170, 0.25)",  # P75-P90
    "rgba(30, 80, 140, 0.30)",  # P90-P97 (darker edge)
]

percentiles = [
    (percentile_3, percentile_10, "P3–P10"),
    (percentile_10, percentile_25, "P10–P25"),
    (percentile_25, percentile_50, "P25–P50"),
    (percentile_50, percentile_75, "P50–P75"),
    (percentile_75, percentile_90, "P75–P90"),
    (percentile_90, percentile_97, "P90–P97"),
]

# Plot
fig = go.Figure()

# Percentile bands as filled areas
for (lower, upper, label), color in zip(percentiles, band_colors, strict=False):
    fig.add_trace(
        go.Scatter(
            x=np.concatenate([age_months, age_months[::-1]]),
            y=np.concatenate([upper, lower[::-1]]),
            fill="toself",
            fillcolor=color,
            line={"color": "rgba(0,0,0,0)"},
            showlegend=False,
            hoverinfo="skip",
            name=label,
        )
    )

# Percentile boundary lines (thin, subtle)
percentile_values = [
    (percentile_3, "P3"),
    (percentile_10, "P10"),
    (percentile_25, "P25"),
    (percentile_50, "P50"),
    (percentile_75, "P75"),
    (percentile_90, "P90"),
    (percentile_97, "P97"),
]

for pct_data, pct_label in percentile_values:
    is_median = pct_label == "P50"
    fig.add_trace(
        go.Scatter(
            x=age_months,
            y=pct_data,
            mode="lines",
            line={
                "color": "rgba(30, 80, 140, 0.8)" if is_median else "rgba(60, 120, 180, 0.4)",
                "width": 3 if is_median else 1.5,
            },
            showlegend=False,
            hoverinfo="skip",
            name=pct_label,
        )
    )

# Percentile labels on right margin
for pct_data, pct_label in percentile_values:
    fig.add_annotation(
        x=37,
        y=pct_data[-1],
        text=f"<b>{pct_label}</b>" if pct_label == "P50" else pct_label,
        showarrow=False,
        font={"size": 14, "color": "rgba(30, 80, 140, 0.9)" if pct_label == "P50" else "rgba(60, 120, 180, 0.7)"},
        xanchor="left",
    )

# Patient data overlay
fig.add_trace(
    go.Scatter(
        x=patient_ages,
        y=patient_weights,
        mode="lines+markers",
        line={"color": "#E74C3C", "width": 3},
        marker={"size": 12, "color": "#E74C3C", "line": {"color": "white", "width": 2}},
        name="Patient (Boy)",
        showlegend=True,
    )
)

# Layout
fig.update_layout(
    title={
        "text": "Weight-for-Age Boys (0–36 months) · line-growth-percentile · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Age (months)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [0, 39],
        "dtick": 3,
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(128, 128, 128, 0.15)",
    },
    yaxis={
        "title": {"text": "Weight (kg)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "range": [0, 24],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(128, 128, 128, 0.15)",
    },
    legend={
        "font": {"size": 18},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255, 255, 255, 0.8)",
        "bordercolor": "rgba(128, 128, 128, 0.3)",
        "borderwidth": 1,
    },
    template="plotly_white",
    hovermode="x unified",
    margin={"l": 80, "r": 80, "t": 80, "b": 60},
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
