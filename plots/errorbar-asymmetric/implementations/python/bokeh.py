"""anyplot.ai
errorbar-asymmetric: Asymmetric Error Bars Plot
Library: bokeh 3.10.1 | Python 3.14.10
Quality: 85/100 | Updated: 2026-11-09
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Range1d, TeeHead, Whisker
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens (see prompts/default-style-guide.md "Background" + "Theme-adaptive Chrome")
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"  # Imprint palette position 1 — a single-series plot uses it alone

# Columns: set these to your table's column names
QUARTER = "Quarter"  # role: x
REVENUE = "Revenue forecast ($ millions)"  # role: y
ERROR_LOWER = "Downside to 10th percentile ($ millions)"  # role: error_lower
ERROR_UPPER = "Upside to 90th percentile ($ millions)"  # role: error_upper

# Data: replace this block with your own table, for example df = pd.read_csv("forecast.csv")
# Quarterly median revenue forecasts; downside risk is larger than upside potential
df = pd.DataFrame(
    {
        QUARTER: ["Q1 2024", "Q2 2024", "Q3 2024", "Q4 2024", "Q1 2025", "Q2 2025"],
        REVENUE: [12.5, 14.2, 13.8, 16.5, 15.0, 17.8],
        ERROR_LOWER: [2.5, 3.0, 2.2, 4.0, 2.8, 3.5],
        ERROR_UPPER: [1.5, 2.0, 1.8, 2.5, 2.0, 2.8],
    }
)

# Plot: reads only df and the constants above
plot_df = df.dropna(subset=[QUARTER]).astype({QUARTER: str})
plot_df["lower"] = plot_df[REVENUE] - plot_df[ERROR_LOWER]
plot_df["upper"] = plot_df[REVENUE] + plot_df[ERROR_UPPER]
source = ColumnDataSource(plot_df)

low, high = plot_df["lower"].min(), plot_df["upper"].max()
pad = (high - low) * 0.08

p = figure(
    width=3200,
    height=1800,
    x_range=list(plot_df[QUARTER].unique()),
    y_range=Range1d(low - pad, high + pad),
    title="errorbar-asymmetric · python · bokeh · anyplot.ai",
    x_axis_label=QUARTER,
    y_axis_label=REVENUE,
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# Asymmetric error bars: each arm reaches its own bound, capped at both ends
cap = {"size": 70, "line_color": INK_SOFT, "line_width": 6}
p.add_layout(
    Whisker(
        source=source,
        base=QUARTER,
        lower="lower",
        upper="upper",
        line_color=INK_SOFT,
        line_width=6,
        lower_head=TeeHead(**cap),
        upper_head=TeeHead(**cap),
    )
)

p.scatter(
    x=QUARTER,
    y=REVENUE,
    source=source,
    size=40,
    color=BRAND,
    line_color=PAGE_BG,
    line_width=4,
    legend_label="Median forecast · bars span 10th–90th percentile",
)

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "50pt"
p.title.text_font_style = "bold"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.axis_label_text_font_style = "normal"
p.yaxis.axis_label_text_font_style = "normal"
p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 2
p.yaxis.axis_line_width = 2
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.15

p.legend.location = "top_left"
p.legend.label_text_font_size = "34pt"
p.legend.label_text_color = INK_SOFT
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = INK_SOFT
p.legend.border_line_alpha = 0.4
# Bokeh draws legend markers at 0.4x the glyph box, so 100 px matches the 40 px plotted markers
p.legend.glyph_width = 100
p.legend.glyph_height = 100
p.legend.padding = 24
p.legend.margin = 40

# Save: interactive HTML, then a headless-Chrome screenshot at the exact canvas size
output_file(f"plot-{THEME}.html")
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
