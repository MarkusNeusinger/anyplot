#' anyplot.ai
#' sankey-basic: Basic Sankey Diagram
#' Library: ggplot2 | R 4.4
#' Quality: pending | Created: 2026-07-25

library(ggplot2)
library(dplyr)
library(tibble)
library(ragg)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME    <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG  <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK      <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data: national energy supply (PJ/year) by source and end-use sector -
flows <- tibble::tribble(
  ~source,   ~target,        ~value,
  "Coal",    "Industrial",   220,
  "Coal",    "Commercial",   90,
  "Coal",    "Residential",  40,
  "Coal",    "Transport",    30,
  "Gas",     "Residential",  140,
  "Gas",     "Commercial",   80,
  "Gas",     "Industrial",   70,
  "Gas",     "Transport",    20,
  "Nuclear", "Industrial",   100,
  "Nuclear", "Commercial",   70,
  "Nuclear", "Residential",  70,
  "Wind",    "Residential",  60,
  "Wind",    "Commercial",   50,
  "Wind",    "Industrial",   40,
  "Solar",   "Residential",  50,
  "Solar",   "Commercial",   30,
  "Solar",   "Industrial",   10
)

source_order <- c("Coal", "Gas", "Nuclear", "Wind", "Solar")
target_order <- c("Industrial", "Residential", "Commercial", "Transport")

# ggplot2 has no native Sankey geom; nodes/links are laid out by hand below
# (geom_rect for nodes, geom_ribbon with smoothstep-eased curves for links)
# using only ggplot2 + dplyr — no ggalluvial/ggsankey/ggforce dependency.

# --- Layout: stack nodes top-down with a fixed padding between them -----
node_width <- 0.07
gap_frac   <- 0.025
total_value <- sum(flows$value)
gap <- gap_frac * total_value

stack_nodes <- function(order, totals) {
  n <- length(order)
  heights <- totals[order]
  y1 <- sum(heights) + gap * (n - 1)
  y0_vec <- numeric(n)
  y1_vec <- numeric(n)
  for (i in seq_len(n)) {
    y0 <- y1 - heights[i]
    y1_vec[i] <- y1
    y0_vec[i] <- y0
    y1 <- y0 - gap
  }
  tibble::tibble(name = order, total = as.numeric(heights), y0 = y0_vec, y1 = y1_vec)
}

source_totals <- flows |> group_by(source) |> summarise(total = sum(value)) |> tibble::deframe()
target_totals <- flows |> group_by(target) |> summarise(total = sum(value)) |> tibble::deframe()

source_nodes <- stack_nodes(source_order, source_totals) |>
  mutate(xmin = 0, xmax = node_width,
         fill_color = IMPRINT_PALETTE[match(name, source_order)])

target_nodes <- stack_nodes(target_order, target_totals) |>
  mutate(xmin = 1 - node_width, xmax = 1, fill_color = INK_SOFT)

node_rects <- bind_rows(source_nodes, target_nodes)

# --- Assign each link a vertical slice within its source and target nodes
link_positions <- flows |>
  arrange(match(source, source_order), match(target, target_order)) |>
  group_by(source) |>
  mutate(src_cum1 = cumsum(value), src_cum0 = src_cum1 - value) |>
  ungroup() |>
  arrange(match(target, target_order), match(source, source_order)) |>
  group_by(target) |>
  mutate(tgt_cum1 = cumsum(value), tgt_cum0 = tgt_cum1 - value) |>
  ungroup() |>
  left_join(source_nodes |> select(source = name, src_top = y1), by = "source") |>
  left_join(target_nodes |> select(target = name, tgt_top = y1), by = "target") |>
  mutate(
    src_ymin = src_top - src_cum1,
    src_ymax = src_top - src_cum0,
    tgt_ymin = tgt_top - tgt_cum1,
    tgt_ymax = tgt_top - tgt_cum0,
    link_id  = row_number()
  )

# --- Interpolate each link into a smooth ribbon (cubic smoothstep ease) -
make_curve <- function(row, n = 60) {
  t <- seq(0, 1, length.out = n)
  ease <- t^2 * (3 - 2 * t)
  tibble::tibble(
    link_id = row$link_id,
    source  = row$source,
    x       = node_width + (1 - 2 * node_width) * t,
    ymin    = row$src_ymin + (row$tgt_ymin - row$src_ymin) * ease,
    ymax    = row$src_ymax + (row$tgt_ymax - row$src_ymax) * ease
  )
}

curves <- link_positions |>
  split(seq_len(nrow(link_positions))) |>
  lapply(make_curve) |>
  bind_rows()

# --- Title (fontsize scales with title length, see plot-generator.md) ---
title_str <- "sankey-basic · r · ggplot2 · anyplot.ai"
title_ratio <- if (nchar(title_str) > 67) 67 / nchar(title_str) else 1.0
title_fontsize <- round(12 * title_ratio)

# --- Plot -----------------------------------------------------------------
p <- ggplot() +
  geom_ribbon(
    data = curves,
    aes(x = x, ymin = ymin, ymax = ymax, group = link_id, fill = source),
    alpha = 0.6, color = NA
  ) +
  geom_rect(
    data = node_rects,
    aes(xmin = xmin, xmax = xmax, ymin = y0, ymax = y1, fill = I(fill_color)),
    color = PAGE_BG, linewidth = 0.6
  ) +
  geom_text(
    data = source_nodes,
    aes(x = xmin - 0.015, y = (y0 + y1) / 2, label = paste0(name, "  ·  ", total, " PJ")),
    hjust = 1, size = 3.2, color = INK
  ) +
  geom_text(
    data = target_nodes,
    aes(x = xmax + 0.015, y = (y0 + y1) / 2, label = paste0(name, "  ·  ", total, " PJ")),
    hjust = 0, size = 3.2, color = INK
  ) +
  scale_fill_manual(values = setNames(IMPRINT_PALETTE[seq_along(source_order)], source_order)) +
  scale_y_continuous(expand = expansion(mult = c(0.02, 0.05))) +
  coord_cartesian(xlim = c(-0.34, 1.34), clip = "off") +
  labs(title = title_str) +
  theme_void(base_size = 8) +
  theme(
    plot.background  = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background = element_rect(fill = PAGE_BG, color = NA),
    plot.title        = element_text(color = INK, size = title_fontsize,
                                      margin = margin(b = 16)),
    legend.position   = "none",
    plot.margin       = margin(t = 24, r = 100, b = 14, l = 100)
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
