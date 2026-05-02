"""anyplot.ai
sparkline-basic: Basic Sparkline
Library: altair 6.1.0 | Python 3.13.12
Quality: /100 | Updated: 2026-05-02
"""

import os

import altair as alt
import numpy as np
import pandas as pd


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito categorical palette — identical across themes; only chrome flips.
LINE_COLOR = "#009E73"
MIN_COLOR = "#D55E00"
MAX_COLOR = "#009E73"

# Data — daily web-traffic sessions over 60 days, with a launch bump,
# a mid-month decline, and weekend dips. Mixes ups and downs so the
# sparkline shape is informative.
np.random.seed(42)
n_points = 60
day = np.arange(n_points)
trend = 100 + 0.6 * day
launch_bump = 25 * np.exp(-((day - 12) ** 2) / 30.0)
mid_decline = -22 * np.exp(-((day - 35) ** 2) / 60.0)
weekend = np.where(day % 7 >= 5, -10.0, 0.0)
noise = np.random.randn(n_points) * 4
values = trend + launch_bump + mid_decline + weekend + noise

df = pd.DataFrame({"x": day, "value": values})
min_idx = int(df["value"].idxmin())
max_idx = int(df["value"].idxmax())
extremes = df.iloc[[min_idx, max_idx]].assign(kind=["min", "max"])
endpoints = df.iloc[[0, -1]]

x_enc = alt.X("x:Q", axis=None)
y_enc = alt.Y("value:Q", axis=None, scale=alt.Scale(zero=False))

line = alt.Chart(df).mark_line(strokeWidth=3, color=LINE_COLOR, interpolate="monotone").encode(x=x_enc, y=y_enc)

endpoint_dots = alt.Chart(endpoints).mark_circle(size=160, color=INK_SOFT, opacity=0.7).encode(x=x_enc, y=y_enc)

extreme_dots = (
    alt.Chart(extremes)
    .mark_circle(size=420)
    .encode(
        x=x_enc,
        y=y_enc,
        color=alt.Color("kind:N", scale=alt.Scale(domain=["min", "max"], range=[MIN_COLOR, MAX_COLOR]), legend=None),
    )
)

chart = (
    (line + endpoint_dots + extreme_dots)
    .properties(
        width=1600, height=260, title=alt.Title("sparkline-basic · altair · anyplot.ai", fontSize=28, color=INK)
    )
    .configure_view(strokeWidth=0, fill=PAGE_BG)
    .configure(background=PAGE_BG)
)

chart.save(f"plot-{THEME}.png", scale_factor=3.0)
chart.save(f"plot-{THEME}.html")
