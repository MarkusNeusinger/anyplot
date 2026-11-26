"""anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: plotly 6.7.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-11-26
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # normal return bars
TAIL = IMPRINT_PALETTE[1]  # tail region bars
CURVE = IMPRINT_PALETTE[2]  # normal distribution curve

# Constants
N_BINS = 40  # 20-50 bins suit 252+ observations
TAIL_SIGMAS = 2  # tail regions lie beyond this many standard deviations

# Columns: set these to your table's column names
DATE = "Date"  # role: date
RETURNS = "Daily returns (%)"  # role: returns

# Data: replace this block with your own table, for example df = pd.read_csv("returns.csv")
np.random.seed(42)
n_days = 504  # two years of trading days
daily_returns = np.random.normal(loc=0.0005, scale=0.015, size=n_days)
outliers = np.random.choice(n_days, size=20, replace=False)
daily_returns[outliers] *= np.random.uniform(2, 4, size=20) * np.random.choice([-1, 1], size=20)
df = pd.DataFrame({DATE: pd.bdate_range("2023-01-02", periods=n_days), RETURNS: daily_returns * 100})

# Plot: reads only df and the constants above
returns_pct = df[RETURNS].dropna().to_numpy()
mean_ret = np.mean(returns_pct)
std_ret = np.std(returns_pct)
skewness = stats.skew(returns_pct)
kurtosis = stats.kurtosis(returns_pct)

hist_values, bin_edges = np.histogram(returns_pct, bins=N_BINS, density=True)
bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
bin_width = bin_edges[1] - bin_edges[0]

x_norm = np.linspace(returns_pct.min(), returns_pct.max(), 200)
y_norm = stats.norm.pdf(x_norm, mean_ret, std_ret)

lower_tail = mean_ret - TAIL_SIGMAS * std_ret
upper_tail = mean_ret + TAIL_SIGMAS * std_ret

# Split bins into normal-range and tail for correct legend swatches
tail_mask = (bin_centers < lower_tail) | (bin_centers > upper_tail)
normal_x, normal_y = bin_centers[~tail_mask], hist_values[~tail_mask]
tail_x, tail_y = bin_centers[tail_mask], hist_values[tail_mask]

# Figure
fig = go.Figure()

# Normal-range bars (green, primary legend entry)
fig.add_trace(
    go.Bar(
        x=normal_x,
        y=normal_y,
        width=bin_width,
        marker_color=BRAND,
        marker_line={"color": PAGE_BG, "width": 0.5},
        name="Returns Distribution",
        opacity=0.75,
        hovertemplate="Return: %{x:.2f}%<br>Density: %{y:.4f}<br>Range: Normal<extra></extra>",
    )
)

# Tail bins (vermillion, separate legend entry)
fig.add_trace(
    go.Bar(
        x=tail_x,
        y=tail_y,
        width=bin_width,
        marker_color=TAIL,
        marker_line={"color": PAGE_BG, "width": 0.5},
        name=f"Tail Region (>±{TAIL_SIGMAS}σ)",
        opacity=0.75,
        hovertemplate="Return: %{x:.2f}%<br>Density: %{y:.4f}<br>Range: Tail<extra></extra>",
    )
)

fig.add_trace(
    go.Scatter(x=x_norm, y=y_norm, mode="lines", line={"color": CURVE, "width": 3}, name="Normal Distribution")
)

fig.add_vline(
    x=mean_ret,
    line={"color": INK, "width": 2, "dash": "dash"},
    annotation_text="Mean",
    annotation_position="top",
    annotation_font={"color": INK, "size": 11},
)
fig.add_vline(x=lower_tail, line={"color": TAIL, "width": 1.5, "dash": "dot"})
fig.add_vline(x=upper_tail, line={"color": TAIL, "width": 1.5, "dash": "dot"})

stats_text = (
    f"<b>Statistics</b><br>"
    f"Mean: {mean_ret:.3f}%<br>"
    f"Std Dev: {std_ret:.3f}%<br>"
    f"Skewness: {skewness:.3f}<br>"
    f"Kurtosis: {kurtosis:.3f}"
)

fig.add_annotation(
    x=0.98,
    y=0.98,
    xref="paper",
    yref="paper",
    text=stats_text,
    showarrow=False,
    font={"size": 12, "family": "monospace", "color": INK},
    align="left",
    bgcolor=ELEVATED_BG,
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=8,
)

fig.update_layout(
    autosize=False,
    margin={"l": 80, "r": 40, "t": 80, "b": 60},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "histogram-returns-distribution · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": RETURNS, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickformat": ".1f",
        "ticksuffix": "%",
        "zeroline": True,
        "zerolinewidth": 1,
        "zerolinecolor": INK_SOFT,
        "gridcolor": GRID,
        "showline": True,
        "linecolor": INK_SOFT,
        "mirror": False,
    },
    yaxis={
        "title": {"text": "Probability Density", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "gridcolor": GRID,
        "showline": True,
        "linecolor": INK_SOFT,
        "mirror": False,
    },
    legend={
        "x": 0.02,
        "y": 0.98,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 10, "color": INK_SOFT},
    },
    bargap=0,
    barmode="overlay",
    showlegend=True,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
