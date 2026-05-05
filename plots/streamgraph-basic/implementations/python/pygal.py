""" anyplot.ai
streamgraph-basic: Basic Stream Graph
Library: pygal 3.1.0 | Python 3.13.13
Quality: 79/100 | Updated: 2026-05-05
"""

import os
import sys


# Remove script directory from sys.path so 'import pygal' finds the installed package
_script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path = [p for p in sys.path if os.path.abspath(p) != _script_dir]

import numpy as np
import pygal
from pygal.style import Style


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

OKABE_ITO = ("#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00")

# Data: monthly streaming hours by music genre over two years
np.random.seed(42)

months = 24
month_labels = [
    "Jan 23",
    "Feb 23",
    "Mar 23",
    "Apr 23",
    "May 23",
    "Jun 23",
    "Jul 23",
    "Aug 23",
    "Sep 23",
    "Oct 23",
    "Nov 23",
    "Dec 23",
    "Jan 24",
    "Feb 24",
    "Mar 24",
    "Apr 24",
    "May 24",
    "Jun 24",
    "Jul 24",
    "Aug 24",
    "Sep 24",
    "Oct 24",
    "Nov 24",
    "Dec 24",
]
genres = ["Pop", "Rock", "Hip-Hop", "Electronic", "Jazz"]
base_values = {"Pop": 45, "Rock": 35, "Hip-Hop": 40, "Electronic": 30, "Jazz": 15}

data = {}
for genre in genres:
    base = base_values[genre]
    trend = np.linspace(0, np.random.uniform(-10, 15), months)
    seasonal = 8 * np.sin(np.linspace(0, 4 * np.pi, months) + np.random.uniform(0, 2 * np.pi))
    noise = np.random.randn(months) * 3
    values = base + trend + seasonal + noise
    values = np.maximum(values, 5)
    data[genre] = values.tolist()

# Centered baseline for streamgraph effect
data_array = np.array([data[genre] for genre in genres])
total_at_each_time = data_array.sum(axis=0)
baseline_offset = total_at_each_time / 2

y_min = -baseline_offset.max() * 1.1
y_max = baseline_offset.max() * 1.1

# Style
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=OKABE_ITO,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
    opacity=0.88,
    opacity_hover=0.95,
)

# Chart
chart = pygal.StackedLine(
    width=4800,
    height=2700,
    title="streamgraph-basic · pygal · anyplot.ai",
    x_title="Month",
    y_title="Streaming Hours (centered)",
    style=custom_style,
    fill=True,
    show_dots=False,
    show_y_guides=True,
    show_x_guides=False,
    legend_at_bottom=True,
    legend_box_size=30,
    margin=100,
    spacing=40,
    truncate_legend=-1,
    truncate_label=-1,
    interpolate="cubic",
    show_minor_x_labels=False,
    x_label_rotation=45,
    range=(y_min, y_max),
)

chart.x_labels = month_labels
chart.x_labels_major = ["Jan 23", "Jul 23", "Jan 24", "Jul 24"]

# Shift first layer to center the streamgraph around y=0
shifted_data = []
for i, genre in enumerate(genres):
    if i == 0:
        shifted_values = (np.array(data[genre]) - baseline_offset).tolist()
    else:
        shifted_values = data[genre]
    shifted_data.append((genre, shifted_values))

for genre, values in shifted_data:
    chart.add(genre, values)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
