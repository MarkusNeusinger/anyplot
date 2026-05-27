""" anyplot.ai
volcano-basic: Volcano Plot for Statistical Significance
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-14
"""

import os
import time
from pathlib import Path

import numpy as np
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

# Okabe-Ito palette
COLOR_UP = "#C475FD"  # vermillion
COLOR_DOWN = "#4467A3"  # blue
COLOR_NS = "#AAAAAA"  # neutral gray

# Data - Simulated differential expression results
np.random.seed(42)
n_genes = 2000

# Generate log2 fold changes (effect sizes)
log2_fc = np.random.normal(0, 1.5, n_genes)

# Generate p-values: most genes non-significant, some highly significant
# Use inverse relationship with fold change magnitude for realism
base_pvals = np.random.uniform(0.001, 1, n_genes)
fold_effect = np.abs(log2_fc) / np.max(np.abs(log2_fc))
pvals = base_pvals * (1 - 0.7 * fold_effect) + 0.01 * np.random.random(n_genes)
pvals = np.clip(pvals, 1e-50, 1)

neg_log10_pval = -np.log10(pvals)

# Significance thresholds
pval_threshold = -np.log10(0.05)  # ~1.3
fc_threshold = 1.0  # log2(2) = 1

# Classify points by significance
significant_up = (neg_log10_pval > pval_threshold) & (log2_fc > fc_threshold)
significant_down = (neg_log10_pval > pval_threshold) & (log2_fc < -fc_threshold)

# Create separate data sources for each category (enables proper legend)
source_up = ColumnDataSource(
    data={
        "x": log2_fc[significant_up],
        "y": neg_log10_pval[significant_up],
        "description": [
            f"Up-regulated: FC={x:.2f}, p={10 ** (-y):.2e}"
            for x, y in zip(log2_fc[significant_up], neg_log10_pval[significant_up], strict=True)
        ],
    }
)

source_down = ColumnDataSource(
    data={
        "x": log2_fc[significant_down],
        "y": neg_log10_pval[significant_down],
        "description": [
            f"Down-regulated: FC={x:.2f}, p={10 ** (-y):.2e}"
            for x, y in zip(log2_fc[significant_down], neg_log10_pval[significant_down], strict=True)
        ],
    }
)

source_ns = ColumnDataSource(
    data={
        "x": log2_fc[~(significant_up | significant_down)],
        "y": neg_log10_pval[~(significant_up | significant_down)],
        "description": [
            f"Not significant: FC={x:.2f}, p={10 ** (-y):.2e}"
            for x, y in zip(
                log2_fc[~(significant_up | significant_down)], neg_log10_pval[~(significant_up | significant_down)], strict=True
            )
        ],
    }
)

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="volcano-basic · bokeh · anyplot.ai",
    x_axis_label="Log₂ Fold Change",
    y_axis_label="-Log₁₀ (P-value)",
)

# Hover tool
hover = HoverTool(tooltips=[("", "@description")])
p.add_tools(hover)

# Plot points by category (non-significant first, then significant on top)
p.scatter(x="x", y="y", source=source_ns, color=COLOR_NS, size=18, alpha=0.5, legend_label="Not significant")

p.scatter(x="x", y="y", source=source_down, color=COLOR_DOWN, size=25, alpha=0.7, legend_label="Down-regulated")

p.scatter(x="x", y="y", source=source_up, color=COLOR_UP, size=25, alpha=0.7, legend_label="Up-regulated")

# Add threshold lines
hline = Span(
    location=pval_threshold, dimension="width", line_color=INK_SOFT, line_dash="dashed", line_width=3, line_alpha=0.5
)
p.add_layout(hline)

vline_pos = Span(
    location=fc_threshold, dimension="height", line_color=INK_SOFT, line_dash="dashed", line_width=3, line_alpha=0.5
)
p.add_layout(vline_pos)

vline_neg = Span(
    location=-fc_threshold, dimension="height", line_color=INK_SOFT, line_dash="dashed", line_width=3, line_alpha=0.5
)
p.add_layout(vline_neg)

# Styling - scaled for 4800x2700 canvas
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.1
p.ygrid.grid_line_alpha = 0.1

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Legend styling
p.legend.location = "top_right"
p.legend.label_text_font_size = "18pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.spacing = 15
p.legend.padding = 20
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
