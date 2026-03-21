""" pyplots.ai
titration-curve: Acid-Base Titration Curve
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-21
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Strong acid/strong base: 25 mL of 0.1 M HCl titrated with 0.1 M NaOH
concentration_acid = 0.1
volume_acid = 25.0
concentration_base = 0.1

volume_naoh = np.linspace(0, 50, 200)
ph = np.zeros_like(volume_naoh)

for i, v in enumerate(volume_naoh):
    moles_acid = concentration_acid * volume_acid / 1000
    moles_base = concentration_base * v / 1000
    total_volume = (volume_acid + v) / 1000

    if moles_base < moles_acid:
        excess_h = (moles_acid - moles_base) / total_volume
        ph[i] = -np.log10(excess_h)
    elif np.isclose(moles_base, moles_acid, atol=1e-8):
        ph[i] = 7.0
    else:
        excess_oh = (moles_base - moles_acid) / total_volume
        poh = -np.log10(excess_oh)
        ph[i] = 14.0 - poh

# Derivative (dpH/dV) for secondary overlay
dpH = np.gradient(ph, volume_naoh)

# Equivalence point (strong acid/strong base → pH 7.0)
equiv_volume = volume_acid * concentration_acid / concentration_base
equiv_ph = 7.0

# Normalize derivative to fit on pH scale (0-14) for visual overlay
dpH_max = np.max(dpH)
dpH_normalized = dpH / dpH_max * 6.0

df = pd.DataFrame({"volume_ml": volume_naoh, "ph": ph, "dpH_normalized": dpH_normalized})

# Equivalence point data
equiv_point = pd.DataFrame(
    {
        "volume_ml": [equiv_volume],
        "ph": [equiv_ph],
        "label": [f"Equivalence Point\n{equiv_volume:.0f} mL, pH {equiv_ph:.1f}"],
    }
)

# Colors
COLOR_CURVE = "#306998"
COLOR_DERIV = "#D35400"
COLOR_EQUIV = "#C0392B"
COLOR_BUFFER = "#306998"

# Plot
plot = (
    ggplot()  # noqa: F405
    + geom_area(  # noqa: F405
        aes(x="volume_ml", y="ph"),  # noqa: F405
        data=df[(df["volume_ml"] >= 0) & (df["volume_ml"] <= 50)],
        fill=COLOR_BUFFER,
        alpha=0.0,
    )
    + geom_line(  # noqa: F405
        aes(x="volume_ml", y="ph"),  # noqa: F405
        data=df,
        color=COLOR_CURVE,
        size=2.5,
        tooltips=layer_tooltips()  # noqa: F405
        .format("volume_ml", ".1f")
        .format("ph", ".2f")
        .line("Volume: @volume_ml mL")
        .line("pH: @ph"),
    )
    + geom_line(  # noqa: F405
        aes(x="volume_ml", y="dpH_normalized"),  # noqa: F405
        data=df,
        color=COLOR_DERIV,
        size=1.5,
        linetype="dashed",
        alpha=0.8,
        tooltips=layer_tooltips().line("dpH/dV (scaled)"),  # noqa: F405
    )
    + geom_vline(  # noqa: F405
        xintercept=equiv_volume, color=COLOR_EQUIV, size=1.0, linetype="dashed", alpha=0.7
    )
    + geom_point(  # noqa: F405
        aes(x="volume_ml", y="ph"),  # noqa: F405
        data=equiv_point,
        color=COLOR_EQUIV,
        size=10,
        shape=18,
    )
    + geom_label(  # noqa: F405
        aes(x="volume_ml", y="ph", label="label"),  # noqa: F405
        data=equiv_point,
        size=16,
        color=COLOR_EQUIV,
        fill="#FADBD8",
        label_padding=0.4,
        label_r=0.15,
        fontface="bold",
        nudge_x=8,
        nudge_y=1.5,
    )
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=pd.DataFrame({"x": [42], "y": [4.5], "label": ["dpH/dV (scaled)"]}),
        size=14,
        color=COLOR_DERIV,
        fontface="italic",
    )
    + scale_x_continuous(  # noqa: F405
        limits=[0, 50], breaks=list(range(0, 55, 5))
    )
    + scale_y_continuous(  # noqa: F405
        limits=[0, 14], breaks=list(range(0, 15, 2))
    )
    + labs(  # noqa: F405
        x="Volume of NaOH added (mL)", y="pH", title="titration-curve \u00b7 letsplot \u00b7 pyplots.ai"
    )
    + flavor_high_contrast_light()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20, face="bold"),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        plot_title=element_text(size=26, hjust=0.5, face="bold"),  # noqa: F405
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_border=element_blank(),  # noqa: F405
        axis_line=element_line(color="#AAAAAA", size=0.5),  # noqa: F405
        plot_margin=[30, 30, 10, 20],
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
