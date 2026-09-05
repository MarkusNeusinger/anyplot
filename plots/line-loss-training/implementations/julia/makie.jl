# anyplot.ai
# line-loss-training: Training Loss Curve
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 86/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
const THEME    = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
const IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
const ANYPLOT_AMBER = colorant"#DDCC77"  # warning / caution — early-stopping marker

# --- Data ---------------------------------------------------------------
# Synthetic training history: training loss decays smoothly, validation loss
# decays alongside it until the model starts overfitting past epoch 45.
epochs = collect(1:80)
n = length(epochs)

train_loss_base = 2.0 .* exp.(-0.065 .* epochs) .+ 0.03
train_loss = train_loss_base .* (1 .+ 0.04 .* randn(n))
train_loss = clamp.(train_loss, 0.02, Inf)

overfit_start = 45
val_loss = zeros(n)
for (i, e) in enumerate(epochs)
    base = 2.2 * exp(-0.058 * e) + 0.16
    if e > overfit_start
        base += 0.0035 * (e - overfit_start)^1.3
    end
    val_loss[i] = clamp(base + 0.035 * randn(), 0.05, Inf)
end

best_epoch = epochs[argmin(val_loss)]
best_val_loss = minimum(val_loss)

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "line-loss-training · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Epoch",
    ylabel             = "Cross-Entropy Loss (log scale)",
    xlabelsize         = 14,
    ylabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    backgroundcolor    = PAGE_BG,
    yscale             = log10,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xgridvisible       = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xminorgridvisible  = false,
    yminorgridvisible  = false,
)

vlines!(ax, [best_epoch]; color = ANYPLOT_AMBER, linewidth = 1.5, linestyle = :dash)

lines!(ax, epochs, train_loss; color = IMPRINT_PALETTE[1], linewidth = 3.0, label = "Training loss")
lines!(ax, epochs, val_loss; color = IMPRINT_PALETTE[2], linewidth = 3.0, label = "Validation loss")

scatter!(ax, [best_epoch], [best_val_loss];
    color = ANYPLOT_AMBER, markersize = 18, strokewidth = 1.5, strokecolor = PAGE_BG,
    label = "Early-stopping epoch")

text!(ax, best_epoch + 3, best_val_loss * 1.9;
    text     = "Best val loss @ epoch $(best_epoch)",
    color    = INK_SOFT,
    fontsize = 13,
    align    = (:left, :baseline),
)

axislegend(ax;
    position      = :rt,
    labelcolor    = INK_SOFT,
    framevisible  = false,
    backgroundcolor = PAGE_BG,
)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
