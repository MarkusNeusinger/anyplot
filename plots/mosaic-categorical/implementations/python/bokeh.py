"""anyplot.ai
mosaic-categorical: Mosaic Plot for Categorical Association Analysis
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-19
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
CELL_TEXT = "#FFFDF6"
GAP = 0.015

CLASS = "Passenger Class"  # role: category_1
SURVIVAL = "Outcome"  # role: category_2
COUNT = "Passengers"  # role: frequency

# Data - Titanic survival data (class vs survival)
df = pd.DataFrame(
    {
        CLASS: ["First", "First", "Second", "Second", "Third", "Third"],
        SURVIVAL: ["Survived", "Did Not Survive", "Survived", "Did Not Survive", "Survived", "Did Not Survive"],
        COUNT: [203, 122, 118, 167, 178, 528],
    }
)

# Plot
classes = list(df[CLASS].unique())
outcomes = list(df[SURVIVAL].unique())
outcome_color = {o: IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)] for i, o in enumerate(outcomes)}
total = df[COUNT].sum()

plot_width = 0.90
mosaic_bottom = 0.12
mosaic_height = 0.75

# Build mosaic rectangles and class labels in one pass over the columns
rows = []
column_centers = []
x_start = 0.05
for cls in classes:
    cls_df = df[df[CLASS] == cls]
    cls_total = cls_df[COUNT].sum()
    cls_span = cls_total / total * plot_width
    left, right = x_start, x_start + cls_span - GAP
    column_centers.append((cls, (left + right) / 2))

    y_start = mosaic_bottom
    for outcome in outcomes:
        count = cls_df.loc[cls_df[SURVIVAL] == outcome, COUNT].sum()
        span = count / cls_total * mosaic_height
        rows.append(
            {
                "left": left,
                "right": right,
                "bottom": y_start,
                "top": y_start + span - GAP / 2,
                "color": outcome_color[outcome],
                "cls": cls,
                "outcome": outcome,
                "count": int(count),
                "pct": f"{count / cls_total * 100:.1f}%",
            }
        )
        y_start += span
    x_start += cls_span

source = ColumnDataSource(pd.DataFrame(rows))

# Figure
p = figure(
    width=3200,
    height=1800,
    title="mosaic-categorical · python · bokeh · anyplot.ai",
    x_range=(0, 1),
    y_range=(0, 1),
    tools="",
    toolbar_location=None,
)

# Mosaic rectangles
quads = p.quad(
    left="left",
    right="right",
    bottom="bottom",
    top="top",
    source=source,
    color="color",
    line_color=PAGE_BG,
    line_width=3,
    alpha=0.9,
)

# HoverTool for interactivity
p.add_tools(
    HoverTool(
        renderers=[quads], tooltips=[(CLASS, "@cls"), (SURVIVAL, "@outcome"), (COUNT, "@count"), ("Proportion", "@pct")]
    )
)

# Count labels inside each rectangle
for r in rows:
    p.add_layout(
        Label(
            x=(r["left"] + r["right"]) / 2,
            y=(r["bottom"] + r["top"]) / 2,
            text=str(r["count"]),
            text_align="center",
            text_baseline="middle",
            text_font_size="32pt",
            text_font_style="bold",
            text_color=CELL_TEXT,
        )
    )

# Class labels at bottom of each column
for cls, cx in column_centers:
    p.add_layout(
        Label(
            x=cx,
            y=0.07,
            text=cls,
            text_align="center",
            text_baseline="middle",
            text_font_size="30pt",
            text_font_style="bold",
            text_color=INK,
        )
    )

# X-axis description
p.add_layout(
    Label(
        x=0.5,
        y=0.02,
        text=f"{CLASS}  (column width ∝ share of total passengers)",
        text_align="center",
        text_baseline="bottom",
        text_font_size="22pt",
        text_color=INK_SOFT,
    )
)

# Centered legend, one swatch per outcome
legend_y = 0.905
legend_x = [0.38 + 0.20 * i for i in range(len(outcomes))]
for outcome, lx in zip(outcomes, legend_x, strict=True):
    p.quad(
        left=[lx - 0.015],
        right=[lx + 0.015],
        bottom=[legend_y - 0.018],
        top=[legend_y + 0.018],
        color=outcome_color[outcome],
        line_color=PAGE_BG,
        line_width=2,
    )
    p.add_layout(
        Label(
            x=lx + 0.025,
            y=legend_y,
            text=outcome,
            text_align="left",
            text_baseline="middle",
            text_font_size="24pt",
            text_color=INK_SOFT,
        )
    )

# Subtitle
p.add_layout(
    Label(
        x=0.5,
        y=0.97,
        text="Titanic Survival by Passenger Class",
        text_align="center",
        text_baseline="top",
        text_font_size="28pt",
        text_font_style="italic",
        text_color=INK_SOFT,
    )
)

# Style
p.title.text_font_size = "40pt"
p.title.text_font_style = "bold"
p.title.align = "center"
p.title.text_color = INK

p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome via Selenium
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
