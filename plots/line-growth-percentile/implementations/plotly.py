"""pyplots.ai
line-growth-percentile: Pediatric Growth Chart with Percentile Curves
Library: plotly 6.6.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-19
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
patient_weights = np.array([3.5, 4.1, 4.8, 6.1, 7.2, 8.8, 10.3, 11.7, 13.0, 15.6, 17.7, 19.4])

# Colors - graduated blue tones for boys chart
band_fills = [
    "rgba(30, 80, 140, 0.28)",  # P3-P10 (darker edge)
    "rgba(50, 110, 170, 0.22)",  # P10-P25
    "rgba(80, 145, 210, 0.20)",  # P25-P50
    "rgba(80, 145, 210, 0.20)",  # P50-P75
    "rgba(50, 110, 170, 0.22)",  # P75-P90
    "rgba(30, 80, 140, 0.28)",  # P90-P97 (darker edge)
]

band_lines = [
    "rgba(30, 80, 140, 0.35)",
    "rgba(50, 110, 170, 0.30)",
    "rgba(80, 145, 210, 0.25)",
    "rgba(80, 145, 210, 0.25)",
    "rgba(50, 110, 170, 0.30)",
    "rgba(30, 80, 140, 0.35)",
]

# Ordered percentile arrays for tonexty fill stacking (bottom to top)
percentile_stack = [
    (percentile_3, "P3", None),
    (percentile_10, "P10", band_fills[0]),
    (percentile_25, "P25", band_fills[1]),
    (percentile_50, "P50", band_fills[2]),
    (percentile_75, "P75", band_fills[3]),
    (percentile_90, "P90", band_fills[4]),
    (percentile_97, "P97", band_fills[5]),
]

# Plot
fig = go.Figure()

# Percentile bands using idiomatic fill='tonexty' stacking
for i, (pct_data, pct_label, fill_color) in enumerate(percentile_stack):
    is_median = pct_label == "P50"
    fig.add_trace(
        go.Scatter(
            x=age_months,
            y=pct_data,
            mode="lines",
            line={
                "color": "rgba(25, 70, 130, 0.7)"
                if is_median
                else band_lines[i - 1]
                if i > 0
                else "rgba(30, 80, 140, 0.35)",
                "width": 2.5 if is_median else 1,
                "dash": "solid",
            },
            fill="tonexty" if fill_color else None,
            fillcolor=fill_color,
            showlegend=False,
            name=pct_label,
            customdata=np.column_stack([np.full_like(age_months, float(pct_label[1:])), pct_data]),
            hovertemplate=(
                "<b>%{customdata[0]:.0f}th Percentile</b><br>"
                "Age: %{x} months<br>"
                "Weight: %{customdata[1]:.1f} kg"
                "<extra></extra>"
            ),
        )
    )

# Percentile labels on right margin with smart spacing
label_data = [
    (percentile_3[-1], "P3"),
    (percentile_10[-1], "P10"),
    (percentile_25[-1], "P25"),
    (percentile_50[-1], "P50"),
    (percentile_75[-1], "P75"),
    (percentile_90[-1], "P90"),
    (percentile_97[-1], "P97"),
]

# Apply minimum vertical spacing to avoid crowding
min_gap = 0.55
label_positions = [y for y, _ in label_data]
for i in range(1, len(label_positions)):
    if label_positions[i] - label_positions[i - 1] < min_gap:
        label_positions[i] = label_positions[i - 1] + min_gap

for (_, pct_label), y_pos in zip(label_data, label_positions, strict=False):
    is_median = pct_label == "P50"
    fig.add_annotation(
        x=37.2,
        y=y_pos,
        text=f"<b>{pct_label}</b>" if is_median else pct_label,
        showarrow=False,
        font={
            "size": 19 if is_median else 17,
            "color": "rgba(25, 70, 130, 0.95)" if is_median else "rgba(50, 100, 160, 0.75)",
            "family": "Arial",
        },
        xanchor="left",
    )

# Patient data overlay - use dark teal for contrast (not red per library guide)
patient_color = "#1A7A6D"
fig.add_trace(
    go.Scatter(
        x=patient_ages,
        y=patient_weights,
        mode="lines+markers",
        line={"color": patient_color, "width": 3.5, "shape": "spline"},
        marker={"size": 13, "color": patient_color, "line": {"color": "white", "width": 2.5}, "symbol": "circle"},
        name="Patient (Boy)",
        showlegend=True,
        customdata=np.column_stack([patient_ages, patient_weights]),
        hovertemplate=(
            "<b>Patient Visit</b><br>Age: %{customdata[0]:.0f} months<br>Weight: %{customdata[1]:.1f} kg<extra></extra>"
        ),
    )
)

# Milestone annotation at 36 months showing percentile position
fig.add_annotation(
    x=34,
    y=patient_weights[-1] + 0.8,
    text="<b>~25th percentile</b><br>at 36 months",
    showarrow=True,
    arrowhead=2,
    arrowsize=1,
    arrowwidth=1.5,
    arrowcolor=patient_color,
    ax=-50,
    ay=-35,
    font={"size": 15, "color": patient_color, "family": "Arial"},
    align="center",
    bordercolor=patient_color,
    borderwidth=1,
    borderpad=5,
    bgcolor="rgba(255, 255, 255, 0.85)",
)

# Layout
fig.update_layout(
    title={
        "text": "Weight-for-Age Boys (0–36 months) · line-growth-percentile · plotly · pyplots.ai",
        "font": {"size": 28, "family": "Arial", "color": "#2C3E50"},
        "x": 0.5,
        "xanchor": "center",
        "y": 0.96,
    },
    xaxis={
        "title": {"text": "Age (months)", "font": {"size": 22, "family": "Arial"}, "standoff": 10},
        "tickfont": {"size": 18},
        "range": [-0.5, 40],
        "dtick": 3,
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(180, 180, 180, 0.2)",
        "zeroline": False,
    },
    yaxis={
        "title": {"text": "Weight (kg)", "font": {"size": 22, "family": "Arial"}, "standoff": 10},
        "tickfont": {"size": 18},
        "range": [0, 24],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(180, 180, 180, 0.2)",
        "zeroline": False,
    },
    legend={
        "font": {"size": 18, "family": "Arial"},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": "rgba(255, 255, 255, 0.85)",
        "bordercolor": "rgba(160, 160, 160, 0.4)",
        "borderwidth": 1,
    },
    template="plotly_white",
    hovermode="closest",
    hoverlabel={"font": {"size": 15, "family": "Arial"}, "bgcolor": "white"},
    margin={"l": 80, "r": 90, "t": 80, "b": 65},
    plot_bgcolor="rgba(248, 250, 252, 1)",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn", config={"displayModeBar": True, "scrollZoom": True})
