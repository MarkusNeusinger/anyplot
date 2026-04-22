""" pyplots.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: seaborn 0.13.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-09
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Set seaborn context for better sizing at high resolution
sns.set_theme(style="whitegrid")
sns.set_context("talk", font_scale=1.3)

# Data - Programming language names with 2D coordinates (simulating dimensionality reduction)
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
    "PHP",
    "Scala",
    "R",
    "Julia",
    "Perl",
    "Haskell",
    "Elixir",
    "Clojure",
    "F#",
    "Dart",
    "Lua",
    "MATLAB",
    "SQL",
    "Bash",
]

# Generate base coordinates with well-separated clusters
# Order: Python, JavaScript, Java, C++, Ruby, Go, Rust, Swift, Kotlin, TypeScript,
#        PHP, Scala, R, Julia, Perl, Haskell, Elixir, Clojure, F#, Dart,
#        Lua, MATLAB, SQL, Bash
base_x = np.array(
    [
        -1.0,
        0.8,
        1.5,
        0.5,
        -3.8,
        -2.2,
        -3.0,
        2.0,
        2.5,
        1.0,  # First 10
        3.5,
        2.8,
        -0.5,
        -2.0,
        4.2,
        4.5,
        4.0,
        3.5,
        0.5,
        3.0,  # Next 10
        -1.5,
        -2.5,
        1.0,
        3.5,  # Last 4: Lua, MATLAB, SQL, Bash
    ]
)
base_y = np.array(
    [
        -2.0,
        2.0,
        -0.5,
        2.8,
        -2.8,
        0.5,
        1.0,
        3.5,
        -1.5,
        0.0,  # First 10
        -1.5,
        1.2,
        -3.0,
        2.0,
        -0.5,
        1.5,
        -2.5,
        0.0,
        -1.8,
        2.8,  # Next 10
        0.5,
        -0.8,
        -3.5,
        4.5,  # Last 4: Lua, MATLAB, SQL, Bash
    ]
)

# Add small jitter to prevent exact overlaps
x = base_x + np.random.uniform(-0.1, 0.1, len(base_x))
y = base_y + np.random.uniform(-0.1, 0.1, len(base_y))

# Define language categories for coloring
categories = [
    "General Purpose",
    "Web",
    "Enterprise",
    "Systems",
    "Scripting",
    "Systems",
    "Systems",
    "Mobile",
    "Mobile",
    "Web",
    "Web",
    "JVM",
    "Data Science",
    "Data Science",
    "Scripting",
    "Functional",
    "Functional",
    "Functional",
    "Functional",
    "Mobile",
    "Scripting",
    "Data Science",
    "Data",
    "Scripting",
]

# Create DataFrame for seaborn
df = pd.DataFrame({"x": x, "y": y, "language": languages, "category": categories})

# Define colorblind-safe palette for categories
category_colors = {
    "General Purpose": "#4477AA",
    "Web": "#EE6677",
    "Enterprise": "#228833",
    "Systems": "#CCBB44",
    "Scripting": "#66CCEE",
    "Mobile": "#AA3377",
    "JVM": "#BBBBBB",
    "Data Science": "#44AA99",
    "Functional": "#882255",
    "Data": "#999933",
}

# Create figure using seaborn's FacetGrid for better integration
g = sns.FacetGrid(df, height=9, aspect=16 / 9)

# Use seaborn's scatterplot to create the base structure with category colors
g.map_dataframe(
    sns.scatterplot,
    x="x",
    y="y",
    hue="category",
    palette=category_colors,
    s=0,  # Invisible markers (text labels replace them)
    legend=False,
)

ax = g.ax

# Add text labels at each coordinate position with larger font
for _, row in df.iterrows():
    color = category_colors[row["category"]]
    ax.text(
        row["x"],
        row["y"],
        row["language"],
        fontsize=20,
        fontweight="bold",
        ha="center",
        va="center",
        color=color,
        alpha=0.9,
    )

# Create custom legend for categories
legend_elements = [
    Line2D([0], [0], marker="o", color="w", markerfacecolor=color, markersize=12, label=cat)
    for cat, color in category_colors.items()
]
ax.legend(
    handles=legend_elements,
    title="Category",
    loc="upper left",
    bbox_to_anchor=(0.0, 0.98),
    framealpha=0.95,
    fontsize=12,
    title_fontsize=14,
    ncol=2,
)

# Styling with seaborn's despine
sns.despine(ax=ax, left=False, bottom=False)

ax.set_xlabel("Dimension 1 (t-SNE)", fontsize=22)
ax.set_ylabel("Dimension 2 (t-SNE)", fontsize=22)
ax.set_title("scatter-text · seaborn · pyplots.ai", fontsize=26)
ax.tick_params(axis="both", labelsize=18)
ax.grid(True, alpha=0.3, linestyle="--")

# Set axis limits with padding for text labels
x_margin = 1.2
y_margin = 1.0
ax.set_xlim(x.min() - x_margin, x.max() + x_margin)
ax.set_ylim(y.min() - y_margin, y.max() + y_margin)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
