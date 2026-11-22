"""anyplot.ai
scatter-text: Scatter Plot with Text Labels Instead of Points
Library: matplotlib 3.10.9 | Python 3.13.13
Quality: pending | Updated: 2026-05-17
"""

import os

import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.patches import Patch


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions, one per category in order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
LABEL = "Language"  # role: label
X = "Embedding Dimension 1"  # role: x
Y = "Embedding Dimension 2"  # role: y
PARADIGM = "Paradigm"  # role: extra

# Data: replace this block with your own table, for example df = pd.read_csv("embeddings.csv")
# Programming languages positioned by paradigm similarity (simulating dimensionality reduction output)
rows = [
    ("Python", 1.5, 5.8, "Dynamic/Scripting"),
    ("JavaScript", 3.2, 4.8, "Dynamic/Scripting"),
    ("Ruby", 2.5, 5.5, "Dynamic/Scripting"),
    ("TypeScript", 3.5, 4.3, "Dynamic/Scripting"),
    ("Julia", 2.2, 4.8, "Dynamic/Scripting"),
    ("R", 1.2, 4.2, "Dynamic/Scripting"),
    ("MATLAB", 2.3, 3.8, "Dynamic/Scripting"),
    ("Perl", 3.5, 3.2, "Dynamic/Scripting"),
    ("PHP", 2.5, 2.8, "Dynamic/Scripting"),
    ("Lua", 4.5, 2.5, "Dynamic/Scripting"),
    ("Dart", 5.8, 4.5, "Dynamic/Scripting"),
    ("Haskell", 0.5, 6.8, "Functional"),
    ("Clojure", 1.0, 6.5, "Functional"),
    ("Elixir", 0.8, 5.8, "Functional"),
    ("F#", 2.8, 6.2, "Functional"),
    ("OCaml", 0.3, 6.2, "Functional"),
    ("Erlang", 1.8, 5.5, "Functional"),
    ("Crystal", 3.2, 5.8, "Functional"),
    ("C++", 5.8, 2.0, "Systems"),
    ("Go", 6.2, 3.5, "Systems"),
    ("Rust", 6.8, 2.5, "Systems"),
    ("Swift", 5.0, 3.8, "Systems"),
    ("Zig", 6.5, 1.8, "Systems"),
    ("Nim", 5.5, 2.2, "Systems"),
    ("Fortran", 7.0, 1.2, "Systems"),
    ("Java", 4.0, 3.2, "JVM-based"),
    ("Kotlin", 4.8, 3.2, "JVM-based"),
    ("Scala", 3.0, 4.0, "JVM-based"),
    ("C#", 4.2, 3.0, "JVM-based"),
    ("Groovy", 4.5, 3.2, "JVM-based"),
]
df = pd.DataFrame(rows, columns=[LABEL, X, Y, PARADIGM])

# Plot: reads only df and the constants above
fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)
ax.set_facecolor(PAGE_BG)

# The text is the mark: every label is centered on its exact (x, y) value
legend_elements = []
for i, (paradigm, group) in enumerate(df.groupby(PARADIGM, sort=False)):
    color = IMPRINT_PALETTE[i % len(IMPRINT_PALETTE)]
    legend_elements.append(Patch(facecolor=color, label=paradigm))
    for xi, yi, label in zip(group[X], group[Y], group[LABEL], strict=True):
        ax.text(xi, yi, label, fontsize=9, ha="center", va="center", color=color, fontweight="bold", alpha=0.9)

# Axis limits with padding around the data
x_pad = (df[X].max() - df[X].min()) * 0.06
y_pad = (df[Y].max() - df[Y].min()) * 0.1
ax.set_xlim(df[X].min() - x_pad, df[X].max() + x_pad)
ax.set_ylim(df[Y].min() - y_pad, df[Y].max() + y_pad)

# Style
ax.set_xlabel(X, fontsize=10, color=INK)
ax.set_ylabel(Y, fontsize=10, color=INK)
ax.set_title("scatter-text · python · matplotlib · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

for side in ("top", "right"):
    ax.spines[side].set_visible(False)
for side in ("left", "bottom"):
    ax.spines[side].set_color(INK_SOFT)
ax.grid(True, alpha=0.1, linewidth=0.8, color=INK)

leg = ax.legend(
    handles=legend_elements, title=PARADIGM, loc="upper right", fontsize=8, title_fontsize=8, framealpha=0.9
)
leg.get_frame().set_facecolor(PAGE_BG)
leg.get_frame().set_edgecolor(INK_SOFT)
plt.setp(leg.get_texts(), color=INK_SOFT)
leg.get_title().set_color(INK_SOFT)

plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
