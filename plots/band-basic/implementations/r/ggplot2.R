#' anyplot.ai
#' band-basic: Basic Band Plot
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-05-29

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens (Imprint palette)
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

IMPRINT_PALETTE <- c(
    "#009E73",  # 1 — brand green, first series
    "#C475FD", "#4467A3", "#BD8233",
    "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# Data — 60-month temperature forecast with widening 95% confidence interval
months    <- seq_len(60)
base_temp <- 13.5 + 0.03 * months + 7.5 * sin(2 * pi * (months - 3) / 12)
noise     <- rnorm(60, sd = 0.35)
y_center  <- base_temp + noise
band_half <- 1.0 + 0.018 * months  # forecast uncertainty widens over time
y_lower   <- y_center - band_half
y_upper   <- y_center + band_half

df <- data.frame(
    month    = months,
    y_center = y_center,
    y_lower  = y_lower,
    y_upper  = y_upper
)

# Plot
p <- ggplot(df, aes(x = month)) +
    geom_ribbon(
        aes(ymin = y_lower, ymax = y_upper),
        fill  = IMPRINT_PALETTE[1],
        alpha = 0.25,
        color = NA
    ) +
    geom_line(
        aes(y = y_center),
        color     = IMPRINT_PALETTE[1],
        linewidth = 1.0
    ) +
    scale_x_continuous(
        breaks = c(1, 13, 25, 37, 49),
        labels = paste0("Year ", 1:5)
    ) +
    labs(
        x     = "Forecast Horizon",
        y     = "Temperature (°C)",
        title = "band-basic · r · ggplot2 · anyplot.ai"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background   = element_rect(fill = PAGE_BG, color = NA),
        panel.grid.major.y = element_line(color = INK_SOFT, linewidth = 0.25),
        panel.grid.major.x = element_blank(),
        panel.grid.minor   = element_blank(),
        panel.border       = element_blank(),
        axis.title         = element_text(color = INK,      size = 10),
        axis.text          = element_text(color = INK_SOFT, size = 8),
        axis.line          = element_line(color = INK_SOFT, linewidth = 0.4),
        plot.title         = element_text(color = INK,      size = 12),
        plot.margin        = margin(16, 20, 12, 12)
    )

# Save
ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 8,
    height   = 4.5,
    units    = "in",
    dpi      = 400
)
