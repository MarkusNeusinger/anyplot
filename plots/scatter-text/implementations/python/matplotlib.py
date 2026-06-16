""" anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Okabe-Ito categorical palette
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data: Programming languages positioned by paradigm similarity
# (simulating dimensionality reduction output)
languages = [
    "Python",
    "JavaScript",
    "Java",
    "C++",
    "Ruby",
    "Go",
    "Rust",
    "Swift",
    "Kotlin",
    "TypeScript",
    "Scala",
    "Haskell",
    "Clojure",
    "Elixir",
    "Julia",
    "R",
    "MATLAB",
    "Perl",
    "PHP",
    "C#",
    "F#",
    "OCaml",
    "Erlang",
    "Lua",
    "Dart",
    "Zig",
    "Nim",
    "Crystal",
    "Groovy",
    "Fortran",
]

# Improved coordinates to reduce overlap while maintaining logical clusters
x = np.array(
    [
        1.5,
        3.2,
        4.0,
        5.8,
        2.5,
        6.2,
        6.8,
        5.0,
        4.8,
        3.5,
        3.0,
        0.5,
        1.0,
        0.8,
        2.2,
        1.2,
        2.3,
        3.5,
        2.5,
        4.2,
        2.8,
        0.3,
        1.8,
        4.5,
        5.8,
        6.5,
        5.5,
        3.2,
        4.5,
        7.0,
    ]
)

y = np.array(
    [
        5.8,
        4.8,
        3.2,
        2.0,
        5.5,
        3.5,
        2.5,
        3.8,
        3.2,
        4.3,
        4.0,
        6.8,
        6.5,
        5.8,
        4.8,
        4.2,
        3.8,
        3.2,
        2.8,
        3.0,
        6.2,
        6.2,
        5.5,
        2.5,
        4.5,
        1.8,
        2.2,
        5.8,
        3.2,
        1.2,
    ]
)

# Category assignments
categories = [
    "dynamic",
    "dynamic",
    "jvm",
    "systems",
    "dynamic",
    "systems",
    "systems",
    "systems",
    "jvm",
    "dynamic",
    "jvm",
    "functional",
    "functional",
    "functional",
    "dynamic",
    "dynamic",
    "dynamic",
    "dynamic",
    "dynamic",
    "jvm",
    "functional",
    "functional",
    "functional",
    "dynamic",
    "dynamic",
    "systems",
    "systems",
    "functional",
    "jvm",
    "systems",
]

category_to_color = {"dynamic": IMPRINT[0], "functional": IMPRINT[1], "systems": IMPRINT[2], "jvm": IMPRINT[3]}

color_list = [category_to_color[cat] for cat in categories]

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# Plot text labels at each coordinate
for xi, yi, label, color in zip(x, y, languages, color_list, strict=True):
    ax.text(
        xi, yi, label, fontsize=18, ha="center", va="center", color=color, fontweight="bold", alpha=0.9
    )

# Set axis limits with padding
ax.set_xlim(-0.5, 7.5)
ax.set_ylim(0.5, 7.5)

# Labels and styling
ax.set_xlabel("Embedding Dimension 1", fontsize=20, color=INK)
ax.set_ylabel("Embedding Dimension 2", fontsize=20, color=INK)
ax.set_title("scatter-text · Python · matplotlib · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Spines
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
for s in ("left", "bottom"):
    ax.spines[s].set_color(INK_SOFT)

# Grid
ax.grid(True, alpha=0.1, linewidth=0.8, color=INK)

# Legend
legend_elements = [
    Patch(facecolor=IMPRINT[0], label="Dynamic/Scripting"),
    Patch(facecolor=IMPRINT[1], label="Functional"),
    Patch(facecolor=IMPRINT[2], label="Systems"),
    Patch(facecolor=IMPRINT[3], label="JVM-based"),
]
leg = ax.legend(handles=legend_elements, loc="upper right", fontsize=16, framealpha=0.9)
if leg:
    leg.get_frame().set_facecolor(PAGE_BG)
    leg.get_frame().set_edgecolor(INK_SOFT)
    for text in leg.get_texts():
        text.set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
