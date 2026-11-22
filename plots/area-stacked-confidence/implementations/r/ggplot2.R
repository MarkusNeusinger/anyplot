#' anyplot.ai
#' area-stacked-confidence: Stacked Area Chart with Confidence Bands
#' Library: ggplot2 | R
#' Quality: 87/100 | Updated: 2026-11-22

library(ggplot2)
library(dplyr)
library(ragg)

# Theme tokens
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# Columns: set these to your table's column names
QUARTER <- "Quarter"            # role: x
SOURCE  <- "Source"             # role: group
OUTPUT  <- "Output (MWh)"       # role: value
HALF_CI <- "90% interval (+/- MWh)"  # role: band half-width

# Data: replace this block with your own table, for example df <- read.csv("output.csv", check.names = FALSE)
set.seed(42)
sources <- c("Solar", "Wind", "Hydro", "Battery")
n_q <- 20
q <- rep(1:n_q, times = length(sources))
src <- rep(sources, each = n_q)
trend <- c(Solar = 800, Wind = 1200, Hydro = 600, Battery = 200)[src] +
  c(Solar = 50, Wind = 30, Hydro = -10, Battery = 15)[src] * q
spread <- c(Solar = 50, Wind = 60, Hydro = 40, Battery = 30)[src] +
  c(Solar = 3, Wind = 4, Hydro = 2, Battery = 2)[src] * q
df <- tibble::tibble(
  !!QUARTER := q,
  !!SOURCE  := src,
  !!OUTPUT  := trend + rnorm(length(q), 0, c(Solar = 30, Wind = 40, Hydro = 25, Battery = 15)[src]),
  !!HALF_CI := spread
)

# Plot: reads only df and the constants above
df[[SOURCE]] <- factor(df[[SOURCE]], levels = unique(df[[SOURCE]]))
lev <- levels(df[[SOURCE]])

# Stack: first source sits on the zero baseline, later sources pile on top
stacked <- df |>
  mutate(.rank = as.integer(.data[[SOURCE]])) |>
  arrange(.data[[QUARTER]], .rank) |>
  group_by(.data[[QUARTER]]) |>
  mutate(
    .top    = cumsum(.data[[OUTPUT]]),
    .bottom = .top - .data[[OUTPUT]]
  ) |>
  ungroup()

band_label <- "Shaded band: 90% interval"
title_text <- "area-stacked-confidence · r · ggplot2 · anyplot.ai"

p <- ggplot(stacked, aes(x = .data[[QUARTER]], fill = .data[[SOURCE]], color = .data[[SOURCE]],
                         group = .data[[SOURCE]])) +
  geom_ribbon(aes(ymin = .bottom, ymax = .top), alpha = 0.55, color = NA) +
  geom_ribbon(aes(ymin = .top - .data[[HALF_CI]], ymax = .top + .data[[HALF_CI]]),
              alpha = 0.3, color = NA) +
  geom_line(aes(y = .top), linewidth = 0.9) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  scale_color_manual(values = IMPRINT_PALETTE) +
  scale_x_continuous(breaks = seq(1, max(df[[QUARTER]]), by = 2),
                     expand = expansion(mult = c(0.01, 0.01))) +
  scale_y_continuous(labels = scales::label_comma(),
                     expand = expansion(mult = c(0, 0.04))) +
  labs(title = title_text, x = QUARTER, y = OUTPUT, fill = SOURCE,
       caption = band_label) +
  guides(color = "none",
         fill = guide_legend(nrow = 1, override.aes = list(alpha = 0.7, color = NA))) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background   = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background  = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.major  = element_line(color = INK_SOFT, linewidth = 0.1),
    panel.grid.minor  = element_blank(),
    axis.title        = element_text(color = INK, size = 10),
    axis.text         = element_text(color = INK_SOFT, size = 8),
    plot.title        = element_text(color = INK, size = 12, face = "bold"),
    plot.caption      = element_text(color = INK_SOFT, size = 8, hjust = 0),
    legend.position   = "top",
    legend.justification = "left",
    legend.background = element_rect(fill = ELEVATED_BG, color = INK_SOFT, linewidth = 0.3),
    legend.text       = element_text(color = INK_SOFT, size = 8),
    legend.title      = element_text(color = INK, size = 10),
    plot.margin       = margin(12, 16, 10, 12)
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
