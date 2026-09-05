#' anyplot.ai
#' line-filled: Filled Line Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 79/100 | Created: 2026-09-05

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")
BRAND <- IMPRINT_PALETTE[1]

# --- Data ---------------------------------------------------------------
# Daily page views for a product landing page over one month, with a
# gradual ramp plus day-to-day noise and a weekend dip.
day <- 1:30
weekend_dip <- ifelse(day %% 7 %in% c(6, 0), -800, 0)
page_views <- 4200 + 60 * day + weekend_dip + rnorm(30, mean = 0, sd = 350)
page_views <- pmax(page_views, 0)

df <- tibble::tibble(day = day, page_views = page_views)

avg_views  <- mean(df$page_views)
peak_idx   <- which.max(df$page_views)
peak_day   <- df$day[peak_idx]
peak_views <- df$page_views[peak_idx]
peak_hjust <- if (peak_day > 25) 1 else if (peak_day < 5) 0 else 0.5

# --- Plot -----------------------------------------------------------------
title_text <- "line-filled · r · ggplot2 · anyplot.ai"

p <- ggplot(df, aes(x = day, y = page_views)) +
  geom_area(fill = BRAND, alpha = 0.35) +
  geom_hline(yintercept = avg_views, linetype = "dashed", color = INK_SOFT, linewidth = 0.4) +
  geom_line(color = BRAND, linewidth = 1.4) +
  geom_point(color = BRAND, size = 1.3, alpha = 0.85) +
  annotate("point", x = peak_day, y = peak_views, size = 3, color = BRAND) +
  annotate(
    "text", x = peak_day, y = peak_views, hjust = peak_hjust, vjust = -1,
    label = sprintf("Peak: %s views (day %d)", scales::label_comma()(round(peak_views)), peak_day),
    color = INK, size = 3
  ) +
  annotate(
    "text", x = 0.5, y = avg_views, hjust = 0, vjust = -0.6,
    label = sprintf("Monthly avg: %s", scales::label_comma()(round(avg_views))),
    color = INK_SOFT, size = 2.6
  ) +
  scale_x_continuous(breaks = seq(0, 30, by = 5)) +
  scale_y_continuous(labels = scales::label_comma(), limits = c(0, NA), expand = expansion(mult = c(0, 0.14))) +
  labs(title = title_text, x = "Day of Month", y = "Page Views") +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor  = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.25),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.ticks        = element_blank(),
    plot.title        = element_text(color = INK, size = 12)
  )

# --- Save -------------------------------------------------------------------
ggsave(
  filename = sprintf("plot-%s.png", THEME),
  plot     = p,
  device   = ragg::agg_png,
  width    = 8,
  height   = 4.5,
  units    = "in",
  dpi      = 400
)
