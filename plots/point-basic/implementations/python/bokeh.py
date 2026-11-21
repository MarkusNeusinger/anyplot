"""anyplot.ai
point-basic: Point Estimate Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-11
"""

import os
import sys
import time
from pathlib import Path

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Avoid shadowing bokeh module - remove current directory from path
_original_path = sys.path.copy()
sys.path = [p for p in sys.path if p not in ("", ".", str(Path(__file__).parent))]

try:
    import bokeh.io as bk_io
    import bokeh.models as bk_models
    import bokeh.plotting as bk_plotting
finally:
    sys.path = _original_path


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
# Imprint palette: first position only (single series)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
BRAND = IMPRINT_PALETTE[0]

# Constants
NULL_VALUE = 0  # reference line: no effect

# Columns: set these to your table's column names
TREATMENT = "Treatment Group"  # role: category
EFFECT = "Effect Size"  # role: estimate
LOWER = "Lower 95% CI"  # role: lower_bound
UPPER = "Upper 95% CI"  # role: upper_bound

# Data: replace this block with your own table, for example df = pd.read_csv("effects.csv")
df = pd.DataFrame(
    {
        TREATMENT: ["Treatment A", "Treatment B", "Treatment C", "Treatment D", "Treatment E", "Control"],
        EFFECT: [2.5, 1.8, 3.2, -0.5, 1.2, 0.0],
    }
)
half_width = [0.8, 1.2, 0.6, 0.9, 1.5, 0.4]
df[LOWER] = df[EFFECT] - half_width
df[UPPER] = df[EFFECT] + half_width

# Plot: reads only df and the constants above
source = bk_models.ColumnDataSource(df)
pad = (df[UPPER].max() - df[LOWER].min()) * 0.06

p = bk_plotting.figure(
    width=3200,
    height=1800,
    y_range=list(df[TREATMENT])[::-1],
    x_range=bk_models.Range1d(min(df[LOWER].min(), NULL_VALUE) - pad, max(df[UPPER].max(), NULL_VALUE) + pad),
    title="point-basic · python · bokeh · anyplot.ai",
    x_axis_label=EFFECT,
    y_axis_label=TREATMENT,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Reference line at the null value
zero_line = bk_models.Span(
    location=NULL_VALUE, dimension="height", line_color=INK_SOFT, line_width=4, line_dash="dashed"
)
p.add_layout(zero_line)

# Interval whiskers with caps
whisker = bk_models.Whisker(
    source=source,
    base=TREATMENT,
    lower=LOWER,
    upper=UPPER,
    dimension="width",
    line_color=BRAND,
    line_width=7,
    upper_head=bk_models.TeeHead(size=44, line_color=BRAND, line_width=7),
    lower_head=bk_models.TeeHead(size=44, line_color=BRAND, line_width=7),
)
p.add_layout(whisker)

# Point estimates
p.scatter(x=EFFECT, y=TREATMENT, source=source, size=34, color=BRAND, line_width=3, line_color=PAGE_BG)

# Typography sizing
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

# Theme-adaptive colors
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

p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.0

# Save HTML
bk_io.output_file(f"plot-{THEME}.html")
bk_io.save(p)

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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
