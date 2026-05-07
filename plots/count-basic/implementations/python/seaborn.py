""" anyplot.ai
count-basic: Basic Count Plot
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 94/100 | Updated: 2026-05-07
"""

import os
import sys
from pathlib import Path


# Avoid shadowing by the matplotlib.py file in same directory
script_dir = Path(__file__).parent
old_path = sys.path[:]
sys.path = [p for p in sys.path if str(p) != str(script_dir)]

import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import seaborn as sns  # noqa: E402


sys.path = old_path


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
BRAND = "#009E73"

# Data - Survey responses about preferred programming languages
np.random.seed(42)
languages = ["Python", "JavaScript", "Java", "C++", "Go", "Rust", "TypeScript", "Ruby"]
weights = [0.28, 0.22, 0.15, 0.10, 0.08, 0.07, 0.06, 0.04]
n_responses = 500
responses = np.random.choice(languages, size=n_responses, p=weights)

df = pd.DataFrame({"language": responses})

# Configure seaborn with theme-adaptive styling
sns.set_theme(
    style="ticks",
    rc={
        "figure.facecolor": PAGE_BG,
        "axes.facecolor": PAGE_BG,
        "axes.edgecolor": INK_SOFT,
        "axes.labelcolor": INK,
        "text.color": INK,
        "xtick.color": INK_SOFT,
        "ytick.color": INK_SOFT,
        "grid.color": INK,
        "grid.alpha": 0.10,
        "legend.facecolor": ELEVATED_BG,
        "legend.edgecolor": INK_SOFT,
    },
)

# Plot
fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)

# Count plot sorted by frequency (descending)
order = df["language"].value_counts().index.tolist()
sns.countplot(data=df, x="language", order=order, color=BRAND, ax=ax)

# Add count labels on top of bars for precision
for container in ax.containers:
    ax.bar_label(container, fontsize=16, padding=5, color=INK)

# Style
ax.set_xlabel("Programming Language", fontsize=20, color=INK)
ax.set_ylabel("Response Count", fontsize=20, color=INK)
ax.set_title("count-basic · seaborn · anyplot.ai", fontsize=24, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=16, colors=INK_SOFT)

# Subtle grid on y-axis only
ax.yaxis.grid(True, alpha=0.15, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

# Remove top and right spines for cleaner look
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
