""" pyplots.ai
donut-nested: Nested Donut Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-25
"""

import plotly.graph_objects as go


# Data - Company budget allocation by department and expense category
departments = ["Engineering", "Marketing", "Sales", "Operations"]
dept_values = [45, 25, 18, 12]  # Millions
dept_colors = ["#306998", "#FFD43B", "#4ECDC4", "#FF6B6B"]

# Child categories (outer ring) with consistent color families
categories = [
    # Engineering (blues)
    "Salaries",
    "Infrastructure",
    "R&D",
    "Tools",
    # Marketing (yellows/golds)
    "Advertising",
    "Events",
    "Content",
    # Sales (teals)
    "Commissions",
    "Travel",
    "Training",
    # Operations (reds/corals)
    "Facilities",
    "IT Support",
]
cat_values = [
    # Engineering: 45M total
    22,
    12,
    8,
    3,
    # Marketing: 25M total
    14,
    7,
    4,
    # Sales: 18M total
    10,
    5,
    3,
    # Operations: 12M total
    8,
    4,
]
# Color families - lighter shades for children within each parent
cat_colors = [
    # Engineering blues
    "#306998",
    "#4682B4",
    "#5B9BD5",
    "#7CB9E8",
    # Marketing yellows
    "#FFD43B",
    "#FFE066",
    "#FFEB99",
    # Sales teals
    "#4ECDC4",
    "#7DDCD5",
    "#A6EBE6",
    # Operations reds
    "#FF6B6B",
    "#FF9999",
]

# Create figure with two pie traces (inner and outer rings)
fig = go.Figure()

# Inner ring - Departments (parent categories)
fig.add_trace(
    go.Pie(
        values=dept_values,
        labels=departments,
        hole=0.30,
        domain={"x": [0.12, 0.72], "y": [0.05, 0.95]},
        marker=dict(colors=dept_colors, line=dict(color="white", width=3)),
        textinfo="percent",
        textposition="inside",
        textfont=dict(size=20, color="white"),
        hovertemplate="<b>%{label}</b><br>$%{value}M<br>%{percent}<extra></extra>",
        name="Departments",
        sort=False,
    )
)

# Outer ring - Expense categories (child categories)
fig.add_trace(
    go.Pie(
        values=cat_values,
        labels=categories,
        hole=0.58,
        domain={"x": [0.12, 0.72], "y": [0.05, 0.95]},
        marker=dict(colors=cat_colors, line=dict(color="white", width=2)),
        textinfo="label",
        textposition="outside",
        textfont=dict(size=16),
        hovertemplate="<b>%{label}</b><br>$%{value}M<br>%{percent}<extra></extra>",
        name="Categories",
        sort=False,
    )
)

# Layout
fig.update_layout(
    title=dict(
        text="Company Budget Allocation · donut-nested · plotly · pyplots.ai",
        font=dict(size=28),
        x=0.5,
        xanchor="center",
    ),
    showlegend=True,
    legend=dict(font=dict(size=16), orientation="v", x=1.02, y=0.5, yanchor="middle"),
    template="plotly_white",
    margin=dict(l=80, r=200, t=100, b=80),
    annotations=[dict(text="<b>$100M</b><br>Total Budget", x=0.42, y=0.5, font=dict(size=24), showarrow=False)],
)

# Save as PNG (4800 x 2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html("plot.html", include_plotlyjs="cdn")
