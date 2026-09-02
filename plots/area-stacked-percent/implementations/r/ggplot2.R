#' anyplot.ai
#' area-stacked-percent: 100% Stacked Area Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 88/100 | Created: 2026-09-02

library(ggplot2)
library(dplyr)
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

# --- Direct end-of-line labels (replaces side legend) ------------------------
# Stacking order is reverse-factor (bottom-to-top: E, D, C, B, A), so cumulative
# shares must be computed in that same order to land labels on the right band.
last_quarter <- max(df$quarter)
label_df <- df %>%
  filter(quarter == last_quarter) %>%
  mutate(pct = revenue / sum(revenue)) %>%
  arrange(desc(vendor)) %>%
  mutate(ymax = cumsum(pct), ymin = ymax - pct, ymid = (ymin + ymax) / 2) %>%
  arrange(ymid)

# Nudge overlapping labels apart (thin bands, e.g. Vendor D/E, sit within a
# text-height of each other) so labels never collide, and keep the bottom
# label clear of the 0% axis line.
min_gap <- 0.06
label_df$ylabel <- label_df$ymid
label_df$ylabel[1] <- max(label_df$ylabel[1], 0.04)
for (i in 2:nrow(label_df)) {
  if (label_df$ylabel[i] - label_df$ylabel[i - 1] < min_gap) {
    label_df$ylabel[i] <- label_df$ylabel[i - 1] + min_gap
  }
}
label_df$label_x <- last_quarter + 60

# --- Plot -----------------------------------------------------------------
title_text <- "Cloud Market Share · area-stacked-percent · r · ggplot2 · anyplot.ai"
title_fontsize <- round(12 * min(1.0, 67 / nchar(title_text)))

p <- ggplot(df, aes(x = quarter, y = revenue, fill = vendor)) +
  geom_area(position = "fill", color = PAGE_BG, linewidth = 0.3) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  geom_segment(
    data = label_df,
    aes(x = last_quarter, xend = label_x, y = ymid, yend = ylabel, color = vendor),
    inherit.aes = FALSE, linewidth = 0.35
  ) +
  geom_text(
    data = label_df,
    aes(x = label_x, y = ylabel, label = vendor, color = vendor),
    inherit.aes = FALSE, hjust = 0, size = 3, fontface = "bold"
  ) +
  scale_color_manual(values = IMPRINT_PALETTE, guide = "none") +
  scale_y_continuous(labels = scales::percent_format(), expand = c(0, 0)) +
  scale_x_date(
    expand = expansion(mult = c(0, 0.02), add = c(0, 250)),
    date_labels = "%Y", date_breaks = "1 year"
  ) +
  coord_cartesian(clip = "off") +
  labs(
    title = title_text,
    x = "Quarter",
    y = "Market Share (%)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    legend.position     = "none",
    plot.background     = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background    = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.y  = element_line(color = INK, linewidth = 0.2),
    panel.grid.minor    = element_blank(),
    panel.grid.major.x  = element_blank(),
    axis.title          = element_text(color = INK, size = 10),
    axis.text           = element_text(color = INK_SOFT, size = 8),
    axis.ticks          = element_blank(),
    plot.title          = element_text(color = INK, size = title_fontsize),
    plot.margin         = margin(t = 5, r = 34, b = 5, l = 5)
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
