""" pyplots.ai
line-win-probability: Win Probability Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    coord_cartesian,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_hline,
    geom_line,
    geom_point,
    geom_rect,
    geom_ribbon,
    geom_segment,
    geom_text,
    ggplot,
    labs,
    scale_alpha_identity,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data
np.random.seed(42)

n_plays = 130
plays = np.arange(n_plays)
win_prob = np.zeros(n_plays)
win_prob[0] = 0.50

scoring_plays = {
    12: ("FG Home", 0.10),
    28: ("TD Away", -0.18),
    42: ("TD Home", 0.22),
    55: ("FG Away", -0.08),
    68: ("TD Home", 0.15),
    82: ("TD Away", -0.20),
    95: ("FG Home", 0.12),
    110: ("TD Home", 0.16),
    122: ("FG Away", -0.05),
}

events = {}
for i in range(1, n_plays):
    drift = np.random.normal(0, 0.012)
    if i in scoring_plays:
        label, shift = scoring_plays[i]
        win_prob[i] = win_prob[i - 1] + shift + drift
        events[i] = label
    else:
        win_prob[i] = win_prob[i - 1] + drift

win_prob = np.clip(win_prob, 0.04, 0.96)

for i in range(n_plays - 8, n_plays):
    t = (i - (n_plays - 8)) / 7.0
    win_prob[i] = win_prob[n_plays - 9] * (1 - t) + 0.78 * t

home_fill = np.maximum(win_prob, 0.5)
away_fill = np.minimum(win_prob, 0.5)

df = pd.DataFrame({"play": plays, "win_prob": win_prob})

df_home = pd.DataFrame({"play": plays, "ymin": 0.5, "ymax": home_fill, "team": "Eagles (Home)"})
df_away = pd.DataFrame({"play": plays, "ymin": away_fill, "ymax": 0.5, "team": "Cowboys (Away)"})
df_ribbon = pd.concat([df_home, df_away], ignore_index=True)

event_df = pd.DataFrame(
    {"play": list(events.keys()), "win_prob": [win_prob[p] for p in events.keys()], "label": list(events.values())}
)

# Smart annotation positioning with staggered offsets to avoid overlap in Q4
label_offsets = []
for _idx, row in event_df.iterrows():
    base = 0.06 if row["win_prob"] > 0.5 else -0.06
    # Extra offset for crowded late-game region
    if row["play"] >= 90:
        base *= 1.5
    label_offsets.append(row["win_prob"] + base)
event_df["label_y"] = label_offsets

# Highlight the decisive moment (TD Home at play 110 that sealed the game)
decisive_play = 110
highlight_df = pd.DataFrame({"xmin": [104], "xmax": [116], "ymin": [0.50], "ymax": [0.96], "alpha": [0.06]})

# Quarter boundary data for geom_segment (plotnine-idiomatic layer composition)
quarter_df = pd.DataFrame({"x": [32, 65, 97], "ymin": [0.0] * 3, "ymax": [1.0] * 3})

# Plot
quarter_breaks = [0, 32, 65, 97, 129]
quarter_labels = ["Kickoff", "Q2", "Halftime", "Q4", "Final"]

plot = (
    ggplot()
    # Decisive moment highlight zone
    + geom_rect(
        aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", alpha="alpha"),
        data=highlight_df,
        fill="#DAA520",
        inherit_aes=False,
    )
    + scale_alpha_identity()
    # Team-colored area fills
    + geom_ribbon(aes(x="play", ymin="ymin", ymax="ymax", fill="team"), data=df_ribbon, alpha=0.35)
    # 50% reference line
    + geom_hline(yintercept=0.5, color="#888888", size=0.6, linetype="dashed")
    # Quarter boundaries via geom_segment (plotnine-idiomatic vs geom_vline)
    + geom_segment(
        aes(x="x", xend="x", y="ymin", yend="ymax"),
        data=quarter_df,
        color="#cccccc",
        size=0.4,
        linetype="dotted",
        inherit_aes=False,
    )
    # Win probability trace
    + geom_line(aes(x="play", y="win_prob"), data=df, color="#1a1a1a", size=1.2)
    # Scoring event markers
    + geom_point(
        aes(x="play", y="win_prob"), data=event_df, color="#1a1a1a", size=4, fill="white", stroke=0.8, shape="o"
    )
    # Event annotations
    + geom_text(aes(x="play", y="label_y", label="label"), data=event_df, size=7, fontweight="bold", color="#333333")
    # Scales
    + scale_fill_manual(values={"Eagles (Home)": "#004C54", "Cowboys (Away)": "#8B1A1A"})
    + scale_x_continuous(breaks=quarter_breaks, labels=quarter_labels, expand=(0.03, 2))
    + scale_y_continuous(
        labels=lambda lst: [f"{int(v * 100)}%" for v in lst], limits=(0, 1), breaks=[0, 0.25, 0.5, 0.75, 1.0]
    )
    + coord_cartesian(xlim=(-2, 134))
    + labs(
        x="Game Progression", y="Home Win Probability", title="line-win-probability · plotnine · pyplots.ai", fill=""
    )
    # Final score box - placed bottom-left for balance
    + annotate(
        "label",
        x=10,
        y=0.06,
        label="Final: Eagles 24 – Cowboys 17",
        size=9,
        fill="#f5f5f5",
        color="#333333",
        fontweight="bold",
        label_padding=0.5,
    )
    # Theme with plotnine-specific element styling
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title_x=element_text(size=18),
        axis_title_y=element_text(size=18),
        axis_text=element_text(size=16, color="#555555"),
        legend_text=element_text(size=15),
        legend_position="top",
        legend_background=element_rect(fill="#fafafa", color="#e0e0e0", size=0.3),
        legend_key_size=18,
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#e8e8e8", size=0.3),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
