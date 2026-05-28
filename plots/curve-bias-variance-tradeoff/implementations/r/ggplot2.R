#' anyplot.ai
#' curve-bias-variance-tradeoff: Bias-Variance Tradeoff Curve
#' Library: ggplot2 | R
#' Quality: pending | Created: 2026-05-28

library(ggplot2)
library(ragg)

set.seed(42)

# --- Theme tokens ---
THEME       <- Sys.getenv("ANYPLOT_THEME", "light")
PAGE_BG     <- if (THEME == "light") "#FAF8F1" else "#1A1A17"
INK         <- if (THEME == "light") "#1A1A17" else "#F0EFE8"
INK_SOFT    <- if (THEME == "light") "#4A4A44" else "#B8B7B0"
INK_MUTED   <- if (THEME == "light") "#6B6A63" else "#A8A79F"
ELEVATED_BG <- if (THEME == "light") "#FFFDF6" else "#242420"

ANYPLOT_PALETTE <- c("#009E73", "#C475FD", "#4467A3", "#BD8233")

# --- Data ---
n            <- 100
complexity   <- seq(1, 10, length.out = n)
irreducible  <- rep(0.15, n)
bias_squared <- 0.70 * exp(-0.5 * (complexity - 1))
variance     <- 0.70 * exp(-0.5 * (10 - complexity))
total_error  <- bias_squared + variance + irreducible

optimal_idx <- which.min(total_error)
optimal_x   <- complexity[optimal_idx]
optimal_y   <- total_error[optimal_idx]

bias_ann_y <- bias_squared[which.min(abs(complexity - 1.4))] + 0.04
var_ann_y  <- variance[which.min(abs(complexity - 8.5))] + 0.04
tot_ann_y  <- total_error[which.min(abs(complexity - 3.0))] + 0.05

# --- Long format ---
components <- c("Bias²", "Variance", "Total Error", "Irreducible Error")
df_long <- data.frame(
    complexity = rep(complexity, 4),
    error      = c(bias_squared, variance, total_error, irreducible),
    component  = factor(rep(components, each = n), levels = components)
)

curve_colors    <- setNames(ANYPLOT_PALETTE, components)
curve_linetypes <- c("Bias²" = "solid", "Variance" = "longdash",
                     "Total Error" = "solid", "Irreducible Error" = "dotted")
curve_lwidths   <- c("Bias²" = 1.0, "Variance" = 1.0,
                     "Total Error" = 1.7, "Irreducible Error" = 0.9)

title_str <- "curve-bias-variance-tradeoff · r · ggplot2 · anyplot.ai"

# --- Plot ---
p <- ggplot(df_long,
            aes(x = complexity, y = error,
                color = component, linetype = component,
                linewidth = component)) +
    annotate("rect", xmin = 1, xmax = optimal_x,
             ymin = -Inf, ymax = Inf, fill = "#009E73", alpha = 0.05) +
    annotate("rect", xmin = optimal_x, xmax = 10,
             ymin = -Inf, ymax = Inf, fill = "#AE3030", alpha = 0.05) +
    geom_vline(xintercept = optimal_x, color = INK_SOFT,
               linetype = "dashed", linewidth = 0.5) +
    geom_line() +
    scale_color_manual(values = curve_colors) +
    scale_linetype_manual(values = curve_linetypes) +
    scale_linewidth_manual(values = curve_lwidths) +
    annotate("text", x = (1 + optimal_x) / 2, y = 0.86,
             label = "Underfitting", color = INK_MUTED, size = 3.0) +
    annotate("text", x = (optimal_x + 10) / 2, y = 0.86,
             label = "Overfitting", color = INK_MUTED, size = 3.0) +
    annotate("text", x = optimal_x + 0.2, y = optimal_y - 0.04,
             label = "Optimal", color = INK_SOFT, size = 2.8, hjust = 0) +
    annotate("text", x = 1.4, y = bias_ann_y,
             label = "Bias²", color = ANYPLOT_PALETTE[1],
             size = 3.2, hjust = 0, fontface = "bold") +
    annotate("text", x = 8.5, y = var_ann_y,
             label = "Variance", color = ANYPLOT_PALETTE[2],
             size = 3.2, hjust = 0.5, fontface = "bold") +
    annotate("text", x = 3.0, y = tot_ann_y,
             label = "Total Error", color = ANYPLOT_PALETTE[3],
             size = 3.0, hjust = 0.5, fontface = "bold") +
    annotate("text", x = 7.0, y = 0.10,
             label = "Irreducible Error", color = ANYPLOT_PALETTE[4],
             size = 2.8, hjust = 0.5) +
    scale_x_continuous(
        breaks = c(1, optimal_x, 10),
        labels = c("Low", "Optimal", "High"),
        expand = c(0.02, 0)
    ) +
    scale_y_continuous(expand = c(0.02, 0)) +
    labs(
        title    = title_str,
        subtitle = "Total Error = Bias² + Variance + Irreducible Error",
        x        = "Model Complexity",
        y        = "Prediction Error"
    ) +
    theme_minimal(base_size = 8) +
    theme(
        plot.background    = element_rect(fill = PAGE_BG, color = PAGE_BG),
        panel.background   = element_rect(fill = PAGE_BG, color = NA),
        panel.grid.major.y = element_line(color = INK, linewidth = 0.15),
        panel.grid.major.x = element_blank(),
        panel.grid.minor   = element_blank(),
        panel.border       = element_blank(),
        axis.title         = element_text(color = INK, size = 10),
        axis.text          = element_text(color = INK_SOFT, size = 8),
        axis.line          = element_line(color = INK_SOFT, linewidth = 0.4),
        plot.title         = element_text(color = INK, size = 12, face = "bold"),
        plot.subtitle      = element_text(color = INK_MUTED, size = 8),
        legend.position    = "none",
        plot.margin        = margin(15, 20, 15, 15)
    )

# --- Save ---
ggsave(
    filename = sprintf("plot-%s.png", THEME),
    plot     = p,
    device   = ragg::agg_png,
    width    = 8,
    height   = 4.5,
    units    = "in",
    dpi      = 400
)
