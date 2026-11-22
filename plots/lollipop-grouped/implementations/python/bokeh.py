"""anyplot.ai
lollipop-grouped: Grouped Lollipop Chart
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 86/100 | Updated: 2026-05-17
"""

import os
import sys
import time
from pathlib import Path


# Keep the script's own directory off sys.path so sibling files named after libraries can't shadow them
_orig_path = sys.path[:]
sys.path = [p for p in sys.path if p not in ("", ".", os.getcwd())]

import pandas as pd  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, Range1d  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from bokeh.transform import dodge  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


sys.path = _orig_path

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette (first series is always #009E73)
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
W, H = 3200, 1800

# Columns
REGION = "Region"  # role: category
PRODUCT_LINE = "Product line"  # role: series
REVENUE = "Revenue ($ million)"  # role: value

# Data
df = pd.DataFrame(
    {
        REGION: ["North", "South", "East", "West"] * 4,
        PRODUCT_LINE: ["Electronics"] * 4 + ["Clothing"] * 4 + ["Food"] * 4 + ["Home"] * 4,
        REVENUE: [85, 72, 91, 68, 62, 78, 55, 71, 45, 52, 48, 58, 38, 41, 35, 47],
    }
)

# Plot
regions = list(df[REGION].unique())
lines = list(df[PRODUCT_LINE].unique())
step = 0.17
df["_zero"] = 0

p = figure(
    width=W,
    height=H,
    title="lollipop-grouped · python · bokeh · anyplot.ai",
    x_axis_label=REGION,
    y_axis_label=REVENUE,
    x_range=regions,
    y_range=Range1d(0, df[REVENUE].max() * 1.15),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

for i, line in enumerate(lines):
    rows = ColumnDataSource(df[df[PRODUCT_LINE] == line])
    offset = (i - (len(lines) - 1) / 2) * step
    pos = dodge(REGION, offset, range=p.x_range)
    p.segment(x0=pos, y0="_zero", x1=pos, y1=REVENUE, source=rows, line_width=6, color=IMPRINT_PALETTE[i], alpha=0.85)
    p.scatter(
        x=pos,
        y=REVENUE,
        source=rows,
        size=30,
        color=IMPRINT_PALETTE[i],
        line_color=PAGE_BG,
        line_width=3,
        legend_label=str(line),
    )

# Legend
p.legend.title = PRODUCT_LINE
p.legend.title_text_font_size = "30pt"
p.legend.title_text_color = INK
p.legend.label_text_font_size = "30pt"
p.legend.location = "top_right"
p.legend.glyph_height = 30
p.legend.glyph_width = 30
p.legend.spacing = 10
p.legend.padding = 16
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.95
p.legend.border_line_color = INK_SOFT
p.legend.label_text_color = INK_SOFT

# Text sizing for 3200x1800 px
p.title.text_font_size = "50pt"
p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None
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

# Save HTML + PNG
output_file(f"plot-{THEME}.html")
save(p)

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
