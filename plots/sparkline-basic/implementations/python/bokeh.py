"""anyplot.ai
sparkline-basic: Basic Sparkline
Library: bokeh 3.8.1 | Python 3.13.11
Quality: 90/100 | Updated: 2026-05-02
"""

import os

import numpy as np
from bokeh.io import export_png, output_file, save
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito categorical palette — identical across themes; only chrome flips.
LINE_COLOR = "#009E73"
MIN_COLOR = "#D55E00"
MAX_COLOR = "#009E73"

# Data — daily web-traffic sessions over 60 days, with a launch bump,
# a mid-month decline, and weekend dips. Mixes ups and downs so the
# sparkline shape is informative.
np.random.seed(42)
n_points = 60
day = np.arange(n_points)
trend = 100 + 0.6 * day
launch_bump = 25 * np.exp(-((day - 12) ** 2) / 30.0)
mid_decline = -22 * np.exp(-((day - 35) ** 2) / 60.0)
weekend = np.where(day % 7 >= 5, -10.0, 0.0)
noise = np.random.randn(n_points) * 4
values = trend + launch_bump + mid_decline + weekend + noise

min_idx = int(np.argmin(values))
max_idx = int(np.argmax(values))

line_source = ColumnDataSource(data={"x": day, "y": values})
endpoint_source = ColumnDataSource(data={"x": [day[0], day[-1]], "y": [values[0], values[-1]]})
extreme_source = ColumnDataSource(
    data={"x": [day[min_idx], day[max_idx]], "y": [values[min_idx], values[max_idx]], "color": [MIN_COLOR, MAX_COLOR]}
)

# Compact ~4:1 sparkline canvas
p = figure(width=4800, height=1200, title="sparkline-basic · bokeh · anyplot.ai", toolbar_location=None)

# Strip all chart chrome — sparkline minimalism
p.xaxis.visible = False
p.yaxis.visible = False
p.xgrid.visible = False
p.ygrid.visible = False
p.outline_line_color = None
p.min_border = 80

# Theme-adaptive chrome (data colors stay identical across themes)
p.background_fill_color = PAGE_BG
p.border_fill_color = PAGE_BG
p.title.text_color = INK
p.title.text_font_size = "32pt"
p.title.align = "center"

# Sparkline geometry
p.line(x="x", y="y", source=line_source, line_width=6, color=LINE_COLOR, alpha=0.95)
p.scatter(x="x", y="y", source=endpoint_source, size=22, color=INK_SOFT, alpha=0.7)
p.scatter(x="x", y="y", source=extreme_source, size=44, color="color", alpha=0.95)

export_png(p, filename=f"plot-{THEME}.png")
output_file(f"plot-{THEME}.html")
save(p)
