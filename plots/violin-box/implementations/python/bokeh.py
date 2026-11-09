""" anyplot.ai
violin-box: Violin Plot with Embedded Box Plot
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 82/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Legend, LegendItem
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
STUDY_METHOD = "Study Method"  # role: group
TEST_SCORE = "Test Score"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
method_a = np.random.normal(72, 12, 120)  # standard distribution
method_b = np.concatenate([np.random.normal(78, 8, 100), [48, 52, 95, 98]])  # outliers at both ends
method_c = np.random.normal(65, 15, 120)  # wider spread
method_d = np.concatenate([np.random.normal(80, 6, 90), np.random.normal(55, 3, 20), [38, 40, 42]])  # bimodal
df = pd.DataFrame(
    {
        STUDY_METHOD: ["Method A"] * len(method_a)
        + ["Method B"] * len(method_b)
        + ["Method C"] * len(method_c)
        + ["Method D"] * len(method_d),
        TEST_SCORE: np.concatenate([method_a, method_b, method_c, method_d]),
    }
)

# Plot: reads only df and the constants above
scores = df.dropna(subset=[STUDY_METHOD, TEST_SCORE]).astype({STUDY_METHOD: str, TEST_SCORE: float})
methods = list(scores[STUDY_METHOD].unique())

p = figure(
    width=3200,
    height=1800,
    title="violin-box · python · bokeh · anyplot.ai",
    x_axis_label=STUDY_METHOD,
    y_axis_label=TEST_SCORE,
    x_range=methods,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Theme-adaptive styling
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.title.text_font_size = "50pt"

p.xaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_font_size = "42pt"

p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_font_size = "34pt"

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid styling - subtle
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Violin width scaling (share of category spacing on each side)
violin_width = 0.38
box_width = 0.08
cap_width = 0.05

# Track renderers for legend
violin_renderer = None
box_renderer = None
median_renderer = None
outlier_mask = pd.Series(False, index=scores.index)

# Draw violins with embedded box plots for each category
for i, method in enumerate(methods):
    group_scores = scores[scores[STUDY_METHOD] == method][TEST_SCORE]
    values = group_scores.to_numpy()
    n = len(values)

    # Compute KDE using Gaussian kernel (Silverman's rule for bandwidth)
    std = np.std(values)
    iqr = np.percentile(values, 75) - np.percentile(values, 25)
    bandwidth = 0.9 * min(std, iqr / 1.34) * n ** (-0.2)
    bandwidth = max(bandwidth, 0.1)

    # Tails end one bandwidth past the data range
    y_grid = np.linspace(values.min() - bandwidth, values.max() + bandwidth, 100)
    density = np.zeros_like(y_grid, dtype=float)
    for xi in values:
        density += np.exp(-0.5 * ((y_grid - xi) / bandwidth) ** 2)
    density /= n * bandwidth * np.sqrt(2 * np.pi)

    # Scale density to violin width
    density_scaled = density / density.max() * violin_width

    # Create violin shape (mirrored on both sides) in categorical offset format
    xs_left = [(method, float(-d)) for d in density_scaled]
    xs_right = [(method, float(d)) for d in density_scaled[::-1]]

    violin_color = IMPRINT_PALETTE[i]
    vr = p.patch(
        xs_left + xs_right,
        list(y_grid) + list(y_grid[::-1]),
        fill_color=violin_color,
        fill_alpha=0.6,
        line_color=violin_color,
        line_width=3,
    )
    if violin_renderer is None:
        violin_renderer = vr

    # Compute box plot statistics
    q1 = np.percentile(values, 25)
    median = np.percentile(values, 50)
    q3 = np.percentile(values, 75)
    iqr_val = q3 - q1
    whisker_low = max(values.min(), q1 - 1.5 * iqr_val)
    whisker_high = min(values.max(), q3 + 1.5 * iqr_val)

    # Draw box inside violin (IQR from Q1 to Q3)
    br = p.quad(
        left=[(method, -box_width)],
        right=[(method, box_width)],
        top=[q3],
        bottom=[q1],
        fill_color=violin_color,
        fill_alpha=0.9,
        line_color=INK,
        line_width=3,
    )
    if box_renderer is None:
        box_renderer = br

    # Draw median line
    mr = p.segment(
        x0=[(method, -box_width * 1.3)],
        y0=[median],
        x1=[(method, box_width * 1.3)],
        y1=[median],
        line_color=INK,
        line_width=5,
    )
    if median_renderer is None:
        median_renderer = mr

    # Whiskers (vertical lines from box to whisker limits) with caps
    p.segment(
        x0=[method, method],
        y0=[q1, q3],
        x1=[method, method],
        y1=[whisker_low, whisker_high],
        line_color=INK_SOFT,
        line_width=3,
    )
    p.segment(
        x0=[(method, -cap_width), (method, -cap_width)],
        y0=[whisker_low, whisker_high],
        x1=[(method, cap_width), (method, cap_width)],
        y1=[whisker_low, whisker_high],
        line_color=INK_SOFT,
        line_width=3,
    )

    # Mark outliers beyond the whiskers
    outlier_mask |= (scores[STUDY_METHOD] == method) & (
        (scores[TEST_SCORE] < whisker_low) | (scores[TEST_SCORE] > whisker_high)
    )

# Draw all outliers at their values
outlier_renderer = None
if outlier_mask.any():
    outlier_renderer = p.scatter(
        x=STUDY_METHOD,
        y=TEST_SCORE,
        source=ColumnDataSource(scores[outlier_mask]),
        size=22,
        fill_color=PAGE_BG,
        line_color=INK,
        line_width=3,
        marker="circle",
    )

# Create legend
legend_items = [
    LegendItem(label="Distribution (KDE)", renderers=[violin_renderer]),
    LegendItem(label="IQR (Q1–Q3)", renderers=[box_renderer]),
    LegendItem(label="Median", renderers=[median_renderer]),
]
if outlier_renderer is not None:
    legend_items.append(LegendItem(label="Outliers", renderers=[outlier_renderer]))

legend = Legend(items=legend_items, location="top_right")
legend.label_text_color = INK_SOFT
legend.label_text_font_size = "34pt"
legend.background_fill_color = ELEVATED_BG
legend.border_line_color = INK_SOFT
legend.glyph_height = 50
legend.glyph_width = 50
legend.spacing = 20
legend.padding = 30
p.add_layout(legend, "right")

# Save HTML output
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
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
time.sleep(3)  # let bokeh's JS render the canvas
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
