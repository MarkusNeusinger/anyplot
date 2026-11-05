### Fixed

- **A summary or a question no longer shows its queue position after the wait.**
  A turn without pipeline steps kept its `queue 1/2` badge until the reply,
  because nothing told the page the wait was over. The agents service now sends
  `status{step:"started"}` once, when a run that waited takes its slot. The API
  passes it on both lanes, and a turn read again after a cut replays it. The
  page clears the badge on it. A plot run that leaves the queue before its first
  step shows `starting…` in its progress grid again. (#12577)
