"""anyplot.ai
wordcloud-basic: Basic Word Cloud
Library: plotnine 0.15.8 | Python 3.14.10
Quality: 84/100 | Updated: 2026-11-09
"""

import os

import numpy as np
import pandas as pd
from matplotlib.font_manager import FontProperties
from matplotlib.textpath import TextToPath
from plotnine import (
    aes,
    coord_cartesian,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    ggplot,
    labs,
    scale_size_identity,
    theme,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"

# Imprint palette position 1; color is decorative because size already carries the frequency
WORD_COLOR = "#009E73"

# Constants
PANEL_W, PANEL_H = 564, 289  # panel size in points under this figure size and title
MIN_SIZE = 10  # smallest font size in pt, readable on both page colors
PAD = 5.0  # clearance in pt kept around every word
ROTATE_EVERY = 5  # every fifth word by rank is set vertically for an organic outline

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
font = FontProperties(family=["sans-serif"], size=1)
text_metrics = TextToPath()
glyph_box = {}
for word in cloud[WORD].astype(str):
    # advance width incl. side bearings per pt of font size, the span of the rendered text box
    width = text_metrics.get_text_width_height_descent(word, font, ismath=False)[0]
    glyph_box[word] = (width, 1.2)  # line height incl. descenders

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

plot = (
    ggplot(cloud, aes(x="x", y="y"))
    + geom_text(aes(label=WORD, size="size", angle="angle"), color=WORD_COLOR, family="sans-serif")
    + scale_size_identity()
    + coord_cartesian(xlim=(0, PANEL_W), ylim=(0, PANEL_H), expand=False)
    + labs(title="wordcloud-basic · python · plotnine · anyplot.ai")
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
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
