"""anyplot.ai
scatter-regression-polynomial: Scatter Plot with Polynomial Regression
Library: bokeh 3.9.2 | Python 3.13.14
Quality: 85/100 | Updated: 2026-08-11
"""

import os
import time
from pathlib import Path

import numpy as np
from bokeh.events import MouseMove
from bokeh.io import output_file, save
from bokeh.models import Band, BoxAnnotation, ColumnDataSource, CustomJS, HoverTool, Label, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]  # data points - always first series
ACCENT = IMPRINT_PALETTE[1]  # regression curve - lavender, second series
MUTED = INK_MUTED  # confidence band fill - "other" semantic anchor

# Data - Manufacturing efficiency curve (diminishing returns pattern)
np.random.seed(42)
n_points = 100

# Investment amount (thousands of dollars)
x = np.linspace(10, 100, n_points)
# Efficiency gains follow a quadratic pattern with diminishing returns
# True relationship: y = -0.005x^2 + 1.2x + 20 + noise
y = -0.005 * x**2 + 1.2 * x + 20 + np.random.normal(0, 3, n_points)

# Polynomial regression (degree 2 - quadratic)
coeffs = np.polyfit(x, y, 2)
poly = np.poly1d(coeffs)

# Calculate R-squared
y_pred = poly(x)
ss_res = np.sum((y - y_pred) ** 2)
ss_tot = np.sum((y - np.mean(y)) ** 2)
r_squared = 1 - (ss_res / ss_tot)

# Create smooth curve for regression line + a 95% prediction band from the
# residual spread (approximate, but conveys fit uncertainty at a glance)
residual_std = np.std(y - y_pred)
x_smooth = np.linspace(x.min(), x.max(), 200)
y_smooth = poly(x_smooth)
y_lower = y_smooth - 1.96 * residual_std
y_upper = y_smooth + 1.96 * residual_std

# Format polynomial equation
a, b, c = coeffs
equation = f"y = {a:.4f}x² + {b:.2f}x + {c:.2f}"

# Marginal gain dy/dx = 2ax + b — the story this curve is telling. Mark where
# the marginal gain has fallen to half its value at x.min(): everything past
# that point is the "diminishing returns" regime the spec's domain is about.
marginal_at_xmin = 2 * a * x.min() + b
zone_start = (0.5 * marginal_at_xmin - b) / (2 * a)

# Create data sources
scatter_source = ColumnDataSource(data={"x": x, "y": y})
line_source = ColumnDataSource(data={"x": x_smooth, "y": y_smooth})
band_source = ColumnDataSource(data={"x": x_smooth, "lower": y_lower, "upper": y_upper})

# Create figure — canvas is the hard 3200x1800 contract; min_border reserves
# room for the 34-42pt axis text so it isn't clipped at the PNG edge.
p = figure(
    width=3200,
    height=1800,
    title="scatter-regression-polynomial · bokeh · anyplot.ai",
    x_axis_label="Investment (thousands $)",
    y_axis_label="Efficiency Gain (%)",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Shade the diminishing-returns regime (past zone_start) so the curve's own
# story — gains flattening out — reads at a glance, not just from the equation
box = BoxAnnotation(left=zone_start, fill_color=MUTED, fill_alpha=0.07, line_color=None, level="underlay")
p.add_layout(box)
zone_label = Label(
    x=zone_start + 1.5,
    y=93,
    text="Diminishing returns",
    text_font_size="22pt",
    text_font_style="italic",
    text_color=INK_MUTED,
)
p.add_layout(zone_label)

# Confidence band first so scatter + curve render on top of it. A faint
# dashed edge (vs. no line) gives the band a defined silhouette instead of
# just a flat fill — a small but deliberate refinement over the bare default.
band = Band(
    base="x",
    lower="lower",
    upper="upper",
    source=band_source,
    fill_color=MUTED,
    fill_alpha=0.18,
    line_color=ACCENT,
    line_alpha=0.3,
    line_dash="dashed",
    line_width=1.5,
)
band.level = "underlay"
p.add_layout(band)

# Plot scatter points
p.scatter(x="x", y="y", source=scatter_source, size=12, color=BRAND, alpha=0.65, legend_label="Data Points")

# Plot polynomial regression curve
p.line(x="x", y="y", source=line_source, line_width=3.5, color=ACCENT, legend_label="Polynomial Fit (degree 2)")

# Add HoverTool for interactivity
hover = HoverTool(tooltips=[("Investment", "@x{0.0}"), ("Efficiency", "@y{0.0}")])
p.add_tools(hover)

# Add R² and equation annotation
annotation_text = f"R² = {r_squared:.4f}\n{equation}"
annotation = Label(
    x=68,
    y=78,
    text=annotation_text,
    text_font_size="30pt",
    text_color=INK,
    text_line_height=1.3,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.9,
    border_line_color=INK_SOFT,
)
p.add_layout(annotation)

# Bokeh-distinctive touch: a live marginal-gain readout. CustomJS recomputes
# dy/dx = 2ax + b from the mouse's data-space x on every move, so the HTML
# detail view lets a reader probe exactly where the curve is still climbing
# vs. already flattening — a live derivative isn't something a static-image
# library can offer.
crosshair_x = 35.0
marginal_initial = 2 * a * crosshair_x + b
crosshair = Span(location=crosshair_x, dimension="height", line_color=INK_SOFT, line_dash="dashed", line_width=2)
p.add_layout(crosshair)
marginal_label = Label(
    x=13,
    y=34,
    text=f"Marginal gain: {marginal_initial:.2f}%/$k at $35k (hover to probe)",
    text_font_size="22pt",
    text_color=INK_SOFT,
)
p.add_layout(marginal_label)
p.js_on_event(
    MouseMove,
    CustomJS(
        args={
            "span": crosshair,
            "label": marginal_label,
            "a": float(a),
            "b": float(b),
            "xmin": float(x.min()),
            "xmax": float(x.max()),
        },
        code="""
        const px = cb_obj.x
        if (px < xmin || px > xmax) { return }
        span.location = px
        const marginal = 2 * a * px + b
        label.x = px < (xmin + xmax) / 2 ? px + 1 : px - 24
        label.text = `Marginal gain: ${marginal.toFixed(2)}%/$k at $${px.toFixed(0)}k (hover to probe)`
        """,
    ),
)

# Styling - text sizes for the 3200x1800 canonical canvas
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
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = INK_SOFT
p.yaxis.minor_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_alpha = 0.35
p.yaxis.minor_tick_line_alpha = 0.35

# Grid styling
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_alpha = 0.15

# Legend styling - top left placement for better visibility
p.legend.location = "top_left"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = INK_SOFT
p.legend.border_line_width = 1.5
p.legend.padding = 16
p.legend.spacing = 10
p.legend.margin = 20

# Background and outline
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save as HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome using Selenium
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
# Headless Chrome's --window-size sets the OUTER window, which still reserves
# a phantom title-bar height even headless; pin the viewport exactly via CDP.
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
