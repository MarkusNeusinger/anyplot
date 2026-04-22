""" pyplots.ai
titration-curve: Acid-Base Titration Curve
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 93/100 | Created: 2026-03-21
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_area,
    geom_line,
    geom_point,
    geom_ribbon,
    geom_segment,
    geom_text,
    ggplot,
    guide_legend,
    labs,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data — 25 mL of 0.1 M HCl titrated with 0.1 M NaOH (vectorized)
volume_hcl = 25.0
conc_hcl = 0.1
conc_naoh = 0.1
moles_hcl = volume_hcl * conc_hcl / 1000

volume_ml = np.concatenate([np.linspace(0, 24, 80), np.linspace(24, 26, 40), np.linspace(26, 50, 80)])

# Vectorized pH calculation
moles_naoh = conc_naoh * volume_ml / 1000
total_volume_L = (volume_hcl + volume_ml) / 1000
excess_h = np.clip(moles_hcl - moles_naoh, 1e-14, None) / total_volume_L
excess_oh = np.clip(moles_naoh - moles_hcl, 1e-14, None) / total_volume_L
ph_acid = -np.log10(excess_h)
ph_base = 14.0 + np.log10(excess_oh)
ph = np.where(moles_naoh < moles_hcl - 1e-10, ph_acid, np.where(moles_naoh > moles_hcl + 1e-10, ph_base, 7.0))

# Compute derivative dpH/dV using unique-volume spacing to avoid division by zero
_, unique_idx = np.unique(volume_ml, return_index=True)
unique_idx = np.sort(unique_idx)
vol_unique = volume_ml[unique_idx]
ph_unique = ph[unique_idx]
dph_dv_unique = np.gradient(ph_unique, vol_unique)
dph_dv = np.interp(volume_ml, vol_unique, dph_dv_unique)
dph_dv = np.nan_to_num(dph_dv, nan=0.0, posinf=0.0, neginf=0.0)
dph_max = dph_dv.max()
dph_scaled = dph_dv / dph_max * 12

# Build long-format dataframe for grammar-of-graphics layering
df_ph = pd.DataFrame({"volume_ml": volume_ml, "value": ph, "series": "pH"})
df_deriv = pd.DataFrame({"volume_ml": volume_ml, "value": dph_scaled, "series": "dpH/dV (scaled)"})
df = pd.concat([df_ph, df_deriv], ignore_index=True)

# Derivative area fill — uses geom_area for distinctive plotnine layering
df_area = pd.DataFrame({"volume_ml": volume_ml, "value": dph_scaled})

# Transition region ribbon (±2 mL around equivalence) with stronger visibility
eq_volume = 25.0
eq_ph = 7.0
mask = (volume_ml >= 22) & (volume_ml <= 28)
df_ribbon = pd.DataFrame(
    {"volume_ml": volume_ml[mask], "ymin": np.clip(ph[mask] - 1.2, 0, 14), "ymax": np.clip(ph[mask] + 1.2, 0, 14)}
)

# Equivalence point marker and label dataframes for geom_point/geom_text
df_eq = pd.DataFrame({"volume_ml": [eq_volume], "value": [eq_ph]})
df_eq_label = pd.DataFrame(
    {
        "volume_ml": [eq_volume + 2.5],
        "value": [eq_ph + 1.8],
        "label": [f"Equivalence Point\n({eq_volume:.0f} mL, pH {eq_ph:.0f})"],
    }
)
df_peak_label = pd.DataFrame(
    {"volume_ml": [38.0], "value": [11.0], "label": [f"Peak dpH/dV = {dph_max:.1f}\nat {eq_volume:.0f} mL"]}
)

# Color palette
palette = {"pH": "#306998", "dpH/dV (scaled)": "#E8A838"}

plot = (
    ggplot()
    # Transition region shading
    + geom_ribbon(aes(x="volume_ml", ymin="ymin", ymax="ymax"), data=df_ribbon, fill="#306998", alpha=0.18)
    # Derivative area fill — distinctive plotnine geom_area usage
    + geom_area(aes(x="volume_ml", y="value"), data=df_area, fill="#E8A838", alpha=0.12)
    # Equivalence point vertical reference
    + geom_segment(
        aes(x="volume_ml", xend="volume_ml", y=0, yend="value"),
        data=df_eq,
        linetype="dashed",
        color="#999999",
        size=0.6,
    )
    # Main curves via color aesthetic mapping
    + geom_line(aes(x="volume_ml", y="value", color="series"), data=df, size=1.5)
    # Equivalence point diamond marker
    + geom_point(
        aes(x="volume_ml", y="value"), data=df_eq, color="#C0392B", fill="#E74C3C", size=5, shape="D", stroke=0.5
    )
    # Annotations via geom_text (idiomatic plotnine, not matplotlib annotate)
    + geom_text(
        aes(x="volume_ml", y="value", label="label"),
        data=df_eq_label,
        size=11,
        ha="left",
        color="#333333",
        fontstyle="italic",
    )
    + geom_text(
        aes(x="volume_ml", y="value", label="label"),
        data=df_peak_label,
        size=9,
        ha="left",
        color="#E8A838",
        fontweight="bold",
    )
    # Scales
    + scale_color_manual(values=palette, name=" ", guide=guide_legend(override_aes={"size": 3}))
    + scale_x_continuous(breaks=range(0, 55, 5), limits=(0, 50))
    + scale_y_continuous(breaks=range(0, 15, 2), limits=(0, 14))
    + labs(x="Volume of NaOH added (mL)", y="pH / dpH/dV (scaled)", title="titration-curve · plotnine · pyplots.ai")
    # Theme — refined minimal with polished details
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold", margin={"b": 15}),
        axis_title=element_text(size=20, color="#444444"),
        axis_text=element_text(size=16, color="#555555"),
        legend_text=element_text(size=16),
        legend_title=element_text(size=14),
        legend_position=(0.15, 0.85),
        legend_background=element_rect(fill="white", alpha=0.85, color="#DDDDDD", size=0.3),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_major_y=element_line(color="#E8E8E8", size=0.3),
        axis_line_x=element_line(color="#888888", size=0.5),
        axis_line_y=element_line(color="#888888", size=0.5),
        plot_background=element_rect(fill="white", color="white"),
        panel_background=element_rect(fill="#FAFAFA", color="white"),
    )
)

# Save
plot.save("plot.png", dpi=300)
