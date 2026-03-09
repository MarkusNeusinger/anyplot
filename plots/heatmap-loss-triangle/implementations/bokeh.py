""" pyplots.ai
heatmap-loss-triangle: Actuarial Loss Development Triangle
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 83/100 | Created: 2026-03-09
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import BasicTicker, ColorBar, ColumnDataSource, LinearColorMapper, Title
from bokeh.plotting import figure
from bokeh.resources import Resources
from bokeh.transform import transform


# Data: Cumulative paid claims triangle (10 accident years x 10 development periods)
np.random.seed(42)

accident_years = list(range(2015, 2025))
dev_periods = list(range(1, 11))

# Generate realistic cumulative claims data using chain-ladder pattern
# Base initial claims by accident year (in thousands)
initial_claims = np.array([4200, 4500, 4800, 5100, 5400, 5700, 6000, 6300, 6600, 7000])
initial_claims = initial_claims + np.random.normal(0, 200, 10)

# Typical age-to-age development factors (diminishing over time)
dev_factors = np.array([2.50, 1.45, 1.22, 1.12, 1.07, 1.04, 1.025, 1.015, 1.008])

# Build the full 10x10 cumulative triangle
full_triangle = np.zeros((10, 10))
for i in range(10):
    full_triangle[i, 0] = initial_claims[i]
    for j in range(1, 10):
        noise = np.random.normal(1.0, 0.02)
        full_triangle[i, j] = full_triangle[i, j - 1] * dev_factors[j - 1] * noise

# Determine actual vs projected: actual values are where row + col < 10
is_actual = np.zeros((10, 10), dtype=bool)
for i in range(10):
    for j in range(10):
        if i + j < 10:
            is_actual[i, j] = True

# Prepare data for bokeh heatmap
x_coords = []
y_coords = []
values = []
text_values = []
text_colors = []
projected_flags = []
cell_alphas = []

max_val = full_triangle.max()
min_val = full_triangle.min()

for i in range(10):
    for j in range(10):
        x_coords.append(str(dev_periods[j]))
        y_coords.append(str(accident_years[i]))
        val = full_triangle[i, j]
        values.append(val)
        text_values.append(f"{val:,.0f}")
        projected_flags.append("Projected" if not is_actual[i, j] else "Actual")
        # White text for darker cells, dark text for lighter cells
        norm_val = (val - min_val) / (max_val - min_val)
        text_colors.append("white" if norm_val > 0.55 else "#1a1a2e")
        cell_alphas.append(1.0 if is_actual[i, j] else 0.65)

source = ColumnDataSource(
    data={
        "x": x_coords,
        "y": y_coords,
        "value": values,
        "text": text_values,
        "text_color": text_colors,
        "alpha": cell_alphas,
        "status": projected_flags,
    }
)

# Color mapper: sequential blue palette for magnitude
colors = ["#E8F0FE", "#C5DAEF", "#9DC3E0", "#6AAED0", "#4292C6", "#2171B5", "#08519C", "#083D7F", "#062D60"]
mapper = LinearColorMapper(palette=colors, low=min_val, high=max_val)

# Create figure
dev_labels = [str(d) for d in dev_periods]
year_labels = [str(y) for y in accident_years]

p = figure(
    width=4800,
    height=2700,
    x_range=dev_labels,
    y_range=list(reversed(year_labels)),
    title="Actuarial Loss Development Triangle · heatmap-loss-triangle · bokeh · pyplots.ai",
    x_axis_location="above",
    toolbar_location=None,
)

# Heatmap rectangles
p.rect(
    x="x",
    y="y",
    width=1,
    height=1,
    source=source,
    fill_color=transform("value", mapper),
    fill_alpha="alpha",
    line_color="white",
    line_width=3,
)

# Cell annotations
p.text(
    x="x",
    y="y",
    text="text",
    source=source,
    text_align="center",
    text_baseline="middle",
    text_font_size="14pt",
    text_color="text_color",
)

# Development factors row: display below the heatmap as subtitle info
factor_text = "  ".join([f"F{j + 1}-{j + 2}: {dev_factors[j]:.3f}" for j in range(len(dev_factors))])

# Style
p.title.text_font_size = "28pt"
p.title.align = "center"
p.xaxis.axis_label = "Development Period (Years)"
p.yaxis.axis_label = "Accident Year"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.axis.axis_line_color = None
p.axis.major_tick_line_color = None
p.grid.grid_line_color = None

# Add subtitle with development factors
p.add_layout(
    Title(
        text=f"Age-to-Age Development Factors:  {factor_text}",
        text_font_size="14pt",
        text_color="#555555",
        align="center",
    ),
    "below",
)

# Add subtitle for legend distinction
p.add_layout(
    Title(
        text="Full opacity = Actual (observed)  |  Reduced opacity = Projected (estimated IBNR)",
        text_font_size="15pt",
        text_color="#666666",
        align="center",
    ),
    "below",
)

# Colorbar
color_bar = ColorBar(
    color_mapper=mapper,
    ticker=BasicTicker(desired_num_ticks=8),
    label_standoff=12,
    major_label_text_font_size="16pt",
    title="Cumulative Claims ($K)",
    title_text_font_size="18pt",
    width=40,
    location=(0, 0),
)
p.add_layout(color_bar, "right")

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=Resources(mode="cdn"), title="Heatmap Loss Triangle")
