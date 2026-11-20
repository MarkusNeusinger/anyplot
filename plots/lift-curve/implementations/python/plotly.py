"""anyplot.ai
lift-curve: Model Lift Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-10
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

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
BASELINE_LIFT = 1.0  # lift of random selection
CALLOUT_SHARE = 0.10  # the share of the population the callout names
MARKER_STEP = 10  # one marker per this many ranked cases

# Columns: set these to your table's column names
Y_TRUE = "Responded (0/1)"  # role: y_true
Y_SCORE = "Model score"  # role: y_score

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
n_samples = 1000
base_score = np.random.beta(2, 5, n_samples)
true_signal = np.random.rand(n_samples)
score = np.clip(0.6 * base_score + 0.4 * true_signal, 0, 1)
responded = (np.random.rand(n_samples) < 0.3 * score + 0.1).astype(int)
df = pd.DataFrame({Y_TRUE: responded, Y_SCORE: score})

# Plot: reads only df and the constants above
ranked = df.sort_values(Y_SCORE, ascending=False, kind="stable")
n = len(ranked)
hits = ranked[Y_TRUE].to_numpy()
cumulative = np.cumsum(hits)
cases = np.arange(1, n + 1)
percentile = cases / n * 100
lift = cumulative / (cases * hits.sum() / n)

# Markers at every MARKER_STEP-th case, plus the first and last
picks = np.unique(np.r_[0, np.arange(MARKER_STEP - 1, n, MARKER_STEP), n - 1])
callout_idx = max(int(n * CALLOUT_SHARE) - 1, 0)

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=percentile[picks],
        y=lift[picks],
        mode="lines+markers",
        name="Model Lift",
        line={"color": IMPRINT_PALETTE[0], "width": 2.5},
        marker={"size": 5, "color": IMPRINT_PALETTE[0]},
        hovertemplate="Top %{x:.0f}%<br>Lift: %{y:.2f}x<extra></extra>",
    )
)
fig.add_trace(
    go.Scatter(
        x=[0, 100],
        y=[BASELINE_LIFT, BASELINE_LIFT],
        mode="lines",
        name="Random Selection",
        line={"color": IMPRINT_PALETTE[1], "width": 2, "dash": "dash"},
        hovertemplate="Random baseline<br>Lift: 1.0x<extra></extra>",
    )
)

fig.add_annotation(
    x=percentile[callout_idx],
    y=lift[callout_idx],
    text=f"Top {percentile[callout_idx]:.0f}%: {lift[callout_idx]:.1f}x lift",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=1.5,
    arrowcolor=IMPRINT_PALETTE[0],
    ax=45,
    ay=-30,
    font={"size": 10, "color": INK},
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=4,
)

# Style
fig.update_layout(
    autosize=False,
    title={
        "text": "lift-curve · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    font={"color": INK},
    xaxis={
        "title": {"text": "Percentage of Population Targeted (%)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [0, 100],
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "dtick": 10,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Cumulative Lift Ratio", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "range": [0, max(lift[picks].max(), BASELINE_LIFT) * 1.1],
        "showgrid": True,
        "gridcolor": GRID,
        "gridwidth": 1,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.98,
        "y": 0.98,
        "xanchor": "right",
        "yanchor": "top",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    margin={"l": 70, "r": 30, "t": 60, "b": 55},
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
