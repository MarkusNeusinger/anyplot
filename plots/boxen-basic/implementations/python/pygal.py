""" anyplot.ai
boxen-basic: Basic Boxen Plot (Letter-Value Plot)
Library: pygal 3.1.0 | Python 3.13.13
Quality: 61/100 | Created: 2026-05-17
"""

import importlib
import os
import sys

import numpy as np


script_dir = sys.path[0]
sys.path.pop(0)
pygal = importlib.import_module("pygal")
Style = importlib.import_module("pygal.style").Style
sys.path.insert(0, script_dir)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

np.random.seed(42)
endpoints = ["API-Auth", "API-Search", "API-Report", "API-Download"]

api_auth = np.concatenate([np.random.gamma(shape=2, scale=20, size=3500), np.random.uniform(200, 1000, size=200)])

api_search = np.concatenate([np.random.gamma(shape=1.5, scale=30, size=3500), np.random.uniform(300, 1200, size=200)])

api_report = np.concatenate([np.random.gamma(shape=2.5, scale=25, size=3500), np.random.uniform(250, 900, size=200)])

api_download = np.concatenate([np.random.gamma(shape=2, scale=35, size=3500), np.random.uniform(400, 1500, size=200)])

datasets = [api_auth, api_search, api_report, api_download]


def get_letter_values(data):
    """Calculate letter values at multiple quantile levels"""
    quantiles = {
        "sixteenths": (np.percentile(data, 6.25), np.percentile(data, 93.75)),
        "eighths": (np.percentile(data, 12.5), np.percentile(data, 87.5)),
        "quartiles": (np.percentile(data, 25), np.percentile(data, 75)),
        "median": (np.percentile(data, 50), np.percentile(data, 50)),
    }
    return quantiles


def get_outliers(data):
    """Get points beyond sixteenths"""
    q_lower = np.percentile(data, 6.25)
    q_upper = np.percentile(data, 93.75)
    return data[(data < q_lower) | (data > q_upper)].tolist()


custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=18,
    major_label_font_size=16,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

boxen_chart = pygal.XY(
    title="boxen-basic · pygal · anyplot.ai",
    x_title="Endpoint",
    y_title="Response Time (ms)",
    width=4800,
    height=2700,
    style=custom_style,
    show_legend=True,
    range=(0, 1200),
    show_dots=True,
    dots_size=6,
)

for endpoint_idx, endpoint in enumerate(endpoints):
    data = datasets[endpoint_idx]
    lv = get_letter_values(data)

    # Add data points for each letter value level to create nested boxes
    # Sixteenths - outermost box
    s_lower, s_upper = lv["sixteenths"]
    boxen_chart.add(f"{endpoint}: Sixteenths", [(endpoint_idx, s_lower), (endpoint_idx, s_upper)], stroke_width=2)

    # Eighths - middle outer box
    e_lower, e_upper = lv["eighths"]
    boxen_chart.add(f"{endpoint}: Eighths", [(endpoint_idx, e_lower), (endpoint_idx, e_upper)], stroke_width=2)

    # Quartiles - middle inner box (IQR)
    q_lower, q_upper = lv["quartiles"]
    boxen_chart.add(f"{endpoint}: Quartiles", [(endpoint_idx, q_lower), (endpoint_idx, q_upper)], stroke_width=4)

    # Median - innermost
    m_val = lv["median"][0]
    boxen_chart.add(f"{endpoint}: Median", [(endpoint_idx, m_val)], stroke_width=6)

    # Outliers
    outliers = get_outliers(data)
    if outliers:
        outlier_x = [endpoint_idx + np.random.normal(0, 0.06) for _ in outliers]
        outlier_points = list(zip(outlier_x, outliers, strict=False))
        boxen_chart.add(f"{endpoint}: Outliers", outlier_points, dots_size=4)

boxen_chart.x_labels = endpoints

boxen_chart.render_to_png(f"plot-{THEME}.png")

with open(f"plot-{THEME}.html", "wb") as f:
    f.write(boxen_chart.render())
