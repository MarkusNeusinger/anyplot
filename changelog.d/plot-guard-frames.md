### Fixed

- **The render harness refuses frames to plot code.** In plot mode the agent
  chat's audit hook (`PlotGuard`) now refuses `gi_frame`, `cr_frame`,
  `ag_frame`, `tb_frame`, `sys._getframe` and `sys._current_frames` while plot
  code is on the stack, as data mode already did, so a frame's `f_builtins`
  cannot hand out `open` and `__import__` past the validator. Import bodies, a
  short list of library readers (pandas' chained-assignment check, statsmodels'
  graphics, the `traceback` summaries pyparsing builds for mathtext) and the
  traceback the interpreter prints after a failed plot stay allowed. A sweep of
  the 572 eligible catalogue matplotlib and seaborn files rendered the same 565
  before and after, with no refusal. (#12181)
- **The code validator bans cache and spill directories.** The keywords
  `memory=`, `temp_folder=` and `cachedir=` and the helpers `Memory`,
  `check_memory` and `Parallel` are findings, so exported code with a
  scikit-learn `Pipeline(memory=...)` no longer writes a cache directory on the
  user's machine. (#12181)
