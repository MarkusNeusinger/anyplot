### Changed

- **The privacy policy says that a telemetry line can be matched to its
  request for 30 days.** A telemetry line of the data assistant holds no
  request id, but while the request's own log lines are kept it can be
  matched to them: by its time, and exactly by its token counts, which are
  the sums of that request's lines. The "logs" row on `/legal` and its
  crawler copy now say so in one sentence; the telemetry reference describes
  the match in detail. (#13185)
