#' anyplot.ai
#' quiver-basic: Basic Quiver Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-07-24

library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint sequential cmap (single-polarity: wind speed magnitude)
IMPRINT_SEQ_LOW  <- "#009E73"
IMPRINT_SEQ_HIGH <- "#4467A3"

# --- Data: cyclonic wind field around a low-pressure eye ----------------
# Rotational flow (u = -y, v = x) modulated by a radial Gaussian decay so
# speed peaks in a ring around the calm eye and fades toward the outskirts.
grid <- expand_grid(
    x = seq(-8, 8, by = 1),
    y = seq(-4.5, 4.5, by = 1)
)

wind <- grid %>%
    mutate(
        radius = sqrt(x^2 + y^2),
        decay  = exp(-radius^2 / 40),
        u      = -y * decay,
        v      = x * decay,
        speed  = sqrt(u^2 + v^2)
    )

# Scale arrow length so the fastest vector spans ~80% of the 1-unit grid
# spacing, keeping neighbouring arrows from overlapping.
arrow_scale <- 0.8 / max(wind$speed)
wind <- wind %>%
    mutate(
        xend = x + u * arrow_scale,
        yend = y + v * arrow_scale
    )

# --- Plot ----------------------------------------------------------------
p <- ggplot(wind, aes(x = x, y = y, xend = xend, yend = yend, color = speed)) +
    geom_segment(
        linewidth = 0.7,
        arrow = arrow(length = unit(2, "mm"), type = "closed", angle = 20)
    ) +
    coord_fixed(ratio = 1, expand = TRUE) +
    scale_color_gradient(
        low = IMPRINT_SEQ_LOW, high = IMPRINT_SEQ_HIGH,
        name = "Wind speed (m/s)"
    ) +
    labs(
        x = "Distance east of eye (km)",
        y = "Distance north of eye (km)",
        title = "Cyclonic Wind Field · quiver-basic · r · ggplot2 · anyplot.ai"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background   = element_rect(fill = PAGE_BG, color = NA),
        panel.grid         = element_blank(),
        axis.title         = element_text(color = INK, size = 10),
        axis.text          = element_text(color = INK_SOFT, size = 8),
        axis.ticks         = element_blank(),
        plot.title         = element_text(color = INK, size = 12),
        legend.background  = element_rect(fill = ELEVATED_BG, color = NA),
        legend.text        = element_text(color = INK_SOFT, size = 8),
        legend.title       = element_text(color = INK, size = 10),
        legend.key         = element_rect(fill = PAGE_BG, color = NA),
        plot.margin        = margin(10, 14, 10, 10)
    )

# --- Save ------------------------------------------------------------------
ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 8,
    height   = 4.5,
    units    = "in",
    dpi      = 400
)
