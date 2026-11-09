""" anyplot.ai
wordcloud-basic: Basic Word Cloud
Library: plotnine 0.15.7 | Python 3.13.14
Quality: 85/100 | Updated: 2026-08-04
"""

import os

import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, to_hex
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_rect,
    element_text,
    geom_point,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_size_identity,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Frequency tiers are ordered, so they take steps of the imprint_seq ramp (brand green -> blue);
# both ends keep at least 3:1 against the page in either theme
IMPRINT_SEQ = LinearSegmentedColormap.from_list("imprint_seq", ["#009E73", "#4467A3"])

# Word frequency data - technology survey responses; common words in lowercase,
# acronyms and proper nouns in their usual case
words_data = {
    "word": [
        "Python",
        "data",
        "machine",
        "learning",
        "AI",
        "cloud",
        "API",
        "database",
        "security",
        "DevOps",
        "analytics",
        "automation",
        "software",
        "code",
        "development",
        "integration",
        "platform",
        "infrastructure",
        "testing",
        "deployment",
        "monitoring",
        "framework",
        "Docker",
        "AWS",
        "Azure",
        "Kubernetes",
        "Terraform",
        "GraphQL",
        "Redis",
    ],
    "frequency": [
        95,
        88,
        82,
        78,
        75,
        70,
        65,
        62,
        58,
        55,
        52,
        48,
        45,
        42,
        38,
        35,
        32,
        30,
        28,
        26,
        24,
        22,
        20,
        18,
        16,
        14,
        11,
        8,
        6,
    ],
}

df = pd.DataFrame(words_data)

# Font sizes (6-25 pt) carry the frequency; size alone, no alpha ramp, so small words stay readable
min_freq, max_freq = df["frequency"].min(), df["frequency"].max()
freq_norm = (df["frequency"] - min_freq) / (max_freq - min_freq)
df["size"] = 6 + freq_norm * 19

# Sort by frequency descending
df = df.sort_values("frequency", ascending=False).reset_index(drop=True)

# Hand-crafted positions to ensure no overlap
positions = [
    (45, 28),  # Python (largest) - center
    (70, 36),  # data
    (22, 24),  # machine
    (72, 22),  # learning
    (30, 36),  # AI
    (55, 16),  # cloud
    (18, 42),  # API
    (45, 42),  # database
    (68, 46),  # security
    (25, 10),  # DevOps
    (50, 6),  # analytics
    (78, 8),  # automation
    (6, 28),  # software
    (88, 28),  # code
    (35, 50),  # development
    (60, 50),  # integration
    (12, 50),  # platform
    (82, 50),  # infrastructure
    (6, 16),  # testing
    (6, 40),  # deployment
    (55, 36),  # monitoring
    (88, 40),  # framework
    (30, 6),  # Docker
    (6, 6),  # AWS
    (86, 16),  # Azure - free gap right of learning, clear of automation
    (94, 10),  # Kubernetes - fills empty right margin
    (94, 24),  # Terraform - fills empty right margin
    (78, 53),  # GraphQL - fills empty upper-right quadrant
    (42, 20),  # Redis - fills gap between the mid-canvas clusters
]

df["x"] = [p[0] for p in positions]
df["y"] = [p[1] for p in positions]

# AWS sits alone in the bottom-left corner - rotate it for an organic word-cloud feel
df["angle"] = np.where(df["word"] == "AWS", 90, 0)

# Frequency tiers, highest first, each with its ramp step
tiers = ["High (65+)", "Medium (35-64)", "Low-Med (15-34)", "Low (<15)"]
df["tier"] = pd.cut(df["frequency"], bins=[-np.inf, 15, 35, 65, np.inf], right=False, labels=tiers[::-1])
tier_colors = [to_hex(IMPRINT_SEQ(v)) for v in np.linspace(0, 1, len(tiers))]

# Create plot; the invisible points only give the legend its colour swatches
plot = (
    ggplot(df, aes(x="x", y="y", color="tier"))
    + geom_text(aes(label="word", size="size", angle="angle"), family="sans-serif", show_legend=False)
    + geom_point(alpha=0, size=0.1)
    + scale_size_identity()
    + scale_color_manual(values=tier_colors, limits=tiers, drop=False)
    + guides(color=guide_legend(nrow=1, override_aes={"alpha": 1, "size": 4, "shape": "s"}))
    + coord_cartesian(xlim=(0, 100), ylim=(0, 56.25), expand=False)
    + labs(title="wordcloud-basic · python · plotnine · anyplot.ai", color="Frequency")
    + theme(
        figure_size=(8, 4.5),
        plot_title=element_text(size=12, ha="center", weight="bold", color=INK, margin={"b": 6}),
        plot_title_position="plot",
        panel_background=element_rect(fill=PAGE_BG, color=None),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_grid_major=element_blank(),
        panel_grid_minor=element_blank(),
        axis_text=element_blank(),
        axis_title=element_blank(),
        axis_ticks=element_blank(),
        legend_position="top",
        legend_background=element_rect(fill=PAGE_BG, color=None),
        legend_key=element_rect(fill=PAGE_BG, color=None),
        legend_title=element_text(size=9, weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
