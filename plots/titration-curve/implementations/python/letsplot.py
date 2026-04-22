""" pyplots.ai
titration-curve: Acid-Base Titration Curve
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-21
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

# Derivative (dpH/dV)
dpH = np.gradient(ph, volume_naoh)

# Equivalence point (strong acid/strong base -> pH 7.0)
equiv_volume = volume_acid * concentration_acid / concentration_base
equiv_ph = 7.0

# Scale derivative to secondary axis range (0-14 mapped from dpH values)
dpH_max = np.max(dpH)
dpH_scaled = dpH / dpH_max * 12.0

# Buffer region: slow pH change area before the steep rise
buffer_mask = (volume_naoh >= 2) & (volume_naoh <= 20)
df_buffer = pd.DataFrame({"volume_ml": volume_naoh[buffer_mask], "ph": ph[buffer_mask]})

# Acidic and basic region shading for visual hierarchy
df_acidic = pd.DataFrame({"volume_ml": [0, 50], "ymin": [0, 0], "ymax": [7, 7]})
df_basic = pd.DataFrame({"volume_ml": [0, 50], "ymin": [7, 7], "ymax": [14, 14]})

# Main data with series labels for legend
df_ph = pd.DataFrame({"volume_ml": volume_naoh, "y": ph, "series": "pH Curve"})
df_deriv = pd.DataFrame({"volume_ml": volume_naoh, "y": dpH_scaled, "series": "dpH/dV (scaled)"})

# Equivalence point data
equiv_point = pd.DataFrame(
    {
        "volume_ml": [equiv_volume],
        "ph": [equiv_ph],
        "label": [f"Equivalence Point\n{equiv_volume:.0f} mL, pH {equiv_ph:.1f}"],
    }
)

# Colors - refined palette
COLOR_CURVE = "#1B4F72"
COLOR_DERIV = "#E67E22"
COLOR_EQUIV = "#C0392B"
COLOR_BUFFER = "#2E86C1"
COLOR_ACIDIC = "#FDEDEC"
COLOR_BASIC = "#EBF5FB"

# Plot
plot = (
    ggplot()  # noqa: F405
    # Acidic/basic region shading for visual hierarchy
    + geom_rect(  # noqa: F405
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),  # noqa: F405
        data=pd.DataFrame({"xmin": [0], "xmax": [50], "ymin": [0], "ymax": [7]}),
        fill=COLOR_ACIDIC,
        alpha=0.6,
        tooltips="none",
    )
    + geom_rect(  # noqa: F405
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),  # noqa: F405
        data=pd.DataFrame({"xmin": [0], "xmax": [50], "ymin": [7], "ymax": [14]}),
        fill=COLOR_BASIC,
        alpha=0.6,
        tooltips="none",
    )
    # pH 7 neutral line
    + geom_hline(  # noqa: F405
        yintercept=7.0, color="#95A5A6", size=0.6, linetype="dotted"
    )
    # Buffer region shading
    + geom_area(  # noqa: F405
        aes(x="volume_ml", y="ph"),  # noqa: F405
        data=df_buffer,
        fill=COLOR_BUFFER,
        alpha=0.1,
        tooltips="none",
    )
    # Region labels for storytelling
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=pd.DataFrame({"x": [46], "y": [2.5], "label": ["Acidic"]}),
        size=14,
        color="#922B21",
        fontface="bold",
        alpha=0.4,
    )
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=pd.DataFrame({"x": [46], "y": [12.0], "label": ["Basic"]}),
        size=14,
        color="#1A5276",
        fontface="bold",
        alpha=0.4,
    )
    + geom_text(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=pd.DataFrame({"x": [11], "y": [2.0], "label": ["Buffer Region"]}),
        size=12,
        color=COLOR_BUFFER,
        fontface="italic",
        alpha=0.6,
    )
    # Derivative curve (scaled, more visible)
    + geom_line(  # noqa: F405
        aes(x="volume_ml", y="y", color="series"),  # noqa: F405
        data=df_deriv,
        size=2.0,
        linetype="dashed",
        alpha=0.9,
        tooltips=layer_tooltips().line("dpH/dV (scaled)"),  # noqa: F405
    )
    # Main pH curve
    + geom_line(  # noqa: F405
        aes(x="volume_ml", y="y", color="series"),  # noqa: F405
        data=df_ph,
        size=2.8,
        tooltips=layer_tooltips()  # noqa: F405
        .format("volume_ml", ".1f")
        .format("y", ".2f")
        .line("Volume: @volume_ml mL")
        .line("pH: @y"),
    )
    # Equivalence point vertical line
    + geom_vline(  # noqa: F405
        xintercept=equiv_volume, color=COLOR_EQUIV, size=1.0, linetype="dashed", alpha=0.6
    )
    # Equivalence point marker
    + geom_point(  # noqa: F405
        aes(x="volume_ml", y="ph"),  # noqa: F405
        data=equiv_point,
        color=COLOR_EQUIV,
        size=11,
        shape=18,
    )
    # Equivalence point label
    + geom_label(  # noqa: F405
        aes(x="volume_ml", y="ph", label="label"),  # noqa: F405
        data=equiv_point,
        size=15,
        color=COLOR_EQUIV,
        fill="#FADBD8",
        label_padding=0.5,
        label_r=0.2,
        fontface="bold",
        nudge_x=8,
        nudge_y=1.8,
    )
    + scale_color_manual(  # noqa: F405
        values=[COLOR_DERIV, COLOR_CURVE], name=""
    )
    + scale_x_continuous(  # noqa: F405
        limits=[0, 50], breaks=list(range(0, 55, 5))
    )
    + scale_y_continuous(  # noqa: F405
        limits=[0, 14], breaks=list(range(0, 15, 2))
    )
    + labs(  # noqa: F405
        x="Volume of NaOH added (mL)",
        y="pH",
        title="titration-curve \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="Strong Acid\u2013Base: 25 mL of 0.1 M HCl titrated with 0.1 M NaOH",
    )
    + flavor_high_contrast_light()  # noqa: F405
    + theme(  # noqa: F405
        axis_title=element_text(size=20, face="bold"),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        plot_title=element_text(size=26, hjust=0.5, face="bold"),  # noqa: F405
        plot_subtitle=element_text(size=17, hjust=0.5, color="#555555"),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_position=[0.85, 0.15],
        legend_justification=[0.5, 0.5],
        legend_background=element_rect(  # noqa: F405
            fill="white", color="#BBBBBB", size=0.5
        ),
        panel_grid_major_y=element_line(color="#E8E8E8", size=0.3),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_border=element_blank(),  # noqa: F405
        axis_line=element_line(color="#999999", size=0.5),  # noqa: F405
        plot_margin=[30, 30, 10, 20],
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
