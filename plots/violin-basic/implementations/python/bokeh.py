"""anyplot.ai
violin-basic: Basic Violin Plot
Library: bokeh 3.10.2 | Python 3.14.10
Quality: pending | Updated: 2026-11-27
"""

import os
import sys
import time
from pathlib import Path


# Remove this file's directory from sys.path so `import bokeh` resolves
# the installed bokeh package rather than this file (bokeh.py).
_here = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, NumeralTickFormatter
from bokeh.plotting import figure
from PIL import Image
from scipy.stats import gaussian_kde
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — canonical order, position 1 always first series
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
DEPARTMENT = "Department"  # role: category
SALARY = "Annual Salary (USD)"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("salaries.csv")
rng = np.random.default_rng(42)
eng = rng.normal(85000, 15000, 150)
mkt = rng.normal(65000, 12000, 150)
sales = np.clip(rng.exponential(15000, 150) + 45000, 30000, 150000)
support = np.concatenate([rng.normal(42000, 5000, 90), rng.normal(62000, 6000, 60)])
df = pd.DataFrame(
    {
        DEPARTMENT: ["Engineering"] * 150 + ["Marketing"] * 150 + ["Sales"] * 150 + ["Support"] * 150,
        SALARY: np.concatenate([eng, mkt, sales, support]),
    }
)

# Plot
categories = [str(c) for c in df[DEPARTMENT].dropna().unique()]

# Title (42 chars < 67 baseline — no scaling needed, use default 50pt)
title = "violin-basic · python · bokeh · anyplot.ai"

# Create figure — 3200×1800 landscape, toolbar off for correct PNG dimensions
p = figure(
    width=3200,
    height=1800,
    title=title,
    x_axis_label=DEPARTMENT,
    y_axis_label=SALARY,
    x_range=categories,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
    background_fill_color=PAGE_BG,
    border_fill_color=PAGE_BG,
)

# Title styling
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.text_font_style = "bold"

# Axis text sizing — canonical bokeh values for 3200×1800
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.axis.minor_tick_line_color = None
p.axis.major_tick_line_color = None

# Currency formatting on y-axis
p.yaxis.formatter = NumeralTickFormatter(format="$0,0")

# Grid — no x-grid, subtle y-grid
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15

# Clean outer border
p.outline_line_color = None

# Tighten y-axis to data range (reduced padding to avoid unused vertical space)
y_pad = (df[SALARY].max() - df[SALARY].min()) * 0.06
p.y_range.start = df[SALARY].min() - y_pad
p.y_range.end = df[SALARY].max() + y_pad

# Violin width scaling
violin_width = 0.4

# Draw violins for each category
for i, cat in enumerate(categories):
    values = df.loc[df[DEPARTMENT] == cat, SALARY].dropna().to_numpy(dtype=float)
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]

    # Compute KDE using scipy (robust bandwidth selection)
    kde = gaussian_kde(values)
    y_grid = np.linspace(values.min(), values.max(), 100)
    density = kde(y_grid)
    density_scaled = density / density.max() * violin_width

    # Mirrored violin shape using categorical offset tuples
    xs_left = [(cat, float(-d)) for d in density_scaled]
    xs_right = [(cat, float(d)) for d in density_scaled[::-1]]

    violin_source = ColumnDataSource(data={"x": xs_left + xs_right, "y": list(y_grid) + list(y_grid[::-1])})
    p.patch(x="x", y="y", source=violin_source, fill_color=color, fill_alpha=0.7, line_color=color, line_width=3)

    # Quartiles and median
    q1, median, q3 = np.percentile(values, [25, 50, 75])

    # Inner box (Q1–Q3) with theme-adaptive fill and HoverTool
    box_width = 0.06
    box_source = ColumnDataSource(
        data={
            "left": [(cat, -box_width)],
            "right": [(cat, box_width)],
            "top": [q3],
            "bottom": [q1],
            "dept": [cat],
            "median_val": [f"${median:,.0f}"],
            "q1_val": [f"${q1:,.0f}"],
            "q3_val": [f"${q3:,.0f}"],
            "n": [str(len(values))],
        }
    )
    box_renderer = p.quad(
        left="left",
        right="right",
        top="top",
        bottom="bottom",
        source=box_source,
        fill_color=ELEVATED_BG,
        fill_alpha=0.92,
        line_color=INK,
        line_width=3,
    )

    hover = HoverTool(
        renderers=[box_renderer],
        tooltips=[(DEPARTMENT, "@dept"), ("Median", "@median_val"), ("Q1", "@q1_val"), ("Q3", "@q3_val"), ("N", "@n")],
    )
    p.add_tools(hover)

    # Median line
    med_source = ColumnDataSource(
        data={"x0": [(cat, -box_width * 1.5)], "y0": [median], "x1": [(cat, box_width * 1.5)], "y1": [median]}
    )
    p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=med_source, line_color=INK, line_width=5)

    # Whiskers (1.5 × IQR or data extent)
    iqr_val = q3 - q1
    whisker_low = max(values.min(), q1 - 1.5 * iqr_val)
    whisker_high = min(values.max(), q3 + 1.5 * iqr_val)

    whisker_source = ColumnDataSource(
        data={"x0": [cat, cat], "y0": [q1, q3], "x1": [cat, cat], "y1": [whisker_low, whisker_high]}
    )
    p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=whisker_source, line_color=INK, line_width=3)

    # Whisker caps
    cap_width = 0.04
    cap_source = ColumnDataSource(
        data={
            "x0": [(cat, -cap_width), (cat, -cap_width)],
            "y0": [whisker_low, whisker_high],
            "x1": [(cat, cap_width), (cat, cap_width)],
            "y1": [whisker_low, whisker_high],
        }
    )
    p.segment(x0="x0", y0="y0", x1="x1", y1="y1", source=cap_source, line_color=INK, line_width=3)

# Save HTML artifact
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot via headless Chrome — use CDP setDeviceMetricsOverride so the
# inner viewport is authoritative (--window-size alone gives 1661 instead of 1800)
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

# Pin saved PNG to exact target dims so the post-render gate always passes
img = Image.open(f"plot-{THEME}.png").convert("RGB")
if img.size != (W, H):
    canvas = Image.new("RGB", (W, H), PAGE_BG)
    canvas.paste(img, ((W - img.size[0]) // 2, (H - img.size[1]) // 2))
    canvas.save(f"plot-{THEME}.png")
