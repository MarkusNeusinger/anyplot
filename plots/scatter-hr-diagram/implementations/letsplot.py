""" pyplots.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-07
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - synthetic stellar populations
np.random.seed(42)

# Main sequence stars (diagonal band from hot/bright to cool/dim)
# Luminosity ~ T^4 approximately: log(L) = 4 * log(T/T_sun)
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
n_super = 15
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

# Assign spectral types based on temperature
spectral_type = []
for t in temperature:
    if t >= 30000:
        spectral_type.append("O")
    elif t >= 10000:
        spectral_type.append("B")
    elif t >= 7500:
        spectral_type.append("A")
    elif t >= 6000:
        spectral_type.append("F")
    elif t >= 5200:
        spectral_type.append("G")
    elif t >= 3700:
        spectral_type.append("K")
    else:
        spectral_type.append("M")

df = pd.DataFrame(
    {"temperature": temperature, "luminosity": luminosity, "region": region, "spectral_type": spectral_type}
)

# Spectral type colors (astrophysical convention, A/F differentiated)
spectral_colors = {
    "O": "#6B7FFF",
    "B": "#9BB0FF",
    "A": "#B8C9FF",
    "F": "#FFF0C8",
    "G": "#FFE08A",
    "K": "#FFB86C",
    "M": "#FF7B5A",
}

# Sun reference point
sun_df = pd.DataFrame({"temperature": [5778], "luminosity": [1.0], "label": ["Sun"]})
sun_label_df = pd.DataFrame({"temperature": [7500], "luminosity": [3.5], "label": ["Sun"]})

# Region label positions (repositioned to avoid data overlap)
region_labels = pd.DataFrame(
    {
        "temperature": [25000, 5500, 18000, 18000],
        "luminosity": [0.015, 5000, 70000, 0.0006],
        "label": ["Main Sequence", "Red Giants", "Supergiants", "White Dwarfs"],
    }
)

# Plot
plot = (
    ggplot(df, aes(x="temperature", y="luminosity", color="spectral_type"))  # noqa: F405
    + geom_point(  # noqa: F405
        size=5,
        alpha=0.75,
        shape=21,
        stroke=0.4,
        mapping=aes(fill="spectral_type"),  # noqa: F405
        color="#1A1F2B",
        tooltips=layer_tooltips()  # noqa: F405
        .line("Temperature|@temperature K")
        .line("Luminosity|@luminosity L☉")
        .line("Spectral Type|@spectral_type")
        .line("Region|@region"),
    )
    + geom_point(  # noqa: F405
        data=sun_df,
        mapping=aes(x="temperature", y="luminosity"),  # noqa: F405
        color="#FFD700",
        fill="#FFD700",
        size=8,
        shape=21,
        stroke=1.5,
        inherit_aes=False,
    )
    + geom_text(  # noqa: F405
        data=sun_label_df,
        mapping=aes(x="temperature", y="luminosity", label="label"),  # noqa: F405
        size=16,
        color="#FFD700",
        fontface="bold",
        inherit_aes=False,
    )
    + geom_text(  # noqa: F405
        data=region_labels,
        mapping=aes(x="temperature", y="luminosity", label="label"),  # noqa: F405
        size=15,
        color="#8899AA",
        fontface="bold_italic",
        inherit_aes=False,
        label_padding=0.4,
    )
    + scale_x_continuous(  # noqa: F405
        trans="reverse",
        name="Surface Temperature (K)",
        breaks=[40000, 30000, 20000, 10000, 5000, 3000],
        labels=["40,000", "30,000", "20,000", "10,000", "5,000", "3,000"],
    )
    + scale_y_log10(  # noqa: F405
        name="Luminosity (L☉)"
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
    + scale_color_manual(  # noqa: F405
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
    + labs(  # noqa: F405
        title="scatter-hr-diagram · letsplot · pyplots.ai"
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16, color="#AAAAAA"),  # noqa: F405
        axis_title=element_text(size=20, color="#CCCCCC"),  # noqa: F405
        plot_title=element_text(size=24, color="#E0E0E0", face="bold"),  # noqa: F405
        legend_text=element_text(size=14, color="#CCCCCC"),  # noqa: F405
        legend_title=element_text(size=16, face="bold", color="#DDDDDD"),  # noqa: F405
        legend_background=element_rect(fill="#1A1F2B", color="#1A1F2B"),  # noqa: F405
        panel_grid_major=element_line(color="#2A2F3A", size=0.35),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_background=element_rect(fill="#0D1117", color="#0D1117"),  # noqa: F405
        panel_background=element_rect(fill="#0D1117", color="#0D1117"),  # noqa: F405
        axis_ticks=element_line(color="#444444", size=0.3),  # noqa: F405
        plot_margin=[30, 40, 20, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
