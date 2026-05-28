""" anyplot.ai
bar-basic: Basic Bar Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 90/100 | Created: 2026-05-28
"""

import os
import sys


# Prevent self-import: remove this script's own directory from sys.path so that
# "import plotly" resolves to the installed package, not this file.
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")

PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# anyplot palette: brand green for top performer, blue for rest
BRAND = "#009E73"
BASE = "#4467A3"

# Data — product sales by department, sorted descending
categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Automotive", "Health"]
values = [45200, 38700, 31500, 27800, 24300, 21600, 18900, 15400]

bar_colors = [BRAND] + [BASE] * (len(categories) - 1)

fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=categories,
        y=values,
        marker={"color": bar_colors, "line": {"color": "rgba(0,0,0,0.06)", "width": 1}},
        text=values,
        textposition="outside",
        texttemplate="$%{text:,.0f}",
        textfont={"size": 10, "color": INK_SOFT},
        hovertemplate="<b>%{x}</b><br>Sales: $%{y:,.0f}<extra></extra>",
    )
)

# Annotation: arrow from Electronics bar top sweeps right to a callout in clear whitespace;
# the shallow diagonal passes above all shorter bars, avoiding the Clothing value label
fig.add_annotation(
    x="Electronics",
    y=45200,
    text="<b>Top seller</b><br>17% ahead of #2",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=2,
    arrowcolor=BRAND,
    ax=280,
    ay=30,
    font={"size": 10, "color": BRAND},
    align="left",
    bordercolor=BRAND,
    borderwidth=1.5,
    borderpad=6,
    bgcolor=ELEVATED_BG,
)

avg_value = sum(values) / len(values)
fig.add_hline(
    y=avg_value,
    line={"color": INK_MUTED, "width": 1.5, "dash": "dot"},
    annotation_text=f"Avg ${avg_value:,.0f}",
    annotation_font_size=10,
    annotation_font_color=INK_MUTED,
    annotation_position="top left",
)

fig.update_layout(
    autosize=False,
    title={
        "text": "bar-basic · python · plotly · anyplot.ai",
        "font": {"size": 16, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Product Category", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "linecolor": INK_SOFT,
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "Sales ($)", "font": {"size": 12, "color": INK}},
        "tickfont": {"size": 10, "color": INK_SOFT},
        "tickprefix": "$",
        "tickformat": ",.0f",
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zeroline": False,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    template="plotly_white",
    bargap=0.3,
    margin={"t": 80, "b": 60, "l": 100, "r": 40},
    showlegend=False,
)

fig.write_image(f"plot-{THEME}.png", width=800, height=450, scale=4)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
