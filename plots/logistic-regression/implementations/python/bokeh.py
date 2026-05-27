""" anyplot.ai
logistic-regression: Logistic Regression Curve Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Updated: 2026-05-18
"""

import os

# Remove the current directory from sys.path to avoid circular imports with bokeh.py
import sys
import time
from pathlib import Path


sys.path = [p for p in sys.path if p not in ("", ".", os.getcwd(), os.path.dirname(__file__))]

import numpy as np  # noqa: E402
from bokeh.io import output_file, save  # noqa: E402
from bokeh.models import ColumnDataSource, Label, Span  # noqa: E402
from bokeh.plotting import figure  # noqa: E402
from selenium import webdriver  # noqa: E402
from selenium.webdriver.chrome.options import Options  # noqa: E402
from sklearn.datasets import make_classification  # noqa: E402
from sklearn.linear_model import LogisticRegression  # noqa: E402


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito colors
COLOR_0 = "#009E73"  # Class 0 - bluish green (brand color)
COLOR_1 = "#C475FD"  # Class 1 - vermillion

# Data - Generate binary classification data
np.random.seed(42)
X, y = make_classification(
    n_samples=200, n_features=1, n_informative=1, n_redundant=0, n_clusters_per_class=1, flip_y=0.1, random_state=42
)
x = X.flatten()

# Scale x to meaningful range (e.g., test score 20-80)
x = (x - x.min()) / (x.max() - x.min()) * 60 + 20

# Fit logistic regression
model = LogisticRegression()
model.fit(x.reshape(-1, 1), y)

# Generate smooth curve for logistic regression
x_curve = np.linspace(x.min() - 2, x.max() + 2, 300)
prob_curve = model.predict_proba(x_curve.reshape(-1, 1))[:, 1]

# Compute confidence intervals (using asymptotic approximation)
p_val = prob_curve
se = np.sqrt(p_val * (1 - p_val) / len(x))
z = 1.96
ci_lower = np.clip(prob_curve - z * se * 3, 0, 1)
ci_upper = np.clip(prob_curve + z * se * 3, 0, 1)

# Jitter y values for visibility
jitter = np.random.uniform(-0.03, 0.03, len(y))
y_jittered = y + jitter

# Separate data by class
class_0_mask = y == 0
class_1_mask = y == 1

# Create data sources
source_class0 = ColumnDataSource(data={"x": x[class_0_mask], "y": y_jittered[class_0_mask]})
source_class1 = ColumnDataSource(data={"x": x[class_1_mask], "y": y_jittered[class_1_mask]})
source_curve = ColumnDataSource(data={"x": x_curve, "prob": prob_curve, "ci_lower": ci_lower, "ci_upper": ci_upper})

# Create figure
p = figure(
    width=4800,
    height=2700,
    title="logistic-regression · python · bokeh · anyplot.ai",
    x_axis_label="Test Score",
    y_axis_label="Probability of Passing",
    x_range=(x.min() - 5, x.max() + 5),
    y_range=(-0.08, 1.08),
)

# Confidence interval band
p.varea(
    x="x", y1="ci_lower", y2="ci_upper", source=source_curve, fill_color=COLOR_0, fill_alpha=0.15, legend_label="95% CI"
)

# Logistic curve
p.line(x="x", y="prob", source=source_curve, line_color=COLOR_0, line_width=5, legend_label="Logistic Curve")

# Data points - Class 0
p.scatter(
    x="x",
    y="y",
    source=source_class0,
    size=20,
    fill_color=COLOR_0,
    fill_alpha=0.6,
    line_color=PAGE_BG,
    line_width=2,
    legend_label="Class 0 (Failed)",
)

# Data points - Class 1
p.scatter(
    x="x",
    y="y",
    source=source_class1,
    size=20,
    fill_color=COLOR_1,
    fill_alpha=0.6,
    line_color=PAGE_BG,
    line_width=2,
    legend_label="Class 1 (Passed)",
)

# Decision threshold line at p=0.5
threshold = Span(location=0.5, dimension="width", line_color=INK_SOFT, line_width=4, line_dash="dashed")
p.add_layout(threshold)

# Add threshold label
threshold_label = Label(
    x=x.max() - 5,
    y=0.53,
    text="Decision Threshold (p=0.5)",
    text_font_size="20pt",
    text_color=INK_SOFT,
    text_align="right",
)
p.add_layout(threshold_label)

# Model accuracy annotation
accuracy = model.score(x.reshape(-1, 1), y)
accuracy_label = Label(
    x=x.min() + 2, y=0.92, text=f"Model Accuracy: {accuracy:.1%}", text_font_size="22pt", text_color=INK
)
p.add_layout(accuracy_label)

# Styling
p.title.text_font_size = "28pt"
p.title.text_color = INK
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.axis_label_text_color = INK
p.yaxis.axis_label_text_color = INK
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"
p.xaxis.major_label_text_color = INK_SOFT
p.yaxis.major_label_text_color = INK_SOFT

# Axis styling
p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

# Grid styling
p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

# Legend styling - repositioned to top-left to avoid data overlap
p.legend.location = "top_left"
p.legend.label_text_font_size = "18pt"
p.legend.label_text_color = INK_SOFT
p.legend.glyph_height = 35
p.legend.glyph_width = 35
p.legend.spacing = 12
p.legend.background_fill_color = ELEVATED_BG
p.legend.background_fill_alpha = 0.9
p.legend.border_line_color = INK_SOFT
p.legend.padding = 15

# Background
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

# Save HTML
output_file(f"plot-{THEME}.html")
save(p)

# Screenshot with Selenium
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
