### Fixed

- **The plot-code validator refuses frame and generator introspection.** A security review
  of 2026-10-14 found that a generator's frame (`gi_frame`, then `f_builtins`) reached the
  interpreter's builtins without a dunder name, which the SECURITY profile allowed. Frame,
  generator, coroutine, traceback and code-object attributes (`gi_frame`, `gi_code`,
  `cr_frame`, `f_back`, `f_builtins`, `f_globals`, `f_locals`, `tb_frame`, `co_consts` and
  their siblings) are now refused on any object. The renderer's gVisor sandbox (read-only,
  no egress, no secrets in its environment) bounded the exposure; catalogue eligibility is
  unchanged (285 matplotlib and 287 seaborn files).
