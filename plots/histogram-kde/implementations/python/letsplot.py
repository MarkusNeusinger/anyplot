"""anyplot.ai
histogram-kde: Histogram with KDE Overlay
Library: letsplot 4.11.0 | Python 3.13.13
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd
from lets_plot import *  # noqa: F403


LetsPlot.setup_html()  # noqa: F405

# Theme tokens (Imprint palette — see prompts/default-style-guide.md)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
RULE = "rgba(26,26,23,0.15)" if THEME == "light" else "rgba(240,239,232,0.15)"
BRAND = "#009E73"  # Imprint palette position 1
AMBER = "#DDCC77"  # semantic warning anchor — tail-risk callout

# Data - simulated stock daily returns: a calm regime plus a stress regime
# (large drawdowns) and a short rally, producing visible left-skew and a
# heavy left tail that the KDE overlay reveals more clearly than raw bins.
np.random.seed(42)
returns = np.concatenate(
    [np.random.normal(0.001, 0.015, 400), np.random.normal(-0.02, 0.03, 50), np.random.normal(0.02, 0.025, 50)]
)
returns = returns * 100
mean_return = float(np.mean(returns))

df = pd.DataFrame({"Daily Return (%)": returns})

# Illustrative "stress day" cutoff: returns beyond this are the fat left tail
tail_cutoff = -5.0
tail_band = pd.DataFrame({"xmin": [returns.min() - 1], "xmax": [tail_cutoff]})

anyplot_theme = (
    theme_minimal()  # noqa: F405
    # custom overrides must be added after theme_minimal() — lets-plot resolves
    # theme layers in order, and an earlier fill gets clobbered by a later
    # base theme's own default otherwise
    + theme(  # noqa: F405
        plot_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),  # noqa: F405
        panel_grid_major=element_line(color=RULE, size=0.5),  # noqa: F405
        panel_grid_minor=element_blank(),  # noqa: F405
        axis_title=element_text(size=12, color=INK),  # noqa: F405
        axis_text=element_text(size=10, color=INK_SOFT),  # noqa: F405
        axis_line=element_line(color=INK_SOFT, size=0.5),  # noqa: F405
        plot_title=element_text(size=16, color=INK),  # noqa: F405
        legend_position="none",  # single series — legend would be redundant
    )
)

plot = (
    ggplot(df, aes(x="Daily Return (%)"))  # noqa: F405
    # Tail-risk callout band drawn first so bars/KDE sit on top of it
    + geom_rect(  # noqa: F405
        aes(xmin="xmin", xmax="xmax"),  # noqa: F405
        data=tail_band,
        ymin=0,
        ymax=0.28,
        fill=AMBER,
        color="rgba(221,204,119,0)",
        alpha=0.12,
        inherit_aes=False,
    )
    + geom_histogram(  # noqa: F405
        aes(y="..density.."),  # noqa: F405
        bins=35,
        fill=BRAND,
        alpha=0.55,
        color=BRAND,
        size=0.5,
        tooltips=layer_tooltips()  # noqa: F405
        .format("^x", ".1f")
        .format("..density..", ".3f")
        .line("Return|^x%")
        .line("Density|@..density..")
        .line("Count|@..count.."),
    )
    + geom_area(  # noqa: F405
        stat="density", color=INK_SOFT, fill=INK_SOFT, alpha=0.12, size=1.5
    )
    + geom_vline(  # noqa: F405
        xintercept=mean_return, color=INK, linetype="dashed", size=0.8
    )
    + geom_text(  # noqa: F405
        x=mean_return + 0.4, y=0.27, label=f"mean {mean_return:+.1f}%", color=INK, size=3.2, hjust=0
    )
    + geom_text(  # noqa: F405
        x=tail_cutoff - 0.3, y=0.27, label="stress tail", color=INK_SOFT, size=3.2, hjust=1
    )
    + labs(  # noqa: F405
        x="Daily Return (%)", y="Density", title="histogram-kde · letsplot · anyplot.ai"
    )
    + ggsize(800, 450)  # noqa: F405
    + anyplot_theme
)

# Save
output_dir = Path(__file__).parent
ggsave(plot, str(output_dir / f"plot-{THEME}.png"), scale=4)  # noqa: F405
ggsave(plot, str(output_dir / f"plot-{THEME}.html"))  # noqa: F405
