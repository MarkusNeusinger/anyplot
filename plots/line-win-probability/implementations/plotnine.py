""" pyplots.ai
line-win-probability: Win Probability Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 87/100 | Created: 2026-03-20
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
    geom_ribbon,
    geom_text,
    geom_vline,
    ggplot,
    labs,
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

df_home = pd.DataFrame({"play": plays, "ymin": 0.5, "ymax": home_fill, "team": "Home (Eagles)"})
df_away = pd.DataFrame({"play": plays, "ymin": away_fill, "ymax": 0.5, "team": "Away (Cowboys)"})
df_ribbon = pd.concat([df_home, df_away], ignore_index=True)

event_df = pd.DataFrame(
    {"play": list(events.keys()), "win_prob": [win_prob[p] for p in events.keys()], "label": list(events.values())}
)
event_df["label_y"] = event_df["win_prob"] + np.where(event_df["win_prob"] > 0.5, 0.055, -0.055)

# Plot
quarter_breaks = [0, 32, 65, 97, 129]
quarter_labels = ["Kickoff", "Q2", "Halftime", "Q4", "Final"]

plot = (
    ggplot()
    + geom_ribbon(aes(x="play", ymin="ymin", ymax="ymax", fill="team"), data=df_ribbon, alpha=0.4)
    + geom_hline(yintercept=0.5, color="#666666", size=0.7, linetype="dashed")
    + geom_line(aes(x="play", y="win_prob"), data=df, color="#1a1a1a", size=1.2)
    + geom_point(aes(x="play", y="win_prob"), data=event_df, color="#1a1a1a", size=3, fill="white", stroke=0.5)
    + geom_text(aes(x="play", y="label_y", label="label"), data=event_df, size=7, fontweight="bold", color="#333333")
    + geom_vline(xintercept=[32, 65, 97], color="#bbbbbb", size=0.4, linetype="dotted")
    + scale_fill_manual(values={"Home (Eagles)": "#004C54", "Away (Cowboys)": "#8B1A1A"})
    + scale_x_continuous(breaks=quarter_breaks, labels=quarter_labels)
    + scale_y_continuous(
        labels=lambda lst: [f"{int(v * 100)}%" for v in lst], limits=(0, 1), breaks=[0, 0.25, 0.5, 0.75, 1.0]
    )
    + labs(
        x="Game Progression",
        y="Home Win Probability",
        title="line-win-probability \u00b7 plotnine \u00b7 pyplots.ai",
        fill="",
    )
    + annotate(
        "label",
        x=110,
        y=0.06,
        label="Final: Eagles 24 \u2013 Cowboys 17",
        size=9,
        fill="#f5f5f5",
        color="#333333",
        fontweight="bold",
        label_padding=0.4,
    )
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        plot_title=element_text(size=24, weight="bold"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        legend_text=element_text(size=16),
        legend_position="top",
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#e0e0e0", size=0.4),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
