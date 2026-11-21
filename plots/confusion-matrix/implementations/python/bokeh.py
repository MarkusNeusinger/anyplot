""" anyplot.ai
confusion-matrix: Confusion Matrix Heatmap
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColorBar, ColumnDataSource, LabelSet, LinearColorMapper
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

# Imprint palette: sequential ramp runs from position 1 to position 3
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def lerp_hex(c0, c1, t):
    r0, g0, b0 = (int(c0[i : i + 2], 16) for i in (1, 3, 5))
    r1, g1, b1 = (int(c1[i : i + 2], 16) for i in (1, 3, 5))
    r, g, b = (round(a + (z - a) * t) for a, z in ((r0, r1), (g0, g1), (b0, b1)))
    return f"#{r:02X}{g:02X}{b:02X}"


def luminance(color):
    channels = []
    for i in (1, 3, 5):
        c = int(color[i : i + 2], 16) / 255
        channels.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


SEQ_RAMP = [lerp_hex(IMPRINT_PALETTE[0], IMPRINT_PALETTE[2], t / 255) for t in range(256)]

# Columns: set these to your labels
TRUE_LABEL = "True Label"  # role: true_labels
PRED_LABEL = "Predicted Label"  # role: predicted_labels
CLASS_NAMES = "Class"  # role: class_names
COUNT = "Count"  # role: extra

# Data: replace this block with your own matrix, for example df = pd.crosstab(y_true, y_pred)
# Sentiment classifier results: rows are the true class, columns the predicted class
class_names = ["Negative", "Neutral", "Positive", "Very Positive"]  # the CLASS_NAMES axis labels
df = pd.DataFrame(
    [
        [142, 23, 8, 2],  # Negative: mostly correct, some confused with Neutral
        [18, 98, 31, 5],  # Neutral: often confused with adjacent classes
        [5, 28, 156, 24],  # Positive: good accuracy, some confusion with Neutral/Very Positive
        [1, 4, 19, 86],  # Very Positive: smaller class, good precision
    ],
    index=pd.Index(class_names, name=TRUE_LABEL),
    columns=pd.Index(class_names, name=PRED_LABEL),
)

# Plot: reads only df and the constants above
df = df.astype(float)
df.index = df.index.map(str)
df.columns = df.columns.map(str)
top = float(np.nanmax(df.to_numpy()))
long = df.rename_axis(index=TRUE_LABEL, columns=PRED_LABEL).stack().dropna().rename(COUNT).reset_index()
long["text"] = long[COUNT].map(lambda v: f"{v:.0f}")
mapper = LinearColorMapper(palette=SEQ_RAMP, low=0, high=top)


def cell_color(value):
    fill = SEQ_RAMP[round(255 * value / top)]
    lum = luminance(fill) + 0.05
    # WCAG contrast against white versus against the dark ink
    return "#FFFFFF" if 1.05 / lum >= lum / (luminance("#1A1A17") + 0.05) else "#1A1A17"


long["text_color"] = long[COUNT].map(cell_color)
source = ColumnDataSource(long)

p = figure(
    width=2400,
    height=2400,
    title="confusion-matrix · python · bokeh · anyplot.ai",
    x_range=list(df.columns),
    y_range=list(reversed(df.index)),  # first class at the top
    x_axis_label=PRED_LABEL,
    y_axis_label=TRUE_LABEL,
    tools="",
    toolbar_location=None,
    min_border_left=190,
    min_border_right=60,
    min_border_top=120,
    min_border_bottom=170,
)

p.rect(
    x=PRED_LABEL,
    y=TRUE_LABEL,
    width=1,
    height=1,
    source=source,
    fill_color=transform(COUNT, mapper),
    line_color=PAGE_BG,
    line_width=4,
)

labels = LabelSet(
    x=PRED_LABEL,
    y=TRUE_LABEL,
    text="text",
    text_color="text_color",
    text_font_size="38pt",
    text_font_style="bold",
    text_align="center",
    text_baseline="middle",
    source=source,
)
p.add_layout(labels)

# Style
p.title.text_font_size = "44pt"
p.title.text_font_style = "bold"
p.title.align = "center"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "36pt"
p.yaxis.axis_label_text_font_size = "36pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "30pt"
p.yaxis.major_label_text_font_size = "30pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_width = 2
p.yaxis.major_tick_line_width = 2

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = None

color_bar = ColorBar(
    color_mapper=mapper,
    title=COUNT,
    title_text_font_size="30pt",
    title_text_color=INK,
    major_label_text_font_size="26pt",
    major_label_text_color=INK_SOFT,
    label_standoff=14,
    bar_line_color=INK_SOFT,
    bar_line_width=2,
    major_tick_line_color=INK_SOFT,
    width=36,
    padding=30,
    background_fill_color=PAGE_BG,
)
p.add_layout(color_bar, "right")

# Save interactive HTML, then screenshot it with headless Chrome
output_file(f"plot-{THEME}.html")
save(p)

W, H = 2400, 2400
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
