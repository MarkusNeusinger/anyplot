"""pyplots.ai
histogram-capability: Process Capability Plot with Specification Limits
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-19
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    after_stat,
    annotate,
    element_blank,
    element_line,
    element_text,
    geom_histogram,
    geom_line,
    geom_vline,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from scipy import stats


# Data - shaft diameter measurements (mm)
np.random.seed(42)
target = 10.00
lsl = 9.95
usl = 10.05
measurements = np.random.normal(loc=10.002, scale=0.012, size=200)

# Capability indices
mean = np.mean(measurements)
sigma = np.std(measurements, ddof=1)
cp = (usl - lsl) / (6 * sigma)
cpk = min((usl - mean) / (3 * sigma), (mean - lsl) / (3 * sigma))

df = pd.DataFrame({"diameter": measurements})

# Normal distribution curve data
x_curve = np.linspace(mean - 4 * sigma, mean + 4 * sigma, 300)
y_curve = stats.norm.pdf(x_curve, mean, sigma)

# Scale curve to match histogram density
bin_width = (measurements.max() - measurements.min()) / 25
curve_df = pd.DataFrame({"x": x_curve, "y": y_curve})

# Plot
plot = (
    ggplot(df, aes(x="diameter"))
    + geom_histogram(aes(y=after_stat("density")), bins=25, fill="#306998", color="white", alpha=0.7)
    + geom_line(data=curve_df, mapping=aes(x="x", y="y"), color="#1a3d5c", size=1.8)
    + geom_vline(xintercept=lsl, linetype="dashed", color="#c0392b", size=1.2)
    + geom_vline(xintercept=usl, linetype="dashed", color="#c0392b", size=1.2)
    + geom_vline(xintercept=target, linetype="dashed", color="#27ae60", size=1.0)
    + annotate("text", x=lsl - 0.003, y=max(y_curve) * 0.95, label="LSL", size=12, color="#c0392b", fontweight="bold")
    + annotate("text", x=usl + 0.003, y=max(y_curve) * 0.95, label="USL", size=12, color="#c0392b", fontweight="bold")
    + annotate(
        "text", x=target + 0.003, y=max(y_curve) * 0.85, label="Target", size=11, color="#27ae60", fontweight="bold"
    )
    + annotate(
        "text",
        x=mean + 3.2 * sigma,
        y=max(y_curve) * 0.70,
        label=f"Cp = {cp:.2f}\nCpk = {cpk:.2f}\nμ = {mean:.4f}\nσ = {sigma:.4f}",
        size=12,
        color="#2c3e50",
        ha="left",
    )
    + labs(x="Shaft Diameter (mm)", y="Density", title="histogram-capability · plotnine · pyplots.ai")
    + scale_x_continuous(breaks=np.round(np.arange(9.94, 10.07, 0.01), 2).tolist())
    + scale_y_continuous(expand=(0, 0, 0.1, 0))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        plot_title=element_text(size=24),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#cccccc", alpha=0.2, size=0.5),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
