""" pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-21
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave
from scipy import stats


LetsPlot.setup_html()  # noqa: F405

# Data - First-order decomposition reaction rate constants at various temperatures
np.random.seed(42)
temperature_K = np.array([300, 325, 350, 375, 400, 425, 450, 475, 500, 550, 600])
R = 8.314  # Gas constant (J/(mol·K))
Ea_true = 75000  # Activation energy (J/mol) ~75 kJ/mol
A_true = 1e12  # Pre-exponential factor (s⁻¹)

rate_constant_k = A_true * np.exp(-Ea_true / (R * temperature_K))
noise = np.random.normal(0, 0.15, len(temperature_K))
ln_k = np.log(rate_constant_k) + noise

inv_T = 1.0 / temperature_K

# Linear regression: ln(k) = -Ea/R * (1/T) + ln(A)
slope, intercept, r_value, p_value, std_err = stats.linregress(inv_T, ln_k)
r_squared = r_value**2
Ea_extracted = -slope * R / 1000  # Convert to kJ/mol

# Fit line
inv_T_fit = np.linspace(inv_T.min() * 0.97, inv_T.max() * 1.03, 200)
ln_k_fit = slope * inv_T_fit + intercept

# DataFrames
df_points = pd.DataFrame(
    {
        "inv_T": inv_T,
        "ln_k": ln_k,
        "temp_K": [f"{t} K" for t in temperature_K],
        "k_val": [f"{np.exp(lk):.2e}" for lk in ln_k],
    }
)

df_fit = pd.DataFrame({"inv_T": inv_T_fit, "ln_k": ln_k_fit})

# Annotation
eq_text = f"Slope = −Ea/R = {slope:.0f} K\nEa = {Ea_extracted:.1f} kJ/mol\nR² = {r_squared:.4f}"
y_range = ln_k.max() - ln_k.min()
df_annotation = pd.DataFrame(
    {"x": [inv_T.max() - (inv_T.max() - inv_T.min()) * 0.02], "y": [ln_k.min() + y_range * 0.25], "label": [eq_text]}
)

# Secondary x-axis: temperature labels at top of plot
temp_ticks = np.array([600, 500, 450, 400, 350, 300])
inv_T_ticks = 1.0 / temp_ticks
y_top = ln_k.max() + y_range * 0.12
df_temp_labels = pd.DataFrame(
    {"inv_T": inv_T_ticks, "y": [y_top] * len(temp_ticks), "label": [f"{t} K" for t in temp_ticks]}
)
df_temp_axis_label = pd.DataFrame(
    {"inv_T": [np.mean(inv_T_ticks)], "y": [y_top + y_range * 0.08], "label": ["Temperature (K)"]}
)

# Plot with lets-plot specific features: tooltips, flavor, geom_smooth
plot = (
    ggplot()
    + geom_line(aes(x="inv_T", y="ln_k"), data=df_fit, color="#306998", size=1.8, alpha=0.6, linetype="solid")
    + geom_point(
        aes(x="inv_T", y="ln_k"),
        data=df_points,
        fill="#306998",
        color="white",
        size=6,
        shape=21,
        stroke=1.2,
        tooltips=layer_tooltips().line("@temp_K").line("1/T = @inv_T").line("ln(k) = @ln_k").line("k = @k_val"),
    )
    # Annotation with regression parameters (positioned at right side near data)
    + geom_text(
        aes(x="x", y="y", label="label"), data=df_annotation, size=12, color="#333333", family="monospace", hjust=1
    )
    # Secondary x-axis: temperature labels at top
    + geom_text(aes(x="inv_T", y="y", label="label"), data=df_temp_labels, size=11, color="#777777")
    + geom_segment(
        aes(x="inv_T", y="y", xend="inv_T", yend="yend"),
        data=pd.DataFrame(
            {
                "inv_T": inv_T_ticks,
                "y": [y_top - y_range * 0.02] * len(temp_ticks),
                "yend": [y_top - y_range * 0.05] * len(temp_ticks),
            }
        ),
        color="#BBBBBB",
        size=0.5,
    )
    + geom_text(
        aes(x="inv_T", y="y", label="label"), data=df_temp_axis_label, size=13, color="#555555", fontface="italic"
    )
    + labs(x="1/T (K⁻¹)", y="ln(k)", title="line-arrhenius · letsplot · pyplots.ai")
    + scale_x_continuous(breaks=inv_T_ticks.tolist(), labels=[f"{v:.2e}" for v in inv_T_ticks])
    + scale_y_continuous(limits=[ln_k.min() - y_range * 0.08, y_top + y_range * 0.15])
    + coord_cartesian(xlim=[inv_T.min() * 0.95, inv_T.max() * 1.05])
    + ggsize(1600, 900)
    + flavor_solarized_light()
    + theme(
        axis_text=element_text(size=16, color="#555555"),
        axis_title=element_text(size=20, color="#333333"),
        plot_title=element_text(size=24, color="#222222", face="bold"),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color="#D5D0C8", size=0.4),
        panel_grid_minor=element_blank(),
        axis_ticks=element_blank(),
        axis_ticks_length=0,
        plot_margin=[40, 40, 20, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
