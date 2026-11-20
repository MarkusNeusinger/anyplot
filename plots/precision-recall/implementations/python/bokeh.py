"""anyplot.ai
precision-recall: Precision-Recall Curve
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-10
"""

import os
import time
from pathlib import Path

import pandas as pd
from bokeh.io import output_file, save
from bokeh.models import ColumnDataSource, Legend
from bokeh.plotting import figure
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sklearn.datasets import make_classification
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.model_selection import train_test_split
from sklearn.naive_bayes import GaussianNB


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per classifier in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
Y_TRUE = "Actual class"  # role: y_true
SCORE_COLUMNS = ["Logistic Regression", "Naive Bayes"]  # role: y_scores

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
# Imbalanced binary classification (70/30), two classifiers scored on a held-out test set
X, y = make_classification(
    n_samples=2000, n_features=20, n_informative=10, n_redundant=5, n_classes=2, weights=[0.7, 0.3], random_state=42
)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.5, random_state=42, stratify=y)
lr_model = LogisticRegression(random_state=42, max_iter=1000).fit(X_train, y_train)
nb_model = GaussianNB().fit(X_train, y_train)
df = pd.DataFrame(
    {
        Y_TRUE: y_test,
        SCORE_COLUMNS[0]: lr_model.predict_proba(X_test)[:, 1],
        SCORE_COLUMNS[1]: nb_model.predict_proba(X_test)[:, 1],
    }
)

# Plot: reads only df and the constants above
baseline = (df[Y_TRUE].dropna() == df[Y_TRUE].max()).mean()  # a random classifier sits at the positive class ratio

p = figure(
    width=3200,
    height=1800,
    title="precision-recall · python · bokeh · anyplot.ai",
    x_axis_label="Recall",
    y_axis_label="Precision",
    x_range=(-0.02, 1.05),
    y_range=(0, 1.08),
    toolbar_location=None,
)

legend_items = []
for i, name in enumerate(SCORE_COLUMNS):
    rows = df[[Y_TRUE, name]].dropna()
    is_positive = (rows[Y_TRUE] == df[Y_TRUE].max()).to_numpy(dtype=int)
    scores = rows[name].to_numpy(dtype=float)
    precision, recall, _ = precision_recall_curve(is_positive, scores)
    ap = average_precision_score(is_positive, scores)
    source = ColumnDataSource(data={"recall": recall, "precision": precision})
    line = p.step(
        x="recall", y="precision", source=source, line_width=6, color=IMPRINT_PALETTE[i], alpha=0.95, mode="after"
    )
    legend_items.append((f"{name} (AP = {ap:.3f})", [line]))

# Baseline reference line (random classifier)
baseline_source = ColumnDataSource(data={"x": [0, 1], "y": [baseline, baseline]})
baseline_line = p.line(
    x="x", y="y", source=baseline_source, line_width=5, line_dash="dashed", color=INK_SOFT, alpha=0.8
)
legend_items.append((f"Random classifier (baseline = {baseline:.2f})", [baseline_line]))

legend = Legend(
    items=legend_items,
    location="top_right",
    label_text_font_size="30pt",
    label_text_color=INK_SOFT,
    glyph_width=80,
    glyph_height=40,
    spacing=16,
    padding=24,
    background_fill_alpha=0.95,
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
    border_line_width=2,
)
p.add_layout(legend)

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

p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 3
p.yaxis.axis_line_width = 3
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.major_tick_line_width = 3
p.yaxis.major_tick_line_width = 3

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.outline_line_width = 2

p.min_border_left = 180
p.min_border_right = 60
p.min_border_top = 110
p.min_border_bottom = 160

# Save
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
