""" pyplots.ai
pp-basic: Probability-Probability (P-P) Plot
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-15
"""

from math import erf, sqrt

import numpy as np
import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: pharmaceutical tablet weight measurements (mg) from a filling machine
# Real-world QC scenario - checking if weights follow a normal distribution
np.random.seed(42)
n_samples = 200

# Tablet weights: target 500mg, slight right skew from occasional overfills
normal_fill = np.random.normal(500, 8, 160)
overfill_events = np.random.exponential(5, 40) + 498
observed = np.concatenate([normal_fill, overfill_events])
observed = observed[:n_samples]

# Sort observed data
observed_sorted = np.sort(observed)

# Compute empirical CDF using plotting position formula i/(n+1)
empirical_cdf = np.arange(1, n_samples + 1) / (n_samples + 1)

# Fit normal distribution (MLE: mean and std of data)
mu = np.mean(observed_sorted)
sigma = np.std(observed_sorted, ddof=0)

# Compute theoretical CDF values (normal CDF inline)
z_scores = (observed_sorted - mu) / (sigma * sqrt(2))
theoretical_cdf = 0.5 * (1 + np.vectorize(erf)(z_scores))

# Compute deviation from perfect fit for color mapping
deviation = empirical_cdf - theoretical_cdf

# Classify deviation region for annotation
region = np.where(np.abs(deviation) < 0.02, "Near fit", np.where(deviation > 0, "Above diagonal", "Below diagonal"))

# Create dataframe for P-P plot points
df_pp = pd.DataFrame(
    {
        "theoretical": theoretical_cdf,
        "empirical": empirical_cdf,
        "deviation": deviation,
        "abs_deviation": np.abs(deviation),
        "weight": observed_sorted,
        "region": region,
    }
)

# Confidence envelope around diagonal (approximate 95% Kolmogorov band)
ks_band = 1.36 / sqrt(n_samples)
envelope_x = np.linspace(0, 1, 100)
df_envelope = pd.DataFrame(
    {
        "x": envelope_x,
        "y_upper": np.minimum(envelope_x + ks_band, 1.0),
        "y_lower": np.maximum(envelope_x - ks_band, 0.0),
    }
)

# Reference line (perfect fit diagonal)
df_ref = pd.DataFrame({"x": [0, 1], "y": [0, 1]})

# Annotation for max deviation point
max_dev_idx = np.argmax(np.abs(deviation))
df_annotation = pd.DataFrame(
    {
        "x": [theoretical_cdf[max_dev_idx]],
        "y": [empirical_cdf[max_dev_idx]],
        "label": [f"Max deviation: {deviation[max_dev_idx]:+.3f}"],
    }
)

# Plot with lets-plot distinctive features: tooltips, flavor theme, text annotations
plot = (
    ggplot()
    + geom_ribbon(
        aes(x="x", ymin="y_lower", ymax="y_upper"),
        data=df_envelope,
        fill="#306998",
        alpha=0.2,
        size=0.3,
        tooltips=layer_tooltips().line("95% Kolmogorov band"),
    )
    + geom_line(aes(x="x", y="y"), data=df_ref, color="#A0A8B0", size=1.2, linetype="dashed", tooltips="none")
    + geom_point(
        aes(x="theoretical", y="empirical", color="deviation", size="abs_deviation"),
        data=df_pp,
        alpha=0.85,
        shape=16,
        tooltips=layer_tooltips()
        .format("weight", ".1f")
        .format("deviation", "+.4f")
        .line("@|@weight mg")
        .line("Deviation|@deviation")
        .line("@region"),
    )
    + geom_text(
        aes(x="x", y="y", label="label"), data=df_annotation, size=15, color="#E8E8E8", nudge_y=0.06, fontface="italic"
    )
    + scale_color_gradient2(
        low="#E86B56", mid="#C8CDD0", high="#5B9BD5", midpoint=0, name="Deviation\n(Empirical − Theoretical)"
    )
    + scale_size(range=[4.5, 8], guide="none")
    + labs(
        x="Theoretical CDF (Normal)",
        y="Empirical CDF",
        title="pp-basic \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="QC Check: Tablet Weight Distribution vs. Normal Reference (n=200)",
    )
    + scale_x_continuous(limits=[0, 1], breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + scale_y_continuous(limits=[0, 1], breaks=[0, 0.2, 0.4, 0.6, 0.8, 1.0])
    + coord_fixed(ratio=1)
    + flavor_darcula()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_subtitle=element_text(size=16),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_major=element_line(size=0.3),
        panel_grid_minor=element_blank(),
        legend_title=element_text(size=16),
        legend_text=element_text(size=14),
        legend_position="right",
    )
    + ggsize(1200, 1200)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
