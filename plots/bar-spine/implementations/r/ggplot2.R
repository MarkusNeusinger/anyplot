#' anyplot.ai
#' bar-spine: Spine Plot for Two-Variable Proportions
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 89/100 | Created: 2026-09-02

library(ggplot2)
library(dplyr)
library(scales)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c(
  "#009E73", # 1 - brand green (semantic: retained / good)
  "#AE3030"  # 5 - matte red   (semantic: churned / bad)
)
SEGMENT_TEXT <- "#FFFDF6" # warm near-white, legible on both fills

# --- Data -----------------------------------------------------------------
# SaaS customer base split by subscription tier (bar width = tier size) and
# retention outcome over the last billing cycle (segment height = share).
TIER_LEVELS   <- c("Basic", "Standard", "Premium", "Enterprise")
STATUS_LEVELS <- c("Retained", "Churned")

df_counts <- tibble::tibble(
  tier   = factor(rep(TIER_LEVELS, each = 2), levels = TIER_LEVELS),
  status = factor(rep(STATUS_LEVELS, times = 4), levels = STATUS_LEVELS),
  count  = c(816, 384, 738, 162, 460, 40, 288, 12)
)

tier_totals <- df_counts %>%
  group_by(tier) %>%
  summarise(total = sum(count), .groups = "drop") %>%
  arrange(tier) %>%
  mutate(
    width = total / sum(total),
    xmax  = cumsum(width),
    xmin  = xmax - width,
    xmid  = (xmin + xmax) / 2
  )

spine_df <- df_counts %>%
  left_join(tier_totals, by = "tier") %>%
  group_by(tier) %>%
  arrange(tier, status) %>%
  mutate(
    prop = count / total,
    ymax = cumsum(prop),
    ymin = ymax - prop,
    ymid = (ymin + ymax) / 2
  ) %>%
  ungroup()

# --- Plot -------------------------------------------------------------------
plot_title <- "Customer Retention by Subscription Tier · bar-spine · r · ggplot2 · anyplot.ai"
title_fontsize <- max(8, round(12 * 67 / nchar(plot_title)))

p <- ggplot(spine_df) +
  geom_rect(
    aes(xmin = xmin, xmax = xmax, ymin = ymin, ymax = ymax, fill = status),
    color = NA
  ) +
  geom_text(
    data = filter(spine_df, prop > 0.06),
    aes(x = xmid, y = ymid, label = percent(prop, accuracy = 1)),
    color = SEGMENT_TEXT, size = 3.2, fontface = "bold"
  ) +
  scale_fill_manual(
    values = c(Retained = IMPRINT_PALETTE[1], Churned = IMPRINT_PALETTE[2]),
    name = "Status"
  ) +
  scale_x_continuous(
    breaks = tier_totals$xmid, labels = tier_totals$tier,
    expand = c(0, 0)
  ) +
  scale_y_continuous(
    labels = percent_format(accuracy = 1),
    expand = expansion(mult = c(0, 0.02))
  ) +
  labs(
    title = plot_title,
    x = "Subscription Tier (bar width ∝ customer base)",
    y = "Share of Customers"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.3),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    axis.ticks         = element_blank(),
    plot.title         = element_text(color = INK, size = title_fontsize, face = "bold"),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 10)
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
