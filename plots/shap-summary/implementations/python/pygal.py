"""anyplot.ai
shap-summary: SHAP Summary Plot
Library: pygal | Python 3.13
Quality: pending | Created: 2025-05-14
"""

import os
import sys


sys.path = [p for p in sys.path if not p.endswith("implementations/python")]  # noqa: E402

import matplotlib as mpl  # noqa: E402
import numpy as np  # noqa: E402
import pygal  # noqa: E402
from matplotlib.colors import Normalize  # noqa: E402
from pygal.style import Style  # noqa: E402


script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

np.random.seed(42)
n_samples = 200
n_features = 10

feature_names = [
    "Age",
    "Income",
    "Credit Score",
    "Debt Ratio",
    "Employment Years",
    "Savings",
    "Loan Amount",
    "Interest Rate",
    "Payment History",
    "Inquiries",
]

shap_values = np.zeros((n_samples, n_features))
feature_values = np.zeros((n_samples, n_features))

for i in range(n_features):
    shap_values[:, i] = np.random.normal(0, 0.3 + i * 0.05, n_samples)
    feature_values[:, i] = np.random.uniform(0, 1, n_samples)

importance = np.abs(shap_values).mean(axis=0)
sorted_idx = np.argsort(-importance)

shap_values = shap_values[:, sorted_idx]
feature_values = feature_values[:, sorted_idx]
feature_names = [feature_names[i] for i in sorted_idx]

custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=("#009E73",),
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    stroke_width=2,
)

chart = pygal.XY(
    style=custom_style,
    title="shap-summary · pygal · anyplot.ai",
    x_title="SHAP Value",
    y_title="Feature",
    width=4800,
    height=2700,
    show_legend=False,
    y_labels=feature_names,
)

cmap = mpl.colormaps.get_cmap("BrBG")
norm = Normalize(vmin=0, vmax=1)

for j in range(n_features):
    n_bands = 10
    for band in range(n_bands):
        band_color_value = (band + 0.5) / n_bands
        color_rgba = cmap(norm(band_color_value))
        hex_color = "#{:02x}{:02x}{:02x}".format(
            int(color_rgba[0] * 255), int(color_rgba[1] * 255), int(color_rgba[2] * 255)
        )

        points = []
        for i in range(n_samples):
            feature_val = feature_values[i, j]
            if band / n_bands <= feature_val < (band + 1) / n_bands:
                jitter = np.random.normal(0, 0.15)
                points.append((shap_values[i, j], j + jitter))

        if points:
            chart.add(f"{feature_names[j]}_band_{band}", points, show_legend=False, color=hex_color)

chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
