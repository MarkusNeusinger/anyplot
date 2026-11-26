"""anyplot.ai
drawdown-basic: Drawdown Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-23
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
GRID = "rgba(26, 26, 23, 0.10)" if THEME == "light" else "rgba(240, 239, 232, 0.10)"

# Imprint palette: full list in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
RECOVERY_GREEN = IMPRINT_PALETTE[0]  # semantic: recovery / new high
LOSS_RED = IMPRINT_PALETTE[4]  # semantic: loss / drawdown
LOSS_FILL = "rgba(174, 48, 48, 0.30)"  # LOSS_RED, semi-transparent

# Constants
DRAWDOWN = "Drawdown (%)"  # role: extra

# Column constants
DATE = "Date"  # role: date
PRICE = "Price (index, start = 100)"  # role: price

# Data: replace this block with your own table, for example df = pd.read_csv("prices.csv")
np.random.seed(42)
n_days = 500
returns = np.random.normal(0.0003, 0.015, n_days)
returns[100:150] -= 0.008  # market correction
returns[300:350] -= 0.012  # larger drawdown period
df = pd.DataFrame({DATE: pd.date_range("2022-01-01", periods=n_days, freq="B"), PRICE: 100 * np.cumprod(1 + returns)})

# Plot
# Drawdown: percentage decline from the running maximum
running_max = df[PRICE].cummax()
df[DRAWDOWN] = (df[PRICE] - running_max) / running_max * 100

# Maximum drawdown
max_dd_idx = df[DRAWDOWN].idxmin()
max_dd_value = df.loc[max_dd_idx, DRAWDOWN]
max_dd_date = df.loc[max_dd_idx, DATE]

# Recovery points: drawdown returns to zero after being negative
recovery_mask = (df[DRAWDOWN] == 0) & (df[DRAWDOWN].shift(1) < 0)
recovery_dates = df.loc[recovery_mask, DATE]

# Longest run of consecutive days below the previous peak
under_water = df[DRAWDOWN] < 0
max_dd_duration = int(under_water.groupby((~under_water).cumsum()).sum().max())

fig = go.Figure()

# Drawdown fill area
fig.add_trace(
    go.Scatter(
        x=df[DATE],
        y=df[DRAWDOWN],
        fill="tozeroy",
        fillcolor=LOSS_FILL,
        line=dict(color=LOSS_RED, width=2),
        name="Drawdown",
        hovertemplate="Date: %{x|%Y-%m-%d}<br>Drawdown: %{y:.2f}%<extra></extra>",
    )
)

# Maximum drawdown marker
fig.add_trace(
    go.Scatter(
        x=[max_dd_date],
        y=[max_dd_value],
        mode="markers+text",
        marker=dict(size=14, color=LOSS_RED, symbol="diamond"),
        text=[f"Max DD: {max_dd_value:.1f}%"],
        textposition="bottom center",
        textfont=dict(size=10, color=INK),
        name="Max Drawdown",
        showlegend=False,
        hovertemplate=f"Max Drawdown<br>Date: {max_dd_date:%Y-%m-%d}<br>Drawdown: {max_dd_value:.2f}%<extra></extra>",
    )
)

# Recovery point markers
if len(recovery_dates) > 0:
    fig.add_trace(
        go.Scatter(
            x=recovery_dates,
            y=[0] * len(recovery_dates),
            mode="markers",
            marker=dict(size=16, color=RECOVERY_GREEN, symbol="triangle-up"),
            name="Recovery (New High)",
            hovertemplate="Recovery<br>Date: %{x|%Y-%m-%d}<extra></extra>",
        )
    )

# Statistics annotation inside plot (bottom-left)
stats_text = (
    f"<b>Drawdown Statistics</b><br>"
    f"Max Drawdown: {max_dd_value:.2f}%<br>"
    f"Max Duration: {max_dd_duration} days<br>"
    f"Recovery Points: {len(recovery_dates)}"
)

fig.add_annotation(
    text=stats_text,
    xref="paper",
    yref="paper",
    x=0.02,
    y=0.04,
    xanchor="left",
    yanchor="bottom",
    showarrow=False,
    font=dict(size=10, color=INK_SOFT),
    align="left",
    bordercolor=INK_SOFT,
    borderwidth=1,
    borderpad=8,
    bgcolor=ELEVATED_BG,
)

# Layout
fig.update_layout(
    autosize=False,
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title=dict(
        text="drawdown-basic · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text=DATE, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text=DRAWDOWN, font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        ticksuffix="%",
        showgrid=True,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zeroline=True,
        zerolinewidth=2,
        zerolinecolor=INK_SOFT,
    ),
    showlegend=True,
    legend=dict(
        font=dict(size=10, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        orientation="h",
        yanchor="bottom",
        y=1.0,
        xanchor="center",
        x=0.5,
    ),
    margin=dict(l=80, r=40, t=80, b=60),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
