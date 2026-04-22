""" pyplots.ai
histogram-basic: Basic Histogram
Library: letsplot 4.8.2 | Python 3.14.0
Quality: 94/100 | Created: 2025-12-23
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
    geom_histogram,
    geom_text,
    geom_vline,
    ggplot,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data — two cherry tree cultivars with distinct trunk diameters
np.random.seed(42)
cultivar_a = np.random.normal(28.5, 4.2, 350)  # Yoshino cherry (cm)
cultivar_b = np.random.normal(39.0, 5.5, 250)  # Kwanzan cherry (cm)

df = pd.DataFrame(
    {"diameter": np.concatenate([cultivar_a, cultivar_b]), "cultivar": ["Yoshino"] * 350 + ["Kwanzan"] * 250}
)

# Population means
mean_a = float(np.mean(cultivar_a))
mean_b = float(np.mean(cultivar_b))

# Tighter axis limits using percentiles (clips extreme outliers)
all_diameters = np.concatenate([cultivar_a, cultivar_b])
x_min = float(np.floor(np.percentile(all_diameters, 0.5)) - 1)
x_max = float(np.ceil(np.percentile(all_diameters, 99.5)) + 1)

# Colors
color_a = "#306998"  # Python Blue for Yoshino cultivar
color_b = "#B07430"  # Warm amber for Kwanzan cultivar

# Annotation positions — nudged right so text doesn't sit on the dashed line
annotations_a = pd.DataFrame({"x": [mean_a + 2.5], "y": [60], "label": [f"Yoshino avg {mean_a:.1f} cm"]})
annotations_b = pd.DataFrame({"x": [mean_b + 2.5], "y": [60], "label": [f"Kwanzan avg {mean_b:.1f} cm"]})

# Plot — two overlapping semi-transparent histograms to reveal bimodality
plot = (
    ggplot(df, aes(x="diameter", fill="cultivar"))
    + geom_histogram(
        bins=30,
        alpha=0.65,
        size=0.2,
        color="white",
        position="identity",
        tooltips=layer_tooltips()
        .format("..count..", "d")
        .format("^x", ".1f")
        .line("@|cultivar")
        .line("Count|@..count.."),
    )
    + scale_fill_manual(values={"Yoshino": color_a, "Kwanzan": color_b}, name="Cultivar")
    # Mean reference lines matching fill colors
    + geom_vline(xintercept=mean_a, color=color_a, size=1.2, linetype="dashed")
    + geom_vline(xintercept=mean_b, color=color_b, size=1.2, linetype="dashed")
    # Mean labels — color-coded to match fills
    + geom_text(
        data=annotations_a,
        mapping=aes(x="x", y="y", label="label"),
        size=11,
        color=color_a,
        fontface="bold",
        inherit_aes=False,
    )
    + geom_text(
        data=annotations_b,
        mapping=aes(x="x", y="y", label="label"),
        size=11,
        color=color_b,
        fontface="bold",
        inherit_aes=False,
    )
    + scale_x_continuous(name="Trunk Diameter (cm)", format=".0f", limits=[x_min, x_max])
    + scale_y_continuous(name="Frequency", format="d")
    + labs(
        title="histogram-basic · letsplot · pyplots.ai",
        subtitle="Bimodal distribution of cherry tree trunk diameters — two cultivars in the same orchard",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_subtitle=element_text(size=16, color="#666666"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=16, face="bold"),
        legend_text=element_text(size=14),
        legend_position=[0.88, 0.85],
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
