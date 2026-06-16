""" anyplot.ai
precision-recall: Precision-Recall Curve
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 92/100 | Updated: 2026-05-10
"""

import os
import time
from pathlib import Path

import numpy as np
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

BRAND = "#009E73"  # Okabe-Ito position 1
ACCENT = "#C475FD"  # Okabe-Ito position 2

# Data - Generate imbalanced classification dataset
np.random.seed(42)
X, y_true = make_classification(
    n_samples=2000, n_features=20, n_informative=10, n_redundant=5, n_classes=2, weights=[0.7, 0.3], random_state=42
)

# Split into train and test for realistic evaluation
X_train, X_test, y_train, y_test = train_test_split(X, y_true, test_size=0.5, random_state=42, stratify=y_true)

# Train two classifiers for comparison
lr_model = LogisticRegression(random_state=42, max_iter=1000)
nb_model = GaussianNB()

lr_model.fit(X_train, y_train)
nb_model.fit(X_train, y_train)

# Get prediction probabilities on test set
lr_scores = lr_model.predict_proba(X_test)[:, 1]
nb_scores = nb_model.predict_proba(X_test)[:, 1]

# Calculate precision-recall curves
lr_precision, lr_recall, _ = precision_recall_curve(y_test, lr_scores)
nb_precision, nb_recall, _ = precision_recall_curve(y_test, nb_scores)

# Calculate Average Precision scores
lr_ap = average_precision_score(y_test, lr_scores)
nb_ap = average_precision_score(y_test, nb_scores)

# Baseline (random classifier) - positive class ratio
baseline = np.mean(y_test)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="precision-recall · bokeh · anyplot.ai",
    x_axis_label="Recall",
    y_axis_label="Precision",
    x_range=(-0.02, 1.05),
    y_range=(0, 1.08),
)

# Create data sources for stepped lines
lr_source = ColumnDataSource(data={"recall": lr_recall, "precision": lr_precision})
nb_source = ColumnDataSource(data={"recall": nb_recall, "precision": nb_precision})

# Plot Precision-Recall curves with step style
lr_line = p.step(x="recall", y="precision", source=lr_source, line_width=5, color=BRAND, alpha=0.9, mode="after")

nb_line = p.step(x="recall", y="precision", source=nb_source, line_width=5, color=ACCENT, alpha=0.9, mode="after")

# Baseline reference line (random classifier)
baseline_source = ColumnDataSource(data={"x": [0, 1], "y": [baseline, baseline]})
baseline_line = p.line(
    x="x", y="y", source=baseline_source, line_width=4, line_dash="dashed", color=INK_SOFT, alpha=0.6
)

# Create legend with AP scores
legend = Legend(
    items=[
        (f"Logistic Regression (AP = {lr_ap:.3f})", [lr_line]),
        (f"Naive Bayes (AP = {nb_ap:.3f})", [nb_line]),
        (f"Random Classifier (baseline = {baseline:.2f})", [baseline_line]),
    ],
    location="top_right",
    label_text_font_size="18pt",
    glyph_width=50,
    glyph_height=30,
    spacing=20,
    padding=25,
    background_fill_alpha=0.95,
    background_fill_color=ELEVATED_BG,
    border_line_color=INK_SOFT,
    border_line_width=2,
)

p.add_layout(legend)

# Style the plot
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK

# Axis styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.axis_line_width = 3
p.yaxis.axis_line_width = 3
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT
p.xaxis.major_tick_line_width = 3
p.yaxis.major_tick_line_width = 3

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT
p.outline_line_width = 2

# Min border for padding
p.min_border_left = 100
p.min_border_right = 100
p.min_border_top = 80
p.min_border_bottom = 100

# Save
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with headless Chrome
W, H = 4800, 2700
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
time.sleep(3)
driver.save_screenshot(f"plot-{THEME}.png")
driver.quit()
