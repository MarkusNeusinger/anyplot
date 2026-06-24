""" anyplot.ai
qrcode-basic: Basic QR Code Generator
Library: letsplot 4.10.1 | Python 3.13.14
Quality: 86/100 | Updated: 2026-06-24
"""

import os

import pandas as pd
import qrcode
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_rect,
    element_text,
    geom_raster,
    ggplot,
    ggsave,
    ggsize,
    labs,
    scale_fill_identity,
    theme,
    theme_void,
)


LetsPlot.setup_html()

# Theme-adaptive chrome tokens (Imprint palette)
THEME = os.getenv("ANYPLOT_THEME", "light")
PAGE_BG = "#FAF8F1" if THEME == "light" else "#1A1A17"
INK = "#1A1A17" if THEME == "light" else "#F0EFE8"
INK_SOFT = "#4A4A44" if THEME == "light" else "#B8B7B0"
INK_MUTED = "#6B6A63" if THEME == "light" else "#A8A79F"

# Generate QR code data
content = "https://pyplots.ai"
qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=4)
qr.add_data(content)
qr.make(fit=True)

# Convert QR matrix to dataframe — fill column used directly by scale_fill_identity
matrix = qr.get_matrix()
size = len(matrix)
rows = []
for y, row in enumerate(matrix):
    for x, cell in enumerate(row):
        rows.append({"x": x, "y": size - 1 - y, "fill": INK if cell else PAGE_BG})
df = pd.DataFrame(rows)

# Title length: 46 chars — shorter than 67-char baseline, use default 16px
title = "qrcode-basic · python · letsplot · anyplot.ai"

# Plot — square canvas: ggsize(600, 600) × scale=4 → 2400×2400 px (hard rule)
plot = (
    ggplot(df, aes(x="x", y="y", fill="fill"))
    + geom_raster()
    + scale_fill_identity()
    + coord_fixed()
    + labs(
        title=title,
        subtitle=f"Encoded: {content}  |  Error Correction: M (15%)",
        caption=f"Version {qr.version}  ·  {size}×{size} modules  ·  ECC Level M (15%)",
    )
    + ggsize(600, 600)
    + theme_void()
    + theme(
        plot_title=element_text(size=16, hjust=0.5, face="bold", color=INK),
        plot_subtitle=element_text(size=10, hjust=0.5, color=INK_SOFT),
        plot_caption=element_text(size=8, hjust=0.5, color=INK_MUTED),
        plot_background=element_rect(fill=PAGE_BG, color="#009E73", size=3),
        panel_background=element_rect(fill=PAGE_BG, color=PAGE_BG),
    )
)

# Save — square 2400×2400 px (PNG + HTML for interactive library)
ggsave(plot, f"plot-{THEME}.png", path=".", scale=4)
ggsave(plot, f"plot-{THEME}.html", path=".")
