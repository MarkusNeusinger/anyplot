"""anyplot.ai
bubble-basic: Basic Bubble Chart
Library: bokeh 3.10.0 | Python 3.13.15
Quality: 92/100 | Created: 2026-09-27
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import (
    Arrow,
    BoxAnnotation,
    ColorBar,
    ColumnDataSource,
    HoverTool,
    Label,
    LinearColorMapper,
    NormalHead,
    Range1d,
)
from bokeh.plotting import figure
from bokeh.transform import transform
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# imprint_seq colormap (single-polarity: brand green → blue)
_t = np.linspace(0, 1, 256)
_c0 = np.array([0x00, 0x9E, 0x73])
_c1 = np.array([0x44, 0x67, 0xA3])
ANYPLOT_SEQ256 = ["#{:02X}{:02X}{:02X}".format(*(_c0 + (_c1 - _c0) * t).round().astype(int)) for t in _t]

# Data — City metrics: population density vs median income, bubble = green space per capita
# Green space inversely correlated with density (denser cities have less green space)
np.random.seed(42)
n_cities = 55

population_density = np.random.uniform(500, 12000, n_cities)  # people per km²
median_income = 30 + population_density / 400 + np.random.normal(0, 4, n_cities)  # thousands USD
density_norm = (population_density - population_density.min()) / (population_density.max() - population_density.min())
green_space = 100 - density_norm * 90 + np.random.normal(0, 5, n_cities)
green_space = np.clip(green_space, 10, 100)  # m² per capita

# Transit accessibility index — a genuinely independent fourth attribute (not
# derived from density/income/green_space) so color adds new information
# instead of echoing the size encoding. Also breaks up color runs inside the
# densest cluster, since neighboring points no longer share near-identical hue.
transit_score = np.clip(np.random.normal(5.5, 2.3, n_cities), 0, 10)

# Area-proportional bubble sizes: size² ∝ data value, so size ∝ sqrt(data)
size_min, size_max = 16, 80
green_norm = (green_space - green_space.min()) / (green_space.max() - green_space.min())
bubble_size = np.sqrt(size_min**2 + (size_max**2 - size_min**2) * green_norm)

color_mapper = LinearColorMapper(palette=ANYPLOT_SEQ256, low=transit_score.min(), high=transit_score.max())

source = ColumnDataSource(
    data={
        "density": population_density,
        "income": median_income,
        "size": bubble_size,
        "transit_score": transit_score,
        "density_display": np.round(population_density).astype(int),
        "income_display": np.round(median_income, 1),
        "green_display": np.round(green_space, 1),
        "transit_display": np.round(transit_score, 1),
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
    min_border_top=130,
    min_border_right=260,
)
p.x_range = Range1d(start=x_start, end=x_end)
p.y_range = Range1d(start=y_start, end=y_end)

main_renderer = p.scatter(
    x="density",
    y="income",
    size="size",
    source=source,
    fill_color=transform("transit_score", color_mapper),
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

# Native ColorBar — the transit-score -> color mapping, independent of the
# size legend below (which explains the green-space -> bubble-size mapping).
color_bar = ColorBar(
    color_mapper=color_mapper,
    width=22,
    location=(0, 0),
    title="Transit Score (0-10)",
    title_text_font_size="30pt",
    title_text_color=INK,
    major_label_text_font_size="28pt",
    major_label_text_color=INK_SOFT,
    background_fill_color=PAGE_BG,
    border_line_color=None,
    bar_line_color=INK_SOFT,
    major_tick_line_color=INK_SOFT,
)
p.add_layout(color_bar, "right")

# Hover tool — scoped to the main data renderer only (skip the legend swatches)
hover = HoverTool(
    renderers=[main_renderer],
    tooltips=[
        ("Density", "@density_display{,} people/km²"),
        ("Income", "$@income_display{0.0}k"),
        ("Green Space", "@green_display m²/capita"),
        ("Transit Score", "@transit_display / 10"),
    ],
    mode="mouse",
)
p.add_tools(hover)

# Dashed trend line — guides viewer to the positive density-income correlation
trend_coeffs = np.polyfit(population_density, median_income, 1)
x_trend = np.linspace(x_start, x_end, 100)
y_trend = np.polyval(trend_coeffs, x_trend)
p.line(x=x_trend, y=y_trend, line_color=INK_SOFT, line_dash="dashed", line_width=5, line_alpha=0.5)

# Outlier callout — the point furthest above the trend line
residual = median_income - np.polyval(trend_coeffs, population_density)
outlier_idx = int(np.argmax(residual))
outlier_x = population_density[outlier_idx]
outlier_y = median_income[outlier_idx]

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
p.outline_line_alpha = 0

p.title.text_font_size = "58pt"
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
        x="x", y="y", size="size", source=ref_src, fill_color=INK_SOFT, fill_alpha=0.5, line_color=PAGE_BG, line_width=2
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

# Outlier callout — arrow + label pointing at the point furthest above trend
p.add_layout(
    Arrow(
        end=NormalHead(size=14, fill_color=INK_SOFT, line_color=INK_SOFT),
        x_start=outlier_x + x_range * 0.09,
        y_start=outlier_y + y_range * 0.06,
        x_end=outlier_x + x_range * 0.012,
        y_end=outlier_y + y_range * 0.012,
        line_color=INK_SOFT,
        line_width=3,
    )
)
p.add_layout(
    Label(
        x=outlier_x + x_range * 0.095,
        y=outlier_y + y_range * 0.065,
        text="Outlier: income well above trend",
        text_font_size="28pt",
        text_font_style="italic",
        text_color=INK_SOFT,
        text_align="left",
        text_baseline="bottom",
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
