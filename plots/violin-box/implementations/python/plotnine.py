""" anyplot.ai
violin-box: Violin Plot with Embedded Box Plot
Library: plotnine 0.15.4 | Python 3.13.13
Quality: 87/100 | Updated: 2026-05-12
"""

import importlib
import os
import sys


# Avoid importing from local directory
for path in list(sys.path):
    if "violin-box" in path or "implementations" in path:
        sys.path.remove(path)

np = importlib.import_module("numpy")
pd = importlib.import_module("pandas")
plotnine = importlib.import_module("plotnine")

THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
ELEVATED_BG = "#FFFDF6" if THEME == "light" else "#242420"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"

IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data
np.random.seed(42)
n_per_group = 80

data = pd.DataFrame(
    {
        "Value": np.concatenate(
            [
                np.random.normal(55, 10, n_per_group),
                np.random.exponential(8, n_per_group) + 35,
                np.concatenate([np.random.normal(40, 5, n_per_group // 2), np.random.normal(65, 5, n_per_group // 2)]),
                np.random.uniform(30, 70, n_per_group),
            ]
        ),
        "Group": ["Product A"] * n_per_group
        + ["Product B"] * n_per_group
        + ["Product C"] * n_per_group
        + ["Product D"] * n_per_group,
    }
)

# Plot
anyplot_theme = plotnine.theme(
    plot_background=plotnine.element_rect(fill=PAGE_BG, color=PAGE_BG),
    panel_background=plotnine.element_rect(fill=PAGE_BG, color=None),
    panel_grid_major=plotnine.element_line(color=INK, size=0.3, alpha=0.10),
    panel_grid_minor=plotnine.element_line(color=INK, size=0.2, alpha=0.05),
    panel_border=plotnine.element_blank(),
    axis_title=plotnine.element_text(color=INK, size=20, weight="bold"),
    axis_text=plotnine.element_text(color=INK_SOFT, size=16),
    axis_line_x=plotnine.element_line(color=INK_SOFT, size=0.7),
    axis_line_y=plotnine.element_line(color=INK_SOFT, size=0.7),
    axis_ticks=plotnine.element_line(color=INK_SOFT, size=0.4),
    axis_ticks_length=3,
    plot_title=plotnine.element_text(color=INK, size=24, weight="bold"),
    legend_background=plotnine.element_rect(fill=ELEVATED_BG, color=INK_SOFT),
    legend_text=plotnine.element_text(color=INK_SOFT, size=16),
    legend_title=plotnine.element_text(color=INK, size=16, weight="bold"),
    figure_size=(16, 9),
)

plot = (
    plotnine.ggplot(data, plotnine.aes(x="Group", y="Value", fill="Group"))
    + plotnine.geom_violin(alpha=0.65, color=INK_SOFT, size=0.7, width=0.85)
    + plotnine.geom_boxplot(
        width=0.25, alpha=0.9, color=INK_SOFT, fill=ELEVATED_BG, size=0.6, outlier_size=4, outlier_alpha=0.7
    )
    + plotnine.scale_fill_manual(values=IMPRINT, name="Product", guide=plotnine.guide_legend(nrow=1))
    + plotnine.labs(title="violin-box · plotnine · anyplot.ai", x="Product Category", y="Satisfaction Score (points)")
    + anyplot_theme
    + plotnine.theme(legend_position="top", legend_direction="horizontal")
)

# Save to script directory
script_dir = os.path.dirname(os.path.abspath(__file__))
output_path = os.path.join(script_dir, f"plot-{THEME}.png")
plot.save(output_path, dpi=300, verbose=False)
