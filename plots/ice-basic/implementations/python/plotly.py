""" anyplot.ai
ice-basic: Individual Conditional Expectation (ICE) Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-07
"""

import os
import sys


# Prevent this file (plotly.py) from shadowing the plotly package
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.normpath(os.path.abspath(p or ".")) != _here]

import numpy as np
import plotly.colors as pc
import plotly.graph_objects as go
from sklearn.ensemble import GradientBoostingRegressor


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data — synthetic housing dataset
np.random.seed(42)
n_houses = 120

sqft = np.random.uniform(800, 3500, n_houses)
bedrooms = np.random.randint(2, 6, n_houses).astype(float)
house_age = np.random.uniform(1, 50, n_houses)
lot_size = np.random.uniform(3000, 15000, n_houses)
neighborhood_score = np.random.uniform(3, 10, n_houses)

sale_price = (
    150 * sqft
    + 8000 * bedrooms
    - 1200 * house_age
    + 5 * lot_size
    + 15000 * neighborhood_score
    + np.random.normal(0, 25000, n_houses)
)

X = np.column_stack([sqft, bedrooms, house_age, lot_size, neighborhood_score])
model = GradientBoostingRegressor(n_estimators=100, max_depth=4, random_state=42)
model.fit(X, sale_price)

# ICE predictions: vary square footage, hold all other features fixed per house
sqft_grid = np.linspace(sqft.min(), sqft.max(), 80)
ice_preds = np.zeros((n_houses, len(sqft_grid)))
for j, val in enumerate(sqft_grid):
    X_mod = X.copy()
    X_mod[:, 0] = val
    ice_preds[:, j] = model.predict(X_mod)

pdp = ice_preds.mean(axis=0)

# ICE line colors from viridis mapped to house age
age_norm = (house_age - house_age.min()) / (house_age.max() - house_age.min())
raw_colors = pc.sample_colorscale("viridis", age_norm.tolist())
ice_colors = [c.replace("rgb(", "rgba(").replace(")", ", 0.30)") for c in raw_colors]

# Plot
fig = go.Figure()

# ICE lines colored by house age (viridis)
for i in range(n_houses):
    fig.add_trace(
        go.Scatter(
            x=sqft_grid,
            y=ice_preds[i],
            mode="lines",
            line=dict(width=1.5, color=ice_colors[i]),
            showlegend=False,
            hoverinfo="skip",
        )
    )

# PDP overlay — bold brand-green curve
fig.add_trace(
    go.Scatter(
        x=sqft_grid,
        y=pdp,
        mode="lines",
        name="Partial Dependence (PDP)",
        line=dict(width=5, color=BRAND),
        showlegend=True,
    )
)

# Rug plot — distribution of observed square footage values
y_range = ice_preds.max() - ice_preds.min()
y_rug = ice_preds.min() - y_range * 0.05
fig.add_trace(
    go.Scatter(
        x=sqft,
        y=[y_rug] * n_houses,
        mode="markers",
        marker=dict(symbol="line-ns", size=18, color=INK_SOFT, line=dict(width=1.5, color=INK_SOFT)),
        showlegend=False,
        hoverinfo="skip",
    )
)

# Dummy trace to render the house age colorbar
fig.add_trace(
    go.Scatter(
        x=[None],
        y=[None],
        mode="markers",
        marker=dict(
            colorscale="viridis",
            color=[house_age.min(), house_age.max()],
            cmin=house_age.min(),
            cmax=house_age.max(),
            colorbar=dict(
                title=dict(text="House Age (yrs)", font=dict(size=18, color=INK_SOFT)),
                tickfont=dict(size=16, color=INK_SOFT),
                thickness=22,
                len=0.75,
                x=1.02,
                bgcolor=ELEVATED_BG,
                bordercolor=INK_SOFT,
                borderwidth=1,
            ),
            showscale=True,
        ),
        showlegend=False,
        hoverinfo="skip",
    )
)

# Style
fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    title=dict(text="ice-basic · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Square Footage", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=GRID,
        showgrid=True,
        mirror=False,
    ),
    yaxis=dict(
        title=dict(text="Predicted Sale Price (USD)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=GRID,
        showgrid=True,
        tickformat="$,.0f",
        range=[y_rug - y_range * 0.02, ice_preds.max() + y_range * 0.03],
    ),
    legend=dict(
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        font=dict(size=18, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
    ),
    margin=dict(l=80, r=140, t=80, b=80),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
