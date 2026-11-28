"""anyplot.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: letsplot 4.10.1 | Python 3.13.13
Quality: 90/100 | Updated: 2026-06-01
"""

import math
import os

import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()

# Theme tokens
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"
ON_BAR = "#F0EFE8"  # label color on the red and blue segments
ON_NEUTRAL = "#1A1A17" if THEME == "dark" else "#F0EFE8"  # the muted neutral grey is light in the dark theme

# Imprint palette (full list) and the diverging ends of imprint_div
IMPRINT_PALETTE = ["#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030", "#2ABCCD", "#954477", "#99B314"]
NEG_STRONG, POS_STRONG = "#AE3030", "#4467A3"


def blend(c0, c1, share):
    """Hex colour a share of the way from c0 to c1, blended linearly in sRGB."""
    return "#" + "".join(
        f"{round(int(c0[i : i + 2], 16) * (1 - share) + int(c1[i : i + 2], 16) * share):02X}" for i in (1, 3, 5)
    )


# Constants
# Likert levels, ordered from the disagree end to the agree end; the middle one is the neutral level
LEVEL_COLORS = [NEG_STRONG, blend(NEG_STRONG, INK_MUTED, 0.5), INK_MUTED, blend(INK_MUTED, POS_STRONG, 0.5), POS_STRONG]
LABEL_COLORS = [ON_BAR, ON_BAR, ON_NEUTRAL, ON_BAR, ON_BAR]
MIN_LABEL_PCT = 8  # narrower segments stay unlabeled
TICK_STEP = 20

# Column constants
QUESTION = "Question"  # role: question
STRONGLY_DISAGREE = "Strongly Disagree"  # role: strongly_disagree
DISAGREE = "Disagree"  # role: disagree
NEUTRAL = "Neutral"  # role: neutral
AGREE = "Agree"  # role: agree
STRONGLY_AGREE = "Strongly Agree"  # role: strongly_agree
LEVELS = [STRONGLY_DISAGREE, DISAGREE, NEUTRAL, AGREE, STRONGLY_AGREE]

# Data: employee engagement survey, percentages per question (each row sums to 100).
# Replace this block with your own table, for example df = pd.read_csv("survey.csv")
df = pd.DataFrame(
    {
        QUESTION: [
            "My manager supports me",
            "I'd recommend this company",
            "I feel valued at work",
            "Goals are well-defined",
            "Work-life balance is good",
            "Resources are adequate",
            "I have growth opportunities",
            "Communication is clear",
        ],
        STRONGLY_DISAGREE: [3, 4, 5, 7, 8, 10, 12, 15],
        DISAGREE: [8, 9, 10, 15, 18, 20, 22, 25],
        NEUTRAL: [12, 14, 15, 18, 15, 22, 20, 18],
        AGREE: [42, 40, 45, 38, 38, 32, 30, 28],
        STRONGLY_AGREE: [35, 33, 25, 22, 21, 16, 16, 14],
    }
)

# Plot
# Sort by net agreement (agree minus disagree), lowest at the bottom
net = df[AGREE] + df[STRONGLY_AGREE] - df[DISAGREE] - df[STRONGLY_DISAGREE]
df = df.assign(net=net).sort_values("net").reset_index(drop=True)
df = df.assign(row=df.index)

# Long table: one rectangle per question and level, centered on the middle of the neutral level
mid = LEVELS.index(NEUTRAL)
long = df.melt(id_vars=[QUESTION, "row"], value_vars=LEVELS, var_name="level", value_name="pct")
long["level_idx"] = long["level"].map(LEVELS.index)
long = long.sort_values(["row", "level_idx"]).reset_index(drop=True)
long["cum_end"] = long.groupby("row")["pct"].cumsum()
long["cum_start"] = long["cum_end"] - long["pct"]
neutral_start = long[long["level_idx"] == mid].set_index("row")["cum_start"]
neutral_pct = long[long["level_idx"] == mid].set_index("row")["pct"]
shift = long["row"].map(neutral_start + neutral_pct / 2)
long["xmin"] = long["cum_start"] - shift
long["xmax"] = long["cum_end"] - shift
long["ymin"] = long["row"] - 0.38
long["ymax"] = long["row"] + 0.38
long["x_mid"] = (long["xmin"] + long["xmax"]) / 2
long["label"] = long["pct"].map(lambda v: f"{v:g}%" if pd.notna(v) and v >= MIN_LABEL_PCT else "")
long["label_color"] = long["level_idx"].map(lambda k: LABEL_COLORS[k])
labeled = long[long["label"] != ""]

# Axis range and ticks from the data
row_right = long.groupby("row")["xmax"].max()
left_lim = math.ceil(-long["xmin"].min() / TICK_STEP) * TICK_STEP
right_lim = math.ceil((row_right.max() + 14) / TICK_STEP) * TICK_STEP
breaks = list(range(-left_lim, right_lim + 1, TICK_STEP))

# Net agreement annotations and highlight bands for the best and worst question
best, worst = df["row"].max(), df["row"].min()
notes = pd.DataFrame(
    {
        "x": [row_right[best] + 2, row_right[worst] + 2],
        "y": [best, worst],
        "label": [f"Net {int(df.loc[best, 'net']):+d}%", f"Net {int(df.loc[worst, 'net']):+d}%"],
        "color": [POS_STRONG, NEG_STRONG],
    }
)
bands = pd.DataFrame(
    {
        "xmin": [-left_lim] * 2,
        "xmax": [right_lim] * 2,
        "ymin": [best - 0.48, worst - 0.48],
        "ymax": [best + 0.48, worst + 0.48],
        "fill": ["#DFF0F8" if THEME == "light" else "#1B2229", "#F8E6E6" if THEME == "light" else "#291C1B"],
    }
)

title_str = "bar-diverging-likert · python · letsplot · anyplot.ai"

plot = (
    ggplot()
    # Highlight bands for the best and worst question
    + geom_rect(
        data=bands.iloc[[0]],
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill=bands["fill"][0],
        color=bands["fill"][0],
        alpha=0.7,
    )
    + geom_rect(
        data=bands.iloc[[1]],
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill=bands["fill"][1],
        color=bands["fill"][1],
        alpha=0.7,
    )
    # Center reference line, under the bars so it never strikes through a label
    + geom_vline(xintercept=0, color=INK_SOFT, size=0.8)
    # Diverging bar segments with interactive tooltips
    + geom_rect(
        data=long,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="level"),
        color=PAGE_BG,
        size=0.4,
        tooltips=layer_tooltips().line(f"@{{{QUESTION}}}").line("@level: @{pct}%"),
    )
    # Percentage labels inside segments
    + geom_text(
        data=labeled, mapping=aes(x="x_mid", y="row", label="label", color="label_color"), size=4.5, fontface="bold"
    )
    # Net agreement annotations
    + geom_text(data=notes, mapping=aes(x="x", y="y", label="label", color="color"), size=4, fontface="bold", hjust=0)
    + scale_fill_manual(values=LEVEL_COLORS, breaks=LEVELS, name="Response")
    + scale_color_identity()
    + scale_y_continuous(breaks=list(df["row"]), labels=list(df[QUESTION]))
    + scale_x_continuous(breaks=breaks, labels=[f"{abs(b)}%" for b in breaks], limits=[-left_lim, right_lim])
    + labs(
        title=title_str,
        subtitle="Employee engagement survey — sorted by net agreement",
        x="Percentage of Responses",
        y="",
    )
    + theme_minimal()
    + theme(
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_blank(),
        axis_line=element_blank(),
        axis_ticks=element_blank(),
        plot_title=element_text(size=16, face="bold", color=INK),
        plot_subtitle=element_text(size=13, color=INK_MUTED),
        axis_title_x=element_text(size=12, color=INK),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=10, color=INK_SOFT),
        axis_text_y=element_text(size=10, color=INK_SOFT),
        legend_title=element_text(size=12, color=INK),
        legend_text=element_text(size=10, color=INK_SOFT),
        legend_background=element_rect(fill=ELEVATED_BG, color=ELEVATED_BG),
        legend_position="bottom",
        panel_grid_major_x=element_line(color=INK_SOFT, size=0.2),
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(800, 450)
)

# Save
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
