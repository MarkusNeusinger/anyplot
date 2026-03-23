""" pyplots.ai
line-retention-cohort: User Retention Curve by Cohort
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 91/100 | Created: 2026-03-16
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    geom_ribbon,
    geom_text,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_alpha_identity,
    scale_color_manual,
    scale_size_identity,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data
np.random.seed(42)

cohorts = {
    "Jan 2025": {"size": 1245, "decay": 0.22, "plateau": 8},
    "Feb 2025": {"size": 1102, "decay": 0.17, "plateau": 12},
    "Mar 2025": {"size": 1380, "decay": 0.13, "plateau": 18},
    "Apr 2025": {"size": 1290, "decay": 0.11, "plateau": 22},
    "May 2025": {"size": 1455, "decay": 0.08, "plateau": 30},
}

weeks = np.arange(0, 13)
rows = []

for cohort_name, info in cohorts.items():
    base = (100 - info["plateau"]) * np.exp(-info["decay"] * weeks) + info["plateau"]
    noise = np.concatenate(([0], np.cumsum(np.random.normal(0, 0.6, len(weeks) - 1))))
    retention = np.clip(base + noise, 0, 100)
    retention[0] = 100.0
    label = f"{cohort_name} (n={info['size']:,})"
    for w, r in zip(weeks, retention, strict=True):
        rows.append({"week": w, "retention": r, "cohort": label})

df = pd.DataFrame(rows)

cohort_labels = list(df["cohort"].unique())
df["cohort"] = pd.Categorical(df["cohort"], categories=cohort_labels, ordered=True)

# Alpha: ensure oldest is still readable
alpha_values = [0.6, 0.7, 0.8, 0.9, 1.0]
alpha_map = dict(zip(cohort_labels, alpha_values, strict=True))
df["line_alpha"] = df["cohort"].map(alpha_map).astype(float)

# Line width: thinner for older, bolder for newer
size_values = [1.0, 1.2, 1.4, 1.6, 2.0]
size_map = dict(zip(cohort_labels, size_values, strict=True))
df["line_size"] = df["cohort"].map(size_map).astype(float)

# Ribbon data: show spread between oldest and newest cohort
oldest_label = cohort_labels[0]
newest_label = cohort_labels[-1]
df_oldest = df[df["cohort"] == oldest_label][["week", "retention"]].rename(columns={"retention": "ymin"})
df_newest = df[df["cohort"] == newest_label][["week", "retention"]].rename(columns={"retention": "ymax"})
df_ribbon = df_oldest.merge(df_newest, on="week")

# Colors: refined palette with clear progression
colors = ["#94B8D1", "#6A9EC1", "#306998", "#E07941", "#C94420"]

# Endpoint labels for storytelling
df_endpoints = df[df["week"] == 12].copy()
df_endpoints["ret_label"] = df_endpoints["retention"].apply(lambda x: f"{x:.0f}%")

# Plot
plot = (
    ggplot(df, aes(x="week", y="retention", color="cohort", group="cohort"))
    + geom_ribbon(
        aes(x="week", ymin="ymin", ymax="ymax"), data=df_ribbon, inherit_aes=False, fill="#306998", alpha=0.07
    )
    + geom_hline(yintercept=20, linetype="dashed", color="#AAAAAA", size=0.7)
    + geom_line(aes(alpha="line_alpha", size="line_size"))
    + scale_alpha_identity()
    + scale_size_identity()
    + geom_point(aes(alpha="line_alpha"), size=2.5, show_legend=False)
    + geom_text(aes(label="ret_label"), data=df_endpoints, nudge_x=0.5, size=10, ha="left", show_legend=False)
    + scale_color_manual(values=colors)
    + scale_x_continuous(breaks=range(0, 13), labels=[str(w) for w in range(0, 13)], expand=(0.02, 0.8))
    + scale_y_continuous(
        limits=(0, 108), breaks=[0, 20, 40, 60, 80, 100], labels=["0%", "20%", "40%", "60%", "80%", "100%"]
    )
    + annotate(
        "text",
        x=11.8,
        y=22.5,
        label="20% retention threshold",
        size=11,
        color="#888888",
        ha="right",
        fontstyle="italic",
    )
    + annotate(
        "label",
        x=6,
        y=55,
        label="Improvement\ngap",
        size=10,
        color="#306998",
        fill="#F0F4F8",
        alpha=0.85,
        ha="center",
        label_size=0,
    )
    + labs(
        x="Weeks Since Signup",
        y="Retained Users",
        color="Cohort",
        title="line-retention-cohort · plotnine · pyplots.ai",
    )
    + guides(color=guide_legend(override_aes={"size": 3, "alpha": 1}))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(family="sans-serif", size=14, color="#333333"),
        plot_title=element_text(size=24, weight="bold", color="#1a1a1a"),
        axis_title=element_text(size=20, color="#444444"),
        axis_text=element_text(size=16, color="#555555"),
        legend_title=element_text(size=18, weight="bold"),
        legend_text=element_text(size=14),
        legend_position="right",
        legend_background=element_rect(fill="#FAFAFA", color="#E0E0E0", size=0.5),
        legend_key=element_rect(fill="none", color="none"),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#EBEBEB", size=0.4, alpha=0.6),
        axis_line_x=element_line(color="#333333", size=0.5),
        axis_line_y=element_line(color="#333333", size=0.5),
        plot_margin=0.04,
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
