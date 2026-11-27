"""anyplot.ai
bullet-basic: Basic Bullet Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 83/100 | Updated: 2026-05-29
"""

import os
import sys


# Prevent self-import: remove this script's own directory from sys.path so that
# "import plotly" resolves to the installed package, not this file.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_RGB = "26,26,23" if THEME == "light" else "240,239,232"

# Imprint palette position 1: the single measure-bar color
BRAND = "#009E73"

# Constants: grayscale band shades from poor (darkest) to good (lightest), ink at graded opacity
BAND_COLORS = [f"rgba({INK_RGB},{alpha})" for alpha in (0.34, 0.20, 0.09)]
FONT = "Helvetica Neue, Arial, sans-serif"

# Columns: set these to your table's column names
METRIC = "Hospital KPI"  # role: label
ACTUAL = "Actual (%)"  # role: actual
TARGET = "Target (%)"  # role: target
POOR = "Poor up to (%)"  # role: ranges
SATISFACTORY = "Satisfactory up to (%)"  # role: extra
GOOD = "Good up to (%)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("kpis.csv")
df = pd.DataFrame(
    {
        METRIC: ["Bed occupancy", "On-time surgery starts", "Hand-hygiene compliance", "Discharges before noon"],
        ACTUAL: [87, 72, 94, 38],
        TARGET: [85, 90, 95, 50],
        POOR: [60, 50, 80, 30],
        SATISFACTORY: [80, 75, 90, 45],
        GOOD: [100, 100, 100, 100],
    }
)

# Plot: one bullet per row on a common scale
bands = [POOR, SATISFACTORY, GOOD]
scale_max = df[bands].max().max()
n = len(df)
row_height = 1.0 / (n + 0.25 * (n - 1))
spacing = 0.25 * row_height

fig = go.Figure()
for i, row in df.iterrows():
    y_end = 1.0 - i * (row_height + spacing)
    edges = [0, *row[bands]]
    fig.add_trace(
        go.Indicator(
            mode="number+gauge",
            value=row[ACTUAL],
            number={"font": {"size": 15, "color": INK, "family": FONT}, "valueformat": ".0f"},
            domain={"x": [0.22, 0.90], "y": [max(0.0, y_end - row_height), y_end]},
            title={"text": row[METRIC], "font": {"size": 13, "color": INK, "family": FONT}, "align": "left"},
            gauge={
                "shape": "bullet",
                "axis": {
                    "range": [0, scale_max],
                    "tickfont": {"size": 11, "color": INK_SOFT, "family": FONT},
                    "tickcolor": INK_SOFT,
                },
                "bar": {"color": BRAND, "thickness": 0.36},
                "bgcolor": PAGE_BG,
                "borderwidth": 0,
                "threshold": {"line": {"color": INK, "width": 3}, "thickness": 0.85, "value": row[TARGET]},
                "steps": [
                    {"range": [edges[k], edges[k + 1]], "color": BAND_COLORS[k]} for k in range(len(BAND_COLORS))
                ],
            },
        )
    )

fig.update_layout(
    autosize=False,
    title={
        "text": "bullet-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "family": FONT, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK, "family": FONT},
    margin={"l": 40, "r": 40, "t": 60, "b": 40},
    width=800,
    height=450,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
