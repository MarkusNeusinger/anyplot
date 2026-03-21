"""pyplots.ai
titration-curve: Acid-Base Titration Curve
Library: plotnine 0.15.3 | Python 3.14.3
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
    geom_point,
    geom_ribbon,
    geom_vline,
    ggplot,
    guide_legend,
    labs,
    scale_color_manual,
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

# Compute derivative dpH/dV and scale to fit pH axis
dph_dv = np.gradient(ph, volume_ml)
dph_dv = np.nan_to_num(dph_dv, nan=0.0, posinf=0.0, neginf=0.0)
dph_max = dph_dv.max()
dph_scaled = dph_dv / dph_max * 12  # Scale peak to 12 on pH axis

# Build main dataframe with both curves
df = pd.DataFrame(
    {
        "volume_ml": np.tile(volume_ml, 2),
        "value": np.concatenate([ph, dph_scaled]),
        "series": ["pH"] * len(volume_ml) + ["dpH/dV (scaled)"] * len(volume_ml),
    }
)

# Shading for steep transition region (±2 mL around equivalence), clipped to curve
eq_volume = 25.0
eq_ph = 7.0
mask = (volume_ml >= 23) & (volume_ml <= 27)
ph_in_region = ph[mask]
df_ribbon = pd.DataFrame(
    {
        "volume_ml": volume_ml[mask],
        "ymin": np.clip(ph_in_region - 0.8, 0, 14),
        "ymax": np.clip(ph_in_region + 0.8, 0, 14),
    }
)

# Equivalence point data
df_eq = pd.DataFrame({"volume_ml": [eq_volume], "value": [eq_ph], "series": ["pH"]})

# Plot
palette = {"pH": "#306998", "dpH/dV (scaled)": "#E8A838"}

plot = (
    ggplot()
    + geom_ribbon(aes(x="volume_ml", ymin="ymin", ymax="ymax"), data=df_ribbon, fill="#306998", alpha=0.15)
    + geom_vline(xintercept=eq_volume, linetype="dashed", color="#AAAAAA", size=0.7)
    + geom_line(aes(x="volume_ml", y="value", color="series"), data=df, size=1.5)
    + geom_point(aes(x="volume_ml", y="value"), data=df_eq, color="#C0392B", size=5, shape="D")
    + annotate(
        "text",
        x=eq_volume + 2,
        y=eq_ph + 1.5,
        label=f"Equivalence Point\n({eq_volume:.0f} mL, pH {eq_ph:.0f})",
        size=11,
        ha="left",
        color="#333333",
        fontstyle="italic",
    )
    + scale_color_manual(values=palette, name=" ", guide=guide_legend(override_aes={"size": 3}))
    + scale_x_continuous(breaks=range(0, 55, 5), limits=(0, 50))
    + scale_y_continuous(breaks=range(0, 15, 2), limits=(0, 14))
    + labs(x="Volume of NaOH added (mL)", y="pH / dpH/dV (scaled)", title="titration-curve · plotnine · pyplots.ai")
    + annotate(
        "text",
        x=38,
        y=11,
        label=f"Peak dpH/dV = {dph_max:.1f}\nat {eq_volume:.0f} mL",
        size=9,
        ha="left",
        color="#E8A838",
        fontweight="bold",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", margin={"b": 15}),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
        legend_position=(0.15, 0.85),
        legend_background=element_rect(fill="white", alpha=0.8),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.4),
        axis_line_x=element_line(color="#888888", size=0.5),
        axis_line_y=element_line(color="#888888", size=0.5),
        plot_background=element_rect(fill="white", color="white"),
    )
)

# Save
plot.save("plot.png", dpi=300)
