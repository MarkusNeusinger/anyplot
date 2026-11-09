### Changed

- **The chat assistant's turn bounds are code, not prompt sentences.** Each turn may call `prepare_data` and
  `generate_data` twice, `query_data` three times, `run_data_code` twice and the plot pipeline once. The call after a
  cap is refused with a fixed message that tells the assistant to answer with what it has, so the "never more than
  twice" sentences left its instructions. (#12853)
- **No plot run in a turn that changed the data, or on a paste's summary turn.** The server refuses the plot call
  before the run (on a summary turn while the data is unconfirmed), keeps the first plot's wish, and records the stop
  as before. The chat shows no failed plot card for such a turn, and the daily run count no longer counts it, nor a
  plot call made after a library switch was asked for. (#12853)
- **The plot buttons' turns tell the assistant what to call.** On "create the plot" turns, the session facts say to
  call the plot pipeline with no arguments, so the instructions no longer open that rule with it. (#12853)

### Fixed

- **A data change whose result the server refused still counts as the turn's answer.** The empty-reply check read
  only results that passed the size and key checks, so an empty reply after such a change ended as "no reply" although
  the data had changed. (#12853)
