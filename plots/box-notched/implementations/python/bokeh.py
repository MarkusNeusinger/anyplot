""" anyplot.ai
box-notched: Notched Box Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-07
"""

import os
import sys
import time
from pathlib import Path


# Remove the script's own directory from sys.path so "bokeh" resolves to the
# installed package, not this file.
_this_dir = str(Path(__file__).parent.resolve())
sys.path = [p for p in sys.path if os.path.abspath(p) != _this_dir and p != ""]

import numpy as np  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series is always #009E73)
IMPRINT = [
    "#009E73",  # bluish green (brand)
    "#C475FD",  # vermillion
    "#4467A3",  # blue
    "#BD8233",  # reddish purple
    "#AE3030",  # orange
]

# Data - Employee performance scores across departments
np.random.seed(42)

categories = ["Engineering", "Sales", "Marketing", "Operations", "HR"]

# Generate realistic performance score data with varying distributions
data = {
    "Engineering": np.random.normal(78, 8, 60),
    "Sales": np.random.normal(72, 12, 55),
    "Marketing": np.random.normal(75, 6, 50),
    "Operations": np.random.normal(68, 10, 65),
    "HR": np.random.normal(74, 7, 45),
}

# Add some outliers (constrained to 0-100 range)
data["Sales"] = np.append(data["Sales"], [45, 98])
data["Operations"] = np.append(data["Operations"], [42, 95])
data["HR"] = np.append(data["HR"], [50])

# Clip all values to 0-100 range
for cat in categories:
    data[cat] = np.clip(data[cat], 0, 100)

# Compute box plot statistics with notches for each category
box_data = {
    "categories": [],
    "q1": [],
    "q2": [],  # median
    "q3": [],
    "upper": [],
    "lower": [],
    "notch_lower": [],
    "notch_upper": [],
    "colors": [],
}

outlier_data = {"category": [], "value": [], "color": []}

for i, cat in enumerate(categories):
    values = data[cat]
    q1 = np.percentile(values, 25)
    q2 = np.percentile(values, 50)
    q3 = np.percentile(values, 75)
    iqr = q3 - q1
    n = len(values)

    # Whiskers at 1.5 * IQR
    lower_fence = q1 - 1.5 * iqr
    upper_fence = q3 + 1.5 * iqr

    # Find values within whisker range for accurate whisker placement
    in_range = values[(values >= lower_fence) & (values <= upper_fence)]
    if len(in_range) > 0:
        lower_whisker = in_range.min()
        upper_whisker = in_range.max()
    else:
        lower_whisker = q1
        upper_whisker = q3

    # Notch: 95% CI around median = ±1.57 × IQR / √n
    notch_width = 1.57 * iqr / np.sqrt(n)
    notch_lower = q2 - notch_width
    notch_upper = q2 + notch_width

    box_data["categories"].append(cat)
    box_data["q1"].append(q1)
    box_data["q2"].append(q2)
    box_data["q3"].append(q3)
    box_data["upper"].append(upper_whisker)
    box_data["lower"].append(lower_whisker)
    box_data["notch_lower"].append(notch_lower)
    box_data["notch_upper"].append(notch_upper)
    box_data["colors"].append(IMPRINT[i])

    # Find outliers
    outliers = values[(values < lower_fence) | (values > upper_fence)]
    for o in outliers:
        outlier_data["category"].append(cat)
        outlier_data["value"].append(o)
        outlier_data["color"].append(IMPRINT[i])

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="box-notched · bokeh · anyplot.ai",
    x_range=categories,
    y_axis_label="Performance Score (0–100)",
    x_axis_label="Department",
)

# Styling - larger sizes for 4800x2700 canvas
p.title.text_font_size = "28pt"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.title.text_color = INK
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

# Box width
box_width = 0.6

# Draw each notched box manually
for i, _cat in enumerate(categories):
    q1 = box_data["q1"][i]
    q2 = box_data["q2"][i]
    q3 = box_data["q3"][i]
    nl = box_data["notch_lower"][i]
    nu = box_data["notch_upper"][i]
    lower = box_data["lower"][i]
    upper = box_data["upper"][i]
    color = box_data["colors"][i]

    half_width = box_width / 2
    notch_indent = box_width / 4

    # Lower box (q1 to notch_lower)
    p.quad(
        top=[nl],
        bottom=[q1],
        left=[i - half_width],
        right=[i + half_width],
        fill_color=color,
        fill_alpha=0.85,
        line_color=INK_SOFT,
        line_width=2,
    )

    # Upper box (notch_upper to q3)
    p.quad(
        top=[q3],
        bottom=[nu],
        left=[i - half_width],
        right=[i + half_width],
        fill_color=color,
        fill_alpha=0.85,
        line_color=INK_SOFT,
        line_width=2,
    )

    # Left notch triangle
    p.patch(
        x=[i - half_width, i - notch_indent, i - half_width],
        y=[nl, q2, nu],
        fill_color=color,
        fill_alpha=0.85,
        line_color=INK_SOFT,
        line_width=2,
    )

    # Right notch triangle
    p.patch(
        x=[i + half_width, i + notch_indent, i + half_width],
        y=[nl, q2, nu],
        fill_color=color,
        fill_alpha=0.85,
        line_color=INK_SOFT,
        line_width=2,
    )

    # Median line
    p.segment(x0=[i - notch_indent], x1=[i + notch_indent], y0=[q2], y1=[q2], line_color=INK, line_width=3)

    # Whiskers (vertical lines)
    p.segment(x0=[i], x1=[i], y0=[q3], y1=[upper], line_color=INK_SOFT, line_width=2)
    p.segment(x0=[i], x1=[i], y0=[q1], y1=[lower], line_color=INK_SOFT, line_width=2)

    # Whisker caps (horizontal lines)
    cap_width = box_width / 3
    p.segment(x0=[i - cap_width], x1=[i + cap_width], y0=[upper], y1=[upper], line_color=INK_SOFT, line_width=2)
    p.segment(x0=[i - cap_width], x1=[i + cap_width], y0=[lower], y1=[lower], line_color=INK_SOFT, line_width=2)

# Draw outliers
if outlier_data["category"]:
    outlier_source = ColumnDataSource(
        data={"x": outlier_data["category"], "y": outlier_data["value"], "color": outlier_data["color"]}
    )

    p.scatter(
        x="x",
        y="y",
        source=outlier_source,
        size=15,
        fill_color=PAGE_BG,
        line_color="color",
        line_width=3,
        fill_alpha=0.9,
    )

# Remove toolbar
p.toolbar_location = None

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
