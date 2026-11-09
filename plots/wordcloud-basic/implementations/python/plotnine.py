""" anyplot.ai
wordcloud-basic: Basic Word Cloud
Library: plotnine 0.15.8 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from matplotlib.colors import LinearSegmentedColormap, to_hex
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextPath
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

# Constants
PANEL_W, PANEL_H = 564, 265  # panel size in points under this figure size, title and top legend
MIN_SIZE = 8  # smallest font size in pt, still readable in the thumbnail
PAD = 5.0  # clearance in pt kept around every word
ROTATE_EVERY = 5  # every fifth word by rank is set vertically for an organic outline
TIER_SHARES = [0.0, 0.15, 0.35, 0.65, np.inf]  # tier edges as shares of the top frequency
TIER_LABELS = ["Low", "Low-Med", "Medium", "High"]

# Columns: set these to your table's column names
WORD = "word"  # role: word
FREQUENCY = "frequency"  # role: frequency

# Data: replace this block with your own table, for example df = pd.read_csv("terms.csv")
# Technology survey responses; common words in lowercase, acronyms and proper nouns in their usual case
df = pd.DataFrame(
    {
        WORD: [
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
        FREQUENCY: [
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
)

# Plot: reads only df and the constants above
cloud = df.dropna(subset=[WORD, FREQUENCY]).sort_values(FREQUENCY, ascending=False).reset_index(drop=True)
freq = cloud[FREQUENCY].astype(float)
span = freq.max() - freq.min()
freq_norm = (freq - freq.min()) / span if span > 0 else pd.Series(1.0, index=cloud.index)
font = FontProperties(family=["sans-serif"])
glyph_box = {}
for word in cloud[WORD].astype(str):
    ext = TextPath((0, 0), word, size=1, prop=font).get_extents()
    glyph_box[word] = (ext.width, 1.2)  # width per pt of font size; line height incl. descenders

# Spiral placement in panel points: each word, largest first, goes to the first free spot along an
# Archimedean spiral stretched to the panel's aspect; the size range shrinks until every word fits,
# so the cloud fills the panel instead of floating in it
t_steps = np.arange(0, 600, 0.05)
spiral_x = t_steps * np.cos(t_steps) * PANEL_W / PANEL_H
spiral_y = t_steps * np.sin(t_steps)
size_span = 40.0
while True:
    sizes = MIN_SIZE + freq_norm.to_numpy() * size_span
    placed, layout = [], []
    for rank, (word, size) in enumerate(zip(cloud[WORD].astype(str), sizes, strict=True)):
        w, h = glyph_box[word][0] * size + PAD, glyph_box[word][1] * size + PAD
        angle = 90 if (rank + 1) % ROTATE_EVERY == 0 else 0
        if angle:
            w, h = h, w
        spot = None
        for sx, sy in zip(spiral_x, spiral_y, strict=True):
            x0, y0 = PANEL_W / 2 + sx - w / 2, PANEL_H / 2 + sy - h / 2
            if x0 < 0 or y0 < 0 or x0 + w > PANEL_W or y0 + h > PANEL_H:
                if abs(sx) > PANEL_W and abs(sy) > PANEL_H:
                    break
                continue
            if all(x0 + w <= a or a + c <= x0 or y0 + h <= b or b + d <= y0 for a, b, c, d in placed):
                spot = (x0, y0)
                break
        if spot is None:
            break
        placed.append((spot[0], spot[1], w, h))
        layout.append((spot[0] + w / 2, spot[1] + h / 2, size, angle))
    if len(layout) == len(cloud) or size_span <= 1:
        break
    size_span *= 0.92

cloud = cloud.iloc[: len(layout)].copy()
cloud["x"], cloud["y"], cloud["size"], cloud["angle"] = map(list, zip(*layout, strict=True))

# Frequency tiers relative to the top frequency, highest first, each with its ramp step
edges = [share * freq.max() if np.isinf(share) else round(share * freq.max()) for share in TIER_SHARES]
tiers = [
    f"{label} ({lo}+)" if np.isinf(hi) else f"{label} ({lo}-{hi - 1})"
    for label, lo, hi in zip(TIER_LABELS, edges[:-1], edges[1:], strict=True)
][::-1]
cloud["tier"] = pd.cut(cloud[FREQUENCY].astype(float), bins=edges, right=False, labels=tiers[::-1])
tier_colors = [to_hex(IMPRINT_SEQ(v)) for v in np.linspace(0, 1, len(tiers))]

# The invisible points only give the legend its colour swatches
plot = (
    ggplot(cloud, aes(x="x", y="y", color="tier"))
    + geom_text(aes(label=WORD, size="size", angle="angle"), family="sans-serif", show_legend=False)
    + geom_point(alpha=0, size=0.1)
    + scale_size_identity()
    + scale_color_manual(values=tier_colors, limits=tiers, drop=False)
    + guides(color=guide_legend(nrow=1, override_aes={"alpha": 1, "size": 4, "shape": "s"}))
    + coord_cartesian(xlim=(0, PANEL_W), ylim=(0, PANEL_H), expand=False)
    + labs(title="wordcloud-basic · python · plotnine · anyplot.ai", color=FREQUENCY.capitalize())
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
        legend_box_spacing=0.01,
        legend_background=element_rect(fill=PAGE_BG, color=None),
        legend_key=element_rect(fill=PAGE_BG, color=None),
        legend_title=element_text(size=9, weight="bold", color=INK),
        legend_text=element_text(size=8, color=INK_SOFT),
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
