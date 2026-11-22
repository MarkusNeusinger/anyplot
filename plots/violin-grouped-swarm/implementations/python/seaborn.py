"""anyplot.ai
violin-grouped-swarm: Grouped Violin Plot with Swarm Overlay
Library: seaborn 0.13.2 | Python 3.13.13
Quality: 93/100 | Updated: 2026-05-18
"""

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

# Imprint palette: all eight positions in canonical order
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Columns: set these to your table's column names
TEST_TYPE = "Test Type"  # role: category
EXPERIENCE = "Experience"  # role: group
SCORE = "Score"  # role: value

# Data: replace this block with your own table, for example df = pd.read_csv("scores.csv")
np.random.seed(42)
test_types = ["Reading Comprehension", "Arithmetic", "Pattern Recognition"]
experience_levels = ["Novice", "Expert"]
# (mean, std) of the cognitive test score per test type, for Novice then Expert
profiles = {
    "Reading Comprehension": [(72, 12), (88, 6)],
    "Arithmetic": [(65, 15), (85, 8)],
    "Pattern Recognition": [(58, 18), (82, 10)],
}
rows = []
for test_type in test_types:
    for exp_level, (mean, std) in zip(experience_levels, profiles[test_type]):
        scores = np.clip(np.random.normal(mean, std, 45), 20, 100)
        rows.extend({TEST_TYPE: test_type, EXPERIENCE: exp_level, SCORE: score} for score in scores)
df = pd.DataFrame(rows)

# Plot
n_groups = df[EXPERIENCE].nunique()
palette = IMPRINT_PALETTE[:n_groups]

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

fig, ax = plt.subplots(figsize=(8, 4.5), dpi=400, facecolor=PAGE_BG)

# Translucent violins so the swarm points stay visible
sns.violinplot(
    data=df, x=TEST_TYPE, y=SCORE, hue=EXPERIENCE, palette=palette, alpha=0.5, inner=None, ax=ax, linewidth=1
)

# Swarm overlay dodged onto each violin, in the hue of its group
sns.swarmplot(
    data=df, x=TEST_TYPE, y=SCORE, hue=EXPERIENCE, palette=palette, dodge=True, size=2, alpha=0.7, ax=ax, legend=False
)

# Style
ax.set_xlabel(TEST_TYPE, fontsize=10, color=INK)
ax.set_ylabel(SCORE, fontsize=10, color=INK)
ax.set_title("violin-grouped-swarm · python · seaborn · anyplot.ai", fontsize=12, fontweight="medium", color=INK)
ax.tick_params(axis="both", labelsize=8, colors=INK_SOFT)

ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
ax.spines["left"].set_color(INK_SOFT)
ax.spines["bottom"].set_color(INK_SOFT)

ax.yaxis.grid(True, alpha=0.10, linewidth=0.8, color=INK)
ax.set_axisbelow(True)

ax.legend(title=EXPERIENCE, fontsize=8, title_fontsize=9, loc="lower right")

plt.tight_layout()
plt.savefig(f"plot-{THEME}.png", dpi=400, facecolor=PAGE_BG)
