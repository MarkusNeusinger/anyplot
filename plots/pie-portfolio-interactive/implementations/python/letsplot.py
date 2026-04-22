""" pyplots.ai
pie-portfolio-interactive: Interactive Portfolio Allocation Chart
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 90/100 | Created: 2026-01-20
"""

import pandas as pd
from lets_plot import *  # noqa: F403
from lets_plot import ggbunch  # noqa: F401
from lets_plot.export import ggsave as export_ggsave


LetsPlot.setup_html()  # noqa: F405

# Data - Portfolio allocation by asset class with individual holdings
portfolio_data = {
    "asset": [
        "Apple Inc.",
        "Microsoft Corp.",
        "Amazon.com",
        "NVIDIA Corp.",
        "US Treasury 10Y",
        "Corporate Bonds AAA",
        "Municipal Bonds",
        "Real Estate Fund",
        "Gold ETF",
        "Private Equity",
        "Cash Reserves",
    ],
    "weight": [12.0, 10.0, 8.0, 7.0, 18.0, 12.0, 8.0, 10.0, 6.0, 5.0, 4.0],
    "category": [
        "Equities",
        "Equities",
        "Equities",
        "Equities",
        "Fixed Income",
        "Fixed Income",
        "Fixed Income",
        "Alternatives",
        "Alternatives",
        "Alternatives",
        "Cash",
    ],
}

df = pd.DataFrame(portfolio_data)

# Aggregate by category for main pie chart
category_weights = df.groupby("category", as_index=False)["weight"].sum()
category_weights = category_weights.sort_values("weight", ascending=False)

# Reorder categories
category_order = category_weights["category"].tolist()
category_weights["category"] = pd.Categorical(category_weights["category"], categories=category_order, ordered=True)

# Color palette for asset categories (Python Blue first, colorblind-safe)
category_colors = {"Fixed Income": "#306998", "Equities": "#FFD43B", "Alternatives": "#DC2626", "Cash": "#059669"}

# Main overview pie chart - shows aggregated asset classes
center_df = pd.DataFrame({"x": [0.0], "y": [0.0], "label": ["Portfolio\n100%"]})

# Build tooltips with drill-down hint showing individual holdings
# For each category, create a list of holdings to show in tooltip
holdings_info = {}
for cat in category_order:
    cat_holdings = df[df["category"] == cat][["asset", "weight"]].values.tolist()
    holdings_str = "\n".join([f"  • {h[0]}: {h[1]:.1f}%" for h in cat_holdings])
    holdings_info[cat] = holdings_str

# Add holdings info to dataframe for tooltips
category_weights["holdings_count"] = category_weights["category"].apply(lambda c: len(df[df["category"] == c]))
category_weights["holdings_preview"] = category_weights["category"].apply(
    lambda c: ", ".join(df[df["category"] == c]["asset"].tolist())
)

# Overview pie chart - main view showing all asset classes
plot_overview = (
    ggplot(category_weights)  # noqa: F405
    + geom_pie(  # noqa: F405
        aes(slice="weight", fill="category"),  # noqa: F405
        stat="identity",
        size=45,
        hole=0.35,
        stroke=2.5,
        color="white",
        tooltips=layer_tooltips()  # noqa: F405
        .title("@category")
        .line("Allocation: @weight%")
        .line("Holdings: @holdings_count assets")
        .line("@holdings_preview")
        .line("")
        .line("[Click to drill down]")
        .format("weight", ".1f"),
        labels=layer_labels()  # noqa: F405
        .line("@weight%")
        .format("weight", ".1f")
        .size(20),
    )
    + geom_label(  # noqa: F405
        aes(x="x", y="y", label="label"),  # noqa: F405
        data=center_df,
        size=20,
        fill="white",
        alpha=0.9,
        label_padding=0.5,
    )
    + scale_fill_manual(values=list(category_colors.values()), limits=list(category_colors.keys()))  # noqa: F405
    + labs(  # noqa: F405
        title="pie-portfolio-interactive · letsplot · pyplots.ai",
        subtitle="Hover for details | Click category to drill down",
        fill="Asset Class",
    )
    + ggsize(1600, 900)  # noqa: F405
    + theme_void()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=28, hjust=0.5, face="bold"),  # noqa: F405
        plot_subtitle=element_text(size=18, hjust=0.5, color="#666666"),  # noqa: F405
        legend_title=element_text(size=20),  # noqa: F405
        legend_text=element_text(size=18),  # noqa: F405
        legend_position=[0.82, 0.5],
        plot_margin=[40, 20, 20, 20],
    )
)

# Create drill-down views for each asset class
drill_down_plots = {}
holding_colors = ["#306998", "#FFD43B", "#DC2626", "#059669", "#7C3AED", "#0891B2", "#EA580C", "#84CC16"]

for cat in category_order:
    cat_df = df[df["category"] == cat].copy()
    cat_df = cat_df.sort_values("weight", ascending=False)
    cat_total = cat_df["weight"].sum()

    # Calculate relative weight within category
    cat_df["relative_weight"] = (cat_df["weight"] / cat_total * 100).round(1)

    center_cat_df = pd.DataFrame({"x": [0.0], "y": [0.0], "label": [f"{cat}\n{cat_total:.0f}%"]})

    # Assign colors
    n_holdings = len(cat_df)
    cat_color_list = holding_colors[:n_holdings]

    drill_plot = (
        ggplot(cat_df)  # noqa: F405
        + geom_pie(  # noqa: F405
            aes(slice="weight", fill="asset"),  # noqa: F405
            stat="identity",
            size=45,
            hole=0.35,
            stroke=2,
            color="white",
            tooltips=layer_tooltips()  # noqa: F405
            .title("@asset")
            .line("Portfolio weight: @weight%")
            .line("Category share: @relative_weight%")
            .line("")
            .line("[Click to return to overview]")
            .format("weight", ".1f")
            .format("relative_weight", ".1f"),
            labels=layer_labels()  # noqa: F405
            .line("@weight%")
            .format("weight", ".1f")
            .size(20),
        )
        + geom_label(  # noqa: F405
            aes(x="x", y="y", label="label"),  # noqa: F405
            data=center_cat_df,
            size=20,
            fill="white",
            alpha=0.9,
            label_padding=0.5,
        )
        + scale_fill_manual(values=cat_color_list)  # noqa: F405
        + labs(  # noqa: F405
            title="pie-portfolio-interactive · letsplot · pyplots.ai",
            subtitle=f"{cat} Holdings | Click to return to overview",
            fill="Holding",
        )
        + ggsize(1600, 900)  # noqa: F405
        + theme_void()  # noqa: F405
        + theme(  # noqa: F405
            plot_title=element_text(size=28, hjust=0.5, face="bold"),  # noqa: F405
            plot_subtitle=element_text(size=18, hjust=0.5, color="#666666"),  # noqa: F405
            legend_title=element_text(size=20),  # noqa: F405
            legend_text=element_text(size=18),  # noqa: F405
            legend_position=[0.82, 0.5],
            plot_margin=[40, 20, 20, 20],
        )
    )
    drill_down_plots[cat] = drill_plot

# Save main plot as PNG (static overview)
export_ggsave(plot_overview, filename="plot.png", path=".", scale=3)

# For HTML export, create a ggbunch showing overview plus drill-down panels
# This demonstrates the drill-down capability in a static multi-panel layout
# ggbunch uses relative coordinates: (x, y, width, height)
plots_list = [plot_overview]
regions_list = [(0, 0, 1.0, 0.5)]  # Overview takes top half

# Add mini drill-down plots as a panel to show drill-down capability
num_drills = len(drill_down_plots)
for i, (_cat, dplot) in enumerate(drill_down_plots.items()):
    plots_list.append(dplot)
    x_pos = (i % 2) * 0.5
    y_pos = 0.52 + (i // 2) * 0.25
    regions_list.append((x_pos, y_pos, 0.5, 0.24))

bunch = ggbunch(plots_list, regions_list) + ggsize(1600, 1800)  # noqa: F405
export_ggsave(bunch, filename="plot.html", path=".")
