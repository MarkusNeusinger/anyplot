"""anyplot.ai
line-retention-cohort: User Retention Curve by Cohort
Library: plotly 6.6.0 | Python 3.14.3
Quality: 90/100 | Updated: 2026-06-20
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens — Imprint palette (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030"]

# Data — plateau-based retention decay: retention(t) = plateau + (100 - plateau) * exp(-steep * t)
# Later cohorts achieve higher plateaus, showing improving long-term retention.
np.random.seed(42)

cohorts = {
    "Jan 2025": {"size": 1245, "plateau": 8, "steep": 0.35},
    "Feb 2025": {"size": 1102, "plateau": 11, "steep": 0.33},
    "Mar 2025": {"size": 1380, "plateau": 14, "steep": 0.30},
    "Apr 2025": {"size": 1510, "plateau": 17, "steep": 0.27},
    "May 2025": {"size": 1425, "plateau": 21, "steep": 0.24},
}

weeks = np.arange(0, 13)

retention_data = {}
for cohort, params in cohorts.items():
    base = params["plateau"] + (100 - params["plateau"]) * np.exp(-params["steep"] * weeks)
    noise = np.random.normal(0, 1.2, len(weeks))
    noise[0] = 0
    retention = np.clip(base + noise, 0, 100)
    retention[0] = 100.0
    retention_data[cohort] = retention

# Older cohorts thinner / less opaque to emphasize recent improvement
line_widths = [1.8, 2.0, 2.2, 2.5, 3.0]
opacities = [0.55, 0.65, 0.75, 0.85, 1.0]

# Plot
fig = go.Figure()

for i, (cohort, retention) in enumerate(retention_data.items()):
    params = cohorts[cohort]
    color = IMPRINT_PALETTE[i]
    rgb = tuple(int(color[j : j + 2], 16) for j in (1, 3, 5))
    fill_alpha = 0.04 + i * 0.02

    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=retention,
            mode="none",
            fill="tozeroy",
            fillcolor=f"rgba({rgb[0]},{rgb[1]},{rgb[2]},{fill_alpha})",
            showlegend=False,
            hoverinfo="skip",
        )
    )

    fig.add_trace(
        go.Scatter(
            x=weeks,
            y=retention,
            mode="lines+markers",
            name=f"{cohort} (n={params['size']:,})",
            line={"color": color, "width": line_widths[i]},
            marker={"size": 7 + i, "color": color},
            opacity=opacities[i],
        )
    )

# 20% long-term retention threshold
fig.add_hline(
    y=20,
    line_dash="dash",
    line_color=INK_SOFT,
    line_width=1.5,
    annotation_text="20% threshold",
    annotation_position="top left",
    annotation_font={"size": 10, "color": INK_SOFT},
)

# Title — compute fontsize from length (baseline 16px for ~67 chars)
title = "line-retention-cohort · python · plotly · anyplot.ai"
n = len(title)
title_fontsize = max(round(16 * 67 / n) if n > 67 else 16, 11)

# Style
fig.update_layout(
    autosize=False,
    title={"text": title, "font": {"size": title_fontsize, "color": INK}, "x": 0.5, "xanchor": "center"},
    xaxis={
        "title": {"text": "Weeks Since Signup", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "dtick": 1,
        "showgrid": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Retained Users (%)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [0, 105],
        "ticksuffix": "%",
        "dtick": 20,
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "showline": True,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "yanchor": "top",
        "y": 0.95,
        "xanchor": "right",
        "x": 0.98,
    },
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
)

# Save
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
