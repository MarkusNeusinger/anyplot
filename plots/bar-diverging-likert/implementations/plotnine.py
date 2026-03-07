""" pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 90/100 | Created: 2026-03-04
"""

import pandas as pd
from plotnine import (
    aes,
    annotate,
    element_blank,
    element_line,
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


# Data - Employee engagement survey (10 questions, 5-point Likert scale)
survey_data = pd.DataFrame(
    {
        "question": [
            "Career growth opportunities",
            "Work-life balance",
            "Team collaboration",
            "Management communication",
            "Compensation & benefits",
            "Training & development",
            "Workplace environment",
            "Recognition & rewards",
            "Job security",
            "Company culture",
        ],
        "strongly_disagree": [5, 8, 3, 12, 15, 10, 4, 14, 6, 7],
        "disagree": [10, 12, 7, 18, 20, 15, 8, 16, 10, 12],
        "neutral": [15, 18, 12, 20, 22, 18, 14, 18, 16, 15],
        "agree": [40, 35, 42, 30, 25, 32, 38, 30, 38, 36],
        "strongly_agree": [30, 27, 36, 20, 18, 25, 36, 22, 30, 30],
    }
)

# Sort by net agreement for visual hierarchy
survey_data["net_agreement"] = (
    survey_data["agree"] + survey_data["strongly_agree"] - survey_data["disagree"] - survey_data["strongly_disagree"]
)
survey_data = survey_data.sort_values("net_agreement", ascending=True).reset_index(drop=True)

# Wide-to-long transformation (tidy data for grammar of graphics)
response_cols = ["strongly_disagree", "disagree", "neutral", "agree", "strongly_agree"]
long_df = survey_data.melt(id_vars=["question"], value_vars=response_cols, var_name="response_key", value_name="pct")

# Ordered categorical for factor-level control (plotnine idiom)
name_map = {
    "strongly_disagree": "Strongly Disagree",
    "disagree": "Disagree",
    "neutral": "Neutral",
    "agree": "Agree",
    "strongly_agree": "Strongly Agree",
}
response_order = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
long_df["response"] = pd.Categorical(long_df["response_key"].map(name_map), categories=response_order, ordered=True)

# Vectorized diverging position computation via cumsum
# Centering offset = sum of negative side + half neutral
offset_map = survey_data.set_index("question")[["strongly_disagree", "disagree", "neutral"]].assign(
    offset=lambda d: d["strongly_disagree"] + d["disagree"] + d["neutral"] / 2
)["offset"]
long_df["offset"] = long_df["question"].map(offset_map)

# Stack segments left-to-right within each question
stack_pos = {col: i for i, col in enumerate(response_cols)}
long_df["stack_pos"] = long_df["response_key"].map(stack_pos)
long_df = long_df.sort_values(["question", "stack_pos"]).reset_index(drop=True)

# Cumulative sum gives right edge; subtract offset to center on neutral
long_df["xmax"] = long_df.groupby("question")["pct"].cumsum() - long_df["offset"]
long_df["xmin"] = long_df["xmax"] - long_df["pct"]

# Bar geometry
question_order = survey_data["question"].tolist()
y_map = {q: i for i, q in enumerate(question_order)}
long_df["y_pos"] = long_df["question"].map(y_map)
bar_height = 0.7
long_df["ymin"] = long_df["y_pos"] - bar_height / 2
long_df["ymax"] = long_df["y_pos"] + bar_height / 2
long_df["label_x"] = (long_df["xmin"] + long_df["xmax"]) / 2

# Percentage labels only for segments wide enough to read
long_df["label"] = long_df["pct"].apply(lambda v: f"{v}%" if v >= 10 else "")

# Diverging color palette: red → gray → blue
fill_colors = {
    "Strongly Disagree": "#C0392B",
    "Disagree": "#E78B84",
    "Neutral": "#BDC3C7",
    "Agree": "#7FB3D8",
    "Strongly Agree": "#2471A3",
}

# Contrast-aware label colors mapped via scale_color_manual (ggplot2 aesthetic idiom)
label_colors = {
    "Strongly Disagree": "white",
    "Disagree": "#5A1A14",
    "Neutral": "#444444",
    "Agree": "#133B5C",
    "Strongly Agree": "white",
}

# Grammar of graphics composition
plot = (
    ggplot(long_df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="response"))
    + geom_text(
        aes(x="label_x", y="y_pos", label="label", color="response"), size=11, fontweight="bold", show_legend=False
    )
    + geom_vline(xintercept=0, color="#333333", size=0.8)
    + scale_fill_manual(values=fill_colors, breaks=response_order)
    + scale_color_manual(values=label_colors, breaks=response_order)
    + scale_y_continuous(breaks=list(range(len(question_order))), labels=question_order)
    + scale_x_continuous(labels=lambda ticks: [f"{abs(int(v))}%" for v in ticks])
    + annotate("text", x=0, y=9.8, label="← Disagree    Agree →", size=11, color="#555555", fontstyle="italic")
    + labs(x="Percentage of Responses", y="", title="bar-diverging-likert · plotnine · pyplots.ai", fill="Response")
    + guides(fill=guide_legend(nrow=1))
    + theme_minimal()
    + theme(
        figure_size=(16, 9),
        text=element_text(size=14),
        axis_title=element_text(size=20),
        axis_text_y=element_text(size=16),
        axis_text_x=element_text(size=16),
        plot_title=element_text(size=24, ha="center"),
        legend_text=element_text(size=16),
        legend_title=element_text(size=16),
        legend_position="bottom",
        panel_grid_major_y=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_x=element_line(color="#E0E0E0", linetype="dashed", size=0.4),
    )
)

# Save
plot.save("plot.png", dpi=300, verbose=False)
