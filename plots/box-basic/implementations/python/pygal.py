""" pyplots.ai
box-basic: Basic Box Plot
Library: pygal 3.1.0 | Python 3.14
Quality: 90/100 | Created: 2025-12-23
"""

import re

import cairosvg
import numpy as np
import pygal
from pygal.style import Style


# Data - Generate salary distributions for different departments
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "Operations", "HR"]
data = {
    "Engineering": np.random.normal(85000, 15000, 100),
    "Marketing": np.random.normal(72000, 12000, 100),
    "Sales": np.random.normal(68000, 18000, 100),
    "Operations": np.random.normal(62000, 10000, 100),
    "HR": np.random.normal(58000, 8000, 100),
}

# Add outliers to demonstrate box plot features
data["Engineering"] = np.append(data["Engineering"], [130000, 135000, 40000])
data["Sales"] = np.append(data["Sales"], [120000, 25000])

# Compute medians for annotation storytelling
medians = {cat: float(np.median(data[cat])) for cat in categories}
highest_dept = max(medians, key=medians.get)
lowest_dept = min(medians, key=medians.get)

# Custom style for 4800x2700 canvas — strong, vivid colors
custom_style = Style(
    background="white",
    plot_background="#FAFAFA",
    foreground="#333333",
    foreground_strong="#222222",
    foreground_subtle="#E0E0E0",
    colors=("#306998", "#E69F00", "#009E73", "#D55E00", "#7B68EE"),
    title_font_size=72,
    label_font_size=48,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    opacity=1.0,
    opacity_hover=1.0,
)

# Create box chart — set y range to focus on actual data, not starting at 0
chart = pygal.Box(
    width=4800,
    height=2700,
    style=custom_style,
    title="box-basic · pygal · pyplots.ai",
    x_title="Department",
    y_title="Salary ($)",
    show_legend=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=5,
    legend_box_size=36,
    truncate_legend=-1,
    truncate_label=-1,
    show_y_guides=True,
    show_x_guides=False,
    margin=80,
    spacing=40,
    box_mode="tukey",
    range=(5000, 145000),
    y_labels=[20000, 40000, 60000, 80000, 100000, 120000, 140000],
)

# Add data for each category
for category in categories:
    chart.add(category, data[category].tolist())

# Render SVG, then post-process for visual improvements
svg_string = chart.render().decode("utf-8")

# Fix 1: Increase box fill opacity from 0.2 to 0.7 (pygal hardcodes subtle-fill)
svg_string = svg_string.replace(".subtle-fill{fill-opacity:.2}", ".subtle-fill{fill-opacity:.7}")

# Fix 2: Enlarge outlier dots (pygal hardcodes r=3 for box outliers)
svg_string = re.sub(r'(<circle[^>]*) r="3" (class="subtle-fill)', r'\1 r="10" \2', svg_string)

# Fix 3: Add storytelling annotation as subtitle
annotation_svg = (
    f'<text x="2400" y="200" text-anchor="middle" '
    f'font-size="38" fill="#555555" font-family="sans-serif" font-style="italic">'
    f"Highest median: {highest_dept} (${medians[highest_dept]:,.0f})"
    f"  \u00b7  Lowest median: {lowest_dept} (${medians[lowest_dept]:,.0f})"
    f"  \u00b7  Gap: ${medians[highest_dept] - medians[lowest_dept]:,.0f}"
    f"</text>"
)
svg_string = svg_string.replace("</svg>", f"{annotation_svg}</svg>")

# Save outputs
with open("plot.html", "w") as f:
    f.write(svg_string)

cairosvg.svg2png(bytestring=svg_string.encode("utf-8"), write_to="plot.png")
