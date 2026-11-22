#' anyplot.ai
#' bar-stacked-labeled: Stacked Bar Chart with Total Labels
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: pending | Created: 2026-05-18

library(ggplot2)
library(dplyr)
library(ragg)

# --- Theme tokens -----------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint palette
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Columns: set these to your table's column names -------------------------
QUARTER <- "Quarter"          # role: category
PRODUCT <- "Product"          # role: group
REVENUE <- "Revenue (USD)"    # role: value

# --- Data: replace this block with your own table ----------------------------
set.seed(42)
df <- tibble::tibble(
  !!QUARTER := rep(c("Q1", "Q2", "Q3", "Q4"), each = 3),
  !!PRODUCT := rep(c("Electronics", "Apparel", "Home"), 4),
  !!REVENUE := c(
    450000, 320000, 280000,  # Q1
    520000, 380000, 310000,  # Q2
    580000, 420000, 350000,  # Q3
    650000, 480000, 400000   # Q4
  )
)

# --- Plot -------------------------------------------------------------------
df <- df |>
  mutate(across(all_of(c(QUARTER, PRODUCT)), \(v) factor(v, levels = unique(v))))

df_totals <- df |>
  group_by(.data[[QUARTER]]) |>
  summarize(total = sum(.data[[REVENUE]]), .groups = "drop")

fmt_millions <- function(x) paste0("$", format(round(x / 1e6, 2), nsmall = 2), "M")

p <- ggplot(df, aes(x = .data[[QUARTER]], y = .data[[REVENUE]], fill = .data[[PRODUCT]])) +
  geom_col(position = "stack", width = 0.6) +
  geom_text(
    data = df_totals,
    aes(x = .data[[QUARTER]], y = total, label = fmt_millions(total)),
    vjust = -0.5,
    size = 4.2,
    fontface = "bold",
    color = INK,
    inherit.aes = FALSE
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE) +
  scale_y_continuous(
    labels = fmt_millions,
    expand = expansion(mult = c(0, 0.1))
  ) +
  labs(
    title = "bar-stacked-labeled · r · ggplot2 · anyplot.ai",
    x = QUARTER,
    y = REVENUE,
    fill = PRODUCT,
    caption = "Total quarterly revenue by product category"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major   = element_line(color = INK, linewidth = 0.1),
    panel.grid.minor   = element_blank(),
    panel.grid.major.x = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    plot.title         = element_text(color = INK, size = 12, face = "bold", margin = margin(b = 8)),
    plot.caption       = element_text(color = INK_SOFT, size = 7, margin = margin(t = 6)),
    legend.background  = element_rect(fill = PAGE_BG, color = NA),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 10),
    legend.position    = "right",
    plot.margin        = margin(12, 14, 10, 12)
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
