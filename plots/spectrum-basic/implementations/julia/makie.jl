# anyplot.ai
# spectrum-basic: Frequency Spectrum Plot
# Library: makie 0.21.9 | Julia 1.11.9
# Quality: 80/100 | Created: 2026-09-09

using CairoMakie
using Colors
using Random

Random.seed!(42)

# --- Theme tokens -----------------------------------------------------------
THEME    = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG  = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
INK      = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"
IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]

# --- Data --------------------------------------------------------------------
# Synthetic vibration signal from a rotating machine: shaft rotation (42 Hz),
# a gear-mesh harmonic (126 Hz), a bearing-fault tone (310 Hz), plus noise.
sample_rate = 2048.0
n_samples = 2048
t = (0:(n_samples - 1)) ./ sample_rate

shaft_hz = 42.0
gearmesh_hz = 126.0
bearing_hz = 310.0

signal = 1.0 .* sin.(2π * shaft_hz .* t) .+
         0.5 .* sin.(2π * gearmesh_hz .* t) .+
         0.25 .* sin.(2π * bearing_hz .* t) .+
         0.05 .* randn(n_samples)

# Discrete Fourier transform (positive-frequency half), vectorized as a
# matrix-vector product since FFTW is not available in this runtime.
bin_index = collect(0:(n_samples ÷ 2))
sample_index = collect(0:(n_samples - 1))
angle_matrix = (-2π / n_samples) .* (bin_index * sample_index')
spectrum = sqrt.((cos.(angle_matrix) * signal) .^ 2 .+ (sin.(angle_matrix) * signal) .^ 2) ./ n_samples

frequency = bin_index .* (sample_rate / n_samples)
amplitude_db = 20 .* log10.(spectrum .+ 1e-6)

# Keep only the audible/mechanical band of interest (skip the DC bin for log scale)
mask = frequency .>= 1.0
frequency = frequency[mask]
amplitude_db = amplitude_db[mask]

# Locate the actual peak bin nearest each named harmonic, so the annotation
# sits exactly on the rendered curve rather than the theoretical frequency.
function nearest_peak_index(target_hz, window_hz = 8.0)
    candidates = findall(f -> abs(f - target_hz) <= window_hz, frequency)
    candidates[argmax(amplitude_db[candidates])]
end

peak_names = ["shaft", "gear mesh", "bearing fault"]
peak_targets = [shaft_hz, gearmesh_hz, bearing_hz]
peak_indices = [nearest_peak_index(f) for f in peak_targets]
peak_freqs = frequency[peak_indices]
peak_amps = amplitude_db[peak_indices]
peak_labels = ["$(round(Int, f)) Hz · $name" for (f, name) in zip(peak_freqs, peak_names)]

# --- Plot ---------------------------------------------------------------------
title_str = "spectrum-basic · julia · makie · anyplot.ai"

fig = Figure(
    resolution = (1600, 900),
    fontsize = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis(
    fig[1, 1];
    title = title_str,
    titlesize = 20,
    titlecolor = INK,
    xlabel = "Frequency (Hz)",
    ylabel = "Amplitude (dB)",
    xlabelsize = 14,
    ylabelsize = 14,
    xlabelcolor = INK,
    ylabelcolor = INK,
    xticklabelsize = 12,
    yticklabelsize = 12,
    xticklabelcolor = INK_SOFT,
    yticklabelcolor = INK_SOFT,
    xtickcolor = INK_SOFT,
    ytickcolor = INK_SOFT,
    xscale = log10,
    backgroundcolor = PAGE_BG,
    topspinevisible = false,
    rightspinevisible = false,
    leftspinecolor = INK_SOFT,
    bottomspinecolor = INK_SOFT,
    ygridcolor = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xgridvisible = false,
    yminorgridvisible = false,
)

lines!(ax, frequency, amplitude_db; color = IMPRINT_PALETTE[1], linewidth = 2.5)

# Highlight the three dominant harmonics with markers + labels, giving the
# viewer a guided read of the shaft/gear-mesh/bearing-fault components.
scatter!(
    ax, peak_freqs, peak_amps;
    color = IMPRINT_PALETTE[1], markersize = 14,
    strokewidth = 2, strokecolor = PAGE_BG,
)
text!(
    ax, peak_freqs, peak_amps;
    text = peak_labels, color = INK, fontsize = 13,
    align = (:center, :bottom), offset = (0, 10),
)

# --- Save -----------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
