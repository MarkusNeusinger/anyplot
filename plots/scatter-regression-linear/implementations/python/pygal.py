""" anyplot.ai
scatter-regression-linear: Scatter Plot with Linear Regression
Library: pygal 3.1.0 | Python 3.13.13
Quality: 82/100 | Updated: 2026-05-06
"""

import os

import numpy as np
import pygal
from pygal.style import Style
from scipy import stats


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

IMPRINT = ("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477")

# Data - Study hours vs exam scores
np.random.seed(42)
n_points = 80
x = np.random.uniform(1, 10, n_points)
y = 45 + 5 * x + np.random.normal(0, 8, n_points)

# Calculate linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
r_squared = r_value**2

# Generate regression line points
x_line = np.linspace(min(x), max(x), 100)
y_line = slope * x_line + intercept

# Calculate confidence interval (95%)
n = len(x)
x_mean = np.mean(x)
se_y = np.sqrt(np.sum((y - (slope * x + intercept)) ** 2) / (n - 2))
t_val = stats.t.ppf(0.975, n - 2)
se_line = se_y * np.sqrt(1 / n + (x_line - x_mean) ** 2 / np.sum((x - x_mean) ** 2))
ci_upper = y_line + t_val * se_line
ci_lower = y_line - t_val * se_line

# Custom style for 4800x2700 px canvas
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

# Create XY scatter chart
chart = pygal.XY(
    width=4800,
    height=2700,
    style=custom_style,
    title="scatter-regression-linear · pygal · anyplot.ai",
    x_title="Study Hours (hrs)",
    y_title="Exam Score (points)",
    show_legend=True,
    legend_at_bottom=False,
    legend_box_size=24,
    dots_size=16,
    stroke=False,
    show_x_guides=True,
    show_y_guides=True,
    truncate_legend=-1,
)

# Add scatter points
scatter_data = [{"value": (float(x[i]), float(y[i]))} for i in range(n_points)]
chart.add("Data Points", scatter_data, dots_size=16, stroke=False)

# Add confidence interval band (95%) as semi-transparent fill
ci_band_data = []
step = 3
for i in range(0, len(x_line), step):
    ci_band_data.append((float(x_line[i]), float(ci_upper[i])))
for i in range(len(x_line) - 1, -1, -step):
    ci_band_data.append((float(x_line[i]), float(ci_lower[i])))
ci_band_data.append(ci_band_data[0])

chart.add(
    "95% CI Band", ci_band_data, stroke=True, fill=True, show_dots=False, stroke_style={"width": 1, "opacity": 0.2}
)

# Add regression line (thicker, more prominent)
equation = f"y = {slope:.2f}x + {intercept:.1f}, R² = {r_squared:.3f}"
chart.add(
    "Regression Line",
    [(float(x_line[i]), float(y_line[i])) for i in range(len(x_line))],
    stroke=True,
    show_dots=False,
    stroke_style={"width": 5},
)

# Render to PNG and HTML
chart.render_to_png(f"plot-{THEME}.png")
with open(f"plot-{THEME}.html", "wb") as f:
    f.write(chart.render())
