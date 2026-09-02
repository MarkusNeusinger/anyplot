#' anyplot.ai
#' bar-stacked: Stacked Bar Chart
#' Library: ggplot2 3.5.1 | R 4.4.1
#' Quality: 86/100 | Created: 2026-09-02

library(ggplot2)
library(dplyr)
library(ragg)
library(scales)

set.seed(42)

# --- Theme tokens -------------------------------------------------------
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"

# Imprint categorical palette — first series is always brand green
IMPRINT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233",
                     "#AE3030", "#2ABCCD", "#954477", "#99B314")

# --- Data -----------------------------------------------------------------
# Monthly department budget breakdown, in thousands of dollars.
department_levels   <- c("Engineering", "Sales", "Marketing", "Support")
department_baseline <- c(Engineering = 120, Sales = 80, Marketing = 50, Support = 40)

expense_df <- tibble::tibble(
  month = rep(factor(month.abb[1:6], levels = month.abb[1:6]), times = length(department_levels)),
  department = factor(rep(department_levels, each = 6), levels = department_levels),
  expense = as.vector(sapply(department_baseline, function(base) {
    pmax(round(base + rnorm(6, mean = 0, sd = base * 0.12)), 5)
  }))
)

totals_df <- expense_df %>%
  group_by(month) %>%
  summarise(total = sum(expense), .groups = "drop")

# --- Plot -------------------------------------------------------------------
p <- ggplot(expense_df, aes(x = month, y = expense, fill = department)) +
  geom_col(position = "stack", width = 0.65, color = PAGE_BG, linewidth = 0.3) +
  geom_text(
    data = totals_df,
    aes(x = month, y = total, label = dollar(total, prefix = "$", suffix = "K")),
    inherit.aes = FALSE,
    vjust = -0.6,
    size = 3.2,
    color = INK
  ) +
  scale_fill_manual(values = IMPRINT_PALETTE[1:4], name = "Department") +
  scale_y_continuous(
    labels = label_dollar(prefix = "$", suffix = "K"),
    expand = expansion(mult = c(0, 0.12))
  ) +
  labs(
    title = "bar-stacked · r · ggplot2 · anyplot.ai",
    x = "Month",
    y = "Expense ($K)"
  ) +
  theme_minimal(base_size = 8) +
  theme(
    plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
    panel.background   = element_rect(fill = PAGE_BG, color = NA),
    panel.grid.major.x = element_blank(),
    panel.grid.minor   = element_blank(),
    panel.grid.major.y = element_line(color = INK, linewidth = 0.25),
    axis.ticks         = element_blank(),
    axis.title         = element_text(color = INK, size = 10),
    axis.text          = element_text(color = INK_SOFT, size = 8),
    plot.title         = element_text(color = INK, size = 12),
    legend.background  = element_rect(fill = ELEVATED_BG, color = NA),
    legend.text        = element_text(color = INK_SOFT, size = 8),
    legend.title       = element_text(color = INK, size = 10),
    legend.position    = "right"
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
