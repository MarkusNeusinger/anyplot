#' anyplot.ai
#' area-stacked-percent: 100% Stacked Area Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-09-02

library(ggplot2)
library(dplyr)
library(tidyr)
library(ragg)

set.seed(42)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233", "#AE3030")

# --- Data ---------------------------------------------------------------
# Cloud infrastructure market share by vendor, quarterly, 2020-2024
quarters <- seq(as.Date("2020-01-01"), as.Date("2024-10-01"), by = "quarter")
vendors <- c("Vendor A", "Vendor B", "Vendor C", "Vendor D", "Vendor E")
n_periods <- length(quarters)

trend <- rbind(
  cumsum(rnorm(n_periods, mean = 1.4, sd = 1.0)) + 30,
  cumsum(rnorm(n_periods, mean = 0.6, sd = 1.0)) + 22,
  cumsum(rnorm(n_periods, mean = -0.2, sd = 1.0)) + 20,
  cumsum(rnorm(n_periods, mean = -0.9, sd = 1.0)) + 16,
  cumsum(rnorm(n_periods, mean = -1.1, sd = 1.0)) + 12
)
trend[trend < 2] <- 2

df <- expand.grid(quarter = quarters, vendor = vendors) %>%
  arrange(vendor, quarter) %>%
  mutate(revenue = as.vector(t(trend)))

df$vendor <- factor(df$vendor, levels = vendors)

# --- Plot -----------------------------------------------------------------
title_text <- "Cloud Market Share · area-stacked-percent · r · ggplot2 · anyplot.ai"
title_fontsize <- round(12 * min(1.0, 67 / nchar(title_text)))

p <- ggplot(df, aes(x = quarter, y = revenue, fill = vendor)) +
  geom_area(position = "fill", color = PAGE_BG, linewidth = 0.3) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  scale_y_continuous(labels = scales::percent_format(), expand = c(0, 0)) +
  scale_x_date(expand = c(0, 0), date_labels = "%Y", date_breaks = "1 year") +
  labs(
    title = title_text,
    x = "Quarter",
    y = "Market Share",
    fill = "Vendor"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.2),
    panel.grid.minor   = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.ticks         = element_blank(),
    plot.title         = element_text(color = INK, size = title_fontsize),
    legend.title       = element_text(color = INK, size = 10),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.background  = element_blank(),
    legend.key         = element_blank()
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
