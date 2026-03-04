""" pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 84/100 | Created: 2026-03-04
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
palette = ["#C0392B", "#E8837C", "#BDBDBD", "#7CB5D2", "#306998"]
text_color_map = {
    "Strongly Disagree": "#FFFFFF",
    "Disagree": "#333333",
    "Neutral": "#555555",
    "Agree": "#333333",
    "Strongly Agree": "#FFFFFF",
}

rows = []
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
            }
        )

rect_df = pd.DataFrame(rows)

# Ensure string columns use object dtype (lets-plot compatibility)
for col in ["category", "label", "text_color"]:
    rect_df[col] = rect_df[col].astype(object)

# Label data (only segments wide enough to fit text)
label_df = rect_df[rect_df["label"] != ""].copy()

# Question labels for y-axis
q_labels = survey["question"].tolist()
q_breaks = list(range(len(q_labels)))

# Plot
plot = (
    ggplot()
    + geom_rect(
        data=rect_df,
        mapping=aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="category"),
        tooltips=layer_tooltips().line("@category").line("@{pct}%").format("pct", "d"),
    )
    + geom_text(
        data=label_df, mapping=aes(x="x_mid", y="y", label="label", color="text_color"), size=12, fontface="bold"
    )
    + geom_vline(xintercept=0, color="#444444", size=0.8)
    + scale_fill_manual(values=palette, breaks=categories, name="Response")
    + scale_color_identity()
    + scale_y_continuous(breaks=q_breaks, labels=q_labels)
    + scale_x_continuous(breaks=[-40, -20, 0, 20, 40, 60, 80], labels=["40%", "20%", "0%", "20%", "40%", "60%", "80%"])
    + labs(title="bar-diverging-likert · letsplot · pyplots.ai", x="Percentage of Responses", y="")
    + theme_minimal()
    + theme(
        plot_title=element_text(size=28, face="bold"),
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
