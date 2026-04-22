""" pyplots.ai
sunburst-basic: Basic Sunburst Chart
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-23
"""

import plotly.graph_objects as go


# Data - Company budget breakdown by department, team, and project (in $ millions)
# Structure: Company -> Departments -> Teams
labels = [
    # Level 1 - Root (innermost)
    "Company Budget",
    # Level 2 - Departments
    "Engineering",
    "Sales",
    "Marketing",
    "Operations",
    # Level 3 - Teams (outer ring)
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
    "",  # Company has no parent
    # Departments report to Company
    "Company Budget",
    "Company Budget",
    "Company Budget",
    "Company Budget",
    # Teams report to their departments
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

# Values in millions - using branchvalues="total" so parent values equal sum of children
values = [
    48,  # Company total (sum of all departments)
    18,  # Engineering total
    15,  # Sales total
    7,  # Marketing total
    8,  # Operations total
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

# Colors - Python Blue and Yellow as primary, variations for hierarchy
colors = [
    "#306998",  # Company - Python Blue
    # Departments
    "#306998",  # Engineering - Python Blue
    "#FFD43B",  # Sales - Python Yellow
    "#4B8BBE",  # Marketing - Light Blue
    "#FFE873",  # Operations - Light Yellow
    # Engineering teams (blue variations)
    "#1e4f7a",
    "#306998",
    "#4B8BBE",
    # Sales teams (yellow variations)
    "#e6be00",
    "#FFD43B",
    # Marketing teams (blue variations)
    "#5a9fd4",
    "#7ab8e6",
    # Operations teams (yellow variations)
    "#fff3b8",
    "#FFE873",
]

# Create sunburst chart
fig = go.Figure(
    go.Sunburst(
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        textfont=dict(size=22),
        insidetextorientation="radial",
        hovertemplate="<b>%{label}</b><br>Budget: $%{value}M<extra></extra>",
    )
)

# Update layout for 4800x2700 px canvas
fig.update_layout(
    title=dict(text="sunburst-basic · plotly · pyplots.ai", font=dict(size=36), x=0.5, xanchor="center"),
    template="plotly_white",
    margin=dict(t=120, l=40, r=40, b=40),
)

# Save as PNG (4800x2700 px)
fig.write_image("plot.png", width=1600, height=900, scale=3)

# Save as HTML for interactivity
fig.write_html("plot.html", include_plotlyjs="cdn")
