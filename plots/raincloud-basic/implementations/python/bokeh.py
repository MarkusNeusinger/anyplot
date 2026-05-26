"""anyplot.ai
raincloud-basic: Basic Raincloud Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 81/100 | Updated: 2026-05-26
"""

import base64
import os
import time
from pathlib import Path

import numpy as np
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BOX_FILL = "#FFFDF6" if THEME == "light" else "#242420"
GRID_ALPHA = 0.15 if THEME == "light" else 0.20

ANYPLOT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data — reaction times (ms) across four experimental conditions
np.random.seed(42)
categories = ["Control", "Treatment A", "Treatment B", "Treatment C"]
n_points = [80, 75, 85, 70]
data = {
    "Control": np.random.normal(450, 80, n_points[0]),
    "Treatment A": np.random.normal(380, 60, n_points[1]),
    "Treatment B": np.concatenate(
        [np.random.normal(350, 40, n_points[2] // 2), np.random.normal(460, 45, n_points[2] - n_points[2] // 2)]
    ),
    "Treatment C": np.random.normal(320, 50, n_points[3]),
}

W, H = 3200, 1800

p = figure(
    width=W,
    height=H,
    title="raincloud-basic · python · bokeh · anyplot.ai",
    x_axis_label="Reaction Time (ms)",
    y_axis_label="Treatment Group",
    y_range=(-0.55, len(categories) - 0.30),
    x_range=(150, 650),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=220,
    min_border_top=110,
    min_border_right=80,
    tools="",
)

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
p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = None
p.xgrid.grid_line_alpha = GRID_ALPHA

p.yaxis.ticker = list(range(len(categories)))
p.yaxis.major_label_overrides = dict(enumerate(categories))

for idx, (cat, values) in enumerate(data.items()):
    color = ANYPLOT_PALETTE[idx]
    y_base = idx

    # KDE — Silverman's rule
    n = len(values)
    std = np.std(values)
    bw = 1.06 * std * n ** (-1 / 5)
    x_min, x_max = values.min() - 25, values.max() + 25
    x_kde = np.linspace(x_min, x_max, 256)
    y_kde = np.zeros_like(x_kde)
    for point in values:
        y_kde += np.exp(-0.5 * ((x_kde - point) / bw) ** 2) / (bw * np.sqrt(2 * np.pi))
    y_kde /= n
    y_kde_scaled = y_kde / y_kde.max() * 0.40

    # Cloud — half-violin above the baseline
    violin_x = np.concatenate([x_kde, x_kde[::-1]])
    violin_y = np.concatenate([y_base + y_kde_scaled, np.full(len(x_kde), y_base)])
    p.patch(x=violin_x, y=violin_y, fill_color=color, fill_alpha=0.55, line_color=color, line_width=2)

    # Box plot — sits on the baseline
    q1, q2, q3 = np.percentile(values, [25, 50, 75])
    iqr = q3 - q1
    whisker_low = max(values.min(), q1 - 1.5 * iqr)
    whisker_high = min(values.max(), q3 + 1.5 * iqr)
    box_h = 0.11

    p.line(x=[whisker_low, q1], y=[y_base, y_base], line_color=INK, line_width=3)
    p.line(x=[q3, whisker_high], y=[y_base, y_base], line_color=INK, line_width=3)
    p.line(x=[whisker_low, whisker_low], y=[y_base - box_h / 2, y_base + box_h / 2], line_color=INK, line_width=3)
    p.line(x=[whisker_high, whisker_high], y=[y_base - box_h / 2, y_base + box_h / 2], line_color=INK, line_width=3)
    p.patch(
        x=[q1, q3, q3, q1],
        y=[y_base - box_h, y_base - box_h, y_base + box_h, y_base + box_h],
        fill_color=BOX_FILL,
        fill_alpha=0.95,
        line_color=INK,
        line_width=3,
    )
    p.line(x=[q2, q2], y=[y_base - box_h, y_base + box_h], line_color=color, line_width=6)

    # Rain — jittered points below the baseline
    jitter = np.random.uniform(-0.40, -0.08, len(values))
    mean_val = float(np.mean(values))
    std_val = float(np.std(values))
    source_points = ColumnDataSource(
        data={
            "x": values,
            "y": y_base + jitter,
            "category": [cat] * len(values),
            "mean": [f"{mean_val:.1f}"] * len(values),
            "median": [f"{q2:.1f}"] * len(values),
            "std": [f"{std_val:.1f}"] * len(values),
            "n": [str(n)] * len(values),
        }
    )
    scatter_glyph = p.scatter(
        x="x",
        y="y",
        source=source_points,
        size=12,
        fill_color=color,
        fill_alpha=0.65,
        line_color=PAGE_BG,
        line_width=1.0,
    )

    hover = HoverTool(
        renderers=[scatter_glyph],
        tooltips=[
            ("Group", "@category"),
            ("Value", "@x{0.1f} ms"),
            ("Mean", "@mean ms"),
            ("Median", "@median ms"),
            ("Std", "@std ms"),
            ("n", "@n"),
        ],
        point_policy="follow_mouse",
    )
    p.add_tools(hover)

# Annotate Treatment B's bimodality — the most interesting feature of the synthetic data
p.add_layout(
    Label(
        x=475,
        y=2.35,
        text="bimodal distribution",
        text_color=INK_SOFT,
        text_font_size="28pt",
        text_font_style="italic",
        text_align="left",
        text_baseline="middle",
    )
)

# Save HTML (catalog artifact) + PNG via headless Chrome
output_file(f"plot-{THEME}.html", title="raincloud-basic · python · bokeh · anyplot.ai")
save(p)

opts = Options()
for arg in (
    "--headless=new",
    "--no-sandbox",
    "--disable-dev-shm-usage",
    "--disable-gpu",
    f"--window-size={W},{H + 200}",
    "--hide-scrollbars",
    "--force-device-scale-factor=1",
):
    opts.add_argument(arg)
driver = webdriver.Chrome(options=opts)
driver.get(f"file://{Path(f'plot-{THEME}.html').resolve()}")
time.sleep(3)

shot = driver.execute_cdp_cmd(
    "Page.captureScreenshot",
    {"clip": {"x": 0, "y": 0, "width": W, "height": H, "scale": 1}, "captureBeyondViewport": True},
)
Path(f"plot-{THEME}.png").write_bytes(base64.b64decode(shot["data"]))
driver.quit()
