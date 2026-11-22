"""anyplot.ai
indicator-ema: Exponential Moving Average (EMA) Indicator Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-19
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
GOLDEN_CLR = "#DDCC77"  # Imprint amber (outside the categorical pool): golden cross
DEATH_CLR = IMPRINT_PALETTE[4]  # death cross

# Constants
SHORT_SPAN = 12  # fast EMA period in trading days
LONG_SPAN = 26  # slow EMA period in trading days

# Columns: set these to your table's column names
DATE = "Date"  # role: date
CLOSE = "Price (USD per barrel)"  # role: close

# Data: replace this block with your own table, for example df = pd.read_csv("brent.csv")
# Brent crude oil: a sharp supply-shock rally, then a long consolidation
rng = np.random.default_rng(11)
n_days = 120
drift = np.concatenate([np.full(35, 0.011), np.full(n_days - 35, -0.0004)])
log_returns = drift + rng.normal(0, 0.014, n_days)
df = pd.DataFrame(
    {DATE: pd.date_range(start="2024-01-02", periods=n_days, freq="B"), CLOSE: 72 * np.exp(np.cumsum(log_returns))}
)

# Plot
short_label, long_label = f"EMA {SHORT_SPAN}", f"EMA {LONG_SPAN}"
short_ema = df[CLOSE].ewm(span=SHORT_SPAN, adjust=False).mean()
long_ema = df[CLOSE].ewm(span=LONG_SPAN, adjust=False).mean()
above = short_ema > long_ema
was_above = above.shift(1, fill_value=above.iloc[0])
golden = above & ~was_above
death = ~above & was_above

fig = go.Figure()
fig.add_trace(
    go.Scatter(
        x=df[DATE],
        y=df[CLOSE],
        mode="lines",
        name="Price",
        line={"color": IMPRINT_PALETTE[0], "width": 3},
        hovertemplate="%{x|%Y-%m-%d}<br>Price: $%{y:.2f}<extra></extra>",
    )
)
for label, series, color in [(short_label, short_ema, IMPRINT_PALETTE[1]), (long_label, long_ema, IMPRINT_PALETTE[2])]:
    fig.add_trace(
        go.Scatter(
            x=df[DATE],
            y=series,
            mode="lines",
            name=label,
            line={"color": color, "width": 2},
            hovertemplate=f"{label}: $%{{y:.2f}}<extra></extra>",
        )
    )
for mask, label, symbol, color in [
    (golden, "Golden cross", "triangle-up", GOLDEN_CLR),
    (death, "Death cross", "triangle-down", DEATH_CLR),
]:
    if mask.any():
        fig.add_trace(
            go.Scatter(
                x=df.loc[mask, DATE],
                y=short_ema[mask],
                mode="markers",
                name=label,
                marker={"color": color, "size": 9, "symbol": symbol, "line": {"color": PAGE_BG, "width": 1}},
                hovertemplate=f"{label}<br>%{{x|%Y-%m-%d}}<br>EMA: $%{{y:.2f}}<extra></extra>",
            )
        )

fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "indicator-ema · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "linecolor": INK_SOFT,
        "rangeslider": {"visible": True, "bgcolor": PAGE_BG, "bordercolor": INK_SOFT, "thickness": 0.08},
    },
    yaxis={
        "title": {"text": CLOSE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickformat": "$,.0f",
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    legend={
        "font": {"size": 10, "color": INK_SOFT},
        "x": 0.02,
        "y": 0.98,
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    hovermode="x unified",
    margin={"l": 80, "r": 40, "t": 60, "b": 60},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
