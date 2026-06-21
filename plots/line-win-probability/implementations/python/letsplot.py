"""anyplot.ai
line-win-probability: Win Probability Chart
Library: letsplot 4.10.1 | Python 3.13.14
Quality: 86/100 | Updated: 2026-06-21
"""

import os

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F401
from lets_plot import ggsave


LetsPlot.setup_html()  # noqa: F405

THEME = os.getenv("ANYPLOT_THEME", "light")

# Theme-adaptive chrome tokens
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint categorical palette — first series always #009E73
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]

# Team fills — semantic: home team (Eagles) → Imprint green, away (Cowboys) → Imprint blue
HOME_COLOR = IMPRINT_PALETTE[0]  # #009E73 — Eagles/home
AWAY_COLOR = IMPRINT_PALETTE[2]  # #4467A3 — Cowboys/away

# --- Data: simulated NFL game, Eagles vs Cowboys ---
np.random.seed(42)
total_plays = 120
play_number = np.arange(total_plays)

win_prob = np.zeros(total_plays)
win_prob[0] = 0.50

# Scoring events: (play_index, probability_shift, label)
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

# Converge to Eagles win at the end
win_prob[-5:] = np.linspace(win_prob[-6], 0.95, 5)
win_prob[-1] = 0.97

df = pd.DataFrame(
    {
        "play": play_number,
        "win_prob": win_prob,
        "baseline": 0.5,
        "above_50": np.maximum(win_prob, 0.5),
        "below_50": np.minimum(win_prob, 0.5),
    }
)

# Key events — alternating label offsets to avoid overlap
key_event_indices = [1, 2, 4, 5, 7]
nudge_directions = [-0.08, 0.07, -0.08, 0.07, -0.08]
key_events = pd.DataFrame(
    {
        "play": [events[i][0] for i in key_event_indices],
        "win_prob": [win_prob[events[i][0]] for i in key_event_indices],
        "label": [events[i][2] for i in key_event_indices],
        "label_y": [win_prob[events[i][0]] + nudge_directions[j] for j, i in enumerate(key_event_indices)],
    }
)

# --- Theme-adaptive chrome ---
anyplot_theme = theme(  # noqa: F405
    plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
    panel_background=element_rect(fill=PAGE_BG),  # noqa: F405
    panel_grid_major_y=element_line(color=INK_MUTED, size=0.2),  # noqa: F405
    panel_grid_major_x=element_blank(),  # noqa: F405
    panel_grid_minor=element_blank(),  # noqa: F405
    axis_title=element_text(color=INK, size=12),  # noqa: F405
    axis_text=element_text(color=INK_SOFT, size=10),  # noqa: F405
    axis_line=element_line(color=INK_SOFT),  # noqa: F405
    panel_border=element_blank(),  # noqa: F405
    plot_title=element_text(color=INK, size=16),  # noqa: F405
    plot_subtitle=element_text(color=INK_SOFT, size=10),  # noqa: F405
    plot_margin=[40, 60, 20, 20],
)

# --- Build plot ---
plot = (
    ggplot(df, aes(x="play"))  # noqa: F405
    # Area fills — Imprint palette, theme-constant data colors
    + geom_ribbon(  # noqa: F405
        aes(ymin="baseline", ymax="above_50"),  # noqa: F405
        fill=HOME_COLOR,
        alpha=0.28,
    )
    + geom_ribbon(  # noqa: F405
        aes(ymin="below_50", ymax="baseline"),  # noqa: F405
        fill=AWAY_COLOR,
        alpha=0.28,
    )
    # Win probability line — theme-adaptive ink
    + geom_line(  # noqa: F405
        aes(y="win_prob"),  # noqa: F405
        color=INK,
        size=1.0,
        tooltips=layer_tooltips()  # noqa: F405
        .line("Play @play")
        .format("win_prob", ".0%")
        .line("Win prob: @win_prob"),
    )
    # 50% reference line
    + geom_hline(yintercept=0.5, color=INK_SOFT, size=0.7, linetype="dashed")  # noqa: F405
    # Quarter dividers
    + geom_vline(xintercept=30, color=INK_MUTED, size=0.5, linetype="dotted")  # noqa: F405
    + geom_vline(xintercept=60, color=INK_MUTED, size=0.5, linetype="dotted")  # noqa: F405
    + geom_vline(xintercept=90, color=INK_MUTED, size=0.5, linetype="dotted")  # noqa: F405
    # Key event markers
    + geom_point(  # noqa: F405
        data=key_events,
        mapping=aes(x="play", y="win_prob"),  # noqa: F405
        size=3.0,
        color=INK,
        fill=PAGE_BG,
        shape=21,
        stroke=1.5,
    )
    # Key event labels with elevated background
    + geom_label(  # noqa: F405
        data=key_events,
        mapping=aes(x="play", y="label_y", label="label"),  # noqa: F405
        size=4,
        color=INK,
        fill=ELEVATED_BG,
        alpha=0.92,
        label_padding=0.3,
        label_r=0.15,
        label_size=0.3,
    )
    # Scales
    + scale_y_continuous(  # noqa: F405
        breaks=[0.0, 0.25, 0.5, 0.75, 1.0], labels=["0%", "25%", "50%", "75%", "100%"]
    )
    + coord_cartesian(ylim=[0.0, 1.05])  # noqa: F405
    + scale_x_continuous(  # noqa: F405
        breaks=[0, 30, 60, 90, 120], labels=["Q1", "Q2", "Q3", "Q4", "End"]
    )
    + labs(  # noqa: F405
        x="Game Progress",
        y="Eagles Win Probability",
        title="line-win-probability · python · letsplot · anyplot.ai",
        subtitle="Eagles 27 – Cowboys 17  ·  Eagles recover from Q3 deficit for convincing finish",
    )
    # Canvas: 800×450 × scale=4 → 3200×1800 px (landscape)
    + ggsize(800, 450)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + anyplot_theme
)

# --- Save PNG + HTML ---
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
