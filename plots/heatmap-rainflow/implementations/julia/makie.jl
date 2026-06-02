# anyplot.ai
# heatmap-rainflow: Rainflow Counting Matrix for Fatigue Analysis
# Library: makie 0.22.10 | Julia 1.11.9
# Quality: 88/100 | Created: 2026-06-02

using CairoMakie
using Colors
using Random

Random.seed!(42)

# Theme tokens
const THEME   = get(ENV, "ANYPLOT_THEME", "light")
const PAGE_BG = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
const INK     = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
const INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

# Imprint sequential colormap for single-polarity continuous data
const ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])

# Data: simulated rainflow counting matrix — variable-amplitude bridge loading
# 80 000 stress cycles binned into a 20×20 amplitude × mean-stress matrix
n_amp  = 20
n_mean = 20

amp_min  = 0.0;   amp_max  = 200.0   # MPa
mean_min = -50.0; mean_max = 250.0   # MPa

amp_step  = (amp_max  - amp_min)  / n_amp
mean_step = (mean_max - mean_min) / n_mean

amp_centers  = [amp_min  + (i - 0.5) * amp_step  for i in 1:n_amp]
mean_centers = [mean_min + (i - 0.5) * mean_step for i in 1:n_mean]

n_cycles = 80_000
# Exponential amplitude distribution: many small cycles, few large ones
amp_raw  = clamp.(-35.0 .* log.(rand(n_cycles)), amp_min + 1e-6, amp_max - 1e-6)
# Gaussian mean stress centred at 100 MPa (σ = 45 MPa)
mean_raw = clamp.(randn(n_cycles) .* 45.0 .+ 100.0, mean_min + 1e-6, mean_max - 1e-6)

amp_idx  = clamp.(ceil.(Int, (amp_raw  .- amp_min)  ./ amp_step),  1, n_amp)
mean_idx = clamp.(ceil.(Int, (mean_raw .- mean_min) ./ mean_step), 1, n_mean)

count_matrix = zeros(Int, n_amp, n_mean)
for k in 1:n_cycles
    count_matrix[amp_idx[k], mean_idx[k]] += 1
end

# Log10 transform; zero-count bins become NaN so they render as background
count_display = Float64.(count_matrix)
count_display[count_matrix .== 0] .= NaN
count_log = log10.(count_display)

valid_log = filter(!isnan, vec(count_log))
max_log   = isempty(valid_log) ? 1.0 : maximum(valid_log)

# Colorbar ticks at round decade values within the data range
all_cb_counts = [1, 10, 100, 1_000, 10_000]
all_cb_vals   = log10.(Float64.(all_cb_counts))
keep          = all_cb_vals .<= max_log + 0.05
cb_vals       = all_cb_vals[keep]
cb_labels     = string.(all_cb_counts[keep])

# Figure: square canvas — 1200×1200 → 2400×2400 at px_per_unit=2
fig = Figure(
    size            = (1200, 1200),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title              = "heatmap-rainflow · julia · makie · anyplot.ai",
    titlesize          = 22,
    titlecolor         = INK,
    xlabel             = "Mean Stress (MPa)",
    ylabel             = "Cycle Amplitude (MPa)",
    xlabelsize         = 16,
    ylabelsize         = 16,
    xticklabelsize     = 13,
    yticklabelsize     = 13,
    backgroundcolor    = PAGE_BG,
    topspinevisible    = false,
    rightspinevisible  = false,
    leftspinecolor     = INK_SOFT,
    bottomspinecolor   = INK_SOFT,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    xgridvisible       = false,
    ygridvisible       = false,
)

# heatmap!(ax, x, y, z): x → mean (cols), y → amplitude (rows); z must be n_mean × n_amp
hm = heatmap!(
    ax,
    mean_centers,
    amp_centers,
    count_log';
    colormap   = ANYPLOT_SEQ,
    nan_color  = PAGE_BG,
    colorrange = (0.0, max_log),
)

cb = Colorbar(
    fig[1, 2],
    hm;
    label          = "Cycle Count",
    labelsize      = 16,
    labelcolor     = INK,
    ticklabelsize  = 13,
    ticklabelcolor = INK_SOFT,
    tickcolor      = INK_SOFT,
    ticks          = (cb_vals, cb_labels),
)

colgap!(fig.layout, 12)

save("plot-$(THEME).png", fig; px_per_unit = 2)
