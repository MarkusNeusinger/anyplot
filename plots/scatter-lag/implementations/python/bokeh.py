""" pyplots.ai
scatter-lag: Lag Plot for Time Series Autocorrelation Diagnosis
Library: bokeh 3.9.0 | Python 3.14.3
Quality: 85/100 | Created: 2026-04-12
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import ColorBar, ColumnDataSource, Label, LinearColorMapper
from bokeh.palettes import Viridis256
from bokeh.plotting import figure
from bokeh.resources import CDN
from bokeh.transform import linear_cmap


# Data - AR(1) process with moderate positive autocorrelation
np.random.seed(42)
n_obs = 500
phi = 0.85
noise = np.random.normal(0, 1, n_obs)
series = np.zeros(n_obs)
series[0] = noise[0]
for i in range(1, n_obs):
    series[i] = phi * series[i - 1] + noise[i]

lag = 1
y_t = series[:-lag]
y_t_lag = series[lag:]
time_index = np.arange(len(y_t))

correlation = np.corrcoef(y_t, y_t_lag)[0, 1]

source = ColumnDataSource(data={"y_t": y_t, "y_t_lag": y_t_lag, "time_index": time_index})

# Plot
color_mapper = LinearColorMapper(palette=Viridis256, low=time_index.min(), high=time_index.max())

p = figure(
    width=4800, height=2700, title="scatter-lag · bokeh · pyplots.ai", x_axis_label="y(t)", y_axis_label="y(t + 1)"
)

p.scatter(
    x="y_t",
    y="y_t_lag",
    source=source,
    size=20,
    fill_color=linear_cmap("time_index", palette=Viridis256, low=time_index.min(), high=time_index.max()),
    line_color="white",
    line_width=0.8,
    fill_alpha=0.8,
)

# Diagonal reference line (y = x)
axis_min = min(y_t.min(), y_t_lag.min()) - 0.5
axis_max = max(y_t.max(), y_t_lag.max()) + 0.5
p.line(
    [axis_min, axis_max], [axis_min, axis_max], line_color="#AAAAAA", line_dash="dashed", line_width=3, line_alpha=0.5
)

# Color bar for time index
color_bar = ColorBar(
    color_mapper=color_mapper,
    title="Time Index",
    title_text_font_size="22pt",
    title_standoff=20,
    major_label_text_font_size="18pt",
    label_standoff=12,
    width=50,
    padding=40,
)
p.add_layout(color_bar, "right")

# Correlation annotation
corr_label = Label(
    x=axis_min + 0.3, y=axis_max - 0.5, text=f"r = {correlation:.3f}", text_font_size="24pt", text_color="#333333"
)
p.add_layout(corr_label)

# Style
p.title.text_font_size = "32pt"
p.title.text_font_style = "normal"
p.xaxis.axis_label_text_font_size = "24pt"
p.yaxis.axis_label_text_font_size = "24pt"
p.xaxis.major_label_text_font_size = "20pt"
p.yaxis.major_label_text_font_size = "20pt"

p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None

p.xgrid.grid_line_alpha = 0.2
p.ygrid.grid_line_alpha = 0.2
p.xgrid.grid_line_width = 1
p.ygrid.grid_line_width = 1

p.outline_line_color = None
p.background_fill_color = "#FFFFFF"
p.border_fill_color = "#FFFFFF"

p.toolbar_location = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="scatter-lag · bokeh · pyplots.ai")
