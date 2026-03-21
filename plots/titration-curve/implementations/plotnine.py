"""pyplots.ai
titration-curve: Acid-Base Titration Curve
Library: plotnine | Python 3.13
Quality: pending | Created: 2026-03-21
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_text,
    geom_line,
    geom_point,
    geom_vline,
    ggplot,
    labs,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — 25 mL of 0.1 M HCl titrated with 0.1 M NaOH
volume_hcl = 25.0
conc_hcl = 0.1
conc_naoh = 0.1
moles_hcl = volume_hcl * conc_hcl / 1000

volume_ml = np.concatenate([np.linspace(0, 24, 80), np.linspace(24, 26, 40), np.linspace(26, 50, 80)])

ph = np.zeros_like(volume_ml)
for i, v in enumerate(volume_ml):
    moles_naoh = conc_naoh * v / 1000
    total_volume_L = (volume_hcl + v) / 1000
    if v == 0:
        ph[i] = -np.log10(conc_hcl * volume_hcl / (volume_hcl + v))
    elif moles_naoh < moles_hcl:
        excess_h = (moles_hcl - moles_naoh) / total_volume_L
        ph[i] = -np.log10(excess_h)
    elif np.isclose(moles_naoh, moles_hcl, atol=1e-10):
        ph[i] = 7.0
    else:
        excess_oh = (moles_naoh - moles_hcl) / total_volume_L
        poh = -np.log10(excess_oh)
        ph[i] = 14.0 - poh

df = pd.DataFrame({"volume_ml": volume_ml, "ph": ph})

# Equivalence point
eq_volume = 25.0
eq_ph = 7.0

# Plot
plot = (
    ggplot(df, aes(x="volume_ml", y="ph"))
    + geom_line(color="#306998", size=1.5)
    + geom_vline(xintercept=eq_volume, linetype="dashed", color="#888888", size=0.8)
    + geom_point(
        aes(x="volume_ml", y="ph"),
        data=pd.DataFrame({"volume_ml": [eq_volume], "ph": [eq_ph]}),
        color="#E74C3C",
        size=4,
    )
    + annotate(
        "text",
        x=eq_volume + 1.5,
        y=eq_ph + 1.2,
        label=f"Equivalence Point\n({eq_volume:.0f} mL, pH {eq_ph:.0f})",
        size=12,
        ha="left",
        color="#333333",
    )
    + scale_x_continuous(breaks=range(0, 55, 5), limits=(0, 50))
    + scale_y_continuous(breaks=range(0, 15, 2), limits=(0, 14))
    + labs(
        x="Volume of NaOH added (mL)", y="pH", title="HCl + NaOH Titration · titration-curve · plotnine · pyplots.ai"
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=22, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_blank(),
    )
)

# Save
plot.save("plot.png", dpi=300)
