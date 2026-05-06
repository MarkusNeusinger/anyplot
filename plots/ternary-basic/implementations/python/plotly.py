""" anyplot.ai
ternary-basic: Basic Ternary Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-06
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette (first series is always #009E73)
OKABE_ITO = [
    "#009E73",  # bluish green (brand — primary)
    "#D55E00",  # vermillion (secondary)
    "#0072B2",  # blue (tertiary)
    "#CC79A7",  # reddish purple (quaternary)
]

# Data: Soil composition samples with meaningful clustering by soil type
np.random.seed(42)

# Generate clustered data representing distinct soil types
sandy_soils = np.array(
    [
        [75, 15, 10],
        [70, 20, 10],
        [80, 12, 8],
        [76, 14, 10],
        [78, 16, 6],
        [72, 18, 10],
        [77, 15, 8],
        [74, 19, 7],
        [81, 13, 6],
        [75, 17, 8],
    ]
)

silty_soils = np.array(
    [
        [35, 55, 10],
        [30, 60, 10],
        [32, 58, 10],
        [28, 62, 10],
        [38, 52, 10],
        [33, 57, 10],
        [31, 59, 10],
        [36, 54, 10],
        [29, 61, 10],
        [34, 56, 10],
    ]
)

clayey_soils = np.array(
    [
        [20, 20, 60],
        [15, 25, 60],
        [18, 22, 60],
        [22, 18, 60],
        [16, 24, 60],
        [19, 21, 60],
        [21, 19, 60],
        [17, 23, 60],
        [20, 22, 58],
        [18, 24, 58],
    ]
)

loam_soils = np.array(
    [
        [40, 40, 20],
        [42, 38, 20],
        [38, 42, 20],
        [41, 39, 20],
        [43, 37, 20],
        [39, 41, 20],
        [40, 38, 22],
        [42, 40, 18],
        [41, 41, 18],
        [39, 39, 22],
    ]
)

# Combine all soil types
compositions = np.vstack([sandy_soils, silty_soils, clayey_soils, loam_soils])
sand = compositions[:, 0]
silt = compositions[:, 1]
clay = compositions[:, 2]

# Soil type labels for color encoding (fourth variable)
soil_types = (
    ["Sandy"] * len(sandy_soils)
    + ["Silty"] * len(silty_soils)
    + ["Clayey"] * len(clayey_soils)
    + ["Loam"] * len(loam_soils)
)
soil_type_indices = np.array(
    [0] * len(sandy_soils) + [1] * len(silty_soils) + [2] * len(clayey_soils) + [3] * len(loam_soils)
)

# Create ternary plot with color-encoded soil type
fig = go.Figure()

# Add traces for each soil type
for soil_idx, (name, color) in enumerate(zip(["Sandy", "Silty", "Clayey", "Loam"], OKABE_ITO, strict=True)):
    mask = soil_type_indices == soil_idx
    fig.add_trace(
        go.Scatterternary(
            a=sand[mask],
            b=silt[mask],
            c=clay[mask],
            mode="markers",
            name=name,
            marker={"size": 14, "color": color, "opacity": 0.75, "line": {"width": 1, "color": "white"}},
            hovertemplate=(
                "<b>%{customdata}</b><br>Sand: %{a:.1f}%<br>Silt: %{b:.1f}%<br>Clay: %{c:.1f}%<extra></extra>"
            ),
            customdata=soil_types,
        )
    )

# Layout and styling with theme-adaptive colors
fig.update_layout(
    title={
        "text": "ternary-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    ternary={
        "sum": 100,
        "aaxis": {
            "title": {"text": "Sand (%)", "font": {"size": 22, "color": INK}},
            "tickmode": "linear",
            "tick0": 0,
            "dtick": 20,
            "tickfont": {"size": 18, "color": INK_SOFT},
            "linewidth": 2,
            "linecolor": INK_SOFT,
            "gridwidth": 1,
            "gridcolor": GRID,
        },
        "baxis": {
            "title": {"text": "Silt (%)", "font": {"size": 22, "color": INK}},
            "tickmode": "linear",
            "tick0": 0,
            "dtick": 20,
            "tickfont": {"size": 18, "color": INK_SOFT},
            "linewidth": 2,
            "linecolor": INK_SOFT,
            "gridwidth": 1,
            "gridcolor": GRID,
        },
        "caxis": {
            "title": {"text": "Clay (%)", "font": {"size": 22, "color": INK}},
            "tickmode": "linear",
            "tick0": 0,
            "dtick": 20,
            "tickfont": {"size": 18, "color": INK_SOFT},
            "linewidth": 2,
            "linecolor": INK_SOFT,
            "gridwidth": 1,
            "gridcolor": GRID,
        },
        "bgcolor": PAGE_BG,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    margin={"l": 100, "r": 100, "t": 150, "b": 100},
    legend={
        "x": 0.98,
        "y": 0.02,
        "xanchor": "right",
        "yanchor": "bottom",
        "bgcolor": PAGE_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"color": INK_SOFT, "size": 16},
    },
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
