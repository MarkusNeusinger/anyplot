""" anyplot.ai
bar-feature-importance: Feature Importance Bar Chart
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, LabelSet, LinearColorMapper, Range1d, Whisker
from bokeh.palettes import interp_palette
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint sequential ramp (imprint_seq): brand green for the weakest feature → blue for the strongest
IMPRINT_SEQ = interp_palette(("#009E73", "#4467A3"), 256)

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
IMPORTANCE = "Importance score"  # role: importance
STD = "Std. deviation"  # role: std

# Data: replace this block with your own table, for example df = pd.read_csv("importances.csv")
df = pd.DataFrame(
    {
        FEATURE: [
            "Income",
            "Credit Score",
            "Age",
            "Employment Years",
            "Debt Ratio",
            "Num Accounts",
            "Loan Amount",
            "Education Level",
            "Num Inquiries",
            "Home Ownership",
            "Payment History",
            "Account Balance",
        ],
        IMPORTANCE: [0.185, 0.162, 0.124, 0.098, 0.089, 0.076, 0.068, 0.058, 0.052, 0.041, 0.032, 0.015],
        STD: [0.021, 0.018, 0.016, 0.012, 0.014, 0.010, 0.011, 0.009, 0.008, 0.007, 0.006, 0.005],
    }
)

# Plot: reads only df and the constants above
ranked = df.sort_values(IMPORTANCE).reset_index(drop=True)  # bokeh stacks factors bottom-up: highest lands on top
reach = np.fmax(ranked[IMPORTANCE], ranked[IMPORTANCE] + ranked[STD])  # bar end or whisker tip, whichever is further
x_max = np.nanmax(reach)
ranked["lower"] = ranked[IMPORTANCE] - ranked[STD]
ranked["upper"] = ranked[IMPORTANCE] + ranked[STD]
ranked["label_x"] = reach + x_max * 0.012
ranked["label"] = ranked[IMPORTANCE].map(lambda v: "" if pd.isna(v) else f"{v:.3f}")
source = ColumnDataSource(ranked)

color_mapper = LinearColorMapper(palette=IMPRINT_SEQ, low=ranked[IMPORTANCE].min(), high=ranked[IMPORTANCE].max())

title = "bar-feature-importance · python · bokeh · anyplot.ai"
p = figure(
    width=3200,
    height=1800,
    y_range=[str(name) for name in ranked[FEATURE]],
    x_range=Range1d(0, x_max * 1.12),
    title=title,
    x_axis_label=IMPORTANCE,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=460,  # feature names at 34pt need more room than the default 180
    min_border_top=110,
    min_border_right=50,
)

p.hbar(
    y=FEATURE,
    right=IMPORTANCE,
    left=0,
    height=0.7,
    source=source,
    fill_color={"field": IMPORTANCE, "transform": color_mapper},
    line_color=PAGE_BG,
    line_width=2,
)

# Error bars: ± one standard deviation, drawn in ink so they read against every step of the ramp
p.add_layout(
    Whisker(
        base=FEATURE,
        lower="lower",
        upper="upper",
        dimension="width",
        source=source,
        line_color=INK,
        line_width=3,
        upper_head=None,
        lower_head=None,
        level="overlay",
    )
)

p.add_layout(
    LabelSet(
        x="label_x",
        y=FEATURE,
        text="label",
        source=source,
        text_font_size="30pt",
        text_color=INK_SOFT,
        text_baseline="middle",
    )
)

# Style
p.title.text_font_size = f"{round(50 * min(1.0, 67 / len(title)))}pt"
p.title.text_color = INK
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_style = "normal"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.15
p.ygrid.grid_line_color = None

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

# Save: interactive HTML, then a headless-Chrome screenshot at the exact canvas size
output_file(f"plot-{THEME}.html", title=title)
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
