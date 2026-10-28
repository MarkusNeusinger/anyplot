### Changed

- **The agents deploy serves all six Python libraries.** `_LIBRARIES` in
  `agents/cloudbuild.yaml` now names plotnine, altair, pygal and lets-plot next to
  matplotlib and seaborn, so the admin can test each one in the live chat; only the
  admin reaches the chat yet. Each library's 80 % eval matrix now gates the public
  release. `AGENT_LIBRARIES` keeps its default `matplotlib,seaborn`.

### Security

- **The render harness has the kernel refuse every program start.** Arming a guard
  now installs a seccomp filter (`install_exec_deny` in
  `agents/anyplot/render/harness.py`) under which the kernel refuses every `execve`
  and `execveat` of the process, its threads (those already running included) and
  its children. So native code the audit hook cannot see, such as the ImageMagick
  delegates in lets-plot's bridge, starts no program, whatever is on `PATH`. The
  filter covers every in-process run (Python renders, data runs and conversions);
  `fork` and threads stay allowed. lets-plot's command row requires it
  (`ANYPLOT_DENY_EXEC=required`): without the filter, its render stops before the
  plot. Every other run goes on and reports the filter's state in the harness's end
  line, which the renderer logs with every launch. `ci-image.yml` checks the routes in
  the built image.
