"""anyplot.ai
histogram-2d: 2D Histogram Heatmap
Library: plotly | Python 3.13
Quality: 91/100 | Created: 2025-12-25
"""

import os

import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Data - customer age vs annual purchase frequency in retail market research
np.random.seed(42)
n_points = 5000

# Create correlated data: older customers tend to have slightly higher purchase frequency
# with realistic distributions
mean = [45, 25]  # Mean age and mean purchases per year
cov = [[150, 35], [35, 120]]  # Positive correlation (0.6)
data = np.random.multivariate_normal(mean, cov, n_points)
age = np.clip(data[:, 0], 18, 85)  # Realistic age range
purchases = np.clip(data[:, 1], 0, 80)  # Purchases per year

# Create figure with marginal histograms using shared_xaxes/shared_yaxes
fig = make_subplots(
    rows=2,
    cols=2,
    column_widths=[0.8, 0.2],
    row_heights=[0.2, 0.8],
    horizontal_spacing=0.01,
    vertical_spacing=0.01,
    shared_xaxes=True,
    shared_yaxes=True,
    specs=[[{"type": "histogram"}, None], [{"type": "histogram2d"}, {"type": "histogram"}]],
)

# Main 2D histogram heatmap
fig.add_trace(
    go.Histogram2d(
        x=age,
        y=purchases,
        colorscale="Viridis",
        nbinsx=40,
        nbinsy=40,
        colorbar=dict(
            title=dict(text="Count", font=dict(size=20)), tickfont=dict(size=16), len=0.65, y=0.35, yanchor="middle"
        ),
    ),
    row=2,
    col=1,
)

# Marginal histogram for age (top)
fig.add_trace(
    go.Histogram(x=age, nbinsx=40, marker=dict(color="#009E73", line=dict(width=0)), showlegend=False), row=1, col=1
)

# Marginal histogram for purchases (right)
fig.add_trace(
    go.Histogram(y=purchases, nbinsy=40, marker=dict(color="#009E73", line=dict(width=0)), showlegend=False),
    row=2,
    col=2,
)

# Update layout with theme-adaptive styling
fig.update_layout(
    title=dict(
        text="histogram-2d · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center", y=0.98
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    bargap=0.02,
)

# Update axes for main plot with descriptive labels
fig.update_xaxes(
    title=dict(text="Customer Age (years)", font=dict(size=22, color=INK)),
    tickfont=dict(size=18, color=INK_SOFT),
    gridcolor=GRID,
    linecolor=INK_SOFT,
    row=2,
    col=1,
)
fig.update_yaxes(
    title=dict(text="Annual Purchases (count)", font=dict(size=22, color=INK)),
    tickfont=dict(size=18, color=INK_SOFT),
    gridcolor=GRID,
    linecolor=INK_SOFT,
    row=2,
    col=1,
)

# Configure marginal histogram axes with grid lines
fig.update_xaxes(showticklabels=False, gridcolor=GRID, linecolor=INK_SOFT, row=1, col=1)
fig.update_yaxes(showticklabels=False, gridcolor=GRID, linecolor=INK_SOFT, row=1, col=1)
fig.update_xaxes(showticklabels=False, gridcolor=GRID, linecolor=INK_SOFT, row=2, col=2)
fig.update_yaxes(showticklabels=False, gridcolor=GRID, linecolor=INK_SOFT, row=2, col=2)

# Save as PNG (4800 x 2700 px)
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)

# Save as interactive HTML
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
