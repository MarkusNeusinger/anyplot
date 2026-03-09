"""pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-09
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_line,
    geom_point,
    geom_ribbon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    theme,
    theme_minimal,
)
from scipy import stats


# Data
np.random.seed(42)
concentrations = np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0, 12.0])
molar_absorptivity = 0.045
absorbances = molar_absorptivity * concentrations + np.random.normal(0, 0.008, len(concentrations))
absorbances = np.clip(absorbances, 0, None)

# Linear regression
slope, intercept, r_value, p_value, std_err = stats.linregress(concentrations, absorbances)
r_squared = r_value**2

# Fit line and prediction interval
conc_fit = np.linspace(-0.5, 13.5, 200)
abs_fit = slope * conc_fit + intercept
n = len(concentrations)
conc_mean = np.mean(concentrations)
se_fit = np.sqrt(
    (np.sum((absorbances - slope * concentrations - intercept) ** 2) / (n - 2))
    * (1 + 1 / n + (conc_fit - conc_mean) ** 2 / np.sum((concentrations - conc_mean) ** 2))
)
t_val = stats.t.ppf(0.975, n - 2)
upper = abs_fit + t_val * se_fit
lower = abs_fit - t_val * se_fit

df_fit = pd.DataFrame({"concentration": conc_fit, "absorbance": abs_fit, "lower": lower, "upper": upper})

# Unknown sample
unknown_absorbance = 0.34
unknown_concentration = (unknown_absorbance - intercept) / slope

df_standards = pd.DataFrame({"concentration": concentrations, "absorbance": absorbances})

df_unknown = pd.DataFrame({"concentration": [unknown_concentration], "absorbance": [unknown_absorbance]})

# Segments for unknown sample dashed lines
df_seg_h = pd.DataFrame(
    {"x": [0.0], "xend": [unknown_concentration], "y": [unknown_absorbance], "yend": [unknown_absorbance]}
)
df_seg_v = pd.DataFrame(
    {"x": [unknown_concentration], "xend": [unknown_concentration], "y": [0.0], "yend": [unknown_absorbance]}
)

# Annotation text
eq_text = f"y = {slope:.4f}x + {intercept:.4f}"
r2_text = f"R\u00b2 = {r_squared:.5f}"
df_annotation = pd.DataFrame({"concentration": [1.5, 1.5], "absorbance": [0.48, 0.44], "label": [eq_text, r2_text]})

# Plot
plot = (
    ggplot()
    + geom_ribbon(df_fit, aes(x="concentration", ymin="lower", ymax="upper"), fill="#306998", alpha=0.15)
    + geom_line(df_fit, aes(x="concentration", y="absorbance"), color="#306998", size=1.2)
    + geom_segment(df_seg_h, aes(x="x", xend="xend", y="y", yend="yend"), linetype="dashed", color="#888888", size=0.8)
    + geom_segment(df_seg_v, aes(x="x", xend="xend", y="y", yend="yend"), linetype="dashed", color="#888888", size=0.8)
    + geom_point(
        df_standards, aes(x="concentration", y="absorbance"), color="#306998", size=4, fill="white", stroke=1.5
    )
    + geom_point(df_unknown, aes(x="concentration", y="absorbance"), color="#D04848", size=5, shape="D")
    + geom_text(
        df_annotation, aes(x="concentration", y="absorbance", label="label"), ha="left", size=12, color="#333333"
    )
    + labs(x="Concentration (mg/L)", y="Absorbance", title="calibration-beer-lambert \u00b7 plotnine \u00b7 pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24, weight="bold"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.5),
        axis_line=element_line(color="#333333", size=0.5),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
