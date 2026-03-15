"""pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: bokeh 3.9.0 | Python 3.14.3
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import Band, ColumnDataSource, HoverTool, Label, LinearColorMapper
from bokeh.palettes import Cividis256
from bokeh.plotting import figure, save
from bokeh.resources import CDN
from bokeh.transform import transform
from scipy import stats


# Data — manufacturing quality control: bolt tensile strength measurements
np.random.seed(42)
bolt_strength = np.random.normal(loc=850, scale=45, size=200) + np.random.exponential(scale=15, size=200)

observed_sorted = np.sort(bolt_strength)
n = len(observed_sorted)

mu, sigma = stats.norm.fit(observed_sorted)
empirical_cdf = np.arange(1, n + 1) / (n + 1)
theoretical_cdf = stats.norm.cdf(observed_sorted, loc=mu, scale=sigma)

# Deviation from perfect fit — key diagnostic insight
deviation = empirical_cdf - theoretical_cdf

# Confidence band (Kolmogorov-Smirnov), clipped to [0, 1]
ks_bound = 1.36 / np.sqrt(n)
band_x = np.linspace(0, 1, 200)
band_source = ColumnDataSource(
    data={"x": band_x, "upper": np.clip(band_x + ks_bound, 0, 1), "lower": np.clip(band_x - ks_bound, 0, 1)}
)

source = ColumnDataSource(
    data={
        "theoretical": theoretical_cdf,
        "empirical": empirical_cdf,
        "deviation": deviation,
        "abs_deviation": np.abs(deviation),
        "strength": observed_sorted,
        "rank": np.arange(1, n + 1),
    }
)

# Color mapper — emphasize deviation magnitude
max_dev = np.max(np.abs(deviation))
color_mapper = LinearColorMapper(palette=Cividis256, low=-max_dev, high=max_dev)

# Plot
p = figure(
    width=3600,
    height=3600,
    title="pp-basic · bokeh · pyplots.ai",
    x_axis_label="Theoretical Cumulative Probability (Normal Fit)",
    y_axis_label="Empirical Cumulative Probability",
    x_range=(-0.02, 1.02),
    y_range=(-0.02, 1.02),
)

# Confidence band
band = Band(
    base="x",
    upper="upper",
    lower="lower",
    source=band_source,
    fill_alpha=0.06,
    fill_color="#93b7d1",
    line_color="#93b7d1",
    line_alpha=0.2,
    line_width=1.5,
)
p.add_layout(band)

# Reference line
p.line([0, 1], [0, 1], line_color="#666666", line_width=4, line_dash="dashed", line_alpha=0.6)

# Data points colored by deviation
scatter = p.scatter(
    x="theoretical",
    y="empirical",
    source=source,
    size=20,
    fill_color=transform("deviation", color_mapper),
    alpha=0.85,
    line_color="white",
    line_width=1.5,
)

# HoverTool — Bokeh-distinctive interactive feature
hover = HoverTool(
    renderers=[scatter],
    tooltips=[
        ("Bolt Strength", "@strength{0.1} MPa"),
        ("Rank", "@rank / 200"),
        ("Theoretical P", "@theoretical{0.000}"),
        ("Empirical P", "@empirical{0.000}"),
        ("Deviation", "@deviation{+0.000}"),
    ],
    mode="mouse",
)
p.add_tools(hover)

# Annotation — highlight the S-shaped deviation pattern
label_upper = Label(
    x=0.72,
    y=0.60,
    text="Heavy right tail →\npoints fall below diagonal",
    text_font_size="22pt",
    text_color="#a0522d",
    text_alpha=0.85,
    text_font_style="italic",
)
p.add_layout(label_upper)

label_lower = Label(
    x=0.08,
    y=0.28,
    text="← Light left tail\nempirical > theoretical",
    text_font_size="22pt",
    text_color="#2c5f7c",
    text_alpha=0.85,
    text_font_style="italic",
)
p.add_layout(label_lower)

# KS band label
ks_label = Label(
    x=0.55,
    y=0.92,
    text=f"95% KS confidence band (D = {ks_bound:.3f})",
    text_font_size="20pt",
    text_color="#306998",
    text_alpha=0.6,
)
p.add_layout(ks_label)

# Style
p.title.text_font_size = "48pt"
p.title.text_font_style = "normal"
p.title.text_color = "#2c3e50"
p.xaxis.axis_label_text_font_size = "34pt"
p.yaxis.axis_label_text_font_size = "34pt"
p.xaxis.major_label_text_font_size = "26pt"
p.yaxis.major_label_text_font_size = "26pt"
p.xaxis.axis_label_text_color = "#444444"
p.yaxis.axis_label_text_color = "#444444"

p.xaxis.minor_tick_line_color = None
p.yaxis.minor_tick_line_color = None
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None

p.xaxis.axis_line_color = "#888888"
p.yaxis.axis_line_color = "#888888"
p.xaxis[0].ticker.desired_num_ticks = 6
p.yaxis[0].ticker.desired_num_ticks = 6

p.outline_line_color = None
p.xgrid.grid_line_color = "#e0e0e0"
p.ygrid.grid_line_color = "#e0e0e0"
p.xgrid.grid_line_alpha = 0.4
p.ygrid.grid_line_alpha = 0.4
p.xgrid.grid_line_width = 1
p.ygrid.grid_line_width = 1
p.xgrid.grid_line_dash = [4, 4]
p.ygrid.grid_line_dash = [4, 4]

p.toolbar_location = None
p.background_fill_color = "#fafafa"
p.border_fill_color = "#FFFFFF"
p.min_border_left = 180
p.min_border_bottom = 150
p.min_border_top = 100
p.min_border_right = 60

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="pp-basic · bokeh · pyplots.ai")
