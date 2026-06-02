"""anyplot.ai
scatter-hr-diagram: Hertzsprung-Russell Diagram
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 87/100 | Updated: 2026-06-02
"""

import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_point,
    geom_text,
    ggplot,
    ggsize,
    guides,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_log10,
    theme,
    theme_minimal,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens (Imprint palette — theme-adaptive chrome)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Spectral type colors — closest Imprint palette members to astrophysical convention
spectral_colors = {
    "O": "#C475FD",  # lavender — nearest Imprint member to hot-violet O-type
    "B": "#4467A3",  # blue
    "A": "#2ABCCD",  # cyan — lighter blue-white A-type
    "F": "#BD8233",  # ochre — nearest to yellow-white F-type
    "G": "#99B314",  # lime — nearest to solar-yellow G-type
    "K": "#954477",  # rose — closest Imprint member to orange K-type
    "M": "#AE3030",  # matte red — cool red M-type
}

# Data — synthetic stellar populations
np.random.seed(42)

# Main sequence (diagonal band from hot/bright to cool/dim)
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

temperature = np.concatenate([main_temp, giant_temp, super_temp, dwarf_temp])
luminosity = np.concatenate([main_luminosity, giant_luminosity, super_luminosity, dwarf_luminosity])
region = (
    ["Main Sequence"] * n_main + ["Red Giants"] * n_giants + ["Supergiants"] * n_super + ["White Dwarfs"] * n_dwarfs
)

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

sun_df = pd.DataFrame({"temperature": [5778], "luminosity": [1.0]})
sun_label_df = pd.DataFrame({"temperature": [7800], "luminosity": [4.0], "label": ["☉ Sun"]})

region_labels = pd.DataFrame(
    {
        "temperature": [25000, 4500, 14000, 18000],
        "luminosity": [0.012, 8000, 120000, 0.0005],
        "label": ["Main Sequence", "Red Giants", "Supergiants", "White Dwarfs"],
    }
)

# Spectral class markers — staggered y-positions to avoid bunching on the linear scale
spectral_axis_labels = pd.DataFrame(
    {
        "temperature": [35000, 18000, 8500, 6800, 5500, 4200, 3100],
        "luminosity": [1200000, 500000, 1200000, 500000, 1200000, 500000, 1200000],
        "label": ["O", "B", "A", "F", "G", "K", "M"],
    }
)

# Plot
TITLE = "scatter-hr-diagram · python · letsplot · anyplot.ai"
title_size = round(16 * 67 / len(TITLE)) if len(TITLE) > 67 else 16

plot = (
    ggplot(df, aes(x="temperature", y="luminosity"))
    + geom_point(
        size=4.5,
        alpha=0.75,
        shape=21,
        stroke=1.0,
        mapping=aes(fill="spectral_type"),
        color=INK_MUTED,
        tooltips=layer_tooltips()
        .line("@region")
        .line("Temperature|@temperature K")
        .line("Luminosity|@luminosity L☉")
        .line("Spectral Type|@spectral_type"),
    )
    + geom_point(
        data=sun_df,
        mapping=aes(x="temperature", y="luminosity"),
        color="#FFD700",
        fill="#FFD700",
        size=9,
        shape=21,
        stroke=2.0,
        inherit_aes=False,
    )
    + geom_text(
        data=sun_label_df,
        mapping=aes(x="temperature", y="luminosity", label="label"),
        size=5,
        color="#FFD700",
        fontface="bold",
        inherit_aes=False,
    )
    + geom_text(
        data=region_labels,
        mapping=aes(x="temperature", y="luminosity", label="label"),
        size=4,
        color=INK_MUTED,
        fontface="bold_italic",
        inherit_aes=False,
    )
    + geom_text(
        data=spectral_axis_labels,
        mapping=aes(x="temperature", y="luminosity", label="label"),
        size=4.5,
        color=INK_SOFT,
        fontface="bold",
        inherit_aes=False,
    )
    + scale_x_continuous(
        trans="reverse",
        name="Surface Temperature (K)",
        breaks=[40000, 30000, 20000, 10000, 5000, 3000],
        labels=["40,000", "30,000", "20,000", "10,000", "5,000", "3,000"],
    )
    + scale_y_log10(name="Luminosity (L☉)", limits=[0.00005, 2000000])
    + scale_fill_manual(
        values=[spectral_colors[k] for k in ["O", "B", "A", "F", "G", "K", "M"]],
        limits=["O", "B", "A", "F", "G", "K", "M"],
        name="Spectral Type",
    )
    + guides(color="none")
    + labs(title=TITLE)
    + ggsize(800, 450)
    + theme_minimal()
    + theme(
        axis_text=element_text(size=10, color=INK_SOFT),
        axis_title=element_text(size=12, color=INK),
        plot_title=element_text(size=title_size, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color=INK_SOFT),
        panel_grid_major=element_line(color=INK_MUTED, size=0.2),
        panel_grid_minor=element_blank(),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        axis_line=element_line(color=INK_SOFT),
        axis_ticks=element_line(color=INK_SOFT, size=0.3),
        plot_margin=[30, 40, 20, 20],
    )
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
