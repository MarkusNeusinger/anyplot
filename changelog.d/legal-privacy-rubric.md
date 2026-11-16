### Changed

- **The privacy policy puts periods and places beside their data.** On `/legal`, the
  periods and places of the separate "how long it stays" and "where it runs" tables now
  stand in the rows of the data they belong to, most of them on a closing line of their own,
  so the server logs' 30 days stand beside the IP addresses they hold instead of a screen
  further down. On a phone, each item of that line takes a line of its own. The two tables
  are gone; the row that holds for the whole site, the hosting on Google Cloud, stays as a
  sentence under the first table. The crawler copy of the page (`/seo-proxy/legal`) now says what the page says, row
  by row: it gains the shared links it lacked, and the right to object gets back its
  condition.
- **The privacy policy speaks in plain words, without article numbers.** On `/legal`, the
  table of GDPR article numbers is gone: one sentence under "why this is allowed" names each
  legal basis in words beside what it covers, a legitimate interest, your request and your
  consent. The other terms of legal texts give way to everyday words: "who is responsible"
  replaces "controller", the right to object keeps its condition without the statute's
  phrase, and a complaint goes to a data protection authority. Cloudflare uses the bot
  check's signals "on its own behalf"; its legal role is no longer named. The crawler copy
  says the same, word for word, and now also names who is responsible.
- **The privacy policy is shorter.** On `/legal`, the privacy section drops from 998 to 876
  words, and on a phone (390 px) from 6590 to 5654 px high; on a desktop (1440 px), from 3659
  to 2968 px. The machine readers and the shared links share one row, under both anchors
  the stats page links, with each period beside its own store; the edge and the bot check
  are one Cloudflare row whose place stands once. Explanations go: why an unverified share is
  no verdict (the stats tile's hint already says it), that browsing never reaches a model
  because the catalogue is written at build time, the sentence that repeated the
  assistant's heading, what the assistant does and that it is open to everyone, the
  comparison of your code with the catalogue's MIT License, and the sentence naming the
  laws. Every kind of data, its period, place and recipients, the bases and the rights stay.
  The server logs are now "read only to look into a fault or an attack".

### Fixed

- **The database reference no longer contradicts the privacy policy.** The "Data privacy"
  list in `docs/reference/database.md` promised anonymous session ids, usage data deleted
  after 90 days and no personal data, and its first item broke off mid-sentence. It now
  names what each store holds, with the file that shows it, and points to the privacy
  section of the legal page for how long data is kept and where it runs. Its storage
  overview no longer has only an admin send a feedback case of the agent chat, and it says
  that a case keeps the conversation and up to 5 sample rows of the data even when the data
  file is left out.
