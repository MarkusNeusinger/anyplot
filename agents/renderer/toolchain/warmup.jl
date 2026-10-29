# What the renderer's Julia row loads with `-L` before `plot.jl` (agents/renderer/commands.py, JULIA_WARMUP): the
# precompile workload's package, whose image carries the native code of the calls a plot makes most
# (AnyplotWarmup/src/AnyplotWarmup.jl). `-L` keeps `plot.jl` the program: PROGRAM_FILE, the error frames and the exit
# code stay the plot's.
import AnyplotWarmup
