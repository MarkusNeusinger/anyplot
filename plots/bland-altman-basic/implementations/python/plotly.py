""" anyplot.ai
bland-altman-basic: Bland-Altman Agreement Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-07
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

BRAND = "#009E73"
ACCENT = "#C475FD"

# Data - Glucose meter readings comparison (medical device validation)
np.random.seed(73)
n_samples = 95

# Lab reference method (plasma glucose in mg/dL)
method1 = np.random.normal(120, 35, n_samples)

# New handheld glucose meter with slight systematic bias
bias = -3.2
method2 = method1 + bias + np.random.normal(0, 8, n_samples)

# Calculate Bland-Altman statistics
means = (method1 + method2) / 2
differences = method1 - method2

mean_diff = np.mean(differences)
std_diff = np.std(differences, ddof=1)
upper_loa = mean_diff + 1.96 * std_diff
lower_loa = mean_diff - 1.96 * std_diff

# Create figure
fig = go.Figure()

# Scatter plot of differences vs means
fig.add_trace(
    go.Scatter(
        x=means,
        y=differences,
        mode="markers",
        marker={"size": 14, "color": BRAND, "opacity": 0.65, "line": {"width": 1.5, "color": PAGE_BG}},
        name="Observations",
        hovertemplate="Mean: %{x:.1f} mg/dL<br>Difference: %{y:.1f} mg/dL<extra></extra>",
    )
)

# Mean difference line (bias)
fig.add_hline(
    y=mean_diff,
    line={"color": BRAND, "width": 3},
    annotation_text=f"Mean: {mean_diff:.2f}",
    annotation_position="right",
    annotation_font={"size": 18, "color": INK},
)

# Upper limit of agreement
fig.add_hline(
    y=upper_loa,
    line={"color": ACCENT, "width": 2.5, "dash": "dash"},
    annotation_text=f"+1.96 SD: {upper_loa:.2f}",
    annotation_position="right",
    annotation_font={"size": 18, "color": ACCENT},
)

# Lower limit of agreement
fig.add_hline(
    y=lower_loa,
    line={"color": ACCENT, "width": 2.5, "dash": "dash"},
    annotation_text=f"−1.96 SD: {lower_loa:.2f}",
    annotation_position="right",
    annotation_font={"size": 18, "color": ACCENT},
)

# Layout
fig.update_layout(
    title={"text": "bland-altman-basic · plotly · anyplot.ai", "font": {"size": 28, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Mean Glucose (mg/dL)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "showgrid": True,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Difference (Lab − Handheld) (mg/dL)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "showgrid": True,
        "zeroline": False,
        "linecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"l": 100, "r": 220, "t": 100, "b": 100},
    hovermode="closest",
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
