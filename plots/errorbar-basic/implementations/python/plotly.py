"""pyplots.ai
errorbar-basic: Basic Error Bar Plot
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Updated: 2026-04-25
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"  # Okabe-Ito position 1

# Data — clinical trial response (mg/dL) with asymmetric 95% confidence intervals
np.random.seed(42)
groups = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E"]
x_positions = list(range(len(groups)))
means = np.array([42.3, 51.7, 63.2, 47.8, 72.4, 58.9])
err_upper = np.array([5.4, 7.8, 4.1, 9.3, 3.6, 6.5])
err_lower = np.array([4.1, 6.2, 3.8, 7.9, 4.7, 5.1])

# Plot
fig = go.Figure()

fig.add_trace(
    go.Scatter(
        x=x_positions,
        y=means,
        mode="markers",
        marker=dict(size=28, color=BRAND, line=dict(color=PAGE_BG, width=3)),
        error_y=dict(
            type="data",
            symmetric=False,
            array=err_upper,
            arrayminus=err_lower,
            visible=True,
            thickness=4,
            width=18,
            color=BRAND,
        ),
        name="Mean ± 95% CI",
        customdata=np.stack([np.array(groups), means - err_lower, means + err_upper], axis=-1),
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "Mean: %{y:.1f} mg/dL<br>"
            "95%% CI: [%{customdata[1]:.1f}, %{customdata[2]:.1f}]"
            "<extra></extra>"
        ),
    )
)

# Style
fig.update_layout(
    title=dict(
        text="Clinical Response by Group · errorbar-basic · plotly · pyplots.ai",
        font=dict(size=28, color=INK),
        x=0.5,
        xanchor="center",
        y=0.95,
    ),
    xaxis=dict(
        title=dict(text="Experimental Group", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        tickmode="array",
        tickvals=x_positions,
        ticktext=groups,
        showgrid=False,
        linecolor=INK_SOFT,
        zeroline=False,
        ticks="",
    ),
    yaxis=dict(
        title=dict(text="Response (mg/dL)", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        linecolor=INK_SOFT,
        zeroline=False,
        range=[0, 90],
        ticks="",
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    margin=dict(l=140, r=80, t=130, b=120),
    showlegend=True,
    legend=dict(
        font=dict(size=16, color=INK_SOFT),
        bgcolor=ELEVATED_BG,
        bordercolor=INK_SOFT,
        borderwidth=1,
        x=0.98,
        y=0.98,
        xanchor="right",
        yanchor="top",
    ),
    hoverlabel=dict(bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, font=dict(color=INK, size=16)),
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
