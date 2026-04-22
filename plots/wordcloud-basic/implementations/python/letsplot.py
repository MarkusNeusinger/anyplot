""" pyplots.ai
wordcloud-basic: Basic Word Cloud
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import math

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
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

# Data - Programming language popularity (realistic survey data)
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

# Scale font sizes for readability (inline calculation)
min_freq, max_freq = min(frequencies), max(frequencies)
min_size, max_size = 9, 26  # Increased minimum for better readability

sizes = []
for freq in frequencies:
    normalized = (freq - min_freq) / (max_freq - min_freq)
    size = min_size + (normalized**0.6) * (max_size - min_size)
    sizes.append(size)

# Spiral word placement with collision detection (inline)
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
        # Center bias to improve layout balance
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

# Colorblind-safe palette starting with Python colors
colors_palette = ["#306998", "#FFD43B", "#4CAF50", "#E91E63", "#00BCD4", "#FF9800", "#9C27B0", "#607D8B"]
df["color"] = [colors_palette[i % len(colors_palette)] for i in range(len(df))]

# Plot
plot = (
    ggplot(df, aes(x="x", y="y", label="word", size="size", color="color"))
    + geom_text(fontface="bold")
    + scale_size_identity()
    + scale_color_manual(values=colors_palette, guide="none")
    + xlim(0, canvas_width)
    + ylim(0, canvas_height)
    + labs(title="wordcloud-basic \u00b7 letsplot \u00b7 pyplots.ai")
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        legend_position="none",
        axis_title=element_blank(),
        axis_text=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save to current directory (not default lets-plot-images folder)
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
