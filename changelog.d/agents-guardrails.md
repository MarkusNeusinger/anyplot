### Added

- **The agent chat refuses requests for data it would have to fetch.** A
  message that wants stock prices, the weather, inflation figures, exchange
  rates, sports results, the contents of a URL or a public dataset now ends at
  the first turn with a fixed answer, in the user's language, that no internet
  source can be tapped and that the data must be pasted as a table. The scope
  judge has a new verdict `needs_data`, the stream a matching `refusal` code,
  and the chat page counts it as its own `agent_guardrail_block` reason.
- **A scope eval measures the scope judge.** `python -m agents.evals.scope`
  sends the 175 synthetic cases of `agents/evals/scope.evalset.json` (57 in
  scope, three of them with personal data such as payee names or an e-mail
  address in a byline; 53 off-topic; 65 adversarial: overrides, role play,
  German, base64, multi-turn drift, plot-framed and mixed requests,
  advertisements and calls to action in plot text, data to fetch) straight to
  the judge, with no agent and no render, and fails below the design's gates:
  every adversarial case refused and at most 5 % false refusals. A run costs
  about $0.03; a `--tags` subset gates only what it measures and writes its
  own report.
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
  and plot text whose purpose is an advertisement, a call to action or a
  message to other people are out of scope, judged by intent, with twelve
  examples in the rubric; the root's prompt says the same. The judge now also
  gets the user's last three turns (1,500 characters at most), so a request
  split across turns is judged as a whole, and after a refusal the refusal
  itself as the last assistant turn.
- **Personal data is allowed in plots and in the chat.** A user may plot
  their own tax return, contact list or customer table: names, postal and
  e-mail addresses, phone numbers, web addresses and amounts may appear in
  tick labels, titles, annotations and the conversation, and no guardrail
  refuses or strips them for what they are. The guardrails stop misuse of the
  model (spam text, off-topic generation, advertisements, calls to action,
  messages to other people), and the dataset judge and its pre-filter look
  for injection only. The agents service keeps a session's data in memory for
  the session's lifetime; anyplot stores it only when the user submits quick
  feedback, with the data file only when its data box is ticked.
- **Plot text that a change adds is bounded.** A change of a previous version
  may add at most 300 characters of new string literals instead of 2,000, and
  all versions together at most 2,000 against the catalogue code; dataset
  headers and cells are free. The budget bounds how much text the model
  writes, not what it says.
- **Root replies over 1,200 characters become the fixed refusal, in every
  language.** The output guard replaces a sanitised reply longer than root.md's
  "two to five sentences, or a short list" allows with the fixed
  `out_of_scope` refusal before it is stored, so it never reaches the next
  turn's context. It counts characters, not sentences, and uses no word list,
  so it works the same in every language and script. Root replies were cut at
  3,000 characters before.
- **The fixed refusals speak eight languages.** The out-of-scope, data,
  budget and text-only refusals are hand-written in English, German, French,
  Spanish, Italian, Portuguese, Dutch and Polish, in the informal address;
  every other language gets the English text, and no model writes or
  translates a refusal.
- **The dataset judge sees what the root and the adapter see.** It now gets the
  same five sample rows and five top values as the profile, cells in full, in
  parts of about 4,000 characters instead of a cut-down view; a deterministic
  pre-filter refuses a header or cell addressed to an AI anywhere in the
  dataset before the judge runs.
