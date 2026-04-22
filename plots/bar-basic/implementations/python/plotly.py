""" pyplots.ai
bar-basic: Basic Bar Chart
Library: plotly 6.5.2 | Python 3.14
Quality: 92/100 | Created: 2026-02-14
"""

import plotly.graph_objects as go


# Data — product sales by department, sorted descending
categories = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books", "Toys", "Automotive", "Health"]
values = [45200, 38700, 31500, 27800, 24300, 21600, 18900, 15400]

# Highlight the top performer with a distinct shade
bar_colors = ["#1A4971"] + ["#306998"] * (len(categories) - 1)

# Create figure
fig = go.Figure()

fig.add_trace(
    go.Bar(
        x=categories,
        y=values,
        marker={"color": bar_colors, "line": {"color": "rgba(0,0,0,0.08)", "width": 1}},
        text=values,
        textposition="outside",
        texttemplate="$%{text:,.0f}",
        textfont={"size": 20, "color": "#444444"},
        hovertemplate="<b>%{x}</b><br>Sales: $%{y:,.0f}<extra></extra>",
    )
)

# Annotation: highlight the leading category with an insight callout
fig.add_annotation(
    x="Electronics",
    y=45200,
    text="<b>Top seller</b><br>17% ahead of #2",
    showarrow=True,
    arrowhead=2,
    arrowsize=1.2,
    arrowwidth=2,
    arrowcolor="#1A4971",
    ax=100,
    ay=-75,
    font={"size": 18, "color": "#1A4971"},
    align="left",
    bordercolor="#1A4971",
    borderwidth=1.5,
    borderpad=6,
    bgcolor="rgba(255,255,255,0.85)",
)

# Subtle average reference line
avg_value = sum(values) / len(values)
fig.add_hline(
    y=avg_value,
    line={"color": "rgba(0,0,0,0.25)", "width": 1.5, "dash": "dot"},
    annotation={
        "text": f"Avg ${avg_value:,.0f}",
        "font": {"size": 16, "color": "#666666"},
        "showarrow": False,
        "xanchor": "left",
    },
)

# Layout
fig.update_layout(
    title={
        "text": "bar-basic · plotly · pyplots.ai",
        "font": {"size": 28, "color": "#222222"},
        "x": 0.5,
        "xanchor": "center",
    },
    xaxis={
        "title": {"text": "Product Category", "font": {"size": 22, "color": "#333333"}},
        "tickfont": {"size": 18, "color": "#444444"},
    },
    yaxis={
        "title": {"text": "Sales ($)", "font": {"size": 22, "color": "#333333"}},
        "tickfont": {"size": 18, "color": "#444444"},
        "tickprefix": "$",
        "tickformat": ",.0f",
        "gridcolor": "rgba(0,0,0,0.07)",
        "zeroline": False,
    },
    template="plotly_white",
    bargap=0.3,
    margin={"t": 100, "b": 80, "l": 100, "r": 120},
    plot_bgcolor="white",
    showlegend=False,
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html")
