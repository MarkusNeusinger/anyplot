"""anyplot.ai
swarm-basic: Basic Swarm Plot
Library: plotnine 0.15.7 | Python 3.13.13
Quality: 87/100 | Updated: 2026-07-26
"""

import sys


sys.path.pop(0)  # prevent this file from shadowing the installed plotnine package

import os

import numpy as np
import pandas as pd
from plotnine import (
    aes,
    element_blank,
    element_line,
    element_rect,
    element_text,
    geom_line,
    geom_point,
    ggplot,
    labs,
    scale_color_manual,
    scale_x_continuous,
    theme,
    theme_minimal,
)


THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
IMPRINT = ["#009E73", "#C475FD", "#4467A3", "#BD8233"]

# Data - Patient biomarker levels across treatment groups
np.random.seed(42)

treatment_groups = ["Placebo", "Low Dose", "Medium Dose", "High Dose"]

distributions = {
    "Placebo": {"mean": 45, "std": 12, "n": 50},
    "Low Dose": {"mean": 55, "std": 10, "n": 45},
    "Medium Dose": {"mean": 68, "std": 8, "n": 55},
    "High Dose": {"mean": 75, "std": 6, "n": 40},
}

data = []
for group, params in distributions.items():
    values = np.random.normal(params["mean"], params["std"], params["n"])
    values = np.clip(values, 20, 100)
    data.extend([(group, value) for value in values])

df = pd.DataFrame(data, columns=["treatment", "biomarker"])
df["treatment"] = pd.Categorical(df["treatment"], categories=treatment_groups, ordered=True)
df["x_num"] = df["treatment"].cat.codes.astype(float)


# Deterministic beeswarm packing: bin each group's values, then stack points
# alternating left/right of center within a bin so nearby values spread out
# instead of colliding (a random jitter would overlap in the denser groups).
def beeswarm_offsets(values, n_bins=22, spacing=0.05):
    bin_width = (values.max() - values.min()) / n_bins
    bin_seen = {}
    offsets = np.zeros(len(values))
    for idx in np.argsort(values):
        b = round(values[idx] / bin_width)
        count = bin_seen.get(b, 0)
        side = 1 if count % 2 == 0 else -1
        rank = (count // 2) + 1 if count > 0 else 0
        offsets[idx] = side * rank * spacing
        bin_seen[b] = count + 1
    return offsets


for group in treatment_groups:
    mask = df["treatment"] == group
    df.loc[mask, "x_num"] += beeswarm_offsets(df.loc[mask, "biomarker"].to_numpy())

medians_df = df.groupby("treatment", observed=True)["biomarker"].median().reset_index()
medians_df["x_num"] = medians_df["treatment"].cat.codes.astype(float)

# Plot
plot = (
    ggplot(df, aes(x="x_num", y="biomarker", color="treatment"))
    + geom_point(size=2.5, alpha=0.8)
    + geom_line(
        medians_df,
        aes(x="x_num", y="biomarker", group=1),
        linetype="dashed",
        color=INK_SOFT,
        size=1.0,
        inherit_aes=False,
    )
    + geom_point(medians_df, aes(x="x_num", y="biomarker"), size=6, shape="D", color=INK, inherit_aes=False)
    + scale_color_manual(values=IMPRINT)
    + scale_x_continuous(breaks=list(range(len(treatment_groups))), labels=treatment_groups)
    + labs(x="Treatment Group", y="Biomarker Level (ng/mL)", title="swarm-basic · plotnine · anyplot.ai")
    + theme_minimal()
    + theme(
        figure_size=(8, 4.5),
        text=element_text(size=7),
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
        panel_background=element_rect(fill=PAGE_BG),
        panel_border=element_blank(),
        panel_grid_major=element_line(color=INK, size=0.3, alpha=0.08),
        panel_grid_minor=element_line(color=INK, size=0.2, alpha=0.04),
        axis_ticks_major=element_blank(),
        axis_title=element_text(color=INK, size=10),
        axis_text=element_text(color=INK_SOFT, size=8),
        plot_title=element_text(color=INK, size=13),
        legend_position="none",
    )
)

# Save
plot.save(f"plot-{THEME}.png", dpi=400, width=8, height=4.5, units="in")
