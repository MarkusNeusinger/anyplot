""" pyplots.ai
histogram-epidemic: Epidemic Curve (Epi Curve)
Library: pygal 3.1.0 | Python 3.14.3
Quality: 80/100 | Created: 2026-03-05
"""

import numpy as np
import pandas as pd
import pygal
from pygal.style import Style


# Data - Simulated outbreak with two waves (propagated transmission pattern)
np.random.seed(42)
dates = pd.date_range("2024-01-15", periods=90, freq="D")

# Wave 1: peaks around day 20, Wave 2: peaks around day 55
days = np.arange(90)
wave1 = 35 * np.exp(-0.5 * ((days - 20) / 7) ** 2)
wave2 = 50 * np.exp(-0.5 * ((days - 55) / 9) ** 2)
baseline = 2 + 3 * np.random.rand(90)
total_signal = wave1 + wave2 + baseline

# Split into confirmed, probable, suspect cases
confirmed_frac = np.clip(0.6 + 0.15 * np.sin(days / 15), 0.45, 0.75)
probable_frac = np.clip(0.25 + 0.05 * np.cos(days / 10), 0.15, 0.35)
suspect_frac = 1.0 - confirmed_frac - probable_frac

confirmed = np.round(total_signal * confirmed_frac).astype(int)
probable = np.round(total_signal * probable_frac).astype(int)
suspect = np.round(total_signal * suspect_frac).astype(int)

# X-axis labels
date_labels = [d.strftime("%b %d") for d in dates]
major_labels = [d.strftime("%b %d") for i, d in enumerate(dates) if i % 7 == 0]

# Style
custom_style = Style(
    background="white",
    plot_background="white",
    foreground="#333333",
    foreground_strong="#333333",
    foreground_subtle="#cccccc",
    colors=("#306998", "#FFB347", "#E57373"),
    title_font_size=60,
    label_font_size=32,
    major_label_font_size=32,
    legend_font_size=36,
    value_font_size=28,
    tooltip_font_size=28,
    stroke_width=1,
    opacity=0.9,
    opacity_hover=1.0,
)

# Chart
chart = pygal.StackedBar(
    width=4800,
    height=2700,
    style=custom_style,
    title="Epidemic Curve (Respiratory Outbreak) \u00b7 histogram-epidemic \u00b7 pygal \u00b7 pyplots.ai",
    x_title="Date of Symptom Onset",
    y_title="New Cases",
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_box_size=30,
    margin=50,
    margin_bottom=120,
    spacing=2,
    truncate_legend=-1,
    truncate_label=-1,
    x_label_rotation=45,
    show_minor_x_labels=False,
)

chart.x_labels = date_labels
chart.x_labels_major = major_labels

# Add stacked series
chart.add("Confirmed", confirmed.tolist())
chart.add("Probable", probable.tolist())
chart.add("Suspect", suspect.tolist())

# Save
chart.render_to_png("plot.png")
chart.render_to_file("plot.html")
