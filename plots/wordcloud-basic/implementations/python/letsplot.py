""" anyplot.ai
wordcloud-basic: Basic Word Cloud
Library: letsplot 4.9.0 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-06
"""

import math
import os

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_rect,
    element_text,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_color_manual,
    scale_size_identity,
    theme,
    theme_void,
    xlim,
    ylim,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito palette (first series always #009E73)
OKABE_ITO = ["#009E73", "#D55E00", "#0072B2", "#CC79A7", "#E69F00", "#56B4E9", "#F0E442"]

# Data - Programming language popularity
np.random.seed(42)
words_data = {
    "Python": 100,
    "JavaScript": 92,
    "Java": 85,
    "TypeScript": 78,
    "SQL": 75,
    "HTML": 70,
    "CSS": 68,
    "Rust": 62,
    "Go": 58,
    "C++": 55,
    "Kotlin": 52,
    "Swift": 50,
    "Shell": 48,
    "Ruby": 45,
    "PHP": 42,
    "Scala": 38,
    "R": 35,
    "Perl": 32,
    "Dart": 30,
    "Julia": 28,
    "MATLAB": 26,
    "Haskell": 24,
    "Lua": 22,
    "Clojure": 20,
    "Elixir": 18,
    "GraphQL": 35,
}

words = list(words_data.keys())
frequencies = list(words_data.values())

# Sort by frequency (largest first for better placement)
sorted_indices = np.argsort(frequencies)[::-1]
words = [words[i] for i in sorted_indices]
frequencies = [frequencies[i] for i in sorted_indices]

# Canvas dimensions
canvas_width = 280
canvas_height = 140

# Scale font sizes for readability
min_freq, max_freq = min(frequencies), max(frequencies)
min_size, max_size = 9, 26

sizes = []
for freq in frequencies:
    normalized = (freq - min_freq) / (max_freq - min_freq)
    size = min_size + (normalized**0.6) * (max_size - min_size)
    sizes.append(size)

# Spiral word placement with collision detection
placed = []
positions_x = []
positions_y = []
char_width_ratio = 0.52

for word, size in zip(words, sizes, strict=True):
    word_width = len(word) * size * char_width_ratio
    word_height = size * 1.05

    t = 0
    step = 0.08
    max_iterations = 4000
    placed_word = False

    while t < max_iterations and not placed_word:
        r = 0.1 + t * 0.08
        angle = t * 0.35
        x = canvas_width / 2 + r * math.cos(angle) * 0.95
        y = canvas_height / 2 + r * math.sin(angle)

        margin = 3
        if (
            x - word_width / 2 < margin
            or x + word_width / 2 > canvas_width - margin
            or y - word_height / 2 < margin
            or y + word_height / 2 > canvas_height - margin
        ):
            t += step
            continue

        collision = False
        padding = 0.6
        for px, py, pw, ph in placed:
            if abs(x - px) < (word_width / 2 + pw / 2 + padding) and abs(y - py) < (word_height / 2 + ph / 2 + padding):
                collision = True
                break

        if not collision:
            placed.append((x, y, word_width, word_height))
            positions_x.append(x)
            positions_y.append(y)
            placed_word = True
        else:
            t += step

    if not placed_word:
        positions_x.append(None)
        positions_y.append(None)

# Build dataframe with placed words
df_data = []
for word, freq, size, x, y in zip(words, frequencies, sizes, positions_x, positions_y, strict=True):
    if x is not None and y is not None:
        df_data.append({"word": word, "frequency": freq, "size": size, "x": x, "y": y})

df = pd.DataFrame(df_data)

# Assign Okabe-Ito colors to words
df["color"] = [OKABE_ITO[i % len(OKABE_ITO)] for i in range(len(df))]

# Plot with theme-adaptive chrome
anyplot_theme = theme(
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    plot_title=element_text(size=24, color=INK, hjust=0.5),
    legend_position="none",
    axis_title=element_blank(),
    axis_text=element_blank(),
)

plot = (
    ggplot(df, aes(x="x", y="y", label="word", size="size", color="color"))
    + geom_text(fontface="bold")
    + scale_size_identity()
    + scale_color_manual(values=df["color"].unique(), guide="none")
    + xlim(0, canvas_width)
    + ylim(0, canvas_height)
    + labs(title="wordcloud-basic · letsplot · anyplot.ai")
    + theme_void()
    + anyplot_theme
    + ggsize(1600, 900)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=3)
ggsave(plot, f"plot-{THEME}.html", path=".")
