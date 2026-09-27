""" anyplot.ai
bar-error: Bar Chart with Error Bars
Library: plotly 7.1.0 | Python 3.13.15
Quality: 85/100 | Updated: 2026-09-27
"""

import os

import numpy as np
import plotly.graph_objects as go


# Theme tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"  # Imprint palette position 1

# Data - lab experiment comparing treatment effectiveness against a control
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C", "Treatment D"]
values = np.array([45.2, 62.8, 58.3, 71.5, 55.9])
# Asymmetric errors (±1 SD), more dramatic variation across groups
errors_lower = np.array([3.2, 7.8, 2.9, 8.1, 3.5])
errors_upper = np.array([4.1, 9.2, 3.6, 11.3, 4.8])
control_value = values[0]

fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=categories,
        y=values,
        marker=dict(color=BRAND, line=dict(color=INK_SOFT, width=1.5)),
        error_y=dict(
            type="data",
            symmetric=False,
            array=errors_upper,
            arrayminus=errors_lower,
            color=INK_SOFT,
            thickness=2.5,
            width=8,
        ),
        name="Measurement",
        hovertemplate="<b>%{x}</b><br>Value: %{y:.1f}%<br>+%{error_y.array:.1f}% / -%{error_y.arrayminus:.1f}%<extra></extra>",
    )
)

# Dashed control baseline so the reader can immediately see which treatments
# beat the control, without needing to eyeball the axis (design storytelling).
# Label sits in the empty top-left corner of the plot area, not on the line
# itself, so it never overlaps the Control bar's own error cap.
fig.add_hline(y=control_value, line=dict(color=INK_SOFT, width=1.5, dash="dash"))

fig.update_layout(
    autosize=False,
    title=dict(text="bar-error · python · plotly · anyplot.ai", font=dict(size=16, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Treatment Group", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        showgrid=False,
        showline=True,
        linecolor=INK_SOFT,
        linewidth=1,
        mirror=False,
        ticks="outside",
        tickcolor=INK_SOFT,
    ),
    yaxis=dict(
        title=dict(text="Response Value (%)", font=dict(size=12, color=INK)),
        tickfont=dict(size=10, color=INK_SOFT),
        gridcolor=GRID,
        gridwidth=1,
        zeroline=False,
        showline=True,
        linecolor=INK_SOFT,
        linewidth=1,
        mirror=False,
        range=[0, 90],
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    bargap=0.3,
    showlegend=True,
    legend=dict(
        x=0.98, y=0.98, bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, borderwidth=1, font=dict(size=10, color=INK_SOFT)
    ),
    margin=dict(l=80, r=40, t=80, b=60),
)

# NOTE: added via add_annotation (not update_layout(annotations=[...])) so
# repeated calls append instead of clobbering each other.
fig.add_annotation(
    text="Error bars: ±1 SD (asymmetric)",
    xref="paper",
    yref="paper",
    x=0.02,
    y=0.02,
    xanchor="left",
    yanchor="bottom",
    font=dict(size=10, color=INK_SOFT),
    showarrow=False,
)
fig.add_annotation(
    text=f"┄ Control baseline ({control_value:.1f}%)",
    xref="paper",
    yref="paper",
    x=0.02,
    y=0.95,
    xanchor="left",
    yanchor="top",
    font=dict(size=10, color=INK_SOFT),
    showarrow=False,
)

# Theme-aware hover tooltip so the interactive HTML stays legible in dark mode too.
fig.update_traces(hoverlabel=dict(bgcolor=ELEVATED_BG, bordercolor=INK_SOFT, font=dict(color=INK, size=10)))

# Hard target: 3200 x 1800 (landscape). See prompts/library/plotly.md "Canvas".
fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
