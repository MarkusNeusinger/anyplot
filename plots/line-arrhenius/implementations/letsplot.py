"""pyplots.ai
line-arrhenius: Arrhenius Plot for Reaction Kinetics
Library: letsplot | Python 3.13
Quality: pending | Created: 2026-03-21
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
df_points = pd.DataFrame({"inv_T": inv_T, "ln_k": ln_k, "temp_label": [f"{t} K" for t in temperature_K]})

df_fit = pd.DataFrame({"inv_T": inv_T_fit, "ln_k": ln_k_fit})

# Annotation data
eq_text = f"Slope = −Ea/R = {slope:.0f} K\nEa = {Ea_extracted:.1f} kJ/mol\nR² = {r_squared:.4f}"
df_annotation = pd.DataFrame(
    {
        "x": [inv_T.min() + (inv_T.max() - inv_T.min()) * 0.05],
        "y": [ln_k.min() + (ln_k.max() - ln_k.min()) * 0.15],
        "label": [eq_text],
    }
)

# Secondary x-axis tick labels (temperature in K)
temp_ticks = np.array([600, 500, 450, 400, 350, 300])
inv_T_ticks = 1.0 / temp_ticks
tick_labels = [f"1/{t}" for t in temp_ticks]

# Plot
plot = (
    ggplot()
    + geom_line(aes(x="inv_T", y="ln_k"), data=df_fit, color="#306998", size=1.8, alpha=0.7)
    + geom_point(aes(x="inv_T", y="ln_k"), data=df_points, fill="#306998", color="white", size=6, shape=21, stroke=1.2)
    + geom_text(
        aes(x="x", y="y", label="label"), data=df_annotation, size=12, color="#333333", family="monospace", hjust=0
    )
    + labs(x="1/T (K⁻¹)", y="ln(k)", title="line-arrhenius · letsplot · pyplots.ai")
    + scale_x_continuous(breaks=inv_T_ticks.tolist(), labels=[f"{v:.2e}" for v in inv_T_ticks])
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
