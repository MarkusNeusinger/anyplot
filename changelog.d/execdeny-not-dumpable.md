### Fixed

- **The renderer deploy builds its toolchain again: R survives a killed child on
  older kernels.** The first deploy of the toolchain image failed in its R check
  with "Bad system call": the exec filter kills the child R's `popen` and
  `system()` start with `vfork`, and before Linux 5.16 that child's core dump
  killed every process sharing its memory, R included. The preload library now
  makes the process non-dumpable before it installs the filter, so the child dies
  alone on every kernel.
