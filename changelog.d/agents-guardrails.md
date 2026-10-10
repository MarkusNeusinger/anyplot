### Added

- **The agent chat refuses requests for data it would have to fetch.** A
  message that wants stock prices, the weather, inflation figures, exchange
  rates, sports results, the contents of a URL or a public dataset now ends at
  the first turn with a fixed answer, in English or German, that no internet
  source can be tapped and that the data must be pasted as a table. The scope
  judge has a new verdict `needs_data`, the stream a matching `refusal` code,
  and the chat page counts it as its own `agent_guardrail_block` reason.
- **A scope eval measures the scope judge.** `python -m agents.evals.scope`
  sends the 172 synthetic cases of `agents/evals/scope.evalset.json` (54 in
  scope, 53 off-topic, 65 adversarial: overrides, role play, German, base64,
  multi-turn drift, plot-framed and mixed requests, contact details in plot
  text, data to fetch) straight to the judge, with no agent and no render, and
  fails below the design's gates: every adversarial case refused and at most
  5 % false refusals. A run costs about $0.03; a `--tags` subset gates only
  what it measures and writes its own report.
- **`AGENT_KEEP_REFUSALS` and `AGENT_ATTACK_STRIKES`.** With the first switch
  on, the text and verdict of each refused message stay in a bounded in-memory
  ring per session that the feedback bundle of the `/v1` route shows while the
  session lives, a phase-1 stub until refusals are stored with the quick
  feedback. Three `attack` verdicts of the scope or dataset judge in a day, on
  three different messages or datasets, give a user the budget refusal for the
  rest of it.

### Changed

- **The scope judge refuses mixed and plot-framed requests and sees the last
  turns.** A message that also asks for anything out of scope, text meant for
  use outside the plot (emails, posts, newsletters, summaries, translations)
  and plot text with an advertisement or contact details are out of scope, with
  ten examples in the rubric; the root's prompt says the same. The judge now
  also gets the user's last three turns (1,500 characters at most), so a
  request split across turns is judged as a whole, and after a refusal the
  refusal itself as the last assistant turn.
- **Contact details are kept out of change requests, new plot text, datasets
  and the chat.** A new deterministic filter finds web addresses (a
  top-level-domain list in code, Unicode look-alikes folded, code-name
  subdomains seen through), e-mail addresses and phone numbers (German and
  North American formats): the stream strips them from every root reply,
  ToolSafety refuses a change request that carries one, the pipeline rejects
  new string literals and comments with one, and the dataset route refuses a
  dataset with one in a header or a cell (a cell that is only a bare domain,
  such as `amazon.com`, passes). Text the plot code builds at run time is not
  covered yet. A change of a previous version may add at most 300 characters
  of new string literals instead of 2,000, and all versions together at most
  2,000 against the catalogue code; dataset headers and cells are free.
- **An output guard replaces off-topic root replies.** A reply of more than
  five sentences or 500 characters that ties fewer than a third of its
  sentences to the plot, its data, its code or its files becomes the fixed
  refusal, in English, German, French, Spanish and Italian, before it is
  stored, so it never reaches the next turn's context. Root replies are capped
  at 1,200 characters instead of 3,000.
- **The dataset judge sees what the root and the adapter see.** It now gets the
  same five sample rows and five top values as the profile, cells in full, in
  parts of about 4,000 characters instead of a cut-down view; a deterministic
  pre-filter refuses a header or cell addressed to an AI anywhere in the
  dataset before the judge runs.
