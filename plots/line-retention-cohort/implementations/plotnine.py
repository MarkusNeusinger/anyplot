""" pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 86/100 | Created: 2026-03-16
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_alpha_identity,
    scale_color_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data
np.random.seed(42)

cohorts = {
    "Jan 2025": {"size": 1245, "decay": 0.18},
    "Feb 2025": {"size": 1102, "decay": 0.16},
    "Mar 2025": {"size": 1380, "decay": 0.14},
    "Apr 2025": {"size": 1290, "decay": 0.12},
    "May 2025": {"size": 1455, "decay": 0.10},
}

weeks = np.arange(0, 13)
rows = []

for cohort_name, info in cohorts.items():
    retention = 100 * np.exp(-info["decay"] * weeks)
    noise = np.concatenate(([0], np.cumsum(np.random.normal(0, 0.8, len(weeks) - 1))))
    retention = np.clip(retention + noise, 0, 100)
    retention[0] = 100.0
    label = f"{cohort_name} (n={info['size']:,})"
    for w, r in zip(weeks, retention, strict=True):
        rows.append({"week": w, "retention": r, "cohort": label})

df = pd.DataFrame(rows)

cohort_labels = list(df["cohort"].unique())
df["cohort"] = pd.Categorical(df["cohort"], categories=cohort_labels, ordered=True)

alpha_map = dict(zip(cohort_labels, [0.45, 0.55, 0.65, 0.80, 1.0], strict=True))
df["line_alpha"] = df["cohort"].map(alpha_map).astype(float)

# Colors
colors = ["#8FADC2", "#7A9AB5", "#306998", "#E8783A", "#D4522A"]

# Plot
plot = (
    ggplot(df, aes(x="week", y="retention", color="cohort", group="cohort"))
    + geom_hline(yintercept=20, linetype="dashed", color="#AAAAAA", size=0.6)
    + geom_line(aes(alpha="line_alpha"), size=1.5)
    + scale_alpha_identity()
    + geom_point(aes(alpha="line_alpha"), size=2.5)
    + scale_color_manual(values=colors)
    + scale_x_continuous(breaks=range(0, 13), labels=[str(w) for w in range(0, 13)])
    + scale_y_continuous(
        limits=(0, 105), breaks=[0, 20, 40, 60, 80, 100], labels=["0%", "20%", "40%", "60%", "80%", "100%"]
    )
    + annotate("text", x=12.3, y=22.5, label="20% threshold", size=9, color="#999999", ha="right")
    + labs(
        x="Weeks Since Signup",
        y="Retained Users",
        color="Cohort",
        title="line-retention-cohort · plotnine · pyplots.ai",
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=14),
        legend_position="right",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.5, alpha=0.5),
        axis_line_x=element_line(color="#333333", size=0.5),
        axis_line_y=element_line(color="#333333", size=0.5),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
