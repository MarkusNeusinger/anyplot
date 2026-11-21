"""anyplot.ai
polar-line: Polar Line Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-12
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
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions, one per series in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
HOURS_PER_CYCLE = 24  # the angular axis is a 24-hour clock

# Columns: set these to your table's column names
HOUR = "Hour of day"  # role: theta
SESSIONS = ["Weekday", "Weekend"]  # role: radius

# Data: replace this block with your own table, for example df = pd.read_csv("traffic.csv")
rng = np.random.default_rng(42)
hours = np.arange(HOURS_PER_CYCLE)


def bump(center, width):
    """Smooth daily peak on a 24-hour clock (wraps around midnight)."""
    gap = (hours - center + 12) % 24 - 12
    return np.exp(-(gap**2) / (2 * width**2))


weekday = 6 + 30 * bump(10, 2.2) + 22 * bump(15, 2.5) + 14 * bump(21, 2.0) + rng.normal(0, 1.0, 24)
weekend = 5 + 12 * bump(12, 3.0) + 26 * bump(21.5, 2.6) + rng.normal(0, 0.8, 24)
df = pd.DataFrame({HOUR: hours, SESSIONS[0]: np.round(weekday, 1), SESSIONS[1]: np.round(weekend, 1)})

# Plot: reads only df and the constants above
DEG_PER_HOUR = 360 / HOURS_PER_CYCLE
table = df.sort_values(HOUR)
closed = pd.concat([table, table.iloc[[0]]], ignore_index=True)
closed.loc[closed.index[-1], HOUR] = table[HOUR].iloc[0] + HOURS_PER_CYCLE
theta = closed[HOUR] * DEG_PER_HOUR

fig = go.Figure()
for i, name in enumerate(SESSIONS):
    fig.add_trace(
        go.Scatterpolar(
            r=closed[name],
            theta=theta,
            mode="lines+markers",
            name=name,
            line=dict(color=IMPRINT_PALETTE[i], width=2.5),
            marker=dict(size=5, color=IMPRINT_PALETTE[i]),
            customdata=closed[HOUR] % HOURS_PER_CYCLE,
            hovertemplate="%{customdata}:00<br>%{r:.1f}k sessions<extra>" + name + "</extra>",
        )
    )

title = "Hourly Website Traffic · polar-line · python · plotly · anyplot.ai"
title_size = round(16 * min(1.0, 67 / len(title)))

fig.update_layout(
    autosize=False,
    title=dict(text=title, font=dict(size=title_size, color=INK), x=0.5, xanchor="center"),
    font=dict(color=INK),
    polar=dict(
        domain=dict(x=[0.1, 0.9], y=[0.1, 0.9]),
        bgcolor=PAGE_BG,
        radialaxis=dict(
            range=[0, df[SESSIONS].to_numpy().max() * 1.08],
            angle=90,
            tickangle=0,
            tickfont=dict(size=10, color=INK_SOFT),
            gridcolor=GRID,
            linecolor=INK_SOFT,
        ),
        angularaxis=dict(
            direction="clockwise",
            rotation=90,
            tickmode="array",
            tickvals=[h * DEG_PER_HOUR for h in range(0, HOURS_PER_CYCLE, 3)],
            ticktext=[f"{h}:00" for h in range(0, HOURS_PER_CYCLE, 3)],
            tickfont=dict(size=11, color=INK_SOFT),
            gridcolor=GRID,
            linecolor=INK_SOFT,
        ),
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend=dict(
        font=dict(size=11, color=INK_SOFT),
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    annotations=[
        dict(
            text="Radius: sessions (thousands per hour) · Angle: hour of day",
            x=0.5,
            y=-0.01,
            xref="paper",
            yref="paper",
            yanchor="top",
            showarrow=False,
            font=dict(size=12, color=INK),
        )
    ],
    width=600,
    height=600,
    margin=dict(l=60, r=60, t=70, b=60),
)

# Save outputs
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
