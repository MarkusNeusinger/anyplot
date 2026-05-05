""" anyplot.ai
treemap-basic: Basic Treemap
Library: plotly 6.7.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-05
"""

import os
import sys


sys.path = [p for p in sys.path if p != os.path.dirname(os.path.abspath(__file__))]
import plotly.graph_objects as go  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette for main categories
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00"]

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
treemap_values = [sum(values)]
treemap_values += [category_totals[cat] for cat in unique_cats_ordered]
treemap_values += values

# Create color map using Okabe-Ito palette
color_map = {
    "Budget": PAGE_BG,
    "Engineering": OKABE_ITO[0],
    "Marketing": OKABE_ITO[1],
    "Sales": OKABE_ITO[2],
    "Operations": OKABE_ITO[3],
    "HR": OKABE_ITO[4],
}

# Assign colors based on category hierarchy
colors = []
for i, label in enumerate(labels):
    if label in color_map:
        colors.append(color_map[label])
    else:
        parent = parents[i]
        colors.append(color_map.get(parent, OKABE_ITO[0]))

# Create treemap
fig = go.Figure(
    go.Treemap(
        labels=labels,
        parents=parents,
        values=treemap_values,
        marker={"colors": colors, "line": {"width": 2, "color": PAGE_BG}},
        textfont={"size": 22, "color": INK},
        textinfo="label+value",
        hovertemplate="<b>%{label}</b><br>Value: $%{value}K<br>Percent of parent: %{percentParent:.1%}<extra></extra>",
        branchvalues="total",
    )
)

# Layout with theme-adaptive styling
fig.update_layout(
    title={
        "text": "treemap-basic · plotly · anyplot.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    margin={"t": 80, "l": 20, "r": 20, "b": 20},
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK, "size": 18},
)

# Save
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
