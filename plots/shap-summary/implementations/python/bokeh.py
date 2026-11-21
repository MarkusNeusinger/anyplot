"""anyplot.ai
shap-summary: SHAP Summary Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-11-21
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.models import ColorBar, ColumnDataSource, FixedTicker, LinearColorMapper, Range1d, Span
from bokeh.plotting import figure, output_file, save
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]


def lerp_hex(c0, c1, t):
    a = [int(c0[i : i + 2], 16) for i in (1, 3, 5)]
    b = [int(c1[i : i + 2], 16) for i in (1, 3, 5)]
    return "#" + "".join(f"{round(x + (y - x) * t):02X}" for x, y in zip(a, b, strict=True))


# imprint_div, low = blue to high = red; the midpoint is the page color
IMPRINT_DIV256 = [lerp_hex("#4467A3", PAGE_BG, t / 127) for t in range(128)] + [
    lerp_hex(PAGE_BG, "#AE3030", t / 127) for t in range(128)
]

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature_names
SHAP = "SHAP value (impact on predicted price)"  # role: shap_values
FEATURE_VALUE = "Feature value"  # role: feature_values

# Data: replace this block with your own table, for example df = pd.read_csv("shap.csv")
np.random.seed(42)
n_samples = 150
names = [
    "Square Footage",
    "Age (years)",
    "Bedrooms",
    "Bathrooms",
    "Distance to Center",
    "Lot Size",
    "Condition Score",
    "Parking Spaces",
    "Garage Size",
    "Year Built",
]
shap_matrix = np.random.normal(0, 1, (n_samples, len(names)))
shap_matrix[:, 0] *= 1.5
shap_matrix[:, 1] *= 1.2
shap_matrix[:, 5] *= 0.8
value_matrix = np.column_stack(
    [
        np.random.normal(mean, sd, n_samples)
        for mean, sd in [
            (2500, 800),
            (30, 15),
            (3.5, 1.2),
            (2.0, 0.8),
            (10, 5),
            (8000, 3000),
            (70, 20),
            (2.0, 0.7),
            (500, 250),
            (1995, 20),
        ]
    ]
)
df = pd.DataFrame(
    {FEATURE: np.repeat(names, n_samples), SHAP: shap_matrix.T.ravel(), FEATURE_VALUE: value_matrix.T.ravel()}
)

# Plot: reads only df and the constants above
importance = df.groupby(FEATURE, sort=False)[SHAP].apply(lambda s: s.abs().mean()).sort_values(ascending=False)
ranked = list(importance.index)
n_rows = len(ranked)
row_of = {name: n_rows - 1 - i for i, name in enumerate(ranked)}  # most important on top

# Vertical jitter inside each row is layout only
by_feature = df.groupby(FEATURE, sort=False)[FEATURE_VALUE]
df["relative"] = (df[FEATURE_VALUE] - by_feature.transform("min")) / (
    by_feature.transform("max") - by_feature.transform("min")
)
df["row"] = df[FEATURE].map(row_of) + np.random.uniform(-0.3, 0.3, len(df))
source = ColumnDataSource(df.rename(columns={SHAP: "shap", FEATURE_VALUE: "fvalue"}))

mapper = LinearColorMapper(palette=IMPRINT_DIV256, low=0, high=1)
span = df[SHAP].abs().max() * 1.08

p = figure(
    width=3200,
    height=1800,
    title="shap-summary · python · bokeh · anyplot.ai",
    x_axis_label=SHAP,
    y_axis_label=FEATURE,
    x_range=Range1d(-span, span),
    y_range=Range1d(-0.7, n_rows - 0.3),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=60,
)

p.scatter(
    x="shap",
    y="row",
    source=source,
    size=15,
    fill_color={"field": "relative", "transform": mapper},
    fill_alpha=0.85,
    line_color=INK_SOFT,
    line_alpha=0.55,
    line_width=1.2,
)
p.add_layout(Span(location=0, dimension="height", line_color=INK, line_width=3, line_alpha=0.6, line_dash="dashed"))

color_bar = ColorBar(
    color_mapper=mapper,
    ticker=FixedTicker(ticks=[0, 1]),
    major_label_overrides={0: "Low", 1: "High"},
    title=FEATURE_VALUE,
    title_text_font_size="30pt",
    title_text_color=INK,
    major_label_text_font_size="28pt",
    major_label_text_color=INK_SOFT,
    major_tick_line_color=None,
    bar_line_color=INK_SOFT,
    background_fill_color=PAGE_BG,
    border_line_color=None,
    width=60,
    height=700,
    padding=20,
)
p.add_layout(color_bar, "right")

# Style
p.yaxis.ticker = FixedTicker(ticks=list(row_of.values()))
p.yaxis.major_label_overrides = {row_of[name]: name for name in ranked}

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

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

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
