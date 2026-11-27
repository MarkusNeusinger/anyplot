#' anyplot.ai
#' band-basic: Basic Band Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-05-29

library(ggplot2)
library(ragg)

set.seed(42)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
GRID        <- alpha(INK, 0.15)

IMPRINT_PALETTE <- c(
    "#009E73",  # 1 — brand green
    "#C475FD", "#4467A3", "#BD8233",
    "#AE3030", "#2ABCCD", "#954477", "#99B314"
)

# Data — 60-month temperature forecast with widening 95% CI
months    <- seq_len(60)
base_temp <- 13.5 + 0.03 * months + 7.5 * sin(2 * pi * (months - 3) / 12)
noise     <- rnorm(60, sd = 0.35)
y_center  <- base_temp + noise
band_half <- 1.0 + 0.018 * months  # uncertainty grows with forecast horizon
y_lower   <- y_center - band_half
y_upper   <- y_center + band_half

df <- data.frame(
    month    = months,
    y_center = y_center,
    y_lower  = y_lower,
    y_upper  = y_upper
)

p <- ggplot(df, aes(x = month)) +
    geom_ribbon(
        aes(ymin = y_lower, ymax = y_upper, fill = "95% CI"),
        alpha = 0.4,
        color = NA
    ) +
    geom_line(
        aes(y = y_center, color = "Central Forecast"),
        linewidth = 1.2
    ) +
    scale_fill_manual(
        values = c("95% CI" = IMPRINT_PALETTE[1]),
        guide  = guide_legend(order = 1, override.aes = list(alpha = 0.5))
    ) +
    scale_color_manual(
        values = c("Central Forecast" = IMPRINT_PALETTE[2]),
        guide  = guide_legend(order = 2, override.aes = list(linewidth = 1.5))
    ) +
    scale_x_continuous(
        breaks = c(1, 13, 25, 37, 49),
        labels = paste0("Year ", 1:5)
    ) +
    labs(
        x        = "Forecast Horizon",
        y        = "Temperature (°C)",
        title    = "band-basic · r · ggplot2 · anyplot.ai",
        subtitle = "Seasonal temperature forecast with widening 95% confidence interval",
        fill     = NULL,
        color    = NULL
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background   = element_rect(fill = PAGE_BG, color = NA),
        panel.grid.major.y = element_line(color = GRID, linewidth = 0.3),
        panel.grid.major.x = element_blank(),
        panel.grid.minor   = element_blank(),
        panel.border       = element_blank(),
        axis.title         = element_text(color = INK,      size = 10),
        axis.text          = element_text(color = INK_SOFT, size = 8),
        axis.line          = element_line(color = INK_SOFT, linewidth = 0.4),
        plot.title         = element_text(color = INK,      size = 12),
        plot.subtitle      = element_text(color = INK_SOFT, size = 9,
                                          margin = margin(b = 8)),
        legend.position      = "top",
        legend.justification = "left",
        legend.background    = element_rect(fill = ELEVATED_BG, color = NA),
        legend.text          = element_text(color = INK_SOFT, size = 8),
        legend.margin        = margin(2, 4, 2, 4),
        legend.key.size      = unit(0.8, "lines"),
        legend.spacing.x     = unit(0.3, "cm"),
        plot.margin          = margin(16, 20, 12, 12)
    )

ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 8,
    height   = 4.5,
    units    = "in",
    dpi      = 400
)
