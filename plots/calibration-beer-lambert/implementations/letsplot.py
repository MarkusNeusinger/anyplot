"""pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-09
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave
from scipy import stats


LetsPlot.setup_html()  # noqa: F405

# Data - Calibration standards for UV-Vis spectrophotometry (e.g., Cu²⁺ at 810 nm)
np.random.seed(42)
concentrations = np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0])
molar_absorptivity = 0.045
absorbance_true = molar_absorptivity * concentrations
absorbance_measured = absorbance_true + np.random.normal(0, 0.008, len(concentrations))
absorbance_measured[0] = max(0.002, absorbance_measured[0])

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(concentrations, absorbance_measured)
r_squared = r_value**2

# Prediction interval (limited to data range)
n = len(concentrations)
x_mean = np.mean(concentrations)
x_fit = np.linspace(0, 12.5, 200)
y_fit = slope * x_fit + intercept
se_y = np.sqrt(np.sum((absorbance_measured - (slope * concentrations + intercept)) ** 2) / (n - 2))
t_val = stats.t.ppf(0.975, n - 2)
prediction_interval = t_val * se_y * np.sqrt(1 + 1 / n + (x_fit - x_mean) ** 2 / np.sum((concentrations - x_mean) ** 2))
y_upper = y_fit + prediction_interval
y_lower = y_fit - prediction_interval

# Unknown sample
unknown_absorbance = 0.34
unknown_concentration = (unknown_absorbance - intercept) / slope

# DataFrames
df_standards = pd.DataFrame({"concentration": concentrations, "absorbance": absorbance_measured})

df_fit = pd.DataFrame({"concentration": x_fit, "absorbance": y_fit, "upper": y_upper, "lower": y_lower})

df_unknown = pd.DataFrame({"concentration": [unknown_concentration], "absorbance": [unknown_absorbance]})

# Segments for unknown sample dashed lines (idiomatic geom_segment)
df_segments = pd.DataFrame(
    {
        "x": [0, unknown_concentration],
        "y": [unknown_absorbance, 0],
        "xend": [unknown_concentration, unknown_concentration],
        "yend": [unknown_absorbance, unknown_absorbance],
    }
)

eq_label = f"y = {slope:.4f}x + {intercept:.4f}\nR\u00b2 = {r_squared:.5f}"

df_eq = pd.DataFrame({"x": [1.5], "y": [0.48], "label": [eq_label]})

df_unknown_label = pd.DataFrame(
    {
        "x": [unknown_concentration + 0.6],
        "y": [unknown_absorbance + 0.04],
        "label": [f"Unknown\n({unknown_concentration:.1f} mg/L, A = {unknown_absorbance})"],
    }
)

# Plot
plot = (
    ggplot()
    # Prediction interval band
    + geom_ribbon(aes(x="concentration", ymin="lower", ymax="upper"), data=df_fit, fill="#306998", alpha=0.12)
    # Regression line
    + geom_line(aes(x="concentration", y="absorbance"), data=df_fit, color="#306998", size=1.8)
    # Dashed lines for unknown sample using geom_segment
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"), data=df_segments, color="#D95319", size=1.2, linetype="dashed"
    )
    # Calibration standard points
    + geom_point(
        aes(x="concentration", y="absorbance"),
        data=df_standards,
        fill="#306998",
        color="white",
        size=6,
        alpha=0.9,
        shape=21,
        stroke=1.0,
    )
    # Unknown sample point
    + geom_point(
        aes(x="concentration", y="absorbance"),
        data=df_unknown,
        fill="#D95319",
        color="white",
        size=7,
        shape=23,
        stroke=1.0,
    )
    # Equation annotation
    + geom_text(aes(x="x", y="y", label="label"), data=df_eq, size=13, color="#333333", family="monospace", hjust=0)
    # Unknown sample label
    + geom_text(
        aes(x="x", y="y", label="label"), data=df_unknown_label, size=11, color="#D95319", hjust=0, fontface="italic"
    )
    # Labels and styling
    + labs(x="Concentration (mg/L)", y="Absorbance", title="calibration-beer-lambert \u00b7 letsplot \u00b7 pyplots.ai")
    + scale_x_continuous(limits=[-0.5, 13.5], breaks=[0, 2, 4, 6, 8, 10, 12])
    + scale_y_continuous(limits=[-0.02, 0.58], breaks=[0, 0.1, 0.2, 0.3, 0.4, 0.5])
    + coord_cartesian(xlim=[-0.5, 13.5], ylim=[-0.02, 0.58])
    + ggsize(1600, 900)
    + theme_minimal()
    + theme(
        axis_text=element_text(size=16, color="#555555"),
        axis_title=element_text(size=20, color="#333333"),
        plot_title=element_text(size=24, color="#222222", face="bold"),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),
        panel_background=element_rect(fill="#FAFAFA", color="#FAFAFA"),
        axis_ticks=element_blank(),
        axis_ticks_length=0,
        plot_margin=[30, 40, 20, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
