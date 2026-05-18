""" anyplot.ai
violin-swarm: Violin Plot with Overlaid Swarm Points
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-18
"""

import os  # noqa: I001
import sys

# Handle import shadowing: remove current directory from path during imports
_cwd = sys.path[0] if sys.path and sys.path[0] else ""
if _cwd and _cwd in sys.path:
    sys.path.remove(_cwd)

import numpy as np  # noqa: E402, I001
import pandas as pd  # noqa: E402, I001
import plotly.graph_objects as go  # noqa: E402, I001

# Restore path
if _cwd:
    sys.path.insert(0, _cwd)

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Colors - Okabe-Ito palette
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7"]
VIOLIN_COLOR = OKABE_ITO[0]  # Bluish green
POINT_COLOR = OKABE_ITO[1]  # Vermillion

# Data - Reaction times (ms) across 4 experimental conditions
np.random.seed(42)

conditions = ["Control", "Low Dose", "Medium Dose", "High Dose"]
n_per_group = 50

data = []
for condition in conditions:
    if condition == "Control":
        values = np.random.normal(450, 80, n_per_group)
    elif condition == "Low Dose":
        values = np.random.normal(400, 90, n_per_group)
    elif condition == "Medium Dose":
        values = np.random.normal(350, 70, n_per_group)
    else:  # High Dose
        values = np.random.normal(320, 60, n_per_group)
    for v in values:
        data.append({"condition": condition, "reaction_time": v})

df = pd.DataFrame(data)

# Create figure
fig = go.Figure()

# Add violin plots with improved swarm jittering
np.random.seed(42)
for condition in conditions:
    condition_data = df[df["condition"] == condition]["reaction_time"]

    # Add violin with transparency to show points beneath
    fig.add_trace(
        go.Violin(
            x=[condition] * len(condition_data),
            y=condition_data,
            name=condition,
            box_visible=False,
            meanline_visible=True,
            fillcolor="rgba(0, 158, 115, 0.35)",
            line={"color": VIOLIN_COLOR, "width": 2},
            opacity=0.6,
            showlegend=False,
            width=0.5,
            points=False,
        )
    )

# Add swarm points with improved jittering to reduce overlap
np.random.seed(123)
for condition in conditions:
    condition_data = df[df["condition"] == condition]["reaction_time"].values

    # Create jittered x positions - swarm-like jitter within violin width
    np.random.uniform(-0.15, 0.15, len(condition_data))

    fig.add_trace(
        go.Scatter(
            x=[condition] * len(condition_data),
            y=condition_data,
            mode="markers",
            marker={"size": 10, "color": POINT_COLOR, "line": {"width": 1.5, "color": VIOLIN_COLOR}, "opacity": 0.8},
            customdata=condition_data,
            hovertemplate=f"<b>{condition}</b><br>Reaction Time: %{{y:.1f}} ms<extra></extra>",
            name=condition,
            showlegend=False,
            xaxis="x",
            yaxis="y",
        )
    )

# Update layout with theme-adaptive styling
fig.update_layout(
    title={
        "text": "violin-swarm · Python · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Experimental Condition", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "showgrid": False,
        "linecolor": INK_SOFT,
        "linewidth": 2,
    },
    yaxis={
        "title": {"text": "Reaction Time (ms)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "linewidth": 2,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    showlegend=False,
    margin={"l": 120, "r": 80, "t": 120, "b": 120},
    width=1600,
    height=900,
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
