""" anyplot.ai
donut-nested: Nested Donut Chart
Library: plotly 6.7.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-08
"""

import os

import plotly.graph_objects as go


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito categorical palette (canonical order, positions 1-4 for inner ring)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]


def lighten_hex(hex_color, factor=0.4):
    """Create a lighter shade of a hex color by blending with white."""
    hex_color = hex_color.lstrip("#")
    r, g, b = tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
    r = int(r + (255 - r) * factor)
    g = int(g + (255 - g) * factor)
    b = int(b + (255 - b) * factor)
    return f"#{r:02x}{g:02x}{b:02x}"


# Data - Company budget allocation by department and expense category
departments = ["Engineering", "Marketing", "Sales", "Operations"]
dept_values = [45, 25, 18, 12]  # Millions
dept_colors = IMPRINT

# Child categories (outer ring) with consistent color families (lighter shades)
categories = [
    # Engineering
    "Salaries",
    "Infrastructure",
    "R&D",
    "Tools",
    # Marketing
    "Advertising",
    "Events",
    "Content",
    # Sales
    "Commissions",
    "Travel",
    "Training",
    # Operations
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

# Generate child colors as lighter shades of parent colors
cat_colors = []
child_counts = [4, 3, 3, 2]  # Children per department
for dept_idx, count in enumerate(child_counts):
    base_color = dept_colors[dept_idx]
    for i in range(count):
        # Create progressively lighter shades
        shade = lighten_hex(base_color, factor=0.15 + i * 0.15)
        cat_colors.append(shade)

# Create figure with two pie traces (inner and outer rings)
fig = go.Figure()

# Inner ring - Departments (parent categories) with both name and percentage
fig.add_trace(
    go.Pie(
        values=dept_values,
        labels=departments,
        hole=0.30,
        domain={"x": [0.12, 0.72], "y": [0.05, 0.95]},
        marker={"colors": dept_colors, "line": {"color": PAGE_BG, "width": 3}},
        textinfo="label+percent",
        textposition="inside",
        textfont={"size": 18, "color": "white"},
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
        marker={"colors": cat_colors, "line": {"color": PAGE_BG, "width": 2}},
        textinfo="label",
        textposition="outside",
        textfont={"size": 15, "color": INK},
        hovertemplate="<b>%{label}</b><br>$%{value}M<br>%{percent}<extra></extra>",
        name="Categories",
        sort=False,
    )
)

# Layout with theme-adaptive colors
fig.update_layout(
    title={
        "text": "Company Budget Allocation · donut-nested · plotly · pyplots.ai",
        "font": {"size": 28, "color": INK},
        "x": 0.5,
        "xanchor": "center",
    },
    showlegend=True,
    legend={
        "font": {"size": 16, "color": INK_SOFT},
        "orientation": "v",
        "x": 1.02,
        "y": 0.5,
        "yanchor": "middle",
        "bgcolor": ELEVATED_BG,
        "bordercolor": INK_SOFT,
        "borderwidth": 1,
    },
    paper_bgcolor=PAGE_BG,
    plot_bgcolor=PAGE_BG,
    font={"color": INK},
    margin={"l": 80, "r": 200, "t": 100, "b": 80},
    annotations=[
        {
            "text": "<b>$100M</b><br>Total Budget",
            "x": 0.42,
            "y": 0.5,
            "font": {"size": 24, "color": INK},
            "showarrow": False,
        }
    ],
)

# Save as PNG (4800 x 2700 px)
fig.write_image(f"plot-{THEME}.png", width=1600, height=900, scale=3)

# Save interactive HTML
fig.write_html(f"plot-{THEME}.html", include_plotlyjs="cdn")
