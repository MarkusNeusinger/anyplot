""" pyplots.ai
treemap-basic: Basic Treemap
Library: plotly 6.5.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-24
"""

import plotly.graph_objects as go


# Data - Budget allocation by department and project (in thousands)
categories = [
    "Engineering",
    "Engineering",
    "Engineering",
    "Engineering",
    "Marketing",
    "Marketing",
    "Marketing",
    "Sales",
    "Sales",
    "Sales",
    "Operations",
    "Operations",
    "HR",
    "HR",
]
subcategories = [
    "Infrastructure",
    "Product Dev",
    "QA",
    "Research",
    "Digital Ads",
    "Content",
    "Events",
    "Direct Sales",
    "Partnerships",
    "Support",
    "Logistics",
    "Facilities",
    "Recruiting",
    "Training",
]
values = [450, 380, 120, 200, 280, 150, 90, 320, 180, 140, 160, 120, 110, 80]

# Build parent-child hierarchy for treemap
unique_cats_ordered = ["Engineering", "Marketing", "Sales", "Operations", "HR"]

# Calculate category totals
category_totals = {}
for cat, val in zip(categories, values, strict=True):
    category_totals[cat] = category_totals.get(cat, 0) + val

# Construct labels, parents, and values for treemap
labels = ["Budget"] + unique_cats_ordered + subcategories
parents = [""] + ["Budget"] * len(unique_cats_ordered) + categories
treemap_values = [sum(values)]  # Root total
treemap_values += [category_totals[cat] for cat in unique_cats_ordered]
treemap_values += values

# Colors for main categories (Python colors + colorblind-safe)
color_map = {
    "Budget": "#FFFFFF",
    "Engineering": "#306998",
    "Marketing": "#FFD43B",
    "Sales": "#2CA02C",
    "Operations": "#9467BD",
    "HR": "#E377C2",
}

# Assign colors based on category hierarchy
colors = []
for i, label in enumerate(labels):
    if label in color_map:
        colors.append(color_map[label])
    else:
        # Subcategory - use parent category color
        parent = parents[i]
        colors.append(color_map.get(parent, "#306998"))

# Create treemap
fig = go.Figure(
    go.Treemap(
        labels=labels,
        parents=parents,
        values=treemap_values,
        marker={"colors": colors, "line": {"width": 2, "color": "white"}},
        textfont={"size": 24},
        textinfo="label+value",
        hovertemplate="<b>%{label}</b><br>Value: $%{value}K<br>Percent of parent: %{percentParent:.1%}<extra></extra>",
        branchvalues="total",
    )
)

# Layout
fig.update_layout(
    title={"text": "treemap-basic · plotly · pyplots.ai", "font": {"size": 32}, "x": 0.5, "xanchor": "center"},
    margin={"t": 80, "l": 20, "r": 20, "b": 20},
    template="plotly_white",
)

# Save
fig.write_image("plot.png", width=1600, height=900, scale=3)
fig.write_html("plot.html", include_plotlyjs="cdn")
