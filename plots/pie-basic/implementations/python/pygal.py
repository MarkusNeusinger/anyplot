""" pyplots.ai
pie-basic: Basic Pie Chart
Library: pygal 3.1.0 | Python 3.14.0
Quality: 90/100 | Created: 2025-12-23
"""

import pygal
from pygal.style import Style


# Data - Global smartphone market share (2024)
categories = [("Apple", 23.3), ("Samsung", 19.4), ("Xiaomi", 14.1), ("OPPO", 8.7), ("vivo", 7.5), ("Others", 27.0)]

# Saturated, high-contrast palette — colorblind-safe (no red-green ambiguity)
palette = ("#2563EB", "#D97706", "#0D9488", "#E11D48", "#7C3AED", "#64748B")

custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#1E293B",
    foreground_strong="#0F172A",
    foreground_subtle="#94A3B8",
    colors=palette,
    title_font_size=76,
    label_font_size=48,
    major_label_font_size=48,
    value_label_font_size=44,
    legend_font_size=60,
    value_font_size=56,
    tooltip_font_size=36,
    value_colors=("#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF", "#FFFFFF"),
    stroke_opacity=1,
)

chart = pygal.Pie(
    width=3600,
    height=3600,
    style=custom_style,
    title="Smartphone Market Share · pie-basic · pygal · pyplots.ai",
    inner_radius=0,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    legend_box_size=40,
    print_values=True,
    print_labels=True,
    print_values_position="center",
    value_formatter=lambda x: f"{x:.1f}%",
    margin=60,
    margin_bottom=100,
    truncate_legend=-1,
)

# Storytelling: narrative legend names convey insight; on-slice labels add context
legend_names = {"Others": "Others (largest segment)", "Apple": "Apple (#1 brand)", "Samsung": "Samsung (#2 worldwide)"}

for company, value in categories:
    slice_css = "stroke: white; stroke-width: 5"
    slice_data = {"value": value, "style": slice_css}

    # Explode the largest slice ("Others") with a subtle fixed offset for emphasis
    if company == "Others":
        slice_data["node"] = {"transform": "translate(0, -18)"}
        slice_data["label"] = "Largest"
    elif company == "Apple":
        slice_data["label"] = "#1 brand"

    name = legend_names.get(company, company)
    chart.add(name, [slice_data])

chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
