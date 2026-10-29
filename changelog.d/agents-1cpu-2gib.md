### Changed

- **The agents service runs on 1 vCPU and 2 GiB.** `anyplot-agents` was sized
  at 2 vCPU and 4 GiB when it still hosted the sandboxes; over the 14 days to
  2026-10-29 its hourly p99 peaked at 0.46 of a core and 370 MiB, since it
  mostly waits on the model and the renderer. 2 GiB keeps headroom for the
  worst case of about 1.1 GiB (the dataset and render stores' 256 MiB caps, a
  1 MB paste's parse and the PNG gates), because an out-of-memory kill would
  lose every session in memory. The renderer stays at 2 vCPU and 4 GiB.
