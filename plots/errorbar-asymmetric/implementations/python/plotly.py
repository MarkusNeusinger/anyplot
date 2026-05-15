"""anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: plotly 6.7.0 | Python 3.13.13
Quality: 80/100 | Updated: 2026-05-15
"""

import os

import numpy as np
import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

np.random.seed(42)

products = ["Product A", "Product B", "Product C", "Product D", "Product E", "Product F"]
sales_median = np.array([85, 62, 45, 78, 95, 55])
error_lower = np.array([12, 8, 15, 10, 18, 7])
error_upper = np.array([25, 18, 10, 22, 35, 20])

lower_bound = sales_median - error_lower
upper_bound = sales_median + error_upper

fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=products,
        y=sales_median,
        mode="markers",
        marker=dict(size=18, color=BRAND, line=dict(width=2, color=PAGE_BG)),
        error_y=dict(
            type="data", symmetric=False, array=error_upper, arrayminus=error_lower, color=BRAND, thickness=3, width=12
        ),
        name="Median Sales (10th–90th percentile)",
        showlegend=True,
        hovertemplate=(
            "<b>%{x}</b><br>"
            "Median: %{y:.0f}k USD<br>"
            "10th–90th: %{customdata[0]:.0f}k – %{customdata[1]:.0f}k USD"
            "<extra></extra>"
        ),
        customdata=np.column_stack([lower_bound, upper_bound]),
    )
)

fig.update_layout(
    title=dict(
        text="errorbar-asymmetric · plotly · anyplot.ai", font=dict(size=32, color=INK), x=0.5, xanchor="center"
    ),
    xaxis=dict(
        title=dict(text="Product Category", font=dict(size=24, color=INK)),
        tickfont=dict(size=20, color=INK_SOFT),
        showgrid=False,
        showline=True,
        linecolor=INK_SOFT,
        mirror=False,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Quarterly Sales (thousands USD)", font=dict(size=24, color=INK)),
        tickfont=dict(size=20, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        gridwidth=1,
        showline=True,
        linecolor=INK_SOFT,
        mirror=False,
        zeroline=False,
        range=[0, 150],
    ),
    template="none",
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    legend=dict(
        font=dict(size=18, color=INK_SOFT),
        x=0.02,
        y=0.98,
        xanchor="left",
        yanchor="top",
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
    ),
    margin=dict(l=100, r=80, t=120, b=100),
)

fig.add_annotation(
    x=0.98,
    y=0.02,
    xref="paper",
    yref="paper",
    text="Error bars show 10th–90th percentile range",
    showarrow=False,
    font=dict(size=16, color=INK_MUTED),
    align="right",
    xanchor="right",
    yanchor="bottom",
)

fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
