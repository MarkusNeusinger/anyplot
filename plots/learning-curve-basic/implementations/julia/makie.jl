# anyplot.ai
# learning-curve-basic: Model Learning Curve
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 85/100 | Created: 2026-09-05

using CairoMakie
using Colors
using Random
using Statistics

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
const TRAIN_COLOR = IMPRINT_PALETTE[1]  # brand green — always first series
const VAL_COLOR   = IMPRINT_PALETTE[3]  # blue — second series

# --- Data ---------------------------------------------------------------
# Digit classifier learning curve: accuracy vs training set size, across
# 8 cross-validation folds. Training accuracy starts near-perfect and eases
# down as the model sees more (harder) examples; validation accuracy starts
# low (underfit on tiny samples) and climbs toward the training curve as
# more data narrows the generalization gap — the classic bias/variance
# diagnostic shape.
n_folds = 8
train_sizes = [80, 160, 240, 360, 480, 640, 800, 1000, 1250, 1500]
n_sizes = length(train_sizes)

train_mean_target = 0.995 .- 0.055 .* (1 .- exp.(-train_sizes ./ 900))
val_mean_target = 0.965 .- 0.28 .* exp.(-train_sizes ./ 500)

train_std_target = 0.05 .* exp.(-train_sizes ./ 500) .+ 0.004
val_std_target = 0.09 .* exp.(-train_sizes ./ 600) .+ 0.008

train_scores = Matrix{Float64}(undef, n_folds, n_sizes)
validation_scores = Matrix{Float64}(undef, n_folds, n_sizes)
for j in 1:n_sizes
    train_scores[:, j] = clamp.(train_mean_target[j] .+ train_std_target[j] .* randn(n_folds), 0.0, 1.0)
    validation_scores[:, j] = clamp.(val_mean_target[j] .+ val_std_target[j] .* randn(n_folds), 0.0, 1.0)
end

train_mean = vec(mean(train_scores; dims = 1))
train_std = vec(std(train_scores; dims = 1))
val_mean = vec(mean(validation_scores; dims = 1))
val_std = vec(std(validation_scores; dims = 1))

# --- Plot -----------------------------------------------------------------
fig = Figure(
    resolution      = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "learning-curve-basic · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "Training Set Size",
    ylabel             = "Accuracy",
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
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    topspinevisible     = false,
    rightspinevisible   = false,
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xgridvisible       = false,
    yminorgridvisible  = false,
)

band!(ax, train_sizes, train_mean .- train_std, train_mean .+ train_std;
      color = (TRAIN_COLOR, 0.18))
band!(ax, train_sizes, val_mean .- val_std, val_mean .+ val_std;
      color = (VAL_COLOR, 0.18))

lines!(ax, train_sizes, train_mean; color = TRAIN_COLOR, linewidth = 3, label = "Training score")
scatter!(ax, train_sizes, train_mean; color = TRAIN_COLOR, markersize = 11, strokewidth = 1.5, strokecolor = PAGE_BG)

lines!(ax, train_sizes, val_mean; color = VAL_COLOR, linewidth = 3, label = "Validation score")
scatter!(ax, train_sizes, val_mean; color = VAL_COLOR, markersize = 11, strokewidth = 1.5, strokecolor = PAGE_BG)

ylims!(ax, 0.6, 1.02)

axislegend(ax; position = :rb, labelcolor = INK_SOFT, framevisible = false, labelsize = 12)

# --- Save -------------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
