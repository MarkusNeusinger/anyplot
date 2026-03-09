"""pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-09
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Band, ColumnDataSource, HoverTool, Label
from bokeh.plotting import figure
from bokeh.resources import CDN
from scipy import stats


# Data - UV-Vis calibration standards for copper sulfate at 810 nm
np.random.seed(42)
concentrations = np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0])
epsilon_l = 0.045  # molar absorptivity * path length
true_absorbance = epsilon_l * concentrations
noise = np.random.normal(0, 0.008, len(concentrations))
noise[0] = np.random.normal(0, 0.003)  # blank has less noise
absorbance = true_absorbance + noise
absorbance[0] = max(0.001, absorbance[0])  # blank stays near zero

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(concentrations, absorbance)
r_squared = r_value**2

# Regression line and prediction interval
conc_line = np.linspace(-0.5, 13.5, 200)
abs_line = slope * conc_line + intercept

n = len(concentrations)
conc_mean = np.mean(concentrations)
residuals = absorbance - (slope * concentrations + intercept)
se = np.sqrt(np.sum(residuals**2) / (n - 2))
t_val = stats.t.ppf(0.975, n - 2)  # 95% prediction interval

# Prediction interval (for a new observation)
se_pred = se * np.sqrt(1 + 1 / n + (conc_line - conc_mean) ** 2 / np.sum((concentrations - conc_mean) ** 2))
pi_upper = abs_line + t_val * se_pred
pi_lower = abs_line - t_val * se_pred

# Unknown sample
unknown_absorbance = 0.32
unknown_concentration = (unknown_absorbance - intercept) / slope

# Data sources
scatter_source = ColumnDataSource(
    data={
        "conc": concentrations,
        "abs": absorbance,
        "conc_fmt": [f"{c:.1f}" for c in concentrations],
        "abs_fmt": [f"{a:.4f}" for a in absorbance],
    }
)
line_source = ColumnDataSource(data={"conc": conc_line, "abs": abs_line})
band_source = ColumnDataSource(data={"conc": conc_line, "lower": pi_lower, "upper": pi_upper})
unknown_source = ColumnDataSource(
    data={
        "conc": [unknown_concentration],
        "abs": [unknown_absorbance],
        "conc_fmt": [f"{unknown_concentration:.2f}"],
        "abs_fmt": [f"{unknown_absorbance:.4f}"],
    }
)

# Plot
p = figure(
    width=4800,
    height=2700,
    title="calibration-beer-lambert \u00b7 bokeh \u00b7 pyplots.ai",
    x_axis_label="Concentration (mg/L)",
    y_axis_label="Absorbance",
    x_range=(-0.5, 13.5),
    y_range=(-0.03, 0.65),
)

# Background styling
p.background_fill_color = "#F7F9FC"
p.border_fill_color = "#FFFFFF"

# Prediction interval band
band = Band(
    base="conc",
    lower="lower",
    upper="upper",
    source=band_source,
    fill_color="#306998",
    fill_alpha=0.12,
    line_color="#306998",
    line_alpha=0.2,
    line_width=1,
)
p.add_layout(band)

# Regression line - dark teal for strong contrast
p.line("conc", "abs", source=line_source, line_color="#1A5276", line_width=5, legend_label="Linear Fit")

# Calibration standards
standards_renderer = p.scatter(
    "conc",
    "abs",
    source=scatter_source,
    size=36,
    color="#306998",
    alpha=0.9,
    line_color="white",
    line_width=3,
    legend_label="Standards",
)

# Unknown sample point
unknown_renderer = p.scatter(
    "conc",
    "abs",
    source=unknown_source,
    size=40,
    color="#C0392B",
    alpha=0.95,
    line_color="white",
    line_width=3,
    marker="diamond",
    legend_label="Unknown",
)

# HoverTool for standards
hover_standards = HoverTool(
    renderers=[standards_renderer],
    tooltips=[("Concentration", "@conc_fmt mg/L"), ("Absorbance", "@abs_fmt")],
    mode="mouse",
)
p.add_tools(hover_standards)

# HoverTool for unknown
hover_unknown = HoverTool(
    renderers=[unknown_renderer],
    tooltips=[("Unknown Sample", ""), ("Concentration", "@conc_fmt mg/L"), ("Absorbance", "@abs_fmt")],
    mode="mouse",
)
p.add_tools(hover_unknown)

# Dashed lines from unknown sample to axes
p.line(
    [unknown_concentration, unknown_concentration],
    [0, unknown_absorbance],
    line_color="#C0392B",
    line_width=4,
    line_dash="dashed",
    line_alpha=0.6,
)
p.line(
    [0, unknown_concentration],
    [unknown_absorbance, unknown_absorbance],
    line_color="#C0392B",
    line_width=4,
    line_dash="dashed",
    line_alpha=0.6,
)

# Regression equation and R-squared annotation
eq_text = f"y = {slope:.4f}x + {intercept:.4f}\nR\u00b2 = {r_squared:.4f}"
eq_label = Label(
    x=0.8,
    y=0.48,
    text=eq_text,
    text_font_size="34pt",
    text_color="#1A5276",
    text_font_style="bold",
    background_fill_color="#F7F9FC",
    background_fill_alpha=0.9,
)
p.add_layout(eq_label)

# Unknown sample annotation
unknown_text = f"Unknown: {unknown_concentration:.1f} mg/L"
unknown_label = Label(
    x=unknown_concentration + 0.3,
    y=unknown_absorbance + 0.025,
    text=unknown_text,
    text_font_size="30pt",
    text_color="#C0392B",
    text_font_style="bold",
    background_fill_color="#F7F9FC",
    background_fill_alpha=0.9,
)
p.add_layout(unknown_label)

# 95% PI label
pi_label = Label(
    x=10.5,
    y=float(pi_upper[160]) + 0.015,
    text="95% Prediction Interval",
    text_font_size="22pt",
    text_color="#306998",
    text_alpha=0.7,
    text_font_style="italic",
)
p.add_layout(pi_label)

# Style - refined typography
p.title.text_font_size = "40pt"
p.title.text_color = "#2C3E50"
p.title.align = "center"

p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.axis_label_text_color = "#2C3E50"
p.yaxis.axis_label_text_color = "#2C3E50"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"
p.xaxis.major_label_text_color = "#555555"
p.yaxis.major_label_text_color = "#555555"

p.legend.label_text_font_size = "26pt"
p.legend.location = "top_left"
p.legend.background_fill_color = "#F7F9FC"
p.legend.background_fill_alpha = 0.92
p.legend.border_line_color = "#CCCCCC"
p.legend.border_line_alpha = 0.4
p.legend.glyph_height = 40
p.legend.glyph_width = 40
p.legend.padding = 25
p.legend.spacing = 15
p.legend.margin = 20

# Grid and axis refinement
p.xgrid.grid_line_color = "#CCCCCC"
p.ygrid.grid_line_color = "#CCCCCC"
p.xgrid.grid_line_alpha = 0.3
p.ygrid.grid_line_alpha = 0.3
p.xgrid.grid_line_dash = [4, 4]
p.ygrid.grid_line_dash = [4, 4]

p.axis.axis_line_color = "#AAAAAA"
p.axis.axis_line_width = 1
p.axis.minor_tick_line_color = None
p.axis.major_tick_line_color = "#AAAAAA"

p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Beer-Lambert Calibration Curve")
