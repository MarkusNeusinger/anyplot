""" anyplot.ai
forest-basic: Meta-Analysis Forest Plot
Library: plotly 7.1.0 | Python 3.14.10
Quality: 89/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import statsmodels.api as sm
from scipy.stats import norm


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"  # Imprint palette position 1: the studies are the one data series
ANYPLOT_NEUTRAL = INK  # semantic anchor for totals: the pooled diamond

# Constants
NULL_EFFECT = 0  # a mean difference of zero: treatment and control do not differ
CI_LEVEL = 0.95  # confidence level of every interval in the table

# Columns: set these to your table's column names
STUDY = "Study"  # role: study
EFFECT = "Mean difference in systolic blood pressure (mmHg)"  # role: effect_size
CI_LOWER = "95% CI lower bound (mmHg)"  # role: ci_lower
CI_UPPER = "95% CI upper bound (mmHg)"  # role: ci_upper
WEIGHT = "Study weight"  # role: weight

# Data: replace this block with your own table, for example df = pd.read_csv("trials.csv")
effects = np.array([-8.2, -5.1, -12.3, -6.8, -9.5, -4.2, -7.8, -11.0, -3.5, -8.9, -6.2, -10.1])
df = pd.DataFrame(
    {
        STUDY: [
            "Smith et al. 2018",
            "Johnson & Lee 2019",
            "Garcia et al. 2019",
            "Williams 2020",
            "Chen et al. 2020",
            "Anderson et al. 2021",
            "Thompson 2021",
            "Martinez et al. 2022",
            "Brown & Davis 2022",
            "Wilson et al. 2023",
            "Taylor 2023",
            "Robinson et al. 2024",
        ],
        EFFECT: effects,
        CI_LOWER: effects - np.array([3.5, 4.2, 4.8, 3.1, 3.8, 5.2, 2.9, 4.1, 4.5, 3.3, 3.7, 4.0]),
        CI_UPPER: effects + np.array([3.2, 3.8, 4.5, 2.8, 3.5, 4.8, 2.6, 3.8, 4.2, 3.0, 3.4, 3.7]),
        WEIGHT: [8.5, 7.2, 9.8, 6.5, 8.9, 5.8, 7.8, 9.2, 6.2, 8.1, 7.5, 8.8],
    }
)

# Plot: reads only df and the constants above; a study with a missing value has no row to draw
studies = df.dropna(subset=[EFFECT, CI_LOWER, CI_UPPER, WEIGHT])

# Pooled estimate: DerSimonian-Laird random effects, each study's variance read off its interval width
z = norm.ppf(0.5 + CI_LEVEL / 2)
variance = ((studies[CI_UPPER] - studies[CI_LOWER]) / (2 * z)) ** 2
pooled = sm.stats.combine_effects(studies[EFFECT], variance, method_re="dl").summary_frame(alpha=1 - CI_LEVEL)
pooled_effect, pooled_lower, pooled_upper = pooled.loc["random effect", ["eff", "ci_low", "ci_upp"]]

# Rows: studies top to bottom in table order, the pooled diamond a row and a half below the last one
width, height = 800, 450
margin = {"l": 160, "r": 90, "t": 80, "b": 90}
study_rows = np.arange(len(studies), 0, -1, dtype=float)
pooled_row = -0.5
row_px = (height - margin["t"] - margin["b"]) / (len(studies) + 2)

# Axis span: every interval, the null line and the diamond, padded on both sides
lowest = min(studies[CI_LOWER].min(), pooled_lower, NULL_EFFECT)
highest = max(studies[CI_UPPER].max(), pooled_upper, NULL_EFFECT)
pad = 0.06 * (highest - lowest)

fig = go.Figure()

# Studies: square marker at the effect, area proportional to weight, whisker over the interval
largest_marker = min(18, 0.8 * row_px)
fig.add_trace(
    go.Scatter(
        x=studies[EFFECT],
        y=study_rows,
        mode="markers",
        marker={
            "symbol": "square",
            "color": BRAND,
            "size": studies[WEIGHT],
            "sizemode": "area",
            "sizeref": 2 * studies[WEIGHT].max() / largest_marker**2,
            "sizemin": 4,
            "opacity": 1,
            "line": {"width": 0},
        },
        error_x={
            "type": "data",
            "symmetric": False,
            "array": studies[CI_UPPER] - studies[EFFECT],
            "arrayminus": studies[EFFECT] - studies[CI_LOWER],
            "color": BRAND,
            "thickness": 2,
            "width": 0,
        },
        customdata=studies[[STUDY, CI_LOWER, CI_UPPER, WEIGHT]],
        hovertemplate="<b>%{customdata[0]}</b><br>%{x:.1f} [%{customdata[1]:.1f}, %{customdata[2]:.1f}]"
        "<br>Weight %{customdata[3]:.1f}<extra></extra>",
        showlegend=False,
    )
)

# Pooled diamond: centred on the estimate, tips at the pooled interval's bounds
fig.add_trace(
    go.Scatter(
        x=[pooled_lower, pooled_effect, pooled_upper, pooled_effect, pooled_lower],
        y=[pooled_row, pooled_row + 0.42, pooled_row, pooled_row - 0.42, pooled_row],
        mode="lines",
        fill="toself",
        fillcolor=ANYPLOT_NEUTRAL,
        line={"color": ANYPLOT_NEUTRAL, "width": 1},
        hoveron="fills",
        hovertemplate=f"Pooled (random effects)<br>{pooled_effect:.1f} [{pooled_lower:.1f}, {pooled_upper:.1f}]"
        "<extra></extra>",
        showlegend=False,
    )
)

# Null-effect line through every row, with its labels set beside it, never on it
fig.add_vline(x=NULL_EFFECT, line={"color": INK_SOFT, "width": 1.5, "dash": "dash"}, layer="below")
direction_labels = [
    ("No effect", "center", 0, 1, "bottom", 4),
    ("← Favors treatment", "right", -8, 0, "top", -22),
    ("Favors control →", "left", 8, 0, "top", -22),
]
for text, xanchor, xshift, y, yanchor, yshift in direction_labels:
    fig.add_annotation(
        x=NULL_EFFECT,
        y=y,
        yref="paper",
        text=text,
        showarrow=False,
        xanchor=xanchor,
        xshift=xshift,
        yanchor=yanchor,
        yshift=yshift,
        font={"size": 10, "color": INK_MUTED},
    )

# Style
fig.update_layout(
    autosize=False,
    width=width,
    height=height,
    margin=margin,
    title={"text": "forest-basic · python · plotly · anyplot.ai", "font": {"size": 16, "color": INK}, "x": 0.5},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    xaxis={
        "title": {"text": EFFECT, "font": {"size": 12, "color": INK}, "standoff": 30},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [lowest - pad, highest + pad],
        "showgrid": True,
        "gridcolor": GRID,
        "zeroline": False,
        "showline": True,
        "linecolor": INK_SOFT,
        "ticks": "",
    },
    yaxis={
        "tickmode": "array",
        "tickvals": [*study_rows, pooled_row],
        "ticktext": [*studies[STUDY].astype(str), "<b>Pooled (random effects)</b>"],
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [pooled_row - 1, len(studies) + 0.8],
        "showgrid": False,
        "zeroline": False,
        "showline": False,
        "ticks": "",
    },
    showlegend=False,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=width, height=height, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
