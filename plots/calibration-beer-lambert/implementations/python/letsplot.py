"""pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: letsplot | Python
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave
from scipy import stats


LetsPlot.setup_html()  # noqa: F405

THEME = os.getenv("ANYPLOT_THEME", "light")

# Imprint palette: position 1 = calibration standards/regression; position 5 = unknown focal point
BRAND = "#009E73"  # calibration standards + regression (Imprint position 1)
FOCAL = "#AE3030"  # unknown sample highlight (Imprint position 5)

# Theme-adaptive chrome tokens
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Data — calibration standards for UV-Vis spectrophotometry (Cu²⁺ at 810 nm)
np.random.seed(42)
concentrations = np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0])
absorbance_true = 0.045 * concentrations
absorbance_measured = absorbance_true + np.random.normal(0, 0.008, len(concentrations))
absorbance_measured[0] = max(0.002, absorbance_measured[0])

# Linear regression
slope, intercept, r_value, _p, _se = stats.linregress(concentrations, absorbance_measured)
r_squared = r_value**2

# Prediction interval over fit range
n = len(concentrations)
x_mean = np.mean(concentrations)
x_fit = np.linspace(0, 12.5, 200)
y_fit = slope * x_fit + intercept
se_y = np.sqrt(np.sum((absorbance_measured - (slope * concentrations + intercept)) ** 2) / (n - 2))
t_val = stats.t.ppf(0.975, n - 2)
pi = t_val * se_y * np.sqrt(1 + 1 / n + (x_fit - x_mean) ** 2 / np.sum((concentrations - x_mean) ** 2))

# Unknown sample — concentration determined from absorbance via regression
unknown_absorbance = 0.34
unknown_concentration = (unknown_absorbance - intercept) / slope

# DataFrames
df_standards = pd.DataFrame({"concentration": concentrations, "absorbance": absorbance_measured})
df_fit = pd.DataFrame({"concentration": x_fit, "absorbance": y_fit, "upper": y_fit + pi, "lower": y_fit - pi})
df_unknown = pd.DataFrame({"concentration": [unknown_concentration], "absorbance": [unknown_absorbance]})
df_segments = pd.DataFrame(
    {
        "x": [0.0, unknown_concentration],
        "y": [unknown_absorbance, 0.0],
        "xend": [unknown_concentration, unknown_concentration],
        "yend": [unknown_absorbance, unknown_absorbance],
    }
)

eq_label = f"y = {slope:.4f}x + {intercept:.4f}\nR² = {r_squared:.5f}"
df_eq = pd.DataFrame({"x": [1.0], "y": [0.49], "label": [eq_label]})
df_unknown_label = pd.DataFrame(
    {
        "x": [unknown_concentration + 0.5],
        "y": [unknown_absorbance + 0.032],
        "label": [f"Unknown\n({unknown_concentration:.1f} mg/L, A = {unknown_absorbance})"],
    }
)

# Build plot — layer_tooltips() is a lets-plot distinctive feature for interactive HTML output
plot = (
    ggplot()
    + geom_ribbon(aes(x="concentration", ymin="lower", ymax="upper"), data=df_fit, fill=BRAND, alpha=0.12)
    + geom_line(aes(x="concentration", y="absorbance"), data=df_fit, color=BRAND, size=1.0)
    + geom_segment(
        aes(x="x", y="y", xend="xend", yend="yend"), data=df_segments, color=FOCAL, size=0.7, linetype="dashed"
    )
    + geom_point(
        aes(x="concentration", y="absorbance"),
        data=df_standards,
        fill=BRAND,
        color="white",
        size=2.5,
        alpha=0.9,
        shape=21,
        stroke=1.0,
        tooltips=layer_tooltips()
        .title("Calibration Standard")
        .line("Concentration: @concentration mg/L")
        .line("Absorbance: @absorbance"),
    )
    + geom_point(
        aes(x="concentration", y="absorbance"),
        data=df_unknown,
        fill=FOCAL,
        color="white",
        size=3.0,
        shape=23,
        stroke=1.0,
        tooltips=layer_tooltips()
        .title("Unknown Sample")
        .line("Concentration: @concentration mg/L")
        .line("Absorbance: @absorbance"),
    )
    + geom_text(aes(x="x", y="y", label="label"), data=df_eq, size=4, color=INK, family="monospace", hjust=0)
    + geom_text(
        aes(x="x", y="y", label="label"), data=df_unknown_label, size=3.5, color=FOCAL, hjust=0, fontface="italic"
    )
    + labs(x="Concentration (mg/L)", y="Absorbance", title="calibration-beer-lambert · letsplot · pyplots.ai")
    + scale_x_continuous(limits=[-0.5, 13.5], breaks=[0, 2, 4, 6, 8, 10, 12])
    + scale_y_continuous(limits=[-0.02, 0.58], breaks=[0, 0.1, 0.2, 0.3, 0.4, 0.5])
    + coord_cartesian(xlim=[-0.5, 13.5], ylim=[-0.02, 0.58])
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        plot_title=element_text(size=16, color=INK, face="bold"),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color=INK_SOFT, size=0.3),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        axis_ticks=element_blank(),
        axis_ticks_length=0,
        plot_margin=[30, 40, 20, 20],
    )
)

# Save theme-suffixed PNG (3200×1800 via ggsize(800,450) × scale=4) and interactive HTML
ggsave(plot, filename=f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, filename=f"plot-{THEME}.html", path=".")
