### Added

- **The agent chat refuses requests for data it would have to fetch.** A
  message that wants stock prices, the weather, inflation figures, exchange
  rates, sports results, the contents of a URL or a public dataset now ends at
  the first turn with a fixed answer, in English or German, that no internet
  source can be tapped and that the data must be pasted as a table. The scope
  judge has a new verdict `needs_data`, the stream a matching `refusal` code,
  and the chat page counts it as its own `agent_guardrail_block` reason.
- **A scope eval measures the scope judge.** `python -m agents.evals.scope`
  sends the 170 synthetic cases of `agents/evals/scope.evalset.json` (54 in
  scope, 53 off-topic, 63 adversarial: overrides, role play, German, base64,
  multi-turn drift, plot-framed and mixed requests, contact details in plot
  text, data to fetch) straight to the judge, with no agent and no render, and
  fails below the design's gates: every adversarial case refused and at most
  5 % false refusals. A run costs about $0.03.
- **`AGENT_KEEP_REFUSALS` and `AGENT_ATTACK_STRIKES`.** With the first switch
  on, the text and verdict of each refused message stay in a bounded in-memory
  ring per session that only the feedback bundle shows, so false refusals can
  be found and turned into eval cases. Three `attack` verdicts of the scope or
  dataset judge in a day give a user the budget refusal for the rest of it.

### Changed

- **The scope judge refuses mixed and plot-framed requests and sees the last
  turns.** A message that also asks for anything out of scope, text meant for
  use outside the plot (emails, posts, newsletters, summaries, translations)
  and plot text with an advertisement or contact details are out of scope, with
  ten examples in the rubric; the root's prompt says the same. The judge now
  also gets the user's last three turns (1,500 characters at most), so a
  request split across turns is judged as a whole.
- **Contact details never reach the user's plot or the chat.** A new
  deterministic filter finds web addresses (a top-level-domain list in code),
  e-mail addresses and phone numbers: the stream strips them from every root
  reply, ToolSafety refuses a change request that carries one, and the pipeline
  rejects new string literals with one. A change of a previous version may add
  at most 300 characters of new string literals instead of 2,000, and a root
  reply of more than five sentences that never mentions the plot becomes the
  fixed refusal.
- **The dataset judge sees what the root and the adapter see.** It now gets the
  same five sample rows and five top values as the profile, cells in full, in
  parts of about 4,000 characters instead of a cut-down view; a deterministic
  pre-filter refuses a header or cell addressed to an AI, or a URL, anywhere in
  the dataset before the judge runs.
