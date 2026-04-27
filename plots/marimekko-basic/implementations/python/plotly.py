"""anyplot.ai
marimekko-basic: Basic Marimekko Chart
Library: plotly | Python 3.13
Quality: 93/100 | Created: 2025-12-23
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"

# Okabe-Ito palette — first series always #009E73
COLORS = ["#009E73", "#D55E00", "#0072B2"]

# Data: Market share by region and product line (in millions USD)
regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
products = ["Enterprise", "SMB", "Consumer"]

# Values: rows = products, columns = regions
# Europe adjusted to create clearer width variation from North America
values = [
    [120, 55, 150, 30],  # Enterprise
    [90, 65, 120, 40],  # SMB
    [60, 45, 180, 50],  # Consumer
]

# Calculate bar widths (proportional to column totals)
column_totals = [sum(values[i][j] for i in range(len(products))) for j in range(len(regions))]
total = sum(column_totals)
widths = [ct / total for ct in column_totals]

# Calculate x positions (cumulative widths, centered)
x_positions = []
cumulative = 0
for w in widths:
    x_positions.append(cumulative + w / 2)
    cumulative += w

# Create figure
fig = go.Figure()

# Build stacked bars with proportional heights
for i, product in enumerate(products):
    color = COLORS[i]
    bottoms = []
    heights = []
    for j in range(len(regions)):
        bottom = sum(values[k][j] for k in range(i)) / column_totals[j] if column_totals[j] > 0 else 0
        height = values[i][j] / column_totals[j] if column_totals[j] > 0 else 0
        bottoms.append(bottom)
        heights.append(height)

    fig.add_trace(
        go.Bar(
            x=x_positions,
            y=heights,
            width=widths,
            name=product,
            marker={"color": color, "line": {"color": PAGE_BG, "width": 2}},
            base=bottoms,
            text=[f"${values[i][j]}M" for j in range(len(regions))],
            textposition="inside",
            textfont={"size": 18, "color": "white"},
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "Product: " + product + "<br>"
                "Value: $%{customdata[1]:.0f}M<br>"
                "Share: %{y:.1%}<extra></extra>"
            ),
            customdata=[[regions[j], values[i][j]] for j in range(len(regions))],
        )
    )

# Layout
fig.update_layout(
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    title={
        "text": "Market Share by Region · marimekko-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Region (width = market size)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickmode": "array",
        "tickvals": x_positions,
        "ticktext": regions,
        "range": [0, 1],
        "showgrid": False,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    yaxis={
        "title": {"text": "Product Mix (share within region)", "font": {"size": 22, "color": INK}},
        "tickfont": {"size": 18, "color": INK_SOFT},
        "tickformat": ".0%",
        "range": [0, 1],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": GRID,
        "linecolor": INK_SOFT,
        "zerolinecolor": INK_SOFT,
    },
    barmode="stack",
    bargap=0.02,
    legend={
        "title": {"text": "Product Line", "font": {"size": 20, "color": INK}},
        "font": {"size": 18, "color": INK_SOFT},
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
    },
    margin={"l": 80, "r": 40, "t": 120, "b": 80},
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
