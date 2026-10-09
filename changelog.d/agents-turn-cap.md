### Changed

- **A chat turn may wait the full queue maximum.** anyplot-api's Cloud Run
  request timeout rises from 600 to 900 seconds and the BFF's turn cap
  `AGENT_TURN_MAX_S` from 590 to 890 seconds, so a turn at the back of a full
  run queue (600 seconds of waiting plus the 180-second run) ends with its own
  `error` and `done` instead of being cut at about 385 seconds. The design
  document records the owner's decisions of 2026-10-10: the queue's capacity
  formula stays, and one run or theme toggle in flight per user stays. (#12113)
