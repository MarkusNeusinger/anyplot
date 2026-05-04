""" anyplot.ai
sunburst-basic: Basic Sunburst Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-04
"""

import os

import plotly.graph_objects as go


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

labels = [
    "Company",
    "Engineering",
    "Sales",
    "Marketing",
    "Operations",
    "Backend",
    "Frontend",
    "DevOps",
    "Enterprise",
    "SMB",
    "Digital",
    "Brand",
    "HR",
    "Finance",
]

parents = [
    "",
    "Company",
    "Company",
    "Company",
    "Company",
    "Engineering",
    "Engineering",
    "Engineering",
    "Sales",
    "Sales",
    "Marketing",
    "Marketing",
    "Operations",
    "Operations",
]

# Values in $M — branchvalues="total" so each parent value equals sum of its children
values = [
    48,  # Company
    18,  # Engineering — dominant at 37.5% of total
    15,  # Sales
    7,  # Marketing
    8,  # Operations
    8,  # Backend
    6,  # Frontend
    4,  # DevOps
    10,  # Enterprise
    5,  # SMB
    4,  # Digital
    3,  # Brand
    3,  # HR
    5,  # Finance
]

# Okabe-Ito palette — departments get canonical positions 1-4,
# teams get lighter/darker variants to preserve family grouping
colors = [
    ELEVATED_BG,  # Company root — adapts cleanly to both light and dark themes
    "#009E73",  # Engineering — Okabe-Ito #1 (dominant: 37.5%)
    "#D55E00",  # Sales — Okabe-Ito #2
    "#0072B2",  # Marketing — Okabe-Ito #3
    "#CC79A7",  # Operations — Okabe-Ito #4
    "#00B589",  # Backend — lighter green
    "#009E73",  # Frontend — base green
    "#007A58",  # DevOps — darker green
    "#F07030",  # Enterprise — lighter vermillion
    "#D55E00",  # SMB — base vermillion
    "#2090CC",  # Digital — lighter blue
    "#0072B2",  # Brand — base blue
    "#DD99C0",  # HR — lighter pink
    "#CC79A7",  # Finance — base pink
]

fig = go.Figure(
    go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker={"colors": colors, "line": {"color": PAGE_BG, "width": 2}},
        textfont={"size": 22},
        insidetextorientation="radial",
        hovertemplate="<b>%{label}</b><br>Budget: $%{value}M<br>%{percentParent:.1%} of %{parent}<extra></extra>",
        leaf={"opacity": 0.88},
    )
)

fig.update_layout(
    title={
        "text": "sunburst-basic · plotly · anyplot.ai",
        "font": {"size": 36, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"t": 120, "l": 60, "r": 60, "b": 110},
)

# Insight annotation — surface Engineering's outsized 37.5% share
fig.add_annotation(
    text="Engineering leads with 37.5% of total budget — nearly double Sales, the next-largest department",
    xref="paper",
    yref="paper",
    x=0.5,
    y=0.02,
    xanchor="center",
    yanchor="bottom",
    font={"size": 20, "color": INK_MUTED},
    showarrow=False,
)

# Square format — optimal for symmetric radial charts
fig.write_image(f"plot-{THEME}.png", width=1200, height=1200, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
