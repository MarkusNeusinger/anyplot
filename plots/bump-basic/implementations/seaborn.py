"""pyplots.ai
bump-basic: Basic Bump Chart
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 86/100 | Updated: 2026-02-22
"""

import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data - Sports league standings over 6 weeks
teams = ["Lions", "Tigers", "Bears", "Eagles", "Wolves"]
weeks = ["Week 1", "Week 2", "Week 3", "Week 4", "Week 5", "Week 6"]
ranks = [
    3,
    2,
    1,
    1,
    2,
    1,  # Lions - start mid, climb to top
    1,
    1,
    2,
    3,
    1,
    2,  # Tigers - start top, fluctuate
    5,
    4,
    4,
    2,
    3,
    3,  # Bears - steady climb from bottom
    2,
    3,
    3,
    4,
    4,
    5,  # Eagles - gradual decline
    4,
    5,
    5,
    5,
    5,
    4,  # Wolves - mostly bottom, slight recovery
]
df = pd.DataFrame(
    {"Team": [team for team in teams for _ in weeks], "Competition Week": weeks * len(teams), "League Position": ranks}
)

# Colorblind-safe muted palette via seaborn (Python Blue first)
palette = sns.color_palette(["#306998", "#D4823E", "#8B6CAF", "#3A9E8F", "#C27185"])
markers = {"Lions": "o", "Tigers": "X", "Bears": "s", "Eagles": "P", "Wolves": "D"}

# Refined theme
sns.set_theme(style="whitegrid", rc={"grid.linestyle": "--", "grid.alpha": 0.15})
fig, ax = plt.subplots(figsize=(16, 9))

sns.lineplot(
    data=df,
    x="Competition Week",
    y="League Position",
    hue="Team",
    style="Team",
    markers=markers,
    dashes=False,
    markersize=18,
    linewidth=4,
    palette=palette,
    hue_order=teams,
    sort=False,
    ax=ax,
)

# Invert y-axis so rank 1 is at top
ax.invert_yaxis()
ax.set_yticks([1, 2, 3, 4, 5])
ax.xaxis.grid(False)
sns.despine(ax=ax)

# Style
ax.set_xlabel("Competition Week", fontsize=20)
ax.set_ylabel("League Position (Rank)", fontsize=20)
ax.set_title("bump-basic · seaborn · pyplots.ai", fontsize=24, fontweight="medium", pad=20)
ax.tick_params(axis="both", labelsize=16)

# End-of-line labels for direct identification and storytelling
final_positions = {team: ranks[i * 6 + 5] for i, team in enumerate(teams)}
for i, team in enumerate(teams):
    rank = final_positions[team]
    ax.annotate(
        team,
        xy=(5, rank),
        xytext=(12, 0),
        textcoords="offset points",
        fontsize=15,
        fontweight="bold" if rank <= 2 else "normal",
        color=palette[i],
        va="center",
    )

# Remove legend (replaced by end-of-line labels for cleaner design)
ax.get_legend().remove()

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
