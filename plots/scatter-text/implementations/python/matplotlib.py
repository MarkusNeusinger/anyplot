""" pyplots.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: matplotlib 3.10.8 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch


# Data: Programming languages positioned by paradigm similarity and age
# (simulating dimensionality reduction output)
np.random.seed(42)

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

# Cluster-like positioning to simulate embedding space
# Positions spread out to avoid text overlap while maintaining logical clusters
x = np.array(
    [
        1.8,
        3.5,
        4.2,
        5.8,
        3.0,
        6.2,
        6.8,
        5.0,  # Python, JS, Java, C++, Ruby, Go, Rust, Swift
        4.8,
        3.8,
        3.5,
        0.8,
        1.3,
        1.0,
        2.5,  # Kotlin, TS, Scala, Haskell, Clojure, Elixir, Julia
        1.5,
        2.0,
        3.2,
        2.8,
        4.5,
        2.3,
        0.6,
        1.6,  # R, MATLAB, Perl, PHP, C#, F#, OCaml, Erlang
        4.2,
        5.5,
        6.5,
        5.2,
        2.8,
        4.0,
        7.0,  # Lua, Dart, Zig, Nim, Crystal, Groovy, Fortran
    ]
)

y = np.array(
    [
        5.8,
        4.8,
        3.2,
        2.0,
        5.0,
        3.5,
        2.5,
        3.8,  # Python, JS, Java, C++, Ruby, Go, Rust, Swift
        3.5,
        4.3,
        4.0,
        6.8,
        6.3,
        5.5,
        4.5,  # Kotlin, TS, Scala, Haskell, Clojure, Elixir, Julia
        4.2,
        3.8,
        3.6,
        2.8,
        3.0,
        6.2,
        6.0,
        5.0,  # R, MATLAB, Perl, PHP, C#, F#, OCaml, Erlang
        2.5,
        4.5,
        1.8,
        2.2,
        5.5,
        3.2,
        1.2,  # Lua, Dart, Zig, Nim, Crystal, Groovy, Fortran
    ]
)

# Color by language category - using darker yellow for better contrast on white
colors = {
    "dynamic": "#306998",  # Python Blue - dynamic/scripting
    "functional": "#D4A017",  # Darker golden yellow - functional (better contrast)
    "systems": "#4ECDC4",  # Teal - systems programming
    "jvm": "#FF6B6B",  # Coral - JVM languages
}

# Assign categories
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
    "dynamic",
    "jvm",
    "systems",
]

color_list = [colors[cat] for cat in categories]

# Create plot
fig, ax = plt.subplots(figsize=(16, 9))

# Plot text labels at each coordinate
for i, (xi, yi, label) in enumerate(zip(x, y, languages, strict=True)):
    ax.text(xi, yi, label, fontsize=16, ha="center", va="center", color=color_list[i], fontweight="bold", alpha=0.9)

# Set axis limits with padding
ax.set_xlim(0, 8)
ax.set_ylim(0, 7.5)

# Labels and styling
ax.set_xlabel("Embedding Dimension 1", fontsize=20)
ax.set_ylabel("Embedding Dimension 2", fontsize=20)
ax.set_title("scatter-text · matplotlib · pyplots.ai", fontsize=24)
ax.tick_params(axis="both", labelsize=16)
ax.grid(True, alpha=0.3, linestyle="--")

# Add legend for categories
legend_elements = [
    Patch(facecolor="#306998", label="Dynamic/Scripting"),
    Patch(facecolor="#D4A017", label="Functional"),
    Patch(facecolor="#4ECDC4", label="Systems"),
    Patch(facecolor="#FF6B6B", label="JVM-based"),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=16, framealpha=0.9)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
