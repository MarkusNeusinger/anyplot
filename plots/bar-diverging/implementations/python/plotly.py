""" anyplot.ai
bar-diverging: Diverging Bar Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 84/100 | Updated: 2026-05-08
"""

import os

import plotly.graph_objects as go


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
GRID = "rgba(26,26,23,0.10)" if THEME == "light" else "rgba(240,239,232,0.10)"

# Okabe-Ito palette: position 1 (green) for positive, position 2 (orange) for negative
POSITIVE_COLOR = "#009E73"
NEGATIVE_COLOR = "#AE3030"  # imprint red — semantic negative

# Data: Customer satisfaction survey results by department
# Scores range from -100 (very dissatisfied) to +100 (very satisfied)
categories = [
    "Customer Support",
    "Product Quality",
    "Delivery Speed",
    "Website Experience",
    "Return Policy",
    "Price Value",
    "Mobile App",
    "Payment Options",
    "Product Variety",
    "Checkout Process",
]
values = [72, 58, -25, 45, -42, 31, -15, 68, 22, -8]

# Sort by value for better pattern recognition
sorted_data = sorted(zip(categories, values, strict=True), key=lambda x: x[1])
categories_sorted = [item[0] for item in sorted_data]
values_sorted = [item[1] for item in sorted_data]

# Assign colors: Okabe-Ito green for positive, orange for negative
colors = [POSITIVE_COLOR if v >= 0 else NEGATIVE_COLOR for v in values_sorted]

# Create horizontal diverging bar chart
fig = go.Figure()

fig.add_trace(
    go.Bar(
        y=categories_sorted,
        x=values_sorted,
        orientation="h",
        marker=dict(color=colors, line=dict(color=PAGE_BG, width=1)),
        text=[f"{v:+d}" for v in values_sorted],
        textposition="outside",
        textfont=dict(size=16, color=INK_SOFT),
    )
)

# Add zero baseline
fig.add_vline(x=0, line=dict(color=INK_SOFT, width=2))

# Layout styling for 4800x2700
fig.update_layout(
    title=dict(
        text="Customer Satisfaction Survey · bar-diverging · plotly · anyplot.ai",
        font=dict(size=28, color=INK),
        x=0.5,
        xanchor="center",
    ),
    xaxis=dict(
        title=dict(text="Satisfaction Score", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        range=[-100, 100],
        dtick=25,
        gridcolor=GRID,
        linecolor=INK_SOFT,
        zerolinecolor=INK_SOFT,
        zeroline=False,
    ),
    yaxis=dict(
        title=dict(text="Department", font=dict(size=22, color=INK)),
        tickfont=dict(size=18, color=INK_SOFT),
        automargin=True,
        linecolor=INK_SOFT,
    ),
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    showlegend=False,
    margin=dict(l=20, r=100, t=80, b=60),
    bargap=0.3,
)

# Save outputs
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
