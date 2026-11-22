"""anyplot.ai
frontier-efficient: Efficient Frontier for Portfolio Optimization
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-17
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
IMPRINT_SEQ = [[0.0, "#009E73"], [1.0, "#4467A3"]]  # Imprint sequential scale for the Sharpe ratio

# Constants
RISK_FREE_RATE = 0.03  # annual return of the risk-free asset
N_SHOWN = 300  # portfolios drawn as the scatter cloud; the rest only trace the frontier
N_BINS = 60  # return bins used to find the lowest-risk portfolio per return level

# Columns: set these to your table's column names
RISK = "Risk (standard deviation)"  # role: risk
RETURN = "Expected return (annual)"  # role: return

# Data: replace this block with your own table, for example df = pd.read_csv("portfolios.csv")
# One row per simulated portfolio: the first N_SHOWN rows form the scatter cloud,
# the remaining rows are the larger pool that traces the efficient frontier.
np.random.seed(42)
expected_returns = np.array([0.08, 0.12, 0.15, 0.10, 0.18])
cov_matrix = np.array(
    [
        [0.04, 0.01, 0.02, 0.01, 0.02],
        [0.01, 0.06, 0.02, 0.01, 0.03],
        [0.02, 0.02, 0.09, 0.02, 0.04],
        [0.01, 0.01, 0.02, 0.05, 0.02],
        [0.02, 0.03, 0.04, 0.02, 0.12],
    ]
)
weights = np.random.random((N_SHOWN + 50000, len(expected_returns)))
weights /= weights.sum(axis=1, keepdims=True)
df = pd.DataFrame(
    {RISK: np.sqrt(np.einsum("ij,jk,ik->i", weights, cov_matrix, weights)), RETURN: weights @ expected_returns}
)

# Plot: reads only df and the constants above
SHARPE = "Sharpe ratio"
df[SHARPE] = (df[RETURN] - RISK_FREE_RATE) / df[RISK]
shown = df.iloc[:N_SHOWN]

# Efficient frontier: lowest-risk portfolio per return bin, kept while risk keeps rising with return
bins = pd.cut(df[RETURN], N_BINS)
best = df.loc[df.groupby(bins, observed=True)[RISK].idxmin()].sort_values(RETURN)
start = best[RISK].to_numpy().argmin()
best = best.iloc[start:]
frontier = best[best[RISK] >= best[RISK].cummax()]

# Key portfolios sit on the frontier: its leftmost point, and the tangency point of the capital market line
min_var = frontier.loc[frontier[RISK].idxmin()]
max_sharpe = frontier.loc[frontier[SHARPE].idxmax()]

x_max = max(shown[RISK].max(), frontier[RISK].max()) * 1.05
y_max = max(shown[RETURN].max(), frontier[RETURN].max()) * 1.08
cml_x = np.array([0.0, x_max])
cml_y = RISK_FREE_RATE + max_sharpe[SHARPE] * cml_x

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=shown[RISK],
        y=shown[RETURN],
        mode="markers",
        marker={
            "size": 5,
            "color": shown[SHARPE],
            "colorscale": IMPRINT_SEQ,
            "opacity": 0.65,
            "colorbar": {
                "title": {"text": SHARPE, "font": {"size": 12, "color": INK}},
                "tickfont": {"size": 10, "color": INK_SOFT},
                "thickness": 14,
                "len": 0.6,
                "outlinewidth": 0,
            },
        },
        name="Random portfolios",
        hovertemplate="Risk: %{x:.2%}<br>Return: %{y:.2%}<br>Sharpe: %{marker.color:.2f}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=cml_x,
        y=cml_y,
        mode="lines",
        line={"color": IMPRINT_PALETTE[1], "width": 2, "dash": "dash"},
        name="Capital market line",
        hoverinfo="skip",
    )
)

fig.add_trace(
    go.Scatter(
        x=frontier[RISK],
        y=frontier[RETURN],
        mode="lines",
        line={"color": IMPRINT_PALETTE[0], "width": 4},
        name="Efficient frontier",
        hovertemplate="Risk: %{x:.2%}<br>Return: %{y:.2%}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=[0],
        y=[RISK_FREE_RATE],
        mode="markers",
        marker={"size": 9, "color": INK_SOFT, "line": {"width": 1.5, "color": PAGE_BG}},
        name=f"Risk-free rate ({RISK_FREE_RATE:.0%})",
        hovertemplate="Risk: 0%<br>Return: %{y:.2%}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=[min_var[RISK]],
        y=[min_var[RETURN]],
        mode="markers",
        marker={"size": 13, "color": IMPRINT_PALETTE[2], "symbol": "diamond", "line": {"width": 1.5, "color": PAGE_BG}},
        name="Minimum variance",
        hovertemplate="Risk: %{x:.2%}<br>Return: %{y:.2%}<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(
        x=[max_sharpe[RISK]],
        y=[max_sharpe[RETURN]],
        mode="markers",
        marker={"size": 15, "color": IMPRINT_PALETTE[3], "symbol": "star", "line": {"width": 1.5, "color": PAGE_BG}},
        name="Maximum Sharpe ratio",
        hovertemplate="Risk: %{x:.2%}<br>Return: %{y:.2%}<extra></extra>",
    )
)

# Style
fig.update_layout(
    title={
        "text": "frontier-efficient · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": RISK, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickformat": ".0%",
        "range": [0, x_max],
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    yaxis={
        "title": {"text": RETURN, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickformat": ".0%",
        "range": [0, y_max],
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    autosize=False,
    margin={"l": 70, "r": 30, "t": 60, "b": 55},
    width=800,
    height=450,
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
