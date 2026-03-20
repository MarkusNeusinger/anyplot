""" pyplots.ai
scatter-pitch-events: Soccer Pitch Event Map
Library: seaborn 0.13.2 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-20
"""

import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.lines import Line2D


# Data
np.random.seed(42)

n_events = 180
event_types = np.random.choice(["Pass", "Shot", "Tackle", "Interception"], size=n_events, p=[0.50, 0.15, 0.20, 0.15])
outcomes = np.random.choice(["Successful", "Unsuccessful"], size=n_events, p=[0.65, 0.35])

x_coords = np.zeros(n_events)
y_coords = np.zeros(n_events)

for i, etype in enumerate(event_types):
    if etype == "Pass":
        x_coords[i] = np.random.uniform(10, 95)
        y_coords[i] = np.random.uniform(5, 63)
    elif etype == "Shot":
        x_coords[i] = np.random.uniform(72, 100)
        y_coords[i] = np.random.uniform(18, 50)
    elif etype == "Tackle":
        x_coords[i] = np.random.uniform(5, 70)
        y_coords[i] = np.random.uniform(5, 63)
    elif etype == "Interception":
        x_coords[i] = np.random.uniform(15, 80)
        y_coords[i] = np.random.uniform(5, 63)

arrow_dx = np.zeros(n_events)
arrow_dy = np.zeros(n_events)
for i, etype in enumerate(event_types):
    if etype == "Pass":
        arrow_dx[i] = np.random.uniform(5, 20) * np.random.choice([-1, 1], p=[0.2, 0.8])
        arrow_dy[i] = np.random.uniform(-10, 10)
    elif etype == "Shot":
        arrow_dx[i] = np.random.uniform(3, 12)
        arrow_dy[i] = np.random.uniform(-5, 5)

df = pd.DataFrame(
    {"x": x_coords, "y": y_coords, "Event Type": event_types, "Outcome": outcomes, "dx": arrow_dx, "dy": arrow_dy}
)

# Plot
palette = {"Pass": "#4FC3F7", "Shot": "#FF7043", "Tackle": "#FFD54F", "Interception": "#CE93D8"}
marker_map = {"Pass": "o", "Shot": "*", "Tackle": "^", "Interception": "D"}

sns.set_theme(style="white", rc={"axes.facecolor": "#2d8a4e", "figure.facecolor": "#1a472a"})
sns.set_context("talk", font_scale=1.1)

fig, ax = plt.subplots(figsize=(16, 9))
fig.set_facecolor("#1a472a")
ax.set_facecolor("#2d8a4e")

# Draw pitch markings
pitch_color = "white"
lw = 2.0
alpha_line = 0.9

ax.plot([0, 105, 105, 0, 0], [0, 0, 68, 68, 0], color=pitch_color, lw=lw + 0.5, alpha=alpha_line)
ax.plot([52.5, 52.5], [0, 68], color=pitch_color, lw=lw, alpha=alpha_line)

center_circle = patches.Circle((52.5, 34), 9.15, fill=False, edgecolor=pitch_color, lw=lw, alpha=alpha_line)
ax.add_patch(center_circle)
ax.plot(52.5, 34, "o", color=pitch_color, markersize=4, alpha=alpha_line)

ax.plot([0, 16.5, 16.5, 0], [13.84, 13.84, 54.16, 54.16], color=pitch_color, lw=lw, alpha=alpha_line)
ax.plot([105, 88.5, 88.5, 105], [13.84, 13.84, 54.16, 54.16], color=pitch_color, lw=lw, alpha=alpha_line)
ax.plot([0, 5.5, 5.5, 0], [24.84, 24.84, 43.16, 43.16], color=pitch_color, lw=lw, alpha=alpha_line)
ax.plot([105, 99.5, 99.5, 105], [24.84, 24.84, 43.16, 43.16], color=pitch_color, lw=lw, alpha=alpha_line)

ax.plot(11, 34, "o", color=pitch_color, markersize=4, alpha=alpha_line)
ax.plot(94, 34, "o", color=pitch_color, markersize=4, alpha=alpha_line)

left_arc = patches.Arc(
    (11, 34), 18.3, 18.3, angle=0, theta1=308, theta2=52, edgecolor=pitch_color, lw=lw, alpha=alpha_line
)
ax.add_patch(left_arc)
right_arc = patches.Arc(
    (94, 34), 18.3, 18.3, angle=0, theta1=128, theta2=232, edgecolor=pitch_color, lw=lw, alpha=alpha_line
)
ax.add_patch(right_arc)

for cx, cy, t1, t2 in [(0, 0, 0, 90), (105, 0, 90, 180), (105, 68, 180, 270), (0, 68, 270, 360)]:
    corner = patches.Arc((cx, cy), 2, 2, angle=0, theta1=t1, theta2=t2, edgecolor=pitch_color, lw=lw, alpha=alpha_line)
    ax.add_patch(corner)

ax.plot([-1.5, 0], [30.34, 30.34], color=pitch_color, lw=lw + 1, alpha=alpha_line)
ax.plot([-1.5, 0], [37.66, 37.66], color=pitch_color, lw=lw + 1, alpha=alpha_line)
ax.plot([-1.5, -1.5], [30.34, 37.66], color=pitch_color, lw=lw + 1, alpha=alpha_line)
ax.plot([105, 106.5], [30.34, 30.34], color=pitch_color, lw=lw + 1, alpha=alpha_line)
ax.plot([105, 106.5], [37.66, 37.66], color=pitch_color, lw=lw + 1, alpha=alpha_line)
ax.plot([106.5, 106.5], [30.34, 37.66], color=pitch_color, lw=lw + 1, alpha=alpha_line)

# Density contours per event type using seaborn kdeplot
for etype in ["Pass", "Shot", "Tackle", "Interception"]:
    subset = df[df["Event Type"] == etype]
    if len(subset) > 5:
        sns.kdeplot(
            data=subset,
            x="x",
            y="y",
            color=palette[etype],
            levels=3,
            alpha=0.25,
            linewidths=1.2,
            ax=ax,
            zorder=3,
            warn_singular=False,
            clip=((0, 105), (0, 68)),
        )

# Event markers using seaborn scatterplot with hue and style
df_success = df[df["Outcome"] == "Successful"]
df_unsuccess = df[df["Outcome"] == "Unsuccessful"]

sns.scatterplot(
    data=df_success,
    x="x",
    y="y",
    hue="Event Type",
    style="Event Type",
    markers=marker_map,
    palette=palette,
    s=120,
    alpha=0.92,
    edgecolor="white",
    linewidth=0.5,
    legend=False,
    ax=ax,
    zorder=5,
)

sns.scatterplot(
    data=df_unsuccess,
    x="x",
    y="y",
    hue="Event Type",
    style="Event Type",
    markers=marker_map,
    palette=palette,
    s=80,
    alpha=0.55,
    edgecolor="white",
    linewidth=0.8,
    legend=False,
    ax=ax,
    zorder=5,
)

# Directional arrows — only for successful events, thinned to reduce clutter
arrows = df_success[df_success["Event Type"].isin(["Pass", "Shot"])]
arrow_sample = arrows.sample(frac=0.6, random_state=42)
for _, row in arrow_sample.iterrows():
    ax.annotate(
        "",
        xy=(row["x"] + row["dx"], row["y"] + row["dy"]),
        xytext=(row["x"], row["y"]),
        arrowprops={"arrowstyle": "->", "color": palette[row["Event Type"]], "lw": 1.0, "alpha": 0.45},
        zorder=4,
    )

# Style
ax.set_xlim(-4, 109)
ax.set_ylim(-3, 71)
ax.set_aspect("equal")
ax.axis("off")

ax.set_title("scatter-pitch-events · seaborn · pyplots.ai", fontsize=24, fontweight="medium", color="white", pad=20)

# Legend
legend_elements = []
for etype in ["Pass", "Shot", "Tackle", "Interception"]:
    legend_elements.append(
        Line2D(
            [0],
            [0],
            marker=marker_map[etype],
            color="none",
            markerfacecolor=palette[etype],
            markeredgecolor="white",
            markersize=12 if etype == "Shot" else 9,
            markeredgewidth=0.8,
            label=f"{etype} (successful)",
        )
    )
    legend_elements.append(
        Line2D(
            [0],
            [0],
            marker=marker_map[etype],
            color="none",
            markerfacecolor=palette[etype],
            markeredgecolor="white",
            markersize=10 if etype == "Shot" else 8,
            markeredgewidth=0.8,
            alpha=0.55,
            label=f"{etype} (unsuccessful)",
        )
    )

ax.legend(
    handles=legend_elements,
    loc="lower center",
    bbox_to_anchor=(0.5, -0.06),
    ncol=4,
    fontsize=18,
    frameon=True,
    facecolor="#1a472a",
    edgecolor="white",
    labelcolor="white",
    handletextpad=0.5,
    columnspacing=1.5,
)

plt.tight_layout()
plt.savefig("plot.png", dpi=300, bbox_inches="tight", facecolor=fig.get_facecolor())
