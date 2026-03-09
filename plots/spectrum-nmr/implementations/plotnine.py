""" pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-09
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_x_reverse,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - synthetic 1H NMR spectrum of ethanol (CH3CH2OH)
np.random.seed(42)
chemical_shift = np.linspace(0, 12, 6000)

# Lorentzian peak shape: amplitude * width^2 / ((x - center)^2 + width^2)
w = 0.015  # default peak width
intensity = np.zeros_like(chemical_shift)

# TMS reference peak at 0 ppm (singlet)
w_tms = 0.012
intensity += 0.4 * w_tms**2 / ((chemical_shift - 0.0) ** 2 + w_tms**2)

# CH3 triplet near 1.18 ppm (3 peaks, ratio 1:2:1)
triplet_center = 1.18
j_coupling = 0.07
intensity += 0.7 * w**2 / ((chemical_shift - (triplet_center - j_coupling)) ** 2 + w**2)
intensity += 1.4 * w**2 / ((chemical_shift - triplet_center) ** 2 + w**2)
intensity += 0.7 * w**2 / ((chemical_shift - (triplet_center + j_coupling)) ** 2 + w**2)

# CH2 quartet near 3.69 ppm (4 peaks, ratio 1:3:3:1)
quartet_center = 3.69
intensity += 0.35 * w**2 / ((chemical_shift - (quartet_center - 1.5 * j_coupling)) ** 2 + w**2)
intensity += 1.05 * w**2 / ((chemical_shift - (quartet_center - 0.5 * j_coupling)) ** 2 + w**2)
intensity += 1.05 * w**2 / ((chemical_shift - (quartet_center + 0.5 * j_coupling)) ** 2 + w**2)
intensity += 0.35 * w**2 / ((chemical_shift - (quartet_center + 1.5 * j_coupling)) ** 2 + w**2)

# OH singlet near 2.61 ppm
intensity += 0.55 * w**2 / ((chemical_shift - 2.61) ** 2 + w**2)

# Add slight baseline noise
intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.maximum(intensity, 0)

df = pd.DataFrame({"chemical_shift": chemical_shift, "intensity": intensity})

# Peak annotation data using DataFrames for geom_text and geom_segment
labels_df = pd.DataFrame(
    {
        "x": [triplet_center, quartet_center, 2.61, 0.0],
        "y": [1.55, 1.2, 0.70, 0.48],
        "peak_y": [1.40, 1.05, 0.55, 0.40],
        "label": [
            "CH\u2083 (triplet)\n1.18 ppm",
            "CH\u2082 (quartet)\n3.69 ppm",
            "OH (singlet)\n2.61 ppm",
            "TMS\n0.00",
        ],
        "group": ["main", "main", "main", "ref"],
    }
)

main_labels = labels_df[labels_df["group"] == "main"]
ref_labels = labels_df[labels_df["group"] == "ref"]

# Plot
plot = (
    ggplot(df, aes(x="chemical_shift", y="intensity"))
    + geom_line(color="#306998", size=0.9)
    # Peak markers at top of each peak group
    + geom_point(
        data=labels_df, mapping=aes(x="x", y="peak_y"), color="#306998", size=2.5, shape="o", inherit_aes=False
    )
    # Connector segments from peak tops to labels
    + geom_segment(
        data=labels_df,
        mapping=aes(x="x", xend="x", y="peak_y", yend="y"),
        color="#c0c0c0",
        size=0.4,
        linetype="dotted",
        inherit_aes=False,
    )
    # Main peak labels using geom_text (grammar of graphics approach)
    + geom_text(
        data=main_labels,
        mapping=aes(x="x", y="y", label="label"),
        size=11,
        color="#1e4d6d",
        fontweight="bold",
        va="bottom",
        ha="center",
        inherit_aes=False,
    )
    # TMS reference label (lighter, smaller)
    + geom_text(
        data=ref_labels,
        mapping=aes(x="x", y="y", label="label"),
        size=10,
        color="#555555",
        va="bottom",
        ha="center",
        inherit_aes=False,
    )
    + scale_x_reverse(limits=(12, -0.5), breaks=list(range(13)))
    + scale_y_continuous(breaks=[], limits=(-0.05, 1.85))
    + labs(
        x="Chemical Shift (ppm)",
        y="Intensity",
        title="\xb9H NMR of Ethanol \u00b7 spectrum-nmr \u00b7 plotnine \u00b7 pyplots.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14, color="#2d2d2d"),
        axis_title_x=element_text(size=20, color="#2d2d2d"),
        axis_title_y=element_text(size=20, color="#888888"),
        axis_text_x=element_text(size=16, color="#555555"),
        axis_text_y=element_blank(),
        plot_title=element_text(size=24, weight="bold", color="#1a1a1a"),
        panel_background=element_rect(fill="#fafafa", color="none"),
        plot_background=element_rect(fill="#ffffff", color="none"),
        panel_grid_major_x=element_line(color="#e8e8e8", size=0.3),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        axis_line_x=element_line(color="#999999", size=0.6),
        axis_ticks_major_x=element_line(color="#999999", size=0.4),
        axis_ticks_major_y=element_blank(),
        plot_margin=0.04,
    )
)

plot.save("plot.png", dpi=300, verbose=False)
