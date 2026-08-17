"""anyplot.ai
radar-multi: Multi-Series Radar Chart
Library: bokeh 3.9.2 | Python 3.13.12
Quality: pending | Updated: 2026-08-17
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Legend, Title
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Product comparison across 6 attributes
categories = ["Performance", "Reliability", "Features", "Support", "Price Value", "Ease of Use"]
n_categories = len(categories)

# Three products to compare
products = {
    "Product A": [85, 90, 75, 80, 70, 88],
    "Product B": [70, 75, 95, 85, 80, 72],
    "Product C": [92, 65, 80, 70, 95, 78],
}
overall_leader = max(products, key=lambda name: sum(products[name]) / n_categories)
overall_leader_avg = sum(products[overall_leader]) / n_categories

# Calculate angles for each axis (starting from top, going clockwise)
angles = np.linspace(0, 2 * np.pi, n_categories, endpoint=False)
angles = angles + np.pi / 2

# Create figure with square aspect for radar chart
p = figure(
    width=2400,
    height=2400,
    title="radar-multi · bokeh · anyplot.ai",
    x_range=(-145, 145),
    y_range=(-145, 145),
    tools=[],
    toolbar_location=None,
)

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Remove axes and grid
p.axis.visible = False
p.grid.visible = False

# Subtle alternating radial bands (target-board depth cue) behind the grid
grid_values = [20, 40, 60, 80, 100]
band_edges = [0, *grid_values]
theta_full = np.linspace(0, 2 * np.pi, 200)
for band_idx in range(len(grid_values)):
    if band_idx % 2 == 0:
        continue  # leave every other band transparent to show PAGE_BG
    inner, outer = band_edges[band_idx], band_edges[band_idx + 1]
    p.annular_wedge(
        x=0,
        y=0,
        inner_radius=inner,
        outer_radius=outer,
        start_angle=0,
        end_angle=2 * np.pi,
        fill_color=ELEVATED_BG,
        fill_alpha=0.6,
        line_color=None,
    )

# Draw circular gridlines at 20, 40, 60, 80, 100
for gv in grid_values:
    x_grid = gv * np.cos(theta_full)
    y_grid = gv * np.sin(theta_full)
    p.line(x_grid, y_grid, line_color=INK_SOFT, line_width=2, line_alpha=0.4)

# Draw radial spokes from center to each axis (dotted for a lighter touch)
for angle in angles:
    x_line = [0, 105 * np.cos(angle)]
    y_line = [0, 105 * np.sin(angle)]
    p.line(x_line, y_line, line_color=INK_SOFT, line_width=2, line_alpha=0.3, line_dash="dotted")

# Add axis labels at the outer edge
label_radius = 125
label_x = [label_radius * np.cos(a) for a in angles]
label_y = [label_radius * np.sin(a) for a in angles]
label_source = ColumnDataSource(data={"x": label_x, "y": label_y, "text": categories})
labels = LabelSet(
    x="x",
    y="y",
    text="text",
    source=label_source,
    text_font_size="42pt",
    text_align="center",
    text_baseline="middle",
    text_color=INK,
    text_font_style="bold",
)
p.add_layout(labels)

# Add grid value labels on one axis (shifted for visibility)
for gv in grid_values:
    p.text(
        x=[gv * np.cos(angles[0]) + 8],
        y=[gv * np.sin(angles[0]) + 8],
        text=[str(gv)],
        text_font_size="28pt",
        text_color=INK_SOFT,
        text_alpha=0.9,
    )

# Per-axis leader: the product with the highest value on each category gets
# a slightly larger vertex marker, turning the chart into a quick "who wins
# on which dimension" read instead of a flat overlay of three polygons.
leader_per_axis = [max(products, key=lambda name: products[name][i]) for i in range(n_categories)]

# Plot each product series
legend_items = []
vertex_renderers = []
for idx, (product_name, values) in enumerate(products.items()):
    # Convert values to x, y coordinates
    x_vals = [v * np.cos(a) for v, a in zip(values, angles, strict=True)]
    y_vals = [v * np.sin(a) for v, a in zip(values, angles, strict=True)]

    # Close the polygon
    x_closed = [*x_vals, x_vals[0]]
    y_closed = [*y_vals, y_vals[0]]

    # Draw filled polygon
    fill_renderer = p.patch(
        x_closed,
        y_closed,
        fill_color=IMPRINT[idx],
        fill_alpha=0.25,
        line_color=IMPRINT[idx],
        line_width=5 if product_name == overall_leader else 4,
        line_alpha=0.9,
    )

    # Draw vertex markers via a ColumnDataSource so hover can surface the
    # exact category/value on inspection — leans into bokeh's HTML output
    # rather than treating it as a throwaway artifact.
    vertex_sizes = [30 if leader_per_axis[i] == product_name else 20 for i in range(n_categories)]
    vertex_source = ColumnDataSource(
        data={
            "x": x_vals,
            "y": y_vals,
            "category": categories,
            "value": values,
            "product": [product_name] * n_categories,
            "size": vertex_sizes,
        }
    )
    vertex_renderer = p.scatter(
        x="x",
        y="y",
        source=vertex_source,
        size="size",
        fill_color=IMPRINT[idx],
        line_color=PAGE_BG,
        line_width=3,
        alpha=0.9,
    )
    vertex_renderers.append(vertex_renderer)

    legend_items.append((product_name, [fill_renderer]))

# Hover reveals the per-axis value driving each vertex — a distinctive
# bokeh capability the static PNG can't show, but the saved HTML can.
hover = HoverTool(
    renderers=vertex_renderers, tooltips=[("Product", "@product"), ("Category", "@category"), ("Value", "@value")]
)
p.add_tools(hover)

# Add legend
legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="34pt",
    glyph_height=48,
    glyph_width=48,
    spacing=22,
    padding=28,
    background_fill_color=PAGE_BG,
    background_fill_alpha=0.85,
    border_line_color=INK_SOFT,
    label_text_color=INK_SOFT,
)
p.add_layout(legend, "right")

# Style title + a data-driven subtitle calling out the overall leader
p.title.text_font_size = "50pt"
p.title.align = "center"
p.title.text_color = INK
subtitle = Title(
    text=f"Overall leader: {overall_leader} ({overall_leader_avg:.0f} avg score)",
    text_font_size="26pt",
    text_font_style="italic",
    text_color=INK_SOFT,
    align="center",
)
p.add_layout(subtitle, "above")

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 2400, 2400
opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H}",
    "--hide-scrollbars",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
