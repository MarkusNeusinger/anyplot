"""anyplot.ai
line-stock-comparison: Stock Price Comparison Chart
Library: plotly 7.1.0 | Python 3.14.10
Quality: 86/100 | Updated: 2026-11-26
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
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
SELECTOR_ACTIVE = "rgba(26,26,23,0.12)" if THEME == "light" else "rgba(240,239,232,0.12)"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DATE = "Date"  # role: date
SYMBOL = "Symbol"  # role: symbol
PRICE = "Adjusted close (USD)"  # role: price

# Constants
BASE = 100  # every series is rebased to this value on its first date

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 252  # approximately 1 year of trading days
date_range = pd.date_range(start="2024-01-01", periods=n_days, freq="B")
stocks = {
    "AAPL": {"total_return": 1.32, "volatility": 0.014},
    "GOOGL": {"total_return": 1.08, "volatility": 0.016},
    "MSFT": {"total_return": 0.93, "volatility": 0.013},
    "SPY": {"total_return": 1.18, "volatility": 0.007},
}
frames = []
for symbol, params in stocks.items():
    noise = np.random.normal(0, params["volatility"], n_days)
    # centre the noise so the year ends at the stated total return
    returns = noise - noise.mean() + np.log(params["total_return"]) / n_days
    frames.append(pd.DataFrame({DATE: date_range, SYMBOL: symbol, PRICE: 100 * np.exp(np.cumsum(returns))}))
df = pd.concat(frames, ignore_index=True)

# Plot: rebase every series to BASE at its first date
REBASED = f"Rebased price (start = {BASE})"
df[REBASED] = df[PRICE] / df.groupby(SYMBOL, sort=False)[PRICE].transform("first") * BASE

fig = go.Figure()
ends = []
for i, (symbol, rows) in enumerate(df.groupby(SYMBOL, sort=False)):
    color = IMPRINT[i % len(IMPRINT)]
    fig.add_trace(
        go.Scatter(
            x=rows[DATE],
            y=rows[REBASED],
            mode="lines",
            name=str(symbol),
            line={"width": 2.5, "color": color},
            hovertemplate=f"{symbol}<br>Date: %{{x|%Y-%m-%d}}<br>Value: %{{y:.1f}}<extra></extra>",
        )
    )
    ends.append((rows[DATE].iloc[-1], rows[REBASED].iloc[-1], color))

# Add horizontal reference line at the base value
fig.add_hline(
    y=BASE,
    line_dash="dash",
    line_color=INK_MUTED,
    line_width=1.5,
    annotation_text=f"Starting Point ({BASE})",
    annotation_position="right",
    annotation_font_size=10,
    annotation_font_color=INK_MUTED,
)

# Add end-point value labels for each series to show final performance
for end_date, final_value, color in ends:
    pct = final_value - BASE
    sign = "+" if pct >= 0 else ""
    fig.add_annotation(
        x=end_date,
        y=final_value,
        text=f"  {sign}{pct:.0f}%",
        showarrow=False,
        xanchor="left",
        yanchor="middle",
        font={"size": 9, "color": color},
    )

# Layout
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "line-stock-comparison · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": DATE, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": False,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
        "rangeselector": {
            "buttons": [
                {"count": 1, "label": "1M", "step": "month", "stepmode": "backward"},
                {"count": 3, "label": "3M", "step": "month", "stepmode": "backward"},
                {"count": 6, "label": "6M", "step": "month", "stepmode": "backward"},
                {"step": "all", "label": "1Y"},
            ],
            "bgcolor": ELEVATED_BG,
            "activecolor": SELECTOR_ACTIVE,
            "bordercolor": INK_SOFT,
            "borderwidth": 1,
            "font": {"color": INK_SOFT, "size": 9},
        },
        "rangeslider": {"visible": True, "bgcolor": ELEVATED_BG, "bordercolor": INK_SOFT, "thickness": 0.05},
    },
    yaxis={
        "title": {"text": REBASED, "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "showgrid": True,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    legend={
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "font": {"size": 10, "color": INK_SOFT},
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
    },
    margin={"l": 80, "r": 110, "t": 80, "b": 80},
    hovermode="x unified",
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
