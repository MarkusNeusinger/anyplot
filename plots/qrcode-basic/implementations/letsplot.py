"""pyplots.ai
qrcode-basic: Basic QR Code Generator
Library: letsplot 4.9.0 | Python 3.14.3
"""

import pandas as pd
import qrcode
from lets_plot import (
    LetsPlot,
    aes,
    coord_fixed,
    element_geom,
    element_rect,
    element_text,
    flavor_high_contrast_light,
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

# Generate QR code data
content = "https://pyplots.ai"
qr = qrcode.QRCode(version=1, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=1, border=4)
qr.add_data(content)
qr.make(fit=True)

# Convert QR matrix to dataframe — use fill values directly for scale_fill_identity
matrix = qr.get_matrix()
size = len(matrix)
rows = []
for y, row in enumerate(matrix):
    for x, cell in enumerate(row):
        rows.append({"x": x, "y": size - 1 - y, "fill": "#1A1A2E" if cell else "#FFFFFF"})
df = pd.DataFrame(rows)

# Plot using lets-plot distinctive features:
# - theme_void() for clean base with no axes/grid
# - flavor_high_contrast_light() for crisp white background
# - geom_raster() optimized for grid/matrix rendering
# - scale_fill_identity() maps fill column directly to colors
# - element_geom() for global geom styling
plot = (
    ggplot(df, aes(x="x", y="y", fill="fill"))
    + geom_raster()
    + scale_fill_identity()
    + coord_fixed()
    + labs(
        title="qrcode-basic · letsplot · pyplots.ai",
        subtitle="Encoded: https://pyplots.ai | Error Correction: M (15%)",
        caption="Version 2 · 25×25 modules · ECC Level M (15%)",
    )
    + ggsize(1200, 1200)
    + theme_void()
    + flavor_high_contrast_light()
    + theme(
        plot_title=element_text(size=26, hjust=0.5, face="bold"),
        plot_subtitle=element_text(size=16, hjust=0.5, color="#555555"),
        plot_caption=element_text(size=13, hjust=0.5, color="#888888"),
        plot_background=element_rect(fill="#FFFFFF", color="#FFFFFF"),
        panel_background=element_rect(fill="#FFFFFF", color="#FFFFFF"),
        geom=element_geom(pen="#1A1A2E", brush="#1A1A2E", paper="#FFFFFF"),
    )
)

# Save — square format (3600×3600 px)
ggsave(plot, "plot.png", path=".", scale=3)
