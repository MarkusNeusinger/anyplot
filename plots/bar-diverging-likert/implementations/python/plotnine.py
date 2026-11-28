"""anyplot.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: plotnine 0.15.4 | Python 3.13.13
Quality: pending | Updated: 2026-06-01
"""

import sys


# Remove the script directory from sys.path so the plotnine package isn't shadowed by this file
if sys.path and sys.path[0] in ("", "."):
    sys.path.pop(0)
sys.path = [p for p in sys.path if not p.endswith("/implementations/python")]

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_rect,
    geom_text,
    geom_vline,
    ggplot,
    guide_legend,
    guides,
    labs,
    scale_color_manual,
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Imprint palette: the diverging ends take the matte red and the blue, the neutral step a theme-adaptive grey
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
NEUTRAL_MID = "#6B6A63" if THEME == "light" else "#A8A79F"

# Constants
LABEL_MIN = 10  # segments narrower than this many percent stay unlabeled
BAR_HEIGHT = 0.7

# Columns: set these to your table's column names
QUESTION = "Question"  # role: question
STRONGLY_DISAGREE = "Strongly Disagree"  # role: strongly_disagree
DISAGREE = "Disagree"  # role: disagree
NEUTRAL = "Neutral"  # role: neutral
AGREE = "Agree"  # role: agree
STRONGLY_AGREE = "Strongly Agree"  # role: strongly_agree
RESPONSE = "Response"  # role: extra
XMIN = "xmin"  # role: extra
XMAX = "xmax"  # role: extra
YMIN = "ymin"  # role: extra
YMAX = "ymax"  # role: extra
YPOS = "ypos"  # role: extra
LABEL_X = "label_x"  # role: extra
LABEL = "label"  # role: extra

# Likert scale in order, from the left end of a bar to the right end
RESPONSES = [STRONGLY_DISAGREE, DISAGREE, NEUTRAL, AGREE, STRONGLY_AGREE]

# Data: employee engagement survey, percent of responses per question
# Replace this block with your own table, for example df = pd.read_csv("survey.csv")
df = pd.DataFrame(
    {
        QUESTION: [
            "Team collaboration",
            "Workplace environment",
            "Job security",
            "Company culture",
            "Career growth",
            "Training & development",
            "Work-life balance",
            "Management communication",
            "Recognition & rewards",
            "Compensation & benefits",
        ],
        STRONGLY_DISAGREE: [3, 4, 6, 7, 5, 10, 8, 12, 14, 20],
        DISAGREE: [7, 8, 10, 12, 10, 15, 12, 18, 16, 25],
        NEUTRAL: [12, 14, 16, 15, 15, 18, 18, 20, 18, 20],
        AGREE: [42, 38, 38, 36, 40, 32, 35, 30, 30, 22],
        STRONGLY_AGREE: [36, 36, 30, 30, 30, 25, 27, 20, 22, 13],
    }
)

# Plot: reads only df and the constants above
# Diverging palette: red end -> neutral grey -> blue end, interpolated piecewise in RGB
c_neg = np.array([int(IMPRINT_PALETTE[4][i : i + 2], 16) for i in (1, 3, 5)], dtype=float)
c_mid = np.array([int(NEUTRAL_MID[i : i + 2], 16) for i in (1, 3, 5)], dtype=float)
c_pos = np.array([int(IMPRINT_PALETTE[2][i : i + 2], 16) for i in (1, 3, 5)], dtype=float)
steps = np.linspace(0, 1, len(RESPONSES))
rgb = [(c_neg + t * 2 * (c_mid - c_neg)) if t <= 0.5 else (c_mid + (t * 2 - 1) * (c_pos - c_mid)) for t in steps]
levels = ["#" + "".join(f"{int(c):02x}" for c in np.clip(color, 0, 255)) for color in rgb]
fill_colors = dict(zip(RESPONSES, levels, strict=False))

# Label text: white on the dark fills, near-black on the lighter dark-theme mid fills
mid_label = "#1A1A17" if THEME == "dark" else "white"
label_colors = {level: ("white" if i in (0, len(RESPONSES) - 1) else mid_label) for i, level in enumerate(RESPONSES)}

# Sort ascending by net agreement, so the lowest sits at the bottom
net = df[AGREE] + df[STRONGLY_AGREE] - df[DISAGREE] - df[STRONGLY_DISAGREE]
table = df.loc[net.sort_values(kind="stable").index].reset_index(drop=True)
n_questions = len(table)

# Diverging position: the offset puts the middle of the neutral segment on zero
values = table[RESPONSES].to_numpy(dtype=float)
offset = np.nan_to_num(values[:, 0]) + np.nan_to_num(values[:, 1]) + np.nan_to_num(values[:, 2]) / 2
xmax = np.cumsum(np.nan_to_num(values), axis=1) - offset[:, None]
xmin = xmax - np.nan_to_num(values)
xmin[np.isnan(values)] = np.nan
xmax[np.isnan(values)] = np.nan

# Neutral labels sit slightly right of centre, clear of the x=0 reference line
label_x = (xmin + xmax) / 2
neutral_idx = RESPONSES.index(NEUTRAL)
label_x[:, neutral_idx] = xmin[:, neutral_idx] + values[:, neutral_idx] * 0.60

y_pos = np.repeat(np.arange(n_questions), len(RESPONSES))
long_df = pd.DataFrame(
    {
        QUESTION: np.repeat(table[QUESTION].to_numpy(), len(RESPONSES)),
        RESPONSE: pd.Categorical(np.tile(RESPONSES, n_questions), categories=RESPONSES, ordered=True),
        XMIN: xmin.ravel(),
        XMAX: xmax.ravel(),
        YPOS: y_pos,
        YMIN: y_pos - BAR_HEIGHT / 2,
        YMAX: y_pos + BAR_HEIGHT / 2,
        LABEL_X: label_x.ravel(),
        LABEL: [f"{v:.0f}%" if v >= LABEL_MIN else "" for v in values.ravel()],
    }
)

title = "bar-diverging-likert · python · plotnine · anyplot.ai"

plot = (
    ggplot(long_df)
    + geom_rect(aes(xmin=XMIN, xmax=XMAX, ymin=YMIN, ymax=YMAX, fill=RESPONSE))
    + geom_text(aes(x=LABEL_X, y=YPOS, label=LABEL, color=RESPONSE), size=2.8, fontweight="bold", show_legend=False)
    + geom_vline(xintercept=0, color=INK_SOFT, size=0.8)
    + scale_fill_manual(values=fill_colors, breaks=RESPONSES)
    + scale_color_manual(values=label_colors, breaks=RESPONSES)
    + scale_y_continuous(
        breaks=list(range(n_questions)), labels=table[QUESTION].tolist(), limits=(-0.5, n_questions + 0.2)
    )
    + scale_x_continuous(labels=lambda ticks: [f"{abs(int(v))}%" for v in ticks], expand=(0.02, 2))
    + annotate(
        "text",
        x=-1.5,
        y=n_questions - 0.1,
        label="← Disagree",
        size=4.5,
        color=INK_MUTED,
        fontstyle="italic",
        ha="right",
    )
    + annotate(
        "text", x=1.5, y=n_questions - 0.1, label="Agree →", size=4.5, color=INK_MUTED, fontstyle="italic", ha="left"
    )
    + labs(x="Percentage of Responses", y="", title=title, fill=RESPONSE)
    + guides(fill=guide_legend(nrow=1))
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color=INK, size=0.3, alpha=0.15),
        text=element_text(size=7),
        axis_title=element_text(size=10, color=INK),
        axis_text_y=element_text(size=8, color=INK_SOFT),
        axis_text_x=element_text(size=8, color=INK_SOFT),
        plot_title=element_text(size=12, color=INK, ha="center"),
        legend_text=element_text(size=8, color=INK_SOFT),
        legend_title=element_text(size=8, color=INK),
        legend_background=element_rect(fill=ELEVATED_BG, color="none"),
        legend_key=element_rect(fill=ELEVATED_BG, color="none"),
        legend_position="bottom",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in", verbose=False)
