"""pyplots.ai
calibration-beer-lambert: Beer-Lambert Calibration Curve
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-09
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_label,
    geom_point,
    geom_segment,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    stat_smooth,
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

# Linear regression (for equation annotation and unknown sample calculation)
slope, intercept, r_value, p_value, std_err = stats.linregress(concentrations, absorbances)
r_squared = r_value**2

# Unknown sample
unknown_absorbance = 0.34
unknown_concentration = (unknown_absorbance - intercept) / slope

df_standards = pd.DataFrame(
    {"concentration": concentrations, "absorbance": absorbances, "series": "Calibration Standards"}
)

df_unknown = pd.DataFrame(
    {"concentration": [unknown_concentration], "absorbance": [unknown_absorbance], "series": "Unknown Sample"}
)

# Segments for unknown sample dashed lines
df_seg_h = pd.DataFrame(
    {"x": [0.0], "xend": [unknown_concentration], "y": [unknown_absorbance], "yend": [unknown_absorbance]}
)
df_seg_v = pd.DataFrame(
    {"x": [unknown_concentration], "xend": [unknown_concentration], "y": [0.0], "yend": [unknown_absorbance]}
)

# Annotation text
eq_text = f"y = {slope:.4f}x + {intercept:.4f}"
r2_text = f"R² = {r_squared:.5f}"

# Annotation label dataframe for geom_label
df_eq = pd.DataFrame({"x": [1.5], "y": [0.49], "label": [eq_text]})
df_r2 = pd.DataFrame({"x": [1.5], "y": [0.44], "label": [r2_text]})

# Plot
plot = (
    ggplot(df_standards, aes(x="concentration", y="absorbance"))
    + stat_smooth(method="lm", color="#306998", fill="#306998", alpha=0.15, size=1.2, fullrange=True)
    + geom_segment(
        df_seg_h,
        aes(x="x", xend="xend", y="y", yend="yend"),
        linetype="dashed",
        color="#888888",
        size=0.8,
        inherit_aes=False,
    )
    + geom_segment(
        df_seg_v,
        aes(x="x", xend="xend", y="y", yend="yend"),
        linetype="dashed",
        color="#888888",
        size=0.8,
        inherit_aes=False,
    )
    + geom_point(aes(color="series"), size=5.5, fill="white", stroke=1.5)
    + geom_point(
        df_unknown, aes(x="concentration", y="absorbance", color="series"), size=6, shape="D", inherit_aes=False
    )
    + scale_color_manual(values={"Calibration Standards": "#306998", "Unknown Sample": "#D04848"}, name=" ")
    + geom_label(
        df_eq,
        aes(x="x", y="y", label="label"),
        ha="left",
        size=18,
        color="#2A2A2A",
        fill="#F5F5F0",
        label_size=0.3,
        label_r=0.02,
        inherit_aes=False,
        show_legend=False,
    )
    + geom_label(
        df_r2,
        aes(x="x", y="y", label="label"),
        ha="left",
        size=18,
        color="#2A2A2A",
        fill="#F5F5F0",
        label_size=0.3,
        label_r=0.02,
        inherit_aes=False,
        show_legend=False,
    )
    + scale_x_continuous(breaks=np.arange(0, 14, 2), limits=(-0.5, 13.5), expand=(0, 0.3))
    + scale_y_continuous(breaks=np.arange(0, 0.65, 0.1), limits=(-0.02, 0.6), expand=(0, 0.01))
    + labs(x="Concentration (mg/L)", y="Absorbance", title="calibration-beer-lambert · plotnine · pyplots.ai")
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, family="sans-serif"),
        axis_title=element_text(size=20, weight="bold"),
        axis_text=element_text(size=16, color="#444444"),
        plot_title=element_text(size=24, weight="bold"),
        plot_background=element_rect(fill="white", color="white"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E8E8E8", size=0.4),
        axis_line_x=element_line(color="#333333", size=0.5),
        axis_line_y=element_line(color="#333333", size=0.5),
        legend_position="bottom",
        legend_text=element_text(size=15),
        legend_background=element_rect(fill="white", color="white"),
        plot_margin=0.04,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
