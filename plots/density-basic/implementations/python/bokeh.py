"""anyplot.ai
density-basic: Basic Density Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-30
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter, Range1d
from bokeh.plotting import figure
from PIL import Image
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — first categorical series is always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
RESPONSE_TIME = "Response time (ms)"  # role: values

# Data: replace this block with your own table, for example df = pd.read_csv("response_times.csv")
np.random.seed(42)
df = pd.DataFrame(
    {
        RESPONSE_TIME: np.concatenate(
            [
                np.random.normal(150, 30, 300),  # fast responses
                np.random.normal(280, 40, 100),  # slower responses
            ]
        )
    }
)

# Plot: reads only df and the constants above
values = df[RESPONSE_TIME].dropna().to_numpy()
n = len(values)

# Gaussian KDE with Silverman's rule-of-thumb bandwidth
iqr = np.percentile(values, 75) - np.percentile(values, 25)
bandwidth = 0.9 * min(np.std(values), iqr / 1.34) * n ** (-0.2)

# Grid ends three bandwidths past the data so the curve falls back to zero at both ends
x_grid = np.linspace(values.min() - 3 * bandwidth, values.max() + 3 * bandwidth, 500)
density = np.exp(-0.5 * ((x_grid[:, None] - values[None, :]) / bandwidth) ** 2).sum(axis=1)
density /= n * bandwidth * np.sqrt(2 * np.pi)

top = density.max()
source = ColumnDataSource(data={"x": x_grid, "density": density, "base": np.zeros_like(x_grid)})
rug_source = ColumnDataSource(data={"x": values, "y0": np.zeros(n), "y1": np.full(n, top * 0.05)})

p = figure(
    width=3200,
    height=1800,
    title="density-basic · python · bokeh · anyplot.ai",
    x_axis_label=RESPONSE_TIME,
    y_axis_label="Density",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
    x_range=Range1d(x_grid.min(), x_grid.max()),
    y_range=Range1d(0, top * 1.1),
)

# Fill under the curve, then the curve itself (also the hover target)
p.varea(x="x", y1="base", y2="density", source=source, fill_color=IMPRINT_PALETTE[0], fill_alpha=0.18)
density_line = p.line(x="x", y="density", source=source, line_color=IMPRINT_PALETTE[0], line_width=5)

# Rug: one short tick per observation along the baseline
p.segment(
    x0="x", y0="y0", x1="x", y1="y1", source=rug_source, line_color=IMPRINT_PALETTE[0], line_width=2, line_alpha=0.4
)

p.add_tools(
    HoverTool(
        renderers=[density_line],
        tooltips=[(RESPONSE_TIME, "@x{0.0}"), ("Density", "@density{0.00000}")],
        mode="vline",
        line_policy="nearest",
    )
)

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.formatter = NumeralTickFormatter(format="0.0000")

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Save interactive HTML, then screenshot it with headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_script(
    "document.documentElement.style.background = arguments[0]; document.body.style.background = arguments[0];", PAGE_BG
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()

# Normalize to the exact canvas — guards against a 1-2 px rounding in headless Chrome
img = Image.open(f"plot-{THEME}.png")
if img.size != (W, H):
    canvas = Image.new("RGB", (W, H), PAGE_BG)
    canvas.paste(img, ((W - img.size[0]) // 2, (H - img.size[1]) // 2))
    canvas.save(f"plot-{THEME}.png")
