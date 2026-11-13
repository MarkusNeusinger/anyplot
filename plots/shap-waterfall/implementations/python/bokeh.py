"""anyplot.ai
shap-waterfall: SHAP Waterfall Plot for Feature Attribution
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 85/100 | Updated: 2026-11-13
"""

import os
import sys
import time
from pathlib import Path


# Prevent this file from shadowing the bokeh package
_this_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _this_dir and p != ""]

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Range1d, Span
from bokeh.plotting import figure
from bokeh.resources import INLINE
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette, canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
POS_COLOR = IMPRINT_PALETTE[4]  # red — positive SHAP (pushes prediction up)
NEG_COLOR = IMPRINT_PALETTE[2]  # blue — negative SHAP (pushes prediction down)
LABEL_INK = "#F0EFE8"  # near-white for text on colored bar segments

# Columns: set these to your table's column names
FEATURE = "Feature"  # role: feature
SHAP_VALUE = "SHAP value"  # role: shap_value
BASE_VALUE = "Base value"  # role: base_value

# Data: replace this block with your own table, for example df = pd.read_csv("shap.csv")
# Credit default risk model: explaining one loan applicant's prediction
df = pd.DataFrame(
    {
        FEATURE: [
            "Credit Score (715)",
            "Debt-to-Income Ratio",
            "Monthly Income",
            "Late Payments (2)",
            "Employment Duration",
            "Loan Amount",
            "Savings Balance",
            "Credit History Age",
            "Credit Inquiries (3)",
            "Credit Cards Count",
            "Housing (Renter)",
            "Education Level",
        ],
        SHAP_VALUE: [-0.18, 0.15, -0.12, 0.11, -0.08, 0.07, -0.05, -0.04, 0.04, 0.03, 0.02, -0.02],
        BASE_VALUE: [0.35] * 12,
    }
)

# Plot: reads only df and the constants above
# Features sorted by |SHAP| so the largest contribution sits at the top
df = df.reindex(df[SHAP_VALUE].abs().sort_values(ascending=False, kind="stable").index).reset_index(drop=True)
base_value = df[BASE_VALUE].iloc[0]
ends = base_value + df[SHAP_VALUE].cumsum()
starts = ends.shift(fill_value=base_value)
final_value = ends.iloc[-1]

df["left"] = pd.concat([starts, ends], axis=1).min(axis=1)
df["right"] = pd.concat([starts, ends], axis=1).max(axis=1)
df["mid"] = (df["left"] + df["right"]) / 2
df["end"] = ends
df["color"] = [POS_COLOR if v > 0 else NEG_COLOR for v in df[SHAP_VALUE]]
df["label"] = [f"{v:+.2f}" for v in df[SHAP_VALUE]]
source = ColumnDataSource(df)

features = list(df[FEATURE])
span = df["right"].max() - df["left"].min()
x_low = df["left"].min() - 0.06 * span
x_high = df["right"].max() + 0.30 * span  # room for the base value label right of its line

p = figure(
    width=3200,
    height=1800,
    # Reversed: bokeh puts the first factor at the bottom
    y_range=list(reversed(features)),
    x_range=Range1d(x_low, x_high),
    title="Credit Default Risk · shap-waterfall · python · bokeh · anyplot.ai",
    toolbar_location=None,
    x_axis_label="Cumulative Default Probability",
    min_border_bottom=150,
    min_border_left=40,
    min_border_top=110,
    min_border_right=60,
)
p.y_range.range_padding = 0.25  # headroom above the first bar for the reference labels

# Waterfall bars
p.hbar(y=FEATURE, left="left", right="right", height=0.62, color="color", alpha=0.9, source=source)

# Connector lines: vertical dashed segments from each bar end to the next bar
p.segment(
    x0="end",
    y0=FEATURE,
    x1="end",
    y1="next_feature",
    line_color=INK_SOFT,
    line_dash="dashed",
    line_width=2,
    line_alpha=0.7,
    source=ColumnDataSource(df.iloc[:-1].assign(next_feature=features[1:])),
)

# SHAP value labels centered on the bars
p.text(
    x="mid",
    y=FEATURE,
    text="label",
    text_align="center",
    text_baseline="middle",
    text_font_size="28pt",
    text_color=LABEL_INK,
    text_font_style="bold",
    source=source,
)

# Reference lines for base value and final prediction
p.add_layout(
    Span(location=base_value, dimension="height", line_color=INK_SOFT, line_dash="dashed", line_width=4, line_alpha=0.8)
)
p.add_layout(Span(location=final_value, dimension="height", line_color=INK, line_dash="solid", line_width=4))

# Reference labels in the empty headroom above the first bar: base to the right of its line,
# final prediction to the left of its line (bokeh y_offset: negative moves up)
p.text(
    x=[base_value],
    y=[features[0]],
    text=[f"Base value: {base_value:.2f}"],
    x_offset=12,
    y_offset=-70,
    text_align="left",
    text_font_size="28pt",
    text_color=INK_SOFT,
)
p.text(
    x=[final_value],
    y=[features[0]],
    text=[f"Prediction: {final_value:.2f}"],
    x_offset=-12,
    y_offset=-70,
    text_align="right",
    text_font_size="28pt",
    text_color=INK,
    text_font_style="bold",
)

# Theme-adaptive chrome
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = None

p.title.text_font_size = "50pt"
p.title.text_color = INK
p.title.text_font_style = "bold"

p.xaxis.axis_label_text_font_size = "42pt"
p.xaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "34pt"
p.xaxis.major_label_text_color = INK_SOFT
p.xaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.xaxis.minor_tick_line_color = None

p.yaxis.major_label_text_font_size = "30pt"
p.yaxis.major_label_text_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.yaxis.major_tick_line_color = None

p.xgrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_color = None

# Save HTML and take PNG screenshot with headless Chrome
output_file(f"plot-{THEME}.html")
save(p, resources=INLINE)

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
time.sleep(4)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
