""" anyplot.ai
shap-summary: SHAP Summary Plot
Library: bokeh 3.9.0 | Python 3.13.13
Quality: 89/100 | Created: 2026-05-14
"""

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
from bokeh.models import ColumnDataSource
from bokeh.palettes import BrBG11
from bokeh.plotting import figure, output_file, save
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

np.random.seed(42)

feature_names = [
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

n_samples = 150
n_features = len(feature_names)

shap_values = np.random.normal(0, 1, (n_samples, n_features))
shap_values[:, 0] *= 1.5
shap_values[:, 1] *= 1.2
shap_values[:, 5] *= 0.8

feature_values = np.zeros((n_samples, n_features))
feature_values[:, 0] = np.random.normal(2500, 800, n_samples)
feature_values[:, 1] = np.random.normal(30, 15, n_samples)
feature_values[:, 2] = np.random.normal(3.5, 1.2, n_samples)
feature_values[:, 3] = np.random.normal(2.0, 0.8, n_samples)
feature_values[:, 4] = np.random.normal(10, 5, n_samples)
feature_values[:, 5] = np.random.normal(8000, 3000, n_samples)
feature_values[:, 6] = np.random.normal(70, 20, n_samples)
feature_values[:, 7] = np.random.normal(2.0, 0.7, n_samples)
feature_values[:, 8] = np.random.normal(500, 250, n_samples)
feature_values[:, 9] = np.random.normal(1995, 20, n_samples)

mean_abs_shap = np.abs(shap_values).mean(axis=0)
sorted_indices = np.argsort(-mean_abs_shap)
sorted_feature_names = [feature_names[i] for i in sorted_indices]
sorted_shap = shap_values[:, sorted_indices]
sorted_values = feature_values[:, sorted_indices]

data_dict = {"x": [], "y": [], "color_val": [], "feature": []}

for feature_idx, feature_name in enumerate(sorted_feature_names):
    n = len(sorted_shap[:, feature_idx])
    y_positions = np.linspace(feature_idx - 0.3, feature_idx + 0.3, n)
    np.random.shuffle(y_positions)

    data_dict["x"].extend(sorted_shap[:, feature_idx])
    data_dict["y"].extend(y_positions)
    data_dict["color_val"].extend(sorted_values[:, feature_idx])
    data_dict["feature"].extend([feature_name] * n)

df = pd.DataFrame(data_dict)
feature_min = df["color_val"].min()
feature_max = df["color_val"].max()
df["color_normalized"] = (df["color_val"] - feature_min) / (feature_max - feature_min) * 10
df["color_normalized"] = df["color_normalized"].round(0).astype(int).clip(0, 10)

color_palette_map = {
    0: BrBG11[0],
    1: BrBG11[1],
    2: BrBG11[2],
    3: BrBG11[3],
    4: BrBG11[4],
    5: BrBG11[5],
    6: BrBG11[6],
    7: BrBG11[7],
    8: BrBG11[8],
    9: BrBG11[9],
    10: BrBG11[10],
}
df["color"] = df["color_normalized"].map(color_palette_map)

source = ColumnDataSource(df)

p = figure(width=4800, height=2700, y_range=sorted_feature_names[::-1], title="shap-summary · bokeh · anyplot.ai")

p.circle(x="x", y="y", source=source, size=12, color="color", alpha=0.6, line_color=None)

p.line(x=[0, 0], y=[-1, len(sorted_feature_names)], line_width=2, color=INK_SOFT, alpha=0.5)

p.xaxis.axis_label = "SHAP Value"
p.yaxis.axis_label = "Feature"

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

p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.outline_line_color = INK_SOFT

p.xgrid.grid_line_color = INK
p.ygrid.grid_line_color = INK
p.xgrid.grid_line_alpha = 0.10
p.ygrid.grid_line_alpha = 0.10

p.xaxis.axis_line_color = INK_SOFT
p.yaxis.axis_line_color = INK_SOFT
p.xaxis.major_tick_line_color = INK_SOFT
p.yaxis.major_tick_line_color = INK_SOFT

output_file(f"plot-{THEME}.html")
save(p)

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
