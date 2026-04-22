""" pyplots.ai
ks-test-comparison: Kolmogorov-Smirnov Plot for Distribution Comparison
Library: letsplot 4.8.2 | Python 3.14.3
Quality: 96/100 | Created: 2026-02-17
"""

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403, F405
from scipy import stats


LetsPlot.setup_html()  # noqa: F405

# Data - Credit scoring: Good vs Bad customer score distributions
np.random.seed(42)
n_good = 500
n_bad = 300

good_scores = np.random.normal(loc=620, scale=80, size=n_good)
bad_scores = np.random.normal(loc=520, scale=90, size=n_bad)

# Clip to realistic credit score range
good_scores = np.clip(good_scores, 300, 850)
bad_scores = np.clip(bad_scores, 300, 850)

# Compute ECDFs
good_sorted = np.sort(good_scores)
good_ecdf = np.arange(1, len(good_sorted) + 1) / len(good_sorted)

bad_sorted = np.sort(bad_scores)
bad_ecdf = np.arange(1, len(bad_sorted) + 1) / len(bad_sorted)

# K-S test
ks_stat, p_value = stats.ks_2samp(good_scores, bad_scores)

# Find the point of maximum divergence
all_values = np.sort(np.concatenate([good_sorted, bad_sorted]))
good_ecdf_at_all = np.searchsorted(good_sorted, all_values, side="right") / len(good_sorted)
bad_ecdf_at_all = np.searchsorted(bad_sorted, all_values, side="right") / len(bad_sorted)
differences = np.abs(good_ecdf_at_all - bad_ecdf_at_all)
max_idx = np.argmax(differences)
max_x = all_values[max_idx]
max_good_y = good_ecdf_at_all[max_idx]
max_bad_y = bad_ecdf_at_all[max_idx]

# Build combined DataFrame for idiomatic ggplot usage with data argument
df_good = pd.DataFrame({"score": good_sorted, "ecdf": good_ecdf, "group": "Good Customers"})
df_bad = pd.DataFrame({"score": bad_sorted, "ecdf": bad_ecdf, "group": "Bad Customers"})
df_ecdf = pd.concat([df_good, df_bad], ignore_index=True)

# Shaded ribbon between the two ECDFs across entire overlapping range
ribbon_ymin = np.minimum(good_ecdf_at_all, bad_ecdf_at_all)
ribbon_ymax = np.maximum(good_ecdf_at_all, bad_ecdf_at_all)
df_ribbon = pd.DataFrame({"score": all_values, "ymin": ribbon_ymin, "ymax": ribbon_ymax})

# Vertical K-S segment at maximum divergence
df_ks_seg = pd.DataFrame(
    {"x": [max_x], "y": [min(max_good_y, max_bad_y)], "xend": [max_x], "yend": [max(max_good_y, max_bad_y)]}
)

# K-S statistic annotation arrow segment from label to max divergence midpoint
ks_mid_y = (max_good_y + max_bad_y) / 2
df_ks_arrow = pd.DataFrame({"x": [max_x + 40], "y": [ks_mid_y + 0.06], "xend": [max_x + 3], "yend": [ks_mid_y]})

# Label for K-S statistic
df_ks_label = pd.DataFrame({"score": [max_x + 42], "ecdf": [ks_mid_y + 0.07], "label": [f"D = {ks_stat:.3f}"]})

# Subtitle with lets-plot element_markdown for colored emphasis
subtitle_text = (
    f"K-S Statistic: **{ks_stat:.3f}** | "
    f"p-value: **{p_value:.2e}** "
    f"<span style='color:#888888'>(highly significant)</span>"
)

# Colors: blue + amber for colorblind-safe pairing (protanopia-friendly)
color_good = "#306998"
color_bad = "#D4820C"
color_ks = "#7B68AE"

# Plot using idiomatic lets-plot with data argument
plot = (
    ggplot(df_ecdf, aes(x="score", y="ecdf"))  # noqa: F405
    # Shaded region between CDFs showing full divergence area
    + geom_ribbon(  # noqa: F405
        data=df_ribbon,
        mapping=aes(x="score", ymin="ymin", ymax="ymax"),  # noqa: F405
        fill=color_ks,
        alpha=0.18,
        tooltips="none",  # noqa: F405
    )
    # Both ECDFs as step functions with tooltips
    + geom_step(  # noqa: F405
        mapping=aes(color="group"),  # noqa: F405
        size=2.2,
        tooltips=layer_tooltips()  # noqa: F405
        .line("@group")
        .line("Score|@score")
        .line("ECDF|@ecdf")
        .format("@score", ".0f")
        .format("@ecdf", ".3f"),
    )
    # Vertical K-S segment at maximum divergence using geom_segment
    + geom_segment(  # noqa: F405
        data=df_ks_seg,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
        color=color_ks,
        size=2.5,
        linetype="dashed",
        tooltips="none",  # noqa: F405
    )
    # Arrow from label to the K-S line midpoint
    + geom_segment(  # noqa: F405
        data=df_ks_arrow,
        mapping=aes(x="x", y="y", xend="xend", yend="yend"),  # noqa: F405
        color=color_ks,
        size=1.2,
        arrow=arrow(length=8, type="closed"),  # noqa: F405
        tooltips="none",  # noqa: F405
    )
    # K-S statistic label
    + geom_text(  # noqa: F405
        data=df_ks_label,
        mapping=aes(x="score", y="ecdf", label="label"),  # noqa: F405
        color="#5B4A8E",
        size=14,
        fontface="bold",
        tooltips="none",  # noqa: F405
    )
    + scale_color_manual(  # noqa: F405
        values={"Good Customers": color_good, "Bad Customers": color_bad}
    )
    + labs(  # noqa: F405
        x="Credit Score (points)",
        y="Cumulative Proportion",
        title="ks-test-comparison · letsplot · pyplots.ai",
        subtitle=subtitle_text,
        color="",
    )
    + coord_cartesian(xlim=[280, 860])  # noqa: F405
    + scale_x_continuous(breaks=list(range(300, 851, 100)))  # noqa: F405
    + scale_y_continuous(limits=[0, 1.05], breaks=[0, 0.25, 0.5, 0.75, 1.0])  # noqa: F405
    + ggsize(1600, 900)  # noqa: F405
    + theme_minimal()  # noqa: F405
    + flavor_high_contrast_light()  # noqa: F405
    + theme(  # noqa: F405
        plot_title=element_text(size=24, face="bold"),  # noqa: F405
        plot_subtitle=element_markdown(size=18, color="#555555"),  # noqa: F405
        axis_title=element_text(size=20, face="bold"),  # noqa: F405
        axis_text=element_text(size=16),  # noqa: F405
        legend_text=element_text(size=16),  # noqa: F405
        legend_position="top",
        panel_grid_major_x=element_blank(),  # noqa: F405
        panel_grid_major_y=element_line(color="#D8D8D8", size=0.3, linetype="dashed"),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_line=element_line(color="#BBBBBB", size=0.5),  # noqa: F405
        plot_margin=[40, 20, 20, 20],
    )
)

# Save PNG (scale 3x for 4800 x 2700 px) and HTML with interactive tooltips
ggsave(plot, "plot.png", path=".", scale=3)  # noqa: F405
ggsave(plot, "plot.html", path=".")  # noqa: F405
