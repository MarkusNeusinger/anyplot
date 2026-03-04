""" pyplots.ai
bar-diverging-likert: Likert Scale Diverging Bar Chart
Library: bokeh 3.8.2 | Python 3.14.3
Quality: 85/100 | Created: 2026-03-04
"""

import numpy as np
from bokeh.io import export_png
from bokeh.models import ColumnDataSource, HoverTool, LabelSet, Legend, LegendItem, Span
from bokeh.plotting import figure, save


# Data - Employee engagement survey (10 questions, 5-point Likert scale)
questions = [
    "I feel valued at work",
    "My manager provides feedback",
    "I have growth opportunities",
    "Work-life balance is good",
    "I understand company goals",
    "My team communicates well",
    "I have the tools I need",
    "I would recommend this company",
    "Meetings are productive",
    "My contributions are recognized",
]

strongly_disagree = [5, 12, 18, 8, 3, 6, 10, 15, 22, 7]
disagree = [10, 15, 20, 12, 8, 10, 14, 18, 25, 12]
neutral = [15, 18, 22, 15, 12, 14, 16, 17, 20, 15]
agree = [40, 30, 25, 35, 42, 38, 32, 28, 20, 36]
strongly_agree = [30, 25, 15, 30, 35, 32, 28, 22, 13, 30]

# Sort questions by net agreement for easy comparison
net_agreement = [
    (sa + a) - (sd + d) for sa, a, sd, d in zip(strongly_agree, agree, strongly_disagree, disagree, strict=True)
]
sorted_idx = np.argsort(net_agreement)
questions_sorted = [questions[i] for i in sorted_idx]
sd_sorted = [strongly_disagree[i] for i in sorted_idx]
d_sorted = [disagree[i] for i in sorted_idx]
n_sorted = [neutral[i] for i in sorted_idx]
a_sorted = [agree[i] for i in sorted_idx]
sa_sorted = [strongly_agree[i] for i in sorted_idx]

# Diverging color scheme: red-to-blue with muted neutral
likert_colors = {
    "Strongly Disagree": "#C44E52",
    "Disagree": "#E8927C",
    "Neutral": "#B0B0B0",
    "Agree": "#6BAED6",
    "Strongly Agree": "#306998",
}

label_text_colors = {
    "Strongly Disagree": "white",
    "Disagree": "#333333",
    "Neutral": "#333333",
    "Agree": "#333333",
    "Strongly Agree": "white",
}

# Plot
p = figure(
    width=4800,
    height=2700,
    y_range=questions_sorted,
    x_range=(-65, 90),
    title="bar-diverging-likert · bokeh · pyplots.ai",
    toolbar_location=None,
)

# Build diverging bars: neutral centered at 0, disagree extends left, agree extends right
likert_categories = ["Strongly Disagree", "Disagree", "Neutral", "Agree", "Strongly Agree"]
data_by_cat = {
    "Strongly Disagree": sd_sorted,
    "Disagree": d_sorted,
    "Neutral": n_sorted,
    "Agree": a_sorted,
    "Strongly Agree": sa_sorted,
}

legend_items = []
for cat_name in likert_categories:
    cat_values = data_by_cat[cat_name]
    lefts = []
    rights = []

    for q_idx in range(len(questions_sorted)):
        half_n = n_sorted[q_idx] / 2

        if cat_name == "Strongly Disagree":
            r = -(half_n + d_sorted[q_idx])
            lft = r - sd_sorted[q_idx]
        elif cat_name == "Disagree":
            r = -half_n
            lft = r - d_sorted[q_idx]
        elif cat_name == "Neutral":
            lft = -half_n
            r = half_n
        elif cat_name == "Agree":
            lft = half_n
            r = lft + a_sorted[q_idx]
        else:
            lft = half_n + a_sorted[q_idx]
            r = lft + sa_sorted[q_idx]

        lefts.append(lft)
        rights.append(r)

    source = ColumnDataSource(
        data={
            "question": questions_sorted,
            "left": lefts,
            "right": rights,
            "value": cat_values,
            "category": [cat_name] * len(questions_sorted),
        }
    )

    renderer = p.hbar(
        y="question",
        left="left",
        right="right",
        height=0.7,
        source=source,
        color=likert_colors[cat_name],
        line_color="white",
        line_width=1.5,
        alpha=0.9,
    )
    legend_items.append(LegendItem(label=cat_name, renderers=[renderer]))

    hover = HoverTool(
        renderers=[renderer], tooltips=[("Question", "@question"), ("Response", "@category"), ("Percentage", "@value%")]
    )
    p.add_tools(hover)

    # Percentage labels inside bar segments where space permits (≥10%)
    label_x = []
    label_y = []
    label_text = []
    for q_idx in range(len(questions_sorted)):
        if cat_values[q_idx] >= 10:
            label_x.append((lefts[q_idx] + rights[q_idx]) / 2)
            label_y.append(questions_sorted[q_idx])
            label_text.append(f"{cat_values[q_idx]}%")

    if label_text:
        label_source = ColumnDataSource(data={"x": label_x, "y": label_y, "text": label_text})
        labels = LabelSet(
            x="x",
            y="y",
            text="text",
            source=label_source,
            text_align="center",
            text_baseline="middle",
            text_font_size="14pt",
            text_color=label_text_colors[cat_name],
        )
        p.add_layout(labels)

# Center baseline
center_line = Span(location=0, dimension="height", line_color="#333333", line_width=2)
p.add_layout(center_line)

# Legend at bottom, horizontal
legend = Legend(
    items=legend_items,
    orientation="horizontal",
    label_text_font_size="18pt",
    spacing=25,
    padding=15,
    background_fill_alpha=0.0,
    border_line_alpha=0.0,
    glyph_height=25,
    glyph_width=25,
)
p.add_layout(legend, "below")

# Style
p.title.text_font_size = "28pt"
p.xaxis.axis_label = "\u2190 Disagree          Percentage          Agree \u2192"
p.xaxis.axis_label_text_font_size = "22pt"
p.yaxis.axis_label_text_font_size = "22pt"
p.xaxis.major_label_text_font_size = "18pt"
p.yaxis.major_label_text_font_size = "18pt"

# Grid
p.xgrid.grid_line_alpha = 0.2
p.xgrid.grid_line_dash = "dashed"
p.ygrid.grid_line_alpha = 0.0

# Clean up
p.outline_line_color = None
p.background_fill_color = "#ffffff"
p.xaxis.major_tick_line_color = None
p.yaxis.major_tick_line_color = None

# Save
export_png(p, filename="plot.png")
save(p, filename="plot.html", title="bar-diverging-likert \u00b7 bokeh \u00b7 pyplots.ai")
