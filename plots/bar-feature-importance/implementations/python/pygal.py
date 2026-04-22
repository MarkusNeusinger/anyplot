""" pyplots.ai
bar-feature-importance: Feature Importance Bar Chart
Library: pygal 3.1.0 | Python 3.13.11
Quality: 92/100 | Created: 2025-12-26
"""

import pygal
from pygal.style import Style


# Data - Feature importances from a RandomForest classifier (house price prediction)
features = [
    "OverallQual",
    "GrLivArea",
    "TotalBsmtSF",
    "GarageCars",
    "YearBuilt",
    "FullBath",
    "TotRmsAbvGrd",
    "Fireplaces",
    "BsmtQual",
    "LotArea",
    "GarageArea",
    "YearRemodAdd",
    "KitchenQual",
    "Neighborhood",
    "ExterQual",
]
importances = [0.245, 0.182, 0.098, 0.087, 0.076, 0.054, 0.048, 0.042, 0.038, 0.035, 0.031, 0.024, 0.019, 0.012, 0.009]

# Sort by importance (descending) - pygal renders bottom to top, so reverse for highest at top
sorted_pairs = sorted(zip(features, importances, strict=True), key=lambda x: x[1], reverse=False)
sorted_features = [p[0] for p in sorted_pairs]
sorted_importances = [p[1] for p in sorted_pairs]

# Generate colors from light blue to Python Blue based on importance
min_imp = min(sorted_importances)
max_imp = max(sorted_importances)


def importance_to_color(value):
    """Map importance to color gradient: light blue -> Python Blue (#306998)"""
    if max_imp == min_imp:
        ratio = 1
    else:
        ratio = (value - min_imp) / (max_imp - min_imp)
    # Interpolate from light blue (180, 210, 240) to Python Blue (48, 105, 152)
    r = int(180 - ratio * (180 - 48))
    g = int(210 - ratio * (210 - 105))
    b = int(240 - ratio * (240 - 152))
    return f"#{r:02x}{g:02x}{b:02x}"


# Custom style for large canvas (4800 x 2700 px)
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#666666",
    colors=("#306998",),
    font_family="sans-serif",
    title_font_size=72,
    label_font_size=42,
    major_label_font_size=38,
    legend_font_size=40,
    value_font_size=36,
    value_colors=("#333333",),
    stroke_width=0,
)

# Create horizontal bar chart
chart = pygal.HorizontalBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="bar-feature-importance · pygal · pyplots.ai",
    x_title="Importance Score",
    show_legend=False,
    show_y_guides=False,
    show_x_guides=True,
    print_values=True,
    print_values_position="top",
    value_formatter=lambda x: f"{x:.3f}",
    margin=60,
    spacing=15,
    truncate_label=-1,
    x_label_rotation=0,
)

# Set feature names as y-axis labels (x_labels become y-axis in horizontal chart)
chart.x_labels = sorted_features

# Add data with individual colors per bar
bar_data = [{"value": imp, "color": importance_to_color(imp)} for imp in sorted_importances]
chart.add("Importance", bar_data)

# Save outputs
chart.render_to_file("plot.html")
chart.render_to_png("plot.png")
