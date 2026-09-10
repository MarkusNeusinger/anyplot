# anyplot.ai
# line-3d-trajectory: 3D Line Plot for Trajectory Visualization
# Library: Makie.jl 0.21 | Julia 1.11
# Quality: pending | Created: 2026-09-10

using CairoMakie
using Colors

# --- Theme tokens -----------------------------------------------------------
THEME       = get(ENV, "ANYPLOT_THEME", "light")
PAGE_BG     = THEME == "light" ? colorant"#FAF8F1" : colorant"#1A1A17"
ELEVATED_BG = THEME == "light" ? colorant"#FFFDF6" : colorant"#242420"
INK         = THEME == "light" ? colorant"#1A1A17" : colorant"#F0EFE8"
INK_SOFT    = THEME == "light" ? colorant"#4A4A44" : colorant"#B8B7B0"

IMPRINT_PALETTE = [
    colorant"#009E73", colorant"#C475FD", colorant"#4467A3", colorant"#BD8233",
    colorant"#AE3030", colorant"#2ABCCD", colorant"#954477", colorant"#99B314",
]
ANYPLOT_SEQ = cgrad([colorant"#009E73", colorant"#4467A3"])  # sequential — time progression

# --- Data: Lorenz attractor trajectory (classic chaotic system) ------------
sigma, rho, beta = 10.0, 28.0, 8.0 / 3.0
dt = 0.014
n_steps = 2000

traj_x = zeros(n_steps)
traj_y = zeros(n_steps)
traj_z = zeros(n_steps)
traj_x[1], traj_y[1], traj_z[1] = 0.1, 0.0, 0.0

for i in 1:(n_steps - 1)
    xi, yi, zi = traj_x[i], traj_y[i], traj_z[i]

    k1x, k1y, k1z = sigma * (yi - xi), xi * (rho - zi) - yi, xi * yi - beta * zi
    xa, ya, za = xi + 0.5dt * k1x, yi + 0.5dt * k1y, zi + 0.5dt * k1z

    k2x, k2y, k2z = sigma * (ya - xa), xa * (rho - za) - ya, xa * ya - beta * za
    xb, yb, zb = xi + 0.5dt * k2x, yi + 0.5dt * k2y, zi + 0.5dt * k2z

    k3x, k3y, k3z = sigma * (yb - xb), xb * (rho - zb) - yb, xb * yb - beta * zb
    xc, yc, zc = xi + dt * k3x, yi + dt * k3y, zi + dt * k3z

    k4x, k4y, k4z = sigma * (yc - xc), xc * (rho - zc) - yc, xc * yc - beta * zc

    traj_x[i + 1] = xi + (dt / 6) * (k1x + 2k2x + 2k3x + k4x)
    traj_y[i + 1] = yi + (dt / 6) * (k1y + 2k2y + 2k3y + k4y)
    traj_z[i + 1] = zi + (dt / 6) * (k1z + 2k2z + 2k3z + k4z)
end

# --- Plot ---------------------------------------------------------------
fig = Figure(
    size            = (1600, 900),
    fontsize        = 14,
    backgroundcolor = PAGE_BG,
)

ax = Axis3(
    fig[1, 1];
    title              = "line-3d-trajectory · julia · makie · anyplot.ai",
    titlesize          = 20,
    titlecolor         = INK,
    xlabel             = "X",
    ylabel             = "Y",
    zlabel             = "Z",
    xlabelsize         = 14,
    ylabelsize         = 14,
    zlabelsize         = 14,
    xlabelcolor        = INK,
    ylabelcolor        = INK,
    zlabelcolor        = INK,
    xticklabelsize     = 12,
    yticklabelsize     = 12,
    zticklabelsize     = 12,
    xticklabelcolor    = INK_SOFT,
    yticklabelcolor    = INK_SOFT,
    zticklabelcolor    = INK_SOFT,
    xtickcolor         = INK_SOFT,
    ytickcolor         = INK_SOFT,
    ztickcolor         = INK_SOFT,
    xgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    ygridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    zgridcolor         = RGBAf(INK.r, INK.g, INK.b, 0.15),
    xspinecolor_1      = INK_SOFT,
    yspinecolor_1      = INK_SOFT,
    zspinecolor_1      = INK_SOFT,
    xspinecolor_2      = INK_SOFT,
    yspinecolor_2      = INK_SOFT,
    zspinecolor_2      = INK_SOFT,
    xspinecolor_3      = INK_SOFT,
    yspinecolor_3      = INK_SOFT,
    zspinecolor_3      = INK_SOFT,
    xypanelcolor       = PAGE_BG,
    yzpanelcolor       = PAGE_BG,
    xzpanelcolor       = PAGE_BG,
    backgroundcolor    = PAGE_BG,
    aspect             = :data,
    elevation          = 0.22 * pi,
    azimuth            = -0.32 * pi,
)

lines!(ax, traj_x, traj_y, traj_z; color = 1:n_steps, colormap = ANYPLOT_SEQ, linewidth = 2.5)
scatter!(ax, [traj_x[1]], [traj_y[1]], [traj_z[1]]; color = IMPRINT_PALETTE[1], markersize = 16, strokewidth = 0)

Colorbar(
    fig[1, 2];
    limits       = (0, n_steps * dt),
    colormap     = ANYPLOT_SEQ,
    label        = "Time",
    labelsize    = 14,
    labelcolor   = INK,
    ticklabelsize = 12,
    ticklabelcolor = INK_SOFT,
    tickcolor    = INK_SOFT,
    width        = 14,
)

colsize!(fig.layout, 1, Relative(0.92))

# --- Save -----------------------------------------------------------------
save("plot-$(THEME).png", fig; px_per_unit = 2)
