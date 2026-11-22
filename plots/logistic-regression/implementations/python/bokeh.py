"""anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: pending | Updated: 2026-05-18
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Label, Span
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per group in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Constants
THRESHOLD = 0.5  # default decision threshold of a binary classifier
Z_95 = 1.96  # two-sided 95 % normal quantile

# Columns: set these to your table's column names
TEST_SCORE = "Test Score"  # role: x
PASSED = "Passed"  # role: y
PROBABILITY = "Fitted probability"  # role: probability
CI_LOWER = "CI lower"  # role: ci_lower
CI_UPPER = "CI upper"  # role: ci_upper

# Data: replace this block with your own table, for example df = pd.read_csv("exam.csv")
X, y = make_classification(
    n_samples=200, n_features=1, n_informative=1, n_redundant=0, n_clusters_per_class=1, flip_y=0.1, random_state=42
)
score = X.flatten()
df = pd.DataFrame({TEST_SCORE: (score - score.min()) / (score.max() - score.min()) * 60 + 20, PASSED: y})

# Plot: reads only df and the constants above
df = df.dropna(subset=[TEST_SCORE, PASSED])
x = df[TEST_SCORE].to_numpy(dtype=float)
outcome = df[PASSED].to_numpy(dtype=float)
classes = sorted(df[PASSED].unique())

# Fit the model and a Wald 95 % band on the logit scale (delta method)
model = LogisticRegression(C=1e6)
model.fit(x.reshape(-1, 1), outcome)
x_curve = np.linspace(x.min() - 2, x.max() + 2, 300)
design = np.column_stack([np.ones_like(x_curve), x_curve])
beta = np.array([model.intercept_[0], model.coef_[0, 0]])
design_fit = np.column_stack([np.ones_like(x), x])
p_fit = 1 / (1 + np.exp(-design_fit @ beta))
cov = np.linalg.inv(design_fit.T @ (design_fit * (p_fit * (1 - p_fit))[:, None]))
logit = design @ beta
logit_se = np.sqrt(np.einsum("ij,jk,ik->i", design, cov, design))
curve = pd.DataFrame(
    {
        TEST_SCORE: x_curve,
        PROBABILITY: 1 / (1 + np.exp(-logit)),
        CI_LOWER: 1 / (1 + np.exp(-(logit - Z_95 * logit_se))),
        CI_UPPER: 1 / (1 + np.exp(-(logit + Z_95 * logit_se))),
    }
)
source_curve = ColumnDataSource(curve)

# Jitter the binary outcome along y only, so the classes stay readable
jitter = np.random.default_rng(42).uniform(-0.03, 0.03, len(df))
df = df.assign(jittered=outcome + jitter)
accuracy = model.score(x.reshape(-1, 1), outcome)

p = figure(
    width=3200,
    height=1800,
    title="logistic-regression · python · bokeh · anyplot.ai",
    x_axis_label=TEST_SCORE,
    y_axis_label="Probability of Passing",
    x_range=(x.min() - 5, x.max() + 5),
    y_range=(-0.08, 1.08),
    toolbar_location=None,
    min_border_bottom=160,
    min_border_left=180,
    min_border_top=110,
    min_border_right=50,
)

# 95 % confidence band
p.varea(
    x=TEST_SCORE,
    y1=CI_LOWER,
    y2=CI_UPPER,
    source=source_curve,
    fill_color=IMPRINT_PALETTE[0],
    fill_alpha=0.25,
    legend_label="95% CI",
)

# Observations per class
class_names = {0: "Class 0 (Failed)", 1: "Class 1 (Passed)"}
for i, cls in enumerate(classes):
    p.scatter(
        x=TEST_SCORE,
        y="jittered",
        source=ColumnDataSource(df[df[PASSED] == cls]),
        size=22,
        fill_color=IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)],
        fill_alpha=0.6,
        line_color=PAGE_BG,
        line_width=2,
        legend_label=class_names.get(int(cls), f"Class {cls}"),
    )

# Fitted curve on top of band and points
p.line(
    x=TEST_SCORE,
    y=PROBABILITY,
    source=source_curve,
    line_color=IMPRINT_PALETTE[0],
    line_width=7,
    legend_label="Logistic Curve",
)

# Decision threshold
p.add_layout(Span(location=THRESHOLD, dimension="width", line_color=INK_SOFT, line_width=4, line_dash="dashed"))
p.add_layout(
    Label(
        x=x.max() + 4,
        y=THRESHOLD + 0.03,
        text=f"Decision Threshold (p={THRESHOLD})",
        text_font_size="30pt",
        text_color=INK_SOFT,
        text_align="right",
    )
)

# Model accuracy annotation
p.add_layout(
    Label(
        x=x.min() - 4,
        y=THRESHOLD + 0.22,
        text=f"Model Accuracy: {accuracy:.1%}",
        text_font_size="34pt",
        text_color=INK,
        text_font_style="bold",
    )
)

# Style
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
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.legend.location = "center_left"
p.legend.label_text_font_size = "30pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.spacing = 12
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = INK_SOFT
p.legend.padding = 18

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

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
