"""anyplot.ai
histogram-returns-distribution: Returns Distribution Histogram
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-20
"""

import os
import sys
import time
from pathlib import Path


# Remove the current directory from sys.path to avoid shadowing the bokeh package
sys.path = [p for p in sys.path if p not in ("", ".", os.getcwd(), os.path.dirname(__file__))]

import numpy as np  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import BoxAnnotation, ColumnDataSource, HoverTool, Label  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data
np.random.seed(42)
n_days = 252
daily_returns = np.random.normal(loc=0.0005, scale=0.015, size=n_days) * 100

mean_return = np.mean(daily_returns)
std_return = np.std(daily_returns)
n = len(daily_returns)
skewness = np.sum(((daily_returns - mean_return) / std_return) ** 3) / n
kurtosis = np.sum(((daily_returns - mean_return) / std_return) ** 4) / n - 3

n_bins = 30
hist, edges = np.histogram(daily_returns, bins=n_bins, density=True)

x_norm = np.linspace(daily_returns.min() - std_return, daily_returns.max() + std_return, 200)
y_norm = (1 / (std_return * np.sqrt(2 * np.pi))) * np.exp(-0.5 * ((x_norm - mean_return) / std_return) ** 2)

lower_tail = mean_return - 2 * std_return
upper_tail = mean_return + 2 * std_return

bar_colors = [
    "#D55E00" if (edges[i] < lower_tail or edges[i + 1] > upper_tail) else "#009E73" for i in range(len(hist))
]

hist_source = ColumnDataSource(
    data={
        "top": hist,
        "left": edges[:-1],
        "right": edges[1:],
        "bottom": [0] * len(hist),
        "color": bar_colors,
        "bin_left": [f"{edges[i]:.2f}" for i in range(len(hist))],
        "bin_right": [f"{edges[i + 1]:.2f}" for i in range(len(hist))],
        "density": [f"{h:.4f}" for h in hist],
    }
)

norm_source = ColumnDataSource(data={"x": x_norm, "y": y_norm})

# Plot
p = figure(
    width=3200,
    height=1800,
    title="histogram-returns-distribution · python · bokeh · anyplot.ai",
    x_axis_label="Daily Returns (%)",
    y_axis_label="Density",
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

p.add_layout(BoxAnnotation(right=lower_tail, fill_alpha=0.10, fill_color="#D55E00"))
p.add_layout(BoxAnnotation(left=upper_tail, fill_alpha=0.10, fill_color="#D55E00"))

bars = p.quad(
    top="top",
    bottom="bottom",
    left="left",
    right="right",
    fill_color="color",
    line_color=PAGE_BG,
    fill_alpha=0.80,
    line_width=1,
    source=hist_source,
)

hover = HoverTool(renderers=[bars], tooltips=[("Range", "@bin_left% – @bin_right%"), ("Density", "@density")])
p.add_tools(hover)

p.line(x="x", y="y", source=norm_source, line_color="#0072B2", line_width=5, legend_label="Normal Distribution")

stats_text = f"Mean: {mean_return:.3f}%\nStd Dev: {std_return:.3f}%\nSkewness: {skewness:.3f}\nKurtosis: {kurtosis:.3f}"
stats_label = Label(
    x=210,
    y=1180,
    x_units="screen",
    y_units="screen",
    text=stats_text,
    text_font_size="30pt",
    text_color=INK,
    background_fill_color=ELEVATED_BG,
    background_fill_alpha=0.90,
    border_line_color=INK_SOFT,
    border_line_width=2,
)
p.add_layout(stats_label)

# Style
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "50pt"
p.title.text_color = INK

p.xaxis.axis_label_text_font_size = "42pt"
p.yaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK

p.xaxis.major_label_text_font_size = "34pt"
p.yaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

p.xgrid.grid_line_color = None
p.ygrid.grid_line_color = INK
p.ygrid.grid_line_alpha = 0.10

p.legend.location = "top_right"
p.legend.label_text_font_size = "34pt"
p.legend.background_fill_color = ELEVATED_BG
p.legend.border_line_color = None
p.legend.label_text_color = INK_SOFT

# Save
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
driver.execute_cdp_cmd(
    "Emulation.setDeviceMetricsOverride", {"width": W, "height": H, "deviceScaleFactor": 1, "mobile": False}
)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
