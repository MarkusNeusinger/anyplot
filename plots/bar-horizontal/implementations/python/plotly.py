""" anyplot.ai
bar-horizontal: Horizontal Bar Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 91/100 | Updated: 2026-05-07
"""

import os
import sys


sys.path = [p for p in sys.path if not p.endswith(os.path.dirname(__file__))]

import plotly.graph_objects as go


np = __import__("numpy")
np.random.seed(42)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"
BRAND = "#009E73"

# Data - Survey results: "What programming language do you use most?"
categories = ["Python", "JavaScript", "TypeScript", "Java", "C++", "Go", "Rust", "Ruby", "PHP", "Swift"]
values = [2847, 2156, 1823, 1542, 987, 756, 623, 412, 389, 298]

# Create horizontal bar chart
fig = go.Figure()

fig.add_trace(
    go.Bar(
        y=categories,
        x=values,
        orientation="h",
        marker=dict(color=BRAND, line=dict(color=INK_SOFT, width=1)),
        text=values,
        textposition="outside",
        textfont=dict(size=24, color=INK_SOFT),
    )
)

# Layout for 4800x2700 px
fig.update_layout(
    title=dict(text="bar-horizontal · plotly · anyplot.ai", font=dict(size=28, color=INK), x=0.5, xanchor="center"),
    xaxis=dict(
        title=dict(text="Number of Responses", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        showgrid=True,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        range=[0, max(values) * 1.08],
    ),
    yaxis=dict(
        title=dict(text="Programming Language", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        autorange="reversed",
        showgrid=False,
        linecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font=dict(color=INK),
    margin=dict(l=200, r=120, t=120, b=100),
    bargap=0.3,
    hovermode="closest",
)

# Save as PNG and HTML to the script's directory
script_dir = os.path.dirname(os.path.abspath(__file__))
fig.write_image(os.path.join(script_dir, f"plot-{THEME}.png"), width=1600, height=900, scale=3)
fig.write_html(os.path.join(script_dir, f"plot-{THEME}.html"), include_plotlyjs="cdn")
