""" anyplot.ai
bar-stacked-percent: 100% Stacked Bar Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 95/100 | Updated: 2026-05-08
"""

import os
import sys
import time
from pathlib import Path


# Workaround: Remove current directory from import path to avoid circular import
# when the file bokeh.py conflicts with the bokeh package name
original_path = sys.path.copy()
sys.path = [p for p in sys.path if p != "" and not (os.path.isfile(os.path.join(p, "bokeh.py")) if p else False)]

try:
    import pandas as pd
    from bokeh.io import output_file, save
    from bokeh.models import ColumnDataSource, LabelSet
    from bokeh.plotting import figure
    from selenium import webdriver
    from selenium.webdriver.chrome.options import Options
finally:
    sys.path = original_path

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Market share of smartphone brands over quarters
categories = ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025"]
components = ["Apple", "Samsung", "Xiaomi", "Others"]

raw_data = {
    "Apple": [28, 25, 22, 31, 27],
    "Samsung": [23, 24, 26, 22, 24],
    "Xiaomi": [14, 16, 18, 15, 17],
    "Others": [35, 35, 34, 32, 32],
}

# Calculate percentages (already sum to 100, but normalize for safety)
df = pd.DataFrame(raw_data, index=categories)
totals = df.sum(axis=1)
df_percent = df.div(totals, axis=0) * 100

# Calculate bottom positions for stacking
bottoms = {}
cumulative = [0.0] * len(categories)
for comp in components:
    bottoms[comp] = cumulative.copy()
    cumulative = [c + v for c, v in zip(cumulative, df_percent[comp], strict=True)]

# Create figure with categorical x-axis
p = figure(
    x_range=categories,
    width=4800,
    height=2700,
    title="bar-stacked-percent · bokeh · anyplot.ai",
    y_range=(0, 100),
    toolbar_location=None,
)

# Draw stacked bars
renderers = []
for i, comp in enumerate(components):
    source = ColumnDataSource(
        data={
            "x": categories,
            "top": [b + v for b, v in zip(bottoms[comp], df_percent[comp], strict=True)],
            "bottom": bottoms[comp],
            "value": df_percent[comp].tolist(),
        }
    )
    r = p.vbar(
        x="x",
        top="top",
        bottom="bottom",
        source=source,
        width=0.7,
        color=IMPRINT[i],
        legend_label=comp,
        line_color=PAGE_BG,
        line_width=2,
    )
    renderers.append(r)

# Add percentage labels inside each segment
for i, comp in enumerate(components):
    values = df_percent[comp].tolist()
    mids = [(b + b + v) / 2 for b, v in zip(bottoms[comp], values, strict=True)]

    # Only show labels for segments >= 10%
    labels = [f"{v:.0f}%" if v >= 10 else "" for v in values]

    label_source = ColumnDataSource(data={"x": categories, "y": mids, "text": labels})

    # Text color: white on dark colors (first series), INK on light colors
    text_color = "white" if i == 0 else INK

    label_set = LabelSet(
        x="x",
        y="y",
        text="text",
        source=label_source,
        text_align="center",
        text_baseline="middle",
        text_font_size="24pt",
        text_color=text_color,
        text_font_style="bold",
    )
    p.add_layout(label_set)

# Styling for large canvas
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label = "Quarter"
p.yaxis.axis_label = "Market Share (%)"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Axis colors
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK_SOFT
p.ygrid.grid_line_alpha = 0.10

# Background and border
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Legend styling
p.legend.location = "top_right"
p.legend.label_text_font_size = "18pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.border_line_color = INK_SOFT
p.legend.glyph_width = 50
p.legend.glyph_height = 50
p.legend.spacing = 15
p.legend.padding = 20

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
W, H = 4800, 2700
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
