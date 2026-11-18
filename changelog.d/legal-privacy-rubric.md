### Changed

- **The privacy policy puts periods and places beside their data.** On `/legal`, the
  periods and places of the separate "how long it stays" and "where it runs" tables now
  stand in the rows of the data they belong to, most of them on a closing line of their own,
  so the server logs' 30 days stand beside the IP addresses they hold instead of a screen
  further down. On a phone, each item of that line takes a line of its own. The two tables
  are gone; the row that holds for the whole site, the hosting on Google Cloud, stays as a
  sentence under the first table. The crawler copy of the page (`/seo-proxy/legal`) now
  says what the page says, row by row: it gains the shared links it lacked, and the right
  to object gets back its condition. (#13182)
- **The privacy policy speaks in plain words, without article numbers.** On `/legal`, the
  table of GDPR article numbers is gone: three points under "why this is allowed" name each
  legal basis in words beside what it covers, a legitimate interest, your request and your
  consent. The other terms of legal texts give way to everyday words: "who is responsible"
  replaces "controller", the right to object keeps its condition without the statute's
  phrase, and a complaint goes to a data protection authority. Cloudflare uses the bot
  check's signals "on its own behalf"; its legal role is no longer named. The three points
  that were headed "what we do not do" stand under "in short": each starts with "no", and a
  heading that negates as well read as the opposite. The crawler copy says the same, and now
  also names who is responsible. (#13182)
- **The privacy policy is set more compactly.** On `/legal`, the privacy section is 6859 px
  high on a phone (390 px) where it was 7328, and 3421 px on a desktop (1440 px) where it was
  4009. Its word count stays about the same (1128 to 1120, counted at 390 px), because the
  page also says more than it did: who reads feedback and under which terms, and how long
  backups keep a deleted entry. The data assistant's status, its limits and the terms for
  your code now stand on its explainer page, `/agent`, which the assistant's first row
  links; what the limits count on, your tab id and your IP address, stays on the legal page.
  The machine readers and the shared links share one row, under both anchors the
  stats page links: it says what each counts, that neither holds an IP address or a
  user-agent, and how long each is kept, beside its own store, and where; the fields of a
  line and of a counter stay in the docs, and with them that a line is content-free and says
  nothing about anyone's browsing, and that a counter holds no time of day and nothing about
  who shared. The edge and the bot check are one Cloudflare row whose place stands once.
  Explanations go: why an unverified share is no verdict (the stats tile's hint already says
  it), that browsing never reaches a model because the catalogue is written at build time,
  the sentence that repeated the assistant's heading, that the assistant is open to
  everyone, the comparison of your code with the catalogue's MIT License, and the sentence
  naming the laws. Every kind of data, its period, place and recipients, the bases and the
  rights stay. The list of what the site does not do speaks as its one operator, "what I do
  not do", and stands right after "who is responsible": three short points, with what the
  browser's storage keeps and the operator's own Cloudflare Access sign-in in a paragraph
  below them. Long sentences are split without adding or dropping a claim: the legal bases
  are three points, and the bot check, the ids row and the assistant's feedback row each
  read as shorter sentences. (#13182)
- **The privacy policy says who reads feedback.** The site's feedback row no longer says that
  only the operator reads an entry: he reads them, and when he works on one, its message, page
  and reaction can go to an AI coding assistant such as Claude Code by Anthropic. The data
  assistant's feedback row adds that he reads the cases to fix what went wrong, also with AI
  coding assistants and in test runs on other AI models: the visitor's reaction and message,
  the conversation, the data sample or file, the plot and its code, the run's details and the
  two hashes. Both rows name the terms: those tools process the data under their providers'
  own terms, outside the EU hosting and the EU route the page names, with training on what the
  operator sends switched off. The consent line under the chat's feedback form says who reads
  a case in the same words, and names both periods: 180 days for the chat, its plots and the
  data sample, and the message and the reaction until their deletion is asked. The crawler
  copy says the same as the page, and names the operator, not
  admins, as the holder of the Cloudflare Access login cookie. (#13182)
- **The chat's hint for a table that is too large no longer points at a way that ends in the
  same refusal.** It recommended opening an Excel or Parquet file, which may be 5 MB, but the
  table inside such a file has to fit the same 20,000 rows and 1 MB of text. The hint now
  says so. (#13182)
- **The feedback widget speaks as the operator, and the copied prompt asks not to quote the
  visitor's message.** The widget's thank-you line now reads "I read every note.", as the
  site's feedback row says "I read them". The prompt that the admin page copies for the coding
  assistant asks it not to quote the visitor's message in a commit, a pull request or an
  issue, because the repository is public. (#13182)
- **The legal notice links the About page.** Its disclaimer says the plot examples are
  generated and maintained by AI workflows and links the About page for how that works and
  the operator's part in it. (#13182)
- **The privacy policy says how to find your entry, and what stays.** The rights paragraph
  on `/legal` now asks for what you sent and roughly when, or the contact you typed, so the
  operator can find the entry, and says that log lines cannot be deleted one by one: they
  expire after 30 days (server logs) or 180 days (machine reads, assistant telemetry), the
  periods their own rows give, and that the database's automatic backups keep a deleted entry
  for about 30 days. The GitHub row adds that the operator removes a credited username from
  its spec on request, while the public history keeps it. The crawler copy says the same.
  (#13182)

### Fixed

- **The privacy policy names the session hash a feedback case keeps.** The data assistant's
  feedback row said that a case's triage row keeps a hash of your tab id; it also keeps a
  hash of the session id. The row and its crawler copy now name both. (#13182)
- **The database reference no longer contradicts the privacy policy.** The "Data privacy"
  list in `docs/reference/database.md` promised anonymous session ids, usage data deleted
  after 90 days and no personal data, and its first item broke off mid-sentence. It now
  names what each store holds, with the file that shows it, and points to the privacy
  section of the legal page for how long data is kept and where it runs. Its storage
  overview no longer has only an admin send a feedback case of the agent chat, and it says
  that a case keeps the conversation and up to 5 sample rows of the data even when the data
  file is left out, and it names the case bucket's region, the Netherlands (europe-west4), as
  the privacy section does. (#13182)
- **The database reference gives the real backup settings.** Its "Automated backups" list in
  `docs/reference/database.md` said the backups start at 3:00 AM UTC and are kept for 7 days.
  They start at 19:00 UTC, and the 30 most recent are kept, about 30 days, with
  point-in-time recovery over 7 days of transaction logs, in the EU multi-region. The section
  now says so and names the read-only command that shows the settings. (#13182)
