""" pyplots.ai
marimekko-basic: Basic Marimekko Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 93/100 | Created: 2025-12-23
"""

import plotly.graph_objects as go


# Data: Market share by region and product line (in millions USD)
regions = ["North America", "Europe", "Asia Pacific", "Latin America"]
products = ["Enterprise", "SMB", "Consumer"]
colors = ["#306998", "#FFD43B", "#4ECDC4"]

# Values: rows = products, columns = regions
values = [
    [120, 80, 150, 30],  # Enterprise
    [90, 100, 120, 40],  # SMB
    [60, 70, 180, 50],  # Consumer
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
    color = colors[i]
    bottoms = []
    heights = []
    for j in range(len(regions)):
        # Calculate cumulative bottom from previous products
        bottom = sum(values[k][j] for k in range(i)) / column_totals[j] if column_totals[j] > 0 else 0
        height = values[i][j] / column_totals[j] if column_totals[j] > 0 else 0
        bottoms.append(bottom)
        heights.append(height)

    # Add bars for this product across all regions
    fig.add_trace(
        go.Bar(
            x=x_positions,
            y=heights,
            width=widths,
            name=product,
            marker={"color": color, "line": {"color": "white", "width": 2}},
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
    title={
        "text": "Market Share by Region · marimekko-basic · plotly · pyplots.ai",
        "font": {"size": 28},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Region (width = market size)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "tickmode": "array",
        "tickvals": x_positions,
        "ticktext": regions,
        "range": [0, 1],
        "showgrid": False,
    },
    yaxis={
        "title": {"text": "Product Mix (share within region)", "font": {"size": 22}},
        "tickfont": {"size": 18},
        "tickformat": ".0%",
        "range": [0, 1],
        "showgrid": True,
        "gridwidth": 1,
        "gridcolor": "rgba(0,0,0,0.1)",
    },
    barmode="stack",
    bargap=0.02,
    template="plotly_white",
    legend={
        "title": {"text": "Product Line", "font": {"size": 20}},
        "font": {"size": 18},
        "orientation": "h",
        "yanchor": "bottom",
        "y": 1.02,
        "xanchor": "center",
        "x": 0.5,
    },
    margin={"l": 80, "r": 40, "t": 120, "b": 80},
)

# Save outputs
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
