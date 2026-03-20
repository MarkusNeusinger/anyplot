""" pyplots.ai
line-win-probability: Win Probability Chart
Library: letsplot 4.9.0 | Python 3.14.3
Quality: 92/100 | Created: 2026-03-20
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data — simulated NFL game: Eagles vs Cowboys
np.random.seed(42)
total_plays = 120
play_number = np.arange(total_plays)

# Generate win probability with realistic momentum swings
win_prob = np.zeros(total_plays)
win_prob[0] = 0.50

# Scoring events with play index, probability shift, and label
events = [
    (8, 0.12, "Eagles FG 3-0"),
    (22, -0.15, "Cowboys TD 3-7"),
    (35, 0.18, "Eagles TD 10-7"),
    (52, 0.08, "Eagles FG 13-7"),
    (68, -0.22, "Cowboys TD 13-14"),
    (78, 0.15, "Eagles TD 20-14"),
    (92, -0.10, "Cowboys FG 20-17"),
    (105, 0.20, "Eagles TD 27-17"),
]

event_plays = {e[0]: e[1] for e in events}

for i in range(1, total_plays):
    drift = 0.002 if i > 90 else 0.0
    noise = np.random.normal(0, 0.02)
    shift = event_plays.get(i, 0.0)
    win_prob[i] = np.clip(win_prob[i - 1] + shift + noise + drift, 0.02, 0.98)

# Force final convergence to winner
win_prob[-5:] = np.linspace(win_prob[-6], 0.95, 5)
win_prob[-1] = 0.97

# Create main dataframe with helper columns for area fill
df = pd.DataFrame(
    {
        "play": play_number,
        "win_prob": win_prob,
        "baseline": 0.5,
        "above_50": np.maximum(win_prob, 0.5),
        "below_50": np.minimum(win_prob, 0.5),
    }
)

# Event annotations — select key swings only, with alternating positions
key_event_indices = [1, 2, 4, 5, 7]
nudge_directions = [-0.08, 0.07, -0.08, 0.07, -0.08]  # alternate below/above
key_events = pd.DataFrame(
    {
        "play": [events[i][0] for i in key_event_indices],
        "win_prob": [win_prob[events[i][0]] for i in key_event_indices],
        "label": [events[i][2] for i in key_event_indices],
        "label_y": [win_prob[events[i][0]] + nudge_directions[j] for j, i in enumerate(key_event_indices)],
    }
)

# Team colors
eagles_green = "#004C54"
cowboys_blue = "#869397"

# Plot
plot = (
    ggplot(df, aes(x="play"))  # noqa: F405
    # Area fill — home team above 50%
    + geom_ribbon(  # noqa: F405
        aes(ymin="baseline", ymax="above_50"),  # noqa: F405
        fill=eagles_green,
        alpha=0.35,
    )
    # Area fill — away team below 50%
    + geom_ribbon(  # noqa: F405
        aes(ymin="below_50", ymax="baseline"),  # noqa: F405
        fill=cowboys_blue,
        alpha=0.35,
    )
    # Win probability line
    + geom_line(  # noqa: F405
        aes(y="win_prob"),  # noqa: F405
        color="#1a1a1a",
        size=1.8,
        tooltips=layer_tooltips()  # noqa: F405
        .line("Play @play")
        .format("win_prob", ".0%")
        .line("Win prob: @win_prob"),
    )
    # 50% reference line
    + geom_hline(yintercept=0.5, color="#888888", size=0.8, linetype="dashed")  # noqa: F405
    # Quarter dividers
    + geom_vline(xintercept=30, color="#CCCCCC", size=0.6, linetype="dotted")  # noqa: F405
    + geom_vline(xintercept=60, color="#CCCCCC", size=0.6, linetype="dotted")  # noqa: F405
    + geom_vline(xintercept=90, color="#CCCCCC", size=0.6, linetype="dotted")  # noqa: F405
    # Key event markers
    + geom_point(  # noqa: F405
        data=key_events,
        mapping=aes(x="play", y="win_prob"),  # noqa: F405
        size=6,
        color="#1a1a1a",
        fill="white",
        shape=21,
        stroke=2.0,
    )
    # Key event labels with background fill (letsplot geom_label)
    + geom_label(  # noqa: F405
        data=key_events,
        mapping=aes(x="play", y="label_y", label="label"),  # noqa: F405
        size=10,
        color="#1a1a1a",
        fill="white",
        alpha=0.85,
        label_padding=0.4,
        label_r=0.2,
        label_size=0.5,
    )
    # Scales
    + scale_y_continuous(  # noqa: F405
        breaks=[0.0, 0.25, 0.5, 0.75, 1.0], labels=["0%", "25%", "50%", "75%", "100%"]
    )
    + coord_cartesian(ylim=[0.0, 1.05])  # noqa: F405
    + scale_x_continuous(  # noqa: F405
        breaks=[0, 30, 60, 90, 120], labels=["Q1", "Q2", "Q3", "Q4", "End"]
    )
    # Labels
    + labs(  # noqa: F405
        x="Game Progress",
        y="Eagles Win Probability",
        title="line-win-probability \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="Eagles 27 \u2013 Cowboys 17  \u00b7  Eagles recover from Q3 deficit for convincing finish",
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + flavor_high_contrast_light()  # noqa: F405
    + theme(  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        axis_title=element_text(size=20),  # noqa: F405
        plot_title=element_text(size=24),  # noqa: F405
        plot_subtitle=element_text(size=16, color="#555555"),  # noqa: F405
        panel_grid_major_y=element_line(color="#E0E0E0", size=0.3),  # noqa: F405
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        plot_margin=[40, 60, 20, 20],
    )
)

# Save
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
