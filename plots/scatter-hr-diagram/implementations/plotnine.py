""" pyplots.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 88/100 | Created: 2026-03-07
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_text,
    geom_point,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_x_reverse,
    scale_y_log10,
    theme,
    theme_minimal,
)


# Data
np.random.seed(42)

# Main sequence: L ~ T^3.5 (approx), with scatter
n_main = 250
main_log_temp = np.random.uniform(np.log10(2800), np.log10(38000), n_main)
main_temp = 10**main_log_temp
main_log_lum = 3.5 * (main_log_temp - np.log10(5778)) + np.random.normal(0, 0.15, n_main)
main_lum = 10**main_log_lum

# Red giants (cool but luminous)
n_giants = 60
giant_temp = np.random.uniform(3200, 5200, n_giants)
giant_lum = 10 ** np.random.uniform(1.0, 3.0, n_giants)

# Supergiants (very luminous, broad temp range)
n_super = 25
super_temp = np.random.uniform(3500, 28000, n_super)
super_lum = 10 ** np.random.uniform(3.5, 5.5, n_super)

# White dwarfs (hot but very dim)
n_wd = 40
wd_temp = np.random.uniform(5000, 30000, n_wd)
wd_lum = 10 ** np.random.uniform(-4, -1.5, n_wd)


spectral_colors = {
    "O": "#4A6FA5",
    "B": "#7096C8",
    "A": "#A8B8D0",
    "F": "#D4C86A",
    "G": "#F0B830",
    "K": "#E07020",
    "M": "#CC3333",
}


temperatures = np.concatenate([main_temp, giant_temp, super_temp, wd_temp])
luminosities = np.concatenate([main_lum, giant_lum, super_lum, wd_lum])
regions = ["Main Sequence"] * n_main + ["Red Giants"] * n_giants + ["Supergiants"] * n_super + ["White Dwarfs"] * n_wd

spectral_bins = [0, 3700, 5200, 6000, 7500, 10000, 30000, np.inf]
spectral_labels = ["M", "K", "G", "F", "A", "B", "O"]
spectral = pd.cut(temperatures, bins=spectral_bins, labels=spectral_labels, ordered=False)

df = pd.DataFrame(
    {
        "temperature": temperatures,
        "luminosity": luminosities,
        "region": regions,
        "spectral_type": pd.Categorical(spectral, categories=["O", "B", "A", "F", "G", "K", "M"]),
    }
)

# Sun reference
sun = pd.DataFrame({"temperature": [5778], "luminosity": [1.0], "label": ["Sun"]})

# Region labels
region_labels = pd.DataFrame(
    {
        "temperature": [9000, 3200, 15000, 18000],
        "luminosity": [0.15, 1500, 120000, 0.003],
        "label": ["Main Sequence", "Red Giants", "Supergiants", "White Dwarfs"],
    }
)

# Plot
plot = (
    ggplot(df, aes(x="temperature", y="luminosity", color="spectral_type"))
    + geom_point(size=4, alpha=0.65, stroke=0.3)
    + geom_point(
        data=sun,
        mapping=aes(x="temperature", y="luminosity"),
        color="black",
        fill="#F0B830",
        size=7,
        shape="*",
        stroke=1.5,
        inherit_aes=False,
    )
    + geom_text(
        data=sun,
        mapping=aes(x="temperature", y="luminosity", label="label"),
        color="black",
        size=13,
        nudge_x=2500,
        nudge_y=0.4,
        inherit_aes=False,
        fontweight="bold",
    )
    + geom_text(
        data=region_labels,
        mapping=aes(x="temperature", y="luminosity", label="label"),
        color="#555555",
        size=12,
        fontstyle="italic",
        inherit_aes=False,
    )
    + scale_x_reverse()
    + scale_y_log10()
    + scale_color_manual(values=spectral_colors, name="Spectral Type")
    + labs(x="Surface Temperature (K)", y="Luminosity (L☉)", title="scatter-hr-diagram · plotnine · pyplots.ai")
    + guides(color=guide_legend(override_aes={"size": 5, "alpha": 1}))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="right",
        panel_grid_minor=element_blank(),
        panel_grid_major=element_line(color="#E0E0E0", size=0.5, alpha=0.3),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
