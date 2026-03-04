"""pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: plotnine 0.15.3 | Python 3.14.3
Quality: 82/100 | Created: 2026-03-04
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
    scale_fill_manual,
    scale_x_continuous,
    scale_y_continuous,
    theme,
    theme_minimal,
)


# Data - Employee engagement survey (10 questions, 5-point Likert scale)
questions = [
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
]

survey_data = pd.DataFrame(
    {
        "question": questions,
        "strongly_disagree": [5, 8, 3, 12, 15, 10, 4, 14, 6, 7],
        "disagree": [10, 12, 7, 18, 20, 15, 8, 16, 10, 12],
        "neutral": [15, 18, 12, 20, 22, 18, 14, 18, 16, 15],
        "agree": [40, 35, 42, 30, 25, 32, 38, 30, 38, 36],
        "strongly_agree": [30, 27, 36, 20, 18, 25, 36, 22, 30, 30],
    }
)

# Sort by net agreement for easy comparison
survey_data["net_agreement"] = (
    survey_data["agree"] + survey_data["strongly_agree"] - survey_data["disagree"] - survey_data["strongly_disagree"]
)
survey_data = survey_data.sort_values("net_agreement", ascending=True).reset_index(drop=True)

# Build segments for diverging layout centered on neutral midpoint
segments = []
bar_height = 0.7

for idx, row in survey_data.iterrows():
    sd = row["strongly_disagree"]
    d = row["disagree"]
    n = row["neutral"]
    a = row["agree"]
    sa = row["strongly_agree"]
    q = row["question"]
    half_n = n / 2

    segments.append(
        {
            "question": q,
            "response": "Strongly Disagree",
            "xmin": -(sd + d + half_n),
            "xmax": -(d + half_n),
            "y_pos": idx,
            "value": sd,
        }
    )
    segments.append(
        {"question": q, "response": "Disagree", "xmin": -(d + half_n), "xmax": -half_n, "y_pos": idx, "value": d}
    )
    segments.append({"question": q, "response": "Neutral", "xmin": -half_n, "xmax": half_n, "y_pos": idx, "value": n})
    segments.append({"question": q, "response": "Agree", "xmin": half_n, "xmax": half_n + a, "y_pos": idx, "value": a})
    segments.append(
        {
            "question": q,
            "response": "Strongly Agree",
            "xmin": half_n + a,
            "xmax": half_n + a + sa,
            "y_pos": idx,
            "value": sa,
        }
    )

seg_df = pd.DataFrame(segments)
seg_df["label_x"] = (seg_df["xmin"] + seg_df["xmax"]) / 2
seg_df["ymin"] = seg_df["y_pos"] - bar_height / 2
seg_df["ymax"] = seg_df["y_pos"] + bar_height / 2

# Percentage labels only where segments are wide enough to read
seg_df["label"] = seg_df["value"].apply(lambda v: f"{v}%" if v >= 10 else "")

# Use dark text on lighter segments (Neutral, Agree, Disagree), white on darker ones
label_colors = {
    "Strongly Disagree": "white",
    "Disagree": "#5A1A14",
    "Neutral": "#444444",
    "Agree": "#133B5C",
    "Strongly Agree": "white",
}
seg_df["label_color"] = seg_df["response"].apply(lambda r: label_colors[r])

# Response ordering for legend
response_order = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
seg_df["response"] = pd.Categorical(seg_df["response"], categories=response_order, ordered=True)

# Diverging color palette: red → gray → blue
colors = {
    "Strongly Disagree": "#C0392B",
    "Disagree": "#E78B84",
    "Neutral": "#BDC3C7",
    "Agree": "#7FB3D8",
    "Strongly Agree": "#2471A3",
}

# Y-axis labels mapped to numeric positions
question_labels = survey_data["question"].tolist()
y_breaks = list(range(len(question_labels)))

# Plot
plot = (
    ggplot(seg_df)
    + geom_rect(aes(xmin="xmin", xmax="xmax", ymin="ymin", ymax="ymax", fill="response"))
    + geom_text(
        aes(x="label_x", y="y_pos", label="label"), color=seg_df["label_color"].tolist(), size=11, fontweight="bold"
    )
    + geom_vline(xintercept=0, color="#333333", size=0.8)
    + scale_fill_manual(values=colors, breaks=response_order)
    + scale_y_continuous(breaks=y_breaks, labels=question_labels)
    + scale_x_continuous(labels=lambda ticks: [f"{abs(int(v))}%" for v in ticks])
    + annotate("text", x=30, y=9.6, label="← Disagree    Agree →", size=10, color="#666666", fontstyle="italic")
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
