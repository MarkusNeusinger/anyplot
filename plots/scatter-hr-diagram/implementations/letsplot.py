""" pyplots.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-07
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - synthetic stellar populations
np.random.seed(42)

# Main sequence stars (diagonal band from hot/bright to cool/dim)
n_main = 200
main_temp = 10 ** np.random.uniform(np.log10(3000), np.log10(35000), n_main)
main_log_lum = 4.0 * (np.log10(main_temp) - np.log10(5778))
main_log_lum += np.random.normal(0, 0.25, n_main)
main_luminosity = 10**main_log_lum

# Red giants (cool but bright)
n_giants = 40
giant_temp = np.random.uniform(3200, 5500, n_giants)
giant_luminosity = 10 ** np.random.uniform(1.0, 3.5, n_giants)

# Supergiants (very bright, wide temp range)
n_super = 25
super_temp = np.random.uniform(3500, 30000, n_super)
super_luminosity = 10 ** np.random.uniform(3.5, 5.5, n_super)

# White dwarfs (hot but very dim)
n_dwarfs = 30
dwarf_temp = np.random.uniform(5000, 30000, n_dwarfs)
dwarf_luminosity = 10 ** np.random.uniform(-4, -1.5, n_dwarfs)

# Combine all
temperature = np.concatenate([main_temp, giant_temp, super_temp, dwarf_temp])
luminosity = np.concatenate([main_luminosity, giant_luminosity, super_luminosity, dwarf_luminosity])
region = (
    ["Main Sequence"] * n_main + ["Red Giants"] * n_giants + ["Supergiants"] * n_super + ["White Dwarfs"] * n_dwarfs
)

# Assign spectral types based on temperature (vectorized)
spectral_type = np.select(
    [
        temperature >= 30000,
        temperature >= 10000,
        temperature >= 7500,
        temperature >= 6000,
        temperature >= 5200,
        temperature >= 3700,
    ],
    ["O", "B", "A", "F", "G", "K"],
    default="M",
)

df = pd.DataFrame(
    {"temperature": temperature, "luminosity": luminosity, "region": region, "spectral_type": spectral_type}
)

# Spectral type colors (astrophysical convention with improved A/B distinction)
spectral_colors = {
    "O": "#6644CC",
    "B": "#6699FF",
    "A": "#C8D8FF",
    "F": "#FFF4D6",
    "G": "#FFD866",
    "K": "#FF9944",
    "M": "#FF5533",
}

# Sun reference point
sun_df = pd.DataFrame({"temperature": [5778], "luminosity": [1.0], "label": ["☉ Sun"]})
sun_label_df = pd.DataFrame({"temperature": [7800], "luminosity": [4.0], "label": ["☉ Sun"]})

# Region label positions (repositioned to avoid data overlap)
region_labels = pd.DataFrame(
    {
        "temperature": [25000, 5200, 14000, 18000],
        "luminosity": [0.012, 6000, 120000, 0.0005],
        "label": ["Main Sequence", "Red Giants", "Supergiants", "White Dwarfs"],
    }
)

# Spectral class markers along the top (secondary x-axis)
spectral_axis_labels = pd.DataFrame(
    {
        "temperature": [35000, 18000, 8500, 6800, 5500, 4200, 3100],
        "luminosity": [600000] * 7,
        "label": ["O", "B", "A", "F", "G", "K", "M"],
    }
)

# Plot
plot = (
    ggplot(df, aes(x="temperature", y="luminosity", color="spectral_type"))  # noqa: F405
    + geom_point(  # noqa: F405
        size=4.5,
        alpha=0.7,
        shape=21,
        stroke=0.3,
        mapping=aes(fill="spectral_type"),  # noqa: F405
        color="#0D1117",
        tooltips=layer_tooltips()  # noqa: F405
        .line("@region")
        .line("Temperature|@temperature K")
        .line("Luminosity|@luminosity L☉")
        .line("Spectral Type|@spectral_type"),
    )
    + geom_point(  # noqa: F405
        data=sun_df,
        mapping=aes(x="temperature", y="luminosity"),  # noqa: F405
        color="#FFD700",
        fill="#FFD700",
        size=9,
        shape=21,
        stroke=2.0,
        inherit_aes=False,
    )
    + geom_text(  # noqa: F405
        data=sun_label_df,
        mapping=aes(x="temperature", y="luminosity", label="label"),  # noqa: F405
        size=17,
        color="#FFD700",
        fontface="bold",
        inherit_aes=False,
    )
    + geom_text(  # noqa: F405
        data=region_labels,
        mapping=aes(x="temperature", y="luminosity", label="label"),  # noqa: F405
        size=16,
        color="#667788",
        fontface="bold_italic",
        inherit_aes=False,
        label_padding=0.4,
    )
    + geom_text(  # noqa: F405
        data=spectral_axis_labels,
        mapping=aes(x="temperature", y="luminosity", label="label"),  # noqa: F405
        size=18,
        color="#99AABB",
        fontface="bold",
        inherit_aes=False,
    )
    + scale_x_continuous(  # noqa: F405
        trans="reverse",
        name="Surface Temperature (K)",
        breaks=[40000, 30000, 20000, 10000, 5000, 3000],
        labels=["40,000", "30,000", "20,000", "10,000", "5,000", "3,000"],
    )
    + scale_y_log10(  # noqa: F405
        name="Luminosity (L☉)", limits=[0.00005, 2000000]
    )
    + scale_fill_manual(  # noqa: F405
        values=[
            spectral_colors["O"],
            spectral_colors["B"],
            spectral_colors["A"],
            spectral_colors["F"],
            spectral_colors["G"],
            spectral_colors["K"],
            spectral_colors["M"],
        ],
        limits=["O", "B", "A", "F", "G", "K", "M"],
        name="Spectral Type",
    )
    + guides(color="none")  # noqa: F405
    + labs(  # noqa: F405
        title="scatter-hr-diagram · letsplot · pyplots.ai"
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16, color="#99AABB"),  # noqa: F405
        axis_title=element_text(size=20, color="#BBCCDD"),  # noqa: F405
        plot_title=element_text(size=24, color="#E8ECF0", face="bold"),  # noqa: F405
        legend_text=element_text(size=15, color="#BBCCDD"),  # noqa: F405
        legend_title=element_text(size=17, face="bold", color="#DDDDDD"),  # noqa: F405
        legend_background=element_rect(fill="#131820", color="#1E2530"),  # noqa: F405
        panel_grid_major=element_line(color="#171D28", size=0.3),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_background=element_rect(fill="#0D1117", color="#0D1117"),  # noqa: F405
        panel_background=element_rect(fill="#0D1117", color="#0D1117"),  # noqa: F405
        axis_ticks=element_line(color="#334455", size=0.3),  # noqa: F405
        plot_margin=[30, 40, 20, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
