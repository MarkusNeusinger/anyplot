""" pyplots.ai
box-basic: Basic Box Plot
Library: letsplot 4.8.2 | Python 3.14
Quality: 90/100 | Created: 2025-12-23
"""

import numpy as np
import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    as_discrete,
    element_blank,
    element_line,
    element_rect,
    element_text,
    flavor_high_contrast_light,
    geom_boxplot,
    geom_hline,
    geom_text,
    ggplot,
    ggsave,
    ggsize,
    labs,
    layer_tooltips,
    scale_fill_manual,
    scale_y_continuous,
    theme,
)


LetsPlot.setup_html()

# Data
np.random.seed(42)
categories = ["Engineering", "Marketing", "Sales", "HR", "Finance"]
data = []
distributions = {
    "Engineering": (85000, 15000),
    "Marketing": (65000, 12000),
    "Sales": (70000, 20000),
    "HR": (55000, 10000),
    "Finance": (75000, 14000),
}

for cat in categories:
    mean, std = distributions[cat]
    n = np.random.randint(50, 100)
    values = np.random.normal(mean, std, n)
    outliers = np.random.choice([mean + 3.5 * std, mean - 2.5 * std], size=3)
    values = np.concatenate([values, outliers])
    data.extend([(cat, v) for v in values])

df = pd.DataFrame(data, columns=["department", "salary"])

# Compute medians for annotation labels
medians = df.groupby("department")["salary"].median().reset_index()
medians.columns = ["department", "median_salary"]
medians["label"] = medians["median_salary"].apply(lambda x: f"${x:,.0f}")

# Insight: compare highest vs lowest median departments
sorted_medians = medians.sort_values("median_salary")
low_dept = sorted_medians.iloc[0]
high_dept = sorted_medians.iloc[-1]
pct_diff = (high_dept["median_salary"] - low_dept["median_salary"]) / low_dept["median_salary"]
insight_text = f"+{pct_diff:.0%} vs. {low_dept['department']}"

# Overall mean for reference line
overall_mean = df["salary"].mean()

# Annotation dataframes
insight_df = pd.DataFrame(
    {
        "department": [high_dept["department"]],
        "y": [high_dept["median_salary"] + 22000],
        "lbl": [f"{high_dept['department'][:3]}. {insight_text}"],
    }
)
mean_label_df = pd.DataFrame(
    {"department": [high_dept["department"]], "y": [overall_mean + 3000], "lbl": [f"Avg: ${overall_mean:,.0f}"]}
)

# Plot
# Wong colorblind-safe palette (no two similar blues)
colors = ["#0072B2", "#E69F00", "#D55E00", "#009E73", "#CC79A7"]

plot = (
    ggplot(df, aes(x=as_discrete("department", order=1, order_by="..middle.."), y="salary", fill="department"))
    + geom_boxplot(
        alpha=0.85,
        size=1.2,
        outlier_size=5,
        outlier_shape=21,
        outlier_color="#333333",
        width=0.72,
        tooltips=layer_tooltips()
        .title("@department")
        .line("Median|$@{..middle..}")
        .line("Q1|$@{..lower..}")
        .line("Q3|$@{..upper..}")
        .line("Min|$@{..ymin..}")
        .line("Max|$@{..ymax..}"),
    )
    + scale_fill_manual(values=colors)
    # Median value labels above each box
    + geom_text(
        aes(x="department", y="median_salary", label="label"),
        data=medians,
        size=11,
        color="#333333",
        fontface="bold",
        nudge_y=5000,
        inherit_aes=False,
    )
    # Overall mean reference line
    + geom_hline(yintercept=overall_mean, color="#888888", size=0.8, linetype="dashed")
    + geom_text(
        aes(x="department", y="y", label="lbl"),
        data=mean_label_df,
        size=10,
        color="#666666",
        fontface="italic",
        hjust=0.5,
        inherit_aes=False,
    )
    # Key insight annotation
    + geom_text(
        aes(x="department", y="y", label="lbl"),
        data=insight_df,
        size=11,
        color="#1E4F72",
        fontface="bold italic",
        inherit_aes=False,
    )
    + scale_y_continuous(format="${,.0f}")
    + labs(
        x="Department",
        y="Annual Salary (USD)",
        title="box-basic \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="Salary distributions across five departments, ordered by median",
    )
    + flavor_high_contrast_light()
    + theme(
        plot_title=element_text(size=24, face="bold"),
        plot_subtitle=element_text(size=16, color="#555555"),
        axis_title=element_text(size=20),
        axis_text=element_text(size=16),
        axis_ticks=element_blank(),
        panel_grid_major_x=element_blank(),
        panel_grid_minor=element_blank(),
        panel_grid_major_y=element_line(color="#DDDDDD", size=0.5),
        legend_position="none",
        plot_background=element_rect(fill="white", color="white"),
        plot_margin=[10, 35, 10, 10],
    )
    + ggsize(1600, 900)
)

# Save
ggsave(plot, "plot.png", path=".", scale=3)
ggsave(plot, "plot.html", path=".")
