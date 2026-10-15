### Fixed

- **The prep eval measures the root, not the fake renderer.** Under the default
  `AGENT_RENDERER=fake`, every `run_data_code` call got the fake's fixed
  four-row table back. The root rightly distrusted a 500-step walk that came
  back as four squares and ran its code again, so 9 of the 11 data-code cases
  missed for the fake alone. The eval's data runs now execute the snippet with
  the real harness in data mode and the renderer's limits
  (`agents/evals/host_data.py`). The outcome is read by the same reader as the
  local renderer's. Every data-code case compares the size of the table it
  stored again. (#12198)
- **Two stale prep fixtures.** Since the parser leaves out a summary row at the
  end of a paste, two cases still expected the root to drop that row. The
  English total-row case now has its total at the top, where the parser keeps
  it. The German chain case expects no second drop. A fixture test now refuses
  an expected `drop_rows` that drops nothing. (#12198)
- **Count requests and filters by place stay in step 1.** The scope judge
  refused "only the orders from Bern that were delivered" as data to fetch, and
  read pasted JavaScript data code as a request for another library. The root
  answered "count the bookings per category" as a question instead of
  aggregating. Both prompts now name these cases, and the scope eval has three
  new cases. (#12198)
