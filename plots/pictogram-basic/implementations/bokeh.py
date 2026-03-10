"""pyplots.ai
pictogram-basic: Pictogram Chart (Isotype Visualization)
Library: bokeh 3.8.2 | Python 3.14.3
Created: 2026-03-10
"""

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, CustomJSTickFormatter, FixedTicker, Label, Range1d, Title
from bokeh.plotting import figure


# Data - Fruit production (thousands of tonnes)
categories = ["Apples", "Oranges", "Bananas", "Grapes", "Mangoes"]
values = [35, 22, 18, 28, 12]
icon_value = 5
colors = ["#306998", "#E8963E", "#F2C94C", "#7B68AE", "#5DA87E"]

# Sort by value descending for visual hierarchy
sorted_data = sorted(zip(categories, values, colors, strict=True), key=lambda x: x[1], reverse=True)
categories = [d[0] for d in sorted_data]
values = [d[1] for d in sorted_data]
colors = [d[2] for d in sorted_data]

# Build icon grid positions
full_x, full_y, full_c, full_alpha = [], [], [], []
bg_x, bg_y = [], []
wedge_x, wedge_y, wedge_c, wedge_end, wedge_alpha = [], [], [], [], []
n_cats = len(categories)
radius = 0.40

# Emphasis: top category full opacity, bottom fades for visual hierarchy
alphas = [1.0, 0.88, 0.88, 0.82, 0.72]

for i, (_cat, val, color) in enumerate(zip(categories, values, colors, strict=True)):
    n_full = int(val // icon_value)
    remainder = val % icon_value
    fraction = remainder / icon_value
    y = n_cats - 1 - i

    for j in range(n_full):
        full_x.append(j)
        full_y.append(y)
        full_c.append(color)
        full_alpha.append(alphas[i])

    if fraction > 0:
        bg_x.append(n_full)
        bg_y.append(y)
        wedge_x.append(n_full)
        wedge_y.append(y)
        wedge_c.append(color)
        wedge_end.append(np.pi / 2 - fraction * 2 * np.pi)
        wedge_alpha.append(alphas[i])

# Figure — landscape format for horizontal pictogram layout
max_icons = max(int(np.ceil(v / icon_value)) for v in values)
p = figure(
    width=4800,
    height=2700,
    x_range=Range1d(-0.7, max_icons + 1.2),
    y_range=Range1d(-0.85, n_cats - 0.2),
    toolbar_location=None,
    title="Fruit Production · pictogram-basic · bokeh · pyplots.ai",
)

# Subtitle with units context — centered to match title
subtitle = Title(
    text="Annual output in thousands of tonnes", text_font_size="22pt", text_color="#777777", align="center"
)
p.add_layout(subtitle, "above")

# Alternating row background bands for visual structure
for i in range(n_cats):
    if i % 2 == 0:
        band = BoxAnnotation(bottom=i - 0.48, top=i + 0.48, fill_color="#F5F5F5", fill_alpha=0.5, level="underlay")
        p.add_layout(band)

# Full icons
full_source = ColumnDataSource(data={"x": full_x, "y": full_y, "color": full_c, "alpha": full_alpha})
p.circle(
    x="x", y="y", radius=radius, source=full_source, color="color", alpha="alpha", line_color="white", line_width=3
)

# Partial icon backgrounds (gray circles)
if bg_x:
    bg_source = ColumnDataSource(data={"x": bg_x, "y": bg_y})
    p.circle(
        x="x", y="y", radius=radius, source=bg_source, color="#E0E0E0", alpha=0.35, line_color="white", line_width=3
    )

    # Partial icon fills (wedges)
    wedge_source = ColumnDataSource(
        data={"x": wedge_x, "y": wedge_y, "color": wedge_c, "end_angle": wedge_end, "alpha": wedge_alpha}
    )
    p.wedge(
        x="x",
        y="y",
        radius=radius,
        start_angle=np.pi / 2,
        end_angle="end_angle",
        direction="clock",
        source=wedge_source,
        color="color",
        alpha="alpha",
        line_color="white",
        line_width=3,
    )

# Value annotations on the right side of each row
for i, (_cat, val) in enumerate(zip(categories, values, strict=True)):
    y = n_cats - 1 - i
    n_icons = int(np.ceil(val / icon_value))
    font_size = "24pt" if i == 0 else "22pt"
    font_style = "bold" if i == 0 else "normal"
    val_label = Label(
        x=n_icons + 0.15,
        y=y,
        text=f"{val:,} k",
        text_font_size=font_size,
        text_font_style=font_style,
        text_color="#333333" if i == 0 else "#555555",
        text_baseline="middle",
        x_units="data",
        y_units="data",
    )
    p.add_layout(val_label)

# Legend annotation
legend_label = Label(
    x=0,
    y=-0.6,
    text="Each ● = 5,000 tonnes",
    text_font_size="26pt",
    text_color="#555555",
    x_units="data",
    y_units="data",
)
p.add_layout(legend_label)

# Style
p.title.text_font_size = "36pt"
p.title.align = "center"

# Y-axis: category labels
cat_labels = [categories[n_cats - 1 - i] for i in range(n_cats)]
p.yaxis.ticker = FixedTicker(ticks=list(range(n_cats)))
p.yaxis.formatter = CustomJSTickFormatter(args={"labels": cat_labels}, code="return labels[tick] || '';")
p.yaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_style = "bold"

# X-axis: hide
p.xaxis.visible = False

# Remove spines and grid
p.outline_line_color = None
p.grid.grid_line_color = None
p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.yaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None

# Background
p.background_fill_color = "#FFFFFF"
p.border_fill_color = "#FFFFFF"

# Padding
p.min_border_left = 220
p.min_border_bottom = 100
p.min_border_top = 80
p.min_border_right = 60

# Save
export_png(p, filename="plot.png")
output_file("plot.html")
save(p)
