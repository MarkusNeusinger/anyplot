"""anyplot.ai
coefficient-confidence: Coefficient Plot with Confidence Intervals
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NULL_VALUE = 0  # the null hypothesis: a coefficient of zero
Z_95 = 1.96  # normal quantile of a 95% confidence interval
LEGEND_LABELS = {True: "Significant (95% CI excludes zero)", False: "Not significant (95% CI crosses zero)"}

# Columns: set these to your table's column names
VARIABLE = "Predictor variable"  # role: variable
COEFFICIENT = "Coefficient estimate (standardized)"  # role: coefficient
CI_LOWER = "95% CI lower"  # role: ci_lower
CI_UPPER = "95% CI upper"  # role: ci_upper
SIGNIFICANT = "Significant"  # role: significant

# Data: replace this block with your own table, for example df = pd.read_csv("coefficients.csv")
# Coefficients from a multiple linear regression predicting housing prices
estimates = pd.DataFrame(
    {
        VARIABLE: [
            "Square Footage",
            "Number of Bedrooms",
            "Number of Bathrooms",
            "Age of House",
            "Distance to City Center",
            "Lot Size",
            "Garage Size",
            "School Rating",
            "Crime Rate Index",
            "Property Tax Rate",
        ],
        COEFFICIENT: [0.45, 0.12, 0.18, -0.08, -0.22, 0.15, 0.09, 0.28, -0.35, -0.05],
        "std_error": [0.05, 0.08, 0.06, 0.03, 0.07, 0.04, 0.06, 0.05, 0.09, 0.07],
    }
)
df = pd.DataFrame(
    {
        VARIABLE: estimates[VARIABLE],
        COEFFICIENT: estimates[COEFFICIENT],
        CI_LOWER: estimates[COEFFICIENT] - Z_95 * estimates["std_error"],
        CI_UPPER: estimates[COEFFICIENT] + Z_95 * estimates["std_error"],
    }
)
df[SIGNIFICANT] = ~((df[CI_LOWER] < NULL_VALUE) & (df[CI_UPPER] > NULL_VALUE))

# Plot: reads only df and the constants above
# Order the rows by coefficient magnitude, largest at the top
df = df.sort_values(COEFFICIENT, key=abs).reset_index(drop=True)
df[SIGNIFICANT] = df[SIGNIFICANT].astype(bool)
df["_label"] = df[SIGNIFICANT].map(LEGEND_LABELS)
colors = {True: IMPRINT_PALETTE[0], False: INK_SOFT}

p = figure(
    width=3200,
    height=1800,
    y_range=list(df[VARIABLE]),
    title="coefficient-confidence · python · bokeh · anyplot.ai",
    x_axis_label=COEFFICIENT,
    y_axis_label=VARIABLE,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

# Vertical reference line at zero, drawn above the gridlines
p.add_layout(
    Span(location=NULL_VALUE, dimension="height", line_color=INK, line_width=3, line_dash="dashed", line_alpha=0.8)
)

# One group per significance flag: interval segments, then points on top
renderers = []
for flag in (True, False):
    rows = df[df[SIGNIFICANT] == flag]
    if rows.empty:
        continue
    source = ColumnDataSource(rows)
    p.segment(x0=CI_LOWER, x1=CI_UPPER, y0=VARIABLE, y1=VARIABLE, source=source, line_width=7, line_color=colors[flag])
    renderers.append(
        p.scatter(
            x=COEFFICIENT,
            y=VARIABLE,
            source=source,
            size=32,
            color=colors[flag],
            line_color=PAGE_BG,
            line_width=3,
            legend_label=LEGEND_LABELS[flag],
        )
    )

p.add_tools(
    HoverTool(
        tooltips=[
            ("Variable", f"@{{{VARIABLE}}}"),
            ("Coefficient", f"@{{{COEFFICIENT}}}{{0.000}}"),
            ("95% CI", f"[@{{{CI_LOWER}}}{{0.000}}, @{{{CI_UPPER}}}{{0.000}}]"),
            ("Status", "@_label"),
        ],
        renderers=renderers,
    )
)

# Style
p.title.text_font_size = "46pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "30pt"
p.yaxis.major_label_text_font_size = "30pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.legend.location = "top_left"
p.legend.label_text_font_size = "28pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_width = 40
p.legend.glyph_height = 40
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.border_line_color = INK_SOFT
p.legend.border_line_width = 2
p.legend.padding = 20
p.legend.margin = 30

for grid in (p.xgrid, p.ygrid):
    grid.grid_line_color = INK
    grid.grid_line_alpha = 0.10
    grid.grid_line_dash = "dashed"

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
for axis in (p.xaxis, p.yaxis):
    axis.axis_line_color = INK_SOFT
    axis.axis_line_width = 2
    axis.major_tick_line_color = INK_SOFT
    axis.major_tick_line_width = 2

# Save the interactive HTML, then screenshot it with headless Chrome
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
driver.set_window_size(W, H)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
