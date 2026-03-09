"""pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-09
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
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


# Lorentzian peak shape for NMR signals
def _peak(center, amplitude, width=0.015):
    return amplitude * width**2 / ((chemical_shift - center) ** 2 + width**2)


# TMS reference peak at 0 ppm (singlet)
intensity = _peak(0.0, 0.4, width=0.012)

# CH3 triplet near 1.18 ppm (3 peaks, ratio 1:2:1)
triplet_center = 1.18
j_coupling = 0.07
intensity += _peak(triplet_center - j_coupling, 0.7)
intensity += _peak(triplet_center, 1.4)
intensity += _peak(triplet_center + j_coupling, 0.7)

# CH2 quartet near 3.69 ppm (4 peaks, ratio 1:3:3:1)
quartet_center = 3.69
intensity += _peak(quartet_center - 1.5 * j_coupling, 0.35)
intensity += _peak(quartet_center - 0.5 * j_coupling, 1.05)
intensity += _peak(quartet_center + 0.5 * j_coupling, 1.05)
intensity += _peak(quartet_center + 1.5 * j_coupling, 0.35)

# OH singlet near 2.61 ppm
intensity += _peak(2.61, 0.55)

# Add slight baseline noise
intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.maximum(intensity, 0)

df = pd.DataFrame({"chemical_shift": chemical_shift, "intensity": intensity})

# Plot
plot = (
    ggplot(df, aes(x="chemical_shift", y="intensity"))
    + geom_line(color="#306998", size=0.6)
    + scale_x_reverse(limits=(12, -0.5), breaks=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
    + scale_y_continuous(breaks=[], limits=(-0.05, 1.8))
    # Peak labels
    + annotate("text", x=0.0, y=0.48, label="TMS\n0.00", size=10, color="#555555", ha="center")
    + annotate(
        "text",
        x=triplet_center,
        y=1.55,
        label="CH\u2083 (triplet)\n1.18 ppm",
        size=11,
        color="#1e4d6d",
        ha="center",
        fontweight="bold",
    )
    + annotate(
        "text",
        x=quartet_center,
        y=1.2,
        label="CH\u2082 (quartet)\n3.69 ppm",
        size=11,
        color="#1e4d6d",
        ha="center",
        fontweight="bold",
    )
    + annotate(
        "text", x=2.61, y=0.7, label="OH (singlet)\n2.61 ppm", size=11, color="#1e4d6d", ha="center", fontweight="bold"
    )
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
