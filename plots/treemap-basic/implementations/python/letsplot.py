""" pyplots.ai
treemap-basic: Basic Treemap
Library: letsplot 4.8.2 | Python 3.13.11
Quality: 91/100 | Created: 2025-12-24
"""

import pandas as pd
from lets_plot import (
    LetsPlot,
    aes,
    element_blank,
    element_text,
    geom_rect,
    geom_text,
    ggplot,
    ggsize,
    labs,
    scale_fill_manual,
    theme,
    theme_void,
)
from lets_plot.export import ggsave


LetsPlot.setup_html()

# Data - Budget allocation by department (realistic corporate budget scenario)
data = {
    "category": ["Engineering", "Marketing", "Sales", "Operations", "HR", "Finance", "R&D", "Legal"],
    "value": [32, 22, 18, 12, 7, 5, 3, 1],
}

df_data = pd.DataFrame(data)
df_data = df_data.sort_values("value", ascending=False).reset_index(drop=True)


# Squarify algorithm for treemap layout
def squarify(values, x, y, width, height):
    """Compute treemap rectangles using squarify algorithm."""
    if len(values) == 0:
        return []

    total = sum(values)
    if total == 0:
        return []

    rects = []
    remaining_values = list(values)
    remaining_x, remaining_y = x, y
    remaining_w, remaining_h = width, height

    while remaining_values:
        # Determine layout direction based on aspect ratio
        if remaining_w >= remaining_h:
            # Lay out horizontally
            row_values = []
            row_sum = 0
            best_ratio = float("inf")

            for v in remaining_values:
                test_values = row_values + [v]
                test_sum = row_sum + v
                row_width = (test_sum / total) * width if total > 0 else 0

                if row_width > 0:
                    worst_ratio = 0
                    for rv in test_values:
                        rect_height = (rv / test_sum) * remaining_h if test_sum > 0 else 0
                        ratio = (
                            max(row_width / rect_height, rect_height / row_width) if rect_height > 0 else float("inf")
                        )
                        worst_ratio = max(worst_ratio, ratio)

                    if worst_ratio <= best_ratio:
                        best_ratio = worst_ratio
                        row_values = test_values
                        row_sum = test_sum
                    else:
                        break
                else:
                    row_values = test_values
                    row_sum = test_sum

            # Place rectangles in this row
            row_width = (row_sum / total) * width if total > 0 else 0
            current_y = remaining_y
            for rv in row_values:
                rect_height = (rv / row_sum) * remaining_h if row_sum > 0 else 0
                rects.append((remaining_x, current_y, row_width, rect_height))
                current_y += rect_height

            remaining_x += row_width
            remaining_w -= row_width
            remaining_values = remaining_values[len(row_values) :]
        else:
            # Lay out vertically
            col_values = []
            col_sum = 0
            best_ratio = float("inf")

            for v in remaining_values:
                test_values = col_values + [v]
                test_sum = col_sum + v
                col_height = (test_sum / total) * height if total > 0 else 0

                if col_height > 0:
                    worst_ratio = 0
                    for cv in test_values:
                        rect_width = (cv / test_sum) * remaining_w if test_sum > 0 else 0
                        ratio = (
                            max(col_height / rect_width, rect_width / col_height) if rect_width > 0 else float("inf")
                        )
                        worst_ratio = max(worst_ratio, ratio)

                    if worst_ratio <= best_ratio:
                        best_ratio = worst_ratio
                        col_values = test_values
                        col_sum = test_sum
                    else:
                        break
                else:
                    col_values = test_values
                    col_sum = test_sum

            # Place rectangles in this column
            col_height = (col_sum / total) * height if total > 0 else 0
            current_x = remaining_x
            for cv in col_values:
                rect_width = (cv / col_sum) * remaining_w if col_sum > 0 else 0
                rects.append((current_x, remaining_y, rect_width, col_height))
                current_x += rect_width

            remaining_y += col_height
            remaining_h -= col_height
            remaining_values = remaining_values[len(col_values) :]

    return rects


# Compute treemap layout
rects = squarify(df_data["value"].tolist(), 0, 0, 100, 100)

# Build rectangle dataframe
rect_df = pd.DataFrame(
    {
        "xmin": [r[0] for r in rects],
        "ymin": [r[1] for r in rects],
        "xmax": [r[0] + r[2] for r in rects],
        "ymax": [r[1] + r[3] for r in rects],
        "category": df_data["category"].tolist(),
        "value": df_data["value"].tolist(),
    }
)

# Calculate label positions (center of each rectangle)
rect_df["label_x"] = (rect_df["xmin"] + rect_df["xmax"]) / 2
rect_df["label_y"] = (rect_df["ymin"] + rect_df["ymax"]) / 2

# Calculate rectangle dimensions for label visibility
rect_df["width"] = rect_df["xmax"] - rect_df["xmin"]
rect_df["height"] = rect_df["ymax"] - rect_df["ymin"]

# Create labels - show percentage for larger rectangles, omit for smaller ones
total_value = df_data["value"].sum()


def make_label(row):
    w, h = row["width"], row["height"]
    pct = row["value"] / total_value * 100
    # Large rectangles: full label with name and percentage
    if w > 18 and h > 18:
        return f"{row['category']}\n{pct:.0f}%"
    # Medium rectangles: just percentage
    elif w > 8 and h > 8:
        return f"{pct:.0f}%"
    # Small rectangles: no label (visible in legend)
    return ""


rect_df["label"] = rect_df.apply(make_label, axis=1)

# Colors - Python palette primary, extended with colorblind-safe colors
colors = ["#306998", "#FFD43B", "#4CAF50", "#FF7043", "#AB47BC", "#26A69A", "#7E57C2", "#5C6BC0"]

# Plot
plot = (
    ggplot(rect_df)
    + geom_rect(
        aes(xmin="xmin", ymin="ymin", xmax="xmax", ymax="ymax", fill="category"), color="white", size=2.5, alpha=0.92
    )
    + geom_text(aes(x="label_x", y="label_y", label="label"), size=14, color="white", fontface="bold")
    + scale_fill_manual(values=colors)
    + labs(title="Budget Allocation · treemap-basic · letsplot · pyplots.ai", fill="Department")
    + theme_void()
    + theme(
        plot_title=element_text(size=24, hjust=0.5),
        legend_title=element_text(size=18),
        legend_text=element_text(size=16),
        legend_position=[0.85, 0.5],
        axis_title=element_blank(),
        axis_text=element_blank(),
    )
    + ggsize(1600, 900)
)

# Save PNG (scale=3 gives 4800x2700)
ggsave(plot, "plot.png", path=".", scale=3)

# Save HTML for interactivity
ggsave(plot, "plot.html", path=".")
