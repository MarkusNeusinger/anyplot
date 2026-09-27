#' anyplot.ai
#' count-basic: Basic Count Plot
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Updated: 2026-09-27

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
# Faint gridline tone -- ggplot2 has no grid alpha, so blend INK ~15% into
# PAGE_BG instead of using full-opacity INK (which reads as bold as the axis).
GRID_COLOR  <- colorRampPalette(c(PAGE_BG, INK))(100)[15]

# --- Data ---------------------------------------------------------------
# Raw, uncounted survey responses -- ggplot2's geom_bar() tallies them itself.
support_levels <- c(
  "Strongly Agree", "Agree", "Neutral", "Disagree", "Strongly Disagree"
)
response_weights <- c(0.32, 0.30, 0.19, 0.13, 0.06)
survey_responses <- sample(
  support_levels,
  size = 480,
  replace = TRUE,
  prob = response_weights
)

df <- tibble::tibble(
  response = factor(survey_responses, levels = support_levels)
)

# Order categories by descending frequency for readability
freq_order <- df %>%
  count(response, name = "n") %>%
  arrange(desc(n)) %>%
  pull(response)
df$response <- factor(df$response, levels = freq_order)

# Highlight the leading category as a focal point; other bars get a solid,
# lightened tint of the same brand hue (opaque, not alpha) so the mix stays
# identical between light and dark renders -- alpha would blend with the
# theme background and make the tint shift between themes.
leader     <- freq_order[1]
bar_muted  <- colorRampPalette(c(IMPRINT_PALETTE[1], "#FFFFFF"))(100)[55]
bar_colors <- setNames(rep(bar_muted, length(freq_order)), freq_order)
bar_colors[leader] <- IMPRINT_PALETTE[1]

# --- Plot -----------------------------------------------------------------
title_text <- "count-basic · r · ggplot2 · anyplot.ai"

# Count + percentage labels are computed by stat_count() itself via
# after_stat(), not by a separate dplyr summary -- `group = 1` forces the
# stat to pool every bar into one group so `sum(after_stat(count))` is the
# grand total rather than each bar's own (always-1) share. This leans on
# ggplot2's stat/aes machinery beyond geom_bar()'s plain tally.
p <- ggplot(df, aes(x = response)) +
  geom_bar(aes(fill = response), width = 0.65) +
  geom_text(
    aes(
      y     = after_stat(count),
      group = 1,
      label = sprintf(
        "%d (%.0f%%)",
        after_stat(count),
        100 * after_stat(count) / sum(after_stat(count))
      )
    ),
    stat  = "count",
    vjust = -0.6,
    size  = 3.2,
    color = INK
  ) +
  scale_fill_manual(values = bar_colors, guide = "none") +
  scale_y_continuous(expand = expansion(mult = c(0, 0.12))) +
  labs(
    title = title_text,
    x = "Survey Response",
    y = "Count"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    panel.grid.major.y = element_line(color = GRID_COLOR, linewidth = 0.3),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    axis.ticks         = element_blank(),
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
