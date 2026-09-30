""" anyplot.ai
bubble-basic: Basic Bubble Chart
Library: bokeh 3.10.0 | Python 3.13.15
Quality: 89/100 | Created: 2026-09-30
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, Label, Range1d
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — first series is always brand green
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Data — City metrics: population density vs median income, bubble = green space per capita
# Green space inversely correlated with density (denser cities have less green space)
np.random.seed(42)
n_cities = 55

population_density = np.random.uniform(500, 12000, n_cities)  # people per km²
median_income = 30 + population_density / 400 + np.random.normal(0, 4, n_cities)  # thousands USD
density_norm = (population_density - population_density.min()) / (population_density.max() - population_density.min())
green_space = 100 - density_norm * 90 + np.random.normal(0, 5, n_cities)
green_space = np.clip(green_space, 10, 100)  # m² per capita

# Area-proportional bubble sizes: size² ∝ data value, so size ∝ sqrt(data)
size_min, size_max = 16, 80
green_norm = (green_space - green_space.min()) / (green_space.max() - green_space.min())
bubble_size = np.sqrt(size_min**2 + (size_max**2 - size_min**2) * green_norm)

source = ColumnDataSource(
    data={
        "density": population_density,
        "income": median_income,
        "size": bubble_size,
        "density_display": np.round(population_density).astype(int),
        "income_display": np.round(median_income, 1),
        "green_display": np.round(green_space, 1),
    }
)

# Modest, symmetric axis padding — the size legend below lives inside the
# naturally sparse bottom-right corner (high density + low income is rare
# given the positive density-income correlation), so no extra headroom needs
# to be reserved just to make room for it.
x_pad = (population_density.max() - population_density.min()) * 0.07
y_pad = (median_income.max() - median_income.min()) * 0.07
x_start = population_density.min() - x_pad * 1.3
x_end = population_density.max() + x_pad * 1.3
y_start = median_income.min() - y_pad
y_end = median_income.max() + y_pad * 2.2

x_range = x_end - x_start
y_range = y_end - y_start

# Plot
title = "bubble-basic · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label="Population Density (people/km²)",
    y_axis_label="Median Income (thousands USD)",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)
p.x_range = Range1d(start=x_start, end=x_end)
p.y_range = Range1d(start=y_start, end=y_end)

main_renderer = p.scatter(
    x="density",
    y="income",
    size="size",
    source=source,
    fill_color=BRAND,
    fill_alpha=0.65,
    line_color=PAGE_BG,
    line_width=2,
    # Bokeh-specific hover_* vectorized props auto-build a hover glyph: the
    # bubble under the cursor snaps to full opacity with an ink outline, no
    # custom JS required.
    hover_fill_alpha=1.0,
    hover_line_color=INK,
    hover_line_width=3,
)

# Hover tool — scoped to the main data renderer only (skip the legend swatches)
hover = HoverTool(
    renderers=[main_renderer],
    tooltips=[
        ("Density", "@density_display{,} people/km²"),
        ("Income", "$@income_display{0.0}k"),
        ("Green Space", "@green_display m²/capita"),
    ],
    mode="mouse",
)
p.add_tools(hover)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.outline_line_alpha = 0

p.title.text_font_size = "50pt"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = None
p.yaxis.axis_line_color = None
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.12
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.12

# Size legend — anchored in the bottom-right corner, which the positive
# density-income correlation leaves naturally sparse (high density rarely
# pairs with low income), reclaiming space instead of padding the canvas.
# Reference bubbles use the same fill, outline and translucency as the data
# marks so they read as miniatures of the real thing.
legend_cx = x_end - x_range * 0.20
legend_top = y_start + y_range * 0.34
y_step = y_range * 0.07

ref_green = [green_space.min(), (green_space.min() + green_space.max()) / 2, green_space.max()]
ref_norm = [(v - green_space.min()) / (green_space.max() - green_space.min()) for v in ref_green]
ref_sizes = [np.sqrt(size_min**2 + (size_max**2 - size_min**2) * n) for n in ref_norm]
ref_labels = [f"{v:.0f} m²/capita" for v in ref_green]

legend_box = BoxAnnotation(
    left=legend_cx - x_range * 0.17,
    right=legend_cx + x_range * 0.17,
    top=legend_top + y_range * 0.01,
    bottom=legend_top - y_step * 3.8,
    fill_color=ELEVATED_BG,
    fill_alpha=0.9,
    line_color=INK_SOFT,
    line_alpha=0.4,
    level="underlay",
)
p.add_layout(legend_box)

p.add_layout(
    Label(
        x=legend_cx,
        y=legend_top - y_range * 0.01,
        text="Green Space",
        text_font_size="38pt",
        text_font_style="bold",
        text_color=INK,
        text_align="center",
    )
)

for i, (sz, lbl) in enumerate(zip(ref_sizes, ref_labels, strict=True)):
    ly = legend_top - y_step * (i + 0.85)
    ref_src = ColumnDataSource(data={"x": [legend_cx - x_range * 0.04], "y": [ly], "size": [sz]})
    p.scatter(
        x="x", y="y", size="size", source=ref_src, fill_color=BRAND, fill_alpha=0.65, line_color=PAGE_BG, line_width=2
    )
    p.add_layout(
        Label(
            x=legend_cx + x_range * 0.01,
            y=ly,
            text=lbl,
            text_font_size="34pt",
            text_baseline="middle",
            text_color=INK_SOFT,
        )
    )

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Save PNG via headless Chrome — pin the viewport exactly via CDP, since
# --window-size sets the OUTER window and still reserves a phantom title-bar
# height even headless, which would shrink the screenshot below H.
W, H = 3200, 1800
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
