"""pyplots.ai
bar-tornado-sensitivity: Tornado Diagram for Sensitivity Analysis
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 89/100 | Created: 2026-03-07
"""

import pandas as pd


pd.options.future.infer_string = False
from lets_plot import *  # noqa: E402, F403
from lets_plot.export import ggsave as export_ggsave  # noqa: E402


LetsPlot.setup_html()  # noqa: F405

# Data - NPV sensitivity analysis for a capital investment project
base_npv = 12.5  # Base case NPV in $M

parameters = [
    "Discount Rate",
    "Revenue Growth",
    "Material Cost",
    "Labor Cost",
    "Sales Volume",
    "Tax Rate",
    "Salvage Value",
    "Operating Expenses",
    "Inflation Rate",
    "Capacity Utilization",
]

low_values = [16.8, 8.2, 14.9, 13.8, 9.1, 14.2, 11.6, 13.9, 13.4, 10.8]
high_values = [9.1, 17.3, 10.4, 11.0, 16.2, 10.9, 13.5, 11.2, 11.7, 14.1]

df = pd.DataFrame({"parameter": parameters, "low_value": low_values, "high_value": high_values})

# Sort by total range (widest bar at top)
df["total_range"] = abs(df["high_value"] - df["low_value"])
df = df.sort_values("total_range", ascending=True).reset_index(drop=True)

# Build long-form data: each parameter gets two bars (low side and high side)
rows = []
for _, row in df.iterrows():
    low_side = min(row["low_value"], row["high_value"])
    high_side = max(row["low_value"], row["high_value"])
    low_delta = low_side - base_npv
    high_delta = high_side - base_npv

    # Offset labels away from reference line
    low_nudge = low_delta - 0.3
    high_nudge = high_delta + 0.3

    rows.append(
        {
            "parameter": row["parameter"],
            "value": low_delta,
            "scenario": "Low Scenario",
            "label": f"{low_delta:+.1f}",
            "npv": f"${low_side:.1f}M",
            "label_x": low_nudge,
        }
    )
    rows.append(
        {
            "parameter": row["parameter"],
            "value": high_delta,
            "scenario": "High Scenario",
            "label": f"{high_delta:+.1f}",
            "npv": f"${high_side:.1f}M",
            "label_x": high_nudge,
        }
    )

plot_df = pd.DataFrame(rows)

# Preserve sorted order (ascending range = narrowest at bottom, widest at top)
param_order = df["parameter"].tolist()
plot_df["parameter"] = pd.Categorical(plot_df["parameter"], categories=param_order, ordered=True)

# Plot
plot = (
    ggplot(plot_df, aes(x="value", y="parameter", fill="scenario"))  # noqa: F405
    + geom_bar(  # noqa: F405
        stat="identity",
        width=0.7,
        alpha=0.92,
        position="identity",
        tooltips=layer_tooltips()  # noqa: F405
        .line("@parameter")
        .line("Scenario: @scenario")
        .line("NPV Impact: @label $M")
        .line("Resulting NPV: @npv")
        .format("@label", "{} $M"),
    )
    + geom_vline(xintercept=0, color="#2A2A2A", size=1.4, linetype="solid")  # noqa: F405
    + geom_text(  # noqa: F405
        aes(x="label_x", label="label"),  # noqa: F405
        position="identity",
        hjust=-0.05,
        size=15,
        color="#222222",
        fontface="bold",
        data=plot_df[plot_df["scenario"] == "High Scenario"],
    )
    + geom_text(  # noqa: F405
        aes(x="label_x", label="label"),  # noqa: F405
        position="identity",
        hjust=1.05,
        size=15,
        color="#222222",
        fontface="bold",
        data=plot_df[plot_df["scenario"] == "Low Scenario"],
    )
    + scale_fill_manual(  # noqa: F405
        values=["#306998", "#E8783A"], labels=["\u25c0 Low Scenario", "High Scenario \u25b6"]
    )
    + scale_x_continuous(  # noqa: F405
        expand=[0.15, 0], format="{.1f}", breaks=[-5, -4, -3, -2, -1, 0, 1, 2, 3, 4, 5]
    )
    + labs(  # noqa: F405
        x="Change in NPV ($M)",
        y="",
        title="NPV Sensitivity Analysis \u00b7 bar-tornado-sensitivity \u00b7 letsplot \u00b7 pyplots.ai",
        subtitle="One-at-a-time parameter variation from base case (NPV = $12.5M)",
        caption="Revenue Growth and Discount Rate account for over 50% of total NPV sensitivity",
        fill="",
    )
    + theme_minimal()  # noqa: F405
    + flavor_high_contrast_light()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, face="bold", hjust=0.5),  # noqa: F405
        plot_subtitle=element_text(size=16, hjust=0.5, color="#666666"),  # noqa: F405
        axis_title_x=element_text(size=20, margin=[10, 0, 0, 0]),  # noqa: F405
        axis_title_y=element_text(size=20),  # noqa: F405
        axis_text_x=element_text(size=16),  # noqa: F405
        axis_text_y=element_text(size=18),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_title=element_blank(),  # noqa: F405
        legend_position="top",
        panel_grid_major_y=element_blank(),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        panel_grid_major_x=element_line(color="#E0E0E0", size=0.5),  # noqa: F405
        plot_caption=element_text(size=14, color="#888888", face="italic", hjust=0.5),  # noqa: F405
        plot_margin=[20, 30, 20, 10],
    )
    + ggsize(1600, 900)  # noqa: F405
)

# Save at scale=3 for 4800x2700 output
export_ggsave(plot, filename="plot.png", path=".", scale=3)
export_ggsave(plot, filename="plot.html", path=".")
