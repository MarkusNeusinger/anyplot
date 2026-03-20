"""pyplots.ai
bifurcation-basic: Bifurcation Diagram for Dynamical Systems
Library: bokeh | Python 3.13
Quality: pending | Created: 2026-03-20
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColumnDataSource, Label
from bokeh.plotting import figure
from bokeh.resources import Resources


# Data - Logistic map: x(n+1) = r * x(n) * (1 - x(n))
r_min, r_max = 2.5, 4.0
n_r = 2000
n_transient = 200
n_keep = 100

r_values = np.linspace(r_min, r_max, n_r)
all_r = np.repeat(r_values, n_keep)
all_x = np.empty_like(all_r)

idx = 0
for r in r_values:
    x = 0.5
    for _ in range(n_transient):
        x = r * x * (1.0 - x)
    for _ in range(n_keep):
        x = r * x * (1.0 - x)
        all_x[idx] = x
        idx += 1

source = ColumnDataSource(data={"r": all_r, "x": all_x})

# Plot
p = figure(
    width=4800,
    height=2700,
    title="bifurcation-basic · bokeh · pyplots.ai",
    x_axis_label="Growth Rate (r)",
    y_axis_label="Steady-State Population (x)",
    toolbar_location=None,
    x_range=(r_min - 0.02, r_max + 0.02),
    y_range=(-0.05, 1.05),
)

p.scatter(x="r", y="x", source=source, size=1, color="#306998", alpha=0.12, line_color=None)

# Key bifurcation point annotations
bifurcation_points = [(3.0, 0.68, "r ≈ 3.0"), (3.449, 0.86, "r ≈ 3.449"), (3.5699, 0.10, "r ≈ 3.57 (chaos)")]

for r_bif, y_pos, label_text in bifurcation_points:
    label = Label(
        x=r_bif,
        y=y_pos,
        text=label_text,
        text_font_size="30pt",
        text_color="#AA3939",
        text_alpha=0.75,
        text_align="center",
        x_offset=5,
    )
    p.add_layout(label)

# Style
p.title.text_font_size = "72pt"
p.title.text_color = "#333333"

p.xaxis.axis_label_text_font_size = "48pt"
p.yaxis.axis_label_text_font_size = "48pt"
p.xaxis.major_label_text_font_size = "36pt"
p.yaxis.major_label_text_font_size = "36pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.grid.grid_line_alpha = 0.15
p.grid.grid_line_width = 2
p.grid.grid_line_color = "#888888"

p.background_fill_color = "#FAFAFA"
p.border_fill_color = "white"
p.outline_line_color = None

p.xaxis.ticker.desired_num_ticks = 12
p.yaxis.ticker.desired_num_ticks = 8

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=Resources(mode="cdn"), title="Bifurcation Diagram")
