"""anyplot.ai
curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-28
"""

import os
import sys
import time
from pathlib import Path


# Remove the script's own directory from sys.path so 'bokeh' resolves to the
# installed package, not this file (bokeh.py in the same directory).
sys.path = [p for p in sys.path if os.path.abspath(p) != os.path.abspath(os.path.dirname(__file__) or ".")]

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import BoxAnnotation, ColumnDataSource, Label, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
COLOR_TOTAL = IMPRINT_PALETTE[0]  # brand green — first/most prominent (U-shaped key curve)
COLOR_BIAS = IMPRINT_PALETTE[2]  # blue — semantic fit with underfitting zone
COLOR_VARIANCE = IMPRINT_PALETTE[1]  # purple — overfitting zone

# Constants
IRREDUCIBLE_LEVEL = 0.5  # noise floor of the theoretical model

# Column constants
COMPLEXITY = "Model Complexity"  # role: model_complexity
BIAS = "Bias²"  # role: bias_squared
VARIANCE = "Variance"  # role: variance
IRREDUCIBLE = "Irreducible Error"  # role: irreducible_error
TOTAL = "Total Error"  # role: total_error
Y_LABEL = "Prediction Error"

# Data: theoretical bias-variance curves; replace with your own table, for example df = pd.read_csv("errors.csv")
complexity = np.linspace(0.1, 10, 100)
bias_squared = 4.0 / (1 + complexity) ** 1.2
variance = 0.15 * complexity**1.3
df = pd.DataFrame(
    {
        COMPLEXITY: complexity,
        BIAS: bias_squared,
        VARIANCE: variance,
        IRREDUCIBLE: np.full_like(complexity, IRREDUCIBLE_LEVEL),
        TOTAL: bias_squared + variance + IRREDUCIBLE_LEVEL,
    }
)

# Plot
title_str = "curve-bias-variance-tradeoff · python · bokeh · anyplot.ai"

best = df[TOTAL].idxmin()
optimal_complexity = df.loc[best, COMPLEXITY]
optimal_error = df.loc[best, TOTAL]
x_max = df[COMPLEXITY].max() * 1.05
y_max = df[TOTAL].max() * 1.35
source = ColumnDataSource(df)


def curve_at(column, x):
    """Value of a curve at complexity x, for placing labels next to it."""
    return float(np.interp(x, df[COMPLEXITY], df[column]))


p = figure(
    width=3200,
    height=1800,
    title=title_str,
    x_axis_label=COMPLEXITY,
    y_axis_label=Y_LABEL,
    x_range=(0, x_max),
    y_range=(0, y_max),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Shaded underfitting / overfitting zones
p.add_layout(BoxAnnotation(left=0, right=optimal_complexity, fill_alpha=0.07, fill_color=COLOR_BIAS))
p.add_layout(BoxAnnotation(left=optimal_complexity, right=x_max, fill_alpha=0.07, fill_color=COLOR_VARIANCE))

# Curves — background lines first, Total Error on top
p.line(
    COMPLEXITY,
    IRREDUCIBLE,
    source=source,
    line_width=4,
    line_color=INK_SOFT,
    line_dash="dashed",
    legend_label=IRREDUCIBLE,
)
p.line(COMPLEXITY, BIAS, source=source, line_width=5, line_color=COLOR_BIAS, legend_label=BIAS)
p.line(COMPLEXITY, VARIANCE, source=source, line_width=5, line_color=COLOR_VARIANCE, legend_label=VARIANCE)
p.line(COMPLEXITY, TOTAL, source=source, line_width=7, line_color=COLOR_TOTAL, legend_label=TOTAL)

# Optimal complexity — vertical dotted guide + marker at the minimum of the total error
p.add_layout(Span(location=optimal_complexity, dimension="height", line_color=INK, line_width=2, line_dash="dotted"))
p.scatter([optimal_complexity], [optimal_error], size=20, color=COLOR_TOTAL, line_color=PAGE_BG, line_width=3)

# Direct curve labels, each placed relative to its own curve
x_bias, x_var, x_irr, x_tot = 0.14 * x_max, 0.76 * x_max, 0.60 * x_max, 0.55 * x_max
p.add_layout(
    Label(
        x=x_bias,
        y=curve_at(BIAS, x_bias) + 0.1,
        text=BIAS,
        text_font_size="28pt",
        text_color=COLOR_BIAS,
        text_font_style="bold",
    )
)
p.add_layout(
    Label(
        x=x_var,
        y=curve_at(VARIANCE, x_var) - 0.55,
        text=VARIANCE,
        text_font_size="28pt",
        text_color=COLOR_VARIANCE,
        text_font_style="bold",
    )
)
p.add_layout(
    Label(
        x=x_irr,
        y=IRREDUCIBLE_LEVEL + 0.18,
        text=IRREDUCIBLE,
        text_font_size="22pt",
        text_color=INK_SOFT,
        text_font_style="italic",
    )
)
p.add_layout(
    Label(
        x=x_tot,
        y=curve_at(TOTAL, x_tot) + 0.25,
        text=TOTAL,
        text_font_size="28pt",
        text_color=COLOR_TOTAL,
        text_font_style="bold",
    )
)
p.add_layout(
    Label(
        x=optimal_complexity + 0.02 * x_max,
        y=optimal_error + 0.3,
        text="Optimal complexity",
        text_font_size="28pt",
        text_color=INK,
        text_font_style="bold",
    )
)

# Formula annotation
p.add_layout(
    Label(
        x=0.012 * x_max,
        y=0.93 * y_max,
        text=f"{TOTAL} = {BIAS} + {VARIANCE} + {IRREDUCIBLE}",
        text_font_size="24pt",
        text_color=INK_SOFT,
        text_font_style="italic",
    )
)

# Zone labels (top corners of each region)
p.add_layout(Label(x=0.04 * x_max, y=0.84 * y_max, text="Underfitting", text_font_size="24pt", text_color=COLOR_BIAS))
p.add_layout(Label(x=0.04 * x_max, y=0.75 * y_max, text="(High Bias)", text_font_size="24pt", text_color=COLOR_BIAS))
p.add_layout(
    Label(x=0.72 * x_max, y=0.84 * y_max, text="Overfitting", text_font_size="24pt", text_color=COLOR_VARIANCE)
)
p.add_layout(
    Label(x=0.72 * x_max, y=0.75 * y_max, text="(High Variance)", text_font_size="24pt", text_color=COLOR_VARIANCE)
)

# Text sizing
p.title.text_font_size = "50pt"
p.title.text_font_style = "bold"
p.title.text_color = INK
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
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid — Y-axis grid only for line charts
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.12

# Background and chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Legend
p.legend.location = "top_right"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.spacing = 12
p.legend.padding = 20

# Save HTML (interactive artifact) + PNG via headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

# Window height is set ~140px taller than the figure so the viewport
# content area (figure height = 1800) isn't clipped by browser chrome.
W, H = 3200, 1940
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
