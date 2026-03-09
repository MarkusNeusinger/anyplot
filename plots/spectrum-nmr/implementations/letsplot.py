""" pyplots.ai
spectrum-nmr: NMR Spectrum (Nuclear Magnetic Resonance)
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-09
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Synthetic 1H NMR spectrum of ethanol (CH3CH2OH)
np.random.seed(42)
chemical_shift = np.linspace(5.0, -0.5, 5000)
w = 0.008  # Lorentzian half-width for sharp peaks

# Build spectrum by summing Lorentzian peaks: A * w^2 / ((x - c)^2 + w^2)
intensity = np.zeros_like(chemical_shift)

# TMS reference peak at 0 ppm
intensity += 1.0 * w**2 / ((chemical_shift - 0.0) ** 2 + w**2)

# CH3 triplet near 1.18 ppm (J-coupling = 0.06 ppm, intensity ratio 1:2:1)
j = 0.06
for center, amp in [(1.18 - j, 0.75), (1.18, 1.5), (1.18 + j, 0.75)]:
    intensity += amp * w**2 / ((chemical_shift - center) ** 2 + w**2)

# CH2 quartet near 3.69 ppm (J-coupling = 0.06 ppm, intensity ratio 1:3:3:1)
for center, amp in [(3.69 - 1.5 * j, 0.4), (3.69 - 0.5 * j, 1.2), (3.69 + 0.5 * j, 1.2), (3.69 + 1.5 * j, 0.4)]:
    intensity += amp * w**2 / ((chemical_shift - center) ** 2 + w**2)

# OH singlet near 2.61 ppm (broader due to exchange)
w_oh = 0.012
intensity += 0.6 * w_oh**2 / ((chemical_shift - 2.61) ** 2 + w_oh**2)

# Add subtle baseline noise
intensity += np.random.normal(0, 0.003, len(chemical_shift))
intensity = np.clip(intensity, 0, None)

df = pd.DataFrame({"chemical_shift": chemical_shift, "intensity": intensity})

# Peak labels with increased y-offsets to avoid overlap
peak_labels = pd.DataFrame(
    {
        "x": [0.0, 1.18, 2.61, 3.69],
        "y": [1.15, 1.60, 0.75, 1.38],
        "label": [
            "TMS\n0.00 ppm",
            "CH\u2083 (triplet)\n1.18 ppm",
            "OH (singlet)\n2.61 ppm",
            "CH\u2082 (quartet)\n3.69 ppm",
        ],
    }
)

# Plot - using geom_area for filled spectrum (lets-plot distinctive feature)
plot = (
    ggplot(df, aes(x="chemical_shift", y="intensity"))  # noqa: F405
    + geom_area(fill="#306998", alpha=0.15)  # noqa: F405
    + geom_line(color="#306998", size=1.2)  # noqa: F405
    + geom_text(  # noqa: F405
        data=peak_labels,
        mapping=aes(x="x", y="y", label="label"),  # noqa: F405
        size=11,
        color="#1a1a1a",
        fontface="bold",
    )
    + labs(  # noqa: F405
        x="\u03b4 Chemical Shift (ppm)",
        y="Intensity (a.u.)",
        title="Ethanol \u00b9H NMR \u00b7 spectrum-nmr \u00b7 letsplot \u00b7 pyplots.ai",
    )
    + scale_x_reverse(limits=[-0.5, 5.0])  # noqa: F405
    + scale_y_continuous(expand=[0.02, 0, 0.15, 0])  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20, color="#333333"),  # noqa: F405
        axis_text=element_text(size=16, color="#555555"),  # noqa: F405
        plot_title=element_text(size=24, color="#222222", face="bold"),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_ticks=element_blank(),  # noqa: F405
        plot_margin=[30, 40, 20, 20],  # noqa: F405
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
