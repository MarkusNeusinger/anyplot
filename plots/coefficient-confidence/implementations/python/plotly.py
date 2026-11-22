"""anyplot.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: plotly 6.7.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-18
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

# Imprint palette: position 1 marks significant coefficients
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NULL_VALUE = 0  # the null hypothesis: no effect

# Columns: set these to your table's column names
VARIABLE = "Predictor variable"  # role: variable
COEFFICIENT = "Coefficient estimate (standardized)"  # role: coefficient
CI_LOWER = "CI lower (95%)"  # role: ci_lower
CI_UPPER = "CI upper (95%)"  # role: ci_upper
SIGNIFICANT = "Significant"  # role: significant

# Data: replace this block with your own table, for example df = pd.read_csv("coefficients.csv")
# Housing price regression: coefficients with standard errors, 95% intervals
variables = [
    "Square Footage",
    "Bedrooms",
    "Bathrooms",
    "Garage Spaces",
    "Lot Size (acres)",
    "Age (years)",
    "Distance to City Center",
    "School Rating",
    "Crime Rate Index",
    "Property Tax Rate",
    "Has Pool",
    "Has Basement",
]
estimates = [0.45, 0.12, 0.18, 0.08, 0.22, -0.15, -0.28, 0.32, -0.19, -0.05, 0.14, 0.09]
std_errors = [0.08, 0.09, 0.06, 0.05, 0.07, 0.04, 0.10, 0.08, 0.11, 0.06, 0.05, 0.07]
df = pd.DataFrame({VARIABLE: variables, COEFFICIENT: estimates})
df[CI_LOWER] = df[COEFFICIENT] - 1.96 * pd.Series(std_errors)
df[CI_UPPER] = df[COEFFICIENT] + 1.96 * pd.Series(std_errors)
df[SIGNIFICANT] = (df[CI_LOWER] > NULL_VALUE) | (df[CI_UPPER] < NULL_VALUE)

# Plot: reads only df and the constants above
df = df.sort_values(COEFFICIENT).reset_index(drop=True)
df[SIGNIFICANT] = df[SIGNIFICANT].fillna(False).astype(bool)
order = df[VARIABLE].tolist()
groups = [(True, "Significant (CI excludes zero)", IMPRINT_PALETTE[0]), (False, "Not significant", INK_SOFT)]
pad = 0.1 * (df[CI_UPPER].max() - df[CI_LOWER].min())

fig = go.Figure()

# Confidence intervals: one line per coefficient, end caps as short vertical ticks
for _, row in df.iterrows():
    color = IMPRINT_PALETTE[0] if row[SIGNIFICANT] else INK_SOFT
    fig.add_trace(
        go.Scatter(
            x=[row[CI_LOWER], row[CI_UPPER]],
            y=[row[VARIABLE]] * 2,
            mode="lines+markers",
            line={"color": color, "width": 2},
            marker={"symbol": "line-ns", "size": 8, "color": color, "line": {"width": 1.5, "color": color}},
            showlegend=False,
            hoverinfo="skip",
        )
    )

# Point estimates, one trace per significance group
for flag, label, color in groups:
    rows = df[df[SIGNIFICANT] == flag]
    fig.add_trace(
        go.Scatter(
            x=rows[COEFFICIENT],
            y=rows[VARIABLE],
            mode="markers",
            marker={
                "size": 10,
                "color": color if flag else PAGE_BG,
                "symbol": "circle",
                "line": {"width": 2, "color": color},
            },
            name=label,
            customdata=rows[[CI_LOWER, CI_UPPER]],
            hovertemplate="%{y}<br>Estimate: %{x:.3f}<br>95% CI: [%{customdata[0]:.3f}, %{customdata[1]:.3f}]<extra></extra>",
        )
    )

# Reference line at the null value
fig.add_vline(x=NULL_VALUE, line={"color": INK, "width": 1.5, "dash": "dash"})

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "coefficient-confidence · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": COEFFICIENT, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "zeroline": False,
        "gridcolor": GRID,
        "range": [df[CI_LOWER].min() - pad, df[CI_UPPER].max() + pad],
        "linecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": VARIABLE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "categoryorder": "array",
        "categoryarray": order,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
        "font": {"size": 10, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 130, "r": 40, "t": 80, "b": 60},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
