""" pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 81/100 | Created: 2026-03-19
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_area,
    geom_histogram,
    geom_text,
    geom_vline,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave
from scipy import stats


LetsPlot.setup_html()

# Data — shaft diameter measurements (mm)
np.random.seed(42)
lsl = 9.95
usl = 10.05
target = 10.00

measurements = np.random.normal(loc=10.002, scale=0.012, size=200)
sample_mean = float(np.mean(measurements))
sample_std = float(np.std(measurements, ddof=1))

# Capability indices
cp = (usl - lsl) / (6 * sample_std)
cpk = min((usl - sample_mean) / (3 * sample_std), (sample_mean - lsl) / (3 * sample_std))

df = pd.DataFrame({"measurement": measurements})

# Normal distribution curve fitted to data
x_curve = np.linspace(sample_mean - 4 * sample_std, sample_mean + 4 * sample_std, 300)
y_curve = stats.norm.pdf(x_curve, sample_mean, sample_std)

# Scale PDF to match histogram counts (bin_width * n_observations)
bin_width = (measurements.max() - measurements.min()) / 30
y_curve_scaled = y_curve * bin_width * len(measurements)

df_curve = pd.DataFrame({"x": x_curve, "y": y_curve_scaled})

# Annotation text
cap_text = f"Cp = {cp:.2f}  |  Cpk = {cpk:.2f}"
stats_text = f"Mean = {sample_mean:.4f} mm  |  Std = {sample_std:.4f} mm"

# Find y position for annotations
hist_counts, _ = np.histogram(measurements, bins=30)
y_max = float(hist_counts.max())

ann_df = pd.DataFrame({"x": [sample_mean], "y": [y_max * 0.95], "label": [cap_text]})

stats_ann_df = pd.DataFrame({"x": [sample_mean], "y": [y_max * 0.85], "label": [stats_text]})

# Plot
plot = (
    ggplot(df, aes(x="measurement"))
    + geom_histogram(
        bins=30,
        fill="#306998",
        color="white",
        alpha=0.7,
        size=0.3,
        tooltips=layer_tooltips().format("..count..", "d").format("^x", ".4f").line("Count|@..count.."),
    )
    + geom_area(
        data=df_curve,
        mapping=aes(x="x", y="y"),
        fill="#306998",
        alpha=0.15,
        color="#306998",
        size=1.5,
        inherit_aes=False,
    )
    # Specification limits
    + geom_vline(xintercept=lsl, color="#D64541", size=1.5, linetype="dashed")
    + geom_vline(xintercept=usl, color="#D64541", size=1.5, linetype="dashed")
    + geom_vline(xintercept=target, color="#27AE60", size=1.5, linetype="dashed")
    # Spec limit labels
    + geom_text(
        data=pd.DataFrame({"x": [lsl - 0.003], "y": [y_max * 0.7], "label": ["LSL\n9.950"]}),
        mapping=aes(x="x", y="y", label="label"),
        size=11,
        color="#D64541",
        fontface="bold",
        inherit_aes=False,
    )
    + geom_text(
        data=pd.DataFrame({"x": [usl + 0.003], "y": [y_max * 0.7], "label": ["USL\n10.050"]}),
        mapping=aes(x="x", y="y", label="label"),
        size=11,
        color="#D64541",
        fontface="bold",
        inherit_aes=False,
    )
    + geom_text(
        data=pd.DataFrame({"x": [target], "y": [y_max * 0.55], "label": ["Target\n10.000"]}),
        mapping=aes(x="x", y="y", label="label"),
        size=11,
        color="#27AE60",
        fontface="bold",
        inherit_aes=False,
    )
    # Capability indices annotation
    + geom_text(
        data=ann_df,
        mapping=aes(x="x", y="y", label="label"),
        size=13,
        color="#333333",
        fontface="bold",
        inherit_aes=False,
    )
    + geom_text(
        data=stats_ann_df, mapping=aes(x="x", y="y", label="label"), size=11, color="#666666", inherit_aes=False
    )
    + scale_x_continuous(name="Shaft Diameter (mm)", format=".3f")
    + scale_y_continuous(name="Frequency", format="d")
    + labs(
        title="histogram-capability · letsplot · pyplots.ai",
        subtitle="Process capability analysis — shaft diameter measurements against specification limits",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_subtitle=element_text(size=16, color="#666666"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_position="none",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.5),
        plot_background=element_rect(fill="white", color="white"),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
