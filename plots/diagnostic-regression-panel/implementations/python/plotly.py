"""anyplot.ai
diagnostic-regression-panel: Regression Diagnostic Panel (Four-Plot Display)
Library: plotly 6.7.0 | Python 3.13.13
Quality: 89/100 | Created: 2026-05-13
"""

import os

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from scipy import stats
from statsmodels.nonparametric.smoothers_lowess import lowess


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
COOK_LEVELS = (0.5, 1.0)  # Cook's distance contours the leverage panel draws
N_LABELED = 3  # most influential observations labeled in every panel

# Columns: set these to your table's column names
FITTED = "Fitted values"  # role: fitted
RESIDUALS = "Residuals"  # role: residuals
STD_RESIDUALS = "Standardized residuals"  # role: std_residuals
LEVERAGE = "Leverage"  # role: leverage
COOKS_D = "Cook's distance"  # role: cooks_d

# Data: replace this block with your own table, for example df = pd.read_csv("diagnostics.csv")
# Synthetic apartment-rent regression (rent ~ sqft + bedrooms) with a few injected outliers
rng = np.random.default_rng(42)
n_obs = 200
sqft = rng.uniform(400, 3000, n_obs)
beds = rng.uniform(1.0, 6.0, n_obs)
sqft[185], sqft[186] = 5800.0, 6200.0  # high-leverage observations
beds[190], beds[191] = 11.0, 12.5
design = np.column_stack([np.ones(n_obs), sqft, beds])
noise = rng.normal(0, 25, n_obs)
noise[[15, 22, 67]] += [110, -95, 70]  # high-residual outliers
rent = design @ [200.0, 0.18, 120.0] + noise

xtx_inv = np.linalg.inv(design.T @ design)
fit = design @ (xtx_inv @ design.T @ rent)
resid = rent - fit
hat = np.clip(np.einsum("ij,jk,ik->i", design, xtx_inv, design), 0.0, 1.0 - 1e-10)
n_params = design.shape[1]
mse = resid @ resid / (n_obs - n_params)
std_resid = resid / np.sqrt(mse * (1.0 - hat))
df = pd.DataFrame(
    {
        FITTED: fit,
        RESIDUALS: resid,
        STD_RESIDUALS: std_resid,
        LEVERAGE: hat,
        COOKS_D: std_resid**2 * hat / (n_params * (1.0 - hat)),
    }
)

# Plot: reads only df and the constants above
fitted = df[FITTED].to_numpy()
resid = df[RESIDUALS].to_numpy()
sr = df[STD_RESIDUALS].to_numpy()
lev = df[LEVERAGE].to_numpy()
cooks = df[COOKS_D].to_numpy()
sqrt_abs_sr = np.sqrt(np.abs(sr))

# Number of model parameters, recovered from Cook's distance = sr^2 * h / (p * (1 - h))
valid = np.isfinite(cooks) & (cooks > 0)
n_params = np.median(sr[valid] ** 2 * lev[valid] / ((1.0 - lev[valid]) * cooks[valid]))

# Most influential observations: highest Cook's distance, labeled by row index
top = np.argsort(np.nan_to_num(cooks, nan=-np.inf))[-N_LABELED:][::-1]
labels = [str(df.index[i]) for i in top]

# LOWESS smoothers for the residual and scale-location panels
lo_resid = lowess(resid, fitted)
lo_scale = lowess(sqrt_abs_sr, fitted)

# Normal Q-Q: theoretical quantiles against standardized residuals, with the fitted reference line
(theo, ordered), (qq_slope, qq_icpt, _) = stats.probplot(sr, dist="norm")
rank = np.empty(len(sr), dtype=int)
rank[np.argsort(sr)] = np.arange(len(sr))
qq_x = np.array([theo.min(), theo.max()])

# Cook's distance contours: |standardized residual| = sqrt(D * p * (1 - h) / h)
lev_grid = np.linspace(lev.min() * 0.5 + 1e-3, lev.max() * 1.5, 400)
r_limit = np.nanmax(np.abs(sr)) * 1.2

fig = make_subplots(
    rows=2,
    cols=2,
    subplot_titles=["Residuals vs Fitted", "Normal Q-Q", "Scale-Location", "Residuals vs Leverage"],
    horizontal_spacing=0.14,
    vertical_spacing=0.17,
)

point = dict(color=IMPRINT_PALETTE[0], size=6, opacity=0.7, line=dict(color=PAGE_BG, width=0.5))
smoother = dict(color=IMPRINT_PALETTE[1], width=1.8)
reference = dict(color=INK_SOFT, width=1.0, dash="dash")


def labeled(x, y, row, col):
    """Observation-index labels beside the most influential points."""
    fig.add_trace(
        go.Scatter(
            x=x,
            y=y,
            mode="text",
            text=labels,
            textposition="middle right",
            textfont=dict(size=10, color=INK_MUTED),
            showlegend=False,
        ),
        row=row,
        col=col,
    )


# Residuals vs Fitted
fig.add_trace(go.Scatter(x=fitted, y=resid, mode="markers", marker=point), row=1, col=1)
fig.add_trace(go.Scatter(x=[fitted.min(), fitted.max()], y=[0, 0], mode="lines", line=reference), row=1, col=1)
fig.add_trace(go.Scatter(x=lo_resid[:, 0], y=lo_resid[:, 1], mode="lines", line=smoother), row=1, col=1)
labeled(fitted[top], resid[top], 1, 1)

# Normal Q-Q
fig.add_trace(go.Scatter(x=theo, y=ordered, mode="markers", marker=point), row=1, col=2)
fig.add_trace(go.Scatter(x=qq_x, y=qq_slope * qq_x + qq_icpt, mode="lines", line=reference), row=1, col=2)
labeled(theo[rank[top]], ordered[rank[top]], 1, 2)

# Scale-Location
fig.add_trace(go.Scatter(x=fitted, y=sqrt_abs_sr, mode="markers", marker=point), row=2, col=1)
fig.add_trace(go.Scatter(x=lo_scale[:, 0], y=lo_scale[:, 1], mode="lines", line=smoother), row=2, col=1)
labeled(fitted[top], sqrt_abs_sr[top], 2, 1)

# Residuals vs Leverage
fig.add_trace(go.Scatter(x=lev, y=sr, mode="markers", marker=point), row=2, col=2)
fig.add_trace(go.Scatter(x=[0.0, lev_grid.max()], y=[0, 0], mode="lines", line=reference), row=2, col=2)
for k, level in enumerate(COOK_LEVELS):
    radius = np.sqrt(level * n_params * (1.0 - lev_grid) / lev_grid)
    keep = radius < r_limit
    contour = dict(color=IMPRINT_PALETTE[3], width=1.2 + 0.6 * k, dash="dot")
    for sign in (1, -1):
        fig.add_trace(go.Scatter(x=lev_grid[keep], y=sign * radius[keep], mode="lines", line=contour), row=2, col=2)
    if keep.any():
        fig.add_trace(
            go.Scatter(
                x=[lev_grid[keep][-1]],
                y=[radius[keep][-1]],
                mode="text",
                text=[f"D = {level:g}"],
                textposition="top left",
                textfont=dict(size=9, color=IMPRINT_PALETTE[3]),
            ),
            row=2,
            col=2,
        )
labeled(lev[top], sr[top], 2, 2)

# Style
fig.update_layout(
    autosize=False,
    title=dict(
        text="diagnostic-regression-panel · python · plotly · anyplot.ai",
        font=dict(size=14, color=INK),
        x=0.5,
        xanchor="center",
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    showlegend=False,
    margin=dict(t=60, l=50, r=20, b=45),
)
fig.update_annotations(font=dict(size=12, color=INK))

axis_style = dict(
    title_font=dict(size=11, color=INK),
    title_standoff=4,
    tickfont=dict(size=10, color=INK_SOFT),
    gridcolor=GRID,
    linecolor=INK_SOFT,
    zeroline=False,
    showgrid=True,
    showline=True,
    mirror=False,
)
fig.update_xaxes(title_text=FITTED, row=1, col=1, **axis_style)
fig.update_xaxes(title_text="Theoretical quantiles", row=1, col=2, **axis_style)
fig.update_xaxes(title_text=FITTED, row=2, col=1, **axis_style)
fig.update_xaxes(title_text=LEVERAGE, row=2, col=2, **axis_style)
fig.update_yaxes(title_text=RESIDUALS, row=1, col=1, **axis_style)
fig.update_yaxes(title_text=STD_RESIDUALS, row=1, col=2, **axis_style)
fig.update_yaxes(title_text=f"√|{STD_RESIDUALS}|", row=2, col=1, **axis_style)
fig.update_yaxes(title_text=STD_RESIDUALS, row=2, col=2, range=[-r_limit, r_limit], **axis_style)

fig.write_image(f"plot-{THEME}.png", width=600, height=600, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
