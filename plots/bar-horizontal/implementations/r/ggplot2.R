#' anyplot.ai
#' bar-horizontal: Horizontal Bar Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 85/100 | Created: 2026-08-05

library(ggplot2)
library(dplyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")
BRAND <- IMPRINT_PALETTE[1]  # ALWAYS first series

# --- Data ---------------------------------------------------------------
# Survey: "What best describes your current work arrangement?"
df <- tibble::tibble(
  arrangement = c(
    "Fully remote",
    "Hybrid, 2-3 days in office",
    "Fully in-office",
    "Hybrid, 4 days in office",
    "Flexible, self-directed schedule",
    "Compressed four-day workweek",
    "Job-share arrangement"
  ),
  share_pct = c(34.5, 24.8, 18.3, 12.1, 6.4, 2.7, 1.2)
)

# --- Plot ---------------------------------------------------------------
plot_title <- "Preferred Work Arrangement Survey · bar-horizontal · r · ggplot2 · anyplot.ai"
title_n <- nchar(plot_title)
title_ratio <- if (title_n > 67) 67 / title_n else 1.0
title_fontsize <- max(8, round(12 * title_ratio))

p <- ggplot(df, aes(x = reorder(arrangement, share_pct), y = share_pct)) +
  geom_col(fill = BRAND, color = PAGE_BG, linewidth = 0.4, width = 0.7) +
  geom_text(
    aes(label = paste0(share_pct, "%")),
    hjust = -0.15, size = 3.2, color = INK
  ) +
  scale_y_continuous(expand = expansion(mult = c(0, 0.16))) +
  coord_flip(clip = "off") +
  labs(
    title = plot_title,
    x = NULL,
    y = "Share of Respondents (%)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_blank(),
    panel.grid.major.x = element_line(color = INK, linewidth = 0.2),
    panel.grid.minor   = element_blank(),
    axis.ticks         = element_blank(),
    axis.title.x       = element_text(color = INK, size = 10, margin = margin(t = 10)),
    axis.text.x        = element_text(color = INK_SOFT, size = 8),
    axis.text.y        = element_text(color = INK, size = 9),
    plot.title         = element_text(color = INK, size = title_fontsize, margin = margin(b = 14)),
    plot.margin        = margin(t = 16, r = 40, b = 12, l = 12)
  )

# --- Save -----------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
