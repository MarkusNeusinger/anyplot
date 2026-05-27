""" anyplot.ai
polar-scatter: Polar Scatter Plot
Library: pygal 3.1.0 | Python 3.13.13
Quality: 84/100 | Created: 2026-05-09
"""

# Ensure we import the installed pygal package, not this file
import importlib.util
import os
import sys

import numpy as np


pygal_spec = importlib.util.find_spec("pygal")
if pygal_spec and pygal_spec.origin != __file__:
    import pygal
    from pygal.style import Style
else:
    # Fallback: remove current directory from path temporarily
    cwd = os.getcwd()
    sys.path = [p for p in sys.path if os.path.abspath(p) != cwd]
    try:
        import pygal
        from pygal.style import Style
    finally:
        sys.path.insert(0, cwd)

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data: Wind observations with direction and speed
np.random.seed(42)
n_morning = 35
n_afternoon = 40
n_evening = 35

# Morning: winds from NW (around 315°)
morning_angles = np.random.normal(315, 30, n_morning) % 360
morning_speeds = np.random.uniform(6, 15, n_morning)

# Afternoon: winds from N-NE (around 45°)
afternoon_angles = np.random.normal(45, 35, n_afternoon) % 360
afternoon_speeds = np.random.uniform(8, 18, n_afternoon)

# Evening: winds from S (around 180°)
evening_angles = np.random.normal(180, 25, n_evening) % 360
evening_speeds = np.random.uniform(5, 12, n_evening)

angles = np.concatenate([morning_angles, afternoon_angles, evening_angles])
speeds = np.concatenate([morning_speeds, afternoon_speeds, evening_speeds])
categories = ["morning"] * n_morning + ["afternoon"] * n_afternoon + ["evening"] * n_evening

# Convert polar to Cartesian coordinates
radians = np.radians(angles)
x = speeds * np.cos(radians)
y = speeds * np.sin(radians)

# Create chart
custom_style = Style(
    background=PAGE_BG,
    plot_background=PAGE_BG,
    foreground=INK,
    foreground_strong=INK,
    foreground_subtle=INK_MUTED,
    colors=IMPRINT,
    title_font_size=28,
    label_font_size=22,
    major_label_font_size=18,
    legend_font_size=16,
    value_font_size=14,
    stroke_width=3,
)

chart = pygal.XY(
    style=custom_style,
    width=4800,
    height=2700,
    title="polar-scatter · pygal · anyplot.ai",
    x_title="X Component (m/s)",
    y_title="Y Component (m/s)",
    show_legend=True,
    dots_size=8,
    show_y_guides=True,
    show_x_guides=True,
    range=(-20, 20),
    stroke=False,
)

# Add data by category (reordered so first series is green #009E73)
categories_order = ["morning", "afternoon", "evening"]
for cat in categories_order:
    mask = np.array(categories) == cat
    cat_x = x[mask]
    cat_y = y[mask]
    data = [(float(cx), float(cy)) for cx, cy in zip(cat_x, cat_y, strict=False)]
    chart.add(cat.title(), data)

# Save
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
