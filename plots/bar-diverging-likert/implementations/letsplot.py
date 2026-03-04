"""pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: letsplot 4.8.2 | Python 3.14.3
"""

import pandas as pd
from lets_plot import *


LetsPlot.setup_html()

# Data: Employee engagement survey (percentages, each row sums to 100)
survey = pd.DataFrame(
    {
        "question": [
            "My manager supports me",
            "I'd recommend this company",
            "I feel valued at work",
            "Goals are well-defined",
            "Work-life balance is good",
            "Resources are adequate",
            "I have growth opportunities",
            "Communication is clear",
        ],
        "Strongly Disagree": [3, 4, 5, 7, 8, 10, 12, 15],
        "Disagree": [8, 9, 10, 15, 18, 20, 22, 25],
        "Neutral": [12, 14, 15, 18, 15, 22, 20, 18],
        "Agree": [42, 40, 45, 38, 38, 32, 30, 28],
        "Strongly Agree": [35, 33, 25, 22, 21, 16, 16, 14],
    }
)

# Sort by net agreement (positive minus negative)
survey["net"] = survey["Agree"] + survey["Strongly Agree"] - survey["Disagree"] - survey["Strongly Disagree"]
survey = survey.sort_values("net").reset_index(drop=True)

# Build diverging bar segments centered on neutral midpoint
categories = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
# Warmer orange for Disagree improves luminance separation from Neutral gray
palette = ["#C0392B", "#D4763C", "#B0B0B0", "#7CB5D2", "#306998"]
text_color_map = {
    "Strongly Disagree": "#FFFFFF",
    "Disagree": "#FFFFFF",
    "Neutral": "#444444",
    "Agree": "#333333",
    "Strongly Agree": "#FFFFFF",
}

rows = []
bar_extents = {}
for idx, row in survey.iterrows():
    half_n = row["Neutral"] / 2
    segments = [
        (
            "Strongly Disagree",
            -(half_n + row["Disagree"] + row["Strongly Disagree"]),
            -(half_n + row["Disagree"]),
            row["Strongly Disagree"],
        ),
        ("Disagree", -(half_n + row["Disagree"]), -half_n, row["Disagree"]),
        ("Neutral", -half_n, half_n, row["Neutral"]),
        ("Agree", half_n, half_n + row["Agree"], row["Agree"]),
        ("Strongly Agree", half_n + row["Agree"], half_n + row["Agree"] + row["Strongly Agree"], row["Strongly Agree"]),
    ]
    bar_extents[idx] = half_n + row["Agree"] + row["Strongly Agree"]

    for cat, xmin, xmax, pct in segments:
        rows.append(
            {
                "y": idx,
                "ymin": idx - 0.38,
                "ymax": idx + 0.38,
                "xmin": xmin,
                "xmax": xmax,
                "category": cat,
                "pct": int(pct),
                "x_mid": (xmin + xmax) / 2,
                "label": f"{int(pct)}%" if pct >= 8 else "",
                "text_color": text_color_map[cat],
                "question": row["question"],
            }
        )

rect_df = pd.DataFrame(rows)
for col in ["category", "label", "text_color", "question"]:
    rect_df[col] = rect_df[col].astype(object)

label_df = rect_df[rect_df["label"] != ""].copy()

q_labels = survey["question"].tolist()
q_breaks = list(range(len(q_labels)))

# Storytelling: annotate top (highest agreement) and bottom (most divided)
top_idx = len(survey) - 1
bot_idx = 0
top_net = int(survey.iloc[top_idx]["net"])
bot_net = int(survey.iloc[bot_idx]["net"])

annot_top = pd.DataFrame({"x": [bar_extents[top_idx] + 2], "y": [top_idx], "label": [f"Net +{top_net}%"]})
annot_bot = pd.DataFrame({"x": [bar_extents[bot_idx] + 2], "y": [bot_idx], "label": [f"Net +{bot_net}%"]})

# Subtle highlight bands for visual focal emphasis
hl_top = pd.DataFrame({"xmin": [-55], "xmax": [100], "ymin": [top_idx - 0.48], "ymax": [top_idx + 0.48]})
hl_bot = pd.DataFrame({"xmin": [-55], "xmax": [100], "ymin": [bot_idx - 0.48], "ymax": [bot_idx + 0.48]})

# Plot
plot = (
    ggplot()
    # Highlight bands — visual emphasis on best/worst items
    + geom_rect(
        data=hl_top,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill="#E8F4FD",
        color="#E8F4FD",
        alpha=0.5,
    )
    + geom_rect(
        data=hl_bot,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax"),
        fill="#FDE8E0",
        color="#FDE8E0",
        alpha=0.5,
    )
    # Diverging bar segments with rich tooltips
    + geom_rect(
        data=rect_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="category"),
        tooltips=layer_tooltips().line("@question").line("@category: @{pct}%").format("pct", "d"),
    )
    # Percentage labels inside bars
    + geom_text(
        data=label_df, mapping=aes(x="x_mid", y="y", label="label", color="text_color"), size=12, fontface="bold"
    )
    # Center reference line
    + geom_vline(xintercept=0, color="#444444", size=0.8)
    # Net agreement annotations — storytelling focal points
    + geom_text(
        data=annot_top, mapping=aes(x="x", y="y", label="label"), color="#306998", size=11, fontface="bold", hjust=0
    )
    + geom_text(
        data=annot_bot, mapping=aes(x="x", y="y", label="label"), color="#C0392B", size=11, fontface="bold", hjust=0
    )
    # Scales
    + scale_fill_manual(values=palette, breaks=categories, name="Response")
    + scale_color_identity()
    + scale_y_continuous(breaks=q_breaks, labels=q_labels)
    + scale_x_continuous(breaks=[-40, -20, 0, 20, 40, 60, 80], labels=["40%", "20%", "0%", "20%", "40%", "60%", "80%"])
    + labs(
        title="bar-diverging-likert · letsplot · pyplots.ai",
        subtitle="Employee engagement survey — sorted by net agreement",
        x="Percentage of Responses",
        y="",
    )
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
        plot_subtitle=element_text(size=18, color="#666666"),
        axis_title_x=element_text(size=20),
        axis_title_y=element_blank(),
        axis_text_x=element_text(size=16),
        axis_text_y=element_text(size=16),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position="bottom",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
