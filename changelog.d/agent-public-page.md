### Added

- **The public "use with my data" page at `/agent`, experimental.** The chat
  page runs on the public lane while the API says it is open
  (`GET /agent/lane`), so one switch on the server opens and closes the page
  and its entry points. It talks to `/agent/*` without a cookie, with a random
  id per browser tab and the session id as headers, and says above the first
  input that an AI does the work, which one and where, that results can be
  wrong and are not checked by hand, what not to paste, that nothing is stored
  without feedback, and that daily limits apply. The plot page's `.adapt()`
  button shows for everyone while the lane is open, and the landing page
  points to the chat with one line. Admins keep `/debug/agent` with
  everything (#12528).

### Changed

- **Feedback and `.save()` leave the data file out unless you tick the box.**
  On the public page both `# include data.csv` boxes start unticked, and the
  feedback form says what sending stores; admins keep their default (#12528).
- **The legal page covers the public assistant.** Its section (now
  `#assistant`) says the assistant is experimental, open to everyone and
  pausable, how ids and IP addresses are salted and never written down, adds
  use and warranty, the generated code's licence with the Highcharts note, and
  the transfers under Google Cloud's and Cloudflare's terms; the feedback IP
  hash wording follows the salted hash, and the bot-facing legal page mirrors
  the facts (#12528).
