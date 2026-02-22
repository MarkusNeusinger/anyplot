""" pyplots.ai
bullet-basic: Basic Bullet Chart
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 87/100 | Updated: 2026-02-22
"""

import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns


# Data - Multiple KPIs with actual values, targets, and qualitative ranges
metrics = ["Revenue", "Customer\nSatisfaction", "Efficiency", "Quality\nScore"]
actuals = [78, 85, 35, 91]
targets = [90, 80, 75, 85]
# Ranges define thresholds for qualitative bands (poor/satisfactory/good)
ranges_list = [
    [50, 75, 100],  # Revenue
    [60, 80, 100],  # Customer Satisfaction
    [40, 60, 100],  # Efficiency
    [70, 85, 100],  # Quality Score
]

# Build a long-form DataFrame for qualitative range bands
range_labels = ["Good", "Satisfactory", "Poor"]
range_records = []
for metric, ranges in zip(metrics, ranges_list, strict=True):
    prev = 0
    for end, label in zip(ranges, range_labels[::-1], strict=True):
        range_records.append({"Metric": metric, "Range": label, "Start": prev, "Width": end - prev})
        prev = end
df_ranges = pd.DataFrame(range_records)

# Seaborn grayscale palette for qualitative bands (dark=poor, medium=satisfactory, light=good)
band_palette = dict(zip(range_labels, sns.light_palette("#555555", n_colors=4, reverse=True)[1:], strict=True))

# Create figure with seaborn theme
sns.set_theme(style="whitegrid", rc={"axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False})
fig, ax = plt.subplots(figsize=(16, 9))

# Draw qualitative range bands using seaborn barplot layering
range_height = 0.7
for label in range_labels:
    subset = df_ranges[df_ranges["Range"] == label]
    sns.barplot(
        data=subset,
        x="Width",
        y="Metric",
        color=band_palette[label],
        left=subset["Start"].values,
        width=range_height,
        edgecolor="none",
        ax=ax,
        zorder=1,
    )

# Actual value bars using seaborn barplot
df_actual = pd.DataFrame({"Metric": metrics, "Actual": actuals})
sns.barplot(
    data=df_actual,
    x="Actual",
    y="Metric",
    color="#306998",
    width=0.35,
    edgecolor="#1e4d6b",
    linewidth=1.5,
    ax=ax,
    zorder=3,
)

# Draw target markers as vertical lines
for i, target in enumerate(targets):
    ax.plot(
        [target, target],
        [i - range_height / 2 + 0.02, i + range_height / 2 - 0.02],
        color="#1a1a1a",
        linewidth=5,
        zorder=4,
        solid_capstyle="butt",
    )

# Add actual value labels at end of bars
for i, (actual, target) in enumerate(zip(actuals, targets, strict=True)):
    label_x = max(actual, target) + 2
    ax.text(label_x, i, f"{actual}%", va="center", ha="left", fontsize=18, fontweight="bold", color="#306998")

# Styling
ax.set_xlim(0, 115)
ax.set_xlabel("Performance (%)", fontsize=20)
ax.set_ylabel("")
ax.set_title("bullet-basic · seaborn · pyplots.ai", fontsize=24, fontweight="bold", pad=20)
ax.tick_params(axis="both", labelsize=16)
ax.tick_params(axis="y", length=0)

# Customize grid - subtle vertical lines only
ax.xaxis.grid(True, alpha=0.3, linestyle="--", zorder=0)
ax.yaxis.grid(False)

# Create legend
legend_elements = [
    mpatches.Patch(facecolor=band_palette["Poor"], label="Poor"),
    mpatches.Patch(facecolor=band_palette["Satisfactory"], label="Satisfactory"),
    mpatches.Patch(facecolor=band_palette["Good"], label="Good"),
    mpatches.Patch(facecolor="#306998", edgecolor="#1e4d6b", linewidth=1.5, label="Actual"),
    plt.Line2D([0], [0], color="#1a1a1a", linewidth=5, label="Target"),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=13, framealpha=0.95)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight")
