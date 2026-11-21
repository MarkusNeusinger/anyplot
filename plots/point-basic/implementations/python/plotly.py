"""anyplot.ai
point-basic: Point Estimate Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os

import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Imprint palette position 1

# Constants
NULL_VALUE = 0  # the null effect the reference line marks

# Columns: set these to your table's column names
GROUP = "Treatment group"  # role: category
ESTIMATE = "Effect size (units)"  # role: estimate
LOWER = "Lower 95% bound"  # role: lower_bound
UPPER = "Upper 95% bound"  # role: upper_bound

# Data: replace this block with your own table, for example df = pd.read_csv("effects.csv")
estimates = [0.0, 2.3, 3.8, 1.5, 4.2, 2.9]
half_widths = [0.8, 1.2, 0.9, 1.5, 1.1, 1.3]
df = pd.DataFrame(
    {
        GROUP: ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"],
        ESTIMATE: estimates,
        LOWER: [e - w for e, w in zip(estimates, half_widths, strict=True)],
        UPPER: [e + w for e, w in zip(estimates, half_widths, strict=True)],
    }
)

# Plot: reads only df and the constants above
fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[ESTIMATE],
        y=df[GROUP],
        mode="markers",
        marker={"size": 9, "color": BRAND, "symbol": "circle"},
        error_x={
            "type": "data",
            "symmetric": False,
            "array": df[UPPER] - df[ESTIMATE],
            "arrayminus": df[ESTIMATE] - df[LOWER],
            "color": BRAND,
            "thickness": 1.5,
            "width": 5,
        },
        name="Estimate ± 95% CI",
    )
)

# Null reference line
fig.add_vline(
    x=NULL_VALUE,
    line={"color": INK_SOFT, "width": 1.5, "dash": "dash"},
    annotation_text="Null",
    annotation_position="top",
    annotation_font={"size": 10, "color": INK_SOFT},
)

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "point-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": ESTIMATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "zeroline": False,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": GROUP, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "autorange": "reversed",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    template="plotly_white",
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "x": 0.98,
        "y": 0.02,
        "xanchor": "right",
        "yanchor": "bottom",
    },
    margin={"l": 90, "r": 40, "t": 60, "b": 50},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
