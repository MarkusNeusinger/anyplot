""" pyplots.ai
line-yield-curve: Yield Curve (Interest Rate Term Structure)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-14
"""

import pygal
from pygal.style import Style


# Data - U.S. Treasury yield curves on three dates
maturities = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
maturity_years = [0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30]

# Normal upward-sloping curve (Jan 2021)
yields_normal = [0.04, 0.06, 0.07, 0.10, 0.13, 0.24, 0.44, 0.74, 1.09, 1.65, 1.87]

# Flat curve (Dec 2018)
yields_flat = [2.36, 2.40, 2.56, 2.63, 2.49, 2.46, 2.51, 2.59, 2.69, 2.87, 3.02]

# Inverted curve (Mar 2023)
yields_inverted = [4.73, 4.90, 5.09, 4.95, 4.60, 4.27, 3.85, 3.76, 3.58, 3.89, 3.70]

# Style — 4th color is a soft red fill for inversion zone
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#e0e0e0",
    colors=("#306998", "#E6A817", "#C0392B", "#555555"),
    title_font_size=72,
    label_font_size=44,
    major_label_font_size=40,
    legend_font_size=44,
    value_font_size=32,
    tooltip_font_size=28,
    stroke_width=6,
    opacity=0.9,
    opacity_hover=1.0,
)

# Create XY chart for proper maturity spacing
chart = pygal.XY(
    width=4800,
    height=2700,
    title="U.S. Treasury Yield Curves · line-yield-curve · pygal · pyplots.ai",
    x_title="Maturity (Years)",
    y_title="Yield (%)",
    style=custom_style,
    show_dots=True,
    dots_size=10,
    stroke_style={"width": 5},
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_at_bottom_columns=4,
    legend_box_size=36,
    truncate_legend=-1,
    x_value_formatter=lambda x: f"{x:.0f}Y" if x >= 1 else f"{x * 12:.0f}M",
    y_value_formatter=lambda y: f"{y:.2f}%",
    margin=80,
    margin_top=150,
    margin_bottom=150,
    xrange=(0, 31),
    range=(0, 5.5),
    x_labels=[0.083, 0.25, 0.5, 1, 2, 3, 5, 7, 10, 20, 30],
    x_labels_major=[0.083, 1, 2, 5, 10, 20, 30],
    show_minor_x_labels=False,
)

# Add curves
normal_points = list(zip(maturity_years, yields_normal, strict=False))
flat_points = list(zip(maturity_years, yields_flat, strict=False))
inverted_points = list(zip(maturity_years, yields_inverted, strict=False))

chart.add("Jan 2021 (Normal)", normal_points)
chart.add("Dec 2018 (Flat)", flat_points)
chart.add("Mar 2023 (Inverted)", inverted_points)

# Highlight inversion zone: 2Y-10Y spread on the inverted curve
# The 2Y yield (4.60%) exceeds the 10Y yield (3.58%) by 102 basis points
# Show this as a dashed connector with enlarged markers at the endpoints
spread_2y10y = 4.60 - 3.58  # +1.02% = inverted
inversion_zone = [(2, 4.60), (10, 3.58)]
chart.add(
    f"⬍ 2Y–10Y Inversion (−{spread_2y10y * 100:.0f} bps)",
    inversion_zone,
    stroke_dasharray="15,10",
    dots_size=16,
    show_dots=True,
)

# Save
chart.render_to_png("plot.png")

with open("plot.html", "w") as f:
    f.write(f"""<!DOCTYPE html>
<html>
<head>
    <title>Yield Curve - pygal</title>
    <style>
        body {{ margin: 0; padding: 20px; background: white; }}
        svg {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    {chart.render(is_unicode=True)}
</body>
</html>""")
