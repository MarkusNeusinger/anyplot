"""anyplot.ai
precision-recall: Precision-Recall Curve
Library: pygal 3.1.0 | Python 3.13.13
Quality: 90/100 | Updated: 2026-05-10
"""

import os

import pandas as pd
import pygal
from pygal.style import Style
from sklearn.datasets import make_classification
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import average_precision_score, precision_recall_curve
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
Y_TRUE = "Actual class"  # role: y_true
SCORES = ["SVM", "Gradient Boosting"]  # role: y_scores

# Data: replace this block with your own table, for example df = pd.read_csv("predictions.csv")
X, y = make_classification(
    n_samples=2000,
    n_features=20,
    n_informative=10,
    n_redundant=5,
    n_classes=2,
    weights=[0.5, 0.5],
    flip_y=0.05,
    random_state=42,
)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
svm_model = SVC(kernel="rbf", probability=True, random_state=42, gamma="scale").fit(X_train, y_train)
gb_model = GradientBoostingClassifier(n_estimators=50, max_depth=5, random_state=42).fit(X_train, y_train)
df = pd.DataFrame(
    {Y_TRUE: y_test, SCORES[0]: svm_model.predict_proba(X_test)[:, 1], SCORES[1]: gb_model.predict_proba(X_test)[:, 1]}
)

# Plot: reads only df and the constants above
table = df.dropna()  # a missing label or score drops that sample instead of being filled
positive = (table[Y_TRUE] > table[Y_TRUE].min()).astype(int)  # the higher label is the positive class
baseline = positive.mean()  # a random classifier's precision equals the positive class ratio

TICKS = [0, 0.2, 0.4, 0.6, 0.8, 1.0]  # fixed 0-1 domain of both axes
chart_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=tuple(IMPRINT_PALETTE),
    title_font_size=66,
    label_font_size=56,
    major_label_font_size=44,
    legend_font_size=44,
    value_font_size=36,
    stroke_width=5,
)

chart = pygal.XY(
    width=3200,
    height=1800,
    title="precision-recall · python · pygal · anyplot.ai",
    x_title="Recall",
    y_title="Precision",
    style=chart_style,
    show_dots=False,
    show_x_guides=True,
    show_y_guides=True,
    legend_at_bottom=True,
    legend_at_bottom_columns=3,
    truncate_legend=-1,
    range=(0, 1),
    xrange=(0, 1),
    x_labels=TICKS,
    x_labels_major=TICKS,
    y_labels=TICKS,
    y_labels_major=TICKS,
    show_minor_x_labels=False,
    show_minor_y_labels=False,
)

for name in SCORES:
    precision, recall, _ = precision_recall_curve(positive, table[name])
    ap = average_precision_score(positive, table[name])
    # Stepped line: hold the previous precision until the next threshold's recall
    points = [(float(recall[0]), float(precision[0]))]
    for i in range(1, len(recall)):
        points.append((float(recall[i]), float(precision[i - 1])))
        points.append((float(recall[i]), float(precision[i])))
    chart.add(f"{name} (AP={ap:.3f})", points)

chart.add(
    f"Random baseline ({baseline:.2f})", [(0, baseline), (1, baseline)], stroke_style={"width": 4, "dasharray": "24,14"}
)

# Output
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
