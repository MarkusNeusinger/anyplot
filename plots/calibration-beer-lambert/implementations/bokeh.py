""" pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-09
"""

import numpy as np
from bokeh.io import export_png, save
from bokeh.models import Band, ColumnDataSource, Label
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
scatter_source = ColumnDataSource(data={"conc": concentrations, "abs": absorbance})
line_source = ColumnDataSource(data={"conc": conc_line, "abs": abs_line})
band_source = ColumnDataSource(data={"conc": conc_line, "lower": pi_lower, "upper": pi_upper})
unknown_source = ColumnDataSource(data={"conc": [unknown_concentration], "abs": [unknown_absorbance]})

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

# Prediction interval band
band = Band(
    base="conc",
    lower="lower",
    upper="upper",
    source=band_source,
    fill_color="#306998",
    fill_alpha=0.15,
    line_color="#306998",
    line_alpha=0.25,
    line_width=2,
)
p.add_layout(band)

# Regression line
p.line("conc", "abs", source=line_source, line_color="#FFD43B", line_width=6, legend_label="Linear Fit")

# Calibration standards
p.scatter(
    "conc",
    "abs",
    source=scatter_source,
    size=30,
    color="#306998",
    alpha=0.85,
    line_color="white",
    line_width=2,
    legend_label="Standards",
)

# Unknown sample point
p.scatter(
    "conc",
    "abs",
    source=unknown_source,
    size=30,
    color="#E74C3C",
    alpha=0.9,
    line_color="white",
    line_width=2,
    marker="diamond",
    legend_label="Unknown",
)

# Dashed lines from unknown sample to axes
p.line(
    [unknown_concentration, unknown_concentration],
    [0, unknown_absorbance],
    line_color="#E74C3C",
    line_width=4,
    line_dash="dashed",
    line_alpha=0.7,
)
p.line(
    [0, unknown_concentration],
    [unknown_absorbance, unknown_absorbance],
    line_color="#E74C3C",
    line_width=4,
    line_dash="dashed",
    line_alpha=0.7,
)

# Regression equation and R-squared annotation
eq_text = f"y = {slope:.4f}x + {intercept:.4f}\nR\u00b2 = {r_squared:.4f}"
eq_label = Label(
    x=0.8,
    y=0.48,
    text=eq_text,
    text_font_size="32pt",
    text_color="#306998",
    background_fill_color="white",
    background_fill_alpha=0.85,
)
p.add_layout(eq_label)

# Unknown sample annotation
unknown_text = f"Unknown: {unknown_concentration:.1f} mg/L"
unknown_label = Label(
    x=unknown_concentration + 0.3,
    y=unknown_absorbance + 0.02,
    text=unknown_text,
    text_font_size="28pt",
    text_color="#E74C3C",
    background_fill_color="white",
    background_fill_alpha=0.8,
)
p.add_layout(unknown_label)

# Style
p.title.text_font_size = "40pt"
p.title.text_color = "#333333"
p.title.align = "center"

p.xaxis.axis_label_text_font_size = "28pt"
p.yaxis.axis_label_text_font_size = "28pt"
p.xaxis.major_label_text_font_size = "22pt"
p.yaxis.major_label_text_font_size = "22pt"

p.legend.label_text_font_size = "24pt"
p.legend.location = "top_left"
p.legend.background_fill_alpha = 0.85
p.legend.border_line_alpha = 0.3
p.legend.glyph_height = 30
p.legend.glyph_width = 30
p.legend.padding = 20
p.legend.spacing = 10

p.xgrid.grid_line_alpha = 0.2
p.ygrid.grid_line_alpha = 0.2

p.axis.axis_line_width = 2
p.axis.axis_line_color = "#555555"

p.outline_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", resources=CDN, title="Beer-Lambert Calibration Curve")
