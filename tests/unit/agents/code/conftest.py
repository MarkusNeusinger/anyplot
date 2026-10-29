"""Shared fixtures for the code-handling tests: a catalogue-style source and the catalogue files."""

import textwrap
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
CODE_LIBRARIES = ("matplotlib", "seaborn", "plotnine", "altair", "pygal", "letsplot")
"""The libraries with a Python code profile (`normalise.SUPPORTED_LIBRARIES`), in the corpus order."""
CATALOGUE_FILES = [
    path
    for library in CODE_LIBRARIES
    for path in sorted(REPO_ROOT.glob(f"plots/*/implementations/python/{library}.py"))
]
R_CATALOGUE_FILES = sorted(REPO_ROOT.glob("plots/*/implementations/r/ggplot2.R"))
"""The ggplot2 catalogue files, which the R profile (`agents/anyplot/code/profiles/r/`) reads."""


def source(text: str) -> str:
    """Dedent a triple-quoted snippet and drop its leading newline."""
    return textwrap.dedent(text).lstrip("\n")


# A catalogue file in miniature: header, sys.path guard, theme block, palette, synthetic
# data, a literal limit, the catalogue title and a tight savefig at a 16:9 figure.
CATALOGUE = source('''
    """ anyplot.ai
    scatter-demo: Demo Scatter
    Library: matplotlib 3.11.2 | Python 3.13.13
    Quality: 90/100 | Updated: 2026-10-01
    """

    import os
    import sys


    # This file is named matplotlib.py; drop its directory from sys.path.
    _here = os.path.dirname(os.path.abspath(__file__))
    sys.path = [p for p in sys.path if os.path.abspath(p) != _here]

    import matplotlib.pyplot as plt
    import numpy as np


    # Theme tokens
    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
    IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

    np.random.seed(42)
    x = np.random.uniform(0, 10, 50)
    y = 2 * x + np.random.normal(0, 1, 50)

    fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
    ax.scatter(x, y, color=IMPRINT[0])
    ax.set_ylim(0, 25)
    ax.set_title("scatter-demo · python · matplotlib · anyplot.ai", color=INK)
    plt.savefig(f"plot-{THEME}.png", dpi=300, bbox_inches="tight", facecolor=PAGE_BG)
''')

# The same file after normalisation: header, guard and title gone, dpi 200, no bbox_inches.
CATALOGUE_NORMALISED = source("""
    import os


    import matplotlib.pyplot as plt
    import numpy as np


    # Theme tokens
    THEME = os.getenv("ANYPLOT_THEME", "light")
    PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
    INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
    IMPRINT = ["#009E73", "#C475FD", "#4467A3"]

    np.random.seed(42)
    x = np.random.uniform(0, 10, 50)
    y = 2 * x + np.random.normal(0, 1, 50)

    fig, ax = plt.subplots(figsize=(16, 9), facecolor=PAGE_BG)
    ax.scatter(x, y, color=IMPRINT[0])
    ax.set_ylim(0, 25)
    ax.set_title("", color=INK)
    plt.savefig(f"plot-{THEME}.png", dpi=200, facecolor=PAGE_BG)
""")

# A ggplot2 catalogue file in miniature: roxygen header, theme block, palette, column
# constants, the Data and Plot markers, synthetic data, the title and a 4800x2700 save.
R_CATALOGUE = source("""
    #' anyplot.ai
    #' scatter-demo: Demo Scatter
    #' Library: ggplot2 4.0.3 | R 4.6.1
    #' Quality: 90/100 | Updated: 2026-10-29

    library(ggplot2)
    library(ragg)

    # Theme tokens
    THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
    PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
    INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
    ALPHA    <- if (THEME == "light") 0.4 else 0.6
    IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                         "#AE3030", "#2ABCCD", "#954477", "#99B314")

    # Columns: set these to your table's column names
    SPEND   <- "Spend (k USD)"    # role: x
    REVENUE <- "Revenue (k USD)"  # role: y

    # Data: replace this block with your own table
    set.seed(42)
    df <- tibble::tibble(!!SPEND := runif(50, 5, 150), !!REVENUE := rnorm(50, 300, 40))

    # Plot: reads only df and the constants above
    p <- ggplot(df, aes(x = .data[[SPEND]], y = .data[[REVENUE]])) +
      geom_point(color = IMPRINT_PALETTE[1], alpha = ALPHA) +
      labs(title = "scatter-demo · r · ggplot2 · anyplot.ai", x = SPEND, y = REVENUE) +
      theme_minimal(base_size = 8) +
      theme(plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG))

    # Save
    ggsave(
      filename = sprintf("plot-%s.png", THEME),
      plot     = p,
      device   = ragg::agg_png,
      width    = 16,
      height   = 9,
      units    = "in",
      dpi      = 300
    )
""")

# The same file after normalisation: header and title gone, dpi 200.
R_CATALOGUE_NORMALISED = source("""
    library(ggplot2)
    library(ragg)

    # Theme tokens
    THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
    PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
    INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
    ALPHA    <- if (THEME == "light") 0.4 else 0.6
    IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                         "#AE3030", "#2ABCCD", "#954477", "#99B314")

    # Columns: set these to your table's column names
    SPEND   <- "Spend (k USD)"    # role: x
    REVENUE <- "Revenue (k USD)"  # role: y

    # Data: replace this block with your own table
    set.seed(42)
    df <- tibble::tibble(!!SPEND := runif(50, 5, 150), !!REVENUE := rnorm(50, 300, 40))

    # Plot: reads only df and the constants above
    p <- ggplot(df, aes(x = .data[[SPEND]], y = .data[[REVENUE]])) +
      geom_point(color = IMPRINT_PALETTE[1], alpha = ALPHA) +
      labs(title = "", x = SPEND, y = REVENUE) +
      theme_minimal(base_size = 8) +
      theme(plot.background = element_rect(fill = PAGE_BG, color = PAGE_BG))

    # Save
    ggsave(
      filename = sprintf("plot-%s.png", THEME),
      plot     = p,
      device   = ragg::agg_png,
      width    = 16,
      height   = 9,
      units    = "in",
      dpi      = 200
    )
""")
