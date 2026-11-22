"""anyplot.ai
pdp-basic: Partial Dependence Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 96/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.datasets import load_diabetes
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.inspection import partial_dependence


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Imprint palette: first position is the brand green
BRAND = "#009E73"

# Columns: set these to your table's column names
FEATURE = "BMI (standardized)"  # role: feature_values
PARTIAL_DEPENDENCE = "Partial dependence (centered)"  # role: partial_dependence
BAND_HALF_WIDTH = "Std deviation of ICE curves"  # role: confidence_interval
OBSERVED = "Observed BMI (standardized)"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("pdp.csv")
diabetes = load_diabetes()
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(diabetes.data, diabetes.target)
bmi = diabetes.feature_names.index("bmi")
average = partial_dependence(model, diabetes.data, features=[bmi], kind="average", grid_resolution=100)
individual = partial_dependence(model, diabetes.data, features=[bmi], kind="individual", grid_resolution=100)
ice_std = individual["individual"][0].std(axis=0)
shift = average["average"][0].mean()
grid = pd.DataFrame(
    {FEATURE: average["grid_values"][0], PARTIAL_DEPENDENCE: average["average"][0] - shift, BAND_HALF_WIDTH: ice_std}
)
# One row per observation; the grid columns are empty past the last grid point
df = pd.concat([grid, pd.Series(diabetes.data[:, bmi], name=OBSERVED)], axis=1)

# Plot: reads only df and the constants above
curve = df.dropna(subset=[FEATURE])
lower = curve[PARTIAL_DEPENDENCE] - curve[BAND_HALF_WIDTH]
upper = curve[PARTIAL_DEPENDENCE] + curve[BAND_HALF_WIDTH]
observed = df[OBSERVED].dropna()
x = curve[FEATURE]
span = upper.max() - lower.min()
rug_y = lower.min() - 0.08 * span

fig = go.Figure()

# Variability band behind the line
fig.add_trace(
    go.Scatter(
        x=pd.concat([x, x[::-1]]),
        y=pd.concat([upper, lower[::-1]]),
        fill="toself",
        fillcolor="rgba(0, 158, 115, 0.15)",
        line=dict(color="rgba(255,255,255,0)"),
        name="±1 Std Deviation",
        hoverinfo="skip",
    )
)

# Partial dependence line
fig.add_trace(
    go.Scatter(
        x=x, y=curve[PARTIAL_DEPENDENCE], mode="lines", line=dict(color=BRAND, width=3), name="Partial Dependence"
    )
)

# Rug of observed values
fig.add_trace(
    go.Scatter(
        x=observed,
        y=np.full(len(observed), rug_y),
        mode="markers",
        marker=dict(symbol="line-ns", size=9, color=INK_SOFT, opacity=0.5, line=dict(width=1)),
        name="Data Distribution",
        hoverinfo="skip",
    )
)

# Zero reference line for the centered curve
fig.add_hline(y=0, line_dash="dash", line_color=INK_SOFT, line_width=1.5)

# Style
fig.update_layout(
    autosize=False,
    width=800,
    height=450,
    title=dict(text="pdp-basic · python · plotly · anyplot.ai", font=dict(size=16, color=INK)),
    xaxis=dict(
        title=dict(text=FEATURE, font=dict(size=13, color=INK)),
        tickfont=dict(size=11, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text=PARTIAL_DEPENDENCE, font=dict(size=13, color=INK)),
        tickfont=dict(size=11, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    legend=dict(
        font=dict(size=11, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=70, r=40, t=70, b=60),
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
