""" anyplot.ai
forest-basic: Meta-Analysis Forest Plot
Library: bokeh 3.10.2 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-21
"""

import os
import sys
import time
from pathlib import Path


# Remove local directory from sys.path to avoid importing local bokeh.py
sys.path = [p for p in sys.path if not p.startswith(str(Path(__file__).parent))]

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, HoverTool, Span  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
NULL_EFFECT = 0  # no difference between treatment and control (mean difference)
Z_95 = 1.96  # normal quantile of a 95 % confidence interval
POOLED = "Pooled estimate"

# Columns: set these to your table's column names
STUDY = "Study"  # role: study
EFFECT = "Mean difference in blood pressure (mmHg)"  # role: effect_size
CI_LOWER = "CI lower (mmHg)"  # role: ci_lower
CI_UPPER = "CI upper (mmHg)"  # role: ci_upper
WEIGHT = "Weight"  # role: weight

# Data: replace this block with your own table, for example df = pd.read_csv("studies.csv")
df = pd.DataFrame(
    {
        STUDY: [
            "Smith et al. 2018",
            "Johnson et al. 2019",
            "Williams et al. 2019",
            "Brown et al. 2020",
            "Davis et al. 2020",
            "Miller et al. 2021",
            "Wilson et al. 2021",
            "Moore et al. 2022",
            "Taylor et al. 2022",
            "Anderson et al. 2023",
            "Thomas et al. 2023",
            "Chen et al. 2023",
        ],
        EFFECT: [-3.2, -5.1, -2.8, -4.5, -6.2, -3.9, -4.1, -5.8, -3.5, 0.3, -2.9, -4.7],
        CI_LOWER: [-5.8, -8.2, -5.1, -7.3, -9.1, -6.5, -6.8, -8.9, -6.2, -2.5, -5.6, -7.1],
        CI_UPPER: [-0.6, -2.0, -0.5, -1.7, -3.3, -1.3, -1.4, -2.7, -0.8, 3.1, -0.2, -2.3],
        WEIGHT: [8, 12, 6, 15, 10, 9, 11, 14, 7, 9, 5, 11],
    }
)

# Plot: reads only df and the constants above
n = len(df)
studies = df.assign(y=np.arange(n, 0, -1))  # first study on top, pooled row below the last
studies["cap_low"] = studies["y"] - 0.17
studies["cap_high"] = studies["y"] + 0.17

# Inverse-variance pooled estimate (fixed effect) computed from the study intervals
se = (df[CI_UPPER] - df[CI_LOWER]) / (2 * Z_95)
inv_var = 1 / se**2
pooled_effect = float((df[EFFECT] * inv_var).sum() / inv_var.sum())
pooled_se = float(1 / np.sqrt(inv_var.sum()))
pooled_lower = pooled_effect - Z_95 * pooled_se
pooled_upper = pooled_effect + Z_95 * pooled_se
pooled_y = 0

# Marker area proportional to weight
studies["size"] = 14 * np.sqrt(df[WEIGHT] / df[WEIGHT].max()) * 2.2 + 10

x_low = min(df[CI_LOWER].min(), NULL_EFFECT)
x_high = max(df[CI_UPPER].max(), NULL_EFFECT)
pad = (x_high - x_low) * 0.05

p = figure(
    width=3200,
    height=1800,
    title="forest-basic · python · bokeh · anyplot.ai",
    x_axis_label=EFFECT,
    x_range=(x_low - pad, x_high + pad),
    y_range=(-0.9, n + 0.7),
    tools="pan,wheel_zoom,reset",
    toolbar_location=None,
    min_border_left=560,
    min_border_bottom=160,
    min_border_top=110,
    min_border_right=60,
)

# Null effect reference line through every row
p.add_layout(Span(location=NULL_EFFECT, dimension="height", line_color=INK_SOFT, line_width=4, line_dash="dashed"))

source = ColumnDataSource(studies)

# Confidence intervals with end caps
p.segment(x0=CI_LOWER, x1=CI_UPPER, y0="y", y1="y", source=source, line_width=5, line_color=IMPRINT_PALETTE[0])
for bound in (CI_LOWER, CI_UPPER):
    p.segment(
        x0=bound, x1=bound, y0="cap_low", y1="cap_high", source=source,
        line_width=4, line_color=IMPRINT_PALETTE[0],
    )  # fmt: skip

# Study markers, sized by weight
markers = p.scatter(x=EFFECT, y="y", source=source, size="size", marker="square", color=IMPRINT_PALETTE[0])
p.add_tools(
    HoverTool(
        renderers=[markers],
        tooltips=[(STUDY, f"@{{{STUDY}}}"), (EFFECT, f"@{{{EFFECT}}}{{0.0}}"), (WEIGHT, f"@{{{WEIGHT}}}")],
    )
)

# Pooled estimate: diamond in its own row, tips at the pooled interval bounds
p.patch(
    x=[pooled_lower, pooled_effect, pooled_upper, pooled_effect],
    y=[pooled_y, pooled_y + 0.32, pooled_y, pooled_y - 0.32],
    fill_color=IMPRINT_PALETTE[1],
    line_color=INK,
    line_width=3,
)

# Row labels on the y axis
p.yaxis.ticker = [*studies["y"], pooled_y]
p.yaxis.major_label_overrides = {int(y): str(s) for y, s in zip(studies["y"], df[STUDY], strict=True)} | {
    pooled_y: POOLED
}
p.yaxis.major_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.yaxis.axis_line_color = None

# Style
p.title.text_font_size = "50pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK
p.xaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_color = None
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
